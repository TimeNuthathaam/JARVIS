#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")/second-brain-system-complete-20260917" && pwd)"
RUNTIME_DIR="${HOME}/.local/share/second-brain-system"
VAULT_DIR="${SECOND_BRAIN_DIR:-${HOME}/.second-brain}"
SKILL_DIR="${HOME}/.codex/skills"

mkdir -p "$RUNTIME_DIR" "$SKILL_DIR"
rsync -a "$SOURCE_DIR/vault-template/" "$RUNTIME_DIR/vault-template/"
rsync -a "$SOURCE_DIR/skills/" "$RUNTIME_DIR/skills/"

if [[ ! -e "$VAULT_DIR" ]]; then
  cp -R "$RUNTIME_DIR/vault-template" "$VAULT_DIR"
  find "$VAULT_DIR" -name .DS_Store -delete
fi

for skill in sb second-brain second-brain-audit; do
  ln -sfn "$RUNTIME_DIR/skills/$skill" "$SKILL_DIR/$skill"
done

cat <<EOF
Global second brain installed.
Vault: $VAULT_DIR
Runtime: $RUNTIME_DIR
Search: python3 $RUNTIME_DIR/vault-template/bin/sb-search.py --vault "$VAULT_DIR" search "..."
Skills: /sb, /second-brain, /second-brain-audit (available after restart)
EOF
