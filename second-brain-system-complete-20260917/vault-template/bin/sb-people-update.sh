#!/usr/bin/env bash
# People file frontmatter + body operations.
# Usage: sb-people-update.sh <slug> <action> [args...] [people_dir]
#   ensure                       — create empty file with frontmatter
#   set <key> <value>            — set frontmatter field
#   add-note <date> <bullet>     — append to ## Notes
#   add-followup <due> <text>    — append to ## Follow-ups
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

slug="${1:?usage: <slug> <action> [args...]}"
action="${2:?missing action}"
shift 2

# Optional trailing arg = people_dir (default vault people/)
# Detection: last arg is treated as a dir if it LOOKS like a path (contains "/").
# We do NOT require [ -d ... ] — that would fall through to default if the dir
# doesn't exist yet, and `ensure` would silently write to the wrong place.
# `mkdir -p` later in the action handles creation.
people_dir=""
last="${!#}"
if [ -n "$last" ] && [[ "$last" == */* ]]; then
  people_dir="$last"
  set -- "${@:1:$#-1}"
fi
[ -z "$people_dir" ] && people_dir="$VAULT/people"

file="$people_dir/$slug.md"

case "$action" in
  ensure)
    if [ ! -f "$file" ]; then
      # G-003: caller may not have created people_dir yet — do it ourselves
      # (matches sb-encounter-anon.sh pattern; prevents silent fallthrough
      # to a wrong dir via the trailing-[people_dir]-arg logic above)
      mkdir -p "$people_dir"
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
    # Auto-bump met_last only on actual contact:
    #   - setting next_meeting_at = scheduling/scheduling-change is a contact signal
    #   - meeting_status=done means the meeting happened
    #   - meeting_status=cancelled|no_show does NOT count as contact
    if [ "$key" = "next_meeting_at" ] || { [ "$key" = "meeting_status" ] && [ "$value" = "done" ]; }; then
      today="$(date +%Y-%m-%d)"
      fm_set "$file" met_last "$today"
    fi
    fm_set "$file" updated "$(date +%Y-%m-%d)"
    ;;

  add-note)
    date="${1:?missing date}"
    bullet="${2:?missing bullet}"
    today="$(date +%Y-%m-%d)"
    # Ensure ## Notes section exists (mirrors add-followup pattern)
    if ! grep -q '^## Notes' "$file"; then
      printf '\n## Notes (เรียงเวลา ใหม่สุดบน)\n' >> "$file"
    fi
    # Single pass: update frontmatter met_last+updated AND insert note bullet at first ## Notes
    awk -v d="$date" -v b="$bullet" -v t="$today" '
      BEGIN { inserted=0 }
      # Frontmatter: update met_last and updated in one pass
      NR == 1 && $0 != "---" { print "---"; fm=1; next }
      fm && /^---$/ { fm=0; next }
      fm && /^met_last:/ { print "met_last: " t; next }
      fm && /^updated:/ { print "updated: " t; next }
      # Body: insert bullet after FIRST ## Notes header only
      !inserted && /^## Notes/ { print; print "- " d ": " b; inserted=1; next }
      { print }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
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
