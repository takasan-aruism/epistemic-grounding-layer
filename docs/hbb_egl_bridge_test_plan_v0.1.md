# HBB-EGL BRIDGE — test plan v0.1

Companion to `hbb_egl_bridge_spec_v0.1.md`. All tests are gated behind the independent construct audit + user
go; **none are implemented or run this round.** Tests T1–T4, T8–T10 are mechanical/hermetic (no LLM). T5–T7
require one existing-mechanism `answer_question` call on the pinned offline fixture.

| id | assertion | kind | method (design) | pass condition |
|---|---|---|---|---|
| **T1** | adapter preserves source material content identity | mechanical | for every candidate, `record.text == candidate` (byte/char identical) | 240/240 exact match |
| **T2** | source/run/origin refs preserved where available | mechanical | assert `record.provenance` has incident/condition/seed/cand_idx; `run_ref`==artifact sha256; `parent_ref` ABSENT | all present-fields correct; parent_ref not fabricated |
| **T3** | no bridge-side semantic verdict | mechanical | scan adapter output keys ∩ {correctness, tension, suspicious, premise, validity, relevance, rubric, score, DETECTION, RECONSTRUCTION} | empty intersection |
| **T4** | EGL admission/answer path actually used (no bypass) | mechanical | assert the code path calls `answer_question` + `validate_answer`; assert it does NOT write `open_gaps` directly and does NOT call `apply_outcome`/`gates.decide` | both hold |
| **T5** | unresolved material can reach `open_gaps` | LLM (1 call) | run bridge on pinned fixture; inspect `answer_dict.open_gaps` | `open_gaps` non-empty and each item traceable to fed records |
| **T6** | `answer_claims` coexists with `open_gaps` | LLM (same call) | inspect both keys | both non-empty simultaneously |
| **T7** | `open_gaps` does not auto-reject the answer | mechanical (on the T5/T6 output) | assert `answer_claims` still present when `open_gaps` non-empty; no exclusivity | answer retained |
| **T8** | ordinary EGL path byte/behaviour unchanged | mechanical | diff the normal EGL question flow with/without the bridge module imported; run existing `test_self_grounding` / `test_sor` | identical outputs; existing tests green |
| **T9** | no rubric vocabulary in bridge | mechanical | grep the adapter + system prompt for rubric tokens | zero hits |
| **T10** | no self-reference / live-ledger contamination | mechanical | assert corpus = only adapted HBB-30 records; assert input hashes == pinned (§6); assert no EGL ledger read | all hold |

**Snapshot pin (DE-0132):** T5–T7 read only the hash-pinned fixture (`b7c98296…` / subset `9e1ca25b…` /
frame `bc09d36d…`). A verify re-run MUST NOT overwrite the committed replay output; write to a distinct path.

**Anti-goals asserted as tests:** T3 (no verdict), T4 (no bypass), T9 (no rubric), T10 (no self-reference) —
these are the invalidators; any failure ⇒ BRIDGE DESIGN INVALID. T8 protects the normal path.
