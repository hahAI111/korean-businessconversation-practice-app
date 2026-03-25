"""
Cosmos DB 客户端 —— 文档型数据存储 (对话记录 / 韩剧内容 / 学习事件)
COSMOS_ENDPOINT 为空时自动降级为内存 Mock（本地开发无需 Emulator）
"""

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── 容器定义 ──
CONTAINERS = {
    "conversations": "/user_id",
    "drama_content": "/drama_id",
    "learning_events": "/user_id",
}

# ── 模块级客户端（lifespan 中初始化）──
_cosmos_client: Any = None
_database: Any = None
_containers: dict[str, Any] = {}
_use_mock: bool = False


# =============================================
# 内存 Mock（本地开发 / COSMOS_ENDPOINT 未配置）
# =============================================
class _MockContainer:
    """dict 模拟 Cosmos container，满足本地开发基本 CRUD。"""

    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, dict] = {}

    async def upsert_item(self, body: dict) -> dict:
        self._items[body["id"]] = body
        return body

    async def read_item(self, item: str, partition_key: Any) -> dict:
        if item not in self._items:
            raise KeyError(f"Item {item} not found in mock container {self.name}")
        return self._items[item]

    async def delete_item(self, item: str, partition_key: Any) -> None:
        self._items.pop(item, None)

    def query_items(self, query: str, parameters: list | None = None,
                    partition_key: Any = None) -> "_MockPager":
        # 简单过滤：本地 mock 返回全部数据（不解析 SQL）
        results = list(self._items.values())
        if partition_key is not None:
            pk_field = None
            for cname, pk in CONTAINERS.items():
                if cname == self.name:
                    pk_field = pk.lstrip("/")
                    break
            if pk_field:
                results = [r for r in results if r.get(pk_field) == partition_key]
        return _MockPager(results)


class _MockPager:
    """模拟异步分页器。"""

    def __init__(self, items: list[dict]):
        self._items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


# =============================================
# 初始化 / 关闭
# =============================================
async def init_cosmos() -> None:
    """应用启动时调用，初始化 Cosmos 客户端和容器。"""
    global _cosmos_client, _database, _containers, _use_mock

    if not settings.COSMOS_ENDPOINT:
        _use_mock = True
        for name in CONTAINERS:
            _containers[name] = _MockContainer(name)
        logger.info("Cosmos DB: using in-memory mock (COSMOS_ENDPOINT not set)")
        return

    try:
        from azure.cosmos.aio import CosmosClient
        from azure.identity.aio import DefaultAzureCredential

        credential = DefaultAzureCredential()
        _cosmos_client = CosmosClient(settings.COSMOS_ENDPOINT, credential=credential)
        _database = _cosmos_client.get_database_client(settings.COSMOS_DATABASE)

        for name, pk in CONTAINERS.items():
            _containers[name] = _database.get_container_client(name)

        # 验证连接可用（防止 publicNetworkAccess=Disabled 时只在操作时才报 403）
        await _database.read()

        logger.info("Cosmos DB: connected to %s / %s", settings.COSMOS_ENDPOINT, settings.COSMOS_DATABASE)
    except Exception as e:
        # 连不上时降级为 Mock，不影响整体启动
        if _cosmos_client is not None:
            try:
                await _cosmos_client.close()
            except Exception:
                pass
            _cosmos_client = None
            _database = None
        _use_mock = True
        _containers.clear()
        for name in CONTAINERS:
            _containers[name] = _MockContainer(name)
        logger.warning("Cosmos DB init failed, falling back to mock: %s", e)


async def close_cosmos() -> None:
    """应用关闭时清理 Cosmos 客户端。"""
    global _cosmos_client
    if _cosmos_client is not None:
        await _cosmos_client.close()
        _cosmos_client = None
        logger.info("Cosmos DB: client closed")


def get_container(name: str) -> Any:
    """获取指定容器客户端。"""
    if name not in _containers:
        raise ValueError(f"Unknown Cosmos container: {name}")
    return _containers[name]


def is_mock() -> bool:
    """当前是否使用内存 Mock。"""
    return _use_mock
