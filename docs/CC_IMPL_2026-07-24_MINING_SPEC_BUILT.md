# 実装担当 → 設計/監査担当: RTHREAD stage 2b-1 MINING_SPEC v0.1（BUILT・結論 NO_STABLE_STRUCTURE）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `MINING_SPEC_v0.1.md` / `CC_DESIGN_2026-07-24_MINING_SPEC_HANDOFF.md`
- repo=egl。LLM 不使用・決定論・byte一致再生成。

## 成果物（working tree・未commit）

- `egl/structure/s_mine_accounts.py`（決定論 feature 抽出＋k-means＋stability＋負の制御＋`--check` 常設ゲート）
- `egl/structure/ACCOUNT_CHART_STABILITY.json`（測定記録）
- `egl/structure/ACCOUNT_CHART_CANDIDATE.jsonl`（**空＝account を捏造しない**）

## 結論: `chart_status = NO_STABLE_STRUCTURE`（正当な結論・§0/§4 どおり）

- 決定論素性（cooc 全文ID共起＋band＋kind、prose 不使用）× k-means（seed {0..4}・K∈{4,6,8,10}・argmin 辞書順 tie-break）。
- **意味ある account トポロジは無い。** 唯一安定な構造は **record-kind の自明分割**（DE/RREQ/RINT/RSIG）。cluster vs record-kind の ARI=**0.957**（>=0.50=自明）。決定論素性は種別しか復元しない＝§0 の予想どおり。
- account を捏造せず、命名（2b-2）へ進まない。

## 検証（負の制御が load-bearing の核）

- **計器を2度疑い自己修正（族A 回避）**:
  1. 初回 raw Rand index は K 大で true-negative ペア支配により膨張（real 0.98/neg 0.80 とも高く解釈不能）→ **chance 補正の Adjusted Rand Index (ARI) に差し替え**。
  2. ARI でも real 0.96/neg 0.52 で STABLE に見えた→ **クラスタ実体を検査**し record-type 自明分割と判明→ **自明分割ガード（cluster-vs-kind ARI）追加**→ 正直な NO_STABLE。
- **負の制御 load-bearing 実証**: 素性を固定 seed で列 shuffle → cross-seed ARI が 0.96→0.52 に崩壊（margin 0.44）。shuffle=恒等なら margin~0＝miner が vacuous なら検出可能。
- **byte一致再生成**: `--check` GREEN（両出力 byte一致）。
- 判定を甘くしていない（MARGIN 0.05・自明ガード 0.50・agreement は chance 補正 ARI）。

## 重要 finding（§5・Taka 裁定/DE 化候補）

- **「決定論素性（cooc/band）では chart of accounts が出ない」**＝ stage 2 の「chart は MINING で出す」前提への重要 finding。実データでは ID 共起も band も **record-kind と交絡**し、種別以上の topic/account 構造を安定に復元しない。
- 含意: (a) 実 chart は決定論クラスタリング単独では得られない → 2b-2 の LLM 命名は**安定クラスタが無いので着手しない**、(b) account 次元（stage 2a の chart 検証）は当面 **UNCLASSIFIED + 極小テスト chart** のまま、(c) chart 前提そのものを Taka 裁定候補に。

## ハンドオフ

- 次: **CC 再監査（byte一致 + 負の制御 load-bearing + agreement 記録 + 非捏造）→ CONSISTENT → commit=Taka → DE 起票**（NO_STABLE_STRUCTURE 自体を finding として DE 化）。
