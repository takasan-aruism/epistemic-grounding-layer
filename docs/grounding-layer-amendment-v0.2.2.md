# Epistemic Grounding Layer — Amendment v0.2.2

対象: grounding-layer-unified-v0.2.md + Amendment v0.2.1
契機: GPT監査(2026-07-05)。v0.2.1の残存穴4系統の指摘:
  (1) 離散化後も残る findings の相関誤判定
  (2) 「縮小は害が小さい」仮定の claim type 依存性(semantic narrowing問題)
  (3) Claude bootstrap の ground truth 化(盲点の蒸留)
  (4) Evidence 抽出段の重み共有(判定者の世界が生成者に切られている)
本修正の主題: 役割分離の次段階としての「故障相関の分離」。
LLM を裁定者からセンサーへ下げる方向(v0.2.1)を維持し、センサー自体の
相関故障を計測・分離可能にする。

優先度: P0 = AM-11 / AM-12 / AM-13 / AM-14(実装前必須)
        P1 = AM-10 / AM-17 / AM-19
        P2 = AM-15 / AM-16 / AM-18 / AM-20

---

## AM-10 Finding Family / Finding Independence 【P1】

### 問題
F1〜F8 は独立した8条件に見えるが、同一 LLM call から出る限り、単一の潜在判断の
8表現である可能性がある(多数のリンクに見えて同根、の finding 版)。

### 規則
```
FI-1  findings を単一 LLM call 由来のまま独立証票として数えてはならない。
FI-2  各 finding は finding_family を持つ:
        ENTAILMENT family:  F1(support) / F5(relation_type)
        SCOPE family:       F2(scope) / F4(residual_axes)
        MODE family:        F3(validation_mode)
        IDENTITY family:    F6(duplicate) / F7(conflict)
        SECURITY family:    F8(taint)
FI-3  IDENTITY family の候補生成は Gate 2 [code]、SECURITY は ETB scanner [code]、
      MODE は AM-15 により主にコード導出とする。
      LLM judge の本務は ENTAILMENT と SCOPE の2 family に縮小される。
FI-4  HIGH epistemic risk candidate(判定基準 DD-21)では、ENTAILMENT と SCOPE を
      別 run(blind input / 別質問構造。可能なら別重み)から取得する。
FI-5  全 finding は common_run_id を保持する。同一 run 由来 finding 群の
      「見かけ上の合議」を後から層別できるようにする。
FI-6  Decision Table は finding の個数を根拠にせず、必要 family の充足を
      根拠とする(G4-2 の解釈規則として追加)。
FI-7  [Phase 1a 運用] 既定は単一 run + common_run_id 記録。family 分割 run は
      HIGH risk のみ。記録された common_run_id により、run 内 finding 相関は
      後から実測可能である(仮定を測定対象に変える)。
```

## AM-11 UNJUDGEABLE / EVIDENCE_INSUFFICIENT 【P0】

### 問題
強制4択 enum は判定不能を最も近い値へ押し込む(離散化の既知の副作用)。
また v0.2.1 は曖昧を全部 DEFER へ送るため、DEFER queue が
schema破壊・finding矛盾・LLM故障・証拠不足のゴミ箱になる。

### 改訂
enum 拡張:
```
F1: SUPPORTED / PARTIAL / NOT_SUPPORTED / CONTRADICTS / UNJUDGEABLE
F2: WITHIN / EXCEEDS / NARROWER / DISJOINT / UNRESOLVED
F3: DECLARED / SPECIFIED / OBSERVED / MEASURED / REPRODUCED / UNRESOLVED
```

経路分離:
```
G4-6  UNJUDGEABLE / UNRESOLVED は DEFER ではなく、原則として
      EVIDENCE_INSUFFICIENT outcome を生成する。
G4-7  EVIDENCE_INSUFFICIENT は candidate failure ではなく正常な
      epistemic result である。処理経路:
      (a) 追加 evidence 要求として Knowledge Gap を生成 or 再OPENし、
          SearchPlan 候補を添付する(§9/§10 への統合)。
      (b) または RD へ scope 縮小候補として返す(AM-12 の経路)。
G4-8  DEFER の適用範囲を「システム異常・finding間矛盾・enum逸脱・
      人間例外」に限定する。epistemic な不足は DEFER に入れない。
```

DEFER = 系の判断不能(異常系)、EVIDENCE_INSUFFICIENT = 世界についての
正常な中間結果、という区別を固定する。

## AM-12 Semantic Narrowing Contract 【P0】

### 問題
v0.2.1 RR-4' (a) は「縮小方向の編集は害が非対称に小さい」と仮定したが、
これは syntactic shrink と semantic narrowing の混同である。

反例:
```
works(runtime=vLLM 0.17, gpu=RTX5090)
  → gpu を known_omissions へ移動 →
works(runtime=vLLM 0.17)
```
フィールドは減ったが、命題空間では RTX5090 限定から GPU 無限定へ**拡張**している。
PROCEDURE(flag削除で手順破壊)/ COMPATIBILITY(組合せ条件の脱落で成立範囲拡大)
でも同型の危険がある。

### 規則
```
SN-1  次元削除は縮小ではない。恒真とする:
        「固定された次元集合の上で、制約を追加する・値集合を狭めることのみが
         narrowing である。次元を削除することは narrowing では決してない。」
SN-2  自動適用可能な編集は、コードが scope algebra 上で
        編集後claimの成立世界集合 ⊆ 元claimの成立世界集合
      を決定的に証明できるものに限る(semantic narrowing の証明可能性)。
      Phase 1b での許容例: 同一次元内の値集合精緻化
      (runtime_version ">=0.10" → ">=0.11"、entity集合の階層下位への限定
       ただし entity 階層が Registry に登録済みの場合のみ)。
SN-3  PROCEDURE / COMPATIBILITY / MEASUREMENT claim では自動 scope 編集を
      Phase 1a/1b を通じて全面禁止する。
SN-4  [Phase 1a] 自動 scope 編集そのものを実装しない。
      F2=EXCEEDS の処理: SCOPE_REDUCTION_REQUIRED outcome として
      candidate を RD へ返却し、RD が新 candidate を生成する。
      旧 candidate は原本として保存(削除・改変なし)。
      理由: スパインの目的は「根拠なし claim を構造的に不可能にする」の
      1点であり、自動矯正は目的に含まれない。v0.2.1 RR-4' の自動適用条項は
      Phase 1b の SN-2/SN-3 準拠実装まで凍結する。
SN-5  known_omissions への次元移動は「claim が当該次元について何も主張しない」
      ことを意味する scope 意味論を明文化する。statement 自然文が無限定な
      一般主張に読める場合、Curator findings は F2=EXCEEDS を返すべきであり、
      omission 移動で応急処置してはならない。
```

## AM-13 Bootstrap Gold Set Separation 【P0】

### 問題
v0.2.1 CB-3 は「35B findings と CDEC(Claude判定)の一致率」を移行条件とした。
これは「35B が正しいか」ではなく「35B が Claude を模倣できるか」を測る。
Claude にも盲点があり、一致率最適化はその盲点を local model へ蒸留する。
同型モデル自己監査の失敗を一段上で再演する構図。

### 改訂
```
CB-3' 35B 移行条件を Claude agreement から adjudicated benchmark 上の
      class別 error profile に差し替える:
        FAR(False Accept Rate: 無根拠 candidate の受理)  <= 閾値【主指標】
        Scope Overreach Rate                              <= 閾値
        Challenge set pass rate                           >= 閾値
      単純一致率は補助指標に格下げする。閾値は DD-22。
CB-5  Claude findings は teacher signal であり ground truth ではない。
CB-6  dataset を3分割する:
        A. Operational stream — 実運用 candidate(訓練・較正に使用可)
        B. Adjudicated benchmark — 複数独立視点(Claude / GPT / 人間または
           決定的 evidence 再検査)の一致でラベル確定した 50〜100件。
           3-way 一致 → adjudicated label、不一致 → adjudication queue。
           移行判定専用。プロンプト調整・few-shot 構築への混入禁止。
        C. Challenge set — 過去の誤ACCEPT / scope overreach / prompt injection /
           partial evidence / false absence を含む意図的難例。
CB-7  adjudicator の実体は本プロジェクトの現有組織に対応させる:
      Claude(bootstrap判定者とは別セッション)+ GPT + Taka または
      決定的再検査(evidence excerpt の機械照合が可能な型の candidate)。
CB-8  移行後の Claude 抜き打ち再審査(v0.2.1 CB-3 後段)は維持し、
      サンプリングに benchmark B の再判定を含めて drift を検出する。
```

## AM-14 Evidence Extraction Independence 【P0】

### 問題
generator と judge の重み非共有(WS-1)は candidate 生成段の相関を切るが、
Evidence Fragment 自体が抽出者の盲点で切られている場合、judge の世界は
既に汚染されている。例: 原文「NVFP4 is supported on Blackwell. GeForce
Blackwell devices are excluded.」から前半のみ fragment 化 → Claude judge は
fragment だけを見て SUPPORTED を返す。別重みでは防げない。

### 規則
```
EI-1  重み非共有(WS-1)のみで independence 成立とみなさない。
EI-2  fragment の extraction_run_id 必須(v0.2 EF-3 / RL-4 で対応済み。確認条項)。
EI-3  [Phase 1a 既定・全 candidate] judge packet には fragment 単体でなく
      bounded source context を含める:
        section heading + 直前 block + fragment + 直後 block。
      normalized observation は既に保存されているため、これはパケット構築
      コストのみで実現できる。window 幅の既定値は DD-24。
EI-4  HIGH risk candidate(DD-21)では、独立 extractor(別重みまたは別 run)に
      同一 normalized observation からの second fragment proposal を出させる。
EI-5  fragment 選択の不一致は EVIDENCE_BOUNDARY_CONFLICT として記録し、
      candidate を EVIDENCE_INSUFFICIENT 経路(G4-7)へ送る。
EI-6  judge は FRAGMENT_INSUFFICIENT を出せる(bounded context を見ても
      判定に足りない場合)。その場合も EVIDENCE_INSUFFICIENT 経路。
      judge に source の自由探索はさせない(観測は既に手元にある。
      同一 normalized content 内での不足申告のみを許す)。
```

## AM-15 Validation Mode Provenance Derivation 【P2】

### 問題
F3 を LLM に無から選ばせる必要はなく、むしろ「benchmark table だから
REPRODUCED」型の誤分類リスクを作る。mode の大部分は provenance metadata
から決定的に導出できる。

### 規則
```
VP-1  F3 を二段に分割する:
        F3a provenance_mode_candidate [CODE]
            source.kind / run.activity_type / measurement schema の有無 /
            reproduction run へのリンク有無、から候補 mode を導出。
        F3b semantic_mode_confirmation [LLM]
            CONFIRM / DOWNGRADE(下位modeを指定) / UNRESOLVED の3値のみ。
VP-2  mode 単調性: LLM は F3a の候補より上位の mode へ UPGRADE できない。
      コードが provenance から見出せなかった検証様式を LLM が主張するのは
      定義上根拠がない(provenance にないものは mode の根拠にならない)。
VP-3  DOWNGRADE は無条件に受理してよい(主張を弱める方向)。
      ※これは semantic narrowing であることがコードで自明なケース
        (mode 序列は固定次元上の値精緻化)であり、SN-2 と整合する。
```

## AM-16 Bounded Duplicate / Conflict Reference 【P2】

### 問題
F6/F7 に claim_id を自由記述させると ID hallucination の余地がある。

### 規則
```
BR-1  F6/F7 を bounded reference 構造に変更する:
        F6_duplicate_relation: {target, type: EXACT|SUBSUMES|SUBSUMED_BY|
                                            NONE|UNRESOLVED}
        F7_conflict_relation:  {target, type: DIRECT|CONDITIONAL|TEMPORAL|
                                            NONE|UNRESOLVED}
BR-2  target は Gate 2 が supplied した candidate set 内の ID のみ有効。
      schema validator が set 外 ID を拒否する(即 DEFER: 異常系)。
```

## AM-17 Critical DEFER Dependency Handling 【P1】

### 問題
v0.2.1 G4-3「DEFER は task をブロックしない」は放置耐性として正しいが、
task が依存する critical candidate が DEFER されたまま RD が別の弱い claim で
穴埋めして SOLVED に到達する経路を開いてしまった。

### 規則
```
DF-1  DEFER / EVIDENCE_INSUFFICIENT は task を自動ブロックしない(維持)。
DF-2  candidate は importance を持つ:
        REQUIRED_FOR_RESOLUTION / SUPPORTING / OPTIONAL / BACKGROUND。
      importance の出所は Manager の task dependency graph であり、
      RD の自己評価ではない(G4-4 ブラインドパケット原則と両立。
      judge packet には含めない — importance は処分段 Gate 5 で参照する)。
DF-3  REQUIRED_FOR_RESOLUTION の candidate が DEFER /
      EVIDENCE_INSUFFICIENT になった場合、対応 Knowledge Gap を OPEN へ戻す。
DF-4  required gap が未解決である限り、Manager は resolution status を
      SOLVED へ遷移させられない。ACTIONABLE は許可するが、resolution に
      blocked requirement を明示的に列挙する。
```
「人間待ちで task 停止はしない。しかし DEFER された必須 claim を
存在しないことにして解決済みにもしない。」

## AM-18 Bootstrap Knowledge Partition 【P2】

### 問題
bootstrap=true フラグ(v0.2.1 CS-3)だけでは、成熟前の初期 claim が
通常の Global RAG で高優先検索され、初期汚染が長く残る。

### 規則
```
BP-1  retrieval index を GLOBAL_STABLE / GLOBAL_BOOTSTRAP に分割する。
      RD retrieval は stable を優先し、bootstrap 由来は区別して提示する。
BP-2  bootstrap claim を FACT の ground に使う場合、bootstrap provenance
      flag を assertion(grounds_snapshot)へ伝播する。
BP-3  consolidation run(CS-2)完了後、当該 claim を STABLE へ昇格する。
BP-4  BOOTSTRAP は status と直交する(VERIFIED + BOOTSTRAP は有効:
      一次確認済みだが entity/axis/dedup 成熟前、の意)。
```

## AM-19 Design Decision Evidence Ledger 【P1】

### 問題
AP-3 発動(「実験結果により設計原理を修正」)の発動条件と履歴が自然文でしか
残っていない。半年後「なぜ Gate 4 を離散化した?」に「設計思想です」ではなく
「実験 X で自由文自己監査が失敗したため」と逆走できる必要がある。

### 規則
```
DE-1  設計変更は Design Evidence Record を持つ:
        {design_evidence_id, affected_rules, experiment_ref, observation,
         replication_status(SINGLE_EXPERIMENT/REPLICATED/...),
         decision(AMEND/REJECT/DEFER), amendment_ref, decision_owner}
DE-2  Design Decision Ledger は Knowledge DB とは別の台帳とする
      (repo 内 jsonl / md で足りる)。
DE-3  replication_status=SINGLE_EXPERIMENT の変更は、反証実験が出た場合の
      巻き戻し対象として扱う(設計にも RC の精神を適用)。
DE-4  初期レコードとして本 Amendment 系列を遡及登録する:
        DE-0001: codegen-loop-audit 実験 → AM-1/2/3(v0.2.1)
        DE-0002: GPT監査(2026-07-05)による論理的反例(semantic narrowing 等)
                 → AM-11/12/13/14。※実験でなく反例による発動も
                 evidence class として記録する(experiment_ref を
                 counterexample_ref に読み替え)。
```

## AM-20 Finding Classification Residual 【P2】

### 問題
離散化の副作用: 現行 F1〜F8 で表現できない新種の失敗が全部 DEFER へ落ち、
finding schema 自体が新しい軸を学習しない(finding 版の schema 硬直)。

### 規則
```
FA-1  judge は enum 外の値を生成してはならない(維持)。
FA-2  既存 finding axis で判定不能な場合、judge は
      classification_residual: {present: true, code: "NO_MATCHING_FINDING_AXIS"}
      を返せる。自由文は decision table が読まない(維持)。
FA-3  residual rate を finding family 別に計測する。
FA-4  閾値(DD-23)超過で Finding Schema Review を起動する
      (サンプルの free_note を Claude / 人間がレビューし、新 F9 の要否を検討)。
FA-5  Review 完了までは既存 Decision Table を変更しない。
FA-6  finding schema の変更は AXIS_REBOOT(AX-5)と同形式の migration event
      として記録し、Decision Table version(下記)を更新する。
DT-1  Decision Table はバージョンを持ち、CDEC に decision_table_version を
      刻む。table 変更前後の判定を層別可能にする。
```

---

## DD 追加・改訂

```
DD-18' (改訂) 35B 移行閾値の対象を CB-3' の error profile
        (FAR / Scope Overreach / Challenge pass)に変更。
DD-21  HIGH epistemic risk candidate の判定基準
        (FI-4 family分割・EI-4 second extraction の発動条件)。
        初期案: EP-TECH-STRICT profile 下 / NEGATIVE polarity /
        Critical Claim への conflict / retraction 再審査系。
DD-22  FAR / Scope Overreach / Challenge pass の閾値と benchmark B の件数。
DD-23  classification residual rate の Review 起動閾値(family 別)。
DD-24  bounded source context の window 幅(既定: heading + 前後1 block)。
```

## Phase 1a への影響(AM-4 改訂)

```
追加: AM-11(enum拡張 + EVIDENCE_INSUFFICIENT 経路) /
      AM-14 EI-3(bounded context packet — 構築コストのみ) /
      AM-17(importance + required gap 差し戻し — Manager 側は最小の
      依存表で可) / FI-5,FI-7(common_run_id 記録のみ)
削除: v0.2.1 RR-4' 自動縮小適用(SN-4 により 1a では不実装。
      F2=EXCEEDS → SCOPE_REDUCTION_REQUIRED 返却に置換)
純増減: AM-12 と AM-11 は実装を単純化する方向(自動編集の削除、
      enum 値追加)であり、1a の重量は実質増えない。
1b へ: AM-10 family分割 run / AM-13 benchmark 構築と移行判定 /
      AM-15 / AM-16 / AM-18 / AM-20
```

## 監査記録(AU 続番)

```
AU-28  finding family と単一run相関の明示(FI-1〜7)。「8 finding = 8視点」の
       誤認を禁止し、common_run_id で相関を測定対象化。
AU-29  UNJUDGEABLE / UNRESOLVED 追加と EVIDENCE_INSUFFICIENT 経路の新設。
       DEFER を異常系専用に純化。
AU-30  semantic narrowing contract。「次元削除は縮小ではない」を恒真化し、
       Phase 1a の自動 scope 編集を全廃(v0.2.1 RR-4' の部分巻き戻し)。
AU-31  bootstrap gold set 分離。Claude = teacher not oracle。移行判定を
       agreement から FAR 主体の error profile へ変更。
AU-32  extraction independence。bounded context を全 candidate 既定に、
       second extraction を HIGH risk に。EVIDENCE_BOUNDARY_CONFLICT 新設。
AU-33  validation mode のコード導出 + LLM は confirm/downgrade のみ
       (mode 単調性: provenance 上限を超える UPGRADE 禁止)。
AU-34  F6/F7 の bounded reference 化(ID hallucination 遮断)。
AU-35  critical DEFER の gap 差し戻し(SOLVED 遷移の封鎖、ACTIONABLE は
       blocked requirement 明示で許可)。
AU-36  bootstrap retrieval partition(STABLE/BOOTSTRAP、status と直交)。
AU-37  Design Decision Evidence Ledger(AP-3 発動の形式化・設計への RC 適用)。
AU-38  finding classification residual(finding schema の硬直監視。
       Axis Emergence の finding 層への適用)+ Decision Table versioning。
```

有効文書セット: 親文書 v0.1 + grounding-layer-unified-v0.2.md +
Amendment v0.2.1 + 本 Amendment v0.2.2。
v0.2.1 のうち RR-4'(a) 自動縮小適用は本書 SN-4 により凍結
(Phase 1b で SN-2/SN-3 準拠実装として復活可)。
