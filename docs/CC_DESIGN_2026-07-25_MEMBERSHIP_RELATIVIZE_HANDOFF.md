# 設計/監査 → 実装: membership を負の制御相対に（絶対 MEMB_TH 撤廃）HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用・CPU e5 pin `614241f6`
- 正本: `CC_IMPL_2026-07-25_CORPUS_DE_EXCLUSION_REBASELINE_BUILT.md`(primary flag) + 裁定A(絶対閾値定数禁止) + 本 handoff
- 位置づけ: ★3 本線。2b-r3 を genuinely 評価可能にする前提（現状は membership 退化で vacuous）。

## 0. 問題（再監査で確認済）
- `s_account_axes.py` の `MEMB_TH=0.55`（絶対 cosine 閾値）は e5 anisotropy 下限(~0.81)を大きく下回る → frozen 軸への density が全388件 0.811〜0.984 → **全件1軸所属・その他=0**。
- 帰結: 2b-r3 が その他=0 で **vacuous NO_CANDIDATE**（弱い構造か退化か見分け不能）。
- `MEMB_TH=0.55` は**裁定Aが禁じた幻覚的絶対閾値定数**。撤廃する。

## 1. 依頼: membership を負の制御相対に（新絶対定数ゼロ）
- 各要素 e・各 frozen 軸 a について:
  1. `density_a(e)` = e の埋め込みと軸 a 方向の cosine（従来どおり）。
  2. **`null_a`** = 負の制御（列 shuffle）した埋め込みの軸 a への density（＝anisotropy 由来の下限・既存 shuffle 機構を再利用）。
  3. **所属条件（相対）: `density_a(e) − null_a > R.MARGIN`**（real−null margin。既存 `R.MARGIN` 再利用・**新定数を作らない**）。多重所属可（複数軸が条件を満たせば複数所属）。
  4. **全軸で未達なら その他/UNCLASSIFIED**。
- これで anisotropy 由来の底上げ（全件0.81+）が null で相殺され、**genuinely 軸に近い要素だけ所属**、残りは正当に その他。
- `MEMB_TH` 定数と `dens[a] >= MEMB_TH` 判定を削除。`ACCOUNT_AXES_v1.json` の `membership_threshold` フィールドも撤廃（or null_a/margin を記録）。

## 2. 再baseline
- s_account_axes（2b-r2 membership 再計算）→ s_rthread_2br3（2b-r3 を非退化 その他 に対して再評価）。
- 埋め込み・frozen 軸方向は不変（相対化は membership 割当のみ・軸凍結ロジックは触らない）。

## 3. ゲート（`s_account_axes.py --check` に追加/更新）
- **byte一致再生成**。
- **membership 相対性（陰性対照・load-bearing）**: 列 shuffle した埋め込みで再割当 → **所属が崩壊し全件 その他へ**（崩れなければ非 load-bearing=RED）。＝anisotropy 底上げでなく真の近さを測っている証拠。
- **絶対定数ゼロ**: `MEMB_TH` 等の絶対 cosine 定数が残っていれば RED。
- I1 保存不変（軸∪その他 で全要素説明）。

## 4. 報告（BUILT に正直に）
- 相対化後の **その他率**と各軸所属数。**その他が非ゼロで意味を持つか**（退化解消の実証）。
- 2b-r3 が非退化 その他 に対し候補を出すか / NO_CANDIDATE か（**今度は genuine な measure-first 結果**）。UNEVALUABLE を脱したことを示す。
- AX-72ead44e に真に所属する要素数（patch-bridge topic の実体サイズ）。

## 5. 受入（設計が独立再検証）
- 私が fresh 再実行して byte一致 GREEN・**その他≠0**（退化解消）・membership 陰性対照が load-bearing・絶対定数ゼロ。
- 2b-r3 が genuine に評価可能（vacuous でない）。measure-first で DE 再投入なし。

## 6. 完了後
- `CC_IMPL_2026-07-25_MEMBERSHIP_RELATIVIZE_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → CONSISTENT。
- そこで設計(私)が REQUIRED_INPUTS の DE台帳除去（C drift 解消）→ **commit=Taka（DE除外+再baseline+membership相対化+2b-r3+contract+LLM_INVOCATIONS を1コミット群）** → DE 起票。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。絶対閾値定数を相対化で根治。measure-first 厳守。★3 本線・止めない。*
