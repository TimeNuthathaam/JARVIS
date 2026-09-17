# GUARDRAILS — ทะเบียนกับดักของ vault นี้ (อย่าพลาดซ้ำ)

> append ผ่าน /close-session หรือเมื่อเจอบทเรียนราคาแพง — เรียงใหม่ไปเก่า
> รูปแบบ: ### G-<n>: ชื่อ → อาการ / สาเหตุ / วิธีที่ถูก / กฎ

## กฎยืนพื้นของ vault
- ทุก write op จบด้วย `bin/sb-commit.sh` เท่านั้น — ห้าม `git commit` ตรง (flock + log)
- `raw/*.md` immutable — แตะได้เฉพาะ `status:` frontmatter
- `index.md` derived — regenerate ด้วย `bin/sb-index.sh` ห้ามแก้มือ
- เขียน knowledge node → อ่าน `SCHEMA.md` ก่อนเสมอ + **search-then-update, create-last**
- **ห้าม** `/graphify --obsidian-dir` ชี้เข้า vault นี้ (มันเขียน vault ของมันทับโครงสร้าง typed เรา)
- ความรู้เท่านั้นที่เข้า vault — session state อยู่ `.claude/memory/` ของแต่ละโปรเจกต์

## กับดักที่เจอแล้ว (registry)

### G-001: /watch ingest gate ไม่เคยเจอ vault นี้เลยตั้งแต่สร้าง
- อาการ: ดูคลิปด้วย /watch แล้วไม่เคยมีข้อเสนอ ingest เข้า vault — เงียบหาย
- สาเหตุ: /watch หา vault ที่ `$WATCH_VAULT_DIR` → `~/Second brain` → `~/Documents/Obsidian` → `~/Obsidian` — ไม่มีตัวไหนชี้มาที่ `/home/time/second-brain` และ env var ไม่เคยถูกตั้ง
- วิธีที่ถูก: ตั้ง `WATCH_VAULT_DIR=/home/time/second-brain` ใน `~/.claude/settings.json` → `env` (ทำแล้ว 2026-07-08 — มีผล session ใหม่เป็นต้นไป)
- กฎ: **skill ที่พึ่ง env var = ตรวจว่า env ถูกตั้งจริงในวันติดตั้ง ไม่ใช่วันที่สงสัยว่าทำไมไม่ทำงาน**

### G-002: SDD 7-task plan ใช้ token budget จนเหลือ 20% ที่ Task 6 (opus tier, งานที่ต้อง review หนัก)
- อาการ: รัน subagent-driven-development กับแผน 7 tasks (5 helpers + CLAUDE.md + e2e) — หลัง Task 6 คอนเท็กซ์เหลือ ~20% ทั้งที่ subagent tasks ทำเสร็จดีทุกตัว, reviewer per task หลายรอบ (Task 3 มี fix+re-review)
- สาเหตุ: (a) คอนเท็กซ์หลักโตเร็วเพราะแต่ละ task ต้องเก็บ brief + report + review + fix message ในหน่วยความจำหลักระหว่าง dispatch (b) Task 6 เป็น CLAUDE.md rewrite ขนาดใหญ่ที่ implementer ใช้ token เยอะในการวิเคราะห์ file ทั้ง vault ก่อนเขียน
- วิธีที่ถูก: **แบ่งแผน 7 tasks เป็น 2 SDD session** — รอบแรก 4-5 tasks (ที่ไม่ต้องแก้ CLAUDE.md) ปิด session, save-progress; รอบสอง CLAUDE.md-extensions + e2e; หรือ: ใช้ cheap-tier model (haiku) สำหรับ implementer + reviewer ของ mechanical tasks (helpers + tests), opus tier เฉพาะ Task 6+7+final-review
- กฎ: **แผน SDD >5 tasks ให้วาง checkpoint /save-progress ไว้ก่อนเริ่ม — ไม่ใช่หลังเหลือน้อย**

### G-003: helper arg-parsing silently falls through to default vault path เมื่อ target dir ไม่มี
- อาการ: `sb-encounter-anon.sh` รับ trailing `[journal_dir]` arg แต่ถ้า dir ไม่มี → `[ -d "${!#}" ]` false → fallthrough ไป default `$VAULT/journal` (real vault!) — e2e test step 8 leak `journal/2026-07-08-1917.md` เข้า real journal/ ทั้งที่ test "passed" (เพราะ test assert แค่ `[ -f "$file" ]` ไม่ได้ assert path)
- สาเหตุ: pattern `if [ -d "${!#}" ]; then ... fi; [ -z "$dir" ] && dir="$VAULT/<default>"` ที่ใช้ในทุก helper — เงียบเสียงไม่ error เมื่อ dir ไม่อยู่ และ test ไม่ assert path = silent leak
- วิธีที่ถูก: **(a) helper: `mkdir -p` target dir ก่อนเขียน** (defensive — same line as default fallthrough) เพื่อให้ test/CLI caller ไม่ต้องจำ mkdir เอง **(b) test: assert file path อยู่ใน fixture** (`[[ "$out3" == "$FIX"* ]]`) ไม่ใช่แค่ `assert_contains` content — เพราะ write-to-wrong-dir ผ่าน `assert_contains` ได้สบาย
- กฎ: **write helper ที่รับ target dir = `mkdir -p` ก่อนเขียนเสมอ; write test = assert path-prefix ไม่ใช่แค่ content**
- **FIXED 2026-07-08** (cherry-pick session):
  - `sb-encounter-anon.sh` — already had `mkdir -p` ✓ (F-1 original fix)
  - `sb-people-update.sh` — **was broken** → เปลี่ยน detection เป็น `[[ "$last" == */* ]]` (looks-like-path) + `mkdir -p` ใน `ensure` action; test ใหม่ 3 assertions covers "ensure with non-existent nested dir" → 49/49 green
  - **Helper อื่นๆ ที่รับ trailing-dir arg ต้องตรวจ pattern เดียวกัน** ก่อนเพิ่ม (sb-this-week.sh, sb-follow-up.sh ฯลฯ — ตอนนี้ไม่รับ dir arg, OK; แต่ถ้าจะเพิ่ม → apply pattern)

### G-004: per-task reviews ทุกตัวสะอาด แต่ whole-branch review เจอ HIGH finding ที่ทุก task พลาด
- อาการ: People CRM plan 7 tasks × per-task reviewer = ทุก task review clean → แต่ final whole-branch review (NEEDS-FIXES) เจอ F-1 HIGH (anonymous encounter fallback ไม่มี helper ไม่มี test — spec acceptance test #4) ที่ไม่เคยถูก flag ใน review ใดๆ
- สาเหตุ: per-task review optimize for "task implementation matches its brief" — ไม่ได้ optimize for "spec coverage matrix" หรือ "spec acceptance scenarios"; brief เองก็ไม่ครอบคลุม anonymous path เพราะ plan แยก task ตาม script ไม่แยกตาม spec scenario
- วิธีที่ถูก: **ก่อน declare plan "shipped" ต้องมี final whole-branch review ที่ (a) อ่าน spec section-by-section แล้วเช็ค coverage matrix (b) ไล่ acceptance test scenarios ทีละข้อ (c) cross-check CLAUDE.md routing table กับ scripts จริง** — per-task reviews ไม่ทำสิ่งนี้
- กฎ: **แผน SDD ที่มี spec → ก่อน ship ต้องมี final review แบบ spec-coverage ไม่ใช่แค่ per-task review**

