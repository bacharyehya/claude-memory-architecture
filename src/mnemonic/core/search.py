"""Search operations for memories."""

import json
from typing import Any, Optional

from mnemonic.db.connection import get_db
from mnemonic.core.memory import _get_memory_tags, _get_memory_triggers, _row_to_dict


async def search_memories(
    query: Optional[str] = None,
    tags: Optional[list[str]] = None,
    status: str = "active",
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search memories using full-text search and/or tag filtering.

    Args:
        query: Search query for FTS (searches title and content)
        tags: Filter by tags (memories must have ALL specified tags)
        status: Filter by status (default: 'active')
        limit: Maximum results
        offset: Skip first N results

    Returns:
        Dictionary with items, total count, and pagination info
    """
    async with get_db() as db:
        # Build query based on search parameters
        if query and tags:
            # Both FTS and tag filter
            tag_placeholders = ",".join("?" * len(tags))
            sql = f"""
                SELECT DISTINCT m.* FROM memories m
                JOIN memories_fts fts ON m.id = fts.id
                JOIN memory_tags mt ON m.id = mt.memory_id
                JOIN tags t ON mt.tag_id = t.id
                WHERE fts.memories_fts MATCH ?
                AND t.name IN ({tag_placeholders})
                AND m.status = ?
                GROUP BY m.id
                HAVING COUNT(DISTINCT t.name) = ?
                ORDER BY fts.rank, m.weight DESC
                LIMIT ? OFFSET ?
            """
            params = [query, *[t.lower() for t in tags], status, len(tags), limit, offset]

            # Count query
            count_sql = f"""
                SELECT COUNT(DISTINCT m.id) as count FROM memories m
                JOIN memories_fts fts ON m.id = fts.id
                JOIN memory_tags mt ON m.id = mt.memory_id
                JOIN tags t ON mt.tag_id = t.id
                WHERE fts.memories_fts MATCH ?
                AND t.name IN ({tag_placeholders})
                AND m.status = ?
                GROUP BY m.id
                HAVING COUNT(DISTINCT t.name) = ?
            """
            count_params = [query, *[t.lower() for t in tags], status, len(tags)]

        elif query:
            # FTS only
            sql = """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.id = fts.id
                WHERE fts.memories_fts MATCH ?
                AND m.status = ?
                ORDER BY fts.rank, m.weight DESC
                LIMIT ? OFFSET ?
            """
            params = [query, status, limit, offset]

            count_sql = """
                SELECT COUNT(*) as count FROM memories m
                JOIN memories_fts fts ON m.id = fts.id
                WHERE fts.memories_fts MATCH ?
                AND m.status = ?
            """
            count_params = [query, status]

        elif tags:
            # Tag filter only
            tag_placeholders = ",".join("?" * len(tags))
            sql = f"""
                SELECT m.* FROM memories m
                JOIN memory_tags mt ON m.id = mt.memory_id
                JOIN tags t ON mt.tag_id = t.id
                WHERE t.name IN ({tag_placeholders})
                AND m.status = ?
                GROUP BY m.id
                HAVING COUNT(DISTINCT t.name) = ?
                ORDER BY m.weight DESC, m.updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = [*[t.lower() for t in tags], status, len(tags), limit, offset]

            count_sql = f"""
                SELECT COUNT(*) as count FROM (
                    SELECT m.id FROM memories m
                    JOIN memory_tags mt ON m.id = mt.memory_id
                    JOIN tags t ON mt.tag_id = t.id
                    WHERE t.name IN ({tag_placeholders})
                    AND m.status = ?
                    GROUP BY m.id
                    HAVING COUNT(DISTINCT t.name) = ?
                )
            """
            count_params = [*[t.lower() for t in tags], status, len(tags)]

        else:
            # No search criteria - return by weight
            sql = """
                SELECT * FROM memories
                WHERE status = ?
                ORDER BY weight DESC, updated_at DESC
                LIMIT ? OFFSET ?
            """
            params = [status, limit, offset]

            count_sql = "SELECT COUNT(*) as count FROM memories WHERE status = ?"
            count_params = [status]

        # Execute count query
        cursor = await db.execute(count_sql, count_params)
        result = await cursor.fetchone()
        total = result["count"] if result else 0

        # Execute main query
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()

        # Convert to list of dicts with tags and triggers
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
        "query": query,
        "tags": tags,
    }


async def search_by_trigger(phrase: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Find memories by trigger phrase.

    This searches for memories whose trigger phrases contain the given phrase.

    Args:
        phrase: Trigger phrase to search for
        limit: Maximum results

    Returns:
        List of matching memories
    """
    phrase = phrase.lower().strip()

    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT DISTINCT m.* FROM memories m
            JOIN triggers t ON m.id = t.memory_id
            WHERE t.phrase LIKE ?
            AND m.status = 'active'
            ORDER BY m.weight DESC
            LIMIT ?
            """,
            (f"%{phrase}%", limit),
        )
        rows = await cursor.fetchall()

        items = []
        for row in rows:
            memory = _row_to_dict(row)
            memory["tags"] = await _get_memory_tags(db, memory["id"])
            memory["triggers"] = await _get_memory_triggers(db, memory["id"])
            if memory.get("metadata"):
                memory["metadata"] = json.loads(memory["metadata"])
            items.append(memory)

    return items


async def get_stats() -> dict[str, Any]:
    """
    Get memory statistics.

    Returns:
        Dictionary with counts, weight distribution, tag counts, etc.
    """
    async with get_db() as db:
        # Total counts by status
        cursor = await db.execute(
            """
            SELECT status, COUNT(*) as count
            FROM memories
            GROUP BY status
            """
        )
        status_counts = {row["status"]: row["count"] for row in await cursor.fetchall()}

        # Weight distribution
        cursor = await db.execute(
            """
            SELECT
                CASE
                    WHEN weight >= 0.9 THEN 'high (0.9-1.0)'
                    WHEN weight >= 0.7 THEN 'medium (0.7-0.9)'
                    WHEN weight >= 0.5 THEN 'low (0.5-0.7)'
                    ELSE 'very_low (<0.5)'
                END as bracket,
                COUNT(*) as count
            FROM memories
            WHERE status = 'active'
            GROUP BY bracket
            """
        )
        weight_dist = {row["bracket"]: row["count"] for row in await cursor.fetchall()}

        # Pinned count
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM memories WHERE pinned = TRUE AND status = 'active'"
        )
        pinned_count = (await cursor.fetchone())["count"]

        # Emotional count
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM memories WHERE emotional_flag = TRUE AND status = 'active'"
        )
        emotional_count = (await cursor.fetchone())["count"]

        # Top tags
        cursor = await db.execute(
            """
            SELECT t.name, COUNT(*) as count
            FROM tags t
            JOIN memory_tags mt ON t.id = mt.tag_id
            JOIN memories m ON mt.memory_id = m.id
            WHERE m.status = 'active'
            GROUP BY t.name
            ORDER BY count DESC
            LIMIT 10
            """
        )
        top_tags = {row["name"]: row["count"] for row in await cursor.fetchall()}

        # Average weight
        cursor = await db.execute(
            "SELECT AVG(weight) as avg FROM memories WHERE status = 'active'"
        )
        avg_weight = (await cursor.fetchone())["avg"] or 0

        # Total trigger count
        cursor = await db.execute("SELECT COUNT(*) as count FROM triggers")
        trigger_count = (await cursor.fetchone())["count"]

    return {
        "total_memories": sum(status_counts.values()),
        "by_status": status_counts,
        "weight_distribution": weight_dist,
        "average_weight": round(avg_weight, 3),
        "pinned_count": pinned_count,
        "emotional_count": emotional_count,
        "top_tags": top_tags,
        "total_triggers": trigger_count,
    }
