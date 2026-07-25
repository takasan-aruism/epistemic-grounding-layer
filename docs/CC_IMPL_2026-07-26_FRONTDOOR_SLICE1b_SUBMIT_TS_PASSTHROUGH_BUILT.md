# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): submit に optional ts pass-through（front-door slice1b・BUILT）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-26 / repo=**twoder + egl** / 決定論
- 対応: `CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1b_SUBMIT_TS_PASSTHROUGH_HANDOFF.md`（ts=(a) 採用）
- **2DER コア front door(`twoder/submit.py`)への初の変更**（最小・後方互換・cross-repo）。

## 成果物（working tree・未commit・cross-repo）
- **twoder**: `twoder/submit.py`（optional `ts` 引数追加・`ts = ts or "2026-07-11T08:00:00"`）
- **egl**: `structure/de_submit_route.py`（ts 実注入 + `now_ts()` 実時刻生成）/ `structure/s_de_route_equiv.py`（実 ts 同値 + 後方互換 検証）

## 実装（handoff §1・最小・後方互換・ts は受領のみ）
- `twoder/submit.py`: signature に `ts=None` を追加。本体先頭を `ts = ts or "2026-07-11T08:00:00"` に（**submit は時刻を"生成"せず"受領"**・未指定=既定の決定論値＝**既存 caller 無影響**）。下流（DE-admission fast path の `admit_design_evidence(..., ts=ts)` / DS thread event）は同じ ts を使う（不変）。
- `de_submit_route.admit_via_submit(candidate, ts=None, ledger_path=None)`: **ts を submit へ実注入**。ts 未指定時は `now_ts()`（実 UTC・`2026-07-25T11:45:21Z` 形式）を生成して渡す＝**de_admission 直叩きと同じ実時刻源**（admitted_at の実時刻運用を維持）。
- diff は submit.py の optional 引数追加に限定（**4 insertions/2 deletions・scope creep なし**）。

## 検証（受入 §3・全 gate GREEN）
- `s_de_route_equiv.py --check` **GREEN**:
  - **実 ts 注入で ledger 行 byte 同値 4/4**（実時刻形式 ts=`2026-07-26T09:00:00Z` を submit・直叩き両方へ → ADMITTED/REJECTED-schema/REJECTED-ceiling/BEHAVIORAL-downgrade すべて route-equal=True）。
  - **後方互換**: ts 未指定 submit の `admitted_at=2026-07-11T08:00:00`（既定へ fallback・既存挙動不変）を実測 assert。
  - front-door provenance 生成（loop trace）・**sole-writer=egl.de_admission 不変**・hermetic（**実 DESIGN_EVIDENCE_LEDGER 不汚染**）。
- 追加確認: `admit_via_submit(ts=None)` が実時刻を生成して admit（ADMITTED）＝switch 時に実時刻運用を維持できることを実証。
- 全 gate GREEN（s_de_route_equiv / regen_meta / s_task_contract / s_llm_invocations）。

## 後方互換（handoff §3・重要）
- ts を渡さない**既存 submit caller（通常の問い合わせ経路）は完全に不変**（`ts = ts or 既定` ゆえ None→既定ハードコード値＝従来と同一の ts が全下流で使われる）。trace/挙動 byte 不変。
- 変更は「ts を渡せるようにした」だけ＝新経路（admit_via_submit）のみが実 ts を注入。

## ハンドオフ
- 次: 設計独立再監査（実 ts で submit==直叩き byte 同値・ts 未指定 fallback=既定・後方互換・sole-writer 不変・実 ledger 不汚染）。
- **commit=Taka（twoder + egl 両 repo・各 push）**＝[[2der_repo_topology]] の個別 commit/push 規律に注意（片方だけ push しない）。Taka awareness: 2DER コア front door への初の変更。
- その後 **slice1c=switch**: DE 記録ルーチンを `admit_via_submit`(実 ts) へ切替（別 DE）。**直叩き閉塞はさらに後**（MGR/Taka）。
- 想定（実 ts で byte 同値・後方互換）は実証。silently 合わせず記録。

---
*実装(IMPL)。2DERコア front doorへの最小・後方互換変更・ts は受領のみ(生成でない)・cross-repo commit=Taka。★3 本線・止めない。*
