# CC 設計/監査 → 実装: EMBED_AXES(F-A/F-B fix)再監査 = CONSISTENT

- 発: 設計/監査(CC-α)/ 2026-07-25 / 対応: `CC_IMPL_2026-07-25_EMBED_AXES_FIX_BUILT.md`
- 正本: `SPEC_EMBED_AXES_v0.1.md` + `CC_DESIGN_2026-07-25_EMBED_AXES_FIX_HANDOFF.md`

## VERDICT: **CONSISTENT**。AXES_FOUND(意味埋め込みで安定軸あり)。commit=Taka gate へ。

self-report を鵜呑みにせず独立再検証:
- **F-A 解消(検証済み):** REVISION を commit `614241f6…` に pin、snapshot_download 撤去。**私が fresh 再生成しても STABILITY.json byte 完全一致**、`--check` GREEN robust(前回は online 再フェッチで RED だった)。
- **F-B 中核解消(検証済み):** per-axis に kind_purity/content_diversity/verdict を記録。**INTENT-pure 軸(purity 1.0・diversity 0.006=resolved 退化 collapse)を RESIDUAL に落とし candidate から除外**。
- **負の制御 load-bearing 不変:** 列(次元)shuffle で real ARI 0.885→0.079(chance)。行 shuffle=非 load-bearing を実装が正しく回避(私の spec の誤りを訂正)。

## 正直な結果(過剰主張しない)
`chart_status=AXES_FOUND / n_topic_axes=3 / RESIDUAL=1`。per-axis:
| axis | n | purity | diversity | verdict |
|---|---|---|---|---|
| AX-86dd22eb | 371 | 0.91 | 0.981 | TOPIC(=DE偏重だが高多様=退化でない) |
| AX-1ea3da2e | 314 | 0.58 | 0.987 | TOPIC(クロス種別) |
| AX-36ff6cb7 | 68 | 0.66 | 0.985 | TOPIC(クロス種別) |
| AX-03251eb8 | 153 | 1.00 | 0.006 | RESIDUAL(退化) |

- **私の TOPIC=2 予想は外れ、私自身のルール(purity≥0.85 **かつ** diversity<0.30)を忠実適用すると TOPIC=3。** 実装は silently 決めず正直に差分を報告した(良い規律)。AX-86dd22eb(91%DE・高多様)は退化でないためルール上 TOPIC。
- **未解決の二次論点(2b-r2 送り):** AX-86dd22eb が「本物の DE 話題」か「DE の catch-all」か。私は凝集度で判別を試みたが、**e5 埋め込みの強い異方性(global 凝集度 0.919)で centroid-凝集度は判別力が弱い**。→ **freeze 時(2b-r2)に silhouette 等で凝集度を測り、catch-all なら RESIDUAL/その他へ**。r1(=軸が在るか)の結論には影響しない。

## 核心 finding
**構造素性=NO_STABLE(DE-0521)/ CPU 意味埋め込み=AXES_FOUND(TOPIC 3・退化1)。** chart の抽出源は**意味ベクトル**が妥当。ただし「clean な多数の科目」ではなく「**少数の本物の軸 + 退化/その他**」=Taka モデル(凍結される少数軸+その他優勢)の実証。

## commit 対象(Taka gate / 「任せる」委任下)
- `egl/structure/s_embed_axes.py` / `EMBED_AXES_STABILITY.json` / `EMBED_AXES_CANDIDATE.jsonl`。`.npy` は derived(G-5)ゆえ非 commit(pin モデル+cache で byte一致再現を確認済み)。
- DE 起票=「意味埋め込みで TOPIC 軸あり・INTENT は退化その他」。次=2b-r2(TOPIC 軸を versioned Frozenset 凍結 + 多重所属 + 濃淡、freeze 時に catch-all 凝集度判定)。
