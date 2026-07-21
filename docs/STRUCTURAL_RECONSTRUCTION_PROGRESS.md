# 2DER 構造再構成 — 進行レポート（追記式）

- **status: IN_PROGRESS**（living document）
- **spec:** `docs/STRUCTURAL_RECONSTRUCTION_SPEC_v0.1.md`
- **claim ceiling:** 本書は実測値と、その導出方法のみを記す。未計算の列については「未計算」と書く。
- **追記規約:** 各 Stage 完了ごとに §3 に追記する。**過去の記述を書き換えない。**
  訂正が必要な場合は取り消し線ではなく「§3.x で訂正」と追記し、訂正側に根拠を書く（append-only）。

---

## §1. 進捗サマリ

| Stage | 内容 | 手段 | 状態 |
|---|---|---|---|
| 1a | FILE_MANIFEST（全ファイル台帳） | 決定論 | ✅ 完了 2026-07-22 |
| 1b | SYMBOL_INDEX（AST / md / json 抽出） | 決定論 | ✅ 完了 2026-07-22 |
| 1c | REACHABILITY（module 単位 `wired`） | 決定論 | ✅ 完了 2026-07-22（**十分条件ではない。§4-U1**） |
| 1d | symbol 単位 到達可能性 | 決定論 | ⬜ 未着手 |
| 1e | `executed` 列（runs/ + events.jsonl） | 決定論 | ⬜ 未着手 |
| 2 | file-level extraction | Qwen 30並列 | ⬜ 未着手 |
| 2b | 再現性ゲート（10% 二重実行） | Qwen | ⬜ 未着手 |
| 3 | COMPONENT_INVENTORY | Qwen 25並列 | ⬜ 未着手 |
| 4 | EDGE_INVENTORY（中核） | Qwen + 決定論 | ⬜ 未着手 |
| 5 | HISTORY_EVENTS / フェーズ分割 | 決定論 + Qwen | ⬜ 未着手 |
| 6 | 統合・矛盾監査・系譜監査 | Qwen 3–5 + Claude | ⬜ 未着手 |
| 7 | TR-1..6 トレーサビリティ試験 | 決定論 | ⬜ 未着手 |

**LLM はまだ 1 トークンも使っていない。** 現時点の全数値は決定論的計算であり、再実行でバイト一致する。

---

## §2. 成果物の現況

### 機械可読層 `egl/structure/`（すべて DERIVED / regenerable、SoR ではない）

| ファイル | 行数 | 生成元 | 決定性 |
|---|---|---|---|
| `FILE_MANIFEST.jsonl` | 1,317 | git + filesystem | ✅ バイト一致 |
| `SYMBOL_INDEX.jsonl` | 1,215 | ast / regex | ✅ バイト一致 |
| `REACHABILITY.jsonl` | 427 | import グラフ BFS | ✅ バイト一致 |

生成スクリプト: `s1_manifest.py` / `s1_symbols.py` / `s1_reach.py`

未生成: `COMPONENT_INVENTORY` / `EDGE_INVENTORY` / `CLAIM_EVIDENCE_INDEX` / `HISTORY_EVENTS` / `CONTRADICTIONS` / `UNRESOLVED`

---

## §3. 実行ログ（追記部）

### §3.1 — 2026-07-22 Stage 1a/1b/1c 完了

#### 対象の確定

```
総ファイル数            1,317   (__pycache__ / .git 除く)
  T1_TRACKED             826    git 管理下
  T2_RUNTIME             491    実行時記録（executed 列の唯一の根拠源）
```

内訳（tier 別）:

| classification | T1 | T2 |
|---|---|---|
| runtime_trace | 4 | **341** |
| source | 247 | 31 |
| ledger | 217 | 42 |
| test | 147 | 10 |
| doc | 140 | 6 |
| artifact | 52 | 28 |
| event_store | – | 22 |
| archive | 14 | – |
| generated | 5 | 12 |

リポ別: egl 495/30、twoder 204/351、dev-workcell 76/109、rri 37/1、ds 14/1（T1/T2）。

#### 抽出量

```
SYMBOL_INDEX 対象   python 427 / markdown 146 / json 588 / jsonl 54
定義シンボル総数    2,122
Python 総 LOC       44,914
import 文総数       2,215
parse error         0
```

#### 【所見 F1】live path は 68 ファイル / 9,810 LOC

live entrypoint 4 本（`twoder/webui.py`, `twoder/submit.py`, `twoder/operator.py`,
`dev-workcell/dw/dispatch.py`）からの import グラフ BFS：

| 分類 | files | LOC |
|---|---|---|
| **LIVE_REACHABLE** | **68** | **9,810** |
| TEST_ONLY | 157 | 13,808 |
| ARCHIVE_OR_EXPERIMENT | 97 | 9,748 |
| SUPPORT_OFF_LIVE_PATH | 66 | 7,503 |
| STANDALONE_ENTRYPOINT | 19 | 2,738 |
| ORPHAN（呼び出し元も CLI も無い） | 20 | 1,307 |

**全 Python の 16% / LOC の 22% しか live path 上に無い。** 最大到達深度は 4。
live のリポ別内訳: twoder 36 / rri 16 / dev-workcell 7 / egl 7 / ds 2。

> 注: TEST_ONLY 157 / ARCHIVE_OR_EXPERIMENT 97 は「無駄」を意味しない。
> 分類であって評価ではない（spec §5 の 6 分類へ Stage 6 で写像する）。

#### 【所見 F2】既存監査文書 `twoder/audit/MISSING_EDGES.md`（07-12）は stale

同文書 §11 の記述:
> RRI formal validation/handoff suite — `iec.validate_iec`, `resolved_intent.…`,
> `research_axis.…`, `rdec.…`, `request_resolution.…`, `need_validation.…`,
> `approved_rq_set.…`. All implemented + individually tested, **all unwired**.

本計算での実測:
```
twoder/rri_formal.py            <- twoder/submit.py           (depth 1)
  rri/rri/approved_rq_set.py    <- twoder/rri_formal.py       (depth 2)
  rri/rri/iec.py                <- twoder/rri_formal.py
  rri/rri/rdec.py               <- twoder/rri_formal.py
  rri/rri/need_validation.py    <- twoder/rri_formal.py
  rri/rri/request_resolution.py <- twoder/rri_formal.py
  rri/rri/research_axis.py      <- twoder/rri_formal.py
  rri/rri/resolved_intent.py    <- twoder/rri_formal.py
  rri/rri/rq_candidate.py       <- twoder/rri_formal.py
```
→ **DE-0231（2026-07-13, "RRI formal-validation suite wired into submit forward path"）で塞がっている。**
監査文書が書かれた翌日である。

**意義:** 本パイプラインが、人手の as-built 監査が捉えていない変化を独立に再検出した。
spec §7 の TR-4（陽性対照）の予行として機能している。ただし正式な TR-4 は Stage 7 で実施する。

#### 【インシデント I1】自己参照による決定性破壊（修正済み）

Stage 1a の初回実装で、導出物 `FILE_MANIFEST.jsonl` を `egl/structure/` に置いた結果、
2 回目の走査が自分自身を対象に含め、行数が 1,317 → 1,318 に増加した。

- **同型の先例:** DE-0132「live-ledger self-referential reproducibility bug, fixed by pinning input snapshot」
- **修正:** `egl/structure/*.jsonl`（T3_DERIVED）を走査対象から除外（`s1_manifest.py`）。
- **検証:** 再実行でバイト一致を確認。
- **一般化:** 導出層は自身を観測対象にしてはならない。Stage 1e 以降も同じ除外を適用する。

---

## §4. 未解決 / 既知の限界（UNRESOLVED）

### 【U1】`wired` は現状「必要条件」であり十分条件ではない ★最重要

Stage 1c の到達可能性は **module import 単位**である。
`A.py` が `B.py` を import していても、`B` の当該関数が実行経路で呼ばれる保証はない。

- 影響: 所見 F1 の 68 ファイルは **上限値**である。symbol 単位ではこれより小さくなりうる。
- 対策: Stage 1d（symbol 単位到達可能性）を Qwen 投入前に実施する。
  ここを甘くすると、その上に載る Component / Edge / 系譜のすべてが甘くなる。
- **現時点で「68 ファイルが稼働中」と主張してはならない。**「68 ファイルが到達可能」までが言えること。

### 【U2】`introduced_by_de` の解決率 57%

826 T1 ファイル中 473 件のみ、初出 commit のメッセージから DE を解決できた。
残り 353 件は `ARTIFACT_REGISTRY` / CHANGE_LOG との突合が必要（Stage 5）。

### 【U3】`egl/docs/SUBMIT_2026-07-21/` にコードの複製がある

`patch_bridge.py` / `bridge_reconciler.py` / `runner_v0.2.3.py` 等が出荷束の展開物として
docs 配下に存在する。現分類では `ARCHIVE_OR_EXPERIMENT`。
Stage 6 の重複検出（同一 sha256 / 近接内容）で正式に扱う。

### 【U4】`executed` 列 未計算

`twoder/runs/` 337 トレース、`dev-workcell/events.jsonl`（4.0MB）、
`egl/data*/events.jsonl`、`ds/ds_events.jsonl`、`rri/rri_records.jsonl` は未解析。
現時点で「実際に動いた」ことは**一切主張していない**。

### 【U5】Taka 裁定待ち 4 点（spec §10）

1. `ARTIFACT_REGISTRY.used_by_live_path`（210 件中 198 件が `unknown`）への計算値書き戻しの可否
2. 生成物の置き場所を `egl/structure/` とすることの可否（第 6 リポを作らない判断）
3. TERMINAL 条件 T-3（欠損辺 producer 仕様の導出）を必須とすることの可否
4. 予算上限（Qwen 生成トークン / 壁時計時間）

### 【U6】本作業自身が支流化するリスク

spec §0 の反・支流条項を参照。地図の完成を成功としない。
T-3（`PROJECT_GOAL.md §3` の欠損辺 ①→② の producer 仕様導出）に到達しなければ失敗として記録する。

---

## §5. 次の一手

**Stage 1d: symbol 単位到達可能性**（決定論、LLM 不要）。U1 を閉じるまで Qwen は投入しない。
