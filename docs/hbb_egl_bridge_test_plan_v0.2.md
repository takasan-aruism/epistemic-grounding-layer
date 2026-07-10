# HBB-EGL BRIDGE — test plan v0.2 (supersedes v0.1)

Companion to `hbb_egl_bridge_spec_v0.2.md`. Gated behind the independent re-audit + user go; **none implemented
or run this round.** T1–T4b, T7–T11 are mechanical/hermetic. T5–T6 require the offline `answer_question` call(s)
on the pinned fixture. Changes vs v0.1: T4 split into no-bypass + coverage (FIX-1); T5 grounding claim removed
(FIX-3); T11 self-reference-guard added (FIX-2); T12 supersession-guard (FIX-4); call-sizing note (FIX-5).

| id | assertion | kind | method (design) | pass condition |
|---|---|---|---|---|
| **T1** | adapter preserves material content identity | mech | `record.text == candidate` for all 240 | 240/240 exact |
| **T2** | provenance refs preserved where available | mech | provenance has incident/condition/seed/cand_idx; run_ref==artifact sha256; parent_ref ABSENT | all present-fields correct; parent_ref not fabricated |
| **T3** | no bridge-side semantic verdict | mech | adapter output keys ∩ {correctness,tension,suspicious,premise,validity,relevance,rubric,score,DETECTION,RECONSTRUCTION} | empty intersection |
| **T4a** | no bypass | mech | code path calls `answer_question`+`validate_answer`; does NOT write `open_gaps` directly; does NOT call `apply_outcome`/`gates.decide` | all hold |
| **T4b** | **FIX-1** all records provably fed | mech | force_include=[all ids]; assert `set(retrieved_ids)==set(all_ids)`; log any drop | 240/240 retrieved; 0 unlogged drops |
| **T5** | unresolved material reaches `open_gaps` | LLM | run bridge on pinned fixture; inspect `open_gaps` | `open_gaps` **non-empty** (grounding NOT asserted — FIX-3) |
| **T6** | `answer_claims` coexists with `open_gaps` | LLM | inspect both keys | both non-empty simultaneously |
| **T7** | `open_gaps` does not auto-reject the answer | mech | on T5/T6 output: answer_claims present while open_gaps non-empty | answer retained (no exclusivity) |
| **T8** | ordinary EGL path byte/behaviour unchanged | mech | diff normal flow with/without bridge import; run `test_self_grounding`/`test_sor` | identical; existing tests green |
| **T9** | no rubric vocabulary in bridge | mech | grep adapter + system prompt for rubric tokens | zero hits |
| **T10** | no live-ledger contamination (input) | mech | corpus = only adapted HBB-30 records; input hashes == pinned (§6) | all hold |
| **T11** | **FIX-2** no self-reference default | mech | assert `records` is a non-empty list; assert `records is None` path unreachable (load_corpus never called) | both hold |
| **T12** | **FIX-4** no supersession heuristic bleed | mech | assert `superseded={}` passed; `detect_supersession` not invoked on HBB text | holds |

**Snapshot pin (DE-0132):** T5/T6 read only the hash-pinned fixture; a verify re-run MUST NOT overwrite the
committed output (distinct path).

**FIX-5 sizing (feasibility, not a pass/fail test):** record the input token estimate; if the single call
exceeds context, the per-condition batched fallback (≤4 calls) MUST be logged.

**Invalidators (any failure ⇒ BRIDGE DESIGN INVALID):** T3 (verdict), T4a (bypass), T4b (silent drop), T9
(rubric), T10/T11 (self-reference), T12 (supersession bleed). T8 protects the normal path.
