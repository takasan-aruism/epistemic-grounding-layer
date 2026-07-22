# 2DER SESSION ANCHOR — 毎セッション冒頭に添付する

- **これは何か:** 現在進行中の作業・手順・決定事項の1枚。セッション開始時に Claude Web / Claude Code に貼る。
  **目的は痴呆対策の応急処置。** システム連結が進めばこの文書ごと不要になる(それが成功条件)。
- **保存場所:** `egl/docs/2DER_SESSION_ANCHOR.md`（durable 化。Claude Code が毎セッション末に更新）。
- **更新規律:** セッション終了時に更新して保存(更新は依頼された側が行い、Taka は保存のみ)。
- **矛盾時の優先順位: 台帳(DE) > 本書 > 会話中の誰の記憶よりも。** DE 番号があれば記憶より DE を引く。
- last_updated: 2026-07-23 (provenance 受け渡し完了 DE-0515: CLAUDE_WEB が v0.2 で確定[J1 kp 内ネスト / J2 fail-closed 撤回=seam は導管]→ seam を導管化。新 immutable 5/5・封印58・regression 全緑。死因#3 機械閉塞。残=実 PROBE 再走で DONE)

---

## §1. 不変の前提(変更には Taka 裁定が要る)

- [ ] **恒久裁定:** Claude Code = 監査のみ。実装は Qwen(2DER 経由)のみ。例外議論は再開しない。
- [ ] **投入経路:** 開発依頼は仕様文書を raw_input として submit へ(canonical 経路)。手作りタスク禁止(DE-0301 が弾く)。
- [ ] **人間の扉は2枚:** 判定(JUDGE)と実 repo 書込み(トークン)。ここは自動化しない。
- [ ] **runner 方式が標準:** 骨格(実 import 込み)+マーカーはこちらが組む。**worker は全文生成する
      (マーカー穴埋め worker は存在しない=DE-0511 実測。★1/FIX-01c も全文生成だった)**。生成後、骨格の固定区間
      (import 等の接続)が bytes 一致で保存されているかを**決定論検査**する(verify_skeleton_preserved, DE-0512)。
      採点は仕様同梱の不変テストのみ。worker のテスト自作は違反。**(★1 DE-0497 / 実態訂正 DE-0511・0512)**
- [ ] **DONE の定義:** live 経路からの実行痕跡があって DONE。無ければ BUILT。(30件降格は実施済み)
- [ ] **FIX-01c / 橋工事は凍結中。再開しない。** 橋 = ループ出口の自動化。必要になった日に Taka が再開判断。

## §2. 現在の本線(上から順に。今ここ → ★)

| # | 作業 | 状態 | 次の一手 |
|---|---|---|---|
| 1 | producer を runner 方式で完成 | ✅ **完了・commit 済み(twoder 85af03c / DE-0497)** | — |
| 2 | walking skeleton 受入(仕様 §4) | ✅ **完了(DE-0498)。TASK-2DER-AUTO-68518E15 が実台帳に。claim=AUTONOMOUS_SELECTION_DEMONSTRATED_ONCE_UNDER_APPROVAL** | — |
| ★3(A) | **恒久連結: GENERATE 段 = runner** | cw 再配線 LIVE。機構完備(passthrough A+B+iv+**provenance**)。**§6 DONE 構造達成**(DE-0513)。**provenance 受け渡し完了(DE-0515)**: seam=導管。CREATE.knowledge_packet.provenance を run_runner→run_minimal_slice(provenance=) へ verbatim。runner の門判定(REJECTED_BYPASS 等)を素通し。新 immutable 5/5・封印58・regression 全緑 | **残=実 PROBE 再走**(死因#3 は機械閉塞済。live 経路で REJECTED_BYPASS が解け runner が実 PASS/次の死因に到達するかを確認 → 到達で DONE、現状 BUILT) |
| ★3(B) | provenance・ts・token=authority 統合 | **ts 完了(DE-0505)**。**provenance 受け渡し完了(DE-0515)**。残: token=authority 方式統合 | 3重複 _now 統合は家事。provenance は A/B と同型欠陥(段間で作り直す)を導管化で解消=SPR 行候補(3例目) |
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
| DE-0503 | ★3(A) cw 再配線 **LIVE**。GENERATE backend=generate\_via\_runner seam(無条件・fallback 無)。webui 再起動。immutable 14/14・保持挙動無傷。契約無しtaskは fail-closed(§5)。test\_live\_coder\_backend は §2 禁止挙動を検証→反転済(DE-0506) |
| DE-0504 | iv 前段 read-only(削除可・DE-0511 に統合) |
| DE-0505 | ★3(B) ts 実ISO化。CREATE ts=fingerprint→実ISO8601(clock=failure\_memory.\_now, 最軽量選択)。recompute basis\_fingerprint 自キー化+body で emitted\_ts 封印。**既存5本緑+ts8本=13/13** |
| DE-0506 | 契約passthrough 棚卸し3点(断点=PLAN が契約キー継承せず)。test\_live\_coder\_backend **反転** 8/8(live backend=seam 検証)。submit.py:88 裏付けDE無し |
| DE-0507 | 契約passthrough(a) 棚卸し: CREATE kp に契約キー無=断点上流 / seam は task\_id 未受領 |
| DE-0508 | 契約passthrough A 棚卸し: kp=決定論dict(claims の一部のみ:8005)→契約キーは LLM非経由で封印可 / cw が task\_id 受領 |
| DE-0509 | 契約passthrough **A 完了**。contract\_seal(決定論マーカー抽出/壊れは ValueError/LLM非経由)→ submit 1行 → create\_task(contract=) → CREATE payload[contract]。8/8 |
| DE-0510 | 契約passthrough **B 完了**。seam が CREATE payload[contract] を dw.workcell.\_read\_events で読み sha 検証/contract\_source 記録/fail-closed。cw が task\_id 注入。44 green |
| DE-0511 | iv 棚卸し4点(run\_minimal\_slice 署名/戻り・実呼出=make\_dw\_coding\_actor パターン・sandbox・oracle)。gap: worker は skeleton-fill せず全生成 |
| DE-0512 | **iv 完成**。run\_runner が task\_packet+sandbox+token+QwenWorker で run\_minimal\_slice 呼出。verify\_skeleton\_preserved(全文生成のまま骨格固定区間の順序bytes一致検査→SKELETON\_VIOLATION)。53本green |
| DE-0513 | PROBE-PIPE-01 live。**§6 DONE 構造達成**(実 GENERATE に runner run\_id=SLICE-TASK-2DER-6E2C9F16)。claim=CONTRACT\_TASK\_TRAVERSED\_FUNNEL\_ONCE。死因=run\_runner が provenance 未渡し→run\_minimal\_slice REJECTED\_BYPASS(DE-0301) |
| DE-0514 | provenance 受け渡しテストで **halt**(回避せず)。矛盾2件: (1)実 provenance は payload.knowledge\_packet.provenance(ネスト)で test の flat payload[key] と不一致 (2)fail-closed 要求が B の test\_contract\_is\_read\_from\_ledger(provenance 無で ok=True)と矛盾→B8 緑維持不能。reconcile 待ち |
| DE-0515 | **provenance 受け渡し完了(死因#3閉塞)**。CLAUDE_WEB が v0.2 で確定(J1: 実在位置=payload.knowledge\_packet.provenance / **J2: fail-closed 要求撤回**=DE-0301 の複製を避け seam は導管に徹する)。改修3点: (1)generate が契約と**同一 CREATE 読取**から provenance 抽出(段間で作り直さない) (2)run_runner が run_minimal_slice(provenance=) へ **verbatim** 受け渡し(未渡し=DE-0513 死因#3 の実体) (3)runner の門判定(status/reason/classification)を作り替えず素通し。欠落時 seam は裁かず捏造もしない(門は runner)。新 immutable 5/5・封印58(旧53+新5)・regression(live_coder_backend 8/8・dispatch_provenance 11/11・live_worker_runtime 15/15)全緑。B8 との矛盾は J2 で**消滅**。残=実 PROBE 再走で DONE |

**U13(ファネル歩留まり)の死因、実測2件:** ①worker 自作テストの品質(→runner 方式で解決 DE-0497) ②初回 GENERATE 失敗でトークン永久消費(webui.TS 固定)。
※②は恒久連結(§2-3)の前に個別修正が要る(§2-3 の前提)。

## §4. 小さい保留裁定(本線を塞いでいない)

- principal 統制語彙に CLAUDE_WEB を足すか、設計主体は provenance 側表現と明文化するか(現状 content_provenance で回避中)
- Claude Code による authority.POLICY 追加(CHG-0128)の事後承認 / 次回からゲート追加も Qwen 経由か
- create_task アダプタの完全 dispatchability 化(DS/RRI provenance)を ★2 で詰めるか ★3 に回すか
- **submit.py:88 の決定論 ts 規約(`ts="2026-07-11T08:00:00" # no Date.now`)に裏付け DE は無い**(DE-0505/0506/0507 で計3回確認)。規約を DE 化して棚に載せるか、コード規約のまま放置するか。→ **もう調べ直さない(この行を典拠とする)**

## §5. セッションの回し方(チェックリスト)

1. [ ] 本書を貼る。「本書に従う。再発明禁止。仕様起草前に §1 と突き合わせる」と一言添える
2. [ ] 作業は §2 の ★ から。飛ばすときは理由を DE に残す
3. [ ] 新しい教訓が出たら: DE 化 → 本書更新 → 可能なら**配線に埋める**(読む棚ではなく通る道へ)
4. [ ] セッション終了時: §2 の状態と §3 の DE 番号を更新した本書を保存する
5. [ ] 「前に決めたはず」と思ったら、思い出させようとせず DE 番号か本書を投げる

## §6. 本書の廃止条件(成功の定義)

§2-3(恒久連結)完了後、本書 §2 相当は決定論の status 導出(twoder_status 系譜)が生成できるはずである。
機械生成が本書と同等になった時点で、手動アンカーは廃止する。**この文書が要らなくなることが、繋がったことの証明。**
