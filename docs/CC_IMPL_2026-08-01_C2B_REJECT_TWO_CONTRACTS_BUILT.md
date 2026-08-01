# 【BUILT / C-2 訂正】2組は弾けた・雛形も直った — **★(b-3)「埋めた方が採られた」は★示せない**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 15:3x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_C2B_REJECT_TWO_CONTRACTS.md`
- **commit していない** ／ **`:8005` を叩いていない** ／ **`twoder` 配下で python を動かしていない**（★`cd /home/takasan` から実行）

---

# 1. ★変更行数（★誰が書いたか）
```
★★Claude（IMPL）が書いた。★2DER の実績に数えない。
   `twoder/contract_seal.py`     ★+4（★弾く検査2行＋理由のコメント2行）
   `twoder/request_template.py`  ★33行 → ★50行（★+17。★`_strip_contracts` と `STRIPPED` の1行）
★★C-2 全体の累計: ★`request_template.py` 50行（新規）／`webui.py` +2／`contract_seal.py` +4 ＝ ★56行
★★★`contract_seal` の★既存の4つの `ValueError` は ★1つも緩めていない（★§2 で実測）
★新しい関数・台帳・マーカー・状態語・エンドポイントは作っていない
```

---

# 2. ★受入 (b-1)(b-2)(b-3)

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **(b-1)** | 契約2組の文字列 → `ValueError` | **★○** | **逐語: `multiple contracts: only one contract block is allowed`**（★試験用の文字列・**★投入していない**） |
| **(b-2)** | 雛形の契約は1組・中身は空・外した跡の1行 | **★○** | `TASK-2DER-B37727E3` の雛形: **SK/IT/END = 1/1/2**・**`def test_` 0行**・**「（前回の契約はここに在りましたが、新しく書くために外しました）」が在る** |
| **(b-3)** | 埋めて投入すると **埋めた方が採られる** | **★★示せない** | ★下記 §3 |

**★既存検査を緩めていないことの実測**: 1組で中身を空にすると **`ValueError: immutable_tests has no pytest-collectable test (^def test_)`** が今も出る。

---

# 3. ★★(b-3) は「示せない」（★通ったと書かない）

```
★投入は通った: ★`task_id = "TASK-2DER-ACC5B7FB"`（★予告と★一致）
★★しかし ★★「埋めた方が採られた」ことは ★front door から★示せない。★理由を2つ 書く:

★理由① ★文字列は出るが ★出所が ★`goal` である（★思い込みで書かない・★出現場所を機械で特定した）
   ★`/api/state` での出現場所: ★`/goal` と ★`/egl/current_claims[1]/text` の2箇所だけ
   ＝ ★★投入した本文の★echo であり、★★契約として採られた証拠ではない

★理由② ★★そもそも ★契約は封印されていない
   ★`claude_packet.knowledge_packet` のキー: `packet_type / schema_version / task_context / provenance`
     ＝ ★★`contract` キーが ★無い
   ★原因: ★この投入は ★`request_type = OBSERVE_CURRENT_STATE` に分類された
     ∴ ★`contract_seal.extract_contract` を呼ぶ ★DW 分岐（`submit.py:506`）に ★到達していない
   ★★★＝ ★前回 報告した「★機構は経路による」と ★★同じことが ★今回も起きた（★2回目）

★★★★★∴ ★(b-3) は ★★「示せない」。★★「埋めた方が採られた」とは書かない。
```

---

# 4. ★予告の当否（★投入前に固定・`c2b_pre.txt`）
| 予告 | 結果 |
|---|---|
| 変更行数（`contract_seal` +4 ／ `request_template` +17） | **★当たり** |
| (b-1) 2組 → `ValueError` | **★当たり**（逐語つき） |
| (b-2) 1組・空・跡の1行 | **★当たり**（3つとも） |
| (b-3) **示せるか未確認。示せなければ「示せない」と書く** | **★示せなかった ∴ そう書いた** |
| 埋めた投入の `task_id` = `TASK-2DER-ACC5B7FB` | **★当たり**（sha1 から先に出した） |

---

# 5. ★戻し方（★可逆）
```
★① `twoder/contract_seal.py` の ★弾く2行（＋コメント2行）を消す
★② `twoder/request_template.py` の ★`_strip_contracts` / `STRIPPED` と ★`build` 内の1行を消す
★③ （C-2 本体）`request_template.py` を消し、`webui.py` の2行を戻す
★★`git checkout -- contract_seal.py request_template.py webui.py` ＋ `rm request_template.py` で戻る
```

---

# 6. ★副作用と、★測っていないこと
```
★副作用: ★(b-3) の測定で ★task が1件 増えた（`TASK-2DER-ACC5B7FB` / `CREATED`）。★消していない
★★測っていない（★設計が §6 で挙げたもの）: ★過去の依頼文に契約が2組 在ったか ／ ★`progress_seal` の同じ問題
   ★★どちらも ★今回 触っていない（★規律9）
★★★★私が測っていないこと（★追加で1件）: ★★`OBSERVE` 経路に分類された投入で ★契約が封印されないことを
   ★どう扱うか。★★これは §3-理由② そのものであり、★C-2 の受入(b-3) が ★構造的に満たせない原因である。
   ★★★私は直していない（★指示が無い・★経路の設計判断）。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。C-2 訂正。**Claude（IMPL）が `contract_seal.py` +4（弾く2行＋コメント2行）と `request_template.py` +17（`_strip_contracts`）を書いた。C-2 全体の累計は56行。既存の4つの `ValueError` は1つも緩めていない（1組で中身が空なら今も `immutable_tests has no pytest-collectable test` が出ることを実測）。新しい関数・台帳・マーカー・状態語・エンドポイントは作っていない。** **受入 (b-1)○——契約2組の文字列で逐語 `multiple contracts: only one contract block is allowed`（試験用の文字列で、投入していない）。(b-2)○——`B37727E3` の雛形は SK/IT/END=1/1/2、`def test_` 0行、外した跡の1行も在る。** **★(b-3) は「示せない」。投入は通り `task_id` は予告 `TASK-2DER-ACC5B7FB` と一致したが、①文字列の出現場所を機械で特定すると `/goal` と `/egl/current_claims[1]/text` だけで投入本文の echo に過ぎず、②そもそも `claude_packet.knowledge_packet` に `contract` キーが無い＝契約が封印されていない。原因はこの投入が `OBSERVE_CURRENT_STATE` に分類され、`extract_contract` を呼ぶ DW 分岐（`submit.py:506`）に到達しないこと——前回 報告した「機構は経路による」が2回目として再現した。「埋めた方が採られた」とは書かない。** 予告は行数・(b-1)・(b-2)・task_id が当たり、(b-3) は「示せなければそう書く」と予告したとおりにした。**副作用は task が1件 増えたこと（消していない）。測っていないことは、設計が挙げた2件（過去の依頼文の2組・`progress_seal` の同じ問題）に加えて、`OBSERVE` 経路で契約が封印されない件の扱い——これが (b-3) を構造的に満たせない原因だが、経路の設計判断なので私は直していない。** 戻し方は3箇所を戻すだけ。`twoder` 配下で python を動かしていない。commit していない。*
