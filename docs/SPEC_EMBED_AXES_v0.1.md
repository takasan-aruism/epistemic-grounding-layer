# SPEC: RTHREAD 2b-r1 EMBED_AXES v0.1 — 意味埋め込みで安定軸が出るかの経験的テスト

> **RTHREAD stage 2b 作り直しの第一スライス(measure-first)。** 内容の意味埋め込み(CPU)から
> **安定な離散軸(=科目候補)が実在するか**を、負の制御付きで測る。出れば 2b-r2 で凍結、出なければ「その他優勢」=正当な結果。
> 起草: 設計/監査(CC-α)/ 2026-07-25 / 正本: `CC_DESIGN_2026-07-25_RTHREAD_STAGE2b_REDESIGN_PLAN.md` + `RRI_SPEC_MACHINE_v1_1.json`。

- **置き場:** `egl/structure/s_embed_axes.py`。出力 `EMBED_AXES_STABILITY.json` + `EMBED_AXES_CANDIDATE.jsonl`(name=null)。
- **前提比較:** 構造素性マイニングは NO_STABLE(DE-0521, record-kind の自明分割のみ)。**本テストの問い=「内容の意味なら構造素性が拾えない話題軸が出るか」。**

## §0. 仕様との整合(明示的な supersede)
初版 mining_spec_order は「free text は素性にしない(prose Jaccard 0.51)」と禁じる。**これは浅い字句素性(Jaccard/token)への禁止**であり、本 spec が使う**学習済み意味埋め込み**は別物。Taka 方針(2026-07-25)がこの点を意図的に supersede する(意味ベクトルで軸を出す)。字句 Jaccard は使わない=禁止は精神として保つ。

## §1. 埋め込み(CPU・決定論)
- 各レコードの**内容テキスト**を作る: DE=`title + observation + decision`、rri REQUEST=`raw_input`、rri INTENT=`content.resolved`。IDや封印フィールドは含めない(内容のみ)。
- モデル= **`intfloat/multilingual-e5-small`(pin revision)**、`transformers` + `torch`(device=cpu, eval, no-grad)。e5 規約で `"passage: " + text`、mean-pool + L2 正規化。**決定論**(同一入力→byte一致ベクトル)。初回のみ HF から DL(GPU/serve 不要)。
- 出力ベクトルは 384 次元 float。**ベクトル自体は artifact 化しても gate しない(advisory・T26)。**

## §2. 軸抽出 + 安定性測定(MINING_SPEC の機構を流用)
- k-means を固定 seed 集合 {0..4} × K∈{4,6,8,10,12}、seed 決定論・辞書順 tie-break。
- **cross-seed agreement = chance 補正 ARI**(生 Rand でなく ARI。前回の計器教訓を継承)。
- **負の制御(load-bearing の核)**: 埋め込み行を固定 seed shuffle した「意味を壊した入力」で cross-seed ARI が崩れることを実測。崩れなければ vacuous → RED。
- **自明分割ガード(前回の教訓を継承)**: クラスタ vs record-kind の ARI が閾値(0.5)以上なら「また種別を復元しただけ」=軸でない。**内容軸と呼ぶには kind_align < 0.5 が必須。**
- 判定: `real_ari - neg_ari >= MARGIN(0.05)` **かつ** `real > neg` **かつ** `kind_align < 0.5` の時のみ `AXES_FOUND`、それ以外 `NO_STABLE_AXES`。

## §3. 出力
- `EMBED_AXES_STABILITY.json`: chart_status(AXES_FOUND | NO_STABLE_AXES)/ chosen_K / real・neg・kind ARI / margin / n_records / model+revision。
- `EMBED_AXES_CANDIDATE.jsonl`: AXES_FOUND 時のみ各軸 = {axis_id: `AX-<8hex>`(メンバ集合ハッシュ), members[], centroid_top_terms[](説明用・命名でない), name: null}。NO_STABLE 時は空(捏造しない)。

## §4. 受入(measure-first・出なくてよい)
- **byte一致再生成**(同一 seed・同一入力・同一モデル pin)。
- **負の制御が load-bearing**(意味 shuffle で ARI 崩壊を実測、恒等でない)。
- **自明ガード実測**(kind_align を記録、AXES_FOUND なら < 0.5 を実証)。
- **NO_STABLE_AXES を捏造なしで受容**(空 candidate)。
- 構造素性 NO_STABLE(DE-0521)との対比を stability に記録(意味 vs 構造で結論が変わるか)。

## §5. スコープ / 非スコープ
- v0.1 = **軸が在るかの測定のみ**。凍結(Frozenset)・多重所属・濃淡表示は **2b-r2(AXES_FOUND 時のみ)**。
- LLM(:8005)不使用(CPU 埋め込みのみ)。density は最後まで gate しない。
- hard 不変量は問い台帳 I1 のみ(本スライスは会計に触れない=測定専用)。

## §6. 完了後
- `CC_IMPL_..._EMBED_AXES_BUILT.md` → 設計側が再監査(byte一致 + 負の制御 load-bearing + 自明ガード + 非捏造)→ CONSISTENT → commit=Taka → DE 起票(AXES_FOUND でも NO_STABLE_AXES でも登記)。
