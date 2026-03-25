"""
对话 API —— 文字聊天 + 语音聊天
"""

import asyncio
import json
import logging
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.auth import get_current_user_id
from app.schemas.schemas import ChatRequest, ChatResponse, TtsRequest, VoiceChatRequest, VoiceChatResponse
from app.services.agent_service import agent_service
from app.services.cache_service import cache_service
from app.services import cosmos_service
from app.services.speech_service import speech_to_text, text_to_speech, text_to_speech_ssml

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting for cleaner TTS input."""
    import re
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'>\s+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


async def _save_messages(user_id: int, thread_id: str, user_msg: str, assistant_msg: str):
    """Save user + assistant messages to Cosmos DB conversations container."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        new_msgs = [
            {"role": "user", "content": user_msg, "timestamp": now},
            {"role": "assistant", "content": assistant_msg, "timestamp": now},
        ]
        # 按 thread_id 查找现有对话
        convos = await cosmos_service.list_conversations(user_id, limit=50)
        existing = next((c for c in convos if c.get("thread_id") == thread_id), None)

        from app.core.cosmos import get_container
        if existing:
            msgs = list(existing.get("messages") or [])
            msgs.extend(new_msgs)
            existing["messages"] = msgs
            existing["updated_at"] = now
            await get_container("conversations").upsert_item(existing)
        else:
            title = user_msg[:50] + ("..." if len(user_msg) > 50 else "")
            doc = await cosmos_service.create_conversation(
                user_id=user_id, thread_id=thread_id, title=title,
            )
            doc["messages"] = new_msgs
            doc["updated_at"] = now
            await get_container("conversations").upsert_item(doc)
    except Exception as e:
        logger.warning("Failed to save conversation (non-fatal): %s", e)


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, user_id: int = Depends(get_current_user_id)):
    try:
        # 限流
        if not await cache_service.check_rate_limit(user_id):
            raise HTTPException(status_code=429, detail="Too many requests, please try again later")

        # 获取或创建 thread
        thread_id = body.thread_id
        if not thread_id:
            thread_id = await cache_service.get_thread_id(user_id)
        if not thread_id:
            thread_id = agent_service.create_thread()
            await cache_service.set_thread_id(user_id, thread_id)

        # 调用 Agent (blocking SDK → run in thread to avoid blocking event loop)
        import asyncio
        reply = await asyncio.to_thread(agent_service.chat, thread_id, body.message)

        # TTS 不再同步生成 —— 前端点击播放按钮时通过 /api/chat/tts 按需获取
        # 这样用户可以立刻看到文字回复，不用等 2-4 秒的语音合成
        reply_audio_base64 = None

        # Fire-and-forget: 记录学习时间 + 保存对话 + 学习事件
        async def _background_saves():
            try:
                await cache_service.record_study_session(user_id, 1)
            except Exception:
                pass
            try:
                await _save_messages(user_id, thread_id, body.message, reply)
            except Exception:
                pass
            try:
                await cosmos_service.log_event(user_id, "chat_message", {
                    "thread_id": thread_id,
                    "user_msg_len": len(body.message),
                    "reply_len": len(reply),
                })
            except Exception:
                pass
        asyncio.create_task(_background_saves())

        return ChatResponse(reply=reply, thread_id=thread_id, reply_audio_base64=reply_audio_base64)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat error: {type(e).__name__}: {e}")


@router.post("/stream")
async def chat_stream(body: ChatRequest, user_id: int = Depends(get_current_user_id)):
    """SSE streaming chat — 逐字返回回复。"""
    try:
        if not await cache_service.check_rate_limit(user_id):
            raise HTTPException(status_code=429, detail="Too many requests")

        thread_id = body.thread_id
        if not thread_id:
            thread_id = await cache_service.get_thread_id(user_id)
        if not thread_id:
            thread_id = agent_service.create_thread()
            await cache_service.set_thread_id(user_id, thread_id)

        async def event_generator():
            # Send thread_id first
            yield f"data: {json.dumps({'type': 'meta', 'thread_id': thread_id})}\n\n"

            full_reply = ""
            try:
                gen = agent_service.chat_stream(thread_id, body.message)
                # Run sync generator in a thread, pushing chunks via a queue
                queue: asyncio.Queue = asyncio.Queue()

                def _run_gen():
                    try:
                        for chunk in gen:
                            queue.put_nowait(chunk)
                        queue.put_nowait(None)  # sentinel
                    except Exception as e:
                        queue.put_nowait(e)

                asyncio.get_event_loop().run_in_executor(None, _run_gen)

                while True:
                    item = await queue.get()
                    if item is None:
                        break
                    if isinstance(item, Exception):
                        yield f"data: {json.dumps({'type': 'error', 'text': str(item)})}\n\n"
                        break
                    full_reply += item
                    yield f"data: {json.dumps({'type': 'delta', 'text': item})}\n\n"
            except Exception as e:
                logger.error("Stream error: %s", e, exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Background saves
            try:
                await cache_service.record_study_session(user_id, 1)
            except Exception:
                pass
            try:
                await _save_messages(user_id, thread_id, body.message, full_reply)
            except Exception:
                pass
            try:
                await cosmos_service.log_event(user_id, "chat_message", {
                    "thread_id": thread_id,
                    "user_msg_len": len(body.message),
                    "reply_len": len(full_reply),
                })
            except Exception:
                pass

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat stream error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def tts_endpoint(body: TtsRequest, user_id: int = Depends(get_current_user_id)):
    """On-demand TTS: convert text to speech audio."""
    try:
        clean_text = _strip_markdown(body.text)[:3000]
        if not clean_text:
            raise HTTPException(400, "No text to synthesize")
        audio_b64 = await text_to_speech_ssml(clean_text)
        if not audio_b64:
            raise HTTPException(500, "TTS synthesis returned empty audio")
        return {"audio_base64": audio_b64}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("TTS endpoint error: %s", e)
        raise HTTPException(500, f"TTS error: {type(e).__name__}")


@router.post("/new-thread")
async def new_thread(user_id: int = Depends(get_current_user_id)):
    thread_id = agent_service.create_thread()
    await cache_service.set_thread_id(user_id, thread_id)
    return {"thread_id": thread_id}


@router.get("/history")
async def list_history(user_id: int = Depends(get_current_user_id)):
    """List user's past conversations (newest first, max 30)."""
    convos = await cosmos_service.list_conversations(user_id, limit=30)
    return [
        {
            "id": c.get("id"),
            "thread_id": c.get("thread_id"),
            "title": c.get("title", ""),
            "message_count": len(c.get("messages") or []),
            "updated_at": c.get("updated_at"),
        }
        for c in convos
    ]


@router.get("/history/{thread_id}")
async def load_history(thread_id: str, user_id: int = Depends(get_current_user_id)):
    """Load messages for a specific conversation."""
    convos = await cosmos_service.list_conversations(user_id, limit=50)
    conv = next((c for c in convos if c.get("thread_id") == thread_id), None)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {
        "thread_id": conv.get("thread_id"),
        "title": conv.get("title", ""),
        "messages": conv.get("messages") or [],
    }


@router.delete("/history/{thread_id}")
async def delete_history(thread_id: str, user_id: int = Depends(get_current_user_id)):
    """Delete a conversation."""
    convos = await cosmos_service.list_conversations(user_id, limit=50)
    conv = next((c for c in convos if c.get("thread_id") == thread_id), None)
    if conv:
        from app.core.cosmos import get_container
        await get_container("conversations").delete_item(item=conv["id"], partition_key=user_id)
    return {"ok": True}


@router.post("/voice-test")
async def voice_test(body: VoiceChatRequest, user_id: int = Depends(get_current_user_id)):
    """Diagnostic: decode audio and return header info without calling Speech SDK."""
    import base64, struct
    try:
        raw = base64.b64decode(body.audio_base64)
        info = {"size": len(raw), "first4": raw[:4].hex(), "language": body.language}
        if len(raw) >= 44 and raw[:4] == b'RIFF':
            info["format"] = "WAV"
            info["channels"] = struct.unpack_from('<H', raw, 22)[0]
            info["sample_rate"] = struct.unpack_from('<I', raw, 24)[0]
            info["bits"] = struct.unpack_from('<H', raw, 34)[0]
            info["data_size"] = struct.unpack_from('<I', raw, 40)[0]
        else:
            info["format"] = "non-WAV"
            info["first12_hex"] = raw[:12].hex()
        return info
    except Exception as e:
        return {"error": str(e)}


@router.get("/speech-check")
async def speech_check():
    """Check if Speech REST API dependencies are working."""
    import sys
    info = {"python": sys.version, "platform": sys.platform}
    try:
        import httpx
        info["httpx_version"] = httpx.__version__
        info["httpx_ok"] = True
    except Exception as e:
        info["httpx_ok"] = False
        info["httpx_error"] = str(e)
    try:
        from azure.identity import DefaultAzureCredential
        cred = DefaultAzureCredential()
        token = cred.get_token("https://cognitiveservices.azure.com/.default")
        info["token_length"] = len(token.token)
        info["token_ok"] = True
    except Exception as e:
        info["token_ok"] = False
        info["token_error"] = str(e)
    try:
        import subprocess
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        info["ffmpeg"] = r.stdout.decode()[:100] if r.returncode == 0 else f"exit {r.returncode}"
    except Exception as e:
        info["ffmpeg"] = f"not found: {e}"
    return info


@router.get("/agent-check")
async def agent_check():
    """Diagnose AzureOpenAI + Responses API connectivity on App Service."""
    import os
    info = {}
    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        endpoint = os.environ.get("AZURE_AI_ENDPOINT", "NOT SET")
        info["endpoint"] = endpoint
        # Extract root endpoint
        ep = endpoint.rstrip("/")
        if "/api/" in ep:
            ep = ep.split("/api/")[0]
        info["azure_endpoint"] = ep
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        # Test token provider
        token = token_provider()
        info["token_length"] = len(token) if token else 0
        # Create client
        client = AzureOpenAI(
            azure_endpoint=ep,
            azure_ad_token_provider=token_provider,
            api_version="2025-03-01-preview",
        )
        info["base_url"] = str(client.base_url)
        # Quick test
        r = client.responses.create(model="gpt-5.2", input="say hi", instructions="reply: ok")
        info["response_id"] = r.id
        info["output"] = r.output_text[:100]
        info["status"] = "ok"
        client.close()
    except Exception as e:
        import traceback
        info["status"] = "error"
        info["error"] = str(e)
        info["traceback"] = traceback.format_exc()[-500:]
    return info


@router.get("/redis-check")
async def redis_check():
    """Check Redis connectivity and auth mode."""
    from app.core.redis import get_redis, get_auth_mode
    info = {"auth_mode": get_auth_mode()}
    try:
        r = await get_redis()
        if r is None:
            info["status"] = "memory-fallback"
            info["warning"] = "Redis unavailable — cache is in-memory only (not persistent)"
        else:
            pong = await r.ping()
            info["ping"] = pong
            info["status"] = "ok"
    except Exception as e:
        info["status"] = "error"
        info["error"] = str(e)
    return info


@router.post("/stt-test")
async def stt_test(body: VoiceChatRequest):
    """Test STT only — no Agent, no TTS, no Redis."""
    try:
        print(f"[STT-TEST] audio_len={len(body.audio_base64)}, lang={body.language}", flush=True)
        text = await speech_to_text(body.audio_base64, body.language)
        print(f"[STT-TEST] result: '{text}'", flush=True)
        return {"text": text, "status": "ok"}
    except Exception as e:
        import traceback
        print(f"[STT-TEST] error: {traceback.format_exc()}", flush=True)
        return {"text": "", "status": "error", "error": str(e)}


@router.get("/cosmos-check")
async def cosmos_check():
    """Check Cosmos DB connectivity and container status."""
    from app.core.cosmos import is_mock, get_container
    info = {"mode": "mock" if is_mock() else "connected"}
    try:
        container = get_container("conversations")
        # Quick read to verify connection
        items = []
        async for item in container.query_items(
            query="SELECT VALUE COUNT(1) FROM c", partition_key=None
        ):
            items.append(item)
        info["conversations_count"] = items[0] if items else "unknown"
        info["status"] = "ok"
    except Exception as e:
        info["status"] = "error"
        info["error"] = str(e)
    return info


@router.post("/voice", response_model=VoiceChatResponse)
async def voice_chat(body: VoiceChatRequest, user_id: int = Depends(get_current_user_id)):
    """语音对话：音频输入 → STT → Agent → TTS → 音频输出（不依赖Redis）"""
    print(f"[VOICE] start, audio_len={len(body.audio_base64)}, lang={body.language}", flush=True)

    try:
        # 1) STT
        print("[VOICE] calling STT...", flush=True)
        user_text = await speech_to_text(body.audio_base64, body.language)
        print(f"[VOICE] STT done: '{user_text[:80] if user_text else ''}'", flush=True)
        if not user_text:
            raise HTTPException(status_code=400, detail="Could not recognize speech, please try again")

        # 2) 创建 thread（不依赖Redis）
        thread_id = body.thread_id
        if not thread_id:
            thread_id = agent_service.create_thread()

        # 3) Agent 对话（用voice agent，纯韩语短回复）
        print("[VOICE] calling Agent...", flush=True)
        reply_text = agent_service.voice_chat(thread_id, user_text)
        print(f"[VOICE] Agent done: {len(reply_text)} chars", flush=True)

        # 4) TTS — 자연스러운 SSML 한국 여성 음성
        print("[VOICE] calling TTS-SSML...", flush=True)
        reply_audio = await text_to_speech_ssml(reply_text)
        print(f"[VOICE] TTS done: {len(reply_audio)} chars audio", flush=True)

        return VoiceChatResponse(
            reply_text=reply_text,
            reply_audio_base64=reply_audio,
            user_transcript=user_text,
            thread_id=thread_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[VOICE] EXCEPTION: {traceback.format_exc()}", flush=True)
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {e}")
