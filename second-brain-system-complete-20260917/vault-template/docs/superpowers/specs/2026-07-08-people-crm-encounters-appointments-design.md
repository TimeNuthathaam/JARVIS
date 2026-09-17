---
title: People CRM — Encounters & Appointments
date: 2026-07-08
status: draft
---

# People CRM — Encounters & Appointments

ขยาย `people/<slug>.md` ที่ออกแบบไว้แล้วใน vault ให้รองรับ 2 use case ที่ user เจอจริง:

1. **Appointment** — เซลล์/คนรู้จักนัดพบวัน-เวลา-สถานที่ชัดเจน ต้องการ query "สัปดาห์นี้มีอะไร"
2. **Encounter** — เจอคนแปลกหน้าระหว่างทาง แลกเปลี่ยนความรู้/contact เล็กๆ อยากจำได้ภายหลัง

ทั้งคู่ใช้โครงสร้าง `people/<slug>.md` เดียวกัน (1 slug = 1 คน) ไม่เพิ่ม folder ใหม่ ไม่ผูก Google Calendar เป็น **pull-only markdown vault** ตามจิตวิญญาณของ CLAUDE.md

## หลักการ

- **1 slug = 1 คน** (per vault convention). Encounters ซ้ำ → append `## Notes`; appointment ที่จะมาถึง → frontmatter field เดียว
- **Frontmatter = machine-readable** (appointment scheduling fields)
- **Body = human narrative** (`## Notes` dated bullets + `## Follow-ups` checklist)
- **Anonymous encounter fallback** = journal/ entry — ไม่บังคับตั้งชื่อ
- **Pull-only** — ไม่มี push ไป Google Calendar, ไม่มี cron (per CLAUDE.md "never scheduled/cron'd")

## Data Model

### `people/<slug>.md` Frontmatter (extended)

```yaml
---
name: คุณเบียร์ (สมชาย ใจดี)
aliases: [beer, สมชาย, sm]                       # required — search handles name variants
met_first: 2026-03-15                              # when we first met
met_last: 2026-07-08                               # most recent contact (auto-updated)
org: บริษัท ABC                                    # optional
role: ที่ปรึกษาการตลาด                              # optional
contact:                                           # at least one entry usually
  line: beerline
  mobile: 08x-xxx-xxxx
  email: beer@example.com
next_meeting_at: 2026-07-15T14:00                 # ISO 8601, optional — appointment only
meeting_location: ร้านกาแฟ XYZ สยาม              # optional
meeting_agenda: demo สินค้า + คุยราคา            # optional
meeting_status: scheduled                          # scheduled|done|cancelled|no_show, optional
sources: [2026-07-15-...]                          # raw file(s) that taught us this person
updated: 2026-07-08
---
```

### Body Shape

```markdown
# คุณเบียร์ (สมชาย ใจดี)

> ที่ปรึกษาการตลาด ABC — รู้จักผ่านคุณ A ที่งาน Depry Clinic

## Notes (เรียงเวลา ใหม่สุดบน)
- 2026-07-08: เจอที่งาน Depry, คุยเรื่อง X เขาสนใจ Y
- 2026-05-12: โทรคุย 15 นาที, ส่ง line โดย ล.
- 2026-03-15: แนะนำตัวที่งาน Depry Clinic ครั้งแรก

## Follow-ups
- [ ] 2026-07-20 — ส่ง slide deck ให้เขา (due 5 วันหลัง demo)
- [ ] 2026-08-01 — นัดเจออีกรอบ (no due yet)
```

### Anonymous Encounter Fallback — journal/

ถ้า user เจอคนแต่ลืม/ไม่ทราบชื่อ → `/sb เจอ <story>` route เขียน journal entry:

```markdown
# journal/2026-07-08-1430.md

> mood: curious

## People seen (unnamed)
- ชายเสื้อแดงที่บูธ 3 งาน Depry Clinic: เล่าเรื่อง X สนใจ Y
- บาริสต้าร้านกาแฟหลังตลาด: แนะนำชง cold brew แบบ slow drip
```

ไม่สร้าง person file ไม่บังคับตั้งชื่อ — fallback ลด friction ของการจับ encounter แบบเร็ว

## `/sb` Routes

| Route | Op | Behavior |
|---|---|---|
| `/sb คน <story>` | PERSON-extended | heuristic: มี date+time → appointment mode; อื่นๆ → encounter append `## Notes`; ถ้ากำกวม → ถาม 1 คำถาม |
| `/sb นัด <story>` | NEW | explicit appointment: ตั้ง `next_meeting_at`, `meeting_location?`, `meeting_agenda?`, `meeting_status: scheduled` |
| `/sb เจอ <story>` | NEW | explicit encounter: มีชื่อ → append `## Notes`; ไม่มีชื่อ → journal entry under `## People seen` |
| `/sb this week` | NEW | query: `next_meeting_at` ใน [today, today+7] AND `meeting_status` ∈ {scheduled, ∅} |
| `/sb follow-up` | NEW | query: `## Follow-ups` ทุกคน ที่ยังไม่ checked, sort by due date |
| `/sb done <slug>` | NEW | flip `meeting_status: done` + update `met_last: today` + append `## Notes` summary |
| `/sb cancel <slug>` | NEW | flip `meeting_status: cancelled` + ถามเหตุผลสั้น append `## Notes` |
| `/sb who <name>` | ASK-scoped | existing — grep people/ ด้วย name + aliases |

### Detection Heuristic สำหรับ `/sb คน`

ไม่ใช้ LLM ตัดสิน (latency + cost) — regex/keyword check:

- มี `\d{1,2}[:.]\d{2}` หรือ `\d{1,2}\s*โมง` หรือคำว่า พรุ่งนี้/พบ/นัด/อาทิตย์หน้า → appointment mode
- อื่นๆ → encounter mode
- ถ้ายังกำกวม → ถาม 1 คำถามสั้น ("นี่คือนัดหมาย หรือ encounter?")

### Output Examples

**`/sb this week`:**
```
📅 สัปดาห์นี้คุณมีนัด 3 อย่าง:

1. พ. 9 ก.ค. 14:00 — beer (ร้านกาแฟ XYZ สยาม)
   └─ demo สินค้า + คุยราคา
2. ศ. 11 ก.ค. 10:30 — pim (ออนไลน์ Zoom)
   └─ คุย contract รอบ 2
3. อา. 13 ก.ค. 19:00 — dr.somchai (โรงพยาบาล BNH)
   └─ ตรวจสุขภาพประจำปี

`/sb done <slug>` เมื่อเสร็จแล้ว
```

**`/sb follow-up`:**
```
📋 ติดตามค้าง 4 อย่าง:

1. ⏰ วันนี้ — ส่ง slide deck ให้ beer (นัด demo ผ่านไป 5 วัน ⚠️)
2. ⏰ พฤ. 10 ก.ค. — ส่ง contract ให้ pim
3. ⏰ ไม่มี due — นัดเจอ beer อีกรอบ (เขา propose อาทิตย์หน้า)
4. ⏰ ไม่มี due — ส่ง line ถามสุขภาพ dr.somchai
```

## Lifecycle

```
[add via /sb นัด] → meeting_status: scheduled
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   /sb done         /sb cancel       (no transition)
   → done           → cancelled
        │                 │
        └──── both ───────┴── → เก็บไว้ในไฟล้ (audit trail)
                              query filters exclude
```

- `meeting_status: scheduled` (default เมื่อ add)
- User-driven transitions: `done | cancelled | no_show` ผ่าน `/sb done|cancel <slug>`
- After done/cancelled, frontmatter meeting_* fields คงอยู่ (audit) แต่ filter exclude จาก `/sb this week`
- **ไม่ลบไฟล้ ไม่ archive ใน v1** (YAGNI — query speed OK ที่ scale hundreds)

## Error Handling

| Case | Behavior |
|---|---|
| 2 appointments คนเดิม เวลาทับซ้อน | warn + ขอ confirm ก่อนเขียน |
| เวลา relative ("พรุ่งนี้บ่าย 2") | resolve จาก today ใน context; ถ้าคลุมเครือ → ถาม |
| `/sb done beer` เมื่อไม่มี appointment scheduled | "ไม่พบนัดที่ค้างของ beer — ใช้ `/sb cancel beer` ถ้ายกเลิก, หรือ `/sb คน beer ...` เพื่อบันทึก encounter แทน" |
| Anonymous encounter (no name) | journal/ entry ไม่สร้าง person file |
| Capture จาก ingest (LINE/FB message) | route ผ่าน `raw/` → PROCESS op ดึงเข้า people/ |
| Ambiguous intent (ไม่รู้ว่า appointment/encounter) | ถาม 1 คำถาม — ไม่ guess (per CLAUDE.md "ask, don't guess") |

## Concurrency

- `## Notes` append → ต่อท้าย (single-writer per file OK per CLAUDE.md rule)
- Frontmatter update → read-modify-write ทั้งไฟล้ (single-writer per slug OK)
- ทุก op จบด้วย `bin/sb-commit.sh "<op>: <slug>"` (ไม่ใช้ git commit ตรง)

## Privacy (out of scope แต่ call out)

- Vault เป็น git plaintext — เบอร์โทร/อีเมลอยู่ใน history ตลอดไป
- ถ้าต้องการ privacy tier: `.gitignore` `people/_private/` หรือแยก private repo — **ไม่ทำใน spec นี้**

## YAGNI (ไม่ทำใน v1)

- Archive folder สำหรับ done appointments
- Auto-detect recurrence ("ทุกจันทร์")
- Voice/Line notification
- Google Calendar push (ตัดสินใจแล้วว่าไม่ทำ)
- Multi-user sharing
- LLM-based intent detection (ใช้ heuristic แทน)

## CLAUDE.md Changes Required

ใน section "Frontmatter schemas" ขยาย:

```yaml
people/: name, aliases, met_first, met_last, org, role, contact,
         next_meeting_at?, meeting_location?, meeting_agenda?, meeting_status?,
         sources, updated
```

ใน section "Operations" เพิ่ม:
- **PERSON-extended**: อธิบาย heuristic + ตัวอย่าง
- **APPOINTMENT** (ใหม่): `/sb นัด`, `/sb this week`, `/sb done`, `/sb cancel`
- **ENCOUNTER** (ใหม่): `/sb เจอ`, anonymous fallback

ใน "Routing `/sb` input → op" table เพิ่ม rows ใหม่

ใน section "Frontmatter schemas" → `journal/` ขยาย: เพิ่ม optional section `## People seen (unnamed)` สำหรับ anonymous encounter fallback (timestamp ในชื่อไฟล์อยู่แล้ว ไม่กระทบ dedup)

## Acceptance Test (verification target)

- ✅ `/sb นัด beer พุ่งนี้ 14:00 ที่ร้าน XYZ คุยเรื่อง demo` → สร้าง `next_meeting_at: <tomorrow>T14:00`, `meeting_location: ร้าน XYZ`, `meeting_agenda: คุยเรื่อง demo`, `meeting_status: scheduled`
- ✅ `/sb this week` แสดง beer พร้อม agenda + location
- ✅ `/sb done beer` → status=done + append bullet ใน Notes
- ✅ `/sb เจอ ชายเสื้อแดง ที่งาน Depry คุยเรื่อง X` → journal entry (ไม่มี person file)
- ✅ `/sb คน beer` (ambiguous) → ถาม "appointment หรือ encounter?"
- ✅ Existing `people/` schema (`met_at`, `met_when` ใน CLAUDE.md) → **rename เป็น `met_first`, `met_last`** (folder ว่างเปล่า 0 files — no migration needed)
- ✅ `bin/sb-commit.sh` เรียกครั้งเดียวต่อ op — ไม่มี orphan commits