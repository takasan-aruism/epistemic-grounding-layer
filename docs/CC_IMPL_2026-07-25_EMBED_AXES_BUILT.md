# 実装担当 → 設計/監査担当: RTHREAD 2b-r1 EMBED_AXES v0.1（BUILT・結論 AXES_FOUND）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-25
- 対応: `SPEC_EMBED_AXES_v0.1.md` / `CC_DESIGN_2026-07-25_EMBED_AXES_HANDOFF.md`
- repo=egl。CPU のみ・:8005/GPU/スリープ不使用。measure-first。

## 成果物（working tree・未commit）

- `egl/structure/s_embed_axes.py`（CPU e5 埋め込み＋k-means＋ARI＋負の制御＋自明ガード＋`--check`）
- `egl/structure/EMBED_AXES_STABILITY.json`（測定記録）
- `egl/structure/EMBED_AXES_CANDIDATE.jsonl`（**4 軸候補**・name=null・凍結は 2b-r2）
- `structure/.embed_axes_vectors.npy`（埋め込みの内部キャッシュ＝再生成可・DL 回避用。commit 対象外推奨）

## 結論: `AXES_FOUND`（意味埋め込みで安定な内容軸が実在）

構造素性は NO_STABLE(DE-0521, record-kind 自明分割のみ)だったが、**意味埋め込みは話題軸を出す**:
- モデル `intfloat/multilingual-e5-small`（CPU, eval, no-grad, `passage:` 接頭, mean-pool+L2, 6桁丸め・決定論）。records=906（DE 518 / REQUEST 212 / INTENT 176・内容テキストのみ、ID/封印は不使用）。
- K=4 採用（K∈{4,6,8,10,12} で最大）。**real ARI=0.885 / neg ARI=0.079 / real-neg=0.806 / kind_align=0.411**。
- **4 軸はクロス種別の話題クラスタ**（例: 軸2=DE182+REQUEST132 混在、軸4=INTENT23+REQUEST45）＝record-type でなく topic。

## 検証（負の制御が load-bearing の核）

- **負の制御が chance まで崩壊**: 埋め込みの各次元を固定 seed で shuffle → cross-seed ARI が 0.885→**0.079**（≈chance）。構造版(neg 0.52)と対照的に**意味構造は shuffle で消える＝load-bearing**。（注: handoff の「行 shuffle」は点集合不変で非 load-bearing のため、MINING で実証済みの**列(次元)shuffle**を採用。）
- **自明分割ガード**: kind_align=0.411 < 0.5＝「また record-kind を復元しただけ」でない（クロス種別混在で実証）。
- **byte一致再生成**: `--check` GREEN（埋め込みは .npy キャッシュで再 DL 不要・同一入力→同一クラスタ）。
- **判定を甘くしていない**（MARGIN 0.05・自明ガード 0.5・chance 補正 ARI・負の制御は列 shuffle）。

## 実装中に修正した bug（結論前の diligence）

- 初回 REQUEST 抽出が spec の `raw_input` でなく `content.raw` を見て **212 中 211 を空判定→脱落**（軸が DE/INTENT のみに偏った）。REQUEST content は異種（raw_input153/t45/task13/raw1）と判明し、全て拾うよう修正 → 906 件・**REQUEST を含むクロス種別軸**で AXES_FOUND が強化（real 0.76→0.885）。

## 構造 vs 意味の対比（§4 記録）

- **構造素性=NO_STABLE(record-kind のみ) / 意味埋め込み=AXES_FOUND(cross-kind topic)**。→「決定論の構造素性では chart が出ないが、CPU 意味埋め込みでは安定な話題軸が出る」＝ chart-of-accounts の抽出源は**意味ベクトル**が妥当、という finding。

## ハンドオフ

- 次: **CC 再監査（byte一致 + 負の制御 load-bearing + 自明ガード + 非捏造）→ CONSISTENT → commit=Taka → DE 起票**。
- AXES_FOUND ゆえ **2b-r2（軸を versioned Frozenset `ACCOUNT_AXES` に凍結 + 多重所属 + 濃淡観測）へ進める**（別スライス・SPEC 待ち）。命名（centroid_top_terms）は 2b-r2 で。
