# Procedure — People CRM Real Usage

> ใช้เมื่อ: ต้องการ log คน/นัด/เจอจริง หลังจาก People CRM plan ship (2026-07-08)
> ต้องอ่าน: `CLAUDE.md` (routing table) — `/sb` ทุกคำสั่งเป็น op ที่มี routing ชัดเจน
> ตัวช่วยทั้งหมด: `bin/sb-{encounter-detect,encounter-anon,people-update,this-week,follow-up}.sh` (verified e2e ด้วย dummy data 2026-07-08 — dummy นั้นลบไปแล้ว)

---

## Quick reference (copy-paste)

| ต้องการ | คำสั่ง | ผลลัพธ์ |
|---|---|---|
| นัดคนใหม่ | `/sb นัด <name> <วันเวลา> <สถานที่> <agenda>` | สร้าง `people/<slug>.md` + ตั้ง `next_meeting_at` |
| นัดคนเดิม | `/sb นัด <name> <วันเวลาใหม่> ...` | อัปเดต `next_meeting_at` (met_last auto-bump) |
| เจอคนรู้จัก | `/sb เจอ <name> <เรื่องที่คุย>` | append bullet ใต้ `## Notes` ของ person file |
| เจอคนไม่รู้จัก | `/sb เจอ <descriptor: takeaway>` | append bullet ใต้ `## People seen (unnamed)` ของ journal วันนี้ |
| ดูนัดสัปดาห์นี้ | `/sb this week` | list meetings ใน 7 วันข้างหน้า |
| ดู follow-up ค้าง | `/sb follow-up` | list open `- [ ]` ทุกคน เรียง due date |
| ปิดนัด (เสร็จ) | `/sb done <slug>` | flip `meeting_status: done` + ถามให้ใส่สรุปสั้นๆ → append `## Notes` |
| ยกเลิกนัด | `/sb cancel <slug>` | flip `meeting_status: cancelled` + ถาม reason → append `## Notes` |

`<slug>` = ชื่อคนในรูป kebab-case อังกฤษ (เช่น `beer`, `john-doe`) — agent route จากชื่อไทย/นามแฝงด้วย `aliases`

---

## 1. `/sb นัด` — scheduled meeting

**Story format** (agent จะ parse): `นัด <name> <วันเวลา> <สถานที่> <agenda>`

**ตัวอย่าง:**

```
/sb นัด beer พฤหัสนี้ 14:00 ที่ร้าน XYZ demo สินค้า
```

**Agent จะทำ:**
1. `echo "..." | bin/sb-encounter-detect.sh` → ควรได้ `appointment` (มีคำว่า "นัด" + เวลา + พรุ่งนี้/วัน...)
2. `bin/sb-people-update.sh <slug> ensure` → สร้าง `people/<slug>.md` ถ้ายังไม่มี
3. `set next_meeting_at "<ISO datetime Bangkok>"` + `set meeting_location "..."` + `set meeting_agenda "..."` + `set meeting_status scheduled`
4. `bin/sb-commit.sh "appointment: <slug> <ISO>"` (write gate — flock + log + commit)

**ISO datetime format:** `YYYY-MM-DDTHH:MM:SS+0700` (Bangkok = UTC+7)
- ตัวอย่าง: `2026-07-09T14:00:00+0700`
- ถ้าคุณพิมพ์ "พรุ่งนี้ 14:00" agent จะ translate เป็น ISO ให้

**Conflict check (manual):** ถ้า person มี `next_meeting_at` เดิมอยู่แล้ว agent **ไม่** detect conflict อัตโนมัติ — agent จะหยุดถามก่อนเขียนทับ

**Verify หลังเสร็จ:**
```
/sb this week
```
ต้องเห็นนัดใหม่ในรายการ

---

## 2. `/sb เจอ` (named) — encounter with known person

**Story format:** `เจอ <name> <เรื่องที่คุย>`

**ตัวอย่าง:**

```
/sb เจอ beer คุยเรื่อง spec ใหม่ 15 นาที เขาสนใจ feature X
```

**Agent จะทำ:**
1. `bin/sb-encounter-detect.sh` → `encounter` (ไม่มีเวลา)
2. `bin/sb-people-update.sh <slug> ensure` (ถ้ายังไม่มี)
3. `add-note <today> "<bullet>"` → append `- <date>: <bullet>` ใต้ `## Notes` ของ person file
4. `bin/sb-commit.sh "encounter: <slug>"`

**Verify หลังเสร็จ:**
```
cat people/<slug>.md
```
ดู `## Notes` section — bullet ใหม่อยู่บนสุด (sort: ใหม่สุดบน)

---

## 3. `/sb เจอ` (anonymous) — encounter ไม่รู้ชื่อ

**Story format:** `เจอ <descriptor>: <takeaway>` (มี colon หรือ description ที่ไม่ match เป็นชื่อคน)

**ตัวอย่าง:**

```
/sb เจอ ชายเสื้อแดงที่งาน Depry: เล่าเรื่อง X สนใจ Y
```

**Agent จะทำ:**
1. `bin/sb-encounter-detect.sh` → `encounter` (heuristic)
2. Detect ไม่มีชื่อ → route ไป anonymous helper
3. `bin/sb-encounter-anon.sh "<bullet>"` → สร้าง `journal/YYYY-MM-DD-HHMM.md` พร้อม `## People seen (unnamed)` section
4. ถ้าเรียกอีกในนาทีเดียวกัน → append bullet เดียวกับไฟล์ (per-minute idempotency)
5. `bin/sb-commit.sh "encounter-anon: <ISO date>"`

**Verify หลังเสร็จ:**
```
cat journal/$(date +%Y-%m-%d-%H%M).md
```
ดู `## People seen (unnamed)` — ต้องมี bullet ใหม่

---

## 4. `/sb this week` — query

```
/sb this week
```

**Output format:**
```
📅 สัปดาห์นี้คุณมีนัด N อย่าง:

1. <Thai day> <date> <time> — <person name> (<location>)
   └─ <agenda>

/sb done <slug> เมื่อเสร็จแล้ว
```

Empty case: `📅 สัปดาห์นี้ไม่มีนัดหมาย`

**Filter:** `meeting_status: scheduled` (หรือ absent) + `next_meeting_at` ใน [today, today+7]

---

## 5. `/sb follow-up` — query

```
/sb follow-up
```

**Output format:** open `- [ ]` items จาก `## Follow-ups` ของทุกคน เรียง `due` ASC, items ไม่มี due ไปท้าย

```
📋 open follow-ups (N):

1. 2026-07-20 — beer: ส่ง slide deck
2. 2026-07-25 — john: confirm meeting
3. (no due) — alice: review proposal
```

---

## 6. `/sb done <slug>` / `/sb cancel <slug>`

**Format:** `/sb done beer` หรือ `/sb cancel beer`

**Agent จะ:**
1. flip `meeting_status: done` (หรือ `cancelled`)
2. update `met_last` (auto-bump เมื่อ done — cancelled ไม่ bump)
3. ถามให้ใส่ short summary → append bullet ใต้ `## Notes`
4. `bin/sb-commit.sh "appointment-close: <slug> <status>"`

**Cancel special:** จะถาม "เหตุผลที่ยกเลิก" — เก็บใน Notes เพื่อ trace

---

## Edge cases (อ่านก่อนเรียกครั้งแรก)

- **First-time person** → agent สร้าง file ใหม่ พร้อม frontmatter `name`, `aliases: []`, `met_first`, `met_last`, `updated`, sections `## Notes` + `## Follow-ups`
- **Alias match** → agent resolve slug จาก `aliases:` array ใน frontmatter — ถ้าคุณรู้จักคนนี้หลายชื่อ บอก agent ให้ update aliases ได้
- **Multiple meetings** → `set next_meeting_at` ทับของเดิม — agent จะถามก่อนถ้า conflict
- **Past date** → `next_meeting_at` ในอดีต → agent จะถาม "ตั้งนัดย้อนหลัง หรือ close เป็น done?"
- **No name detect** → ถ้า story ambiguous (เช่น "นัด พบ พรุ่งนี้" ไม่มีชื่อ) → agent จะถาม 1 คำถามก่อน route

---

## Sanity check (รันก่อนใช้งานจริง ถ้าอยากมั่นใจ)

```bash
# Test 1: routing
echo "นัด beer พรุ่งนี้ 14:00" | bin/sb-encounter-detect.sh
# expected: appointment

# Test 2: full test suite
for t in tests/test-*.sh; do bash "$t" >/dev/null; echo "$t: exit=$?"; done
# expected: all exit=0
```

---

_อัปเดตล่าสุด: 8 ก.ค. 2026 · เขียนหลัง People CRM e2e verified + G-003 cherry-pick landed_
