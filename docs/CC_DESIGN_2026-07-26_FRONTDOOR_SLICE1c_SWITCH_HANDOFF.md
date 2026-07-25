# 設計/監査 → 実装: DE 記録を submit 経由へ switch（front-door slice1c）HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=egl / 決定論
- 正本: `CC_MGR_2026-07-26_FRONTDOOR_SLICE1_SWITCH_GO_HANDOFF.md`（switch GO・Taka 承認）+ DE-0538/0539 + 本 handoff
- 位置づけ: front-door 移行(A) slice1 の最終＝**DE 記録の呼び出し口を `admit_via_submit`（front door・実 ts）へ向ける**。我々の DE 記録が初めて正面玄関を通る。

## 0. 規律（厳守）
- **直叩きは閉塞しない**（enforcement なし・並行運用・ロールバック余地）。閉塞は後の別スライス（Taka）。
- sole-writer=egl.de_admission 不変（submit は呼ぶだけ）。hermetic・冪等・measure-first・commit=Taka。★3 本線は止めない。

## 1. 依頼: 正典 DE 記録ルーチン
- `structure/de_submit_route.py` に **`record_de(candidate, ts=None, ledger_path=None)`** を正典入口として整える:
  - 既定 = **front door 経由**（`admit_via_submit` → submit → egl.de_admission、実 ts）。
  - **rollback フラグ**（env or 引数 `route="submit"|"direct"`、既定 "submit"）で直叩き `admit_design_evidence` に即戻せる（並行運用・ロールバック手順を docstring に明記）。
  - 返り値は admission result（`admitted`/`design_evidence_id`/`admission_status`/…）で直叩きと同形。
- **切替点は「呼び出し口」のみ**（de_admission 本体・ledger schema は不変）。

## 2. real-ts 同値 再監査（switch 前・GREEN 必須）
- `s_de_route_equiv.py --check`: **実時刻 ts を渡した admission が front door 経由 == 直叩き で ledger 行 byte 同値**（代表 candidate・GREEN 必須）。差が出たら switch せず `ROUTE_DIVERGENCE` surface。
- `record_de(route="submit")` と `record_de(route="direct")` が同一 candidate+ts で byte 同値 ledger 行を生むことを hermetic（temp ledger）で確認。

## 3. dogfood（本 slice の DE を front door で記録）
- **slice1c の DE（DE-0540）自身を `record_de`（front door 既定）で実 ledger に記録**＝初の front-door DE。
- 記録後、その行が実 ts の正規 admission 行であること・DS thread event / RRI residual の front-door provenance が生成されたことを確認（provenance の永続先を BUILT に明記）。

## 4. 受入（設計が独立再検証）
- `s_de_route_equiv.py --check` GREEN（real-ts byte 同値）。`record_de` 既定が front door・rollback で direct に戻せる。
- DE-0540 が front door 経由で実 ledger に実 ts で記録され、直叩きと同値の行形。sole-writer=de_admission 不変・実 ledger は DE-0540 の1行増のみ（想定外汚染なし）。
- 全 gate GREEN。**直叩きパスは生きたまま**（並行運用の確認）。

## 5. 完了後
- `CC_IMPL_2026-07-26_FRONTDOOR_SLICE1c_SWITCH_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査（real-ts 同値 GREEN 確認）→ **switch 確定** → commit=Taka → DE-0540（front door 経由で記録済み）。
- 以後、我々の DE 記録は既定で front door。**直叩き閉塞はさらに後の別スライス**（MGR/Taka）。
- 次スライス② = 開発作業を DW workcell 経由へ（本 switch 固定後・別 handoff）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。呼び出し口のみ切替・直叩き未閉塞・rollback 余地・sole-writer 不変・初の front-door DE を dogfood。★3 本線・止めない。*
