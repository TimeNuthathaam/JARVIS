# People CRM — Encounters & Appointments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `/home/time/second-brain` vault with appointment + encounter capture, time-aware query (`/sb this week`), and lifecycle management (`done|cancel`) — pull-only, markdown, no infra, no cron.

**Architecture:** Bash helpers in `bin/` read/write `people/<slug>.md` frontmatter (machine-readable for appointments) and append `## Notes` bullets (human narrative for encounters). Anonymous encounters fall back to `journal/YYYY-MM-DD-HHMM.md` under `## People seen (unnamed)`. CLAUDE.md routes `/sb` to the right helper. Heuristic (regex) detects appointment vs encounter from the input — no LLM.

**Tech Stack:** bash 5 + awk + grep + flock + git. No new dependencies. Tests are plain bash assertion helpers (no bats).

---

## File Structure

**New files:**
- `bin/lib-frontmatter.sh` — shared read/parse/write helpers (single source of truth for all people frontmatter ops)
- `bin/sb-encounter-detect.sh` — heuristic classifier (appointment vs encounter)
- `bin/sb-people-update.sh` — read-modify-write frontmatter for `/sb นัด`, `/sb done`, `/sb cancel`
- `bin/sb-this-week.sh` — query appointments in next 7 days
- `bin/sb-follow-up.sh` — query open follow-ups across people/
- `tests/test-lib-frontmatter.sh` — frontmatter roundtrip tests
- `tests/test-sb-encounter-detect.sh` — classifier tests
- `tests/test-sb-people-update.sh` — update helper tests
- `tests/test-sb-this-week.sh` — week-query tests with fixtures
- `tests/test-sb-follow-up.sh` — follow-up query tests
- `tests/helpers.sh` — shared assertion functions + fixture cleanup
- `tests/fixtures/` — temp vault copies for isolated tests (gitignored)
- `tests/.gitignore` — `fixtures/` excluded

**Modified files:**
- `CLAUDE.md` — extend `people/` frontmatter schema, extend routing table, add `APPOINTMENT` + `ENCOUNTER` op sections, extend `journal/` schema with `## People seen (unnamed)`
- `.gitignore` — add `tests/fixtures/`

**Untouched (per YAGNI):**
- `SCHEMA.md` — doesn't reference people/ directly, no change needed
- `bin/sb-commit.sh`, `bin/sb-index.sh` — already cover lock + commit + index; new scripts call them

---

## Global Constraints

- **Vault path:** `/home/time/second-brain` (absolute — Telegram bot sessions have different cwd)
- **Frontmatter format:** YAML between `---` markers; awk-based parser (no Python, no jq dependency)
- **Slug rule:** ASCII kebab-case (`beer.md`, `somchai-j.md`); aliases carry Thai variants
- **Concurrency:** every write op finishes with `bin/sb-commit.sh "<op>: <slug>"` (flock-serialized); never `git commit` directly
- **Date format:** `YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM` ISO 8601 for `next_meeting_at`
- **Language:** user-facing strings in Thai (per CLAUDE.md); code comments in English
- **No new folders** beyond `tests/fixtures/` (gitignored, transient)
- **No cron, no push** to external services (per CLAUDE.md "never scheduled/cron'd")
- **Test pattern:** bash scripts that source `tests/helpers.sh`, write fixtures to `tests/fixtures/`, assert, cleanup via trap

---

## Task 1: Frontmatter Library + Test Helper

**Files:**
- Create: `/home/time/second-brain/bin/lib-frontmatter.sh`
- Create: `/home/time/second-brain/tests/helpers.sh`
- Create: `/home/time/second-brain/tests/.gitignore`
- Create: `/home/time/second-brain/tests/fixtures/.gitkeep`

**Interfaces:**
- Produces: `fm_get <file> <key>` → stdout (value or empty); `fm_set <file> <key> <value>` → in-place rewrite; `fm_has <file> <key>` → exit 0/1

- [ ] **Step 1: Create `tests/.gitignore`**

```
fixtures/*
!fixtures/.gitkeep
```

- [ ] **Step 2: Create `tests/fixtures/.gitkeep`**

```
# placeholder so git tracks the dir
```

- [ ] **Step 3: Write `tests/helpers.sh` (assertion library)**

```bash
#!/usr/bin/env bash
# Shared test helpers — source this from every test file.
set -euo pipefail
VAULT="${VAULT:-/home/time/second-brain}"
TEST_NAME="${TEST_NAME:-$(basename "$0")}"
FIX="$VAULT/tests/fixtures/$TEST_NAME"
mkdir -p "$FIX"

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; echo "    expected: $2"; echo "    actual:   $3"; exit 1; }

assert_eq() {
  local actual="$1" expected="$2" label="${3:-value}"
  [ "$actual" = "$expected" ] && pass "$label" || fail "$label" "$expected" "$actual"
}

assert_contains() {
  local haystack="$1" needle="$2" label="${3:-content}"
  echo "$haystack" | grep -qF -- "$needle" && pass "$label" || fail "$label" "contains '$needle'" "$haystack"
}

write_fixture() {
  local path="$FIX/$1"; shift
  mkdir -p "$(dirname "$path")"
  cat > "$path"
}

cleanup() { rm -rf "$FIX"; }
trap cleanup EXIT
```

- [ ] **Step 4: Write failing test `tests/test-lib-frontmatter.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-lib-frontmatter"
source "$SCRIPT_DIR/helpers.sh"

# Source the lib under test
source "$VAULT/bin/lib-frontmatter.sh"

# Fixture: person with full frontmatter
write_fixture person.md <<'EOF'
---
name: คุณเบียร์
aliases: [beer, สมชาย]
met_first: 2026-03-15
met_last: 2026-07-08
next_meeting_at: 2026-07-15T14:00
meeting_status: scheduled
---
body here
EOF

echo "[fm_get: existing key]"
assert_eq "$(fm_get "$FIX/person.md" name)" "คุณเบียร์" "name field"
assert_eq "$(fm_get "$FIX/person.md" met_first)" "2026-03-15" "met_first"
assert_eq "$(fm_get "$FIX/person.md" aliases)" "[beer, สมชาย]" "aliases (raw value)"

echo "[fm_get: missing key]"
assert_eq "$(fm_get "$FIX/person.md" nonexistent)" "" "missing key returns empty"

echo "[fm_has]"
fm_has "$FIX/person.md" next_meeting_at && pass "has next_meeting_at" || fail "has next_meeting_at" "true" "false"
! fm_has "$FIX/person.md" nonexistent && pass "missing key returns false" || fail "missing key returns false" "false" "true"

echo "[fm_set: new key]"
fm_set "$FIX/person.md" meeting_location "ร้าน XYZ"
assert_eq "$(fm_get "$FIX/person.md" meeting_location)" "ร้าน XYZ" "newly set key"

echo "[fm_set: update existing]"
fm_set "$FIX/person.md" meeting_status "done"
assert_eq "$(fm_get "$FIX/person.md" meeting_status)" "done" "updated key"

echo "[fm_set: preserves body]"
fm_set "$FIX/person.md" updated "2026-07-09"
body_after=$(cat "$FIX/person.md")
assert_contains "$body_after" "body here" "body preserved"
assert_contains "$body_after" "meeting_status: done" "frontmatter still valid YAML"
```

- [ ] **Step 5: Run test — expect FAIL (lib doesn't exist yet)**

Run: `bash /home/time/second-brain/tests/test-lib-frontmatter.sh`
Expected: FAIL with "lib-frontmatter.sh: No such file or directory"

- [ ] **Step 6: Implement `bin/lib-frontmatter.sh`**

```bash
#!/usr/bin/env bash
# YAML frontmatter read/parse/write helpers — single source of truth.
# Usage: source this file. Provides fm_get, fm_set, fm_has.
set -euo pipefail

# fm_get <file> <key> — print value of frontmatter key (empty if missing)
fm_get() {
  local file="$1" key="$2"
  awk -v k="$key" '
    NR==1 && $0 != "---" { exit }
    /^---$/ { c++; if (c == 2) exit; next }
    c == 1 && $0 ~ "^"k":[[:space:]]*" {
      sub("^"k":[[:space:]]*", "")
      print
      exit
    }
  ' "$file"
}

# fm_has <file> <key> — exit 0 if key exists, 1 if not
fm_has() {
  local file="$1" key="$2"
  fm_get "$file" "$key" | grep -q . && return 0 || return 1
}

# fm_set <file> <key> <value> — in-place rewrite, preserves body
fm_set() {
  local file="$1" key="$2" value="$3"
  local tmp="${file}.tmp.$$"

  awk -v k="$key" -v v="$value" '
    NR==1 && $0 != "---" { print "---"; fm_open=1 }
    /^---$/ {
      if (c == 0) { print; c=1; next }
      if (c == 1) {
        if (!wrote && k != "") { print k": "v }
        print
        wrote=1
        c=2
        next
      }
    }
    c == 1 {
      if ($0 ~ "^"k":[[:space:]]*") {
        print k": "v
        wrote=1
        next
      }
      print
      next
    }
    { print }
  ' "$file" > "$tmp"

  # If key was missing, insert before closing ---
  if ! grep -q "^${key}:" "$tmp"; then
    awk -v k="$key" -v v="$value" '
      /^---$/ && c == 1 { print k": "v }
      { print }
      /^---$/ { c++ }
    ' "$file" > "$tmp"
  fi

  mv "$tmp" "$file"
}
```

- [ ] **Step 7: Make scripts executable + run test**

```bash
chmod +x /home/time/second-brain/bin/lib-frontmatter.sh /home/time/second-brain/tests/test-lib-frontmatter.sh
bash /home/time/second-brain/tests/test-lib-frontmatter.sh
```

Expected: all `✓` lines, exit 0

- [ ] **Step 8: Commit**

```bash
cd /home/time/second-brain
git add bin/lib-frontmatter.sh tests/helpers.sh tests/.gitignore tests/fixtures/.gitkeep tests/test-lib-frontmatter.sh .gitignore
git commit -m "feat: frontmatter library + test helper (Task 1 of people-crm plan)"
```

---

## Task 2: Encounter Detector (Heuristic Classifier)

**Files:**
- Create: `/home/time/second-brain/bin/sb-encounter-detect.sh`
- Create: `/home/time/second-brain/tests/test-sb-encounter-detect.sh`

**Interfaces:**
- Consumes: stdin text (user's `/sb` input)
- Produces: stdout `appointment` or `encounter` (single token); exit 0 always
- Use: future `/sb คน` handler calls this to decide route

- [ ] **Step 1: Write failing test `tests/test-sb-encounter-detect.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-encounter-detect"
source "$SCRIPT_DIR/helpers.sh"
DETECT="$VAULT/bin/sb-encounter-detect.sh"

echo "[appointment signals]"
assert_eq "$(echo 'พรุ่งนี้ 14:00 นัดเจอ beer ที่ร้าน XYZ' | bash "$DETECT")" "appointment" "พรุ่งนี้ + เวลา"
assert_eq "$(echo 'นัด 9 ก.ค. 14:00 demo สินค้า' | bash "$DETECT")" "appointment" "explicit นัด + date"
assert_eq "$(echo 'เจอ beer วันศุกร์ 10:30' | bash "$DETECT")" "appointment" "เจอ + date + time"
assert_eq "$(echo 'next monday 9am meet pim' | bash "$DETECT")" "appointment" "English appointment"

echo "[encounter signals]"
assert_eq "$(echo 'เจอชายเสื้อแดงที่งาน Depry คุยเรื่อง X' | bash "$DETECT")" "encounter" "เจอ without time"
assert_eq "$(echo 'คุยกับ beer เรื่อง contract' | bash "$DETECT")" "encounter" "คุย + name, no time"
assert_eq "$(echo 'met stranger at coffee shop, talked about cold brew' | bash "$DETECT")" "encounter" "English encounter"

echo "[empty input]"
assert_eq "$(echo '' | bash "$DETECT")" "encounter" "empty defaults to encounter (safer)"
```

- [ ] **Step 2: Run test — expect FAIL (script missing)**

Run: `bash /home/time/second-brain/tests/test-sb-encounter-detect.sh`
Expected: FAIL with "sb-encounter-detect.sh: No such file"

- [ ] **Step 3: Implement `bin/sb-encounter-detect.sh`**

```bash
#!/usr/bin/env bash
# Heuristic: appointment vs encounter detection from /sb คน input.
# Reads stdin. Prints "appointment" or "encounter".
set -euo pipefail
input="$(cat)"

# Appointment signals (any one triggers):
#   - explicit time format HH:MM or HH.MM
#   - Thai time markers (โมง, นาฬิกา)
#   - date keywords (พรุ่งนี้, มะรืน, อาทิตย์หน้า, วัน..., next..., monday..sunday)
#   - intent keywords (นัด, พบ, meet, schedule)
if echo "$input" | grep -qE '[0-9]{1,2}[:.][0-9]{2}'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qE 'โมง|นาฬิกา'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qiE 'พรุ่งนี้|มะรืน|อาทิตย์หน้า|เดือนหน้า|วันจันทร์|วันอังคาร|วันพุธ|วันพฤหัส|วันศุกร์|วันเสาร์|วันอาทิตย์|next (monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month)'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qE 'นัด|พบ(?!ประมาณ)|meet[[:space:]]|schedule'; then
  echo "appointment"; exit 0
fi

# Default: encounter (safer — user can re-run with /sb นัด explicitly if needed)
echo "encounter"
```

- [ ] **Step 4: Make executable + run test**

```bash
chmod +x /home/time/second-brain/bin/sb-encounter-detect.sh
bash /home/time/second-brain/tests/test-sb-encounter-detect.sh
```

Expected: all `✓` lines

- [ ] **Step 5: Commit**

```bash
cd /home/time/second-brain
git add bin/sb-encounter-detect.sh tests/test-sb-encounter-detect.sh
git commit -m "feat: encounter detector heuristic (Task 2)"
```

---

## Task 3: People Update Helper

**Files:**
- Create: `/home/time/second-brain/bin/sb-people-update.sh`
- Create: `/home/time/second-brain/tests/test-sb-people-update.sh`

**Interfaces:**
- `sb-people-update.sh <slug> set <key> <value>` — sets one frontmatter key
- `sb-people-update.sh <slug> add-note <date> <bullet>` — appends to `## Notes`
- `sb-people-update.sh <slug> add-followup <due> <text>` — appends to `## Follow-ups`
- `sb-people-update.sh <slug> ensure` — creates empty file with frontmatter if missing

- [ ] **Step 1: Write failing test `tests/test-sb-people-update.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-people-update"
source "$SCRIPT_DIR/helpers.sh"
UPD="$VAULT/bin/sb-people-update.sh"

# Use isolated fixture dir for people files
PEOPLE_DIR="$FIX/people"
mkdir -p "$PEOPLE_DIR"

echo "[ensure: creates file with frontmatter]"
bash "$UPD" beer ensure "$PEOPLE_DIR"
[ -f "$PEOPLE_DIR/beer.md" ] && pass "file created" || fail "file created" "exists" "missing"
assert_eq "$(grep -c '^---$' "$PEOPLE_DIR/beer.md")" "2" "frontmatter delimiters"
assert_eq "$(awk '/^name:/{sub(/^name: /,""); print; exit}' "$PEOPLE_DIR/beer.md")" "beer" "default name"

echo "[set: frontmatter field]"
bash "$UPD" beer set next_meeting_at "2026-07-15T14:00" "$PEOPLE_DIR"
bash "$UPD" beer set meeting_status "scheduled" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "next_meeting_at: 2026-07-15T14:00" "meeting time set"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "meeting_status: scheduled" "status set"

echo "[add-note: appends to ## Notes]"
bash "$UPD" beer add-note "2026-07-08" "เจอที่งาน Depry คุยเรื่อง X" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "- 2026-07-08: เจอที่งาน Depry คุยเรื่อง X" "note appended"

echo "[add-note: idempotent — second call adds another bullet]"
bash "$UPD" beer add-note "2026-05-12" "โทรคุย 15 นาที" "$PEOPLE_DIR"
note_count=$(grep -c '^- 2026-' "$PEOPLE_DIR/beer.md")
assert_eq "$note_count" "2" "two notes appended"

echo "[add-followup: appends to ## Follow-ups]"
bash "$UPD" beer add-followup "2026-07-20" "ส่ง slide deck" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "- [ ] 2026-07-20 — ส่ง slide deck" "followup appended"

echo "[set: preserves existing body content]"
original_note="- 2026-07-08: เจอที่งาน Depry คุยเรื่อง X"
bash "$UPD" beer set meeting_status "done" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "$original_note" "note preserved after set"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `bash /home/time/second-brain/tests/test-sb-people-update.sh`
Expected: FAIL "sb-people-update.sh: No such file"

- [ ] **Step 3: Implement `bin/sb-people-update.sh`**

```bash
#!/usr/bin/env bash
# People file frontmatter + body operations.
# Usage: sb-people-update.sh <slug> <action> [args...] [people_dir]
#   ensure                       — create empty file with frontmatter
#   set <key> <value>            — set frontmatter field
#   add-note <date> <bullet>     — append to ## Notes
#   add-followup <due> <text>    — append to ## Follow-ups
set -euo pipefail
VAULT="${VAULT:-/home/time/second-brain}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

slug="${1:?usage: <slug> <action> [args...]}"
action="${2:?missing action}"
shift 2

# Optional trailing arg = people_dir (default vault people/)
people_dir=""
if [ "${!#}" = "${@: -1}" ] && [ -d "${!#}" ]; then
  people_dir="${!#}"
  set -- "${@:1:$#-1}"
fi
[ -z "$people_dir" ] && people_dir="$VAULT/people"

file="$people_dir/$slug.md"

case "$action" in
  ensure)
    if [ ! -f "$file" ]; then
      today="$(date +%Y-%m-%d)"
      cat > "$file" <<EOF
---
name: $slug
aliases: []
met_first: $today
met_last: $today
updated: $today
---

# $slug

## Notes (เรียงเวลา ใหม่สุดบน)

## Follow-ups
EOF
    fi
    ;;

  set)
    key="${1:?missing key}"
    value="${2:?missing value}"
    fm_set "$file" "$key" "$value"
    # Auto-bump updated + met_last if this is a "contact" update
    if [ "$key" = "meeting_status" ] || [ "$key" = "next_meeting_at" ]; then
      today="$(date +%Y-%m-%d)"
      fm_set "$file" met_last "$today"
    fi
    fm_set "$file" updated "$(date +%Y-%m-%d)"
    ;;

  add-note)
    date="${1:?missing date}"
    bullet="${2:?missing bullet}"
    # Ensure ## Notes section exists
    if ! grep -q '^## Notes' "$file"; then
      printf '\n## Notes (เรียงเวลา ใหม่สุดบน)\n' >> "$file"
    fi
    # Insert just after the ## Notes header (newest on top)
    awk -v d="$date" -v b="$bullet" '
      /^## Notes/ { print; print "- " d ": " b; inserted=1; next }
      inserted && /^## / { inserted=0 }
      { print }
    ' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
    today="$(date +%Y-%m-%d)"
    fm_set "$file" met_last "$today"
    fm_set "$file" updated "$today"
    ;;

  add-followup)
    due="${1:?missing due}"
    text="${2:?missing text}"
    if ! grep -q '^## Follow-ups' "$file"; then
      printf '\n## Follow-ups\n' >> "$file"
    fi
    echo "- [ ] $due — $text" >> "$file"
    fm_set "$file" updated "$(date +%Y-%m-%d)"
    ;;

  *)
    echo "unknown action: $action" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 4: Make executable + run test**

```bash
chmod +x /home/time/second-brain/bin/sb-people-update.sh
bash /home/time/second-brain/tests/test-sb-people-update.sh
```

Expected: all `✓` lines

- [ ] **Step 5: Commit**

```bash
cd /home/time/second-brain
git add bin/sb-people-update.sh tests/test-sb-people-update.sh
git commit -m "feat: people update helper (frontmatter + notes + followups) (Task 3)"
```

---

## Task 4: This Week Query

**Files:**
- Create: `/home/time/second-brain/bin/sb-this-week.sh`
- Create: `/home/time/second-brain/tests/test-sb-this-week.sh`

**Interfaces:**
- `sb-this-week.sh [people_dir]` — prints formatted appointment list for next 7 days

- [ ] **Step 1: Write failing test `tests/test-sb-this-week.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-this-week"
source "$SCRIPT_DIR/helpers.sh"
QUERY="$VAULT/bin/sb-this-week.sh"

PEOPLE_DIR="$FIX/people"
mkdir -p "$PEOPLE_DIR"

# Today (for ISO math)
TODAY="$(date +%Y-%m-%d)"
TODAY_ISO="${TODAY}T00:00"
TOMORROW="$(date -d '+1 day' +%Y-%m-%d)T14:00"
NEXT_WEEK="$(date -d '+6 day' +%Y-%m-%d)T10:00"
FAR_FUTURE="$(date -d '+30 day' +%Y-%m-%d)T09:00"

# Fixture 1: appointment tomorrow (should appear)
cat > "$PEOPLE_DIR/beer.md" <<EOF
---
name: beer
next_meeting_at: $TOMORROW
meeting_status: scheduled
---
EOF

# Fixture 2: appointment in 6 days (should appear)
cat > "$PEOPLE_DIR/pim.md" <<EOF
---
name: pim
next_meeting_at: $NEXT_WEEK
meeting_status: scheduled
---
EOF

# Fixture 3: appointment 30 days out (should NOT appear)
cat > "$PEOPLE_DIR/far.md" <<EOF
---
name: far
next_meeting_at: $FAR_FUTURE
meeting_status: scheduled
---
EOF

# Fixture 4: appointment tomorrow but already done (should NOT appear)
cat > "$PEOPLE_DIR/done.md" <<EOF
---
name: done
next_meeting_at: $TOMORROW
meeting_status: done
---
EOF

# Fixture 5: no frontmatter (should NOT appear, no crash)
cat > "$PEOPLE_DIR/empty.md" <<EOF
---
name: empty
---
EOF

echo "[shows tomorrow appointment]"
out=$(bash "$QUERY" "$PEOPLE_DIR")
assert_contains "$out" "beer" "beer appears"
assert_contains "$out" "$(date -d '+1 day' +%Y-%m-%d | awk -F- '{print $3}')" "tomorrow's day-of-month appears"

echo "[shows appointment within 7 days]"
assert_contains "$out" "pim" "pim (6 days out) appears"

echo "[excludes appointment > 7 days]"
! echo "$out" | grep -q "far" && pass "far (30d) excluded" || fail "far excluded" "absent" "present"

echo "[excludes done appointments]"
! echo "$out" | grep -q "done" && pass "done excluded" || fail "done excluded" "absent" "present"

echo "[handles empty file gracefully]"
echo "$out" | grep -q "empty" && fail "empty file ignored" "absent" "present" || pass "empty file ignored"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `bash /home/time/second-brain/tests/test-sb-this-week.sh`
Expected: FAIL "sb-this-week.sh: No such file"

- [ ] **Step 3: Implement `bin/sb-this-week.sh`**

```bash
#!/usr/bin/env bash
# Query: appointments in next 7 days with meeting_status: scheduled.
# Usage: sb-this-week.sh [people_dir]
set -euo pipefail
VAULT="${VAULT:-/home/time/second-brain}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

people_dir="${1:-$VAULT/people}"
[ ! -d "$people_dir" ] && { echo "no people dir: $people_dir" >&2; exit 1; }

today_epoch="$(date +%s)"
week_epoch="$(date -d '+7 day' +%s)"

# Collect appointments in window
results=()
for f in "$people_dir"/*.md; do
  [ -f "$f" ] || continue
  next=$(fm_get "$f" next_meeting_at)
  [ -z "$next" ] && continue

  # Status filter: only scheduled (or absent status = assume scheduled)
  status=$(fm_get "$f" meeting_status)
  [ -n "$status" ] && [ "$status" != "scheduled" ] && continue

  # Parse next_meeting_at → epoch
  appt_epoch=$(date -d "$next" +%s 2>/dev/null) || continue
  [ "$appt_epoch" -lt "$today_epoch" ] && continue
  [ "$appt_epoch" -gt "$week_epoch" ] && continue

  name=$(fm_get "$f" name)
  [ -z "$name" ] && name=$(basename "$f" .md)
  location=$(fm_get "$f" meeting_location)
  agenda=$(fm_get "$f" meeting_agenda)

  # Format date for display: "พ. 9 ก.ค." style — keep simple Thai day name
  thai_day=$(date -d "$next" '+%a %d %b' | sed 's/^Mon/จ./;s/^Tue/อ./;s/^Wed/พ./;s/^Thu/พฤ./;s/^Fri/ศ./;s/^Sat/ส./;s/^Sun/อา./')
  time_part=$(date -d "$next" '+%H:%M')

  results+=("$thai_day $time_part|$name|$location|$agenda")
done

if [ "${#results[@]}" -eq 0 ]; then
  echo "📅 สัปดาห์นี้ไม่มีนัดหมาย"
  exit 0
fi

echo "📅 สัปดาห์นี้คุณมีนัด ${#results[@]} อย่าง:"
echo
i=1
for r in "${results[@]}"; do
  IFS='|' read -r when name loc agenda <<< "$r"
  echo "$i. $when — $name${loc:+ ($loc)}"
  [ -n "$agenda" ] && echo "   └─ $agenda"
  i=$((i + 1))
done
echo
echo "\`/sb done <slug>\` เมื่อเสร็จแล้ว"
```

- [ ] **Step 4: Make executable + run test**

```bash
chmod +x /home/time/second-brain/bin/sb-this-week.sh
bash /home/time/second-brain/tests/test-sb-this-week.sh
```

Expected: all `✓` lines

- [ ] **Step 5: Commit**

```bash
cd /home/time/second-brain
git add bin/sb-this-week.sh tests/test-sb-this-week.sh
git commit -m "feat: this-week appointment query (Task 4)"
```

---

## Task 5: Follow-Up Query

**Files:**
- Create: `/home/time/second-brain/bin/sb-follow-up.sh`
- Create: `/home/time/second-brain/tests/test-sb-follow-up.sh`

**Interfaces:**
- `sb-follow-up.sh [people_dir]` — prints formatted open-followup list

- [ ] **Step 1: Write failing test `tests/test-sb-follow-up.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-follow-up"
source "$SCRIPT_DIR/helpers.sh"
QUERY="$VAULT/bin/sb-follow-up.sh"

PEOPLE_DIR="$FIX/people"
mkdir -p "$PEOPLE_DIR"

TODAY="$(date +%Y-%m-%d)"

# Fixture: beer has one overdue followup + one upcoming
cat > "$PEOPLE_DIR/beer.md" <<EOF
---
name: beer
---
## Follow-ups
- [ ] $TODAY — ส่ง slide deck ให้เขา
- [ ] 2026-08-01 — นัดเจออีกรอบ
EOF

# Fixture: pim has a done followup (should not appear)
cat > "$PEOPLE_DIR/pim.md" <<EOF
---
name: pim
---
## Follow-ups
- [x] $TODAY — ส่ง contract แล้ว
EOF

# Fixture: empty followups section
cat > "$PEOPLE_DIR/empty.md" <<EOF
---
name: empty
---
## Follow-ups
EOF

# Fixture: no followups section at all
cat > "$PEOPLE_DIR/none.md" <<EOF
---
name: none
---
EOF

echo "[shows open followups]"
out=$(bash "$QUERY" "$PEOPLE_DIR")
assert_contains "$out" "beer" "beer's followups appear"
assert_contains "$out" "ส่ง slide deck" "followup text appears"

echo "[excludes done followups]"
! echo "$out" | grep -q "pim" && pass "pim (done only) excluded" || fail "pim excluded" "absent" "present"

echo "[handles missing followups section gracefully]"
echo "$out" | grep -q "none" && fail "no-section file ignored" "absent" "present" || pass "no-section file ignored"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `bash /home/time/second-brain/tests/test-sb-follow-up.sh`
Expected: FAIL "sb-follow-up.sh: No such file"

- [ ] **Step 3: Implement `bin/sb-follow-up.sh`**

```bash
#!/usr/bin/env bash
# Query: open follow-ups across all people/, sorted by due date.
# Usage: sb-follow-up.sh [people_dir]
set -euo pipefail
VAULT="${VAULT:-/home/time/second-brain}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

people_dir="${1:-$VAULT/people}"
[ ! -d "$people_dir" ] && { echo "no people dir: $people_dir" >&2; exit 1; }

results=()
for f in "$people_dir"/*.md; do
  [ -f "$f" ] || continue
  name=$(fm_get "$f" name)
  [ -z "$name" ] && name=$(basename "$f" .md)

  # Extract open followup lines (- [ ] ...)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Skip done
    echo "$line" | grep -q '^- \[x\]' && continue
    # Match "- [ ] <due> — <text>"
    due=$(echo "$line" | sed -nE 's/^- \[ \] ([0-9]{4}-[0-9]{2}-[0-9]{2}) — .*/\1/p')
    text=$(echo "$line" | sed -E 's/^- \[ \] ([0-9]{4}-[0-9]{2}-[0-9]{2} )?— //; s/^- \[ \] //')
    sort_key="${due:-9999-99-99}"  # no-due sorts last
    results+=("$sort_key|$due|$name|$text")
  done < <(awk '/^## Follow-ups/,/^## / || /^## Follow-ups/,EOF' "$f" | grep -E '^- \[' | head -20)
done

# Sort by due key
IFS=$'\n' sorted=($(sort <<<"${results[*]:-}"))
unset IFS

if [ "${#sorted[@]}" -eq 0 ] || [ -z "${sorted[0]:-}" ]; then
  echo "📋 ไม่มี follow-up ค้าง"
  exit 0
fi

echo "📋 ติดตามค้าง ${#sorted[@]} อย่าง:"
echo
i=1
for r in "${sorted[@]}"; do
  IFS='|' read -r _ due name text <<< "$r"
  if [ -n "$due" ]; then
    echo "$i. ⏰ $due — $text ($name)"
  else
    echo "$i. ⏰ ไม่มี due — $text ($name)"
  fi
  i=$((i + 1))
done
```

- [ ] **Step 4: Make executable + run test**

```bash
chmod +x /home/time/second-brain/bin/sb-follow-up.sh
bash /home/time/second-brain/tests/test-sb-follow-up.sh
```

Expected: all `✓` lines

- [ ] **Step 5: Commit**

```bash
cd /home/time/second-brain
git add bin/sb-follow-up.sh tests/test-sb-follow-up.sh
git commit -m "feat: follow-up query across people/ (Task 5)"
```

---

## Task 6: Update CLAUDE.md (Schema + Routes + Op Sections)

**Files:**
- Modify: `/home/time/second-brain/CLAUDE.md`

**No tests** — pure documentation change. Verify with `git diff`.

- [ ] **Step 1: Read current CLAUDE.md to find exact sections to modify**

Run: `grep -n "people/\|Frontmatter schemas\|Operations\|Routing\|journal/" /home/time/second-brain/CLAUDE.md`

Expected output (approximate line numbers):
- Frontmatter schemas block around line 35-45
- Operations block around line 53-127
- Routing table around line 12-21

- [ ] **Step 2: Update `people/` frontmatter schema (in CLAUDE.md "Frontmatter schemas" section)**

Find:
```
**people/**: `name, aliases, met_at, met_when, org, role, contact, updated`
```

Replace with:
```
**people/**: `name, aliases, met_first, met_last, org, role, contact, next_meeting_at?, meeting_location?, meeting_agenda?, meeting_status?, sources, updated` — `met_first`/`met_last` ISO dates; `next_meeting_at` ISO 8601 datetime; `meeting_status` ∈ {scheduled, done, cancelled, no_show}
```

- [ ] **Step 3: Update `journal/` frontmatter schema (add People seen extension)**

Find:
```
**journal/**: `date, mood (optional)`
```

Replace with:
```
**journal/**: `date, mood (optional)` — optional body section `## People seen (unnamed)` for anonymous encounter fallback (one-line per person: descriptor + takeaway)
```

- [ ] **Step 4: Add new rows to `/sb` routing table (in CLAUDE.md "Routing `/sb` input → op" table)**

Find the table end (after `/sb graph` row) and append:

```
| `/sb นัด <story>` | APPOINTMENT-add (creates/updates `next_meeting_at` + frontmatter on existing person) |
| `/sb เจอ <story>` | ENCOUNTER-add (appends `## Notes` bullet; falls back to `journal/ ## People seen` if unnamed) |
| `/sb this week` | APPOINTMENT-query (lists scheduled meetings in next 7 days) |
| `/sb follow-up` | ENCOUNTER-query (lists open `## Follow-ups` across all people, sorted by due) |
| `/sb done <slug>` | APPOINTMENT-close (flips `meeting_status: done` + appends `## Notes` summary) |
| `/sb cancel <slug>` | APPOINTMENT-close (flips `meeting_status: cancelled` + asks for reason, appends to Notes) |
```

- [ ] **Step 5: Add new operation sections (after PERSON section)**

Find the PERSON section and add immediately after it:

```markdown
### APPOINTMENT — scheduled meetings on a person

Captures time-bound commitments with a known person. Person file `people/<slug>.md` already exists (created via PERSON op).

**Add (`/sb นัด`):**
1. Resolve `<slug>` from input (name → slug, or alias match)
2. Ensure person file exists (`sb-people-update.sh <slug> ensure`)
3. Parse `<story>` for date+time+location+agenda; if relative ("พรุ่งนี้ 14:00") resolve against today
4. `sb-people-update.sh <slug> set next_meeting_at "<ISO>"` + `meeting_location`, `meeting_agenda`, `meeting_status: scheduled`
5. If time conflicts with existing `next_meeting_at` → warn + confirm before overwriting
6. `bin/sb-commit.sh "appointment: <slug> <ISO>"`

**Query (`/sb this week`):**
1. `bin/sb-this-week.sh` — scans `people/*.md` for `next_meeting_at` in [today, today+7] AND `meeting_status: scheduled` (or absent)
2. Format output (Thai day name + time + person + location + agenda)

**Close (`/sb done` / `/sb cancel`):**
1. `sb-people-update.sh <slug> set meeting_status done|cancelled`
2. Append `## Notes` bullet summarizing outcome (ask user for short text if not provided)
3. `bin/sb-commit.sh "appointment-close: <slug> <status>"`

### ENCOUNTER — meetings logged without time commitment

Lightweight capture of "เจอคน" or "คุยกับ" — append-only dated bullets under `## Notes`.

**Add (`/sb เจอ`):**
1. Detect if name/handle is present in story
2. If named → `sb-people-update.sh <slug> ensure` then `add-note <today> <bullet>`
3. If anonymous → `journal/YYYY-MM-DD-HHMM.md` with `## People seen (unnamed)` section (descriptor + takeaway)
4. `bin/sb-commit.sh "encounter: <slug-or-anon>"`

**Detection heuristic (`/sb คน` ambiguity):**
- `bin/sb-encounter-detect.sh` reads input → returns `appointment` or `encounter`
- If `appointment` → route to APPOINTMENT-add
- If `encounter` → route to ENCOUNTER-add
- If genuinely ambiguous → ask 1 question before routing

**Query (`/sb follow-up`):**
1. `bin/sb-follow-up.sh` — scans all `people/*.md` for `## Follow-ups` section
2. Filters `- [ ]` (open) items
3. Sorts by `due` date ascending; items without due go last
4. Format output (due + text + person name)
```

- [ ] **Step 6: Verify changes via diff**

Run: `git -C /home/time/second-brain diff CLAUDE.md`

Expected: 3 hunks — (1) people schema extended, (2) journal schema extended, (3) routing table + APPOINTMENT/ENCOUNTER sections added. No other changes.

- [ ] **Step 7: Run all tests to verify nothing broke**

Run: `for t in /home/time/second-brain/tests/test-*.sh; do echo "=== $t ==="; bash "$t" || exit 1; done`

Expected: all tests pass, exit 0

- [ ] **Step 8: Commit**

```bash
cd /home/time/second-brain
git add CLAUDE.md
git commit -m "docs: extend CLAUDE.md with appointment + encounter ops (Task 6)"
```

---

## Task 7: End-to-End Smoke Test

**Files:**
- Create: `/home/time/second-brain/tests/test-e2e-smoke.sh`

**No production code changes** — verifies all helpers + CLAUDE.md contract work together.

- [ ] **Step 1: Write smoke test `tests/test-e2e-smoke.sh`**

```bash
#!/usr/bin/env bash
# End-to-end smoke: simulate /sb นัด → /sb this week → /sb done workflow
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-e2e-smoke"
source "$SCRIPT_DIR/helpers.sh"

PEOPLE_DIR="$FIX/people"
mkdir -p "$PEOPLE_DIR"

UPD="$VAULT/bin/sb-people-update.sh"
QUERY_WEEK="$VAULT/bin/sb-this-week.sh"
DETECT="$VAULT/bin/sb-encounter-detect.sh"

echo "[1. Detect appointment from natural language]"
result=$(echo 'พรุ่งนี้ 14:00 นัดเจอ beer ที่ร้าน XYZ คุย demo สินค้า' | bash "$DETECT")
assert_eq "$result" "appointment" "classifier returns appointment"

echo "[2. Capture appointment via people-update]"
tomorrow_iso="$(date -d '+1 day' +%Y-%m-%d)T14:00"
bash "$UPD" beer ensure "$PEOPLE_DIR"
bash "$UPD" beer set name "คุณเบียร์" "$PEOPLE_DIR"
bash "$UPD" beer set next_meeting_at "$tomorrow_iso" "$PEOPLE_DIR"
bash "$UPD" beer set meeting_location "ร้าน XYZ" "$PEOPLE_DIR"
bash "$UPD" beer set meeting_agenda "คุย demo สินค้า" "$PEOPLE_DIR"
bash "$UPD" beer set meeting_status "scheduled" "$PEOPLE_DIR"

assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "next_meeting_at: $tomorrow_iso" "appointment stored"

echo "[3. /sb this week surfaces it]"
out=$(bash "$QUERY_WEEK" "$PEOPLE_DIR")
assert_contains "$out" "คุณเบียร์" "person name in output"
assert_contains "$out" "ร้าน XYZ" "location in output"
assert_contains "$out" "คุย demo สินค้า" "agenda in output"

echo "[4. Add follow-up via people-update]"
bash "$UPD" beer add-followup "$(date +%Y-%m-%d)" "ส่ง slide deck หลัง demo" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "- [ ] $(date +%Y-%m-%d) — ส่ง slide deck หลัง demo" "followup recorded"

echo "[5. Add encounter note via people-update]"
bash "$UPD" beer add-note "2026-07-08" "เจอที่งาน Depry คุยเรื่อง X" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "- 2026-07-08: เจอที่งาน Depry คุยเรื่อง X" "encounter note recorded"

echo "[6. /sb done flips status"
bash "$UPD" beer set meeting_status "done" "$PEOPLE_DIR"
bash "$UPD" beer add-note "$(date +%Y-%m-%d)" "เสร็จ demo แล้ว ลูกค้าสนใจ" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "meeting_status: done" "status flipped"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "เสร็จ demo แล้ว" "completion note recorded"

echo "[7. After done, no longer in this-week query"
out2=$(bash "$QUERY_WEEK" "$PEOPLE_DIR")
! echo "$out2" | grep -q "beer" && pass "beer (done) excluded from this week" || fail "done excluded" "absent" "present"

echo ""
echo "✓ All e2e checks passed"
```

- [ ] **Step 2: Run smoke test**

```bash
chmod +x /home/time/second-brain/tests/test-e2e-smoke.sh
bash /home/time/second-brain/tests/test-e2e-smoke.sh
```

Expected: all `✓` lines, "All e2e checks passed"

- [ ] **Step 3: Run full test suite to confirm no regression**

```bash
for t in /home/time/second-brain/tests/test-*.sh; do
  echo "=== $(basename $t) ==="
  bash "$t" || { echo "FAILED: $t"; exit 1; }
done
```

Expected: all 6 test files pass

- [ ] **Step 4: Commit**

```bash
cd /home/time/second-brain
git add tests/test-e2e-smoke.sh
git commit -m "test: end-to-end smoke test for people-crm flow (Task 7)"
```

---

## Self-Review

**1. Spec coverage:**
- Data model (Section 1 of spec) → Task 1 (lib-frontmatter), Task 3 (people-update)
- Routes (Section 2) → CLAUDE.md updates in Task 6 (route table + op sections)
- Detection heuristic → Task 2
- This-week query → Task 4
- Follow-up query → Task 5
- Encounter fallback → Task 3 (add-note) + Task 6 (journal ## People seen extension in CLAUDE.md)
- Lifecycle (done/cancel) → Task 3 (set meeting_status) + Task 6 (op section)
- Error handling → Task 6 (CLAUDE.md warns about conflict detection in APPOINTMENT-add); conflict warning is manual step in flow
- Concurrency → existing flock via sb-commit.sh called from each op flow (Task 6 op sections)
- Privacy → out of scope per spec
- YAGNI list → confirmed not implemented
- Acceptance test scenarios (6 items) → covered: Tasks 1-5 + e2e Task 7

**2. Placeholder scan:**
- No "TBD/TODO/FIXME/implement later" — all code blocks complete
- No "add appropriate error handling" — error cases specified where they appear (Task 3 conflict warn, Task 6 ambiguity question)
- No "similar to Task N" — each task's code is self-contained

**3. Type consistency:**
- `fm_get`, `fm_set`, `fm_has` defined Task 1; consumed Tasks 3, 4, 5
- `sb-people-update.sh` actions: `ensure | set | add-note | add-followup` — used consistently across Tasks 3, 7
- `meeting_status` values: `scheduled | done | cancelled | no_show` — consistent with design spec
- `next_meeting_at` format: ISO 8601 `YYYY-MM-DDTHH:MM` — used in Tasks 3, 4, 7
- Slug format: kebab-case ASCII — consistent

All checks pass. Plan is complete and ready for execution.