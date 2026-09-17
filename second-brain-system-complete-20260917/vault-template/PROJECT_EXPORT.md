# PROJECT_EXPORT — second-brain

## What this is
Personal knowledge vault (Karpathy LLM-wiki architecture) with bash-driven ops. Typed knowledge folders (`raw/` → `entities/`, `concepts/`, `comparisons/`, `queries/`) plus a people/CRM + journal layer. All writes funnel through `bin/sb-commit.sh` (flock + log append + git commit). Operates via `/sb <op>` commands in Claude Code or via the Telegram bot.

## Capability / domain
- Personal knowledge capture (research, articles, YouTube, notes, LINE/FB content)
- Typed knowledge graph (entities, concepts, comparisons, queries)
- People CRM (named + anonymous encounters, scheduled meetings, follow-ups)
- Rebuildable hybrid retrieval (SQLite FTS5 trigram + Gemini embeddings for changed structured content)
- Session audit (reads `~/.claude/projects/**/*.jsonl` — the only op that goes outside the vault)
- Obsidian-compatible (vault registered, viewable in Obsidian app, no write dependencies)

## Consult this project when
- Need to capture something into the brain (URL, text, file, screenshot)
- Need to find/synthesize from prior research (ASK)
- Need to log a meeting/encounter with a person (PERSON, APPOINTMENT, ENCOUNTER)
- Need to list upcoming meetings or open follow-ups
- Need a self-audit of recent Claude Code sessions (AUDIT)

## Primary source-of-truth files
- `/home/time/second-brain/CLAUDE.md` — operating manual (folder contract, routing table, op procedures)
- `/home/time/second-brain/SCHEMA.md` — taxonomy + routing rules (read before writing any knowledge node)
- `/home/time/second-brain/.claude/memory/SESSION.md` — current state + next steps
- `/home/time/second-brain/.claude/memory/GUARDRAILS.md` — vault-specific gotchas

## Important guardrails
- G-001: `/watch` needs `WATCH_VAULT_DIR=/home/time/second-brain` set in `~/.claude/settings.json` (else ingest gate never fires)
- G-002: SDD plans >5 tasks → checkpoint with `/save-progress` before starting
- G-003: write helpers that take target dir must `mkdir -p` defensively; write tests must assert path-prefix not just content
- G-004: spec-driven plans need a final whole-branch review (per-task reviews miss integration gaps)

## Integration entrypoints
- `cd /home/time/second-brain && /project-memory` (load brief)
- `cd /home/time/second-brain && /close-session` (finalize handoff)

## Discovery keywords / tags
knowledge-vault, karpathy-llm-wiki, obsidian, personal-knowledge, crm, journal, bash, sdd, thai, second-brain
