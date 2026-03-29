"""
Cosmos DB service layer — conversations / drama_content / learning_events CRUD
All operations are transparent to existing PostgreSQL logic, no impact on existing features.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.cosmos import get_container


# =============================================
# Conversations container
# =============================================

async def create_conversation(user_id: int, thread_id: str, title: str = "New Chat") -> dict:
    """Create new conversation document."""
    container = get_container("conversations")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "thread_id": thread_id,
        "title": title,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await container.upsert_item(doc)


async def append_message(doc_id: str, user_id: int, role: str, content: str) -> dict:
    """Append messages to conversation document."""
    container = get_container("conversations")
    doc = await container.read_item(item=doc_id, partition_key=user_id)
    doc["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    return await container.upsert_item(doc)


async def get_conversation(doc_id: str, user_id: int) -> dict | None:
    """Read a single conversation document."""
    container = get_container("conversations")
    try:
        return await container.read_item(item=doc_id, partition_key=user_id)
    except Exception:
        return None


async def list_conversations(user_id: int, limit: int = 20) -> list[dict]:
    """List user's recent conversations."""
    container = get_container("conversations")
    query = "SELECT * FROM c WHERE c.user_id = @uid ORDER BY c.updated_at DESC OFFSET 0 LIMIT @lim"
    params: list[dict[str, Any]] = [
        {"name": "@uid", "value": user_id},
        {"name": "@lim", "value": limit},
    ]
    results = []
    async for item in container.query_items(query=query, parameters=params, partition_key=user_id):
        results.append(item)
    return results


# =============================================
# Drama Content container
# =============================================

async def upsert_drama(drama_doc: dict) -> dict:
    """Insert/update K-drama content document."""
    container = get_container("drama_content")
    drama_doc.setdefault("id", str(uuid.uuid4()))
    return await container.upsert_item(drama_doc)


async def get_drama(doc_id: str, drama_id: str) -> dict | None:
    """Get a single K-drama document."""
    container = get_container("drama_content")
    try:
        return await container.read_item(item=doc_id, partition_key=drama_id)
    except Exception:
        return None


async def list_dramas(drama_id: str | None = None) -> list[dict]:
    """List K-drama content (filterable by drama_id)."""
    container = get_container("drama_content")
    if drama_id:
        query = "SELECT * FROM c WHERE c.drama_id = @did"
        params: list[dict[str, Any]] = [{"name": "@did", "value": drama_id}]
    else:
        query = "SELECT * FROM c"
        params = []
    results = []
    async for item in container.query_items(query=query, parameters=params,
                                            partition_key=drama_id):
        results.append(item)
    return results


# =============================================
# Learning Events container
# =============================================

async def log_event(user_id: int, event_type: str, payload: dict | None = None) -> dict:
    """Append learning event (insert only, no update)."""
    container = get_container("learning_events")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_type": event_type,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ttl": 7_776_000,  # 90 days auto-expire
    }
    return await container.upsert_item(doc)


async def get_user_events(user_id: int, event_type: str | None = None,
                          limit: int = 50) -> list[dict]:
    """Query user learning events."""
    container = get_container("learning_events")
    if event_type:
        query = (
            "SELECT * FROM c WHERE c.user_id = @uid AND c.event_type = @et "
            "ORDER BY c.timestamp DESC OFFSET 0 LIMIT @lim"
        )
        params: list[dict[str, Any]] = [
            {"name": "@uid", "value": user_id},
            {"name": "@et", "value": event_type},
            {"name": "@lim", "value": limit},
        ]
    else:
        query = (
            "SELECT * FROM c WHERE c.user_id = @uid "
            "ORDER BY c.timestamp DESC OFFSET 0 LIMIT @lim"
        )
        params = [
            {"name": "@uid", "value": user_id},
            {"name": "@lim", "value": limit},
        ]
    results = []
    async for item in container.query_items(query=query, parameters=params, partition_key=user_id):
        results.append(item)
    return results
