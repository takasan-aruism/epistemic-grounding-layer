# CC 管理(MGR) → 設計/監査(CC-α): slice1 switch GO（HANDOFF）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-26 / TYPE=HANDOFF
- 対応: `CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1_TS_SOURCE_ADJRESULT`（判断①(a)/②）+ DE-0538/0539
- 権限: **Taka 承認（2026-07-26「次に進めて構わん」＝switch GO）**。

## GO：DE 記録ルーチンを submit 経由へ switch
proof(DE-0538) と submit ts pass-through(DE-0539) 完了。**実時刻を渡した状態で最終の同値を確認し、DE 記録の実ルーチンを `admit_via_submit`(submit front door 経由) へ切替**してよい。
＝我々の DE 記録が初めて正面玄関を通る＝「外からの侵入」でなく「内部アクター」への実移行の第一歩。

## デリケート・ハンドリング（厳守）
1. **switch 前に real-ts 同値を再監査**：submit に実時刻を渡した admission が、直叩きと **byte 同値の ledger 行**を生むことを代表 candidate で再実証（GREEN 必須）。差分が出たら switch せず surface。
2. **直叩きパスは閉塞しない**（この slice では enforcement しない）。並行運用のまま＝ロールバック余地を残す。閉塞は後の別スライス（Taka 判断）。
3. switch の実体＝「DE 記録の呼び出し口を `admit_via_submit` に向ける」だけ。sole-writer=de_admission 不変（submit は呼ぶだけ）。
4. hermetic・冪等・measure-first・commit=Taka・★3(帳簿)は止めない。

## 依頼フロー
DESIGN が switch spec（real-ts 同値再監査ハーネス・切替点・ロールバック手順・不変テスト）→ IMPL 実装 → AUDIT 独立再監査 → **real-ts 同値 GREEN を確認**して switch → commit=Taka → DE 起票。
- 監査が「real-ts でも byte 同値 GREEN」を出せば switch 実行可（追加 Taka 確認不要）。**もし同値が崩れる／想定外が出たら MGR 経由で最小 set を Taka へ**。

## 次（本 slice 完了後）
優先順② = 開発作業を DW workcell 経由へ（最重要）。本 slice の switch が固まってから別 handoff。
