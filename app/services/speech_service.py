"""
Azure Speech Service -- STT / TTS via REST API
Identity-based auth (DefaultAzureCredential), no native SDK needed.
"""

import asyncio
import base64
import logging
import subprocess
import tempfile

import httpx
from azure.identity import DefaultAzureCredential

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_credential = DefaultAzureCredential()

# Reusable HTTP client with connection pooling (avoids creating new connections per request)
_http_pool = httpx.Client(timeout=30.0, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))
_tts_pool = httpx.Client(timeout=60.0, limits=httpx.Limits(max_connections=10, max_keepalive_connections=5))


def _get_bearer_token() -> str:
    """Get Azure AD bearer token for Speech REST API."""
    token = _credential.get_token("https://cognitiveservices.azure.com/.default")
    return token.token


def _resample_wav_python(audio_bytes: bytes, target_sr: int = 16000) -> bytes:
    """Pure Python WAV resampling (no ffmpeg needed). Handles sample rate and channel conversion."""
    import struct
    import wave
    import io

    try:
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            src_sr = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        # Convert to array of int16 samples
        if sampwidth == 2:
            samples = struct.unpack(f'<{len(raw)//2}h', raw)
        elif sampwidth == 1:
            samples = tuple((b - 128) * 256 for b in raw)
        else:
            print(f"[RESAMPLE] Unsupported sample width: {sampwidth}", flush=True)
            return audio_bytes

        # Mix to mono if stereo
        if channels == 2:
            mono = []
            for i in range(0, len(samples), 2):
                mono.append((samples[i] + samples[i + 1]) // 2)
            samples = mono
        elif channels > 2:
            mono = []
            for i in range(0, len(samples), channels):
                mono.append(sum(samples[i:i + channels]) // channels)
            samples = mono

        # Resample using linear interpolation
        if src_sr != target_sr:
            ratio = target_sr / src_sr
            new_len = int(len(samples) * ratio)
            resampled = []
            for i in range(new_len):
                src_pos = i / ratio
                idx = int(src_pos)
                frac = src_pos - idx
                if idx + 1 < len(samples):
                    val = samples[idx] * (1 - frac) + samples[idx + 1] * frac
                else:
                    val = samples[min(idx, len(samples) - 1)]
                resampled.append(int(max(-32768, min(32767, val))))
            samples = resampled

        # Build WAV output
        data = struct.pack(f'<{len(samples)}h', *samples)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(target_sr)
            wf.writeframes(data)
        result = buf.getvalue()
        print(f"[RESAMPLE] Python resample: {src_sr}Hz {channels}ch -> {target_sr}Hz 1ch, {len(result)} bytes", flush=True)
        return result
    except Exception as e:
        print(f"[RESAMPLE] Python resample failed: {e}", flush=True)
        return audio_bytes


def _convert_to_wav(audio_bytes: bytes) -> bytes:
    """Convert audio to 16kHz mono 16-bit WAV via ffmpeg. Returns WAV bytes."""
    import struct

    is_wav = audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE'
    suffix = ".wav" if is_wav else ".webm"

    if is_wav and len(audio_bytes) >= 28:
        sr = struct.unpack_from('<I', audio_bytes, 24)[0]
        ch = struct.unpack_from('<H', audio_bytes, 22)[0]
        print(f"[CONVERT] Input WAV: {len(audio_bytes)} bytes, sr={sr}, ch={ch}", flush=True)
        if sr == 16000 and ch == 1:
            return audio_bytes
        print(f"[CONVERT] WAV needs resample: {sr}Hz {ch}ch -> 16000Hz 1ch", flush=True)
    else:
        print(f"[CONVERT] Non-WAV input: first12={audio_bytes[:12]!r}, size={len(audio_bytes)}", flush=True)

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    dst_path = src_path.rsplit(".", 1)[0] + "_out.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", "-f", "wav", dst_path],
            capture_output=True, timeout=30, check=True,
        )
        with open(dst_path, "rb") as f:
            wav_data = f.read()
        print(f"[CONVERT] ffmpeg output: {len(wav_data)} bytes", flush=True)
        return wav_data
    except FileNotFoundError:
        print("[CONVERT] ffmpeg not found, trying Python resample", flush=True)
        if is_wav:
            return _resample_wav_python(audio_bytes)
        print("[CONVERT] Non-WAV without ffmpeg, returning raw", flush=True)
        return audio_bytes
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr[:500].decode(errors='replace') if e.stderr else str(e)
        print(f"[CONVERT] ffmpeg error: {err_msg}", flush=True)
        if is_wav:
            return _resample_wav_python(audio_bytes)
        return audio_bytes


async def speech_to_text(audio_base64: str, language: str = "ko-KR") -> str:
    """STT via Azure Speech REST API."""
    audio_bytes = base64.b64decode(audio_base64)
    print(f"[STT] audio_bytes={len(audio_bytes)}, first4={audio_bytes[:4]!r}, language={language}", flush=True)

    wav_data = await asyncio.to_thread(_convert_to_wav, audio_bytes)
    print(f"[STT] wav_data={len(wav_data)} bytes", flush=True)

    # Debug: check if audio is silent (all zeros after header)
    if wav_data[:4] == b'RIFF' and len(wav_data) > 44:
        import struct
        pcm_data = wav_data[44:]
        samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data[:len(pcm_data) - (len(pcm_data) % 2)])
        max_amp = max(abs(s) for s in samples) if samples else 0
        rms = (sum(s*s for s in samples) / len(samples)) ** 0.5 if samples else 0
        print(f"[STT] Audio analysis: {len(samples)} samples, max_amplitude={max_amp}, rms={rms:.1f}", flush=True)
        if max_amp < 10:
            print("[STT] WARNING: Audio appears to be SILENT (max_amp < 10)!", flush=True)

    def _stt_request(data: bytes, lang_param: str) -> dict:
        token = _get_bearer_token()
        endpoint = settings.AZURE_SPEECH_RESOURCE_ENDPOINT.rstrip("/")
        url = f"{endpoint}/stt/speech/recognition/conversation/cognitiveservices/v1"
        params = {"language": lang_param, "format": "detailed"}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        }
        resp = _http_pool.post(url, params=params, headers=headers, content=data)
        return {"status": resp.status_code, "body": resp.text, "json": resp.json() if resp.status_code == 200 else None}

    def _parse_stt_result(result_data: dict, label: str = "STT") -> tuple[str, float]:
        """Parse STT response, return (text, confidence). Raises on HTTP error."""
        status = result_data["status"]
        if status != 200:
            error_text = result_data["body"][:500]
            print(f"[{label}] REST error {status}: {error_text}", flush=True)
            raise RuntimeError(f"Speech REST API error {status}: {error_text}")
        result = result_data["json"]
        recognition_status = result.get("RecognitionStatus", "")
        if recognition_status == "Success":
            nbest = result.get("NBest", [])
            if nbest:
                return nbest[0].get("Display", ""), nbest[0].get("Confidence", 0.0)
            return result.get("DisplayText", ""), 0.0
        return "", -1.0

    if language == "auto":
        # Try all candidate languages in parallel, pick highest confidence
        candidates = ["ko-KR", "en-US", "zh-CN"]
        tasks = [asyncio.to_thread(_stt_request, wav_data, lang) for lang in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        best_text, best_confidence, best_lang = "", -1.0, ""
        for lang, result_data in zip(candidates, results):
            if isinstance(result_data, Exception):
                print(f"[STT-AUTO] {lang} error: {result_data}", flush=True)
                continue
            text, confidence = _parse_stt_result(result_data, f"STT-AUTO-{lang}")
            if text:
                print(f"[STT-AUTO] {lang}: conf={confidence:.3f}, text='{text[:60]}'", flush=True)
                if confidence > best_confidence:
                    best_confidence, best_text, best_lang = confidence, text, lang
            else:
                print(f"[STT-AUTO] {lang}: no match", flush=True)

        if best_text:
            print(f"[STT-AUTO] Winner: {best_lang} (conf={best_confidence:.3f})", flush=True)
        else:
            print("[STT-AUTO] No language matched", flush=True)
        return best_text
    else:
        # Single language mode
        result_data = await asyncio.to_thread(_stt_request, wav_data, language)
        text, confidence = _parse_stt_result(result_data, "STT")
        if text:
            print(f"[STT] recognized ({language}, conf={confidence:.3f}): {text[:100]}", flush=True)
        else:
            print(f"[STT] No speech detected ({language})", flush=True)
        return text


async def text_to_speech(text: str, voice: str = "ko-KR-SunHiNeural") -> str:
    """TTS via Azure Speech REST API. Returns base64-encoded audio."""
    from xml.sax.saxutils import escape as xml_escape

    def _tts_request():
        token = _get_bearer_token()
        endpoint = settings.AZURE_SPEECH_RESOURCE_ENDPOINT.rstrip("/")
        url = f"{endpoint}/tts/cognitiveservices/v1"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        }
        safe_text = xml_escape(text)
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">'
            f'<voice name="{voice}">{safe_text}</voice>'
            f'</speak>'
        )
        resp = _tts_pool.post(url, headers=headers, content=ssml.encode("utf-8"))
        print(f"[TTS] REST status={resp.status_code}, audio_size={len(resp.content)}", flush=True)
        if resp.status_code != 200:
            print(f"[TTS] REST error: {resp.text[:500]}", flush=True)
            return ""
        return base64.b64encode(resp.content).decode("utf-8")

    return await asyncio.to_thread(_tts_request)


async def text_to_speech_ssml(text: str) -> str:
    """
    고급 TTS — SSML 프로소디 튜닝으로 자연스러운 한국 여성 비즈니스 음성.
    수진(SunHiNeural) 목소리: 따뜻하고 전문적이며 구어체.
    Returns base64-encoded MP3 audio.
    """
    from xml.sax.saxutils import escape as xml_escape

    def _tts_ssml_request():
        token = _get_bearer_token()
        endpoint = settings.AZURE_SPEECH_RESOURCE_ENDPOINT.rstrip("/")
        url = f"{endpoint}/tts/cognitiveservices/v1"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        }
        safe_text = xml_escape(text)
        # SSML with prosody — 자연스럽고 따뜻한 비즈니스 한국어
        ssml = (
            '<speak version="1.0" '
            'xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="https://www.w3.org/2001/mstts" '
            'xml:lang="ko-KR">'
            '<voice name="ko-KR-SunHiNeural">'
            '<mstts:express-as style="friendly" styledegree="1.2">'
            '<prosody rate="0.95" pitch="+2%">'
            f'{safe_text}'
            '</prosody>'
            '</mstts:express-as>'
            '</voice>'
            '</speak>'
        )
        resp = _tts_pool.post(url, headers=headers, content=ssml.encode("utf-8"))
        logger.info("[TTS-SSML] status=%d, audio_size=%d", resp.status_code, len(resp.content))
        if resp.status_code != 200:
            logger.error("[TTS-SSML] error: %s", resp.text[:500])
            return ""
        return base64.b64encode(resp.content).decode("utf-8")

    return await asyncio.to_thread(_tts_ssml_request)


async def assess_pronunciation(
    audio_base64: str,
    reference_text: str,
    language: str = "ko-KR",
) -> dict:
    """Pronunciation assessment via REST API."""
    import json
    audio_bytes = base64.b64decode(audio_base64)
    wav_data = await asyncio.to_thread(_convert_to_wav, audio_bytes)

    def _assess_request():
        token = _get_bearer_token()
        endpoint = settings.AZURE_SPEECH_RESOURCE_ENDPOINT.rstrip("/")
        url = f"{endpoint}/stt/speech/recognition/conversation/cognitiveservices/v1"
        pron_config = {
            "referenceText": reference_text,
            "gradingSystem": "HundredMark",
            "granularity": "Word",
        }
        params = {"language": language, "format": "detailed"}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
            "Pronunciation-Assessment": base64.b64encode(json.dumps(pron_config).encode()).decode(),
        }
        resp = _http_pool.post(url, params=params, headers=headers, content=wav_data)
        if resp.status_code != 200:
            logger.error("Pronunciation API error: %s", resp.text[:500])
            return None
        return resp.json()

    result = await asyncio.to_thread(_assess_request)
    empty = {"accuracy_score": 0, "fluency_score": 0, "completeness_score": 0, "pronunciation_score": 0, "words": []}
    if result is None:
        return empty

    nbest = result.get("NBest", [])
    if not nbest:
        return empty

    best = nbest[0]
    pa = best.get("PronunciationAssessment", {})
    words_raw = best.get("Words", [])
    words = []
    for w in words_raw:
        wa = w.get("PronunciationAssessment", {})
        words.append({
            "word": w.get("Word", ""),
            "accuracy_score": wa.get("AccuracyScore", 0),
            "error_type": wa.get("ErrorType", "None"),
        })

    return {
        "accuracy_score": pa.get("AccuracyScore", 0),
        "fluency_score": pa.get("FluencyScore", 0),
        "completeness_score": pa.get("CompletenessScore", 0),
        "pronunciation_score": pa.get("PronScore", 0),
        "words": words,
    }
