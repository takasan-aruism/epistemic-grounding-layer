# 設計/監査 → 実装: front-door slice1 — DE 記録を submit 経由へ（同値検証ハーネス）HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / repo=egl(+twoder/rri 参照) / 決定論
- 正本: `CC_MGR_2026-07-26_FRONT_DOOR_MIGRATION_A_ANALYSIS_AND_SLICE1_HANDOFF.md` + 本 handoff
- 位置づけ: front-door 移行(A) 第一スライス。**証明→切替→（後の別スライスで）閉塞**の順。**この段では直叩きパスを塞がない**（enforcement なし）。
- [[ai-must-be-internal-actor-not-intruder]]（正面玄関から入る内部アクター）。

## 0. 事実（独立確認済）
- `twoder/submit.py:107-147` の DE-admission fast path は、admission と判定された時 **`egl.de_admission.admit_design_evidence(admission_payload, ts=ts, ledger_path=ledger_path)`（＝直叩きと同一関数）**を呼び、周囲に RRI 分類 / residual_update / DS thread event / trace を付す。**ledger を追記するのは egl.de_admission のみ**（submit は手動 append しない）。
- `submit(raw_input, conversation_id="taka-main", seed=0, admission_payload=None, ledger_path=None, ...)`。
- `rri.admission_request.detect(raw_input)`: 決定論キーワード（"egl admission" / "admission request" / "register de" / "de を登録" / **"開発エビデンスを登録"** / "開発根拠を登録" 等）で `is_admission_request`。
- `admission_payload is None`（NL のみ）→ boundary fail（submit.py:117-120）。**構造化 DE candidate（payload）必須**。

## 1. payload schema（＝現行 DE candidate・新設不要）
- `admission_payload` = 我々が今 `admit_design_evidence` に渡している **DE candidate dict そのまま**（`observation`/`decision`/`decision_owner`/`claimed_status`/`evidence_refs`/`design_evidence_id`…）。新スキーマ不要。
- `raw_input` = admission キーワードを含む文字列（例: `"開発エビデンスを登録: {design_evidence_id} — {observation 冒頭120字}"`）。決定論生成。目的は AR.detect を is_admission=True にすることのみ（payload が正典）。

## 2. helper（DESIGN/我々が submit 経由で admit するための薄い入口）
- `structure/de_submit_route.py`（or egl 側の薄いラッパ）: `admit_via_submit(candidate, ts, ledger_path=None)` = raw_input を candidate から決定論生成 → `twoder.submit.submit(raw_input, admission_payload=candidate, ledger_path=ledger_path)` → TRACE から `EGL_ADMISSION_RESULT` を取り出して返す。
- **egl.de_admission は依然 sole ledger writer**（submit はそれを呼ぶだけ）。手動 append 経路は使わない。

## 3. 同値検証ハーネス（最重要・byte 同値を先に証明）
- `structure/s_de_route_equiv.py --check`:
  - **同一 candidate + 同一 ts** を、**別々の temp ledger** に対して2経路で admit:
    - (a) 直叩き `admit_design_evidence(cand, ts, ledger_path=tmpA)`
    - (b) submit 経由 `admit_via_submit(cand, ts, ledger_path=tmpB)`
  - **tmpA と tmpB に追記された ledger 行を byte 比較 → 完全一致を assert**（差が出たら `ROUTE_DIVERGENCE` で具体 diff を surface・握り潰さない）。
  - temp ledger 使用は **実 ledger を汚さない + dup rejection（同一 design_evidence_id 二重）を避ける**ため必須。
  - 複数の代表 candidate（ADMITTED / REJECTED / downgrade 例）で同値を確認。
- **scope 明記**: 同値は **ledger 行**について。submit は追加で RRI residual / DS thread event / trace を生む（＝front-door provenance＝移行の価値）。これは ledger 行を変えないことを確認（ledger-row-neutral）。

## 4. 不変テスト / 規律
- **sole-writer 不変**: ledger 追記は egl.de_admission のみ（submit 経由でも同じ・二重 writer 無し）。
- 決定論・冪等（同 candidate+ts→同 ledger 行）。measure-first（diff は surface）。
- **この段では直叩きを塞がない**（enforcement 無し・並行運用）。★3 本線（帳簿）は止めない。commit=Taka。

## 5. 受入（設計が独立再検証）
- 私が fresh に `s_de_route_equiv.py --check` → **2経路の ledger 行 byte 一致**（複数 candidate で）。
- submit 経由が RRI 分類→admission→residual→DS thread の loop trace を生み、かつ ledger 行は直叩きと同値。
- egl.de_admission 以外が ledger を書かない。--check GREEN。

## 6. 完了後 / 切替
- `CC_IMPL_2026-07-26_FRONTDOOR_SLICE1_DE_VIA_SUBMIT_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → 結果を MGR へ。
- 同値が実証されたら、**DE 記録ルーチンを submit 経由へ切替**（我々が今後 `admit_via_submit` を使う）。**直叩きパスの閉塞は後の別スライス**（MGR/Taka 判断）。
- 想定と実測がズレたら silently 合わせず記録。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。同値を先に証明・直叩きは塞がない・sole-writer 不変・正面玄関から入る。★3 本線・止めない。*
