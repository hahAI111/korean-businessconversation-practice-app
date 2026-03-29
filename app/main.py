"""
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, chat, pronunciation, progress, vocab, voice_ws
from app.core.config import get_settings
from app.core.cosmos import close_cosmos, init_cosmos, is_mock as cosmos_is_mock
from app.core.database import Base, engine
from app.core.redis import close_redis
from app.models.models import *  # noqa: F401,F403 — ensure models registered
from app.services.agent_service import agent_service

settings = get_settings()

# ── MCP Server init (requires lifespan for task group) ──
_mcp_http_app = None
try:
    from mcp_server.server import mcp as _mcp_server
    _mcp_http_app = _mcp_server.http_app(path="/", transport="streamable-http", stateless_http=True)
except Exception as _e:
    import logging as _log
    _log.getLogger(__name__).warning("Failed to create MCP app: %s", _e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-create tables (don't crash if DB is temporarily unavailable)
    import logging
    logger = logging.getLogger(__name__)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready")
    except Exception as e:
        logger.error("Database init failed (will retry on first request): %s", e)
    # Cosmos DB (auto-fallback to in-memory Mock if unavailable)
    await init_cosmos()
    # MCP Server lifespan (init StreamableHTTPSessionManager task group)
    if _mcp_http_app:
        async with _mcp_http_app.router.lifespan_context(_mcp_http_app):
            logger.info("MCP server lifespan initialized")
            yield
    else:
        yield
    # Shutdown
    agent_service.cleanup()
    await close_cosmos()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="Business Korean Speaking Coach API — text/voice chat, pronunciation scoring, learning progress",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (needed for mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production should restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(voice_ws.router)
app.include_router(pronunciation.router)
app.include_router(progress.router)
app.include_router(vocab.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "cosmos_db": "mock" if cosmos_is_mock() else "connected",
    }


# ── Root redirect to frontend ──
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/admin")
async def admin_redirect():
    return RedirectResponse(url="/static/admin_dashboard.html")


# ── MCP Server (Korean Business Teacher Tools, for Foundry Agent remote access) ──
if _mcp_http_app is not None:
    app.mount("/mcp", _mcp_http_app)
    import logging as _log
    _log.getLogger(__name__).info("MCP server mounted at /mcp/ (streamable-http, stateless)")

# ── PWA: Service Worker and manifest must be at root path ──
_static_dir = Path(__file__).resolve().parent.parent / "static"

@app.get("/service-worker.js")
async def service_worker():
    return FileResponse(_static_dir / "service-worker.js", media_type="application/javascript")

@app.get("/manifest.json")
async def manifest():
    return FileResponse(_static_dir / "manifest.json", media_type="application/manifest+json")

# ── Static files (Web frontend) ──
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
