# Corrected chain re-run (chain2) — running notes for §20 report

## rda (TASK-RRI-RDA-02) — JUDGE_REQUIRED (6 swaps)
- Cause 1 (RUNNER BUG, FIXED): extract() leaked trailing markdown ``` fence into source -> SyntaxError
  -> all 3 GENERATE attempts errored -> F5 drove rework -> JUDGE_REQUIRED. Fixed extract() with _strip_fence.
- Cause 2 (GENUINE, §4 NOT closed): with fence stripped, coder's rda is 12/13 — audit_findings=None
  fails OPEN (`or []` -> treated as no findings -> may_proceed True; should be False), and =123 crashes.
  So §4 residual C-TOTALITY is NOT closed by this coder attempt. DW gate correctly did not ship it.
- Action: re-run rda post-chain with fixed extract; coder must handle non-list audit_findings.
  If coder still fails-open on None -> honest JUDGE_REQUIRED (coder C-TOTALITY limit), record narrowly.
- NOTE: §4 discipline + cases are hermetically correct; the LIVE closure is pending a clean coder pass.
