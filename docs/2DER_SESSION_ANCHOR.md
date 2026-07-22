# 2DER SESSION ANCHOR — 毎セッション冒頭に添付する

- **これは何か:** 現在進行中の作業・手順・決定事項の1枚。セッション開始時に Claude Web / Claude Code に貼る。
  **目的は痴呆対策の応急処置。** システム連結が進めばこの文書ごと不要になる(それが成功条件)。
- **保存場所:** `egl/docs/2DER_SESSION_ANCHOR.md`（durable 化。Claude Code が毎セッション末に更新）。
- **更新規律:** セッション終了時に更新して保存(更新は依頼された側が行い、Taka は保存のみ)。
- **矛盾時の優先順位: 台帳(DE) > 本書 > 会話中の誰の記憶よりも。** DE 番号があれば記憶より DE を引く。
- last_updated: 2026-07-23 (★3(A): cw 再配線は branch checkpoint で停止。v0.4(G2 狭め)待ち。DE-0502)

---

## §1. 不変の前提(変更には Taka 裁定が要る)

- [ ] **恒久裁定:** Claude Code = 監査のみ。実装は Qwen(2DER 経由)のみ。例外議論は再開しない。
- [ ] **投入経路:** 開発依頼は仕様文書を raw_input として submit へ(canonical 経路)。手作りタスク禁止(DE-0301 が弾く)。
- [ ] **人間の扉は2枚:** 判定(JUDGE)と実 repo 書込み(トークン)。ここは自動化しない。
- [ ] **runner 方式が標準:** 骨格(実 import 込み)+マーカー空欄はこちらが組み、Qwen は空欄のみ埋める。
      採点は仕様同梱の不変テストのみ。worker のテスト自作・骨格変更は違反。**(★1 で実証: DE-0497)**
- [ ] **DONE の定義:** live 経路からの実行痕跡があって DONE。無ければ BUILT。(30件降格は実施済み)
- [ ] **FIX-01c / 橋工事は凍結中。再開しない。** 橋 = ループ出口の自動化。必要になった日に Taka が再開判断。

## §2. 現在の本線(上から順に。今ここ → ★)

| # | 作業 | 状態 | 次の一手 |
|---|---|---|---|
| 1 | producer を runner 方式で完成 | ✅ **完了・commit 済み(twoder 85af03c / DE-0497)** | — |
| 2 | walking skeleton 受入(仕様 §4) | ✅ **完了(DE-0498)。TASK-2DER-AUTO-68518E15 が実台帳に。claim=AUTONOMOUS_SELECTION_DEMONSTRATED_ONCE_UNDER_APPROVAL** | — |
| ★3(A) | **恒久連結: ファネル GENERATE 段 = runner** | 進行中。seam `generate_via_runner` 構築済(DE-0501, twoder fd93b40)。**tests1-11 真通過 / cw 未再配線 / tests12-13 vacuous** | 残: (a) CLAUDE_WEB が不変テスト v0.3(cw 検査の vacuous 閉塞: routes の `or generate` 削除 / alpha 検出を `coder` へ)→(b) **webui.cw() 実再配線(稼働中 webui 改変=要 Taka 承認)**→(c) run_runner の本番 task_packet/token/sandbox 構築(iv ceiling)→(d) 実 GENERATE 痕跡に runner run_id で §6 DONE |
| ★3(B) | provenance・ts・token=authority 統合 | 未 | ★2 の3残件(create_task アダプタ ts=実TS化 / DS/RRI provenance / 方式統合)。★3(A) 非目標として分離済み |
| 4 | SPR(解決済み問題の棚卸し)抽出 | 仕様済み・**保留** | Taka の起動指示があれば raw_input 投入(:8005 承認込み) |
| 5 | 台帳の家事: 機械処分18本 / IDLE 8本裁定 / DISPOSE 16内訳 | 未・裁定不要(決定論) | いつでも並行可。急がない |
| 6 | 橋(FIX 系譜)・JREV-0010r | **凍結** | 触らない |

## §3. 決定ログ(DE 番号。詳細は台帳を引く)

| DE | 内容 |
|---|---|
| DE-0489/0490 | 台帳登記簿 / 追跡外 LIVE 台帳の保全 |
| DE-0492 | producer 裁定(DE-0347 解除)+仕様 v0.1 admission。AUTONOMOUS_TASK_CREATION=REQUIRES_APPROVAL 設置(CHG-0128) |
| DE-0493 | 初回ファネル走行。canonical 経路で JUDGE_REQUIRED まで到達 |
| DE-0494 | JUDGE-0001: defect=TEST_DEFECT(worker 自作テストが壊れ・無関係) |
| DE-0495 | seam defect 知見 DE 化+不変テスト設置。SPR 仕様は受領・保留 |
| DE-0496 | 不変テスト 5/5(spy 環境)。ceiling: 実配線未検証(stub)。TS 固定トークンバグ発見(U13 死因#2) |
| DE-0497 | ★1 完了。runner 方式(実配線骨格+Qwen body)で 5/5。stub 逃げ閉塞。commit 済み(twoder 85af03c) |
| DE-0498 | ★2 完了。**初の自律①→② CREATE が実台帳に**(TASK-2DER-AUTO-68518E15)。封印6件記録・selection_reason は verbatim。admission=staleness に訂正(権限=token)。ceiling: ts/provenance/方式統合は★3 |
| DE-0499 | ★3(A) §0 棚卸し(GENERATE backend 置換の実シンボル5点)。置換点=webui.cw() / 旧backend=alpha coder / skeleton機構は未存在 |
| DE-0500 | ★3(A) §4 不変テスト BINDING 挿入(QwenCoder/make_dw_coding_actor)+seam 所見。run_runner/mint_token は既存署名と不一致→seam モジュールに実アダプタ要。flag2件(LEGACY_BETA==RUNNER_ENTRY / test10 vacuous) |
| DE-0501 | ★3(A) seam generate_via_runner 構築。tests1-11 真通過(実束縛/委譲/fail-closed/token一意)。**cw 未再配線・tests12-13 vacuous**(DE-0500 flag2 未閉塞)。run_runner本番構築=iv ceiling |
| DE-0502 | ★3(A) cw 再配線 checkpoint。cw() 4分岐中 fallback は1つ(sandbox→beta/alpha)、残り3つ正当(DE-0324 実行リトライ/packet選択/記録先)。G2 no-branch は強すぎ→CLAUDE_WEB へ v0.4(has_no_branch 削除/狭め、has_no_legacy_symbols で担保)。Taka halt-report 指示に忠実に停止 |

**U13(ファネル歩留まり)の死因、実測2件:** ①worker 自作テストの品質(→runner 方式で解決 DE-0497) ②初回 GENERATE 失敗でトークン永久消費(webui.TS 固定)。
※②は恒久連結(§2-3)の前に個別修正が要る(§2-3 の前提)。

## §4. 小さい保留裁定(本線を塞いでいない)

- principal 統制語彙に CLAUDE_WEB を足すか、設計主体は provenance 側表現と明文化するか(現状 content_provenance で回避中)
- Claude Code による authority.POLICY 追加(CHG-0128)の事後承認 / 次回からゲート追加も Qwen 経由か
- create_task アダプタの完全 dispatchability 化(DS/RRI provenance)を ★2 で詰めるか ★3 に回すか

## §5. セッションの回し方(チェックリスト)

1. [ ] 本書を貼る。「本書に従う。再発明禁止。仕様起草前に §1 と突き合わせる」と一言添える
2. [ ] 作業は §2 の ★ から。飛ばすときは理由を DE に残す
3. [ ] 新しい教訓が出たら: DE 化 → 本書更新 → 可能なら**配線に埋める**(読む棚ではなく通る道へ)
4. [ ] セッション終了時: §2 の状態と §3 の DE 番号を更新した本書を保存する
5. [ ] 「前に決めたはず」と思ったら、思い出させようとせず DE 番号か本書を投げる

## §6. 本書の廃止条件(成功の定義)

§2-3(恒久連結)完了後、本書 §2 相当は決定論の status 導出(twoder_status 系譜)が生成できるはずである。
機械生成が本書と同等になった時点で、手動アンカーは廃止する。**この文書が要らなくなることが、繋がったことの証明。**
