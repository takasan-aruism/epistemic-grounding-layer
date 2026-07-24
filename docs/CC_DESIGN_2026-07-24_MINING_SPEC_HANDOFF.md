# 設計/監査 → 実装: RTHREAD stage 2b-1 MINING_SPEC handoff(決定論クラスタリング + 安定性測定)

- 発: 設計/監査(CC-α)/ 2026-07-24 / 正本: `MINING_SPEC_v0.1.md`
- **repo=egl**(structure 作法)。LLM 不使用・決定論・byte一致再生成。
- 設計は **実データで grounding 済み**(ID 共起が唯一濃い信号、repos/request_type は退化。**安定 chart が出ない可能性が実在**)。

## 依頼(MINING_SPEC §1〜§3)
1. `egl/structure/s_mine_accounts.py` を実装。入力=DE ledger + rri_records。決定論素性(§1)を抽出、**prose を素性にしない**。
2. k-means を固定 seed 集合 {0..4} × K∈{4,6,8,10} で実行(seed 決定論・辞書順 tie-break)。出力 `ACCOUNT_CHART_CANDIDATE.jsonl`(name=null)+ `ACCOUNT_CHART_STABILITY.json`。
3. **負の制御(最重要 load-bearing)**: 素性を固定 seed shuffle したノイズ入力で cross-seed agreement が崩れることを実測。**崩れなければ RED**(miner が vacuous)。
4. `--check`: byte一致再生成 + 負の制御が「実データ > ノイズ」を保つこと。
5. **NO_STABLE_STRUCTURE を出口に持つ**: 実 agreement が負の制御を明確に上回らなければ `chart_status=NO_STABLE_STRUCTURE` を記録し、**chart を捏造しない**(2b-2 命名に進まない)。これは失敗でなく正当な結論。

## 拘束
- **account を発明しない**(初版最重要)。クラスタ ID はメンバ集合ハッシュ、名前は null(命名は 2b-2・安定時のみ)。
- LLM 不使用・決定論・byte一致。新 Registry を作らず `egl/structure/`。
- green のため負の制御を弱めない/ agreement 閾値を甘くしない → halt。
- **NO_STABLE_STRUCTURE は正しい結果**。無理にクラスタを立てない。

## 完了後
- `CC_IMPL_..._MINING_SPEC_BUILT.md` → 設計側が再監査(byte一致 + 負の制御 load-bearing + agreement 記録 + 非捏造)→ CONSISTENT → commit=Taka → DE 起票。
- 結果が NO_STABLE_STRUCTURE でも DE 化(chart 前提への finding)。
