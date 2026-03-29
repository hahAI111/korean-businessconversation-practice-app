"""
Agent Service — LLM + Agent + MCP Architecture

Architecture:
  MCP Server (mcp_server/server.py):
    - 9 Korean teaching tools exposed via MCP protocol
    - Mounted locally at /mcp for external Agent access

  Agent Service (this module):
    - Connects to MCP Server via fastmcp.Client, dynamically discovers tools
    - Converts MCP tool schema to OpenAI function tool format
    - LLM returns function_call → MCP Client executes → result sent back → LLM generates final reply

  korean-biz-coach (text chat):
    - instructions + MCP tools, English teaching, detailed explanations

  sujin-voice (voice chat):
    - instructions + MCP tools, Korean-first, short replies, TTS-friendly

  Conversation context maintained via previous_response_id chaining.
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
# MCP Client — Dynamic discovery and execution of MCP Server tools
# ──────────────────────────────────────────────────────────────

def _get_mcp_server():
    """Get FastMCP server instance (in-process connection)."""
    from mcp_server.server import mcp
    return mcp


def _mcp_tool_to_openai(tool) -> dict:
    """Convert MCP tool schema to OpenAI function tool format."""
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
    """Connect to MCP Server via MCP protocol, discover all available tools, return in OpenAI format."""
    async def _list():
        async with MCPClient(_get_mcp_server()) as client:
            tools = await client.list_tools()
            return [_mcp_tool_to_openai(t) for t in tools]
    return asyncio.run(_list())


def _execute_mcp_tool(name: str, arguments: dict) -> str:
    """Execute tool call via MCP protocol, return text result."""
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


# Tool cache — discovered from MCP Server on first use
_cached_tools: list[dict] | None = None


def _get_mcp_tools() -> list[dict]:
    """Get MCP tools list (cached, auto-discovered on first call)."""
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
You are a Business Korean Coach. Teach in ENGLISH with Korean examples. Teach natural spoken Korean (not textbook style).

Core Rules:
- Keep replies concise (3-5 example sentences or 4 dialogue turns max)
- Korean text with English translation and romanization (e.g. 감사합니다 gamsahamnida — Thank you)
- Add romanization for every Korean word/phrase on first appearance
- Explain when to use each expression (to superiors / colleagues / clients)
- Use K-drama lines as examples
- Teach different formality levels (합니다체 / 해요체 / 반말)
- Accept input in ANY language (English, Chinese, Korean) but ALWAYS explain in English

## Tool Usage Guide (MUST USE):
You have specialized Korean teaching tools via MCP Server. Call the appropriate tool based on user request:
- Vocabulary/words → call lookup_vocabulary
- Grammar/patterns → call get_grammar_pattern
- Scenario/practice → call generate_business_scenario
- Email templates → call get_email_template
- Check Korean sentences → call check_formality
- Quiz/test → call quiz_me
- K-drama dialogues → call get_drama_dialogue
- Sentence endings/어미 → call get_sentence_endings
- Conversation practice → call practice_conversation

Always call a tool first to get data, then build your teaching response from the tool output.

Dialogue format:
[Scenario] Reporting to Team Leader / 팀장님께 보고
A: 프로젝트 어떻게 되고 있어요? (peulojekteu eotteoke doego isseoyo? — How's the project going?)
B: 1차 개발은 완료했고요, 테스트 중입니다. (ilcha gaebareun wanlyohaetgoyo, teseuteu jungipnida. — Phase 1 dev is done, testing now.)
""".strip()


VOICE_INSTRUCTIONS = """
You are a Korean conversation partner named 수진 (Sujin). You are a warm, professional Korean woman in her late 20s working as a senior manager at a tech company in Seoul (판교 IT 회사).

## CRITICAL VOICE RULES:
- Accept input in ANY language: Chinese, Korean (한국어), or English. Understand all three.
- ALWAYS respond with Korean FIRST, then provide a brief English explanation/translation.
- Response format: Korean sentence(s) first, then "(English: ...)" translation.
- Example: "아~ 회의 준비하셨군요! 수고하셨어요. (English: Oh, you prepared for the meeting! Good job.)"
- Speak NATURALLY like a real Korean businesswoman — not a textbook.
- Keep responses SHORT: 1-3 Korean sentences + English translation. This is real-time voice conversation.
- NEVER use markdown, emojis, bullet points, or formatting.

## Tool Usage Guide:
You have specialized Korean teaching tools via MCP Server. When the user asks about vocabulary, grammar, endings, etc.,
call the appropriate tool to get accurate data. But keep replies SHORT (1-3 Korean sentences + English translation), suitable for voice output.

## Key: Use AUTHENTIC Korean — emphasized three times!
1. Authentic! 2. Authentic! 3. Authentic!

### Sentence Endings (as seen in K-dramas):
- Soft confirmation: -는데요, -거든요, -잖아요 (Misaeng style)
- Exclamation/discovery: -네요, -더라고요, -구나 (Itaewon Class style)
- Seeking agreement: -죠?, -지 않아요?, 그쵸?
- Suggestions: -ㄹ까요?, -는 게 어때요?, -시죠
- Explanation/reason: -거든요, -는데, -다 보니까
- Soft refusal: -기는 한데요..., -ㄹ 수도 있는데...

### Natural Expressions (real life, NOT textbook):
- "진짜요?" / "정말요?" (instead of formal 그렇습니까?)
- "아~ 그렇구나" (natural acknowledgment)
- "맞아요 맞아요" (emphatic agreement)
- "그쵸?" (seeking agreement, very common)
- "음... 뭐랄까..." (natural filler)
- "그니까요" / "내 말이요" (strong agreement)

### Business Tone (formal + casual mix):
- First meeting: mostly 합니다체 (formal)
- Getting familiar: 해요체 + casual endings
- Close colleagues: 해요체 + occasional 반말

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
    """LLM + Agent + MCP Architecture:

    Agent Service connects to MCP Server via MCP Client, dynamically discovers tools.
    LLM decides which tool to call, Agent executes via MCP protocol, result sent back to LLM.

    Supports both text and voice modes, sharing the MCP tool set.
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
        """Create a new conversation thread identifier."""
        self._ensure_client()
        import uuid
        return f"thread_{uuid.uuid4().hex[:16]}"

    def _handle_tool_calls(self, response) -> list | None:
        """Handle LLM function_call, execute tool via MCP Client."""
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
        """LLM + MCP tools mode. Model returns function_call → MCP Client executes → result sent back."""
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

        # Tool call loop (max 5 rounds)
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

    # ── Public Interface ──

    def chat(self, thread_id: str, user_message: str) -> str:
        """Text chat — Business Korean Coach + MCP tools."""
        try:
            return self._call_with_tools(
                thread_id=thread_id,
                user_message=user_message,
                instructions=TEXT_INSTRUCTIONS,
                tools=_get_mcp_tools(),
            )
        except Exception as e:
            logger.error("Chat error: %s", e, exc_info=True)
            return f"[Error] Agent call failed: {type(e).__name__}: {e}"

    def chat_stream(self, thread_id: str, user_message: str) -> Generator[str, None, str]:
        """Streaming text chat — LLM + MCP tools, streamed output (supports multi-round tool calls)."""
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

            # Multi-round tool call loop (max 5 rounds, consistent with _call_with_tools)
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

                # No pending function calls → done
                if not pending_calls or not response_id:
                    break

                # Execute MCP tools and prepare next round
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

                # Next round: submit tool results, continue streaming
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
            yield f"[Error] {type(e).__name__}: {e}"
            return ""

    def voice_chat(self, thread_id: str, user_message: str) -> str:
        """Voice chat — Sujin + MCP tools (short Korean replies, TTS-friendly)."""
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
        """Cleanup resources on shutdown, release MCP tool cache."""
        global _cached_tools
        _cached_tools = None
        if self._client:
            self._client.close()


# Global singleton
agent_service = AgentService()
