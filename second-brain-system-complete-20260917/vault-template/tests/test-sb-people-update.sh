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

echo "[ensure: creates target dir if missing (G-003 fix)]"
G003_DIR="$FIX/people-deep/nested/who/does/not/exist/yet"
# Pre-condition: dir must NOT exist
[ ! -d "$G003_DIR" ] && pass "precondition: dir absent" || fail "precondition" "absent" "present"
# Defensive: real people/ must not contain alice.md before test (would mean a prior run leaked)
[ ! -f "$VAULT/people/alice.md" ] && pass "precondition: real people/ clean of alice.md" || fail "precondition" "absent" "leaked from prior run"
bash "$UPD" alice ensure "$G003_DIR" 2>&1
[ -d "$G003_DIR" ] && pass "helper created the dir" || fail "mkdir-p" "created" "missing"
[ -f "$G003_DIR/alice.md" ] && pass "file created in newly-mkdir-p'd dir" || fail "file" "exists" "missing"
# Defensive: real people/ must STILL not contain alice.md after test (catches G-003 regression)
[ ! -f "$VAULT/people/alice.md" ] && pass "no leak to real people/" || fail "leak check" "clean" "alice.md leaked to real people/"
# Cleanup so other tests don't see it
rm -rf "$FIX/people-deep"
