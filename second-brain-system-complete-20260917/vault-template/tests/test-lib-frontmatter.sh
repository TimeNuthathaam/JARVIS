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
