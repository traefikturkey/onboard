# Instruction Improvement Tracking Plan

## 1. Purpose
Establish objective, repeatable metrics to measure whether changes to instruction files improve assistant behavior (accuracy, efficiency, compliance, minimalism). Keep data collection lightweight and automatable.

## 2. Instruction Versioning
- Add a single `INSTRUCTION_VERSION` line to `.github/instructions/VERSION` (e.g. `2025-09-14.1`).
- On any material instruction change, increment suffix (semantic date-based versioning).
- Every task log entry captures the version for later correlation.

## 3. Quantitative Metrics (Per Task / Session)
| Code | Metric | Definition | Goal (Initial) |
|------|--------|------------|----------------|
| VC  | Verification Completed | Build+lint+tests run before declaring done (Y/N) | >95% |
| PC  | Premature Completion | Declared done without evidence (Y/N) | <5% |
| PF  | Patch Failures | Count of failed patch applications | <0.08 / patch |
| EA  | Edit Attempts | Avg attempts per file (successful apply) | <1.3 |
| SC  | Scope Creep | Touched unrelated files vs request (Y/N) | <3% |
| UC  | User Corrections | User messages directing reversal/redirect | <1 per task |
| LR  | Large Rewrite Flag | >150 changed lines w/o explicit user request | 0 |
| FP  | First-Pass Tests Pass | Tests green on first run after change (Y/N) | >70% (raise to 85%) |
| FL  | First-Pass Lint Pass | Lint passes first attempt (Y/N) | >80% |
| VR  | Verbosity Ratio | Actual chars / target band midpoint | 0.7–1.1 |
| DR  | Delta Reporting | Only deltas (not full checklist) in progress updates (Y/N) | >90% |
| BW  | Build Wait Count | Redundant rebuilds for same root cause | <=1 |

## 4. Qualitative Metrics (Weekly Sample of 5 Tasks)
Score 1–5:
- Clarity
- Brevity
- Fidelity (followed user directives ordering)
- Minimalism (surgical diffs)
- Proactive Verification
Collect top 3 negative patterns with brief examples.

## 5. Data Collection Implementation
Create log file: `.devplanning/instruction-metrics/log.tsv`

Header:
```
# date\ttime\ttask_id\tinstruction_version\tbuild_run\tlint_run\ttests_run\tverification_complete\tpremature_done\tedit_attempts\tpatch_failures\tscope_creep\tuser_corrections\tlarge_rewrite\tfirst_pass_tests\tfirst_pass_lint\tlines_changed\tverbosity_chars\ttarget_band\tdelta_reporting\tnotes
```
Append one line per completed task.

### Minimal Helper Convention (Manual to Start)
When finishing a task, append structured line (can be automated later by a script). Maintain target band per complexity class:
- Simple (command/run): 80–250 chars.
- Moderate (single-file edit): 250–600.
- Complex (multi-file feature): 600–1200.

## 6. Thresholds & Alerting
Flag any metric degrade >10% week-over-week or any threshold breach. Add a weekly section to `tracking_improvements.md` summarizing breaches and planned adjustments.

## 7. Weekly Aggregation Workflow
1. Parse `log.tsv` (simple Python script later) to compute:
   - Rates: premature completion %, scope creep %, etc.
   - Averages: edit attempts, patch failures, verbosity ratio.
2. Compare to previous week.
3. Update `tracking_improvements.md` with a `## Weekly Report (YYYY-MM-DD)` section.
4. List: Improved, Regressed, Stable, New Issues.
5. Propose at most 2 micro-changes to instruction files (to keep attribution clear).

## 8. Improvement Lifecycle
```
Collect → Aggregate → Identify Top 2 Issues → Propose Instruction Edits → Version Bump → Monitor Next Week → Accept or Revert
```

## 9. Large Rewrite Detection
- Compute changed line count per patch; if >150 and not explicitly requested, mark `large_rewrite=Y` and open an "investigate scope violation" note.

## 10. Failure Recovery Rule
If two consecutive patch failures or two successive build/test failures in same context:
- Require a "Consolidated Root Cause & Plan" message before further edits.
Track whether this rule was triggered and followed (future metric FR: failure recovery compliance).

## 11. Optional Future Enhancements
- Add Git hook to reject commits exceeding large rewrite threshold without commit message tag `[broad-change-ok]`.
- Lightweight CLI script `scripts/log_task.py` to append rows safely.
- Visualization: generate weekly sparkline PNG (coverage, premature rate) for README.
- A/B testing: maintain alternate instruction branch and alternate daily usage; compare metrics (only after baseline stabilizes 2 weeks).

## 12. CHANGELOG Discipline
- Maintain `.github/instructions/CHANGELOG.md` capturing: version, date, change summary, hypothesized metric impact, actual impact after one week.

## 13. Coverage Tie-In
Correlate first-pass test success with modules touched to identify chronic problem areas (e.g., Dockerfile vs Python). Optionally add dimension columns: `domain=docker|python|tests`.

## 14. Example Log Entry
```
2025-09-14	10:32:05	TASK-123	2025-09-14.1	Y	Y	Y	Y	N	1	0	N	0	N	Y	N	42	540	moderate	Y	Minimal diff; all checks green.
```

## 15. Success Definition (Stabilization Targets)
All below sustained for 3 consecutive weeks:
- Premature completion <2%
- Scope creep <1%
- First-pass tests >85%
- Patch failure rate <5%
- Large rewrites = 0
- Verbosity ratio median 0.85–1.05

## 16. Action Mapping Table
| Issue | Metric Trigger | Instruction Adjustment Type |
|-------|----------------|-----------------------------|
| Premature completion spike | PC >5% | Strengthen verification wording / add checklist gate |
| Scope creep increase | SC >3% | Emphasize surgical diff & dependent enumeration |
| Verbosity high | VR >1.2 | Tighten concise guidance, reduce allowed char band |
| Patch failures rising | PF >0.12 | Add pre-edit validation step emphasis |
| User corrections up | UC >1.5 | Reinforce Primacy + ask-only-if-blocked clause |

## 17. Review Cadence
- Daily: Quick scan of new entries (30s).
- Weekly: Full aggregation and adjustments.
- Monthly: Assess if any metrics can be retired or automated.

## 18. Minimal Startup Tasks (To Do)
- [x] Add `VERSION` file.
- [ ] Add initial `log.tsv` with header.
- [ ] Record baseline for last 5 recent tasks manually (estimate metrics).
- [ ] Add CHANGELOG entry for current version baseline.

---
This document should evolve ONLY via logged, versioned changes correlated with metrics.
