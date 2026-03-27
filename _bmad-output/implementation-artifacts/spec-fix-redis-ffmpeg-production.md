---
title: 'Fix Redis connection + ffmpeg missing on Azure production'
type: 'bugfix'
created: '2026-03-27'
status: 'in-progress'
baseline_commit: 'NO_VCS'
context: [docs/OPERATIONS.md, docs/NETWORK.md]
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Production site has two issues: (1) Redis shows `not-connected` / `memory-fallback`, meaning verification codes, rate limiting, and session cache are non-persistent — breaks multi-worker scenarios. (2) ffmpeg is not installed on Azure App Service, so voice audio format conversion fails for non-WAV input (WebM from browsers).

**Approach:** Install ffmpeg in startup.sh, improve Redis connection diagnostics to surface the real failure reason, fix redis-check endpoint ordering bug, and add a pure-Python WebM-to-WAV fallback using standard library.

## Boundaries & Constraints

**Always:** Don't change auth or infrastructure code. Don't restart/redeploy without user permission. Keep existing fallback behavior (memory-fallback for Redis, Python resample for WAV).

**Ask First:** Any changes to Azure App Service configuration (env vars).

**Never:** Remove existing fallback mechanisms. Change .env files. Touch Cosmos DB or PostgreSQL code.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Redis URL set correctly | `rediss://:key@host:6380/0` | `auth_mode: "access-key"`, ping OK | N/A |
| Redis URL not set | default `redis://localhost:6379/0` | `memory-fallback` + clear diagnostic log showing attempted URL | Log masked URL |
| Redis URL set but connection fails | Invalid key or network | `memory-fallback` + log with error details | Graceful fallback |
| ffmpeg installed | WAV/WebM voice input | Proper 16kHz mono WAV conversion | N/A |
| ffmpeg missing, WAV input | WAV audio bytes | Python resample fallback | Log warning |
| ffmpeg missing, WebM input | WebM audio bytes | Pure Python fallback or clear error | Log + return graceful error |
| redis-check endpoint | GET request | Accurate current auth_mode | N/A |

</frozen-after-approval>

## Code Map

- `startup.sh` -- Azure App Service startup script, needs ffmpeg install
- `app/core/redis.py` -- Redis client init, lazy connection, needs better diagnostics
- `app/api/chat.py` -- redis-check endpoint, auth_mode ordering bug
- `app/services/speech_service.py` -- Audio conversion, ffmpeg call + fallback

## Tasks & Acceptance

**Execution:**
- [x] `startup.sh` -- Add `ffmpeg` to apt-get install line alongside zstd
- [x] `app/core/redis.py` -- Add diagnostic logging: log masked REDIS_URL on connection attempt and detailed error on failure
- [x] `app/api/chat.py` -- Fix redis-check endpoint to show auth_mode AFTER get_redis() call, and add diagnostic info (masked URL, error detail)
- [x] `app/services/speech_service.py` -- Improve non-WAV fallback: when ffmpeg missing and input is WebM, log clear error instead of silently returning raw bytes

**Acceptance Criteria:**
- Given ffmpeg is installed via startup.sh, when voice input is WebM, then audio converts to 16kHz WAV successfully
- Given Redis URL is misconfigured, when redis-check is called, then response includes masked URL and specific error message
- Given Redis is in memory-fallback, when redis-check is called, then auth_mode accurately shows "memory-fallback" (not "not-connected")

## Verification

**Commands:**
- `python -c "from app.main import app; print('OK')"` -- expected: no import errors
- `curl http://127.0.0.1:8000/health` -- expected: 200 OK
- `curl http://127.0.0.1:8000/api/chat/redis-check` -- expected: shows accurate auth_mode + diagnostic info
