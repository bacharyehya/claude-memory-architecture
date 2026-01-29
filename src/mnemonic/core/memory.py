"""CRUD operations for memories."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from mnemonic.config import DEFAULT_WEIGHT, MIN_WEIGHT, MAX_WEIGHT
from mnemonic.db.connection import get_db


def _now() -> str:
    """Get current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    """Generate a unique memory ID."""
    return str(uuid.uuid4())


async def _get_or_create_tag(db, tag_name: str) -> int:
    """Get tag ID, creating if it doesn't exist."""
    tag_name = tag_name.lower().strip()

    # Try to get existing tag
    cursor = await db.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
    row = await cursor.fetchone()
    if row:
        return row["id"]

    # Create new tag
    cursor = await db.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
    return cursor.lastrowid


async def _set_memory_tags(db, memory_id: str, tags: list[str]) -> None:
    """Set tags for a memory (replaces existing)."""
    # Remove existing tags
    await db.execute("DELETE FROM memory_tags WHERE memory_id = ?", (memory_id,))

    # Add new tags
    for tag in tags:
        tag_id = await _get_or_create_tag(db, tag)
        await db.execute(
            "INSERT OR IGNORE INTO memory_tags (memory_id, tag_id) VALUES (?, ?)",
            (memory_id, tag_id),
        )


async def _set_memory_triggers(db, memory_id: str, triggers: list[str]) -> None:
    """Set trigger phrases for a memory (replaces existing)."""
    # Remove existing triggers
    await db.execute("DELETE FROM triggers WHERE memory_id = ?", (memory_id,))

    # Add new triggers
    for phrase in triggers:
        phrase = phrase.lower().strip()
        if phrase:
            await db.execute(
                "INSERT INTO triggers (memory_id, phrase) VALUES (?, ?)",
                (memory_id, phrase),
            )


async def _get_memory_tags(db, memory_id: str) -> list[str]:
    """Get all tags for a memory."""
    cursor = await db.execute(
        """
        SELECT t.name FROM tags t
        JOIN memory_tags mt ON t.id = mt.tag_id
        WHERE mt.memory_id = ?
        ORDER BY t.name
        """,
        (memory_id,),
    )
    rows = await cursor.fetchall()
    return [row["name"] for row in rows]


async def _get_memory_triggers(db, memory_id: str) -> list[str]:
    """Get all trigger phrases for a memory."""
    cursor = await db.execute(
        "SELECT phrase FROM triggers WHERE memory_id = ? ORDER BY phrase",
        (memory_id,),
    )
    rows = await cursor.fetchall()
    return [row["phrase"] for row in rows]


def _row_to_dict(row) -> dict[str, Any]:
    """Convert a database row to a dictionary."""
    return dict(row)


async def create_memory(
    title: str,
    content: str,
    tags: Optional[list[str]] = None,
    triggers: Optional[list[str]] = None,
    pinned: bool = False,
    emotional_flag: bool = False,
    memory_type: str = "memory",
    weight: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Create a new memory.

    Args:
        title: Short title for the memory
        content: Full content/description
        tags: Optional list of tags for categorization
        triggers: Optional list of trigger phrases that should surface this memory
        pinned: If True, memory won't decay
        emotional_flag: Marks memory as emotionally significant
        memory_type: Type of memory (default: 'memory')
        weight: Initial weight (default: 0.8)
        metadata: Optional JSON metadata

    Returns:
        The created memory as a dictionary
    """
    memory_id = _generate_id()
    now = _now()
    weight = weight if weight is not None else DEFAULT_WEIGHT
    weight = max(MIN_WEIGHT, min(MAX_WEIGHT, weight))  # Clamp weight

    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO memories (
                id, type, title, content, weight, pinned, emotional_flag,
                created_at, updated_at, last_accessed_at, access_count, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?)
            """,
            (
                memory_id,
                memory_type,
                title,
                content,
                weight,
                pinned,
                emotional_flag,
                now,
                now,
                now,
                json.dumps(metadata) if metadata else None,
            ),
        )

        if tags:
            await _set_memory_tags(db, memory_id, tags)
        if triggers:
            await _set_memory_triggers(db, memory_id, triggers)

        await db.commit()

    # Return the created memory
    return await get_memory(memory_id)


async def get_memory(memory_id: str) -> Optional[dict[str, Any]]:
    """
    Get a memory by ID.

    Args:
        memory_id: The memory UUID

    Returns:
        Memory dictionary or None if not found
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        memory = _row_to_dict(row)
        memory["tags"] = await _get_memory_tags(db, memory_id)
        memory["triggers"] = await _get_memory_triggers(db, memory_id)

        # Parse metadata JSON
        if memory.get("metadata"):
            memory["metadata"] = json.loads(memory["metadata"])

        return memory


async def update_memory(
    memory_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[list[str]] = None,
    triggers: Optional[list[str]] = None,
    weight: Optional[float] = None,
    pinned: Optional[bool] = None,
    emotional_flag: Optional[bool] = None,
    status: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[dict[str, Any]]:
    """
    Update an existing memory.

    Args:
        memory_id: The memory UUID
        title: New title (optional)
        content: New content (optional)
        tags: New tags - replaces existing (optional)
        triggers: New triggers - replaces existing (optional)
        weight: New weight (optional)
        pinned: New pinned status (optional)
        emotional_flag: New emotional flag (optional)
        status: New status (optional)
        metadata: New metadata - replaces existing (optional)

    Returns:
        Updated memory or None if not found
    """
    # Check memory exists
    existing = await get_memory(memory_id)
    if not existing:
        return None

    # Build update query
    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if weight is not None:
        weight = max(MIN_WEIGHT, min(MAX_WEIGHT, weight))
        updates.append("weight = ?")
        params.append(weight)
    if pinned is not None:
        updates.append("pinned = ?")
        params.append(pinned)
    if emotional_flag is not None:
        updates.append("emotional_flag = ?")
        params.append(emotional_flag)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))

    # Always update updated_at
    updates.append("updated_at = ?")
    params.append(_now())
    params.append(memory_id)

    async with get_db() as db:
        if updates:
            query = f"UPDATE memories SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)

        # Update tags and triggers if provided
        if tags is not None:
            await _set_memory_tags(db, memory_id, tags)
        if triggers is not None:
            await _set_memory_triggers(db, memory_id, triggers)

        await db.commit()

    return await get_memory(memory_id)


async def delete_memory(memory_id: str) -> bool:
    """
    Delete a memory.

    Args:
        memory_id: The memory UUID

    Returns:
        True if deleted, False if not found
    """
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM memories WHERE id = ?", (memory_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def list_memories(
    status: Optional[str] = "active",
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List memories with optional filtering and pagination.

    Args:
        status: Filter by status (default: 'active', None for all)
        sort_by: Field to sort by (weight, created_at, updated_at, last_accessed_at)
        sort_order: 'asc' or 'desc'
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dictionary with items, total count, and pagination info
    """
    # Validate sort field
    valid_sorts = ["weight", "created_at", "updated_at", "last_accessed_at", "title"]
    if sort_by not in valid_sorts:
        sort_by = "updated_at"
    if sort_order.lower() not in ["asc", "desc"]:
        sort_order = "desc"

    async with get_db() as db:
        # Build query
        where_clause = ""
        params = []
        if status:
            where_clause = "WHERE status = ?"
            params.append(status)

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM memories {where_clause}"
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())["count"]

        # Get paginated results
        query = f"""
            SELECT * FROM memories
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        # Convert to list of dicts with tags
        items = []
        for row in rows:
            memory = _row_to_dict(row)
            memory["tags"] = await _get_memory_tags(db, memory["id"])
            memory["triggers"] = await _get_memory_triggers(db, memory["id"])
            if memory.get("metadata"):
                memory["metadata"] = json.loads(memory["metadata"])
            items.append(memory)

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }


async def pin_memory(memory_id: str, pinned: bool = True) -> Optional[dict[str, Any]]:
    """
    Pin or unpin a memory.

    Args:
        memory_id: The memory UUID
        pinned: True to pin, False to unpin

    Returns:
        Updated memory or None if not found
    """
    return await update_memory(memory_id, pinned=pinned)


async def record_access(memory_id: str) -> Optional[dict[str, Any]]:
    """
    Record that a memory was accessed.

    Updates last_accessed_at and increments access_count.

    Args:
        memory_id: The memory UUID

    Returns:
        Updated memory or None if not found
    """
    async with get_db() as db:
        cursor = await db.execute(
            """
            UPDATE memories
            SET last_accessed_at = ?, access_count = access_count + 1
            WHERE id = ?
            """,
            (_now(), memory_id),
        )
        await db.commit()

        if cursor.rowcount == 0:
            return None

    return await get_memory(memory_id)
