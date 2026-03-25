"""
실시간 음성 대화 WebSocket API
─────────────────────────────
브라우저 ↔ 서버 간 양방향 음성 통신:
  1. 클라이언트가 오디오 바이너리 프레임 전송
  2. 서버가 STT → AI Agent → TTS 파이프라인 실행
  3. 결과를 JSON 메타데이터 + 오디오 바이너리로 반환
"""

import asyncio
import base64
import json
import logging
import struct

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.agent_service import agent_service
from app.services.cache_service import cache_service
from app.services import cosmos_service
from app.services.speech_service import speech_to_text, text_to_speech_ssml

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_valid_wav(data: bytes) -> bool:
    """WAV 파일 유효성 검사"""
    return len(data) >= 44 and data[:4] == b'RIFF' and data[8:12] == b'WAVE'


def _wav_info(data: bytes) -> dict:
    """WAV 헤더 정보 추출"""
    if not _is_valid_wav(data):
        return {"format": "unknown", "size": len(data)}
    return {
        "format": "WAV",
        "size": len(data),
        "channels": struct.unpack_from('<H', data, 22)[0],
        "sample_rate": struct.unpack_from('<I', data, 24)[0],
        "bits": struct.unpack_from('<H', data, 34)[0],
    }


@router.websocket("/ws/voice")
async def voice_websocket(ws: WebSocket):
    """
    실시간 음성 대화 WebSocket

    프로토콜:
    ─────────
    Client → Server:
      - JSON: {"type": "start", "token": "...", "language": "ko-KR"}
      - Binary: WAV audio chunk (recording complete)
      - JSON: {"type": "end_audio"}  — 녹음 종료 신호
      - JSON: {"type": "text", "message": "..."}  — 텍스트 입력

    Server → Client:
      - JSON: {"type": "transcript", "text": "...", "language": "ko-KR"}
      - JSON: {"type": "reply", "text": "...", "thread_id": "..."}
      - Binary: TTS audio (MP3)
      - JSON: {"type": "error", "message": "..."}
      - JSON: {"type": "status", "status": "processing|speaking|ready"}
    """
    await ws.accept()
    logger.info("Voice WebSocket connected")

    user_id = None
    thread_id = None
    audio_buffer = bytearray()

    try:
        # 1. 첫 메시지: 인증 + 설정
        init_data = await asyncio.wait_for(ws.receive_json(), timeout=10)
        if init_data.get("type") != "start":
            await ws.send_json({"type": "error", "message": "Expected 'start' message"})
            await ws.close()
            return

        # JWT 검증
        token = init_data.get("token", "")
        if not token:
            await ws.send_json({"type": "error", "message": "Missing token"})
            await ws.close()
            return

        from app.core.auth import _verify_token
        user_id = _verify_token(token)
        if user_id is None:
            await ws.send_json({"type": "error", "message": "Invalid token"})
            await ws.close()
            return

        language = init_data.get("language", "auto")

        # 스레드 복원 or 생성
        thread_id = await cache_service.get_thread_id(user_id)
        if not thread_id:
            thread_id = agent_service.create_thread()
            await cache_service.set_thread_id(user_id, thread_id)

        await ws.send_json({
            "type": "ready",
            "thread_id": thread_id,
            "message": "Voice session ready. Send audio or text.",
        })

        # 2. 메시지 루프
        while True:
            message = await ws.receive()

            # 바이너리 프레임 — 오디오 데이터
            if "bytes" in message and message["bytes"]:
                audio_buffer.extend(message["bytes"])
                continue

            # 텍스트 프레임 — JSON 명령
            if "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")

                # ── 오디오 종료 → STT + AI + TTS 파이프라인 ──
                if msg_type == "end_audio":
                    if not audio_buffer:
                        await ws.send_json({"type": "error", "message": "No audio data received"})
                        continue

                    await ws.send_json({"type": "status", "status": "processing"})
                    wav_data = bytes(audio_buffer)
                    audio_buffer.clear()

                    info = _wav_info(wav_data)
                    logger.info("Voice input: %s", info)

                    try:
                        # STT
                        audio_b64 = base64.b64encode(wav_data).decode()
                        transcript = await speech_to_text(audio_b64, language=language)

                        if not transcript.strip():
                            await ws.send_json({
                                "type": "transcript",
                                "text": "",
                                "message": "음성이 감지되지 않았습니다. 다시 말씀해 주세요.",
                            })
                            await ws.send_json({"type": "status", "status": "ready"})
                            continue

                        # 사용자 발화 텍스트 전달
                        await ws.send_json({
                            "type": "transcript",
                            "text": transcript,
                        })

                        # AI Agent 응답
                        reply = agent_service.voice_chat(thread_id, transcript)

                        await ws.send_json({
                            "type": "reply",
                            "text": reply,
                            "thread_id": thread_id,
                        })

                        # TTS — 자연스러운 한국 여성 음성
                        await ws.send_json({"type": "status", "status": "speaking"})
                        audio_b64_reply = await text_to_speech_ssml(reply)

                        if audio_b64_reply:
                            audio_bytes = base64.b64decode(audio_b64_reply)
                            await ws.send_bytes(audio_bytes)

                        # 학습 시간 기록
                        await cache_service.record_study_session(user_id, 1)

                        # 학습 이벤트 기록 (fire-and-forget)
                        try:
                            await cosmos_service.log_event(user_id, "voice_message", {
                                "thread_id": thread_id,
                                "transcript_len": len(transcript),
                                "reply_len": len(reply),
                                "language": language,
                            })
                        except Exception:
                            pass

                        await ws.send_json({"type": "status", "status": "ready"})

                    except Exception as e:
                        logger.error("Voice pipeline error: %s", e, exc_info=True)
                        await ws.send_json({
                            "type": "error",
                            "message": f"처리 중 오류: {type(e).__name__}",
                        })
                        await ws.send_json({"type": "status", "status": "ready"})

                # ── 텍스트 입력 → AI + TTS ──
                elif msg_type == "text":
                    user_msg = data.get("message", "").strip()
                    if not user_msg:
                        continue

                    await ws.send_json({"type": "status", "status": "processing"})

                    try:
                        reply = agent_service.voice_chat(thread_id, user_msg)

                        await ws.send_json({
                            "type": "reply",
                            "text": reply,
                            "thread_id": thread_id,
                        })

                        # TTS
                        await ws.send_json({"type": "status", "status": "speaking"})
                        audio_b64_reply = await text_to_speech_ssml(reply)

                        if audio_b64_reply:
                            audio_bytes = base64.b64decode(audio_b64_reply)
                            await ws.send_bytes(audio_bytes)

                        await cache_service.record_study_session(user_id, 1)

                        # 학습 이벤트 기록 (fire-and-forget)
                        try:
                            await cosmos_service.log_event(user_id, "voice_text_input", {
                                "thread_id": thread_id,
                                "user_msg_len": len(user_msg),
                                "reply_len": len(reply),
                            })
                        except Exception:
                            pass

                        await ws.send_json({"type": "status", "status": "ready"})

                    except Exception as e:
                        logger.error("Text-to-voice error: %s", e, exc_info=True)
                        await ws.send_json({
                            "type": "error",
                            "message": f"처리 중 오류: {type(e).__name__}",
                        })
                        await ws.send_json({"type": "status", "status": "ready"})

                # ── 새 스레드 ──
                elif msg_type == "new_thread":
                    thread_id = agent_service.create_thread()
                    await cache_service.set_thread_id(user_id, thread_id)
                    await ws.send_json({
                        "type": "ready",
                        "thread_id": thread_id,
                        "message": "새 대화가 시작되었습니다.",
                    })

                # ── 언어 변경 ──
                elif msg_type == "set_language":
                    language = data.get("language", "ko-KR")
                    await ws.send_json({
                        "type": "status",
                        "status": "ready",
                        "message": f"Language set to {language}",
                    })

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected (user=%s)", user_id)
    except asyncio.TimeoutError:
        logger.warning("Voice WebSocket timeout waiting for init")
        await ws.close(code=1008, reason="Init timeout")
    except Exception as e:
        logger.error("Voice WebSocket error: %s", e, exc_info=True)
        try:
            await ws.send_json({"type": "error", "message": "Internal server error"})
            await ws.close(code=1011)
        except Exception:
            pass
