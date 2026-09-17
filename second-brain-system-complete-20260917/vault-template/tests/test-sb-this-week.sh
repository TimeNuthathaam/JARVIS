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
future_date() { python3 -c 'import datetime, sys; print((datetime.date.today() + datetime.timedelta(days=int(sys.argv[1]))).isoformat())' "$1"; }
TOMORROW="$(future_date 1)T14:00"
NEXT_WEEK="$(future_date 6)T10:00"
FAR_FUTURE="$(future_date 30)T09:00"

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

# Fixture 5: appointment tomorrow but cancelled (should NOT appear)
cat > "$PEOPLE_DIR/cancelled.md" <<EOF
---
name: cancelled
next_meeting_at: $TOMORROW
meeting_status: cancelled
---
EOF

# Fixture 6: appointment tomorrow but no_show (should NOT appear)
cat > "$PEOPLE_DIR/noshow.md" <<EOF
---
name: noshow
next_meeting_at: $TOMORROW
meeting_status: no_show
---
EOF

# Fixture 7: no frontmatter (should NOT appear, no crash)
cat > "$PEOPLE_DIR/empty.md" <<EOF
---
name: empty
---
EOF

echo "[shows tomorrow appointment]"
out=$(bash "$QUERY" "$PEOPLE_DIR")
assert_contains "$out" "beer" "beer appears"
assert_contains "$out" "$(future_date 1 | awk -F- '{print $3}')" "tomorrow's day-of-month appears"

echo "[shows appointment within 7 days]"
assert_contains "$out" "pim" "pim (6 days out) appears"

echo "[excludes appointment > 7 days]"
! echo "$out" | grep -q "far" && pass "far (30d) excluded" || fail "far excluded" "absent" "present"

echo "[excludes done appointments]"
! echo "$out" | grep -q " — done" && pass "done excluded" || fail "done excluded" "absent" "present"

echo "[excludes cancelled appointments]"
! echo "$out" | grep -q " — cancelled" && pass "cancelled excluded" || fail "cancelled excluded" "absent" "present"

echo "[excludes no_show appointments]"
! echo "$out" | grep -q " — noshow" && pass "no_show excluded" || fail "no_show excluded" "absent" "present"

echo "[handles empty file gracefully]"
echo "$out" | grep -q "empty" && fail "empty file ignored" "absent" "present" || pass "empty file ignored"
