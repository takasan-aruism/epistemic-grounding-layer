# 設計/監査 → 実装: 意図調べ arm-C3 — held-out 例文 / 理由を一級市民 / 二階建て評価（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=HANDOFF / model=Qwen3.6-35B-A3B(:8005)
- 正典: `CC_DESIGN_2026-07-26_INTENT_PROBE_ARMC2_REAUDIT_FINDING.md`（特に §1 汚染 / §5b Taka 指摘）+ DE-0543 + RRI spec §7/§9 + 既存 `s_intent_probe_armc2.py`
- Taka GO: 2026-07-26「OK。任せる」（汚染除去 + 理由の一級市民化 を**1回の再実験に統合**）
- 成果物: `structure/s_intent_probe_armc3.py` + `INTENT_PROBE_ARMC3.jsonl`

## 0. なぜやり直すか（前提の共有・短く）
arm-C2 の 0.88 は**8 fixture 中 7 個が正解付きで prompt の例文に混入**していたため、汎化でなく記憶の測定だった（起因は DESIGN handoff の例文指定＝**設計側の欠陥・IMPL の逸脱ではない**）。加えて metric が arm-C と不揃い（seed0 単発 vs seed 平均）。同時に Taka 指摘「正解/不正解は揺れる。理由を入れれば揺れるが、その揺れは誤りではない」が実データで支持された（FINDING §5b）。**この2つは測定設計を共有するので 1 回で直す。**

## 1. ★汚染除去は「気をつける」でなく**機械ゲート**にする（最重要・恒久機構）
- 例文（few-shot）は **fixture と素性の異なる held-out** にする。fixture の依頼文・その言い換え・固有名詞を例文に使わない。
- **`--check` に CONTAMINATION 検査を必須実装**（これが本 handoff の中核）:
  - 正規化（空白/句読点/全半角/「?？」を除去）した **全 fixture の request 文**と、正規化した**全 prompt template 文字列**を突合。
  - fixture 側の **連続 5 文字以上**が template に出現したら **RED**（該当 fixture_id / binary_id / 一致断片を列挙）。固有名詞単独一致の誤検知が出るなら閾値でなく**除外語リストを明示的に置き、その語を記録する**（黙って緩めない）。
  - RED の時 `--check` は rc=1。＝**将来 誰かが例文に fixture を混ぜたら CI 相当で落ちる。**
- 併せて `prompt_id="armc3-heldout-reasons-v1"` を記録。

## 2. ★理由(根拠)を一級市民にする
- 出力スキーマ: `{"choice":"A"|"B"|"unsure", "reason":"<1文・40字以内・なぜその選択か>"}`。
  - **`note`(10字) を `reason` に格上げ**。10字では (b)(c) の診断ができなかった一方、think ON の 1230tok は不要（FINDING §5b(d)：買うのは thinking でなく根拠）。**40字程度で足りることを実測で確かめる**（超過が多いなら報告して上げる）。
  - `reason` 欠落・空は **parse verdict = `DIVERGE_NO_REASON`**（＝根拠なき claim を通さない。EGL 中核と同型）。
- **think は OFF 固定**（精度寄与ゼロ・15倍コストが測定済＝再測不要）。ON を再測しないことを BUILT に明記。

## 3. ★「空回りの答え」を構造で可視化する（FINDING §5b(b)）
問題: 適用条件を満たさない二択も無条件に全件発行するため、モデルが中身のない答えを返す（F4 `b_probe_type`= B「前提が怪しい」なのに理由「プーチンの存在は確実」）。
- **並列発行はやめない**（arm-C の設計思想＝全件並列+決定論ツリーが取捨、を維持）。
- 代わりに、各行へ **決定論で計算した `applicable` フラグ**を付す: その fixture の確定ツリー経路上で、その二択が実際に参照されたか。
- 指標を分ける: **`applicable` な行だけで精度を出す**。非 applicable 行は「発行はしたが集計に使っていない」ことを明示（コストとしては計上）。
- `vacuity`: applicable 行のうち choice と reason が矛盾するものを**二階（§4）で人が判定**（自動判定しない）。

## 4. ★二階建て評価（揺れを消さず、自動測定も失わない）
- **一階（機械・全件・無料）**: 従来のラベル一致。ただし**意味を「正しさ」から「前回からの変化検知(regression detector)」へ再定義**する。BUILT の文言でも「正解率」と書かず **`label_agreement`** と呼ぶこと。
- **二階（不一致時のみ）**: 一階で期待とズレた件について、`reason` 付きの一覧を **決定論で `DISAGREEMENTS` セクションに出力**する（fixture / binary / choice / reason / 期待ラベル）。
  - **IMPL は 別解/誤り/空回り の判定を自分でしない。** 判定は DESIGN が propose → **Taka 承認**（2b-r3 の propose→承認 規律を再利用）。IMPL は**材料を決定論で揃えるところまで**。
- **書き戻し**: 承認された「別解」は fixture に `acceptable_strategies`（複数可）+ `acceptance_reason` として追記できる構造にしておく（今回は器だけ用意。実際の書き戻しは承認後）。
  - 例（承認されれば）: F4「プーチンの今後は？」= `["CHOICE","BOUNDED_MULTI_VIEW"]` / 理由「選ばせる有限の選択肢が存在しないため BMV も可」。
  - ＝[[llm_arithmetic_drift_tolerant_design]]「LLM 分類→機械 consolidation で徐々に固める」の実装。**綴り一致で auto-collapse しないこと**（[[exec_arch_task_contract_pivot]]）。

## 5. 測定の統制（arm-C / C2 と比較可能にする）
- **metric は seed 平均に統一**: `label_agreement = hit / (fixture数 × seed数)`。single(seed0) は参考値として併記可だが**見出しにしない**。seed 一貫も出す。
- **A/B 並び順を統制**: arm-C→C2 で `b_probe_type` の A/B が反転しており定義例の効果と交絡していた。**各二択を「順序 正/逆」の両方**で実行し、**position bias を数値で出す**（順序間の一致率）。
- **fixture 拡充**: 各戦略（DIRECT/CONTEXT_RESOLVE/CHOICE/BMV/INTENT_PROBE/PREMISE_PROBE/DEFER）**3 件以上**。既存 8 件は残し、追加分は held-out 例文とも重ならないこと。
- 規模の目安: 21 fixture × 6 binary × 3 seed × 2 順序 ≒ 756 呼出。並列 16・think OFF なら数十秒（C2 は 144 呼出 6.86s）。**先に呼出数と想定 wall を BUILT に書く。**

## 6. 受入（全部 measured で示すこと）
1. `s_intent_probe_armc3.py --check` **GREEN**、かつ **CONTAMINATION 検査を含む**（わざと fixture 文を例文に入れた negative control で RED になることを実証＝検査が効いていることの証明）。
2. 決定論部の byte 再現（parser / 多数決 / 集計ツリー / applicable 判定）。LLM 非再実行。
3. provenance 完全（prompt_id / think / 順序 / seed / reason / completion_tokens / applicable / 並列数 / wall）。
4. **`label_agreement`(seed 平均) を arm-C 0.5833 / arm-C2 0.8333 と同一 metric で並べる**。
5. `DISAGREEMENTS` 一覧が出ている（判定は付けない・材料のみ）。
6. `reason` 欠落率・40字超過率・position bias・applicable 率を報告。
7. :8005 CALL_SITE 登録（meta fold）。**commit 時に新 script を必ず同梱**（未同梱だと meta gap で clean checkout RED＝DE-0543 で実際に起きた）。

## 7. 規律（不変）
- **measure-first**: 改善しなければ「しなかった」と正直に書く。**汚染前(0.88)より下がるのが正常**（0.88 は嵩上げ値）。**下がったことを失敗として隠さない**。
- 数字は**能力主張として書かない**。単一 fixture セット・LLM 非決定論ゆえ run 毎に±。
- commit=Taka。DE は front door `record_de` + `generated_by_principal`/`claiming_principal`="CLAUDE_CODE" / `generation_mode`="DIRECT" 明示。
- ★3 本線（帳簿）は止めない。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。汚染は機械ゲートで断つ・理由は根拠として必須・揺れは二階建てで受ける・metric は seed 平均で統一。*
