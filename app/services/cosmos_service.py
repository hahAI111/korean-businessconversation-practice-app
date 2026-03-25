"""
Cosmos DB 服务层 —— conversations / drama_content / learning_events CRUD
所有操作对现有 PostgreSQL 逻辑透明，不影响已有功能。
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.cosmos import get_container


# =============================================
# Conversations 容器
# =============================================

async def create_conversation(user_id: int, thread_id: str, title: str = "新对话") -> dict:
    """创建新对话文档。"""
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
    """追加消息到对话文档。"""
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
    """读取单个对话文档。"""
    container = get_container("conversations")
    try:
        return await container.read_item(item=doc_id, partition_key=user_id)
    except Exception:
        return None


async def list_conversations(user_id: int, limit: int = 20) -> list[dict]:
    """列出用户最近的对话。"""
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
# Drama Content 容器
# =============================================

async def upsert_drama(drama_doc: dict) -> dict:
    """插入/更新韩剧内容文档。"""
    container = get_container("drama_content")
    drama_doc.setdefault("id", str(uuid.uuid4()))
    return await container.upsert_item(drama_doc)


async def get_drama(doc_id: str, drama_id: str) -> dict | None:
    """获取单个韩剧文档。"""
    container = get_container("drama_content")
    try:
        return await container.read_item(item=doc_id, partition_key=drama_id)
    except Exception:
        return None


async def list_dramas(drama_id: str | None = None) -> list[dict]:
    """列出韩剧内容（可按 drama_id 过滤）。"""
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
# Learning Events 容器
# =============================================

async def log_event(user_id: int, event_type: str, payload: dict | None = None) -> dict:
    """追加学习事件（仅插入，不更新）。"""
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
    """查询用户学习事件。"""
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
