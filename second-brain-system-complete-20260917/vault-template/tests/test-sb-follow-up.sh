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
