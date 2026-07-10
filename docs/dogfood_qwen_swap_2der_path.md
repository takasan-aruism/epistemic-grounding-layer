# Dogfood — Qwen swap problem through the 2DER path (vs Claude-alone baseline)

**as-of 2026-07-11.** Real-work dogfood: feed the live Qwen3.6↔Coder-Next swap problem through 2DER's own
ingest path and compare against the Claude-alone investigation already done. **Claim ceiling: "2DER pre-routing
changed the investigation process on THIS task."** No general-intelligence claim, no HBB/REC2. Read-only audit +
one reversible slice (`autonomy/ingest.py`). Prior Claude-alone trace is frozen as BASELINE, not injected.

## PHASE 1 — current 2DER dogfood path audit (actual executable only)

| stage | current component | file/function | status |
|---|---|---|---|
| INGEST (arbitrary Taka problem) | **NEW this slice** | `autonomy/ingest.ingest_problem` | **LIVE** |
| CURRENT REALITY / STATE | repo state builder | `autonomy/current_state.build_current_state` | **LIVE (repo)**; runtime/machine acquisition **NARROW** (investigator must read nvidia-smi/docker) |
| OBJECTIVE / CONSTRAINT / HISTORY | grounded retrieval | `egl.self_grounding.answer_question` over DE/REVIEW | **LIVE (retrieval)**; *persistent objective* store = **DESIGN-ONLY** (RRI) |
| TRIAGE | — | RRI spec only | **MISSING** (DESIGN-ONLY) |
| DETECTION (frame defect) | HBB arms | `run_hbb_*`/`run_afe_*` | **EXHIBIT-ONLY**, not wired to general input |
| RECONSTRUCTION / alt realization frame | scheduler exhibit | `run_scheduler_exhibit` | **MISSING for general input** (EXHIBIT-ONLY + **CLOSED NEGATIVE DE-0130**) |
| NEXT OPERATION | default route | `ingest.assemble_handoff` (route-to-Claude) / router SLICE-3 (repo-work only) | **LIVE-narrow** |
| CLAUDE INVESTIGATOR TASK envelope | **NEW this slice** | `autonomy/ingest.assemble_handoff` | **LIVE** |
| EXECUTION / RESULT | Claude senior (interactive) + DW reflux | this session / `egl.result_packet` | **LIVE-narrow**; *headless senior executor* = **MISSING** |
| STATE UPDATE / LOOP | DE ledger + state | `DESIGN_EVIDENCE_LEDGER` + `current_state` | **LIVE** |

**Honest net:** the *collect-context-and-hand-to-Claude* spine (INGEST → CURRENT-STATE → **relevant-history retrieval** → HANDOFF → STATE-UPDATE) is now LIVE. The *intelligent middle* (triage, detection, **reconstruction/alternative-frame**, headless execution) is MISSING/EXHIBIT-ONLY and is **not faked** in the handoff.

## PHASE 5 — Claude-alone (BASELINE) vs 2DER→Claude (DOGFOOD), on the Qwen swap task

| # | dimension | BASELINE (Claude-alone) | DOGFOOD (2DER→Claude handoff) |
|---|---|---|---|
| 1 | starting point | raw premise "3分" taken at face value | **grounded**: retrieval surfaced MEASURED ~174.5s/swap and **corrected the premise** (6–12 min per rework) |
| 2 | prior-history reuse | found DE-0086 by *manual grep* | auto-surfaced DE-0073/74/75 (measured latency, co-serve VRAM); **missed DE-0086 this run** (naive retrieval is phrasing-sensitive) |
| 3 | repeated-known-failure avoidance | re-discovered "sleep not viable" by grep | flagged co-serve IMPOSSIBLE up front; **did not flag the sleep-wake failure this run** → MIXED |
| 4 | blocker localization | **localized**: vLLM #39078 (fp8-kv sleep-wake bug) via investigation + WebSearch | **did NOT localize** — no detection/reconstruction; deferred to Claude |
| 5 | false leads | Triton `.odt` was a candidate red-herring; correctly dismissed as historical | n/a (no live investigation) |
| 6 | alternative realization paths | proposed (drop `--kv-cache-dtype fp8`; sleep-both; `reload_weights`) | **candidate_frames = MISSING (honest)** |
| 7 | unresolved-material retention | found the fp8-kv lever via WebSearch | **retained the ledger open_gap** "co-serve VRAM — fp8 KV variation not measured" (points at the same lever) |
| 8 | next-action specificity | specific + testable | generic ("route to Claude") |
| 9 | unnecessary Taka escalation | asked bare "試していい?" (Taka corrected this) | prescribes structured escalation **only** at the :8005-stop point |
| 10 | executable progress | produced a testable workaround | produced a **better-grounded starting point**, no fix itself |

## FINAL ANSWERS

**A. Claude Code はこれまで2DERを通さず直接problem-solvingしていたか — YES.** 今回の baseline がまさにそれ、かつ本 session の大半も Claude-alone workflow だった。

**B. current 2DER で general Taka problem input をどこまで処理できるか — 「文脈収集→Claude handoff」までは LIVE、「賢く frame を組み直す」中核は未所有.** LIVE: INGEST / CURRENT-STATE(repo) / RELEVANT-HISTORY(retrieval) / HANDOFF / STATE-UPDATE。MISSING/EXHIBIT-ONLY: TRIAGE / DETECTION / RECONSTRUCTION / next-realization-path / headless execution。

**C. 今回新しく接続したもの — `autonomy/ingest.py`**（general problem-ingest + investigator handoff）。既存 `build_current_state` + `self_grounding` retrieval を再利用し、TAKA→2DER→CLAUDE の最小 path を敷いた。新しい intelligence engine は作っていない。

**D. Qwen swap で両者はどう違ったか — 上表.** 要点: 2DER は premise を実測で訂正し、measured history / constraint / solution-relevant gap を**先出し**した。しかし blocker localization(#39078)と workaround は依然 Claude-alone の成果で、2DER retrieval はこの phrasing で DE-0086 を落とした。

**E. 2DER を通す価値は実仕事で観測されたか — MIXED.** grounding(前提訂正・measured history 先出し)は改善。problem-solving(localization/alternative frame)は未寄与(honestly MISSING)。retrieval は不安定(query phrasing 依存)。= 「starting point は良くなったが、解いたのは Claude」。

**F. 次回から Claude task を2DER経由へ強制する entrypoint — `autonomy/ingest.run(raw_input)` → handoff を investigator が `must_start_from` で消費.** 現状 advisory(runtime 強制でない)。強制するには (i) UI Home / task 起点を ingest に配線、(ii) Claude 運用規律として「raw prompt でなく handoff から開始」を既定化。UI の QUESTION/RESULT_LOG/TASK/CORRECTION taxonomy は最終形にしない — Home の本来の意味は「2DER に問題・発想・目的を渡す入口」。

## evidence status (unchanged)
scheduler CLOSED NEGATIVE · center-shift NOT CONFIRMED · AFE content WEAK/NEGATIVE · bridge CONFIRMED-narrow ·
Attention Center / same-object binding / structural re-centering / local Aruism regime **UNOWNED**. No negative
branch re-wrapped. self-improvement claim なし. C≠H.
