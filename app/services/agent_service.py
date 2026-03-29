"""
Agent 服务 —— LLM + Agent + MCP 架构

架构:
  MCP Server (mcp_server/server.py):
    - 9 个韩语教学工具, 通过 MCP 协议暴露
    - 本地 HTTP 挂载在 /mcp, 供外部 Agent 访问

  Agent Service (本模块):
    - 通过 fastmcp.Client 连接 MCP Server, 动态发现工具
    - 将 MCP 工具 schema 转换为 OpenAI function tool 格式
    - LLM 返回 function_call → MCP Client 执行 → 结果回传 → LLM 生成最终回复

  korean-biz-coach (文字对话):
    - instructions + MCP tools, 中文教学, 详细讲解

  sujin-voice (语音对话):
    - instructions + MCP tools, 韩语为主, 简短回复, TTS 友好

  对话上下文通过 previous_response_id 链式维护。
"""

import asyncio
import json
import logging
from typing import Generator

from openai import OpenAI
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from fastmcp import Client as MCPClient

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ──────────────────────────────────────────────────────────────
# MCP Client — 动态发现和执行 MCP Server 工具
# ──────────────────────────────────────────────────────────────

def _get_mcp_server():
    """获取 FastMCP server 实例（in-process 连接）。"""
    from mcp_server.server import mcp
    return mcp


def _mcp_tool_to_openai(tool) -> dict:
    """将 MCP tool schema 转换为 OpenAI function tool 格式。"""
    input_schema = tool.inputSchema if hasattr(tool, "inputSchema") else {}
    schema = dict(input_schema) if input_schema else {"type": "object", "properties": {}}
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        if isinstance(prop, dict):
            prop.pop("title", None)
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description or "",
        "parameters": schema,
    }


def _discover_tools() -> list[dict]:
    """通过 MCP 协议连接 Server, 发现所有可用工具, 返回 OpenAI 格式。"""
    async def _list():
        async with MCPClient(_get_mcp_server()) as client:
            tools = await client.list_tools()
            return [_mcp_tool_to_openai(t) for t in tools]
    return asyncio.run(_list())


def _execute_mcp_tool(name: str, arguments: dict) -> str:
    """通过 MCP 协议执行工具调用, 返回文本结果。"""
    async def _call():
        async with MCPClient(_get_mcp_server()) as client:
            result = await client.call_tool(name, arguments)
            if isinstance(result, str):
                return result
            if isinstance(result, list):
                parts = []
                for item in result:
                    if isinstance(item, str):
                        parts.append(item)
                    elif hasattr(item, "text"):
                        parts.append(item.text)
                    else:
                        parts.append(str(item))
                return "\n".join(parts) if parts else json.dumps({"result": "empty"})
            if hasattr(result, "content"):
                parts = []
                for item in result.content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif hasattr(item, "text"):
                        parts.append(item.text)
                    else:
                        parts.append(str(item))
                return "\n".join(parts) if parts else json.dumps({"result": "empty"})
            return str(result)
    try:
        return asyncio.run(_call())
    except Exception as e:
        logger.error("MCP tool %s execution error: %s", name, e, exc_info=True)
        return json.dumps({"error": str(e)})


# 工具缓存 — 首次使用时从 MCP Server 动态发现
_cached_tools: list[dict] | None = None


def _get_mcp_tools() -> list[dict]:
    """获取 MCP 工具列表（带缓存, 首次调用时自动发现）。"""
    global _cached_tools
    if _cached_tools is None:
        _cached_tools = _discover_tools()
        logger.info("🔌 MCP tools discovered: %d tools", len(_cached_tools))
        for t in _cached_tools:
            logger.info("  🔧 %s: %s", t["name"], t["description"][:60])
    return _cached_tools


# ──────────────────────────────────────────────────────────────
# Agent Instructions
# ──────────────────────────────────────────────────────────────

TEXT_INSTRUCTIONS = """
你是商务韩语教练。用中文教学，韩语附中文翻译。教自然口语（非教科书式）。

核心规则：
- 回复简洁（3-5个例句或4轮对话即可）
- 韩语附中文翻译，首次出现的词加罗马音
- 说明适用场合（对上级/同事/客户）
- 用韩剧台词当例句
- 教不同语气等级（합니다体/해요体/반말）

## 工具使用指南 (MUST USE):
你有专业韩语教学工具（通过 MCP Server 提供）。请根据用户请求调用对应工具：
- 用户问词汇/单词 → 调用 lookup_vocabulary
- 用户问语法/句式 → 调用 get_grammar_pattern
- 用户想模拟场景/练习 → 调用 generate_business_scenario
- 用户要邮件模板 → 调用 get_email_template
- 用户贴韩语句子检查 → 调用 check_formality
- 用户想测验/考试 → 调用 quiz_me
- 用户想看韩剧台词 → 调用 get_drama_dialogue
- 用户问语尾/어미 → 调用 get_sentence_endings
- 用户想对话练习 → 调用 practice_conversation

先调用工具获取数据，再结合工具返回的内容生成教学回复。

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

## 工具使用指南:
你有专业韩语教学工具（通过 MCP Server 提供）。当用户问到词汇、语法、语尾等需要查询的内容时，
调用相应工具获取准确数据。但回复必须保持简短（1-3句韩语 + 英语翻译），适合语音输出。

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
    """LLM + Agent + MCP 架构:

    Agent Service 通过 MCP Client 连接 MCP Server, 动态发现工具。
    LLM 决定调用哪个工具, Agent 通过 MCP 协议执行, 结果回传给 LLM。

    支持文字和语音两种模式, 共享 MCP 工具集。
    """

    def __init__(self):
        self._client: OpenAI | None = None
        self._last_response: dict[str, str] = {}

    def _ensure_client(self):
        if self._client is None:
            credential = DefaultAzureCredential()
            project_client = AIProjectClient(
                endpoint=settings.AZURE_AI_ENDPOINT,
                credential=credential,
            )
            self._client = project_client.get_openai_client()
            logger.info("AIProjectClient OpenAI initialized: %s", settings.AZURE_AI_ENDPOINT)

    def create_thread(self) -> str:
        """创建新对话线程标识。"""
        self._ensure_client()
        import uuid
        return f"thread_{uuid.uuid4().hex[:16]}"

    def _handle_tool_calls(self, response) -> list | None:
        """处理 LLM 的 function_call, 通过 MCP Client 执行工具。"""
        tool_calls = []
        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(item)

        if not tool_calls:
            return None

        results = []
        for call in tool_calls:
            args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            logger.info("🔧 MCP tool call: %s(%s)", call.name, json.dumps(args, ensure_ascii=False)[:200])
            output = _execute_mcp_tool(call.name, args)
            results.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": output,
            })
            logger.info("🔧 MCP tool result: %s → %s", call.name, output[:200])

        return results

    def _call_with_tools(
        self, thread_id: str, user_message: str,
        instructions: str, tools: list,
    ) -> str:
        """LLM + MCP tools 模式。模型返回 function_call → MCP Client 执行 → 结果回传。"""
        self._ensure_client()
        prev_id = self._last_response.get(thread_id)

        kwargs: dict = {
            "model": settings.MODEL_DEPLOYMENT,
            "input": user_message,
            "instructions": instructions,
            "tools": tools,
        }
        if prev_id:
            kwargs["previous_response_id"] = prev_id

        resp = self._client.responses.create(**kwargs)

        # 工具调用循环 (最多 5 轮)
        for _ in range(5):
            tool_results = self._handle_tool_calls(resp)
            if not tool_results:
                break
            resp = self._client.responses.create(
                model=settings.MODEL_DEPLOYMENT,
                input=tool_results,
                previous_response_id=resp.id,
                instructions=instructions,
                tools=tools,
            )

        self._last_response[thread_id] = resp.id
        text = resp.output_text
        if not text:
            logger.warning("Empty output_text, output types: %s", [i.type for i in resp.output])
        return text

    # ── 公开接口 ──

    def chat(self, thread_id: str, user_message: str) -> str:
        """文字对话 — 商务韩语教练 + MCP 工具。"""
        try:
            return self._call_with_tools(
                thread_id=thread_id,
                user_message=user_message,
                instructions=TEXT_INSTRUCTIONS,
                tools=_get_mcp_tools(),
            )
        except Exception as e:
            logger.error("Chat error: %s", e, exc_info=True)
            return f"[错误] Agent 调用失败: {type(e).__name__}: {e}"

    def chat_stream(self, thread_id: str, user_message: str) -> Generator[str, None, str]:
        """流式文字对话 — LLM + MCP tools, 流式输出 (支持多轮工具调用)。"""
        try:
            self._ensure_client()
            prev_id = self._last_response.get(thread_id)
            mcp_tools = _get_mcp_tools()
            kwargs: dict = {
                "model": settings.MODEL_DEPLOYMENT,
                "input": user_message,
                "instructions": TEXT_INSTRUCTIONS,
                "tools": mcp_tools,
                "stream": True,
            }
            if prev_id:
                kwargs["previous_response_id"] = prev_id

            full_text = ""
            response_id = None

            # 多轮工具调用循环 (最多 5 轮, 与 _call_with_tools 一致)
            for round_num in range(5):
                stream = self._client.responses.create(**kwargs)
                pending_calls = {}

                for event in stream:
                    if not hasattr(event, 'type'):
                        continue

                    if event.type == 'response.output_text.delta':
                        full_text += event.delta
                        yield event.delta

                    elif event.type == 'response.output_item.done':
                        item = event.item
                        if item.type == 'function_call':
                            pending_calls[item.call_id] = {
                                "name": item.name,
                                "arguments": item.arguments,
                            }

                    elif event.type == 'response.completed':
                        response_id = event.response.id

                # 无 pending function calls → 完成
                if not pending_calls or not response_id:
                    break

                # 执行 MCP 工具并准备下一轮
                tool_results = []
                for call_id, call_info in pending_calls.items():
                    args = json.loads(call_info["arguments"]) if isinstance(call_info["arguments"], str) else call_info["arguments"]
                    logger.info("🔧 Stream MCP tool (round %d): %s(%s)", round_num + 1, call_info["name"], json.dumps(args, ensure_ascii=False)[:200])
                    output = _execute_mcp_tool(call_info["name"], args)
                    tool_results.append({
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": output,
                    })
                    logger.info("🔧 Stream MCP result: %s → %s", call_info["name"], output[:200])

                # 下一轮: 提交工具结果, 继续流式
                kwargs = {
                    "model": settings.MODEL_DEPLOYMENT,
                    "input": tool_results,
                    "previous_response_id": response_id,
                    "instructions": TEXT_INSTRUCTIONS,
                    "tools": mcp_tools,
                    "stream": True,
                }

            if response_id:
                self._last_response[thread_id] = response_id
            return full_text
        except Exception as e:
            logger.error("Chat stream error: %s", e, exc_info=True)
            yield f"[错误] {type(e).__name__}: {e}"
            return ""

    def voice_chat(self, thread_id: str, user_message: str) -> str:
        """语音对话 — 수진 + MCP 工具（简短韩语回复, TTS 友好）。"""
        try:
            return self._call_with_tools(
                thread_id=thread_id,
                user_message=user_message,
                instructions=VOICE_INSTRUCTIONS,
                tools=_get_mcp_tools(),
            )
        except Exception as e:
            logger.error("Voice chat error: %s", e, exc_info=True)
            return "죄송해요, 다시 한번 말씀해 주세요."

    def cleanup(self):
        """关闭时清理资源, 释放 MCP 工具缓存。"""
        global _cached_tools
        _cached_tools = None
        if self._client:
            self._client.close()


# 全局单例
agent_service = AgentService()
