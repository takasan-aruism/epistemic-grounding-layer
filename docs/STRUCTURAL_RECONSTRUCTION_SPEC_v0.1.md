# 2DER STRUCTURAL RECONSTRUCTION — 実装仕様 v0.1

- **status: SPEC / PRE-IMPLEMENTATION**
- **authored_by: CLAUDE_CODE** — 2026-07-22
- **origin:** Taka 指示（開発史の再接続）+ GPT 提案（6段パイプライン）を精緻化したもの
- **claim ceiling:** 本書は設計を定義する。本書自体は 2DER の能力を主張しない。

---

## §0. 目的と終了条件

### 目的
1,315 ファイル / 5 リポ / 484 DE / 676 commit を、**証拠付きの機械可読な構造台帳**へ落とし、
その上で「本線1本」と「支流」を分離した人間向けドキュメントを1本生成する。

### 終了条件（TERMINAL）
以下 3 つが揃った時点で本作業は終了する。延長には Taka 裁定を要する。

- **T-1.** 機械可読層 8 ファイルが生成され、§7 のトレーサビリティ試験 6 本すべてに合格する。
- **T-2.** 人間向けドキュメント 4 本が生成され、各主張が機械可読層の行を引用している。
- **T-3.** `PROJECT_GOAL.md §3` の欠損辺（① ITEM選択 → ② DWタスク生成）について、
  **接続に必要な具体的 producer の仕様が、実測された edge inventory から導出されている。**

### 反・支流条項（ANTI-TRIBUTARY CLAUSE）
本作業は、それ自体が新しい支流になる危険がある。
実測では detection 系の実験（DE-0101–0150 / DE-0301–0350、計 DE 約100件）は
いずれも CLOSED-NEGATIVE で閉じている。同じ形をとらないために：

- 本作業は **新しい検出器を作らない**。既存の実体を写像するだけである。
- 本作業の成果物は **DERIVED（導出物）であり SoR ではない**（§1.3）。
- T-3 に到達しない構造理解は、**本作業の失敗として記録する**。地図を作って終わることを成功としない。
- 予算: Qwen 生成トークン総量と壁時計時間を `HISTORY_EVENTS.jsonl` に記録し、超過時は停止して Taka に報告する。

---

## §1. 基本原則（GPT 提案からの逸脱点を含む）

### 1.1 【逸脱 R1】LLM に配線を主張させない

GPT 提案の file-level 出力スキーマには `calls` / `called_by` / `reads` / `writes` が含まれるが、
**これらを Qwen の出力にしてはならない。**

- `called_by` は単一ファイルからは原理的に決定不能である。LLM に書かせれば必ず捏造される。
- `calls` / `reads` / `writes` は Python AST から一意に決まる。推論の対象ではない。

したがって本仕様では、**これらは Qwen への入力**であり、出力ではない。
Qwen の出力は「AST から出ないもの」に限定する（§3.2）。

> 根拠: DE-0001（自由文自己監査は net マイナス）、および detection 系 2 実験の CLOSED-NEGATIVE。
> もっともらしい配線図は、誤った配線図より危険である。

### 1.2 【中核 R2】5状態はすべて別々の機械的根拠から計算する

2DER の混乱の最大原因は、`documented / implemented / wired / executed / proven` が
「ある / ない」の一語に潰れていることである（GPT 指摘。同意する）。

本仕様では 5 状態を **判断させず、5 つの独立した機械的根拠から計算する**：

| 状態 | 根拠源 | 決定方法 |
|---|---|---|
| `documented` | `*.md` / spec doc | シンボル・コンポーネント名の出現索引 |
| `implemented` | Python AST | シンボル定義の存在 |
| `wired` | import/call グラフ | **live entrypoint からの到達可能性** |
| `executed` | ランタイム記録（untracked 489件） | 実行痕跡への出現 |
| `proven` | `CDEF-2DER-v1` の規則 | bound acceptance artifact の存在 **かつ** (CLASS-N/H なら) JREV verdict の参照 |

`proven` の定義を新設しないことが重要である。既に
`experiments/temporal-provenance/COMPLETION_DEFINITION_v1.json`（Taka 承認, DE-0275）が定義している：

> A flag is SET only when its bound acceptance artifact exists AND (for CLASS-N/H) a JREV verdict references it.

**この 5 列があれば、`documented=yes / implemented=yes / wired=no / executed=no / proven=no` が
一語に潰れずに表現できる。これが本作業の中心的な成果である。**

### 1.3 【逸脱 R3】機械可読層は DERIVED であり SoR ではない

既に `twoder/audit/ARTIFACT_REGISTRY.jsonl`（実体 210 ファイル）が artifact の SoR として存在する。
ここに競合する第 2 の権威を作ると、DE-0447 で調査された二重台帳問題を再生産する。

したがって：

- 機械可読層 8 ファイルはすべて **`regenerable: true` / `derived_from` を持つ導出物**とする。
- 権威主張をしない。矛盾したら **SoR 側が勝つ**。
- 例外的な書き戻しは 1 箇所のみ: `ARTIFACT_REGISTRY.used_by_live_path`
  （現在 210 件中 198 件が `unknown`）を計算値で埋める。これは既存 schema の欄を埋める行為であり、
  新しい store を作る行為ではない。**書き戻しは Taka 承認後**。

### 1.4 【逸脱 R5】tracked と runtime を同一信頼度で混ぜない

すべてのレコードは `trust_tier` を持つ：

| tier | 対象 | 意味 |
|---|---|---|
| `T1_TRACKED` | git 管理下 826 件 | 内容が commit で固定され、履歴を持つ |
| `T2_RUNTIME` | untracked 実行時記録 489 件 | 実行の事実の証拠。再現不能、書き換え可能 |
| `T3_DERIVED` | 本作業の生成物 | 上 2 者からの計算結果 |

`executed` 列は **T2 のみを根拠にできる**。`wired` 列は **T1 のみを根拠にできる**。
T2 は「動いた」ことは示すが「今も繋がっている」ことは示さない（過去の配線の可能性）。逆も同様。

### 1.5 引用必須（citation requirement）

機械可読層の**すべての主張行**は、以下のいずれかを最低 1 つ持たねばならない：

- `file_path` + `line_start`–`line_end`
- `symbol`（完全修飾）
- `record_id`（DE-xxxx / ITEM-xxx / CHG-xxx / ART-xxx / run key / event id）
- `commit`

**引用を欠く行は統合対象から除外する**（破棄ではなく `UNRESOLVED.jsonl` へ隔離）。

---

## §2. Stage 1 — Inventory（決定論・LLM なし）

### 2.1 対象

```
tracked   826   (egl 495 / twoder 204 / dev-workcell 76 / rri 37 / ds 14)
untracked 489   (twoder/runs 337+ / dev-workcell events・experiments / egl data_* / ds・rri 記録)
合計    1,315   (__pycache__ 除く)
```

### 2.2 FILE_MANIFEST.jsonl（全 1,315 行）

```
repo, relative_path, absolute_path, trust_tier,
tracked(bool), git_first_commit, git_first_date, git_last_commit, git_last_date, commit_count,
mtime, size, sha256, extension, language,
classification: source | test | ledger | doc | runtime_trace | event_store | generated | config | archive,
generated(bool)          # 生成物ヒューリスティック（zip 内展開・experiments/out 配下 等）
introduced_by_de         # ARTIFACT_REGISTRY / commit メッセージの DE-xxxx から解決
```

### 2.3 SYMBOL_INDEX.jsonl（Python 388 ファイル、AST）

ファイルごとに機械抽出：

```
imports (module, symbol, is_cross_repo),
defines (class/function, name, lineno, endlineno, decorators, is_public),
calls (callee_name, lineno, resolved_target|null),
cli_entrypoints (__main__ ガード, argparse),
file_reads / file_writes (open/Path 呼び出しのリテラル引数),
subprocess_calls, network_calls (requests/urllib/httpx/socket, :8005 等のリテラル),
event_kinds (文字列リテラルのうち EVENT/KIND 定数に一致するもの),
referenced_schemas, test_targets (test_* → 対象モジュールの逆引き)
```

Markdown（140 件）:
```
title, status_words(PENDING/DONE/LIVE/PROPOSED/...), supersedes, depends_on,
de_refs[], item_refs[], repo_refs[], claimed_capabilities[], claimed_missing[]
```

JSON/JSONL（226 件）:
```
schema_shape(キー集合と出現率), record_count, event_kinds,
first_ts, last_ts, id_ranges, referential_keys, hash_chain_fields
```

**Stage 1 の出力に LLM は一切関与しない。再実行で完全に同一の結果が出ること（決定性）を検証する。**

---

## §3. Stage 2 — File-level extraction（Qwen 並列）

### 3.1 worker への入力（context contract）

各 worker には以下だけを渡す。全体は渡さない。

```
- task_contract      : 固定文言
- target_file        : 本文（平均112行、上限を超える場合は関数単位に分割）
- ast_facts          : Stage 1 の SYMBOL_INDEX 該当行（imports/defines/calls/reads/writes/network）
- reverse_index      : このファイルを import しているファイル一覧（Stage 1 で計算済み）
- known_ids          : このファイルに紐づく DE / ITEM / ART id
- output_schema      : 下記 JSON schema
- prohibitions       : §3.3
```

### 3.2 worker の出力（AST から出ないものだけ）

```json
{
  "file": "twoder/patch_bridge.py",
  "purpose_1line": "",
  "declared_responsibility": "",
  "actual_capabilities":  [{"capability":"", "evidence":{"line_start":0,"line_end":0}}],
  "claimed_capabilities":  [{"claim":"", "evidence":{"line_start":0,"line_end":0}}],
  "capability_gap":        [{"claimed":"", "why_not_actual":"", "evidence":{}}],
  "authority_checks":      [{"check":"", "evidence":{}}],
  "side_effects":          [{"effect":"", "evidence":{}}],
  "failure_modes":         [{"mode":"", "evidence":{}}],
  "limitations":           [{"limitation":"", "evidence":{}}],
  "uncertainties":         [""],
  "lifecycle_signal":      "ACTIVE | SCAFFOLD | EXPERIMENT | DEPRECATED | UNKNOWN"
}
```

**`calls` / `called_by` / `reads` / `writes` / `inputs` / `outputs` / `related_files` は出力に含めない（§1.1）。**
これらは Stage 1 の決定論的出力が唯一の権威である。

### 3.3 禁止事項（プロンプトに明記）

1. 証拠（行範囲）なしに主張しない。不明は `uncertainties` に置く。
2. **文書の自己申告を実装事実として扱わない。** docstring の主張は `claimed_capabilities` であり `actual_capabilities` ではない。
3. **ファイル名から役割を決めない。** 本文に根拠がなければ `UNKNOWN`。
4. **DONE を稼働済みと解釈しない。**
5. **未配線と未実装を混同しない。** 配線の有無は判定してはならない（判定材料を与えていない）。
6. 他ファイルの内容を推測しない。`reverse_index` に無い関係を作らない。

### 3.4 再現性チェック（replication gate）

- 全ファイルの **10%（約39件）を seed 違いで 2 回実行**し、`actual_capabilities` の集合一致率を測る。
- 一致率が閾値を下回るファイルは `UNRESOLVED.jsonl` へ隔離し、Claude が直接読む。
- これは「30 worker がそれぞれもっともらしく書き、31 番目がまとめる」失敗形への直接の対策である。

---

## §4. Stage 3/4 — Component & Wiring reconstruction

### 4.1 コンポーネント境界は宣言しない、計算する

GPT 提案は 14 コンポーネントを事前列挙しているが、本仕様では
**まず import グラフのクラスタリングとディレクトリ構造から候補を計算し**、
既知の 4 責任系（DS/DW/EGL/RRI）+ twoder モジュール群に写像する。
計算結果と事前列挙が食い違った場合、**食い違い自体を `CONTRADICTIONS.jsonl` に記録する**。

`COMPONENT_INVENTORY.jsonl` の各行:
```
component_id, name, repo(s), member_files[],
purpose, inputs, outputs, state_owned, authority,
actual_entrypoint[], actual_callers[], actual_consumers[],
persistent_stores[], tests[],
ladder: {documented, implemented, wired, executed, proven}   # §1.2
known_limitations[], dead_code[], unresolved_dependencies[],
evidence[]
```

### 4.2 EDGE_INVENTORY.jsonl（本作業の中核成果物）

**欲しいのはファイル要約ではなく接続グラフである**（GPT 指摘。同意する）。

```
edge_id, producer, consumer, transport, schema,
actual_caller (file:line|null), actual_callee (symbol|null),
trigger, authority, persistence, test,
last_observed_run,        # T2 ランタイム証拠から。無ければ null
status: LIVE | WIRED_UNEXECUTED | IMPLEMENTED_UNWIRED | DOCUMENTED_ONLY | MISSING | CONTRADICTED,
evidence[]
```

`status` は判断ではなく §1.2 の 5 状態から導出される決定表とする：

| documented | implemented | wired | executed | → status |
|---|---|---|---|---|
| – | yes | yes | yes | `LIVE` |
| – | yes | yes | no | `WIRED_UNEXECUTED` |
| – | yes | no | – | `IMPLEMENTED_UNWIRED` |
| yes | no | – | – | `DOCUMENTED_ONLY` |
| yes | – | – | – (該当コードなし) | `MISSING` |
| （列同士が矛盾） | | | | `CONTRADICTED` |

### 4.3 live entrypoint（`wired` の根）

```
twoder/webui.py         : HTTP エンドポイント
twoder/submit.py        : submit() 直接入力パス
twoder/operator.py      : operator advance
dev-workcell/dw/dispatch.py : 外側ループ
```
これらから到達可能な T1 ファイルのみ `wired=yes`。
**リポをまたぐ import は `sys.path` 越しに解決する必要がある**
（既知の非対称: `dev-workcell` は `egl` を import しない → DW→EGL admission 辺は無線。MISSING_EDGES §3）。
`twoder/operator.py` は標準ライブラリ `operator` を shadow するため、解析は twoder を `sys.path` に載せずに行う（DE-0486 §5(b)）。

### 4.4 `executed` の根拠源（T2）

```
twoder/runs/*.json            337件  per-submit トレース
   → 含有キー DS_INPUT_REF / RRI_REQUEST_TYPE / EGL_QUERY / DW_TASK_ID /
     DISPATCH_RESULT / SELECTED_ACQUISITION_METHOD / NEXT_LEGAL_OPERATION
dev-workcell/events.jsonl     4.0MB  workcell イベント
egl/data*/events.jsonl                EGL RawObservation / 各実験データ
ds/ds_events.jsonl / rri/rri_records.jsonl
twoder/failure_recurrence.jsonl
```

各トレースから「どのコンポーネントが実際に触られたか」を機械抽出し、
コンポーネント/辺ごとに `execution_count` と `last_observed_run` を付ける。
**0 回のものは `executed=no` と明示する。**

---

## §5. Stage 5 — Historical reconstruction

`HISTORY_EVENTS.jsonl`（機械抽出のみ。作文させない）:
```
date, commit, repo, changed_files[], de_refs[], item_refs[], chg_refs[],
claimed_goal (commit subject 原文),
actual_changed_component[] (FILE_MANIFEST から解決),
new_edges[] / removed_edges[]  (前後の EDGE_INVENTORY 差分),
new_safety_layer(bool), supersedes[]
```

フェーズ分割は **別 worker** が行い、境界は「新しい辺が生まれた commit」で定義する（主観的な章立てをしない）。
各フェーズについて出す 3 項目：**本線への寄与 / 新しい支流 / 未完のまま残った前段**。

### 本線判定基準（LINEAGE）

主系譜の定義は 1 つに固定する：

```
入力 → RRI(意図解決) → DW(タスク実行) → 結果 → EGL(admission) → 台帳 → 次の入力
```
この一周に**直接寄与する辺**を持つものが本線。それ以外は以下へ分類（「不要」とは呼ばない）：

`core_path` / `safety_support` / `observability` / `migration_handoff` / `experimental_branch` / `historical_residue`

---

## §6. Stage 6 — Synthesis & Falsification（3役）

### 6.1 矛盾は可能な限り「探させず、計算する」【逸脱 R4】

GPT の矛盾リスト 7 種のうち **5 種は §1.2 の 5 列から機械的に決まる**：

| 矛盾 | 決定方法 |
|---|---|
| doc says implemented / code absent | `documented=yes ∧ implemented=no` |
| code exists / caller absent | `implemented=yes ∧ wired=no` |
| caller exists / tests absent | `wired=yes ∧ tests=[]` |
| test exists / runtime evidence absent | `tests≠[] ∧ executed=no` |
| ledger says done / repo contradicts | `ITEM.status=DONE ∧ ladder が未達` |

残る 2 種（**同一コンポーネントの記述不一致** / **同一権限を複数 store が主張**）は
意味の比較を要するため LLM に回す。**LLM の矛盾探索面積を 7 → 2 に絞る。**

### 6.2 3役

- **Synthesizer**（少数・低並列）— 全体構造の統合。
- **Contradiction auditor** — §6.1 の残り 2 種 + 計算済み矛盾の妥当性反証。
- **Lineage auditor** — §5 の基準で本線/支流を判定。**Synthesizer の出力を見せない**（独立性）。

統合・本線判定・authority 判定・supersede 判定は**高並列に向かない**（GPT 指摘。同意する）。
Wave 3 の統合系は 3–5 worker に絞り、必要なら Claude が直接行う。

---

## §7. トレーサビリティ試験（理解度の判定 = T-1 の合格条件）

自己申告を認めない。機械可読層に対する実行可能なテストとして実装する。

| # | 試験 | 合格条件 |
|---|---|---|
| TR-1 | 任意の機能 → 実装ファイル / caller / test / ledger evidence を返す | 無作為 20 機能で 100% |
| TR-2 | 任意の ITEM → 対応コードと実行記録 | 86 ITEM 全件で解決 or 明示的 `UNRESOLVED` |
| TR-3 | 任意の edge → LIVE/MISSING を証拠付きで | 全 edge が §4.2 決定表で導出可能 |
| TR-4 | 文書とコードの矛盾検出 | 既知 3 件（MISSING_EDGES の #1/#3/#11）を再検出 |
| TR-5 | リポをまたぐデータフロー追跡 | submit → DS → RRI → EGL → DW → 台帳 を端まで |
| TR-6 | 別 worker への同一質問で結論一致 | §3.4 の再現性ゲート合格 |

**TR-4 は既知の正解があるため、本パイプラインの陽性対照（positive control）として機能する。**
再検出できなければパイプライン側の欠陥である（DE-0437: 安全性検証には陽性対照が要る）。

---

## §8. 成果物

### 機械可読層（`egl/structure/`、すべて DERIVED / regenerable）
```
FILE_MANIFEST.jsonl         1,315 行
SYMBOL_INDEX.jsonl          Python 388 + md 140 + json 226
COMPONENT_INVENTORY.jsonl
EDGE_INVENTORY.jsonl        ← 中核
CLAIM_EVIDENCE_INDEX.jsonl
HISTORY_EVENTS.jsonl
CONTRADICTIONS.jsonl
UNRESOLVED.jsonl
```

### 人間向け（`egl/docs/`）
```
2DER_SYSTEM_RECONSTRUCTION.md
2DER_END_TO_END_WIRING_MAP.md
2DER_MAINLINE_AND_BRANCHES.md
2DER_MISSING_EDGES.md        ← twoder/audit/MISSING_EDGES.md (07-12) を SUPERSEDE し diff を併記
```

既存 `twoder/audit/` の 07-12 版 as-built 群（`LIVE_PATH_TRACE.md` / `MISSING_EDGES.md` /
`DUPLICATES_AND_BYPASSES.md` / `AS_BUILT_CAPABILITY_LEDGER.md`）は破棄せず、
**再導出結果との diff を取る**。250 DE 分の変化がそこに出る。

---

## §9. 実行計画（Wave）

`:8005` = Qwen3.6-35B-A3B, `max_model_len=65536`, 常駐, 同時実行上限 32。**30 並列は上限直下で妥当。**

| Wave | 内容 | 並列 | LLM |
|---|---|---|---|
| 0 | Stage 1 Inventory | – | なし |
| 1 | file extraction 388 / ledger 33 / doc 140 | 30 | Qwen |
| 1b | 再現性ゲート（10% 二重実行） | 30 | Qwen |
| 2 | component 復元 / edge 復元 | 25 | Qwen |
| 2b | 5状態ラダー計算・矛盾計算 | – | なし |
| 3 | 統合 / 矛盾監査 / 系譜監査 | 3–5 | Qwen + Claude |
| 4 | TR-1..6 実行 | – | なし |
| 5 | 人間向け 4 本生成 + diff | – | Claude |

計測は req/s と tok/s を primitives から導出する。**GPU util を throughput と誤認しない**（PROCESS-01）。

---

## §10. Taka 裁定を要する点

1. `ARTIFACT_REGISTRY.used_by_live_path` への計算値書き戻しの可否（§1.3）。
2. 生成物の置き場所を `egl/structure/` とすることの可否（第 6 リポを作らない判断）。
3. §0 の TERMINAL 条件、特に **T-3（欠損辺 producer 仕様の導出）を必須とする**ことの可否。
4. 予算上限（Qwen 生成トークン / 壁時計時間）。
