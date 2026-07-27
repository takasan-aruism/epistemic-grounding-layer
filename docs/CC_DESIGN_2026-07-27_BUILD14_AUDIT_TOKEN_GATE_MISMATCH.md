# 設計/監査 → MGR（写: Taka / IMPL）: **Build 14 監査 — 契約の壁は越えた。次の壁は mint 側と検証側の語彙不一致。そして私は資料で `LIVE` を昇格させすぎていた**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD14_GENERATE_BUILT.md`

## 0. 判定
**通過。** 鮮度確認（**相対パスで誤った出力が出たことを自分で見つけて取り直した**）・各1回・依頼文不変・保全対象0の申告・空 sandbox を消さず残した・本番無変更。

---

## 1. ★原因 — mint 側と検証側が3項目とも別の語彙を使っている【監査:CC-α】

```
再現: sed -n '39,47p' twoder/generate_via_runner.py
  mint_token → _REAL_MINTER("USE_VLLM_INFERENCE",
                            "%s#attempt-%s" % (task_id, attempt),
                            "DW_MACHINE_OP", "2der-runner-seam", ts)
再現: grep -n "action_type mismatch\|task_id mismatch" twoder/approval_registry.py   （検証側の文言）
```

| 項目 | **mint が入れた値** | **検証が求める値** |
|---|---|---|
| `action_type` | `USE_VLLM_INFERENCE` | **`LIVE_WORKER_MINIMAL`** |
| `task_id` | `TASK-2DER-21F64D9D#attempt-1` | **`TASK-2DER-21F64D9D`（素）** |
| `operation_class` | `DW_MACHINE_OP` | **`LIVE_WORKER_TASK`** |

**∴ 3項目とも食い違っている。** **∴ 我々の依頼文の欠陥ではない。** **内部の2つの機構が、互いの語彙を知らずに書かれている。**

### 1-1. ★`#attempt-N` は意図的に入れたものである（片方の修理が、もう片方と噛み合っていない）
`mint_token` の docstring 逐語:
> 「**試行ごとに一意な token id(死因#2 修正 / §3)。attempt を入力に含めることで固定 TS 問題(webui.TS)を回避する。**」

**`approval_id` は `sha1(task_id|operation_class|action_type|ts)` で作られ、`ts` は固定値**（`webui.TS`）。
**∴ suffix が無いと、再試行のたびに同じ `approval_id` になり、単回消費の token が既に消費済みになる。** **suffix は効いている（load-bearing）。**
**∴ 単純に suffix を外すと、死因#2 が復活する。**

### 1-2. 本日3回目の同型である
| 回 | 場所 |
|---|---|
| 1 | `UNRESOLVED_NO_CONTRACT`（分析層）と `SPEC_INCOMPLETE_NO_CONTRACT`（生成層） |
| 2 | 決定論の4軸セレクタと LLM 直接選択（同じ7戦略を2通りに） |
| **3** | **mint 側（`generate_via_runner`）と検証側（`approval_registry`）の語彙** |

**∴「互いを知らずに書かれた2つ」は、この系の反復する故障形である。**

---

## 2. ★私は資料で `LIVE` を昇格させすぎていた（訂正する）【監査:CC-α】
**資料 `C-QWEN-WORKER` を私はこう書いた:**
> `status: LIVE` / evidence: 「EXEC: Build 12 で GENERATE が記録され actor_id=QWEN_LIVECODER」

**しかし `GENERATE` が**記録された**ことと、worker が**走った**ことは別である。**
- **Build 12**: 契約が無く `run_runner` の手前で fail-closed。
- **Build 14**: token gate で `run_runner` の手前で fail-closed。
- **∴ `run_runner` に到達した観測は、まだ1件も無い。** **worker は成果物を1度も出していない。**

**∴ 作業指示書 §9「test green だけで本線接続済みとしない」「import が存在するだけで Functional Edge 成立としない」に、私自身が違反していた。**
**∴ 資料を訂正する**（`C-QWEN-WORKER` → **`WIRED_UNPROVEN`**、`E-DISPATCH-WORKER.runtime_proven` → **false**）。**§8 の更新義務による訂正である。**

---

## 3. 予想の答え合わせ
| 項目 | 予想 | 実際 |
|---|---|---|
| sandbox が1つ増える | 増える | **増えた（中身0）・当たり** |
| `contract_source` | `ledger` | **★キーが payload に無い＝指標が成立しない**（本日3回目の「私が選んだ指標が偽のとき値を変えない」） |
| 骨格保存 / T1〜T8 / held-out | — | **すべて判定不能**（`run_runner` に到達せず） |

**★私の賭け（held-out が落ちる）は、今回も未決である。** **オラクルは開けない。**

---

## 4. 次の一手（提案・裁定を待つ）
**★どちらを直すかで結論が変わるので、私は決めない。**

| 案 | 内容 | 懸念 |
|---|---|---|
| **(A)** | **検証側を、token に記録された `task_id` で照合する**（`#attempt-N` を含む形で渡す） | **死因#2 の修理を壊さない。** 変更は照合の引数のみ |
| (B) | mint 側の語彙を検証側に合わせる（`LIVE_WORKER_MINIMAL` / `LIVE_WORKER_TASK`） | **`action_type` と `operation_class` は合うが、`task_id` の suffix 問題が残る** |
| (C) | 両方 | 大きい |

**【設計:CC-α】(A) と (B) の `action_type`/`operation_class` 部分は、おそらく両方要る**（3項目とも食い違っているため）。
**★ただし「どちらが正典の語彙か」を私は知らない。** **`star3(B)`（`38d1988`）が何を正典として配線したのかを読んでから決めるべきである。** **今は読んでいない。**

**∴ 提案: 次の build は「修理」ではなく「どちらが正典かを読む」ことにする。** **本日ずっと守ってきた順序（読んでから作る）である。**

---

## 5. 併せて（事実）
- **`artifact_sha256` が `""`**（Build 12 は `null`）。**空文字と null の使い分けは未確認。**
- **空の `2der_runner_tx15qmh2` が残っている。** **IMPL が消さなかったのは正しい**（証拠）。**掃除は別途。**
- **`ts` が `2026-07-11T09:00:00`**（既報 `G-12`）。**token の `approval_id` がこの固定 ts に依存している**——**∴ `G-12` は記録の見栄えの問題ではなく、token の一意性に効いている。** **`G-12` の重みを上げる。**

---
*CC-α Build 14 監査。通過（鮮度確認で相対パスの誤りを自分で見つけて取り直した点を含む）。★原因=mint 側(`generate_via_runner.mint_token`)と検証側(`approval_registry`)が3項目とも別の語彙——`action_type`(USE_VLLM_INFERENCE vs LIVE_WORKER_MINIMAL) / `task_id`(#attempt-1 付き vs 素) / `operation_class`(DW_MACHINE_OP vs LIVE_WORKER_TASK)。我々の依頼の欠陥ではなく、互いを知らずに書かれた2つ（本日3回目の同型）。`#attempt-N` は死因#2 修正として意図的で、`approval_id` が固定 ts に依存するため load-bearing＝単純に外すと再発する。★私は資料で `LIVE` を昇格させすぎていた——`GENERATE` が**記録された**ことと worker が**走った**ことは別で、Build 12(契約)も Build 14(token)も `run_runner` の手前で fail-closed ∴ worker は成果物を1度も出していない。作業指示書 §9 に私自身が違反していたので `C-QWEN-WORKER` を `WIRED_UNPROVEN`、`E-DISPATCH-WORKER.runtime_proven` を false に訂正する。予想=`contract_source` はキー自体が無く指標不成立（本日3回目の「偽のとき値が変わらない指標」）、賭けは未決でオラクルは開けない。★次は修理でなく「どちらが正典の語彙か」を読むことを提案（`star3(B)`=38d1988 を未読）。併せて `G-12`(固定 ts) は見栄えでなく token の一意性に効いているので重みを上げる。*
