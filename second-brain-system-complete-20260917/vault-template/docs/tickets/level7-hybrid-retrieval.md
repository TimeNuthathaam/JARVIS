# Ticket Breakdown — Level 7 Hybrid Retrieval

## Epic summary

เพิ่ม derived hybrid retrieval ให้ `/sb` โดยคง Markdown-first architecture และ write safety เดิม พร้อม Gemini cost controls และ benchmark ภาษาไทย

## Tickets

### SB-L7-1 — Build deterministic local index and FTS search

- Acceptance: scan scope ถูกต้อง, metadata/content hash อยู่ใน SQLite, Thai trigram search คืน node ที่คาด, deleted/changed files sync แบบ idempotent
- Context: PRD success metrics; architecture data model/source-of-truth/failure contract
- Files: `bin/sb-search.py`, `tests/test-sb-search.py`, `.gitignore`
- Depends on: none

### SB-L7-2 — Add Gemini semantic retrieval and hybrid ranking

- Acceptance: changed structured chunks embed เท่านั้น, raw ไม่ embed, query cache ทำงาน, API failure เหลือ pending และ FTS fallback, RRF ลดน้ำหนัก raw
- Context: architecture embedding/scope/sync decisions; official Gemini embeddings API
- Files: same vertical slice in `bin/sb-search.py` + tests
- Depends on: SB-L7-1

### SB-L7-3 — Integrate `/sb`, benchmark and operational checks

- Acceptance: `sb-commit` sync โดยไม่ถูก API block, manual ระบุ ASK/SEARCH/REINDEX/STATUS, benchmark 20 query ตรวจ Top-5 ≥90%, full suite green
- Context: CLAUDE.md folder/write contracts; `bin/sb-commit.sh`; PRD metrics
- Files: `bin/sb-commit.sh`, `CLAUDE.md`, benchmark fixture, integration tests, reports
- Depends on: SB-L7-2

## Dependency graph

`SB-L7-1 → SB-L7-2 → SB-L7-3`

## Suggested execution order

ทำเป็นหนึ่ง PIV loop ตามลำดับ เพราะทั้งสาม slice แตะ core indexer และ ticket ถัดไปต้องพิสูจน์ behavior ของ ticket ก่อนหน้า ไม่สร้าง worktree ขนาน

