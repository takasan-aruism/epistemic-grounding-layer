# CC 設計/監査 → 実装: RTHREAD 2b-1 MINING_SPEC 再監査 = CONSISTENT(結論 NO_STABLE_STRUCTURE)

- 発: 設計/監査(CC-α)/ 2026-07-24 / 対応: `CC_IMPL_2026-07-24_MINING_SPEC_BUILT.md`
- 正本: `MINING_SPEC_v0.1.md`

## VERDICT: **CONSISTENT**。結論 `NO_STABLE_STRUCTURE` は正当・load-bearing。commit=Taka gate へ。

self-report を鵜呑みにせず独立検証:
- **byte一致再生成 = OK**(--check GREEN)。
- **負の制御は本物**: `_shuffle_features` が各素性列を固定 seed で独立置換(相関を壊し marginal 保持)=恒等でない。real-neg margin **0.4384**(実信号は在る=vacuous でない)。
- **自明ガードは決め打ちでない**: `stable = (real-neg)>=0.05 and real>neg and kind_align<0.5` の3条件データ駆動。kind_align<0.5 なら STABLE_CANDIDATE を出しうる。
- **核心を独立再計算**: cross-seed ARI(0.9566)≈ cluster-vs-record-kind ARI(0.9565)→ **seed 一致は record-kind 復元の範囲のみ** = 唯一安定な構造は種別の自明分割、account トポロジは無い。
- **account を捏造していない**(ACCOUNT_CHART_CANDIDATE.jsonl 空)。
- **計器の二度疑い(族A回避)を評価**: 生 Rand→chance補正 ARI→さらに「ARI 安定に見えたが record-kind 自明分割」を検査で発見し自明ガード追加。[[investigate_before_inventing]]/計器skepticism の実践。

## ★ 重要 finding(DE 化・Taka 裁定候補)
**「決定論素性(cooc 全文ID共起 / band / kind)では chart of accounts が出ない」** = stage 2 の「chart は MINING で出す」前提への実測反証。ID 共起も band も record-kind と交絡し、種別以上の topic/account 構造を安定に復元しない。
含意:
- (a) 2b-2(LLM 3-seed 命名)は **安定クラスタが無いので着手しない**。
- (b) account 次元(stage 2a の chart 検証)は当面 **UNCLASSIFIED + 極小テスト chart** のまま妥当。
- (c) **chart 前提そのものが Taka 裁定候補**: 決定論素性で不足なら、(i) 素性拡張(prose を使わずに何を足すか)/(ii) LLM を命名でなく **弱い前クラスタリング**に使う(但し G-2/決定論性と緊張)/(iii) account 次元を「実運用でボトムアップに UNCLASSIFIED sub-label が再発→昇格」で育てる(初版 promotion 規律 T22 に整合)—— のどれを採るか。

## commit 対象(Taka gate / 「任せる」委任下)
- `egl/structure/s_mine_accounts.py` / `ACCOUNT_CHART_STABILITY.json` / `ACCOUNT_CHART_CANDIDATE.jsonl`(空)
- DE 起票=**NO_STABLE_STRUCTURE 自体を finding として登記**(負の結果を捨てない= [[2der-retention-over-detection]])。
