# Second Brain system package

Exported: 2026-09-17

This package contains the reusable Second Brain system without the owner's
knowledge, captures, contacts, journal, generated index, or credentials.

## Included

- `skills/sb/` — short `/sb` router.
- `skills/second-brain/` — main skill and operation router.
- `skills/second-brain-audit/` — state-vs-event audit skill and scanner.
- `vault-template/CLAUDE.md` — complete operating manual.
- `vault-template/SCHEMA.md` — typed knowledge taxonomy and routing rules.
- `vault-template/bin/` — commit/index/CRM helpers and hybrid search engine.
- `vault-template/tests/` — offline Gemini/FTS tests, shell tests, fixtures, and E2E smoke test.
- `vault-template/docs/` — design, PRD, architecture, implementation plans, reviews, and procedures.
- `vault-template/.claude/`, `.codex/`, `.obsidian/`, `.superpowers/` — reusable project configuration and implementation records. Live session/snapshot and Obsidian workspace state are intentionally excluded.
- Empty vault data directories so the extracted tree has the full architecture.

## Gemini embedding architecture

`vault-template/bin/sb-search.py` is Python stdlib only. It uses:

- Markdown as the source of truth.
- Rebuildable SQLite FTS5 sidecar at `.sb/search.db`.
- Gemini REST API directly, without an SDK.
- Model `gemini-embedding-2`, 768 dimensions.
- `RETRIEVAL_DOCUMENT` for structured notes and `RETRIEVAL_QUERY` for searches.
- `batchEmbedContents` for documents and `embedContent` for queries.
- Content-hash incremental embedding, identical-content reuse, query cache, pending/retry state, lexical fallback, cosine ranking, and Reciprocal Rank Fusion.
- Raw captures remain lexical-only; structured folders receive embeddings.
- Gemini/network/quota failure never blocks durable Markdown capture.

Read these first:

1. `vault-template/CLAUDE.md`
2. `vault-template/SCHEMA.md`
3. `vault-template/docs/architecture/level7-hybrid-retrieval.md`
4. `vault-template/docs/level7-hybrid-retrieval.prd.md`

## Setup

1. Copy `vault-template/` to the desired vault path.
2. Copy `.env.example` to `<vault>/.env`, add a Gemini API key, and run `chmod 600 <vault>/.env`.
3. Set `SECOND_BRAIN_DIR=<vault path>` when the vault is not `~/.second-brain`, or pass `--vault <path>` and `--db <path>` to `sb-search.py`.
4. Copy or symlink the three folders under `skills/` into the agent's skills directory.
5. Run the checks below from the vault root.

```bash
python3 -m py_compile bin/sb-search.py tests/test-sb-search.py
python3 tests/test-sb-search.py
for test_file in tests/test-*.sh; do bash "$test_file" || exit 1; done
python3 bin/sb-search.py reindex --best-effort
python3 bin/sb-search.py status
```

## Deliberately excluded

- `.env` and every API key or credential.
- `.git` history because the vault history contains private knowledge.
- `.sb/search.db`, locks, caches, bytecode, and other rebuildable runtime state.
- `raw/`, `inbox/`, `entities/`, `concepts/`, `comparisons/`, `queries/`, `Magic/`, `people/`, `journal/`, `log/`, `audit/`, and `output/` contents.
- Generated `index.md`, live project-memory session/snapshot, and Obsidian `workspace.json`.

The empty directory structure is included; only private contents are omitted.
