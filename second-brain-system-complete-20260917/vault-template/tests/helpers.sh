#!/usr/bin/env bash
# Shared test helpers — source this from every test file.
set -euo pipefail
VAULT="${VAULT:-${SECOND_BRAIN_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}}"
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
