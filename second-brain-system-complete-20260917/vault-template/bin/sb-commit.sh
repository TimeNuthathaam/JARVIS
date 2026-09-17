#!/usr/bin/env bash
# Single-writer finisher for vault ops: append to monthly log + git commit, serialized by flock.
# Usage: sb-commit.sh "<op>: <message>"
set -euo pipefail
VAULT="${SECOND_BRAIN_DIR:-${VAULT:-${HOME}/.second-brain}}"
MSG="${1:?usage: sb-commit.sh \"<op>: <message>\"}"

exec 9>"$VAULT/.sb.lock"
flock -w 30 9

mapfile -t CHANGED_KNOWLEDGE < <(
  {
    git -C "$VAULT" diff --name-only --diff-filter=ACMR HEAD
    git -C "$VAULT" ls-files --others --exclude-standard
  } | awk '/^(entities|concepts|comparisons|queries|Magic)\/.*\.md$/' | sort -u
)

mapfile -t CHANGED_RAW < <(
  {
    git -C "$VAULT" diff --name-only --diff-filter=ACMR HEAD
    git -C "$VAULT" ls-files --others --exclude-standard
  } | awk '/^raw\/.*\.md$/' | sort -u
)

# A capture is deliberately written to disk before PROCESS so it survives a
# timeout, but it must never be committed as a falsely completed write. Any raw
# file included in an /sb commit must already be processed, have a knowledge
# node touched in the same transaction, and be cited by a real node.
if ((${#CHANGED_RAW[@]})); then
  if ((${#CHANGED_KNOWLEDGE[@]} == 0)); then
    echo "flow error: raw capture changed but no knowledge node was created or updated" >&2
    echo "finish PROCESS (search/update, wikilinks, validation) before committing" >&2
    exit 1
  fi

  for rel in "${CHANGED_RAW[@]}"; do
    file="$VAULT/$rel"
    status=$(awk '
      NR == 1 && $0 != "---" { exit }
      /^---$/ { block++; if (block == 2) exit; next }
      block == 1 && /^status:[[:space:]]*/ {
        sub(/^status:[[:space:]]*/, ""); print; exit
      }
    ' "$file")
    if [[ "$status" != "processed" ]]; then
      echo "flow error: $rel is status '${status:-missing}', expected 'processed'" >&2
      echo "the capture remains safe on disk; complete it with /sb process" >&2
      exit 1
    fi

    raw_name=$(basename "$rel")
    cited=0
    while IFS= read -r node; do
      if awk '
        NR == 1 && $0 != "---" { exit }
        /^---$/ { block++; if (block == 2) exit; next }
        block == 1 && /^sources:/ { print }
      ' "$node" | grep -Fq -- "$raw_name"; then
        cited=1
        break
      fi
    done < <(find "$VAULT/entities" "$VAULT/concepts" "$VAULT/comparisons" "$VAULT/queries" "$VAULT/Magic" -maxdepth 1 -type f -name '*.md')

    if ((cited == 0)); then
      echo "flow error: $rel is not cited in any knowledge node's sources frontmatter" >&2
      exit 1
    fi
  done
fi

if ((${#CHANGED_KNOWLEDGE[@]})); then
  "$VAULT/bin/sb-link-check.sh" "${CHANGED_KNOWLEDGE[@]}"
fi

# index.md is derived state. Rebuild it inside the serialized finisher so an
# agent cannot forget this step and concurrent writers cannot leave it stale.
"$VAULT/bin/sb-index.sh"

# Keep the rebuildable retrieval sidecar fresh inside the same writer lock.
# Gemini failures remain pending and never block a durable Markdown capture;
# local parse/SQLite failures still stop the commit because that index would lie.
if [ -x "$VAULT/bin/sb-search.py" ]; then
  python3 "$VAULT/bin/sb-search.py" sync --best-effort
fi

printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M')" "$MSG" >> "$VAULT/log/$(date +%Y-%m).md"

cd "$VAULT"
git add -A
git diff --cached --quiet || git commit -q -m "$MSG"
echo "committed: $MSG"
