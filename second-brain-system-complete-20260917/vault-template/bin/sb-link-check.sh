#!/usr/bin/env bash
# Validate wikilinks in knowledge nodes touched by an /sb write operation.
# Usage: sb-link-check.sh entities/foo.md concepts/bar.md ...
set -euo pipefail

VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"

if (($# == 0)); then
  echo "usage: sb-link-check.sh <knowledge-node.md> [...]" >&2
  exit 2
fi

declare -A NOTE_PATHS=()
declare -A NOTE_STEM_COUNT=()

while IFS= read -r note; do
  rel="${note#"$VAULT"/}"
  rel_no_ext="${rel%.md}"
  stem="${rel_no_ext##*/}"
  NOTE_PATHS["$rel_no_ext"]=1
  NOTE_STEM_COUNT["$stem"]=$(( ${NOTE_STEM_COUNT["$stem"]:-0} + 1 ))
done < <(
  find "$VAULT" -type f -name '*.md' \
    -not -path "$VAULT/.git/*" \
    -not -path "$VAULT/graphify-out/*" \
    -not -path "$VAULT/output/*" \
    -print
)

errors=0
checked=0

for input in "$@"; do
  if [[ "$input" = /* ]]; then
    file="$input"
    rel="${file#"$VAULT"/}"
  else
    rel="$input"
    file="$VAULT/$rel"
  fi

  [[ -f "$file" ]] || continue
  [[ "$rel" =~ ^(entities|concepts|comparisons|queries|Magic)/.*\.md$ ]] || continue

  checked=$((checked + 1))
  source_no_ext="${rel%.md}"
  source_stem="${source_no_ext##*/}"
  resolved_non_self=0

  mapfile -t raw_links < <(grep -o '\[\[[^][]*\]\]' "$file" || true)

  for raw_link in "${raw_links[@]}"; do
    target="${raw_link#\[\[}"
    target="${target%\]\]}"
    target="${target%%|*}"
    target="${target%%#*}"
    target="${target#/}"
    [[ -n "$target" ]] || continue

    resolved=0
    if [[ -n "${NOTE_PATHS["$target"]:-}" ]]; then
      resolved=1
      [[ "$target" != "$source_no_ext" ]] && resolved_non_self=$((resolved_non_self + 1))
    elif [[ "$target" != */* && "${NOTE_STEM_COUNT["$target"]:-0}" -eq 1 ]]; then
      resolved=1
      [[ "$target" != "$source_stem" ]] && resolved_non_self=$((resolved_non_self + 1))
    fi

    if ((resolved == 0)); then
      echo "wikilink error: $rel -> [[$target]] does not resolve to one vault note" >&2
      errors=$((errors + 1))
    fi
  done

  if ((resolved_non_self == 0)); then
    echo "wikilink error: $rel has no resolved non-self wikilink" >&2
    errors=$((errors + 1))
  fi
done

if ((errors > 0)); then
  echo "wikilink check failed: $errors error(s)" >&2
  exit 1
fi

echo "wikilinks OK: $checked knowledge node(s)"
