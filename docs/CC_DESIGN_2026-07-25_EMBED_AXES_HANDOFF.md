# 設計/監査 → 実装: RTHREAD 2b-r1 EMBED_AXES handoff(CPU 意味埋め込みで軸が出るか測る)

- 発: 設計/監査(CC-α)/ 2026-07-25 / 正本: `SPEC_EMBED_AXES_v0.1.md`
- **repo=egl**(structure)。**CPU のみ・GPU/:8005 不使用・スリープ不使用**(Taka 方針)。measure-first。

## 依頼(SPEC §1〜§4)
1. `egl/structure/s_embed_axes.py` を実装。DE ledger + rri_records の**内容テキスト**を `intfloat/multilingual-e5-small`(pin, CPU, eval, no-grad, `passage: ` 接頭, mean-pool+L2)で埋め込み。初回のみ HF DL(GPU/serve 不要の acquisition)。
2. k-means(seed{0..4}×K{4,6,8,10,12})で軸抽出。**ARI(chance 補正)** で cross-seed 安定・**負の制御(埋め込み行 shuffle→崩壊)**・**自明分割ガード(cluster vs record-kind ARI<0.5)** を測る。
3. 判定=`(real-neg)>=0.05 and real>neg and kind_align<0.5` → `AXES_FOUND` / それ以外 `NO_STABLE_AXES`。
4. 出力 `EMBED_AXES_STABILITY.json` + `EMBED_AXES_CANDIDATE.jsonl`(NO_STABLE なら空・捏造しない)。`--check`=byte一致 + 負の制御 load-bearing。

## 拘束
- **CPU のみ**(torch device=cpu)。:8005/GPU/スリープに触れない。モデルは pin(revision 固定)で決定論・byte一致。
- **字句 Jaccard を使わない**(意味埋め込みのみ)。density/embedding は gate/branch/transition に入れない(T26・advisory)。
- **measure-first**: 軸が在ると仮定しない。**NO_STABLE_AXES は正当な結果**(前回 DE-0521 と同じ retention)。無理に軸を立てない→ green のため負の制御/自明ガードを弱めるなら halt。
- スコープ=**軸が在るかの測定のみ**。凍結/多重所属/濃淡は 2b-r2(AXES_FOUND 時のみ)。

## 完了後
- `CC_IMPL_..._EMBED_AXES_BUILT.md` → 設計側が再監査 → CONSISTENT → commit=Taka → DE 起票(結果に依らず)。
- AXES_FOUND なら 2b-r2(凍結 Frozenset + 多重所属 + 濃淡)へ。NO_STABLE_AXES なら「意味でも構造でも決定論では軸が出ない」を Taka 裁定候補に。
