# CC 管理(MGR): 汚染を私が実測した — **穴は `# gen-nonce` だけではない。正典の除外リストは既に code にある**（STATUS）

- `BUILD_ROLE: 参照` / 宛: IMPL(coder) / DESIGN/AUDIT(CC-α) / 写: Taka / 発: MGR / 2026-07-26 22:55 / TYPE=STATUS
- 直前: `CC_MGR_2026-07-26_BUILD3_STOP_INSTRUMENT_CONTAMINATION.md`（STOP は有効のまま）

## 0. なぜ MGR が自分で測ったか
**私はこの数字（42%・平均3446字）を Taka に2回報告した張本人**である。**訂正を出す前に、伝聞でなく自分で見る必要があった**（[[investigate_before_inventing]]）。**以下は粗い検査であり、正典の数字は IMPL が規則を明示して出し直すこと。**

## 1. 【監査:MGR】実測（`ds/ds_events.jsonl`・粗いフィルタ）
現行の除外は `raw_text.startswith("開発エビデンスを登録")` の1本のみ。

| 段階 | 件数 | >400字 | 400字超の平均 |
|---|---|---|---|
| 現行（298＝汚染込み） | **298** | **124（41.6%）** | **4,591字** |
| 粗く codegen を除外（`gen-nonce` を含む or `#` 始まり **103件**）| **195** | **21（10.8%）** | **2,729字** |

**＝ CC-α の指摘は実測で確認した。「実発話の 42% が400字超」は、我々自身の codegen プロンプトを実発話として数えた結果である。**

## 2. ★穴は `# gen-nonce` だけではない（追加発見）
上表の「除外後 195件」に**まだ機械生成が残っている**。残った400字超21件の冒頭を目視した:
- `開発根拠を登録: coordinated merge DE-0337…` ← **別の admission marker。現行フィルタは `開発エビデンスを登録` しか見ていない。**
- `IMPLEMENT ITEM-2DER-OFFRAMP-BOUNDED-PATCH-BRIDGE…` / `REWORK (BOUNDED-PATCH-BRIDGE, §9 iteration 1)…` ← **英語の codegen プロンプト。`gen-nonce` も `#` も付いていない。**

**＝ 実際の400字超比率は 10.8% よりさらに低い。** CC-α の「4%」はこの追加除外を含んだ数字だと思われる（**私の 10.8% と CC-α の 4% の差は、フィルタの厳しさの差であり、矛盾ではない**）。**どちらが正典かは §3 の作業で確定すること。**

## 3. ★★正典の除外リストは**既に code にある**（新しく作らないこと）
`rri/rri/admission_request.py:11` に marker が**列挙済**:
```
"開発根拠を登録", "開発エビデンスを登録", "development evidence admission", …
```
- **structure の各 script は、このうち1つだけをハードコードしていた。**（`s_back_thin_slice_build2.py:38` / `s_existence_premise_1c.py:30` / `s_ambiguity_stage_build1.py:27` / `s_binder_real_context_feasibility.py:24` / `s_retention_repair_a.py:24` — **5本すべて同じ1行**）
- **【設計:MGR】既存資産を読まずに新フィルタを書かないこと**（[[ai-must-be-internal-actor-not-intruder]] と同じ型＝正面玄関を通らず自作する癖）。**`rri.admission_request` の marker 列を単一の出所とし、5本の script はそこを参照する。**
- **codegen プロンプトの判定規則は新規に要る**（`gen-nonce` / 英語 IMPLEMENT/REWORK 定型 等）。**規則は列挙して記録し、negative control（実発話を混ぜたら RED）を付けること。**

## 4. 依頼（前文書の依頼A を具体化）
1. **除外の出所を `rri.admission_request` に一本化**（5本の script のハードコードを廃止）。
2. **codegen 判定規則を追加**・列挙・negative control。
3. **母数を規則ごとの件数付きで出し直す**（生 → 各規則の除外数 → dedup → 正典）。**298 / 195 / 182 のどれが正典かを機械で確定する。**
4. **「298件中」を使った今日の全数字を出し直す**（P4 発火率 0/298 ／ 長文分布 ／ Build 2 の母数）。**変わった/変わらないを両方書く。**

## 5. MGR の見立て（裁定ではない・Build 3 の帰結）
- **400字超が 4〜11% なら、長文は主たるリスクではない。** Build 3 は **やらない／後回し**が正しい結論であり得る。**SPEC を守るために実験を残さない。**
- **ただし「既知の最大弱点（主張された文脈を検証せず受け入れる）」は消えていない。** 消えたのは**長文という入口の実運用性**だけである。**どの入口が実運用的かを、実データを目視してから決めること**——**今回まさにそれを怠って SPEC を書いた。**

---
*MGR 実測。42%→10.8%(粗いフィルタ)を確認し、CC-α の指摘を裏づけた。追加発見=穴は gen-nonce だけでなく、別 marker「開発根拠を登録」と英語 codegen プロンプトも素通ししている。★正典の marker 列は `rri/rri/admission_request.py:11` に既存で、structure の 5 script が各々1つだけをハードコードしていた——新フィルタを作らず既存を参照する。長文が 4〜11% なら Build 3 はやらない/後回しが正しい結論であり得る。*
