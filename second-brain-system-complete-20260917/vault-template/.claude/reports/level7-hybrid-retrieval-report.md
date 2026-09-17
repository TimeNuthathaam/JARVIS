# Implementation report: Level 7 hybrid retrieval

วันที่: 2026-08-15

## Delivered

- `bin/sb-search.py`: `sync`, `reindex`, `search`, `status`, `benchmark`
- SQLite FTS5 + Gemini `gemini-embedding-2` ขนาด 768 dimensions
- Hybrid retrieval แบบ FTS + semantic ด้วย RRF
- query cache, changed-only embedding และ vector reuse ตาม content hash
- processed `raw/*.md` เป็น lexical-only น้ำหนักต่ำ; structured folders ใช้ทั้งสอง channel
- best-effort index update หลัง `sb-index.sh` ภายใน `sb-commit.sh`
- `.env` local-only, gitignored และ permission 600

## Validation

- Python tests: 7/7 ผ่าน
- Bash test scripts: 7/7 ผ่าน
- Python compile, shell syntax, diff check และ secret scan ผ่าน
- Real vault: 319 documents, 379 chunks, 241 embedded, 138 lexical-only, pending 0
- Thai benchmark Top-5: FTS 65%, hybrid 95% (เกณฑ์ 90%)

## Deliberate limits

- ใช้ SQLite และ brute-force cosine search เพราะขนาด vault ปัจจุบันเล็ก
- ไม่มี login, permissions, Postgres, scheduler หรือ vector extension ตาม scope ที่ยืนยัน
