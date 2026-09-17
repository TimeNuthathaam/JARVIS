# Code review: Level 7 hybrid retrieval

วันที่: 2026-08-15

## Scope

- SQLite FTS5 index สำหรับข้อความทั้งหมดที่อนุญาต
- Gemini embeddings สำหรับ structured knowledge เท่านั้น
- Hybrid ranking ด้วย reciprocal rank fusion
- Incremental sync จาก `sb-commit.sh`
- Offline tests, real-vault benchmark และ secret hygiene

## Findings and resolutions

1. การ rename อาจเรียก embedding ซ้ำโดยไม่จำเป็น — แก้ด้วยการ reuse vector จาก `content_hash` เดิม
2. sync ที่ไม่มีเนื้อหาเปลี่ยนยังแตะ FTS metadata — แก้เป็น no-op และจำกัด FTS trigger เฉพาะ searchable columns
3. เอกสาร project memory ยังระบุ Bash-only/no API — ปรับให้ตรงกับ Python stdlib + optional Gemini
4. architecture map อ้างชื่อ test เก่า — ปรับเป็น test ที่มีอยู่จริง

## Result

ไม่พบ finding ที่ยังเปิดอยู่ใน scope นี้ ระบบล้มกลับไปใช้ FTS5 ได้เมื่อ Gemini ใช้งานไม่ได้ และไม่ทำให้ commit ล้มเหลว
