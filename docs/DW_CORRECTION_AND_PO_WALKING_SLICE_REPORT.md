# DW Correction + Process Optimizer Walking-Slice Report

Narrow implementation/operational review packet (Taka directive §20). Date 2026-07-07.
Not a re-summary of 2DER architecture. Scope: the corrections and the first Optimizer walking slice.

---

## A. DW persistence correction (F-1)

- **Pre-fix loss scope**: DW live-run primitives were written to a `TemporaryDirectory` and discarded at
  process exit. Model-switch / run-boundary events were never recorded at all.
- **Real run SoR location**: `dev-workcell/run_sor/events.jsonl` (append-only). Process primitives
  (`RUN_START/END`, `SWAP_START/END`) recorded into the *same* log with real wall-clock timestamps;
  `derive_state` ignores them; `derive_process_trace` derives the trace from the primitives.
  Trial JSON demoted to `BOOTSTRAP_REPORTED`.
- **Summary-deletion reconstruction test (AC-2)**: **PASS**. For `TASK-RRI-AXIS-01-…`, after deleting the
  summary JSON, reconstruction from primitives alone recovered: final_state=COMPLETE, model identities
  (coder@8006 + qwen@8005-auditor), generator runs + test result, findings, dispositions, revision
  lineage, upper_review, RESULT_PACKET (COMPLETE event). `reconstruction complete WITHOUT summary = True`.
- Evidence: DW DE-0006, `test_process_trace.py` 8/8; `f1_reconstruct.py`.

## B. Disposition-before-rework (the load-bearing correction)

- **Pre-fix workflow**: `AUDIT → raw findings → immediate REGENERATE` (raw auditor findings became worker
  instructions). This caused the axis regression: 7/7 passing → raw findings → rework → 6/7 → JUDGE_REQUIRED.
- **Post-fix workflow**: `AUDIT → MANAGER DISPOSITION → (ACCEPTED/PARTIAL only) REGENERATE → re-AUDIT`.
  New DW states `DISPOSITION_REQUIRED` / `READY_FOR_REGENERATE`; `record_disposition`
  (ACCEPTED/PARTIAL/REJECTED/REMAINS, malformed→fail-closed); `rework_items()` returns ACCEPTED +
  PARTIAL accepted_portion only; completion is disposition-based (REJECTED never blocks COMPLETE).
- **Disposition policy (live runner)**: deterministic + oracle-free — a finding is ACCEPTED only if its
  counterexample **objectively reproduces** a defect (crash / malformed output); otherwise REJECTED.
- **Would known over-flag cases have avoided rework? YES — measured on the corrected chain re-run.**
  Chain dispositions = **{ACCEPTED: 0, PARTIAL: 0, REJECTED: 3, REMAINS: 0}**. The auditor over-flagged
  3 times; all 3 failed to reproduce → REJECTED → **zero auditor-driven rework**. The 3 reworks observed
  were all failing-test (F5) driven. **axis re-ran at 2 swaps / 0 rework / COMPLETE** (vs the prior
  6/7 regression); **transform** (prior JUDGE_REQUIRED) also COMPLETEd.
- Evidence: DW DE-0007, `test_disposition.py` CF-DISP-1..6 (9/9); all 53 DW tests pass.

## C. RDA v2 totality closure (§4)

- v2 residual: `audit_findings=None` fails open (`or []` → treated as no-findings → may_proceed True),
  `=123` crashes. §4 added `audit_findings=None/123` cases + spec clause (non-list → reject, never crash).
- **Live re-run outcome**: **JUDGE_REQUIRED (honest coder limit).** With the fence fixed the code runs
  (GENERATE 12/13); the only failing case is `audit_findings=None` (coder fails open → may_proceed True).
  F5 drove rework twice; the coder could **not** close the None case in 2 reworks (REGEN#1/#2 stayed
  12/13) → escalated to JUDGE_REQUIRED. The Qwen auditor found **0 findings** (it missed the None
  fail-open too) — only the deterministic load-bearing test caught it, and the **gate correctly refused
  to ship the 12/13 code**. So §4's discipline + test are correct and the net worked, but the
  DW-produced code does not satisfy C-TOTALITY on None; rda is **not committed** and awaits a clean coder
  pass or human adjudication. This is the DW gate working (refusing broken code), not a silent pass.
- Note: the first corrected-chain rda hit JUDGE_REQUIRED from **two** causes: (1) a runner `extract()`
  bug leaking the trailing markdown ``` fence into the source → SyntaxError (FIXED via `_strip_fence`),
  and (2) the coder's genuine None fail-open. The §4 discipline + cases are hermetically correct; live
  closure depends on a clean coder pass.

## D. Auditor contract + finding category changes

- **§5 test-set adequacy**: `audit_once` now gives the auditor the test inventory + acceptance goal and
  instructs it to attack whether the supplied tests are load-bearing / the tested surface is narrower
  than the property, and to attach a concrete `counterexample_input` + `uncovered_shape` per finding
  (not merely pass/fail against given tests). Grounded in the RDA-v1 observation (7/7 + clean audit,
  fail-open remained, upper review found the missing shape).
- **§6 category preservation**: `record_audit` preserves finding category — known → keep;
  unknown string → `other` + `raw_category`; non-str → fail-closed. Metrics recomputable from primitives.

## E. Process Optimizer walking slice (§16)

- **Deterministic trigger** (over 6 chain traces, primitives only; LLM is not the cost calculator):
  overhead_ratio = **0.981** (model-switch = 98% of wall-clock), 18 switches. Fired:
  `DOMINANT_OVERHEAD` (0.981 ≥ 0.30), `REPEATED_HIGH_COST` (18 ≥ 3), `SERIAL_INDEPENDENT_WORK` (6 serial).
  Optimizer LLM invoked **only because** a trigger fired.
- **Input trace set**: all 6 completed/attempted RRI deterministic-core traces + set-level aggregate +
  independence relation (all validators mutually independent). Not a single trace.
- **Qwen3.6 candidate (no pre-seed)**: dominant_cost = model_switch_overhead, structurally_avoidable=true,
  dependency_required=false, proposed_change = *"Parallelize execution of mutually independent
  deterministic-core validators…"*. `native_capability` ESTABLISHED claim had no EGL ref → §13 downgraded
  to NOT_ESTABLISHED → research_need.
- **Self-formed axes** (of the forbidden pre-seeds, formed unprompted): raw-findings→avoidable-rework ✓,
  independent-slices-serialized ✓, model-switch-dominates ✓, native-capability-not-inspected ✓. It did
  **not** jump to a specific solution (no "vLLM Sleep Mode"); instead it **emitted RESEARCH_NEED
  (`concurrent_task_dispatch`) and stopped** — routing to RRI Need Validation → Research Design → EGL.
- **Human-taught influence**: H-OPS-01/02 were **not injected**; the parallelization/dependency and
  native-capability axes were self-formed this time. (Transfer measurement remains a future unrelated
  workload — §14/§8, not claimed here.)
- **Property-preservation review** (separate actor, §12): P1–P7 all PRESERVED w/ mechanism_ref →
  `auto_adoptable=True` **against property-set v1**. This is exactly the §11 case: v1 has no
  `P8 cross-item audit context isolation`; if P8 is added, this candidate becomes REVIEW_REQUIRED.
- **Final status**: candidate + RESEARCH_NEED recorded; **no process policy auto-applied** (AC-19).

## F. A vs virtual-B reconstruction (§17)

- dependency graph: all 6 slices independent (batch-eligible). actual A-mode swaps = **18**;
  virtual-B min swaps = **4** (batch generate → 1 swap → batch audit → 1 swap, + one shared rework round).
  measured swap-latency basis ≈ 174.4s. estimated switch-time delta ≈ **2441.6s (~41 min)**.
- **Status: COUNTERFACTUAL_ESTIMATE — NOT measured B performance.** Non-guarantees: B not executed;
  batch buffer / partial-work risk unmodeled; rework distribution ignored. **Do not auto-adopt B.**

## G. Director / scheduler gap candidate

- Recorded narrow (EGL DE-0079, GAP-2DER-2): operational policy evidence was formed (model-switch cost /
  swaps/item decision-relevant), but the chain kept running slice-by-slice A-mode; there is no sanctioned
  Director/scheduler path that re-evaluates and applies execution-mode policy from accumulated evidence.
  General Director NOT implemented here.

## H. Open gaps

- **GAP-2DER-1** (EGL DE-0078): H0–H5 human-intervention events are not yet DW run-SoR primitives.
- **GAP-2DER-2** (EGL DE-0079): no sanctioned Director/scheduler applies execution-mode policy.
- **rda §4 live closure**: pending a clean coder pass (see C).
- **Runner extract() fence bug**: fixed (`_strip_fence`); was the mechanical cause of one JUDGE_REQUIRED.
- **Auditor over-flag rate**: the auditor still over-flags (3 findings, 0 substantiated); §3 makes this
  harmless (REJECTED, no rework), but auditor quality itself remains NOT_PROVEN / unimproved (not claimed).

---

### Acceptance criteria status
AC-1✓ AC-2✓ AC-3✓ AC-4✓ AC-5✓ **AC-6 ✗** (discipline+test correct, but coder can't close `audit_findings=None`;
gate correctly escalated JUDGE_REQUIRED — broken code not shipped; needs clean coder pass / adjudication)
AC-7✓ AC-8✓ AC-9✓ AC-10✓ AC-11✓
AC-12✓ AC-13✓ AC-14✓ AC-15✓ AC-16✓ AC-17✓ AC-18✓ AC-19✓

### Core-question answer (§21)
On the corrected chain, 2DER **did** observe its own process cost from primitives, identify the dominant
structurally-avoidable cost, propose a simpler process (parallelize independent work) **without silently
weakening a required property** (preservation-reviewed against a versioned set, with the future-property
review mechanism in place), and **route the unknown to research rather than absorbing it**. The
human-taught perspective is retained separately; its *transfer* to an unrelated task is not yet claimed.
