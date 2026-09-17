# codex-model

Run `codex-model z.ai/GLM-5.3-Flash --yolo` to start Codex with Z.AI's GLM model. Other Codex model IDs work as `codex-model MODEL [options]`. All options after the model are passed to Codex.

The Z.AI key is stored in `~/.config/codex-model/zai.key` with owner-only permissions. The wrapper uses Z.AI's Coding Plan Responses endpoint and does not change your default Codex configuration.
# JARVIS Memory Galaxy

A local Galaxy-style visual memory for a global Second Brain vault.

## Quick start

```bash
./install-global.sh
python3 server.py
```

Open <http://127.0.0.1:4700>.

The vault defaults to `~/.second-brain`. Override it with `SECOND_BRAIN_DIR=/path/to/vault python3 server.py`.

From any Codex project, the installed `/sb` skill uses the same global vault. Re-run `./install-global.sh` after changing files under `second-brain-system-complete-20260917/`.

## Issue tracker

This repository uses GitHub Issues. See `docs/agents/issue-tracker.md`.
