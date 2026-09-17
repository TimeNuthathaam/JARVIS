#!/usr/bin/env bash
# YAML frontmatter read/parse/write helpers — single source of truth.
# Usage: source this file. Provides fm_get, fm_set, fm_has.
set -euo pipefail

# fm_get <file> <key> — print value of frontmatter key (empty if missing)
fm_get() {
  local file="$1" key="$2"
  awk -v k="$key" '
    NR==1 && $0 != "---" { exit }
    /^---$/ { c++; if (c == 2) exit; next }
    c == 1 && $0 ~ "^"k":[[:space:]]*" {
      sub("^"k":[[:space:]]*", "")
      print
      exit
    }
  ' "$file"
}

# fm_has <file> <key> — exit 0 if key exists, 1 if not
fm_has() {
  local file="$1" key="$2"
  fm_get "$file" "$key" | grep -q . && return 0 || return 1
}

# fm_set <file> <key> <value> — in-place rewrite, preserves body
fm_set() {
  local file="$1" key="$2" value="$3"
  local tmp="${file}.tmp.$$"

  awk -v k="$key" -v v="$value" '
    NR==1 && $0 != "---" { print "---"; fm_open=1 }
    /^---$/ {
      if (c == 0) { print; c=1; next }
      if (c == 1) {
        if (!wrote && k != "") { print k": "v }
        print
        wrote=1
        c=2
        next
      }
    }
    c == 1 {
      if ($0 ~ "^"k":[[:space:]]*") {
        print k": "v
        wrote=1
        next
      }
      print
      next
    }
    { print }
  ' "$file" > "$tmp"

  # If key was missing, insert before closing ---
  if ! grep -q "^${key}:" "$tmp"; then
    awk -v k="$key" -v v="$value" '
      /^---$/ && c == 1 { print k": "v }
      { print }
      /^---$/ { c++ }
    ' "$file" > "$tmp"
  fi

  mv "$tmp" "$file"
}
