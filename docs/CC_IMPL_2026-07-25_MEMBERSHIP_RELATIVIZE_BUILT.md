# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): membership を負の制御相対に（絶対 MEMB_TH 撤廃）BUILT・★3本線

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用・CPU e5 pin `614241f6`
- 対応: `CC_DESIGN_2026-07-25_MEMBERSHIP_RELATIVIZE_HANDOFF.md`（私の primary flag=membership 退化 の裁定＝相対化で根治）

## 成果物（working tree・未commit）
- `structure/s_account_axes.py`: `MEMB_TH` 撤廃 → `assign_membership()`（`density_a(e) − null_a > R.MARGIN`）+ `_null_density()`。gate に membership 陰性対照 + 絶対定数ゼロ検査を追加。
- `structure/s_rthread_2br3.py`: `A.MEMB_TH` 依存を廃し v2 re-membership も `A.assign_membership` を共有。
- 再baseline: `ACCOUNT_AXES_v1`/`ACCOUNT_MEMBERSHIP`（2b-r2）/`ACCOUNT_AXES_FREEZE_CANDIDATE`（2b-r3）/`TASK_CONTRACTS`。

## 実装（handoff §1・新絶対定数ゼロ）
- 各要素 e・各 frozen 軸 a: `density_a(e)`=cosine（従来）/ `null_a`=**列 shuffle 埋め込みの軸 a への平均 cosine**（anisotropy 下限・既存 `R._shuffle_features` 再利用）。
- 所属条件（相対）: `density_a(e) − null_a > R.MARGIN`（既存 `R.MARGIN` 再利用・**新定数ゼロ**）。多重所属可・全軸未達=その他。
- `MEMB_TH` 定数・`>= MEMB_TH` 判定・`membership_threshold` フィールドを削除 → `membership_rule`/`membership_margin`/`membership_null_per_axis` を記録。

## 検証（退化解消・陰性対照 load-bearing）— 実測
- **その他 が非ゼロで意味を持つ**: real_assigned=**114** / **その他=274** / 388 中。null_per_axis(AX-72ead44e)=**0.8948**（anisotropy 下限が定量化された。従来 MEMB_TH=0.55 はこの下限を大きく下回り全件所属していた）。
- **membership 陰性対照 load-bearing**: 列 shuffle 埋め込みで再割当 → assigned **388→1**（near-total 崩壊）。**回帰模擬 `null=0`（絶対閾値退化）では real=388/shuffle=388＝両方全件で崩壊せず RED 相当**。＝anisotropy 底上げでなく真の近さを測っている証拠。
- **絶対定数ゼロ**: `MEMB_TH in globals()` 検査で再導入を RED 化。
- **I1 保存不変**: 軸∪その他 で全要素説明（2b-r3: 274==274）。
- 埋め込み・frozen 軸方向は不変（相対化は membership 割当のみ・軸凍結ロジック不触）。

## 2b-r3 が genuine に評価可能に（UNEVALUABLE を脱した）
- 非退化 その他=274 に対し: K=8, cross-seed ARI **0.934 vs neg 0.030**（強 load-bearing）, 5候補中 **1 QUALIFIED**。
- **vacuous NO_CANDIDATE でなく genuine な measure-first 結果**（今度は「その他に更なる構造が1つ」を正直に検出）。
- 新 QUALIFIED = `CAND-48354b9a`（n=34, sil=0.270, sub=0.164, div=0.794, **kind_purity=1.0**, neg_margin=0.267）。→ **kind-pure ゆえ既裁定 Flag1=(a)（機械は propose のみ・kind 判断は #3 の Taka 承認）が支配**。機械は kind_purity 証拠を載せて停止済み。

## patch-bridge 軸の実体（handoff §4）
- `AX-72ead44e` 真の所属=**114**（全 REQUEST・patch-bridge topic の実サイズ）。従来の「全388所属」は退化だったことが確定。

## 全 gate GREEN + 決定論
`s_embed_axes`/`s_account_axes`/`s_rthread_2br3`/`s_task_contract`/`s_exec_arch_acd`/`s_llm_invocations`/`s_mine_accounts` の `--check` **全て byte一致 GREEN**。

## ハンドオフ
- 次: **設計/監査 独立再監査**（byte一致 / その他≠0 / membership 陰性対照 load-bearing / 絶対定数ゼロ / 2b-r3 genuine / measure-first で DE 再投入なし）。
- §6: 設計が `REQUIRED_INPUTS` から DE台帳除去（C drift 解消）→ **commit=Taka（DE除外+再baseline+membership相対化+2b-r3+contract+LLM_INVOCATIONS を1コミット群）** → DE 起票。
- 想定と実測: 退化解消は成功、その他=274 で 2b-r3 が 1 QUALIFIED（kind-pure・Flag1=(a) 支配）を surface。silently 合わせず正直記録。

---
*実装(IMPL)。★3本線。絶対閾値定数を負の制御相対で根治。measure-first 厳守。*
