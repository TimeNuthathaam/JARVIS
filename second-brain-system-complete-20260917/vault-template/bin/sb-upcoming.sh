#!/usr/bin/env bash
# Query: recurring important dates (วันเกิด/วันครบรอบ) in the next N days.
# Complements sb-this-week.sh — that one reads one-shot appointments (next_meeting_at);
# THIS one reads the `## วันสำคัญ` section and rolls recurring 🔄 dates forward yearly.
# Usage: sb-upcoming.sh [days] [people_dir]   (defaults: 14, $VAULT/people)
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"
LIB="$VAULT/bin/lib-frontmatter.sh"
source "$LIB"

days="${1:-14}"
people_dir="${2:-$VAULT/people}"
[ ! -d "$people_dir" ] && { echo "no people dir: $people_dir" >&2; exit 1; }

# Regex (defined once; reused in the loop). วันสำคัญ line: "- <label>: YYYY-MM-DD [🔄]"
date_re='^[[:space:]]*-[[:space:]]*([^:]+):[[:space:]]*([0-9]{4}-[0-9]{2}-[0-9]{2})'

today_epoch=$(python3 - <<'PY'
import datetime
print(int(datetime.datetime.combine(datetime.date.today(), datetime.time()).timestamp()))
PY
)
this_year=$(date +%Y)
window=$(( days * 86400 ))

# Thai month abbrev for display
thai_month() {
  python3 - "$1" <<'PY'
import datetime, sys
months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
value = datetime.date.fromisoformat(sys.argv[1])
print(f"{value.day:02d} {months[value.month - 1]}")
PY
}

results=()
for f in "$people_dir"/*.md; do
  [ -f "$f" ] || continue
  base=$(basename "$f" .md)
  [ "${base:0:1}" = "_" ] && continue          # skip _TEMPLATE etc.

  name=$(fm_get "$f" name); [ -z "$name" ] && name="$base"

  # Extract the `## วันสำคัญ` section body (until the next `## ` header).
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [[ "$line" =~ $date_re ]]; then
      label="${BASH_REMATCH[1]}"; date="${BASH_REMATCH[2]}"
      recurring=0; [[ "$line" == *"🔄"* ]] && recurring=1
      mm="${date:5:2}"; dd="${date:8:2}"

      if [ "$recurring" = "1" ]; then
        anniv="$this_year-$mm-$dd"
        anniv_epoch=$(python3 - "$anniv" <<'PY'
import datetime, sys
try:
    value = datetime.datetime.fromisoformat(sys.argv[1])
    if value.tzinfo:
        value = value.astimezone()
    print(int(value.timestamp()))
except (ValueError, OverflowError):
    pass
PY
        )
        # already passed this year? roll to next year
        if [ "$anniv_epoch" -lt "$today_epoch" ]; then
          anniv_epoch=$(python3 - "$((this_year+1))-$mm-$dd" <<'PY'
import datetime, sys
try:
    print(int(datetime.datetime.combine(datetime.date.fromisoformat(sys.argv[1]), datetime.time()).timestamp()))
except (ValueError, OverflowError):
    pass
PY
          )
          disp_year=$((this_year+1))
        else
          disp_year=$this_year
        fi
      else
        anniv="$date"
        anniv_epoch=$(python3 - "$date" <<'PY'
import datetime, sys
try:
    value = datetime.datetime.fromisoformat(sys.argv[1])
    if value.tzinfo:
        value = value.astimezone()
    print(int(value.timestamp()))
except (ValueError, OverflowError):
    pass
PY
        )
        disp_year="${date:0:4}"
      fi

      [ "$anniv_epoch" -lt "$today_epoch" ] && continue
      [ $(( anniv_epoch - today_epoch )) -gt "$window" ] && continue

      d=$(( (anniv_epoch - today_epoch) / 86400 ))
      disp=$(thai_month "$anniv")
      results+=("$(printf '%03d|%s|%s|%s %s' "$d" "$name" "$label" "$disp" "$disp_year")")
    fi
  done < <(awk '/^## วันสำคัญ/{s=1;next} /^## /{s=0} s' "$f")
done

if [ "${#results[@]}" -eq 0 ]; then
  echo "🔔 ไม่มีวันสำคัญใน $days วันข้างหน้า"
  exit 0
fi

# Sort by days-until (first pipe-field is zero-padded), then pretty-print
printf '%s\n' "${results[@]}" | sort -t'|' -k1,1n | awk -F'|' '
{
  d=$1+0
  label=$3 " " $2
  when=$4
  if (d==0)      when2="วันนี้"
  else if (d==1) when2="พรุ่งนี้"
  else           when2="อีก " d " วัน"
  printf "🎂 %s — %s (%s)\n", label, when2, when
}'
exit 0
