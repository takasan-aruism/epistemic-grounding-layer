# MINIMUM HBB-EXHIBIT → EGL UNRESOLVED BRIDGE — spec v0.2 (supersedes v0.1)

**v0.1 was AUDIT REQUIRED** (not INVALID): boundary/invariants correct, but two claims were not code-backed
(`retrieve()`'s `score>0` filter can silently drop records; `validate_answer` does NOT ground `open_gaps`), plus
three implementation hazards (`load_corpus()` self-reference default, unpassed `superseded=`, unassessed ~48K
token call). v0.2 fixes all five. Everything else unchanged.

**One purpose:** hand intermediate material generated during HBB/exhibit processing to the existing live EGL
`answer_question` contract so an **answer candidate + unresolved material** are exposed to the user
simultaneously — **without changing the normal reasoning path.** Wiring feasibility only.

**NOT built (UNOWNED):** Attention Center · same-object tension binding · Aruism local analysis · structural
re-centering. **Not revisited:** route-vs-repeat / center-shift. **No** HBB-30-solved / REC2 claim. C≠H.

## 1. Frozen bridge boundary (from the SMALL-WIRING audit; not re-searched)
| role | binding | evidence |
|---|---|---|
| SOURCE artifact | `experiments/scheduler_exhibit_candidates.json` → `records[].candidates` | 40 HBB-30 records × 6 = 240 texts; keys `{incident,seed,condition,n,n_distinct,candidates}` |
| SOURCE object type | `str` (a replacement-frame reconstruction) | `run_scheduler_exhibit.py:167` |
| SOURCE identity | `opaque_id = sha256(f"{incident}|{condition}|{seed}|{cand_idx}")[:14]` | `run_scheduler_exhibit.py:171` |
| EGL TARGET fn | `egl/self_grounding.py:254 answer_question(question, records, system, k, force_include)` + `:296 validate_answer` | only boundary emitting `open_gaps` |
| EGL accepted contract | record dict `{record_id, source_class, ordinal, text}`; answer keys `ANSWER_KEYS` | `_records_block:244-250`; `validate_answer:308` |
| ADAPTER responsibility | format + provenance-preserving wiring only | — |

## 2. Minimal adapter contract
INPUT — existing intermediate material only (no invented field):
`material_id`=opaque_id · `run_ref`=pinned artifact sha256 (no fabricated run_id) · `incident_ref`=record.incident
· `origin_stage`=`"rebuild_out"` · `raw_material`=candidate (byte-identical) · `source_ref`=
`{artifact,incident,condition,seed,cand_idx}` · `parent_ref`=**OMITTED** (compare-stage deltas ephemeral).

OUTPUT — EGL-ingestable record: `{"record_id": material_id, "source_class": "HBB_EXHIBIT_INTERMEDIATE",
"ordinal": <stable idx>, "text": raw_material, "provenance": source_ref}`. `source_class` is a **contextual,
non-authoritative** label ("generated intermediate, NOT an admitted claim").

The adapter **MUST NOT judge** correctness/tension/suspiciousness/premise/question-validity/relevance/rubric.
Format + provenance only.

## 3. EGL data-flow (honest reach; no bypass) — with v0.2 hardening
```
adapter records ─▶ answer_question(question, records, system=NEUTRAL,
                                    k=len(records), force_include=ALL record_ids) ─▶ (answer, retrieved_ids, raw)
                                                     │
                         assert set(retrieved_ids)==set(all record_ids)   [FIX-1 no-silent-drop, logged]
                                                     ▼
                         validate_answer(answer, {record_ids})  (M1 grounds answer_claims/source_trace)
                                                     ▼
                         answer_claims + open_gaps + historical_claims + source_trace
```
- **REACHED:** `answer_claims`, `open_gaps` (+ historical_claims, source_trace).
  - `answer_claims`/`source_trace` **are** grounded (validate_answer M1 requires each claim to cite a fed
    `record_id`, `self_grounding.py:322-329`).
  - **`open_gaps` is NOT mechanically grounded** — `validate_answer` only counts it (`n_open_gaps`); it is
    answerer-produced free text. [FIX-3: v0.1's "open_gaps grounded by M1" claim was FALSE and is withdrawn.]
    If open_gaps grounding is ever required, it is a **separate future construct**, not this slice.
- **NOT reached:** `status`, `validation_mode`, `non_guarantees` (curation `apply_outcome` / DW `result_packet`
  paths; need evidence/claim objects). The bridge creates **no Claim** and calls neither `apply_outcome` nor
  `gates.decide`.
- **Forbidden:** hand-writing `open_gaps`. Only `answer_question` produces it.
- **[FIX-1] no silent drop:** `retrieve()` appends only `score>0` records and `k` does NOT override that filter
  (`self_grounding.py:158-173`). v0.2 uses the existing `force_include=<all record_ids>` (`:262-267`) to append
  every fed record regardless of score, **and** asserts `set(retrieved_ids)==set(all_ids)`; any shortfall is
  **logged and fails the run** (PROCESS-01: no silent cap). No stopword-coincidence dependence.
- **[FIX-2] no self-reference default:** the bridge asserts `records` is a **non-empty list** before the call
  and **never** passes `records=None` (which would default to `load_corpus()` = EGL's own ledgers, DE-0132).
- **[FIX-4] no supersession heuristic bleed:** the bridge passes `superseded={}` explicitly so
  `detect_supersession` does not scan/inject tags over the 240 HBB texts.
- The `system=` override is **neutral**: "given generated intermediate RECORDS, return answer_claims (the answer
  the material supports) and open_gaps (unresolved considerations present); use ONLY provided records; cite
  record_ids in source_trace; JSON with ANSWER_KEYS." **No** rubric vocabulary, **no** correctness scoring,
  **no** outside knowledge.

## 4. Frozen authority invariants (bridge holds NO authority)
generated ≠ validated · retained ≠ evidence · open_gap ≠ false premise · UNRESOLVED ≠ rejection ·
REPORTED/DECLARED unchanged · SUPERSESSION unchanged · answer authority unchanged · user final authority.
Held structurally: bridge calls only `answer_question`+`validate_answer` (answer layer, **no SoR write** —
verified: no `append_event`/sqlite/write in `self_grounding.py`, `gates.py:2-3`); never `apply_outcome`/
`gates.decide`; `source_class=HBB_EXHIBIT_INTERMEDIATE` marks non-admission.

## 5. Normal-path isolation
Explicit adapter invoked from the HBB/exhibit side only. No classifier/heuristic/always-on observer on the
ordinary EGL question path (T8). `normal path: existing EGL flow → UNCHANGED`; `bridge path: material → adapter
→ answer_question`. Retention (A) ≠ surfacing (C).

## 6. HBB-30 offline replay fixture (snapshot-pinned)
- INPUT: frozen `scheduler_exhibit_candidates.json` HBB-30 subset (40 records / 240 candidates).
- QUESTION context: HBB-30 `t0_stuck_frame` (408 chars) — neutral, not answer-aware, no rubric.
- Pins (DE-0132; corpus = ONLY exhibit material, never EGL ledgers): candidates
  `b7c98296a3249ec86a73d9341a1975e863dfa800ec735b5d8672d4a4d032c74b`; subset
  `9e1ca25b1f060109b9b340b008056e99f87822cc6015a1334487737b9a4f49d2`; frame
  `bc09d36ddfbcdb99fdc38adfa61477e33a7a489b88d64c3c4dc5c5f466db7ea0`.
- **[FIX-5] call sizing:** all 240 candidates ≈ 191,942 chars ≈ ~48K input tokens. Nominal = **1 call** IF the
  Qwen model context ≥ ~64K tokens (verify at impl). ELSE **per-condition batching** (R0/RS/RS_pool/RS_flat = 60
  candidates ≈ ~12K tokens each → ≤4 calls), each with its own `force_include`+coverage assert; **the batching,
  if used, is logged** (not silent). Context-window sufficiency is a verify-at-impl item.
- GOAL: bridge → answer contract → `answer_claims + open_gaps` → dual render. **Feasibility only.**

## 7. User-facing dual render (minimal)
Print/return the answer JSON with **ANSWER** and **OPEN / UNRESOLVED** as two separated blocks (raw
`answer_claims`/`open_gaps`, or `answer_evidence.render_compact` if wired). **Do NOT** re-integrate `open_gaps`
into a single clean answer paragraph. Wording NOT hard-coded.

## 8–10
Companion files (v0.2): binding, offline-replay contract, test plan, prereg, seal. Final gate after independent
re-audit ∈ {BRIDGE DESIGN VALID / INVALID / AUDIT REQUIRED / UNKNOWN}. Attention Center / same-object binding /
Aruism remain UNOWNED.
