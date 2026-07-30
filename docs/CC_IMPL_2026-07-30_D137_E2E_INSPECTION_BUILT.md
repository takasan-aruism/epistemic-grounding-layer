# 【BUILT】Phase 4 第一弾 — 2DER 単体 End-to-End 性能検査（★投入1回・★止まった所で終了）

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-30 22:4x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- **★実装源**: `CC_DESIGN_2026-07-30_D137_BUILD_SPEC_E2E_EVIDENCE_PLAN.md`（★これ1本）／**正典**: `TAKA_2026-07-30_PHASE4_E2E_INSPECTION_ORDER.md`
- **受領した MGR 文書の一覧**: **★無し**（役割板に `CC_MGR_HANDOFF_2026-07-30.md` が出たが、MGR 文書から着手しない規律により読んでいない）
- **★`:8005` を使った**（★私が投げたのではない。**★投入が 2DER 内部で4件 呼んだ**。§6 に実測）

---

# 0. ★報告は表から（正典 §報告形式）

**★判定欄は IMPL の記入であって確定ではない。**（SPEC §3「判定を確定しない」と §4「6区分で表を出す」が2通りに読めたため、**★6区分で埋めた上で「確定は設計/監査」と明記する**形にした。**★読み違えていたら差し戻してほしい**）

| 順 | 工程 | 判定 | actor | 主な証拠ID | 備考 |
|---|---|---|---|---|---|
| 1 | 受付 | **PROVEN** | **人(IMPL)が投入 → 2DER が受理** | `receipt.last_recv_at=22:30:24.891921` / `recv_count 70→71` | ★私の POST は `22:30:24.886058`＝**差 5.9ms で一致**。★入力内容は receipt から引けない |
| 2 | ID 発行 | **FAILED** | 2DER | `task_id=null` / `trace_key=SUBMIT-zOlryQ` → `resolve: resolved=false` | **★最初の停止点。**★「壊れている」のか「OBSERVE 経路の設計どおり」なのかは**★私は確定しない** |
| 3 | RRI | **PROVEN** | 2DER (RRI) | `request_type=OBSERVE_CURRENT_STATE` / `acquisition_method=RUNTIME_INSPECTION` | 呼ばれた証拠(値が在る)＋後工程へ渡った証拠(取得方式が決まった)。同区間に `:8005` 呼び出し4件 |
| 4 | 計画 (PLAN) | **NOT_REACHED** | — | — | **★`plan_source`=該当なし / `runtime_recovery`=該当なし（★PLAN が1度も起きていない）**。`claude_packet` は `task_id` 必須で引けない |
| 5 | 実行命令生成 | **NOT_REACHED** | — | — | PLAN が無い。★実際に打たれた4コマンドは planner 生成ではなく **adapter 内蔵** |
| 6 | 実環境での取得 | **OBSERVED_UNATTRIBUTED** | 記録上は `read-only DW executor` | `ARUN-00954`〜`ARUN-00957` | command / host / 時刻は**特定できる**。★正典の「**2DERが生成した指示によって**」が**不成立**（命令の出所が planner でない） |
| 7 | 出力取得 | **FAILED** | 同上 | `measured_state` / `OBS-00955`〜`OBS-00958` | **★5項目中 GPU使用率が取得不能。**直接原因＝`--query-gpu` に `utilization.gpu` が無い（§4） |
| 8 | 検証 | **NOT_REACHED** | — | — | AUDIT は DW task の工程。task が無い。**★出力はそのまま応答に載った**（正典 §6 の不成立条件に当たる） |
| 9 | 記録 | **FAILED（ID 接続）** | 2DER | `OBS-`/`ARUN-`/`SRC-` は resolve 可 ／ `ds_events.jsonl`・`rri_records.jsonl`・`egl data/events.jsonl` が更新 | **★1つの task_id から辿れない（★そもそも task_id が無い）**。○/× は §5 |
| 10 | DW 要約 | **NOT_REACHED** | — | `/api/control` は在る（叩いた） | ★今回の要求に紐づく要約は**引けない**。`/api/control` は roadmap/DE 台帳の集計面であって本件の要約ではない |
| 11 | ユーザ返答 | **FAILED** | 2DER (submit 応答) | `measured_state`（21行の配列） | ★返るには返る。**★要約ではなく生の配列**。★GPU使用率が欠落したまま |

---

# 1. ★投入（★1回だけ・★打ち直していない）
```
字数 54 / sha1 0c458f38c8c98b985a91974773329c0032275aa0
現在のGPU使用状況を取得し、GPUごとの使用率、VRAM使用量、実行中プロセスを確認して要約してください。
```
| | |
|---|---|
| 入口 | **`POST /api/submit`**（★webui 経路・1回） |
| 投入時刻 | **直前 `22:30:24.886058` / 直後 `22:30:31.555002`**（JST） |
| 応答 | **★全文 保存した**（`-o /dev/null` を使っていない）。`task_id=null` / `runnable=false` / `blocked=false` |
| **★直後に叩いた口** | **`GET /api/receipt`**（★他の口を1つも叩く前に。SPEC §1-2 の順を守った） |
| 再投入 | **★していない** |
| `run_next` | **★1回も押していない。**★`task_id` が `null` で、押す対象が無い（別 task を押すのは迂回になるのでしない） |

---

# 2. ★検査開始前に保存した既存状態（正典 §Claude Codeの役割 ①⑦）
```
ds  6f93f8a(main)  rri 564d0f4(main)  egl 49ff25c(main)  dev-workcell 450566f(master)  twoder 760820c(master)
★5 repo とも 未commit 0 で開始
webui: PID 3814663 / 起動 07-30 12:44:07
  ★ソース mtime は webui.py 12:42:01・submit.py 07-29 23:57・build_planner.py 07-15・dispatch.py 07-29 23:56
  ∴ ★稼働プロセスは現行ソースより後の起動＝現行ソースで動いている（★再起動していない）
receipt 基準値: last_recv_at=2026-07-30T19:31:13.080517 / recv_count=70
```
**★検査開始のために行った操作（正典 §実施条件の記録義務）**
| 操作内容 | 操作者 | 理由 | 既存運用か | 主体判定への影響 |
|---|---|---|---|---|
| `POST /api/submit` **1回** | **実装(IMPL)** | 検査課題の投入 | **既存運用**（通常の入口） | **★2DER の担当工程として数えない** |

**★設定変更・コード変更・再起動・新規ファイル（スクリプト含む）は1つも行っていない。**

---

# 3. ★2DER が実際にやったこと（★応答から）
```
request_type            = OBSERVE_CURRENT_STATE          ← ★RRI が分類した
acquisition_method      = RUNTIME_INSPECTION             ← ★後工程へ渡った
runtime_inspection_status = OBSERVED
host_ref                = takasan-System-Product-Name
egl_source_refs         = OBS-00955 / OBS-00956 / OBS-00957 / OBS-00958
next_legal_operation    = "RUNTIME_INSPECTION executed -> observation ingested to EGL
                           (GPU task NOT auto-resumed; 2DER re-evaluates focus on next intent)"
task_id                 = null      ← ★DW の task は作られていない
```

## 3-1. ★取得は「検査時点の実測」か → **★実測である**
```
ARUN-00954 started_at 2026-07-30T13:30:30.840270+00:00 = ★JST 22:30:30.840
                                                          （★私の投入 22:30:24.886〜22:30:31.555 の★内側）
           finished_at 13:30:30.931150+00:00
```
> **★保存済み情報ではない。★投入から約6秒後に走っている。**

## 3-2. ★実際に打たれたコマンド（★4本・全件）
| ARUN | command | 結果 |
|---|---|---|
| `ARUN-00954` | `nvidia-smi --query-gpu=index,memory.used,memory.total,name --format=csv,noheader,nounits` | SUCCESS / OBSERVED |
| `ARUN-00955` | `docker ps --format {{.Names}}::{{.Status}}::{{.Image}}` | SUCCESS / OBSERVED |
| `ARUN-00956` | `ps -eo pid,rss,comm --sort=-rss` | SUCCESS / OBSERVED |
| `ARUN-00957` | `ss -ltn` | SUCCESS / OBSERVED |
```
adapter = ACQ_MANUAL / adapter_version = local-runtime-0
target_locator = localhost-runtime://takasan-System-Product-Name/nvidia-smi
measurement_condition = "read-only DW executor"
```
**★工程5 の確認（投入文に命令が無いことの完全一致）**: `nvidia-smi` / `docker` / `ps ` / `ss ` / `--query-gpu` のいずれも**★投入文に0件**。
**★ただしこれは「planner が作った」ことの証拠ではない。★命令は adapter 内蔵の定型である。**

---

# 4. ★取得5項目（正典 §5・★空を成功にしない）
| 項目 | 取れたか | 実測値 |
|---|---|---|
| GPU 識別情報 | **○** | `NVIDIA GeForce RTX 5090` ×2（GPU 0 / GPU 1） |
| **GPU 使用率** | **★取得不能** | **★無い**（★`--query-gpu` に `utilization.gpu` が入っていない＝`ARUN-00954` の command で確定） |
| VRAM 総量 | **○** | `32607 MiB`（両 GPU） |
| VRAM 使用量 | **○** | GPU0 `30520` / GPU1 `31168` MiB |
| GPU に関連する実行中プロセス | **★部分的（不十分）** | プロセス一覧は在る（`VLLM::Worker_TP` ×2 / `vllm` / `VLLM::EngineCor` ほか）が、**★`ps -eo pid,rss,comm` の RSS 順であって GPU への紐付けが無い**（★どの GPU の VRAM をいくら使っているかは無い。★`claude` プロセスも同列に並ぶ） |

> **★正典「一部取得不能の場合は、空値を成功扱いせず、取得不能として明示する」に従い、★工程7 は不成立と書く。**
> **★私は不足を補っていない。★`nvidia-smi` を自分で叩いていない。**

---

# 5. ★台帳・Event Trace 評価（正典 §7・★1つずつ ○/×）
**★起点にすべき task_id が無いので、「1つの task_id から辿る」という条件は★入口で成立しない。**
以下は**★私の手元にある submit 応答**を起点にした場合の到達可否である（★これ自体が「記録から辿った」ではない）。

| 到達先 | ○/× | 根拠 |
|---|---|---|
| 入力（発話記録 `UTT-`） | **×** | 応答に DS の入力 ID が無い。★引く手がかりが無い |
| RRI | **△** | 応答には値が在る（`request_type`/`acquisition_method`）が、**★記録から ID で引く経路が無い** |
| 計画 | **×** | 起きていない |
| 実行 | **○** | `ARUN-00954`〜`00957` が `resolve` で引ける（command・host・時刻つき） |
| 生出力 | **×** | `OBS-` は `raw_content_hash` と `blob://…` を返すが、**★blob の中身を引く口が無い** |
| 検証結果 | **×** | 存在しない |
| DW 入力 | **×** | 存在しない |
| 最終結果 | **×** | `submit` 応答が事実上の最終結果。**★ID で引けない**（`trace_key` は `resolved=false`） |

**★書き込みは起きている**（★ファイル名のみ確認・中身は読んでいない）:
```
ds/ds_events.jsonl   rri/rri_records.jsonl   egl/data/events.jsonl   ← ★検査前は5 repo とも 未commit 0 だった
```
**★actor 欠落**: 取得の actor は `read-only DW executor` と記録されているが、**★「誰が命令を決めたか」を示す actor が無い**。
**★ID 接続切れ**: `SUBMIT-zOlryQ` が `resolve` で `resolved=false`。**★入口の ID が解決できない。**

---

# 6. ★モデルサーバ側の記録（正典 §監視・証拠「model server call log」）
```
窓 JST 22:30:20〜22:30:40（= UTC 13:30:20〜13:30:40）★打ち切り無し
  13:30:25.179Z  "POST /v1/chat/completions" ★400 Bad Request
  13:30:30.088Z  "POST /v1/chat/completions" 200 OK
  13:30:30.547Z  "POST /v1/chat/completions" 200 OK
  13:30:30.798Z  "POST /v1/chat/completions" 200 OK
  → 計4件（★うち1件は 400）。★直後 13:30:30.840 に nvidia-smi が走っている
```
- **★投入は 2DER 内部で `:8005` を4回 呼んだ。★私は1件も投げていない。**
- **★毎回 400 が1件 出る**：同型（`400`×1＋`200`×n）が **19:11 / 19:13 / 19:31 / 22:30** に在る。**★直していない・掘っていない。**

## 6-1. ★前回報告（D-133）の窓の読みが1つ進んだので書く
```
本日の receipt 基準値 last_recv_at = 19:31:13.080 / last_sent_at = 19:31:24.919
  ＝ D-133 で「窓の1分前の別のかたまり」と書いた 19:31:13〜19:31:24 の7件と★時刻が一致する
∴ ★あのかたまりは「/api/submit の呼び出し」であった可能性が高い（★同型の並びが今回も出た）
∴ ★D-133 の窓（19:32:13〜34）の2件は、★submit 由来ではない
```
**★これは補強であって、D-133 の記述の訂正ではない**（★あのとき「誰の通信か分からない」と書いたのは、その時点では正しい）。

---

# 7. ★最終結果（正典 §報告形式 1〜6）

### 1. 最終結果
**★一周 不成立。** **最後に成立した工程 = 3（RRI）。** **最初に成立しなかった工程 = 2（ID 発行）。**
**★検査終了条件 B（最初の停止点の確定）で完了。**

### 2. ★実際に 2DER が担当した工程（★証拠で主体を示せるものだけ）
| 工程 | 証拠 |
|---|---|
| **3 RRI**（分類と取得方式の決定） | `request_type=OBSERVE_CURRENT_STATE` / `acquisition_method=RUNTIME_INSPECTION` ＋ 同区間の `:8005` 4件 |
| **6 取得の実行** | `ARUN-00954`〜`00957`（command / host / 時刻 / `read-only DW executor`） |
| **9 記録の書き込み** | `ds_events.jsonl` / `rri_records.jsonl` / `egl data/events.jsonl` が更新（★中身は読んでいない） |

### 3. ★人または Claude が担当した工程（★省略しない）
```
★POST /api/submit を1回 押した（実装(IMPL)）。★これだけである
★run_next は押していない（task_id が無い）
★計画・コマンド選択・コマンド修正・実行・出力整形・検証・台帳登録・DW入力・要約補筆は★1つも行っていない
★GPU を自分で測っていない（nvidia-smi を叩いていない）
```

### 4. 台帳・Event Trace 評価 → **§5 の表**（★到達 1/8・△1・×6）

### 5. ★停止原因（正典の区分から）
**★ID 接続不全。** 直接原因は次の連鎖である（★すべて応答で確認できる）:
```
RRI が OBSERVE_CURRENT_STATE と分類 → RUNTIME_INSPECTION 経路へ → ★この経路は DW task を作らない
→ task_id=null → PLAN/GENERATE/AUDIT/DW要約 は★到達しない → 1つの ID から辿る記録が成立しない
```
**★併せて（工程7 の別原因）**: **環境情報不足**。`--query-gpu` の項目に `utilization.gpu` が無く、プロセスは GPU に紐づかない `ps` 出力である。
**★「配線が無い」とは書かない。**（PLAN 以降の配線は在る。★今回の実行では呼ばれていない＝到達していない）

### 6. ★次の最小修正候補（★1件だけ・★実施しない・★確定は設計）
> **`OBSERVE_CURRENT_STATE`／`RUNTIME_INSPECTION` 経路にも、応答に返している `trace_key` を `resolve` で引ける ID として1つ通す。**
> **★新しい台帳は作らない。★既存の `/api/resolve` に、既に応答へ返している ID を1つ通すだけ。**
> **理由: 最初の停止点は「取得できなかった」ではなく「★起きたことを ID で辿れない」である。** ★これが通らない限り、工程9 の評価は毎回 入口で不成立になる。
> **★GPU 使用率の欠落（工程7）は別件である。★1件だけ出す指示に従い、ここでは出さない。**

---

# 8. ★やっていないこと（SPEC §3 に1つずつ）
```
★nvidia-smi など GPU を自分で測っていない          ★取得方法を補完していない・コマンドを選んでいない
★出力を整形していない・要約を書き足していない       ★スクリプトをファイルとして作っていない
★止まった後に直していない・迂回していない・再投入していない
★production repo を1行も変えていない               ★commit していない
★台帳を直読していない（★§5 の書き込みは★ファイル名のみ確認）
★判定を確定していない（★§0 の判定欄は記入であって確定ではない）
```

---
*IMPL → 設計/監査（写: MGR / Taka）。Phase 4 第一弾 E2E 検査の結果。**投入は正典から機械抽出した依頼文（54字 / sha1 `0c458f38…`）を `POST /api/submit` で1回のみ、直後に `GET /api/receipt`（一致 5.9ms・`recv_count` 70→71）。** 結果は**一周 不成立**で、**最後に成立した工程=3 RRI／最初に成立しなかった工程=2 ID 発行（`task_id=null`・`trace_key` は `resolve` で `resolved=false`）**＝**終了条件 B（最初の停止点の確定）**。RRI は `OBSERVE_CURRENT_STATE`→`RUNTIME_INSPECTION` を決め（同区間に `:8005` 呼び出し4件・うち1件は 400）、**投入の内側 22:30:30.840 に実測取得が走った（保存済みではない）**。打たれたのは `nvidia-smi --query-gpu=index,memory.used,memory.total,name` / `docker ps` / `ps -eo pid,rss,comm` / `ss -ltn` の4本で、**adapter 内蔵の定型＝planner 生成ではない**（投入文にコマンド文字列は完全一致で0件）。**取得5項目は GPU使用率が取得不能・プロセスは GPU 紐付け無し ∴ 工程7 不成立（空を成功にしない）**。PLAN/GENERATE/AUDIT/DW要約/返答は task が無いため到達せず、**`plan_source`・`runtime_recovery` は該当なし**。記録は `OBS-`/`ARUN-`/`SRC-` が resolve で引け ds/rri/egl の3台帳が更新されたが、**入口の ID が解決できず1つの task_id から辿れない＝停止原因は ID 接続不全**（工程7 は別に環境情報不足）。**人・Claude がやったのは `POST /api/submit` 1回だけで、run_next は押していない。GPU を自分で測らず、直さず、再投入せず、commit していない。** 最小修正候補は1件のみ（`trace_key` を既存 `resolve` に通す・実施しない）。**判定欄は IMPL の記入であって確定ではない（SPEC §3 と §4 が2通りに読めたため両立させた。読み違えなら差し戻しを）。***
