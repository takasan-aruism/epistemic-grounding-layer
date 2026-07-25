# 設計/監査 → 実装: RTHREAD 2b-r3 発注（再凍結規律 / 機械propose→Taka approve）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / **決定論・LLM 不使用・:8005/GPU 不使用・CPU e5 pin `614241f6`**
- 正本: `CC_MGR_2026-07-25_2BR3_CANONICAL_ADJUDICATION_RESULT.md`(裁定A) + `CC_DESIGN_2026-07-25_RTHREAD_STAGE2b_REDESIGN_PLAN.md`(§2 2b-r3) + DE-0524(2b-r2 freeze-0) + 本 handoff
- 位置づけ: ★3 本線。P2 の Task Contract 作業と並行だが本線を止めない。
- 前提: 2b-r2 は freeze-0（その他優勢）。ゆえに現状 その他/UNCLASSIFIED = ほぼ全 corpus。2b-r3 は**その他が濃い方向を持ったら稀に・意図的に・versioned で新軸を追加凍結**する規律の機械化。

## 0. 絶対規律（裁定A・違反=RED/REJECT）
- **新しい絶対閾値定数を導入しない。** 濃さ・本物判定はすべて**負の制御に対する相対 margin**で表す（幻覚定数の禁止）。
- **機械は凍結しない。候補を証拠付きで surface するだけ。** 実凍結の引き金は Taka 承認（versioned commit=Taka）。
- 決定論・sole-writer 分離維持・捏造ゼロ（候補が無ければ NO_CANDIDATE を正直に）。

## 1. 対象と #1「濃い」（絶対閾値なし）
- 対象 = 現 membership の **その他/UNCLASSIFIED 部分集合**（2b-r2 の `ACCOUNT_MEMBERSHIP` で全軸閾値未満のもの）。
- **#1 濃さ = 2b-r1 と同一の load-bearing 相対検定を その他部分集合に適用**（新定数なし・既存機構再利用）:
  1. その他集合を決定論 k-means で候補方向へ分割し、
  2. **cross-seed 安定**（複数 seed で ARI が高位安定）、
  3. **負の制御（列 shuffle）で silhouette が chance へ崩壊**（load-bearing）、
  4. 候補方向の silhouette が **shuffle margin を超える**。
  - 4条件すべて満たす方向のみ「濃い候補」。満たさなければ **NO_CANDIDATE（その他優勢継続）= 正当な結果**（DE 化）。

## 2. #2 本物 vs ノイズ（退化 collapse 前科・既存ガード再利用）
- 濃い候補は追加で: **F-B 自明性ガード（DE-0522）= content_diversity > 0.30** かつ **2b-r2 catch-all silhouette 検定（sub_silhouette < silhouette）** を通過必須。
- 低多様 collapse / 内部で割れる catch-all は **RESIDUAL に落とし候補から除外**（INTENT 退化の再来を防ぐ）。

## 3. #3 propose→approve（機械は凍結しない）
- 通過候補を `structure/ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl` に**証拠付きで surface**: `{candidate_id, member_ids(seed), silhouette, sub_silhouette, content_diversity, neg_control_margin, cross_seed_ARI, verdict:"QUALIFIED"}`。
- **機械はここで停止**。`ACCOUNT_AXES_v2.json` を自動生成しない。
- 承認経路: Taka approve（versioned commit）時のみ v2 を書く。実装は **approval marker（例 `FREEZE_APPROVALS.jsonl` に candidate_id + approved_by=Taka）が在るときだけ** v2 を生成。marker 無しで v2 を書いたら RED。

## 4. #4 versioning（versioned-append・破壊的再計算なし）
- 承認時: `ACCOUNT_AXES_v2.json` = **v1 の軸を不変コピー + 承認された新軸1本**。`ACCOUNT_AXES_v1.json` は不変（触らない）。
- membership 記録は必ず **`axes_version` を自己記述**。旧 v1 membership は v1 基準のまま不変（再計算しない）。新規/再実行は v2 基準。

## 5. #5 I1 保証（保存則・易しい・淡々と実装）
- freeze/再membership 後に **`count(stage1 問い in) == count(軸∪その他 で説明済み)`** を assert（各問いは 1つ以上の軸 or その他、ゼロ落ちゼロ）。
- **その他が catch-all** ゆえ構造的にゼロ落ちしない。これは曖昧でなく単純な不変量チェック。

## 6. 常設ゲート = `structure/s_rthread_2br3.py --check`（全 GREEN で PASS）
1. **byte 一致再生成**（候補・membership）。
2. **候補検出力（陰性対照）**: その他に合成の濃い方向を注入→QUALIFIED 検出 / 列 shuffle で崩壊（load-bearing）。
3. **退化除外（陰性対照）**: 低多様 collapse を注入→RESIDUAL に落ちる（凍結候補に残ったら RED）。
4. **no-auto-freeze**: approval marker 無しで v2 が存在したら RED。
5. **I1 保存則**: 問い数保存（ゼロ落ち検出）。

## 7. 受入（設計が独立再検証）
- 私が fresh 再実行して候補・membership が byte 一致・`--check` GREEN robust。
- 陰性対照（候補検出 / 退化除外 / no-auto-freeze / I1）で**実際に RED が出る**（load-bearing）。
- **絶対閾値定数ゼロ**（全判定が負の制御相対）。候補が無ければ `NO_CANDIDATE` を正直表示。
- v2 は approval marker 無しには生成されない（機械は propose のみ）。

## 8. 完了後
- `CC_IMPL_2026-07-25_RTHREAD_2b-r3_..._BUILT.md`（宛: AUDIT/DESIGN）→ 設計独立再監査 → CONSISTENT → **commit=Taka** → DE 起票。
- 初回は候補ゼロ（NO_CANDIDATE）でも正当（measure-first）。機構が「話題が積もった時に稀に発火する」状態で在ることが成果。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録。過剰主張より正直な NO_CANDIDATE。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ。裁定要求が要る時は CC_DESIGN_*_ADJREQ.md（宛: MGR）へ。★3 本線・止めない。*
