# Claude Memory Architecture

> Designing weighted, hierarchical memory for AI agents that balances token efficiency with context depth.

## What Is This?

A research project exploring how to give AI assistants better memory without:
- Loading everything into context every time (expensive)
- Losing important details through compression (lossy)
- Requiring constant manual curation (tedious)

## The Core Idea

**Memories should have weight.** Not all memories are equal:
- Some are emotionally significant
- Some are accessed frequently
- Some haven't been touched in months

**Memory should decay.** Like human memory:
- Important things stick
- Unused things fade
- Nothing is truly deleted (deep archive)

**Depth on demand.** Token-efficient by default:
- Load compressed summaries normally
- "Dig deeper" expands to full context when needed

## Architecture Overview

```
Tier 0: Identity Core     (~3KB, always loaded)
Tier 1: Hot Memory        (~20KB, session-loaded)
Tier 2: Indexed Archive   (unlimited, on-demand)
Tier 3: Raw Archive       (full transcripts, rare access)
```

See [SPEC.md](./SPEC.md) for the full specification.

## Status

🚧 **Early Research** — This is a concept being actively explored, not a finished tool.

## Origin

Born from a 3am conversation where I realized the memory systems I was manually maintaining could be smarter. The insight: if memories were weighted and searchable like skill files (with YAML frontmatter), they could be both token-efficient AND recoverable.

## Related Work

- MemGPT
- LangChain Memory modules
- Stanford's Generative Agents paper
- Zep memory service

## License

MIT — do whatever you want with this.

---

*"Current AI assistants have Alzheimer's. Let's fix that."*
