# 設計/監査 → 実装: RTHREAD stage 2a handoff(accounts 機械核)

- 発: 設計/監査(CC-α)/ 2026-07-24 / 正本: `SPEC_RTHREAD_STAGE2a_v0.1.md`
- **別 repo=rri**。前提: stage1 v0.2 配備済(commit `a4e97d6`・11/11 green)。
- 設計は **プロトタイプで D1/D2/D3 の挙動を実証済み**(off-chart 拒否 / suspense 決着 / 改竄 off-chart halt)。

## 依頼(SPEC §1〜§3 のとおり)
1. `request_thread.py` の **FILL 変更4点 + 新例外 `RThreadChartUnavailable` + chart ローダ `_load_chart`** を実装(SPEC §1)。**非FILL区間・他関数は byte 不変**。
2. **stage-1/cov テスト移行**(SPEC §2)を配置(`_fresh` に `RTHREAD_CHART` 追加 / RESOLVED 経路の account を `ACCT_TEST_A` へ)。**契約の述語は変えない**(account 値と chart 設定のみ)。
3. `test_request_thread_stage2a.py`(SPEC §3 verbatim・7本)を新規配置。
4. `python -m pytest rri/test_request_thread_stage1.py rri/test_request_thread_stage1_cov.py rri/test_request_thread_stage2a.py -q` = **全 green**。
5. **mutation check(G-T1)**: SPEC §4 の2 mutation(suspense を raise 数に戻す / off-chart 検査を外す)で該当テストが赤に転じることを実証(テスト内 or 別途手順)。
6. `CC_IMPL_2026-07-24_RTHREAD_STAGE2a_BUILT.md` を置く。

## 拘束
- **imagined な production account を導入しない**。2a で使う名は UNCLASSIFIED と **純テスト fixture `ACCT_TEST_A/B`** のみ。実 chart は stage2b。
- 語彙(G-6)/ 封印(G-1: suspense と account 保存は machine 検査・self-report を信じない)/ chart は DERIVED(G-5)。
- スコープ厳守: MINING(実chart)/ split・merge / 昇格・統計 は **2a に含めない**。green にするために本体が SPEC 外へ広がるなら **halt**(乖離台帳スキーマで報告)。

## 監査ハーネスについて(設計側担当・実装は不要)
`audit_rthread_stage1.py` は `raise_question` 署名を stage1 版で照合しているため 2a 本体変更後は A が赤になる。**これは想定内**——**ハーネスの stage2a 対応更新は設計側(CC-α)が再監査時に行う**。実装は §4 acceptance(全テスト green + 非FILL byte 不変 + mutation check)だけ満たせばよい。

## 完了後
- 設計側が再監査(全 green + 非FILL byte 不変 + ハーネス stage2a 対応で A/B/C 再確認)→ CONSISTENT → commit=Taka → DE 起票(live submit)。
