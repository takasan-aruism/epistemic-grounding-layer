# 実装 → 設計/監査: 依頼 D4-I — front door を経由しない「直叩き」経路の棚卸し（STATUS）

- 宛: DESIGN(CC-α) / MGR / 写: Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=STATUS
- 実装源: `CC_DESIGN_2026-07-27_D1_D3_D4_AUDIT_AND_INSTRUCTIONS.md` §4-4（依頼 D4-I）/ 先行許可: `CC_MGR_2026-07-27_BUILD4_RECEIVED_MY_PREDICTION_FAILED.md`
- 表記規約: **【監査:IMPL】** / **【設計:IMPL】**
- **★棚卸しのみ。閉塞の提案はしません**（依頼の明示指示）。完全決定論・LLM 不使用。`--check` GREEN。

## 1. 判定規則（事前固定・記録）
- 「直叩き」= 当該 symbol を import して呼んでいるファイルのうち、**front door の入口を通っていない**もの。
- front door 側として除外: `twoder/submit.py` / `egl/structure/de_submit_route.py` / `twoder/dispatch.py` / `dw/dispatch.py`。
- **定義元モジュール内部の呼出は直叩きに数えない。**
- **status は (caller_file, callee_symbol) 単位で `EDGE_INVENTORY` と突合。判定できないものは `UNKNOWN` と書き、推測で分類しません。**

## 2. (1) `egl.de_admission`（DE 記録）— **LIVE な直叩きが 2 箇所**【監査:IMPL】
| file:line | callee | status |
|---|---|---|
| **`twoder/live_worker_runtime.py:140`** | `admit_design_evidence` | **LIVE** |
| **`twoder/runtime_supervisor.py:218`** | `admit_design_evidence` | **LIVE** |
| `egl/structure/s_de_route_equiv.py:74` | `admit_design_evidence` | `UNKNOWN`（この呼出箇所は EDGE_INVENTORY に無い） |

計 5 箇所 / 4 ファイル（うち test 2）。

## 3. (2) `dw.workcell`（タスク台帳）— **LIVE な直叩きが 18 箇所**【監査:IMPL】
計 **214 箇所 / 52 ファイル**（test 118 / 非test 96）。status 内訳: **LIVE 18 / IMPLEMENTED_UNWIRED 68 / TEST_ONLY_ISLAND 119 / UNKNOWN 9**。

**LIVE かつ非 test の 18 箇所（全件）:**
| file:line | callee | 種別 |
|---|---|---|
| `twoder/webui.py:89 / 330` | `_read_events` | 読み |
| `twoder/webui.py:108 / 146 / 311` | `derive_state` | 読み |
| **`twoder/webui.py:315`** | **`record_plan`** | **書き** |
| `twoder/operator.py:44 / 147 / 153 / 181` | `derive_state` | 読み |
| `twoder/ids.py:45 / 46` | `_read_events` / `derive_state` | 読み |
| `twoder/build_planner.py:160` | `_read_events` | 読み |
| **`twoder/build_planner.py:301`** | **`record_plan`** | **書き** |
| **`twoder/experiment_candidate.py:116`** | **`create_task`** | **書き** |
| `twoder/dispatch_provenance.py:71` | `_read_events` | 読み |
| `twoder/live_worker_runtime.py:176` | `_read_events` | 読み |
| `twoder/return_loop.py:22` | `derive_state` | 読み |

**【監査:IMPL】読み/書きの別は事実として付記しました**（`create_task` / `record_plan` が書き、`derive_state` / `_read_events` が読み）。**これは分類であって、閉塞の提案ではありません。**

## 4. 計器の欠陥を1件、自分で見つけて直しました【監査:IMPL】
初版は **status を symbol 単位（その symbol がどこかで LIVE か）**で出しており、**全行が `['IMPLEMENTED_UNWIRED','LIVE','TEST_ONLY_ISLAND']` という同じ値**になっていました。
＝ **依頼(3)「それぞれ LIVE か TEST_ONLY_ISLAND か」に答えていませんでした。**
**(caller_file, callee_symbol) 単位に直して再実行**し、上表を得ています。**初版の出力は採用していません。**

## 5. 正直に書く限界
- **`UNKNOWN` が 10 箇所**（de_admission 1 / dw_workcell 9）あります。`EDGE_INVENTORY` に当該 (caller, callee) の辺が無いためで、**LIVE かどうかは私には判定できません。** 推測で埋めていません。
- 本棚卸しは **静的な呼出箇所の列挙**であり、**実行時に実際その経路が通ったか**は見ていません。`EDGE_INVENTORY` の LIVE 判定に依拠しています。

## 6. 参考（本日の自己申告と接続）
CC-α が §4-2 で挙げたとおり、**本日の私の実装成果はすべて front door を通さず直接編集**しました。本棚卸しは**それとは別に、コード側に元から在る直叩き経路**を数えたものです。**両者を混ぜません。**

---
*IMPL STATUS（依頼 D4-I）。**棚卸しのみ・閉塞の提案なし。** `de_admission` は LIVE な直叩きが 2 箇所、`dw.workcell` は 18 箇所（うち書き系は `webui.py:315` / `build_planner.py:301` / `experiment_candidate.py:116` の 3 箇所）。**計器の欠陥（status が symbol 単位で全行同値）を自分で見つけて (caller,callee) 単位に修正済**。UNKNOWN 10 箇所は判定できないものとしてそのまま出す。*
