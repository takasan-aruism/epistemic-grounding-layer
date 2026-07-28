# 設計/監査 → MGR（写: Taka / IMPL）: **D-46 — 4件の分類。★3件は「既定義」だった。ただし定義は★本番に接続されていないファイルに在る**

- `BUILD_ROLE: 参照`（**調査のみ。★実装案を書いていない・何も作っていない・投入していない・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8` — `§12` を最大版で読んだ値）**
- **受領**: `CC_MGR_2026-07-28_D46_REGISTER_4_UNDEFINED_AND_SURVEY.md`（Taka 逐語 §1）

## 0. ★結論
> **★「未定義事項」として登記を命じられた3件のうち、★3件とも既に定義が在った。**
> **★ただし定義は `rri/rri/request_thread.py` に在り、そのファイルは★本番から一度も呼ばれない**（`G-45`）。
> **∴ 正しい分類は「未定義」ではなく★「定義は在るが接続されていない」である。** **本日10回目の「既存の道が既に在った」。**

## 1. 採番した id（v2.8 §6-8 に従い、内容で指名されたものに私が採番）
| # | 内容 | **採った id** |
|---|---|---|
| 1 | RRI の終了条件 | **`G-51`** |
| 2 | RRI への再入時の扱い | **`G-52`** |
| 3 | RRI が保持する状態と、その正規保存場所 | **`G-53`** |
| 4 | Event Trace から RRI の判断結果・根拠・残差記録へ辿る参照構造 | **`G-54`** |

## 2. ★調査（総件数・確認件数・打ち切り無し）
```
調査先と件数（★head / tail / limit / -m を1つも使っていない）:
  RRI 本体のファイル      総24 / 確認24 / 打ち切り無し
  終端状態の定義走査      総16行 / 確認16 / 打ち切り無し
  再入(RESUME_PRIOR)走査  総8行 / 確認8 / 打ち切り無し
  残差(residual)走査      総7行 / 確認7 / 打ち切り無し
  front door 実測         4回（/api/resolve × 2・/api/state・/api/tasks）
```

## 3. ★4件 × 3分類

### `G-51` RRI の終了条件 — **★既定義（コード。ただし本番未接続）**
```
再現: sed -n '/^TRANSITIONS = {/,/^}/p' rri/rri/request_thread.py  ほか

STATES = ("SOFT","NARROWING","AWAITING_HUMAN","RESOLVED","DISPATCHABLE","CLOSED")
("NARROWING","RESOLVED"): ("all_disposed","suspense_settled","all_gaps_presented","thread_accepted")

advance_state が RESOLVED へ進むとき、コードが強制する条件:
  ・in_flight_count == 0 でなければ RThreadIllegalTransition
  ・OPEN_GAP の全てが GAP_PRESENTED 済でなければ「unpresented OPEN_GAP remains before RESOLVED」
  ・THREAD_ACCEPTED が無ければ「THREAD_ACCEPTED required for RESOLVED」
accept_thread は residual_gaps が open gap と完全一致しなければ RThreadResidualIncomplete
```
| | |
|---|---|
| **在る所** | `rri/rri/request_thread.py`（**★宣言ではなく、例外で強制されている**） |
| **★欠けている所** | **このファイルは本番から一度も呼ばれない**（`G-45`。呼び手0・実測済） |
| **∴** | **★「終了条件が無い」のではない。** **「終了条件は在るが、本番の RRI はそれを通らない」である** |

### `G-52` RRI への再入時の扱い — **★部分定義（★2つの機構が別々に在り、互いを知らない）**
| 機構 | 在る所 | 何が在るか | 何が無いか |
|---|---|---|---|
| **A. スレッド側** | `request_thread.TRANSITIONS` | **`("AWAITING_HUMAN","NARROWING"): ("human_replied",)`** ＝人間の返答による再入は定義済 | **★`RESOLVED` / `CLOSED` からの再入（REOPEN）が `TRANSITIONS` に無い。** 一度閉じたスレッドへの再入は**未定義** |
| **B. 依頼側** | `submit.py` | **`RESUME_PRIOR`**（`request_type.py:17` の6種の1つ）＋ `_active_2der_tasks()` ＋ **「盲目的に `active[-1]` を採らない」**（`submit.py:71` / DE-0165） | **★A と接続していない。** `RESUME_PRIOR` は DW task を継ぐが、**RRI スレッドの状態遷移には触れない** |

> **∴ 部分定義。** **★「人間が答えて戻る」は定義済、「同じ依頼が後から戻る」は依頼側だけに在り、スレッド側と繋がっていない。**

### `G-53` RRI が保持する状態と、その正規保存場所 — **★既定義（★ただし正典と本番で場所が違う）**
```
再現: rri/rri/request_thread.py:3
  「sole writer of rthread_events.jsonl。first-class store は event stream のみ(architecture)」
  project(thread_id) が event 列から state を導出
  check_conservation / check_account_conservation が保存則を検査
```
| | |
|---|---|
| **正典が指す保存場所** | **`rthread_events.jsonl`**（event stream から導出。**★state を直接持たない設計**） |
| **★本番が実際に書いている場所** | **`rri_records.jsonl`**（`intent_record` が `RREQ`/`RINT`/`RSIG` を採番。**★state を持たない**） |
| **∴** | **★「正規保存場所は定義されている。** **しかし本番はそこに書いていない」** |

### `G-54` Event Trace から RRI へ辿る参照構造 — **★部分定義（★一部は既に辿れる。実測した）**
```
再現: GET /api/resolve?id=ETR-f0fe8461c407 の RRI event（実物）
{ "event_id":"ETR-f0fe8461c407-0003", "parent_event_id":"…-0002", "component":"RRI",
  "function":"mint", "inputs":"{\"kind\": \"RESEARCH_SIGNAL\"}",
  "outputs":"{\"rri_record_id\": \"RSIG-00329\"}",
  "trace_id": null, "task_id": null }

再現: GET /api/resolve?id=RSIG-00329
  → ★resolved=True / kind=RESEARCH_SIGNAL / content・content_hash・ts を持つ
```
| 辿れるか | 対象 | 実測 |
|---|---|---|
| **★辿れる** | **RRI の記録 id（`RSIG`/`RREQ`/`RINT`）** | **Event Trace の `outputs` に載っており、front door で解決できる。`【実】`** |
| **★辿れない** | **判断結果**（`request_type` / `INTENT_STRATEGY` / `RRI_PREFLIGHT`） | **Event Trace に無い**（合流点は `intent_record.mint` であり、判断そのものは台帳を書かないため emit されない） |
| **★辿れない** | **残差**（`RRI_RESIDUAL`） | `submit.py:151` で **TRACE にのみ記録**。**front door に出ない**（`G-46` の35件の1つ） |
| **★辿れない** | **`trace_id` / `task_id` の紐付け** | **実物が `null`**（emit 側が渡していない） |

> **∴ 部分定義。** **★「id は辿れる。判断・根拠・残差は辿れない」が実測の答えである。**
> **★MGR の §5-2（Taka 訂正）「辿れない現状は設計の到達点ではなく欠落である」は、★この3項目について当たっている。**

---

## 4. ★4件×3分類の表（求められた形）
| # | 内容 | **既定義** | **部分定義** | **未定義** |
|---|---|---|---|---|
| **`G-51`** | RRI の終了条件 | **★○**（`request_thread` に例外で強制。**本番未接続**） | | |
| **`G-52`** | 再入時の扱い | | **★○**（人間の返答＝定義済／`RESOLVED` からの再入＝**無い**／依頼側 `RESUME_PRIOR` と未接続） | |
| **`G-53`** | 状態と正規保存場所 | **★○**（`rthread_events.jsonl`＋`project()`。**本番は別の場所に書いている**） | | |
| **`G-54`** | Event Trace → RRI | | **★○**（id は辿れる／判断・根拠・残差・`trace_id` は辿れない） | |

> **★「未定義」は0件である。** **★4件とも、程度の差はあれ定義か機構が既に在る。**
> **★探索範囲**: RRI 本体24ファイル全数／`twoder/submit.py` 全体／front door 4回。**`egl/docs` の正典文書は★全数走査していない**（§5-1）。

## 5. ★未確認（「全部見た」と書かない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`egl/docs` の正典文書を全数走査していない。** **∴ 文書側に別の定義が在る可能性を排除していない** | **CC-α / MGR が要ると言えば。★「無い」とは書いていない** |
| 2 | `G-51` の終了条件が「正しい終了条件か」は判断していない（**在るか無いかだけを答えた**） | — |
| 3 | `RESOLVED` からの再入が `TRANSITIONS` に無いことは実読だが、**別ファイルに再入機構が在る可能性は排除していない** | CC-α / 必要なら |
| 4 | **私は実装案を1つも書いていない**（Taka 明示「今すぐ実装へ進めない」） | — |

---
*CC-α D-46（調査のみ・実装案なし）。★結論=「未定義事項」として登記を命じられた3件は**3件とも既に定義が在り**、ただし定義は `rri/rri/request_thread.py` に在ってそのファイルは**本番から一度も呼ばれない**（`G-45`）∴ 正しい分類は「未定義」ではなく**「定義は在るが接続されていない」**——本日10回目の「既存の道が既に在った」。★採番=`G-51` 終了条件／`G-52` 再入／`G-53` 状態と正規保存場所／`G-54` Event Trace からの参照構造。★調査は総件数・確認件数を明記し `head` を1つも使っていない（RRI 本体24ファイル全数／終端状態16行／再入8行／残差7行／front door 実測4回）。★分類=**`G-51` 既定義**（`STATES` 6状態・`TRANSITIONS`・`advance_state` が RESOLVED へ進む際に `in_flight_count==0`・全 OPEN_GAP の提示・`THREAD_ACCEPTED` を**例外で強制**し、`accept_thread` は残差の完全一致を要求＝宣言でなく強制。ただし本番未接続 ∴「終了条件が無い」のではなく「在るが本番の RRI はそれを通らない」）／**`G-52` 部分定義**（`("AWAITING_HUMAN","NARROWING"):("human_replied",)` ＝人間の返答による再入は定義済だが**`RESOLVED`/`CLOSED` からの再入が `TRANSITIONS` に無い**。依頼側には `RESUME_PRIOR` と `_active_2der_tasks` と「盲目的に `active[-1]` を採らない」(DE-0165) が在るが**スレッド側と接続していない**＝2機構が互いを知らない）／**`G-53` 既定義**（正典は `rthread_events.jsonl` の event stream のみを first-class store とし `project()` で state を導出、`check_conservation` が保存則を検査。**しかし本番が実際に書いているのは `rri_records.jsonl` で state を持たない** ∴「正規保存場所は定義されているが本番はそこに書いていない」）／**`G-54` 部分定義**（実測: Event Trace の RRI event は `outputs` に `rri_record_id: RSIG-00329` を載せ、`/api/resolve?id=RSIG-00329` が **resolved=True** で解決する＝**id は辿れる**。しかし**判断結果**(`request_type`/`INTENT_STRATEGY`/`RRI_PREFLIGHT`)は Event Trace に無く（合流点が `intent_record.mint` で判断自体は台帳を書かないため）、**残差**(`RRI_RESIDUAL`)は TRACE にのみ在り front door に出ず（`G-46`）、**`trace_id`/`task_id` は実物が `null`** ∴「id は辿れる。判断・根拠・残差は辿れない」——Taka 訂正「辿れない現状は欠落である」はこの3項目について当たっている）。★**「未定義」は0件**で、4件とも程度の差はあれ定義か機構が既に在る。★未確認=**`egl/docs` の正典文書を全数走査しておらず文書側に別の定義が在る可能性を排除していない**（「無い」とは書いていない）／終了条件が「正しいか」は判断していない（在るか無いかだけ）／`RESOLVED` からの再入が別ファイルに在る可能性は排除していない／**実装案を1つも書いていない**。*
