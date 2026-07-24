# 実装担当 → 設計/監査担当: RTHREAD stage 1 v0.1a 修正完了（F-1 load-bearing 化・BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `CC_DESIGN_2026-07-24_RTHREAD_STAGE1_v0.1a_FIX_HANDOFF.md`（F-1 修正指示）

## 修正内容（handoff どおり・変更範囲を厳守）

- `project()` **FILL 本体のみ**変更: `in_flight_count` を残差(plug)でなく**独立導出**へ（`disposed_qids` に含まれない QUESTION_RAISED の数）。他フィールド・他10関数・定数・例外・`_mint`・署名は byte 不変。
- `test_request_thread_stage1.py` に **T14c**（handoff 提供・verbatim）を追加＝実経路の二重処分を sole writer 経由で注入し `check_conservation` が HALT することを検査。

## 検証（決定論・隔離下）

- **5/5 green**（T14 I1 / T14 I2 / T18a / T18b / **T14c**）
- 骨格保存 `verify_skeleton_preserved` = True（固定11区間）
- **CC-α 監査ハーネス VERDICT: CONSISTENT**（A 骨格保存 PASS / B 5テスト PASS / **C 保存則 load-bearing PASS**＝二重処分 projection `in_flight_count=0` で I1 `1 != 1+1` → HALT）
- I1 が実イベント経路で load-bearing（二重処分・幻処分を検出）。前版の tautology（F-1）解消。

## flag（設計側 SPEC の accuracy）

- `SPEC_RTHREAD_STAGE1_v0.1.md` の project docstring 該当行（line 140付近）は **旧文言「in_flight_count=raised-(4種)」のまま**。実装本体は独立導出へ変わったので、docstring は body と食い違う。
- 私は**固定区間（docstring）を byte 一致で保ったまま**にした（skeleton 契約維持・監査 check A は docstring 非対象で CONSISTENT）。**SPEC §2 の docstring 更新は設計側（CC-α）でお願いします**（handoff §1 の確定文言）。次に SPEC が respin されたら私はそれに合わせて rebuild します。

## ハンドオフ

- 次: **CC 再監査 → CONSISTENT 確定 → commit=Taka**（`?? rri/rri/request_thread.py` `?? rri/rri/test_request_thread_stage1.py`）。
- DE 起票（live submit 経由）は設計側担当（手で ledger に書かない）。
