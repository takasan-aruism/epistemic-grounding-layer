# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): DE 記録を submit 経由へ switch（front-door slice1c・BUILT）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-26 / repo=egl(+ds provenance) / 決定論
- 対応: `CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1c_SWITCH_HANDOFF.md`（switch GO・Taka 承認）
- **マイルストーン: 我々の DE 記録が初めて正面玄関(front door)を通った＝「外からの侵入」から「内部アクター」への実移行の第一歩。** [[ai-must-be-internal-actor-not-intruder]]

## 成果物（working tree・未commit）
- `structure/de_submit_route.py`（正典 DE 記録ルーチン `record_de` 追加）
- `structure/s_de_route_equiv.py`（record_de の route 同値検証を追加）
- `DESIGN_EVIDENCE_LEDGER.jsonl`（**+1 行=DE-0540・front door 経由で記録**）
- （ds repo）`ds_events.jsonl`（+2＝front-door DS 証跡）

## 実装（handoff §1・切替点は呼び出し口のみ）
- **`record_de(candidate, ts=None, ledger_path=None, route=None)`**: 正典入口。**既定=front door**（`admit_via_submit`→submit→egl.de_admission・実 ts）。
  - **rollback**: `route="direct"`（or env `DE_ROUTE=direct`）で即 直叩き `admit_design_evidence` へ戻る（**直叩き未閉塞・並行運用・ロールバック余地**）。解決順=引数→env→"submit"。docstring に手順明記。
  - 返り=admission result（直叩きと同形）。de_admission 本体/ledger schema は不変（sole-writer=egl.de_admission）。

## real-ts 同値 再監査（switch 前・§2・GREEN 必須）
`s_de_route_equiv.py --check` **GREEN**:
- 実時刻形式 ts 注入で **front door 経由 == 直叩き の ledger 行 byte 同値 4/4**（ADMITTED/REJECTED-schema/REJECTED-ceiling/BEHAVIORAL-downgrade）。
- **record_de の route="submit" と route="direct" が同 candidate+ts で byte 同値**（切替点 dispatch が行を変えない）。
- 後方互換（ts 未指定 submit=既定 ts）・front-door provenance 生成・sole-writer 不変・**実 ledger 不汚染**（hermetic）。

## ★ dogfood: 初の front-door DE（DE-0540）を実 ledger に記録（§3）
`record_de`(既定 front door) で **DE-0540 を実 ledger に記録**（Taka 承認済み switch GO の実行）:
- 記録行: `DE-0540` ADMITTED / `admitted_at=2026-07-25T16:25:45Z`（**実 UTC 時刻**・now_ts 生成）/ `generated_by_principal=CLAUDE_CODE`（**内部アクター開示**・FI-MIN-4 通過）/ `admitted_by=egl.de_admission`（**sole writer 不変**）。
- **front-door provenance 永続先（実測 delta）**:
  - `egl/DESIGN_EVIDENCE_LEDGER.jsonl` **+1**（DE-0540 の DE 行・egl.de_admission が唯一の writer）。
  - `ds/ds_events.jsonl` **+2**（DS 証跡＝utterance ingestion + `DEV_EVIDENCE_ADMISSION` dialogue event＝正面玄関を通った証拠）。
  - `rri/rri_records.jsonl` **+0**（RRI residual は TRACE 内で算出・rri_records に永続せず＝**mining corpus 不汚染**。DE 台帳を corpus から除外した決定[DE Flag2]の恩恵で、front-door DE が 2b 軸を drift させない）。
- loop trace: `DS_INPUT → RRI_CLASSIFY → EGL_ADMISSION → EGL_LEDGER_APPEND → RRI_RESIDUAL → DS_THREAD_UPDATE`。

## 受入（§4・全 gate GREEN）
- `s_de_route_equiv.py --check` GREEN（real-ts byte 同値）。`record_de` 既定=front door・rollback で direct に戻せる。
- **DE-0540 が front door 経由で実 ledger に実 ts で記録**・直叩きと同値の行形・sole-writer=de_admission 不変・**実 ledger は DE-0540 の1行増のみ**（想定外汚染なし）。
- 全 gate GREEN（s_de_route_equiv / regen_meta / s_task_contract / s_account_axes / s_embed_axes）。**直叩きパスは生きたまま**（並行運用）。

## ハンドオフ / commit
- 次: 設計独立再監査（real-ts 同値 GREEN / DE-0540 の front-door 記録 / provenance 永続 / rollback / sole-writer 不変）→ **switch 確定**。
- **commit=Taka（cross-repo: egl[ledger + de_submit_route + s_de_route_equiv] + ds[ds_events]・各 push）**＝[[2der_repo_topology]] の個別 commit/push 規律（片方だけ push しない）。DE-0540 は既に front door で記録済み（本 slice の DE）。
- 以後、我々の DE 記録は既定で front door。**直叩き閉塞はさらに後の別スライス**（MGR/Taka）。次スライス② = 開発作業を DW workcell 経由へ（本 switch 固定後・別 handoff）。

---
*実装(IMPL)。呼び出し口のみ切替・直叩き未閉塞・rollback 余地・sole-writer 不変・初の front-door DE を dogfood(CLAUDE_CODE 開示)。★3 本線・止めない。*
