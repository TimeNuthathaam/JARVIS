# PROJECT — second-brain

> "ตัวตน" ของ vault นี้ — เปลี่ยนแทบไม่เคยเปลี่ยน อ่านไฟล์เดียวจบ

## One-liner
Personal knowledge vault (Karpathy LLM-wiki) — Markdown-first `/sb` ops with a rebuildable SQLite FTS5 + Gemini retrieval sidecar.

## เป้าหมาย / Goal
- Capture research/articles/encounters/notes ได้เร็วที่สุด (URL → ใน brain ภายใน 1 command)
- Knowledge compound — node เดียวถูกอ้างจากหลาย raw, search-then-update แทน duplication
- People CRM + journal built-in — ไม่ต้องไป Notion/CRM อื่น
- Obsidian-compatible (view-only) — อ่าน/กราฟใน Obsidian ได้ แต่ทุก op วิ่งผ่าน Claude Code
- Markdown + git เป็น source of truth; `.sb/search.db` เป็น derived index และ Gemini ใช้เฉพาะ changed structured chunks

## Tech stack
- Language: Bash 5.x + Python 3 stdlib (`sb-search.py`)
- Storage: git + markdown authority; SQLite FTS5 + embedding BLOBs เป็น derived state
- Retrieval: hybrid FTS5 trigram + Gemini `gemini-embedding-2` 768d, FTS fallback
- View layer: Obsidian (optional, vault id `33eb7929fd0b9b52` registered 2026-07-08)
- Concurrency: `flock` บน `.sb.lock` (one writer at a time)
- Optional external service: Gemini Embeddings API via local gitignored `.env`; FTS5 remains available without it

## คำสั่งสำคัญ / Key commands
| ทำอะไร | คำสั่ง |
| :-- | :-- |
| Capture anything | `/sb <URL\|text\|file>` → INGEST |
| Process raw → nodes | `/sb process [file]` |
| Ask from vault | `/sb ask <question>` |
| Person CRM | `/sb person <name>` / `/sb นัด <story>` / `/sb เจอ <story>` |
| Upcoming meetings | `/sb this week` |
| Open follow-ups | `/sb follow-up` |
| Close meeting | `/sb done <slug>` / `/sb cancel <slug>` |
| Status | `/sb status` |
| Self-audit sessions | `/sb audit [N\|--project]` |
| Reindex | `bin/sb-index.sh` |
| Hybrid search | `bin/sb-search.py search "<q>"` |
| Rebuild search sidecar | `bin/sb-search.py reindex --best-effort` |
| **Write gate (THE only commit path)** | `bin/sb-commit.sh "<op>: <msg>"` |
| Load brief | `/project-memory` |
| Checkpoint | `/save-progress` |
| Close session | `/close-session` |

## Entry points / ไฟล์เริ่มต้น
- `CLAUDE.md` — operating manual (folder contract, routing table, op procedures) — **อ่านไฟล์นี้ก่อนเสมอ**
- `SCHEMA.md` — taxonomy 4 ลิ้นชัก + routing rules — **อ่านก่อนเขียน knowledge node ทุกครั้ง**
- `bin/sb-commit.sh` — THE write gate (flock + log append + git commit)
- `bin/sb-index.sh` — regenerate `index.md`
- `bin/sb-search.py` — sync/search/status/reindex/benchmark derived hybrid index
- `bin/sb-{encounter-detect,encounter-anon,people-update,this-week,follow-up,upcoming}.sh` — People CRM ops
- `bin/lib-frontmatter.sh` — fm_get/fm_set/fm_has single source of truth (โดนทุก node)
- `.claude/memory/SESSION.md` — current state + next steps (re-injected ทุก session)
- `.claude/memory/GUARDRAILS.md` — vault-specific gotchas (G-001..G-004)
- `docs/superpowers/{specs,plans}/` — design specs + implementation plans (per SDD cycle)
- `.superpowers/sdd/` — SDD ledger (progress + per-task brief/report/review)

## กติกาของโปรเจกต์ / Conventions
- **ภาษา**: knowledge nodes + journal + people notes เป็นภาษาไทย, ศัพท์เทคนิคอังกฤษคงไว้, quote ต้นฉบับตามภาษาเดิม
- **ชื่อไฟล์**: kebab-case อังกฤษ เสมอ (`humanoid-robots-2026.md`)
- **Search-then-update, create-last** — grep aliases + node bodies ก่อนสร้างใหม่; on overlap extend existing node
- **raw/ immutable** — แตะได้เฉพาะ `status:` frontmatter
- **ทุก write จบที่ `bin/sb-commit.sh`** — ห้าม `git commit` ตรง (bypass flock + log)
- **ทุก op idempotent** — check `status:` ก่อน process
- **ทุก helper ต้องมี test** ใน `tests/` (bash test suite)
- **aliases: REQUIRED** ใน frontmatter (Thai + English synonyms) — นี่คือสิ่งที่ทำให้ search เจอ

## โปรเจกต์ที่เกี่ยวข้อง / Cross-project links
- `/home/time/Downloads/2ndBrain/` (NEOKNOWLEDGE) — separate Neo4j + NotebookLM RAG system, multi-tenant, ใช้สำหรับงาน structured knowledge ที่ต้อง graph query — **ไม่ merge** กับ vault นี้ (ต่าง paradigm: fast personal capture vs heavy graph)
- `~/.claude/skills/second-brain/` — skill ที่ ClaudeClaw Telegram bot เรียกใช้ ops เดียวกัน
- `~/.claude/skills/watch/` — video ingestion skill (ต้องตั้ง `WATCH_VAULT_DIR` → vault นี้)
