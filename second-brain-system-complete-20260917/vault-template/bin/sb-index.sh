#!/usr/bin/env bash
# Regenerate index.md from file frontmatter. Derived output — safe to rerun anytime.
# ponytail: no -e. Empty sections make `find|sort|while read` return non-zero; under
# set -e that aborts mid-generation, leaves index.md.tmp truncated, and index.md stale.
set -uo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"

fm() { # fm <file> <key> — first frontmatter value for key
  awk -v k="$2" 'NR==1&&$0!="---"{exit} /^---$/{c++; if(c==2)exit; next} c==1 && $0 ~ "^"k":" {sub("^"k":[ ]*",""); print; exit}' "$1"
}

{
  echo "# Index"
  echo
  echo "_สร้างอัตโนมัติโดย bin/sb-index.sh — อย่าแก้มือ อัปเดตล่าสุด $(date '+%Y-%m-%d %H:%M')_"
  for section in entities concepts comparisons queries Magic people journal raw; do
    echo
    case $section in
      entities)    echo "## Entities";;
      concepts)    echo "## Concepts";;
      comparisons) echo "## Comparisons";;
      queries)     echo "## Queries";;
      Magic)       echo "## Magic";;
      people)      echo "## People";;
      journal)     echo "## Journal";;
      raw)         echo "## Raw captures";;
    esac
    find "$VAULT/$section" -maxdepth 1 -name '*.md' 2>/dev/null | sort -r | while read -r f; do
      base=$(basename "$f" .md)
      title=$(fm "$f" title); [ -z "$title" ] && title=$(fm "$f" name); [ -z "$title" ] && title="$base"
      extra=""
      if [ "$section" = raw ]; then
        st=$(fm "$f" status); [ "$st" = raw ] && extra=" ⏳ยังไม่ process"
      fi
      al=$(fm "$f" aliases)
      [ -n "$al" ] && extra="$extra — aliases: $al"
      echo "- [[$section/$base|$title]]$extra"
    done
  done
} > "$VAULT/index.md.tmp"
mv "$VAULT/index.md.tmp" "$VAULT/index.md"
echo "index.md regenerated"
