# 実装 → MGR / 設計: Build 5 前段 — **決定論の判定は意図調べに一言も渡っていない。渡す先すら本番に無い**（STATUS）

- 宛: MGR / DESIGN(CC-α) / 写: Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=STATUS
- 依頼: Taka「コードを読んで『決定論の判定（文脈の有無・存在の接地）が、意図調べに渡っているか』を事実として報告」
- **LLM を1回も呼んでいません。** すべて grep と実物の prompt 生成による事実確認。
- 表記規約: **【監査:IMPL】**

## 0. 結論（3行）
1. **文脈の有無も、存在の接地も、意図調べの prompt に一言も書かれていません。**
2. **`context` が空のときは「文脈の記述が消える」だけ**で、「文脈は空である」とは**言っていません**。
3. **そもそも意図調べは本番コードから一度も呼ばれていません。** 渡す先が LIVE に存在しません。

## 1. 事実【監査:IMPL】

### A. 意図調べは本番から呼ばれていない
```
再現: grep -rn "s_intent_role_split|intent_role_split|_rel_prompt" --include=*.py twoder rri ds dev-workcell
結果: 0 件
```
意図調べは **`egl/structure/s_intent_role_split*.py` にしか存在しない研究スクリプト**です。front door（`twoder/submit.py`）の段には入っていません。

### B. `preflight_gate` は本番 LIVE。ただし `context` を渡していない
```
再現: grep -rn "PG.detect" --include=*.py twoder
結果: twoder/submit.py:239 →  pg = PG.detect(raw_input, failure_hits=_fh)
```
**`context=` 引数は渡されていません**（Build 1a で引数を足しましたが、呼び出し側は未配線のままです。既報）。

### C. `existence_grounding`（存在の接地）の到達範囲
```
再現: grep -rln "existence_grounding" --include=*.py .
結果: rri/rri/preflight_gate.py（本体）+ 測定スクリプト2本のみ
```
**接地判定は `preflight_gate` の内側で完結**しており、**意図調べには構造上一切届きません。**

### D/E. ★prompt に事実が書かれていない（実物）
`context` が空の `IP2` と、`context` が在る `CR1` の prompt を実際に生成して比較しました。
```
IP2（context 空）:
  依頼:「それ、その後どうなった？」
  次の7戦略のうち、…
      ↑ 文脈についての記述が **何も無い**

CR1（context あり）:
  依頼:「プーチンの今後の動向は？」（直前文脈: 直前の会話は…が支配的。）
      ↑ 在るときだけ書かれる
```
**＝ 我々は「文脈が空である」という事実を機械で確定していながら、モデルには何も言っていません。** 空欄が消えるだけで、モデルは**不在から推し量る**しかありません。
**接地状態（`GROUNDED` / `NOT_FOUND` / `UNKNOWN`）に至っては、prompt に文字列すら存在しません。**

## 2. では決定論の判定は何に使われているか【監査:IMPL】
| 使い方 | 実装 | 性質 |
|---|---|---|
| `CONTEXT_RESOLVE` を候補から**消す** | Build 1b（後置フィルタ） | **選択肢の削除** |
| `CONTEXT_RESOLVE` をメニューに**載せない** | Build 4（メニュー制限） | **選択肢の削除** |
| **事実として伝える** | **無し** | — |

**＝ 我々は事実を「選択肢を減らす」ためだけに使っており、「伝える」経路は一度も作っていません。**

## 3. 含意（事実の範囲内で）
- Build 1b も Build 4 も **精度を動かしませんでした**。**どちらも「削る」方式**です。**「伝える」方式はまだ試していません。**
- Taka の指示「**事実を渡せ**」は、**未着手の第三の方式**を指しています。**Build 5 arm C がそれに当たると理解しています。**

## 4. 別件: `origin` 欄【監査:IMPL】
**実装済みです**（Build 4 PART 2）。
- `ds/phase0.py` に `origin`（`HUMAN_DIRECT`/`HUMAN_RELAYED`/`MACHINE_SUBMIT`/`MACHINE_CODEGEN`/`UNSPECIFIED`）と `relayed_by`/`authored_by` を追加。**申告が無ければ `UNSPECIFIED`。推測しません。**
- `HUMAN_RELAYED` は `relayed_by` と `authored_by` の併記を**必須**にしています（「直接打った」と偽らないため）。
- front door 経由は `MACHINE_SUBMIT`。**境界レコードは `UTT-0742`**（ここから `origin` が入る）。
- 非回帰: `test_preflight_gate` 13/13・`ds/test_ds_phase0` 19/19。**既存レコードの差分ゼロ。前向きのみ。**
- **除外フィルタは消していません**（過去は永久に `UNSPECIFIED` なので歴史用に残す・CC-α §8 の訂正どおり）。

## 5. 次（Build 5 本体・着手前の申告）
**arm C（事実を渡す）を実装する場合の見積もりを、投げる前に出します。**
- 比較は最低 **arm A（現行）/ arm C（事実を渡す）** の2本。fixture 20 × seed 3 × 10 run × 2 batch × 2 arm = **選別 2,400 呼出**（+ 選択役分）。**16 並列。**
- **指示があるまで LLM を呼びません。**

---
*IMPL STATUS（Build 5 前段・LLM 不使用）。**①文脈の有無も接地状態も意図調べの prompt に一言も書かれていない。②`context` が空のときは記述が消えるだけで「空である」とは言っていない。③意図調べは本番コードから0参照＝渡す先が LIVE に存在しない。** 決定論の判定は「選択肢を削る」ためだけに使われており、「伝える」経路は未実装。Build 1b も Build 4 も削る方式で精度は動かなかった。`origin` は実装済（境界 `UTT-0742`・前向きのみ・非回帰 GREEN）。*
