# MINIMUM HBB-EXHIBIT → EGL UNRESOLVED BRIDGE — spec v0.1

**One purpose:** hand intermediate material generated during HBB/exhibit processing to the existing live EGL
`answer_question` contract so an **answer candidate + unresolved material** are exposed to the user
simultaneously — **without changing the normal reasoning path.** Feasibility of wiring only.

**Explicitly NOT built (held UNOWNED):** Attention Center · same-object tension binding · Aruism local analysis
· structural re-centering. **Not revisited:** route-vs-repeat / center-shift branches. **No** HBB-30-solved /
REC2 / Attention-Center claim. C≠H.

## 1. Frozen bridge boundary (from the SMALL-WIRING audit; not re-searched)
| role | binding | evidence |
|---|---|---|
| SOURCE artifact | `experiments/scheduler_exhibit_candidates.json` → `records[].candidates` (persisted rebuild-output text) | verified: 40 HBB-30 records × 6 candidates = 240 texts; keys `{incident,seed,condition,n,n_distinct,candidates}` |
| SOURCE object type | `str` (a replacement-frame reconstruction) | `run_scheduler_exhibit.py:167` writes `candidates=[x["candidate"] …]` |
| SOURCE identity | `opaque_id = sha256(f"{incident}|{condition}|{seed}|{cand_idx}")[:14]` | mirrors the exhibit's own scheme, `run_scheduler_exhibit.py:171` |
| EGL TARGET fn | `egl/self_grounding.py:254 answer_question(question, records=…, system=…)` then `:296 validate_answer` | the ONLY boundary that emits `open_gaps` |
| EGL accepted contract | record dict `{record_id, source_class, ordinal, text}` (+ ignored extras); answer JSON keys `ANSWER_KEYS=[answer_claims, historical_claims, open_gaps, source_trace]` | `_records_block` reads those 4 keys; `validate_answer` enforces the 4 answer keys + source_trace |
| ADAPTER responsibility | **format + provenance-preserving wiring only** (text→record dict; run `answer_question`+`validate_answer`) | — |

## 2. Minimal adapter contract
**INPUT — existing intermediate material only** (no field is invented if the source lacks it):
| field | populated from | if absent |
|---|---|---|
| `material_id` | `opaque_id` (computed, matches exhibit scheme) | always available |
| `run_ref` | pinned artifact sha256 (§6) — the artifact has no run_id | use artifact hash, never fabricate a run_id |
| `incident_ref` | `record.incident` | available |
| `origin_stage` | constant `"rebuild_out"` (the frozen source boundary) | — |
| `raw_material` | `candidate` string, **byte-identical** | — |
| `source_ref` | `{artifact, incident, condition, seed, cand_idx}` | available |
| `parent_ref` | **OMITTED** — the compare-stage deltas are ephemeral/unpersisted; no true parent exists | never guessed |

**OUTPUT — EGL-ingestable record:** `{"record_id": material_id, "source_class": "HBB_EXHIBIT_INTERMEDIATE",
"ordinal": <stable index>, "text": raw_material, "provenance": source_ref}`. `source_class` is a **contextual,
non-authoritative** label ("generated intermediate, NOT an admitted claim"), consistent with EGL's contextual-
authority model (`self_grounding.py:9`).

**The adapter MUST NOT judge** correctness · tension · suspiciousness · premise validity · question validity ·
answer relevance · HBB-rubric match. No semantic adjudication. Format + provenance only.

## 3. EGL data-flow (honest reach; no bypass)
```
adapter records ──▶ answer_question(question, records, system=NEUTRAL) ──▶ answer JSON
                                                       │
                                   validate_answer (M1 source_trace / M2 placement / M3 format)
                                                       ▼
                         answer_claims  +  open_gaps  +  historical_claims  +  source_trace
```
- **REACHED by this slice:** `answer_claims`, `open_gaps` (+ `historical_claims`, `source_trace`) — via the
  live answer contract, **grounded** (validate_answer M1 requires every claim to cite a fed `record_id`).
- **NOT reached (honest scope):** `status`, `validation_mode`, `non_guarantees`. These come from the **curation
  admission path** (`gates.decide`→`apply_outcome`) and the **DW reflux** (`result_packet`), which require
  evidence/claim objects. This bridge **does not create Claims** and therefore neither touches nor bypasses
  `gates.decide`. Populating status/validation_mode is explicitly **out of the minimal slice**.
- **Forbidden:** appending raw free-text directly to `open_gaps`. `open_gaps` is produced only by the
  `answer_question` LLM under `validate_answer` grounding — the adapter never writes it.
- The `system=` override is **neutral**: "you are given generated intermediate RECORDS; return answer_claims
  (the answer the material supports) and open_gaps (unresolved considerations present in the material); use ONLY
  provided records; cite record_ids in source_trace." **No** HBB rubric vocabulary (no DETECTION/RECONSTRUCTION/
  "6x-correct"/REC2), **no** correctness scoring, **no** outside knowledge.

## 4. Frozen authority invariants (the bridge holds NO authority)
1. generated material ≠ validated claim
2. retained material ≠ accepted evidence
3. open gap ≠ false premise
4. UNRESOLVED ≠ answer rejection
5. REPORTED / DECLARED semantics unchanged
6. SUPERSESSION semantics unchanged
7. answer authority unchanged
8. user remains final authority

Held structurally: the bridge calls only `answer_question`+`validate_answer` (answer layer, **no DB write**,
`gates.py:2-3`); it never calls `apply_outcome`/`gates.decide`; `source_class=HBB_EXHIBIT_INTERMEDIATE` marks
non-admission.

## 5. Normal-path isolation
The bridge is an **explicit adapter invoked from the HBB/exhibit side only.** No classifier, no heuristic, no
always-on observer is added to the ordinary EGL question path.
```
normal path:  existing EGL question flow            → UNCHANGED (byte-for-byte)
bridge path:  HBB/exhibit material → adapter → answer_question(records=…)   (separate, offline)
```
Ordinary math/factual/coding questions never enter the bridge, so no degradation. Retention (A) ≠ surfacing (C):
the adapter only surfaces when explicitly run on fed material.

## 6. HBB-30 offline replay fixture (snapshot-pinned)
- INPUT: the frozen `scheduler_exhibit_candidates.json` HBB-30 subset (40 records / 240 candidate texts).
- QUESTION context: the HBB-30 `t0_stuck_frame` (408 chars) from `hbb_sealed_t0.json` — neutral, **not**
  answer-aware, **no rubric**.
- Pins (DE-0132 lesson — no live-ledger, no self-reference; the corpus is ONLY exhibit material, never EGL's
  own ledgers): `scheduler_exhibit_candidates.json` = `b7c98296a3249ec86a73d9341a1975e863dfa800ec735b5d8672d4a4d032c74b`;
  HBB-30 canonical subset = `9e1ca25b1f060109b9b340b008056e99f87822cc6015a1334487737b9a4f49d2`;
  `t0_stuck_frame` = `bc09d36ddfbcdb99fdc38adfa61477e33a7a489b88d64c3c4dc5c5f466db7ea0`.
- retrieval: `answer_question(k=<n fed records>)` so **no candidate is silently dropped** (log if truncated —
  PROCESS-01: no silent caps).
- GOAL: bridge → answer contract → `answer_claims + open_gaps` → dual render. **Feasibility only.** No
  HBB-30-solved, no REC2-as-primary.

## 7. User-facing dual render (minimal)
Reuse the existing surface: print/return the answer JSON with **ANSWER** and **OPEN / UNRESOLVED** as two
separated blocks (raw `answer_claims` / `open_gaps`, or `answer_evidence.render_compact` if wired). **Do NOT
re-integrate `open_gaps` back into a single clean answer paragraph** — the whole point is to not extinguish the
unresolved material at integration. Illustrative form (wording NOT hard-coded):
```
ANSWER (candidate):
  - <answer_claims[i].text>   [source: <record_ids>]
OPEN / UNRESOLVED:
  - <open_gaps[j]>
(あなたが最終判断者です / user is the final authority)
```

## 8–10
Test plan, prereg, seal, binding, offline-replay contract are companion files (v0.1). Final gate after
independent construct audit ∈ {BRIDGE DESIGN VALID / BRIDGE DESIGN INVALID / AUDIT REQUIRED / UNKNOWN}.
Attention Center / same-object binding / Aruism remain UNOWNED.
