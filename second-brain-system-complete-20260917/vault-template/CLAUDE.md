# Second Brain — Operating Manual

This folder is a personal knowledge vault (Karpathy LLM-wiki architecture: typed
knowledge folders + people/CRM + journal). Any Claude session working here — terminal,
ClaudeClaw Telegram bot, or the `second-brain` skill — follows this manual. **Read
`SCHEMA.md` before writing any knowledge node** (it owns the taxonomy + routing rules).
Set `VAULT="${SECOND_BRAIN_DIR:-$HOME/.second-brain}"` and use absolute paths under
`$VAULT` (agent sessions may have a different cwd).

## Language rule

Knowledge nodes, people notes, and journal replies: **Thai**, keeping English technical
terms as-is (HIFU, hook, retention…). Source quotes stay in their original language.

## Folder contract

| Path | Rule |
|---|---|
| `raw/` | Immutable captures. One file per capture: `YYYY-MM-DD-<slug>.md`. Never edit content after saving; only the `status:` frontmatter flips `raw` → `processed`. |
| `raw/assets/` | Images for captures, prefix with the same slug. |
| `inbox/` | Personal drop zone. Put Markdown, images, PDFs, or other source files here, then run `/sb process`. Files stay local and are intentionally not committed until they are processed into `raw/`; do not create knowledge nodes here. |
| `entities/` `concepts/` `comparisons/` `queries/` `Magic/` | Typed knowledge folders — which one gets what is governed by `SCHEMA.md` (read it first). `Magic/` is the personal Thai-magic collection; topic-synthesis/overview pages otherwise live in `concepts/`; answered research questions persist in `queries/`. |
| `people/` | One file per person: `<slug>.md`. Update in place (single-writer per person is acceptable). |
| `journal/` | One file per entry: `YYYY-MM-DD-HHMM.md`. Never edit old entries. |
| `log/` | Monthly log `YYYY-MM.md`. Append ONLY via `bin/sb-commit.sh` (it takes the flock). |
| `audit/` | AUDIT op output only, one file per run: `candidates-YYYY-MM-DD-HHMM.md`. Never hand-edit, never auto-executed. |
| `output/` | Deliverables built FROM the vault (write-ups, slide decks, exports) — Karpathy 3-zone: `raw/`=unstructured, knowledge folders+`people/`+`journal/`=structured, `output/`=output. Never a source; never cite output/ in a node's `sources:`. |
| `.sb/` | Derived SQLite hybrid-search state (FTS5 + Gemini embeddings). Gitignored, rebuildable, never a source of truth. |
| `index.md` | Derived. Regenerate with `bin/sb-index.sh`; never hand-edit. |

## Concurrency rules (multiple bots + terminals share this vault)

1. Create new files; don't append to shared markdown files.
2. After any writing op, finish with ONE call: `bin/sb-commit.sh "<op>: <short message>"` —
   it flock-serializes validation, index regeneration, log append, and git commit.
   Never run `git commit` directly.
3. Ops must be idempotent: check `status:` before processing; skip `processed` files.

## Frontmatter schemas

**raw/**: `title, source_url, captured, type: youtube|article|tweet|note|file, status: raw|processed, tags`
**knowledge folders** (entities/concepts/comparisons/queries — same schema): `title, aliases: [Thai and English synonyms — REQUIRED, this is what makes search work], updated, sources: [raw file names or origin]`
**people/**: `name, aliases, met_first, met_last, org?, role?, contact?, next_meeting_at?, meeting_location?, meeting_agenda?, meeting_status?, sources, updated` — only `name, aliases, met_first, met_last, sources, updated` are required at creation; the rest are contextually optional. `met_first`/`met_last` ISO dates; `next_meeting_at` ISO 8601 datetime; `meeting_status` ∈ {scheduled, done, cancelled, no_show}
**journal/**: `date, mood (optional)` — optional body section `## People seen (unnamed)` for anonymous encounter fallback (one-line per person: descriptor + takeaway)
**audit/**: `scope, session_count, generated`

## Understand before you store (ask, don't guess)

Correct capture depends on correct understanding. If intent or content is ambiguous —
unclear which op, which topic, whose note, or what actually matters — **ask one short
question and wait** before writing anything. A wrong capture pollutes the vault and its
search; a quick question is cheaper than a bad file. In a Claude Code session, run a
`/grilling` interview (grill-me skill) for anything non-trivial. Never invent facts to fill
a gap — store only what the user actually meant.

## Filename choice before `/sb` writes

ก่อนสร้าง knowledge node ใหม่จาก `/sb` ต้องเสนอชื่อไฟล์ที่ตั้งใจใช้ก่อนเสมอ แล้วรอเจ้าของเลือก:

- `ไทย: <ชื่อไทย>.md`
- `ENG: <english-kebab-case>.md`

ห้ามสร้าง node จนกว่าจะได้รับคำตอบว่าเลือกแบบใด. ข้อยกเว้นคือ `raw/`, `journal/`, และ `audit/` ที่มีรูปแบบวันที่บังคับอยู่แล้ว, และการอัปเดต node เดิมที่ต้องคงชื่อไฟล์เดิม.

## Routing `/sb` input → op

| Input | Op |
|---|---|
| URL / text / file | INGEST |
| `/sb process [file]` | PROCESS |
| `/sb ask <q>` | ASK |
| `/sb search <q>` | SEARCH (ranked context without answer write-back) |
| `/sb reindex` | REINDEX (rebuild derived FTS5 + Gemini index) |
| `/sb person <name>` | PERSON |
| `/sb journal <text>` | JOURNAL |
| `/sb status` | STATUS |
| `/sb audit [N\|--project]` | AUDIT |
| `/sb graph` | GRAPH |
| `/sb นัด <story>` | APPOINTMENT-add (creates/updates `next_meeting_at` + frontmatter on existing person) |
| `/sb เจอ <story>` | ENCOUNTER-add (appends `## Notes` bullet; falls back to `journal/ ## People seen` if unnamed) |
| `/sb this week` | APPOINTMENT-query (lists scheduled meetings in next 7 days) |
| `/sb follow-up` | ENCOUNTER-query (lists open `## Follow-ups` across all people, sorted by due) |
| `/sb done <slug>` | APPOINTMENT-close (flips `meeting_status: done` + appends `## Notes` summary) |
| `/sb cancel <slug>` | APPOINTMENT-close (flips `meeting_status: cancelled` + asks for reason, appends to Notes) |

## Operations

### INGEST — save something into the brain
Input: a URL, text, or file reference.
1. Build the raw file **first** (capture must survive even if later steps die):
   - **YouTube**: `yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en.*,th.*" --sub-format vtt -o "$VAULT/raw/assets/%(id)s" '<url>'` then convert VTT → plain text lines (strip timestamps/dupes); get title/channel/duration via `yt-dlp --print '%(title)s|%(channel)s|%(duration_string)s' <url>`. If a `watch` skill report already exists for this video, copy it as the raw file instead.
   - **Article/web**: fetch HTML (`curl -sL`), strip to readable text (`python3 -c` with html2text if available, else strip tags crudely). If the fetch is blocked, save the URL + user's note and mark `type: note`.
   - **Plain text from user**: save as `type: note`.
2. Write `raw/YYYY-MM-DD-<slug>.md` with frontmatter (`status: raw`) + content.
3. Immediately run PROCESS **for that one file** (see below).
4. Reply: what was saved, which wiki pages were created/updated.
If step 3 fails or times out, the capture is safe — say so and point to `/sb process`.

### PROCESS — turn inbox/raw material into knowledge nodes
For `/sb process`, first stage every file in `inbox/` (or the named inbox file), then process each `raw/*.md` with `status: raw` (or the specific raw file):
1. **Stage inbox files before interpretation.** Give each capture a date+slug. Move a Markdown file unchanged to `raw/YYYY-MM-DD-<slug>.md` and add the required raw frontmatter with `status: raw`; move its images/PDFs/other attachments to `raw/assets/<slug>-<original-name>` and reference them from that raw capture. For an image/PDF without a Markdown note, create a small `raw/YYYY-MM-DD-<slug>.md` manifest (`type: file`, `status: raw`) that records its original filename and the corresponding `raw/assets/` path. Never process a file in place in `inbox/`; after a successful move it is empty again.
2. Read each raw capture, then read `SCHEMA.md`. Decide which node(s) it teaches and which typed
   folder each belongs to. **Search-then-update, create-last**: grep `aliases:` AND
   node bodies across all knowledge folders first — on overlap, extend the existing
   node instead of creating a near-duplicate. Nodes should compound.
3. Create/update `<folder>/<node>.md` per SCHEMA.md: Thai summary of what THIS source
   adds, `[[wikilinks]]` to related nodes, `aliases:` with Thai+English synonyms, cite
   the raw file in `sources:`. Every knowledge node touched by this op must finish with
   at least one non-self wikilink that resolves to an existing vault note. Do not make
   placeholder wikilinks just to make the graph look dense; use plain text when no
   real target note exists. Add a reciprocal link to an existing node only when it
   genuinely improves navigation or records a meaningful relationship.
4. Run `bin/sb-link-check.sh <every-created-or-updated-knowledge-node>`. If it fails,
   repair the links before continuing. This is the PROCESS Definition of Done.
5. Flip the raw file's `status:` to `processed` only after the link check passes.
6. Run `bin/sb-commit.sh "process: <slug>"`. The commit wrapper repeats the link
   check for all changed knowledge nodes, requires every changed raw capture to be
   `processed` and cited by a knowledge node, regenerates `index.md`, then commits.
   No write path can bypass the complete flow.

### ASK — answer from the vault only
1. Run `python3 "$VAULT/bin/sb-search.py" search "<q>" --json` first.
   It combines SQLite FTS5 + Gemini semantic retrieval, returns structured nodes first,
   and uses processed `raw/` as lower-weight lexical evidence. Follow relevant
   `[[wikilinks]]` and cited `sources:`. If the helper is unavailable, fall back to
   `index.md` + grep variants across `entities/ concepts/ comparisons/ queries/ people/`
   and `journal/`, then `raw/` if needed.
2. Answer from what's found, citing which nodes/sources. If the vault has nothing,
   SAY SO plainly — never fill in with general knowledge without labeling it as such.
3. **Write-back:** if the answer was genuinely useful and took real synthesis (not a
   one-line lookup), persist it as a `queries/` node (search-then-update first) —
   this is why `queries/` exists. Then `bin/sb-index.sh` + `bin/sb-commit.sh "ask: <q>"`.

### SEARCH / REINDEX — derived hybrid retrieval

- `/sb search <q>`: run `bin/sb-search.py search "<q>"` and return ranked paths,
  channels, excerpts, metadata, and sources. This is a lookup only; do not create a
  `queries/` node.
- `/sb reindex`: run `bin/sb-search.py reindex --best-effort`. Markdown remains the
  source of truth; deleting/rebuilding `.sb/search.db` is safe.
- Cost rule: structured files are embedded only when their content hash changes;
  repeated query embeddings are cached. `raw/` is FTS5-only and never sent for embedding.
- Failure rule: Gemini/network/quota failure leaves embeddings `pending` and falls back
  to FTS5. It must never prevent `sb-commit.sh` from preserving a capture.

### PERSON — CRM
1. Search `people/` for an existing file (name + aliases) before creating one.
2. Create or update `people/<slug>.md`: who, where met, when, org, discussion notes
   (append a dated bullet under `## Notes`), commitments/deadlines under `## Follow-ups`.
3. Link related `[[wiki pages]]`. Finish with `bin/sb-commit.sh "person: <slug>"`.
Lookups ("เบียร์ นี่ใครนะ") are ASK ops scoped to `people/` — surface follow-ups with
approaching deadlines.

### APPOINTMENT — scheduled meetings on a person

Captures time-bound commitments with a known person. Person file `people/<slug>.md` already exists (created via PERSON op).

**Add (`/sb นัด`):**
1. Resolve `<slug>` from input (name → slug, or alias match)
2. Ensure person file exists (`sb-people-update.sh <slug> ensure`)
3. Parse `<story>` for date+time+location+agenda; if relative ("พรุ่งนี้ 14:00") resolve against today
4. `sb-people-update.sh <slug> set next_meeting_at "<ISO>"` + `meeting_location`, `meeting_agenda`, `meeting_status: scheduled`
5. If time conflicts with existing `next_meeting_at` → **manual check by operator** (script does not detect/confirm — review the file before re-setting)
6. `bin/sb-commit.sh "appointment: <slug> <ISO>"`

**Query (`/sb this week`):**
1. `bin/sb-this-week.sh` — scans `people/*.md` for `next_meeting_at` in [today, today+7] AND `meeting_status: scheduled` (or absent)
2. Format output (Thai day name + time + person + location + agenda)

**Close (`/sb done` / `/sb cancel`):**
1. `sb-people-update.sh <slug> set meeting_status done|cancelled`
2. Append `## Notes` bullet summarizing outcome (ask user for short text if not provided)
3. `bin/sb-commit.sh "appointment-close: <slug> <status>"`

### ENCOUNTER — meetings logged without time commitment

Lightweight capture of "เจอคน" or "คุยกับ" — append-only dated bullets under `## Notes`.

**Add (`/sb เจอ`):**
1. Detect if name/handle is present in story
2. If named → `sb-people-update.sh <slug> ensure` then `add-note <today> <bullet>`
3. If anonymous → `journal/YYYY-MM-DD-HHMM.md` with `## People seen (unnamed)` section (descriptor + takeaway)
4. `bin/sb-commit.sh "encounter: <slug-or-anon>"`

**Detection heuristic (`/sb คน` ambiguity):**
- `bin/sb-encounter-detect.sh` reads input → returns `appointment` or `encounter`
- If `appointment` → route to APPOINTMENT-add
- If `encounter` → route to ENCOUNTER-add
- If genuinely ambiguous → ask 1 question before routing

**Query (`/sb follow-up`):**
1. `bin/sb-follow-up.sh` — scans all `people/*.md` for `## Follow-ups` section
2. Filters `- [ ]` (open) items
3. Sorts by `due` date ascending; items without due go last
4. Format output (due + text + person name)

### JOURNAL
1. Write `journal/YYYY-MM-DD-HHMM.md` with the user's text verbatim.
2. Reply grounded in the user's OWN vault: grep wiki + previous journal entries for
   relevant material; connect ("คุณเคยเจอแบบนี้เมื่อ มี.ค. แล้วแก้ด้วย…"). No generic advice
   unless the vault is empty on the topic — then say so.
3. `bin/sb-commit.sh "journal: YYYY-MM-DD-HHMM"`.

### STATUS
Report: counts per folder, unprocessed raw count, 3 latest captures, last commit
(`git -C "$VAULT" log -1 --format='%ar %s'`), plus
`python3 "$VAULT/bin/sb-search.py" status` (chunks/embedded/pending).

### AUDIT — self-audit of Claude Code session history
Input: optional `N` (session count) or `--project` flag. Reads OUTSIDE the vault
(`~/.claude/projects/**/*.jsonl`) — the only op that does.
1. **Dry-run first, always:** resolve scope (default `N=20` most recent sessions by file
   mtime, across all projects; `--project` narrows to the current project's sessions only).
   Hard cap: `N` cannot exceed 100 regardless of argument. Print matched file count + total
   size before reading anything. If the user doesn't confirm, stop here.
2. Sub-agents pull raw signals from the matched session transcripts, cluster into repeated
   patterns.
3. Per cluster, decide a candidate: new skill / new automation / fix / nothing.
4. Write `audit/candidates-YYYY-MM-DD-HHMM.md` (frontmatter: `scope, session_count,
   generated`) listing candidates with evidence. Never auto-creates skills/automations,
   never scheduled — diagnosis only, the user acts on candidates manually.
5. `bin/sb-commit.sh "audit: <scope>"`.

## Ingest gate for the `watch` skill

If you are the `watch` skill looking for this vault's Ingest op: copy your `report.md`
to `raw/YYYY-MM-DD-<slug>.md`, add the frontmatter above (`status: raw`,
`type: youtube`), copy hero frames to `raw/assets/`, then run PROCESS for that file.

## GRAPH — seeing the brain (two layers, both optional reads)

1. **Obsidian graph (primary, zero cost):** nodes/edges come from `[[wikilinks]]` in
   the markdown itself — nothing to run. Open Obsidian → vault "second-brain" →
   graph view. If the graph looks sparse, the fix is more wikilinks in nodes, not
   more tooling.
2. **graphify (secondary, on-demand):** deep queryable knowledge graph over the
   whole vault. Run `/graphify "$VAULT"` (first time), then
   `/graphify "$VAULT" --update` (incremental) and
   `/graphify query "<question>"`. Output lands in `graphify-out/` — derived,
   gitignored, safe to delete and rebuild.
   Graphify is not part of INGEST/PROCESS Definition of Done and must not run after
   every `/sb` capture. Use it only for community detection, cross-node path queries,
   confidence-labelled inferred relationships, or an interactive HTML/JSON audit.
   `.graphifyignore` excludes images, audio, video, and derived/private operational
   folders so Graphify works only from text already captured and summarized by the
   approved `/sb` or `watch` flow.
   **⚠ NEVER run graphify with `--obsidian --obsidian-dir` pointing INTO this vault**
   — it would write its own generated vault files inside our typed structure.
   Plain `/graphify <path>` is the only sanctioned form here.

## Other systems (context, not ops)

- **Obsidian** is an optional viewer only — no op depends on it. **Registered 2026-07-08**
  (vault id `33eb7929fd0b9b52` in `~/.config/obsidian/obsidian.json`) — open the Obsidian app
  and pick "second-brain" from the vault switcher. Ops still run entirely via Claude Code;
  Obsidian is read/browse/graph-view only.
- **`/home/time/Downloads/2ndBrain/` (NEOKNOWLEDGE)** is a separate, heavier system (Neo4j +
  NotebookLM RAG, multi-tenant) for structured knowledge work needing graph queries — e.g.
  client chat archives. This vault is for fast personal capture with zero infra. They are
  not meant to merge; if this vault ever needs graph queries, revisit rather than silently
  duplicating effort.
