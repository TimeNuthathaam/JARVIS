# Feature: Level 7 Hybrid Retrieval

## Feature Description

เพิ่ม SQLite sidecar ที่ index Markdown เป็น content + metadata + optional Gemini embeddings และให้ `/sb ask` ใช้ hybrid lexical/semantic retrieval พร้อม fallback และ benchmark ภาษาไทย

## User Story

As a เจ้าของ second brain
I want to ถามความรู้ด้วยภาษาธรรมชาติและคำพ้อง
So that AI พบ context ที่ถูกต้องโดยไม่ต้องจำชื่อไฟล์หรือใช้คำตรง

## Problem Statement

ASK ปัจจุบันอาศัย grep หลาย variant ซึ่งขึ้นกับการเดาคำค้นของ agent และไม่มี persisted ranking/index เมื่อ vault โตขึ้น

## Solution Statement

สร้าง derived SQLite index ด้วย FTS5 trigram, Gemini vectors เฉพาะ structured content, incremental hash/cache และ RRF hybrid ranker; เชื่อม sync เข้ากับ write gate แบบ Gemini best-effort

## Out of Scope / Non-Goals

- Not included: Postgres/pgvector, login/permissions, scheduler, frontend, MCP server
- Not changing: Markdown taxonomy, raw immutability, `sb-commit.sh` เป็น write gate, ASK write-back policy
- Not embedding: flat `raw/*.md`; ใช้ FTS น้ำหนักต่ำเท่านั้น

## Feature Metadata

**Feature Type**: New Capability  
**Estimated Complexity**: Medium  
**Primary Systems Affected**: `/sb` ASK, commit finisher, derived search state, tests  
**Dependencies**: SQLite FTS5 + Gemini REST API; no new package

## Related Work

**Implements**: `docs/level7-hybrid-retrieval.prd.md`  
**Architecture**: `docs/architecture/level7-hybrid-retrieval.md`  
**Tickets**: `docs/tickets/level7-hybrid-retrieval.md`

## CONTEXT REFERENCES

### Relevant Codebase Files

- `CLAUDE.md` — routing, ASK, STATUS และ write contracts
- `SCHEMA.md` — typed folders และ frontmatter rules
- `bin/sb-commit.sh` — serialized write gate; sync ต้องอยู่ภายใน lock และไม่ block เมื่อ Gemini fail
- `bin/sb-index.sh` — pattern ของ derived rebuild
- `bin/lib-frontmatter.sh` — frontmatter behavior ที่ parser ใหม่ต้องเทียบเคียง
- `tests/helpers.sh` และ `tests/test-e2e-smoke.sh` — test style + isolated fixtures
- `.claude/memory/ARCHITECTURE.md` — architecture map ที่ต้อง drift-check หลังเพิ่ม helper

### New Files to Create

- `bin/sb-search.py` — schema, sync, Gemini client, FTS/vector/hybrid search, status, benchmark CLI
- `tests/test-sb-search.py` — unittest แบบ offline พร้อม fake embeddings/API failure
- `tests/fixtures/hybrid-search-benchmark.json` — 20 real queries + expected node paths
- `.claude/reports/level7-hybrid-retrieval-report.md` — implementation report
- `.claude/execution-reports/level7-hybrid-retrieval.md` — execution reflection
- `.claude/system-reviews/level7-hybrid-retrieval-review.md` — process review

### Relevant Documentation

- https://ai.google.dev/gemini-api/docs/embeddings — task types, dimensions, normalization
- https://ai.google.dev/api/embeddings — REST request/response shapes
- https://www.sqlite.org/fts5.html — FTS5 trigram tokenizer and BM25

### Patterns to Follow

- Absolute vault path defaults; testable override via CLI `--vault`
- Derived files are gitignored and rebuildable
- Helpers return non-zero on local correctness errors; remote embedding errors are visible but best-effort when called by commit
- One runnable test file for the new non-trivial module; existing suite remains standalone

## IMPLEMENTATION PLAN

### Phase 1: Foundation

- Add secret/derived ignore rules and local `.env`
- Implement SQLite schema/versioning, frontmatter parsing, scope scan, chunking and idempotent FTS sync

### Phase 2: Core retrieval

- Implement Gemini batch document embeddings and cached query embeddings
- Implement FTS5, cosine semantic ranking and weighted RRF hybrid results
- Preserve pending state and FTS fallback on all remote failures

### Phase 3: Integration

- Wire best-effort sync into `sb-commit.sh`
- Extend `/sb` manual for ASK, SEARCH, REINDEX and STATUS
- Update architecture memory minimally where path map changed

### Phase 4: Testing & Validation

- Offline unit/integration tests with fake client
- 20-query Thai/English benchmark using real vault + Gemini
- Run all Bash/Python tests, compile checks, link checks and secret scans

## STEP-BY-STEP TASKS

### UPDATE `.gitignore` and CREATE `.env`

- **IMPLEMENT:** ignore `.env`, `.sb/`; store provided key only in `.env` with mode 600
- **GOTCHA:** never expose key via diff, status, logs or tests
- **VALIDATE:** `git check-ignore -v .env .sb/search.db && test "$(stat -c %a .env)" = 600`
- **SATISFIES:** secret boundary, derived-state contract

### CREATE `bin/sb-search.py`

- **IMPLEMENT:** schema + sync + metadata + deterministic chunking + FTS5 trigram
- **IMPLEMENT:** Gemini REST batch/document/query embeddings at 768d, hash/query cache
- **IMPLEMENT:** FTS/vector/RRF search; raw penalty; JSON/human output; status/reindex/benchmark
- **GOTCHA:** no API call for unchanged chunks; API errors must not erase working embeddings or FTS
- **VALIDATE:** `python3 -m py_compile bin/sb-search.py`
- **SATISFIES:** all retrieval acceptance criteria

### CREATE `tests/test-sb-search.py`

- **IMPLEMENT:** Thai FTS, scope exclusion, raw lexical-only, incremental fake embedding, hybrid ranking, fallback, stale deletion
- **VALIDATE:** `python3 tests/test-sb-search.py`
- **SATISFIES:** deterministic regression coverage

### UPDATE `bin/sb-commit.sh`

- **IMPLEMENT:** run search sync after Markdown index rebuild while lock is held; Gemini best-effort
- **PATTERN:** preserve current raw/link validation ordering
- **VALIDATE:** existing suite + isolated commit smoke
- **SATISFIES:** automatic freshness without data-loss coupling

### UPDATE `CLAUDE.md` and `.claude/memory/ARCHITECTURE.md`

- **IMPLEMENT:** route `/sb search` and `/sb reindex`; ASK calls hybrid helper first and cites returned paths; status includes search health
- **GOTCHA:** keep rules lean; do not add permissions/scheduler/Postgres
- **VALIDATE:** `rg -n '/sb (search|reindex)|sb-search.py' CLAUDE.md .claude/memory/ARCHITECTURE.md`
- **SATISFIES:** usable `/sb` interface and accurate architecture map

### CREATE benchmark fixture and RUN benchmark

- **IMPLEMENT:** 20 real Thai/English/mixed queries with explicit expected paths
- **VALIDATE:** `python3 bin/sb-search.py benchmark tests/fixtures/hybrid-search-benchmark.json --limit 5`
- **SATISFIES:** Top-5 recall ≥90%, hybrid ≥ FTS

## TESTING STRATEGY

### Unit Tests

Temporary vault + SQLite DB; no network. Fake embedding client returns deterministic normalized vectors and counts calls.

### Integration Tests

Run CLI against real vault, initial sync and benchmark with `.env`; verify changed-only second sync creates zero document embeddings.

### Edge Cases

- empty/malformed frontmatter, Markdown without title, Thai unsegmented text
- missing/invalid key, HTTP timeout/quota/error response, invalid embedding dimension
- file deletion/rename, chunk-count shrink, raw status, repeated query cache
- database schema/model/dimension change forces safe re-embedding

## VALIDATION COMMANDS

1. `python3 -m py_compile bin/sb-search.py tests/test-sb-search.py`
2. `python3 tests/test-sb-search.py`
3. `for t in tests/test-*.sh; do bash "$t"; done`
4. `python3 bin/sb-search.py sync --best-effort`
5. `python3 bin/sb-search.py benchmark tests/fixtures/hybrid-search-benchmark.json --limit 5`
6. `git diff --check`
7. `git grep -n 'AQ\.Ab8' -- ':!.env'` must return no matches

## ACCEPTANCE CRITERIA

- [ ] Thai FTS5 and Gemini semantic retrieval combine into Top-5 hybrid results
- [ ] benchmark 20 queries reaches ≥90% and hybrid is not worse than FTS-only
- [ ] only changed structured chunks are embedded; raw never calls Gemini
- [ ] missing/down Gemini keeps FTS and commit operational with pending count visible
- [ ] SQLite state is rebuildable, gitignored and never becomes Markdown authority
- [ ] all existing/new tests pass and manual/rules docs match implementation
- [ ] secret is mode 600, ignored and absent from tracked diff/logs

## OPEN QUESTIONS / ASSUMPTIONS

- Assumed: direct Gemini REST API accepts the provided key after it is loaded from `.env`; failure is reportable but does not invalidate offline feature correctness
- Deferred by user: 1,536 dimensions only if 768 benchmark fails

## NOTES

`prime-frontend`, `ast-grep`, GitHub issue/PR, worktree, browser, AI Tutor and dark-factory skills have no executable target in this Bash/Markdown local vault or conflict with confirmed no-scheduler/no-remote scope. Their relevant guardrails (observable checks, protected secret, deterministic gates, fresh review) are inherited without creating unrelated infrastructure.

## AMENDMENTS

