#!/usr/bin/env bash
# Query: appointments in next 7 days with meeting_status: scheduled.
# Usage: sb-this-week.sh [people_dir]
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

people_dir="${1:-$VAULT/people}"
[ ! -d "$people_dir" ] && { echo "no people dir: $people_dir" >&2; exit 1; }

today_epoch="$(date +%s)"
week_epoch="$(python3 -c 'import time; print(int(time.time() + 7 * 86400))')"
iso_epoch() {
  python3 - "$1" <<'PY'
import datetime, sys
try:
    value = datetime.datetime.fromisoformat(sys.argv[1])
    if value.tzinfo:
        value = value.astimezone()
    print(int(value.timestamp()))
except (ValueError, OverflowError):
    pass
PY
}

# Collect appointments in window
results=()
for f in "$people_dir"/*.md; do
  [ -f "$f" ] || continue
  next=$(fm_get "$f" next_meeting_at)
  [ -z "$next" ] && continue

  # Status filter: only scheduled (or absent status = assume scheduled)
  status=$(fm_get "$f" meeting_status)
  [ -n "$status" ] && [ "$status" != "scheduled" ] && continue

  # Parse next_meeting_at → epoch
  appt_epoch=$(iso_epoch "$next")
  [ -n "$appt_epoch" ] || continue
  [ "$appt_epoch" -lt "$today_epoch" ] && continue
  [ "$appt_epoch" -gt "$week_epoch" ] && continue

  name=$(fm_get "$f" name)
  [ -z "$name" ] && name=$(basename "$f" .md)
  location=$(fm_get "$f" meeting_location)
  agenda=$(fm_get "$f" meeting_agenda)

  # Format date for display: "พ. 9 ก.ค." style — keep simple Thai day name
  read -r thai_day day_part time_part < <(python3 - "$next" <<'PY'
import datetime, sys
days = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
value = datetime.datetime.fromisoformat(sys.argv[1])
if value.tzinfo:
    value = value.astimezone()
print(days[value.weekday()], value.strftime("%d %b"), value.strftime("%H:%M"))
PY
  )

  results+=("$thai_day $day_part $time_part|$name|$location|$agenda")
done

if [ "${#results[@]}" -eq 0 ]; then
  echo "📅 สัปดาห์นี้ไม่มีนัดหมาย"
  exit 0
fi

echo "📅 สัปดาห์นี้คุณมีนัด ${#results[@]} อย่าง:"
echo
i=1
for r in "${results[@]}"; do
  IFS='|' read -r when name loc agenda <<< "$r"
  echo "$i. $when — $name${loc:+ ($loc)}"
  [ -n "$agenda" ] && echo "   └─ $agenda"
  i=$((i + 1))
done
echo
echo "\`/sb done <slug>\` เมื่อเสร็จแล้ว"
exit 0
