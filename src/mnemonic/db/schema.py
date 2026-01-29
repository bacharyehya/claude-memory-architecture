"""SQLite schema definitions for Mnemonic."""

SCHEMA = """
-- Main memories table
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT DEFAULT 'memory',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    weight REAL DEFAULT 0.8,
    pinned BOOLEAN DEFAULT FALSE,
    emotional_flag BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed_at TEXT NOT NULL,
    access_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    metadata JSON
);

-- Tags table for categorization
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Many-to-many relationship between memories and tags
CREATE TABLE IF NOT EXISTS memory_tags (
    memory_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, tag_id)
);

-- Trigger phrases that should surface a memory
CREATE TABLE IF NOT EXISTS triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT REFERENCES memories(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL
);

-- Full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    id UNINDEXED,
    title,
    content,
    content=memories,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, id, title, content)
    VALUES (NEW.rowid, NEW.id, NEW.title, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, id, title, content)
    VALUES('delete', OLD.rowid, OLD.id, OLD.title, OLD.content);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, id, title, content)
    VALUES('delete', OLD.rowid, OLD.id, OLD.title, OLD.content);
    INSERT INTO memories_fts(rowid, id, title, content)
    VALUES (NEW.rowid, NEW.id, NEW.title, NEW.content);
END;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
CREATE INDEX IF NOT EXISTS idx_memories_weight ON memories(weight DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_triggers_phrase ON triggers(phrase);
"""
