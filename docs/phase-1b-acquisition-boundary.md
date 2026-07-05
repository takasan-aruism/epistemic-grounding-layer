# EGL Phase 1b — Semantic Acquisition Boundary(一次仕様)

日付: 2026-07-05  Status: Draft for implementation planning
Basis: PHASE1A_INVENTORY.md / JREV-0001…0004 / DESIGN_EVIDENCE_LEDGER DE-0001…0030
決定者: Taka(著者=Claude Code は本仕様を一次情報として実装、独断で逸脱しない)

> **実装前に必ずこの文書を読む(一次情報)。** Phase 1b の設計判断はここが正本。

---

## 実装前追補(Taka, 2026-07-05)— AB-1/AB-2/AB-3

3つとも **同じ欠陥クラス**: Phase 1a で延々やってきた「上流の名前/summary でなく実際に起きた primitive を
見る」が取得層へ移っただけ。**予定した ≠ 実際に得た / 取れた ≠ 中身を観測できた / 場所を見た ≠ 必要な探索をした。**
Phase 1b で最初に踏むはずだった穴が、実装前の文書段階で既に見えている。**AB-1 は LegIntent 実装前に必須。**

- **AB-1(必須・LegIntent 前)**: `required_source_kind` を coverage の根にしない。それは SearchPlan が
  *要求* する証拠種別であって *観測された事実* ではない。RD が「OFFICIAL_DOCS を調査、target=random-blog」と
  提案 → code が LegIntent 化 → HTTP 取得成功 → OFFICIAL_DOCS leg COMPLETED、では completion 偽装は塞げても
  **LegIntent 作成時の誤分類で coverage を作れる**(信用の根を一段上げただけ)。分ける:
  `required_source_kind`(要求)vs **`observed_source_kind`**(取得した Source の provenance から評価)。
  取得成功後に **Source Qualification** で observed を評価し、**policy matcher が required と observed を
  照合**。取得成功 ≠ leg requirement 達成。→ 新受入 **ACQ-3b**。
- **AB-2(追補)**: SUCCESS が広すぎる。HTTP 200 でも Cloudflare challenge / login page / "JS required" /
  error payload があり得る(GitHub API 成功でも想定 file でなく error payload)。**transport success と
  content observation success を分ける**: `transport_status`(SUCCESS 等)+ `content_status`
  (OBSERVED / CHALLENGE_PAGE / AUTH_WALL / PLACEHOLDER / EMPTY / UNEXPECTED_CONTENT / UNSUPPORTED)。
  raw blob は何でも保存してよい(challenge page も「この時この URL が challenge を返した」という観測)。
  ただし **Raw Observation created ≠ Evidence-eligible Observation**——content_status=OBSERVED でなければ
  coverage を満たさない。→ 受入 **ACQ-4b**。
- **AB-3(追補)**: NOT_FOUND coverage を source kind だけで見ると粗い。「official repo search、
  query='banana'、0 results」でも OFFICIAL_REPOSITORY COMPLETED になり得る。**どこを見たか だけでなく
  どう探したか が根**。LegIntent に最低限 `search_method / query / scope_locator / pagination_policy /
  revision(time/version bound)` を持たせ、coverage は **『policy-defined な search operation が実行され、
  その結果 snapshot が保存された』** で見る(source kind searched でなく required search operation executed)。
  → 受入 **ACQ-4c**。

以下、本文の §7/§8/§9/§15/§18 はこの追補を反映済み。

---

## 0. Decision — Phase 1a is COMPLETE

Phase 1a は次の **狭い completion claim** の下で閉じる:

> Phase 1a は、上流アクターが有利な状態を self-report したというだけで無根拠な知識が受理されるのを
> 防ぐ **構造強制の背骨(structural enforcement spine)** を完成させた。

この完成主張は意図的に狭い。Phase 1a は次を **主張しない**(すべて Phase 1b の関心):
取得証拠の真正性 / source 分類の意味的正しさ / observation_kind の真正性 / statement→scope 束縛の
意味的正しさ / claim 同一性の意味的完全性 / Gate4 の production-ready 性 / 自律 RD 研究の運用性 /
MEASURED・REPRODUCED 導出の完全性 / taint lineage の完全性。

**閉じる理由は構造的**であって管理上ではない。Phase 1a の反復欠陥クラスは——
「有用な値を計算して捨てる」/「下位 primitive でなく summary/self-report を信用する」/
「guard は在るが sanctioned 実行パスに未接続」——であり、JREV-0001…0004 と counter-factual test が
この欠陥クラスを現背骨全体で実質的に閉じた。残る仕事は質的に異なる:

```
STRUCTURAL ENFORCEMENT
        ↓
SEMANTIC ACQUISITION AND JUDGMENT
```

ゆえに phase 境界はこの変化を表すべき。

---

## 1. Phase 1b 名称と主目的

**Phase 1b — Semantic Acquisition Boundary**

主目的: 外部取得証拠を、**provenance を保存し policy で制御された取得境界**を通してのみ EGL に入れる。
**自律 RD を有効化する前に。**

最初のマイルストーンは「より良い検索」ではない:

> 研究アクターは、後段の gate が取得証拠として扱う *primitive facts* を捏造できてはならない。

これは R4/DE-0023 の直接の帰結。

---

## 2. 決定的な順序制約(release-order invariant)

```
Source Policy → LegIntent → Acquisition Adapter → Acquisition Run/Result
→ Source Qualification(observed_source_kind 評価)→ Policy Matcher(required vs observed)
→ Raw Observation → Evidence Extraction → EGL curation → RD autonomy
```
(AB-1: 取得成功後に observed_source_kind を provenance から評価し、required と照合してから coverage 判定。)

**禁止順序:**
```
LLM-agentic RD → RD が source_kind/plan_id/COMPLETED/source_class を self-report → EGL が leaf を信用
```

R4 は現 leg authenticity が forged plan binding / forged COMPLETED leg に脆弱と確定した。ゆえに
**LegIntent と取得境界強制は、RD が LLM-agentic になる前に land しなければならない。** これは backlog
の好みでなく release-order invariant(= ACQ-10)。

---

## 3. Source Model — 静的 source list でなく Source Policy

EGL は「信頼サイト」の普遍的静的リストで始めない。source 適性は **task 依存**。系は
**Epistemic Task Profile が選ぶ Source Policy** を持つ。

```
Task → Epistemic Task Profile → Source Policy → Search Plan → LegIntent
```

同じ source が claim type によって強くも弱くもなる。例: 公式 repo のソースコードは
「実装 artifact が存在 / 関数シグネチャ / supported code path」には強いが、
「実世界の運用安定性 / dual RTX5090 での性能 / デプロイ成功率」には弱い。source authority は
**contextual** に保つ。

---

## 4. Discovery Source と Evidence Source の分離(必須)

- **Discovery Source**: 候補証拠を *見つける*(検索エンジン / Common Crawl / repo 検索 / 引用グラフ /
  コミュニティ / LLM 生成クエリ / 手供給 URL)。候補 locator/entity/repo/document/query を産むが、
  **自動的に事実的 ground になってはならない**。
- **Evidence Source**: Observation が実際に取得される source(検索結果が公式ドキュメント URL を発見 →
  公式ページを fetch → その raw が Observation source)。

必須の区別: `DISCOVERED_BY ≠ OBSERVED_FROM ≠ SUPPORTS`。単一 "source" field に潰さない。

---

## 5. 初期 Epistemic Task Profiles(3つ、実作業に対応)

Phase 1b で全ドメインをモデル化しない。現行作業に対応する3 profile から。

### 5.1 SOFTWARE_TECHNICAL
問い例: model X は vLLM で動くか / 量子化 Y は SM120 対応か / dual RTX5090 で動くか。
```yaml
profile: SOFTWARE_TECHNICAL
preferred: [FORMAL_SPEC, OFFICIAL_DOCS, OFFICIAL_REPOSITORY, OFFICIAL_RELEASE, OFFICIAL_ISSUE, REPRODUCIBLE_RUN, PRIMARY_RESEARCH]
supplementary: [INDEPENDENT_BENCHMARK, TECHNICAL_REPORT, COMMUNITY_REPORT]
discovery: [SEARCH_ENGINE, REPOSITORY_SEARCH, COMMON_CRAWL, COMMUNITY]
```

### 5.2 LEGAL_REGULATORY
問い例: 外国人が免許切替できるか / どのビザ区分が許すか / 何が法的に禁止か。
法文 / 行政手続 / 実務の窓口挙動 / 私的解釈 を区別せねばならない(矛盾しても片方が malformed とは限らない)。
```yaml
profile: LEGAL_REGULATORY
preferred: [LAW_PRIMARY_TEXT, GOVERNMENT_PROCEDURE, AUTHORITY_GUIDANCE, OFFICIAL_FAQ]
supplementary: [PROFESSIONAL_INTERPRETATION, INSTITUTIONAL_GUIDE, PRIVATE_GUIDE, PRACTICE_REPORT]
discovery: [SEARCH_ENGINE, LEGAL_INDEX, GOVERNMENT_SITE_SEARCH]
```

### 5.3 LANGUAGE_USAGE
問い例: この表現は実際に使われるか / 南部口語か / どんなニュアンスか / 辞書不在は意味を持つか。
辞書は語義定義に強いが口語不在の証明には不十分。dialogue 出現は「使用が観測された」に強いが
「一般的に common」「南部特有」「一義」には不十分。
```yaml
profile: LANGUAGE_USAGE
preferred: [LEXICOGRAPHIC_SOURCE, CORPUS, HUMAN_TRANSCRIPT, NATIVE_MEDIA_DIALOGUE]
supplementary: [MULTIPLE_USAGE_EXAMPLES, NATIVE_SPEAKER_EXPLANATION, MACHINE_INTERPRETATION]
discovery: [SEARCH_ENGINE, VIDEO_SEARCH, CORPUS_SEARCH, WIKI_SEARCH]
```
既存ベトナム語ツールの教訓を再利用可。

---

## 6. Acquisition Layer(adapter-based 実行境界)

初期 adapter: `ACQ_MEDIAWIKI / ACQ_GITHUB / ACQ_GIT / ACQ_HTTP_STATIC / ACQ_PDF / ACQ_RSS_ATOM /
ACQ_BROWSER / ACQ_MANUAL`。後続(任意): `ACQ_COMMONCRAWL / ACQ_HUGGINGFACE / ACQ_YOUTUBE_TRANSCRIPT /
ACQ_LEGAL_DATABASE / ACQ_CORPUS`。

router が target locator + Source Policy から adapter を選ぶ。**取得順序の優先**:
```
structured API > structured downloadable artifact > git/repo protocol > static HTTP > browser automation
```
browser automation は最後の手段(interaction 増 → hidden state 増 → 失敗モード増 → Run metadata 増 →
replayability 低下)。

---

## 7. LegIntent(SearchPlan と Acquisition の必須ブリッジ)

RD は SearchPlan を *提案* してよいが、**leg completed を直接宣言してはならない**。code が immutable な
LegIntent record を実体化する。
```json
{
  "leg_id": "LEG-00128", "plan_id": "PLAN-00031", "task_id": "TASK-00008",
  "required_source_kind": "OFFICIAL_DOCS",          // AB-1: これは *要求* であって観測事実ではない
  "target_locator": "https://...",
  "adapter_class": "ACQ_HTTP_STATIC", "expected_entity": "vLLM",
  "purpose": "verify NVFP4 support declaration", "created_from_plan_revision": "PLAN-00031-R2",
  "search_method": "REPOSITORY_CODE_SEARCH",        // AB-3: どう探したか
  "query": ["NVFP4", "nvfp4", "FP4"],
  "scope_locator": "vllm-project/vllm",
  "revision": "commit SHA",                          // time/version bound
  "pagination_policy": "ALL_RESULTS"
}
```
取得 runner は `leg_id` を受け取り、plan-binding metadata を **immutable LegIntent から解決**する。
completion path は `plan_id / required_source_kind / expected_entity` の **RD 供給値を completion 時に
受理してはならない**。これが R4 binding-forgery クラスを閉じる。

**AB-1(信用の根を一段上げない)**: `required_source_kind` は SearchPlan の *要求* であって、その leg が
その種別を *観測した* 事実ではない。coverage は取得成功だけでは満たされない——取得した Source を
Source Qualification(§11)で評価した `observed_source_kind` が、recorded Source Policy の下で
`required_source_kind` に一致した時のみ満たされる。誤分類された LegIntent(OFFICIAL_DOCS 要求に
random-blog を target)は取得成功しても **coverage requirement UNSATISFIED**。

**AB-3(場所でなく探索を根に)**: `search_method / query / scope_locator / revision / pagination_policy` を
LegIntent が持つ。coverage は「source kind を searched」でなく「**policy-defined な search operation が
実行され、その結果 snapshot(SearchResultSnapshot)が保存された**」で評価する(query='banana' 0件で
OFFICIAL_REPOSITORY COMPLETED を防ぐ)。

---

## 8. Acquisition Run(全取得試行は Activity/Run)

```json
{
  "acquisition_run_id": "ARUN-00122", "leg_id": "LEG-00128", "adapter": "ACQ_HTTP_STATIC",
  "adapter_version": "1.0.0", "started_at": "...", "finished_at": "...", "target_locator": "...",
  "transport_status": "SUCCESS",     // AB-2: 通信レイヤの成否
  "content_status": "OBSERVED",      // AB-2: 中身が観測可能か
  "http_status": 200, "content_type": "text/html",
  "raw_content_hash": "sha256:...", "retrieval_metadata": {}
}
```
**terminal status は RD でなく adapter が付す。AB-2: transport success と content observation success を分ける。**
- `transport_status`(通信の成否、FAILED に潰さない): `SUCCESS / NOT_RETRIEVABLE / ACCESS_DENIED /
  AUTH_REQUIRED / RATE_LIMITED / ROBOTS_DISALLOWED / NOT_FOUND_REMOTE / TIMEOUT / NETWORK_ERROR /
  PARSER_FAILED / UNSUPPORTED_CONTENT / ADAPTER_ERROR`。
- `content_status`(取れた中身が観測に足るか): `OBSERVED / CHALLENGE_PAGE / AUTH_WALL / PLACEHOLDER /
  EMPTY / UNEXPECTED_CONTENT / UNSUPPORTED`。

HTTP 200 でも Cloudflare challenge / login page / "JS required" / error payload はあり得る。
transport_status=SUCCESS + content_status=CHALLENGE_PAGE は正当な観測(「この URL が challenge を返した」)
だが **evidence-eligible ではない**。coverage を満たすのは content_status=OBSERVED のみ(§9/§10、ACQ-4b)。

---

## 9. 取得失敗は coverage についての知識

`SEARCHED_AND_NOT_FOUND / FETCH_FAILED / ACCESS_DENIED / PARSER_FAILED / REMOTE_404 / RATE_LIMITED` は
epistemically 異なり、distinct に保つ。例: 公式ドキュメント URL 特定 → Cloudflare challenge で取得不可、は
「公式ドキュメントが存在しない」を支持せず「target が正常に *観測されなかった*」のみ支持する。ゆえに
**SC-2 coverage は attempted locator でなく successful acquisition primitive を使う**。

```
LegIntent 存在 ≠ leg searched
Acquisition attempted ≠ source observed
source observed(transport)≠ content observed(AB-2: content_status=OBSERVED)
required source kind ≠ observed source qualification(AB-1)
source kind を見た ≠ 必要な search operation を実行した(AB-3)
source observed ≠ claim found
valid coverage 下で claim not found ≠ claim does not exist
```
**AB-3: coverage は『policy-defined な search operation が実行され、その結果 snapshot(SearchResultSnapshot)が
保存された』で評価する**(source kind を searched でなく required search operation executed)。SearchResultSnapshot は
LegIntent の `search_method / query / scope_locator / revision / pagination_policy` と、返った result set(0件も含む)を
記録する。query='banana' 0件は「探索した」ではあるが、policy が要求する search operation を満たさないなら
coverage 未達。

---

## 10. Raw Observation

transport_status=SUCCESS で adapter が Raw Observation 候補を emit(content_status に関わらず raw blob は
保存——challenge page も「この時この URL が challenge を返した」という観測)。ただし **AB-2:
Raw Observation created ≠ Evidence-eligible Observation**——evidence-eligible なのは content_status=OBSERVED
のみ。CHALLENGE_PAGE/AUTH_WALL/PLACEHOLDER/EMPTY/UNEXPECTED_CONTENT は Observation として記録されるが
coverage も extraction 対象も満たさない。**Observation identity ≠ content identity**
(Observation ID=event identity / content_hash=content identity)。同一 content の2度観測は重複データでなく、
両 Observation が同一 content-addressed blob(`blob://sha256/...`)を参照してよい。
```json
{
  "observation_id": "OBS-00128", "acquisition_run_id": "ARUN-00122", "source_id": "SRC-00031",
  "observed_at": "...", "raw_blob_ref": "blob://sha256/...", "raw_content_hash": "sha256:...",
  "content_type": "text/html", "normalization_status": "NOT_NORMALIZED"
}
```

---

## 11. Source Classification(provenance-assisted)

source 分類は可能な限り machine-observable provenance から *候補* を提案する。例: entity registry
(vllm-project/vllm = vLLM の OFFICIAL_REPOSITORY)+ GitHub adapter が commit SHA/path を fetch →
source_class 候補=PRIMARY、observation_kind 候補=IMPLEMENTATION_ARTIFACT。

**Phase 1b 初期ルール(safe-direction)**:
```
CODE が provenance から source_class 候補を提案
LLM は CONFIRM / DOWNGRADE / UNRESOLVED のみ可
LLM は別途 reviewed relation なしに code 候補を超えて ELEVATE できない
```
= 「code 由来の上界、LLM は abstain か narrow のみ」。他所と同じ安全方向原則。

**AB-1: この Source Qualification が `observed_source_kind` を産む**(取得した Source の provenance から
評価された実際の種別)。coverage 判定は **policy matcher が `required_source_kind`(LegIntent の要求)と
`observed_source_kind`(ここで評価)を recorded Source Policy 下で照合**して行う。取得成功だけでは
requirement を満たさない。例: required=OFFICIAL_DOCS / 取得=random-blog.example / observed=PRIVATE_GUIDE
→ Acquisition SUCCESS だが **OFFICIAL_DOCS requirement UNSATISFIED**。observed_source_kind も §11 の
safe-direction(code 上界、LLM は downgrade/unresolved のみ)に従う。

---

## 12. Observation Kind(leaf self-report → provenance-assisted)

初期 controlled vocabulary:
`DECLARATION / SPECIFICATION / IMPLEMENTATION_ARTIFACT / MEASUREMENT / REPRODUCTION_RUN / PROCEDURE /
LEGAL_TEXT / USAGE_OCCURRENCE / LEXICOGRAPHIC_ENTRY / UNSPECIFIED`。

adapter/source relation が候補を提案(GitHub source file→IMPLEMENTATION_ARTIFACT、local runner の
benchmark→MEASUREMENT、RFC/標準節→SPECIFICATION、辞書項→LEXICOGRAPHIC_ENTRY、transcript 行→
USAGE_OCCURRENCE)。**候補≠真実**だが無制限 RD self-report を減らす。

---

## 13. Evidence Extraction Boundary

Raw Observation 取得と Evidence Fragment 抽出は **別 Run** に保つ(正しく fetch ≠ 正しく fragment 選択)。
必須 lineage: `Acquisition Run → Raw Observation → Extraction Run → Evidence Fragment`。
Extraction Run metadata: `extractor_model / extractor_version / prompt_version / source observation_id /
bounded context policy / fragment offsets / normalization version`。

高リスク profile では独立抽出。JREV の教訓を保存: **generator と judge の分離だけでは不十分——
judge が generator 選択の歪んだ fragment しか見なければ**。judge は heading + 前後 bounded context +
fragment を受ける。

---

## 14. Source Policy は生きた Ledger オブジェクト(versioned)

prompt に埋めない。
```json
{
  "source_policy_id": "SPOL-SOFTWARE-0001", "profile": "SOFTWARE_TECHNICAL", "version": 3,
  "valid_from": "...", "preferred_classes": [...], "supplementary_classes": [...],
  "discovery_classes": [...], "coverage_requirements": [...], "supersedes": "SPOL-SOFTWARE-0001-v2"
}
```
SearchPlan は `source_policy_id + version` を記録 → 歴史的再構築が可能(policy が後で変わっても過去
SearchRun は旧 policy 下で解釈可能)。

---

## 15. 初期 Source Policy Coverage Rules(小さい明示ルール)

**SOFTWARE_TECHNICAL**: 互換存在=`{OFFICIAL_DOCS|OFFICIAL_REPOSITORY|OFFICIAL_RELEASE}` の1つ /
運用成功=`{REPRODUCTION_RUN|REPRODUCIBLE_RUN}` or 独立 OPERATIONAL_REPORT ×2 / NOT_FOUND=必須 coverage
leg(OFFICIAL_DOCS, OFFICIAL_REPOSITORY, OFFICIAL_ISSUE_SEARCH)完了。
**LEGAL_REGULATORY**: 法的禁止=`LAW_PRIMARY_TEXT` or 法に grounded な `AUTHORITY_GUIDANCE`
(private guide 単独では法的禁止を確立不可)/ 実務手続=`GOVERNMENT_PROCEDURE`。
**LANGUAGE_USAGE**: 「観測された」=1 USAGE_OCCURRENCE / 「commonly used」=独立多数 occurrence +
source 多様性 / 「南部」=regional corpus/metadata or region-linked 複数 occurrence。
**辞書不在は non-usage を確立してはならない。** 正確なルールは profile 固有で Source Policy に格納。

---

## 16. First Implementation Slice

Acquisition Layer 全体を一度に実装しない。**最初の実タスク**:

> 選択した Qwen checkpoint の dual RTX5090 での現行 vLLM support と運用証拠を調べる。

理由: 既知の現ユーザ需要 / 複数 source class / 公式ドキュメント / GitHub / 実装 artifact / issue /
運用レポートの可能性 / NOT_FOUND リスク / version・entity 同一性問題 / 測定可能な取得失敗。

実装するのは **のみ**:
```
Source Policy: SOFTWARE_TECHNICAL v1
Adapters: ACQ_GITHUB / ACQ_HTTP_STATIC / ACQ_MANUAL
Core: LegIntent(AB-1 required vs observed / AB-3 search fields)
      AcquisitionRun(AB-2 transport_status + content_status + failure taxonomy)
      SearchResultSnapshot(AB-3)
      Source Qualification → observed_source_kind(AB-1)
      Policy Matcher(required vs observed under Source Policy)
      RawObservation(evidence-eligible 判定は content_status=OBSERVED)
```
その後 1 実タスクを end-to-end で走らせる。adapter は実タスクが gap を露出した時だけ足す。

---

## 17. 初期 Phase 1b slice の明示的 Non-Goals(まだ足さない)

Watcher / 継続 crawling / global knowledge graph / 完全 Entity Registry / browser automation framework /
Common Crawl ingestion / vector DB 最適化 / multi-domain source ontology / 自動 policy 生成 /
自律 policy mutation / 完全 taint 伝播 / MEASURED・REPRODUCED 完成。これらは正当な後続能力だが、
取得境界の実証には不要。

---

## 18. Phase 1b Acquisition Boundary 受入基準(ACQ-1…10)

初期 slice は **全て真** の時のみ成功:

- **ACQ-1**: RD は任意の SearchLeg を COMPLETED にできない。completion は immutable LegIntent に紐づく
  AcquisitionRun terminal state から来る。
- **ACQ-2**: leg primitive を固定したまま SearchConclusion.status を変えても coverage は変わらない
  (既存 H1 保護が live)。
- **ACQ-3**: completion payload の plan_id/source_kind を変えても Run を別 plan に rebind できない
  (それらは LegIntent から解決される)。
- **ACQ-3b(AB-1・最重要)**: `required_source_kind` は要求であって観測事実ではない。coverage は、取得した
  Source を Source Qualification で評価した `observed_source_kind` が recorded Source Policy 下で
  `required_source_kind` に一致した時のみ満たされる。誤分類 LegIntent(要求 OFFICIAL_DOCS に random-blog
  target)は取得成功しても coverage UNSATISFIED。→ 敵対 counter-factual で検証。
- **ACQ-4**: FETCH_FAILED/ACCESS_DENIED/PARSER_FAILED は successful coverage を満たせない。
- **ACQ-4b(AB-2)**: transport_status=SUCCESS でも content_status≠OBSERVED(CHALLENGE_PAGE/AUTH_WALL/
  PLACEHOLDER/EMPTY/UNEXPECTED_CONTENT)は evidence-eligible でなく coverage を満たせない。Raw Observation は
  記録されるが evidence-eligible ではない。
- **ACQ-4c(AB-3)**: coverage は required search operation の実行 + SearchResultSnapshot 保存で満たされ、
  source kind を「見た」だけでは満たされない。0件 snapshot でも search_method/query/scope が policy 要求に
  一致していなければ coverage 未達。
- **ACQ-5**: SUCCESS は AcquisitionRun と raw content hash に辿れる Raw Observation を作る。
- **ACQ-6**: 同一 content の2度取得は1つの content-addressed blob を参照する2 Observation を作れる。
- **ACQ-7**: Discovery metadata は Claim を直接 ground できない。
- **ACQ-8**: SearchPlan が使った Source Policy version が再構築可能。
- **ACQ-9**: adapter が構造的証拠を出せる場合、source_class/observation_kind 候補は provenance-assisted。
- **ACQ-10**: **ACQ-1…4 が敵対 counter-factual test を通過する前に、自律 RD を有効化しない。**

---

## 19. 推奨次シーケンス

```
1. Phase 1a completion decision を記録        ← DE-0031 ✅
2. Phase 1b — Semantic Acquisition Boundary を open ✅
3. Source Policy v0 schema を freeze(required vs observed / coverage=search operation を含む)
4. LegIntent 実装(AB-1 required_source_kind=要求 / AB-3 search_method,query,scope,revision,pagination)
5. AcquisitionRun + failure taxonomy 実装(AB-2 transport_status + content_status)
6. SearchResultSnapshot 実装(AB-3: 実行した search operation と result set を記録)
7. Source Qualification → observed_source_kind + Policy Matcher(AB-1: required vs observed 照合)
8. ACQ_GITHUB 実装
9. ACQ_HTTP_STATIC 実装
10. Raw Observation emit(evidence-eligible = content_status OBSERVED)
11. SOFTWARE_TECHNICAL Source Policy v1 追加
12. 1 実 Qwen/vLLM/dual-5090 研究タスクを走らせる
13. 独立 local attacker(ACQ-1..4c を敵対 counter-factual で)
14. GPT adjudication
15. その後にのみ LLM-agentic RD を検討
```

---

## 20. Final Position

Phase 1a は完了宣言すべき。さらなる前進は構造 skeleton の延長でなく semantic 境界への進入を要する段階。
次の architectural 問題:

> 外部現実は、研究エージェントが後で「観測済み」と扱われる primitive facts を製造することを許さずに、
> どうやって ledger に入るのか?

答えは次の境界を軸に構築する:
```
Task Profile → Versioned Source Policy → SearchPlan → Immutable LegIntent → Acquisition Adapter
→ AcquisitionRun(transport_status + content_status)→ Source Qualification(observed_source_kind)
→ Policy Matcher(required vs observed)→ Raw Observation(evidence-eligible なら)→ Extraction Run
→ Evidence Fragment → typed Evidence Relation → EGL curation
```
AB-1/2/3 の要点は一言で: **予定 ≠ 取得 ≠ 観測 ≠ 探索**。各段で「予定した種別/取れた HTTP/見た場所」でなく
「観測された種別/中身/実行した探索操作」という primitive を根にする。Phase 1a の規律の取得層への延長。
ベトナム語ツールが既に同問題のドメイン特化版を示す(辞書証拠 ≠ 使用証拠 ≠ 地域証拠 ≠ 機械解釈)。
Phase 1b は技術/法律/言語研究を跨いでこの区別を一般化しつつ、取得失敗・source provenance・
evidence relation history を保存する。
