#!/usr/bin/env bash
# Heuristic: appointment vs encounter detection from /sb คน input.
# Reads STDIN (not argv). Prints "appointment" or "encounter".
# Usage:  echo "นัด beer พรุ่งนี้ 14:00 ที่ร้าน X demo" | sb-encounter-detect.sh
set -euo pipefail
input="$(cat)"

# Appointment signals (any one triggers):
#   - explicit time format HH:MM or HH.MM
#   - Thai time markers (โมง, นาฬิกา)
#   - date keywords (พรุ่งนี้, มะรืน, อาทิตย์หน้า, วัน..., next..., monday..sunday)
#   - intent keywords (นัด, พบ, meet, schedule)
if echo "$input" | grep -qE '[0-9]{1,2}[:.][0-9]{2}'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qE 'โมง|นาฬิกา'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qiE 'พรุ่งนี้|มะรืน|อาทิตย์หน้า|เดือนหน้า|วันจันทร์|วันอังคาร|วันพุธ|วันพฤหัส|วันศุกร์|วันเสาร์|วันอาทิตย์|next (monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month)'; then
  echo "appointment"; exit 0
fi
if echo "$input" | grep -qiE '([[:space:]]|^)นัด([[:space:]]|$)|([[:space:]]|^)พบ([[:space:]]|$)|([[:space:]]|^)meet[[:space:]]|([[:space:]]|^)schedule'; then
  echo "appointment"; exit 0
fi

# Default: encounter (safer — user can re-run with /sb นัด explicitly if needed)
echo "encounter"
