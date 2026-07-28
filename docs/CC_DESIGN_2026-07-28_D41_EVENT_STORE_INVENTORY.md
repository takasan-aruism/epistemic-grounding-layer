# 設計/監査 → MGR（写: Taka / IMPL）: **D-41 — 既存の記録機構 棚卸し。★10回目は在った。DW `events.jsonl` が唯一の追記式・本番稼働・provenance 付き基盤である**

- `BUILD_ROLE: 参照`（**調査のみ。何も作っていない・Hook を1つも足していない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **受領**: `CC_MGR_2026-07-28_D41_INVENTORY_EXISTING_EVENT_STORES_FIRST.md`

## 0. ★結論（先に3行）
> **①「10回目を作る危険」は当たっていた。** **既に在る**: `provenance{trace_id, ds_input_id, …}` が **DW `events.jsonl` の `CREATE` payload に封印されている**（`submit.py:419-429` → `workcell.create_task`）。
> **②★私の `G-31`「発話単位の帰属ができない」は言い過ぎだった。** **`trace_id = sha1(utterance_id + ts)` は★発話ごとに違う。** **帰属はできる。できないのは★過去分の保存である。**
> **③ 最重要項目（親 Event ID）は、★どの機構も持っていない。** **本番に在る親子は `preceding_utterance_ref`（発話の直列）1本のみで、イベントの親子ではない。**

---

## 1. Q1 — 記録機構の全列挙【監査:CC-α】
```
再現: grep -rn "\.jsonl" --include=*.py {ds,rri,egl,dev-workcell,twoder}
     + 各書き手関数を実読
```
| # | 機構 | 書き手 | 追記式 | **本番経路から書かれるか** |
|---|---|---|---|---|
| **1** | **DW `events.jsonl`** | `dev-workcell/dw/workcell.py:72 _append_event` | **★追記式（`open("a")`）** | **★書かれる**（`create_task`/`record_plan`/`record_generate`…） |
| **2** | **DS `ds_events.jsonl`** | `ds/ds/phase0.py record_utterance` / `record_dialogue_event` | **★追記式** | **★書かれる**（`submit.py` 段1） |
| **3** | **RRI `rthread_events.jsonl`** | `rri/rri/request_thread.py:68 _append` | **★追記式** | **★書かれない**（§1-2） |
| **4** | **TRACE `twoder/runs/<task_id>.trace.json`** | `twoder/submit.py:33 _rec` | **★追記式でない（dict 上書き）** | 書かれる |
| 5 | `artifact_registry` CHANGE_LOG | `twoder/artifact_registry.py:136 record_change` | 追記式 | Claude が手で呼ぶ |
| 6 | 承認イベント | `twoder/authority.py:122 _record_approval_event` | **DS へ相乗り** | 書かれる |
| 7 | EGL `structure/*.jsonl`（`COMPONENT_INVENTORY` 等 60+） | `egl/structure/s*.py` | 追記/再生成 | **★実行イベントではない**（コードを解析した結果。本番経路から呼ばれない） |
| 8 | EGL `AUTONOMY_LEDGER` / `HANDOFFS` | `egl/autonomy/*.py` | 追記式 | **未確認**（自律系。本件の経路外） |

### 1-1. ★先例として重要（§5 で使う）
> **`authority.py:122` の docstring: 「Persist grant/consume on the DS event stream …★`No new SoR`」**
> **∴ 「新しい保存先を作らず既存の event stream に相乗りする」は、★既にこの系で採られた設計である。** **我々が発明する話ではない。**

### 1-2. ★#3 は「在るのに繋がっていない」【監査:CC-α】
```
再現: grep -rn "request_thread" --include=*.py twoder rri ds | grep -v test
結果: rri/rri/request_thread.py 自身の4行のみ。★外部の呼び手が1つも無い。
```
**`request_thread.py:3` は「first-class store は event stream のみ(architecture)」と書いている。**
**∴ RRI 側の event stream 設計は★存在するが、`submit()` から一度も呼ばれない。** **`G-33` として登録する。**

---

## 2. Q2 — 12項目の充足表（○=持つ / △=部分 / ×=無い）
| 項目 | **DW events** | **DS events** | **TRACE** | RRI rthread |
|---|---|---|---|---|
| **Event ID** | **×**（保存しない。読み出し時に `_ordinal` を付けるだけ＝**位置であって id でない**） | **○** `utterance_id` / `dialogue_event_id` | × | ○ `_mint` |
| **★親 Event ID** | **×** | **△** `preceding_utterance_ref`（**直列。親子でない**） | × | **×** |
| **Session ID** | **△** `run_id`（worker 実行単位。submit 単位でない） | × | × | △ `thread_id` |
| **Request ID** | **○** `task_id` | × | **○** `TRACE_ID` | ○ |
| **Timestamp** | **○** `ts` | ○ | **×** | ○ |
| **Component 名** | **△** `role`+`identity`（`MANAGER`/`WORKER` 等。関数の所属でない） | △ `actor` | × | × |
| **Function 名** | **×**（`phase` は工程名） | × | **△** キー名が段に対応 | × |
| 入力 | △ `payload` | ○ `raw_text` | △ | △ |
| 出力 | △ `payload` | △ | △ | △ |
| **次に渡した先** | **×**（`dispatch._MAP` から導出はできる） | × | × | × |
| 実行結果 | △ `payload.test_result` 等 | × | △ | ○ `to_state` |
| **Error 有無** | **△**（例外は `payload` に入る保証が無い） | × | **△** `boundary_failures` | × |

---

## 3. Q4（最重要）— ★親子関係を持つ機構は無い
```
再現: grep -rn "parent_event|parent_id|caused_by|prev_event|parent_ref" --include=*.py 全5repo
結果: ★1件も無い。 唯一の連結は ds/ds/phase0.py:106 の preceding_utterance_ref。
```
**`preceding_utterance_ref` は「直前の発話」を指す★直列リンクであり、「この処理を呼んだ処理」ではない。**
**しかも検証つき**（`phase0.py:109` — 未知の発話なら `ValueError`）。**∴ 壊れたリンクは入らない。**

> **∴ Q4 の答え: ★無い。** **「一本の系列」を作るには、親 Event ID を★新設するしかない。**
> **∴ ★これは私が決めない**（MGR §4-3）。**「既存では足りない。足りないのは `親 Event ID` と `Event ID` の2項目である」まで書いて上げる。**

## 4. Q5 — Session ID / Request ID 相当は★既に在る（新設不要）
```
再現: twoder/submit.py:312, 418
  trace_id = "TRACE-" + sha1( utterance_id + ts )[:10]
  provenance = {"trace_id":…, "ds_input_id": utterance_id, "ds_thread_id":…,
                "rri_request_id":…, "rri_intent_id":…, "dw_task_id":…}
  → kp["provenance"] → W.create_task(dw_task, …, kp, ts, …)
  → workcell.create_task:322 payload={"knowledge_packet": kp} → _append_event(… "CREATE" …)
```
> **★∴ provenance は DW の追記式 event log の `CREATE` payload に、既に封印されている。**
> **∴ `Request ID` = `trace_id`（発話ごとに一意）／`Session ID` = `conversation_id`・`ds_thread_id`。** **どちらも新設不要。**

### 4-1. ★`G-31` を訂正する（3度目の同型を避けるため、先に書く）
| | |
|---|---|
| 旧 `G-31` | 「TRACE が上書きされるので**発話単位の帰属ができない**」 |
| **新 `G-31`** | **帰属はできる**（`trace_id` は発話ごとに一意で、`CREATE` payload に永続する）。**できないのは★過去分の保存である** |

**★保存の形が2つあり、どちらも「途中」を落とす:**
| 機構 | 同じ文面を3回投入したとき残るもの |
|---|---|
| **DW `CREATE`** | **★最初の1回**（`create_task:320` が `already exists` で `WorkflowViolation`、`submit.py:434` が `except: pass` で握り潰す） |
| **TRACE ファイル** | **★最後の1回**（`webui.py:541` が同名で上書き） |

**∴ 「どの発話が通ったか」は最初と最後だけ分かり、間が消える。** **★これが `G-31` の本体である。**

### 4-2. ★TRACE の、もっと手前の限界（今回まで気づいていなかった）
```
再現: grep -oP '_rec\("\K[A-Z_0-9]+' twoder/submit.py | sort | uniq -c | sort -rn
  総キー 56 / 総呼び出し 114 / ★18キーが複数回書かれる
  NEXT_LEGAL_OPERATION 14回 / DISPATCH_RESULT 9回 / RRI_RESOLVED_INTENT 8回 …
根拠: submit.py:33  def _rec(k, v):  _T()[k] = v      ← ★dict への代入。前の値は消える
```
> **∴ TRACE は系列ではなく★「各キーの最後の値」のスナップショットである。**
> **∴ ★1回の submit の中ですら、途中経過が消えている。** **`NEXT_LEGAL_OPERATION` は14回書かれて1個しか残らない。**
> **∴ TRACE は Event Trace の基盤に★なれない。** **足りないのは `Timestamp` と `Event ID`＝順序を持てない。**

---

## 5. Q3 — 基盤になれるか
| 候補 | 判定 | **足りないものを★項目名で** |
|---|---|---|
| **DW `events.jsonl`** | **★最有力** | **`Event ID`** / **`親 Event ID`** / **`Function 名`** / **`次に渡した先`**（4項目） |
| DS `ds_events.jsonl` | 補完役 | `親 Event ID`・`Component 名`・`Function 名`・`次に渡した先`・`実行結果`・`Error` |
| TRACE | **★不可** | `Event ID`・`親 Event ID`・`Timestamp`（§4-2） |
| RRI rthread | **★不可（現状）** | **呼び手が存在しない**（§1-2） |

**【設計:CC-α】DW `events.jsonl` を基盤に推す。理由:**
1. **追記式で、`submit` から `AUDIT` まで★同じ1本に入る**（唯一、複数層をまたいで既に書かれている）
2. **provenance（`trace_id`/`ds_input_id`）を既に運んでいる**（§4）
3. **`authority.py` の先例（`No new SoR`）と同じ形で相乗りできる**

> **★ただし `Event ID` と `親 Event ID` の2項目は、既存のどの機構にも無い。**
> **∴ 「既存では足りない。足りないのは `Event ID` と `親 Event ID` の2項目。新設が要る」——★ここで止めて MGR に上げる。** **私は決めない。**
> **★なお「新しい保存先」は要らない。要るのは★既存レコードへの2フィールド追加である。** **常設命令 §0-2（新規の台帳を作らない）に触れない形が在ることを、判断材料として添える。**

## 6. Q6/Q7 — 「呼ばれなかった処理」（★できないことを先に）
**Hook は「実行された」しか取れない。** **一覧の候補を実物で当たった:**
| 候補 | 実在 | **一覧として使えるか** |
|---|---|---|
| **`dispatch._MAP`**（`dev-workcell/dw/dispatch.py:28`） | **○ 実在・8状態** | **★使える。** 状態→次工程が全網羅で、**到達しなかった工程を差で出せる** |
| `EXEC_ARCH` の `components`(21)/`edges`(8) | ○ 実在 | **△** 我々が手で書いた資料であり、★コードから再生成されない |
| `egl/structure/COMPONENT_INVENTORY.jsonl` / `REACHABILITY.jsonl` | ○ 実在（`s3_components.py`） | **★候補として有望だが未確認** |
| `submit()` の段構成 | ○ | **×** 一覧が存在しない。`_rec` のキー56個は**書かれた所にしか無い**（分岐で書かれない段は最初から見えない） |

**★Q7（できないこと）を先に書く:**
> **`submit()` の内部については、「呼ばれなかった」は★出せない。** **一覧が無いためである。**
> **出せるのは「★この段に到達しなかった」だけであり、それも `_rec` が在る段に限る。**
> **∴ 完了条件「呼ばれなかった処理も識別できる」は、★DW の工程については満たせるが、`submit()` の内部については満たせない。**
> **★これを満たそうとすると `submit()` の全段に Hook を入れることになり、それは「最小限の Hook」ではない。** **裁定を要する。**

## 7. ★未確認範囲（「全部見た」と書かない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`egl/autonomy/*`（`AUTONOMY_LEDGER`/`HANDOFFS`）の中身** | CC-α / D-41 続行の指示が出れば |
| 2 | **`COMPONENT_INVENTORY.jsonl` が「呼ばれるはずの一覧」として使えるか**（中身を見ていない。**台帳直読は禁止のため front door 経由が要る**） | CC-α / 経路の裁定後 |
| 3 | **`egl/structure/*.jsonl` 60+ の個別内容** | 未着手 |
| 4 | **本表の「本番経路から書かれるか」は★実行で確かめていない**（コード読み。`grep` の呼び手有無まで） | CC-α / 投入許可が出れば |

## 8. 禁止事項の遵守
- **何も作っていない。Hook を1つも足していない。新しいファイル（本文書を除く）を作っていない。投入していない。台帳を直読していない。**
- **「新しい台帳を作ればよい」を結論にしていない**（§5: 要るのは2フィールド追加であって新しい保存先ではない、と書いた）。
- **足りない場合の決定を私がしていない**（§5 末尾で MGR に上げた）。

---
*CC-α D-41。★結論3行=①「10回目を作る危険」は当たっていた——`provenance{trace_id, ds_input_id, …}` は既に **DW `events.jsonl` の `CREATE` payload に封印されている**（`submit.py:419-429`→`workcell.create_task:322`）②★私の `G-31`「発話単位の帰属ができない」は言い過ぎで、`trace_id = sha1(utterance_id + ts)` は発話ごとに違うので帰属はでき、できないのは**過去分の保存**である ③最重要の**親 Event ID はどの機構も持っていない**（本番の親子は `preceding_utterance_ref` の直列1本のみ）。★機構は8つ: DW `events.jsonl`(追記式・本番○)／DS `ds_events.jsonl`(追記式・本番○)／RRI `rthread_events.jsonl`(追記式だが**呼び手が1つも無い**＝`G-33` 登録)／TRACE(**追記式でない。dict 上書き**)／`artifact_registry` CHANGE_LOG／承認イベント(**DS へ相乗り＝`authority.py:122` が `No new SoR` と明記＝先例**)／EGL `structure/*`(コード解析であって実行イベントでない)／EGL autonomy(未確認)。★12項目表で DW events は `Event ID`/`親 Event ID`/`Function 名`/`次に渡した先` の4項目が×。★`Session ID`/`Request ID` は**既に在り新設不要**(`trace_id`/`conversation_id`)。★保存の形が2つあり両方とも途中を落とす=DW `CREATE` は**最初の1回**しか残らず(`create_task:320` が `already exists` で例外→`submit.py:434` が握り潰す)、TRACE ファイルは**最後の1回**しか残らない(`webui.py:541` 上書き)∴間が消えるのが `G-31` の本体。★今回まで気づいていなかった TRACE の手前の限界=`_rec` は `_T()[k]=v` の dict 代入で、総呼び出し114に対しキーは56、**18キーが複数回書かれ**(`NEXT_LEGAL_OPERATION` は14回)∴**1回の submit の中ですら途中経過が消える**——TRACE は系列でなくスナップショットなので基盤になれない。★基盤は DW `events.jsonl` を推す(複数層をまたいで既に1本に入る／provenance を既に運ぶ／`authority` と同じ形で相乗りできる)が、**足りないのは `Event ID` と `親 Event ID` の2項目**で、ここで止めて MGR に上げる（私は決めない）。**なお新しい保存先は要らず、要るのは既存レコードへの2フィールド追加**なので常設命令 §0-2 に触れない形が在ることを判断材料に添える。★Q6/Q7=「呼ばれなかった」の一覧は `dispatch._MAP`(8状態・全網羅)なら差で出せるが、**`submit()` 内部については一覧が存在せず出せない**（`_rec` のキーは書かれた所にしか無い）∴完了条件は DW の工程では満たせるが `submit()` 内部では満たせず、満たそうとすると全段に Hook を入れることになり「最小限の Hook」ではなくなる——裁定を要する。★未確認範囲4件を明記（EGL autonomy／`COMPONENT_INVENTORY` の中身（台帳直読禁止のため front door 経由の裁定が要る）／`structure/*` 60+／本表は実行で確かめておらずコード読みである）。*
