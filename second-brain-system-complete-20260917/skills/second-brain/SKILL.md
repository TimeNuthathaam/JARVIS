---
name: second-brain
description: Use when the user wants to save something into, or recall something from, their personal knowledge vault (second brain) — saving a URL/YouTube/article/note, asking what they've saved about a topic, remembering a person they met (CRM), writing a journal entry, checking vault status, self-auditing session history, or viewing the knowledge graph. Triggers - "/sb", "second brain", "สมองสอง", "เซฟเข้าคลัง", "เก็บเข้าสมอง", "เคยเซฟเรื่อง...ไว้ไหม", "จดไว้ว่าเจอคุณ...", a bare URL sent with intent to save, "บันทึกไดอารี่", "journal", "ถามคลังความรู้", "/sb audit", "/sb graph", "ดูกราฟสมอง".
---

# second-brain — personal knowledge vault

The vault is selected as `VAULT="${SECOND_BRAIN_DIR:-$HOME/.second-brain}"`. Everything
you need to operate it is in the vault's own manual: **read `$VAULT/CLAUDE.md` first**,
then run the matching op.
Knowledge is typed into 4 folders (entities/concepts/comparisons/queries) governed by
**`$VAULT/SCHEMA.md`** — the agent routes; the user only ever types `/sb`.
This file only routes.

## Routing `/sb` input → op

| Input looks like | Op in vault CLAUDE.md |
|---|---|
| `/sb <url>` or a URL + "เซฟ/เก็บ/save" | INGEST |
| `/sb ถาม <q>` / a question about saved knowledge | ASK |
| `/sb คน <story>` / "เจอคุณ X ที่งาน..." / "X นี่ใครนะ" | PERSON |
| `/sb บันทึก <text>` / diary-like text about their day/feelings | JOURNAL |
| `/sb process` | PROCESS (work through unprocessed raw/) |
| `/sb สถานะ` / "status" | STATUS |
| `/sb audit` / `/sb audit N` / `/sb audit --project` | AUDIT (self-audit of Claude Code session history; dry-run first) |
| `/sb graph` / "ดูกราฟ" / "เปิดกราฟสมอง" | GRAPH (vault CLAUDE.md → Obsidian native graph, or /graphify for deep queries) |
| Ambiguous | Ask before acting — one short question (เก็บ / ค้น / journal?); if still unclear, run a `/grilling` interview (grill-me / grilling skill), then capture. |

## Hard rules (from the vault manual — enforced there too)

- **Understand before you store — if unsure, don't guess.** Ambiguous intent or content → ask the user first (for anything non-trivial, run a `/grilling` interview via the grill-me / grilling skill) and capture only once you've confirmed what they mean. Correct understanding → correct capture.
- Write ops finish with `bash "$VAULT/bin/sb-commit.sh" "<op>: <msg>"` — never `git commit` directly.
- ASK answers come from the vault only; if it's not in the vault, say so.
- INGEST saves to `raw/` FIRST, processes second — a timeout never loses the capture.
- Replies to the user: Thai, short, mobile-friendly (most traffic is Telegram); name the files you created/updated.
