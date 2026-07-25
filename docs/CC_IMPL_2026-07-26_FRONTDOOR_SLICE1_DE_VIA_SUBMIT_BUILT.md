# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): front-door slice1 — DE 記録を submit 経由へ（同値実証・BUILT）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-26 / repo=egl(+twoder/rri/ds 参照) / 決定論
- 対応: `CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1_DE_VIA_SUBMIT_HANDOFF.md`
- 位置づけ: front-door 移行(A) 第一スライス。**証明→切替→(後スライスで)閉塞**。**直叩き未閉塞**（enforcement なし・並行運用）。

## 成果物（working tree・未commit）
- `structure/de_submit_route.py`（front door 薄ラッパ `admit_via_submit(candidate, ts=None, ledger_path=None)`）
- `structure/s_de_route_equiv.py`（同値検証ハーネス `--check`・hermetic）
- meta fold（regen_meta）: TASK_CONTRACTS / READ_PATHS

## 実証（受入 §5・全 gate GREEN）
`s_de_route_equiv.py --check` **GREEN**。代表4 candidate（ADMITTED / REJECTED-schema / REJECTED-ceiling / BEHAVIORAL-downgrade）で:
- **ledger 行 byte 同値**（直叩き `admit_design_evidence` vs submit 経由）＝**4/4 route-equal=True**（admit2 は同一行・reject2 は両者とも無追記＝一致）。
- **front-door provenance 生成**（＝移行の価値）: submit 経路が `DS_INPUT → RRI_CLASSIFY → EGL_ADMISSION → [EGL_LEDGER_APPEND] → RRI_RESIDUAL → DS_THREAD_UPDATE` の loop trace を生む。ledger 行はそれに影響されない（**ledger-row-neutral**）。
- **sole-writer 不変**: 追記は egl.de_admission のみ（submit はそれを呼ぶだけ・手動 append なし・二重 writer なし）。
- **hermetic**: 直叩き用/submit用で別 temp ledger（dup rejection 回避）+ DS/RRI/EGL data dir を temp 隔離。**実 DESIGN_EVIDENCE_LEDGER を一切汚さない**（sha 前後不変を assert・GREEN）。
- measure-first: 差は `ROUTE_DIVERGENCE`/`RESULT_DIVERGENCE` で具体 diff を surface（握り潰さない）。

## ★ 正直な flag（switch の前提・デリケート・ハンドリング）: submit の固定 ts vs 実 DE の実時刻
- 同値は「**同一 ts を与えれば**両経路が byte 同一行を生む」という **ledger-row-neutral** の証明です（front door は行を変えない）。ハーネスは submit の ts を抽出し直叩きに合わせて比較。
- **実務上の差異（surface・握り潰さない）**: `twoder.submit.submit` は **ts をハードコード**（`submit.py:88` `ts="2026-07-11T08:00:00"`・"deterministic, no Date.now" 設計）で **ts 引数を取らない**。一方、**実 DE 行は実時刻**を記録している（実測 DE-0535=`2026-07-25T11:45:21Z` / DE-0536=`…13:00:36Z` / DE-0537=`…14:48:40Z`）。
- ∴ **今そのまま submit 経由に切替えると、DE の `admitted_at` が実時刻→固定 `2026-07-11T08:00:00` に後退する**。これは行 byte を変える実差異ゆえ、切替前に ts 源の裁定が要る。
- **裁定候補（DESIGN/MGR・独断で committed submit を変えない）**:
  - (a) `submit()` に optional `ts` 引数を足し de_admission へ pass-through（小改修・実時刻を保てる。submit の replay 決定論は ts 未指定時の既定値で維持）。→ これなら実時刻のまま front door 化。
  - (b) DE の admitted_at を固定 ts で受容（replay 決定論を優先／実時刻を捨てる）。現行 ledger の実時刻運用と不整合ゆえ非推奨。
- ※ `admit_via_submit` の `ts` 引数は現状 API 対称性のため受けるだけ（submit が注入を受けないため）。(a) 採用時に実注入へ配線します。

## 不変テスト / 規律
- 決定論・冪等（同 candidate+ts→同行）。sole-writer=egl.de_admission 不変。**この段では直叩きを塞がない**（並行運用）。★3 は front door 移行自体。

## ハンドオフ
- 次: 設計独立再監査（fresh `s_de_route_equiv.py --check` で byte 同値・front-door provenance・実 ledger 不汚染）。
- **switch 可否 = ts 源の裁定 (a)/(b)**（実時刻を保つなら submit に ts 引数追加の別スライス小 handoff → 私が実装）。同値が実証されたので、ts 裁定後に DE 記録ルーチンを `admit_via_submit` へ切替。直叩き閉塞はさらに後（MGR/Taka）。
- commit=Taka。想定（byte 同値）は実証、実測差異（submit 固定 ts）を silently 合わせず記録。

---
*実装(IMPL)。同値を先に証明・直叩きは塞がない・sole-writer 不変・正面玄関から入る内部アクター。★3 本線＝これ自体。*
