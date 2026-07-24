# 設計/監査 → 実装: EMBED_AXES fix handoff(F-A 再現性 pin / F-B 個別軸の自明性ガード)

- 発: 設計/監査(CC-α)/ 2026-07-25 / 対応監査: 独立検証で 2 finding
- repo=egl。CPU のみ。前提: `s_embed_axes.py` は AXES_FOUND を出したが下記2点で NOT fully CONSISTENT。

## finding(独立検証で確認)
- **F-A(再現性 fragile):** `--check` が既定で HF から再フェッチし revision="main"(可変)で再埋め込み → STABILITY.json 非一致(私の実測で RED)。ただし `HF_HUB_OFFLINE=1`+cache では **byte 完全一致**(=埋め込み自体は決定論)。**pin が甘い**だけ。
- **F-B(集約ガードが個別自明性を隠す):** 独立再計算で 4軸の種別構成 = AX-1ea3da2e(DE182+REQ132・話題)/ AX-36ff6cb7(INT23+REQ45・話題)/ AX-86dd22eb(DE336+REQ35・91%DE 境界)/ **AX-03251eb8(INT153・100%=自明)**。集約 kind_align 0.411 は通るが、**INTENT は content 退化(resolved が "DW_IMPLEMENTATION" 等ほぼ同一)で1点に固まっただけ**=話題でない。「4 clean axes」は過剰主張。

## 依頼(最小修正)
1. **F-A:** `REVISION` を `"main"` → 解決 commit **`614241f622f53c4eeff9890bdc4f31cfecc418b3"` に pin**。`--check`(と再生成)は **`HF_HUB_OFFLINE=1` 相当で cache 固定**し再フェッチしない(=byte一致を robust に)。resolved_commit は引き続き記録。
2. **F-B:** **個別軸の自明性ガード**を追加:各軸について (a) **kind 純度**(最大種別割合)と (b) **content 多様性**(メンバ埋め込みの分散 or 相異なる content 数)を測り、**「単一種別寄り(純度>=0.85)かつ低多様性」の軸は topic 軸でない → `axis_kind="RESIDUAL_OR_OTHER"` と印し、命名候補から外す**。stability に per-axis の {kind_purity, diversity, verdict(TOPIC|RESIDUAL)} を記録。
3. chart_status を精密化: **TOPIC 軸が1つ以上なら `AXES_FOUND`(ただし n_topic_axes を明記)/ 全て RESIDUAL なら NO_STABLE_AXES**。今回は **TOPIC=2(AX-1ea3da2e, AX-36ff6cb7)/ RESIDUAL=2** となる想定。
4. candidate は **TOPIC 軸のみ**を残し(RESIDUAL は members を別掲 or その他行)、name=null は不変(命名は 2b-r2)。

## 受入
- `--check` GREEN が **offline/cache で robust に byte一致**(私が再実行しても GREEN)。
- 負の制御 load-bearing(列 shuffle→崩壊)不変・自明ガードは**個別軸版**で INTENT-pure 軸を RESIDUAL に落とす(実測)。
- STABILITY に per-axis verdict と n_topic_axes を記録。**「2つの本物 + その他」を正直に出す。**

## 完了後
- `CC_IMPL_..._EMBED_AXES_FIX_BUILT.md` → 設計側が再監査 → CONSISTENT → commit=Taka → DE 起票(「意味埋め込みで TOPIC 軸2つ、残りはその他」= Taka モデルの実証)。
- その後 2b-r2(TOPIC 軸を versioned Frozenset に凍結 + 多重所属 + 濃淡)。
