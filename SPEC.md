# Weighted Hierarchical Memory for AI Agents

> A memory architecture that balances token efficiency with context depth, inspired by human memory systems.

**Author:** Bash (with Claude)
**Date:** 2026-01-29
**Status:** Early Research / Concept

---

## The Problem

Current AI memory approaches have fundamental tradeoffs:

| Approach | Pros | Cons |
|----------|------|------|
| **Large context window** | Full fidelity | Expensive, still limited |
| **RAG / Vector DB** | Scalable | Loses structure, retrieval quality varies |
| **Summarization** | Token efficient | Loses detail, can't recover |
| **Static memory files** | Controllable | Flat, no weighting, no decay |
| **Fine-tuning** | Persistent | Expensive, slow, not dynamic |

**What we want:**
- Token efficiency (don't load everything every time)
- Depth on demand (can expand when needed)
- Weighted importance (not all memories are equal)
- Natural decay (unused memories fade)
- Structure (searchable, indexed)
- User-controlled (explicit "remember this" moments)

---

## Proposed Architecture

### Memory Tiers

```
┌─────────────────────────────────────────────────────┐
│  TIER 0: Identity Core (~3KB)                       │
│  Always loaded. Who is this user? Core relationship.│
│  Never decays. Updated only explicitly.             │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  TIER 1: Hot Memory (~10-20KB)                      │
│  Loaded per session. Active projects, recent        │
│  learnings, current context.                        │
│  Refreshed based on access frequency.               │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  TIER 2: Indexed Archive (unlimited)                │
│  YAML-indexed, searchable, not loaded by default.   │
│  Loaded on-demand via triggers/search.              │
│  Subject to decay based on access patterns.         │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  TIER 3: Raw Archive (unlimited)                    │
│  Full transcripts, complete context.                │
│  Never deleted. Rarely accessed.                    │
│  For "dig deeper" recovery operations.              │
└─────────────────────────────────────────────────────┘
```

### Memory Entry Schema

```yaml
---
# Metadata
id: uuid-here
type: memory | learning | milestone | reference
title: Human-readable title
created: 2026-01-29T03:00:00Z
last_accessed: 2026-01-29T03:00:00Z
access_count: 1

# Weighting
weight: 0.95           # 0.0-1.0, decays over time
emotional_flag: true   # User explicitly marked as significant
pinned: false          # Never decay this

# Classification
tags: [validation, portal, wishly]
topics: [meeting-analysis, career]
people: [Sara Uy, Aneesh]
triggers:              # Phrases that should load this memory
  - "going places"
  - "Sara Uy feedback"
  - "portal validation"

# References
refs:
  session: ~/.claude/projects/.../session-id.jsonl
  deep_context: ~/.claude/deep-context/filename.md
  artifacts:
    - ~/Downloads/file.wav
    - Apple Notes: Note Title

# Status
status: active | stale | archived
decay_eligible: true
---

# Content

The compressed, token-efficient version of the memory.
Should be readable standalone but can reference deeper context.
```

### Weighting Algorithm

```python
def calculate_weight(memory):
    base_weight = memory.weight

    # Decay based on time since last access
    days_since_access = (now - memory.last_accessed).days
    time_decay = 0.99 ** days_since_access  # ~0.90 after 10 days

    # Boost based on access frequency
    frequency_boost = min(memory.access_count * 0.02, 0.3)

    # Emotional memories resist decay
    if memory.emotional_flag:
        time_decay = max(time_decay, 0.8)

    # Pinned memories never decay
    if memory.pinned:
        return 1.0

    return min(base_weight * time_decay + frequency_boost, 1.0)
```

### Trigger System

| Trigger Phrase | Action |
|----------------|--------|
| "remember this" | Create Tier 2 entry (simple) |
| "this is significant" | Create Tier 2 entry with emotional_flag + deep_context file |
| "save progress" | Update existing entries, add session summary |
| "dig deeper into X" | Search Tier 2/3, load matching deep_context |
| "what do you remember about X" | Search and summarize relevant memories |
| "memory maintenance" | Run decay pass, consolidate, archive stale |

### Decay & Defragmentation

**Automatic Decay:**
- Weight decreases daily if not accessed
- Entries below 0.3 weight are flagged as "stale"
- Stale entries are candidates for archival

**Consolidation:**
- Multiple similar learnings can be merged
- "Learned X about API" + "Also X about API" → single entry

**Archival:**
- Stale entries move to Tier 3
- Still searchable, but not loaded proactively
- Can be recovered via "dig deeper"

**Pruning (Optional):**
- After N months in archive with zero access, entries could be deleted
- Or: kept forever but with zero weight (never surfaces naturally)

---

## Implementation Approaches

### Approach 1: File-Based (Current)

```
~/.claude/
├── CLAUDE.md           # Tier 0 + Tier 1 (curated)
├── memories/           # Tier 2 (indexed memories)
│   ├── 2026-01-29-going-places.md
│   └── ...
├── deep-context/       # Tier 2 extended (detailed context)
│   └── ...
└── projects/           # Tier 3 (raw transcripts)
    └── *.jsonl
```

**Pros:** Works today, no infrastructure needed
**Cons:** No automatic weighting, manual trigger required

### Approach 2: SQLite + Files

```
~/.claude/
├── memory.db           # Index, weights, metadata
├── content/            # Actual memory content (markdown)
└── transcripts/        # Raw session data
```

**Pros:** Real querying, automatic weight calculation
**Cons:** Requires tooling to read/write

### Approach 3: Hybrid with MCP

Custom MCP server that:
- Exposes memory as tools (`remember`, `recall`, `forget`)
- Handles weighting/decay automatically
- Provides search interface

**Pros:** Clean integration, powerful
**Cons:** Requires building MCP server

---

## Open Questions

1. **Who controls decay?** Should it be automatic, or user-triggered?
2. **How to handle conflicts?** If old memory contradicts new learning?
3. **Privacy:** Some memories might need encryption or separation
4. **Multi-agent:** If multiple Claude instances, how to sync memory?
5. **Portability:** How to export/import memory between systems?

---

## Prior Art / Research

- **MemGPT** - Tiered memory for LLMs with pagination
- **Reflexion** - Self-reflective agents with memory
- **Generative Agents** - Stanford paper on memory streams
- **LangChain Memory** - Various memory implementations
- **Zep** - Long-term memory service for LLM apps

---

## Next Steps

1. [ ] Test current file-based approach (Tier 0-3)
2. [ ] Build simple indexer for YAML frontmatter search
3. [ ] Implement decay calculation as a maintenance script
4. [ ] Consider MCP server for cleaner integration
5. [ ] Document patterns that work / don't work

---

## Why This Matters

Current AI assistants have Alzheimer's. Every conversation starts fresh unless you manually maintain memory files. The burden is on the user to curate, organize, and trigger recall.

A weighted hierarchical memory shifts that burden:
- Important things naturally persist
- Unimportant things naturally fade
- Deep context is available when needed
- Token efficiency by default, depth on demand

This isn't about giving AI "true" memory. It's about making the memory *we already maintain* smarter, more automatic, and more human-like in its behavior.

---

*"The difference between imposter syndrome and reality is that imposter syndrome has no receipts."*
— Bash, 2026-01-29, 3am
