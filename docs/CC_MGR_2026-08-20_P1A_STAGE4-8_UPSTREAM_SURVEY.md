# 宛: Taka ―― **P1-A ／ Stage 4〜8 上流境界 調査表（★MGR が 正規経路から 機械的に 取得）**

**2026-08-20 14:5x ／ ★repo 変更 0 ／ 実装 0 ／ 設計案 0 ／ 修理 0 ／ 2DER への 投入 0**
**★取得できなかった 欄は ★推測せず `UNVERIFIED` ／ ★取得できた 値は そのまま 写した**
**★SELF_DEV_TOKEN = ★5/5**

---

## 0. ★★段の 対応（★先に ここを 確定しないと 表が 別物を 指します）

| ご指定 | 経路表 `ROUTE` の 実物 | 判定 |
|---|---|---|
| 4 RRI分類 | `S04` RRI / `request_type` | **EXISTS**（一致） |
| 5 RRI門 | `S05` RRI / `preflight_gate` | **EXISTS**（一致） |
| 6 RRI戦略 | `S06` RRI / **`mint`（intent_record）** | **★CONFLICT** |
| 7 EGL admission | `S07` EGL / `admit_design_evidence` | **EXISTS**（一致） |
| 8 routing | `S08` SEAL / **`extract_contract`（contract_seal）** | **★CONFLICT** |

```
★CONFLICT ①(段6)
  ご指定の「RRI戦略」の 実物 = `rri/rri/intent_strategy.py::resolve_consensus`
  ★本線で 呼ばれて いる = `twoder/submit.py:440`(import) / `:470`(呼び出し) / `:485`(停止判定)
  ★但し ★経路表 S06 は ★別物(`intent_record.mint`)を 指す ＝ ★「RRI戦略」は ★経路表に 段が 無い。

★CONFLICT ②(段8)
  ご指定の「routing」の 実物 = `twoder/submit.py` の ★if/elif 連鎖(★:640〜:700 付近)
  ★経路表 S08 は ★別物(`contract_seal.extract_contract`)を 指す ＝ ★「routing」は ★経路表に 段が 無い。
  ★`contract_seal` 自体は 本線で 呼ばれる(`submit.py:339` / `:723`)＝ ★段は 在るが ★名前が ずれている。
```

**★私は 段を 付け替えて いません。★以下の 表は ★両方（ご指定の 実物 ／ 経路表の 行）を 併記します。**

---

## 1. ★★確定を 求められた 4点

### 問1. request_type は どこで 決まるか → **EXISTS**

```
場所   = /home/takasan/rri/rri/request_type.py::classify_request_type (:61)
呼び手 = /home/takasan/twoder/submit.py:302（★直前 :301 が `_HO("S04", to_key="RRI.classify_request_type")`）
決め方 = ★★LLM。★決定論では ない。
   _ENDPOINT = os.environ.get("RRI_VLLM_ENDPOINT", "http://localhost:8005/v1/chat/completions")  (:14)
   _MODEL    = os.environ.get("RRI_VLLM_MODEL", "Qwen3.6-35B-A3B")                                (:15)
   _SYS      = 固定 prompt (:39) ／ seed=0 ／ max_tokens=500
語彙   = REQUEST_TYPES = 6語 (:17)
   OBSERVE_CURRENT_STATE / BUILD_CAPABILITY / MODIFY_EXISTING / RESUME_PRIOR / DECIDE / OTHER
6語以外= ★"OTHER" に 落とし basis="unparseable" (:72-74) ＝ ★fail-open では なく ★既定値へ 倒す
```

### 問2. WORK_KIND 相当の 概念は 現在 存在するか → **★ABSENT**

```
★機械的に 数えた(ds / rri/rri / egl/egl / dev-workcell/dw / twoder ／ runs 除く):
   work_kind   → ★該当 file 0
   WORK_KIND   → ★該当 file 0
   DELIVERABLE → ★該当 file 0
   stop_at     → ★該当 file 0
   STOP_AT     → ★該当 file 0
   deliverable → ★1 件 ＝ `twoder/human_escalation_ledger.py:4` の ★docstring の 英単語
                 （★欄では ない ／ ★値を 持たない）
★★∴ ★GOAL / WORK_KIND / DELIVERABLE / STOP_AT の 4語は ★★実体と して 存在しない。
```

**★但し ―― ★『止まる』ことだけは ★別の 語で ★既に 在ります（★PARTIAL）:**

```
`SELECTED_ACQUISITION_METHOD` の 実在する 値 = ★9語（`twoder/submit.py` を 機械的に 数えた）
   DW_IMPLEMENTATION / RESUME / RUNTIME_INSPECTION / EGL_RESEARCH / EGL_DE_ADMISSION /
   WEB_RESEARCH_ACQUISITION / ★RRI_PREFLIGHT_HOLD / ★RRI_INTENT_HOLD / ★BLOCKED_DEAD_APPROACH
★★∴ ★『どこで 止めるか』は ★★入口(RRI)に 限れば ★既に 3語 在る。
★★∴ ★無いのは ★『仕事の 種類』と『納品の 形』であって ★『止まる』では ない。
```

### 問3. `BUILD_CAPABILITY → DW_IMPLEMENTATION` の 対応は どこで 決まるか → **EXISTS（★ハードコード）**

```
場所 = /home/takasan/twoder/submit.py:682
   elif rt.get("request_type") in ("BUILD_CAPABILITY", "MODIFY_EXISTING"):
場所 = /home/takasan/twoder/submit.py:693
   _rec("SELECTED_ACQUISITION_METHOD", "DW_IMPLEMENTATION")
★条件 = ★★`request_type` だけ。★他の 入力を 見て いない。
★形   = ★★対応表(map)は 無い ＝ ★if/elif の 連鎖に ★文字列リテラルで 直書き。
★同じ 分岐で task が 作られる = :696  dw_task = "TASK-2DER-" + sha1(raw_input)[:8].upper()
★★∴ ★`BUILD_CAPABILITY` と 判定された 時点で ★DW 実装経路が 確定する（★他の 選択肢が 無い）。
```

### 問4. routing が GENERATE まで 行くことを ★どの 情報から 決めて いるか → **EXISTS**

```
★入口側(submit)は ★GENERATE を 決めて いない。★決めて いるのは ★DW の 状態表 だけ。
場所 = /home/takasan/dev-workcell/dw/dispatch.py::_MAP (:28-39 ／ ★9行)
   "CREATED":                  ("PLAN",     "MANAGER",        "GOAL+KNOWLEDGE_PACKET", True)
   "READY_FOR_IMPLEMENTATION": ("GENERATE", "CODING_WORKER",  "IMPLEMENTATION_PACKET", False)
★★＝ ★`_MAP` の 鍵は ★★`dw_state` ただ 1つ。
★★＝ ★`request_type` も `acquisition_method` も ★★参照して いない。
★★∴ ★GENERATE へ 行くかは ★『PLAN が 通って READY_FOR_IMPLEMENTATION に なったか』だけで 決まる。
★★∴ ★「調査だから GENERATE を 飛ばす」を ★表す 情報が ★★この 表に 1つも 無い。
```

---

## 2. ★★M1〜M16 調査表（★5段 ／ ★取得できない 欄は `UNVERIFIED`）

**★根拠の 書式 = `file:line` ／ ★観測値は そのまま 写した。**

### Stage 4 ―― RRI分類（`S04` ／ `rri/rri/request_type.py::classify_request_type`）

| | 判定 | observed_value | evidence_refs |
|---|---|---|---|
| M1 役割 | EXISTS | raw_input を 6語の どれかに 分類する | request_type.py:61, :17 |
| M2 入力 | EXISTS | `raw_request`, `recent_context`(直近4発話), `seed=0` | submit.py:302 |
| M3 出力 | EXISTS | `{"request_type","requires_current_state","references_prior_work","basis"}` ／ 記録 `RRI_REQUEST_TYPE` | request_type.py:72-75, webui.py:1457 |
| M4 対象範囲 | EXISTS | 6語のみ | request_type.py:17 |
| M5 事前条件 | EXISTS | `:8005` が 応答すること（LLM 呼び出し） | request_type.py:14-15, :20 |
| M6 停止条件 | **ABSENT** | この段に 停止の 語が 無い | submit.py:302-303（後段へ そのまま 進む） |
| M7 次段 | EXISTS | `handoff = ["HANDOFF","S04"]` | route_table.py S04 |
| M8 実接続 | EXISTS | 本線 呼び手 = **1**（submit.py:302） | submit.py:301-302 |
| M9 代替経路 | EXISTS | 試験用に 差し替え可 | counterfactual_runner.py:36 |
| M10 永続性 | EXISTS | TRACE へ 記録され 後から 読める | webui.py:1457 |
| M11 失敗時挙動 | EXISTS | 6語以外 → `"OTHER"` / `basis="unparseable"`（★既定値へ 倒す） | request_type.py:72-74 |
| M12 権限 | **PARTIAL** | `actor="2DER"` だが `actor_confirmed=false` | route_table.py S04 |
| M13 監査可能性 | EXISTS | `etrace.emit("RRI","classify_request_type", …)` | request_type.py:64 |
| M14 work_kind適合 | **ABSENT** | work_kind 概念が 存在しない | 問2 の 計数 |
| M15 may_stop_here | **ABSENT** | 停止語なし | M6 と 同じ |
| M16 正常系依存 | **EXISTS（焼き付きあり）** | ★同一趣旨の 依頼が `MODIFY_EXISTING` と `BUILD_CAPABILITY` に 分かれた（2026-08-20 実測 `5A849467` / `83BD03E1`・★違いは 書き出しの 1文） | 本会話の 実測 |

### Stage 5 ―― RRI門（`S05` ／ `rri/rri/preflight_gate.py::detect`）

| | 判定 | observed_value | evidence_refs |
|---|---|---|---|
| M1 役割 | EXISTS | 曖昧な 定量主張を 検知し DW へ 上げるかを 決める | preflight_gate.py:28-44 |
| M2 入力 | EXISTS | `raw_input`, `failure_hits`(FAIL-002 のみ) | submit.py:386-388 |
| M3 出力 | EXISTS | `{gate_id, claim_pattern_id, triggered, decision, signals, proposed_egl_status, blocks_dw_escalation}` | submit.py:397-399 |
| M4 対象範囲 | EXISTS | 定量主張・未定義指標・出典の 有無 | preflight_gate.py:32-41 |
| M5 事前条件 | EXISTS | `ambiguity_patterns.jsonl` が 読めること | preflight_gate.py:45-47 |
| M6 停止条件 | **EXISTS** | `triggered and blocks_dw_escalation` → `SELECTED_ACQUISITION_METHOD="RRI_PREFLIGHT_HOLD"` | submit.py:400-405 |
| M7 次段 | EXISTS | `handoff = ["HANDOFF","S05"]` | route_table.py S05 |
| M8 実接続 | EXISTS | 本線 呼び手 = **1**（submit.py:388） | submit.py:385-388 |
| M9 代替経路 | UNVERIFIED | 機械的に 取得できず | ― |
| M10 永続性 | EXISTS | `_rec("RRI_PREFLIGHT", …)` + 停止時 `IR.mint("INTENT",…)` | submit.py:397, :401 |
| M11 失敗時挙動 | EXISTS | 4段階 `ALLOW` / `ALLOW_WITH_WARNING` / `STRONGLY_DISCOURAGE_DW` / `CLARIFY_FIRST`（後2つが blocks=True） | preflight_gate.py:238-244 |
| M12 権限 | **PARTIAL** | `actor="2DER"` ／ `actor_confirmed=false` | route_table.py S05 |
| M13 監査可能性 | EXISTS | `etrace.emit("RRI","preflight_gate", …)` | submit.py:391-394 |
| M14 work_kind適合 | **ABSENT** | work_kind を 見て いない（見るのは 主張の 曖昧さだけ） | preflight_gate.py:32-44 |
| M15 may_stop_here | **EXISTS** | `RRI_PREFLIGHT_HOLD` で ここで 終わる | submit.py:405 |
| M16 正常系依存 | UNVERIFIED | 機械的に 取得できず | ― |

### Stage 6 ―― RRI戦略（★ご指定の 実物 ／ `rri/rri/intent_strategy.py::resolve_consensus`）

| | 判定 | observed_value | evidence_refs |
|---|---|---|---|
| M1 役割 | EXISTS | 7つの 戦略から 1つを 選ぶ（合議） | intent_strategy.py:25-33 |
| M2 入力 | EXISTS | `raw_input`, `anchoring`, `supporting_refs`, `context_text`, `extra_facts`(最大2行・決定論) | submit.py:470-471, :440-468 |
| M3 出力 | EXISTS | `{strategy, candidates, status, facts, consensus, reason}` ／ 記録 `INTENT_STRATEGY` | submit.py:472-478 |
| M4 対象範囲 | EXISTS | 戦略7語 `DIRECT / CONTEXT_RESOLVE / CHOICE / BOUNDED_MULTI_VIEW / INTENT_PROBE / PREMISE_PROBE / DEFER` | intent_strategy.py:25-33 |
| M5 事前条件 | EXISTS | `:8005`（`ENDPOINT` / `MODEL` / `MAX_TOKENS=256`） | intent_strategy.py:38-40 |
| M6 停止条件 | **EXISTS（★一部）** | `stops_before_action()` かつ `strategy in {"PREMISE_PROBE","DEFER"}` → `RRI_INTENT_HOLD` | submit.py:485-491 |
| M7 次段 | **CONFLICT** | 経路表に この段が 無い（S06 は `intent_record.mint` を 指す） | route_table.py S06 |
| M8 実接続 | EXISTS | 本線 呼び手 = **1**（submit.py:470） | submit.py:440, :470 |
| M9 代替経路 | EXISTS | 解析用の 別呼び手 4件（`function_table.py:166` / `route_edge_vote.py:208` / `route_candidates_v2.py:210` / `menu_vote.py:19`） | 各 file:line |
| M10 永続性 | EXISTS | `_rec("INTENT_STRATEGY", …)` に 票数・理由まで 残る | submit.py:472-478 |
| M11 失敗時挙動 | EXISTS | `_istrat.get("failure")` → `_fail("RRI", …)` | submit.py:492-493 |
| M12 権限 | UNVERIFIED | 経路表に 段が 無い ∴ actor 欄が 引けない | ― |
| M13 監査可能性 | EXISTS | 票数(`consensus`)と 理由(`reason`)を 記録に 残す | submit.py:477-478 |
| M14 work_kind適合 | **ABSENT** | 戦略7語に work_kind の 概念が 無い | intent_strategy.py:25-33 |
| M15 may_stop_here | **PARTIAL** | 7語のうち 停止に 使うのは **2語**（`PREMISE_PROBE` / `DEFER`）。`INTENT_PROBE` は `STOP_STRATEGIES` に 在るが `_HOLD` に 無い ∴ ★止めない | intent_strategy.py:36, submit.py:483-485 |
| M16 正常系依存 | **EXISTS（逐語）** | コメント 逐語「★`INTENT_PROBE` は 実データ0件なので 書かない」 | submit.py:480-482 |

### Stage 7 ―― EGL admission（`S07` ／ `egl/egl/de_admission.py::admit_design_evidence`）

| | 判定 | observed_value | evidence_refs |
|---|---|---|---|
| M1 役割 | EXISTS | 設計根拠を 台帳へ 受理／却下する | de_admission.py:66, :7-10 |
| M2 入力 | EXISTS | `candidate`, `ts`, `ledger_path`, `reverify` | de_admission.py:66, submit.py:223 |
| M3 出力 | EXISTS | `DE id`（`returns=["DE id"]`） | route_table.py S07 |
| M4 対象範囲 | EXISTS | 必須欄 `("observation","decision","decision_owner")` | de_admission.py:22 |
| M5 事前条件 | EXISTS | `evidence_refs` が 空で ないこと | de_admission.py:7 |
| M6 停止条件 | EXISTS | schema 不備／id 重複／`HARD_REJECT` 語 → `REJECTED` | de_admission.py:7-10, :25 |
| M7 次段 | EXISTS | `handoff = ["HANDOFF","S07"]` | route_table.py S07 |
| M8 実接続 | EXISTS | 本線 呼び手 = **1**（submit.py:223） | submit.py:221-223 |
| M9 代替経路 | EXISTS | `"MANUAL_BYPASS"` の 経路が 在る | de_admission.py:54 |
| M10 永続性 | EXISTS | `DESIGN_EVIDENCE_LEDGER.jsonl` へ 追記 | de_admission.py:20 |
| M11 失敗時挙動 | EXISTS | `REJECTED`（fail-closed） | de_admission.py:7-10 |
| M12 権限 | EXISTS | `actor="2DER"` ／ `actor_confirmed=true` | route_table.py S07 |
| M13 監査可能性 | EXISTS | `etrace.emit("EGL","admit_design_evidence", …)` + 台帳 | de_admission.py:71 |
| M14 work_kind適合 | **ABSENT** | work_kind を 見て いない | 問2 の 計数 |
| M15 may_stop_here | **PARTIAL** | 却下は できるが ★『目的達成で 正常終了』では ない | de_admission.py:7-10 |
| M16 正常系依存 | UNVERIFIED | 機械的に 取得できず | ― |

### Stage 8 ―― routing（★ご指定の 実物 ／ `twoder/submit.py` の if/elif 連鎖）

| | 判定 | observed_value | evidence_refs |
|---|---|---|---|
| M1 役割 | EXISTS | `request_type` から `SELECTED_ACQUISITION_METHOD` を 決める | submit.py:682, :693 |
| M2 入力 | EXISTS | `rt["request_type"]` **のみ** | submit.py:682 |
| M3 出力 | EXISTS | `SELECTED_ACQUISITION_METHOD`（★9語）＋ `DW_TASK_ID` | submit.py の 全 `_rec` を 機械的に 数えた |
| M4 対象範囲 | EXISTS | 9語の いずれか | 同上 |
| M5 事前条件 | EXISTS | S04〜S07 が 停止して いないこと | submit.py:405, :491 |
| M6 停止条件 | **EXISTS** | `RRI_PREFLIGHT_HOLD` / `RRI_INTENT_HOLD` / `BLOCKED_DEAD_APPROACH` の 3語で 終わる | submit.py:405, :491, 他1 |
| M7 次段 | **CONFLICT** | 経路表に この段が 無い（S08 は `contract_seal` を 指す） | route_table.py S08 |
| M8 実接続 | EXISTS | submit の 本体（★分岐 そのもの） | submit.py:676-700 |
| M9 代替経路 | UNVERIFIED | 機械的に 取得できず | ― |
| M10 永続性 | EXISTS | `TRACE` に 全 `_rec` が 残る | webui.py:1457 |
| M11 失敗時挙動 | EXISTS | `_fail(...)` で routing へ 進まず 結果を 返す | submit.py:495-500 |
| M12 権限 | UNVERIFIED | 経路表に 段が 無い ∴ actor 欄が 引けない | ― |
| M13 監査可能性 | EXISTS | `DISPATCH_RESULT` に 理由が 残る | submit.py:490 |
| M14 work_kind適合 | **ABSENT** | `request_type` 6語しか 見ない | submit.py:682 |
| M15 may_stop_here | **PARTIAL** | 3語で 止まれる が ★『調査を 納めて 正常終了』は 無い | M6 と 同じ |
| M16 正常系依存 | **EXISTS（★焼き付き）** | `BUILD_CAPABILITY` → `DW_IMPLEMENTATION` が **文字列リテラルで 直書き**・対応表 無し | submit.py:682, :693 |

---

## 3. ★★成功条件への 答え ―― 「意図 → work → route」の 実在する 対応と ★表現されて いない 部分

### ★実在する 対応（★機械で 引ける）

```
raw_input ──[LLM 分類]──> request_type(6語) ──[if/elif 直書き]──> acquisition_method(9語)
                                                  │
                                                  └─ BUILD_CAPABILITY / MODIFY_EXISTING
                                                        └─> DW_IMPLEMENTATION ＋ task 作成
                                                              └─[dw_state だけ]──> _MAP ──> PLAN ──> GENERATE
```

### ★★表現されて いない 部分（★これが 答え）

```
★★① ★『仕事の 種類(work_kind)』が ★存在しない
   ―― work_kind / WORK_KIND = ★該当 file 0。
   ―― 代わりに 在るのは ★`request_type`(6語)＝ ★『何を したいか』であって
      ★『どんな 仕事か（調査／観測／判断／設計／実装／検証／報告）』では ない。

★★② ★『納品の 形(deliverable)』が ★存在しない
   ―― DELIVERABLE = 0 ／ deliverable = ★docstring の 英単語 1件のみ。
   ―― ∴ ★『調査表を 納める』という 形を ★どこにも 書けない。

★★③ ★『どこで 止めるか(stop_at)』が ★★2つに 割れて いる
   ―― ★入口(RRI)には 在る = `RRI_PREFLIGHT_HOLD` / `RRI_INTENT_HOLD` / `BLOCKED_DEAD_APPROACH`。
   ―― ★但し ★それは 全部 ★『上げない ／ 聞き返す』＝ ★★異常系の 停止。
   ―― ★★『目的を 達したから ここで 正常終了する』という 停止は ★1語も 無い。
   ―― ★DW 側(`_MAP`)の 停止語は ★`NONE`(COMPLETE) と `BLOCKED` の 2つだけ。

★★④ ★DW は ★意図を ★1文字も 受け取って いない
   ―― `_MAP` の 鍵は ★`dw_state` のみ。`request_type` も `acquisition_method` も ★参照しない。
   ―― ∴ ★入口が どれだけ 意図を 精緻化しても ★★GENERATE を 飛ばす 情報が ★DW に 届かない。
   ―― ★★これが 「調査を 頼むと 関数が 返ってくる」の ★機械的な 理由。

★★⑤ ★経路表に ★2段が 無い(★CONFLICT 2件)
   ―― 「RRI戦略」と「routing」は ★本線で 動いて いる のに ★経路表の 行が 別物を 指す。
   ―― ∴ ★★機械が 経路表を 引いても ★この 2段の 制約に 到達できない。
```

---

## 4. ★していないこと

```
★repo 変更 0 ／ 実装 0 ／ 設計案 0 ／ 修理 0 ／ 新しい 欄 0 ／ 新しい state 0
★2DER への 投入 0（★今回は 2DER に 実行させて いません ―― ★ご指示どおり）
★台帳の 直読 0（★経路表・source・`/api/resolve` のみ）
★常駐 停止の まま ／ ★`twoder@04f8b07` 不変 ／ ★`D7977C1A` = `CREATED`
★★取得できなかった 欄を 埋めて いません = ★`UNVERIFIED` 6件（S05 M9/M16 ／ S06 M12 ／ S07 M16 ／ S08 M9/M12）
```

## 5. ★ここで 停止します

**★ご指示「P1-A の 結果を Taka へ 返した 時点で 停止する。P1 実装へ 自動的に 進まない」に 従い、**
**★私は ★次の 投入も 実装も 行いません。**
