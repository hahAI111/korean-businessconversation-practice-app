# Korean Business Coach — Copilot Project Context

## Project Overview
Korean Business Coach (한국어 비즈니스 코치) is an AI-powered web app for learning authentic Korean business language through text and voice conversations. Built with FastAPI + vanilla JS frontend, deployed on Azure App Service.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Uvicorn
- **AI**: Azure OpenAI (GPT-5.2) via Responses API, Azure Speech (STT/TTS/Pronunciation)
- **Database**: PostgreSQL (Azure), Redis (Azure) with memory fallback
- **Auth**: JWT (user login), Azure Managed Identity (service-to-service)
- **Frontend**: Vanilla HTML/CSS/JS (no framework), static files served by FastAPI

## Key Directories
- `app/api/` — FastAPI route handlers (chat.py, voice_ws.py, auth.py)
- `app/services/` — Business logic (agent_service.py, speech_service.py, cache_service.py)
- `app/core/` — Config, auth, database, Redis
- `app/schemas/` — Pydantic request/response models
- `static/` — Frontend HTML/CSS/JS
- `bmad-docs/` — BMAD planning docs (PRD, Architecture, Stories, Tech Stack)
- `_bmad/` — BMAD v6.2.0 framework

## Conventions
- All Python code uses async where possible
- Use `logger` (not print) for logging
- Never modify auth/infra code unless explicitly asked
- Test locally with `uvicorn app.main:app --reload` before deploying
- Agent instructions are in `app/services/agent_service.py` (TEXT_INSTRUCTIONS, VOICE_INSTRUCTIONS)

## BMAD Methodology
This project uses BMAD (Build Measure Analyze Decide) v6.2.0 for agile development.
See `_bmad/` for framework agents and `bmad-docs/` for project planning artifacts.
