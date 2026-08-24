# 引き継ぎ: General Manager → Ledger Domain 担当 v0.1

- **出所**: Taka 指示 2026-08-24 逐語「Ledger内部のW1/W2/W3設計・分類・evidence・dispositionの実装から離れる。ここまでの調査・実装結果をLedger Domain担当へhandoffする。GeneralはDomainの状態集約、dispatch、優先順位、Domain間調整、上申のみを担当する。」
- **渡す側**: Claude Code (MGR / General Manager)
- **受ける側**: Ledger Domain 担当（**2026-08-24 13:5x 時点で台帳に instance も ITEM も存在しない** — §7 参照）
- **正本**: `TAKA_SPEC_2026-08-24_LEDGER_DOMAIN_v0.1.md` (ART-dd54fb656c)。**本書はその要約ではない。** 仕様に書かれていない「既に動いている実体・現在地・詰まっている点」だけを渡す。
- **測ったHEAD**: ds 79b9c2e / rri 1f5709f / egl 6f51fc4 / dev-workcell b003368 / twoder 80f3cfd

---

## 1. 渡す実体（既に在り、動いている。作り直さないこと）

| もの | 場所 | 状態 | commit |
|---|---|---|---|
| Ledger Domain Manager | `twoder/domain_ledger.py` | **動作中**。General から `to_domain` 経由で到達 | b8c97c8 |
| Domain 登録 | `twoder/manager_v0.py` の `DOMAIN_OPERATIONS` / `DOMAIN_MODULES` に `ledger` 5操作 | **動作中**。`to_domain`/`get_domain` は1行も変更していない | b8c97c8 |
| authority | `twoder/authority.py` POLICY に3行 | **動作中**。`LEDGER_CLASSIFY`=AUTO_EXECUTE×REVERSIBLE / `LEDGER_RECORD_EVIDENCE`=同 / `LEDGER_DISPOSE_QUESTION`=REQUIRES_APPROVAL×REVERSIBLE | b8c97c8 |
| 4率の計器 | `twoder/ledger_rates.py` | **動作中**。台帳に1バイトも書かない | b8c97c8 |
| TEST provenance 抽出器 | `twoder/test_provenance_seal.py` | **動作中**。マーカー `<<<2DER:TEST_PROVENANCE>>>` | a118dc6 |
| provenance の書き戻し | `twoder/detail_feedback.py` `_attach_per_detail` | **動作中**。宣言された試験だけ明細粒度で `record_evidence` | a118dc6 |
| 調査報告 | `egl/docs/CC_MGR_2026-08-24_GM_LEDGER_WORKER_SURVEY_v0.1.md` (ART-0d9bdaab46) | Phase 1 Inventory の実体 | 402e54f |

**W1/W2/W3 は新規実装ではない**。既存機構を呼ぶだけ:
- **W1 分類** = `twoder/detail_backfill.py`（`plan_backfill` / `apply_backfill` → `record_typed` / `assign_account`）
- **W2 証拠** = `twoder/detail_feedback.py`（`scan_unrecorded` / `feed_back` → `record_evidence`）
- **W3 処分** = `rri/rri/request_thread.py`（`list_evidence` / `effective_account_of` / `dispose_question`）

---

## 2. 現在地（実走の結果。推測ではない）

### 2-1. provenance は切れずに通った

`TASK-2DER-813D7F46`（2026-08-24 実投入・PLAN→GENERATE→AUDIT→UPPER_REVIEW→COMPLETE 45.6秒）。

| 明細 | 試験 | verdict | evidence | 科目 |
|---|---|---|---|---|
| Q-31d11de9 | test_returns_port_as_int | PASSED | QE-45d32432 | LDET-a5e121fc 関数実装 |
| Q-54cea911 | test_missing_file_raises | PASSED | QE-0cb20301 | LDET-dc8bc11f ファイルパス検証 |
| Q-28be2dd5 | test_malformed_json_raises | PASSED | QE-24eac0b8 | LDET-1213247d 入力検証 |

thread = `RTHREAD-c7560122`。`undetermined` 0 / `out_of_range` 0。

### 2-2. W3 は候補まで出て、門で止まっている

- 候補 **3件**（`proposed_disposal=RESOLVED`・全件 `basis_kind=LOCAL_MEASUREMENT` / `validation_mode=MEASURED` / `evidence_refs=ETR-f8ec80f68285-0009`）
- UNCLASSIFIED で弾かれた **0件**
- `ledger_dispose_apply` を実際に撃った結果 → `ok=False`「requires approval (token 無し)」。**処分済みは5件のまま。台帳は1バイトも動いていない。**

**分類 → evidence → verdict(候補) までは完全に閉じた。disposition だけが閉じていない。** これは欠陥ではなく Taka 裁定①⑥（自動処分は禁止・Domain Manager で止める）の設計どおり。

### 2-3. 4率（同じ script・同じ鍵で測った推移）

| 指標 | 着手時 | Domain接続後 | provenance後 | 人手分類後 |
|---|---|---|---|---|
| 機械記帳率 | 4.70% | 5.81% | 7.42% | **8.04%** |
| direct 記帳率 | 95.59% | 94.63% | 93.01% | **92.38%** |
| 未処分率 | 99.52% | 99.52% | 99.53% | **99.53%** |
| 未分類率 | 37.90% | 38.14% | 39.30% | **39.08%** |

**率は在庫であって流量ではない。** `MGR.backfill` 619件（Claude が手で書いた分）は追記式の台帳に永久に残るので、率は機械の行を足す速さでしか動かない。**流量で見ると、Domain 接続後に増えた行は 100% 機械**（Claude 0件）。この区別は §22-19「Claude の定型作業量が測定可能」の測り方に直結する。

再測は `python3 -m twoder.ledger_rates --json`。**新しい計器を作らず、これを使うこと**（鍵が変わると before/after が比較できなくなる）。

---

## 3. Phase 1 Inventory の結果（仕様 §21 Phase 1 はこれで済んでいる）

### EXISTS（在って生きた経路から呼ばれている）
`raise_question` / `annotate_question` / `propose_account` / `record_evidence` / `record_actor` /
`account_gate` / `account_tree` / `account_candidates` / `approve_account` / `requirement_structure` /
`requirement_gaps` / `gap_report` / `gap_table` / `gap_streak` / `is_known_verdict` / `stage_from_evidence` /
`annotate_gate` / `classify_changes` / `artifact_registry` / `roadmap_registry` / `ids` / `supersede_seal` /
`contract_seal` / `progress_seal` / `merge_progress`

### UNWIRED（在るが生きた経路から呼ばれていない）
- **試験だけが参照**: `detail_backfill` / `detail_refs` / `change_classifier` / `parallel_router` / `dissent_worker` / `task_similarity`
- **試験からも参照されない**: `register_account_axis` / `record_account_experience` / `split_symbol_details` / `dispose_decision` / `classify_items` / `unresolved_rollback` / `resolve_dispatch` / `wiring_state_rederive` / `acceptance_path_check` / `file_census_*`

### PARTIAL
- `dispose_question` … 機構は在る。**非試験の呼び手は `egl/docs/audit_rthread_stage*.py` の2本のみ**（`gap_report` と `requirement_gaps` に出てくるのは**散文であって呼び出しではない** — 逐語確認済）。`domain_ledger.ledger_dispose_apply` を足して**門つきの生きた呼び手**にした。
- `detail_backfill` … `domain_ledger` から呼べるようにしたが、**母集団が 348/686 thread = 50.7%** しかない（`thread_to_task()` が TRACE の `RTHREAD_ID` から作るため、task を持たない 338 thread は**そもそも分母に入らない**）。**「対象なし」は「全部終わった」ではない。**

### MISSING（本当に無い）
- 明細に **finding 専用の欄が無い**（`record_evidence` の欄は evidence_id / question_id / evidence_refs / basis_kind / validation_mode / source_span / evidence_text。`evidence_refs` に入れること自体はできるが**実績0**）。

> **★Inventory の結論: 「本当に無い」はほぼ無い。ほぼ全部が「在るが呼ばれていない」。**

---

## 4. いま最上流で詰まっている1点（次に着手すべき所）

**未分類率 39.08% の正体は、2層モデルの不能ではなく、スナップショットの古さである。**

実測:
- `account_tree._by_question` が値を持つ明細 **644件** / 台帳の明細 **1,063件** ∴ 被覆 **60.6%**、値を持たない **419件（39.4%）**
- 644 は割当済み 644 と**完全に一致** ∴ モデルが出した分がそのまま割当の全部
- 今回の3明細は3件とも `None` — **「決められない」ではなく欄が無い＝一度も問うていない**
- 出所 `egl/structure/LEDGER_ACCOUNT_TREE.json` は **2026-08-23T04:31:36 の一括生成1回きり**（revision 614241f6… / categories 6 / details 52 / members 644 / corpus 逐語「台帳の明細(list_account_proposals)」）
- 3明細は 2026-08-24T06:51 に立った ＝ **スナップショットより26時間新しい**
- 生成器 `egl/structure/s_ledger_account_tree.py` の**非試験の呼び手は0件**（全repo走査）＝手で回すしかない

**∴ W1 に組み込むべきは「新しい明細が立ったら2層モデルを走らせ直す（または増分で足す）」。** 上流が動かない限り、**W1 は永遠に空を引く**。ただし生成は全明細を読むので毎tick は重い — 頻度の設計が要る（未裁定・§6）。

---

## 5. 守ってきた制約（引き継ぎ後も守ること）

- 新台帳 0 / 新state 0 / 新ID族 0 / 新event type 0 / 新authority階層 0
- 出口規則 `UNCLASSIFIED_FORBIDDEN_DISPOSAL` は1バイトも触っていない
- `account_gate` / `account_tree` は1バイトも触っていない（**根拠が在ることを理由に分類条件を緩めない**）
- 過去記録を書き換えていない（依頼粒度の evidence 1行はそのまま残し、明細粒度を**足した**）
- 契約ブロックの中に触っていない ∴ `immutable_tests_sha256` 不変（実測 21fc48a0… が投入前後で同じ）
- 人の裁定は台帳に actor/provenance 明示（`recorded_by="MGR(Taka 裁定(a) の実施)"` / basis に権限の出所と選定者を分けて記載）
- **今回の人手分類（3件）は恒久運用にしない**（Taka 明示）

---

## 6. 未決（Taka 裁定待ち。Ledger Domain 担当が引き継ぐ）

1. **この3件の disposition を閉じるか。** 閉じるなら承認1回（4件目の人の介入）が要る。(i) 今回だけ承認して閉じ切る / (ii) 閉じずに「候補で止まる」を正しい終端とする。
2. **2層モデルの走らせ直しを W1 に組み込んでよいか。** 生成器は `egl/structure` に在り呼び手0。組み込むなら頻度も決める（生成は全明細を読む）。

---

## 7. 受け手が未確定であること（隠さない）

**2026-08-24 13:5x 時点で、Ledger Domain 担当の instance も ITEM も台帳に存在しない**（実測: EVO-0100〜0109 を `/api/resolve` で引き、Ledger Domain の ITEM は0件。EVO-0102 は System Operations Domain）。

∴ General は **dispatch として ITEM を1本立てて本書を綴じる**が、**担当の指名は Taka の手番**である。担当が決まるまで、この ITEM は「受け手待ち」であって「作業中」ではない。**役が居ないことと、条件が成り立たないことは別である。**

---

## 8. General Manager が今後やること / やらないこと

**やらない**（本日をもって離れる）: Ledger 内部の W1/W2/W3 の設計・分類・evidence・disposition の実装。

**やる**: Domain の状態集約（`ledger_summary` を受け取る）/ dispatch / 優先順位 / Domain 間調整（Ledger ↔ ESDE ↔ System Operations ↔ DW）/ 上申。

**General は Ledger 内部構造を知らなくてよい**（仕様 §22-14）。既に `to_domain` が名前だけで委譲する形になっており、General は `ledger_summary` の集約状態しか見ない。
