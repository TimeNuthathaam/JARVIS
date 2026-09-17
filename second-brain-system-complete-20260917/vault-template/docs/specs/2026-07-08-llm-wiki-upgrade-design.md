# Second Brain — LLM Wiki Upgrade (approved 2026-07-08)

Source: Paul Kimmy "ผมสร้างสมองที่สองให้ Agent" (Karpathy LLM Wiki pattern) —
report at `/home/time/watch-output/Paul_Kimmy/agent-20260708-030554/report.md`.
User decisions locked in conversation; advisor-reviewed (no 5th bucket,
search-then-update rule, ASK write-back).

## Goal

Give the vault the Karpathy/Paul-Kimmy layering — typed extraction folders,
SCHEMA governance, persisted query answers, and **automatic memory** (agent
writes knowledge after every research task without being told) — while keeping
the user-facing surface exactly one command (`/sb`), simple, and token-lean.

## Decisions

1. **Target: this vault only** (`/home/time/second-brain`). No second wiki, no
   ClaudeClaw-specific vault.
2. **Real folders, minimal set.** `wiki/` (currently empty, 0 files) is REPLACED by:
   - `entities/` — companies / tools / products / public people-as-subjects
   - `concepts/` — แนวคิด / เทคนิค / pattern, **including topic-synthesis and
     overview pages** (a "topic" is a broad concept node — no general bucket exists)
   - `comparisons/` — A-vs-B pages
   - `queries/` — research questions answered → persisted as permanent nodes
   `people/` stays the CRM (คนรู้จักจริง มี relationship) — distinct from entities.
   `raw/` stays flat (+`raw/assets/`) — NOT split into articles/papers/transcripts
   (simplicity over fidelity to the video). journal/, output/, audit/, log/ unchanged.
3. **`SCHEMA.md`** at vault root — taxonomy governance: which folder gets what,
   naming (kebab-case English), frontmatter per type, wikilink + aliases rules.
   The AGENT routes via SCHEMA.md; the user never needs to know the taxonomy.
4. **Full-auto memory (llm-wiki-protocol)** pinned in user-level `~/.claude/CLAUDE.md`:
   after completing any research-type task (watch/listen/deep-research/perplexity/
   substantial web research), the agent writes/updates relevant nodes in the vault
   automatically — no ask. Constraints that make full-auto safe:
   - **Search-then-update, create-last:** search aliases AND node bodies first;
     on overlap, extend the existing node — never spawn near-duplicates.
   - Write ONCE at end of task (not incrementally) — token-lean.
   - Finish with `bin/sb-commit.sh` as always.
5. **ASK op changes:** retrieval greps all knowledge folders (4 typed + people/);
   genuinely useful answers are written back into `queries/` (closes the loop).
6. **Boundary (unchanged):** project working-state memory (`/save-progress`,
   `/close-session`, `.claude/memory/` per project) is a SEPARATE system. Session
   states never enter this vault; `/sb` ops and the auto-protocol write knowledge only.

## Implementation surface

- vault: `mkdir entities concepts comparisons queries` (+`.gitkeep`), remove empty `wiki/`
- vault `SCHEMA.md` (new)
- vault `CLAUDE.md`: folder contract, frontmatter schemas, PROCESS + ASK ops → typed folders
- `bin/sb-index.sh`: scan the 4 typed folders instead of `wiki/`
- `~/.claude/skills/second-brain/SKILL.md`: point at SCHEMA.md (routing unchanged)
- `~/.claude/CLAUDE.md`: llm-wiki-protocol block (~7 lines)
- Bonus (out-of-vault, promised in same session): `channel-format-dna` skill gets the
  missing `yt-dlp --flat-playlist` channel-listing command.

## Out of scope

- Splitting `raw/` into typed subfolders; new slash commands per type; vector DB;
  NEOKNOWLEDGE; Obsidian graph color pre-config; migrating old content (wiki/ is empty).
