#!/usr/bin/env bash
# Append an anonymous encounter to today's journal under "## People seen (unnamed)".
# Use when /sb เจอ has no name/handle to resolve to a people/<slug>.md.
# Usage: sb-encounter-anon.sh <bullet> [journal_dir]
#   <bullet> is a single line, typically "<descriptor>: <takeaway>".
#   Idempotency: timestamped filename (per-minute) creates a new file each call,
#   so multiple encounters in the same minute land in the same file.
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"

bullet="${1:?usage: sb-encounter-anon.sh <bullet> [journal_dir]}"
journal_dir=""
if [ -d "${!#}" ]; then
  journal_dir="${!#}"
fi
[ -z "$journal_dir" ] && journal_dir="$VAULT/journal"
mkdir -p "$journal_dir"

stamp="$(date +%Y-%m-%d-%H%M)"
today="$(date +%Y-%m-%d)"
file="$journal_dir/${stamp}.md"

if [ ! -f "$file" ]; then
  cat > "$file" <<EOF
---
date: $today
---

## People seen (unnamed)

- $bullet
EOF
else
  # Append to existing same-minute file under the same section
  echo "- $bullet" >> "$file"
fi

echo "$file"
