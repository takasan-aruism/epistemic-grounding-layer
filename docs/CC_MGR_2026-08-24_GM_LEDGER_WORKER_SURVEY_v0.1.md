# GM / Ledger Worker 構成調査 v0.1（ITEM-2DER-EVO-0100）

- **種別**: 調査報告。**実装0行**。**Taka 裁定待ち**。
- **担当**: Claude(MGR)
- **測った日時**: 2026-08-24 05:29〜06:0x
- **測ったHEAD**: ds 79b9c2e / rri 7d1c819 / egl 45c02b2 / dev-workcell 984dcea / twoder e12c261
- **調べ方**: 先に 2DER 自身の読み口（`/api/gap_report` `/api/ledger_rows` `/api/control` `/api/resolve` `/api/accounts` `/api/ledgers`）から引き、**不足した所だけ**ソース構造へ降りた。**数字は文書から写していない。全部この場で測った。**

---

## 0. 先に確定させた重なり（新しい物を作る前に）

**ITEM-2DER-EVO-0099「GDW運用設計 — General/Domain/Worker の3層へ寄せる」が 2026-08-24T05:00 に起票済み**で、§14 の全件調査を既に持つ。その逐語の結論：

> GDW は新規構造ではない。G→D の3層は DW Domain で既に成立（`domain_dw`・EVO-0073）。`to_domain` は汎用。新規実装が必要なのは (A) ESDE Domain Manager 本体 (B) Worker が結果を明細へ戻す1段 の2点だけ。

**∴ 本調査は3層構造そのものを調べ直していない。** 差分は Domain が ESDE ではなく **Ledger（台帳・明細）** である点だけ。以下は Ledger Domain 固有部分の実測である。

---

## 1. 現在の実構成（測った物だけ）

### 1-1. 常駐しているもの（systemd --user・全部 active）

| service | 中身 | 判断の持ち主 |
|---|---|---|
| `twoder-webui.service` | front door :8770（唯一の口） | — |
| `twoder-manager.service` | Manager v0（General）。60秒巡回 | `twoder/manager_decide.decide_tick`（2DERが書いた） |
| `twoder-route-worker.service` | Route Worker（経路表を実態に合わせ続ける） | — |

`domain_dw`（Domain Manager／DW）は**常駐ではなく** `manager_v0` から呼ばれる形で在る（G→D の入口4つ：`contract_with_precheck` / `submit_next_contract` / `receive_finished` / `record_stages`）。

### 1-2. 台帳（front door `/api/ledgers` が返した41本のうち主要なもの）

| 台帳 | 行数 | 役割 |
|---|---|---|
| `ds/data/event_trace.jsonl` | 1,966,453 | ETRACE（実行の痕跡・ESDE の SoR） |
| `rri/rri_records.jsonl` | 8,672 | RRI 記録 |
| `egl/data/events.jsonl` | 28,117 | EGL |
| `dev-workcell/events.jsonl` | 4,792 | DW（実装ループ） |
| `twoder/audit/ARTIFACT_REGISTRY.jsonl` | 4,547 | ART |
| `rri/rri/rthread_events.jsonl` | 3,371 | **明細（本調査の主対象）** |
| `twoder/audit/ROADMAP_REGISTRY.jsonl` | 2,914 | ITEM / PHASE |
| `twoder/audit/CHANGE_LOG.jsonl` | 303 | CHG |

**★不一致1件**: 状況表は「登記簿 56本」と言うが `/api/ledgers` が **readable として返すのは41本**。差15本の所在は本調査では追っていない（**測っていない**）。

---

## 2. Claude が現在 手作業している仕事（分母つき・全部この場で測った）

### 2-1. ★最も強い数字 — ITEM 台帳の記帳

`twoder/audit/ROADMAP_REGISTRY.jsonl` の unique 3,000行（ITEM 2,972 / AMENDMENT 17 / PHASE 10 / ROADMAP 1）。`status_note` が在るのは **2,734 / 3,000 = 91.1%**。その `actor=` の分布：

| actor | 件数 | 割合（actor 欄が在る 2,411件中） |
|---|---|---|
| MGR | 1,212 | 50.3% |
| Claude | 1,113 | 46.2% |
| Claude(MGR) | 2 | 0.1% |
| Taka | 84 | 3.5% |
| **2DER** | **0** | **0.0%** |
| （actor 欄が無い） | 323 | — |

> **★ITEM 台帳への記帳を 2DER が書いた実績は 0件である。** MGR も Claude も同じ人格（Claude Code）∴ **Claude系 2,327 / 2,411 = 96.5%**。

**★併せて観測した欠陥**: `next=` 欄が無い記帳が **550 / 2,734 = 20.1%**。機械は手番を読めない（状況表の「待ち=?」の正体）。

### 2-2. 明細（rthread）への書き込み

front door `/api/ledger_rows` で 3,500行取得、重複を落として **unique 3,394行**。

event_type の内訳：

| event_type | 件数 | 何をしている段か |
|---|---|---|
| QUESTION_TYPED | 1,847 | 段0（種別・原文・位置） |
| QUESTION_ACCOUNT_ASSIGNED | 646 | 段5（勘定科目の割当） |
| QUESTION_ANNOTATED | 253 | 注記（段） |
| QUESTION_RAISED | 250 | 明細の起票 |
| QUESTION_ACCOUNT_PROPOSED | 173 | 科目の提案 |
| THREAD_OPENED | 140 | スレッド開始 |
| QUESTION_EVIDENCE | 40 | 段4（根拠） |
| ACTOR_RECORDED | 39 | 誰が書いたか |
| QUESTION_DISPOSED | 5 | 処分 |
| STATE_ADVANCED | 1 | 状態遷移 |

distinct: typed_id **1,181** / question_id **755** / thread_id **473**。

**書き手（`recorded_by` が在る 686行が分母）**：

| recorded_by | 件数 | 割合 | 主体 |
|---|---|---|---|
| `MGR.backfill` | 619 | 90.2% | **Claude が手で叩いた** |
| `Claude Code (MGR)` | 31 | 4.5% | **Claude が手で渡した文字列** |
| `MANAGER_V0.feedback_one` | 22 | 3.2% | 機械 |
| `MANAGER_V0.tick` | 13 | 1.9% | 機械 |
| `ESDE_WORKER` | 1 | 0.1% | 機械 |

> **★機械 36 / 686 = 5.2%。Claude 650 / 686 = 94.8%。**

**`recorded_via`**: `direct` 651 / `front_door` 35 → **94.9% が front door を通っていない**。

### 2-3. ★「手作業」であることの機械的な裏づけ（推測していない）

`twoder/wiring_state_rederive.reachable_set()` を**今日のソース**で回し、生きた入口（`webui` / `manager_v0` / `route_worker` / `submit` / `senior_review`）からの推移閉包を取った：

- `twoder/*.py` 総数 **274**
- 到達可能 **137**（50.0%）
- **到達不能 137**（50.0%）— うち試験から参照 50 / 試験からも参照されない 87

そのうえで、619行を書いた `detail_backfill` を追うと：

```
detail_backfill  ← 非試験の呼び手は twoder/task_similarity.py の1本だけ
task_similarity  ← 非試験の呼び手は 0本（自分の試験のみ）
∴ 生きた入口から detail_backfill へ到達する経路は 0
```

`detail_backfill.apply_backfill` の既定値が逐語 `recorded_by="MGR.backfill", recorded_via="direct"`。**∴ 619行は、入口を通らずに Claude が端末から直接叩いて書いた。** これは推測ではなく、呼び手の全走査と既定値の逐語による。

---

## 3. 明細・勘定科目の再測定（`/api/gap_report?include=details,esde`・elapsed 26.6秒）

**古い報告値は1つも転載していない。**

| id | 区分 | 分子/分母 | % | 意味 |
|---|---|---|---|---|
| ACCOUNT_UNCLASSIFIED | NOT_WIRED | 149 / 1,031 | 14.5% | 科目が付いていない明細 |
| ACCOUNT_NOT_DECIDED | NOT_WIRED | 687 / 691 | **99.4%** | 科目の提案が裁定されていない |
| DETAIL_NOT_ASSIGNED | NOT_WIRED | 387 / 1,031 | 37.5% | 科目未割当（割当済 644） |
| DETAIL_NOT_DISPOSED | NOT_WIRED | 1,026 / 1,031 | **99.5%** | 処分されず開いたまま（処分済 5） |
| EVIDENCE_ON_DETAIL | NOT_WIRED | 1,004 / 1,031 | **97.4%** | 証拠が明細に戻っていない（付与済 27） |
| DETAIL_TEXT_TRUNCATED | BROKEN | 299 / 1,062 | 28.2% | 原文が200字で切れている |
| ANNOTATION_PHASE_OFF_MENU | BROKEN | 471 / 985 | 47.8% | 注記の段が語彙表に無い |
| DETAIL_TO_ARTIFACT_EDGE | NOT_WIRED | 28本の辺 | — | ART-3 / ETR-24 / ITEM-0。明細1件まで絞れたのは 2 |
| FINDING_TO_DETAIL_EDGE | NO_RECORD | 0 | — | finding 専用の欄が無く 実績も0 |
| ESDE_NOT_EVALUATED | NO_RECORD | 2 task | — | ESDE 評価が付いた task は2件 |
| BRANCH_VERSION_SURFACE | NOT_WIRED | 0 | — | branch/version が front door の口に出ていない |

区分の合計: **NO_RECORD 2 / NOT_WIRED 7 / BROKEN 2**。

### 3-1. 段0（種別）の中身 — 分母 1,847

| kind | 件数 | % |
|---|---|---|
| **UNVERIFIED** | 859 | **46.5%** |
| FACT | 303 | 16.4% |
| CHANGE | 239 | 12.9% |
| CONSTRAINT | 188 | 10.2% |
| SPEC | 138 | 7.5% |
| TEST | 91 | 4.9% |
| GOAL | 29 | 1.6% |

`kind_basis` は `none` 859（= UNVERIFIED と同数）/ `section` 519 / `cue` 328 / `cue_over_section` 128 / `cue_tail_constraint` 13。
> **∴ 決定論の抽出器が決められなかったのが 46.5%。ここが「LLM を使うか」の分岐点である。**

### 3-2. 段5（科目割当）の根拠 — 分母 646

| basis | 件数 |
|---|---|
| `LEDGER_ACCOUNT_TREE rev 614241f6…` | 644 |
| 訂正の実証 | 1 |
| 取消の実証 | 1 |

> **★科目の割当は既に決定論である**（勘定科目ツリーを引くだけ・LLM 非経由）。**LLM が要るのは「提案」の側だけ**であり、その提案は次のとおり全部止まっている。

### 3-3. 科目提案の verdict — 分母 173（この台帳内）

`NOT_DECIDED` **173 / 173 = 100%**。gap_report の広い分母では 687/691 = 99.4%。
> **提案→裁定 の辺が繋がっていない。** 承認の口（`approve_account`）は LIVE だが、**提案を裁定する側の呼び手が居ない。**

### 3-4. 証拠（段4）— 分母 40

`basis_kind`: `LOCAL_MEASUREMENT` 38 / `LOCAL_CODE_OBSERVATION` 2。

### 3-5. 注記の段 — 分母 253

実際に入っている語: PROCESS_EVENT 96 / NOT_DECIDED 55 / PLAN 50 / GENERATE 32 / AUDIT 17 / DISPOSE 2 / UPPER_REVIEW 1。
`annotate_gate.PHASE_MENU` は PLAN/GENERATE/AUDIT/DISPOSE/REGENERATE/UPPER_REVIEW。
> **PROCESS_EVENT と NOT_DECIDED の 151件（59.7%）はメニューに無い語。** 語彙表と実際の書き込みが割れている。

### 3-6. user が書いた明細と RRI 生成の区別 — 分母 292（`actor` 欄が在る行）

| actor | 件数 |
|---|---|
| MANAGER | 106 |
| NOT_DECIDED | 69 |
| CODING_WORKER | 62 |
| claude-mgr | 36 |
| INDEPENDENT_AUDITOR | 16 |
| **TAKA** | **2** |
| AI_CONSULT_QWEN | 1 |

> **人（Taka）が直接書いた明細は 2件。** 区別する欄は在り機能しているが、**母数がほぼ無い**。

---

## 4. 「できる／繋がっていないだけ／本当に無い」の分離（調査2の本体）

### 4-1. 明細 API ごとの 非試験の呼び手（全走査・作用で探索）

| API（正本 = `rri/rri/request_thread.py`） | 非試験の呼び手 | 生きた入口から到達するか | 結果の実測 |
|---|---|---|---|
| `raise_question`（起票） | `twoder/submit.py`, `webui.py`(/api/rthread_add), `egl/structure/s_esde_evaluate.py`, 監査script 2本 | **○ LIVE** | 250件 |
| `annotate_question`（注記） | `submit.py`, `case_table_annotate.py` | **○ LIVE** | 253件 |
| `propose_account`（科目提案） | `submit.py` | **○ LIVE** | 173件 |
| `record_evidence`（証拠） | `detail_feedback.py`, `s_esde_evaluate.py` | **○ LIVE** | 40件 |
| `record_actor`（書き手） | `webui.py`, `s_esde_evaluate.py` | **○ LIVE** | 39件 |
| **`record_typed`（段0 種別）** | **`detail_backfill.py` のみ** | **× 到達不能** | 1,847件（全部 手動） |
| **`assign_account`（段5 科目）** | **`detail_backfill.py` のみ** | **× 到達不能** | 646件（全部 手動） |
| **`dispose_question`（処分）** | **`egl/docs/audit_rthread_stage*.py` の2本のみ**（`gap_report` と `requirement_gaps` の出現は**散文であって呼び出しではない**・逐語確認済） | **× live path 0** | **5件** |

> **★これが「99.5%が処分されていない」の機械的な原因である。** 機構は在る。**処分を呼ぶ生きた経路が1本も無い。**

### 4-2. Ledger Domain の部品ごとの接続状態（今日のソースで再計算）

**LIVE（入口から到達）**: `account_gate` `account_tree` `account_candidates` `approve_account` `detail_feedback` `requirement_gaps` `requirement_structure` `gap_report` `gap_table` `gap_streak` `is_known_verdict` `stage_from_evidence` `annotate_gate` `classify_changes` `manager_v0` `manager_decide` `route_worker` `domain_dw` `build_planner` `qwen_worker` `escalation_router` `get_domain` `live_worker_runtime` `live_worker_scaffold` `tasks_to_enqueue` `requeue_decision` `authority` `authority_rules` `authority_summary` `artifact_registry` `roadmap_registry` `ids` `submit` `webui` `supersede_seal` `contract_seal` `progress_seal` `merge_progress`

**TEST_ONLY（試験だけが参照）**: `detail_backfill` `detail_refs` `change_classifier` `parallel_router` `dissent_worker` `task_similarity`

**未接続（試験からも参照されない）**: `register_account_axis` `record_account_experience` `split_symbol_details` `dispose_decision` `classify_items` `unresolved_rollback` `resolve_dispatch` `wiring_state_rederive` `acceptance_path_check` `file_census_layer_a` `file_census_qwen` `file_census_sort`

**本当に無いもの（実測で名指しできたのは1件だけ）**:
- 明細に **finding 専用の欄** が無い（`record_evidence` の欄は evidence_id / question_id / evidence_refs / basis_kind / validation_mode / source_span / evidence_text。finding を入れること自体は `evidence_refs` でできるが**実績0**）。

> **★結論: 「本当に無い」はほぼ無い。ほぼ全部が「在るが呼ばれていない」である。**

---

## 5. authority（調査6）

### 5-1. 既存の段は5段ではなく 3×3 である

`twoder/authority.py` の `POLICY` に **24 行**。
- 判断: `AUTO_EXECUTE` / `REQUIRES_APPROVAL` / `AUTO_ROLLBACK`
- 段: `OBSERVE` / `REVERSIBLE` / `IRREVERSIBLE`

`/api/control?include=authority_summary` の実測：
- `by_action`: REQUIRES_TAKA **15** / AUTO_APPROVED **9**（合計24）
- `governed` 24/24、`not_governed` 0
- `by_decision`（CHG を鍵にした側）: REQUIRES_TAKA 215 / 215
- **層2（`AUTO_APPROVED_CONDITIONAL`）は 0件**。機械の逐語の理由: 「幅の材料（`affected_artifact_ids`）が**行為の時点で空**だから `_is_wide` が常に False ∴ `REVERSIBLE_LOCAL` にしかならない」。

### 5-2. ★台帳操作は POLICY に1行も無い

`ASSIGN_ACCOUNT` / `RECORD_EVIDENCE` / `DISPOSE_QUESTION` / `RAISE_QUESTION` / `RECORD_TYPED` — **grep 実測 0件**。

> **∴ Ledger Worker が行う操作は、現在どの authority 規則にも掛かっていない。** `not_governed=0` は「24行すべてを判定する」という意味であって「台帳操作が統治されている」という意味ではない（**鍵が違う**）。

### 5-3. LLM を呼ぶことは既に REQUIRES_APPROVAL である

`USE_VLLM_INFERENCE` = `REQUIRES_APPROVAL`（逐語「any touch of :8005」）。
> **∴ 「LLM_ALLOWED」という段を新設する前に、既存の `USE_VLLM_INFERENCE` が Worker からどう通るのかを決める必要がある。** ここは**設計の穴であり、本調査では解いていない**。

---

## 6. 対照 — DW（実装）Domain では Claude は既に 22% まで下がっている

`dev-workcell/events.jsonl` unique **4,880件**の `identity`：

| identity | 件数 |
|---|---|
| 2der-runtime-supervisor | 1,265 |
| claude-senior | 1,038 |
| 2der-conductor | 606 |
| 2der-qwen-build-planner | 478 |
| 2der-generate-via-runner | 440 |
| 2der-adjudicator | 245 |
| 2der-auto-dispose | 235 |
| qwen3.6@8005#auditor-seed101 | 209 |
| 2der-auto-upper-review | 129 |
| qwen-35b-a3b(:8005) | 92 |
| 2der-gate | 87 |
| claude-manager | 27 |
| qwen3.6@8005#coder-seed7 | 7 |
| MGR | 4 |
| manager-claude | 4 |

**機械 3,799 / 4,880 = 77.8% ／ Claude系 1,081 = 22.2%**

工程別：

| phase | 機械 | Claude | Claude率 |
|---|---|---|---|
| PROCESS_EVENT | 1,265 | 6 | 0.5% |
| **UPPER_REVIEW** | 129 | **1,037** | **88.9%** |
| CREATE | 606 | 7 | 1.1% |
| PLAN | 478 | 7 | 1.4% |
| AUDIT | 454 | 1 | 0.2% |
| GENERATE | 421 | 1 | 0.2% |
| DISPOSE | 235 | 18 | 7.1% |
| REGENERATE | 122 | 0 | 0.0% |
| COMPLETE | 87 | 2 | 2.2% |
| BLOCK | 2 | 2 | 50% |

> **★DW では、Claude が残っているのは実質 UPPER_REVIEW（上級監査）1工程だけ。** そこは Taka の裁定で意図的に Claude である。
> **★Ledger では Claude 94.8%。DW では 22.2%。同じ会社の中で 4倍の差がある。**

---

## 7. GM / Worker の分担案（調査4・5）

**GM を巨大 Worker にしない**という制約を、上の実測に当てて分けた。

### 7-1. General Manager が自分でやること（観測と選択だけ）

既に `manager_v0` + `manager_decide` の形が在る。**同じ形をそのまま Ledger に使う**（新しい常駐を作らない）。

1. 観測 — `/api/gap_report` を引く（既に11行を分母つきで返す。実測 26.6秒）
2. 未処理の選択 — NOT_WIRED の行のうち、母数が大きい順
3. Worker の選択 — 下の表
4. 発注 — front door 経由
5. 結果確認 — 分母が動いたか（前と同じ鍵で再測）
6. authority が要るなら停止

### 7-2. Worker の分け方（入出力と authority が同じ物をまとめた）

**仮称「Ledger Worker」は採用しない。** 実測すると **3つ**に割れる。増やさない。

| Worker | 担当する既存関数 | 入力 | 出力 | 決定論か | authority |
|---|---|---|---|---|---|
| **W1 分類（Classification）** | `record_typed` / `assign_account` | 明細の原文 | kind / account_id | **決定論**（`requirement_structure` と `LEDGER_ACCOUNT_TREE`。実測 644/646 がツリー由来） | AUTO（既存値を変更しない・追記のみ） |
| **W2 証拠（Evidence）** | `record_evidence` / `detail_refs` | 走行結果・ETR- | evidence_refs / basis_kind | **決定論**（`detail_feedback` は既に LIVE で 22件書いている） | AUTO_WITH_EVIDENCE（ETR- が front door から引けることを条件） |
| **W3 処分（Disposal）** | `dispose_question` | 明細＋証拠 | disposal 4語 | **判断が要る**（`dispose_decision` が既に「機械の自動処分は決してしない」と書いている） | **GM_APPROVAL 以上。自動処分は禁止**（既存の設計判断を尊重） |

**W1 の中の LLM が要る部分**: 段0 で `kind_basis=none` の **859 / 1,847 = 46.5%**。ここだけが LLM の対象で、残り 53.5% は決定論で足りている。
**科目の「提案」**（`propose_account`）は既に LLM 経路が在り、**verdict が 100% NOT_DECIDED**。これは Worker を足す話ではなく**設問の欠陥**（既知の型）。

### 7-3. 人（Taka）に残すもの

- `approve_account`（科目の新設承認・`REQUIRES_APPROVAL`・現に `approved_by=taka-credential`）
- `USE_VLLM_INFERENCE` の許可の与え方
- W3 の処分の最終裁定
- 層2（`AUTO_APPROVED_CONDITIONAL`）を成立させるかどうか（今 0件で死んでいる）

---

## 8. 最小実装順序（実装せず・順序だけ）

因果で並べた。**上から順に、1つ前が通らないと次は測れない。**

1. **`dispose_question` に生きた呼び手を1本作る** — 母数 1,026件・現在 live path 0。効果が最大かつ機構は既存。
2. **`record_typed` / `assign_account` を入口から到達させる** — 現在 `detail_backfill` が孤島。**新しい Worker を書くのではなく、既存の `detail_backfill` を生きた入口に繋ぐ**。これで 94.8% の手作業が機械側に移る。
3. **提案→裁定 の辺を1本** — 687/691 が NOT_DECIDED。ただし先に「なぜ 100% NOT_DECIDED なのか」を設問側で解く（**機構の問題ではない**）。
4. **台帳操作を `POLICY` に載せる** — 現在0行。1〜3を自動で回す前に必要。
5. `record_evidence` の母数を増やす（現在 40件）。
6. 注記の語彙をメニューに揃える（471/985 が off-menu）。

---

## 9. 何割を 2DER へ移管できるか

### 9-1. 作業種類ベース

Ledger Domain で数えられた作業は **8種**（起票 / 注記 / 種別付与 / 科目提案 / 科目割当 / 証拠付与 / 書き手記録 / 処分）。

| 区分 | 種類 | 内訳 |
|---|---|---|
| 既に機械化済み・LIVE | **5 / 8 = 62.5%** | 起票・注記・科目提案・証拠付与・書き手記録 |
| 繋げば移管できる | **2 / 8 = 25.0%** | 種別付与・科目割当（機構は在り、入口から切れているだけ） |
| 人／上級LLM が残る | **1 / 8 = 12.5%** | 処分（`dispose_decision` が自動処分を明示的に禁じている） |

### 9-2. 実件数ベース

`recorded_by` が在る **686行**が分母（**それ以外の行は書き手が記録されていない ∴ 数えられない**）。

- 現在 機械が書いた: **36 / 686 = 5.2%**
- 手順2（`detail_backfill` を入口に繋ぐ）が通れば移る: **650 / 686 = 94.8%**
- **∴ 実件数ベースでは 5.2% → 最大 94.8% まで移せる余地がある。**

### 9-3. ★推定不能と書くもの

- **ITEM 台帳の記帳（2,327件・Claude系 96.5%）を何割 移管できるかは 推定できない。** 理由: 記帳の中身は「裁定」「受領」「観測の報告」であり、**上の8種のどれにも当たらない**。これを機械が書けるかは、本調査の範囲外である。
- **`recorded_by` が無い 2,708行（3,394 − 686）については、書き手が記録されていない ∴ 分母に入れられない。** 「0件」とは書かない。**測っていない。**

---

## 10. この調査でやっていないこと（隠さない）

- **実装0行**。修理・接続を1つもしていない。
- `/api/pending_approvals` は **3回叩いて3回とも落ちた**（106秒 / 203秒 / 47秒で RemoteDisconnected）∴ **承認待ちの実数は測れていない**。
- 登記簿56本と `/api/ledgers` の41本の差15本を追っていない。
- ETRACE 196万行の全走査をしていない（`gap_report` が返した範囲のみ）。
- `rri_records.jsonl` 8,672行を引いていない ∴ **「明細がどこから生成されるか」の上流側は未測**。
- **1回の観測で断定した箇所は無いが、`dispose_question` の live path 0 は 1回の全走査による**（呼び手を全ファイルで探し、当たった2件の中身を逐語で確認した）。

## 11. 併せて観測した計器自身の欠陥

`gap_report` の `DETAIL_TEXT_TRUNCATED` の説明文が逐語「submit.py が m[:200] で切って保存している」だが、**`submit.py` の保存時切断は既に廃止されている**（`submit.py:543` の逐語が「★直す前=」と書いており、`:562` の `_m[:200]` は LLM への入力であって保存ではない）。
> **∴ 数字（299/1,062）は今日の実測で正しいが、説明文が古い。299件は過去の在庫であって新規発生ではない。** 計器の散文は数字と同じ速さでは腐らない。

---

## 12. Taka へ求める裁定

1. 手順1（`dispose_question` に生きた呼び手を作る）に着手してよいか。**処分そのものは自動化しない**前提で、「処分の候補を出して止まる」までを機械にするか。
2. 手順2（`detail_backfill` を入口へ繋ぐ）を、**新 Worker を作らず既存モジュールの接続だけ**で行ってよいか。
3. 台帳操作を `authority.POLICY` に載せる件 — **新しい段（AUTO_WITH_EVIDENCE / LLM_ALLOWED / GM_APPROVAL）を足すのか、既存の3×3 に収めるのか。** 本調査の見立ては**既存の3×3 に収まる**（W1=AUTO_EXECUTE/REVERSIBLE、W2=AUTO_EXECUTE/REVERSIBLE、W3=REQUIRES_APPROVAL/REVERSIBLE）。**新語を作らない方を推す。**
4. 層2（`AUTO_APPROVED_CONDITIONAL`）が 0件で死んでいる件を、直すか捨てるか。
