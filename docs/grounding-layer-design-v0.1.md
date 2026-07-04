# Epistemic Grounding Layer — 技術設計書 v0.1

対象システム: Distributed Research & Knowledge System (初期設計仕様 v0.1)
本書のスコープ: 「AIが何を根拠に語るのか」を規定する根拠層の設計
上位文書の設計思想・責任分界は変更しない。
実装詳細(具体的なDB製品・ライブラリ選定)は Claude Code への次工程とし、
本書では **契約(contract)とスキーマと状態遷移** を確定する。

---

## 0. 本書の位置づけ

上位文書 v0.1 は「誰が何をしてよいか」(責任分界)を定義した。
本書は「発話・claim・証拠の間に成立しなければならない関係」(根拠契約)を定義する。

本書が確定させるもの:

1. 発話クラスと Grounding Contract(§1)
2. Source / Observation / Claim / SearchRecord の4層データモデル(§2, §3)
3. Claim lifecycle と状態遷移の権限表(§4)
4. NOT_FOUND の形式化 — Absence Claim(§5)
5. 時間モデル — validity / freshness / volatility の分離(§6)
6. 重複検出と矛盾検出(§7)
7. Curator 検証フロー — 決定的ゲートとLLM判断の分離(§8)
8. Task Evidence → Global Knowledge 昇格と汚染対策(§9)
9. RD への構造的強制 — 内部知識遮断の実装方式(§10)
10. ストレージ責務の原則(§11)
11. 評価指標との接続(§12)
12. DESIGN DECISION REQUIRED 一覧(§13)

---

## 1. 発話クラスと Grounding Contract

### 1.1 問題

上位文書は「内部知識を技術的証拠として扱わない」と規定するが、
RDの最終出力(resolution)は自然文を含むため、
**どの文が証拠に支えられ、どの文が推論・仮説なのか**が構造上判別できない。
判別できなければ Unsupported Claim Rate は測定不能であり、原則は飾りになる。

### 1.2 解決: 発話を4クラスに構造化する

RD・External Judge が生成するすべての技術的言明は、
自然文の前に **assertion object** として構造化される。
自然文(resolutionの読み物部分)は assertion 群から**最後に生成**する。
逆順(文章を書いてから根拠を付ける)を禁止する。

| class | 定義 | 根拠要件 |
|---|---|---|
| `FACT` | 外部世界についての事実言明 | grounds に 1件以上の claim_id 必須。かつ最低状態を満たすこと |
| `INFERENCE` | 複数のFACTからの導出 | grounds(前提claim) + inference_rule(導出根拠の言語化) 必須 |
| `HYPOTHESIS` | 未検証の仮説 | grounds 任意。ただし明示的に HYPOTHESIS とラベルされること |
| `DESIGN_CHOICE` | 事実ではなく選択・提案 | 依拠する FACT/INFERENCE の参照を推奨。価値判断であることを明示 |

### 1.3 Grounding Contract(検証器が機械的に強制する規則)

```
GC-1  class=FACT の assertion は grounds が空であってはならない。
GC-2  FACT の grounds が参照する claim の status は、
      task の要求する min_ground_status 以上でなければならない。
      (既定: TASK_REPORTED 以上。安全性に関わる task では TASK_VERIFIED 以上)
GC-3  INFERENCE は grounds と inference_rule の両方を持たねばならない。
      inference_rule は「前提からなぜ結論が出るか」の1〜3文。
GC-4  grounds の claim_id は Knowledge DB または当該 task の
      Task Evidence に実在しなければならない(dangling reference 禁止)。
GC-5  上記を満たさない technical assertion は class=UNSUPPORTED として
      検証器が自動分類し、resolution に含める場合は明示的に
      unsupported_assumptions 節へ隔離する。本文へ混ぜてはならない。
GC-6  自然文 resolution 内の技術的言明は assertion_id への参照を持つ。
      参照を持たない技術的言明の存在は lint エラーとする。
```

GC-1〜GC-6 の検証は **コードで実装する**(LLMによる自己申告に依存しない)。
GC-6 のみ完全自動化が難しいため、実装方式を §13 に DESIGN DECISION として残す。

### 1.4 assertion object スキーマ

```json
{
  "assertion_id": "A-0007",
  "class": "FACT",
  "text": "vLLM >= 0.11 は SM120 (RTX 5090) 上で NVFP4 重みの推論をサポートする",
  "grounds": ["C-000142", "TE-00128-c003"],
  "inference_rule": null,
  "confidence_note": null,
  "scope_echo": {"runtime": "vllm", "gpu_arch": "sm120", "quant": "nvfp4"}
}
```

`scope_echo` は grounds の claim scope の再掲であり、
assertion が claim の scope を**超えて一般化していないか**を Curator/検証器が照合するために置く。
(例: 「vLLM 0.11 で確認」というclaimを根拠に「vLLMでサポート」と書く scope 拡大を検出する)

---

## 2. データモデル — 4層分離

### 2.1 問題

上位文書の claim スキーマは `sources` を claim 内に直接埋め込む。
この形では以下が表現できない。

- 「同じ公式ドキュメントを2026-06と2026-07に見たら内容が違った」(観測の時点性)
- 「このclaimの根拠となったページはもう書き換わっている」(証拠の失効検出)
- 「この観測は誰が・どの手段で取得したか」(取得経路の監査)
- 「見つからなかった」という結果の再現条件

### 2.2 解決: Source / Observation / Claim / SearchRecord を分離する

```
Source        情報源の同一性(登録簿)。「vLLM公式ドキュメント」という存在。
Observation   ある時点で Source を観測した不変レコード。content hash 付き。
Claim         Observation 群を根拠として Curator が確定した言明。
SearchRecord  「探したが見つからなかった」を含む、調査行為そのものの記録。
```

原則:

```
DM-1  Observation は immutable。作成後の変更・削除を禁止する(追記のみ)。
DM-2  Claim は Observation を直接コピーせず、observation_id で参照する。
DM-3  Claim の根拠は Observation のみ。Source を直接根拠にしない。
      (「公式docにあるはず」ではなく「この時点の公式docにこう書いてあった」)
DM-4  SearchRecord は Observation と同格の一次記録であり、
      Absence Claim(§5) の唯一の根拠となる。
DM-5  LLMの内部知識は Observation を生成できない。
      よって構造上、内部知識だけでは Claim を作れない。(§10)
```

DM-5 が本設計の要である。
「内部知識を証拠にするな」をプロンプトで頼むのではなく、
**証拠の型システムとして不可能にする**。

### 2.3 Source(情報源登録簿)

```json
{
  "source_id": "SRC-vllm-docs",
  "class": "PRIMARY",
  "kind": "official_documentation",
  "publisher": "vLLM project",
  "locator": {"type": "url", "value": "https://docs.vllm.ai/"},
  "authority_scope": ["runtime:vllm"],
  "volatility_class": "RELEASE_FAST",
  "watch_policy": {"enabled": true, "schedule": "daily"},
  "language": ["en"],
  "registered_by": "curator",
  "registered_at": "2026-07-04",
  "notes": ""
}
```

`class` の値域と定義:

| class | 定義 | 例 |
|---|---|---|
| `PRIMARY` | 対象の管理主体自身による公表物 | 公式doc, リリースノート, 仕様書, 公式repo |
| `SECONDARY` | 独立した第三者による検証可能な報告 | 技術ブログ(検証手順付き), 論文, ベンチマークサイト |
| `COMMUNITY` | 再現手順が不完全な報告 | GitHub issue, forum, Reddit |
| `GENERATED` | LLM生成物・要約・翻訳 | 別taskのresolution等。**Claimの根拠として単独使用禁止** |

`authority_scope` は「この情報源が一次情報たりうる範囲」。
vLLM公式docはvLLMについてPRIMARYだが、CUDAの挙動については PRIMARY ではない。
Curator は claim の scope と根拠observationの source authority_scope の整合を検査する(§8 Gate 3)。

### 2.4 Observation(観測レコード / immutable)

```json
{
  "observation_id": "OBS-2026-07-04-00871",
  "source_id": "SRC-vllm-docs",
  "retrieved_at": "2026-07-04T03:12:00Z",
  "retrieval_method": "http_get",
  "locator_snapshot": "https://docs.vllm.ai/en/v0.11/quantization.html",
  "content_hash": "sha256:...",
  "content_ref": "blob://observations/OBS-...-raw",
  "excerpt": "NVFP4 quantized checkpoints are supported on ... ",
  "excerpt_selector": "section#nvfp4",
  "collected_by": "rd",
  "task_id": "TASK-00128",
  "integrity": "OK"
}
```

規則:

- `content_ref` は取得時の生データ(または正規化テキスト)の保存先。証拠の原本主義。
- `excerpt` は根拠箇所の抜粋。Claim審査時にLLMへ渡す最小単位。
- 同一URLでも取得時点が異なれば別 Observation。
- Watcher の差分検出は「同一 source_id の最新2 Observation の content_hash / 正規化差分」で行う。

### 2.5 Claim(確定言明 / Curator専有書き込み)

上位文書のスキーマを以下に改訂する(互換フィールドは保持)。

```json
{
  "claim_id": "C-000142",
  "revision": 2,
  "claim_key": "capability:supports(runtime=vllm,arch=sm120,quant=nvfp4)",
  "claim_type": "CAPABILITY",
  "polarity": "POSITIVE",
  "statement": "vLLM 0.11以降はSM120上でNVFP4量子化モデルの推論をサポートする",
  "scope": {
    "runtime": "vllm",
    "runtime_version": ">=0.11",
    "gpu_arch": "sm120",
    "quant": "nvfp4"
  },
  "status": "VERIFIED",
  "evidence": [
    {"observation_id": "OBS-2026-07-04-00871", "role": "SUPPORTS", "source_class": "PRIMARY"},
    {"observation_id": "OBS-2026-07-02-00790", "role": "SUPPORTS", "source_class": "COMMUNITY"}
  ],
  "search_records": [],
  "derivation": {
    "origin": "task",
    "origin_ref": "TASK-00128",
    "curator_decision_ref": "CDEC-00455"
  },
  "volatility_class": "RELEASE_FAST",
  "valid_from": "2026-06-01",
  "valid_until": null,
  "last_verified": "2026-07-04",
  "supersedes": ["C-000091"],
  "superseded_by": null,
  "conflicts_with": [],
  "retraction": null
}
```

`claim_type` の初期値域:

| claim_type | 内容 | 例 |
|---|---|---|
| `CAPABILITY` | あるものが何かをできる/できない | runtime Xがarch Yを支持 |
| `VERSION_FACT` | バージョン・リリースの事実 | v0.11が2026-06-01に公開 |
| `COMPATIBILITY` | 組み合わせの成立性 | driver X + CUDA Y の組合せ |
| `MEASUREMENT` | 実測値・ベンチマーク | tok/s, VRAM使用量(測定条件をscopeに必須) |
| `PROCEDURE` | 手順の有効性 | このflagで起動可能 |
| `SPEC` | 仕様上の規定 | 規格・API契約 |
| `ABSENCE` | 調査範囲内で確認できなかった(§5) | — |

`polarity`:

- `POSITIVE` — 成立する
- `NEGATIVE` — 成立しないことが**明示的根拠により**確認された(= 上位文書の EXPLICITLY_UNSUPPORTED)。PRIMARY observation を最低1件要求する。
- `ABSENCE` — 見つからなかった(§5)。NEGATIVE とは別物。**混同禁止(上位文書 原則7)**

### 2.6 SearchRecord(調査行為の記録)

§5 で詳述。Observation と並ぶ一次記録として同格に扱う。

---

## 3. 状態モデル

### 3.1 status の値域(Global Knowledge DB)

上位文書の状態を維持しつつ、遷移可能性を定義する。

```
VERIFIED       PRIMARY observation により直接確認
CORROBORATED   独立した SECONDARY/COMMUNITY 複数が一致(PRIMARYなし)
REPORTED       単一の SECONDARY/COMMUNITY 報告のみ
PARTIAL        claimの一部scopeのみ確認
CONFLICT       有効なobservation間に矛盾
NOT_FOUND      ABSENCE claim 専用状態(§5)
UNKNOWN        登録のみ・未調査(要求分解で生成されたplaceholder)
DEPRECATED     現在は利用すべきでない(根拠付き)
SUPERSEDED     新claimにより置換
RETRACTED      誤りと判定され撤回(§9.4)。削除はしない
```

判定規則(Curatorが適用):

```
ST-1  VERIFIED には SUPPORTS role の PRIMARY observation が最低1件必要。
ST-2  CORROBORATED には互いに独立な source からの SUPPORTS が最低2件必要。
      「独立」の判定: publisher が異なり、かつ一方が他方の転載でないこと。
ST-3  GENERATED class の observation は status 判定に算入しない。
ST-4  REFUTES role の有効な observation が存在する場合、
      SUPPORTS の数にかかわらず CONFLICT とする(多数決で上書きしない)。
ST-5  status の昇格・降格は Curator decision record を伴う。無記録遷移は禁止。
```

ST-4 は重要である。「賛成9件・反対1件だから成立」という多数決は、
転載・引用の連鎖で膨らんだ同根情報に対して脆弱なため採用しない。
矛盾は矛盾として保持し、解消は根拠の質(source class, authority_scope, 時点)で行う。

### 3.2 Task Evidence 側の状態(RD namespace)

上位文書 7.6 を維持: `DB_VERIFIED / TASK_VERIFIED / TASK_REPORTED / TASK_PARTIAL / TASK_CONFLICT / NOT_FOUND / UNKNOWN`

対応規則:

- `DB_VERIFIED` は Global claim への**参照**であり、Task Evidence 内へのコピーを禁止する
  (コピーするとGlobal側の SUPERSEDED/RETRACTED がtaskへ伝播しなくなる)。
  参照時に claim の status と freshness(§6) を snapshot として記録する。
- `TASK_VERIFIED` は task 内で取得した PRIMARY observation に基づく。
- Task Evidence の状態は Global の status と**別の名前空間**であり、昇格時に Curator が再判定する。
  RD の TASK_VERIFIED は Global の VERIFIED を意味しない。

### 3.3 状態遷移の権限表

| 遷移 | 実行者 | 必要物 |
|---|---|---|
| (新規) → UNKNOWN | Curator (RD要求分解由来のplaceholder登録) | requirement map |
| UNKNOWN → REPORTED/CORROBORATED/VERIFIED | Curator | observation + decision record |
| * → CONFLICT | Curator | REFUTES observation |
| CONFLICT → VERIFIED/... | Curator | 矛盾解消の decision record(根拠の質の比較を明記) |
| * → SUPERSEDED | Curator | 後継claim_id |
| * → DEPRECATED | Curator | 根拠observation |
| * → RETRACTED | Curator | retraction record(§9.4) |
| NOT_FOUND → (通常status) | Curator | 新規observation(発見された場合) |
| Task Evidence 内の全状態 | RD | task namespace 内のみ。Globalへは不可 |

**Watcher・RD・Manager・External Judge による Global status 遷移は全面禁止**(上位文書 原則3,4,5を状態遷移表として固定)。

---

## 4. Claim Lifecycle

```
                    (RD requirement decomposition)
                              │
                              ▼
                    UNKNOWN placeholder ──────────────┐
                              │                       │
              (RD調査 → CandidateClaim → Curator)      │(調査対象外のまま)
                              │                       ▼
        ┌──────────┬──────────┼──────────┐         UNKNOWN
        ▼          ▼          ▼          ▼
    REPORTED  CORROBORATED  VERIFIED  PARTIAL
        │          │          │          │
        └────┬─────┴────┬─────┴─────┬────┘
             │          │           │
     (REFUTES検出)  (後継claim)  (誤り判定)
             ▼          ▼           ▼
         CONFLICT   SUPERSEDED  RETRACTED
             │
      (Curator解消)
             ▼
      VERIFIED / DEPRECATED / ...
```

不変条件:

```
LC-1  いかなる claim も削除されない。終端状態は SUPERSEDED / RETRACTED / DEPRECATED。
LC-2  SUPERSEDED claim は superseded_by を必ず持つ。後継のない置換は存在しない。
LC-3  RETRACTED claim は retraction record を必ず持つ(§9.4)。
LC-4  revision は Curator decision ごとに単調増加。全 revision の履歴を保持(append-only event log)。
LC-5  status 変更イベントはすべて event log に記録され、
      「2026-06-15時点でこのclaimは何statusだったか」を再構成可能とする。
```

LC-5(time-travel再構成)は DB Contamination Rate の測定(§12)に必須。
「当時この誤claimを何個のtaskが参照したか」を後から監査するために置く。

---

## 5. NOT_FOUND の形式化 — Absence Claim

### 5.1 問題

上位文書は NOT_FOUND と DOES_NOT_EXIST の分離を原則化したが、
NOT_FOUND が状態名だけでは以下が起きる。

- 「見つからなかった」の**再現条件**が残らない(どの検索語で、どこを、いつ探したのか)
- 後日情報が出現しても、どの NOT_FOUND が失効したか特定できない
- RDが毎回同じ「見つからない調査」を繰り返す(Loop Rate悪化)

### 5.2 解決: 不在は SearchRecord を根拠とする ABSENCE claim として保存する

SearchRecord スキーマ:

```json
{
  "search_record_id": "SR-00311",
  "task_id": "TASK-00128",
  "objective": "SM120向けNVFP4 kernelのTensorRT-LLM公式サポート記述を確認する",
  "queries": [
    {"engine": "web", "q": "TensorRT-LLM NVFP4 SM120 support", "executed_at": "2026-07-04T04:00Z"},
    {"engine": "github_code", "q": "repo:NVIDIA/TensorRT-LLM nvfp4 sm120", "executed_at": "2026-07-04T04:05Z"}
  ],
  "sources_checked": [
    {"source_id": "SRC-trtllm-docs", "observation_id": "OBS-...", "result": "NO_MATCH"},
    {"source_id": "SRC-trtllm-releases", "observation_id": "OBS-...", "result": "NO_MATCH"}
  ],
  "coverage": {
    "languages": ["en"],
    "time_range": "all",
    "excluded": ["中国語圏フォーラム未調査"]
  },
  "executed_by": "rd",
  "result": "NOT_FOUND"
}
```

ABSENCE claim:

```json
{
  "claim_id": "C-000201",
  "claim_type": "ABSENCE",
  "polarity": "ABSENCE",
  "statement": "指定調査範囲(SR-00311)ではTensorRT-LLMのSM120向けNVFP4公式サポート記述を確認できなかった",
  "status": "NOT_FOUND",
  "evidence": [],
  "search_records": ["SR-00311"],
  "volatility_class": "RELEASE_FAST",
  "valid_from": "2026-07-04",
  "last_verified": "2026-07-04"
}
```

規則:

```
AB-1  ABSENCE claim の根拠は SearchRecord のみ。observation の SUPPORTS を持たない。
AB-2  ABSENCE claim の statement は必ず調査範囲への参照を含む。
      「存在しない」という無限定な statement を Curator は REJECT する。
AB-3  ABSENCE claim の freshness TTL は同 scope の POSITIVE claim より短く設定する
      (不在は出現によって即座に古くなるため)。既定係数は §13 DESIGN DECISION。
AB-4  同一 claim_key に POSITIVE observation が出現した場合、
      ABSENCE claim は SUPERSEDED となる(CONFLICT ではない。不在確認と存在確認は矛盾ではない)。
AB-5  RD は task 開始時に同一 claim_key の ABSENCE claim を検索し、
      SearchRecord の coverage を確認した上で「前回の調査範囲外」だけを追加調査してよい。
      これにより不在調査の重複を構造的に削減する(Loop Rate 対策)。
```

AB-4 は運用上重要である。「昨日は無かったが今日リリースされた」は世界の正常な変化であり、
矛盾として警報を上げる事象ではない。

---

## 6. 時間モデル — validity / freshness / volatility

### 6.1 問題

上位文書は valid_from / valid_until / last_verified を持つが、
「VERIFIEDだが1年前の確認で、対象は月次で変わる領域」を表現する仕組みがない。
status に時間経過で手を入れると履歴が汚れる。

### 6.2 解決: 3概念を直交させる

```
validity   世界側の有効期間。claimが指す事実が成立していた期間。
           valid_from / valid_until。Curatorのみが根拠に基づき設定。
status     証拠の強さ。時間経過では変化しない。
freshness  検証の新しさ。last_verified と volatility_class から**導出**する。
           保存しない。読み出し時に計算する。
```

freshness の導出:

```
freshness = FRESH   if now - last_verified <= ttl(volatility_class)
          = STALE   otherwise
```

volatility_class と TTL の初期案(値は §13 DESIGN DECISION):

| class | 対象例 | TTL目安 |
|---|---|---|
| `RELEASE_FAST` | 活発なOSSランタイム, モデルリリース | 7–14日 |
| `DOC_STABLE` | 安定版ドキュメント, ドライバ要件 | 60–90日 |
| `STANDARD` | 規格, ISA仕様, 論文の内容 | 365日+ |
| `MEASUREMENT_BOUND` | ベンチマーク実測 | 環境変化に連動(runtime再リリースで即STALE) |

規則:

```
TM-1  STALE は status を変えない。VERIFIED(STALE) は「かつて一次確認された」という意味を保つ。
TM-2  RD が STALE claim を FACT の根拠に使う場合、resolution にその旨を明示する
      (grounds の snapshot に freshness を含める)。min_ground_status とは独立の警告軸。
TM-3  STALE claim は re-verification queue に入る。Watcher の観測対象なら自動再検証、
      そうでなければ次に同 scope を扱う task の RD へ再確認subtaskとして添付される。
TM-4  MEASUREMENT claim は測定条件(HW, driver, runtime version, 設定)を scope に必須とする。
      条件なし実測値の Claim 化を Curator は REJECT する。
```

TM-3 の後半(taskに再確認を相乗りさせる)は、Watcher未実装の Phase 1 でも
鮮度維持が回る仕組みとして重要。Phase 1 から実装する。

---

## 7. 重複検出と矛盾検出

### 7.1 claim_key による正規化

重複・矛盾検出の基盤は文字列類似ではなく **claim_key** とする。

```
claim_key = claim_type ":" predicate "(" sorted(scope_dimensions) ")"
例: capability:supports(gpu_arch=sm120,quant=nvfp4,runtime=vllm)
```

- scope の次元名は controlled vocabulary(辞書)で管理する。
  `runtime`, `gpu_arch`, `quant`, `model`, `runtime_version`, `os`, `driver_version` 等。
  辞書への追加は Curator 権限。自由記述の次元名を禁止する。
- バージョン等の連続値は claim_key から外し scope 本体に保持する
  (key衝突判定 → scope重なり判定の2段階)。

### 7.2 検出パイプライン

```
候補生成(recall重視):
  a. claim_key 完全一致
  b. claim_key の claim_type + 部分scope一致
  c. statement の embedding 類似(補助。閾値超えを候補に加えるのみ)

判定(precision担保):
  d. scope の重なり判定(次元ごとの包含/交差/排他)
  e. 時間区間の重なり判定(valid_from/valid_until)
  f. polarity / 値の両立性判定
```

規則:

```
DC-1  embedding 類似は候補生成にのみ使用する。自動マージの根拠にしない。
DC-2  scope が重なり、時間が重なり、両立しない内容 → CONFLICT リンク生成。
DC-3  scope が重なり、時間が重ならない → 矛盾ではなく時間的変化。SUPERSEDE 候補。
DC-4  scope が包含関係(片方がより広い) → PARTIAL/一般化の関係として記録。
      広い方のclaimが狭い方の反例で棄却されうることを Curator は考慮する。
DC-5  MERGE は「同一claim_keyかつ同一内容で evidence のみ異なる」場合に限る。
```

DC-3 が「vLLM 0.10では未対応 / 0.11で対応」を矛盾扱いしないための規則。
上位文書 4.4(履歴保持)の実装上の帰結である。

---

## 8. Curator 検証フロー

### 8.1 設計方針

Manager と同じ思想を Curator にも適用する:
**機械的に判定できるものはコードで落とし、LLMは意味判断のみに使う。**
LLM(Curator instance)は decision object を返すだけで、DB書き込み自体はコードが行う。

### 8.2 ゲート構成

```
CandidateClaim / CandidateUpdate
        │
  Gate 0  schema validation                 [code]
        │   JSON schema 適合。不適合は差戻し(REJECT: MALFORMED)
  Gate 1  evidence integrity                [code]
        │   observation 実在, content_hash 一致, immutability 検査,
        │   GENERATED 単独根拠の検出(→ REJECT)
  Gate 2  duplicate / conflict candidates   [code + vector index]
        │   §7 パイプライン。関連既存claimを decision context に添付
  Gate 3  source authority check            [code]
        │   claim scope と source authority_scope の整合。
        │   逸脱は警告フラグ付きで Gate 4 へ(自動REJECTしない。判断はLLM)
  Gate 4  semantic judgment                 [LLM: Curator instance]
        │   入力: proposed claim + evidence excerpts + 関連既存claims + 警告フラグ
        │   判断: 「excerptは本当にstatementを支持するか」
        │         「scopeは証拠が言っている範囲を超えていないか」
        │         「statusは §3.1 の判定規則に適合するか」
        │   出力: {decision: ACCEPT_NEW|UPDATE_METADATA|SUPERSEDE|MERGE|
        │          CONFLICT|REJECT|DEFER, rationale, edits}
  Gate 5  decision validation + write       [code]
        │   decision object の schema検査, ST-1〜ST-5 との整合検査,
        │   event log 追記, claim write, decision record 保存
        ▼
   Knowledge DB
```

規則:

```
CU-1  Gate 4 の LLM は DB への直接アクセス手段を持たない。読み取りも Gate 2/3 が
      添付した context に限定する(context汚染と越権読み取りの防止)。
CU-2  Gate 4 の出力が Gate 5 の整合検査に落ちた場合、書き込まず DEFER として
      人間レビューqueueへ送る。LLMの判断ミスをコードが最終防衛する。
  CU-3  DEFER の滞留時間に上限を設け、超過は Manager へ BLOCKED 要因として通知する。
CU-4  Curator decision record(CDEC)は claim と同様 append-only で全保存する。
      Curator 自体の品質監査(誤ACCEPT率)を可能にするため。
```

### 8.3 Curator への入力単位

Curator は claim 1件ずつではなく **claim_key クラスタ単位** で審査する。
同一 task から同一領域の candidate が複数出る場合、個別審査は
SUPERSEDE/MERGE 判断を誤らせるため、関連候補をまとめて1回の judgment に渡す。

---

## 9. Task Evidence → Global Knowledge 昇格と汚染対策

### 9.1 昇格パイプライン

```
Task Evidence (claims.jsonl 内の task-local claim)
        │  RD が昇格候補を指名(全件昇格の禁止)
        ▼
CandidateClaim queue
        │  §8 ゲート
        ▼
Global Knowledge DB
```

昇格候補の指名規則:

```
PR-1  RD が指名できるのは TASK_VERIFIED / TASK_REPORTED / TASK_CONFLICT /
      NOT_FOUND(SearchRecord付き) のみ。UNKNOWN と推論結果は指名不可。
PR-2  INFERENCE の結論を claim として昇格させることを原則禁止する。
      昇格するのは観測に基づく事実のみ。導出結果は task の resolution に留める。
      (推論の知識化は「RD自身の誤解の知識化」の主要経路であるため)
PR-3  task が FAILED / ESCALATE で終了した場合も、取得済み observation と
      SearchRecord は昇格候補にできる(調査の失敗と観測の有効性は独立)。
PR-4  昇格候補には origin task_id を必ず刻む(§9.4 のrecallに使用)。
```

### 9.2 Task Evidence の寿命

- Task Evidence は task 終了後も**そのまま保存**する(削除しない)。
  ただし retrieval 対象からは外す(Global RAG に混入させない)。
- 保存目的は Post-hoc Missing Information 監査(§12)と、RETRACTED 発生時の影響追跡。

### 9.3 Global 参照の snapshot 規則

RD が Global claim を参照した時点の {claim_id, revision, status, freshness} を
Task Evidence に snapshot として記録する(§3.2)。
これにより「このresolutionは、当時revision 2だったC-000142に依拠した」が永続化される。

### 9.4 Retraction(撤回)と影響追跡

claim が後日誤りと判定された場合:

```json
{
  "retraction_id": "RET-0009",
  "claim_id": "C-000142",
  "retracted_at": "2026-08-01",
  "reason": "excerptの読み違い。実際はexperimental supportのみ",
  "refuting_observations": ["OBS-..."],
  "decided_by": "curator",
  "impact_scan": {
    "referencing_tasks": ["TASK-00128", "TASK-00131"],
    "derived_claims": [],
    "notified": true
  }
}
```

規則:

```
RT-1  RETRACTED claim は削除せず、status=RETRACTED として保持する(誤りの履歴も知識)。
RT-2  impact_scan は event log(LC-5)から機械的に生成する。
RT-3  RETRACTED claim を根拠にしていた resolution を持つ task は
      Manager の再評価queueに載る(自動再実行はしない。判断はManager/人間)。
RT-4  DB Contamination Rate は RETRACTED 件数と impact_scan の広がりで測定する。
```

---

## 10. RD への構造的強制 — 内部知識の遮断

### 10.1 原則の実装

上位文書 7.1「内部知識を技術的claimの根拠として利用してはならない」を、
以下の3層で構造的に強制する。プロンプトによる注意は第4層(最弱)としてのみ扱う。

```
層1: 型システム
     FACT assertion の grounds は claim_id のみを受け付ける。
     claim は observation / search_record なしに存在できない(DM-5)。
     → 内部知識には「根拠として指す先」が構造上存在しない。

層2: 検証器(Grounding Contract lint)
     GC-1〜GC-6 をコードで検査。違反 assertion は UNSUPPORTED へ自動隔離。
     UNSUPPORTED 率は task ごとに記録され、閾値超過で Manager が差戻す。

層3: ツール設計
     RD の調査ツール(web search, fetch, DB retrieval)は、
     結果を必ず Observation / SearchRecord として自動記録する薄いラッパーを通す。
     「調査したが記録が無い」状態を作れないようにする。

層4: プロンプト
     内部知識の許可用途(検索語生成・調査領域推定・比較軸生成・情報源候補生成)を
     明記し、それ以外での使用を禁止する。層1〜3の存在を前提とした補助。
```

### 10.2 内部知識の許可用途の扱い

検索語生成等に内部知識を使うこと自体は claim を生まないため安全である。
ただし1点、**調査領域推定の漏れ**(内部知識が古く、新しい選択肢を探索候補に挙げない)は
層1〜3では防げない。これは Research Coverage / Post-hoc Missing Information(§12)で
事後測定し、requirement decomposition テンプレートの改訂で対処する運用とする。
(この残存リスクは根拠層では原理的に解決できないことを明記しておく)

### 10.3 External Judge への適用

External Judge の出力にも同じ assertion 構造を要求する。
Judge は新しい observation を生成できない(調査ツールを持たせない)ため、
Judge の FACT は既存 claim / Task Evidence の参照に限られる。
Judge の新規アイデアは HYPOTHESIS / DESIGN_CHOICE として構造上分類される。
これにより「上位モデルが言ったから」が VERIFIED 相当に化ける経路を塞ぐ。

---

## 11. ストレージ責務の原則

具体製品の選定は行わない(上位文書の方針に従い、選定は調査ベースで次工程)。
ただし責務の分離だけを固定する。

```
SoR (System of Record):
  append-only event log + current-state view。
  claim / observation / search_record / decision record / retraction の正本。
  リレーショナルまたはdocument store。トランザクション整合を要求。

Vector index:
  statement / excerpt の類似検索専用。候補生成にのみ使用(DC-1)。
  SoR から常時再構築可能であること。正本性を一切持たない。

Graph / relation view:
  supersedes / conflicts_with / scope包含 / derivation の関係走査。
  専用graph DBか関係テーブルかは DESIGN DECISION(規模が小さいうちは後者で足りる可能性)。

Blob store:
  observation の原本(content_ref)。immutable, content-addressed(hash)。
```

不変条件: **vector index / graph view が失われてもSoRから完全再構築できること。**
再構築可能性を Phase 1 の受け入れ試験に含める。

---

## 12. 評価指標との接続

上位文書 13 の指標が本設計のどの構造から測定可能になるかを固定する。

| 指標 | 測定元 |
|---|---|
| Unsupported Claim Rate | GC lint の UNSUPPORTED 分類数 / 全 assertion 数(§1) |
| False Absence Rate | ABSENCE claim を NEGATIVE として扱った assertion の検出(polarity照合) |
| DB Contamination Rate | RETRACTED 件数 + impact_scan(§9.4) |
| DB Reuse Rate | Task Evidence の Global 参照 snapshot 数(§9.3) |
| Post-hoc Missing Information | 保存された Task Evidence + requirement map と事後監査の突合(§9.2) |
| Loop Rate | SearchRecord の objective/queries 類似クラスタリング(§5) |
| Research Coverage | requirement map の UNKNOWN placeholder 消化率(§3.3) |

指標のために新たな計測機構を作るのではなく、
根拠層の一次記録(observation / search_record / decision record / event log)から
すべて導出できる状態を設計目標とする。

---

## 13. DESIGN DECISION REQUIRED

本書で確定させず、明示的に分離する判断。**勝手に補完しない。**

```
DD-1  volatility_class ごとの TTL 具体値(§6)。
      → 運用データが無い段階で決め打ちしない。Phase 1 は仮値で開始し計測後に確定。

DD-2  ABSENCE claim の TTL 短縮係数(AB-3)。

DD-3  GC-6(自然文とassertionの対応lint)の実装方式。
      候補: (a) resolution本文を assertion からテンプレート生成し自由文を持たせない
            (b) 自由文を許し、対応付けをLLM+ルールで検査
      (a)は確実だが可読性が犠牲。(b)は検査自体がLLM依存になる。

DD-4  scope controlled vocabulary の初期辞書と管理プロセス(§7.1)。

DD-5  embedding モデルと類似閾値(DC候補生成用)。ローカル運用制約(RTX5090環境)込みで
      次工程の調査対象とする。内部知識で選定しない。

DD-6  SoR / vector / graph の具体製品。同上、調査ベースで選定。

DD-7  数値confidence(0-1スコア)を導入するか。
      本書は離散statusのみを採用した(数値は根拠の質の差を隠蔽しやすいため)。
      導入する場合は「表示用の導出値であり判定に使わない」制約を推奨するが、要判断。

DD-8  Curator LLM の二重化(独立2インスタンスの一致要求)を高リスクclaimに適用するか。
      コスト増と汚染防止のトレードオフ。

DD-9  Gate 3 逸脱(authority_scope外のPRIMARY主張)の扱いの厳格度。

DD-10 人間レビューqueue(CU-2のDEFER先)のUIと運用主体。

DD-11 多言語情報源(特に中国語圏のモデル/runtime情報)の coverage 要件。
      SearchRecord の coverage.languages に既に構造は用意した。方針のみ未決。

DD-12 Task Evidence の保存期間とストレージ上限(§9.2 は無期限保存を仮定)。
```

---

## 14. GPT側への監査依頼事項

本書はv0.1(GPT作成)の思想を変更していないつもりだが、以下の解釈追加を行った。
監査対象として明示する。

```
AU-1  Source と Observation の分離(§2)。v0.1のclaim内sources埋め込みを廃した。
      → 思想の変更ではなく精緻化と解釈したが、確認を求める。

AU-2  NEGATIVE polarity を EXPLICITLY_UNSUPPORTED の一般化として導入(§2.5)。

AU-3  ABSENCE と POSITIVE の出現を CONFLICT ではなく SUPERSEDE とする規則(AB-4)。

AU-4  推論結果のclaim昇格を原則禁止(PR-2)。v0.1に明文はないが
      「RD自身の誤解の知識化を防ぐ」(6.4)の帰結として追加した。

AU-5  多数決による矛盾解消の禁止(ST-4)。

AU-6  freshness を status から分離し導出値とした(§6)。

AU-7  External Judge に調査ツールを持たせない設計(§10.3)。
      v0.1 9.3 の役割(追加調査領域の指示等)とは両立するが、Judgeが自ら
      観測を生成する運用を選びたい場合は本書の修正が必要。
```

以上。
