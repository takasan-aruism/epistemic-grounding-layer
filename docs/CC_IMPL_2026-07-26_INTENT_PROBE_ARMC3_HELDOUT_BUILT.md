# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 意図調べ arm-C3（汚染除去・held-out）BUILT — **是正・下方修正**

- 宛: AUDIT（→ DESIGN → MGR/Taka）
- 発: 実装(IMPL) / 2026-07-26 / model=Qwen3.6-35B-A3B(:8005)
- 対応: `..._ARMC2_REAUDIT_FINDING`（汚染指摘）+ `..._ARMC3_HELDOUT_REASONS_HANDOFF`
- **これは能力主張の下方修正である。0.88 は汚染由来だった。正直に低い値を報告する（隠さない）。**

## まず監査の受容と自分の誤りの所有
CC-α の再監査は正しく、一次情報で全て確認しました（汚染・metric不揃い・s11 RED）。私の誤り: (1)例文=fixture の汚染を見逃した、(2)0.88(seed0)と0.58(seed平均)を並べた、(3)点推定から「think 不要と実証」と物語化（皮肉にも私が旗を立てた [[llm-prompt-hygiene-not-budget]] 違反）、(4)s11 を掃引せず「全gate GREEN」と誤報。**全て私の miss として所有します。**

## 成果物（working tree・未commit）
- `structure/s_intent_probe_armc3.py` + `INTENT_PROBE_ARMC3.jsonl`（21 fixture×6 binary×2順序×3 seed=756呼出・think OFF・48s）
- `structure/s11_ledger_flow.py`（**私の slice1b 回帰を修正**: submit.py 行参照 5件を +2 ずれに更新→`0 stale`・GREEN）
- meta fold（:8005 CALL_SITE 登録）

## ★ 是正後の正直な結果（同一 metric=seed平均）
| アーム | label_agreement(seed平均) | 備考 |
|---|---|---|
| arm-A 単発 OFF | 0.54 | baseline |
| arm-C 二択(定義なし) | 0.58 | |
| arm-C2 二択+定義例 | **0.83（汚染）** | 8問中7問が答え付きで例文に混入＝記憶 |
| **arm-C3 二択+定義例 held-out** | **0.54（34/63）** | **汚染除去。定義例の効果は baseline を超えない** |

- **結論: 「定義+例で 0.58→0.88」は汚染だった。held-out にすると 0.54＝素の baseline と同水準。定義+例は"効いていなかった"**（measure-first：改善しなかったと正直に）。
- Qwen のこの task の素の能力（二択分解・clean）は **~0.54**。単一 fixture・非決定論ゆえ run 毎に±、能力主張ではない。

## ★ 恒久機構: 汚染を機械ゲート化（本 handoff の中核・DEAD にしない）
- `--check` に **CONTAMINATION 検査**を実装: 正規化した fixture request の連続5文字以上が例文に出たら RED（該当断片を列挙）。
- **negative control 実証**: --check 内でわざと fixture 文を例文へ注入→検出できることを assert（検査が生きている証明）。GREEN。
- ＝**将来 誰かが例文に fixture を混ぜたら CI 相当で落ちる**（今回の失敗の再発を構造的に断つ）。除外語リスト `EXCLUDE_WORDS`（今は空）は明示・記録（黙って緩めない）。

## ★ 新たに定量化した弱点
- **position bias 一致=0.65**: A/B の**並び順を変えると 35% で答えが変わる**。arm-C→C2 の A/B 反転が定義例効果と交絡していた（FINDING §4）ことの実体。**LLM の選択肢位置バイアスは実在し大きい**＝二択設計で順序を統制すべき（今回は両順序測定で露出）。
- 弱2二択的中 8/11・seed一貫 11/21・applicable 49%（並列発行の半分は経路外＝コスト計上）・reason 欠落0（理由必須が機能）・reason>40字 26件（やや超過・上限緩和 or 圧縮指示を検討）。

## 二階建て評価（揺れを消さず・判定は私がしない）
- 一階=`label_agreement`（**"正解率"でなく regression detector** と再定義）。
- 二階=`DISAGREEMENTS` 29件を**材料として決定論出力**（fixture/got/expected/各二択の reason）。**別解/誤り/空回りの判定は IMPL でなく DESIGN propose→Taka 承認**（2b-r3 規律）。主なズレ: INTENT↔PREMISE(5)・CONTEXT_RESOLVE↔PREMISE/DIRECT(4+3)・BMV↔DIRECT(4)・CHOICE↔probe(6)。`acceptable_strategies` 書き戻し器は用意済（例: 承認されれば CH3/BV に別解）。

## 検証（受入・全 gate GREEN）
- `--check` GREEN: 汚染ゲート健全（negative control 実証）・記録 raw に parser/canonical/多数決/集計ツリーを決定論再適用→一致（LLM 非再実行）・provenance 完全（prompt_id/think/order/seed/reason/completion_tokens/applicable/並列/wall）。
- **s11_ledger_flow GREEN 回復**（私の回帰修正）。全 gate GREEN。

## ハンドオフ
- 次: 設計/監査 独立再監査（汚染ゲートの効き・held-out・seed平均・position bias・DISAGREEMENTS 材料）→ DISAGREEMENTS の二階判定（DESIGN propose→Taka）。
- DE 記録は front door `record_de` + `generated_by_principal`/`claiming_principal`=CLAUDE_CODE・`generation_mode`=DIRECT 明示。**DE 本文に「0.88 は汚染・held-out で 0.54」を明記**し、能力値として残さない。commit 時 armc3.py 同梱（meta gap 回避）。
- 想定と実測: 汚染除去で **0.83→0.54 に低下**。これを失敗として隠さず、恒久ゲートと position bias 定量化を成果とする。

---
*実装(IMPL)。監査を受容し誤りを所有・汚染を機械ゲートで断つ・下がった値を正直に・measure-first。★3 本線・止めない。*
