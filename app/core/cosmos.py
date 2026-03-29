"""
Cosmos DB client — document store (conversations / K-drama content / learning events)
Auto-fallback to in-memory Mock when COSMOS_ENDPOINT is empty (no Emulator needed for local dev)
"""

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Container definitions ──
CONTAINERS = {
    "conversations": "/user_id",
    "drama_content": "/drama_id",
    "learning_events": "/user_id",
}

# ── Module-level client (initialized in lifespan) ──
_cosmos_client: Any = None
_database: Any = None
_containers: dict[str, Any] = {}
_use_mock: bool = False


# =============================================
# In-memory Mock (local dev / COSMOS_ENDPOINT not configured)
# =============================================
class _MockContainer:
    """Dict-based Cosmos container mock for local dev basic CRUD."""

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
        # Simple filter: local mock returns all data (no SQL parsing)
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
    """Mock async pager."""

    def __init__(self, items: list[dict]):
        self._items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


# =============================================
# Init / Close
# =============================================
async def init_cosmos() -> None:
    """Called on app startup to initialize Cosmos client and containers."""
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

        # Verify connection works (prevent 403 only appearing during operations)
        await _database.read()

        logger.info("Cosmos DB: connected to %s / %s", settings.COSMOS_ENDPOINT, settings.COSMOS_DATABASE)
    except Exception as e:
        # Fallback to Mock when connection fails, does not block startup
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
    """Cleanup Cosmos client on app shutdown."""
    global _cosmos_client
    if _cosmos_client is not None:
        await _cosmos_client.close()
        _cosmos_client = None
        logger.info("Cosmos DB: client closed")


def get_container(name: str) -> Any:
    """Get specified container client."""
    if name not in _containers:
        raise ValueError(f"Unknown Cosmos container: {name}")
    return _containers[name]


def is_mock() -> bool:
    """Whether currently using in-memory Mock."""
    return _use_mock
