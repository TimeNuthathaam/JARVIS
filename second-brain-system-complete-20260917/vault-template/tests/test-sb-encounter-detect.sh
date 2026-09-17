#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_NAME="test-sb-encounter-detect"
source "$SCRIPT_DIR/helpers.sh"
DETECT="$VAULT/bin/sb-encounter-detect.sh"

echo "[appointment signals]"
assert_eq "$(echo 'พรุ่งนี้ 14:00 นัดเจอ beer ที่ร้าน XYZ' | bash "$DETECT")" "appointment" "พรุ่งนี้ + เวลา"
assert_eq "$(echo 'นัด 9 ก.ค. 14:00 demo สินค้า' | bash "$DETECT")" "appointment" "explicit นัด + date"
assert_eq "$(echo 'เจอ beer วันศุกร์ 10:30' | bash "$DETECT")" "appointment" "เจอ + date + time"
assert_eq "$(echo 'next monday 9am meet pim' | bash "$DETECT")" "appointment" "English appointment"

echo "[encounter signals]"
assert_eq "$(echo 'เจอชายเสื้อแดงที่งาน Depry คุยเรื่อง X' | bash "$DETECT")" "encounter" "เจอ without time"
assert_eq "$(echo 'คุยกับ beer เรื่อง contract' | bash "$DETECT")" "encounter" "คุย + name, no time"
assert_eq "$(echo 'met stranger at coffee shop, talked about cold brew' | bash "$DETECT")" "encounter" "English encounter"

echo "[empty input]"
assert_eq "$(echo '' | bash "$DETECT")" "encounter" "empty defaults to encounter (safer)"
