# DW Adjudicator Efficacy + EXECUTION Env-Signal — Results (v0.1)

Single result document for the A/B adjudicator-efficacy experiment (DE-0333) and the EXECUTION_DEFECT
env-signal follow-up (DE-0334). Bound to the sealed problemset preregistration DE-0332.

| field | value |
|---|---|
| problemset | `adjudicator_efficacy_problemset_v0.1` (canonical: `egl/docs/adjudicator_efficacy_problemset_v0.1.zip`) |
| **seal_root_sha256** | `928d6700e82d424404ff76f0f885ba9682fc6a71aabb5cc7067218675506afb2` (unchanged across both runs) |
| preregistration | DE-0332 / ADM-0332 (`dev-workcell/experiments/adjudicator_efficacy_v0.1/PREREGISTRATION.md`, seal `2dbc380a`) |
| efficacy run | DE-0333 / ADM-0333 (baseline, pre env-signal) |
| env-signal path | **DE-0334 / ADM-0334** (this document's headline result) |
| arms | A = `DW_ADJUDICATOR=off` (blanket: test-fail → REGENERATE) · B = `on` (3-tier adjudicator). Only the flag differs. |
| integrity | per-file 89/89 hash match · seal_root recomputed == stored == expected · qa all_ok 20/20 · 10 problems · Level 1–5 ×2 · class CODE×3/ORACLE×3/EXECUTION×2/INDETERMINATE×2 |

## 1. Execution conditions

- **Stage 1 (classification / routing isolation)**: no worker generation. CODE/ORACLE/EXECUTION problems: the
  shipped (defect-injected) workspace is run deterministically per `runner.json`; the neutral result is handed to
  the adjudicator. INDETERMINATE (Q04/Q08): not executed — the shipped `stage1_evidence_packet.json` is used as-is
  (deterministic reproduction of missing/unreliable evidence), reference oracle disabled.
- **Stage 2 (full loop → terminal)**: the shipped workspace is the initial artifact; the **real `dw.workcell` state
  machine** is driven under an **isolated `DW_DATA_DIR`** (production ledger untouched); rework runs to a terminal
  state. INDETERMINATE Stage-2 (Q04/Q08) requires a sealed `stage2_injection_mechanism` and a deterministic injector
  that is not built — marked NOT_RUN.
- **Execution matrix**: seed `20260715`, 20 runs, per-problem A/B order frozen pre-run, same initial snapshot, no
  cross-problem carryover.
- **Information barrier**: the only inputs ever given to an LLM (tier-2 reference oracle, Stage-2 regenerator) are
  the **public** `task_packet.objective` + `acceptance_criteria` + entry filename. `sealed/` (ground truth +
  baseline) is read **only** by the deterministic scorer, after all runs are frozen. `workspace_manifest.json` is
  public evidence (README §5), not sealed.
- **Env-signals (DE-0334)**: measured by the neutral runner only (`probe_environment`), never worker self-report.
  Adjudicator code unchanged between A and B — the flag is the sole difference.

## 2. Before → after matrix (env-signal effect)

`A` is the invariant control (blanket); env-signals do not touch its path. `B` is the adjudicator.

| metric | A (before) | A (after) | B (before) | B (after) |
|---|---|---|---|---|
| **defect attribution** | 3/10 | 3/10 | 8/10 | **10/10** |
| routing exact | 3/10 | 3/10 | 8/10 | **9/10** (+1 conditional-alt = 10/10 acceptable) |
| terminal correct (Stage 2, 8 run) | 3/8 | 3/8 | 6/8 | 6/8 |
| **false REGENERATE** | 7/10 | 7/10 | 1/10 | **0/10** |
| **prohibited code-change** (non-CODE churned) | 5/10 | 5/10 | 1/10 | **0/10** |
| false JUDGE_REQUIRED | 0 | 0 | 0 | 0 |
| INDETERMINATE | 0 | 0 | 3/10 | 2/10 (Q04/Q08 only = correct safe-stop) |

Per-problem deltas (B):
- **Q03** (EXECUTION, runner.json wrong script path): INDETERMINATE → **EXECUTION_DEFECT** (`missing_invoked_script`),
  route SAFE_STOP → **RUNTIME_RETRY (exact)**, code preserved.
- **Q07** (EXECUTION, setup.sh destroys fixtures/): CODE_DEFECT (code churned) → **EXECUTION_DEFECT**
  (`workspace_manifest_violation`), route REGENERATE → **RUNTIME_RETRY (∈ allowed_routing_alternatives)**, **code
  preserved**. The intended discrimination Q05 (CODE) vs Q07 (EXECUTION) holds — Q05 stays CODE_DEFECT.

### Headline
- **attribution 8 → 10** (both EXECUTION cases now correct).
- **false-REGENERATE 1 → 0**.
- **prohibited code-change 1 → 0**.

## 3. Classification precedence (env-signal)

`classify_test_failure` gains a highest-precedence pre-gate:
§0 no neutral result → INDETERMINATE → **§0.5 confirmed env corruption → EXECUTION_DEFECT** → §1 precheck
(import/timeout) → §2 ORACLE (test-harness syntax/crash) → §3 CODE (code crash) → §4 assertion → NEEDS_REFERENCE
→ §5 INDETERMINATE. Confirmed environment corruption precedes CODE/ORACLE/assertion/INDETERMINATE (a broken
environment invalidates the test as an observation of the code). **Insufficient/absent env evidence never infers
EXECUTION** — control falls through to the ordinary tiers. `env_signals=None` reproduces the pre-DE-0333
classification exactly (behaviour preserved; 24/24 counterfactual + regression tests).

Env-signal vocabulary (measured): `missing_invoked_script`, `missing_executable`, `missing_cwd`,
`workspace_manifest_violation`, `missing_fixture_precondition`, `permission_denied`, `runner_identity_mismatch`,
`timeout`, `process_spawn_failure`. `execution_subclass` (runner_misconfiguration / environment_corruption /
resource) is recorded but does **not** change routing.

## 4. Why Stage-2 terminal (B) stays 6/8

The two unchanged misses are Q03 and Q07 — now **correctly classified (EXECUTION) and code-preserved**, but their
Stage-2 terminal is `EXEC_ESCALATED_NO_REPAIR_ACTUATOR_CODE_UNCHANGED` (JUDGE_REQUIRED, code unchanged) rather than
the expected `PASS_AFTER_ENV_REPAIR_CODE_UNCHANGED`:

- **No env-repair actuator.** The EXECUTION path re-executes the *same* code via the Runtime Supervisor's bounded
  re-run; it does **not** repair the environment (fix the runner path, restore destroyed fixtures). With the env
  still broken, the retry fails again and the machine escalates at the rework threshold. Building a repair actuator
  was explicitly out of scope (frozen) for the env-signal task — classification/attribution was the target, not
  automated recovery-to-pass.
- **RUNTIME_RETRY vs ENV_REPAIR_RETRY not separated.** The adjudicator emits a single `EXECUTION_DEFECT` →
  `RUNTIME_RETRY`. Q03 (runner misconfiguration) matches exactly; Q07 (environment corruption) expects
  `ENV_REPAIR_RETRY` and is absorbed as a conditional-correct alternative. Sub-routing by `execution_subclass` is
  recorded but not yet wired into routing.

## 5. Remaining ambiguity / not-yet-observed

- Env-repair → PASS actuator: **not implemented** (Stage-2 EXECUTION terminals do not reach PASS).
- RUNTIME_RETRY vs ENV_REPAIR_RETRY sub-routing: **not separated** (single EXECUTION_DEFECT → RUNTIME_RETRY).
- **Live JSONL path**: the env-signal wiring (`live_worker_runtime._run_test` → `webui.au` finding) is implemented,
  but env-signal firing on a real planner-generated task is **not yet observed** (no live EXECUTION corruption seen).
- Stage-2 INDETERMINATE (Q04/Q08): **NOT_RUN** (needs a deterministic sealed injector, unbuilt).

## 6. Claim ceiling

- **`EXECUTION_DEFECT_ENV_SIGNAL_PATH_PROVEN`** — the env-signal path works end-to-end (tier=`env_signal`; Q03/Q07
  reach EXECUTION_DEFECT from measured signals).
- **`EXECUTION_DEFECT_DISCRIMINATION_IMPROVED_ON_SEALED_CASES`** — attribution 8→10, false-REGENERATE 1→0,
  prohibited code-change 1→0, on the sealed v0.1 set.

### Not claimed
`ADJUDICATOR_EFFECTIVE_ON_COMPLEX_SEALED_CASES` · `WORKER_QUALITY_IMPROVED` · `STAGE2_TERMINAL_FULLY_MEASURED`.

## 7. Bindings

- Preregistration: **DE-0332 / ADM-0332** (seal_root 928d6700).
- Efficacy run (baseline): **DE-0333 / ADM-0333**.
- Env-signal path (this result): **DE-0334 / ADM-0334** (owner=taka, RUN_COMPLETE).
- Implementation commits: dev-workcell `5e5a2f7` (adjudicator + harness + scorer), twoder `63e632c` (live wiring).
- Design lineage: DE-0324 (`DESIGN_ADJUDICATION_POINT_v0.1`), closure DE-0323 (oracle-sep measurement not
  identifiable on the current machine).
