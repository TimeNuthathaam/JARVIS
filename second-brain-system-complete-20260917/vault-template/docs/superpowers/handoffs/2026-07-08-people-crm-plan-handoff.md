# People CRM Plan — Final Handoff (2026-07-08)

> Status: **SHIPPED + CLOSED** 🎉
> Cycle: 7-task SDD plan (commits `d158f48..56f2f67` รวม follow-up polish)

---

## TL;DR

People CRM ops พร้อมใช้งานจริง:
- 5 bash helpers (`sb-{encounter-detect,encounter-anon,people-update,this-week,follow-up}.sh`) + 1 frontmatter lib
- 7 test files, **49 assertions ทั้งหมด green** (e2e dummy verified 2026-07-08)
- CLAUDE.md routing table ครอบคลุม 6 ops ใหม่
- G-003 cherry-pick landed (helper mkdir-p fix + new test case)
- Procedure doc สำหรับ real-usage: `docs/procedures/people-crm-real-usage.md`

**Open items ที่ user ต้องทำเอง (มีขั้นตอนใน procedure doc):**
- Real `/sb นัด` / `/sb เจอ` (named + anonymous) — ต้องใช้ชื่อ/เรื่องจริง
- First `/sb audit` — ต้องยืนยัน scope ก่อน

---

## What shipped

### Helpers (bin/)
| File | Purpose | Lines |
|---|---|---|
| `lib-frontmatter.sh` | fm_get/fm_set/fm_has single source of truth | 65 |
| `sb-encounter-detect.sh` | heuristic: นัด vs เจอ (stdin → appointment/encounter) | 28 |
| `sb-encounter-anon.sh` | anonymous encounter → journal/  (F-1 from final review) | 39 |
| `sb-people-update.sh` | 4 actions: ensure/set/add-note/add-followup (G-003 fixed) | 110 |
| `sb-this-week.sh` | query: meetings ใน 7 วันข้างหน้า | small |
| `sb-follow-up.sh` | query: open follow-ups เรียง due | small |

### Tests (tests/)
| File | Assertions | Status |
|---|---|---|
| `test-lib-frontmatter.sh` | 8 | ✓ |
| `test-sb-encounter-detect.sh` | 8 | ✓ |
| `test-sb-encounter-anon.sh` | 6 | ✓ |
| `test-sb-people-update.sh` | 8 (was 5 — added 3 for G-003) | ✓ |
| `test-sb-this-week.sh` | 3 | ✓ |
| `test-sb-follow-up.sh` | 2 | ✓ |
| `test-e2e-smoke.sh` | 14 | ✓ |
| **Total** | **49** | **all green** |

### Docs
- `CLAUDE.md` — routing table + APPOINTMENT + ENCOUNTER op sections
- `docs/superpowers/specs/2026-07-08-people-crm-encounters-appointments-design.md` — design spec
- `docs/superpowers/plans/2026-07-08-people-crm-encounters-appointments.md` — implementation plan (7 tasks)
- `docs/procedures/people-crm-real-usage.md` — **NEW** copy-paste guide for user
- `docs/superpowers/handoffs/2026-07-08-people-crm-plan-handoff.md` — **this doc**

### Artifacts (`.superpowers/sdd/`)
- `progress.md` — commit-by-commit ledger
- `task-{1-7}-brief.md` — extracted briefs for subagents
- `task-{1-7}-report.md` — implementer reports
- `task-{1-5}-review.md` — per-task reviewer reports (Task 6+7 = final review only)
- `final-review.md` — whole-branch review (NEEDS-FIXES, 11 findings → 8 fixed + 3 skipped justified)

---

## Known gotchas (จาก GUARDRAILS)

### G-003 (FIXED 2026-07-08) — helper arg-parsing silently falls through
- **Root cause:** pattern `if [ -d "${!#}" ]` ใน `sb-people-update.sh` ใช้ `dir-exists` เป็น detection signal → ถ้า dir ไม่มี → fall through ไป default `$VAULT/people` → เขียนลง real vault
- **Fix (cherry-pick landed):**
  1. `bin/sb-people-update.sh` — เปลี่ยน detection เป็น `[[ "$last" == */* ]]` (looks-like-a-path) — `mkdir -p` ใน `ensure` action จะสร้าง dir ให้
  2. `tests/test-sb-people-update.sh` — เพิ่ม subtest "ensure: creates target dir if missing" (3 assertions ใหม่)
- **Verification:** test suite 49/49 green, e2e dummy ไม่ leak

### G-004 (standing rule) — spec-driven plans need whole-branch review
- 5 per-task reviews clean ≠ plan shipped — ต้องมี final review against spec coverage matrix + acceptance scenarios
- **Rule:** plans with design spec → must run final review before declaring shipped

### G-001 (existing) — /watch ingest gate
- `WATCH_VAULT_DIR` env var in `~/.claude/settings.json` ตั้งแล้ว — YouTube/clip captures เข้า vault ได้

### G-002 (existing) — SDD >5 tasks need /save-progress checkpoint
- People CRM 7 tasks: ไม่ได้ checkpoint (เรียนรู้หลัง ship) — rule เดียวกันใช้กับ plan ถัดไป

---

## Open items

### User-driven (มี procedure แล้ว)
1. **Real `/sb นัด` first test** — ใช้ชื่อ/เวลา/สถานที่/agenda จริง → `docs/procedures/people-crm-real-usage.md` §1
2. **Real `/sb เจอ` named** — ใช้ชื่อ + เรื่องจริง → §2
3. **Real `/sb เจอ` anonymous** — ใช้ descriptor + takeaway จริง → §3
4. **First `/sb audit`** — agent เสนอ scope (N sessions) + total size → user confirm → scan → `audit/candidates-*.md`

### Future polish (ไม่ block)
- `sb-this-week.sh` / `sb-follow-up.sh` — output format อาจปรับ (Thai day display ทดสอบแล้ว — OK)
- ถ้ามี conflict `next_meeting_at` จริง → พิจารณา add conflict-detection ใน helper
- `sb-encounter-detect.sh` — doc note "stdin" เพิ่มแล้ว (Task 2) แต่ถ้ามี edge case เพิ่มเติม (เช่น "tomorrow" EN + ISO date) → expand regex

---

## How to resume work (สำหรับ session ถัดไป)

1. `/project-memory` → load brief (SESSION.md จะบอก current state)
2. ถ้า user ให้ input จริงสำหรับ `/sb นัด` → follow `docs/procedures/people-crm-real-usage.md` §1
3. ถ้า user ขอ `/sb audit` → dry-run first, present scope, wait for confirm
4. ถ้า user ขอ plan ใหม่ (เช่น "ต่อไปทำ booking flow" / "ทำ reading-list" / etc.) → use GSD spec-phase

---

## Metrics (สำหรับ retrospect)

- **Tasks:** 7 (5 helpers + CLAUDE.md + e2e) — recommended max 5 per session (G-002)
- **Commits:** 11 (3 SDD cycles: implement + final-review-fixes + e2e-fix + memory-bootstrap + G-003-polish + procedure + close-out)
- **Token cost:** high (5/7 tasks had reviewer round-trips, final review 11 findings)
- **Bugs caught post-ship:** 1 (G-003 trailing-dir detection — fixed)
- **Bugs caught pre-ship:** 11 (final review — 8 fixed, 3 skipped justified)

---

_Closed: 8 ก.ค. 2026 · next plan รอ user input_
