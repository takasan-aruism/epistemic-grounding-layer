# 2DER Execution Architecture — 現状記録（v0.1・常設・正典）

- **根拠**: `egl/docs/EXEC_ARCH_WORK_ORDER_v0_1.md`（Taka 受領・GPT 起草・逐語保存）
- 作成: 設計/監査(CC-α) / 2026-07-27
- **★本文書は `egl/docs/2DER_MECHANISM_MAP.md` を包含する。** **同日に私が作った当該文書は本文書に統合し、`SUPERSEDED` とする**（§2.4「新しい正本を無断で作らない」／**正典を2本にしない**）。
- **状態語彙は作業指示書 §2.2 を使う**: `LIVE` / `BUILT` / `WIRED_UNPROVEN` / `DECLARED` / `PLANNED` / `UNKNOWN` / `DEPRECATED` / `CONTRADICTED`
- **証拠の種別**: `【実】`＝実行して確認 ／ `【読】`＝ソースを読んだだけ ／ `【伝聞】`＝他者の報告 ／ `【未確認】`

> **★本文書の限界（先に）**: 調査の大半は**静的（コード構造の読み）**である。**動的確認（§7.3）は、本日 IMPL が実行した数回の観測に限られる。** **`【読】` を `LIVE` に昇格させていない。**

---

## 5.1 Executive Summary

**2DER は、書く側も読む側（`/api/resolve`）も繋がっている。繋がっていないのは、決定論で絞る側である。**
> **★2026-07-28 訂正**: 初版は「読む側が繋がっていない」と書いたが、**誤りだった**。探索範囲を `submit()` の枝に限っていた。

| # | 事実 | 状態 |
|---|---|---|
| **1** | 入口は `submit()` 1つ。呼び方が3通りあり、**等価ではない** | `LIVE`（§5.3） |
| **2** | **★訂正: front door から台帳は引ける**（`GET /api/resolve`・2026-07-28 実測）。`submit()` の acquisition 枝に無かっただけ | `LIVE`（§5.7） |
| **3** | **勘定科目の自動設定は EGL 登録経路に繋がっていない** | `BUILT`（§5.10） |
| **4** | **4軸→7戦略の決定論セレクタは、既定で入らない分岐の中にある。4軸のうち3軸は本番で生成されていない** | `WIRED_UNPROVEN` / 一部欠落（§5.10） |
| **5** | **PLAN は Qwen が書く。決定論テンプレは front door 由来 task では原理的に発火しない** | `LIVE`（§5.6） |
| **6** | **worker は契約（`skeleton`＋`immutable_tests`）が無ければ着手しない。契約は依頼者（Claude）が渡す** | `LIVE`（§5.6） |
| **7** | **worker は production repo に書けない（三重の保証）。配置は Claude の役割** | 設計どおり |
| **8** | 「同じ規律が2回、互いを知らずに実装されている」箇所が在る | `CONTRADICTED` ではない（同型・別物）（§5.11 G-07） |

**★Taka の問い「確実に一本の開発の流れに沿っているか」への回答: 沿っていない。** 根拠は §5.10。

---

## 5.2 Repository Map

| repo | 役割 | 本文書での扱い |
|---|---|---|
| `ds` | 受付・発話の記録 | `LIVE`（記録のみ。選別は無い） |
| `rri` | 要求解決・意図・ゲート | `LIVE`（一部 `BUILT`） |
| `egl` | 帳簿（Design Evidence）・接地・構造再構成 | `LIVE` ＋ `egl/structure/` は研究層 |
| `dev-workcell` | DW（task の状態機械・dispatch・executor） | `LIVE` |
| `twoder` | front door・webui・worker/planner・登記 | `LIVE` |

**調査対象 commit**【実】（`git -C <repo> rev-parse --short HEAD`）:
| repo | commit | 最終 commit 時刻 |
|---|---|---|
| `ds` | `b0dcd32` | — |
| `rri` | `b1adab2` | — |
| `egl` | `4c300c1` | — |
| `dev-workcell` | `9388fb2` | — |
| `twoder` | `88bfa31` | 2026-07-27 18:14 |

**更新履歴（§8 の更新義務・変わった1点だけ直す）**
| 版 | 変更 | 契機 |
|---|---|---|
| v0.1 初版 | — | 段2 |
| v0.1+1 | **`cc_register.py` の `normalize_path` 追加と `counts()` の母数訂正を反映。commit を更新** | 状況表「実行構造の資料: ★古い」の初回発動 |

---

## 5.3 Runtime Entry Points

| 入口 | 実体 | auth | task を作る | **task を進める** | 状態 |
|---|---|---|---|---|---|
| CLI（正典） | `python3 -m twoder.submit "<入力>"` | 不要 | できる | **★できない** | `LIVE`【実】 |
| CLI（直起動） | `python3 twoder/submit.py` | — | **★起動しない** | — | `DEPRECATED`【実】 |
| webui | `POST /api/submit`（body `{"raw": …}`） | **要**（Basic / user=`taka`） | できる | できる | `LIVE`【実】 |
| webui（進行） | `POST /api/run_next` / `/api/run_until_barrier` | 要 | — | できる | `LIVE`【実】 |
| **webui（参照）** | **`GET /api/resolve?id=…`** | **要** | — | — | **`LIVE`【実】（read-only）** |
| 運転者ループ | `twoder/operator.py:151` | — | — | できる | `【未確認】` |

```
再現【実】: python3 twoder/submit.py "test"
  → ImportError: cannot import name 'eq' from 'operator'   （twoder/operator.py が標準ライブラリを隠す）
再現【実】: stat -c '%U:%G %a' twoder/.access_token → takasan:takasan 600
再現【実】: ss -ltn | grep 8770 → LISTEN 100.107.6.119:8770
```

### 5.3-1 ★CLI と webui は等価でない
`webui.py:29-32` の run-gate は `_LAST`（**webui プロセス内のモジュール変数**・`:545` の `/api/submit` でのみ設定）を見て `tid != gate["task_id"]` なら拒否する。
**∴ CLI が作った task は webui からも進められない。** **【実】**（Build 9C 段0: `refused: true / "task … is not the current runnable submit task"`）

### 5.3-2 ★再起動すると run-gate は初期化される（運用上の帰結）
**`_LAST` はプロセス内変数なので、再起動で「まだ何も投入されていない」に戻る。**
**∴ 既存 task を進めたくても、再起動後の `run_next` は `refused: "no submit yet"` になる。** **【実】**（Build 17 で観測）
> **★対処: 同一の依頼文を1回だけ再投入して gate を立て直す。** **task id は依頼文の `sha1` なので、同一文なら同じ task を指し、新しい task を作らない。**

**★これは「知っていたのに手順に入っていなかった」ものである。** `_LAST` がプロセス内変数であることは Build 9C 監査で既に記録していた。
**∴ 知識が手順になっていなければ、無いのと同じである。** **再起動の常設手順に含める**（`CC_2DER_USAGE_GUIDE.md` §1-2-1 と対）。

---

## 5.4 End-to-End Execution Flows

### 5.4-1 現在の経路（CURRENT）
```
Claude / Taka
  │  ★ここから先は 2DER の内部
  ▼
submit()  ── ts 受領（生成しない。既定に落ちたら ts_source に記録）
  ├ 1.   DS   record_utterance          → ds_events.jsonl                    LIVE
  ├ 1.5  EGL  DE admission fast path    → DESIGN_EVIDENCE_LEDGER.jsonl       LIVE
  ├ (1.6) RRI formal validation         → ★if formal_candidates: 既定 None   WIRED_UNPROVEN
  ├ 2.   RRI  bind_context              → anchoring                          LIVE
  ├ 3a.  EGL  self_grounding            → 出典つきの答え                     LIVE
  ├ 3b.  RRI  classify_request_type     → 6分類                              LIVE
  ├ 3c.  RRI  dead-approach guard       → BLOCKED_DEAD_APPROACH              LIVE
  ├ 3d.  RRI  preflight_gate            → RRI_PREFLIGHT_HOLD                 LIVE
  ├ 3e.  RRI  intent_strategy.resolve   → 7戦略（★LLM が直接選ぶ）           LIVE
  ├ 4.   ROUTING → SELECTED_ACQUISITION_METHOD 8種                           LIVE
  └ 7.   FAILURE_MEMORY_GUARD（read-only・注記のみ）                          LIVE
      │
      ├ BUILD_CAPABILITY / MODIFY_EXISTING → DW_IMPLEMENTATION → create_task  LIVE
      └ OBSERVE_CURRENT_STATE → RUNTIME_INSPECTION（★カタログ全件を実行）     LIVE

DW ループ（submit() は進めない。webui の RUN NEXT / operator.py が進める）
  CREATED           → PLAN      MANAGER(CLAUDE 既定) → ★BUILD_PLANNER(Qwen) が在れば Qwen  LIVE
  READY_FOR_IMPL..  → GENERATE  CODING_WORKER(Qwen)  → ★契約が無ければ着手しない            LIVE
  READY_FOR_AUDIT   → AUDIT     INDEPENDENT_AUDITOR(Qwen)                                  【未確認】
  ...               → UPPER_REVIEW / DISPOSE / COMPLETE                                    【未確認】
```

### 5.4-2 ★切断箇所（CURRENT で繋がっていない所）
| # | 切断 | 状態 |
|---|---|---|
| ~~D-1~~ | ~~front door → 台帳の読み出し~~ | **★取り消し。`GET /api/resolve` で通る**（2026-07-28 実測） |
| **D-2** | **EGL 登録 → 勘定科目の自動設定** | **繋がっていない**（§5.10） |
| **D-3** | **4軸 assessment → 決定論の戦略選択** | **既定で入らない ＋ 3軸は生成されていない** |
| **D-4** | **CLI → DW ループの進行** | **経路が無い**（§5.3-1） |
| **D-5** | **front door の結果 → 設計/監査への到達** | **無い**（**IMPL が7回連続で「自分で読んで転記した」と申告**） |
| **D-6** | **`information_need` → acquisition の選別** | **選別に使われていない**（全件実行） |

### 5.4-3 PLANNED（現行と分離する）
```
PLANNED: ART- の**本文**を返す1段（hash 照合つき）  ← ★所在と版を返す /api/resolve は既に LIVE。本文の返却だけが未実装
PLANNED: DS の選別（空 / 無意味 / 意味の薄い投稿の機械的検知）        ← 未設計
PLANNED: 長文 → 明細（1問い合わせ = 複数明細）                        ← 未設計
```

---

## 5.5 Python Module and Function Map（主要のみ）

| 経路 | file:function |
|---|---|
| 入口 | `twoder/submit.py::submit` / `twoder/webui.py`（HTTP） |
| DS 記録 | `ds/ds/phase0.py::record_utterance` → `ds_events.jsonl` |
| RRI 文脈 | `rri/rri/context_binding.py::bind_context` |
| RRI 要求種別 | `rri/rri/request_type.py::classify_request_type`（`REQUEST_TYPES` 6件） |
| RRI ゲート | `rri/rri/preflight_gate.py::detect` / `next_legal_operation` |
| RRI 意図 | `rri/rri/intent_strategy.py::resolve`（`STRATEGIES` 7件・**LLM**） |
| **RRI 決定論選択** | **`rri/rri/request_resolution.py::select_strategy`（4軸→7戦略・`WIRED_UNPROVEN`）** |
| EGL 接地 | `egl/egl/self_grounding.py::answer_question` |
| EGL 記帳 | **`egl/egl/de_admission.py::admit_design_evidence`（唯一の書き手）** |
| EGL 存在判定 | `rri/rri/existence_grounding.py::check_existence`（3状態） |
| ID 解決 | **`twoder/ids.py::resolve`（15系統・正典）** |
| 登記 | `twoder/artifact_registry.py::register` / `record_change` / `verify` |
| DW 状態機械 | `dev-workcell/dw/workcell.py`（`create_task` / `record_plan` / …） |
| DW 進行 | `dev-workcell/dw/dispatch.py::dispatch_once` / `run_until_barrier` |
| DW 実行方針 | `dev-workcell/dw/executor.py::run_command`（allowlist・cwd 制約） |
| 契約封印 | **`twoder/contract_seal.py::extract_contract`（`submit.py:430`）** |
| 生成 | `twoder/generate_via_runner.py::generate` / `twoder/qwen_worker.py` |
| 取得 | `twoder/runtime_inspection.py::inspect`（`_CATALOG` 4件） |

---

## 5.6 LLM Invocation Map

| # | 呼出箇所 | 用途 | 状態 |
|---|---|---|---|
| 1 | `rri/rri/request_type.py::_chat` | 要求種別の分類（6） | `LIVE` |
| 2 | **`rri/rri/intent_strategy.py`** | **7戦略の選択（生テキストから直接）** | `LIVE` |
| 3 | **`twoder/build_planner.py`** | **PLAN の起草＋自己検証** | `LIVE` |
| 4 | `twoder/qwen_worker.py` | コード生成（body のみ） | `LIVE`【実】 |
| 5 | `twoder/adjudicator`（`QwenAuditor`） | 独立監査 | `【未確認】` |
| 6 | `egl/structure/s_account_axis_names.py` | 勘定科目の命名（3-seed consensus） | `BUILT`（研究層） |

**★決定論で行われるもの（LLM を通さない）**: 契約抽出 / preflight gate / dead-approach guard / `validate_plan` / `ids.resolve` / DW の状態遷移。

### 5.6-1 ★契約（`contract`）
```
再現【読】: twoder/contract_seal.py
  BEGIN_SK="<<<2DER:SKELETON>>>" / BEGIN_IT="<<<2DER:IMMUTABLE_TESTS>>>" / END="<<<2DER:END>>>"
  両方在れば抽出、片方のみ/END 欠落は ValueError、両方無ければ None
再現【読】: twoder/generate_via_runner.py:149 付近
  contract 無 → reason="SPEC_INCOMPLETE_NO_CONTRACT"（run_runner を呼ばない）
```
**∴ worker は「骨格」と「変更不可のテスト」を依頼者から受け取り、body だけを埋める。**
**∴ 契約を渡すのは依頼者（Claude）である。** **PLAN より前（`submit.py:430`）で封印される。**

### 5.6-2 ★PLAN の書き手
```
再現【読】: dev-workcell/dw/dispatch.py:97-116 / dev-workcell/dw/plan_template.py:23-36 / twoder/submit.py:424-429
```
`PT.plannable` は kp が `packet_type="KNOWLEDGE_PACKET"`・`experiment` 無し・`rollback_reference` 無しのため **front door 由来 task では常に False**。
**∴ `dispatched: true` になる PLAN は Qwen `BUILD_PLANNER` が書いたものである。**（**導出であり、identity の観測はしていない＝`【未確認】`**）

---

## 5.7 Mandatory Read Paths

| 読む対象 | 経路 | 状態 |
|---|---|---|
| EGL の接地情報 | `self_grounding.answer_question`（段3a） | `LIVE` |
| 過去の失敗 | `failure_memory`（段7・read-only） | `LIVE` |
| **台帳の中身（ID 指定）** | **`GET /api/resolve` → `resolve_view` → `twoder/ids.py::resolve`** | **★`LIVE`**（2026-07-28 実測。存在しない ID は `resolved:false`） |
| ランタイム状態 | `runtime_inspection`（GPU/コンテナ/プロセス/ポート） | `LIVE`。**★`information_need` を選別に使わず全件実行** |

```
再現【読】: grep -rn "LEDGER_QUERY\|ledger_query" --include=*.py twoder/ rri/ ds/ dev-workcell/ → 0件
再現【読】: grep -n "SELECTED_ACQUISITION_METHOD" twoder/submit.py → 8種。帳簿の中身を返すものは無い
```
> **★これが最大の切断（D-1）である。** **我々が台帳を直読してきたのは、読む経路が存在しないからである。**

---

## 5.8 Write-back and Canonical Store Map

| 台帳 | 唯一の書き手 | 場所 |
|---|---|---|
| `DESIGN_EVIDENCE_LEDGER.jsonl` | `egl.de_admission.admit_design_evidence`（docstring 逐語: *"The **ONLY** sanctioned writer"*） | `egl/` |
| `ds_events.jsonl` | `ds.phase0`（`DS_DATA_DIR`） | `ds/` |
| DW events | `dev-workcell/dw/workcell.py` | `dev-workcell/`（`DW_DATA_DIR`） |
| `ARTIFACT_REGISTRY.jsonl` / `CHANGE_LOG.jsonl` | `twoder.artifact_registry` | `twoder/audit/` |
| `rri_records.jsonl` | RRI | `rri/` |
| `CC_REGISTER.jsonl`（**暫定**） | `egl/docs/cc_register.py` | `egl/docs/`（**退役条件つき**） |

**`cc_register.py` の補足（D21FIX で変更・§8 の更新義務による反映）**
- `record_doc` は `normalize_path` で path を1表記に寄せる（先頭 `egl/` を1回剥がし、`docs/` 以外は `ValueError`）。**`doc_id` は `artifact_registry.artifact_id_for` と一致する。**
- `counts().files_since_start` は `egl/docs/` 直下の `*.md` / `*.json` を数える（`CC_*.md` 限定をやめた母数の訂正）。
- **★利用側は `sys.path` に `/home/takasan/egl/docs` を足すこと**（口伝だったので明記）。
- **★`_meta` の1行目を1回だけ書き換えた**（追記のみの例外）。**MGR 裁定により、以後は `META_UPDATE` 行を追記する。**

**★書ける者・書けない者**
| 主体 | production repo | 根拠 |
|---|---|---|
| Qwen worker | **書けない（三重）** | `build_planner.PROD_REPO_ROOTS`(:59/:254) ／ `qwen_worker._safe_target_path` ／ `live_worker_scaffold._MUST_BE_TRUE` に `host_filesystem_unreachable` |
| Claude | 書ける（**Taka が明示的に許可**） | 「プログラムを外注で生成、配置するまで」 |
| Claude（台帳を直接） | **禁止** | 「台帳は 2DER を通さないと読めない、書き込めない」 |

---

## 5.9 State Machine Map
```
dev-workcell/dw/dispatch.py:28-36  _MAP
  CREATED                  → PLAN          MANAGER(claude_barrier=True)
  READY_FOR_IMPLEMENTATION → GENERATE      CODING_WORKER(False)
  READY_FOR_AUDIT          → AUDIT         INDEPENDENT_AUDITOR(False)
  DISPOSITION_REQUIRED     → DISPOSE       MANAGER(True)
  READY_FOR_REGENERATE     → REGENERATE    CODING_WORKER(False)
  READY_FOR_UPPER_REVIEW   → UPPER_REVIEW  CLAUDE_SENIOR(True)
  COMPLETE / BLOCKED       → NONE / BLOCKED
```
**`claude_barrier=True` でも、機械 actor が登録され自己検証を通せば Claude を飛ばす**（PLAN / UPPER_REVIEW / DISPOSE の3箇所）。**通らなければ fail-closed で Claude に戻る。**

---

## 5.10 Current / Planned / Unknown Overlay

### ★Taka が名指しした2機構
```
CURRENT:
  EGL 登録 (admit_design_evidence) → 勘定科目
    → 接続なし（本番コードからの参照 0件）
  勘定科目パイプライン (s_embed_axes → s_account_axes → s_rthread_2br3 → s_account_axis_names)
    → egl/structure/ 内でのみ呼び合う（バッチ）        状態: BUILT

CURRENT:
  生テキスト → intent_strategy(LLM) → 7戦略             状態: LIVE
  4軸 assessment → request_resolution → 7戦略
    → rri_formal 経由のみ / if formal_candidates: 既定 None   状態: WIRED_UNPROVEN
  4軸のうち本番で生成されるのは context_anchoring のみ
    answer_determinacy / intent_breadth / premise_stability → 本番に無い   状態: 欠落
```
```
再現【読】: grep -rn "ACCOUNT\|account_axes\|embed_axes" --include=*.py egl/egl/ ds/ds/ rri/rri/ dev-workcell/dw/ twoder/*.py → 0件
再現【読】: grep -n "^from\|^import" egl/egl/de_admission.py → json, re, pathlib のみ
再現【読】: grep -rn "request_resolution" --include=*.py . → 本体・rri_formal・demo・test のみ
再現【読】: sed -n '104,113p' twoder/submit.py → if formal_candidates:（既定 None・投入口2つとも渡さない）
```
**★注意（誤認を潰す）**: `rri/rri/rq_candidate.py` / `research_axis.py` の `axis_id` は**研究軸(RDEC)**であり、勘定科目ではない。

### BUILT だが未接続の主要要素
| 要素 | 状態 |
|---|---|
| `twoder/ids.py::resolve`（正典 resolver） | `BUILT`（front door から到達せず） |
| 勘定科目パイプライン（4スクリプト＋台帳群） | `BUILT` |
| `egl/structure/s_exec_arch_acd.py` / `s_task_contract.py` / `TASK_CONTRACTS.jsonl` | `BUILT`（本番参照 0件） |
| `rri/rri/request_resolution.py` | `WIRED_UNPROVEN` |

---

## 5.11 Gap and Contradiction Register

| id | 内容 | 種別 | 状態 |
|---|---|---|---|
| **G-01** | **★誤りだった。** front door から台帳は引ける（`GET /api/resolve`）。`submit()` の acquisition 枝には無いが、別の口に在った | Gap | **CLOSED**（2026-07-28 実測） |
| **G-02** | **勘定科目が EGL 登録経路に繋がっていない** | Gap | 未着手 |
| **G-03** | **4軸→7戦略の決定論選択が既定で入らない。3軸は本番で生成されない** | Gap | 未着手 |
| **G-04** | **DS に選別も断りの返答も無い**（空入力は `ds/phase0.py:101` の `ValueError`） | Gap | 未着手 |
| **G-05** | **CLI から DW ループを進める経路が無い**。CLI の task は webui からも進まない | Gap | 未着手 |
| **G-06** | **`information_need` が acquisition の選別に使われず、全件実行される** | Gap | 未着手 |
| **G-07** | **同じ規律が2回、互いを知らずに実装**（`UNRESOLVED_NO_CONTRACT` / `SPEC_INCOMPLETE_NO_CONTRACT`） | 同型・別物 | **統合しない。可視化する** |
| **G-08** | **front door の結果が設計/監査へ自動で届かない**（7回連続で手読み） | Gap | 未着手 |
| **G-09** | **`s10_ledger_registry.py:26` の `TODAY` がハードコード**（放置日数が常に 07-22 基準） | 計器の欠陥 | 修理予定 |
| **G-10** | **`s4_edges.py` に `--check` が無い**（実行すると台帳を書き換える） | 計器の欠陥 | 未着手 |
| **G-11** | **`twoder/operator.py` が標準ライブラリの `operator` を隠す** | Contradiction | 保留（`-m` を正典化） |
| **G-12** | **DW の `generate_runs.ts` が既定値**（`2026-07-11T09:00:00`） | Gap | 未調査 |
| **G-13** | **`test_submit_e2e` の3件が失敗（Build 10 以前から）** | Gap | 未調査 |
| **G-14** | **DS `reconstruct_snapshot failed: HTTP 400`** | Gap | 未調査 |
| **G-15** | **`LEDGER_REGISTRY` と `EDGE_INVENTORY` の鮮度が不揃い**（07-22 / 07-26） | 計器の欠陥 | 未着手 |
| **G-16** | mint 側(generate_via_runner.mint_token)と検証側(approval_registry)が action_type/task_id/operation_class の3項目とも別の語彙を使う | 矛盾 | **CLOSED** |
| **G-17** | /tmp 直下に約1000万エントリ。ルート FS の使用 inode の約88%を占め、cwd を /tmp にすると Python の import が返らない | Gap | **CLOSED** |
| **G-18** | cc_register.py は egl/docs に在り、利用側が sys.path を通す必要がある(口伝だった) | Gap | 未着手 |
| **G-19** | GENERATE は失敗しても段を進める(record_generate が成否に関わらず遷移を記録する) | Gap | 未着手 |
| **G-20** | サンドボックス保証(process_kill_cleanup 等)が仕様辞書の自己申告を検査するだけで実装が無かった | contradicted | PARTIALLY_CLOSED |
| **G-21** |  の timeout が直接の子しか殺さず、孫以降が生き残る | Gap | **CLOSED** |
| **G-22** | 生成コードの危険な形(__main__ 重複・自己 subprocess 起動)を実行前に見る検査が無い | Gap | 未着手 |
| **G-23** | 計器が自分自身を数えてしまう(測る側の命令行に探索文字列が現れる) | 計器の欠陥 | 未着手 |
| **G-24** | runtime_supervisor.qwen_raw_call は system を受け取れるが build_planner は渡していない(auditor は渡している) | Gap | 未着手 |
| **G-25** | RUNNER_FAILED が『落ちた/走らせられなかった/1件も集まらなかった』を1語に潰す | Gap | **CLOSED** |
| **G-26** | immutable_tests の書式要件(pytest が集める test_* 関数)がどこにも書かれず、空の検査を封じられた | Gap | **CLOSED** |
| **G-27** | 検査の供給者と合否の判定者が同一(設計/監査が immutable_tests と受入基準の両方を書く) | Gap | 未着手 |
| **G-28** | 運用方針 §12 の改訂履歴に一貫した並び順が無く、位置で最新版を判定できない | 計器の欠陥 | 未着手 |
| **G-29** | 『【未確認】』が閉じる期限も担当も持たず、宣言が確認の代わりになる | 作法の欠陥 | 未着手 |
| **G-30** | ds.phase0.record_utterance は HUMAN_RELAYED/relayed_by/authored_by を受け取れるが、twoder.submit が引数を持たず origin=MACHINE_SUBMIT を直書きしている | Gap | 未着手 |
| **G-31** | 同一文面の再投入で、途中の発話の実行記録が保存されない（DW CREATE は最初の1回・TRACE ファイルは最後の1回しか残らない）。加えて INTENT_STRATEGY / RRI_PREFLIGHT が /api/state に出ない | Gap | 未着手 |
| **G-32** | 『探した範囲に無い』を『無い』と書く／確かめずに上流へ流す（本日 CC-α 3回・MGR 3回） | 作法の欠陥 | 未着手 |
| **G-33** | RRI の event stream (rthread_events.jsonl) は実装されているが本番経路から一度も呼ばれない | Gap | 未着手 |
| **G-34** | TRACE は系列でなくスナップショット — 1回の submit の中でも途中経過が消える | Gap | 未着手 |
| **G-35** | どの記録機構も『親 Event ID』を持たない — 一本の系列が作れない | Gap | 未着手 |
| **G-36** | CLI 投入(python3 -m twoder.submit)は TRACE を1件も残さない — 使用ガイドが名指しする投入経路が実行記録を作らない | Gap | 未着手 |
| **G-37** | provenance.ds_thread_id が実データで null（threads が空）— Session ID 候補として当てにできない | Gap | **DEFERRED**（原因は【未確認・誰が=CC-α / いつ=Event Trace の SPEC 着手時】。MGR 裁定で本線外） |
| **G-38** | Event Trace の合流点④(DW `_append_event`)は fail-open — 記録の取りこぼしが起きうる | Gap | 未着手（★穴を見える場所に置いた・SPEC §2-5） |
| **G-39** | 既存の依存逆転 — `dw` が `twoder` を import している(3箇所) | Gap | 未着手（D-42 範囲外） |
| **G-40** | Event Trace の概念的な持ち主は EGL だが、辺の向きの制約により `ds` に置いた（設計上の妥協） | Gap | 未着手（★いま動かさない。動かすなら別の裁定） |

---

## 6. 機械可読版
**`egl/docs/2DER_EXECUTION_ARCHITECTURE.json`**（§6 の最低 schema に準拠）。
```
再現【実】: python3 -c "import json;json.load(open('2DER_EXECUTION_ARCHITECTURE.json'))"
結果: JSON 妥当。entrypoints 5 / components 21 / llm_invocations 6 / edges 8 /
      read_paths 4 / write_paths 6 / state_machines 1 / canonical_stores 7 /
      execution_flows 2 / gaps 15 / planned_extensions 5 / unknowns 7
      状態語彙(8種)の逸脱: なし / commits: 5
```
### 6-1. ★乖離しない生成・検証方法（§4.2 の要求）
**v0.1 は Markdown と JSON を並行して手で書いている。生成関係は無い。** **これを隠さない。**
**検証方法（`P-05`・未実装）**: 決定論チェッカを置き、`--check` で次の3点を照合する。
1. `gaps[].id` の集合が MD §5.11 の表の id 集合と一致する
2. `components[].status` が §2.2 の8語彙に含まれる（**現時点で逸脱0を実測済**）
3. `generated_from.commits` が各 repo の `HEAD` と一致する

**★現時点では未実装であり、乖離は検出されない。** **これは `P-05` として登録済みである。**

## 7. 調査方法（本版で用いた範囲）
- **7.2 静的調査**: 実施（本文の再現コマンド）。
- **7.3 動的確認**: **限定的**。本日 IMPL が実行した観測（front door 投入・RUN NEXT・worker 1段）と、私が実行した数件（CLI 起動失敗・token/待受・プロセス鮮度）のみ。
- **7.4 仕様との照合**: **未実施。**

## 10. 完了条件の達成状況
| # | 条件 | 達成 |
|---|---|---|
| 1 | 全対象 repo の commit 記録 | **達成**（§5.2・5 repo） |
| 2 | 正式 entrypoint の特定 | 達成 |
| 3 | 主要実行経路の file/function 追跡 | 達成（§5.5） |
| 4 | LLM invocation 一覧 | 達成（§5.6） |
| 5 | read path / write-back | 達成（§5.7 / §5.8） |
| 6 | RRI→DW の経路（切断含む） | 達成（§5.4） |
| 7 | LIVE/BUILT/PLANNED/UNKNOWN の分離 | 達成 |
| 8 | EventStore/EGL/Ledger/RTHREAD の責務比較 | **未達** |
| 9 | Development Context / Knowledge Dispatcher 構想との差分 | **未達**（構想文書を未読） |
| 10 | Gap Register | 達成（§5.11） |
| 11 | 機械可読版 | **達成**（§6・JSON 妥当性を実測）。**ただし乖離検証は未実装（`P-05`）** |
| 12 | 再現コマンドと証拠 | 達成 |
| 13 | 正式文書体系への登録場所 | **本文書＝`egl/docs/`。`2DER_MECHANISM_MAP.md` を統合し SUPERSEDED とする** |
| 14 | commit 前に Taka へ提示 | **未**（MGR が仲介） |

---
*2DER Execution Architecture v0.1（常設・正典）。`2DER_MECHANISM_MAP.md` を包含し統合する（正典を2本にしない）。★要約=書く側も読む側(`GET /api/resolve`)も繋がっており、繋がっていないのは決定論で絞る側である（★2026-07-28 訂正: 初版は「読む側が繋がっていない」「最大の切断は G-01」と書いたが**誤りだった**——探索範囲を `submit()` の acquisition 枝に限っており、別の口を見ていなかった。G-01 は CLOSED）。勘定科目は EGL 登録経路に無く(G-02)、4軸→7戦略の決定論選択は既定で入らない分岐にあり3軸は本番で生成されない(G-03)。PLAN は Qwen が書き(決定論テンプレは front door 由来 task では原理的に発火しない)、worker は契約(skeleton+immutable_tests)が無ければ着手せず、契約は依頼者(Claude)が渡す。worker は production repo に三重の保証で書けず、配置は Claude の役割。Gap Register は G-01〜G-40（★2026-07-28 D-41 で G-33〜G-35 を追加し、MD 表を JSON と同期した——それまで MD 表は G-15 で止まっており、§6 が自ら宣言した不変条件『`gaps[].id` の集合が MD §5.11 の表と一致する』が破れていた。★この不変条件を検査する計器は存在しない）。★未達=commit 記録／EventStore 等の責務比較／構想との差分／機械可読版／Taka への提示。調査の大半は静的であり、`【読】` を `LIVE` に昇格させていない。*
