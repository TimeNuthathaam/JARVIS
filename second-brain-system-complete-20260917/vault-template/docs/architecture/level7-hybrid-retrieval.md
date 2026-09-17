# Architecture — Level 7 Hybrid Retrieval for `/sb`

## Problem & goals

เพิ่ม retrieval layer ให้ vault ส่วนตัวค้นความรู้ตามคำและความหมายได้ดีขึ้น โดย Markdown และ write rules เดิมยังเป็น authority, การ capture ไม่ขึ้นกับ external API และค่า embedding เพิ่มเฉพาะเมื่อเนื้อหาเปลี่ยน

## Approaches considered

1. **Postgres + pgvector** — ตรงตัวอย่าง company brain แต่ต้องมี server, credentials และ lifecycle ที่ไม่สร้างคุณค่าให้ผู้ใช้คนเดียว
2. **SQLite FTS5 เท่านั้น** — เรียบง่ายและค้นไทยแบบ substring ได้ดี แต่ recall คำพ้อง/คำถามเชิงความหมายยังจำกัด
3. **SQLite FTS5 + Gemini embeddings** — sidecar เดียว, lexical fallback, semantic recall และไม่มี database service; เลือกแนวทางนี้

## Recommended approach

สร้าง derived SQLite sidecar จาก structured Markdown และ flat processed raw captures. FTS5 `trigram` index ครอบคลุมทุก scope; Gemini embeddings ครอบคลุม structured folders เท่านั้น. Search รวม lexical และ semantic rank ด้วย Reciprocal Rank Fusion (RRF), ลดน้ำหนัก raw และคืน path/title/excerpt/metadata ให้ agent ใช้ตอบพร้อม citation.

## Key decisions

- **Stack & libraries:** Python standard library (`sqlite3`, `urllib`, `hashlib`, `array`) และ Bash wrapper เดิม; เรียก Gemini REST โดยตรงเพื่อไม่เพิ่ม SDK dependency
- **Embedding model:** `gemini-embedding-2`, 768 dimensions; document ใช้ `RETRIEVAL_DOCUMENT`, query ใช้ `RETRIEVAL_QUERY`; cache ทั้ง document และ repeated query ด้วย content hash
- **Data model:** หนึ่ง row ต่อ chunk มี content, path, ordinal, typed-folder metadata, content hash, embedding BLOB, model/dimension/status; FTS5 table ผูกกับ row เดียวกัน
- **Scope:** structured = `entities/ concepts/ comparisons/ queries/ people/ journal/`; raw = `/raw/*.md` แบบ lexical-only; ตัด derived/private operational folders
- **Source of truth:** database ลบแล้ว rebuild ได้; ไม่มี write-back จาก SQLite ไป Markdown
- **Failure contract:** local parse/SQLite error เป็น hard failure; Gemini/network/quota error เป็น pending embedding + warning และไม่ block `sb-commit`
- **Secrets:** `.env` local permission 600 และ gitignored; ไม่พิมพ์ secret ใน output/log/error
- **Sync:** `sb-commit.sh` sync local index และ attempt เฉพาะ pending/changed embeddings; `/sb reindex` ซ่อมย้อนหลัง; ไม่มี scheduler
- **Permissions:** ไม่ทำในรอบนี้ตามคำตัดสินผู้ใช้คนเดียว

## Missing pieces

- Derived database schema + migration/version guard
- Markdown/frontmatter parser และ deterministic chunker
- Gemini batch embedding client + retry-safe pending state
- FTS, vector cosine และ hybrid ranker
- `/sb` routing/manual updates, commit integration และ status/reindex commands
- Thai benchmark corpus + deterministic offline tests

## Spikes & experiments

- **Question:** 768 dimensions recall พอหรือไม่
- **Spike:** benchmark 20 Thai/English/mixed queries หลัง full index
- **Decision rule:** ใช้ 768 เมื่อ hybrid Top-5 recall ≥90% และไม่แย่กว่า FTS; ทดลอง 1,536 เฉพาะเมื่อไม่ผ่าน

## Open questions

- permissions, Postgres และ scheduled farming ถูกเลื่อนจนกว่าจะมีผู้ใช้หลายคนหรือ throughput ที่วัดได้

