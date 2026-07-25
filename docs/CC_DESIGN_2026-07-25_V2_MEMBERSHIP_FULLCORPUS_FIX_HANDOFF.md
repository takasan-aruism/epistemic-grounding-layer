# 設計/監査 → 実装: v2 membership を全 corpus 再評価に（HANDOFF・完全性修正）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論・CPU e5 pin `614241f6`
- 契機: CAND-48354b9a 凍結(v2)の再監査で membership_v2 の不完全を検出
- 実行 env 注記: `HF_HOME=/home/takasan/.cc_tmp/hf_home` + `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`（root 所有 .locks 回避・pin snapshot 直読）

## 0. 欠陥（再監査で確認）
- `build_v2`（s_rthread_2br3.py:157-）は `recs=その他部分集合(274)` を membership 母集団にする（`Xall=R._load_vectors(recs)`、line188）。
- コメントは「**全 corpus を v2 基準で再評価**」だが実際は その他 のみ → membership_v2=274。
- 由来: 2b-r3 は freeze-0 時代（v1=0軸）に作られ「その他=全corpus」が成立していた。v1 が AX-72ead44e を持つ今、その他(274)≠全corpus(388)。
- 帰結（要修正）:
  1. membership_v2 が AX-72ead44e 所属の **114件を欠落**（standalone な v2 完全 snapshot でない）。
  2. **多重所属漏れ**: 既存 114件が新軸 AX2-48354b9a にも一致するか未評価（多重所属は設計核）。
  3. **v2 の I1 が 274 しか検証しない**（全388の zero-drop 未担保）。

## 1. 依頼（最小・completeness 修正）
- `build_v2` の membership 再評価を **全 corpus(388)** に:
  - `Xall`/`recs` を **その他部分集合でなく全 corpus**（`R._content_records()` 全件）にして v2 全軸へ `A.assign_membership`（負の制御相対・既存共有・**新絶対定数ゼロ不変**）。
  - membership_v2 = 全388件・各要素を v2 の2軸に対して多重所属評価・`axes_version="v2"` 自己記述・全軸未達=その他。
- **候補 qualify（qualify_candidates）は その他(274) のまま不変**（候補は その他 から surface するのが正しい）。修正は**凍結後の membership_v2 母集団のみ**。
- v1（ACCOUNT_AXES_v1 / ACCOUNT_MEMBERSHIP）は不変・不触。

## 2. I1 保存則を v2 で全corpus に
- v2 の `check_conservation` を **membership_v2(388)** に対して行う（n_in=388, n_explained=388）。全388の zero-drop を担保。
- 候補段階（v2 未承認）の I1 は現状（その他=274）のままで可（そこは その他 の会計）。

## 3. ゲート
- `s_rthread_2br3.py --check` **byte一致 GREEN**。V2_FROZEN・no-auto-freeze・絶対定数ゼロ 不変。
- **v2 I1 が 388==388**（全corpus 保存）を assert（274 なら RED）。
- 多重所属が実際に起きうる（114件のいずれかが AX2 にも一致するなら記録される）ことを確認。

## 4. 受入（設計が独立再検証）
- 私が fresh 再実行（HF offline env）して membership_v2=**388**・v2 I1=388==388・byte一致 GREEN。
- v1 不変・絶対定数ゼロ不変・no-auto-freeze 不変。
- AX2-48354b9a と AX-72ead44e への所属数（多重所属含む）が全corpus で一貫。

## 5. 完了後
- `CC_IMPL_2026-07-25_V2_MEMBERSHIP_FULLCORPUS_FIX_BUILT.md`（宛 AUDIT/DESIGN）→ 設計再監査 → CONSISTENT → **commit=Taka**（凍結承認 marker + v2 + membership_v2 + 本修正を1コミット群）→ DE 起票。
- テスト由来タグ付け（MGR ADJRESULT ②）は別 follow-up（P2）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。freeze-0 前提の崩壊を completeness で根治。★3 本線・止めない。*
