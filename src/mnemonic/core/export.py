"""Export and import operations for memories."""

import json
from datetime import datetime, timezone
from typing import Any

from mnemonic.db.connection import get_db
from mnemonic.core.memory import (
    _get_memory_tags,
    _get_memory_triggers,
    _row_to_dict,
    _now,
    _get_or_create_tag,
    _set_memory_tags,
    _set_memory_triggers,
)


async def export_memories(
    include_archived: bool = False,
    include_metadata: bool = True,
) -> dict[str, Any]:
    """
    Export all memories to a JSON-serializable format.

    Args:
        include_archived: Include archived/inactive memories
        include_metadata: Include metadata field

    Returns:
        Dictionary with memories array and export metadata
    """
    async with get_db() as db:
        # Build query
        if include_archived:
            query = "SELECT * FROM memories ORDER BY created_at"
            params = []
        else:
            query = "SELECT * FROM memories WHERE status = 'active' ORDER BY created_at"
            params = []

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        memories = []
        for row in rows:
            memory = _row_to_dict(row)
            memory["tags"] = await _get_memory_tags(db, memory["id"])
            memory["triggers"] = await _get_memory_triggers(db, memory["id"])

            # Parse metadata if present
            if memory.get("metadata"):
                memory["metadata"] = json.loads(memory["metadata"])

            # Remove metadata if not requested
            if not include_metadata and "metadata" in memory:
                del memory["metadata"]

            memories.append(memory)

    return {
        "version": "1.0",
        "exported_at": _now(),
        "count": len(memories),
        "memories": memories,
    }


async def import_memories(
    data: dict[str, Any],
    overwrite: bool = False,
    preserve_ids: bool = True,
) -> dict[str, Any]:
    """
    Import memories from an export.

    Args:
        data: Export data (must have 'memories' array)
        overwrite: If True, update existing memories with same ID
        preserve_ids: If True, keep original IDs; if False, generate new ones

    Returns:
        Dictionary with import statistics
    """
    if "memories" not in data:
        raise ValueError("Invalid import data: missing 'memories' array")

    memories = data["memories"]
    stats = {
        "total": len(memories),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
    }

    async with get_db() as db:
        for memory in memories:
            try:
                memory_id = memory.get("id") if preserve_ids else None

                # Check if memory exists
                existing = None
                if memory_id:
                    cursor = await db.execute(
                        "SELECT id FROM memories WHERE id = ?", (memory_id,)
                    )
                    existing = await cursor.fetchone()

                if existing:
                    if overwrite:
                        # Update existing memory
                        await db.execute(
                            """
                            UPDATE memories SET
                                type = ?, title = ?, content = ?, weight = ?,
                                pinned = ?, emotional_flag = ?, updated_at = ?,
                                status = ?, metadata = ?
                            WHERE id = ?
                            """,
                            (
                                memory.get("type", "memory"),
                                memory["title"],
                                memory["content"],
                                memory.get("weight", 0.8),
                                memory.get("pinned", False),
                                memory.get("emotional_flag", False),
                                _now(),
                                memory.get("status", "active"),
                                json.dumps(memory.get("metadata")) if memory.get("metadata") else None,
                                memory_id,
                            ),
                        )
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                        continue
                else:
                    # Create new memory
                    import uuid
                    new_id = memory_id or str(uuid.uuid4())
                    now = _now()

                    await db.execute(
                        """
                        INSERT INTO memories (
                            id, type, title, content, weight, pinned, emotional_flag,
                            created_at, updated_at, last_accessed_at, access_count, status, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_id,
                            memory.get("type", "memory"),
                            memory["title"],
                            memory["content"],
                            memory.get("weight", 0.8),
                            memory.get("pinned", False),
                            memory.get("emotional_flag", False),
                            memory.get("created_at", now),
                            now,
                            memory.get("last_accessed_at", now),
                            memory.get("access_count", 0),
                            memory.get("status", "active"),
                            json.dumps(memory.get("metadata")) if memory.get("metadata") else None,
                        ),
                    )
                    memory_id = new_id
                    stats["created"] += 1

                # Set tags and triggers
                if "tags" in memory and memory["tags"]:
                    await _set_memory_tags(db, memory_id, memory["tags"])
                if "triggers" in memory and memory["triggers"]:
                    await _set_memory_triggers(db, memory_id, memory["triggers"])

            except Exception as e:
                stats["errors"].append({
                    "memory": memory.get("title", "unknown"),
                    "error": str(e),
                })

        await db.commit()

    return stats
