# 【BUILT】第2試行 — `trace_key` の ID 接続修正と同一 E2E 再検査（★2工程 前進・★次の停止点を確定）

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 00:0x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）** / **実装源**: `CC_DESIGN_2026-07-30_D140_BUILD_SPEC_TRACEKEY_RESOLVE.md`（進行許可: `D140_ANSWER…` §3 ／ `D141_VERIFIED_PROCEED`）
- **受領した MGR 文書**: **無し**（設計経由で受けた）
- **★2DER 優先原則の例外**（正典 §9 で IMPL が書くと明示）。**★この修正を「2DER が担当した工程」に数えない。★1/8 は動かない。**
- **`:8005` を使った**（★私は1件も投げていない。**★投入が 2DER 内部で4件 呼んだ**）

---

# 0. ★比較表（正典 §8・★説明より先に）

| 工程 | 第1試行 | 第2試行 | 変化 | 主な証拠ID |
|---|---|---|---|---|
| 1 受付 | PROVEN | **PROVEN** | **★入力内容が記録から引けるようになった**（第1試行は receipt に無く不可） | `receipt 23:51:06.865135` ／ POST `23:51:06.858723` ／ `recv_count 71→72` |
| 2 ID 発行 | **FAILED** | **★PROVEN** | **★これが今回の修正対象。`false→true`** | `SUBMIT-_ayfew`（`resolved=true`） |
| 3 RRI | PROVEN | **PROVEN** | **★記録から引けるようになった**（第1試行は応答にしか無かった） | `request_type=OBSERVE_CURRENT_STATE` ／ `ETR-d19f46b8ddd3`(21 event) |
| 4 計画 | NOT_REACHED | **NOT_REACHED** | 変化なし | `dw_task_ref=None` |
| 5 実行命令生成 | NOT_REACHED | **NOT_REACHED** | 変化なし | — |
| 6 実環境での取得 | OBSERVED_UNATTRIBUTED | **OBSERVED_UNATTRIBUTED** | 変化なし（★同じ4コマンド） | `ARUN-00958`〜`00961` |
| 7 出力取得 | FAILED | **FAILED** | 変化なし（★GPU使用率 0件） | `OBS-00959`〜`00962` |
| 8 検証 | NOT_REACHED | **NOT_REACHED** | 変化なし | — |
| 9 記録 | **FAILED** | **★PROVEN** | **★1つの `trace_key` から6点すべてへ到達** | `SUBMIT-_ayfew` → `UTT-1012`／`ETR-`／`ARUN`／`OBS` |
| 10 DW 要約 | NOT_REACHED | **NOT_REACHED** | 変化なし | — |
| 11 ユーザ返答 | FAILED | **FAILED** | 変化なし（★生の配列・使用率欠落） | `measured_state`（21行） |

> **★判定欄は IMPL の記入であって確定ではない**（設計が確定する。SPEC §7 で「書いてよい」と明示された）。

---

# 1. 修正結果 → **★成功**

| | |
|---|---|
| 変更ファイル | **`twoder/ids.py` ★1本のみ** |
| 変更行 | **59行 追加のみ**（削除0）。① docstring に `SUBMIT-` を1行 ② `_resolve_submit_trace()` を追加 ③ `resolve()` に分岐を1つ（★prefix 一覧の最後尾＝既存を隠さない） |
| 採った接続方式 | **(b) `trace_key` から既存の正典 record ID 群へ決定論的に解決する** |
| 選んだ理由（1行） | **(a) は `trace_key` を台帳へ登録する＝台帳に手を出すことになる。(b) は submit が既に書いている record を読むだけで済む** |
| **★作っていないもの** | **新しい台帳／新しい resolve API／今回専用の GPU 分岐／DW task 生成方式の変更／Planner の新設・強制起動／要約処理** |
| fail-closed | `return None` **9箇所**が正典 §3 の6条件に対応。**★`raw_input` を Event Trace の `ENTRY` と完全一致で照合**（「request との対応が曖昧」を機械で潰す） |
| commit | **★私はしていない**（MGR が `d988640 (UNAUDITED)` で commit 済） |

## 1-1. ★テスト（★走らせたものの名前と結果。★総数は書かない）
**T1（後方互換8件・★本番の口で取り直し・期待値は取る前に固定）**
| ID | 期待 | 実測 | |
|---|---|---|---|
| `ARUN-00954` | true/13 | true/13 | ○ |
| `OBS-00955` | true/10 | true/10 | ○ |
| `DE-0525` | true/10 | true/10 | ○ |
| `TASK-2DER-B11764B3` | true/3 | true/3 | ○ |
| `ETR-fdf52322e5bf` | true/5 | true/5 | ○ |
| `UTT-1010` | true/12 | true/12 | ○ |
| `SUBMIT-zOlryQ` | true | true/14 | ○ |
| `NO-SUCH-ID-XYZ` | false | false | ○ |

| test | 結果 |
|---|---|
| **T2** 未知の `trace_key` は失敗する | **○** `SUBMIT-zzzzzz` → `resolved=false` |
| **T3** 実在する `trace_key` が解決できる | **○** `SUBMIT-_ayfew` → `resolved=true` |
| **T4** 解決結果から入力内容を取得できる | **○** 依頼文と完全一致／`received_at=23:51:06.865333` |
| **T5** RRI 記録へ到達できる | **○** `rri.request_type` / `resolved_intent` / `ETR-d19f46b8ddd3`(21 event) |
| **T6** `ARUN`／`OBS` 参照へ到達できる | **○** `OBS-00959〜00962` ／ `ARUN-00958〜00961` |
| **T7** 別 request の記録が混入しない | **○** 第1試行の11個の ID（`ARUN-00954`〜/`OBS-00955`〜/`SUBMIT-zOlryQ`/`UTT-1011`/`ETR-2d6b7350abee`）が**★1件も出ない** |
| **T8** 再解決して結果が変わらない | **○** 本番の口で2回 → **完全一致** |

---

# 2. trace 解決結果

```
trace_key        : SUBMIT-_ayfew        /api/resolve → resolved=true, read_only=true
入力内容         : 「現在のGPU使用状況を取得し、…要約してください。」（★依頼文と完全一致）
受理時刻         : 2026-07-30T23:51:06.865333
                   ★receipt の last_recv_at 23:51:06.865135 と 198µs 差／★私の POST 23:51:06.858723 の直後
入力参照(DS)     : UTT-1012
RRI 参照         : rri.request_type=OBSERVE_CURRENT_STATE / acquisition_method=RUNTIME_INSPECTION
                   ETR-d19f46b8ddd3（21 event・parent_event_id つき）
ARUN 参照        : ARUN-00958 / 00959 / 00960 / 00961
OBS 参照         : OBS-00959 / 00960 / 00961 / 00962
response 参照    : runs/SUBMIT-_ayfew.trace.json
★解決不能な参照  : ★RRI の record ID（RREQ-/RINT-）は TRACE に入っていない（判定値のみ）。★今回の対象外
                   ★DW task（dw_task_ref=None）＝この経路は task を作らない
```
**★正典 §1 の必須6点は、すべて `trace_key` 1つから到達できた。**

---

# 3. E2E 結果

| | |
|---|---|
| 一周 | **★不成立** |
| 最後に成立した工程 | **★3 RRI**（連続処理として。★9 記録も PROVEN だが、4〜8 を飛ばした先である） |
| 最初に成立しなかった工程 | **★4 計画**（第1試行は **2 ID 発行**） |
| **★第1試行から何工程 前進したか** | **★2工程**（2 ID 発行 と 9 記録 が FAILED → PROVEN。**★最初の停止点が 2 → 4 へ動いた**） |

## 3-1. ★正典 §6-B（第1試行で到達しなかった工程に到達したか）
```
計画 / 実行命令生成 / 検証 / DW要約 → ★4つとも到達していない
★無理に起動させていない（★DW task 生成方式を変えていない・Planner を呼んでいない）
```
## 3-2. ★正典 §6-C（GPU 取得の再確認・★修正していない）
| 項目 | 結果 |
|---|---|
| GPU 識別情報 | **○** `NVIDIA GeForce RTX 5090` ×2 |
| **GPU 使用率** | **★取得不能（0件）** — `--query-gpu=index,memory.used,memory.total,name` に `utilization.gpu` が無い |
| VRAM 総量 | **○** `32607 MiB` |
| VRAM 使用量 | **○** GPU0 `30520` / GPU1 `31168` MiB |
| GPU 関連プロセス | **★部分的（不十分）** — `ps -eo pid,rss,comm` の6行。**★GPU への紐付けが無い** |

**★私の計器の誤り（自己申告）**: 使用率の有無を `'%' を含む行` で探したところ、`listening 127.0.0.53%lo:53` を誤検出した。**★GPU 行だけに絞って取り直し、0件を確認した。**（`G-23` と同型＝計器が別物を数えた）

---

# 4. 2DER が担当した工程（★証拠で主体を示せるものだけ）
| 工程 | 証拠 |
|---|---|
| **3 RRI** | `request_type` / `resolved_intent`（分類の根拠文つき）＋ 同区間の `:8005` 4件 |
| **6 取得の実行** | `ARUN-00958`〜`00961`（command / host / `started_at 14:51:11.592907Z`＝**★投入 23:51:06.86〜23:51:12.34 の内側**） |
| **9 記録の書き込み** | `ds_events.jsonl` / `rri_records.jsonl` / `egl data/events.jsonl` が更新（★ファイル名のみ確認） |

**★今回の修正（`ids.py`）は IMPL が書いた ∴ 2DER の担当に数えない。★主体移管 1/8 は動かない。**

---

# 5. 人・Claude が行った操作（★開始操作・監査・実装・テストを区別して全件）

| 区分 | 操作 | 時刻 |
|---|---|---|
| **実装** | `twoder/ids.py` に `SUBMIT-` 解決を追加（59行 追加のみ） | 23:36 |
| **運用操作** | **★webui 再起動**（下表） | 23:49:07 |
| **★誤操作（自己申告）** | **★確認せずに PID 3814626 を kill した。**実体は不明・現存せず。**★実サーバ(3814663)は無傷で、私の `nohup` は `Address already in use` で起動に失敗した**（★1回目の再起動は失敗＝空振り）。**★その後 `:8770` を掴んでいる PID を名指しで止めて再起動した** | 23:48 |
| **テスト** | T1（本番の口・8件）／T2／T3〜T6／T7／T8 | 23:49〜23:52 |
| **開始操作** | **`POST /api/submit` ★1回** | 23:51:06 |
| **していないこと** | **★`run_next` を押していない**（`task_id` が無い）／**★GPU を自分で測っていない**／**★コマンドを選んでいない**／**★出力を整形・要約していない**／**★再投入していない**／**★commit していない** | |

## 5-1. ★再起動の記録（正典 §実施条件・不可避な開始操作）
| 項目 | |
|---|---|
| 操作内容 | `twoder.webui` の停止と再起動（旧 PID 3814663 → 新 PID 3923096 / 23:49:07） |
| 操作者 | **実装(IMPL)** |
| 必要な理由 | **`ids.py` の変更を本番の口へ反映するため**（`from twoder import ids` は関数内 import だが、★module は既に `sys.modules` に載っており再起動なしでは反映されない。★実際、再起動前の `/api/resolve?id=SUBMIT-zOlryQ` は `false` を返していた＝**「ソースに在る≠動く」の実測**） |
| 既存運用か | **★既存運用**（IMPL 引き継ぎ §4-1 に手順が定められている） |
| 主体判定への影響 | **★2DER の担当工程として数えない** |
| **★run-gate** | **★初期化された**（`_LAST` は webui プロセス内の変数）。★ただし本件は投入が `task_id=null` で `runnable=false` のため、**★run-gate の初期化が結果に影響していない** |

---

# 6. モデルサーバ側の記録（`:8005`）
```
窓 JST 23:51:00〜23:51:20（UTC 14:51:00〜14:51:20）★打ち切り無し
  14:51:07.147Z  400 Bad Request      14:51:10.887Z  200 OK
  14:51:11.322Z  200 OK               14:51:11.551Z  200 OK      → 計4件
  ★直後 14:51:11.592 に nvidia-smi が走っている
★第1試行と同じ並び（400×1 + 200×3）。★毎回 400 が1件 出る。★直していない・掘っていない
```

---

# 7. ★次の停止原因（★1件に固定）

> **★工程4「計画」へ到達しない。区分は「配線はあるが呼ばれない」。**
> **根拠**: `RUNTIME_INSPECTION` 経路は DW task を作らない（`dw_task_ref=None`）。**★PLAN／GENERATE／AUDIT／DW要約 は DW task の工程であり、task が無い以上 起動しない。**
> **★「配線が無い」とは書かない。**（PLAN 以降の配線は在る＝第1試行の D-133 で `QWEN_BUILD_PLANNER` の到達経路を確認済み）

# 8. ★次の最小修正候補（★1件だけ・★実施しない）

> **既存の GPU 取得クエリへ `utilization.gpu` を追加し、GPU に関連するプロセスを GPU 単位で取得できるようにする。**
> **★これは正典 §8 が名指しした候補である**（「第2試行でも GPU 使用率が取得不能で…次の候補として検討してよい」）。★私が考案したものではない。
> **★正直に併記する**: **★次の停止原因（工程4）と、この候補（工程7）は別の場所である。** **★どちらを先に採るかは設計／MGR の判断であり、★私は決めない。**

---
*IMPL → 設計/監査（写: MGR / Taka）。第2試行の結果。**修正は `twoder/ids.py` 1ファイル59行 追加のみ（方式(b)＝既存 record への決定論的解決／新しい台帳・API・GPU分岐なし／fail-closed は `return None` 9箇所・`raw_input` を Event Trace `ENTRY` と完全一致照合）**。**T1〜T8 を本番の口で全て通した**（後方互換8件は固定した期待値と1件ずつ一致、`SUBMIT-zOlryQ` は true、対照は false）。**同一依頼（sha1 `0c458f38…`・54字・第1試行と一致）を1回だけ投入**し、`trace_key=SUBMIT-_ayfew` が `resolved=true`、そこから**入力内容／受理時刻(23:51:06.865333・receipt と 198µs 差)／RRI／`ETR-`(21 event)／`ARUN-00958〜61`／`OBS-00959〜62`／response** の**必須6点すべてへ到達**（RRI の record ID と DW task は無く、対象外）。**E2E は一周 不成立だが 2工程 前進**（2 ID発行・9 記録が FAILED→PROVEN、**最初に成立しなかった工程が 2 → 4 へ移動**）。**計画/実行命令生成/検証/DW要約には到達せず、無理に起動させていない。GPU は修正せず再確認し、使用率は再び取得不能・プロセスは GPU 紐付け無し**（★使用率の有無を `%` で探して誤検出した自分の計器を訂正した）。**人・Claude の操作は 実装1件／再起動1件（全件記録・run-gate 初期化・結果に影響なし）／テスト／`POST /api/submit` 1回のみで、`run_next` を押さず GPU を自分で測らず commit もしていない。★確認せずに PID 3814626 を kill した誤操作を自己申告する（実サーバは無傷・1回目の再起動は空振り）。** 次の停止原因は**工程4「計画」へ到達しない＝配線はあるが呼ばれない**の1件、次の最小修正候補は**正典 §8 が名指しした `utilization.gpu` 追加**の1件（★停止原因と場所が違うことを明記・採否は設計/MGR）。*
