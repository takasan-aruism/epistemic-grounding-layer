# 設計/監査 → MGR（写: Taka / IMPL）: **裁定①の土台を front door で実証した。★同時に新事実 — CLI 投入は TRACE を1件も残さない**

- `BUILD_ROLE: 参照`（**調査のみ。投入していない・コードを変えていない・Hook を足していない・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **受領**: `CC_MGR_2026-07-28_D41_RULING_DW_EVENTS_AND_ESCALATE_UNCALLED.md`
- **権限**: 同 §4「未確認4件のうち front door で確かめられるものだけ進めてよい」——**私の §7-4（本番経路から書かれるかを実行で確かめていない）に該当する**

## 0. ★なぜこれを先にやったか
> **裁定① は「provenance が DW `CREATE` payload に既に封印されている」に乗っている。**
> **★その主張を、私はコード読みだけで書いた（`【読】`）。** **裁定の土台が `【読】` のままなのは危うい。**
> **∴ 既存レコードを front door から引いて実証した。** **投入していない。**

---

## 1. ★実証【実】
```
再現: T=$(cat twoder/.access_token)
      curl -s -u "taka:$T" "http://100.107.6.119:8770/api/claude_packet?task_id=TASK-2DER-B9B4DA3B"
（読み取り専用。webui.py:144 claude_packet が CREATE payload の knowledge_packet を返す）

workflow_state = READY_FOR_AUDIT
knowledge_packet.provenance = {
  "trace_id": "TRACE-330d22a317",
  "ds_input_id": "UTT-0761",          ← ★発話に紐づいている
  "ds_thread_id": null,
  "rri_request_id": "RREQ-00218", "rri_intent_id": "RINT-00235", "rri_research_signal_id": "RSIG-00273",
  "egl_source_refs": ["DE-0554"], "dw_task_id": "TASK-2DER-B9B4DA3B" }
```
| 主張 | 旧 | **新** |
|---|---|---|
| provenance が `CREATE` payload に封印されている | `【読】` | **★`【実】`** |
| provenance が front door から引ける | 未確認 | **★`【実】`**（`/api/claude_packet`） |
| `Session ID`/`Request ID` 相当が既に在る | `【読】` | **★`【実】`**（`trace_id`/`rri_request_id`/`rri_intent_id` が実データに在る） |

> **∴ 裁定① の土台は `【実】` になった。** **DW `events.jsonl` を基盤に据える判断は、実データで支えられている。**

## 2. ★両端しか残らないことの実証（推測でなく実値で）
| 記録 | この task について残っている発話 |
|---|---|
| **DW `CREATE` payload** | **`UTT-0761`** ← **★最初** |
| **TRACE ファイル** | **`UTT-0762`** ← 別の発話（前回 `/api/state` で実測） |
| **私が D-40b で追った発話** | **`UTT-0769`** ← **★どちらにも残っていない** |

**∴ 同一文面の4発話（`0761 / 0762 / 0768 / 0769`）のうち、実際に痕跡が在るのは2つだけである。**
**★これは推論ではない。3つの実値である。** **`G-31` の本体（過去分が保存されない）は実証された。**

---

## 3. ★新事実 — TRACE は「最後の1回」ですらない。**CLI 投入は1件も残さない**
```
再現①: grep -rn "trace.json" --include=*.py {ds,rri,egl,dev-workcell,twoder}
        → 書き手は twoder/webui.py:541,543 の★2箇所のみ

再現②: grep -n "return TRACE" twoder/submit.py
        → :113 :129 :155 :231 :254 :481  ★submit() は TRACE を「返す」だけで、1度もファイルに書かない
        → :487 print(json.dumps(t, …))   ★CLI は標準出力に出すだけ
```
> **∴ `python3 -m twoder.submit "…"` は、TRACE ファイルを★1件も作らない。**
> **∴ TRACE に残るのは「最後の webui 投入」であって「最後の投入」ではない。**

**★これが `UTT-0769` の痕跡が無い理由である。** **上書きされたのではなく、★最初から書かれていない可能性が高い。**
**★そして使用ガイド §4 は `python3 -m twoder.submit` を投入の作法として名指ししている。**
> **∴ 我々が「正しい入り方」として書いた経路が、★実行記録を1件も残さない経路である。**
> **∴ `G-36` として登録する。**

**★私の §4-1 の表を訂正する**（今日4度目の同型を避けるため、自分で先に書く）:
| | 旧 | **新** |
|---|---|---|
| TRACE ファイル | 「同じ文面を3回投入すると**最後の1回**が残る」 | **「最後の★webui 投入が残る。CLI 投入は最初から残らない」** |

## 4. ★小さいが記録する — `ds_thread_id` が `null`
```
submit.py:420  "ds_thread_id": (threads[0].get("thread_id") if threads else None)
実データ        "ds_thread_id": null      ← ★threads が空だった
```
**∴ provenance に欄は在るが、この実行では埋まっていない。** **`Session ID` 候補のうち `ds_thread_id` は★当てにできない。**
**∴ `Session ID` は `conversation_id` を採るべきである**（`trace_id` は発話単位＝`Request ID` 側）。
**★ただし `threads` が空になった原因は調べていない**（誰が=CC-α / いつ=MGR が要ると言えば）。

## 5. ★言えないこと（実証の限界を先に）
1. **1件の task で確かめた。** **全 task で provenance が入っている保証はない**（`create_task` に `provenance` の必須検査は無い）。
2. **webui プロセスは10時間前起動でソースより古い。** **本件は「保存済みレコードの読み出し」なので影響しないと考えるが、★断定しない。**
3. **`【実】` にしたのは §1 の3項目だけである。** **§2 の12項目表の残りは `【読】` のままである。**

## 6. 裁定への影響（★私は作らない）
- **裁定① は変わらない。** **むしろ土台が固くなった。**
- **★ただし裁定②（「呼ばれなかった」の範囲）に材料が1つ増えた**: **CLI 投入は TRACE を残さないので、「submit() の内部が見えない」は一覧の欠落だけでなく★記録先の欠落でもある。** **Taka に上げる文に足せる材料として渡す。**
- **私は Hook を1つも足していない。**

---
*CC-α。★裁定① の土台（provenance が DW `CREATE` payload に封印されている）をコード読み `【読】` のままにせず front door で実証した——`GET /api/claude_packet?task_id=TASK-2DER-B9B4DA3B`（読み取り専用・投入なし）で `provenance = {trace_id: TRACE-330d22a317, ds_input_id: UTT-0761, rri_request_id: RREQ-00218, rri_intent_id: RINT-00235, egl_source_refs: [DE-0554], dw_task_id: …}` を実取得 ∴ 「封印されている」「front door から引ける」「Session/Request ID 相当が既に在る」の3点が `【実】` に昇格し、裁定①は実データで支えられた。★両端しか残らないことも実値で実証=DW `CREATE` に残るのは `UTT-0761`(最初)、TRACE に残るのは `UTT-0762`、私が D-40b で追った `UTT-0769` は**どちらにも無い**——同一文面の4発話のうち痕跡が在るのは2つだけで、これは推論でなく3つの実値である。★新事実=`trace.json` の書き手は `webui.py:541,543` の2箇所のみで、`submit()` は `return TRACE` するだけで1度もファイルに書かず CLI は標準出力に出すだけ ∴ **`python3 -m twoder.submit` は TRACE を1件も作らない**——TRACE に残るのは「最後の webui 投入」であって「最後の投入」ではなく、`UTT-0769` の痕跡が無いのは上書きでなく**最初から書かれていない**可能性が高い。**そして使用ガイド §4 は `python3 -m twoder.submit` を投入の作法として名指ししている ∴ 我々が「正しい入り方」と書いた経路が実行記録を1件も残さない経路である**（`G-36` 登録）。自分の §4-1 の表を「最後の1回が残る」→「最後の**webui**投入が残る。CLI 投入は最初から残らない」に訂正した（今日4度目の同型を避けるため自分で先に書いた）。★小さい記録=`ds_thread_id` は実データで `null`（`threads` が空）∴ `Session ID` は `ds_thread_id` でなく `conversation_id` を採るべきで、`threads` が空になった原因は未調査。★言えないことを先に=1件の task でしか確かめておらず全 task の保証はない（`create_task` に provenance 必須検査は無い）／webui プロセスは10時間前起動でソースより古く、保存済みレコードの読み出しなので影響しないと考えるが断定しない／`【実】` にしたのは3項目だけで12項目表の残りは `【読】` のまま。★裁定①は変わらず土台が固くなっただけ。裁定②には材料が1つ増えた（CLI 投入が TRACE を残さないので「submit() の内部が見えない」は一覧の欠落だけでなく**記録先の欠落**でもある）——Taka に上げる文に足せる材料として渡す。Hook は1つも足していない。*
