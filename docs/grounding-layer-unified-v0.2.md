# Epistemic Grounding Layer — 統合設計書 v0.2 (Final)

対象システム: Distributed Research & Knowledge System (初期設計仕様 v0.1)
本書の系譜:
  v0.1 Grounding Layer (Claude) — Source/Observation/Claim/SearchRecordの4層と根拠契約
  GPT監査 — Knowledge Production Pipeline化
  ESDE Structural Extension v0.2 Draft (GPT) — 構造語彙の輸入
  本書 (Claude) — 上記の統合・矛盾解消・Phase分割可能化

本書は v0.1 Grounding Layer 設計書を **SUPERSEDE** する(単独で完結する)。
親文書(初期設計仕様 v0.1)の責任分界は変更しない。

---

## Part 0 — 適用原則

### 0.1 ESDE使用規律

```
AP-1  ESDE公理系は知識の正否判定に使用しない。
      公理との一致を理由に claim を VERIFIED にしてはならない。
      公理との一致を理由に設計判断を正当化してはならない。
AP-2  ESDE公理系は、設計上暗黙になっている構造(同定・連結・記述誤差・
      継続的関与・履歴・観察・軸形成・状態遷移・可逆性)を発見するための
      抽象語彙としてのみ使用した。
AP-3  経験的証拠・運用データと本設計原理が衝突した場合、証拠を優先する。
AP-4  de-ESDEテスト: 本書のすべての設計要素は、ESDEを読んだことのない
      エンジニアに対して、公理を一切参照せず工学的必要性のみで
      正当化できなければならない。各Partの冒頭に工学的根拠を明記する。
AP-5  ε×L≈K_sys 等の公理系の式を実装式・制御則にしない。
      剛直性制御(§18)は観測指標の提示に留め、自動最適化を禁止する。
```

### 0.2 親文書禁止条項の改訂記録

親文書 §15 は「ESDE固有設計へ寄せること」を禁止していた。
本書はこの条項を以下のように **明示的に改訂** する(黙示の逸脱ではない)。

```
旧: ESDE固有設計へ寄せることを禁止する。
新: ESDE公理を判定基準・制御則・正当化根拠として使用することを禁止する。
    構造発見の語彙としての使用は、AP-4(de-ESDEテスト)を通過する限り許可する。
```

改訂理由: v0.2 Draftで輸入された各構造(representation residual、三項文脈、
Provisional Axis、Reversibility Contract)は、いずれもESDEと独立に
工学的必要性が立証できたため。立証は各Part冒頭に記載する。

### 0.3 実装規模の規律

親文書原則「最初から汎用AI組織を作らない」を本書にも適用する。
本書のオブジェクトは以下の3層に分類され、各定義に **[P1-CORE] [P1-SCHEMA] [P2+]** を付す。

```
[P1-CORE]    Phase 1 で実装し運用するもの。
[P1-SCHEMA]  Phase 1 では schema/フィールドのみ確保し、生成・活用は後続Phase。
             (後からのスキーマ追加がマイグレーション地獄になるものだけをここに置く)
[P2+]        Phase 2 以降。Phase 1 の schema はこれらの追加を妨げない形にする。
```

判定基準: **「後付けできるか」**。導出値(centrality、distance、集計)は後付け可能
なので [P2+]。記録の一次フィールド(時間軸、run参照、residual)は後付け困難
なので最低 [P1-SCHEMA]。

---

## Part I — 概念モデル

### 1. オブジェクトモデル全景

工学的根拠: v0.1の4層(Source/Observation/Claim/SearchRecord)では、
(a) 取得と解釈の間の多段圧縮(normalization/extraction)の誤差が追跡できない、
(b) 「誰がいつ何をしたか」(Activity)が各オブジェクトに散在して監査できない、
(c) 対象の同一性(Entity)が文字列一致に依存する、
という3欠陥があった。これを解消する。

#### 1.1 知識生成パイプライン

```
                 EXTERNAL WORLD
                       │
                       ▼
                    ENTITY ──────────────── [P1-CORE] 同定の単位
                       │
                       ▼
                    SOURCE ──────────────── [P1-CORE] 情報源登録簿
                       │
              acquisition run ───────────── [P1-CORE] Run Ledger記録
                       │
                       ▼
               RAW OBSERVATION ──────────── [P1-CORE] immutable原本
                       │
             normalization run ──────────── [P1-CORE]
                       │
                       ▼
            NORMALIZED OBSERVATION ──────── [P1-CORE]
                       │
              extraction run ────────────── [P1-CORE]
                       │
                       ▼
              EVIDENCE FRAGMENT ─────────── [P1-CORE] 根拠の最小引用単位
                       │
              EVIDENCE RELATION ─────────── [P1-CORE] 型付き・文脈付きリンク
                       │
                       ▼
                 ATOMIC CLAIM ───────────── [P1-CORE]
                       │
               curation run ─────────────── [P1-CORE]
                       │
                       ▼
        (Global Knowledge DB 内の claim)
```

**重要: 「Grounded Knowledge」は独立オブジェクトではない。**
curation runを経てGlobal DBに受理されたclaimそのものを指す呼称であり、
別テーブル・別オブジェクトを作ることを禁止する(二重管理の禁止)。

#### 1.2 調査パイプライン(知識生成と独立)

```
        RESEARCH QUESTION / KNOWLEDGE GAP ── [P1-CORE] Gap Registry
                       │
                       ▼
                  SEARCH PLAN ───────────── [P1-CORE]
                       │
                  search run ────────────── [P1-CORE]
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   SEARCH RESULT SNAPSHOT      (observation取得へ)
          │
          ▼
              SEARCH CONCLUSION ─────────── [P1-CORE]
                       │
          (COMPLETED + no positive evidence)
                       ▼
                 ABSENCE CLAIM
```

#### 1.3 導出・拡張(将来)

```
   GROUNDED CLAIMS → derivation run → DERIVED KNOWLEDGE   [P2+] (§15.5)
   SCOPE AXIS REGISTRY                                     [P1-CORE(最小)/P2+(昇格自動化)]
   EPISTEMIC TASK PROFILE                                  [P1-CORE(2種のみ)]
   RUN LEDGER                                              [P1-CORE]
```

#### 1.4 横断原則

```
OM-1  すべてのオブジェクトは一意IDを持つ(Identity)。
OM-2  すべてのオブジェクト生成・状態変更はrun_idを刻む(Activity第三項)。
      「いつの間にか存在するレコード」を禁止する。
OM-3  すべてのリンクは型を持ち、リンク自体がprovenanceを持つ(§7)。
OM-4  すべてのclaimはrepresentation_residualを持ち得る(§8.4)。
OM-5  すべての検証は{時点, scope, validation_mode}に束縛される(§13)。
OM-6  すべての状態遷移はevent logから逆走可能である(§19)。
```

### 2. 発話クラスと Grounding Contract

工学的根拠: RDの出力から Unsupported Claim Rate を機械測定するには、
発話が根拠参照を持つ構造化オブジェクトである必要がある。v0.1から維持し、
GC-7(残差保護)とGC-8(汚染伝播)を追加する。

#### 2.1 発話クラス(v0.1から変更なし)

| class | 定義 | 根拠要件 |
|---|---|---|
| `FACT` | 外部世界についての事実言明 | grounds に claim_id 必須 + min_ground_status |
| `INFERENCE` | 複数FACTからの導出 | grounds + inference_rule 必須 |
| `HYPOTHESIS` | 未検証の仮説 | ラベル明示必須 |
| `DESIGN_CHOICE` | 選択・提案(価値判断) | 依拠FACT/INFERENCEの参照を推奨 |

#### 2.2 Grounding Contract(全規則・確定版)

```
GC-1  class=FACT の assertion は grounds が空であってはならない。
GC-2  FACT の grounds が参照する claim の status は、当該taskの
      Epistemic Profile(§12)が規定する min_ground_status 以上であること。
GC-3  INFERENCE は grounds と inference_rule(前提から結論が出る理由の
      1〜3文)の両方を持つこと。
GC-4  grounds の claim_id は Global DB または当該taskのTask Evidenceに
      実在すること(dangling reference 禁止)。
GC-5  違反 assertion は class=UNSUPPORTED として検証器が自動分類し、
      resolution に含める場合は unsupported_assumptions 節へ隔離する。
GC-6  自然文 resolution 内の技術的言明は assertion_id への参照を持つ。
      実装方式は DD-3(assertion からのテンプレート生成を推奨)。
GC-7  [残差保護] FACT assertion は、grounds claim の representation_residual.
      known_omissions に列挙された axis 次元について、新たな事実を
      追加してはならない。
      機械検証: assertion の scope_echo の次元キー集合と、grounds claim の
      known_omissions の次元キー集合の交差が空でない場合、当該次元を
      支持する別の grounds が存在しなければ lint エラー。
      例: grounds が「NVFP4はSM120対応(known_omissions: operational_stability)」
          のとき「NVFP4はRTX5090で安定動作する」というFACTは、安定性を
          直接支持する別claimなしには生成不能。
GC-8  [汚染伝播] taint フラグ(§16.2)が立った evidence fragment のみを
      根拠とする FACT は、Curator の明示的解除判断なしに生成不能。
```

GC-1〜GC-5, GC-7, GC-8 の検証はコードで実装する [P1-CORE]。
GC-7 が機械検証可能なのは known_omissions を axis キーで記録するため(§8.4)。
自由記述の residual note は検証対象外の補助情報とする。

#### 2.3 assertion object(確定スキーマ)

```json
{
  "assertion_id": "A-0007",
  "class": "FACT",
  "text": "vLLM >= 0.11 は SM120 上で NVFP4 重みの推論をサポートする",
  "grounds": ["C-000142", "TE-00128-c003"],
  "grounds_snapshot": [
    {"claim_id": "C-000142", "revision": 2, "status": "VERIFIED",
     "validation_mode": "DECLARED", "freshness": "FRESH"}
  ],
  "inference_rule": null,
  "scope_echo": {"runtime": "vllm", "gpu_arch": "sm120", "quant": "nvfp4"},
  "residual_ack": ["operational_stability"],
  "created_by_run": "RUN-RD-00311"
}
```

- `grounds_snapshot`: 参照時点のclaim状態の凍結(§15.3)。validation_modeを含む。
- `residual_ack`: grounds の known_omissions のうち、この assertion が
  「言及しないと自覚している」次元。GC-7 lint の突合対象。
- `created_by_run`: OM-2 の適用。

---

## Part II — データオブジェクト詳細

### 3. Entity Registry [P1-CORE]

工学的根拠: 「Qwen3-Coder-Next」「Qwen/Qwen3-Coder-Next」「Qwen3NextForCausalLM」
の文字列不一致がclaim重複・見落としを生む。同定は文字列一致に依存させない。

```json
{
  "entity_id": "ENT-qwen3-coder-next",
  "entity_type": "MODEL",
  "canonical_name": "Qwen3-Coder-Next",
  "aliases": [
    {"alias": "Qwen/Qwen3-Coder-Next", "created_by_run": "RUN-CUR-00021"}
  ],
  "identifiers": {"huggingface_repo": "Qwen/Qwen3-Coder-Next"},
  "related_entities": [
    {"entity_id": "ENT-qwen3-next-arch", "relation": "IMPLEMENTS_ARCHITECTURE",
     "identity_status": "IDENTICAL", "created_by_run": "RUN-CUR-00021"}
  ]
}
```

規則:

```
EN-1  claim の scope 内で entity を指す値は entity_id を用いる。
      entity_id 未登録の対象は、Curator が登録してから claim 化する。
EN-2  identity_status の値域: IDENTICAL / LIKELY_SAME / RELATED /
      DISTINCT / IDENTITY_UNKNOWN。
      同一性が確定しない場合 merge しない。LIKELY_SAME のまま保持してよい。
EN-3  Identity の曖昧さを claim の scope 内へ隠してはならない。
      (曖昧なまま claim 化する場合、scope_uncertainty へ反映する)
EN-4  alias 登録・identity link 生成もそれ自体が主張である。
      必ず created_by_run を持ち、根拠が必要な場合は observation を参照する。
EN-5  entity merge は可逆操作として実装する(§19 RC-5 準用)。
      merge event を保持し、分離(un-merge)を再構成可能にする。
EN-6  entity_type の初期語彙: MODEL / ARCHITECTURE / RUNTIME / LIBRARY /
      HARDWARE / SPEC / ORGANIZATION / DATASET。追加は Curator 権限。
```

Phase 1 では Entity Registry の運用を軽量に保つ:
task 中に RD が発見した未登録 entity は provisional entity として
Task Evidence 内に置き、claim 昇格時に Curator が正式登録する。

### 4. Source(情報源登録簿) [P1-CORE]

v0.1 §2.3 を維持。変更点のみ記す。

```
SO-1  locator の対象が entity_id と関連する場合、covers_entities を持つ。
SO-2  authority_scope は entity_id / axis 次元で記述する(自由記述禁止)。
SO-3  source 間の転載・引用関係は relation(MIRRORS / CITES)として保持し(§7)、
      独立性判定(ST-2)の入力とする。
```

source class 値域は v0.1 のまま: PRIMARY / SECONDARY / COMMUNITY / GENERATED。
GENERATED の単独根拠禁止も維持。

### 5. Run Ledger [P1-CORE]

工学的根拠: 「Source と Observation だけでは、いつ・誰が・どの方法で・何と
比較したかが顕在化しない」。取得・正規化・抽出・審査・検索・移行のすべての
Activity を第三項として記録しなければ、時間変化の再構成(§17)も影響追跡(§15.4)も
成立しない。

```json
{
  "run_id": "RUN-RD-00311",
  "actor": "rd",
  "actor_instance": "rd-qwen36-a3b-01",
  "activity_type": "SEARCH",
  "task_id": "TASK-00128",
  "inputs": ["SPLAN-0042"],
  "outputs": ["SNAP-0091", "OBS-2026-07-04-00871"],
  "started_at": "2026-07-04T04:00:00Z",
  "ended_at": "2026-07-04T04:11:00Z",
  "irreversibility_class": "REPLAYABLE",
  "tool_versions": {"fetcher": "1.2.0", "normalizer": "0.9.1"},
  "status": "COMPLETED",
  "notes": null
}
```

```
RL-1  activity_type 初期語彙: ACQUISITION / NORMALIZATION / EXTRACTION /
      SEARCH / CURATION / PROMOTION / RETRACTION / MIGRATION / REVERIFICATION。
RL-2  irreversibility_class: REVERSIBLE / REPLAYABLE / COMPENSATABLE /
      IRREVERSIBLE。IRREVERSIBLE な外部状態変化(情報源の消滅等)を検出した
      run は、関連 observation の保存優先度を上げる。
RL-3  Run Ledger は append-only。runの削除・改変禁止。
RL-4  LLM を用いた run は model / prompt version を tool_versions に記録する。
      (extraction・curation の解釈誤差を後から層別監査するため)
```

RL-4 は ε 対応の実務形である: 「LLM解釈」も圧縮段の一つであり、
どのモデル・どのプロンプト版が解釈したかを残さなければ誤差の所在を追えない。

### 6. Observation と Evidence Fragment [P1-CORE]

工学的根拠: World → Source表現 → 取得 → 正規化 → 抜粋 → LLM解釈 → Claim の
各段に誤差がある。v0.1 は取得(Observation)しか一次記録しなかった。
正規化と抽出を run として分離し、原本からの再導出を可能にする。

#### 6.1 Raw Observation(v0.1 Observation を改称・immutable)

v0.1 §2.4 のスキーマを維持し、以下を追加:

```json
{
  "observation_id": "OBS-...",
  "taint_flags": [],
  "acquired_by_run": "RUN-..."
}
```

#### 6.2 Normalized Observation

```json
{
  "norm_obs_id": "NOBS-0071",
  "raw_observation_id": "OBS-...",
  "normalized_by_run": "RUN-NORM-0033",
  "normalizer_version": "0.9.1",
  "content_ref": "blob://normalized/NOBS-0071",
  "content_hash": "sha256:..."
}
```

```
NO-1  Raw は不変。Normalized は normalization run と version を保持し、
      normalizer 更新時は新 NOBS を生成する(上書き禁止)。
```

#### 6.3 Evidence Fragment(根拠の最小引用単位)

```json
{
  "fragment_id": "EFRAG-0012",
  "norm_obs_id": "NOBS-0071",
  "selector": {"type": "section", "value": "quantization#nvfp4"},
  "excerpt": "NVFP4 quantized checkpoints are supported on ...",
  "extracted_by_run": "RUN-EXT-0044",
  "extraction_method": "llm",
  "taint_flags": [],
  "mentions_entities": ["ENT-vllm", "ENT-sm120"]
}
```

```
EF-1  claim の根拠参照は fragment 単位とする(observation 全体への参照を廃止)。
      根拠箇所を特定できない「文書ごと支持」を禁止する。
EF-2  fragment は norm_obs への selector を必ず持ち、原文脈へ遡れること。
EF-3  extraction_method=llm の場合、RL-4 により解釈主体が特定できること。
EF-4  taint_flags は raw observation から継承し、追加検出分を加算する(§16.2)。
```

### 7. Relation(型付き・第一級・文脈付き) [P1-CORE]

工学的根拠: (a) 「Evidence が存在する」と「Evidence が Claim を支持する」は
別の主張であり、後者は推論結果なので provenance が要る。
(b) 同一 Evidence でも task の問いによって支持関係が変わる(下記 7.3)。
(c) 転載検出(MIRRORS)なしに独立性(ST-2)を機械判定できない。

#### 7.1 スキーマ

```json
{
  "relation_id": "REL-00881",
  "from_id": "EFRAG-0012",
  "to_id": "C-000142",
  "relation_type": "SUPPORTS",
  "context": {
    "epistemic_profile_id": "EP-TECH-CAPABILITY",
    "question": "checkpoint loading support",
    "scope": {"gpu_arch": "sm120"}
  },
  "created_by_run": "RUN-CUR-00082",
  "valid_from": "2026-07-04",
  "valid_until": null
}
```

#### 7.2 relation_type 語彙管理

**Phase 1 語彙(8種・固定):**

```
SUPPORTS / REFUTES / QUALIFIES / MIRRORS / CITES /
SUPERSEDES / CONFLICTS_WITH / DERIVED_FROM
```

**Reserved(schema上は許容・Phase 1では生成しない):**

```
LIMITS_SCOPE / EXPANDS_SCOPE / EXCEPTION / REPRODUCES /
FAILS_TO_REPRODUCE / CORRECTS / QUOTES / DEPENDS_ON / INVALIDATES
```

```
RE-1  relation 語彙の追加・reservedの有効化は axis と同じ昇格プロセス(§11)。
      理由: 語彙が多いほど Curator(35B)の誤用が増え、relation 自体が
      汚染源になる。必要が繰り返し観測されてから有効化する。
RE-2  evidence→claim の relation(SUPPORTS/REFUTES/QUALIFIES)の Global DB
      への生成は curation run のみ。RD は task namespace 内でのみ生成可。
RE-3  relation は context を必須とする(7.3)。
RE-4  relation の削除禁止。無効化は valid_until 設定で行う(履歴保持)。
```

#### 7.3 三項文脈の必須化

同一 Evidence は問いによって意味が変わる:

```
公式文書「Model X supports NVFP4」
  × 問い「checkpointはロード可能か」        → SUPPORTS
  × 問い「dual RTX5090で48時間安定稼働するか」 → 支持しない(不十分)
```

evidence–claim の二項だけを保存すると前者の SUPPORTS が後者の文脈へ漏れる。
よって relation は Evidence–Claim–Context の三項として保存する(RE-3)。
context の実体は epistemic_profile_id + question + scope である。

#### 7.4 独立性の機械化(ST-2 の実装先)

```
IN-1  2つの evidence fragment が「独立」とは:
      (a) publisher が異なり、かつ
      (b) 両者の source 間・observation 間に MIRRORS / CITES relation が
          存在しない、かつ
      (c) 転載検出 run(内容類似スキャン)が実行済みであること。
IN-2  (c) 未実行の場合、独立性は「推定独立(PRESUMED_INDEPENDENT)」とし、
      「確認独立(CONFIRMED_INDEPENDENT)」と区別する。
      CORROBORATED 判定(ST-2)には推定独立で足りるが、その旨を
      decision record に記す。EP-SAFETY 系 profile は確認独立を要求できる。
IN-3  MIRRORS 検出は claim の status を自動変更しない。Curator の
      再審査 queue へ送る(CORROBORATED → REPORTED への降格候補)。
```

#### 7.5 連結密度の観測 [P2+]

```
LD-1  各 claim について導出する(保存しない):
      incoming_support_count / incoming_refutation_count /
      dependency_count / derived_dependents / impact_radius。
LD-2  dependency centrality が高い claim を Critical Claim とし、
      再検証優先度を上げる(§17 TM-3 の queue で優先)。
LD-3  過剰連結は誤り撤回の影響半径を拡大する。連結数の最大化を
      DB 品質指標にしない(§18)。
```

### 8. Claim [P1-CORE]

#### 8.1 確定スキーマ

```json
{
  "claim_id": "C-000142",
  "revision": 2,
  "claim_key": "capability:supports(gpu_arch=ENT-sm120,quant=nvfp4,runtime=ENT-vllm)",
  "claim_type": "CAPABILITY",
  "polarity": "POSITIVE",
  "statement": "vLLM 0.11以降はSM120上でNVFP4量子化モデルの推論をサポートする",
  "subject_entities": ["ENT-vllm"],
  "scope": {
    "runtime": "ENT-vllm",
    "runtime_version": ">=0.11",
    "gpu_arch": "ENT-sm120",
    "quant": "nvfp4"
  },
  "status": "VERIFIED",
  "validation_mode": "DECLARED",
  "evidence_relations": ["REL-00881", "REL-00902"],
  "search_conclusions": [],
  "representation_residual": {
    "known_omissions": ["operational_stability", "kernel_backend"],
    "unresolved_conditions": ["batch_size依存性は文書に記載なし"],
    "scope_uncertainty": "LOW",
    "extraction_loss_note": "公式docはsupport宣言のみで運用安定性に言及しない"
  },
  "temporal": {
    "event_time": "2026-06-10",
    "publication_time": "2026-06-20",
    "observation_time": "2026-07-04",
    "knowledge_time": "2026-07-06",
    "valid_from": "2026-06-20",
    "valid_from_basis": "publication_time",
    "valid_until": null,
    "last_verified": "2026-07-04"
  },
  "volatility_class": "RELEASE_FAST",
  "derivation": {"origin": "task", "origin_ref": "TASK-00128",
                 "curator_decision_ref": "CDEC-00455"},
  "supersedes": ["C-000091"],
  "superseded_by": null,
  "conflicts_with": [],
  "taint_flags": [],
  "interaction_history_ref": "IH-C-000142",
  "retraction": null
}
```

claim_type / polarity の値域は v0.1 §2.5 を維持
(CAPABILITY / VERSION_FACT / COMPATIBILITY / MEASUREMENT / PROCEDURE / SPEC / ABSENCE、
POSITIVE / NEGATIVE / ABSENCE)。NEGATIVE の PRIMARY 必須も維持。

#### 8.2 Atomic Claim Contract

```
AC-1  claim は原則として単一主語・単一述語・単一対象関係を持つ。
AC-2  AND / OR を用いた複合命題は原則分割する。
AC-3  複数 scope condition の結合は、Evidence がその結合を直接述べる場合のみ
      単一 claim として許可する。
AC-4  複数 Atomic Claim の組合せの帰結は claim ではなく INFERENCE assertion で
      表現する(Global 昇格禁止 PR-2 と整合)。
AC-5  分割で意味が失われる場合のみ COMPOSITE claim を許可する。
      component_claim_ids 必須。component が SUPERSEDED / RETRACTED /
      CONFLICT になった場合、COMPOSITE は自動的に再評価 queue へ載る。
目的: claim 数の削減ではなく、撤回可能範囲の局所化。
```

#### 8.3 Validation Mode

工学的根拠: 「VERIFIED」一語では「公式がそう宣言した」と「動作を再現した」を
区別できない。status(証拠の強さ)と直交する軸として検証様式を持つ。

```
DECLARED    公表主体がそう宣言したことを一次確認
SPECIFIED   正式仕様・規格に規定
OBSERVED    動作を直接観測
MEASURED    条件付き測定済み
REPRODUCED  規定条件または独立 run で再現
```

```
VM-1  validation_mode 間に固定の優劣順位を置かない。
      必要な mode は task の Epistemic Profile が規定する(§12)。
      例: API仕様の問いには SPECIFIED、稼働安定性の問いには REPRODUCED。
VM-2  status 判定(ST-1〜ST-5)と validation_mode 判定は独立に行う。
      VERIFIED + DECLARED は「宣言の存在は確実」であって
      「動作の確実」ではない。RD はこれを FACT の scope_echo に反映する。
```

#### 8.4 Representation Residual

工学的根拠: Observation → Claim は圧縮であり、記述されなかった情報が必ず残る。
通常の RAG は「NVIDIA版NVFP4は23.5GB」という claim から「RTX5090 32GBに載る」へ
ジャンプする。runtime overhead / KV cache / CUDA graph workspace が未記述である
ことを構造として残せば、このジャンプを GC-7 で機械的に遮断できる。

```
RR-1  known_omissions は Axis Registry(§11)の次元キーで記録する。
      自由記述の省略列挙を禁止する(GC-7 の機械検証可能性のため)。
      軸に存在しない省略は extraction_loss_note(自由記述・検証対象外)へ書き、
      頻出するなら Provisional Axis 候補として挙げる(§11)。
RR-2  known_omissions の網羅を要求しない。residual は開世界であり、
      「気づいた省略」の記録である。網羅性を Curator 審査基準にしない。
RR-3  residual の存在を低品質 claim の証拠としない。
      「何を言っていないかが分かっている claim」は「全部分かったことに
      なっている claim」より安全である。
RR-4  Curator は Gate 4 で「statement が evidence の言っていない次元へ
      一般化していないか」を審査し、一般化を検出したら scope を縮めるか
      known_omissions へ移す(REJECT ではなく矯正を優先)。
```

### 9. Knowledge Gap Registry [P1-CORE]

工学的根拠: v0.1 は未知を UNKNOWN placeholder として Claim Registry 内に置いたが、
「世界についての言明」と「我々が答えを持たない問い」は別物であり、
混在させると ABSENCE(調査したが無かった)と UNKNOWN(未調査)の区別が再び曖昧になる。

```json
{
  "gap_id": "KGAP-00129",
  "question": "現行vLLM NVFP4パスはdual RTX5090の持続agent負荷で安定か",
  "origin_task_id": "TASK-00128",
  "parent_gap_id": "KGAP-00120",
  "required_for": ["REQ-005"],
  "status": "OPEN",
  "epistemic_profile_id": "EP-TECH-PERFORMANCE",
  "search_plans": [],
  "resolved_by_claims": [],
  "created_by_run": "RUN-RD-00301"
}
```

```
KG-1  status 値域: OPEN / PLANNED / RESEARCHING / PARTIALLY_RESOLVED /
      RESOLVED / NOT_FOUND / DROPPED / SUPERSEDED。
KG-2  Gap は claim ではない。Claim Registry から分離して保持する。
      v0.1 の「UNKNOWN placeholder claim」は本 Registry へ移管し廃止する。
KG-3  gap lineage: 調査が新しい未知を生むことを parent_gap_id で保持する。
      「最初に何を知らなかったか」に加えて「調査によって何が新しく
      分からなくなったか」を記録する(Research Coverage の補助指標)。
KG-4  RD の requirement decomposition の出力は gap 群として登録される。
      task 終了時、未消化 gap は OPEN のまま残る(Post-hoc Missing
      Information 監査の突合対象)。
```

### 10. Search 構造 [P1-CORE]

工学的根拠: v0.1 の SearchRecord は「計画・実行・結果・結論」を1オブジェクトに
潰していたため、(a) 検索系の失敗(rate limit / truncation)と「無かった」の区別、
(b) 計画済み未実行の検出、ができない。4分割する。**SearchRecord は廃止。**

```
SearchPlan        何を確認する予定か(対象gap、確認すべきsource domain、query方針)
SearchRun         実際に行った行為(Run Ledger上のrun)
SearchResultSnapshot  検索系が返したものの凍結(結果リスト+hash)
SearchConclusion  この計画を完了できたか
```

#### 10.1 SearchConclusion

```json
{
  "conclusion_id": "SCON-0088",
  "search_plan_id": "SPLAN-0042",
  "runs": ["RUN-RD-00311", "RUN-RD-00312"],
  "coverage_profile_id": "COV-TECH-STANDARD",
  "coverage_result": {
    "required_domains_checked": true,
    "unchecked": [],
    "languages_covered": ["en"],
    "languages_uncovered": ["zh"]
  },
  "status": "COMPLETED",
  "outcome": "NO_POSITIVE_EVIDENCE",
  "concluded_at": "2026-07-04T05:00:00Z"
}
```

```
SC-1  status 値域: COMPLETED / SEARCH_INCOMPLETE。
      SEARCH_INCOMPLETE の下位理由: PARTIAL / RATE_LIMITED /
      PROVIDER_TRUNCATED / AUTH_SCOPE_LIMITED / FAILED。
SC-2  ABSENCE claim を生成できるのは status=COMPLETED かつ
      outcome=NO_POSITIVE_EVIDENCE の SearchConclusion のみ。
      SEARCH_INCOMPLETE からの NOT_FOUND 生成を禁止する。
      (検索の失敗を世界の不在と混同しない)
SC-3  ABSENCE claim の search_conclusions は当該 conclusion_id を参照する
      (v0.1 AB-1 の参照先を SearchRecord から SearchConclusion へ変更)。
```

#### 10.2 Search Coverage Profile [P1-CORE]

工学的根拠: 「required source domains checked」の required を未定義のまま
残すと、NOT_FOUND 生成条件が RD の主観に戻る(v0.1 以前への退行)。

```json
{
  "coverage_profile_id": "COV-TECH-STANDARD",
  "domain": "TECHNICAL",
  "required_source_classes": ["PRIMARY"],
  "required_source_kinds": ["official_documentation", "release_notes",
                             "official_repository"],
  "required_languages": ["en"],
  "recommended_languages": ["zh"],
  "min_query_variants": 3
}
```

```
CP-1  SearchPlan は coverage_profile_id を必ず参照する。
      profile は登録制。RD が ad hoc に coverage を定義することを禁止する。
CP-2  ABSENCE claim の再利用判定(v0.1 AB-5)は coverage_result の差分で行う:
      新 task の coverage 要求が既存 ABSENCE の coverage_result に包含される
      なら再調査不要。超過分(例: languages_uncovered の zh)のみ追加調査する。
CP-3  多言語 coverage の要否は DD-11 のまま未決とするが、
      coverage_result.languages_uncovered により「未調査言語圏」は
      常に明示される(暗黙の英語圏限定を禁止する)。
```

#### 10.3 ABSENCE の時間判定(見落としと世界変化の分離)

```
SA-1  ABSENCE claim と矛盾する positive observation が出現した場合、
      publication_time と当時の search run の実行時刻を比較する:
      (a) search_time < publication_time
          → 世界の正常な変化。ABSENCE は SUPERSEDED(v0.1 AB-4 維持)。
      (b) publication_time < search_time かつ当時の coverage profile が
          当該 source を required としていた
          → SEARCH_COVERAGE_FAILURE。ABSENCE は RETRACTED 候補とし、
            coverage profile または検索手順の欠陥として記録する。
SA-2  (a) と (b) は別の指標に計上する。(a) は世界の速度、(b) は
      調査品質の欠陥であり、False Absence Rate に入るのは (b) のみ。
```

### 11. Scope Axis Registry [P1-CORE(最小)]

工学的根拠: scope 語彙を最初から完全設計することは不可能(技術領域だけでも
kernel_backend / KV dtype / attention_backend 等が後から出現し、別領域では
jurisdiction / invoice_class 等になる)。一方、自由記述次元は claim_key の
重複検出(§14.2)を破壊する。固定 schema と free-form chaos の中間を取る。

```json
{
  "axis_id": "AX-kernel-backend",
  "name": "kernel_backend",
  "status": "PROVISIONAL",
  "value_type": "string",
  "origin": {"tasks": ["TASK-00128", "TASK-00131"]},
  "usage_count": 7,
  "distinct_entities": 3,
  "created_by_run": "RUN-CUR-00090"
}
```

```
AX-1  status 値域: PROVISIONAL / ESTABLISHED / DEPRECATED / MERGED / REBOOTED。
AX-2  claim_key の生成には ESTABLISHED axis のみを使用する。
      PROVISIONAL axis は scope 本体には書けるが key には入らない
      (key の安定性を保つため)。
AX-3  RD は Global Schema へ axis を直接追加できない。task 内で必要になった
      新次元は provisional 記法で scope に書き、昇格候補として Curator へ送る。
AX-4  昇格条件: 複数 task または複数 claim cluster で同一次元の必要が
      繰り返し観測されたこと。閾値は DD-13。
AX-5  Axis Reboot: 既存軸の分割が必要になった場合(例: support →
      declared_support / operational_support)、AXIS_REBOOT event を発行する。
      migration run を必須とし、旧 schema での view を再構成可能に保つ(RC-6)。
      Reboot は失敗ではない。ただし頻発は schema instability として計測する。
AX-6  初期 ESTABLISHED 軸(Phase 1): runtime / runtime_version / gpu_arch /
      quant / model / os / driver_version / cuda_version / kv_dtype。
      初期辞書の確定は DD-4。
```

### 12. Epistemic Task Profile [P1-CORE(2種のみ)]

工学的根拠: grounding の厳格度を系全体で一つに固定すると、緩ければ DB 汚染、
硬ければ UNKNOWN 飽和で問題解決不能になる。要求水準は task の性質(リスク・
時間感度)の関数であり、task 単位の契約として明示する。

```json
{
  "epistemic_profile_id": "EP-TECH-STANDARD",
  "domain": "TECHNICAL_CONFIGURATION",
  "risk_tier": "MEDIUM",
  "min_ground_status": "TASK_REPORTED",
  "required_validation_modes": {"default": ["DECLARED"],
                                 "stability_questions": ["REPRODUCED"]},
  "evidence_policy": {"primary_required": false,
                      "community_measurement_allowed": true,
                      "independence": "PRESUMED_INDEPENDENT"},
  "absence_policy": {"coverage_profile_id": "COV-TECH-STANDARD"},
  "freshness_requirement": "HIGH"
}
```

```
EP-1  profile は登録制とし、Phase 1 は 2種のみ:
      EP-TECH-STANDARD(既定) / EP-TECH-STRICT(primary_required=true,
      independence=CONFIRMED_INDEPENDENT)。
EP-2  profile の付与は Manager のコード(task 分類規則)が行う。
      RD による自己選択を禁止する(緩い profile への逃げ道を塞ぐ)。
EP-3  task 途中の profile 変更は event として記録し、Manager の
      escalation 判断事項とする(無断緩和の禁止)。
EP-4  profile は真理の基準ではない。「今回何を判断するために、どの程度の
      根拠を必要とするか」の契約である。同一 claim でも task により
      利用可能性が異なる(§7.3 と同根)。
```

---

## Part III — 動作規則

### 13. 状態モデル(確定版)

status 値域・判定規則(ST-1〜ST-5)・Task Evidence 側状態・遷移権限表は
v0.1 §3 を維持する。変更点のみ:

```
ST-2' 「独立」の判定を IN-1/IN-2(§7.4)へ委譲する。
ST-6  status とは独立に validation_mode を必ず併記する(VM-1/VM-2)。
ST-7  UNKNOWN placeholder claim を廃止し、Gap Registry(§9)へ移管する。
      claim の status から UNKNOWN を削除する。
      (未調査は「claim が無い + gap が OPEN」で表現される)
```

改訂後の status 値域:

```
VERIFIED / CORROBORATED / REPORTED / PARTIAL / CONFLICT /
NOT_FOUND(ABSENCE専用) / DEPRECATED / SUPERSEDED / RETRACTED
```

### 14. Curator 検証フロー(確定版)

v0.1 §8 のゲート構成を維持し、以下を改訂・追加する。

```
Gate 0  schema validation                        [code]
Gate 1  evidence integrity + taint検査            [code]
        fragment実在, hash一致, GENERATED単独根拠検出,
        taint_flags の伝播確認(GC-8)
Gate 2  duplicate / conflict candidates           [code + vector index]
        claim_key(ESTABLISHED軸のみ) → scope重なり → 時間重なり → 両立性
Gate 3  source authority + coverage検査           [code]
        authority_scope整合(entity/axis単位),
        ABSENCE候補は SearchConclusion の COMPLETED 検査(SC-2)
Gate 4  semantic judgment                         [LLM: Curator instance]
        追加審査項目:
        - excerpt は statement を支持するか(従来)
        - scope は evidence の範囲を超えていないか(従来 + RR-4 矯正)
        - validation_mode の判定(VM-1)
        - representation_residual の妥当性(RR-2: 網羅は求めない)
        - relation_type の選択(Phase 1 の8種から)
        - 三項 context の記入(RE-3)
Gate 5  decision validation + write               [code]
        ST/VM/RE/AC 規則との整合検査, event log 追記,
        relation生成, claim write, decision record 保存
```

```
CU-1〜CU-4 は v0.1 を維持(LLMのDB直接アクセス禁止 / 整合検査落ちはDEFER /
DEFER滞留上限 / decision record の append-only 全保存)。
CU-5  審査単位は claim_key クラスタ(v0.1 §8.3 維持)。加えて、同一 entity に
      関する candidate は entity 単位でまとめて文脈添付する。
CU-6  Curator は「正しさを与える存在」ではなく、Evidence と Claim の間の
      関係を記録する観察機構である。Curator decision は claim と同格の
      一次記録であり、Curator 自体の品質(誤ACCEPT率・reject率の偏り)を
      decision record から監査可能に保つ。
```

### 15. 昇格・撤回・影響追跡

#### 15.1 昇格(v0.1 §9.1 維持 + 改訂)

```
PR-1  昇格指名可能: TASK_VERIFIED / TASK_REPORTED / TASK_CONFLICT /
      COMPLETED な SearchConclusion に基づく ABSENCE。
PR-2  INFERENCE の結論の claim 昇格を原則禁止(維持)。将来の緩和は
      Derived Knowledge namespace(15.5)経由でのみ行う。
PR-3  FAILED / ESCALATE 終了 task の observation / SearchConclusion も
      昇格候補にできる(維持)。
PR-4  origin task_id 刻印(維持)。
PR-5  昇格時、task-local の evidence relation は Curator が再判定して
      Global relation を生成し直す(task の三項 context を引き継ぐ)。
```

#### 15.2 Task Evidence の寿命(v0.1 §9.2 維持)

保存継続・retrieval 対象外・監査用。保存上限は DD-12。

#### 15.3 Global 参照 snapshot(v0.1 §9.3 維持 + validation_mode 追加)

snapshot は {claim_id, revision, status, validation_mode, freshness} とする。

#### 15.4 Retraction と影響追跡(v0.1 §9.4 維持 + relation graph 化)

```
RT-1〜RT-4 維持。
RT-5  impact_scan は relation graph(DERIVED_FROM / COMPOSITE component /
      grounds_snapshot)の逆走で機械生成する。event log(LC-5)と併用。
RT-6  Critical Claim(LD-2)の retraction は Manager への即時通知とする。
RT-7  Retraction の存在自体を Curator の失敗としない。計測するのは
      time_to_detect_error / impact_radius / repeat_error_rate である。
```

#### 15.5 Derived Knowledge namespace [P2+]

```
DK-1  Phase 1 では実装しない。schema 予約のみ行う(premises /
      derivation_type / derivation_rule / status)。
DK-2  Derived Knowledge は Grounded Claim と同格に扱わない。
      「記憶された推論」であり外部世界の観測ではない。retrieval 時は
      必ず区別可能なラベルを付す。
DK-3  前提 claim が SUPERSEDED / RETRACTED / CONFLICT となった場合、
      derived claim を自動的に再評価 queue へ載せる(AC-5 と同機構)。
```

### 16. 強制機構

#### 16.1 内部知識の遮断(v0.1 §10 維持)

型システム(claim は fragment/conclusion なしに存在できない) → 検証器(GC lint)
→ ツールラッパー(調査は必ず observation/run を生成) → プロンプト、の4層。
調査領域推定の漏れが残存リスクであることの明記も維持
(Gap lineage KG-3 が新たな補助検出手段になる)。

#### 16.2 Evidence Trust Boundary [P1-CORE]

工学的根拠: 外部 observation は攻撃面である。prompt injection 防御を
「LLMに無視しろと指示する」だけに依存しない。

```
ETB-1  observation の内容は data であり instruction ではない。
ETB-2  observation 内容からのツール起動を構造上不可能にする
       (RD/Curator への evidence 受け渡しは構造化フィールドに隔離)。
ETB-3  observation 内容によるシステムポリシー変更を禁止する。
ETB-4  取得時に hidden text / zero-width / instruction-like pattern を
       スキャンし、taint_flags を付す。
ETB-5  taint は Raw → Normalized → Fragment → Claim へ伝播する(EF-4)。
ETB-6  taint を自動破棄理由にしない(フラグ提示 + Curator 判断)。
       ただし taint fragment のみを根拠とする FACT は GC-8 で遮断する。
ETB-7  Curator の semantic judgment instance は DB write 権限を持たない
       (CU-1 と同一の防衛線。injection が成功しても書けない)。
```

### 17. 時間モデル(確定版)

#### 17.1 4時間軸 [P1-CORE / schema必須]

```
event_time        外部世界で出来事が成立した時刻
publication_time  情報が公表された時刻
observation_time  我々が取得した時刻
knowledge_time    Global DB へ claim 登録された時刻
```

```
TM-5  4軸を単一の valid_from へ潰さない。valid_from には
      valid_from_basis(どの軸から導出したか)を必須で併記する。
TM-6  ABSENCE 評価では publication_time と search_time の比較を用いる
      (SA-1: 世界変化と見落としの分離)。
TM-7  event_time / publication_time が不明の場合は null とし、
      observation_time で代用しない(軸の混同禁止)。
```

#### 17.2 freshness(v0.1 §6 維持)

status(証拠の強さ)/ validity(世界側の有効期間)/ freshness(検証の新しさ・導出値)
の直交を維持。volatility_class と TTL は DD-1。STALE の再検証 queue(TM-3)は
Critical Claim 優先(LD-2)と usage 実績(17.3)で順位付けする。

#### 17.3 Interaction History [P1-SCHEMA]

```
IH-1  claim の利用・挑戦の履歴(CREATED / USED_BY_TASK / REVERIFIED /
      CHALLENGED / CONFLICT_DETECTED / SUPERSEDED / RETRACTED)を
      append-only で記録する。Phase 1 は USED_BY_TASK の記録のみ実装
      (grounds_snapshot から機械生成可能)。
IH-2  使用実績は真実性の証拠ではない(status 判定に算入禁止)。
      high usage + high centrality + old verification の claim の
      再検証優先度を上げるためにのみ使う。
```

### 18. 剛直性制御(Epistemic Operating Point)

工学的根拠: 厳格化しすぎれば「一次情報がない → 何もFACTにできない → UNKNOWN飽和
→ 問題解決不能」、緩めれば DB 汚染。これは単一固定閾値では解けない均衡問題であり、
profile 別の運用点(§12)+ 観測指標で扱う。

```
EO-1  観測指標:
      Unsupported Assertion Rate(緩すぎ検出)
      DB Retraction Rate(緩すぎ検出)
      Unknown Saturation Rate = OPEN gap / 全 gap(硬すぎ検出)
      Research Dead-End Rate = BLOCKED 終了率(硬すぎ検出)
      Claim Centrality Concentration(剛直化検出)
      Evidence Source Concentration(単一源依存検出)
      Curator Reject Rate(運用点の偏り検出)
EO-2  Unknown Saturation が高い場合、「世界に情報がない」と結論する前に
      grounding policy が硬すぎる可能性を疑う。
EO-3  これらの調整は自動最適化しない(AP-5)。指標を Manager / 人間へ提示し、
      profile 改訂は人間の判断で行う。
EO-4  ε×L≈K_sys を制御式として実装することを明示的に禁止する。
      関係が本当にあるなら計測データから後で現れる。先取りしない。
```

### 19. 可逆性契約(Reversibility Contract)[P1-CORE]

工学的根拠: 「間違えないDB」は作れない。安全性は「変更しないこと」ではなく
「誤りと判明した瞬間に、どこから入り、どこへ伝播し、何を再評価すべきかを
逆走できること」で実現する。

```
RC-1  Raw Observation は immutable。
RC-2  Normalized Observation は normalization run と version を保持する。
RC-3  vector index / graph view は SoR から完全再構築可能である。
      再構築可能性を Phase 1 受け入れ試験に含める。
RC-4  claim status transition は event log から time-travel 再構成可能である。
RC-5  claim retraction 時に全参照 task・derived knowledge・composite を
      relation graph 逆走で列挙可能である。entity merge にも準用する(EN-5)。
RC-6  schema / axis 変更は migration event を保持し、旧 schema での view を
      再構成可能にする。
RC-7  自動処理による破壊的 delete を禁止する。
RC-8  すべての run は irreversibility_class を持ち(RL-2)、IRREVERSIBLE な
      外部変化(源の消滅)を検出した場合、ローカル保存を昇格する。
```

ストレージ責務(SoR / vector / graph / blob)は v0.1 §11 を維持。

---

## Part IV — 実装

### 20. Phase 分割

#### Phase 1 実装対象 [P1-CORE]

```
オブジェクト:
  Entity(軽量運用・EN-6語彙) / Source / Run Ledger /
  Raw+Normalized Observation / Evidence Fragment /
  Relation(8種語彙) / Atomic Claim(4時間軸・residual・validation_mode込み) /
  Knowledge Gap Registry / SearchPlan・Run・Snapshot・Conclusion /
  Coverage Profile(COV-TECH-STANDARD 1種) /
  Epistemic Profile(2種) / Axis Registry(初期軸 + PROVISIONAL受付)

機構:
  Grounding Contract lint(GC-1〜5, 7, 8) /
  Curator Gates 0-5 / 昇格パイプライン(PR-1〜5) /
  Retraction + relation逆走(RT-1〜7) / ETB(taint検出・伝播) /
  freshness導出 + 再検証queue(taskへの相乗り方式 TM-3) /
  event log + time-travel再構成(RC-4)
```

#### Phase 1 schema予約のみ [P1-SCHEMA]

```
Interaction History(USED_BY_TASKのみ実装、他はschema) /
Derived Knowledge namespace / reserved relation types /
taint種別の拡張フィールド
```

#### Phase 2 以降 [P2+]

```
Watcher統合(親文書のとおり。Run Ledger / Observation schemaは対応済み) /
Evidence Distance導出(publisher/method/environment/citation distance)と
  corroboration diversity(LOW/MEDIUM/HIGH)のCurator提示 /
centrality系導出とCritical Claim優先制御(LD-*) /
Axis昇格の半自動化(usage計測) / 転載スキャンrun(IN-1(c))の常設化 /
剛直性指標ダッシュボード(EO-1) / 多言語coverage(DD-11) /
Derived Knowledge有効化(DK-*) / Schema Reboot運用(AX-5の本格化)
```

### 21. 評価指標統合表

親文書 §13 + v0.1 §12 + 本書追加分。すべて一次記録からの導出であること。

| 指標 | 測定元 | 方向 |
|---|---|---|
| Unsupported Claim Rate | GC lint の UNSUPPORTED 数 / 全 assertion | 緩すぎ検出 |
| False Absence Rate | SA-1(b) SEARCH_COVERAGE_FAILURE 数のみ計上 | 調査品質 |
| DB Contamination Rate | RETRACTED 数 + impact_scan 半径 | 緩すぎ検出 |
| time_to_detect_error | claim knowledge_time → retraction 時刻 | 検出速度 |
| repeat_error_rate | 同型誤り(同 claim_key 族)の再発 | 学習効果 |
| DB Reuse Rate | grounds_snapshot 中の Global 参照数 | 資産化 |
| Post-hoc Missing Information | 残存 OPEN gap + 事後監査発見数 | RD品質(最重要・親文書指定) |
| Gap Lineage Depth | parent_gap 連鎖長 | 調査の深化 |
| Loop Rate | SearchPlan の objective 類似クラスタ | 効率 |
| Research Coverage | gap 消化率(KG-4) | RD品質 |
| Unknown Saturation Rate | OPEN gap / 全 gap | 硬すぎ検出 |
| Research Dead-End Rate | BLOCKED 終了率 | 硬すぎ検出 |
| Construction Rate | 新規 claim / relation / ESTABLISHED axis / RESOLVED gap | 成長 |
| Deconstruction Rate | retraction / scope縮小 / axis reboot / 偽独立検出 | 健全な解体 |
| Schema Instability | AXIS_REBOOT 頻度 | ontology品質 |
| Curator誤ACCEPT率 | decision record の事後監査 | Curator品質 |

```
EV-1  claims added 単独を DB 品質指標にしない。Construction と
      Deconstruction を並列計測する(解体は失敗ではない)。
EV-2  Retraction の存在を Curator の失敗としない(RT-7)。
```

### 22. DESIGN DECISION REQUIRED(統合版)

v0.1 の DD-1〜DD-12 を維持し、以下を追加・改訂する。

```
DD-1   volatility_class ごとの TTL 具体値(維持)
DD-2   ABSENCE claim の TTL 短縮係数(維持)
DD-3   GC-6 実装方式(維持。assertion からのテンプレート生成を推奨)
DD-4   初期 ESTABLISHED axis 辞書の確定(AX-6 の案を叩き台に)
DD-5   embedding モデルと類似閾値(維持・調査ベース選定)
DD-6   SoR / vector / graph / blob の具体製品(維持・調査ベース選定)
DD-7   数値 confidence の導入可否(維持。本書は離散 status + validation_mode +
       diversity 段階値で代替しており、導入不要が現時点の推奨)
DD-8   Curator LLM 二重化の適用範囲(維持)
DD-9   Gate 3 逸脱の厳格度(維持)
DD-10  人間レビュー queue の UI と運用主体(維持)
DD-11  多言語情報源 coverage 要件(維持。構造は CP-3 で対応済み)
DD-12  Task Evidence 保存期間・上限(維持)
DD-13  Axis 昇格閾値(usage_count / distinct tasks の具体値)【新規】
DD-14  Phase 1 の taint 検出パターン集合(ETB-4)【新規】
DD-15  Epistemic Profile 第3種以降の追加基準(EP-1 は2種で開始)【新規】
DD-16  転載スキャン(IN-1(c))の実行タイミング(昇格時/定期/CORROBORATED判定時)【新規】
DD-17  Entity Registry の provisional entity 昇格手続の詳細【新規】
```

### 23. 監査記録

#### 23.1 v0.2 Draft(GPT)からの変更点 — 再監査対象

```
AU-8   Phase 分類 [P1-CORE / P1-SCHEMA / P2+] を全オブジェクトに付与。
       Evidence Distance / centrality / Interaction History 本体を P2+ へ。
       (親文書「最初から汎用AI組織を作らない」の適用)
AU-9   known_omissions を Axis Registry キー限定に変更(RR-1)。
       これにより GC-7 が機械検証可能になった。自由記述は
       extraction_loss_note へ分離。
AU-10  Search Coverage Profile を first-class 化(§10.2)。
       「required source domains」の未定義を解消。
AU-11  relation 語彙を Phase 1 は8種に制限、残り reserved(RE-1)。
       語彙拡張を axis 昇格と同プロセスに統一。
AU-12  独立性を PRESUMED / CONFIRMED の2段階に(IN-2)。
       MIRRORS 未検出を独立の証明と扱わない。
AU-13  Entity の alias / identity link に provenance 必須化、merge 可逆化
       (EN-4/EN-5)。
AU-14  Epistemic Profile の付与を Manager コードに限定、RD 自己選択禁止
       (EP-2/EP-3)。抜け穴封鎖。
AU-15  「Grounded Knowledge」を独立オブジェクトにしないことを明文化(§1.1)。
AU-16  taint 伝播チェーン(ETB-5 / EF-4 / GC-8)を追加。
AU-17  親文書禁止条項「ESDE固有設計へ寄せること」を明示的に改訂(§0.2)。
       ガードとして de-ESDE テスト(AP-4)を導入。
AU-18  UNKNOWN placeholder claim を廃止し Gap Registry へ移管(ST-7 / KG-2)。
       v0.1 の遷移権限表のうち「(新規)→UNKNOWN」行は Gap 登録に置換。
```

#### 23.2 v0.2 Draft から維持した主要判断

```
representation_residual(ε転用) / Evidence–Claim–Context 三項(T転用) /
Provisional Axis(Axis Emergence転用) / Reversibility Contract(可逆性転用) /
validation_mode の非序列化 / SearchRecord の4分割 / 4時間軸 /
Gap lineage / Construction・Deconstruction 並列計測 /
ε×L≈K_sys の実装式化禁止 / 多数決禁止(ST-4) / 推論昇格禁止(PR-2)
```

以上。本書 + 親文書(初期設計仕様 v0.1)のセットが Claude Code への
引き渡し物であり、§20 の Phase 分割に従って component 設計へ展開する。
