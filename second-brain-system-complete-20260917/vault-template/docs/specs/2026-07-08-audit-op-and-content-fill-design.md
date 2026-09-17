# Second Brain — Content-Fill + AUDIT Op (approved 2026-07-08)

## Context

Vault was built 2026-07-06 (`docs/specs/2026-07-06-second-brain-design.md`) but is still
empty — 1 unprocessed raw capture, no `wiki/`/`people/`/`journal/` content. Two YouTube
videos watched today (via `/listen`, reports at `/home/time/watch-output/Chase_AI/`) both
described a "self-audit" pattern: scan past Claude Code session transcripts, cluster
repeated patterns, surface candidates for new skills/automations — diagnosis-only, human
reviews before anything is created. This spec covers (1) finally putting real content in
the vault, and (2) adding that self-audit pattern as a new vault op.

Reviewed with the model-advisor (Opus) before locking in; its feedback is incorporated
below (AUDIT scope, dry-run requirement, `audit/` landing folder, NEOKNOWLEDGE relationship
line).

## 1. Content-fill

Process the 1 pending raw capture (`raw/2026-07-04-matt-wolfe-ai-second-brain.md`) +
ingest the 2 new Chase AI video reports as new `raw/` files, then run PROCESS on all 3 per
the vault's existing rules (`CLAUDE.md` → PROCESS).

Topic-first, not one-page-per-video — the vault's PROCESS rule already says "prefer
updating an existing wiki page over creating a new one." All 3 sources overlap on
second-brain/self-audit themes, so expect them to compound into a handful of shared pages
rather than 3 separate ones, e.g.:
- `wiki/second-brain-obsidian-pattern.md`
- `wiki/claude-code-self-audit.md`
- `wiki/fable-5-effort-economics.md`
- `wiki/skill-hygiene-audit.md`

No new mechanism — this is running the existing INGEST/PROCESS ops on real input.

## 2. New op: AUDIT

Added as a 6th entry in `/home/time/second-brain/CLAUDE.md`'s Operations table, alongside
INGEST/PROCESS/ASK/PERSON/JOURNAL/STATUS.

**Boundary note:** AUDIT is the only op that reads *outside* the vault (Claude Code session
transcripts under `~/.claude/projects/**/*.jsonl`). Its output still lands inside the vault
as markdown, same as every other op — it does not become a separate tool.

**Trigger:** `/sb audit [N|--project]`
- Default: `N=20` most recent sessions (one session = one `~/.claude/projects/**/*.jsonl`
  file, ordered by file mtime descending), **across all projects** (not scoped to one
  project) — clustering repeated patterns needs cross-project volume; a single project's
  session count is too thin to find repetition.
- `--project` narrows to the current project's sessions only, same N/ordering rule.
- Hard cap: `N` cannot exceed 100 regardless of argument, to prevent a runaway scan (this
  machine has 5,491 session transcripts / 1.9GB in the last 30 days across dozens of
  projects — nothing close to the 30-day/39-session scope the source videos demoed on).

**Step 0 — dry-run (always, before reading anything):** print matched scope — file count
and rough total size — so a bad invocation is visible before it burns tokens reading
gigabytes of transcript.

**Step 1:** sub-agents pull raw signals from the matched session transcripts, cluster into
repeated patterns.

**Step 2:** for each cluster, decide a candidate: new skill / new automation / fix / nothing.

**Step 3:** write results to `audit/candidates-YYYY-MM-DD-HHMM.md` (new top-level vault
folder, sibling to `raw/`/`wiki/`/`people/`/`journal/`/`log/`) — timestamped like
`journal/`, never overwritten, so re-running AUDIT the same day doesn't clobber an earlier
run. Diagnosis output is dated and disposable, not evergreen knowledge — it does not belong
in `wiki/`.

**Hard rule:** AUDIT never auto-creates skills/automations and is never scheduled/cron'd.
Diagnosis only; the user acts on candidates manually. Finishes with
`bin/sb-commit.sh "audit: <scope>"` like every other op.

## 3. Obsidian — deferred, not part of this rollout

Obsidian (the app) is already installed (`/usr/bin/obsidian`, `obsidian 1.12.7`) but this
vault has never been registered/opened in it — only `Downloads/2ndBrain/obsidianFolder/2ndbrain`
(NEOKNOWLEDGE's vault) is currently registered. Per the original spec, Obsidian is an
optional "level 2 viewer" only — no vault op depends on it.

**Trigger for later:** register `/home/time/second-brain/` in Obsidian (Open folder as
vault) once it has real content worth browsing, or once graph-view is actually wanted.
10-second action, zero cost to defer.

## 4. Relationship to NEOKNOWLEDGE (`/home/time/Downloads/2ndBrain/`)

Different jobs, not meant to merge:
- **`/home/time/second-brain/`** (this vault) — fast, low-friction personal capture:
  notes, journal, CRM, self-audit. Zero infra (markdown + git only).
- **NEOKNOWLEDGE** (`Downloads/2ndBrain/`) — structured multi-tenant knowledge work (e.g.
  client chat archives) that needs graph queries, conflict resolution, Neo4j + NotebookLM
  RAG. Heavier infra, different use case.

If this line stops being true (e.g. this vault grows into needing graph queries), revisit
— don't silently duplicate effort across both.

## Out of scope (this build)

- Semantic search / vector DB (unchanged from original spec)
- Telegram bot (unchanged)
- Scheduled/automated AUDIT runs — manual trigger only, for now
- Merging or migrating content between this vault and NEOKNOWLEDGE
