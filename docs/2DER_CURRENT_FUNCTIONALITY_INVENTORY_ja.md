# 2DER 現行機能インベントリ（完全状態資料）

> _as_of 2026-07-15 · owner=Taka · コード一次情報から再導出 · schema v1_
>
> 本資料は「今この瞬間の 2DER が実際に何をやるか」を、5リポのコードを一次情報として棚卸ししたもの。
> 各機能は **LIVE / PARTIAL / CLOSED / ORPHANED** で分類し、根拠（コミット・ファイル・実行 artifact）を紐づける。
> **過剰主張を避けることを最優先**とし、動いていない枝・死んだ枝を「機能」として載せない（載せる場合は必ずタグで区別）。

---

## 0 · この資料の位置づけと、既存ドキュメントとの関係（重要）

現状を写した完全資料は**これまで存在しなかった**。既存ドキュメントは軒並み実装から大きく遅れている：

| ドキュメント | 自称/更新時点 | 実態 |
|---|---|---|
| `egl/DESIGN_EVIDENCE_LEDGER.jsonl` | **DE-0330**（327エントリ） | ✅ **DE の真の一次情報。これが現在地** |
| `twoder/audit/RESTORATION_STATUS.md` | 2026-07-12 | ✅ 現状の権威ある状態ドキュメント（A–F クラス分類） |
| `twoder/audit/AS_BUILT_CAPABILITY_LEDGER.md` | — | ✅ as-built 能力台帳 |
| `egl/docs/STATE.md` | DE-0147・STALE 明記 | ⚠️ **183 DE / ~4日遅れ。状態判断に使うな** |
| `egl/docs/2DER_TECHNICAL_SPECIFICATION.md` | 2026-07-11 07:00（pre-DE-0159） | ⚠️ off-ramp/live-worker/runtime-supervisor/adjudication 全系列を含まない。~DE-0150 以降について権威なし |
| memory (living doc) | DE-0159 | ⚠️ stale |

> **注意**: `STATE.md` の DE-0147 は「2DER autonomy loop」ledger の数字で、EGL 本体の `DESIGN_EVIDENCE_LEDGER`（DE-0330）とは別物。混同禁止。commits は DE-0325 まで参照、ledger 本体はさらに 0326–0330 まで進む。`twoder` ツリー内の `DE-9001/9002` はテストfixture、無視。

---

## 1 · 2DER とは何か（現在の定義）

**2DER = DS→RRI→EGL→DW の4役割系を貫く「直接入力コンダクタ」**。DE-0146 の pivot で確定した姿：

- **2DER が継続アクター**（連続して仕事を運ぶ主体）、**Claude は stateless investigator**（状態を持たない調査役）。
- Taka の RAW 入力を `submit.py` が受け、DS（対話状態）→ RRI（要求解釈）→ EGL（根拠付け・admission）→ DW（実行）と流し、継続ループで閉じる。
- 各系のロジックを他系に import せず、**データ契約パケット**でつなぐ。すべての field は解決可能な id に裏打ちされ、解決できない id は「穴」として扱う（memory から埋めない）。
- **根拠なし claim 不可**（EGL 規律）。DW は claim を提案するだけで、admit はしない。executor は自分の証拠を OBSERVED より上に self-promote できない。

**中核の実行シーム（live seam）**:
```
Taka RAW input
  → submit.py                     (DS→RRI→EGL→DW コンダクタ)
    → DS phase0/phase1            (対話状態・継続)
    → RRI request_type/research   (要求解釈・研究シグナル)
    → EGL de_admission/acquisition/self_grounding  (根拠付け)
    → DW create_task (provenance stamped)
  → webui /api/run_next
    → dispatch_once → _machine_registry
      → beta backend under alpha  (live_worker_runtime.make_dw_coding_actor)
        → QwenWorker(:8005, supervised)  (実 Qwen が1ファイル変更)
        → 実 subprocess test → Judge/Adjudicator
      → return_loop.complete_and_close  (DW→EGL→RRI→DS でループ閉じ)
  ⛔ AUTO_COMMIT_FORBIDDEN — commit は必ず Taka
```

**リポ topology（5独立 private repo）**:

| repo | 役割 | .py | 現在の活性 |
|---|---|---|---|
| `twoder` | 中核コンダクタ・実行系・UI・off-ramp | 163 | 最活発（DE-0324/0325、2026-07-15） |
| `egl` | Epistemic Grounding Layer（根拠系） | 126 | DE-0330、2026-07-14 |
| `rri` | Request Resolution & Research Intent（解釈系） | 29 | DE-0194、2026-07-12 |
| `dev-workcell` | 実行系（DO）・決定論ゲート付き state machine | 29 | DE-0324/0325、2026-07-15 |
| `ds` | Dialogue State & Continuity（対話状態） | 6 | 最小、Phase0+Phase1 slice のみ、2026-07-06 |

ランタイムログは全リポで直近まで書かれている（`ds/ds_events.jsonl` 534行 / `rri/rri_records.jsonl` 300行 / `dev-workcell/events.jsonl` 163行、2026-07-15）。→ **3役割系すべてが実際に稼働（aspirational ではない）**。

---

## 2 · LIVE 機能（今、実際に走る）

### 2.1 コンダクタ・継続ループ（twoder）

| 機能 | 何をするか | entry-point | 根拠 |
|---|---|---|---|
| **直接入力コンダクタ** | Taka RAW 入力を DS→RRI→EGL→DW→継続ループへ。request-type で分岐（OBSERVE/BUILD_CAPABILITY/RESUME/dead-approach/ambiguous-quant）、DW CREATE パケットに解決可能な provenance を刻む | `submit.py:submit()` | ~110 `SUBMIT-*/TASK-2DER-*.trace.json` in `runs/`；webui import；FAIL-001/002 が実欠陥回収 |
| **Operator ループ** | SAFE 作業を自律前進、authority 境界でのみ Taka に聞く。read-only baseline+状態更新、gated 実験を1件提案（実行はしない）。DW MACHINE ops を dispatch loop で自動前進、conformance mismatch で HALT | `operator.py:advance()` / `advance_dw_machine_ops()` | `/api/operator/advance`；`runs/gpu_experiment/*` が実行 artifact |
| **Runtime Supervisor** | 単一 :8005 呼び出しの回復エンベロープ。決定論的 failure 分類（finish_reason=length⇒RESOURCE、execution ではない）、段階的回復（token予算 2048→12288）、全試行を Execution Event 記録。worker+auditor 共通アダプタ | `runtime_supervisor.py:run_with_recovery()` / `supervised_text_call()` | commits `32bc77d`/`e0321c3`/`674fbee`（PHASE-2DER-AC-01） |
| **Live-worker runtime（beta under alpha）** | 実行する最小 live ループ: approval token→task packet→sandbox→1ファイル変更→**実** subprocess test→Judge→EGL証拠→**commit提案**。`AUTO_COMMIT_FORBIDDEN`。HARD DISPATCH INVARIANT 強制 | `live_worker_runtime.py:run_minimal_slice()` / `make_dw_coding_actor()` | `4c4b5bd`「first real-Qwen slice OBSERVED end-to-end on :8005」 |
| **Qwen live worker** | :8005 の Qwen3.6-35B-A3B に関数を書かせ、fenced code を抽出、1ファイル変更。`supervised=True` で Runtime Supervisor 経由 | `qwen_worker.py:QwenWorker.run()` | counterfactual_runner/webui `_machine_registry` が使用 |
| **Dispatch provenance invariant** | raw→DS→RRI→EGL→DW 由来でない live dispatch を機械的に拒否。解決可能な dw/ds/rri id + trace_id を検証、path-only 拒否 | `dispatch_provenance.py:verify()` | `2bb9a36`(DE-0302)/`ca9cce1`(DE-0307 FULL_2DER_E2E_PROVEN) |
| **Canonical ID resolver** | 2DER 発行の全 id を所有ストアの実レコードへ解決（UTT/DEV→DS, TASK→DW, DE→EGL, RREQ/RINT→RRI…）。解決不能 id = 穴 | `ids.py:resolve()` / `all_resolve()` | dispatch_provenance の解決基盤 |
| **Return loop** | 結果の継続性を Claude でなく 2DER が担う。DW RESULT→EGL admit/reject→RRI residual→DS thread 更新。DW 完了 GATE を bypass せず駆動 | `return_loop.py:close_loop()` / `complete_and_close()` | webui 連結；counterfactual の唯一 EGL admitter |

### 2.2 ゲート・authority・retention（twoder）

> **パターン確認**: live ループに触れる **retention/gate** 系は LIVE、**detection/audit-panel** 系は ORPHANED か harness-only。これは DE-0159「retention > detection」の実証と一致。

| 機能 | 何をするか | entry-point | 根拠 |
|---|---|---|---|
| **Authority policy** | 全 operator action を AUTO_EXECUTE / REQUIRES_APPROVAL / AUTO_ROLLBACK に分類。(task_id, operation_class) スコープの単回使用 approval token を発行・検証・burn | `authority.py:gate/grant_approval/consume_approval` | operator/webui 承認フローで稼働；最広の importer |
| **Intervention 記録** | anomaly/conformance HALT を DS ストリーム上の `INTERVENTION` イベントとして記録（新 SoR を作らない）。detected/assessed/approved/executed_by を分離 | `intervention.py:record_intervention` | operator の実 anomaly で呼ばれる |
| **Failure resource precheck** | worker/Qwen 失敗時、10 の決定論シグナル（timeout/oom/truncation…）で「resource 失敗か?」を判定、EXECUTION/DESIGN への誤ラベルを block。LLM 不使用 | `failure_resource_precheck.py:precheck/route_guard` | runtime_supervisor に配線 |
| **Tier-2 reference oracle** | 決定論 tier が分離できない assertion レベル test 失敗で、独立 Qwen 再実装を生成し test を実行。reference pass⇒CODE_DEFECT、reference も fail⇒ORACLE_DEFECT。**Claude fallback OFF** | `reference_oracle.py:make_reference_fn` | **最新 HEAD `aba08f5`**；DISPOSE で稼働、`DW_ADJUDICATOR` flag |
| **Dep-flag registry（off-ramp flags）** | off-ramp flag 集合を依存グラフ付き registry として機械化。flag status は evidence+deps から**導出**（assert しない）。唯一の正規 writer が counterfactual bundle を flag に bind（status は書かない、approver は "taka" 厳密） | `dep_flag_registry.py:effective_status/bind_flag_evidence` | Phase-11 workstream F `ee7e1a4`；`OFFRAMP_FLAGS_v1.json` 実在。**全 flag UNMET を導出で維持** |

### 2.3 取得・登録・読み取り面（twoder）

| 機能 | 何をするか | entry-point | 根拠 |
|---|---|---|---|
| **RRI→EGL source-traced acquisition** | RRI 研究シグナルを実 EGL `ACQ_GITHUB_SEARCH/ISSUE/HTTP_STATIC` へ。各結果が ACQ/SRC/FINDING id 付き RawObservation に。403/challenge/empty は retrieval_failures（invented finding なし） | `research_acquisition.py:run_research_acquisition` | `submit.py:272` で稼働；`88240f9` |
| **Edge-5 実験候補生成** | source-traced findings を、全 field が解決可能 id を引く DW 再現候補へ。claim ceiling=REPRODUCTION_ONLY。PLAN barrier のみで DW task 作成（dispatch しない） | `experiment_candidate.py:build_candidate` | `submit.py:298` |
| **Qwen BUILD_CAPABILITY PLAN actor** | 決定論 plan_template が計画できない BUILD task で、Qwen に構造化 PLAN を書かせ fail-closed 検証（schema/provenance/sandbox/tests/no destructive）。CREATED→PLAN barrier を埋める | `build_planner.py:make_dw_planner_actor` | `webui.py:306` の `BUILD_PLANNER` actor；`28fefa9`。※rejected plan は Claude barrier にフォールバック |
| **Management packet + coverage matrix** | id 裏打ちの 2DER 状態パケット（repo HEADs・registry 件数・最新 DE/CHG・未登録変更ファイル検査・能力 coverage matrix）を記録から生成（memory からでなく） | `management_packet.py:build/coverage_matrix` | DE-0181「実装前に print」規律；実 registry を読む |
| **Roadmap registry** | append-only id 裏打ち roadmap（ROADMAP/PHASE/ITEM/AMENDMENT）、依存（depends_on→DONE まで BLOCKED）、evidence/task/DE リンク | `roadmap_registry.py:register_item/resolve` | `ROADMAP_REGISTRY.jsonl` 308KB、2026-07-15 |
| **Artifact registry + change log** | anti-amnesia ストア。安定 `ART-<sha1>` が解決しない限り substantive file を使用/変更/引用できない。append-only、rename でも id 維持 | `artifact_registry.py:register/resolve/record_change` | `ARTIFACT_REGISTRY.jsonl`（3.7MB）+`CHANGE_LOG.jsonl`、2026-07-14 |
| **Historical velocity / Foundation forecast（読み取り面）** | git commit 時刻から実測 velocity（median/p50/p80/p95、per-session throughput）。forecast は「残り作業＋期待セッション数」を返す（日付は返さない）。薄い履歴⇒UNKNOWN-VARIANCE | `historical_velocity_calculator.py` / `foundation_forecast_report.py` | `control_surface_read`→webui dashboard に配線 |

### 2.4 EGL が 2DER に供給する LIVE 能力（egl）

| EGL 能力 | 2DER 統合点 | 根拠 |
|---|---|---|
| **DE ledger admission**（`de_admission`）— `DESIGN_EVIDENCE_LEDGER` の唯一の正規 writer。schema 強制、HARD_REJECT claim ceiling（self-improvement/proven-correct/guaranteed…）、unbacked BEHAVIORAL_PROPERTY を ADMITTED→REPORTED に降格。Claude の手動 jsonl append を置換 | `submit.py`, `live_worker_runtime.py:129` | ledger 327エントリ/DE-0330 |
| **Evidence-class promotion + SoR routing**（`egl_integration`）— ladder REPORTED<INFERRED<OBSERVED<MEASURED<REPRODUCED<ACCEPTED。executor は OBSERVED 超えの self-promote 不可、ACCEPTED/CONTRADICTED は INDEPENDENT-JUDGE のみ。全 stage を既存 SoR へ（新ストア禁止 DE-0223） | domain/audit/temporal 統合、parallel_router | hermetic 決定論 |
| **SELF_GROUNDING**（`self_grounding`）— EGL 自身の corpus（DE ledger+REVIEW_LEDGER+audit_backlog）から query に構造化回答（answer/historical/open_gaps/source_trace）。設計決定の記録≠実装真実 | `submit.py:177` step 3a（実 Qwen :8005） | JREV-0006 |
| **Semantic Acquisition Boundary**（`acquisition`+`source_policy`）— 「根拠なし claim 不可」の取得規律。LegIntent→AcquisitionRun（transport≠content status）→RawObservation+Source Qualification。coverage は「観測が required に一致」であって「fetch 成功」ではない。RD は leg を COMPLETED にできない | `research_acquisition`, `submit`, `*_inspection`, `experiment_candidate` | **LIVE/PARTIAL**（adapter は first slice） |
| **DW→EGL result-packet reflux**（`result_packet`）— DW RESULT を admission 規律で取り込む。RECORD_OCCURRENCE⇒ADMITTED vs BEHAVIORAL_PROPERTY⇒REPORTED（EGL が独立再実行して初めて VERIFIED）。DW 自己申告の test 結果を auto-promote しない | `return_loop`, `live_worker_runtime`, `submit` | live worker の唯一の DW 完了 reflux |

### 2.5 役割系 LIVE（ds / rri / dev-workcell）

- **DS**: `phase0`（発話/イベント append-only ログ）は毎 submit で LIVE。`phase1`（対話再構成・参照解決、Qwen3.6）は LIVE だが**弱い/PARTIAL**（短い対話 ≤14ターンでは net-negative、length 依存、GAP-DS-2 未解決）。継続境界の失敗を正直に記録（「前の件」= Claude Code 経由で起きたため DS に無い→解決不能）。
- **RRI**: routing の中心。`context_binding`/`request_type`/`research_signal`/`admission_request`/`preflight_gate`/`intent_record` が全て hot path で LIVE。`request_type` が全 routing を駆動（DE-0156 fix）。`preflight_gate` は HBB-30 ambiguous quantitative claim を DW/acquisition 前に HOLD。
- **DW（dev-workcell）**: 最も重く稼働。event-sourced workcell + **決定論 Python ゲート**（COMPLETE 前に独立 audit を構造的に強制、F1: generator≠auditor、F4: DW は admit しない）。`dispatch`（継続ループ）、実 Qwen coder(seed7)+auditor(seed101 supervised)、`executor`（実 subprocess）、`adjudicator`（3-tier: 決定論+reference-oracle+Claude-slot OFF）、`conformance`、scoped dispatch token 全て LIVE。**counterfactual（Claude 不在）モードでも実稼働**。

---

## 3 · PARTIAL 機能（動くが gated / 未配線 / データなし）

- **Counterfactual runner**（`counterfactual_runner.py`）: 実 Qwo(:8005) でフルパスを Claude 不在下で走らせ、実 `ps` snapshot を取り、eligible な時のみ evidence bundle を保存。1件の実 eligible bundle 実在（`cfrun-20260714T051106.json`）。ただし `__main__`（手動/cron）からのみ呼ばれ、flag は UNMET のまま。
- **Execution-event accumulation reader**（`execution_event_log.py`）: DW PROCESS_EVENT 上の read-only 記述的集計（actor×model×task_class×failure_class 層別）。実 corpus 21件あるが `population=SCHEDULED_REPLAY`（baseline 非適格）、cron は `.disabled`。**Phase-2 統計自体は未構築**（DE-0314: まだ捏造するな）。
- **Live-worker scaffold**（`live_worker_scaffold.py`）: sandbox contract/safety detector/judge scope は `run_minimal_slice` から LIVE 呼び出し。ただし `run_scaffold`+`FakeWorker` は hermetic のみ、`LIVE_EXECUTION_ENABLED=False`。
- **Model routing table**（`model_routing_table.py`）: **LIVE だが locked**。readiness 13-flag が全 UNMET（benchmark ledger 不在）のため全 task が §10 default Qwen3.6-35B-A3B に解決。default 変更は readiness 前は構造的に禁止。
- **Economy/benchmark cluster**（`economy_operator`, `economy_decision_ledger`, `benchmark_claim_scope`, `benchmark_run_ledger`, `execution_economy`）: 全て DONE + E2E harness で証明済みだが**live runtime path に未配線、on-disk ledger 不在**（`ECONOMY_DECISION_LEDGER.jsonl` / `BENCHMARK_RUN_LEDGER.jsonl` なし）。measured benchmark が無いのが model routing lock の根本原因。`execution_economy` は単一モデル live path で意図的 NO-OP（co-serve は HW-block DE-0143、sleep-swap は ROLLED_BACK DE-0168/0171）。
- **監査エンベロープ tier**（`change_classifier`, `two_level_audit_policy`, `class_nh_triad_audit`, `weight_independence_policy`, `escalation_router`, `human_escalation_ledger`, `stale_packet_gate`, `failure_classifier_schema/retry_guard`, `unknown_variance_policy`, `independent_judge`, `procedure_audit`）: 全て build 済み・`end_to_end_acceptance_harness.py` で **35/35 AC 証明済み**。ただし harness（一回限りの証明装置）からのみ呼ばれ、**live webui/operator/runtime_supervisor path には未到達**。→ built+proven だが production 未配線。
- **Completion-definition registry / flag gate**: live CSR dashboard に配線されているが、backing ledger（`COMPLETION_DEFINITION_REGISTRY.jsonl`）が空/欠落 or 空 bindings で呼ばれるため production では実質 no-op。
- **EGL Gate4**（`egl/gates`+`judge` の実 adjudication）: EGL 内では LIVE。live :8005 adjudication は approval token（`EGL_GATE4_JUDGE`）で gated。ただし twoder 側 wrapper `gate4.py:gate4_admit` は**継続 submit ループから呼ばれていない**（配線済み・approval-gated だが default hot path 外）。
- **RRI formal validator suite**（`rri_formal.py`）: `submit.py:98` に配線されるが、caller が `formal_candidates` を渡さない限り SKIP（default None）。全 validator は決定論・hermetic。
- **Temporal / domain / role スキーマ群**（`temporal_event_schema`, `time_binding_validator`, `estimation_basis_binding`, `temporal_egl_integration`, `domain_specialization_schema`, `domain_egl_integration`, `role_schema`, `assumption_extractor`, `knowledge_packet_provenance`, `interface_contract_schema`）: DONE の schema/validator ライブラリ。audit 層と E2E harness が消費するが standalone runtime loop なし。

---

## 4 · CLOSED（死んだ枝・負の結果）

`STATE.md` closed-branch リスト × DE ledger `decision` field で確認。これらは「機能」ではなく閉じた探索：

| DE | 決定 | 意味 |
|---|---|---|
| DE-0031 | CLOSE_PHASE_1A / OPEN_PHASE_1B | EGL Phase 1a 閉 |
| DE-0071 | CLOSE_ODF | ODF 枝閉 |
| DE-0086 | SLEEP_MODE_NOT_VIABLE_LOCALLY | sleep-mode ローカルで不可 |
| DE-0101 | 6_OPERATORS_CANDIDATE_SEALED | operator-set sealed（未追求） |
| DE-0112 | ENGINE_NO_ADDED_VALUE_OVER_SKEPTICISM_SEALED | reasoning「engine」は汎用懐疑以上の価値なし |
| DE-0114 | DEMOTE_SINGLE_AXIS_REACH_PROMOTE_2DIM | single-axis reach 降格 |
| DE-0115 | HBB_BRANCH_CLOSED_CANDIDATE | HBB reconstruction 枝閉 |
| DE-0122 | DOWNGRADE_TO_CAPABILITY_EXHIBIT | 単なる exhibit へ降格 |
| DE-0127 | CLOSE_PRIMARY_EXHIBIT_CONFIRMED_NARROW | narrow のみ確認 |
| DE-0130 | CLOSE_SCHEDULER_BRANCH_NEGATIVE | scheduler 能力＝負の結果 |
| DE-0133 | DEMOTE_AS_SHAKE_DETECTOR… | salience-shake detector 降格 |
| DE-0134 | RECORD_CENTER_SHIFT_NEGATIVE_AGGREGATE | center-shift は aggregate で負 |
| DE-0135 | DOWNGRADE_R0_LIFT_NOT_A_SIGNAL | R0 lift は signal でない |

**機械強制の DEAD_APPROACH 拒否リスト**（`twoder/failure_memory.jsonl`）— これらは棚上げでなく**新 submit がキーワード一致すると BLOCK される**：

| failure_id | status | approach |
|---|---|---|
| DEAD-scheduler | CLOSED_NEGATIVE | scheduler を live 機構として |
| DEAD-route-vs-repeat | AUDITED_AND_REJECTED | route-vs-repeat を live discriminator として |
| DEAD-afe-detector | WEAK_NEGATIVE | AFE/Formal 構造演算子を live detector として（≤汎用懐疑） |
| DEAD-salience-shake | CONFOUNDED_DEMOTED | ledger salience を live SHAKE detector として |
| DEAD-center-shift | NOT_CONFIRMED | center-shift/attention re-centering を確認された効果として |

---

## 5 · ORPHANED（コードは在るが現行が呼ばない）

`RESTORATION_STATUS.md` の権威ある宣言：
- **reasoning/detection evolution（07-08…07-10 の作業）→ ORPHANED、意図的に非復活**（DE-0159 retention>detection を根拠）。
- `egl/experiments/{afe,scheduler,formal,hbb}` = class **D**（closed-negative/orphaned）。
- `egl/autonomy/*` parallel pipeline = class **E**（not live、live path に配線されなかった並列複製）。
- ledger: `VERDICT = C. FOUR_SYSTEM_RESTORED_POST_BASELINE_REASONING_ORPHANED`。

**モジュール単位の ORPHANED**（現行 submit/webui/operator から未参照）:

| モジュール | 何だったか | 状態 |
|---|---|---|
| `twoder/gate4.py` | EGL Gate4 を approval-gated admission gate として wrap | ORPHANED（twoder ランタイム/harness いずれからも呼ばれない） |
| `twoder/dissent_worker.py` | 「これは間違いと仮定、疑わしい3箇所を挙げよ」L2 補助証拠 | ORPHANED（regression test のみ参照。detection 系 scaffolding） |
| `twoder/audit_egl_integration.py` | audit 出力を既存 SoR へ route | ORPHANED（自 test 以外に importer なし） |
| `twoder/human_escalation_packet.py` | 単一決定の §15 human packet | ORPHANED（自 test のみ） |
| `twoder/parallel_router.py` | role_schema 上の固定 state machine router | ORPHANED（acceptance harness のみ import） |
| `twoder/role_schema.py` | Phase-09 role 分離 | ORPHANED（parallel_router + harness のみ） |
| `twoder/domain_specialization_schema.py` | Phase-10 16-domain 軸 | ORPHANED（live path 外の2モジュールのみ） |
| `twoder/ab_harness.py` | 27B vs 35B coder 比較 | ORPHANED（非 test caller なし。live dual-serve 未実行、優位は REPORTED 止まり DE-0215） |
| `twoder/active_work_and_wait_ledger.py` | active-work/tool-wait/human-wait 分割 ledger | ORPHANED（producer が append を呼ばず、ledger ファイル未生成） |

**EGL-internal（2DER に未配線）**: `etb`（Evidence Trust Boundary、prompt-injection scan — acquisition 経由でのみ transitive に届く）、`review_mechanisms`（coverage-sweep / C-TOTALITY 恒久機構 — EGL 内部の完全性機構、twoder 参照なし）、`core`/`pipeline`/`curator`/`esde_stream`（twoder は `ids.py`→`egl.core` の id 発行でのみ触れる）。

---

## 6 · Web UI 面（off-ramp）

**フレームワーク = 標準 `http.server.ThreadingHTTPServer`（Flask/FastAPI ではない）**、class `H`。HTML 2ページ + JSON API。

**サーブ状態（実測）**: `python3 -m twoder.webui 8770` が稼働、`LISTEN 100.107.6.119:8770`（Tailscale-4 IP、memory と一致）。default bind = Tailscale interface のみ（never 0.0.0.0、失敗時 127.0.0.1 fallback）、`TWODER_BIND` で上書き可。**認証 = HTTP Basic Auth（単一ユーザ taka、token は `.access_token` 0600 auto-mint）**。全 GET/POST が `_auth_ok()`→失敗で 401。→ **private tailnet + Basic Auth の2層**。

### GET routes
| path | 機能 |
|---|---|
| `/` | off-ramp workstream-A **read-only dashboard**（日本語）。roadmap tile、forecast、off-ramp flags、直近 DE/CHG、intervention 数、completion banner（CDEF-2DER-v1 未完を正直表示）、pending-approval カード + 「認可token発行」ボタン |
| `/command` | legacy submit / RUN NEXT UI。footer 自身が「live worker 未接続、まだ機能しません」と表示 |
| `/api/tasks` | DW event log から distinct TASK id |
| `/api/state` | 完全な派生 DW 状態 view（goal/dw_state/next op/actor/claude_barrier/DS/RRI/EGL、failure-memory 一致・guard block） |
| `/api/claude_packet` | Claude actor barrier 用 bounded packet |
| `/api/roadmap`, `/api/resolve`, `/api/control`, `/api/pending_approvals` | read-only（roadmap / id 解決 / 生 report JSON / pending 承認キュー） |

### POST routes
| path | 機能 |
|---|---|
| `/api/approve` | scoped 単回 approval **token** 発行。`approved_by` は認証 `taka` に固定（client body から取らない）。**token は認可のみ、何も実行しない** |
| `/api/submit` | 実 direct-entry path（Taka→2DER）。DS→RRI→EGL 実行、atomic trace 書込、run-gate 公開 |
| `/api/run_next` | DW op を1つ前進（machine registry 経由）。hard backend gate（前 submit が blocked/非 runnable/task 不一致なら拒否）→`AUTH.gate("DW_MACHINE_DISPATCH")`。完了 gate で `PROPOSE_COMPLETE`+ループ閉じ |
| `/api/run_until_barrier` | 同 gating で次 barrier まで |
| `/api/ingest` | bounded Claude-actor 結果（PLAN/DISPOSE/UPPER_REVIEW）を DW へ ingest |
| `/api/operator/advance` | operator ループ（AUTO safe read-only + 1件 gated 実験） |

**UI から出来ること**: (1) 全 observe、(2) 実 DW pipeline へ submit、(3) DW task を machine registry で advance（Qwen coder/auditor/manager、`DW_MACHINE_DISPATCH` で gated = compute のみ、live-service mutation なし）、(4) scoped approval token 発行。**出来ないこと**: token を consume/execute させること — approve ボタンのラベル自身が「押しても実装/benchmark は走りません（トークンを消費する実行系は未配線）」（`2f6168b` で "authorization-only, no execution" に再ラベル）。

---

## 7 · Authority / autonomy posture（明確に）

> **auto-commit = 禁止。autonomous RD = 未有効。commit 主体 = Taka（人間）。UI = authorize-only, not execute。**

- `live_worker_runtime.py:16` — `AUTO_COMMIT_FORBIDDEN = True`（hard invariant、この runtime は決して commit しない）。commit 提案のみ。commit subject に繰り返し「(auto-commit forbidden)」。
- `autonomous_git.py:14` — `AUTONOMOUS_GIT_ENABLED = False`（policy: commit=Taka、有効化には記録された Taka policy 決定 DE+CHG が要る）。append-only ledger のみ scope 内、code/docs は人間のみ。**built-but-DISABLED gate**。
- 直近 DE（0326–0330）が繰り返し「Claude fallback OFF / 0 起動」を記録 — adjudication tier は Claude を live judge として呼ばない。
- `authority.py` — `AUTO_EXECUTE`（read-only: inspection/log読/nvidia-smi/health/regression/analysis/DW compute dispatch）と `AUTO_ROLLBACK` のみ無許可で走る。全 mutation は単回・human-scoped approval token 必須。
- **net**: read-only inspection と compute-dispatch は自律、全 mutation・live 実験・全 git commit は human 単回承認 token の後ろ、commit authorship は Taka。autonomous-commit と Claude-senior-judge は code に在るが flag-disabled（記録された Taka policy 決定待ち）。

**off-ramp 全体判定**: reporting(A) と approval-token 発行(B) は真に LIVE で :8770 に tailnet+BasicAuth 越しに serve、live-worker ループ(D) は実 Qwen slice OBSERVED。**しかし interface transfer は未完**: **9 flag 全 UNMET**、token-consuming executor 未配線、autonomous git は定数で DISABLED、`LIVE_WORKER_MINIMAL_PASS` は Claude が loop に居る限り構造的に達成不能（counterfactual gate, spec §7 — 認証には (1) Claude Code を閉じ (2) worker を完全無人で走らせる、が必要）。4窓（report/approve/git/implement）は observe+authorize では部分 LIVE だが、**実行と git commit は Taka/Claude に残る**。コードも UI も自らこれを正直に表示。

---

## 8 · 現在の作業スレッドと未所有項目

**現在の作業焦点**: **test-failure adjudication 系列（DE-0323–0330）** — tier-2 `reference_oracle.py` を DISPOSE に配線（最新 commit）、Claude fallback OFF。直前に着地: runtime_supervisor 段階回復（DE-0311–0315）、execution_event_log Phase-2 accumulation reader、build_planner Qwen PLAN actor（DE-0309/0310）。claim ceiling: DE-0324 `DESIGN_REGISTERED_ONLY`→0325 `MECHANISM_IMPLEMENTED_NOT_ACTIVATED`→0326 `ACTIVATION_OBSERVED`→0327 `CLASSIFICATION_IMPROVED`→0329/0330 `TEST_FAILURE_ADJUDICATION_LIVE_PATH_PROVEN`。**効果（false-JR を減らすか）はまだ claim していない**。

**STATE.md 決定キュー（stale だが唯一の構造化キュー）**: `TAKA_AUTHORITY_RECLASSIFICATION`（DO_NOT_ASK, AE-00003）、HBB replay の m1_grounding_fail ×2（HBB は CLOSED 枝 DE-0115、低優先残渣）、`spec_stale`。**適用済み Taka correction: なし**。

**UNOWNED 項目**: Attention Center、same-object tension binding、structural re-centering、local Aruism operational regime、**end-to-end self-operation**。所有者・live 機構なし。

**主要な未認証（設計上）**: `LIVE_WORKER_MINIMAL_PASS` は設計上 UNMET のまま。認証には Claude Code を閉じ worker を完全無人で走らせる必要。それまで live-worker path は「OBSERVED end-to-end」だが自律認証はされていない。

---

## 9 · この資料の限界（正直な範囲）

- 本資料は **現行機能インベントリ**であり、全 ~350 モジュールの逐一リファレンスではない。ORPHANED/CLOSED は代表を挙げたが網羅ではない。
- 各機能の分類は 2026-07-15 時点のコード読解に基づく。DE-0330 以降 / 新 commit で変わり得る。
- ファイル・function・DE 番号を引いた箇所は、推奨/参照前に現存を再確認すること（memory 規律）。
- 権威ある状態一次情報の順: `egl/DESIGN_EVIDENCE_LEDGER.jsonl`（DE truth）> `twoder/audit/RESTORATION_STATUS.md` > 本資料 > （STALE: STATE.md, 2DER_TECHNICAL_SPECIFICATION.md）。
