# 2DER Ledger Domain Manager / Worker 統合仕様 v0.1

出所: Taka（逐語）/ 受領: Claude Code (MGR) 2026-08-24
位置づけ: IMPL_SOURCE（この文書が正本。要約で置き換えない）

---

目的: 2DERにおける台帳管理を、Claude等の担当者による個別作業から、Ledger Domain Manager + Workerによる継続的・決定論的な管理へ移管する。
位置づけ: Ledger Domainは単なる記録機構ではなく、2DER全体の「記録・関係・状態・寿命・根拠・整合性」を管理する中枢Domainとする。
原則: 新しい台帳・状態・ID・概念を増やすことを目的としない。まず既存機構を調査し、既に在る / 在るが未接続 / 一部在る / 本当に無い を確定してから接続・実装する。

## 0. 結論

Ledger Domainの責務を次の一文で定義する。

2DER内部で発生する記録を、後から追跡・検証・処分・再利用できる状態に保ち続ける。

したがって「台帳に書けた」は完了ではない。

記録されたTASK、ITEM、ROADMAP、RTHREAD、明細、evidence、artifact等について、

* 何なのか分からない
* 何と接続しているのか分からない
* 誰が作ったのか分からない
* 根拠がない
* 処分されない
* 終わったのにOPEN
* 実験用なのに永久保存
* 同じものが重複
* IDはあるがresolveできない
* artifactはあるがITEM状態へ反映されない
* 過去の経験が次のTASKで利用されない

という状態を放置しないことまでをLedger管理とする。

Ledger Domain Manager自身はこれらを直接処理しない。
Workerが事実を測定・局所化し、Ledger Domain Managerが状態と次の行動を決める。

## 1. なぜLedger Domainが必要か

現在の2DERでは、実装工程そのものはかなり機械へ移管されている。
一方、Ledger側では調査時点で以下が観測された。

* ITEM記帳2,411件中、2DER自身による記帳実績 0
* 明細686件中、機械36件 = 5.2%
* Claude 650件 = 94.8%
* 明細の94.9%がfront doorを通らないdirect記帳
* DW側では逆に機械77.8%

つまり、2DERは仕事を機械化し始めているが、その仕事を管理する台帳側には人間/Claude作業が大量に残っている。

さらに、調査では「機能が存在しない」のではなく、機能は既にあるが、生きた経路から呼ばれていないケースが多数確認された。

したがって新しい巨大な台帳システムを作るのではなく、既存Ledger機構をDomainとして統合し、継続管理させる。

## 2. Ledger Domainの管理対象

ITEM / TASK / ROADMAP / RTHREAD / DETAIL / QUESTION / ACCOUNT / CLASSIFICATION / REF /
PROVENANCE / EVIDENCE / VERDICT / DISPOSITION / ARTIFACT / CHANGE / ACTOR / AUTHORITY / STATUS / LIFECYCLE

これらを独立した帳票として見るのではない。例えば、

    ITEM
     └─ TASK
         ├─ RTHREAD
         │   └─ DETAIL
         │       ├─ ACCOUNT
         │       ├─ EVIDENCE
         │       └─ DISPOSITION
         ├─ ARTIFACT
         ├─ CHANGE
         ├─ TEST
         └─ RESULT

という関係そのものを管理対象とする。重要なのは行ではなく関係も台帳の一部であること。

## 3. 三層構造

    General Manager
           │
           ▼
    Ledger Domain Manager
           │
           ├── Worker × N

General Manager: Ledger内部を理解しない。Domainを呼ぶ / 集約状態を受け取る / 他Domainとの順序を管理する / 必要なら上申する、まで。
Ledger Domain Manager: 台帳を直接調査しまくらない。何を調べるか / どのWorkerを動かすか / 結果をどう扱うか / 自動処理可能か / 保留か / 上申か / 優先度 / Domain全体が健全か。
Worker: 限定された仕事だけ。原則「Workerは事実を作る。Managerは意味と次の行動を決める」。Worker自身が巨大な判断主体になってはならない。

## 4. Worker構成（名称は既存語調査後に確定。以下は責務名）

### W1 分類・科目管理
既存 record_typed / assign_account 等を利用する。
担当: 未分類明細の検出 / 既存規則による決定論的分類 / 科目候補 / 分類不能理由 / 分類状態の測定。
既存調査では科目割当646件中644件が LEDGER_ACCOUNT_TREE 由来であり、ここはかなり決定論化されている。
LLMを必要としないものへLLMを使わない。

### W2 Evidence / Provenance管理
担当: evidenceの存在確認 / detail ↔ evidence接続 / test ↔ detail ↔ evidence接続 /
provenance切断検出 / 根拠の無いverdict検出 / thread粒度とdetail粒度の区別。
既にTEST_PROVENANCEによって DETAIL → TEST → RUN RESULT → EVIDENCE を切れずに残す実走が成功している。
新しい証拠体系を作るのではなく、既存 record_evidence 等を正本として利用する。

### W3 処分管理
担当: 未処分在庫 / 処分可能候補 / 処分不能理由 / evidence不足 / classification不足 / authority不足 / 長期滞留。
重要: Workerによる自動処分を原則としない。既存 dispose_decision の思想を維持する。
Workerは「処分可能候補 / 理由 / 根拠 / 現在の阻害条件」までを出す。実際の処分はauthorityに従う。

### W4 Relation Integrity
台帳間の接続を管理する。
例: TASK→ITEM / TASK→RTHREAD / RTHREAD→DETAIL / DETAIL→ACCOUNT / DETAIL→EVIDENCE /
TASK→ARTIFACT / TASK→CHANGE / ID→resolver。
検出対象: orphan / dangling reference / resolve不能 / 片方向だけ存在 / repo境界による偽の非実在 /
event identity conflict / task_id形式差 / stale projection。
「値は存在するが読み口がない」場合もここで検出する。

### W5 Lifecycle管理
対象: TASK / ITEM / ROADMAP / 実験 / 調査 / 一時的artifact / 古い候補 / superseded記録。
例えば「試験目的で作られたTASKが、試験終了後も数か月OPEN」を許さない。
ただし単純なTTL削除にはしない。

    長期OPEN → Lifecycle Workerが観測 → 理由を分類
      (active / waiting / blocked / experimental / superseded / abandoned candidate / unknown)
      → Domain Manager
      → KEEP / CLOSE候補 / ARCHIVE候補 / SUPERSEDE候補 / MERGE候補 / ESCALATE

削除・不可逆変更はauthorityへ送る。

## 5. 「OPENであること」に理由を要求する

「OPENだからOPEN」を認めない。長期間OPENなら、少なくとも機械的に説明可能でなければならない。

    OPEN / reason = WAITING_UPPER_REVIEW / since / dependency / next_actor
    OPEN / reason = EXPERIMENT_RUNNING / experiment / last_activity

理由が取得できない場合、OPEN_REASON_UNKNOWN として管理対象にする。
これは即座に閉じるという意味ではない。分からない状態を分からないまま放置しないという意味である。

## 6. 実験・試験資産の寿命

実験用TASKやROADMAPは通常TASKと区別して寿命を管理する必要がある。
判定材料として利用可能なものを先に調査する。
例: actor / work kind / provenance / parent ITEM / artifact / test marker / roadmap relation /
creation reason / downstream dependency / last activity / supersedes / result。
実験終了後、結果あり・依存なし・後続なし・参照なし ならLifecycle候補にする。
ただし「実験らしい名前だから削除」のような名前依存判定は禁止する。

## 7. Stale管理

対象例: OPENのまま更新なし / IN_PROGRESSだが実行なし / approval待ちのまま /
resolvedだが後続状態が更新されていない / artifact追加後もITEM summaryが古い /
cacheが正本より古い / daemonがsourceより古い。
Runtime Control Domainと重なる場合は、Ledger側は記録状態のstaleだけを担当し、process liveness等はRuntime側へ渡す。

## 8. 「記録がある」と「管理されている」を区別する

今回EVO-0094で、artifact 53件 / ITEM status_note 全件None という状態が発見された。
これは重要な管理欠陥である。証拠は存在するが、ITEMを見ても何が起きたか分からない。

    artifact増加 / measurement増加 / change増加
      → ITEM projection / summary が更新されているか
      → NO → STALE_SUMMARY candidate

将来的にはClaudeが長い完了報告を書く代わりに、Domain Managerが既存記録から状態を集約できる形を目指す。

## 9. 類似・経験再利用

現在ClaudeがすすめているA4系作業はLedger Domainへ統合する。
目的は、過去の台帳経験を次のTASKへ再利用すること。
ただしLedger自身がPLANを決めてはならない。

Ledgerができるのは、今回 file=A / SPECなし / TESTなし、過去 file=A / SPECあり / TESTあり から
「近縁TASKにはSPEC/TESTが存在した」という観測を提示するところまで。
「SPECを追加せよ」はPlanner等の別責務である。

## 10. 類似判定の現在地（実測を仕様上の既知事項として残す）

symbol: 生成された封印試験等による大量の偽陽性が存在した。除外後 実在率 0.071 → 0.818。
ただし2 TASK以上で共有されるsymbol = 0。したがって現時点では類似入力に使用しない。
file: symbolより有効だが、coverageは限定的。file追加だけではbaseに無かった有用候補は0。
kind: SPEC / TEST / GOAL等、そのTASKが持つ情報種類として使用。
DONOR_HAS_IT: 「今回無いが近縁TASKには存在する」を見る観測規則。既知実測 提案2 / 有用2 / already_present 0。
ただし独立発火TASKは実質1件なので、採用規則へ昇格しない。Ledger Domainでは observation-only として保持する。

## 11. ObservationとDecisionを分離する

Worker「90日更新されていない」→ Manager「Lifecycle確認対象」→ authority「閉じてよい」のように分ける。
同様に Worker「過去の近縁TASKにはTESTが存在」から直接 TEST_REQUIRED へ昇格してはいけない。
観測と規則採用を分離する。

## 12. 自動実行可能範囲

原則として、可逆・追記式・決定論的な操作は自動化候補となる。
例: 測定 / 集計 / orphan検出 / stale検出 / relation確認 / resolve確認 / candidate生成 /
既存規則による分類 / evidence追記 / status projection更新 / observation記録。
ただし既存authorityを必ず正本とする。Ledger Domain独自の裏authorityを作らない。

## 13. 自動実行してはいけないもの

不可逆削除 / 強制close / 人間裁定の上書き / evidenceの削除 / 履歴改変 / authority変更 /
blocking化 / required化 / LLM利用を伴う権限操作 / restart / kill / 正本変更。
特に「不要そうだから消した」は禁止する。

## 14. 過去記録を書き換えない

Ledger管理改善によって古い記録が不完全と判明しても、原則として履歴を書き換えない。
使用するのは append / supersede / correction / projection再構築 である。
今回refs抽出器でも、過去refsを削除せず読む側で新しい抽出を行った。この原則をLedger Domain全体へ適用する。

## 15. Ledger自身の自己監査

既に発生した実例: Pythonだけ走査してshell callerを見落とす / JSONを加えて自分のtraceをcallerとして数える /
「実在」を正当refのrecallと誤認する / task_id形式違いで接続を過少計測する / stale cacheを現在値として表示する。

したがってWorkerには可能な限り、分母 / 探索範囲 / 除外範囲 / 取得不能数 / 判定不能数 を持たせる。
0件は「0件だった」のか「取得できなかった」のかを区別する。

## 16. 保存則・対称性・対等性

対等性: 書けるものは原則として引けるか。WRITE → RESOLVE が成立するか。発行したID自身がresolve不能なら異常候補。
対称性: 書き手があるなら読み手があるか。producer ↔ consumer。片側しかなければ未接続候補。
保存則: 入口から出口まで件数が説明できるか。総数 = processed + pending + rejected + unavailable + excluded のように、消えた件数を作らない。

## 17. LLMの使用

Ledger管理の基本処理をLLMへ依存させない。
まず 1.決定論 2.既存規則 3.構造比較 4.集計 5.provenance で処理する。
それでも意味判断が必要な場合だけLLM候補とする。
LLMを使用する場合も、LLMの回答そのものをevidenceとしない。入力、判断、根拠、結果を分離する。

## 18. Ledger Domainの状態

Domain ManagerはTASK固有の巨大な情報を持たない。持つのは集約状態だけ。

    LedgerDomainState:
      open_items / open_tasks / stale_tasks / orphan_relations / unclassified_details /
      undisposed_details / missing_evidence / unresolvable_ids / stale_summaries /
      lifecycle_candidates / escalations / worker_health / last_cycle

個々の結果の正本は各Ledgerに置く。

## 19. UI

UIはLedger Domainの正本ではない。UI担当は Ledger Domain Manager → 集約状態 → UI を表示する。
UI自身が複数台帳を横断して独自判定しない。
最低限、正常 / 要確認 / 停滞 / 分類不能 / 処分待ち / Lifecycle候補 / 上申 程度が一目で分かればよい。
Domain UI Manager化は、このLedger側の状態出力が固まった後でよい。

## 20. Claude台帳担当の移管

現在: Claude → 調査 → 数字を読む → 原因分類 → 台帳記帳 → 次を判断
目標: Workers → 測定・局所化 → Ledger Domain Manager → 状態・候補・次行動 → authority → 必要な場合だけClaude/Taka

Claudeは、新規設計 / 規則変更 / 未知ケース / 高度な監査 / authority上必要な判断 へ縮退させる。

## 21. 実装順序（一気にWorkerを大量作成しない）

* Phase 1 — Inventory: 既存機構を全件調査し EXISTS / UNWIRED / PARTIAL / MISSING へ分類する。既存の読み口を最優先する。
* Phase 2 — Observation: Workerを接続し、分類 / evidence / relation / disposition / lifecycle を観測だけさせる。本線を止めない。
* Phase 3 — Candidate Management: 観測結果から stale / lifecycle / disposition / relation repair / reuse の各candidateをDomain Managerが管理する。
* Phase 4 — Safe Automation: 実測で安全性が確認された可逆操作だけAUTOへ移す。
* Phase 5 — Human/Claude Reduction: 残存する人間・Claude作業を測定し、決定論化可能なものをWorkerへ移管する。

## 22. 完了条件（「ファイルができた」で判定しない）

1. Ledger管理対象が列挙されている
2. 各対象の正本が一意
3. 主要relationが機械的に検査できる
4. 未分類を検出できる
5. evidence不足を検出できる
6. 未処分を理由別に説明できる
7. 長期OPENを検出できる
8. 実験・試験資産のLifecycle候補を作れる
9. orphanを検出できる
10. resolve不能IDを検出できる
11. stale projectionを検出できる
12. Worker結果が台帳へ戻る
13. Domain Managerが集約状態を持つ
14. GeneralはLedger内部構造を知らなくてよい
15. authority外の操作をしない
16. 過去記録を書き換えない
17. 自己監査に分母と探索範囲がある
18. 観測と裁定が分離されている
19. Ledger担当Claudeの定型作業量が測定可能
20. Claudeを外しても定常管理が継続する

最終的な完了条件は、「台帳が存在する」ではなく、「放置しても台帳が自分自身を管理し続ける」こと。

## 23. このDomainの位置づけ

Ledger Domainは2DERの補助機能ではない。
実装Workerが間違えても、記録・根拠・関係・履歴が正しく管理されていれば、後から失敗を発見し修正できる。

逆にLedgerが壊れると、何をしたか分からない / なぜそうしたか分からない / 何が終わったか分からない /
何が残っているか分からない / 同じ失敗を再利用できない / Managerが正しい判断材料を得られない 状態になる。

したがってLedger Domainは、2DERが自分の過去を失わず、自分の現在を説明し、自分の未完了を管理し、
過去の経験を次の行動へ再利用するための管理Domain として設計する。

ここを十分に作り込むことで、現在Claudeが担っている「調べる・整理する・記帳する・残件を探す・
古いものを片付ける・過去との関係を調べる」という管理業務そのものを、2DER側へ段階的に移管する。
