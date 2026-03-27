"""
scripts/seed_drama_cosmos.py — 将 business_korean.json 中的 drama_dialogues 导入 Cosmos DB drama_content 容器
用法: python -m scripts.seed_drama_cosmos
"""

import asyncio
import json
import uuid
from pathlib import Path

from app.core.cosmos import init_cosmos, close_cosmos, get_container


async def seed():
    await init_cosmos()
    container = get_container("drama_content")

    data_path = Path(__file__).parent.parent / "data" / "business_korean.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dialogues = data.get("drama_dialogues", [])
    if not dialogues:
        print("No drama_dialogues found in business_korean.json")
        return

    print(f"Seeding {len(dialogues)} drama dialogues to Cosmos DB...")

    for i, dialog in enumerate(dialogues):
        drama_name = dialog.get("drama", "unknown")
        # 用 drama 名作为 partition key 值
        drama_id = drama_name.split("(")[0].strip()

        doc = {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"drama-{drama_id}-{i}")),
            "drama_id": drama_id,
            "drama_name": drama_name,
            "genre": dialog.get("genre", ""),
            "scene": dialog.get("scene", ""),
            "context": dialog.get("context", ""),
            "difficulty": dialog.get("difficulty", "intermediate"),
            "dialogues": dialog.get("dialogue", []),
            "key_expressions": dialog.get("key_expressions", []),
            "culture_note": dialog.get("culture_note", ""),
        }

        result = await container.upsert_item(doc)
        print(f"  [{i+1}/{len(dialogues)}] {drama_name} / {doc['scene']} → {result['id'][:8]}...")

    print(f"Done! Seeded {len(dialogues)} documents.")
    await close_cosmos()


if __name__ == "__main__":
    asyncio.run(seed())
