# Temporal Provenance & Forecast — Decomposition v1 (§11 deliverable)

> The ONE decomposition deliverable for ITEM-2DER-TEMPORAL-PROVENANCE-DECOMPOSITION. Per acceptance: timestamp
> inventory + field diff + retrofit-vs-go-forward split + completion-definition v1 + velocity formula + refs +
> UNKNOWN-VARIANCE rule. NO child ITEM ids issued, NO code, NO retrofit, NO DB change. Parent spec = ART-efd1a6dcf4.
> Self-audit is NON-INDEPENDENT (single Claude context). Child-id issuance requires Taka approval.

## 1. Timestamp inventory (grounded — actual field inspection, not assumed)

| Store | rows | timestamp fields present | filled | timezone |
|---|---|---|---|---|
| **DE ledger** `egl/DESIGN_EVIDENCE_LEDGER.jsonl` | 272 | **NONE** (no recorded_at at all) | — | — |
| **CHANGE_LOG** `twoder/audit/CHANGE_LOG.jsonl` | 161 | recorded_at; before_commit; after_commit | recorded_at 117/161, after_commit 68/161 | naive |
| **ROADMAP_REGISTRY** | 196 | registered_at | 196/196 | naive |
| **ARTIFACT_REGISTRY** | 4447 | registered_at, last_verified_at, file_mtime | all | naive (file_mtime=epoch) |
| **REVIEW_LEDGER (JREV)** | 7 | date | 7/7 | naive |
| **git history** (all 5 repos) | — | commit author/committer time | all | **+09:00 (real, tz-aware)** |

### 1.1 The load-bearing finding
- **git commit time is the ONLY machine-generated, timezone-aware clock in the system.** Everything else is naive.
- **The `ts` values passed into set_status / register_item / admit_design_evidence / record_change are SELF-ASSIGNED by Claude** (e.g. "2026-07-14T12:10:00" typed by the LLM), NOT read from a wall clock. This is exactly the §3.1/§3.2 hazard: an LLM-authored timestamp is an impression, not a measurement. **Any velocity computed from these is measuring typed numbers, not elapsed time.**
- Therefore the real temporal ground truth we already hold is: **git commit timestamps** (per commit, tz-aware) + **file_mtime** (epoch, per artifact). These are the only trustworthy sources for retrospective timing.

## 2. Field diff (existing vs §4 required schema)

| §4 required | Present today | Gap |
|---|---|---|
| recorded_at on every important record | ROADMAP ✓, CHG partial, ART ✓, JREV ✓, **DE ✗** | DE has none; CHG 44 nulls |
| timezone on every timestamp | **none** (all naive); git has +09:00 | add tz; adopt git as canonical clock |
| task started_at / completed_at | ROADMAP has per-status-row registered_at (derivable IN_PROGRESS→DONE) but self-typed | need machine started/completed (git-derived) |
| wall_clock_seconds recomputable | not stored; derivable from two ROADMAP rows (but self-typed) or two commits (real) | compute from git, not typed ts |
| active_work / tool_wait / human_wait separation | **none anywhere** | net-new; not reconstructable from history |
| event id / reference record binding | partial (CHG→DE→ART chain exists) | formalize a temporal_event referencing the source record id |

## 3. Retrofit scope vs go-forward-only

**Retrofit-feasible (from real sources, marked INFERRED not MEASURED):**
- CHG / DE / ITEM completion times → back-attach the git commit timestamp of the commit that recorded them (via after_commit hash → `git show -s --format=%cI`). Real clock, but a proxy for "when the record was authored" → evidence class INFERRED.
- Artifact creation → file_mtime (already present).

**Go-forward-only (never captured; do NOT fabricate for the past):**
- active_work / tool_wait / human_wait split — no historical signal exists → capture from now on only.
- per-task started_at at the moment work truly began (vs when the status row was written).
- human approval request/grant wall-clock (only some INTV/authority events exist).

**Rule:** past records get a `timing_provenance: "git-inferred"` marker + INFERRED class; new records get machine-captured `recorded_at` + `timezone` + the wait split. Never retrofit a MEASURED-class number onto a record that lacks a real measurement.

## 4. Completion Definition v1 (candidate, §7/§8)

```
completion_definition_id: CDEF-2DER-v1
version: 1
created_at: <git commit ts at registration>
approved_by: <Taka — pending>
hash: sha256(canonical JSON of required_flag_ids + rule)
required_flag_ids:                      # each flag binds to an acceptance artifact + JREV verdict
  - FLAG-PHASE10-AUDIT-ENVELOPE   -> Tier-0 11 gates DONE + parity sweep artifact (DE-0251..0261)
  - FLAG-PHASE10-TIER1-CORE       -> Tier-1 deterministic items DONE (DE-0262..0273)
  - FLAG-ECONOMY-OPERATOR         -> ECONOMY-OPERATOR DONE (after temporal)
  - FLAG-TEMPORAL-FOUNDATION      -> temporal child units DONE + AC-TIME/EST/FLAG/FORECAST pass
  - FLAG-LIVE-BENCHMARK           -> VLLM-RUNTIME-PROFILER + benchmarks run, raw-artifact-backed (MEASURED)
  - FLAG-MODEL-ROUTING-READY      -> MODEL_ROUTING_READY chain holds (real provenance, not asserted)
  - FLAG-E2E-ACCEPTANCE           -> END-TO-END-ACCEPTANCE-HARNESS green (AC-01..14 + AC-BENCH/FAIL/KP/WEIGHT/ECON/HUMAN)
rule: a flag is SET only when its bound acceptance artifact exists AND (for CLASS-N/H) a JREV verdict references it.
      Flag removal/relaxation requires CHG + DE + JREV (§7). Set membership is version-hashed (AC-FLAG-02/03).
```
This is a **candidate** — the exact flag set is Taka's to approve; the mechanism (version + hash + binding) is fixed.

## 5. Velocity formula + reference records (§5/§6)

**Source of truth = git (the only real clock). Never self-typed ts.**
```
per_item_duration(item) =
    commit_time(DONE_commit(item)) - commit_time(first_commit(item))          # both from `git show -s --format=%cI`
    reference_records: [ITEM id, CHG.after_commit hash(es), DE id]            # AC-EST-01: cite formula + record ids
```
Aggregate, grouped by (domain, change_class, task_type):
`sample_count, median, p50/p80/p95, min/max, active_work/wall_clock ratio (go-forward), reimpl_count, audit_rework_count, human_intervention_count, estimation_error`.

**Forecast output contract (§6): primary answer = remaining work + expected sessions, NOT a date.**
`{remaining_items, remaining_acceptance_tests, critical_path_items, parallelizable_items, required_JREV_count, expected_sessions, unknown_variance_items, p50/p80/p95 throughput from history}`. Calendar dates ONLY as an explicit "N sessions/week" conditional conversion (AC-EST-03).

**Honest caveat baked into the formula:** within a single session, IN_PROGRESS→DONE elapsed is dominated by user-paced gaps (approval waits) + Claude think-time, so **per-SESSION throughput (items DONE per session) and per-task tool-time** are the meaningful units — not calendar velocity. Today's observable: this session produced ~23 PHASE-10 DONE items across DE-0249..0273, but that is ONE session's throughput, not a rate (n=1 session → see §6 UNKNOWN-VARIANCE).

## 6. UNKNOWN-VARIANCE rule (§6)

An item is emitted as **UNKNOWN-VARIANCE (no fabricated number)** when ANY holds:
- change_class == CLASS-N (novel; no reference implementation), OR
- no prior DONE item shares its (domain, task_type) → no empirical distribution, OR
- sample_count for its group < 3, OR
- the only available timing is self-typed (not git-derived) → INFERRED, cannot ground a p-estimate.
Session-count estimates likewise: with n=1 observed session, expected_sessions is a RANGE flagged UNKNOWN-VARIANCE, not a point.

## 7. Recommended child units (§12) — mapped to build-vs-reuse (NOT issued)

| unit | new / reuse | note |
|---|---|---|
| TEMPORAL-EVENT-SCHEMA | new | recorded_at + timezone + source_record_id; git as canonical clock |
| TIME-BINDING-VALIDATOR | new | AC-TIME-01/02; rejects a record lacking recorded_at+timezone |
| ACTIVE-WORK-AND-WAIT-LEDGER | new (go-forward) | AC-TIME-03; active/tool_wait/human_wait; append-only (benchmark-ledger pattern) |
| HISTORICAL-VELOCITY-CALCULATOR | new | sources = git + ROADMAP + DE + CHG; reuses artifact_registry for refs |
| ESTIMATION-BASIS-BINDING | new | AC-EST-01; every number cites formula + record ids |
| UNKNOWN-VARIANCE-POLICY | new | §6 rule above |
| COMPLETION-DEFINITION-REGISTRY | new | §7/§8; version+hash; reuses artifact_registry content-hash discipline |
| COMPLETION-FLAG-GATE | new | AC-FLAG-01/03; each flag → acceptance artifact + JREV; reuses egl_integration evidence gate |
| FOUNDATION-FORECAST-REPORT | new | §6 output contract |
| TEMPORAL-EGL-INTEGRATION | new (thin) | route temporal artifacts to existing SoR (DOMAIN/AUDIT-EGL-INTEGRATION pattern; no new store) |

Suggested order (like the audit-envelope-first logic): TEMPORAL-EVENT-SCHEMA → TIME-BINDING-VALIDATOR → ACTIVE-WORK-AND-WAIT-LEDGER → HISTORICAL-VELOCITY-CALCULATOR + ESTIMATION-BASIS-BINDING + UNKNOWN-VARIANCE-POLICY → COMPLETION-DEFINITION-REGISTRY + COMPLETION-FLAG-GATE → FOUNDATION-FORECAST-REPORT → TEMPORAL-EGL-INTEGRATION. Then ECONOMY-OPERATOR is unblocked (AMEND-TEMPORAL-ORDERING).

## 8. Not done in this deliverable (explicit)
Child ITEM id issuance; any code; any retrofit of existing records; any DB/schema change; independent (different-weight) review of this plan; Taka approval of the Completion Definition v1 flag set.
