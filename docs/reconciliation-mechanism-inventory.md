# Reconciliation-mechanism inventory (Taka 2026-07-18 §2 — read-only, no build)

Purpose: enumerate the existing "double-entry-bookkeeping-style" reconciliation mechanisms (checking that two
records agree) across the 2DER repos, as an inventory + differential base for the §3 reconciler design. This
is READ-ONLY: nothing was built or changed.

## The DE-0006 distinction (must be explicit)

- **DE-0006 BANS a 2nd System of Record**: a *derivable duplicate* stored as if authoritative (a `counters.json`
  type) — it can silently drift from the SoR, and the drift is invisible because nothing independently produced it.
- **This inventory's target is the OPPOSITE and does NOT conflict**: reconciliation of **two records written by two
  INDEPENDENT writers** (neither is a derived copy of the other). Divergence is *meaningful* (it signals a real
  fault), and detecting it is the whole point. Example (the §3 target): a target repo's **git history** (written by
  git/commits) vs the bridge's **PATCH_APPLICATION events** (written by the bridge) — two independent writers of
  related facts; an orphan on either side = imbalance = a real problem.
- A third, sanctioned category is a **deterministically-derived view** kept as a *cache of the SoR* (not a 2nd SoR):
  RC-3 proves the view is faithfully derived and the log remains the sole SoR. That is allowed and is NOT what
  DE-0006 bans.

Classification used below: **[DE]** double-entry (two independent writers reconciled) · **[DV]** derivation-
determinism (one SoR + a faithfully-derived view) · **[TI]** transport/identity (same bytes, two places) ·
**[BG]** behavioral gate (a claimed property re-derived independently, structural or behavioral).

## Inventory

| # | Mechanism | Class | Record pair (A ↔ B) | Execution mode | On-detect behavior |
|---|---|---|---|---|---|
| 1 | **RC-3 rebuild-consistency** (`egl/verify_rebuild.py`, `egl/core.build_view`) | DV | append-only event log (SoR) ↔ SQLite view rebuilt twice from it (hash-compared) | per-invocation (acceptance test) | FAIL if the two rebuild hashes differ (view not deterministically derivable) |
| 2 | **RC-4 time-travel** (`egl/core.build_view(until_ts=…)`) | DV | full event log ↔ log truncated at a past ts (state reconstructed) | per-invocation (acceptance test) | FAIL if a past state cannot be reconstructed from the log alone |
| 3 | **Hash-transport verification** (§6 commit ritual) | TI | tested module bytes (scratchpad) ↔ committed repo bytes (after cp) | per-commit (every bridge commit) | abort the commit on sha256 mismatch |
| 4 | **LAYER-3 integrated direct re-verify** (`twoder/tools/codegen_run_fn.py`, DE-0417) | DE-ish | pipeline sandbox pass-signal ↔ direct oracle run on (base+out_code) integrated bytes | per-build (run_fn6, before SUCCESS) | do NOT report SUCCESS unless the direct run also passes (two independent evaluators of the same "passes" claim) |
| 5 | **Terminal measurement scripts** (this session's terminal checks) | BG | claimed "terminal" ↔ measured facts: git-contains-origin/master + module symbol presence + oracle/gate green on the exact committed bytes | per-terminal | do not declare terminal / do not auto-refreeze unless all measured |
| 6 | **DE-0349 structural gate** (`scratchpad gate_de0349.py`, dual-token version) | BG | claimed write-safety (sole writers, dual-token gated, zero real-repo minter) ↔ AST-measured module structure | per-integration | GATE FAIL → do not commit |
| 7 | **§4 counterfactual gate** (`scratchpad gate_s4.py`) | BG | claimed non-conduction / scope / integrity ↔ measured behavior under 10 violation injections | per-terminal | any SLIPPED → S-6 stop |
| 8 | **Edge-7 workflow reconciliation** (DE-0183, `twoder/audit/EDGE7_WORKFLOW_RECONCILIATION.md`, `test_dw_workflow_equivalence` 7/7) | DE | DW packaged `run_standard_workflow` path ↔ webui stepping path | one-off audit (resolved: ACCEPT — both → identical RESULT_PACKET at the same propose_complete gate) | mismatch → reconcile-or-accept (was ACCEPTED) |
| 9 | **execution-event-log accumulation** (`twoder/regression/test_execution_event_log.py`) | DV | RUNTIME_SUPERVISOR execution_events (primitives) ↔ derived PROCESS_TRACE / baseline strata | per-read (derive_process_trace) | derives from primitives; a self-reported summary is never promoted over the primitive events |

## Notes / gaps

- **"reconciliation layer v0.2"**: no implemented module by that name exists. The `grounding-layer-unified-v0.2.md`
  references 突合 only as *audit design* (GC-7 lint reconciliation target; Information-audit reconciliation of Task
  Evidence vs a requirement map) — design intent, not a running reconciler. Recorded as design-only.
- **The one true standing [DE] double-entry mechanism that is BUILT** is #4 (LAYER-3) and #8 (Edge-7, one-off).
  Everything else is either derivation-determinism (#1,#2,#9), transport-identity (#3), or a behavioral gate
  (#5,#6,#7). Most are **per-invocation/per-commit/per-terminal**, NOT standing daemons.
- **The §3 reconciler (git history ↔ PATCH_APPLICATION events) does not yet exist.** It would be the first
  *standing, state-based* [DE] reconciler and the first to gate a capability (energization) on its own liveness.
  It is designed (not built) in the §3 energization design doc.
