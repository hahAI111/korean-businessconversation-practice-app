"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, chat, pronunciation, progress, vocab, voice_ws
from app.core.config import get_settings
from app.core.cosmos import close_cosmos, init_cosmos, is_mock as cosmos_is_mock
from app.core.database import Base, engine
from app.core.redis import close_redis
from app.models.models import *  # noqa: F401,F403 — ensure models registered
from app.services.agent_service import agent_service

settings = get_settings()


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
    # Cosmos DB（连不上则自动降级为内存 Mock，不阻塞启动）
    await init_cosmos()
    yield
    # Shutdown
    agent_service.cleanup()
    await close_cosmos()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description="商务韩语口语教练 API —— 支持文字/语音对话、发音评分、学习进度追踪",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS（移动端需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
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


# ── 根路径重定向到前端 ──
@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


# ── 语料 MCP Server（Korean Business Teacher Tools, 供 Foundry Agent 远程访问）──
try:
    from mcp_server.server import mcp as _mcp_server
    app.mount("/mcp", _mcp_server.http_app())
    import logging as _log
    _log.getLogger(__name__).info("MCP server mounted at /mcp")
except Exception as _e:
    import logging as _log
    _log.getLogger(__name__).warning("Failed to mount MCP server: %s", _e)

# ── PWA: Service Worker 和 manifest 必须在根路径 ──
_static_dir = Path(__file__).resolve().parent.parent / "static"

@app.get("/service-worker.js")
async def service_worker():
    return FileResponse(_static_dir / "service-worker.js", media_type="application/javascript")

@app.get("/manifest.json")
async def manifest():
    return FileResponse(_static_dir / "manifest.json", media_type="application/manifest+json")

# ── 静态文件（Web前端）──
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
