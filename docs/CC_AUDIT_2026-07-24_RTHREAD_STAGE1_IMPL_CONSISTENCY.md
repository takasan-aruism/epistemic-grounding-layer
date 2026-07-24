# CC 設計/監査 → 実装: RRI RTHREAD stage 1 v0.1 整合監査結果

- 発: 設計/監査インスタンス（CC-α）/ 2026-07-24
- 対象: `rri/rri/request_thread.py`（実装 Monitor `b0718vzrg` 作）
- 正本: `SPEC_RTHREAD_STAGE1_v0.1.md` + `RRI_IMPL_SPEC_v0.1.md`
- 監査ハーネス（決定論・セルフテスト付き）: `egl/docs/audit_rthread_stage1.py`

## VERDICT: **NOT CONSISTENT** — finding F-1（HIGH）。commit 保留を推奨。

self-report を信じず独立に機械再検証した。合格点と欠陥を分けて報告する。

## 合格（実装は骨格契約に忠実）
- **A. 骨格保存 = PASS**。定数(EVENT_TYPES/STATES/DISPOSALS/UNCLASSIFIED_FORBIDDEN)・TRANSITIONS の RESOLVED/DISPATCHABLE 行・例外4種・`_mint` 本体・**11 署名すべて §2 と byte 一致**。FILL 以外は無改変。
- **B. 4/4 green を再実行で確認**（隔離下）。
- **T18a / T18b は真に load-bearing**。`advance_state`(in_flight!=0 で RESOLVED reject)・`dispose_question`(UNCLASSIFIED→RESOLVED 禁止) を**実経路で**通しており、空振りでない。
- `advance_state` の RESOLVED guard が projection 由来（in_flight==0 / 全 OPEN_GAP presented / THREAD_ACCEPTED）で、self-report キーだけでは通さない設計になっている点も確認。

## F-1（HIGH）: 保存則 I1 が実経路で tautology、二重処分/幻処分を検出しない
**現象（実測、ハーネス C）:** `project()` が `in_flight_count = raised − Σ(4処分)` と**残差(plug)**で定義しているため、I1 `raised == resolved+open_gap+rejected+merged+in_flight` は project() の任意出力に対し**代数的に常に成立**する。結果:
- 同一問いを2度処分 → `raised=1, resolved=1, open_gap=1, in_flight=−1` → I1: `1 == 1+1−1` で **halt しない**
- 未 raise の問いを処分（幻処分）→ in_flight=0 に吸収され **halt しない**

**含意:** T14（I1/I2）の mutation テストは **dict を手で壊して** halt を確認しているだけで、**実イベント経路で生じる本物の bookkeeping バグを検出できない**。stage 1 の中核成果物（保存則）が load-bearing でない = green が偽の安心を与える（[[codegen-loop-audit-efficacy-experiment]] の「監査が空振りで net 負」と同型）。

**帰責:** 起源は §2 骨格の `project` docstring（`in_flight=raised-(4種)`）= **設計(CC-α)側の欠陥**。実装は骨格に忠実であり、実装の過失ではない。よって修正も設計側の責（author≠auditor：実装にオラクルを書き換えさせない）。

**セルフテスト（族A回避）:** 独立導出版 in_flight（未処分の raised 問い数）を参照実装として先に走らせ、それが二重処分で確かに不成立を検出することを示した（ハーネス `selftest_C`=OK）。つまり検出器は空振りしない。

## 次アクション（file signal 済）
- 修正 spec + load-bearing テストを **`CC_DESIGN_2026-07-24_RTHREAD_STAGE1_v0.1a_FIX_HANDOFF.md`** に起票。実装インスタンスは `project()` の FILL を独立導出へ再実装し、追加テスト T14c（実経路の二重処分→HALT）を green にする。
- **I2（科目次元）も同様に partition 恒等式**だが、stage 1 では account 誤配属を生む経路が無い（1問い1 account を raise 時に確定）ため実害は現状ゼロ。v0.2 で account 移動を入れる時に load-bearing 化する（本監査では I1 のみブロッカー）。
- commit=Taka gate。**F-1 未修理のまま「stage 1 完了」で commit すると恒等式の保存則を成果物と称することになる**ため、修理→再監査 CONSISTENT→commit を推奨。
