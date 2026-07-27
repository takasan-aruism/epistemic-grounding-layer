# 設計/監査 → MGR（写: Taka / IMPL）: **D-40b — `UTT-0769`（本線を通る発話）の実行トレース。★RRI の段2〜3e は「コード上のみ確認」から出られない**

- `BUILD_ROLE: 参照`（**調査のみ。コードを1行も変えず・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- 権限: `CC_MGR_2026-07-28_D40_RECEIVED_EXTEND_TO_EXISTING_RECORDS_ONLY.md`（既存レコードに限り範囲拡大）
- **★`UTT-0772` の表（`..._D40_TRACE_UTT0772.md`）は確定済として残す。本文書は別の表である**（条件2）

## 0. 対象の選定（条件3・選ばなかったものも書く）
```
再現: GET /api/resolve?id=UTT-0766〜0769
UTT-0769  origin=MACHINE_SUBMIT  speaker=USER    「宛: 設計/監査(CC-α) 台帳IDの問い合わせに4状態で答える薄いアダプタを…」
UTT-0768  origin=MACHINE_SUBMIT  speaker=USER    ★UTT-0769 と同一文面
UTT-0767  origin=UNSPECIFIED     speaker=SYSTEM  「[AUTHORITY]AUTHORITY_APPROVAL_GRANT APPROVAL-…」
UTT-0766  origin=UNSPECIFIED     speaker=SYSTEM  同上
```
| | |
|---|---|
| **選んだ** | **`UTT-0769`** ——**DE 登録依頼ではない**ので段1.5 の fast path に入らず、**本線（段2〜段4）に進むはずの唯一の型** |
| 選ばなかった | `UTT-0768`（**同一文面。冪等なので同じ task を指し、新しい情報が出ない**）／`UTT-0766`〜`0767`（**SYSTEM の authority 記録であって依頼ではない**） |
| **★選定で結論を作っていないか** | **本線を通る型はこの1つしか無かった。** **選択肢の中から都合の良いものを選んだのではない** |

**★`UTT-0769` も `origin=MACHINE_SUBMIT` である。** **Taka の発話ではない**（D-37 の結論は変わらない）。

---

## 1. ★13項目（同じ様式・同じ4区分）
| # | 項目 | 区分 | 根拠 |
|---|---|---|---|
| **1** | DS 受付後に呼ばれた関数 | **実行確認済み** | `UTT-0769` が front door から引ける。`ts_source=DEFAULT`・`preceding_utterance_ref=UTT-0768` まで記録されている ∴ `phase0.record_utterance` は走った |
| **2** | `request_type` の実行・入出力 | **★未確認** | **走ったはずだが、その記録を front door から引けない**（§2）。**誰が=CC-α / いつ=§3 の裁定後** |
| **3** | `context_binding` の実行・入出力 | **★未確認** | 同上 |
| **4** | `intent_strategy` の実行 | **★未確認** | 同上 |
| **5** | `request_resolution.select_strategy` | **★呼ばれなかった** | `if formal_candidates:` の中にあり、**`webui.py:536` は `SUB.submit(b.get("raw",""))` しか呼ばない** ∴ 引数が届かない。**コードで確定する**（記録の不在に依らない） |
| **6** | 4軸それぞれの生成 | **`context_anchoring` = 未確認 / 他3軸 = 呼ばれなかった** | 他3軸は**本番に実装が無い**（D-18・`egl/structure` とテストにのみ存在）∴ 生成する関数が存在しない |
| **7** | `formal_candidates` の実際の値 | **実行確認済み（間接）** | `webui.py:536` が渡さない ∴ **`None`** |
| **8** | 7戦略の最終決定値と決定主体 | **★未確認** | **決定主体は `intent_strategy`（LLM）であるとコードで言えるが、この発話の決定値を引けない**（§2） |
| **9** | 次アクションの決定 | **実行確認済み（間接）** | **`TASK-2DER-B9B4DA3B` が front door から引ける**（`state=READY_FOR_AUDIT`）。**その task id は `sha1(UTT-0769 の raw_text)` である**（`submit.py:405`）∴ 段4 の ROUTING が `DW_IMPLEMENTATION` を選び `create_task` した |
| **10** | EGL に何が書かれたか | **★未確認** | 段3a の `answer_question` は読み取りで、書き込みは `EGL_FORWARD_ADMISSION`（段4）。**この発話に紐づく DE id を引く手段が無い** |
| **11** | DW が起動したか | **★実行確認済み** | **`TASK-2DER-B9B4DA3B` が実在し `events=8` / `state=READY_FOR_AUDIT`**（front door で確認） |
| **12** | 勘定科目 / Sub-ID / `task_id` の割当 | **`task_id`=実行確認済み / 勘定科目=呼ばれなかった / Sub-ID=存在しない** | `task_id` は §9 のとおり。勘定科目は**登記経路に実装が無い**（`G-02`）。Sub-ID は**機構が存在しない**（明細分解は未実装） |
| **13** | front door から何が読み出せたか | **実行確認済み** | **発話レコード（`UTT-0769`）と DW task（`TASK-2DER-B9B4DA3B`）の2つ。** **段2〜3e の中間結果は1つも引けない** |

---

## 2. ★なぜ段2〜3e が「未確認」から出られないのか【監査:CC-α】
```
再現: GET /api/resolve?id=TRACE-0769   → resolved: false
```
**`submit()` の中間結果（`RRI_REQUEST_TYPE` / 文脈束縛 / `INTENT_STRATEGY`）は `TRACE` に入る。**
**`TRACE` は `twoder/runs/*.trace.json` に書かれるが、★その横読みは v1.8 で潰されている**（正しい措置）。
**`/api/resolve` は `TRACE-…` を解決しない。**

> **∴ 「段2〜3e が何をしたか」を front door から知る手段が、いま存在しない。**
> **∴ これは `UTT-0769` の問題ではなく、★参照経路の欠落である。**

**★これが Taka の問い「RRI が本番でどの経路を通っているか」に、いま答えきれない理由である。**
**∴ 新しい Gap として登録する（`G-31`）。**

## 3. 裁定を仰ぐ（★私は作らない）
| 選択肢 | 内容 |
|---|---|
| **(a)** | **`/api/resolve` が `TRACE-…` を解決できるようにする**（`twoder/runs/` の既存ファイルを引くだけ。**新しい記録を作らない**） |
| (b) | 段2〜3e の結果を DS/EGL に記録する | **★新しい記録が増える。** Taka の禁止に触れうる |
| (c) | 確定を諦め、「front door からは確定できない」を答えとして残す |

**【設計:CC-α】(a) を推す。** **既に在るファイルを、既に在る口から引けるようにするだけである。** **(b) は記録を増やす。**
**★ただし「膨らませる」に当たるかは MGR の判断であり、私は作らない。**

## 4. 禁止事項の遵守
- **コードを1行も変えていない。投入していない。新しい経路を作っていない。**
- **`UTT-0772` の表を書き換えていない**（条件2）。
- **様式（13項目・4区分）を変えていない**（条件4）。

---
*CC-α D-40b。対象は `UTT-0769`（DE 登録依頼でないので fast path に入らず本線に進む唯一の型。`UTT-0768` は同一文面で冪等ゆえ新情報なし、`UTT-0766/0767` は SYSTEM の authority 記録で依頼ではない）——★選択肢の中に本線型は1つしか無く、都合の良いものを選んだのではない。`UTT-0769` も `origin=MACHINE_SUBMIT` で Taka の発話ではない。★13項目=1 DS 受付は実行確認済み／2・3・4・8・10 は**未確認**（走ったはずだが記録を front door から引けない・誰が=CC-α/いつ=§3 の裁定後）／5 は**呼ばれなかった**（`webui.py:536` が `formal_candidates` を渡さないとコードで確定・記録の不在に依らない）／6 は `context_anchoring` が未確認で他3軸は本番に実装が無く**呼ばれなかった**／7 は `None`（間接の実行確認）／9 は**実行確認済み**（`TASK-2DER-B9B4DA3B` が引け、その id は `sha1(UTT-0769 の raw_text)`）／11 は**実行確認済み**（`events=8`/`READY_FOR_AUDIT`）／12 は `task_id` のみ確認・勘定科目は登記経路に実装が無く・Sub-ID は機構が無い／13 は発話と DW task の2つだけ。★段2〜3e が未確認から出られない理由=中間結果は `TRACE` に入り `twoder/runs/*.trace.json` に書かれるが横読みは v1.8 で潰されており(正しい措置)、`/api/resolve` は `TRACE-…` を解決しない(実測 `resolved:false`) ∴ **front door から段2〜3e を知る手段が存在しない＝参照経路の欠落**（`G-31` として登録）。裁定を仰ぐ=(a) `/api/resolve` が `TRACE-…` を引けるようにする（既存ファイルを既存の口から引くだけ・新しい記録を作らない）を推し、(b) 記録を増やす案は採らない、(c) 諦める。私は作らない。*
