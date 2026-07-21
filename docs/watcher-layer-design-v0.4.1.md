# Watcher Layer 設計提案 v0.2 — 系内感覚器(Qwen常駐・判断と書込みを持たない)

status: DRAFT v0.4.1(GA 確認便の blocking edits 3件反映・Taka裁定前・構築ゼロ)
date: 2026-07-21
supersedes: v0.4(627070419)/ watcher-layer-design-v0.3.md(sha256 b477447c)/ v0.2(db15d946)/
  watcher-layer-amendment-v0.2.1.md(吸収済み)
adjudication: GA-1..10 は v0.2 付録A どおり。GA-11..16 の設計側裁定 =
  design-adjudication-20260721 束B(全 ACCEPT、GA-14/16 は ACCEPT-MOD)。
depends: DE-0344 / DE-0426 / DE-0429 / DE-0437 / RL-1..4 / EI-3 / FA-2 /
  DE-0474 / DE-0453 / DE-0446 / DE-0470 / DE-0475 / DE-0476 / DE-0479 / DE-0480
scope: 本書は Watcher 本体のみを扱う(GPT総合裁定準拠)。
  構成台帳の AST・意味層 = 別ITEM(§16)。
  Claude Code 職責 = Taka 恒久裁定(2026-07-19)の参照のみ、本書は制定しない(§14)。
v0.3→v0.4 差分: GA-11..16 対応。一覧は付録C。
v0.4→v0.4.1 差分(GA 確認便 REVISION_REQUIRED の blocking edits):
  (1) §7 全 kind schema から lane を削除(GA-13 の契約矛盾解消)。
  (2) prompt_version の pin 照合を emit_api 自身の義務に(GA-12 remaining)。
  (3) 並行負荷試験 A-5 を W1A 合格条件へ(GA-16 remaining)。
  + CF-10(GA-14 実装 gate)と ts 非全順序注記。

---

## 0. 目的

系内の変更イベントを起点に起動する監視層。位置づけは「系内感覚器」:
変更が起きた事実を忘れず、見落としを観測可能にする。判断と書込みを
持たせず、まず感覚器だけを確実に作る(GPT総合裁定の表現を採用)。

Claude Code のプロンプト駆動起動に由来する常在的追従の不履行
(状態変化への非追従・常設指示の忘却)を、環境側の機構で代替する第一歩。

---

## 1. 非目標

```
NG-1  観測対象系(git working tree / repo history / EGL正典 /
      ENERGIZATION_LEDGER)への書込みは一切しない(W-R0)。
NG-2  Watcher は DE を正典起票しない。観測候補まで。
NG-3  Claude Code の職責定義は本書の対象外(Taka恒久裁定を参照、§14)。
NG-4  apply-semantics-v2(DE-0436)はスコープ外。
NG-5  Watcher 出力を根拠とする自動修復・自動commit・自動再実行は禁止(W-R2)。
NG-6  ライブURL等 materialized view の自動更新は W1 スコープ外。
      W1 は dependency declaration(§9.2)に基づく更新漏れ検知まで。
NG-7  構成台帳の AST symbol table / import graph / 意味層は W1 スコープ外
      (別ITEM、§16)。
NG-8  n=20 規模での統計的有意差 claim は行わない。W1 は記述統計のみ(GA-5)。
```

---

## 2. 書込み三分類(GA-1 裁定 — 「read-only」の再定義)

v0.1 の「Watcher全体read-only」は誤記述であった。正確には:

```
W-R0  観測対象への書込み禁止。
      git working tree / repo history / EGL正典 / ENERGIZATION_LEDGER /
      docs 正本を変更しない。
W-R1  観測イベントの append は C 帳簿(emit_api EventStore)経由のみ許可。
      根拠: DE-0474 境界表「実行の観測事実 → C」。wake / orphan / 観測 /
      集計はすべて WATCHER_* kind として emit_api で記録する。
      Watcher 専用の独立 store は設けない(第4の帳簿の新設禁止)。
      構成 snapshot(as_of_commit 付き・W1B/ITEM-SL-A)も同経路。
      既存 record の上書きは emit_api の append-only 性で構造的に不可。
      一時生成物(観測用 work file)のみ atomic replace 可、C 外の
      恒久書込みは禁止。
W-R2  逆流禁止。派生ストアの内容を根拠とする対象系への自動書込み・
      commit・DE正典化を禁止する。
```

構成 snapshot は FS+git から決定的に再導出可能であり、その記帳は
**C 内の canonical observation record** である(対象状態そのものの独立
SoR ではない——GA 続番監査の語法を採用)。「導出可能な第2 SoR」禁止には
当たらない(観測事実の一次記録。RC-3 準用)。
横断読出しが要る場合は status_views 型の導出ビューで解く(DE-0474 束縛4)。
機械層と意味層は別 kind・別 schema(意味層は本書スコープ外、§16)。

---

## 3. アーキテクチャ — 3層 + 二系統WAKE

```
[層1 WAKE — 決定論コード・二系統(GA-2 裁定)]
  EDGE:      git hook / inotify による即時 WAKE。
  SWEEP:     定時 polling で HEAD / tree hash / ledger offset /
             FS snapshot を EDGE と独立に再計算する検査経路。
             (障害時fallbackではなく hook を検査する独立観測者)
  RECONCILE: EDGE 未観測の SWEEP 差分を WAKE_ORPHAN として記録。
  出力: WATCHER_WAKE / WAKE_ORPHAN

[層2 MULL — Qwen 32B 並列]
  入力: WAKE の指す差分の bounded context のみ(種別ごとの上限、DD-W5')
  出力: インスタンスごとの生 WATCHER_OBSERVATION(全件・集計前)

[層3 AGGREGATE — 決定論コード]
  合議判定 / safety_disposition ルーティング / lane binding 検査 /
  dedupe / null・control 比率計算
  出力: WATCHER_CONSENSUS / WATCHER_EXCEPTION / WATCHER_DISAGREEMENT
```

### 3.1 実装写像 — 既存部品への割付(v0.4 改・GA-15/16 反映)

v0.2 起草時に未配備だった部品が実在稼働している(DE-0446/0470 実測)。
層1/層3 は新規実装ではなく既存部品の組合せとして構築するが、**再利用は
機構と hardening パターンに限り、権限プロファイルは転用しない**(GA-15):

```
記録経路   : emit_api(M1 製 EventStore、sha 6bf41034)。hash-chain /
             sealed-field / lane / registry pin の各機構は §17 の
             emit_api 契約改版後のものを使う。Watcher 側で同等機構を
             再実装しない。
SWEEP 起床 : systemd timer(status timer と同方式)。
EDGE 起床  : git hook。hook script は決定論コードのみ(層1)。
sandbox    : workcell unit の hardening 項目(PrivateNetwork / Protect* /
             系統的 deny)を**参考**に、Watcher 専用 unit を新規設計する
             (§3.2)。workcell unit の authority profile
             (ReadWritePaths=/srv/workcell/runs 等)は Watcher の権限
             要件と一致しないため転用しない。
Qwen 呼出  : vLLM は共用するが、W1A で次の分離を必須とする(GA-16):
             (i) request への caller identity 付与(writer_id / run_id)、
             (ii) request hash と response の binding を
             WATCHER_OBSERVATION payload に記録、
             (iii) Watcher 専用 timeout(短め・fail-closed 即 EXCEPTION)。
             queue/quota 分離は W1B 前の飢餓実測を条件とする別チケット。
             failure domain: vLLM 停止は層2 の停止であり層1(LLM 非依存)
             は生存して EXCEPTION を観測し続けること。
指標導出   : §10 の全指標は status_views 型の導出ビューとして実装
             (一次記録 = C、LLM 非関与、決定的再構築)。
```

### 3.2 Watcher unit プロファイル(新規・GA-15)

```
- 起動: systemd timer(SWEEP)+ hook 起点の短命プロセス(EDGE)。常駐なし。
- 読取: 観測対象 5 repo を read-only mount。packet workspace 不要。
- 書込: C の Watcher 名前空間(§7 GA-14 方式)のみ。OS 層で強制。
- 実行: 生成コードの実行なし(runner と異なり worker 出力を評価しない)。
- network: deny 既定 + vLLM socket のみ(層2 呼出時)。
- 資源: 層2 呼出は 1 WAKE = 1 呼出・短 timeout。run loop なし。
- credential: writer identity は配備固定構成から(WS-4''、per-call 供給禁止)。
```

---

## 4. 構造的制約(WS 規則・改)

```
WS-1a AST ゲート: emit 可能なのは単一 emit API 経由の WATCHER_* のみ。
      書込み関数・subprocess・shell・socket・dynamic import / eval / exec を
      静的に持たない。
WS-1b OS 権限制御(GA-3 裁定 — AST は検査層であり権限制御層ではない):
      - 観測対象 repo は read-only mount で参照
      - Watcher 専用 UID
      - 書込み可能 path は observation store のみ(OS 層で強制)
      - network deny 既定
      - symlink 追跡は realpath 検査で observation store 外を拒否
      - logging handler の出力先も observation store 内に固定
WS-2  fail-closed: スキーマ逸脱・応答異常・タイムアウト・空応答は
      WATCHER_EXCEPTION。既定は「観測失敗」であり「異常なし」ではない。
WS-3  bounded context(EI-3 準用)。段間コンテキスト分離。
WS-4'' 封印原則(GA-8/GA-12)の実装は emit_api に一本化し、**拒否と供給の
      両面**を定義する(拒否だけでは GA-8 を満たさない — GA-12):
      拒否面: actor_instance / prompt_version を PROTECTED_KEYS へ追加し、
      payload・nested・別名 field 経由の供給を schema で遮断(下流は
      payload 内の同名 field を読まない)。
      供給面: writer identity は**プロセス起動時に配備固定の構成
      (root 所有・unit 単位)から確立**し、per-call 引数・payload からは
      受けない。actor_instance = writer identity + instance 連番
      (emit_api 生成)。prompt_version は**受領値をそのまま採用しない**:
      emit_api 自身が writer_id に対応する pinned prompt/config hash を
      registry または root 所有の deployment manifest から照合し、
      不一致・未登録 pin は reject する(GA-12 remaining の解消。
      「payload 外から渡された」だけでは sealed supply ではない)。
WS-5  enum 強制 + classification_residual(FA-2 準用)。自由文は層3 が読まない。
WS-6'' WATCHER_* kind の登録は workcell_events.json の registry 改版として
      行う(DE-0453 pin 方式)。**登録の権限根(GA-11)**: writer の登録・
      変更は Taka 裁定イベント(DE 参照必須)のみを根とする。CONTENT_SEAL
      は内容の固定、Taka 印は権限の付与——役割を分離して条文化する。
      循環遮断: 登録改版の起票者・seal 経路が登録対象 writer 自身で
      あってはならない。emit_api への writer_id 導入は新規契約能力
      (現状不在、DE-0475 系実測)であり M1 契約改版として seal 経路で
      行う(§17 工程1)。emit_api は未登録 writer・登録外 kind/lane を
      fail-closed で reject する。
      「第3 SoR にしない」は C 帳簿への帰属(W-R1)により構造的に充足。
WS-7' 単調性は severity にのみ適用(GA-4 裁定):
      safety_disposition の自律的引き下げ・観測取り消しは発行不可。
      分類名(classification)の訂正・再分類は禁止しない。
```

V項目(実装前検証事項): V-W1 DE-0429 reconciler が実際に持つ OS 層制約の
一次確認(コード・mount 構成の実査。「同型の前例」主張は確認後まで保留)。

---

## 5. 役割インスタンス(W1A/W1B で段階投入)

```
[W1A]
ROLE-OBS   observer 1系統: 中立記述。
[W1B]
ROLE-CLS   classifier N=3(DD-W2: 3で開始。増強は同一重み内誤差の
           独立性実測後)。
ROLE-AUD-C consistency: コード生成の機械候補への注釈のみ(§9.1)。
ROLE-AUD-S scope: DE-0045 型兆候の注釈。
ROLE-NULL  二種(GA-5 裁定):
           NULL-N 意味を保った非異常イベント(誤警報率測定)
           NULL-B 因果・binding のみ破壊(構造異常の検出感度測定)
```

---

## 6. 合議と例外の分離(GA-4 裁定)

```
AG-1  classification_agreement(k/N)と safety_disposition を分離する。
AG-2  safety_disposition ∈ {PASSIVE_RECORD / REVIEW / URGENT_EXCEPTION}。
AG-3  単調昇格: 1インスタンスでも重大候補を出せば REVIEW 以上へ。
      引き下げには裁定パスが必要(WS-7')。
AG-4  分類名の不一致のみ(重大候補なし)は WATCHER_DISAGREEMENT として
      記録し、Taka キューへ流さない(PASSIVE_RECORD)。
AG-5  schema 異常・応答異常は従来どおり EXCEPTION(WS-2)。
```

---

## 7. イベントスキーマ(認証・冪等性込み、GA-8 裁定 + emit_api 写像)

v0.2 の共通フィールドは emit_api の record 封筒と重複するため、二重定義を
廃し次の写像で確定する(v0.3):

```
emit_api 封筒が供給(呼出側封入・Watcher 再定義禁止):
  schema_version / producer_version / ts / lane(§7 EV-W1'' により
  発生源から決定論導出・caller 指定不可)/ kind /
  segment_id + sequence_in_segment(← v0.2 の sequence_no を置換)/
  previous_event_hash + record_hash(hash-chain)/ retention_class(registry 封入)
payload に載る Watcher 固有フィールド:
  run_id / source_process_id / dedupe_key / input_snapshot_hash
  + 各 kind の固有フィールド(下表)。**lane は payload に置かない**
  (二重表現の禁止、GA-13)。actor_instance / prompt_version は WS-4'' の
  供給路により封筒側(payload 供給は遮断)。
```

種別(lane・actor_instance・prompt_version は封筒のみ。payload に置かない):

```
WATCHER_WAKE        {wake_id, trigger_kind, trigger_ref}                [EDGE]
WATCHER_WAKE_ORPHAN {orphan_id, sweep_ref, missed_change_ref}           [SWEEP]
WATCHER_OBSERVATION {obs_id, wake_id, role, classification,
                     severity_proposal, classification_residual,
                     bounded_context_ref,
                     vllm_request_hash, vllm_response_hash}             [層2]
WATCHER_CONSENSUS   {cons_id, wake_id, obs_ids[], agreement,
                     final_classification, safety_disposition,
                     routed_to}                                         [層3]
WATCHER_DISAGREEMENT{dis_id, wake_id, obs_ids[]}                        [層3]
WATCHER_EXCEPTION   {exc_id, wake_id, obs_ids[], reason_enum}           [層3]
WATCHER_CONTROL     {ctrl_id, control_id, injected_ref, expected_route,
                     detected, latency}                                 [層1+3]
```

```
EV-W1'' lane ∈ {real / null_n / null_b / control} を全イベント必須とする。
       **lane は caller が渡さない**(GA-13。現 emit_api の caller 指定は
       契約改版で廃止): 層1 の決定論コードが発生源(実 repo イベント /
       null fixture / control 注入)から lane を導出し、emit_api は
       registry の writer→許可 lane binding で検査、逸脱 reject。
       control / null lane から real queue への routing は schema で拒否
       (LN-2 の機械強制)。
EV-W2  dedupe: 層3 は同一 (wake_id, role, actor_instance, prompt_version)
       の重複 obs を拒否する。
EV-W3  CONSENSUS / EXCEPTION / DISAGREEMENT は obs_ids から決定的に
       再導出可能(受け入れ試験に含む)。
EV-W4  kind の段階導入(v0.3): W1A の registry 改版に載せるのは
       WATCHER_WAKE / WATCHER_WAKE_ORPHAN(旧 WAKE_ORPHAN を接頭辞統一で
       改称)/ WATCHER_OBSERVATION / WATCHER_EXCEPTION / WATCHER_CONTROL
       の5種のみ。WATCHER_CONSENSUS / WATCHER_DISAGREEMENT は W1B の
       registry 改版で追加(W1A は ROLE-OBS 1系統のため合議が発生しない)。
EV-W5  writer 別名前空間(GA-14 CRITICAL の解消・設計側裁定):
       registry が writer_id → namespace prefix を固定し、emit_api は
       writer identity から書込 path を決定論導出する(caller の path
       指定不可)。hash-chain は segment 単位で完結し **writer 間で共有
       しない**——並行 append 競合(duplicate sequence / forked chain)は
       構造的に発生しない。writer 横断の全順序は保証しない(C は観測
       帳簿であり writer 内順序 + ts で足りる。横断読出しは導出ビューの
       read-only merge)。単一 append authority(daemon)方式は「writer
       横断の全順序が必要」という実測が反復された場合のみ再裁定
       (DE-0474 束縛5 と同型の再開条件)。【Taka veto 対象】
```

---

## 8. lane 隔離(GA-9 裁定)

```
LN-1  control 注入は non_canonical fixture / throwaway_target のみを対象とし、
      実 repo・実台帳へ擬似変更を入れない。
LN-2  control / null lane のイベントは DE 候補・Taka 例外キューへ
      構造的に到達不能とする(routed_to の許容値を lane で制限)。
LN-3  lane binding の検査は層3 の決定論コードが行う。
```

---

## 9. 契約駆動の整合検査(GA-7 裁定)

### 9.1 機械候補 → Qwen 注釈

コード側が機械的候補を enum で生成し、Qwen は注釈のみ:

```
HEAD_CHANGED / PATCH_APPLICATION_NOT_FOUND / DE_REFERENCE_NOT_FOUND /
HANDOFF_HEAD_MISMATCH / SNAPSHOT_COUNT_MISMATCH
```

「どの repo・どの変更 class で DE が必要か」は契約(§9.2)に依存し、
Qwen の常識判断に委ねない。

### 9.2 dependency declaration(前提条件)

```
DP-1  「event kind X → materialized view Y は更新義務を持つ」を
      機械可読の宣言として保持する(例: HEAD前進 → 管理ページ /
      handoff の鮮度義務)。
DP-2  更新漏れ検知は DP-1 宣言と実状態の突合のみから発火する。
      宣言なき義務の推測検知は禁止。
DP-3  DP 宣言の初期セットは Taka 承認を要する(何が義務かは組織判断)。
```

---

## 10. 常設検証と指標(GA-5 裁定で分離計測)

```
PC-1  positive control 常設(lane=control、LN-1 制約下)。
PC-2  null 二系統常設。
指標(すべて一次記録から導出・W1 は記述統計):
  wake 完全性        : EDGE↔SWEEP 突合(WAKE_ORPHAN 数)。
                       ※ WAKE_COMPLETENESS_MEASURED はこの突合の
                         実装後にのみ主張可(GA-2)
  positive-control recall
  benign-null false-positive rate(NULL-N)
  binding-null detection rate(NULL-B)
  major-event miss count
  classification_agreement 分布 / DISAGREEMENT 率
  CC 監査差分率 / Taka 棄却率
```

---

## 11. 重み跨ぎ監査(CA 規則・改)

```
CA-1  Claude Code は Watcher 出力のサンプリング監査者。
      監査比率(DD-W3'): 最初の50件は CONSENSUS 20% + EXCEPTION 100%、
      以後 CC 差分率に基づき調整(GPT 裁定案採用)。
CA-2  監査対象選定はコード側乱数(シード記録)。
CA-3' CC は構造化 finding を返すのみ。Run Ledger への記録は監査ハーネス
      (コード)が行う。CC による直接書込みは行わない(GA-6 裁定 —
      「監査のみ」との整合)。
CA-4  感度は過検出側(非対称コスト)。
```

---

## 12. 受け入れ試験と counter-factual(W1A/W1B ゲート)

W1A 合格条件(DD-W1' 初期ゲート、GPT 裁定案採用):

```
重大イベント見逃し 0 / schema 異常の正常扱い 0 /
positive-control recall 100% / benign-null 誤警報率は記録のみ /
軽微分類正答率は参考値
A-1  垂直スライス: 実変更1件 → EDGE WAKE → SWEEP 突合0 orphan →
     ROLE-OBS 観測 → 記録。
A-3  集計の決定的再導出検査(EV-W3)。
A-5  並行負荷試験(GA-16 gate・v0.4.1 追加):
     (a) BUILD 負荷実行中の Watcher request が bounded timeout 内に処理
         されること、(b) 処理されない場合は確実に WATCHER_EXCEPTION に
         なること(無音の欠測ゼロ)、(c) Watcher 負荷が BUILD worker を
         許容不能に阻害しないこと、(d) 並行時に response が別 request へ
         誤 binding されないこと(vllm_request_hash 照合)。
     専用 queue の要否は本試験の実測で判断(不合格なら W1B 前に必須化)。
CF-1 合成変更(throwaway)→ WAKE するか
CF-2 ゴミイベント → EXCEPTION(fail-closed)
CF-6 タイムアウト/空応答 → EXCEPTION
CF-7 control イベントを real lane として再生 → lane binding 不一致で拒否
CF-8 real イベントを null/control lane へ偽装 → source binding 不一致で拒否
CF-10 namespace 検査(GA-14 実装 gate): writer identity からの path 導出の
     決定性 + 他 writer namespace への書込試行の拒否(工程1 injection と
     重複するが W1A 合格条件としても明示)。
```

導出ビューの注意(GA-14 確認便): 横断 merge で ts を厳密な全順序として
扱わない(writer 内順序のみ保証。ビューは ts を表示・粗い整列にのみ使う)。

W1B 追加合格条件:

```
A-2  既知イベント列(過去実イベント採取、n=20)の分類測定(記述統計のみ)
A-4  MODEL_ROUTING_READY(watcher 役割)= A-2 + fail-closed 挙動合格
CF-3 層2 を経ない OBSERVATION 直接 emit → 単一 emit API + OS 層が拒否
CF-4 disposition 引き下げ・観測取り消し発行 → WS-7' が拒否
CF-5 層2 に集計済み CONSENSUS を騙らせる → 層3 再導出で不一致検出
CF-9 封入 metadata の Qwen 出力上書き試行 → 層3 が無視(WS-4)
```

---

## 13. re-battle(JREV-0011、W1B 終端)

DE-0426 準拠。想定攻撃面(v0.1 に GA 由来を追加):

```
- bounded context 迂回による嘘分類・嘘 severity
- WAKE 抑止(EDGE の死角)+ SWEEP 同時盲目化の試行
- lane 混線(CF-7/8 の変形)
- 封入 metadata の偽装経路探索(WS-4 の迂回)
- dedupe_key 衝突による観測握り潰し
```

adjudicator = GPT(Taka リレー)。

---

## 14. Claude Code 職責(参照のみ — 本書は制定しない、GA-6 裁定)

Taka 恒久裁定(2026-07-19): Claude Code の職責は重み跨ぎ監査のみ。
実装は 2DER 系(Qwen 経由)以外を全面禁止。Qwen 不能 = 構造的欠陥として
DE 起票し委譲で迂回しない。例外議論は再開しない。

```
本書内の操作規則: CC-W1 = W1 実装生成は Qwen worker のみ。Claude Code は
W1 成果物の重み跨ぎ監査を担当し、対象コードを直接修正しない(CA-1..4)。
推奨: 上記恒久裁定自体の正典化 DE を別途起票し、本書・handoff・メモリは
それを参照する(裁定内容の再審ではない。トレーサビリティ確保のみ)。
```

---

## 15. claim ceiling 語彙

```
許可: WATCHER_W1A_WAKE_PATH_TESTED / WAKE_ORPHAN_RECONCILIATION_BUILT /
      WATCHER_READONLY_DERIVED_STORE_APPEND_ONLY_VERIFIED /
      CONTROL_INJECTION_DETECTED_ON_TESTED_LANE /
      NULL_RATES_RECORDED(記述統計)
禁止: AMBIENT_MONITORING_PROVEN / WAKE_COMPLETENESS_MEASURED
      (EDGE↔SWEEP 突合の実装・実測前)/ CLAUDE_CODE_DEPENDENCY_REMOVED /
      WATCHER_CANNOT_BE_DECEIVED / ALL_CHANGE_PATHS_COVERED /
      NULL_SEPARATION_SIGNIFICANT(n 不足の間)
```

---

## 16. 別ITEM へ分離(GA-10 裁定)

```
ITEM-SL-A  最小構成 snapshot {repo, commit, path, sha256, file_count}
           → W1B に含める(W1b 相当)。
ITEM-SL-B  AST symbol table / import graph → 別ITEM。
ITEM-SL-C  意味層(Qwen 注釈による機能単位紐づけ)→ 別ITEM。
           Claude Code / 系の探索コスト削減効果を測定指標に持つ。
ITEM-URL   materialized view 自動更新(旧 DD-W6)→ W1 実測後の別裁定。
           watcher 発書込み class の要否もそこで扱う。
ITEM-LEDGER 帳簿ライフサイクル(決算・繰越・retention_class・
           POLICY/CLOSE worker 分離)→ item-ledger-design-v0.2.md
           (v0.1 を supersede)。LG-M1 相当(セグメント化 +
           retention_class の registry 封入)は M1 実装で充足済み
           (DE-0446 実測)。他は W1 実測後。
```

---

## 17. 部分解除 二段(GA 裁定採用 — DE-0439 案改)

```
LIFT-W1A(DE-0439a 案・v0.4 改 — **工程順序つき**):
  工程1(先行必須): emit_api 契約改版 = writer identity(WS-6'' 権限根
        込み)+ lane sealing(EV-W1'')+ writer 別名前空間(EV-W5)+
        PROTECTED_KEYS 拡張と供給路(WS-4'')。C 層中核変更につき
        契約テスト + **DE-0426 再戦(新概念: writer binding / lane 導出 /
        namespace 強制への novel attack)を W1A 本体着工前に完了**。
        injection 最低集合: 未登録 writer / 登録外 kind / 登録外 lane /
        caller lane 指定 / namespace 外 path / sealed-field 偽装(payload・
        nested・別名)。
  工程2: registry 改版 = WATCHER_* 5 kind(EV-W4)+ Watcher writer 登録
        (Taka 裁定イベントを根に)+ 不足 lane 追加。
  工程3: EDGE wake / 独立 SWEEP / RECONCILE(WATCHER_WAKE_ORPHAN)/
        ROLE-OBS 1系統 / 決定論ルーティング / control lane /
        Watcher unit(§3.2)。
  工程4: CF-1,2,6,7,8 + §12 W1A 合格判定。
  auto-refreeze(terminal = 工程1 再戦 BLOCKED + 工程4 合格)
LIFT-W1B(DE-0439b 案・W1A 実測レビュー後):
  ROLE-CLS N=3 / AUD-C・AUD-S(§9 契約駆動)/ null 二系統 /
  CC sampling(CA-1..4)/ ITEM-SL-A / 全 CF / JREV-0011 /
  auto-refreeze(terminal = §12 W1B 合格 + JREV-0011 クローズ)
除外(両段共通): W-R0 対象への書込み一切 / bridge・minter 変更 /
  materialized view 自動更新 / Watcher 観測を入力とする自動アクション
実装者: Qwen worker(ladder/budget 規律下)。CC = 監査のみ(§14)。
```

---

## 18. DD(改・GPT 裁定案を初期値として採用、最終は Taka)

```
DD-W1' 初期ゲート = §12 W1A 条件(重大見逃し0 / schema異常正常扱い0 /
       control recall 100% / null 誤警報は記録のみ / 軽微正答率参考値)
DD-W2  N=3 開始。5 への増強は同一重み内誤差の独立性実測後。
DD-W3' 最初の50件: CONSENSUS 20% + EXCEPTION 100% → 以後 CC 差分率で調整。
DD-W4' SWEEP 周期(hook 検査経路として命名変更)。初期 5〜15 分、
       運用負荷実測で決定。
DD-W5' bounded context 上限をイベント種別ごとに定義(diff / ledger append /
       handoff 変更で別値)。
DD-W6  廃止 → ITEM-URL へ移管(W1 では決めない)。
DD-W7  DP-1 dependency declaration の初期セット(Taka 承認必須、§9.2)。
```

---

## 付録A 裁定表(GA-1..10)

```
GA-1  ACCEPT      W-R0/R1/R2 三分類。snapshot append / atomic replace 限定。
GA-2  ACCEPT      EDGE/SWEEP/RECONCILE。WAKE_COMPLETENESS_MEASURED は
                  突合実装後のみ(ceiling へ反映)。
GA-3  ACCEPT      WS-1b OS 権限制御追加。+ V-W1(DE-0429 実制約の一次確認)。
GA-4  ACCEPT-MOD  agreement/disposition 分離・単調昇格・WS-7' severity 限定。
GA-5  ACCEPT      NULL-N/B 分割・4指標分離・記述統計限定(NG-8)。
GA-6  PARTIAL     ACCEPT: 本書は CC 職責を制定せず参照へ(§14)。正典化 DE
                  別途起票を推奨。CC の Run Ledger 直接書込み廃止(CA-3')。
                  REJECT: 恒久裁定内容の再審は行わない(Taka 既決。GPT 指摘
                  もトレーサビリティ要求であり再審要求ではないと解する)。
GA-7  ACCEPT      機械候補 enum + Qwen 注釈のみ。DP-1..3 前提条件化。
GA-8  ACCEPT      認証・冪等 schema。封入原則 WS-4(Qwen 自己申告排除)。
GA-9  ACCEPT      lane binding LN-1..3。CF-7/8。キュー混入の構造的遮断。
GA-10 ACCEPT      W1a/W1b 分割。AST・意味層は別ITEM(§16)。
総合  ACCEPT      三概念の分離(Watcher 純化 / 構成台帳別ITEM / CC 職責参照化)。
                  「系内感覚器」の位置づけを §0 に採用。
```

---

## 付録B v0.2 → v0.3 変更一覧(GA 裁定の内容変更なし)

```
B-1  §2 W-R1: 観測 store を C 帳簿(emit_api)へ確定(DE-0474 整合。
     旧 WA-1/WA-6)。第4の帳簿の新設禁止を明文化。
B-2  §3.1 新設: 層1/層3 の既存部品への実装写像(emit_api / systemd timer /
     git hook / workcell sandbox 転用 / status_views)。v0.3 改訂の主眼。
B-3  WS-4': 封印は emit_api sealed-field に一本化(旧 WA-4)。
     PROTECTED_KEYS の実測 gap(DE-0475)の解消を W1A スコープへ編入。
B-4  WS-6': dev-workcell 登録 → workcell_events.json registry 改版へ
     supersede(DE-0476 検出の非整合の解消。旧 WA-2/WA-3)。
     writer 外部登録(DE-0474 束縛1 初適用)を追加。
B-5  §7: 共通フィールドを emit_api 封筒との写像で再定義。sequence_no →
     segment_id + sequence_in_segment。EV-W4 で kind の W1A/W1B 段階導入、
     WAKE_ORPHAN → WATCHER_WAKE_ORPHAN 改称。
B-6  EV-W1': lane whitelist の実装先を emit_api に明記(旧 WA-5)。
B-7  §16 ITEM-LEDGER: 参照を v0.2 へ更新、LG-M1 は M1 実装で充足済みと記載。
B-8  §17 LIFT-W1A: (i) registry 改版 (ii) PROTECTED_KEYS 拡張 (vi) 新 writer
     injection を編入。terminal 条件に (vi) ALL-BLOCKED を追加。
B-9  watcher-layer-amendment-v0.2.1.md は本書に吸収され単独文書として廃止。
     WA-7(原文照合)は DE-0476 で完了済み。
```

---

## 付録C v0.3 → v0.4 変更一覧(GA-11..16 対応)

```
C-1  WS-6''(GA-11): writer 登録の権限根 = Taka 裁定イベント。CONTENT_SEAL
     (内容固定)と Taka 印(権限付与)の役割分離。循環遮断条項。
     writer_id は emit_api の新規契約能力として工程1 で導入。
C-2  WS-4''(GA-12): 封印を拒否+供給の両面で定義。writer identity は配備
     固定構成から、actor_instance は emit_api 生成、prompt_version は
     pinned hash を payload 外経路で。下流の同名/別名 field 読取禁止。
C-3  EV-W1''(GA-13): lane の caller 指定廃止・発生源からの決定論導出・
     writer→lane binding の registry 固定。payload から lane を全削除。
C-4  EV-W5(GA-14 CRITICAL): writer 別名前空間。chain の writer 間非共有。
     daemon 方式は実測条件付き棚上げ。【Taka veto 対象】
C-5  §3.1/§3.2(GA-15): sandbox「転用」を hardening 参考流用へ訂正、
     Watcher 専用 unit プロファイルを新設。
C-6  §3.1(GA-16): vLLM 共用の最小分離セット(caller identity / request-
     response binding / 専用 timeout)を W1A 必須化。queue/quota は飢餓
     実測条件付き別チケット。failure domain を明記。
C-7  §2(便-3 所見): 構成 snapshot の語法を「C 内の canonical observation
     record(対象状態の独立 SoR ではない)」へ精密化。
C-8  §17: LIFT-W1A を工程順序つきへ(emit_api 契約改版 + 再戦を先行必須)。
```
