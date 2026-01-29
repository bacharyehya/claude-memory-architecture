"""
Mnemonic MCP Server - AI Memory Management

A FastMCP server providing persistent memory management for AI assistants.
"""

import json
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

from mnemonic.core import (
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    list_memories,
    pin_memory,
    search_memories,
    export_memories,
    import_memories,
    record_access,
)
from mnemonic.core.search import get_stats
from mnemonic.db import init_db


# Initialize FastMCP server
mcp = FastMCP(
    "mnemonic",
    instructions="AI Memory MCP Server - Persistent memory management for Claude and other AI assistants. Use mnemonic_create to store memories, mnemonic_search to find them, and mnemonic_stats for an overview.",
)


# ============================================================================
# Pydantic Models for Tool Inputs
# ============================================================================


class CreateMemoryInput(BaseModel):
    """Input for creating a new memory."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short, descriptive title for the memory",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Full content of the memory. Can be markdown.",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Tags for categorization (e.g., ['project', 'wishly'])",
    )
    triggers: Optional[list[str]] = Field(
        default=None,
        description="Phrases that should surface this memory (e.g., ['load my tasks', 'resume work'])",
    )
    pinned: bool = Field(
        default=False,
        description="If true, memory won't decay over time",
    )
    emotional_flag: bool = Field(
        default=False,
        description="Mark as emotionally significant",
    )
    weight: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=1.0,
        description="Initial importance weight (0.1-1.0, default: 0.8)",
    )


class GetMemoryInput(BaseModel):
    """Input for getting a memory by ID."""

    id: str = Field(..., description="Memory UUID")


class UpdateMemoryInput(BaseModel):
    """Input for updating an existing memory."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Memory UUID to update")
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="New title",
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="New content",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="New tags (replaces existing)",
    )
    triggers: Optional[list[str]] = Field(
        default=None,
        description="New triggers (replaces existing)",
    )
    weight: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=1.0,
        description="New weight",
    )
    pinned: Optional[bool] = Field(default=None, description="Pin/unpin")
    emotional_flag: Optional[bool] = Field(
        default=None, description="Set emotional flag"
    )


class DeleteMemoryInput(BaseModel):
    """Input for deleting a memory."""

    id: str = Field(..., description="Memory UUID to delete")


class SearchMemoriesInput(BaseModel):
    """Input for searching memories."""

    query: Optional[str] = Field(
        default=None,
        description="Search query (searches title and content via full-text search)",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Filter by tags (must have ALL specified tags)",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return",
    )


class ListMemoriesInput(BaseModel):
    """Input for listing memories."""

    status: Optional[str] = Field(
        default="active",
        description="Filter by status: 'active', 'archived', or None for all",
    )
    sort_by: str = Field(
        default="updated_at",
        description="Sort field: weight, created_at, updated_at, last_accessed_at",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results",
    )


class PinMemoryInput(BaseModel):
    """Input for pinning/unpinning a memory."""

    id: str = Field(..., description="Memory UUID")
    pinned: bool = Field(default=True, description="True to pin, False to unpin")


class ImportMemoriesInput(BaseModel):
    """Input for importing memories."""

    data: dict = Field(
        ...,
        description="Export data containing 'memories' array",
    )
    overwrite: bool = Field(
        default=False,
        description="Overwrite existing memories with same ID",
    )


# ============================================================================
# MCP Tools - Free Tier
# ============================================================================


@mcp.tool()
async def mnemonic_create(params: CreateMemoryInput) -> str:
    """
    Create a new memory.

    Use this to store important information that should persist across sessions.
    Memories can be tagged for organization and have trigger phrases that
    surface them when relevant topics come up.

    Example:
        - Title: "Bash's communication style"
        - Content: "Direct, concise, no fluff. Lead with conclusions."
        - Tags: ["preferences", "user-profile"]
        - Triggers: ["how does bash like responses"]
    """
    memory = await create_memory(
        title=params.title,
        content=params.content,
        tags=params.tags,
        triggers=params.triggers,
        pinned=params.pinned,
        emotional_flag=params.emotional_flag,
        weight=params.weight,
    )
    return json.dumps(memory, indent=2)


@mcp.tool()
async def mnemonic_get(params: GetMemoryInput) -> str:
    """
    Get a single memory by its ID.

    Returns the full memory including content, tags, triggers, and metadata.
    Also records that the memory was accessed (updates access count and timestamp).
    """
    memory = await get_memory(params.id)
    if not memory:
        return json.dumps({"error": f"Memory not found: {params.id}"})

    # Record access
    await record_access(params.id)

    return json.dumps(memory, indent=2)


@mcp.tool()
async def mnemonic_update(params: UpdateMemoryInput) -> str:
    """
    Update an existing memory.

    Only specified fields will be updated. Tags and triggers are replaced
    entirely if provided (not merged).

    Example:
        - id: "abc-123"
        - weight: 0.95  # Increase importance
        - tags: ["high-priority"]  # Replace existing tags
    """
    memory = await update_memory(
        memory_id=params.id,
        title=params.title,
        content=params.content,
        tags=params.tags,
        triggers=params.triggers,
        weight=params.weight,
        pinned=params.pinned,
        emotional_flag=params.emotional_flag,
    )
    if not memory:
        return json.dumps({"error": f"Memory not found: {params.id}"})

    return json.dumps(memory, indent=2)


@mcp.tool()
async def mnemonic_delete(params: DeleteMemoryInput) -> str:
    """
    Permanently delete a memory.

    This cannot be undone. Consider setting status to 'archived' instead
    if you might need the memory later.
    """
    deleted = await delete_memory(params.id)
    if not deleted:
        return json.dumps({"error": f"Memory not found: {params.id}"})

    return json.dumps({"success": True, "deleted_id": params.id})


@mcp.tool()
async def mnemonic_search(params: SearchMemoriesInput) -> str:
    """
    Search memories using full-text search and/or tag filtering.

    The query searches both title and content using SQLite FTS5.
    Results are ranked by relevance and weight.

    Examples:
        - query: "wishly deals"  # Find memories about Wishly deals
        - tags: ["project"]  # All memories tagged 'project'
        - query: "API", tags: ["technical"]  # Combine search and filtering
    """
    results = await search_memories(
        query=params.query,
        tags=params.tags,
        limit=params.limit,
    )
    return json.dumps(results, indent=2)


@mcp.tool()
async def mnemonic_list(params: ListMemoriesInput) -> str:
    """
    List all memories with optional filtering and sorting.

    Use this for browsing memories rather than searching.
    Returns paginated results with metadata.
    """
    results = await list_memories(
        status=params.status,
        sort_by=params.sort_by,
        limit=params.limit,
    )
    return json.dumps(results, indent=2)


@mcp.tool()
async def mnemonic_pin(params: PinMemoryInput) -> str:
    """
    Pin or unpin a memory.

    Pinned memories:
    - Won't decay in weight over time (premium feature)
    - Are prioritized in search results
    - Useful for critical information like user preferences
    """
    memory = await pin_memory(params.id, params.pinned)
    if not memory:
        return json.dumps({"error": f"Memory not found: {params.id}"})

    return json.dumps(memory, indent=2)


@mcp.tool()
async def mnemonic_export() -> str:
    """
    Export all active memories to JSON.

    Returns a complete export that can be imported later or backed up.
    Useful for:
    - Backing up memories
    - Transferring to another system
    - Debugging
    """
    export = await export_memories(include_archived=False)
    return json.dumps(export, indent=2)


@mcp.tool()
async def mnemonic_import(params: ImportMemoriesInput) -> str:
    """
    Import memories from a previous export.

    The data must be in the export format with a 'memories' array.

    Options:
    - overwrite: If true, updates existing memories with matching IDs
                 If false, skips memories that already exist

    Returns statistics about the import operation.
    """
    stats = await import_memories(
        data=params.data,
        overwrite=params.overwrite,
    )
    return json.dumps(stats, indent=2)


@mcp.tool()
async def mnemonic_stats() -> str:
    """
    Get memory statistics.

    Returns:
    - Total memory count by status
    - Weight distribution
    - Most used tags
    - Pinned/emotional counts

    Useful for understanding your memory landscape.
    """
    stats = await get_stats()
    return json.dumps(stats, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================


def main():
    """Run the Mnemonic MCP server."""
    import asyncio

    # Initialize database on startup
    asyncio.run(init_db())

    # Run server
    mcp.run()


if __name__ == "__main__":
    main()
