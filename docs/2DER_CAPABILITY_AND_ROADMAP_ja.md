# 2DER 現状能力 & 開発ロードマップ（日本語まとめ）

> **この文書の位置づけ** — 「いま 2DER で何が実際にできるのか / できないのか」を一望するための living doc。
> スナップショット時点: 2026-07-12（最新 `DE-0208` / 登録アーティファクト 60 / ロードマップ 8 DONE・7 PROPOSED）。
> 一次情報は各 repo のコードと `DESIGN_EVIDENCE_LEDGER.jsonl`。本書はそれを人間可読にまとめた索引であり、
> 本書と実装が食い違った場合は**実装が正**。能力主張はすべて「計測済み事実」に限定し、未計測は未計測と明記する。

---

## 1. 2DER とは（1 分で）

単一 AI に全部やらせるのではなく、**認知を 4 つの責任系に分解**し、それぞれ独立 private repo として運用する構成。

| 系 | repo | 責務 | ひとことで |
|---|---|---|---|
| **DS** | `ds` | Dialogue Substrate | 発話・イベント・スレッドの土台（UTT-/DEV-/THREAD-） |
| **RRI** | `rri` | Request / Research Intent | 要求と意図の分類・formal 化（RREQ-/RINT-/RSIG-） |
| **EGL** | `egl` | Epistemic Grounding Layer | 根拠なき claim を通さない知識台帳（OBS-/SRC-/ADM-/DE-） |
| **DW** | `dev-workcell` | Dev Workcell | 実装ワーカー/監査/ゲートの状態機械（TASK-） |
| **twoder** | `twoder` | Conductor / UI / Operator / Guards | 上記を束ねる指揮者・権限ゲート・登録簿 |

**Claude の役割** — Claude は「置き換え可能な 1 アクター」（SENIOR / UPPER_REVIEW / DISPOSE のバリア）でしかない。
ループを回すのは Claude の記憶ではなく**永続化された状態**。だから Claude が別セッションに変わっても継続できる、というのが設計思想。

---

## 2. いま実際にできること（LIVE 能力）

すべて **2DER 発行 ID で裏取り可能**、かつ hermetic な回帰テスト付き（`:8005`/GPU に触れない）。

### 2.1 前向きパス（submit → 経路判定）
- `POST /api/submit` → `twoder/submit.py` が **DS→RRI→EGL→routing** を通す。
- 経路: OBSERVE / RESUME / BUILD / DECIDE / RESEARCH を deterministic に分岐。
- **RRI preflight ゲート**（`RRI-GATE-AMBIGUOUS-QUANT-001`）: 出典の曖昧な定量主張を DW 投入前に保留/明確化（HBB-30 由来、`test_preflight_gate` 13/13）。
- BUILD 経路は `admit_forward_claims` で KNOWLEDGE_PACKET の主張を投入前に格付け（source-backed→ADMITTED / 挙動主張→REPORTED / 過剰→REJECTED）。

### 2.2 取得（acquisition）— 実アダプタ 6 種
`egl.acquisition.ADAPTERS`:
`ACQ_GITHUB` / `ACQ_GITHUB_SEARCH` / `ACQ_GITHUB_ISSUE` / `ACQ_GITHUB_PROV`（commit/PR/release 来歴）/ `ACQ_HTTP_STATIC`（docs）/ `ACQ_MANUAL`。
- research signal → GitHub 検索 → issue 個別取得 → docs → 来歴、を `run_research_acquisition` が束ねる。
- 取得境界を明示（transport/content status、ETB taint、取得失敗は正直に `retrieval_failure`）。**Phase-02 完了**。

### 2.3 開発証拠の admission（DE 台帳）
- `egl.de_admission` が **DE 台帳の唯一の書き手**（手動 append は廃止）。
- スキーマ検査 / 重複 REJECT / **claim 上限**（「self-improving」等のハード禁止語 → REJECTED）/ 挙動主張の REPORTED 降格 / IMPLEMENTED・LIVE 主張には**変更アーティファクト ID 必須**（anti-amnesia）。
- 記録は `submit → RRI 分類 → EGL admission → 台帳 append → RRI residual → DS thread` の生きた経路で dogfood 済み。

### 2.4 記憶の穴を塞ぐ 2 つの登録簿
- **ARTIFACT_REGISTRY**（`ART-<sha1>`）: 60 アーティファクトを repo/path/hash/commit/component/live_status で追跡。**未登録の変更ファイルはパケットが即座に検出**。
- **CHANGE_LOG**（`CHG-NNNN`）: 各変更を before/after commit hash 付きで記録。
- **ROADMAP_REGISTRY**（`ROADMAP/PHASE/ITEM/AMENDMENT`）: ロードマップ自体を ID 化。依存（depends_on→DONE まで BLOCKED）付き。

### 2.5 可観測性（Phase-05 完了）
- **read-only な roadmap/trace UI**（`/api/roadmap`, `/api/resolve?id=`）: 任意の 2DER ID を record へ解決。
- **自動 coverage matrix**（`management_packet` item 10）: artifact を component×live_status、roadmap を phase×status で自動集計。手集計ゼロ。

### 2.6 実行経済（Phase-07、直近実装）
- `twoder/execution_economy.py`: モデル履き替えコストの土台（`EXEC-ECON-SWAP-COST-001`）を**決定に surface** + **コスト意識のアクター選択**。
- 現行ライブは**単一モデル**（Qwen3.6-35B-A3B @ :8005 がコーダー/監査を seed+system-prompt で分離）。よって selector は**現状 no-op**（常駐モデルを返すだけ、履き替えなし、`:8005` に触れない）。
- モデルが 2 つ以上あるときだけコスト順に選び、実際の履き替えは `MODEL_LOAD_UNLOAD → REQUIRES_APPROVAL` としてゲートし**実行はしない**。

### 2.7 権限ゲート（authority）
- **AUTO_EXECUTE**: read-only 検査 / state refresh / log 読み / nvidia-smi / health check / 回帰テスト / trace 確認 / 分析レポート / DW machine dispatch。
- **REQUIRES_APPROVAL**: `:8005` への推論・停止・再起動、モデル load/unload、serve script 変更、GPU 割当変更、commit/push、broad claim。
- 未知コマンドは**安全側（承認必須）に倒す**。

### 2.8 DW ディスパッチ
- 次操作は**永続状態の純関数**（`next_legal_operation`）。機械アクター（Qwen worker/auditor）は自動実行、Claude バリア（DISPOSE/UPPER_REVIEW/PLAN）は PENDING を出して停止。
- 再現が記録状態から確定できる DISPOSE は機械化済み。

---

## 3. 各系の現状マップ（登録アーティファクト 60 の内訳）

| 系 | live | support | test | ledger | audit |
|---|---|---|---|---|---|
| EGL | 7 | — | — | — | — |
| TWODER | 8 | 1 | — | — | — |
| RRI | 5 | — | — | — | — |
| DW | 3 | 3 | — | — | — |
| DS | 1 | — | — | — | — |
| OPERATOR | 1 | — | — | — | — |
| AUTHORITY | 1 | — | — | — | — |
| UI | 1 | — | — | — | — |
| AUDIT | 1 | — | — | — | 4 |
| CONFIG | — | 2 | — | — | — |
| LEDGER | — | — | — | 5 | — |
| TEST | — | — | 17 | — | — |
| **計** | **28** | **6** | **17** | **5** | **4** |

---

## 4. いま「できないこと」/ 明示的な非能力（正直な境界）

過剰主張を避けるための明示リスト。**これらは未達であって、達成済みと偽ってはいけない。**

- **自律 RD は未有効**（`ITEM-2DER-EVO-0010`）。人間権限エンベロープ内でしか回さない設計で、そのゲート自体まだ入れていない。
- **co-serve（2モデル同時常駐）は HW ブロック**（`DE-0143`、gpu-mem-util 0.92）。解決していない・主張しない。
- **sleep-mode 履き替えはロールバック済**（`DE-0168/0171`）。ライブ能力ではない。
- **ライブ推論は承認なしに走らない**（`USE_VLLM_INFERENCE = REQUIRES_APPROVAL`）。テストはすべて hermetic。
- **RRI formal-validation / EGL Gate4 judge はまだ submit 経路に組み込まれていない**（`ITEM-0002/0003`、いずれも :8005 使用のため承認要）。
- **operator の機械オペ自動前進 / UPPER_REVIEW 部分機械化は未実装**（`ITEM-0008/0009`）。
- コーダーモデルの**性能比較は未計測**（下記 §6）。ベンチが上、は現状ユーザ報告（REPORTED）であって計測事実ではない。

---

## 5. 開発ロードマップ `ROADMAP-2DER-EVOLUTION-v0.1`（7 phase / 15 item）

### 完了フェーズ ✅
- **Phase-02 Acquisition breadth** — DONE（GitHub 検索/issue/docs/来歴の実アダプタ）
- **Phase-05 Observability & UI** — DONE（roadmap/trace UI + 自動 coverage matrix）
- **Phase-06 RRI Intelligence / Failure-informed Preflight** — DONE（曖昧定量ゲート）
- **Phase-07 Execution economy** — 実装 1（コスト surface + 選択）DONE、比較テスト 1 が PROPOSED（§6）

### 残 PROPOSED 7 件

| ITEM | Phase | タイトル | 権限 | 依存 | メモ |
|---|---|---|---|---|---|
| **0002** | 01 前向きパス接地 | RRI formal-validation を submit に配線 | 承認要 | — | :8005 使用 |
| **0003** | 01 前向きパス接地 | EGL judge / Gate4 を admission ゲート化 | 承認要 | 0001(済) | :8005 使用 |
| **0007** | 03 継続運用 | 候補由来タスクの PLAN テンプレ化 | 自動 | 0001(済) | ルールベース PLAN 部分の機械化。自由形式は Claude 継続 |
| **0008** | 03 継続運用 | operator の機械オペ自動前進 | 承認要 | 0007 | :8005 で GENERATE/AUDIT を権限内自動実行、人間バリアで停止 |
| **0009** | 03 継続運用 | UPPER_REVIEW 部分機械化 | 自動 | 0008 | gate クリーン&所見ゼロのときだけ自動 pass、非自明は人間 |
| **0010** | 04 自律ゲート | 制御された自律 RD の有効化 | 承認要 | 0003,0008 | 事前承認エンベロープ内でのみ自律 RD |
| **0015** | 07 実行経済 | **Qwen3.6-27B FP8 コーダーモデル本番テスト & 比較**（§6） | 承認要 | 0014(済) | GPU 切替案件のタイミングで実施 |

**推奨シーケンス**: 前向きパス接地（0002→0003）で「投入前の格付け」を強化 → 継続運用（0007→0008→0009）で人手バリアを段階的に機械化 → 自律ゲート（0010）。
0015 は**独立トラック**として GPU 切替案件（`TASK-2DER-GPU-SWITCH-001`）と同期して実施。

---

## 6. コーダーモデル更新の訂正（`ITEM-2DER-EVO-0015` / `DE-0208`）

**以前の想定**: コーディングワーカーの更新先は Qwen3.6-Coder-Next（dense）。

**訂正後の理解**:
- よく調べると、現行ライブの **Qwen3.6-35B-A3B が同等かむしろ上**の可能性。
- 具体的な更新候補は **Qwen3.6-27B**（同じ 3.6 系、DL 済、FP8 量子化 → **2 GPU 必須**）。同一バージョンの 27B で、ベンチは**やや高いと報告**（ただし**未計測 / 本番未稼働**）。

**タスク化した内容**（0015、承認要）:
1. Qwen3.6-27B FP8 を 2 GPU で本番スタンドアップ（`MODEL_LOAD_UNLOAD`/`USE_VLLM_INFERENCE` = 承認要でゲート）。
2. ライブの 35B-A3B と DW コーディング/監査ワークロードで**統制された A/B 比較**、EGL に観測を記録。
3. 計測した履き替えコスト + 品質差を `EXEC-ECON-SWAP-COST-001` の **UNMEASURED 値と差し替え**。
4. `execution_economy.py` の alternate_model 表記を Qwen3.6-27B FP8（2-GPU）に訂正。
5. **計測されるまで優位性は主張しない**（REPORTED のまま）。
6. **実施タイミング = GPU 切替案件を詰めるあたり**。

---

## 7. 運用規律（この系を触るときのルール）

- **ID バック必須**: 使う/変える/引用する実体はすべて 2DER 発行 ART-/DE-/CHG-/ITEM- 等を持ち、即解決可能であること。パスだけの参照は不可。
- **台帳の書き手は一人**: DE 台帳は `egl.de_admission` 経由のみ。手動 append しない。
- **権限境界で止まる**: `:8005`/GPU/commit/push/broad claim は REQUIRES_APPROVAL。承認は 1 コンテキスト限り、次には持ち越さない。
- **5 repo git 規律**: cross-repo 変更後は各 repo 個別に commit+push、全 repo の ahead/behind を 0/0 で検証。片方だけ push しない。
- **計測事実のみ**: 未計測は未計測、失敗は失敗と記録（retention > detection）。

---

*更新方法: 実装が進んだら本書の §2（できること）/ §4（できないこと）/ §5（ロードマップ）を該当 ITEM の DONE に合わせて更新する。数値（DE 番号・artifact 数・phase 状態）は `management_packet` の coverage matrix から取れる。*
