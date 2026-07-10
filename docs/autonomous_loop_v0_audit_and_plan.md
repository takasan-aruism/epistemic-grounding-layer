# 2DER AUTONOMOUS RESEARCH LOOP v0 — autonomy boundary audit + execution plan

- **as-of:** 2026-07-10 · **basis:** repo/code現物 (not chat) · **discipline:** author≠auditor · C≠H · self-improvement claim を書かない · 生成物≠evidence · commit=Taka authority for program-level items.
- **main objective (Taka, v0 direction authority granted):** current system state を読み、authority boundary 内で次の technical work を選び、Claude Code / local worker で調査・設計・実験・validation し、ledger / living spec / component state を更新し、本当に Taka authority が要るまで停止しない research loop へ進める。**self-improvement capability claim ではない** — 既存資産(EGL SoR / DE ledger / seals / prereg discipline / author≠auditor / bridge / negative closure / authority separation)を機械接続し manual relay を減らす試み。

---

## 1. Current research loop — executable map (現物 based)

| # | STEP | CURRENT OWNER | FILE/ARTIFACT | LIVE/EXHIBIT/MANUAL/MISSING | MACHINE-READABLE OUTPUT? | REVERSIBLE | WHY HUMAN NOW |
|---|---|---|---|---|---|---|---|
| 1 | new result/incident | run_* scripts | `experiments/*_result.json`, `*_run.json` | LIVE(manual invoke) | yes | yes | 起動が手動 |
| 2 | state recognition | Claude(chat) | — (**no CURRENT_STATE artifact**) | **MANUAL** | **no** | — | 状態が機械集約されていない |
| 3 | gap/contradiction recognition | Claude | seals, validate outputs, DE ledger | MANUAL + partial mechanical | partial | yes | seal-mismatch/validation-fail は機械可読、解釈は人 |
| 4 | next branch selection | Taka+Claude(chat) | — (**no router**) | **MISSING(machine)** | no | yes | 選択が会話 |
| 5 | actual-path audit | Claude Code | read-only tools | LIVE(this session の運用) | findings(text) | yes | 手動起動 |
| 6 | spec/prereg | Claude | `docs/*_prereg_*.md` | LIVE | yes(files) | yes | 手動 |
| 7 | seal | Claude | `experiments/*_seal.json` (plain sha256) | LIVE | **yes(machine-verifiable)** | yes | 手動起動のみ |
| 8 | independent audit | Claude subagent | Agent(author≠auditor) | LIVE | verdict(json) | yes | 手動起動 |
| 9 | implementation | Claude Code | Edit/Write | LIVE | code | yes(git) | 手動 |
| 10 | run | run_* | vLLM:8005 | LIVE | result json | yes | 手動 |
| 11 | validation | test_*.py / validate_answer | pytest-less asserts | LIVE | pass/fail | yes | 手動起動 |
| 12 | evidence disposition | Claude+Taka | DE `replication_status`/`decision` | MANUAL | semi(free-text) | append-only | experiment vs program disposition 未分離 |
| 13 | DE ledger update | Claude | `DESIGN_EVIDENCE_LEDGER.jsonl` | LIVE(append) | yes | append-only | 手動 append |
| 14 | living spec update | Claude | `docs/2DER_TECHNICAL_SPECIFICATION.md` | LIVE | markdown | yes | 手動、機械節と narrative 未分離 |
| 15 | next work | — | — | **MISSING** | — | — | loop 未接続 |

**現物事実:** DE ledger=136 entries, `replication_status`=**~100 distinct free-text 値**(clean enum でない → 機械 closure 判定は heuristic)。seals=plain sha256(機械検証可)。**CURRENT_STATE artifact なし・web/UI stack なし・work-router なし。** `egl/self_grounding.py` は既に自己状態を LLM 再構成できる(M1 forged-id risk あり=検証必須)。

---

## 2. Autonomy classification matrix (deliverable 3)

| STEP | CLASS | REASON | AUTHORITY BASIS | ROLLBACK |
|---|---|---|---|---|
| state recognition (2) | **AUTO-NOW** | DE ledger/seals/files は機械可読。集約 JSON 生成に判断不要 | — | 派生 artifact 削除で可 |
| seal compute/verify (7) | **AUTO-NOW** | sha256 再計算 vs 記録値 | — | 可 |
| validation run (11) | **AUTO-WITH-SMALL-ADAPTER** | test runner を呼ぶ wiring | — | 可 |
| spec 機械節 update (14a) | **AUTO-NOW** | status/seal/latest-DE は機械導出 | — | 可(git) |
| gap/contradiction (3) | **AUTO-NOW(機械部)** / **CLAUDE-AUTO(解釈)** | seal-mismatch/validation-fail/spec-stale は機械; 意味解釈は調査 | — | 可 |
| next branch selection (4) | **AUTO-WITH-SMALL-ADAPTER** | §6 の deterministic ordering を CURRENT_STATE 上で | — | 可 |
| actual-path audit (5) | **CLAUDE-AUTO** | mechanical でないが現物調査で処理可、Taka 不要 | senior-investigator | 可(read-only) |
| spec/prereg/impl/run (6,9,10) | **CLAUDE-AUTO** | audit VALID かつ authority 不要なら | — | 可(git) |
| independent audit (8) | **CLAUDE-AUTO** | subagent author≠auditor | — | 可 |
| experiment disposition (12a) | **AUTO-WITH-SMALL-ADAPTER** | prereg threshold/seal-match に従う機械記録 | prereg rule | append-only |
| **program disposition (12b)** | **TAKA-GATED** | research line 廃止 / objective / architecture / resource | owner | — |
| living spec narrative (14b) | **CLAUDE-AUTO(draft)** / **TAKA-GATED(commit of interpretation)** | 局在解釈・優先は value 含む | owner for commit | 可(git) |
| new research hypothesis | **TAKA-GATED or CLAUDE-AUTO** | 新 premise は owner endorsement | owner | — |
| Attention Center / same-object binding / structural re-centering / Aruism regime | **CURRENTLY-UNOWNED** | construct 自体が無い | — | — |

**規律:** technical uncertainty は「uncertain therefore Taka」にしない。まず CLAUDE-AUTO で現物調査。

---

## 3. Self-state generation contract (deliverable 4) — `CURRENT_STATE.json`
各 field は **origin ∈ {MECHANICAL, CLAUDE-DERIVED, TAKA-OWNED}** を持つ。

| field | origin | source |
|---|---|---|
| `as_of` | MECHANICAL | wall clock |
| `latest_de`, `n_de_entries` | MECHANICAL | DE ledger tail/len |
| `de_index[]` `{id,evidence_class,replication_status,decision,decision_owner}` | MECHANICAL | ledger parse |
| `seals[]` `{file, referenced, status: OK/MISMATCH/UNVERIFIABLE}` | MECHANICAL | sha256 recompute |
| `component_files` (egl/*.py, experiments/run_*.py, test_*.py) | MECHANICAL | fs listing |
| `component_status_tags` (LIVE/EXHIBIT/…) | **CLAUDE-DERIVED** | living spec §2(authored) |
| `closed_branches[]` | **CLAUDE-DERIVED(heuristic)** | DE `decision`/`replication_status` keyword (CLOSE/NEGATIVE/DEMOTE/NOT_CONFIRMED) — **rule 明示、機械ではあるが解釈的** |
| `unowned_constructs[]` | CLAUDE-DERIVED | living spec §2.8 |
| `open_gaps[]` | CLAUDE-DERIVED | living spec §5 / bridge open_gaps |
| `validation_failures[]` | MECHANICAL | result JSON `coverage_ok=false` / validate `m1_..._pass=false` |
| `spec_staleness` `{spec_latest_de, ledger_latest_de, stale:bool}` | MECHANICAL | compare | 
| `authority_pending[]` | TAKA-OWNED | 明示 Taka 事項のみ(v0 は空 or 明示) |
| `candidate_executable_work[]` | MECHANICAL(subset) | seal mismatch / spec stale / validation fail から機械導出。**LLM 自由作文を primary source にしない** |

**不変:** builder は SoR/ledger に **write しない**(CURRENT_STATE.json のみ生成=派生 projection、再生成・削除可)。status を捏造しない(heuristic は CLAUDE-DERIVED と正直に tag)。

---

## 4. Living-spec auto-update boundary (deliverable 5)

| section | MACHINE REGEN? | SOURCE OF TRUTH | CLAUDE REVIEW | TAKA APPROVAL | AUTO-UPDATE SAFE |
|---|---|---|---|---|---|
| §2 component status tags | partial(file list=yes, tag=no) | spec/DE | yes | tag 変更時 | 部分 |
| §5 evidence status table | **YES(値)** | DE ledger | verify | no(値のみ) | **AUTO-NOW 候補** |
| §9 reproducibility anchors (seals/pins/latest-DE) | **YES** | seals/ledger | verify | no | **AUTO-NOW 候補** |
| §12 changelog (append DE line) | **YES** | DE ledger | verify | no | AUTO-NOW 候補 |
| §1 layer / §3 data contracts | no(stable) | authored | — | 変更時 | no |
| §4 discipline | no | authored | — | 変更時 | no |
| §6 局在 narrative / §8 priority | no | authored | draft only | **YES** | no(value) |

→ **SLICE-2** = §5/§9/§12 の機械節を CURRENT_STATE から再生成(narrative 節は触らない)。

---

## 5. Experiment vs program disposition (deliverable = §5 分離)
- **EXPERIMENT DISPOSITION**(prereg threshold unmet / validation fail / instrument invalid / reproducibility fail / negative result / seal mismatch)→ **AUTO-WITH-SMALL-ADAPTER**: prereg rule に従い DE entry を `replication_status=*_NEGATIVE/…` で自動 append。例: threshold unmet → branch CLOSED NEGATIVE(precedent: DE-0130 は機械 rule に合致する形)。
- **PROGRAM DISPOSITION**(research line を永久放棄 / objective 変更 / architecture 方針 / resource priority)→ **TAKA-GATED**。例: 「scheduler concept を program 全体で永久禁止」。
- 分離の実装: DE entry に `disposition_class ∈ {EXPERIMENT, PROGRAM}` を足す(新 field, 後方互換)か、`decision_owner` を機械判定に使う。**experiment disposition のみ auto-record**、program は STOP_FOR_TAKA。

---

## 6. Next-work selection (deliverable 6) — deterministic ordering 検証
既存 status/failure/gate semantics から near-deterministic ordering が成立するか:
```
priority = 1 broken invariant (test fail / assert fail)
           2 invalid instrument (construct audit gate_pass=false)
           3 failed validation (coverage_ok=false / M1 fail on a load-bearing claim)
           4 approved DESIGN-VALID small adapter not implemented
           5 stale state/spec (spec_latest_de < ledger_latest_de)
           6 unresolved technical wiring (open TODO in DESIGN-ONLY)
           7 new research hypothesis  ← CLAUDE-AUTO/TAKA-GATED, 分離
```
**検証:** 1–5 は CURRENT_STATE の MECHANICAL field から順序が決まる(新 composite score 不要)。6–7 は解釈=CLAUDE-AUTO/TAKA。→ router は 1–5 を deterministic に選び、無ければ 6 を CLAUDE-AUTO へ、7 は STOP_FOR_TAKA。**整合 OK**(既存 evidence discipline: broken invariant/instrument-invalid を最優先=author≠auditor と一致)。

---

## 7. Claude investigator/executor contract (deliverable 7)
INPUT: CURRENT_STATE, task object, artifact pointers, code refs, evidence status, authority boundary。
SEQUENCE: ①現物 open ②actual path 再構成 ③expected vs actual ④issue classify(A real / B echo / C batching / D instrument defect / E missing evidence / F representation loss / G unknown = **出力** family)⑤smallest reversible next action ⑥既存 construct で足りるか ⑦要れば spec→prereg→seal→independent audit ⑧audit VALID かつ authority 不要なら implement→run→validate ⑨record ⑩state update ⑪router へ戻る。
PROHIBITIONS: inspection 前の説明 / objective silent 変更 / CLOSED NEGATIVE を改名再開 / 生成物の evidence 昇格 / disposition path 外の status 変更 / 技術不明だけで Taka / irreversible external / TAKA-GATED の commit。

---

## 8. Auto-continue gate (deliverable 8)
`CONTINUE_AUTONOMOUSLY` / `STOP_FOR_TAKA` / `STOP_INVALID_INSTRUMENT` / `STOP_SYSTEM_ERROR`。
**STOP_FOR_TAKA only when:** objective / acceptable-risk / value・UX preference / 2 genuinely valid incompatible routes / irreversible external / program-level disposition / 新 premise の owner endorsement。
STOP_FOR_TAKA payload 必須: `WHY_TAKA_NEEDED, AVAILABLE_OPTIONS, TECHNICAL_WORK_ALREADY_COMPLETED, WHAT_CANNOT_BE_RESOLVED_FROM_REPO, REVERSIBILITY`。**"unsure" は理由にならない。** それ以外は preferentially CONTINUE。

---

## 9. Minimum UI correction-surface spec (deliverable 9) — INCLUDE NOW
**prior art:** web/UI stack 無し。→ 依存を増やさず **self-contained static HTML dashboard(CDN 無し)** が `CURRENT_STATE.json` + `AUTONOMY_LEDGER.jsonl` を読むだけの read surface + 別途 **CLI amender**(machine event を append)で correction。UI=correction/adjudication surface であって完成品でない。
views: **A SYSTEM STATE**(mode/latest DE/active task/branch/component status/latest result/open gaps/UNOWNED)· **B AUTONOMOUS ACTIVITY**(timeline: what/why/which artifact)· **C TAKA DECISION QUEUE**(TAKA-GATED のみ; card=question/why-authority/technical-findings-done/options/reversible/recommendation/Approve-Reject-Hold-Redirect)· **D CORRECTION/AMENDMENT**(wrong interpretation/priority/status/authority-reclass/context add → **machine event, not text edit**)· **E TASK DETAIL**(input state→task→artifacts→findings→spec/audit→run→validation→disposition; concise default, raw expandable)。

## 10. Taka correction event contract (deliverable 10)
**reuse EGL append-only semantics**(`core.append_event` 形; 別 mutable DB を作らない)。dedicated append-only `AUTONOMY_LEDGER.jsonl`(knowledge SoR と分離、program-governance 用)。event:
```
{event_id, ts, owner:"Taka", target_object, action, content, previous_state_ref, reason?, downstream_effect}
```
action ∈ `TAKA_CORRECTION / TAKA_PRIORITY_OVERRIDE / TAKA_HOLD / TAKA_REJECT / TAKA_REDIRECT / TAKA_AUTHORITY_RECLASSIFICATION / TAKA_CONTEXT_ADDITION`。
**router effect:** router は次 loop 開始時に AUTONOMY_LEDGER を読み、Taka events を CURRENT_STATE へ overlay(HOLD→該当 branch skip / PRIORITY_OVERRIDE→順序上書き / REDIRECT→task 差替 / AUTHORITY_RECLASSIFICATION→class 変更 / CONTEXT_ADDITION→task input へ添付)。append-only ゆえ可逆(後続 event で上書き、履歴保持)。**hardening path:** 将来 `core.append_event` + capability(Taka←root)で semantic write authority を機械検出可能に。

---

## 11. Ordered executable slices (deliverable 11)

| slice | what | class | deps | LOC | new LLM calls | authority | rollback | testability | immediate value |
|---|---|---|---|---|---|---|---|---|---|
| **SLICE-1** | mechanical `CURRENT_STATE.json` builder | **AUTO-NOW** | none | ~120 | 0 | none | delete artifact | high(hermetic) | 状態の単一機械 source |
| SLICE-2 | living-spec §5/§9/§12 regen from CURRENT_STATE | AUTO-NOW | 1 | ~60 | 0 | none | git | high | spec 自動同期 |
| SLICE-3 | autonomy router (deterministic §6 1–5) | SMALL-ADAPTER | 1 | ~80 | 0 | none | none(dry) | high | 次 work 機械選択 |
| SLICE-4 | Claude investigator task runner | CLAUDE-AUTO | 1,3 | ~100 | 1+/task | none(read) | git | med | 調査自動化 |
| SLICE-5 | minimal UI(static HTML)+ CLI amender + AUTONOMY_LEDGER | SMALL-ADAPTER | 1 | ~150 | 0 | Taka surface | append-only | med | Taka correction surface |

**earliest executable = SLICE-1**(dependency of全て, AUTO-NOW, 0 LLM, reversible, testable, immediate value)。→ PHASE 3 で prereg→independent audit→implement→test→record。

---

## 12. 判定(final report は実装後に本文で A–F を回答)
loop の human bottleneck は **capability** ではなく **wiring**(state 集約・router・spec 同期が未接続)。AUTO-NOW/SMALL-ADAPTER で SLICE-1→2→3→5 を接続すれば、experiment disposition までを Taka 無しで回し、program disposition と value/UX と新 premise だけ STOP_FOR_TAKA にできる。Attention Center 系は UNOWNED のまま(この loop の外)。
