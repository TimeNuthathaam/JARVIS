# Second Brain — Content-Fill + AUDIT Op Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put real content into the empty `/home/time/second-brain/` vault (process 1 pending + 2 new raw captures into topic-first wiki pages) and add a new `AUDIT` op to the vault's operating manual for self-auditing Claude Code session history.

> **Scope cut 2026-07-08:** user decided NOT to archive the 2 Chase AI video transcripts as
> vault knowledge — only wants the *use case* (AUDIT op) actually installed. **Task 1 and
> Task 2 are skipped entirely** (no raw ingest, no wiki pages about the videos). Only Task 3
> (add AUDIT op to CLAUDE.md) and Task 4 (wire routing in SKILL.md) are executed, followed
> by a scoped-down Task 5.

**Architecture:** Pure markdown + git vault, no code/no tests in the pytest sense — every "test" below is a structural verification (grep/wc/find) run against the actual files, matching how this vault already verifies itself (`bin/sb-index.sh`, `bin/sb-commit.sh`).

**Tech Stack:** Bash, markdown, git (via `bin/sb-commit.sh` only — never plain `git commit`).

## Global Constraints

- Every writing op in `/home/time/second-brain/` finishes with `bash /home/time/second-brain/bin/sb-commit.sh "<op>: <msg>"` — never `git commit` directly (vault `CLAUDE.md` concurrency rule).
- `raw/*.md` files are immutable except the `status:` frontmatter field (`raw` → `processed`) — never touch their body content.
- `index.md` is derived — always regenerate via `bash /home/time/second-brain/bin/sb-index.sh`, never hand-edit.
- Wiki/people/journal content is Thai, English technical terms kept as-is (vault language rule).
- `wiki/` frontmatter requires `aliases:` with Thai+English synonyms (this is what makes vault search work) and `sources:` citing raw file names.
- AUDIT op: hard cap `N` ≤ 100 sessions, dry-run (print scope + count) required before reading any transcript, diagnosis-only — never auto-creates skills/automations, never scheduled/cron'd.
- `~/.claude/skills/second-brain/SKILL.md` is NOT a git repo (verified: `git rev-parse` fails there) — edit it directly, no commit step for that file.

---

### Task 1: Ingest 2 new Chase AI raw captures

**Files:**
- Create: `/home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md`
- Create: `/home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md`

**Interfaces:**
- Consumes: existing `/watch`/`/listen` reports at `/home/time/watch-output/Chase_AI/you-only-have-1-day-left-for-these-fable-5-use-cases-or-pay--20260708-004942/report.md` and `/home/time/watch-output/Chase_AI/claude-fable-5-use-cases-you-must-do-now-or-lose-thousands-i-20260708-005029/report.md` (both already have TL;DR/analysis filled in — read-only, do not modify them).
- Produces: 2 new `raw/*.md` files with `status: raw`, consumed by Task 2.

- [ ] **Step 1: Create the first raw file (frontmatter + full copy of the existing report)**

```bash
{
  cat <<'EOF'
---
title: You Only Have 1 Day Left For These Fable 5 Use Cases (Or Pay Thousands) — Chase AI
source_url: https://www.youtube.com/watch?v=Tp9CiBeviKk
captured: 2026-07-08
type: youtube
status: raw
tags: [fable-5, claude-code, second-brain, self-audit, skill-hygiene, effort-level]
---

EOF
  cat "/home/time/watch-output/Chase_AI/you-only-have-1-day-left-for-these-fable-5-use-cases-or-pay--20260708-004942/report.md"
} > /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md
```

- [ ] **Step 2: Verify file 1**

Run: `head -8 /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md && grep -c "^status: raw$" /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md`
Expected: frontmatter block printed, and `1` (exactly one `status: raw` line).

- [ ] **Step 3: Create the second raw file**

```bash
{
  cat <<'EOF'
---
title: Claude Fable 5 Use Cases You Must Do NOW (Or Lose Thousands in 1 Week) — Chase AI
source_url: https://www.youtube.com/watch?v=lplVBFr0Ndc
captured: 2026-07-08
type: youtube
status: raw
tags: [fable-5, claude-code, second-brain, self-audit, goal-command, agentic-os, prd]
---

EOF
  cat "/home/time/watch-output/Chase_AI/claude-fable-5-use-cases-you-must-do-now-or-lose-thousands-i-20260708-005029/report.md"
} > /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md
```

- [ ] **Step 4: Verify file 2**

Run: `head -8 /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md && grep -c "^status: raw$" /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md`
Expected: frontmatter block printed, and `1`.

- [ ] **Step 5: Commit**

```bash
bash /home/time/second-brain/bin/sb-commit.sh "ingest: 2 chase-ai fable-5 use-case videos"
```
Expected output: `committed: ingest: 2 chase-ai fable-5 use-case videos`

---

### Task 2: Process all 3 raw captures into 6 topic-first wiki pages

**Files:**
- Create: `/home/time/second-brain/wiki/second-brain-obsidian-pattern.md`
- Create: `/home/time/second-brain/wiki/claude-code-self-audit.md`
- Create: `/home/time/second-brain/wiki/fable-5-effort-economics.md`
- Create: `/home/time/second-brain/wiki/skill-hygiene-audit.md`
- Create: `/home/time/second-brain/wiki/agentic-os-pattern.md`
- Create: `/home/time/second-brain/wiki/fable-5-workflow-patterns.md`
- Modify: `/home/time/second-brain/raw/2026-07-04-matt-wolfe-ai-second-brain.md` (frontmatter `status:` only)
- Modify: `/home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md` (frontmatter `status:` only)
- Modify: `/home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md` (frontmatter `status:` only)
- Modify: `/home/time/second-brain/index.md` (regenerated, not hand-edited)

**Interfaces:**
- Consumes: the 3 raw files (1 from Task 1 setup, 2 from Task 1).
- Produces: 6 wiki pages other future PROCESS runs may extend (per vault rule: "prefer updating an existing wiki page over creating a new one").

**Note on scope:** this deviates from the vault's usual "ingest one file, immediately process that one file" pattern — these 3 sources overlap heavily on topic (second-brain pattern, self-audit pattern), so per the approved spec they're processed together into shared topic pages instead of one page per source.

- [ ] **Step 1: Write `wiki/second-brain-obsidian-pattern.md`**

```markdown
---
title: Second Brain แบบ Obsidian + LLM Wiki (Karpathy pattern)
aliases: [second brain, LLM wiki, Karpathy wiki, obsidian second brain, สมองสำรอง, ระบบความจำสำรอง]
updated: 2026-07-08
sources: [2026-07-04-matt-wolfe-ai-second-brain.md]
---

# Second Brain แบบ Obsidian + LLM Wiki (Karpathy pattern)

## แนวคิดต้นทาง

ไอเดียนี้มาจาก Andrej Karpathy (โพสต์ GitHub อธิบายสถาปัตยกรรม LLM-wiki) — Matt Wolfe
เอามาต่อยอดโดยเพิ่มชั้น journal + CRM ทับบน wiki เดิม รวมเป็น **3 pillars**:

1. **Wiki/Knowledge base** — เก็บทุกอย่างที่เจอจากเน็ต (YouTube transcript, บทความ, podcast, tweet)
2. **CRM** — คนที่เจอในงาน, Zoom call, บันทึกว่าเจอที่ไหน คุยอะไร ติดต่อยังไง
3. **Journal** — เขียนบันทึกประจำวัน แล้ว AI ตอบโดยอิงจาก wiki + CRM + journal เก่า (ไม่ใช่ตอบลอยๆ แบบ ChatGPT ทั่วไป)

## เครื่องมือที่ใช้ (ต้นฉบับของ Matt Wolfe)

- **Obsidian** — ตัวอ่าน/จัดระเบียบ markdown (front-end อย่างเดียว ไม่ใช่ตัวรันโลจิก)
- **Obsidian Web Clipper** (Chrome extension) — ดึงหน้าเว็บ/YouTube transcript ใส่ `raw/` พร้อม frontmatter (source title, source URL, วันที่, tag) อัตโนมัติ
- **Codex** (หรือ Claude Code / Anthropic's co-work ก็ใช้แทนได้) — ตัวรัน agent ที่อ่าน `agents.md` แล้วทำตามคำสั่ง (process raw → wiki, ตอบ journal, อัปเดต CRM)

## โครงสร้างโฟลเดอร์ต้นฉบับ

`raw/` (immutable source) → `wiki/` (AI-generated) → `agents.md` (คู่มือ) → `index.md` (แคตตาล็อก) →
`log.md` (log การเปลี่ยนแปลง) — Matt Wolfe เพิ่ม `raw/processed/` แยกไฟล์ที่ผ่านการ process แล้ว,
auto-link wiki pages ที่เกี่ยวข้องกัน (คล้าย Zettelkasten), และตั้ง automation รายชั่วโมงให้ process
raw ที่ค้างอัตโนมัติ + push backup ขึ้น private GitHub repo

## เทียบกับ vault ของเราเอง (`/home/time/second-brain/`)

Vault นี้ implement pattern เดียวกันอยู่แล้ว (3 pillars ครบ) แต่ต่างในรายละเอียด:

| จุด | Matt Wolfe (ต้นฉบับ) | vault เรา |
|---|---|---|
| ไฟล์คู่มือ | `agents.md` | `CLAUDE.md` (+ `AGENTS.md` symlink) |
| CRM | โฟลเดอร์ `CRM/` | โฟลเดอร์ `people/` |
| Mark ว่า process แล้ว | ย้ายไฟล์ไป `raw/processed/` | flip `status:` frontmatter เป็น `processed` (ไฟล์อยู่ที่เดิม) |
| ตัวรัน agent | Codex + Obsidian Web Clipper (auto-capture) | Claude Code ตรงๆ ผ่าน `/sb` skill (capture แบบ manual/สั่งเอง) |
| Backup | push ขึ้น private GitHub repo ทุกชั่วโมง | local git เท่านั้น ไม่มี remote (ข้อมูลส่วนตัว) |
| Automation | Codex automation รายชั่วโมง (auto-process) | ไม่มี — ทุก op ต้องสั่งเอง (ตั้งใจไว้ตามสเปกเดิม) |

**สรุป:** เราไม่ได้พลาดอะไรจาก pattern ต้นฉบับ — โครงสร้างหลักตรงกันหมด ต่างแค่รายละเอียด
implementation ที่เราเลือกทางที่ตรงไปตรงมากว่า (frontmatter flip แทนการย้ายไฟล์,
ไม่มี auto-capture extension เพราะเราไม่ได้ผูกกับ Chrome) จุดเดียวที่น่าคิดต่อในอนาคตคือ
**backup remote** — ถ้าอยากกัน data loss มากกว่า local git อาจพิจารณา private GitHub repo
เหมือนต้นฉบับ (ยังไม่ได้ตัดสินใจตอนนี้)

## Related
[[claude-code-self-audit]] — journal/wiki pattern เดียวกันที่ Matt Wolfe ใช้ตรวจ pattern ซ้ำๆ
ในบันทึกของตัวเอง ก็คือแนวคิดเดียวกับที่ AUDIT op ของเราทำกับ session history
```

- [ ] **Step 2: Write `wiki/claude-code-self-audit.md`**

```markdown
---
title: Self-audit ประวัติการใช้ Claude Code เพื่อหา skill/automation ใหม่
aliases: [self-audit, session audit, audit sessions, ตรวจสอบการใช้งาน, mining skills from sessions]
updated: 2026-07-08
sources: [2026-07-08-chase-fable5-use-cases-24h.md, 2026-07-08-chase-fable5-use-cases-week.md]
---

# Self-audit ประวัติการใช้ Claude Code

## แนวคิด (พบซ้ำใน 2 คลิปจาก Chase AI)

ให้ AI (Fable 5 หรือรุ่นที่แรงพอ) สแกน session history ย้อนหลัง แล้ว:
1. หา pattern ที่ทำซ้ำๆ พร้อมนับจำนวนครั้ง
2. เสนอ skill/automation ใหม่จาก pattern เหล่านั้น
3. ชี้จุดที่ prompting ไม่มีประสิทธิภาพ

**สำคัญ:** ทั้ง 2 คลิปเน้นย้ำว่าต้อง **diagnosis-only ก่อน** — ให้ AI ใช้ sub-agent ดึงสัญญาณดิบจาก
transcript, cluster เป็นกลุ่ม, แล้วตัดสินใจต่อ cluster ว่าควรเป็น skill ใหม่ / automation ใหม่ /
แก้ไข / ไม่ต้องทำอะไร — ไม่ auto-สร้างอะไรทันทีจนกว่าคนจะ review

แหล่งหนึ่ง (video ที่สอง) บอกว่า prompt ที่ใช้จริงมาจากเอกสารทางการของ Anthropic
เรื่อง prompting Fable 5 โดยเฉพาะ (มี nuance ต่างจาก prompting Opus)

## Scale mismatch ที่ต้องระวัง

คลิปสาธิตบน 39 sessions / 30 วัน แต่เครื่องนี้มี **5,491 session transcripts (1.9GB) ใน 30 วัน**
ข้าม 100+ โปรเจกต์ — เอา prompt จากคลิปมาใช้ตรงๆ (scan ทุกอย่างใน 30 วัน) จะกิน token มหาศาล
ต้อง scope ให้เล็กลงมาก (จำกัดที่ N=20 sessions ล่าสุดข้ามโปรเจกต์เป็นค่าเริ่มต้น, cap ที่ 100,
มี dry-run ก่อนอ่านจริง)

## เราเอาไปใช้ยังไง

Pattern นี้กลายเป็น op ใหม่ชื่อ **AUDIT** ใน `/home/time/second-brain/CLAUDE.md` — ดูรายละเอียด
เต็มที่ `docs/specs/2026-07-08-audit-op-and-content-fill-design.md` เรียกผ่าน `/sb audit [N|--project]`

## Related
[[skill-hygiene-audit]] — แนวคิดคู่กัน แต่ตรวจ skill ที่มีอยู่แล้วแทนที่จะขุดหา pattern ใหม่
[[fable-5-workflow-patterns]] — pattern การแบ่งงาน plan/execute ที่ทั้ง 2 คลิปพูดถึงเช่นกัน
```

- [ ] **Step 3: Write `wiki/fable-5-effort-economics.md`**

```markdown
---
title: Fable 5 — effort level กับต้นทุน/คุณภาพ
aliases: [fable 5 effort level, effort economics, deepswe benchmark, medium vs low effort]
updated: 2026-07-08
sources: [2026-07-08-chase-fable5-use-cases-24h.md]
---

# Fable 5 — Effort Level กับต้นทุน/คุณภาพ

## ตัวเลขจาก DeepSWE benchmark (อ้างในคลิป Chase AI)

Fable 5 ที่ effort **medium** หรือ **low** ทำคะแนนดีกว่า Opus 4.8 ในเบนช์มาร์ก DeepSWE
และถูกกว่ามาก:

- **Medium**: ~$6 เทียบกับ Opus ~$13 (ถูกกว่าประมาณครึ่งหนึ่ง)
- **Low**: ~$3.76 เทียบกับ Opus ~$13 (ถูกกว่าเกือบ 4 เท่า)

## คำแนะนำจากคลิป

ไม่ต้องเปิด max/extra-high effort ทุกครั้ง — ใช้ medium (หรือ low ถ้ากังวลเรื่อง usage) กับงานทั่วไป
เก็บ effort สูงสุด (เช่น Ultracode + dynamic workflows) ไว้สำหรับงานที่ต้องรันยาว/ซับซ้อนจริงๆ
เท่านั้น

## เอาไปใช้ยังไง

เป็น operating tip ทั่วไปเวลาเลือก effort level ใน Fable 5 — ไม่ต้องเปิด max ทุกงาน ประหยัด
usage cap ไว้ใช้กับงานที่คุ้มค่าจริงๆ

## Related
[[fable-5-workflow-patterns]]
```

- [ ] **Step 4: Write `wiki/skill-hygiene-audit.md`**

```markdown
---
title: Skill hygiene audit (keep/merge/rewrite/delete)
aliases: [skill audit, skill hygiene, skill cleanup, ตรวจสอบ skill]
updated: 2026-07-08
sources: [2026-07-08-chase-fable5-use-cases-24h.md]
---

# Skill Hygiene Audit

## แนวคิด (Chase AI use case 4)

ให้ AI สร้างตารางไล่ดู skill ที่มีอยู่ทั้งหมด แล้วตัดสินแต่ละตัวว่า:
- **Keep** — ใช้ได้ดี ไม่ต้องแตะ
- **Merge** — ซ้ำซ้อนกับ skill อื่น ควรรวม
- **Rewrite** — ยังจำเป็นแต่ trigger ไม่แม่น หรือ body ไม่ชัด
- **Delete** — ไม่ได้ใช้แล้ว/ไม่มีประโยชน์

จากนั้นให้แก้ description ของ 3 skill ที่ trigger accuracy แย่ที่สุดก่อน (ไม่ใช่แก้ทั้งหมดทีเดียว
— เลือก highest-leverage ก่อน)

## ทำไมสำคัญ

คลิปบอกว่า "skills are probably the highest leveraged thing when it comes to Claude Code" —
เป็น mechanism หลักที่ทำให้ agent ทำงานแบบ deterministic ได้มากขึ้น

## เอาไปใช้กับระบบเรา

ยังไม่ได้ลงมือทำ — เป็น candidate สำหรับรอบ AUDIT ในอนาคต (ดู [[claude-code-self-audit]])
เครื่องนี้มี skill สะสมเยอะมาก (`~/.claude/skills/`, ปลั๊กอินอีกหลายตัว) ยังไม่เคยมี audit
รอบแบบนี้เลยสักครั้ง

## Related
[[claude-code-self-audit]]
```

- [ ] **Step 5: Write `wiki/agentic-os-pattern.md`**

```markdown
---
title: Agentic OS — dashboard wrapper ครอบ Claude Code
aliases: [agentic os, claude os, headless dashboard, claude --headless -p]
updated: 2026-07-08
sources: [2026-07-08-chase-fable5-use-cases-week.md]
---

# Agentic OS — Dashboard Wrapper ครอบ Claude Code

## แนวคิด (Chase AI, video ที่สอง, use case 3)

สร้าง visual dashboard ครอบ Claude Code: โชว์ content metrics, morning reports, skill/automation
ที่ใช้บ่อยเป็นปุ่มคลิกเดียว เชื่อมกับ Obsidian ข้างใต้เป็น `claude --headless -p` ล้วนๆ
(ไม่เสีย API แล้ว — Anthropic ยกเลิกการคิดราคาแบบ API สำหรับ headless mode ไปแล้ว)

Framing ในคลิป: เป็น follow-on ตามธรรมชาติจาก [[claude-code-self-audit]] — audit หา skill/automation
ก่อน แล้วค่อยเอามาโชว์เป็น dashboard ให้กดใช้ง่ายๆ

Packageable/ขายได้ — ให้ทีมที่ไม่ถนัด CLI ใช้ผ่านหน้าเว็บแทน

## เชื่อมกับงานที่ค้างอยู่

Next step ที่บันทึกไว้ใน `watch-output/.claude/memory/SESSION.md` คือ bootstrap
`/home/time/claudeclaw-os` (ยังไม่มีบนดิสก์) — pattern นี้คือตัวอย่างจริงของสิ่งที่ claudeclaw-os
กำลังจะเป็น **หมายเหตุไว้เฉยๆ ตอนนี้ ไม่ได้ลงมือสร้าง** — เป็นแค่ reference สำหรับตอนที่จะ bootstrap
จริง

## Related
[[claude-code-self-audit]], [[fable-5-workflow-patterns]]
```

- [ ] **Step 6: Write `wiki/fable-5-workflow-patterns.md`**

```markdown
---
title: Fable 5 workflow patterns — plan กับโมเดลถูก, execute กับ Fable 5
aliases: [plan then execute, goal command, prd first, deep research pattern]
updated: 2026-07-08
sources: [2026-07-08-chase-fable5-use-cases-24h.md, 2026-07-08-chase-fable5-use-cases-week.md]
---

# Fable 5 Workflow Patterns

## Pattern หลัก: วางแผนด้วยโมเดลถูก รันยาวด้วย Fable 5

ทั้ง 2 คลิปย้ำ pattern เดียวกัน: อย่าใช้ Fable 5 usage ไปกับงาน research/planning — ใช้ Opus 4.8
หรือ Codex ทำ `/deep_research` หรือ dynamic workflows ก่อน ได้แผนที่โอเคแล้วค่อยส่งให้ Fable 5
รันยาวๆ ด้วย `/goal` (คำสั่งสำหรับ long-running agentic task ที่มี success criteria ชัดเจน)

## ตัวอย่างจากคลิป

- **Clone ซอฟต์แวร์ที่ต้องจ่ายเงิน** (เช่น Whisperflow) ให้รันโลคอล — deep research ก่อนว่าแอปทำงาน
  ยังไง แล้วเอาผลไปทำ `/goal` prompt ให้ Fable 5
- **โปรเจกต์ long-horizon จาก PRD** — เขียน PRD (product requirements doc) ด้วย Opus 4.8 ก่อน
  (คนเขียนร่วมด้วยได้ ไม่ต้องเขียนเองทั้งหมด) แล้วให้ Fable 5 execute อัตโนมัติยาวๆ (ตัวอย่างในคลิป:
  เกม Three.js 21,000 บรรทัด TypeScript, 90+ commits จาก PRD เดียว)
- **Code review หลายตัวขนาน** — 4 reviewer รันพร้อมกัน, dedupe finding, จัดลำดับ severity —
  ภายใน ~5 นาที

## คำเตือนจากคลิป

"ไม่แนะนำให้ใช้ dynamic workflows กับ Fable 5" สำหรับงานที่ Opus ทำได้อยู่แล้ว — จะเปลือง usage
เปล่าๆ เก็บ Fable 5 ไว้สำหรับ execution จริง ไม่ใช่ planning

## Related
[[fable-5-effort-economics]], [[agentic-os-pattern]]
```

- [ ] **Step 7: Flip the 3 raw files' status to `processed` (frontmatter only, body untouched)**

```bash
sed -i 's/^status: raw$/status: processed/' \
  /home/time/second-brain/raw/2026-07-04-matt-wolfe-ai-second-brain.md \
  /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-24h.md \
  /home/time/second-brain/raw/2026-07-08-chase-fable5-use-cases-week.md
```

- [ ] **Step 8: Verify wiki pages + status flips**

Run: `find /home/time/second-brain/wiki -name '*.md' | wc -l && grep -L '^status: processed$' /home/time/second-brain/raw/*.md`
Expected: `6`, and the `grep -L` (files NOT matching) prints nothing — all 3 raw files now say `status: processed`.

- [ ] **Step 9: Regenerate index.md**

```bash
bash /home/time/second-brain/bin/sb-index.sh
```
Expected output: `index.md regenerated`

- [ ] **Step 10: Verify index.md picked up the new content**

Run: `grep -c '^- \[\[wiki/' /home/time/second-brain/index.md`
Expected: `6`

- [ ] **Step 11: Commit**

```bash
bash /home/time/second-brain/bin/sb-commit.sh "process: matt-wolfe + 2 chase-ai captures -> 6 wiki pages"
```
Expected output: `committed: process: matt-wolfe + 2 chase-ai captures -> 6 wiki pages`

---

### Task 3: Add the AUDIT op to the vault's CLAUDE.md

**Files:**
- Modify: `/home/time/second-brain/CLAUDE.md` (4 separate edits, detailed below)

**Interfaces:**
- Consumes: nothing new.
- Produces: the `AUDIT` op definition that Task 4's routing table entry points to.

- [ ] **Step 1: Add `audit/` to the folder contract table**

Modify `/home/time/second-brain/CLAUDE.md`, find this exact text:
```
| `log/` | Monthly log `YYYY-MM.md`. Append ONLY via `bin/sb-commit.sh` (it takes the flock). |
| `index.md` | Derived. Regenerate with `bin/sb-index.sh`; never hand-edit. |
```
Replace with:
```
| `log/` | Monthly log `YYYY-MM.md`. Append ONLY via `bin/sb-commit.sh` (it takes the flock). |
| `audit/` | AUDIT op output only, one file per run: `candidates-YYYY-MM-DD-HHMM.md`. Never hand-edit, never auto-executed. |
| `index.md` | Derived. Regenerate with `bin/sb-index.sh`; never hand-edit. |
```

- [ ] **Step 2: Add `audit/` frontmatter schema**

Find this exact text:
```
**journal/**: `date, mood (optional)`
```
Replace with:
```
**journal/**: `date, mood (optional)`
**audit/**: `scope, session_count, generated`
```

- [ ] **Step 3: Add the `### AUDIT` operation section**

Find this exact text:
```
### STATUS
Report: counts per folder, unprocessed raw count, 3 latest captures, last commit
(`git -C /home/time/second-brain log -1 --format='%ar %s'`).

## Ingest gate for the `watch` skill
```
Replace with:
```
### STATUS
Report: counts per folder, unprocessed raw count, 3 latest captures, last commit
(`git -C /home/time/second-brain log -1 --format='%ar %s'`).

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
```

- [ ] **Step 4: Add the "Other systems" context section at the end of the file**

Append to the end of `/home/time/second-brain/CLAUDE.md` (after its last line, `then run PROCESS for that file.`):
```

## Other systems (context, not ops)

- **Obsidian** is an optional viewer only — no op depends on it. Register this folder as a
  vault (Obsidian → Open folder as vault) once there's content worth browsing or graph-view
  is wanted; skip it otherwise, it's a 10-second action to add later.
- **`/home/time/Downloads/2ndBrain/` (NEOKNOWLEDGE)** is a separate, heavier system (Neo4j +
  NotebookLM RAG, multi-tenant) for structured knowledge work needing graph queries — e.g.
  client chat archives. This vault is for fast personal capture with zero infra. They are
  not meant to merge; if this vault ever needs graph queries, revisit rather than silently
  duplicating effort.
```

- [ ] **Step 5: Verify all 4 edits landed**

Run: `grep -c "audit/" /home/time/second-brain/CLAUDE.md && grep -c "### AUDIT" /home/time/second-brain/CLAUDE.md && grep -c "NEOKNOWLEDGE" /home/time/second-brain/CLAUDE.md`
Expected: a count ≥1 for each (exact counts don't matter, non-zero does — the goal is confirming each section landed).

- [ ] **Step 6: Commit**

```bash
bash /home/time/second-brain/bin/sb-commit.sh "docs: add AUDIT op + other-systems note to CLAUDE.md"
```
Expected output: `committed: docs: add AUDIT op + other-systems note to CLAUDE.md`

---

### Task 4: Wire AUDIT into the skill's routing table

**Files:**
- Modify: `/home/time/.claude/skills/second-brain/SKILL.md` (NOT a git repo — no commit step for this file)

**Interfaces:**
- Consumes: Task 3's `### AUDIT` op (this is what makes it reachable via `/sb audit`).
- Produces: nothing consumed by later tasks — this is the routing entry point.

- [ ] **Step 1: Add the AUDIT routing row**

Modify `/home/time/.claude/skills/second-brain/SKILL.md`, find this exact text:
```
| `/sb process` | PROCESS (work through unprocessed raw/) |
| `/sb สถานะ` / "status" | STATUS |
| Ambiguous | Ask before acting — one short question (เก็บ / ค้น / journal?); if still unclear, run a `/grilling` interview (grill-me / grilling skill), then capture. |
```
Replace with:
```
| `/sb process` | PROCESS (work through unprocessed raw/) |
| `/sb สถานะ` / "status" | STATUS |
| `/sb audit` / `/sb audit N` / `/sb audit --project` | AUDIT (self-audit of Claude Code session history; dry-run first) |
| Ambiguous | Ask before acting — one short question (เก็บ / ค้น / journal?); if still unclear, run a `/grilling` interview (grill-me / grilling skill), then capture. |
```

- [ ] **Step 2: Verify**

Run: `grep -n "AUDIT" /home/time/.claude/skills/second-brain/SKILL.md`
Expected: one line showing the new routing row.

(No commit — this file lives outside the git-tracked vault.)

---

### Task 5: Final verification across the whole vault

**Files:** none (read-only verification of Tasks 1-4's combined output)

**Interfaces:**
- Consumes: everything produced by Tasks 1-4.
- Produces: nothing — this is the plan's overall acceptance check.

- [ ] **Step 1: Confirm vault content counts**

Run:
```bash
echo "wiki: $(find /home/time/second-brain/wiki -name '*.md' | wc -l) (expect 6)"
echo "raw: $(find /home/time/second-brain/raw -maxdepth 1 -name '*.md' | wc -l) (expect 3)"
echo "unprocessed raw: $(grep -L '^status: processed$' /home/time/second-brain/raw/*.md 2>/dev/null | wc -l) (expect 0)"
```
Expected: `wiki: 6`, `raw: 3`, `unprocessed raw: 0`.

- [ ] **Step 2: Confirm CLAUDE.md and SKILL.md both mention AUDIT**

Run: `grep -c "AUDIT" /home/time/second-brain/CLAUDE.md /home/time/.claude/skills/second-brain/SKILL.md`
Expected: non-zero count for both files.

- [ ] **Step 3: Confirm git history**

Run: `git -C /home/time/second-brain log --oneline -6`
Expected: 6 most recent commits are (newest first) the Task 3 commit, the Task 2 commit, the Task 1 commit, then the 2 spec-doc commits from the design phase, then the earlier "docs: add ask-before-store rule" commit.

- [ ] **Step 4: Confirm log.md has entries for every op run**

Run: `tail -6 /home/time/second-brain/log/2026-07.md`
Expected: one line each for the ingest, process, and docs ops just run, each timestamped `2026-07-08`.

- [ ] **Step 5: Report to user**

No code — summarize: vault now has 6 wiki pages, 0 unprocessed raw captures, a new AUDIT op wired end-to-end (CLAUDE.md + SKILL.md routing), all committed. Obsidian registration and NEOKNOWLEDGE reconciliation remain deliberately deferred per the spec.
