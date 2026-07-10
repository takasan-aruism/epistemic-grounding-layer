# Instrument-validity audit — "did we actually use 2DER?" (suspends the DE-0144 MIXED verdict)

**as-of 2026-07-11.** Read-only audit + one full-path dogfood trace. The earlier "2DER→Claude = MIXED /
reconstruction MISSING" conclusion is **SUSPENDED as instrument-invalid**. Evidence below is actual code path +
the saved trace `experiments/dogfood_qwen_fullpath_trace.json`. No capability claim; CLOSED-NEGATIVE mechanisms
were run as-is and are **not** relabeled positive. C≠H.

## THE ONE QUESTION — did the earlier dogfood use 2DER?
**NO.** `autonomy/ingest.py` calls exactly `build_current_state()` + `answer_question()` (self_grounding
retrieval) + handoff assembly. It **never** invokes AFE, Formal, detection, or the scheduler
view→signature→compare→**rebuild** (reconstruction). So the earlier run = **GROUNDING_ONLY / NOT_2DER for the
problem-solving core**. My "reconstruction MISSING" was a **conflation of `not-called` with `not-existing`** —
the instrument-validity failure Taka flagged. The MIXED verdict does not describe 2DER; it describes a minimal
handoff I built. Suspended.

## Full-path run (just executed, dogfood_fullpath.py) — the owned mechanisms DID run
| stage | mechanism (actual code) | ran? | produced (on the Qwen swap problem) |
|---|---|---|---|
| HISTORY | `egl.self_grounding.answer_question` | ✅ | DE-0143/0074/0075/**0086**; correct synthesis (sleep-mode broken → cold-load forced → bottleneck) |
| DETECTION | `run_afe_walking.run_operator`×ADMITTED → `aggregate` → `orchestrate` + `arm_ABE("B")` | ✅ | missing dims: exclusive-ownership **vs shared-pooling**; container-lifecycle **vs model-layer**; binary **vs continuous**; skeptic "174.5s = weight-load or container overhead?" |
| RECONSTRUCTION | `run_scheduler_exhibit.rs_run` (view→signature→compare→rebuild→check) | ✅ | alternative frame "Temporal-Continuity Gap: decouple model residency from container lifecycle; cost isn't loading weights"; `resolved=True` |

**These are NOT MISSING.** They are EXHIBIT-ONLY (manual-gated) + CLOSED-NEGATIVE at the *HBB reconstruction bar*
(= failed to structurally match historical breakthroughs) / WEAK-NEGATIVE evidence (AFE content ≤ generic
skepticism). But on this real problem they **ran and produced detection + a reconstructed alternative frame**.
Whether that reframe is *correct/useful* is for Taka/senior to judge — the mechanism does not claim it.

## PHASE 1 — full current 2DER executable inventory (existence / evidence / general-wiring separated)
| component | file/function | mechanism status | executable today | callable from general problem | why not (already) connected |
|---|---|---|---|---|---|
| history/reality | `self_grounding.answer_question`, `current_state` | LIVE | YES | YES | (connected) |
| acquisition (machine facts) | `egl/acquisition.py`,`adapters.py`,`demo_machine_ai`(DE-0027) | LIVE-narrow | YES | partial | scoped to SOFTWARE_TECHNICAL |
| detection: AFE ensemble | `run_afe_walking` run_operator/aggregate/orchestrate | EXHIBIT-ONLY, content WEAK/NEG (DE-0103/4) | **YES** | **YES** (`arm_C/ABE(frame)`) | never wired to a general-problem entrypoint |
| detection: skepticism | `run_afe_walking.arm_ABE("B")` | EXHIBIT, strong HBB detector | YES | YES | — |
| detection: Formal | `formal_esde_operators` FE-LINK/TERNARY | EXHIBIT, WEAK/NEG | YES | YES | — |
| reconstruction | `run_scheduler_exhibit.rs_run` (view/signature/compare/rebuild) | EXHIBIT-ONLY, **CLOSED-NEGATIVE at HBB bar** (DE-0130) | **YES** | **YES** (`rs_run(frame,seed,V)`) | ephemeral persistence; never wired to general input |
| STOP-SHIFT-RUN-COMPARE scheduler | `run_scheduler_*` | CLOSED-NEGATIVE (DE-0130) | YES | YES | closed at bar, but runnable |
| bridge (unresolved surface) | `run_hbb_egl_bridge` | CONFIRMED-narrow (DE-0136) | YES | needs artifact | — |
| evidence/objective test | `check_call`, `egl.judge`, `answer/open_gap split` | LIVE/EXHIBIT | YES | partial | — |
| next-operation | router SLICE-3 / handoff | LIVE-narrow | YES | repo-work only | general routing thin |
| result-ingest | `egl.result_packet` | LIVE-narrow | YES | DW-shaped | — |
| state/ledger/loop | DE ledger, CURRENT_STATE, AUTONOMY_LEDGER | LIVE | YES | YES | — |
| Attention Center / same-object binding / structural re-centering / Aruism regime | — | **UNOWNED** | NO | NO | not built |

**Discipline honored: CLOSED-NEGATIVE / WEAK-NEGATIVE / NOT-CONFIRMED are NOT collapsed into MISSING.** MISSING =
no mechanism (UNOWNED). The detection/reconstruction mechanisms EXIST + RUN; they are unwired-to-general-input +
unvalidated-at-the-HBB-bar. Different things.

## PHASE 2 — original 4-function path, reconstructed from evidence
1. **CURRENT REALITY / NORMAL** — built: self_grounding + current_state + acquisition. Survived: LIVE. Executable: yes.
2. **DETECT STUCKNESS / MISSING AXIS** — built: AFE(C/E) + skepticism(B) + Formal(D). Evidence: B strong, AFE content ≤ B (WEAK/NEG). Executable: yes (ran today).
3. **RECONSTRUCT ALTERNATIVE PATH** — built: scheduler view→compare→rebuild (DETECTION_RECONSTRUCTION_SPLIT DE-0114). Evidence: CLOSED-NEGATIVE at HBB autonomous-H0 bar. Executable: yes (ran today, produced an alt frame). Unwired to general input.
4. **RETURN / COMPARE / EXECUTE / UPDATE** — built: check_call(CHANGED/HOLD), answer/open_gap split, DE/state update, result_packet, Claude executor. Executable: partial.

## PHASE 4 — judgment
- earlier ingest run: **GROUNDING_ONLY (NOT_2DER)**.
- full-path run: **PARTIAL_PATH_USED → the owned problem-solving mechanisms (history+detection+reconstruction) were actually invoked** for the first time on a general problem.

## FINAL ANSWERS
**A.** existing dogfood = **GROUNDING_ONLY** (code: ingest.py = build_current_state + answer_question only).
**B.** 4-function actual components = table above (§Phase 2).
**C.** fullest callable path = HISTORY(self_grounding) → DETECTION(AFE+skepticism+Formal) → RECONSTRUCTION(scheduler rebuild) → check/compare → next-op. All ran today.
**D.** full-path trace = `experiments/dogfood_qwen_fullpath_trace.json` (detection missing-dims + skeptic + reconstructed alt frame).
**E.** minimal-handoff vs full-path = handoff produced **history only**; full path produced **detection + reconstruction (reframes: decouple loading from container lifecycle / pooling / is-it-container-overhead)** that neither the handoff nor Claude-alone produced.
**F.** 2DER 実力判定 (bounded): **NOT ポンコツ and NOT validated** — the owned mechanisms *run and produce detection+reconstruction content* on a real problem; their HBB-bar failure means unvalidated-for-structural-breakthrough, not content-empty. The earlier "didn't contribute" was because they were never called.
**G.** minimal wiring to remove Claude as program actor: Claude input MUST be a 2DER-produced `INVESTIGATOR_TASK` (task_id/parent_problem_id/2der_state_ref/objective/current_reality/relevant_history/detected_issue/open_gaps/selected_next_operation/artifact_refs/allowed_actions/stop_conditions); route Home → **full-path** 2DER (not minimal handoff) → investigator_task; Claude returns structured result 2DER ingests. Continuous state already held in DE ledger + CURRENT_STATE + AUTONOMY_LEDGER + PROBLEMS/HANDOFFS; only per-problem PROCESS-TRACE / attempted-paths / failed-paths is a small missing field (adapter, no parallel memory).

## bottom line — **WE DID NOT USE 2DER earlier; when actually used, it produced detection + reconstruction.**
