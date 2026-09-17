#!/usr/bin/env bash
# Query: open follow-ups across all people/, sorted by due date.
# Usage: sb-follow-up.sh [people_dir]
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

people_dir="${1:-$VAULT/people}"
[ ! -d "$people_dir" ] && { echo "no people dir: $people_dir" >&2; exit 1; }

results=()
for f in "$people_dir"/*.md; do
  [ -f "$f" ] || continue
  name=$(fm_get "$f" name)
  [ -z "$name" ] && name=$(basename "$f" .md)

  # Extract ## Follow-ups section (handles missing next ## gracefully)
  # awk: from ## Follow-ups line to next ## at start-of-line (or EOF)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Skip done items
    echo "$line" | grep -q '^- \[x\]' && continue
    # Extract due date from "- [ ] YYYY-MM-DD — text" or "- [ ] ไม่มี due — text"
    if echo "$line" | grep -qE '^- \[ \] [0-9]{4}-[0-9]{2}-[0-9]{2}'; then
      due=$(echo "$line" | sed -nE 's/^- \[ \] ([0-9]{4}-[0-9]{2}-[0-9]{2}) — .*/\1/p')
      text=$(echo "$line" | sed -E 's/^- \[ \] [0-9]{4}-[0-9]{2}-[0-9]{2} — //')
    else
      due=""
      text=$(echo "$line" | sed -E 's/^- \[ \] //')
    fi
    sort_key="${due:-9999-99-99}"  # no-due sorts last
    results+=("$sort_key|$due|$name|$text")
  done < <(awk '
    /^## Follow-ups$/ { in_section=1; next }
    in_section && /^## / { exit }
    in_section { print }
  ' "$f")
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
