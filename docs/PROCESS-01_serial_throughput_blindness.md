# PROCESS-01 / SERIAL_THROUGHPUT_BLINDNESS — 2DER process incident (non-validity)

**class: PROCESS (2DER operation), NON-VALIDITY.** The completed frozen primary experiment is **valid** and
**not touched/rerun** (the serial-vs-parallel harness affects wall-clock only, not the candidates/scores).
Ledger: DE-0126. Do NOT auto-apply any process change (DD-ARCH-4).

## 0. The program-level question, audited FIRST
**"Why did the research-operation system fail to notice its own execution anomaly until Taka changed the
observation frame?"**

Honest answer (5 grounded causes):
1. **The operating frame was validity-monocular.** The whole reconstruction track ran a mature, adversarial,
   *independent* VALIDITY-observation apparatus — 6 audit rounds, spec-fidelity, target-leakage, claim-scope,
   exhaustive-completion. It ran **zero** process-observation. `TASK_VALIDITY_MONITORING` was maximal;
   `PROCESS_EFFICIENCY_MONITORING` was null. The anomaly lived entirely in the unobserved dimension.
2. **GPU-busy was conflated with throughput-efficient.** ~96% util on both RTX 5090s read as "productive."
   With TP=2, each *single serial* request saturates both GPUs, so util is a **false positive** for batch
   efficiency. No req/s or tok/s was ever computed — the actual throughput metric was never derived.
3. **No elapsed-time expectation baseline.** I never estimated "at concurrency C this should take ~X min" to
   compare against actual, so there was no anomaly to detect — "long runtime = big workload (3,960 gens)" was
   accepted uncritically. Damningly, I *parallelized the Qwen scoring* (`ThreadPoolExecutor(max_workers=8)`) but
   left **generation serial** (`for k in range(N)` of synchronous `qgen()`), and did not notice the asymmetry —
   because I was not watching throughput at all.
4. **The one relevant viewpoint exists but is not wired to fire.** `H-OPS-01` ("check dependency; parallelize/
   batch repeated independent work", HUMAN_TAUGHT, taught 2026-07-07 from the GPU-swap/batching discussion) sits
   in `optimization_heuristics.jsonl` with **`transfer_evidence: []`** — it has *never* autonomously transferred.
   It is consulted only by the Process Optimizer role, which is (a) **unimplemented** (PLAN stage), (b) **scoped
   to DW/codegen-loop primitives** (`run_sor/events.jsonl`), not bespoke experiment harnesses, and (c) **post-hoc
   cost analysis**, not a live monitor. On `run_recon_exhibit.py` it was structurally out of the loop.
5. **Even the implementation audit was validity-chartered.** The independent impl auditor *saw* the serial
   `for k in range(N)` structure but was tasked ONLY with code-vs-spec faithfulness. The serial structure was
   literally in view and unflagged — because efficiency was in **no** charter. **The observation frame is set by
   the charter, and every charter in this track was validity.**

**Root, stated plainly:** the system did not fail to *see* the code (it was audited); it failed to run any
channel whose *charter* was throughput, it mistook GPU-busy for efficient, and it formed no runtime expectation.
Taka "changing the observation frame" = supplying the missing process-efficiency lens. **The system cannot
self-supply a lens no active channel carries.** This is a missing `PROCESS_OBSERVATION` channel — exactly as
Taka framed — not a validity flaw.

**Connection to the EGL antipattern (important):** this is the *same* "upstream self-report → downstream trust"
failure EGL exists to kill, at the OBSERVATION layer. I trusted the **GPU-util summary** ("96% ⇒ efficient")
instead of **deriving the real metric (req/s, tok/s) from request primitives** — precisely what the Process
Optimizer plan §0 forbids ("building on the summary JSON re-implements the antipattern; must read primitives,
derive its own trace"). The design *knew* this lesson at the codegen-loop layer; I violated it at the
experiment-harness layer.

## A. Incident (ledger form)
- **T0 (frame at the time):** primary frozen run executing (3,960 generations). GPUs ~96%. Long runtime accepted
  as "expected workload volume." Active monitoring = validity only.
- **Missed anomaly:** effective generation request-concurrency ≈ **1** (serial `qgen` in `for k in range(N)`,
  serial incident/seed/condition loops); high GPU util did NOT imply batch throughput; no req/s|tok/s derived.
- **Taka move:** independently questioned the speed and asked about **effective batch size** — changing the
  observation frame from validity to throughput.
- **Breakthrough:** `TASK_VALIDITY_MONITORING != PROCESS_EFFICIENCY_MONITORING`. GPU-utilization is not a
  throughput proxy under TP>1 serial load; throughput must be **derived from request primitives**, and compared
  to a **runtime expectation**.
- **Structural lesson:** a validity-complete operating frame can be **process-blind**; the missing piece is a
  live, cross-cutting `PROCESS_OBSERVATION` channel with its own charter that fires **without a human prompt**.

## B. Map against current 2DER design
- **PROCESS_TRACE (Process Optimizer plan §2):** derived from **DW codegen-loop primitives** (model_switches,
  phase timeline, run_seconds). Does **not** observe arbitrary harnesses (`run_recon_exhibit.py` writes no DW
  SoR). Right *idea* (derive-from-primitives), wrong *scope* for this incident.
- **optimization_triggers (§4):** deterministic, versioned, **but** the metrics are dominant-cost-share /
  component-recurrence over a *completed* trace — **post-hoc cost**, not live throughput/elapsed-anomaly. The
  specific detector (high util + low req/s) is **not specified anywhere**.
- **H-OPS-01 (heuristics ledger):** the exact viewpoint that would flag this — but `transfer_evidence: []`
  (never fired autonomously) and reachable only via the unimplemented, DW-scoped Optimizer. **This incident is a
  negative step-8 transfer measurement: H-OPS-01 did not transfer to an unrelated operational workload.**
- **TRIAGE / ELABORATENESS_ANOMALY (RRI):** RRI-layer concepts (research-requirement triage / anomalous-effort
  detection). *Functional* map only — I could not locate exact definitions in the repo, so I do not quote them.
  Functionally, an "elaborateness/effort anomaly" is the *research-need* analog of what a process channel needs;
  but RRI observes research effort, not client-side request throughput. Neither is a live execution monitor.

## C. Is the design sufficient-but-unimplemented, or incomplete?  **BOTH — precisely:**
- **Partly specified**: the right *viewpoint* (H-OPS-01), a derive-from-primitives *trace* (PROCESS_TRACE), and
  deterministic *triggers* exist in design.
- **Incomplete for this incident** in three ways: (1) **unimplemented** (Optimizer = PLAN-stage, nothing runs);
  (2) **wrong layer** (PROCESS_TRACE is DW/codegen-loop-scoped, blind to bespoke harnesses); (3) **wrong shape /
  missing metric** (post-hoc cost, no *live* elapsed-vs-expectation or busy-but-low-throughput rule; no req/s,
  tok/s, effective-concurrency, or GPU-util-vs-batching signal anywhere).
- **Verdict:** the design has the correct *heuristic* but **no active, cross-cutting, live PROCESS_OBSERVATION
  channel** to carry it to general runs. That channel is genuinely **missing from the design**, not merely
  unbuilt.

## D. Minimum mechanism to autonomously flag "high GPU util + unexpectedly low req/s or tok/s"
Thin, reusable, deterministic — NOT the full Optimizer:
1. **`process_probe`** (a small wrapper any batch client-run imports): per-request primitives `{t_start, t_end,
   latency, prompt_tokens, output_tokens}` to an append-only process SoR; a background sampler for **GPU util
   (nvidia-smi)** + **in-flight request count**; derived **req/s, output tok/s, effective client concurrency**.
   (Derive-from-primitives, mirroring EGL discipline — no trust of the util summary.)
2. **Deterministic anomaly rule** (versioned, in code not prompt — like `optimization_triggers`): fire a
   `PROCESS_ANOMALY` when **(GPU_util > 80% AND effective_concurrency ≈ 1)** OR **(actual tok/s < floor)** OR
   **(actual wall-clock ≫ expected)**, where `expected` = `n_requests / throughput(concurrency)` from the
   benchmark table (F). The flag **prints autonomously** ("busy-but-serial: util high, req-concurrency≈1 → likely
   under-batched") and emits candidate = **H-OPS-01** (parallelize/batch), *routed, not auto-applied* (DD-ARCH-4).
3. **This finally gives H-OPS-01 a live firing site.** If the flag changes the decision path on the next
   workload without a human prompt, that is the first real `transfer_evidence` (step-8 educability measurement).

## E. Frozen experiment: untouched
The completed primary run is NOT modified or rerun. Serial vs parallel changes wall-clock only; candidates and
Qwen scores are identical either way. The exhibit result stands on its own track.

## F. Benchmark plan (before any operationalization / speed benchmark)
1. Build `process_probe` (D-1): log per-request latency, prompt/output token counts, req/s, output tok/s, active
   request count, client concurrency.
2. **Benchmark client concurrency {1, 8, 16, 32, 64}** against vLLM effective throughput (tok/s and req/s) on a
   fixed prompt-mix → the `throughput(concurrency)` table + the `floor` used by D-2.
3. Only after (1)+(2): choose an operational concurrency and wire D-2's live flag.
**Not run now; proposal only** (Taka gate; and F is explicitly "before any operational speed benchmark").
