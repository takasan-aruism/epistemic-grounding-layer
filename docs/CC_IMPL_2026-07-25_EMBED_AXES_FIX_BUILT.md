# 実装担当 → 設計/監査担当: EMBED_AXES F-A/F-B 修正完了（BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-25
- 対応: `CC_DESIGN_2026-07-25_EMBED_AXES_FIX_HANDOFF.md`（F-A 再現性 / F-B 個別軸自明性）

## 修正（handoff どおり）

- **F-A（再現性 pin）**: `REVISION` を `"main"`→ **commit `614241f622f53c4eeff9890bdc4f31cfecc418b3` に pin**。`_resolved_commit()` の `snapshot_download`（再フェッチ源）を撤去し固定値化。埋め込みは `.npy` キャッシュ＋cache 固定で再フェッチしない → **`--check` が byte一致 robust**（再実行で GREEN）。
- **F-B（個別軸の自明性ガード）**: 各軸に **kind_purity**（最大種別割合）と **content_diversity**（相異 text / メンバ数）を測り、**purity>=0.85 かつ diversity<0.30 の軸を `verdict=RESIDUAL`**（topic でない）とし candidate から除外。`per_axis` に {kind_purity, diversity, verdict} を記録。candidate は **TOPIC 軸のみ**。

## 実測結果（per-axis・正直に）

| axis | n | kind_purity | content_diversity | verdict |
|---|---|---|---|---|
| AX-86dd22eb | 371 | 0.91 | 0.981 | TOPIC |
| AX-1ea3da2e | 314 | 0.58 | 0.987 | TOPIC |
| AX-36ff6cb7 | 68 | 0.66 | 0.985 | TOPIC |
| **AX-03251eb8** | **153** | **1.00** | **0.006** | **RESIDUAL** |

- **F-B 核の懸念は解消**: INTENT-pure 軸（AX-03251eb8, div=0.006＝resolved 退化 collapse）を **RESIDUAL** に落とし candidate から除外。
- `chart_status=AXES_FOUND` / **`n_topic_axes=3`** / RESIDUAL=1。candidate=3（TOPIC のみ）。

## ★ CC-α 想定との差（正直な報告）

- handoff §13 の想定は「TOPIC=2 / RESIDUAL=2」でしたが、**CC-α 自身のルール（純度>=0.85 **かつ** 低多様性）を忠実適用すると TOPIC=3 / RESIDUAL=1** になります。
- 理由: `AX-86dd22eb`（91% DE・想定では RESIDUAL）は **content_diversity=0.981（高多様）** で「低多様性」条件を満たさない → ルール上 TOPIC。DE 主体だが content は多様（DE observation は各々ユニーク）＝collapse でない。
- 想定が「purity だけ」で見ると RESIDUAL、ルールの「purity **かつ** 低多様性」では TOPIC。**ルールに忠実な結果を出しました。** もし「91%DE は broad な catch-all で topic でない」とするなら、purity 単独 or diversity 閾値の調整を裁定ください（現状は handoff の2条件 AND を実装）。

## 検証

- **F-A robust byte一致**: `--check` GREEN（commit pin・再フェッチ無し・offline/cache）。
- **負の制御 load-bearing 不変**: 列 shuffle で ARI 0.885→0.079（chance）。
- **個別軸ガード実測**: INTENT-pure（div 0.006）を RESIDUAL に実際に落とすことを実証。

## ハンドオフ

- 次: **CC 再監査（robust byte一致 + 個別軸 RESIDUAL 実測 + per-axis 記録）→ CONSISTENT → commit=Taka → DE 起票**（「意味埋め込みで TOPIC 軸あり + INTENT は退化=その他」）。TOPIC 数（2 か 3 か）の裁定があれば閾値を合わせます。
- その後 2b-r2（TOPIC 軸を versioned Frozenset に凍結 + 多重所属 + 濃淡）。
