# 2DER — 詳細技術仕様書 (living document)

- **version:** 1.1
- **as-of:** 2026-07-10
- **program main theme (2026-07-10, Taka v0-direction authority):** 2DER AUTONOMOUS RESEARCH LOOP v0(既存資産を機械接続し manual relay を減らす; **self-improvement claim ではない**)。boundary audit+plan = `docs/autonomous_loop_v0_audit_and_plan.md`。Attention Center は引き続き重要な research branch だが **main theme ではない**。
- **basis line:** 2026-07-08 現状整理 + (scheduler closure / Attention Center 探索 / HBB-30 trace / HBB→EGL bridge)
- **status:** DESCRIPTIVE SPEC of the current system. NOT a roadmap commitment.
- **epistemic discipline (binding on this document):** author≠auditor · C≠H(新規説明を過去原因へ後付けしない) · 自律RD 未有効 · self-improvement claim を書かない · 生成中間物 ≠ validated evidence · open_gap ≠ false premise · Taka = final authority。
- **honesty rule:** 各 component は必ず **LIVE / EXHIBIT-ONLY / SPEC-ONLY / DESIGN-ONLY / UNOWNED** のいずれかで札付けする。札のない能力主張を書かない。

> この文書の維持方法・「2DER 自身がこれを更新できるか」は §10、更新履歴は §12。

---

## 0. 一文
2DER は「欠けた軸・区別・観測境界を探す fault finder」から、**通常 LLM が処理中に生成したが最終統合で落とす未解消材料を保持し、回答候補と unresolved material を分離して user へ露出できる**段階へ進んだ。ただし *どの周辺観察を注意対象に浮上させ・同じ局所の揺れとして束ね・その局所だけ再中心化し・必要時だけ Aruism を短時間かけて現実へ戻すか* という **Attention Center / operational regime 本体は UNOWNED**。

---

## 1. 層構造 (4 layer)

| layer | role | 実体 (owner) | status |
|---|---|---|---|
| WORKER | solve / generate / detect / reconstruct | Qwen3.6-35B-A3B @ localhost:8005 (vLLM, ctx=32768) | LIVE |
| SUPERVISOR | retain / validate / track / open_gaps / authority 分離 | EGL SoR (`egl/*.py`) + answer contract (`egl/self_grounding.py`) | LIVE |
| SENIOR INVESTIGATOR | 集約 unresolved issue を起点に現物 (artifact/code/runtime) を read-only 監査し next action を絞る | Claude Code (この session の運用そのもの) | 運用 LIVE / MACHINE routing = DESIGN-ONLY (§7) |
| AUTHORITY | objective / acceptable-risk / program scope / final disposition | Taka | LIVE |

**不変則:** WORKER の生成物は SUPERVISOR で validated evidence にならない。SENIOR INVESTIGATOR は read-only 監査・提案・spec 準備はできるが objective 変更・branch 閉鎖・evidence 昇格はできない。AUTHORITY のみが不可逆 program 判断を持つ。

---

## 2. Component inventory (札付き)

### 2.1 EGL SoR — LIVE (test-covered, event-sourced)
- `egl/core.py` — append-only event store (`data/events.jsonl`) + derived view (`data/state.sqlite`)。`object_id` merge (`get_state`)、`PRIVILEGED_EVENTS={CORRECTION,COMPLETION}`、`CAPABILITY_ISSUERS root`。
- `egl/pipeline.py` — GAP→OBSERVATION→FRAGMENT→CANDIDATE→CLAIM。`apply_outcome:108` が **code のみ**で Claim を書く(CU-1)。`mk_gap:71` KnowledgeGap。`status ∈ {VERIFIED, REPORTED, NOT_FOUND}`、`validation_mode` は provenance 導出(導出不能=UNRESOLVED)、`entailment_status` は admission と別軸(DE-0041)。
- `egl/gates.py` — Decision Table `decide:222-245`、outcome ∈ `{EVIDENCE_INSUFFICIENT, REJECT_CONTRADICTED, SCOPE_REDUCTION_REQUIRED, CONFLICT_REVIEW_REQUIRED, ACCEPT}`。authority: 「LLM は DB write 権限を持たない」(`:2-3`)。
- `egl/judge.py` — teacher signal。`F1_VALUES={SUPPORTED,PARTIAL,NOT_SUPPORTED,CONTRADICTS,UNJUDGEABLE}` / `F2_VALUES={WITHIN,EXCEEDS,NARROWER,DISJOINT,UNRESOLVED}` (`:10-11`)。`teacher_signal=True`(ground truth でない)。
- `egl/curator.py` — block/curate、residual 表示。

### 2.2 Answer contract — LIVE
- `egl/self_grounding.py` — `answer_question:254(question, records=, superseded=, system=, k=, force_include=)` → `(answer_dict, retrieved_ids, raw)`。`validate_answer:296` = 3 軸 **M1 GROUNDING_INTEGRITY / M2 SEMANTIC_PLACEMENT / M3 FORMAT**(hermetic, deterministic)。`ANSWER_KEYS=[answer_claims, historical_claims, open_gaps, source_trace]:197`。M1 は `answer_claims`/`source_trace` の record_id 実在を要求; **`open_gaps` は count のみ(=機械 grounding されない)**。
- 現行 workload = SELF_GROUNDING(自分の開発史 = `DESIGN_EVIDENCE_LEDGER`+`REVIEW_LEDGER` を corpus に、自分の epistemic state を再構成)。`records=`/`system=` override で別 workload 可(bridge が使用)。

### 2.3 AEC / AES — SPEC-ONLY (test-covered, unwired)
- `answer_evidence.py` — per-claim packet render (`render_compact`/`render_expanded`)。`VALIDATION_MODES={DECLARED,SPECIFIED,OBSERVED,MEASURED,REPRODUCED,UNRESOLVED}`、`BASIS_KINDS`、`strength_guard`(lexical anti-inflation)。**live answer path には未接続**(test import のみ)。

### 2.4 Reconstruction pipeline — EXHIBIT-ONLY (manual-gated, no test, live vLLM 依存)
- `experiments/run_scheduler_exhibit.py` — `view_call:58 → signature_call:67 (SUBJECT=|LEVEL=|KEY-DISTINCTION=) → compare_call:74 (V→1, frame 不在) → rebuild_call:82 → check_call:89 (CHANGED/HOLD, HOLD-2→ESCALATE)`。persist = `scheduler_exhibit_candidates.json` (records[].candidates = **rebuild text**; `n_distinct:168`)、`_trace.json` (opaque_id `:171`, lenses, verdict)。**views/signatures/deltas は ephemeral(非永続)**。INCIDENTS=`HBB-08/10/30`、conditions=`R0/RS/RS_pool/RS_flat`。
- capability 判定 = **CLOSED NEGATIVE at bar** (DE-0130)。compare→rebuild は directional-only。

### 2.5 AFE / Formal operators — EXHIBIT, content WEAK/NEGATIVE
- `run_afe_walking.py aggregate:47-69` — valid-SIGNAL filter + 同構造 dedup + `support_count=len(set(operator_id))` + provenance。doctrine: **「support count は provenance であって truth vote ではない」(`:73-74`)**。
- FE-LINK / FE-TERNARY (`formal_esde_operators.json:10-11`) — LLM probe。evidence WEAK/NEGATIVE(`hbb_sealed_report.md:40`; DE-0103/0104: AFE は placebo 超えるが generic skepticism を明確に超えず、`C-unique=D-unique=0`)。
- **CONTENT は owned だが弱い。OPERATIONAL REGIME(shake/trigger/duration/reality-return)は UNOWNED。**

### 2.6 HBB→EGL unresolved bridge — IMPLEMENTED (wiring feasibility)
- `experiments/run_hbb_egl_bridge.py`、spec `docs/hbb_egl_bridge_spec_v0.2.md`、seal `c9fedde0`。frozen HBB-30 rebuild-candidate text (240, pinned) を既存 answer contract へ **format-only** で渡し `answer_claims + open_gaps` 同時露出。Claim を作らず、admission gate を呼ばず、answer 層は SoR に read-only。
- v0.2 fixes: FIX-1 `force_include`+coverage assert / FIX-2 records 非空 / FIX-3 open_gaps grounding overclaim 撤回 / FIX-4 `superseded={}` / FIX-5 ctx 不足時 logged batching。independent re-audit = **BRIDGE DESIGN VALID**。
- replay: ctx=32768<64K → per-condition batched (4 calls)、**coverage 240/240、0 drop**、answer_claims+open_gaps 全 batch 共存。**honest caveat:** validate M1 grounding pass R0/RS_pool(src_trace 1.0) / **fail RS(0.4)/RS_flat(0.8)**(answerer が forged record_id を出し contract が検出)、M2 全 batch fail(HISTORICAL 誤配置)。DE-0136 `WIRING_FEASIBILITY_CONFIRMED_NARROW`。
- 現物例: R0 の第1 answer_claim は **54 record_ids を引用**(= 1 claim が 54 生成物を集約、**54 sources ではない**)。

### 2.7 2DER → Claude Code routing layer — DESIGN-ONLY (read-only audit 済、未実装)
- verdict: **SMALL ROUTING LAYER POSSIBLE**(§7)。aggregation boundary = 永続 replay result 上の standalone on-demand card-builder。gate = 既存 signal のみ(validate M1/M2 failure OR provenance recurrence)。**「open_gaps 存在」だけの routing は過剰**として却下。
- reuse: `audit_backlog.jsonl` issue-card schema(DIRECT)、`aggregate()`/`n_distinct` recurrence(DIRECT、provenance≠vote)、`RECON_GPT_HANDOFF` envelope(SMALL-ADAPTER)、`decision_owner`(escalation は現状 prose)。
- new minimum: investigator-task object + `ESCALATED/AWAITING_TAKA` status 値。~60–100 LOC、pipeline LLM call 0。

### 2.8 UNOWNED (未所有・未実装、この文書で resolved 扱いにしない)
- **Attention Center** — どの周辺観察を answer-blind/label-free に注意対象へ浮上させるか。ledger salience は batching を拾い shake detector にならず DEMOTE(DE-0131/0133)。
- **same-object tension binding** — 複数観察を意味ラベルなしに「同じ局所の揺れ」として束ねる object identity。既存に label-free 機構なし(`aggregate.norm()` は文字列正規化)。
- **structural re-centering** — reconstruction に explicit `center_object` state なし。prompt repetition は echo と交絡、center-shift branch は NEGATIVE(DE-0134/0135)。
- **local Aruism operational regime** — 揺れた局所だけに短時間 Aruism を掛け通常系へ戻す trigger/duration/return。未所有。
- **end-to-end self-operation** — incident 投入→次実験提案を 2DER 自身で回す MVP、GPT↔Claude 手動 relay 除去。未完成。

### 2.9 Autonomous research loop v0 — SLICE-1 LIVE / SLICE-2..5 DESIGN-ONLY
- `autonomy/current_state.py` + `build_state.py` + `test_autonomy_state.py`(8/8）= **SLICE-1 mechanical CURRENT_STATE builder(LIVE, AUTO-NOW)**。DE ledger/seals(sha256 recompute)/component files/result artifacts → 状態 projection、各 field に origin(MECHANICAL/CLAUDE-DERIVED/TAKA-OWNED)。side-effect-free(CLI のみ `CURRENT_STATE.json` を生成=再生成可、gitignore)。independent audit=SLICE VALID(DE-0137)。
- `autonomy/amend.py` + `dashboard.py` + overlay in `current_state.py` + `test_autonomy_amend.py`(7/7)= **SLICE-5 Taka correction surface(LIVE)**: Taka corrections = append-only machine events(`AUTONOMY_LEDGER.jsonl`, owner=Taka, 7 actions, latest-per-target supersession, 知識 SoR と分離)。overlay が HOLD/REJECT/PRIORITY を candidate_work へ realize(visible `taka_overlay_effects`+`authority_pending`); REDIRECT/RECLASS=surfaced-only; CORRECTION/CONTEXT=recorded-only(honest)。self-contained static HTML dashboard(CDN/server なし)。independent audit=SLICE VALID(over-claim を pre-commit で honesty 修正; DE-0138)。
- `autonomy/amend.sh`(pure shell)+ `state_report.py` + `docs/STATE.md` + `docs/CLIENT_USAGE.md` + tracked `AUTONOMY_LEDGER.jsonl` + `test_autonomy_client.py`(8/8)= **SLICE-6 client-usable surface via git(LIVE)**: dev≠client。client(git CLI, python/browser 不要)は `git pull`+`cat docs/STATE.md` で観測、`amend.sh`→`git push` で append-only 訂正イベント投入; dev が pull→overlay→STATE.md 再生成。shell↔python event 互換を検証。independent audit 2 周(round-1 が **2 件の gate-blocking defect**〈control-char で JSON 破損→client 訂正 silent 消失 / mawk octal id bug〉を捕捉→修正→round-2 SLICE VALID)。DE-0139。
- `autonomy/webui.py`(stdlib http.server, 依存追加なし)+ `test_autonomy_webui.py`(3/3, HTTP-level)= **SLICE-7 thin Web UI(LIVE)**: Taka が **git 不要**でブラウザ(Mac/iPhone, LAN/Tailscale, bind 0.0.0.0, v0 no-auth)から操作。CURRENT_STATE + candidate work + decision queue 表示、card ボタン(HOLD/REJECT/PRIORITY/REDIRECT/CORRECT/THIS-REQUIRES-TAKA/DO-NOT-ASK)→ 既存7 actions、Home 自由入力('2DERに渡す')は user-selected type + **honest capability(CAN_PROCESS_NOW / CAN_RECORD_ONLY / NOT-YET-SUPPORTED、fake classifier なし)**。write は AUTONOMY_LEDGER only(SoR/DE 不可)、書込後 state 再build して即時反映。independent audit=SLICE VALID(write-scope/owner-unforgeable/XSS/robustness を実HTTPで検証)。DE-0140。起動 `python3 autonomy/webui.py`。
- **DESIGN-ONLY(未実装、plan §11):** SLICE-2 spec §5/§9/§12 機械再生成 / SLICE-3 autonomy router(deterministic §6 1–5)/ SLICE-4 Claude investigator runner。
- **authority:** experiment disposition = AUTO/SMALL-ADAPTER; **program disposition / value・UX / 新 premise = TAKA-GATED**(auto-continue gate = plan §8)。

---

## 3. Data contracts (機械可読な既存 schema)

| contract | 実体 | key fields |
|---|---|---|
| Claim | `pipeline.py apply_outcome` | `status, entailment_status, validation_mode, admission_basis, origin_candidate` |
| answer | `self_grounding ANSWER_KEYS` | `answer_claims[{text,record_ids,currentness}], historical_claims, open_gaps[str], source_trace` |
| validate | `validate_answer` | `{ok, problems, axes:{M1,M2,M3}, metrics:{n_answer_claims,n_open_gaps,source_trace_completeness,...}}` |
| KnowledgeGap | `pipeline.mk_gap` | `gap_id, question, required_for, status:OPEN, epistemic_profile_id` |
| issue-card (既存) | `audit_backlog.jsonl` | `backlog_id, source, touches_rule, observation, class, status, proposed_amendment, note` |
| handoff envelope | `build_recon_gpt_handoff.py` | `object, rubric_sha256, scoring_instruction, incidents, n_items, items[{opaque_id,...}]` |
| DE ledger | `DESIGN_EVIDENCE_LEDGER.jsonl` | `design_evidence_id, affected_rules, evidence_class, experiment_ref, observation, replication_status, decision, amendment_ref, decision_owner, note` |
| seal | `*_seal.json` | plain-bytes sha256 hexdigest (canonical helper なし) |

**anti-inflation 契約(必須):** OBSERVATION MULTIPLICITY(生成件数) / PATH DIVERSITY(condition×seed×cand_idx = 機械可算) / EVIDENCE MULTIPLICITY(independent admitted source = 現 material では **UNKNOWN**, 全 `HBB_EXHIBIT_INTERMEDIATE`)を同一 count として描画禁止。

---

## 4. Evidence & authority discipline (定着した標準規律)
blind scoring · rubric 先行 seal(v2 sha256 `012941ab…`)· opaque_id `sha256(incident|condition|seed|cand_idx)[:14]` · multi-scorer consensus REC2=`GPT∧Qwen`(Claude 除外)· origin leak 監査 · input **pin**(hash 固定)· **no-silent-cap**(PROCESS-01)· author≠auditor(seal→independent audit→stop) · C≠H · user final authority · self-reference 禁止(DE-0132: live-ledger を self corpus に混ぜない)。

---

## 5. Evidence status 表 (DE 参照)

| item | status | ref |
|---|---|---|
| bridge transport / full coverage / dual-output coexistence | **CONFIRMED (narrow, wiring feasibility)** | DE-0136 |
| detection 中に正答方向 piece 生成 (HBB-30) | CONFIRMED-narrow | HBB-30 trace |
| scheduler multi-view compare/rebuild capability | **CLOSED NEGATIVE at bar** | DE-0130 |
| center-shift (prompt re-quote で center 移動) | **NOT CONFIRMED**(R0 lift は noise/anchoring へ downgrade) | DE-0134/0135 |
| ledger salience (temporal) | PROTOTYPE_CONFIRMED_NARROW = work-phase batching; shake detector に非ず → DEMOTE | DE-0131/0133 |
| ledger salience reproducibility | self-reference defect 検出・pin 修正 | DE-0132 |
| AFE operator CONTENT | WEAK/NEGATIVE(`C-unique=D-unique=0`) | DE-0103/0104 |
| route-vs-repeat construct | v0.1 REJECTED / v0.2 hardened but **audited-and-rejected design of record**(未 commit) | 本 session |
| Attention Center / same-object binding / structural re-centering / Aruism regime | **UNOWNED** | — |
| HBB-30 solved / REC2 | **NOT CLAIMED** | — |
| autonomous loop SLICE-1 (CURRENT_STATE builder) | **OPERATIONAL_TEST_VERIFIED (8/8), SLICE VALID** | DE-0137 |
| autonomous loop SLICE-5 (Taka correction surface + UI) | **OPERATIONAL_TEST_VERIFIED (7/7), SLICE VALID** | DE-0138 |
| autonomous loop SLICE-6 (client-usable surface via git) | **OPERATIONAL_TEST_VERIFIED (8/8), SLICE VALID (2 defects caught+fixed)** | DE-0139 |
| autonomous loop SLICE-7 (thin Web UI, browser, no git) | **OPERATIONAL_TEST_VERIFIED (3/3 HTTP), SLICE VALID** | DE-0140 |
| autonomous loop SLICE-2/3/4 | DESIGN-ONLY | plan §11 |

---

## 6. 問題設定の局在 (2026-07-08 → 2026-07-10)
- 旧: 「RECONSTRUCTION engine が足りない」(独立 stage 新設が P0)。
- 現: HBB-30 trace により **「正答方向 piece は途中で出るが、強い task framing に沿う最終結合で落ちる」** へ局在。task-aligned derivation family が後段へ残り、validity/recoverability/method distinction が derivation narrative へ吸収される。
- よって主問は「もっと違う視点を生成」ではなく **「生成済みの弱い周辺観察を消さず保持し、必要なら別 route へ渡す」**。
- 価値基準の拡張: internal REC2 だけでなく **「important unresolved tension を消したまま misleading confidence を出さなかったか」**。

---

## 7. Routing layer 最小案 (DESIGN-ONLY, read-only audit 済)
- **AGGREGATION BOUNDARY:** 永続 `hbb_egl_bridge_replay_result.json`(および live EGL の KnowledgeGap OPEN + answer 出力)上の standalone on-demand card-builder(boundary E)。normal path 無変更。
- **ROUTING GATE(既存 signal のみ・新 composite score 禁止):** `validate` M1/M2 failure **OR** path-diversity≥K + non-empty open_gaps。**「open_gaps 存在」単独は過剰 routing として却下。** semantic「同一 issue」clustering は UNOWNED same-object binding へ寄るため**使わない**。
- **ISSUE CARD:** audit_backlog 形 + recurrence counts(`n_generated`,`n_distinct`,conditions)+ **`n_independent_sources=UNKNOWN`** + open_gap/answer_claims + validate summary + artifact **pin**(240 全文は投入せず pointer/representative)。
- **CLAUDE TASK CONTRACT:** RECON_GPT_HANDOFF 形 envelope、出力 = 調査 verdict family **A(real structural) / B(generation echo) / C(work batching) / D(instrument defect) / E(missing evidence) / F(representation/routing loss) / G(unknown)**(← これは *出力* 分類であって入力ラベルではない)。prohibitions: original question を解かない・実装前に mechanism 発明しない・record count を evidence count 扱いしない・open_gap を false premise 扱いしない・rubric を answer target にしない・監査前に code 変更しない。
- **ESCALATION(§ authority):** objective / acceptable-risk / value / mutually-valid routes / irreversible scope のときだけ Taka。単なる技術的不明は Claude が先に現物調査。「uncertain therefore ask Taka」は禁止。

---

## 8. 優先順位 (2026-07-10, main theme = autonomous loop v0)
- **P0:** autonomous loop の wiring 接続(SLICE-1 済 → SLICE-2 spec-regen / SLICE-3 router / SLICE-5 UI+Taka-event)。human bottleneck は capability でなく wiring。
- **P0:** unresolved material の authority-safe 集約 + 表示(presentation inflation 対策; §3 anti-inflation)。
- **P0:** 2DER→Claude Code routing の最小成立(§7)。
- **P1:** validator/renderer 残差(bridge の M1 fail RS/RS_flat、M2 placement、count-as-evidence 描画リスク)。
- **P2:** routing 運用で live unresolved/recurrence/investigation outcome を蓄積 → **その実データを基に** Attention Center / operational regime を後で再設計(先に巨大機構を作らない)。
- **保留:** end-to-end self-operation MVP、local Aruism regime。**自律RD 未有効。**

---

## 9. Reproducibility anchors
- pins: candidates `b7c98296…` / HBB-30 subset `9e1ca25b…` / t0_frame `bc09d36d…`。
- seals: bridge prereg v0.2 `c9fedde0`、rubric v2 `012941ab…`。
- key entrypoints: `egl/self_grounding.py:254`(answer)、`egl/pipeline.py:108`(admission)、`experiments/run_hbb_egl_bridge.py`(bridge)、`experiments/run_scheduler_exhibit.py`(exhibit)。
- ledger: `DESIGN_EVIDENCE_LEDGER.jsonl`(最新 DE-0136)。

---

## 10. 「2DER 自身がこの仕様書を作成・管理・更新できるか」— honest assessment
- **部分的に YES(自己状態の再構成):** `egl/self_grounding.py answer_question` は既に「今何を信じ / 何が未検証(open_gaps) / 何が superseded / どの過去 failure に似るか」を **自分の台帳(DE+REVIEW ledger)から構造化再構成できる** LIVE 機構。§5 の evidence-status 表のような部分は、DE ledger + seals から**機械的に再生成可能**(routing card-builder と同種の Tier-1、~数十 LOC、0 新規機構)。
- **NO(自律的な仕様書の作成・維持):** (a) self_grounding の出力は JSON answer であって整形 spec ではない; (b) benchmark harness であり doc generator ではない; (c) **bridge replay と同じ M1 grounding 失敗(forged id)を出す**ので出力は検証必須(自動信頼禁止); (d) 何を LIVE/EXHIBIT/UNOWNED と札付けし何を優先とするかは senior-investigator(Claude Code)+ author(Taka)の判断; (e) **自律RD 未有効** — 2DER は自分の spec を自律的に更新する権限を持たない。
- **現実的な運用(推奨):** この doc を repo 常駐 living document とし、**更新は Claude Code が起草 → Taka が commit authority**。将来、DE ledger + seals + self_grounding 出力から **§5 evidence-status 表と §2 component 札だけを機械再生成する小さな doc-builder**(routing layer と同じ boundary-E on-demand 方式)を追加可能。ただし「2DER が仕様書全体を自律生成・自律 commit」は現状 capability に無く、self-improvement claim もしない。

---

## 11. 判定
2DER は Aruism prompt 実験 / missing-axis generator を越え、探索・採点・authority・evidence discipline を持つ**研究処理系**。進化の中心は純粋な回答スコアよりも **「LLM が途中で見たものを捨てない」「不確実性を authority-safe に表示する」「技術的詰まりを上級 AI へ route する」** という運用・製品化側の成熟。本当の未完成点は §2.8 UNOWNED(注意対象の自律選択・同一局所束ね・局所再中心化・局所 Aruism regime)。直近本線は Attention Center を先に巨大機構化することではなく、§7 routing を成立させ、その live データで後から Attention Center を設計すること。

---

## 12. 更新プロトコル / changelog
- **更新規律:** append-only の DE ledger と整合させる。ある branch/DE が status を変えたら、§2 札・§5 表・§8 優先を更新し、version を上げ、下の changelog に 1 行追記。実装を伴う設計変更は seal→independent audit→stop の順(§4)。**commit は Taka authority。**
- **この doc を読むべき時:** 新 branch 着手前 / 能力主張前 / routing・Attention Center 設計前。
- changelog:
  - v1.0 (2026-07-10) — 初版。scheduler closure(DE-0130)、center-shift NEGATIVE(DE-0134/0135)、ledger salience DEMOTE(DE-0131/0133)、HBB→EGL bridge feasibility(DE-0136)、routing layer DESIGN-ONLY を反映。
  - v1.1 (2026-07-10) — program main theme = 2DER AUTONOMOUS RESEARCH LOOP v0(Taka v0-direction authority)。§2.9 追加(SLICE-1 CURRENT_STATE builder LIVE / SLICE-2..5 DESIGN-ONLY)、§5 に SLICE-1 行、§8 P0 更新。DE-0137。boundary audit+plan = docs/autonomous_loop_v0_audit_and_plan.md。
  - v1.2 (2026-07-10) — SLICE-5 Taka correction surface + minimum UI LIVE(§2.9 更新、§5 に SLICE-5 行)。append-only AUTONOMY_LEDGER + state overlay + self-contained dashboard。DE-0138。
  - v1.3 (2026-07-10) — SLICE-6 client-usable surface via git LIVE(dev≠client)。observe=committed `docs/STATE.md`、correct=pure-shell `autonomy/amend.sh`→git、`docs/CLIENT_USAGE.md`。independent audit が control-char JSON 破損 + mawk octal id の 2 defect を捕捉→修正→VALID。DE-0139。
  - v1.4 (2026-07-10) — SLICE-7 thin Web UI LIVE(`autonomy/webui.py`, stdlib)。Taka が git 不要でブラウザ(Mac/iPhone LAN/Tailscale)から state 閲覧・card ボタン訂正・自由入力(honest capability tier)。write=AUTONOMY_LEDGER only、即時反映。independent audit(実HTTP)=SLICE VALID。DE-0140。git-CLI surface(SLICE-6)は dev/sync 用に保持。
