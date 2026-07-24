# 設計/監査 → 実装: RTHREAD 2b-r2 発注(TOPIC 軸の凍結 + 多重所属 + 濃淡)

- 発: 設計/監査(CC-α) / 2026-07-25 / repo=egl / **CPU のみ・LLM 不使用・:8005 不使用・GPU 不使用**(決定論)
- 正本: `docs/RRI_SPEC_MACHINE_v1_1.json` + `docs/CC_DESIGN_2026-07-25_RTHREAD_STAGE2b_REDESIGN_PLAN.md`(§0/§2/§3) + 本 handoff
- 前提(検証済・commit 済): 2b-r1 は **AXES_FOUND / n_topic_axes=3 / RESIDUAL=1**(DE-0522 admitted, `s_embed_axes.py` in HEAD, tree clean)。埋め込み=`intfloat/multilingual-e5-small` @ commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`(pin 済)。
- 位置づけ: ★3(RRI 本線)クリティカルパス P1。A/C/D(P2)より優先。

## 0. 2b-r1 の確定結果(凍結の入力)

| axis | n | kind_purity | content_diversity | r1 verdict |
|---|---|---|---|---|
| AX-86dd22eb | 371 | 0.91 | 0.981 | TOPIC(DE 偏重・高多様=退化でない) |
| AX-1ea3da2e | 314 | 0.58 | 0.987 | TOPIC(cross-kind) |
| AX-36ff6cb7 | 68 | 0.66 | 0.985 | TOPIC(cross-kind) |
| AX-03251eb8 | 153 | 1.00 | 0.006 | RESIDUAL(INTENT 退化 collapse → その他) |

**凍結候補=上記 TOPIC 3 軸。RESIDUAL は凍結しない(その他行)。** ただし §2 の catch-all 裁定を先に通すこと。

## 1. 依頼(3 つ・順序厳守)

### §2. 【先に実施】AX-86dd22eb の catch-all 裁定(監査が 2b-r2 送りにした二次論点)
- 論点: AX-86dd22eb(91% DE・高多様)は「本物の DE 話題軸」か「DE の catch-all(寄せ場)」か。**r1 の centroid 凝集度は e5 の強い異方性(global 凝集度 0.919)で判別力が弱かった** → freeze 時に **separation ベースで測り直す**。
- 決定論テスト(operational definition):
  1. 各 TOPIC 軸について **silhouette**(自軸メンバ vs 他軸メンバの分離)を測る。
  2. 各 TOPIC 軸内で **k=2 の副分割**を試み、**sub-silhouette**(軸内の内部分離度)を測る。
  3. **判定規則**: ある軸の `sub_silhouette >= silhouette`(=他軸と区別されるより自軸内で強く割れている)なら **CATCH_ALL** と印し、**RESIDUAL/その他へ降格して凍結対象から外す**。そうでなければ COHERENT → 凍結。
  4. **負の制御**: 列(次元)shuffle で silhouette が chance へ崩れること(load-bearing)を確認(r1 と同型: real ARI 0.885→0.079 の枠組みを踏襲)。
- `per_axis` に `{silhouette, sub_silhouette, catch_all_verdict(COHERENT|CATCH_ALL)}` を記録。**凍結本数を silently 決めず、3 か 2 かを測定結果で正直に確定**(r1 の per-axis 正直報告と同じ規律)。

### §3. 凍結 = versioned Frozenset `ACCOUNT_AXES`
- COHERENT と確定した TOPIC 軸を **versioned frozen artifact** に凍結: `structure/ACCOUNT_AXES_v1.json`。
- 各軸に: `axis_id` / `frozen_direction`(centroid 単位ベクトル or seed member id 集合=決定論再現可能な形) / `version:"v1"` / `kind_verdict` / `catch_all_verdict` / seed member ids。
- **凍結後は drift させない。** 新軸の追加・軸の再定義は本スライスでは禁止(それは 2b-r3=再凍結規律・versioned で稀に、の担当)。曖昧を解消するために凍結軸を触らない(§3 規律)。

### §4. 多重所属 + 濃淡(density)= `structure/ACCOUNT_MEMBERSHIP.jsonl`
- 各問い(corpus 要素)について **軸ごとの密度**(frozen_direction への cosine 等・決定論)を出す。
- **多重所属可**(A and B を強制排他にしない)。**全軸で閾値未満なら `その他/UNCLASSIFIED`**(会計の「その他」)。
- **濃淡は observed quantity として projection に出すのみ。gate/branch/transition に一切入れない(T26・§3 規律)。** density に保存則を課さない(account 次元は soft)。

## 2. 常設ゲート(必須)= `structure/s_account_axes.py --check`
Stage B(`s_llm_invocations.py`)をテンプレに、同じ s-stage 型・同じゲート型で:
1. **再生成バイト一致**: pin 入力(e5 @ commit 614241f6 / cache 固定 / `HF_HUB_OFFLINE` 相当)から `ACCOUNT_AXES_v1.json` を再生成して byte 完全一致。
2. **凍結不変**: frozen 軸集合・direction が versioned ファイルと一致(drift=RED)。
3. **負の制御(load-bearing)**: 列 shuffle で membership/silhouette が chance へ崩壊(崩れなければ RED=非 load-bearing)。
4. `.npy` 等の埋め込みは derived(G-5)=非 commit。byte 一致は pin+cache で担保。

## 3. 規律(内蔵・違反=RED)
- **hard 不変量は問い台帳 I1(stage1 ゼロ落ち禁止)のみ。account 次元は soft**(密度に保存則を課さない)。
- **measure-first**: 軸が COHERENT と仮定しない。catch-all 裁定で 2 本になっても、それが正当な結果(過剰主張しない)。
- **調査中の修正禁止**の精神を踏襲: 想定と実測がズレたら silently 合わせず per_axis に正直記録し裁定を仰ぐ(r1 の TOPIC=2 予想外し→正直報告が良い規律だった)。
- 決定論・LLM 不使用・:8005/GPU 不使用。出力は `egl/structure/`。新 Ledger/Registry を作らない。

## 4. 受入(設計/監査が独立再検証する条件)
- 私が fresh 再実行して `ACCOUNT_AXES_v1.json` が **byte 一致**・`--check` GREEN robust。
- per_axis に `{silhouette, sub_silhouette, catch_all_verdict}` が記録され、AX-86dd22eb の COHERENT/CATCH_ALL が **測定で**確定(凍結本数の根拠が読める)。
- 負の制御が load-bearing(shuffle→崩壊)。
- membership が多重所属可・全軸閾値未満→その他 を実データで実証。**濃淡が何も gate しない**ことをコード上で確認可能。

## 5. 完了後(ハンドオフ)
- `CC_IMPL_2026-07-25_RTHREAD_2b-r2_..._BUILT.md` を書く → 設計/監査が独立再監査 → CONSISTENT → **commit=Taka** → DE 起票(「TOPIC 軸を versioned Frozenset に凍結・多重所属+濃淡・その他優勢」= Taka モデルの実装到達)。
- 次スライス予告: **2b-r3(再凍結規律)** = その他が育って濃い方向を持った時のみ、稀に・意図的に・versioned で新軸を追加凍結。本 handoff では触れない。

---
*設計/監査 CC-α。実装は本ファイル保存でトリガ。疑義は BUILT でなく途中でも `CONTRADICTIONS.jsonl` or 報告で上げてよい。過剰主張より正直な NO を優先。*
