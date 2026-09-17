#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-encounter-anon"
source "$SCRIPT_DIR/helpers.sh"
ANON="$VAULT/bin/sb-encounter-anon.sh"

JOURNAL_DIR="$FIX/journal"
mkdir -p "$JOURNAL_DIR"

echo "[creates journal file with date frontmatter + People seen section]"
out=$(bash "$ANON" "ชายเสื้อแดงที่งาน Depry: เล่าเรื่อง X สนใจ Y" "$JOURNAL_DIR")
file="$out"
[ -f "$file" ] && pass "file created at $file" || fail "file created" "exists" "missing"
assert_contains "$(cat "$file")" "date: $(date +%Y-%m-%d)" "date frontmatter"
assert_contains "$(cat "$file")" "## People seen (unnamed)" "section header"
assert_contains "$(cat "$file")" "- ชายเสื้อแดงที่งาน Depry: เล่าเรื่อง X สนใจ Y" "bullet recorded"

echo "[second call same minute appends to same file]"
out2=$(bash "$ANON" "หญิงชุดดำบูธ 7: สนใจโปรแกรม" "$JOURNAL_DIR")
assert_eq "$out2" "$file" "same-minute file reused"
assert_contains "$(cat "$file")" "หญิงชุดดำบูธ 7" "second bullet appended"
bullet_count=$(grep -c '^- ' "$file")
assert_eq "$bullet_count" "2" "two bullets in same file"

echo "[filename is timestamped per-minute]"
[[ "$file" =~ [0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}\.md$ ]] && pass "filename matches YYYY-MM-DD-HHMM.md" || fail "filename pattern" "matches" "$file"
