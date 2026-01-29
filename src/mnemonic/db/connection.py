"""Async SQLite connection management for Mnemonic."""

import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mnemonic.config import get_db_path
from mnemonic.db.schema import SCHEMA


_db_initialized = False


async def init_db() -> None:
    """Initialize the database with schema."""
    global _db_initialized
    if _db_initialized:
        return

    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        # Execute schema (CREATE IF NOT EXISTS is idempotent)
        await db.executescript(SCHEMA)
        await db.commit()

    _db_initialized = True


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Get an async database connection.

    Usage:
        async with get_db() as db:
            await db.execute(...)
    """
    # Ensure DB is initialized
    await init_db()

    db_path = get_db_path()
    async with aiosqlite.connect(db_path) as db:
        # Enable foreign keys for this connection
        await db.execute("PRAGMA foreign_keys = ON")
        # Return rows as dictionaries
        db.row_factory = aiosqlite.Row
        yield db
