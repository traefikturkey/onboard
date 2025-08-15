# Proposed Instruction Metrics Workflow (User Perspective)

Status: Draft (commands are illustrative / not yet implemented)

---
## 1. Core Concept
You work exactly as before, but you add one lightweight line to a TSV log **after** each task. A small set of helper prompt commands (future automation) standardizes version bumps, logging, and weekly reports.

The system backbone:
- `.github/instructions/VERSION` → current `INSTRUCTION_VERSION`
- `.devplanning/instruction-metrics/log.tsv` → one line per completed task
- `.github/instructions/CHANGELOG.md` → version rationale + hypothesized & actual impact
- `.devplanning/instruction-metrics/tracking_improvements.md` → canonical metrics definitions & thresholds

---
## 2. Typical Task Lifecycle (High-Level)
1. Start: Read user request → mentally list requirements (already part of normal flow).
2. Work: Perform actions (edits, tests, etc.).
3. Verify: Build / lint / test (where applicable).
4. Log: Append a row (manual now, future: `/metrics log`).
5. If instruction edits occurred → bump version → changelog entry.
6. End of week: Generate a weekly report (`/metrics summarize-week`).

---
## 3. Fictional Prompt Commands (Planned)
These do **not** exist yet; they document the intended UX.

Command | Purpose | Under-the-hood Actions
--------|---------|------------------------
`/metrics init` | Initialize metrics infra (first run) | Create VERSION (if missing), log.tsv with header, empty CHANGELOG
`/metrics status` | Show current version + last 5 log lines + pending TODOs | Read VERSION, tail log.tsv, parse open tasks
`/metrics log` | Append a task entry interactively | Prompt for fields → append sanitized TSV line
`/metrics log --quick <task_id>` | Fast append with defaults (Y/N heuristics) | Auto-fill common Y values, estimate verbosity chars
`/metrics version bump "<reason>"` | Bump instruction version | Increment date-suffix, update VERSION, add CHANGELOG stub
`/metrics summarize-week` | Produce weekly metrics block | Parse log, compute rates, output markdown block ready to paste
`/metrics add-metric <name>=<desc>` | Extend schema (end column) | Update header (new col), document rationale in CHANGELOG
`/metrics guard --lines <n>` | Warn if pending patch > threshold | Compare proposed diff stats to large rewrite limit
`/metrics validate` | Sanity-check log integrity | Check column counts, unknown values, chronological order
`/metrics diff-version <old> <new>` | Show changes between versions | Git diff instruction files + summarize
`/metrics retro-log <task_id>` | Insert historical row at correct position | Rebuild file with chronological insertion
`/metrics prune --dry-run` | Show compression/dedup plan | Identify redundant notes or blank rows

---
## 4. Detailed Flow Examples
### 4.1 New Repository Setup
```
/metrics init
```
Outcome:
- Creates `INSTRUCTION_VERSION=2025-09-14.1` if missing
- Writes TSV header to `log.tsv`
- Generates initial `CHANGELOG.md` baseline entry
- Confirms presence of `tracking_improvements.md`

### 4.2 Standard Task (No Instruction Change)
1. Perform work.
2. Verify (tests/lint/build) → all green.
3. Compute approximate output char count (assistant UI could pre-fill).
4. Log:
```
/metrics log
  task_id: TASK-431
  build_run: Y
  lint_run: Y
  tests_run: Y
  verification_complete: Y
  premature_done: N
  edit_attempts: 1
  patch_failures: 0
  scope_creep: N
  user_corrections: 0
  large_rewrite: N
  first_pass_tests: Y
  first_pass_lint: Y
  lines_changed: 18
  verbosity_chars: 520
  target_band: moderate
  delta_reporting: Y
  notes: Minor feature; all checks green.
```
Appends TSV line with current instruction version.

### 4.3 Task Involving Instruction Edits
1. Make minimal surgical edits to instruction file(s).
2. Decide version bump needed (material change threshold).
3. Bump:
```
/metrics version bump "Clarified patch failure recovery rule; expect PF↓"
```
4. Edit instructions.
5. Log task using new version.
6. CHANGELOG entry auto-filled:
```
## 2025-09-14.2 (2025-09-16)
Change: Clarified patch failure recovery rule.
Hypothesis: Reduce patch_failures rate by 15%.
Actual (T+7d): <pending>
```

### 4.4 Weekly Report
```
/metrics summarize-week --week 2025-W38
```
Produces markdown snippet:
```
## Weekly Report (2025-09-21)
Improved: Patch Failure Rate (0.11 → 0.07)
Regressed: Verbosity Ratio median (0.95 → 1.18)
Stable: Scope Creep (0.0%)
New Issues: Rising user corrections (0.2 → 0.6)
Actions:
1. Tighten verbosity guidance (proposed wording ...)
2. Add clarification prompt gating step.
```
You paste (or auto-append) into `tracking_improvements.md`.

### 4.5 Adding a New Metric (e.g., tool_choice_accuracy)
```
/metrics add-metric tool_choice_accuracy="Was first chosen tool appropriate (Y/N)"
```
Steps:
- Append `\ttool_choice_accuracy` to header end
- Insert blank field for existing lines
- Bump version with rationale
- Add CHANGELOG stub
- Update metrics table in `tracking_improvements.md`

### 4.6 Recovering from Failures
If two patch failures in a row:
```
/metrics status   # shows failure streak trigger
/metrics log --quick TASK-442  # (still logs prior attempt)
# Assistant posts Consolidated Root Cause & Plan message manually
```

### 4.7 Guarding Against Large Rewrite
Before applying big patch:
```
/metrics guard --lines 168
```
Outputs warning:
```
Large rewrite threshold exceeded (150). Require explicit user approval or tag [broad-change-ok].
```

---
## 5. Manual Mode (Current State)
Until tooling exists you manually:
- Edit `VERSION` for bumps
- Append rows to `log.tsv`
- Update `CHANGELOG.md`
- Add weekly report sections manually
This document defines future automation targets.

---
## 6. Log Row Anatomy
Column | Source | Notes
-------|--------|------
`date,time` | System clock | ISO date + HH:MM:SS 24h
`task_id` | User or generated | Must be stable for reference
`instruction_version` | VERSION file | Snapshot at completion
`build_run/lint_run/tests_run` | Verification actions | Y/N
`verification_complete` | Derived (all required ran) | Y/N
`premature_done` | Human/heuristic | Y if declared w/o evidence
`edit_attempts` | Count of successful apply operations | Integer
`patch_failures` | Failed apply retries | Integer
`scope_creep` | Human judgement vs requirements | Y/N
`user_corrections` | Count user redirect messages | Integer
`large_rewrite` | Lines changed >150 & not requested | Y/N
`first_pass_tests` | Tests green on first try | Y/N
`first_pass_lint` | Lint green on first try | Y/N
`lines_changed` | Diff stat | Integer
`verbosity_chars` | Char count of assistant responses (final turn or aggregate) | Integer
`target_band` | simple|moderate|complex | Predefined ranges
`delta_reporting` | Followed delta progress rule | Y/N
`notes` | Brief context | Free text (sanitize tabs)

---
## 7. Version Bump Decision Checklist
Bump if ANY:
- Added/removed metric definition.
- Altered mandatory workflow rule.
- Modified failure recovery or guard thresholds.
- Changed logging schema or column semantics.
Else accumulate minor clarifications until a natural release point.

---
## 8. Weekly Aggregation Pseudocode
```python
import csv, statistics, datetime
from collections import Counter

rows=[]
with open('log.tsv') as f:
    r=csv.reader(f, delimiter='\t')
    for line in r:
        if line and line[0].startswith('#'): continue
        rows.append(line)
# Map indices per header order (omitted for brevity)
# Filter by ISO week, compute rates and medians.
```

---
## 9. Future Automation Roadmap
Phase | Automations
------|------------
1 | `status`, `log`, `version bump` basics
2 | `summarize-week`, `guard`, `validate`
3 | `add-metric`, changelog impact auto-fill, coverage hooks
4 | Branch A/B comparison tooling

---
## 10. Governance Principles
- Add metrics slowly; remove stale ones.
- Always hypothesize impact for instruction edits.
- Never retroactively alter past log lines (immutability); corrections logged as new rows with note.

---
## 11. Quick Reference Cheat Sheet
Action | Manual Now | Future Command
-------|------------|---------------
Log task | Append TSV line | `/metrics log --quick <task>`
Bump version | Edit VERSION + CHANGELOG | `/metrics version bump "reason"`
Weekly report | Manual script/Excel | `/metrics summarize-week`
Add metric | Edit header + docs | `/metrics add-metric ...`
Large rewrite check | Visual diff judgment | `/metrics guard --lines N`

---
## 12. Example Manual Log Line
```
2025-09-14	11:42:10	TASK-438	2025-09-14.1	Y	Y	Y	Y	N	1	0	N	0	N	Y	Y	27	480	moderate	Y	Added metrics workflow doc.
```

---
## 13. Open Questions (For Later Resolution)
- Should `verbosity_chars` be cumulative or final-turn only? (Decide before week 2.)
- Introduce `tool_choice_accuracy` now or wait for 10-task baseline?
- Need a normalization for tasks without build/test context (mark NA vs N?).

---
## 14. First Adoption Steps (Actionable)
1. Create `log.tsv` (header only).
2. Start logging next 5 tasks manually.
3. Draft initial CHANGELOG baseline entry.
4. After 10 tasks, evaluate need for additional metrics.

---
End of proposed workflow.
