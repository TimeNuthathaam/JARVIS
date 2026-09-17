# PRD — Level 7 Hybrid Retrieval for `/sb`

## Problem Statement

เจ้าของ vault ใช้ `/sb` คนเดียวและมี Markdown หลายร้อยไฟล์ที่ค้นด้วย `grep` และการไล่ `[[wikilinks]]` ได้ แต่ recall จะพลาดเมื่อคำถามใช้คำคนละชุดกับข้อความใน node และต้นทุนการอ่านเพิ่มตามขนาด vault หากปล่อยให้โตต่อไป AI จะต้องเดาว่าควรเปิดไฟล์ใดก่อน

## Evidence

- รายงาน *Every Level of AI Memory Explained* ระบุว่าเมื่อความรู้โต ปัญหาหลักเปลี่ยนจาก storage เป็น retrieval และเสนอให้ normalize ความรู้เป็น content + embedding + metadata
- vault มี structured notes 241 ไฟล์โดยประมาณ และ raw captures 96 ไฟล์; raw มีเนื้อหาประมาณ 78% ของ token ทั้งหมด จึงไม่ควรส่งทุกอย่างไปสร้าง embedding
- SQLite FTS5 ในเครื่องรองรับ `trigram` ซึ่งค้นข้อความภาษาไทยที่ไม่มี word boundary ได้
- ผู้ใช้ยืนยันว่าใช้งานส่วนตัว ไม่มี login/permissions และต้องการ Gemini embeddings แบบประหยัด

## Thesis

ถ้า `/sb` มี derived hybrid index ที่รวม lexical และ semantic retrieval โดย Markdown ยังเป็น source of truth ระบบจะ recall ภาษาไทยและคำพ้องได้แม่นขึ้นโดยไม่เพิ่มภาระดูแลฐานข้อมูลหรือเปลี่ยน workflow เดิม

## Hypothesis

เราเชื่อว่า hybrid retrieval จะทำให้เจ้าของ vault ถามด้วยภาษาไทย อังกฤษ หรือคำพ้องแล้วพบ node ที่ต้องการใน Top 5 ได้อย่างสม่ำเสมอ โดยยัง capture ความรู้ได้แม้ Gemini API ใช้งานไม่ได้

- **RIGHT:** benchmark 20 query จริงได้ Top-5 recall อย่างน้อย 90% และ full `/sb` test suite ผ่าน
- **WRONG:** hybrid ต่ำกว่า 90%, แย่กว่า FTS5 เดี่ยว หรือ API failure ทำให้ write/commit ล้ม

## Target User & JTBD

- Primary user: เจ้าของ `/home/time/second-brain` เพียงคนเดียว
- JTBD: เมื่อถาม `/sb` ด้วยภาษาธรรมชาติ ต้องการให้ระบบหยิบ context ที่เกี่ยวข้องพร้อม path/source เพื่อสังเคราะห์คำตอบโดยไม่ต้องจำชื่อไฟล์หรือคำตรง
- Non-users: ทีมหลายคน, public SaaS, ระบบที่ต้องมี tenant isolation หรือ role-based access

## MVP

หนึ่ง flow ตั้งแต่ Markdown → derived index → hybrid search → ranked results ที่ `/sb ask` ใช้ได้ พร้อม incremental reindex, API fallback และ benchmark ภาษาไทย

## Success Metrics

- Top-5 recall ≥90% บน benchmark 20 query ที่กำหนด expected node ไว้ล่วงหน้า
- hybrid recall ไม่ต่ำกว่า FTS5-only recall
- ไฟล์ที่ไม่เปลี่ยนไม่ถูกส่งไป embed ซ้ำ
- Gemini unavailable แล้ว FTS5 search และ `sb-commit.sh` ยังสำเร็จ
- test suite เดิมและใหม่ผ่านทั้งหมด

## Non-goals

- ไม่มี login, password, permission filtering หรือ multi-user tenancy
- ไม่มี Postgres, pgvector, vector-server หรือ cloud database
- ไม่มี scheduler/cron/timer ใหม่
- ไม่ embed `raw/`; raw ใช้ lexical retrieval น้ำหนักต่ำและตาม citation จาก structured node
- ไม่ index `output/`, `audit/`, `log/`, assets หรือ `.claude/`
- ไม่สร้าง frontend, MCP server, GitHub issue/PR หรือ dark factory

## Open Questions

- [ ] หลัง benchmark จริง 768 dimensions เพียงพอหรือควรทดลอง 1,536 ตาม decision rule

