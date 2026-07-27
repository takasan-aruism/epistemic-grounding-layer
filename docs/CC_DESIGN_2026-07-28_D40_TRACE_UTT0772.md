# 設計/監査 → MGR（写: Taka / IMPL）: **D-40 — `UTT-0772` の実行トレース。★この発話は fast path で早期に返っており、RRI の大半は走っていない**

- `BUILD_ROLE: 参照`（**調査のみ。コードを1行も変えていない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **典拠**: Taka（2026-07-28）「**コード上で呼ばれるように見えることと、実行時に呼ばれたことを分けてください**」

## 0. ★結論（先に）
> **`UTT-0772` は「開発エビデンスを登録: DE-? …」という DE 登録依頼である。**
> **∴ `submit()` の段1.5（DE admission fast path）に入り、★そこで `return TRACE` している。**
> **∴ `request_type` / `context_binding` / `intent_strategy` / ROUTING / DW は、この発話については★到達していない。**

**★これは「RRI が壊れている」ではない。** **この入力に対する設計どおりの経路である。**
**★しかし「RRI が本番でどの経路を通っているか」を `UTT-0772` で確定することは、★できない。** **理由は §4。**

---

## 1. 起点の記録（front door から引いた）【実行確認済み】
```
再現: GET /api/resolve?id=UTT-0772
utterance_id UTT-0772 / speaker USER / origin ★MACHINE_SUBMIT / relayed_by None / authored_by None
conversation_id taka-main / preceding_utterance_ref UTT-0769 / ts 2026-07-11T09:00:00 / ts_source CALLER
raw_text "開発エビデンスを登録: DE-? — live-worker minimal slice run SLICE-TASK-2DER-21F64D9D: task=TASK-2DER-21F64D9D,
          1-file change ['impl.py'], deterministi…"
```
**∴ 我々の build 作業が機械投入した DE 登録依頼である。** **Taka の発話ではない**（D-37 で既報）。

## 2. 早期 return の根拠（コード）
```
再現: sed -n '115,140p' twoder/submit.py
  _rec("RRI_ADMISSION_CLASSIFICATION", adm)
  if adm["is_admission_request"]:
      _rec("RRI_RESOLVED_INTENT", {"request_type": "DEVELOPMENT_EVIDENCE_ADMISSION", …})
      _rec("SELECTED_ACQUISITION_METHOD", "EGL_DE_ADMISSION"); _rec("DW_TASK_ID", None)
      if admission_payload is None:
          _rec("NEXT_LEGAL_OPERATION", "admission classified but no DE candidate packet supplied (no append)")
          return TRACE                                   ← ★ここで返る
      result = DEA.admit_design_evidence(...)
      …
```
**∴ 段1.5 より後（段2〜段4）は、この分岐では実行されない。**

---

## 3. ★13項目（Taka 指定の番号のまま・実行順）
| # | 項目 | 区分 | 根拠 |
|---|---|---|---|
| **1** | DS 受付後に呼ばれた関数 | **実行確認済み** | `UTT-0772` が front door から引ける（`record_type=UTTERANCE`）。∴ `phase0.record_utterance` は走った |
| **2** | `request_type` の実行・入出力 | **★コード上のみ確認** | 段3b は段1.5 の `return` より後。**この発話について走った記録は無い** |
| **3** | `context_binding` の実行・入出力 | **★コード上のみ確認** | 同上（段2） |
| **4** | `intent_strategy` の実行 | **★コード上のみ確認** | 同上（段3e） |
| **5** | `request_resolution.select_strategy` | **★コード上のみ確認** | `if formal_candidates:` の中。**既定 `None`・`submit(raw)` しか呼ばれていない**（D-18 で既報） |
| **6** | 4軸それぞれの生成 | **★コード上のみ確認**（3軸は**呼ばれる形すら無い**） | `context_anchoring` は `bind_context` 由来だが段2 に到達せず。他3軸は本番に実装が無い（D-18） |
| **7** | `formal_candidates` の実際の値 | **実行確認済み（間接）** | `webui.py:536` は `SUB.submit(b.get("raw",""))` のみ ∴ **渡されていない＝`None`** |
| **8** | 7戦略の最終決定値と決定主体 | **★呼ばれなかった** | **判定規則を満たす**: 段3e が走れば `TRACE` に `INTENT_STRATEGY` が必ず載る（Build 10R で「載る/載らない」を実測済）。**この経路は段3e に到達しない** |
| **9** | 次アクションの決定 | **実行確認済み** | `NEXT_LEGAL_OPERATION` が「admission classified but no DE candidate packet supplied (no append)」に設定される分岐。**`admission_payload` が渡されていない**（`webui` は渡さない） |
| **10** | EGL に何が書かれたか | **★書かれていない** | 上記のとおり `return` が `admit_design_evidence` の**手前**。**`LEDGER_ENTRY_ID` は設定されない** |
| **11** | DW が起動したか | **★呼ばれなかった** | `DW_TASK_ID` は `None` に設定される分岐（コード）。**`UTT-0772` を起点とする task は無い** |
| **12** | 勘定科目 / Sub-ID / `task_id` の割当 | **★どれも割り当てられていない** | 勘定科目は**登録経路に無い**（`G-02`）。`task_id` は段4 で `sha1(raw_input)`（未到達）。Sub-ID は**存在しない**（`G-06`/明細分解は未実装） |
| **13** | front door から何が読み出せたか | **実行確認済み** | **`UTT-0772` の発話レコード（§1 の全項目）。** それだけである |

### 3-1. ★「呼ばれなかった」を付けた2件の根拠（規則 §3 を守る）
- **#8**: **段3e が走れば `INTENT_STRATEGY` が `TRACE` に必ず載る**ことを、Build 10R で**前後比較で実測**している（旧プロセス=載らない／新プロセス=載る）。**∴「呼ばれれば必ず記録が残る」が確かめられている。**
- **#11**: **`DW_TASK_ID` は fast path で明示的に `None` が設定される。** **∴ 記録の不在ではなく、記録された `None` が根拠である。**
- **★それ以外は「コード上のみ確認」に留めた。** **記録が無いことを「呼ばれなかった」の根拠にしていない。**

---

## 4. ★`UTT-0772` では確定できないこと（黙って乗り換えない・MGR §4-5）
> **Taka の狙いは「現在の RRI が本番でどの経路を通っているか」の確定である。**
> **★`UTT-0772` は DE 登録依頼なので、RRI の本線（段2〜段4）を1つも通らない。**
> **∴ この発話を起点にする限り、RRI の実行経路は確定できない。**

**足りないもの（何が足りないかを書く・MGR §4-5）:**
| 必要なもの | 状態 |
|---|---|
| **DE 登録以外の発話**（`BUILD_CAPABILITY` 等）で、`TRACE` が残っているもの | **在るはず**（`UTT-0769` は「宛: 設計/監査(CC-α)…」で始まる build 依頼）。**★ただし front door から `TRACE` を引く手段を私は知らない** |
| `TRACE` を ID で引く経路 | **【未確認・誰が=CC-α / いつ=次の作業】** `/api/resolve` は `UTT-`/`TASK-`/`DE-` 等を解決するが、**`TRACE-…` を解決できるかは確かめていない** |

**★私は `UTT-0769` に乗り換えていない。** **乗り換えてよいかは MGR の裁定である。**

---

## 5. 禁止事項の遵守
- **コードを1行も変えていない**（Build 22 も止めた）。
- **投入していない**（`submit()` を呼んでいない）。
- **新しい経路を作っていない。台帳に直接手を出していない**（確認は `/api/resolve` のみ）。
- **`UTT-0772` 以外に差し替えていない。**

---
*CC-α D-40。★`UTT-0772` は「開発エビデンスを登録: DE-? …」という DE 登録依頼で、`submit()` の段1.5(fast path)に入り `admission_payload` が渡されていないため **`return TRACE` で早期に返っている** ∴ `request_type`/`context_binding`/`intent_strategy`/ROUTING/DW はこの発話について**到達していない**（設計どおりの経路であり RRI が壊れているのではない）。13項目=1 DS 受付は実行確認済み(front door で引ける)／2〜6 はコード上のみ確認（段1.5 より後・4軸のうち3軸は本番に実装が無い）／7 `formal_candidates` は `webui.py:536` が `raw` しか渡さないので実行確認済み(間接)で `None`／8 7戦略は**呼ばれなかった**（段3e が走れば `INTENT_STRATEGY` が必ず載ることを Build 10R の前後比較で実測済＝規則を満たす）／9 次アクションは実行確認済み（"no DE candidate packet supplied"）／10 EGL には**書かれていない**（`return` が `admit_design_evidence` の手前）／11 DW は**呼ばれなかった**（`DW_TASK_ID=None` が明示設定＝記録の不在でなく記録された値が根拠）／12 勘定科目も Sub-ID も `task_id` も割り当てられていない／13 front door から読めたのは発話レコードのみ。★`UTT-0772` では RRI の本線を1つも通らないので Taka の狙い（RRI がどの経路を通っているかの確定）は**この発話では確定できない**。足りないのは DE 登録以外の発話の `TRACE` で、`TRACE-…` を `/api/resolve` で引けるかは【未確認・誰が=CC-α / いつ=次の作業】。★`UTT-0769` に黙って乗り換えていない（乗り換え可否は MGR 裁定）。コード変更・投入・新経路・台帳直接操作はいずれもしていない。*
