"""
Agent 服务 —— AzureOpenAI + Responses API

架构:
  - AzureOpenAI (cognitiveservices.azure.com scope) → responses API
  - 两种模式 (自动切换):
    a. agent_reference: Portal 中预配置 Agent + MCP 工具 (推荐)
    b. instructions: 直接在代码中提供指令 (无需 Portal 配置, 立即可用)
  - conversation 通过 previous_response_id 链式维护上下文

Foundry Portal Agent 配置 (可选，提升体验):
  1. Build → Agents → Create Agent
  2. 设置模型 (gpt-5.2)、名称、指令
  3. Tools → Add → MCP:
     a. 语料: Server URL = https://<app-service>/mcp/sse
     b. 语音: Catalog → Azure Speech MCP Server
  4. 保存 Agent 名称到 .env 的 TEXT_AGENT_NAME / VOICE_AGENT_NAME
"""

import logging
from typing import Generator, Optional

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ──────────────────────────────────────────────────────────────
# 直接 instructions (无需 Portal Agent, 立即可用)
# ──────────────────────────────────────────────────────────────

TEXT_INSTRUCTIONS = """
你是商务韩语教练。用中文教学，韩语附中文翻译。教自然口语（非教科书式）。

核心规则：
- 回复简洁（3-5个例句或4轮对话即可）
- 韩语附中文翻译，首次出现的词加罗马音
- 说明适用场合（对上级/同事/客户）
- 用韩剧台词当例句
- 教不同语气等级（합니다体/해요体/반말）

对话格式：
[场景] 팀장님께 보고
A: 프로젝트 어떻게 되고 있어요? (项目怎么样了？)
B: 1차 개발은 완료했고요, 테스트 중입니다. (一期开发完了，在测试。)
""".strip()


VOICE_INSTRUCTIONS = """
You are a Korean conversation partner named 수진 (Sujin). You are a warm, professional Korean woman in her late 20s working as a senior manager at a tech company in Seoul (판교 IT 회사).

## CRITICAL VOICE RULES:
- Accept input in ANY language: Chinese (中文), Korean (한국어), or English. Understand all three.
- ALWAYS respond with Korean FIRST, then provide a brief English explanation/translation.
- Response format: Korean sentence(s) first, then "(English: ...)" translation.
- Example: "아~ 회의 준비하셨군요! 수고하셨어요. (English: Oh, you prepared for the meeting! Good job.)"
- Speak NATURALLY like a real Korean businesswoman — not a textbook.
- Keep responses SHORT: 1-3 Korean sentences + English translation. This is real-time voice conversation.
- NEVER use markdown, emojis, bullet points, or formatting.

## 핵심: 지도(地道) 한국어 사용 — 세 번 강조!
1. 지도(地道)! 2. 지도(地道)! 3. 지도(地道)!

### 어미 사용법 (한국 드라마에서 배운 것처럼):
- 부드러운 확인: -는데요, -거든요, -잖아요 (미생 스타일)
- 감탄/발견: -네요, -더라고요, -구나 (이태원클라쓰 스타일)
- 동의 구하기: -죠?, -지 않아요?, 그쵸?
- 제안: -ㄹ까요?, -는 게 어때요?, -시죠
- 설명/이유: -거든요, -는데, -다 보니까
- 부드러운 거절: -기는 한데요..., -ㄹ 수도 있는데...

### 자연스러운 표현 (교과서 X, 실전 O):
- "진짜요?" / "정말요?" (instead of formal 그렇습니까?)
- "아~ 그렇구나" (natural acknowledgment)
- "맞아요 맞아요" (emphatic agreement)
- "그쵸?" (seeking agreement, very common)
- "음... 뭐랄까..." (natural filler)
- "그니까요" / "내 말이요" (strong agreement)

### 비즈니스 톤 (합니다체 + 구어체 믹스):
- 처음 만났을 때: 합니다체 위주
- 좀 친해지면: 해요체 + 구어 어미
- 편한 동료처럼: 해요체 + 가끔 반말

## 수진의 성격:
- 따뜻하고 프로페셔널
- 후배를 잘 챙기는 선배 스타일
- 실수해도 자연스럽게 고쳐주는 방식

## Multi-language input handling:
- If user speaks Chinese: Understand, reply in Korean + English translation
- If user speaks English: Understand, reply in Korean + English translation
- If user speaks Korean: Reply in Korean + English translation to help them learn
- If user mixes languages: Reply naturally in Korean + English translation

## Gentle correction style:
If user makes a grammar/expression mistake, don't point it out directly.
Instead, naturally rephrase using the correct form, and note the correction in English:
User: "저는 어제 회사에 갔습니다" (too formal for daily chat)
수진: "아~ 어제 회사 가셨구나! 저도 어제 야근했거든요... (English: Oh you went to work yesterday! I also worked overtime... Note: 가셨구나 is more natural than 갔습니다 in casual talk)"
""".strip()


class AgentService:
    """通过 AzureOpenAI 直接调用 Responses API。

    使用 cognitiveservices.azure.com scope 认证 (兼容 Managed Identity)。

    支持两种模式:
    1. agent_reference — Portal 中有预配置 Agent (带 MCP 工具)
    2. instructions — 直接在代码中提供指令 (立即可用)

    通过 previous_response_id 维护对话上下文。
    """

    def __init__(self):
        self._client: AzureOpenAI | None = None
        # thread_id → last_response_id 映射, 用于对话上下文
        self._last_response: dict[str, str] = {}

    def _ensure_client(self):
        if self._client is None:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            # 从 AZURE_AI_ENDPOINT 提取 azure_endpoint
            # 支持两种格式:
            #   https://xxx.services.ai.azure.com
            #   https://xxx.services.ai.azure.com/api/projects/proj-default
            endpoint = settings.AZURE_AI_ENDPOINT.rstrip("/")
            # 取根域名部分作为 azure_endpoint
            if "/api/" in endpoint:
                endpoint = endpoint.split("/api/")[0]
            self._client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2025-03-01-preview",
            )
            logger.info("AzureOpenAI client initialized: %s", endpoint)

    def create_thread(self) -> str:
        """创建新对话线程标识。"""
        self._ensure_client()
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:16]}"
        return thread_id

    def _call_agent(
        self,
        thread_id: str,
        user_message: str,
        agent_name: Optional[str],
        instructions: str,
        max_tokens: int = 800,
    ) -> str:
        """统一的 Agent 调用方法。优先用 agent_reference, 失败则 fallback 到 instructions。"""
        self._ensure_client()

        prev_id = self._last_response.get(thread_id)
        kwargs: dict = {
            "model": settings.MODEL_DEPLOYMENT,
            "input": user_message,
            "max_output_tokens": max_tokens,
        }
        if prev_id:
            kwargs["previous_response_id"] = prev_id

        # 尝试 agent_reference 模式
        if agent_name:
            try:
                kwargs["extra_body"] = {
                    "agent_reference": {
                        "name": agent_name,
                        "type": "agent_reference",
                    }
                }
                resp = self._client.responses.create(**kwargs)
                self._last_response[thread_id] = resp.id
                return resp.output_text
            except Exception as e:
                logger.warning(
                    "agent_reference '%s' failed, falling back to instructions: %s",
                    agent_name, e,
                )
                kwargs.pop("extra_body", None)

        # Fallback: 直接用 instructions
        kwargs["instructions"] = instructions
        resp = self._client.responses.create(**kwargs)
        self._last_response[thread_id] = resp.id
        return resp.output_text

    def chat(self, thread_id: str, user_message: str) -> str:
        """文字对话 — 商务韩语教练。"""
        try:
            return self._call_agent(
                thread_id=thread_id,
                user_message=user_message,
                agent_name=settings.TEXT_AGENT_NAME,
                instructions=TEXT_INSTRUCTIONS,
            )
        except Exception as e:
            logger.error("Chat error: %s", e, exc_info=True)
            return f"[错误] Agent 调用失败: {type(e).__name__}: {e}"

    def chat_stream(self, thread_id: str, user_message: str) -> Generator[str, None, str]:
        """流式文字对话 — 逐步返回文本片段, 最终返回完整文本。"""
        try:
            self._ensure_client()
            prev_id = self._last_response.get(thread_id)
            kwargs: dict = {
                "model": settings.MODEL_DEPLOYMENT,
                "input": user_message,
                "max_output_tokens": 800,
                "stream": True,
            }
            if prev_id:
                kwargs["previous_response_id"] = prev_id

            if settings.TEXT_AGENT_NAME:
                kwargs["extra_body"] = {
                    "agent_reference": {
                        "name": settings.TEXT_AGENT_NAME,
                        "type": "agent_reference",
                    }
                }
            else:
                kwargs["instructions"] = TEXT_INSTRUCTIONS

            full_text = ""
            response_id = None
            stream = self._client.responses.create(**kwargs)
            for event in stream:
                if hasattr(event, 'type'):
                    if event.type == 'response.output_text.delta':
                        full_text += event.delta
                        yield event.delta
                    elif event.type == 'response.completed':
                        response_id = event.response.id
            if response_id:
                self._last_response[thread_id] = response_id
            return full_text
        except Exception as e:
            logger.error("Chat stream error: %s", e, exc_info=True)
            yield f"[错误] {type(e).__name__}: {e}"
            return ""

    def voice_chat(self, thread_id: str, user_message: str) -> str:
        """语音对话 — 수진, 纯韩语短回复。"""
        try:
            return self._call_agent(
                thread_id=thread_id,
                user_message=user_message,
                agent_name=settings.VOICE_AGENT_NAME,
                instructions=VOICE_INSTRUCTIONS,
                max_tokens=200,
            )
        except Exception as e:
            logger.error("Voice chat error: %s", e, exc_info=True)
            return "죄송해요, 다시 한번 말씀해 주세요."

    def cleanup(self):
        """关闭时清理资源。"""
        if self._client:
            self._client.close()


# 全局单例
agent_service = AgentService()
