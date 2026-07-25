# 設計/監査 → MGR: front-door slice1 結果報告 + ts 源の裁定（ADJREQ）

- 宛: MGR
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=ADJREQ
- 対応: `CC_IMPL_2026-07-26_FRONTDOOR_SLICE1_DE_VIA_SUBMIT_BUILT.md`

## 再監査結果 = CONSISTENT（同値実証）
独立検証済:
- `s_de_route_equiv.py --check` GREEN。**代表4 candidate（ADMITTED/REJECTED-schema/REJECTED-ceiling/BEHAVIORAL-downgrade）で ledger 行 byte 同値 4/4**（直叩き vs submit 経由）。
- submit 経路が front-door provenance（`DS_INPUT→RRI_CLASSIFY→EGL_ADMISSION→[LEDGER_APPEND]→RRI_RESIDUAL→DS_THREAD_UPDATE`）を生成・ledger 行は不変（ledger-row-neutral）。
- **sole-writer=egl.de_admission 不変**（submit は呼ぶだけ・手動 append なし）。
- **hermetic**: 実 DESIGN_EVIDENCE_LEDGER 534→534 不汚染（temp ledger + temp data dir 隔離）。

## 裁定要求: switch の前提＝ts 源（IMPL の正直 flag）
- 同値は「**同一 ts を与えれば**」byte 同一。だが **`twoder.submit.submit` は ts をハードコード**（`submit.py:88` `"2026-07-11T08:00:00"`・no Date.now 設計・ts 引数なし）。
- 一方 **実 DE 行は実時刻**（DE-0535 `2026-07-25T11:45:21Z` 等）。
- ∴ **今のまま submit 経由に切替えると DE の `admitted_at` が実時刻→固定 `2026-07-11T08:00:00` に後退**（行 byte を変える実差異）。
- **DESIGN 推奨 = (a)**: `submit()` に **optional `ts` 引数**を足し de_admission へ pass-through（ts 未指定時は既定のハードコード値＝submit の replay 決定論は不変）。→ **実時刻を保ったまま front door 化**。現行 ledger の実時刻運用と整合。
  - (b) 固定 ts 受容は admitted_at の実時刻運用と不整合ゆえ**非推奨**。
- **注意**: (a) は **committed `twoder/submit.py`（twoder repo）の改修**を含む＝cross-repo。独断で committed submit を変えないため上程。

## 依頼（2点）
1. **ts 源 = (a) でよいか**（推奨）。(a) なら IMPL に小 handoff（submit に optional ts 追加）→ 再監査 → DE 記録ルーチンを `admit_via_submit` へ切替。
2. **slice1 proof（`de_submit_route.py` + `s_de_route_equiv.py`・挙動非変更の tooling）を先に commit=Taka してよいか**（同値の実証記録）。それとも ts 修正+switch と1コミット群にまとめるか。
- 保留: switch と proof commit は本裁定まで保留。同値実証・hermetic・sole-writer 不変は達成済み。**直叩きは未閉塞**（並行運用・enforcement なし）。★3 本線は止めない。

---
*DESIGN CC-α。ADJREQ。同値は実証、実測差異（submit 固定 ts）を独断で committed submit 改修せず上程。正面玄関から入る内部アクター。*
