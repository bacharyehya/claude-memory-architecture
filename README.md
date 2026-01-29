# Mnemonic - AI Memory MCP Server

Persistent memory management for Claude and other AI assistants. Give your AI a brain that remembers.

> Born from the [Claude Memory Architecture](./SPEC.md) research project.

## Quick Install

```bash
# Using uvx (recommended)
uvx mnemonic-memory

# Or pip
pip install mnemonic-memory
```

## Claude Code Setup

Add to your Claude Code MCP config (`~/.claude.json` or project `.claude/settings.json`):

```json
{
  "mcpServers": {
    "mnemonic": {
      "command": "uvx",
      "args": ["mnemonic-memory"]
    }
  }
}
```

Or with pip-installed version:

```json
{
  "mcpServers": {
    "mnemonic": {
      "command": "mnemonic"
    }
  }
}
```

## Features

### Free Tier (Available Now)

| Tool | Description |
|------|-------------|
| `mnemonic_create` | Create a new memory with tags and triggers |
| `mnemonic_get` | Retrieve a memory by ID |
| `mnemonic_update` | Update an existing memory |
| `mnemonic_delete` | Permanently delete a memory |
| `mnemonic_search` | Full-text search with tag filtering |
| `mnemonic_list` | List all memories with sorting |
| `mnemonic_pin` | Pin important memories |
| `mnemonic_export` | Export all memories to JSON |
| `mnemonic_import` | Import from a previous export |
| `mnemonic_stats` | View memory statistics |

### Premium Tier (Coming Soon) - $29 one-time or $5/mo

- **Semantic Search**: Find memories by meaning, not just keywords
- **Auto-Decay**: Memories fade based on access patterns
- **Consolidation**: Automatically merge similar memories
- **Maintenance**: Clean up stale data

## Usage Examples

### Create a memory

```
mnemonic_create({
  "title": "Bash's communication preferences",
  "content": "Direct and concise. Lead with conclusions (Minto Pyramid). No fluff.",
  "tags": ["preferences", "communication"],
  "triggers": ["how should I respond to bash"]
})
```

### Search memories

```
# Full-text search
mnemonic_search({"query": "communication preferences"})

# Filter by tags
mnemonic_search({"tags": ["preferences"]})

# Combined
mnemonic_search({"query": "direct", "tags": ["communication"]})
```

### Pin important memories

```
mnemonic_pin({"id": "abc-123", "pinned": true})
```

## Data Storage

Memories are stored in `~/.mnemonic/memories.db` (SQLite).

Override with `MNEMONIC_DATA_DIR` environment variable:

```bash
export MNEMONIC_DATA_DIR="/custom/path"
```

## Schema

```
memories
├── id (TEXT, UUID)
├── type (TEXT, default 'memory')
├── title (TEXT)
├── content (TEXT)
├── weight (REAL, 0.1-1.0)
├── pinned (BOOLEAN)
├── emotional_flag (BOOLEAN)
├── created_at (TEXT, ISO timestamp)
├── updated_at (TEXT)
├── last_accessed_at (TEXT)
├── access_count (INTEGER)
├── status (TEXT: active, archived)
└── metadata (JSON)

tags
├── id (INTEGER)
└── name (TEXT, unique)

memory_tags (many-to-many)

triggers
├── id (INTEGER)
├── memory_id (TEXT)
└── phrase (TEXT)
```

## Architecture

This project implements the [Claude Memory Architecture](./SPEC.md) research:

- **Weighted memories**: Not all memories are equal (0.1-1.0 weight)
- **Memory decay**: Unused things fade (premium feature)
- **Depth on demand**: Load summaries, expand when needed
- **Trigger-based recall**: Phrases that surface relevant memories

## Development

```bash
# Clone
git clone https://github.com/bashoh/mnemonic-memory
cd mnemonic-memory

# Install with dev dependencies
pip install -e ".[dev]"

# Run locally
python -m mnemonic
```

## License

MIT

## Author

Built by Bash @ Wishly Group

---

*"Current AI assistants have Alzheimer's. Let's fix that."*
