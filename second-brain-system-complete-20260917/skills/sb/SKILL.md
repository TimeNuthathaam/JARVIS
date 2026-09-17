---
name: sb
description: Shortcut alias for the second-brain skill — lets the user type /sb to save into or recall from their personal knowledge vault.
disable-model-invocation: true
---

`/sb` is a shortcut for the **second-brain** skill.

Load `~/.codex/skills/second-brain/SKILL.md` and follow it exactly: read
`"${SECOND_BRAIN_DIR:-$HOME/.second-brain}/CLAUDE.md"` first, then route this `/sb` input to the matching
op (INGEST / ASK / PERSON / JOURNAL / PROCESS / STATUS) per its table. Do not
reimplement — the vault manual at `"${SECOND_BRAIN_DIR:-$HOME/.second-brain}/CLAUDE.md"` is the source of truth.
