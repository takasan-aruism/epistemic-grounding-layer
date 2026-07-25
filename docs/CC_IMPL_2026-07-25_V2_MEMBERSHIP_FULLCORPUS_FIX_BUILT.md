# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): v2 membership を全corpus再評価に（BUILT・completeness 修正）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・CPU e5 pin `614241f6`
- 対応: `CC_DESIGN_2026-07-25_V2_MEMBERSHIP_FULLCORPUS_FIX_HANDOFF.md`

## 欠陥の所有（私の bug）
再監査の指摘は正当でした。`build_v2` の membership 母集団を **その他部分集合(274)** にしていた（コメントは「全corpus再評価」だが実コードは `R._load_vectors(recs)`＝subset を反復）。由来=2b-r3 を freeze-0 時代（v1=0軸→その他=全corpus）に作ったため。v1 が AX-72ead44e を持つ今 その他(274)≠全corpus(388)。→ AX-72ead44e の114件欠落 / 多重所属未評価 / v2 I1 が 274 過小担保。**私の欠陥として修正しました。**

## 成果物（working tree・未commit）
- `structure/s_rthread_2br3.py`（**唯一の変更**。`build_v2` の membership 母集団を全corpus に + `--check` に v2 completeness assert 追加）
- 生成物 jsonl は **不変**（現状 propose-only=marker 未投入ゆえ v2 は未生成。fix は marker 投入時の挙動）。

## 実装（handoff §1-2・最小・新絶対定数ゼロ不変）
- `build_v2` の re-membership: `full_recs = R._content_records()`（全388）・`Xfull = R._load_vectors(full_recs)` → `A.assign_membership(Xfull, dirs)`（負の制御相対・v2全軸・多重所属可）。membership_v2 = 全388・`axes_version="v2"` 自己記述・全軸未達=その他。
- **候補 qualify は その他(274) のまま不変**（候補は その他 から surface が正しい）。修正は凍結後 membership_v2 の母集団のみ。
- 新軸方向は その他 の候補クラスタ centroid から（不変）。v1（ACCOUNT_AXES_v1 / ACCOUNT_MEMBERSHIP）不変・不触。
- `--check` に **`len(memb2) != len(全corpus) → V2_MEMBERSHIP_INCOMPLETE` RED**（274 で評価していたら RED＝旧 bug を捕捉。`len!=388` ゆえ本質的に load-bearing）。

## 検証（temp marker で凍結を模擬 → 実測 → clean で propose-only 復帰）
承認 marker（`FREEZE_APPROVALS.jsonl` に CAND-48354b9a）を一時投入して凍結挙動を実測（実 marker は authored 系＝設計/承認チャネル所掌ゆえテスト後 remove）:
- **membership_v2 = 388**（全corpus）✓・`axes_version=v2` ✓。従来 274 → 根治。
- **v2 I1 = 388==388**（全corpus zero-drop 担保）✓。候補段階の I1 は その他=274 のまま（そこは その他 の会計・handoff §2 どおり）。
- v2 FROZEN=2軸: `AX-72ead44e`（v1・patch-bridge REQUEST）=**114** / `AX2-48354b9a`（新・承認済み）=**28**。assigned=142 / その他=246。
- **多重所属=0**（機構は多重所属可だがこの2軸は非重複＝正直な実測。114件中 AX2 にも一致する要素は無し）。
- `--check` GREEN（V2_FROZEN(2)・no-auto-freeze 不変・byte一致・I1 388==388）。clean 後 propose-only で GREEN（I1 274==274）。

## marker について（役割確認・私の FINDING と整合）
- 実 `FREEZE_APPROVALS.jsonl`（filename typo `FREEST_APPROVALS` に注意=別 FINDING）は **authored 系ファイル＝設計/承認チャネル所掌**と理解し、私は投入していません（テストは一時 marker→remove）。
- CC-α が正しい filename で marker を authored → `python3 s_rthread_2br3.py`（HF offline env）で v2/membership_v2(388) が生成されます。私が marker も書くべきなら指示ください（Taka 承認は ADJRESULT で記録済み）。

## ハンドオフ
- 次: 設計再監査（HF offline env で fresh 再実行 → membership_v2=388・v2 I1=388==388・byte一致 GREEN・v1不変・絶対定数ゼロ不変・no-auto-freeze 不変）。
- §5: commit=Taka（凍結承認 marker + v2 + membership_v2 + 本 completeness 修正 + 本セッションの他修正群を1コミット群）→ DE 起票。テスト由来タグ付け（MGR ②）は別 P2 follow-up。

---
*実装(IMPL)。freeze-0 前提の崩壊を completeness で根治。自分の bug を silently 直さず所有・記録。★3 本線は止めていません。*
