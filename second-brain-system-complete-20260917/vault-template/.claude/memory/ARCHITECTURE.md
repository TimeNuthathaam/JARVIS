# ARCHITECTURE — แผนที่ second-brain vault

> แผนที่นี้ช่วยให้ Claude หา "ที่ที่ต้องแก้" ได้เร็วโดยไม่ต้องไล่อ่านทั้ง vault
> อัปเดตเมื่อโครงสร้างเปลี่ยน (เพิ่ม folder ใหม่, helper ใหม่, op ใหม่)

## Directory map
```
/home/time/second-brain/
├── CLAUDE.md                      ← operating manual (อ่านก่อนเสมอ)
├── SCHEMA.md                      ← taxonomy 4 ลิ้นชัก (อ่านก่อนเขียน node)
├── PROJECT_EXPORT.md              ← discovery card (for /project-memory cross-load)
├── index.md                       ← derived — regenerate ด้วย bin/sb-index.sh
├── .sb/search.db                  ← derived SQLite FTS5 + Gemini vectors (gitignored)
│
├── raw/                           ← immutable captures (one file per capture)
│   ├── YYYY-MM-DD-<slug>.md       ← frontmatter: status: raw|processed
│   └── assets/                    ← images, prefix ด้วย slug เดียวกัน
│
├── entities/                      ← ความรู้: บริษัท / เครื่องมือ / ผลิตภัณฑ์ / คนดัง
├── concepts/                      ← ความรู้: แนวคิด / เทคนิค / pattern / topic-synthesis
├── comparisons/                   ← ความรู้: A vs B
├── queries/                       ← ความรู้: คำถาม research ที่ตอบแล้ว
│
├── people/                        ← CRM: คนรู้จักจริง (op PERSON/นัด/เจอ)
│   └── <slug>.md                  ← single-writer per person, update in place
├── journal/                       ← journal entries (one per op JOURNAL or anon encounter)
│   └── YYYY-MM-DD-HHMM.md         ← append-only, แก้ย้อนหลังไม่ได้
│
├── log/                           ← monthly log (append via sb-commit only)
│   └── YYYY-MM.md                 ← sb-commit flock-serializes
├── audit/                         ← AUDIT op output only
│   └── candidates-YYYY-MM-DD-HHMM.md
├── output/                        ← deliverables ที่สร้างจาก vault (never cite)
│
├── bin/                           ← bash helpers (THE only write path)
│   ├── lib-frontmatter.sh         ← fm_get/fm_set/fm_has — single source of truth
│   ├── sb-commit.sh               ← write gate: flock + log append + git commit
│   ├── sb-index.sh                ← regenerate index.md
│   ├── sb-search.py               ← sync/search/status/reindex/benchmark hybrid retrieval
│   ├── sb-encounter-detect.sh     ← /sb heuristic: นัด vs เจอ
│   ├── sb-encounter-anon.sh       ← anonymous encounter → journal/ fallback
│   ├── sb-people-update.sh        ← 4 ops: ensure/set/add-note/add-followup
│   ├── sb-this-week.sh            ← query: scheduled meetings in next 7 days
│   └── sb-follow-up.sh            ← query: open follow-ups across people
│
├── tests/                         ← bash test suite (one file per helper)
│   ├── helpers.sh                 ← shared test harness
│   ├── fixtures/                  ← gitignored
│   ├── test-lib-frontmatter.sh    ← 5 assertions
│   ├── test-sb-encounter-detect.sh
│   ├── test-sb-encounter-anon.sh
│   ├── test-sb-people-update.sh
│   ├── test-sb-this-week.sh
│   ├── test-sb-follow-up.sh
│   ├── test-sb-search.py          ← offline FTS/vector/fallback/incremental checks
│   └── test-e2e-smoke.sh          ← people CRM workflow end-to-end
│
├── docs/
│   └── superpowers/
│       ├── specs/                 ← design specs (approved before planning)
│       └── plans/                 ← implementation plans (per SDD cycle)
│
├── .superpowers/
│   └── sdd/                       ← SDD ledger: progress.md + per-task brief/report/review
│
├── .claude/
│   ├── settings.json              ← hooks (session memory), env (WATCH_VAULT_DIR)
│   └── memory/                    ← PROJECT.md / ARCHITECTURE.md / SESSION.md / GUARDRAILS.md
│
└── .sb.lock                       ← flock target for sb-commit
```

## Module หลัก
| Module | หน้าที่ | ไฟล์สำคัญ |
| :-- | :-- | :-- |
| `raw/` | Immutable captures — entry point ของทุกอย่าง | `raw/YYYY-MM-DD-<slug>.md` |
| 4 knowledge folders | Typed long-term memory (search + compound) | `entities/`, `concepts/`, `comparisons/`, `queries/` |
| `people/` | Named CRM (relationships, meetings, follow-ups) | `people/<slug>.md` |
| `journal/` | Time-stamped personal log + anonymous encounter fallback | `journal/YYYY-MM-DD-HHMM.md` |
| `bin/sb-commit.sh` | **Write gate** — flock + log + git commit (only path) | atomic, idempotent |
| `bin/lib-frontmatter.sh` | Frontmatter parser/serializer (used by all helpers) | fm_get/fm_set/fm_has |
| `bin/sb-*` (People CRM) | 6 helpers for PERSON/นัด/เจอ/this-week/follow-up/upcoming ops | single-purpose, composable |
| `bin/sb-index.sh` | Regenerate `index.md` from all typed folders | derived, safe to delete & rebuild |
| `bin/sb-search.py` | Derived SQLite FTS5 + Gemini hybrid retrieval | content-hash incremental, raw lexical-only, API fallback |
| `tests/` | 7 standalone Bash scripts + Python hybrid-search tests | `helpers.sh`, `test-*.sh`, `test-sb-search.py` |

## Data flow
```
INGEST (URL/text/file)
  → raw/YYYY-MM-DD-<slug>.md (status: raw)     ← immutable capture
  → PROCESS (for that file)
      → search-then-update across entities/ concepts/ comparisons/ queries/
      → write/update 1+ typed nodes
      → flip status: processed
  → bin/sb-index.sh (Markdown index)
  → bin/sb-search.py sync --best-effort (SQLite FTS5 + changed embeddings)
  → bin/sb-commit.sh "process: <slug>"          ← write gate

PERSON (name)         → people/<slug>.md  (create or update)
นัด (story with time) → people/<slug>.md next_meeting_at + meeting_status
เจอ (story, named)    → people/<slug>.md ## Notes bullet
เจอ (story, anon)     → journal/YYYY-MM-DD-HHMM.md ## People seen (unnamed)
done/cancel           → flip meeting_status + append ## Notes summary

ASK                   → hybrid search → follow links/sources → answer + write queries/ node
SEARCH                → hybrid ranked context only (no write-back)
REINDEX               → rebuild .sb/search.db from Markdown
AUDIT                 → reads ~/.claude/projects/**/*.jsonl → audit/candidates-*.md
```

## ไฟล์ที่ "ห้ามแตะถ้าไม่จำเป็น"
- `raw/YYYY-MM-DD-*.md` (เนื้อหา) — immutable แตะได้แค่ `status:` frontmatter
- `.sb.lock` — flock target, ห้ามลบขณะ sb-commit กำลังทำงาน
- `log/YYYY-MM.md` — append-only, sb-commit.sh เป็นคนเขียน ห้ามมือแก้
- `index.md` — derived, regenerate ด้วย `bin/sb-index.sh` ห้ามมือแก้
- `.sb/search.db` — derived, gitignored, rebuild ด้วย `bin/sb-search.py reindex`
- `people/<slug>.md` — single-writer per person OK, แต่ห้าม append เอง (ใช้ `sb-people-update.sh add-note`)
- `journal/YYYY-MM-DD-HHMM.md` — append-only, แก้ย้อนหลังไม่ได้
- `bin/lib-frontmatter.sh` — frontmatter parser, change = กระทบทุก helper (G-003 root cause)

## จุดที่มักต้องแก้บ่อย (hotspots)
- **เพิ่ม /sb op ใหม่** → เขียน `bin/sb-<op>.sh` + `tests/test-sb-<op>.sh` + อัปเดต CLAUDE.md routing table + อัปเดต CLAUDE.md op section
- **แก้ retrieval** → `bin/sb-search.py` + `tests/test-sb-search.py`; ห้ามส่ง raw ไป Gemini
- **เพิ่ม knowledge node** → อ่าน SCHEMA.md ก่อน → search-then-update → write `<folder>/<slug>.md` + aliases → `bin/sb-index.sh` + `bin/sb-commit.sh`
- **เพิ่ม person** → `sb-people-update.sh <slug> ensure` แล้ว set fields
- **แก้ helper** → แก้ทั้ง bin + test พร้อมกัน, run test suite ก่อน commit
- **แก้ CLAUDE.md routing table** → check test-e2e-smoke.sh ว่าครอบคลุมทุก op row

## Tests
- `tests/helpers.sh` — shared `assert_*` harness (no external deps)
- Per-helper test: usually 5-10 assertions, exit 0 = green
- E2E: `tests/test-e2e-smoke.sh` — exercises the appointment/encounter/follow-up lifecycle
- Run: `bash tests/test-*.sh` (each file standalone) or wrap in a runner
- Hybrid search: `python3 tests/test-sb-search.py`; real benchmark: `python3 bin/sb-search.py benchmark tests/fixtures/hybrid-search-benchmark.json --limit 5`
- Last known green: **7 Bash scripts + 7 Python hybrid-search cases** (2026-08-15)
