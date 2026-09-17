# System evolution review: Level 7 hybrid retrieval

วันที่: 2026-08-15

## Alignment

ผลลัพธ์ตรงกับ scope ที่ยืนยัน: personal single-user, SQLite-first, hybrid retrieval, Gemini 768 dimensions, ไม่มี scheduler และ embeddings failure ไม่ขวางการเขียน vault

## Improvements learned during execution

- content hash ควรเป็น identity ของ embedding เพื่อเลี่ยงค่าใช้จ่ายเมื่อ rename หรือ rechunk แล้วข้อความซ้ำ
- FTS trigger ควรทำงานเฉพาะ searchable columns เพื่อให้ metadata-only sync เป็น no-op จริง
- benchmark แยก FTS กับ hybrid ทำให้เห็นคุณค่าของ semantic channel ชัดเจนกว่าใช้คะแนนรวมอย่างเดียว

## Next threshold

ค่อยพิจารณา 1,536 dimensions เมื่อ benchmark ต่ำกว่าเกณฑ์จากข้อมูลจริง และค่อยย้ายจาก brute-force/SQLite เมื่อ latency หรือขนาด corpus วัดได้ว่าเป็นปัญหา
