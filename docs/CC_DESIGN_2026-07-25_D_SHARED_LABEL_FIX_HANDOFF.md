# 設計/監査 → 実装: build_D の label を「合意=SHARED」に（HANDOFF・小）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論
- 対応: `CC_IMPL_2026-07-25_D_SHARED_VS_CONFLICT_LABEL_FINDING.md`（label 意味論 flag）
- 裁定: **(b-minimal) を採用**。理由=同一 canonical への写像は **CANONICAL_STATES への authored（人が「同じ」と宣言）**からのみ生じる（auto-collapse 禁止のため）。ゆえに cross-machine 同一 canonical は**合意であって矛盾でない**。

## 依頼（最小・意味論の是正のみ・挙動は不変）
1. `build_D` の `conflicts` ラベルを **`CROSS_MACHINE_STATE_CONFLICT` → `CROSS_MACHINE_SHARED_STATE`** に改名。
   - 意味: 「複数 machine が **authored された同一 canonical** を共有」＝合意・正当・情報提示。surface する挙動自体は不変（STATE_THREAD_CLOSED の実点灯は維持）。
2. `--check` の D 検出力（§3-5 / 既存の CREATED→同 canonical 注入プローブ）の**期待ラベルを SHARED_STATE に更新**。検出力（load-bearing）は不変。
3. record のキー名も `shared`/`shared_state` 等に合わせて可読化（任意・byte 一致は再生成で更新）。

## やらないこと（今回スコープ外・独断で足さない）
- **AMBIGUITY カテゴリは追加しない**。理由: 同綴り未写像（例 CREATED）を「要裁定」と surface すると、**裁定B で distinct 確定済みの CREATED を誤って再浮上**させる。machine は現状「決定済み distinct」と「未決」を区別できない（CANONICAL 未写像＝両方 UNRESOLVED）。→ decided-distinct 表現の導入は必要時に別 ADJREQ で。
- 埋め込み・軸・membership・他ステージは不触。

## ゲート / 受入
- byte 一致再生成 GREEN。`s_task_contract --check` GREEN 維持。
- STATE_THREAD_CLOSED が `CROSS_MACHINE_SHARED_STATE` として surface（ds/rri）。
- D 検出力の陰性対照が SHARED_STATE ラベルで load-bearing。
- CREATED は UNRESOLVED のまま（surface しない・裁定B 維持）。

## 完了後
- `CC_IMPL_2026-07-25_D_SHARED_LABEL_FIX_BUILT.md`（宛 AUDIT/DESIGN）→ 設計再監査 → CONSISTENT → commit=Taka → 単独 DE（軽微）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。意味論の是正のみ・挙動不変。★3 本線・止めない。*
