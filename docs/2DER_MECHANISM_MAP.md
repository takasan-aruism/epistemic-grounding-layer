# 2DER 機構マップ — 接続 / 記帳 / 参照 / 進行（常設・正典）

- **目的**: **我々（Claude 群）が忘れても、システムが何であるかを復元できるようにする。**
- **Taka 直接発話**: 「**２DERにはどのようにしてアクセス、どのような仕組みで台帳の記帳、参照が行われるようになってる？ ここが固まっていれば今後あなた方が健忘してもシステムは不変**」
- 作成: 設計/監査(CC-α) / 2026-07-27 / **常設（日付で版を切らない。訂正は本文書を書き換える）**
- **規律**: 散文で説明しない。**表と経路と再現手順で書く。** **`【読】`＝ソースを読んだだけ／`【実】`＝実行して確かめた／`【未確認】`＝どちらもしていない。**
- **【未確認】を消さないこと。** **「無い」を書くこと。**

---

## 0. ★最初に読む3行（忘れたときはここから）
1. **入口は `submit()` ただ1つ。** 呼び方が3通りある（CLI / webui / 直叩き）。**3つは等価ではない。**
2. **書く側は構造化されている。読む側は front door から通っていない。** ——**この非対称が現在の姿である。**
3. **`twoder/ids.py::resolve` が全 ID を持ち主のストアへ解決する。** **しかし front door から到達する経路は無い。**

---

# 1. 接続 — どうやって入るか

| 入口 | 実体 | auth | task を作れるか | **task を進められるか** | 状態 |
|---|---|---|---|---|---|
| **CLI（正典）** | `python3 -m twoder.submit "<入力>"` | 不要 | **できる** | **★できない** | **【実】** IMPL が2回実行（exit=0・台帳 1179→1180→1181） |
| CLI（直起動） | `python3 twoder/submit.py "<入力>"` | — | **★起動しない** | — | **【実】** `ImportError: cannot import name 'eq' from 'operator'`。`twoder/operator.py` が標準ライブラリの `operator` を隠す |
| **webui** | `POST /api/submit`（body `{"raw": "..."}`） | **要**（HTTP Basic / user=`taka`） | できる | **できる** | **【読】** `webui.py:536`。**投入は未実行** |
| webui（進行） | `POST /api/run_next` / `/api/run_until_barrier` | 要 | — | できる | **【読】** `webui.py:565-598` |
| 直叩き | 各モジュールを直接 import | 不要 | — | — | **在るが使わない**（境界違反） |

**auth の詳細**【実】:
```
再現: stat -c '%n %U:%G %a %s' twoder/.access_token   → takasan:takasan 600 36 bytes
再現: ss -ltn | grep 8770                             → LISTEN 100.107.6.119:8770
コード: webui.py:43-59   AUTH_USER="taka" / パスワード = .access_token の中身（無ければ os.urandom(18).hex() で生成）
```
- **トークンは我々の手元で読める。Taka の資源は要らない。**
- **★トークンを文書・argv・ログに書かない。**

### 1-1. ★CLI と webui が等価でない理由（重要・忘れやすい）
```
webui.py:29-32   run-gate: RUN NEXT は「直前の submit が生んだ runnable な task」だけを進める
webui.py:545     _LAST.update(...)   ← webui プロセス内の /api/submit でのみ設定される
webui.py:571     refuse = (gate["blocked"] or not gate["runnable"] or tid != gate["task_id"])
```
- **`_LAST` はプロセス内変数である。** **CLI は別プロセスなので `_LAST` を設定しない。**
- **∴ CLI が作った task は、webui の RUN NEXT からも進められない。** **【未確認】**（コードからの推論。実測は Build 9C 段0 で行う）
- **run-gate は安全機構である。迂回しない。**

---

# 2. 記帳 — どうやって書かれるか

## 2-1. `submit()` が通る段（順）【読】
| 段 | 内容 | 呼ぶもの | 記録先 |
|---|---|---|---|
| **ts 確定** | `submit` は ts を**生成せず受領**する。未指定なら既定値。**既定に落ちた事実を先に記録**（`ts_source`） | — | 段1 に含む |
| **1. DS** | 発話を出来事として記録。同一 conversation の直前発話 id も記録 | `ds.phase0.record_utterance("USER", raw, conversation_id, ts, ...)` | **`ds_events.jsonl`**（`DS_DATA_DIR` 既定=`ds/`） |
| **1.5 DE admission fast path** | 開発証拠の登録依頼を検出したら、DS→RRI(分類)→EGL admission→RRI残余→DS thread で完結。**Qwen も DW も通らない** | `AR.detect(raw)` → `egl.de_admission.admit_design_evidence(...)` | **`egl/DESIGN_EVIDENCE_LEDGER.jsonl`** |
| **2. RRI 文脈束縛** | DS packet を DATA CONTRACT として受け、`anchoring` を出す（UNRESOLVED/LOW/MEDIUM/HIGH） | `rri.context_binding.bind_context(...)` | TRACE |
| **3a. EGL 接地** | 現在/過去の主張・実測状態・gap を出典つきで引く | `egl.self_grounding.answer_question(...)` | TRACE |
| **3b. RRI 要求種別** | 何をしてほしいか（6種） | `rri.request_type.classify_request_type(...)` | TRACE |
| **3c. 死んだ手法ガード** | CLOSED-NEGATIVE の復活を拒否。出典 DE を引く | — | `SELECTED_ACQUISITION_METHOD=BLOCKED_DEAD_APPROACH` |
| **3d. PREFLIGHT GATE** | 曖昧な数量主張・未接地の参照で**止める**。決定論・LLM 不使用 | `rri.preflight_gate.detect(raw, failure_hits=...)` | `RRI_PREFLIGHT_HOLD` |
| **3e. RRI 意図戦略** | どう応じるか（7戦略）。**3d を通過した入力でのみ呼ぶ** | `rri.intent_strategy.resolve(...)` | TRACE |
| **4. ROUTING** | 8種の `SELECTED_ACQUISITION_METHOD` に振る | — | TRACE / DW |
| **7. FAILURE_MEMORY_GUARD** | 通常経路の**後**に read-only で参照。**判断を置き換えず注記のみ** | — | TRACE |

**★3e のコード内注記（逐語・忘れやすい）**: 「**暫定の単純化: 「1つの問い合わせ = 1つの明細」の前提で通している**」

## 2-2. `SELECTED_ACQUISITION_METHOD` は8種【読】
```
再現: grep -n "SELECTED_ACQUISITION_METHOD" twoder/submit.py
EGL_DE_ADMISSION / BLOCKED_DEAD_APPROACH / RRI_PREFLIGHT_HOLD / WEB_RESEARCH_ACQUISITION /
RUNTIME_INSPECTION / RESUME / DW_IMPLEMENTATION / EGL_RESEARCH
```
**★このうち帳簿の中身を読んで返すものは1つも無い。**

## 2-3. 台帳ごとの「唯一の書き手」【読】
| 台帳 | 書き手 | 場所 |
|---|---|---|
| `DESIGN_EVIDENCE_LEDGER.jsonl` | **`egl.de_admission.admit_design_evidence`** — docstring 逐語: *"The **ONLY** sanctioned writer"* | `egl/` |
| `ds_events.jsonl`（発話・対話事象） | `ds.phase0.record_utterance` ほか | `ds/`（`DS_DATA_DIR`） |
| DW イベント | `dw.workcell`（`create_task` / `record_plan` / `record_generate` / `record_audit` / …） | `dev-workcell/`（`DW_DATA_DIR`） |
| `ARTIFACT_REGISTRY.jsonl` / `CHANGE_LOG.jsonl` | **`twoder.artifact_registry.register` / `record_change`** | `twoder/audit/` |
| `rri_records.jsonl` | RRI | `rri/` |

**`artifact_registry` docstring 逐語（配置の規律）**:
> *"No substantive file may be used/changed/cited/tested/committed in a 2DER slice unless it has a stable 2DER-issued ARTIFACT_ID that resolves NOW to its repo/path/hash/commit. **File paths and prose are not reliable across sessions; artifact records are.**"*

## 2-4. ★誰が書けて、誰が書けないか【読】
| 主体 | production repo へ書けるか | 根拠 |
|---|---|---|
| **Qwen worker** | **★書けない（三重に閉じている）** | `build_planner.py:59` `PROD_REPO_ROOTS` に5リポジトリ／`:254` で決定論的に REJECT ／ `qwen_worker._safe_target_path` が絶対パス・`..`・symlink を拒否／`live_worker_scaffold._MUST_BE_TRUE` に `host_filesystem_unreachable` |
| **Claude** | **書ける。そして Taka が明示的に許している** | Taka 逐語「プログラムを**外注で生成、配置するまで**」 |
| **Claude（台帳を直接）** | **★禁止** | Taka 逐語「台帳は今後２DERを通さないと読めない、書き込めない」 |

**∴ worker が production に置けないのは欠落ではない。サンドボックスの保証である。**
**∴ 配置は Claude の役割であり、`register`+`record_change` に記録が残る場合に限る。**

## 2-5. 勘定科目の決まり方【読】
**2つの別系統がある。混同しないこと（MGR も私も一度混同した）。**
| 系統 | 実体 | 結論 |
|---|---|---|
| (A) 決定論マイニング | `egl/structure/s_mine_accounts.py` | **`chart_status = NO_STABLE_STRUCTURE`。chart を捏造せず終わっている。正当な結論** |
| **(B) 埋め込み軸（本体）** | `s_embed_axes` → `s_account_axes` → `s_rthread_2br3` → `s_account_axis_names` | **軸を埋め込みで発見 → silhouette で決定論裁定 → Taka 承認で版を上げる → LLM 3-seed consensus で命名** |

- **所属は絶対 cosine 閾値を使わない。負の制御に対する相対で決める**（コード逐語: 「**裁定A: 幻覚的絶対定数の禁止**」）。
- **全軸が閾値未満＝「その他」。** **これが「未定」に相当する。仮勘定という機構は存在しない。**
- **「凍結」＝軸集合と方向ベクトルの版の固定。** **科目は増える。増やす（版上げ）時だけ Taka 承認が要る**（`FREEZE_APPROVALS.jsonl`）。
- **★「無い科目を作らない」は誤り。** **account chart そのものは触らない。**

---

# 3. 参照 — どうやって読まれるか

## 3-1. `twoder/ids.py::resolve(rid)` が正典の読み口【読】
**docstring 逐語**:
> *"2DER canonical ID resolver (DE-0180). Every 2DER-issued id resolves through here to its owning store's real record. … **an id that does not resolve is a hole, not something to fill from memory.**"*

| 接頭辞 | 持ち主 | 解決先 |
|---|---|---|
| `UTT-` / `DEV-` / `THREAD-` | DS | `ds.phase0.utterances()` / `dialogue_events()` |
| `OBS-` `SRC-` `ARUN-` `RUN-` `LEG-` `SNAP-` | EGL | `egl.core.get_state(rid)`（**`{}` は `None` に落として「未解決」を保つ**） |
| `DE-` | EGL | `DESIGN_EVIDENCE_LEDGER.jsonl` を走査 |
| `ADM-` | EGL | `egl.de_admission.resolve_admission` |
| `RREQ-` / `RINT-` / `RSIG-` | RRI | `rri.intent_record.resolve` |
| `TASK-` | DW | `dw.workcell._read_events` / `derive_state` |
| `ART-` / `CHG-` | twoder | `artifact_registry.resolve` / `resolve_change` |
| `ROADMAP-` `PHASE-` `ITEM-` `AMEND-` | twoder | `roadmap_registry.resolve` |
| `INTV-` | twoder | `intervention.resolve` |
| `AUTHP:` / `AUTHD:` | twoder | `authority.resolve_policy` |

**【未確認】** `resolve()` を**実行していない**。**読んだだけである。**

## 3-2. ★★ここが最も重要な行 — **front door から台帳を読む経路は無い**【読】
```
再現: grep -rn "LEDGER_QUERY\|ledger_query\|READ_LEDGER" --include=*.py twoder/ rri/ ds/ dev-workcell/
     → 0件
再現: grep -n "SELECTED_ACQUISITION_METHOD" twoder/submit.py
     → 8種すべて。帳簿の中身を読んで返すものは1つも無い
```
- **∴ 「この ID に何が記帳されているか」を front door に聞くと、`OBSERVE_CURRENT_STATE` と読まれ `RUNTIME_INSPECTION` へ行く。**
- **`runtime_inspection.build_request` は `information_need` を選別に使わず、`_CATALOG` 全件（GPU / コンテナ / プロセス / ポート）を実行する。**
- **∴ 何を聞いても GPU の空きメモリとコンテナ一覧が返る。** **該当が無いときに「無い」を返す機構が無く、全件にフォールバックする。**

> **∴ 我々が台帳を直読するのは、規律が緩いからではない。読む経路が存在しないからである。**

---

# 4. 進行 — 誰が動かすか

## 4-1. `submit()` はループを進めない【読】
```
再現: grep -n "dispatch_once\|run_until_barrier" twoder/submit.py   → 0件
```
**∴ `submit()` は DW task を作って返るだけである。**

## 4-2. 進めるのは誰か【読】
| 呼び出し元 | 何か |
|---|---|
| `twoder/webui.py:592` / `:598` | **RUN NEXT / RUN UNTIL BARRIER ボタン**（`_machine_registry()` を渡す） |
| `twoder/operator.py:151` | 運転者ループ（**このファイルが標準ライブラリの `operator` を隠している**） |
| `tools/codegen_run_fn.py` ほか | 道具・試験 |

## 4-3. ★PLAN の actor が Qwen になる条件 / ならない条件【読】
```
dispatch.py:29   "CREATED": ("PLAN", "MANAGER", "GOAL+KNOWLEDGE_PACKET", True)   # 末尾 True = claude_barrier
dispatch.py:42   "MANAGER": "CLAUDE"                                            # ← 既定値にすぎない
dispatch.py:91-107
   ① PT.plannable(task_id) が True → 決定論テンプレで PLAN（限定 subset のみ）
   ② actors["BUILD_PLANNER"] が在る → Qwen planner が PLAN を作り自分で検証し、
      validate_plan を通った時だけ record_plan する
   ③ 拒否 → recorded=False → **Claude barrier に fail-closed**
webui.py:225  _machine_registry() = {"CODING_WORKER", "INDEPENDENT_AUDITOR", "MANAGER", "BUILD_PLANNER"}
```
**コード逐語**: *"This keeps Claude off the runtime PLAN path without adding a parallel pipeline."*

**∴ `actor=CLAUDE` は状態表の既定値であって、実行時の判断ではない。**
**∴ PLAN の「仕事」は既に Qwen。残っているのは「引き金」だけである。**

**`validate_plan` の決定論拒否条件**（`build_planner.py:217-255`）:
- provenance が解決しない / 出力が壊れている / **`target_workspace` が未指定** / **`target_workspace` が production repo**（`PROD_REPO_ROOTS`）/ test・完了条件が無い / 未認可の破壊的操作（`DESTRUCTIVE_MARKERS`）

## 4-4. 【未確認】
- **Qwen planner が我々の依頼を実際に PLAN できるかは、まだ一度も測れていない**（CLI 投入では進まないため）。**Build 9C で測る。**
- `AUTH.gate("DW_MACHINE_DISPATCH")` が `auto` を返すか（コメントは AUTO_EXECUTE と書いているが**未実行**）。

---

# 5. 「無い」の一覧（最も重要・埋める順に）
| # | 無いもの | 影響 |
|---|---|---|
| **N1** | **front door から台帳を読む経路** | 我々が直読を続ける構造的原因 |
| **N2** | **DS の選別**（空 / 無意味 / 意味の薄い投稿の機械的検知） | **DS は「受付」でなく「記録係」。** 空入力は判定されず `ds/phase0.py:101` の `ValueError` で落ちる |
| **N3** | **DS の「繋がない理由を返す」** | 黙って進む |
| **N4** | **CLI から task を進める経路** | 投入した仕事が一歩も進まない |
| **N5** | **front door の結果が設計/監査へ自動で届く経路** | 3回続けて「我々が自分で読みに行った」 |
| **N6** | **長文を明細に分解する段** | 「1問い合わせ=1明細」の暫定のまま |
| **N7** | **`information_need` による acquisition の選別** | 何を聞いても同じ4件が返る |

---

# 6. 本文書の限界（消さない）
- **`ids.resolve()` を実行していない。** §3 は**読んだだけ**である。
- **webui への投入を実行していない。** §1 の webui 行は**読んだだけ**である。
- **「CLI の task は webui からも拒否される」は推論である**（§1-1）。
- **`boundary_failures` の中身を確認していない。**
- **DS の `reconstruct_snapshot failed: HTTP 400` は未調査。**
- **本文書は 2026-07-27 時点の姿である。** **コードが変わったら本文書を書き換える。日付で版を切らない。**

---
*2DER 機構マップ（常設・正典）。★3行要約=入口は `submit()` 1つで呼び方が3通り（等価でない）／書く側は構造化され読む側は front door から通っていない／`ids.py::resolve` が全 ID を解決するが front door から到達しない。1 接続=CLI は task を作れるが進められない・`python3 twoder/submit.py` は `operator.py` の shadowing で起動しない（実測）・webui は Basic Auth（token は手元で読める）・`_LAST` がプロセス内変数のため CLI の task は webui からも進められない（推論）。2 記帳=submit の段（ts受領→DS記録→DE admission fast path→文脈束縛→EGL接地→要求種別→死んだ手法ガード→PREFLIGHT→意図戦略→ROUTING→failure memory）と台帳ごとの唯一の書き手（DE 台帳は `de_admission` が ONLY writer、配置は `artifact_registry`）。worker は production repo に三重に閉じられ書けない＝欠落でなくサンドボックスの保証、配置は Claude の役割で登記が残る場合に限る。勘定科目は埋め込み系統(B)が本体で決定論マイニング(A)の NO_STABLE_STRUCTURE と混同しない、「その他」が未定に相当し仮勘定は無い、凍結は版の固定で科目は増える。3 参照=`ids.resolve` の接頭辞対応表（未実行）。★最重要行=front door から台帳を読む経路は無い（acquisition 8種に無く、聞けば `_CATALOG` 全件が返る）＝直読は規律でなく経路の欠落。4 進行=`submit()` はループを進めず、進めるのは webui の RUN NEXT と `operator.py`。`actor=CLAUDE` は既定値にすぎず `BUILD_PLANNER` 登録済なら Qwen が PLAN を書き、拒否時のみ Claude barrier に fail-closed。5「無い」の一覧 N1〜N7。6 限界=ids.resolve も webui 投入も未実行、日付で版を切らず訂正は本文書を書き換える。*
