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
tomorrow_iso="$(python3 -c 'import datetime; print((datetime.date.today() + datetime.timedelta(days=1)).isoformat())')T14:00"
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

echo "[6. /sb done flips status]"
bash "$UPD" beer set meeting_status "done" "$PEOPLE_DIR"
bash "$UPD" beer add-note "$(date +%Y-%m-%d)" "เสร็จ demo แล้ว ลูกค้าสนใจ" "$PEOPLE_DIR"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "meeting_status: done" "status flipped"
assert_contains "$(cat "$PEOPLE_DIR/beer.md")" "เสร็จ demo แล้ว" "completion note recorded"

echo "[7. After done, no longer in this-week query]"
out2=$(bash "$QUERY_WEEK" "$PEOPLE_DIR")
if echo "$out2" | grep -qF "beer"; then
  fail "beer (done) excluded from this week" "absent" "present"
else
  pass "beer (done) excluded from this week"
fi

echo "[8. Anonymous encounter → journal fallback]"
ANON="$VAULT/bin/sb-encounter-anon.sh"
JOURNAL_DIR="$FIX/journal"
mkdir -p "$JOURNAL_DIR"
out3=$(bash "$ANON" "ชายเสื้อแดงที่งาน Depry: เล่าเรื่อง X สนใจ Y" "$JOURNAL_DIR")
anon_file="$out3"
[ -f "$anon_file" ] && pass "anon journal file created" || fail "anon journal file" "exists" "missing"
assert_contains "$(cat "$anon_file")" "date: $(date +%Y-%m-%d)" "anon date frontmatter"
assert_contains "$(cat "$anon_file")" "## People seen (unnamed)" "anon section header"
assert_contains "$(cat "$anon_file")" "ชายเสื้อแดงที่งาน Depry" "anon bullet"

echo ""
echo "✓ All e2e checks passed"
