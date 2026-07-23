# 2DER SESSION ANCHOR — 毎セッション冒頭に添付する

- **これは何か:** 現在進行中の作業・手順・決定事項の1枚。セッション開始時に Claude Web / Claude Code に貼る。
  **目的は痴呆対策の応急処置。** システム連結が進めばこの文書ごと不要になる(それが成功条件)。
- **保存場所:** `egl/docs/2DER_SESSION_ANCHOR.md`（durable 化。Claude Code が毎セッション末に更新）。
- **更新規律:** セッション終了時に更新して保存(更新は依頼された側が行い、Taka は保存のみ)。
- **矛盾時の優先順位: 台帳(DE) > 本書 > 会話中の誰の記憶よりも。** DE 番号があれば記憶より DE を引く。
- last_updated: 2026-07-23 (**PROBE-PIPE-02 走行済 TASK-2DER-8ADC31CF**: D0 PASS・**S1 provenance 有**・**S2 CONSUMED=0=分岐B**。死因が前進= PROBE-01 の step0 provenance gate は**通過**し、今回は **step1 token gate**('no scoped approval token / bare boolean not accepted')で落下→**DE-0515 の provenance 導管化は目的達成**、reason 具体=**族⑤解消確認**。**新死因#4 候補=token 受け渡し**(seam が approval_id 文字列を渡し runner step1 が別形を期待の疑い/未裏取り)。判定表 B1/B2/B3 不適合→CLAUDE_WEB 改訂事項。webui=DE-0515 コード稼働(PID 215805)。詳細は §2 ★3(A))

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
| ★3(A) | **恒久連結: GENERATE 段 = runner** | 機構完備(passthrough A+B+iv+**provenance** DE-0515)。**§6 DONE 構造達成**(DE-0513)。seam=導管: CREATE.knowledge_packet.provenance を run_runner→run_minimal_slice(provenance=) へ verbatim・門判定素通し。新 immutable 5/5・封印58緑。**P1 済(webui PID 215805 lstart 08:07:33=新コード稼働) / P4 済(封印58緑基準線)** | **残=PROBE-PIPE-02 実走→観測で DONE 判定**。方向確定=(ii) 新 probe(新 task_id)で clean 実行(旧 01=TASK-2DER-6E2C9F16 は JUDGE_REQUIRED で塞がり再利用不可)。**現状 未走行**(DW 最終 ord=702 不変)。**PROBE-PIPE-02 走行済(2026-07-23, TASK-2DER-8ADC31CF)**: D0 PASS(族④無)。**S1 provenance 有**(UTT-0700/RREQ-00212/dw_task_id 一致)。**S2 CONSUMED=0**(attempt-1/2/3 grant のみ)=判定表 **分岐B**。**但し死因が前進**: PROBE-01=step0 provenance gate(REJECTED_BYPASS)で落下→PROBE-02=**step1 token gate**(reason='no scoped approval token (bare boolean not accepted)')で落下。step1 到達=**provenance gate(DE-0301)通過=DE-0515 目的達成**。reason 具体的=**族⑤(RUNNER_FAILED のっぺり)解消確認**。**新=死因#4 候補(token 受け渡し)**: seam mint_token が approval_id 文字列を渡し runner step1 が別形を期待の疑い(未裏取り・観測外)。判定表 B1/B2/B3 に不適合→CLAUDE_WEB 改訂事項。task は再び JUDGE_REQUIRED/BLOCKED |
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
- **【SPR 行候補】段間診断情報の握り潰し族(inter-stage diagnostic swallowing)**(CLAUDE_WEB 記録票 2026-07-23)。共通型=ある段が下位段の具体的失敗理由/値をのっぺり成功/失敗に潰して上位へ返す(J2 の一般形: seam は導管、診断を捨てるな、門でないのに裁くな)。メンバー: **①契約A=DE-0509 解消 / ②契約B=DE-0510 解消 / ③provenance=DE-0515 解消 / ④submit.py:410-411 が create_task の WorkflowViolation を握り潰す(既存タスク有りを成功で潰す)=裏取り済(F1 submit.py:409-411 `try/except: pass`・F2 workcell.py:320-321 `raise WorkflowViolation("task already exists")`・F3 例外は戻り値に現れない)=DE 化可 / ⑤runner reason の RUNNER_FAILED のっぺり化=DE-0515 で解消の可能性・PROBE-PIPE-02 再走の副産物で自動判定(具体 reason→解消/のっぺり→未解消 or 旧コード)**。方針=族一括で「捨てずに具体を上げる」。**急がない・本線を塞がない。DE 化いつでも可**(現場係の「SPR まで待つ」推奨は 2026-07-23 撤回=④は F1/F2/F3 で裏取り済ゆえ DE 化が安い。⑤は PROBE-PIPE-02 の B1/B2 で自動判定)

## §5. セッションの回し方(チェックリスト)

1. [ ] 本書を貼る。「本書に従う。再発明禁止。仕様起草前に §1 と突き合わせる」と一言添える
2. [ ] 作業は §2 の ★ から。飛ばすときは理由を DE に残す
3. [ ] 新しい教訓が出たら: DE 化 → 本書更新 → 可能なら**配線に埋める**(読む棚ではなく通る道へ)
4. [ ] セッション終了時: §2 の状態と §3 の DE 番号を更新した本書を保存する
5. [ ] 「前に決めたはず」と思ったら、思い出させようとせず DE 番号か本書を投げる
6. [ ] **情報の更新は本書(ANCHOR)へ**(Taka 指示 2026-07-23)。チャットに散らさず状態は本書に集約する
7. [ ] **監査観測の既定=PROBE-PIPE-02 節度条件**(CLAUDE_WEB 2026-07-23): 判定は S1(新 task_id+CREATE の kp.provenance 有無)/S2(attempt token CONSUMED 有無)の2点で付ける。成功なら10行で終える。失敗時のみ段階2/3(test_result 全文・artifact sha・PID/lstart・log・分岐痕跡)を開く。観測外の発見は「観測外: 事実1行」で止め掘らない。厚くする時は現場係が明示指定

## §6. 本書の廃止条件(成功の定義)

§2-3(恒久連結)完了後、本書 §2 相当は決定論の status 導出(twoder_status 系譜)が生成できるはずである。
機械生成が本書と同等になった時点で、手動アンカーは廃止する。**この文書が要らなくなることが、繋がったことの証明。**
