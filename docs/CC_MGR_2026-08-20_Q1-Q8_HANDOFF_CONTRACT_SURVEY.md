# 宛: Taka ―― **Q1〜Q8 調査表（★RRI→DW 連動契約 最小仕様 v0.1 の 未確定事項）**

**2026-08-20 15:0x ／ ★調査員と して（★bootstrap 期間の 限定役）**
**★コード 0行 ／ 実装 0 ／ 設計案 0 ／ repo 変更 0 ／ 2DER への 投入 0**
**★実測 = `file:line` を 付けた 物 ／ ★推論 = 「★推論」と 明記した 物（★分けて 書きました）**

---

## Q1. HANDOFF CONTRACT を 既存の どの record / packet / task payload に 載せるのが 最小か → **EXISTS**

**★実測:**

```
`dev-workcell/dw/workcell.py:422`
   def create_task(task_id, project_id, goal, knowledge_packet, ts, manager_identity, contract=None)
`:425`  payload = {"project_id": project_id, "goal": goal, "knowledge_packet": knowledge_packet}
`:426`  if contract is not None: payload["contract"] = contract     # ★有れば 足す・無ければ 鍵を 置かない
`:428`  return _append_event(task_id, "CREATE", "MANAGER", manager_identity, payload, ts)
```

**★既に 任意の 辞書を 運べる 欄が 2つ 在ります（★どちらも 自由形式）:**

| 欄 | 実測の 中身 | 出所 |
|---|---|---|
| `knowledge_packet` | `{packet_type, schema_version, task_context, current_claims, provenance{trace_id, ds_input_id, rri_request_id, rri_intent_id, egl_source_refs, measured_state, dw_task_id}}` | submit.py:643-648 / :744 付近 |
| `contract` | `{skeleton, immutable_tests}`（★`contract_seal` が 封印） | contract_seal.py:4-7 |

```
★`knowledge_packet` は ★schema_version を 持つ 自由形式の 辞書 ＝ ★鍵を 足しても 既存の 読み手が 壊れない
   （★読み手は `.get()` で 引いて いる ―― generate_via_runner の provenance 読み出しが 実例）。
★`contract` は ★『有れば 足す』設計 ＝ ★★不在が 既に 正常系。
★★∴ ★新しい 欄／新しい 台帳／新しい 口を 作らずに 載せられる 場所が ★2つ 実在します。
★★どちらに 載せるかは ★私が 決めません（★ご指示「決められることを 勝手に 決めない」）。
```

---

## Q2. DW task 作成後、どこまで その情報を 現在 保持できるか → **EXISTS**

**★実測:**

```
★CREATE event の payload は ★追記式の event log に そのまま 残る（`_append_event`）。
★読み出しの 実例 = `generate_via_runner`:
     _ce = read_create_event(packet.get("task_id"))
     provenance = ((_ce.get("payload") or {}).get("knowledge_packet") or {}).get("provenance")
   ＝ ★★GENERATE の 段から ★CREATE の payload を 実際に 読めて いる（★2026-08-20 に 私が 配線し 実測）。
★別の 実例 = `domain_dw.py:88`  _c = (ev.get("payload") or {}).get("contract") or {}
   ＝ ★契約も 同じ 形で 後段から 読めて いる。
```

```
★★∴ ★『DW に 入ると 意図が 消える』のは ★★保持できないから では ない。
★★∴ ★保持は できて いる。★★誰も 読んで いない のが 実測（★Q3 へ）。
```

---

## Q3. `dispatch::_MAP` の 前後で `work_kind` / `stop_at` を 参照できる 最小地点は どこか → **EXISTS（★地点は 実在する）**

**★実測:**

```
`dev-workcell/dw/dispatch.py:49`
   def next_legal_operation(task_id, events=None)
`:59`   state, view = W.derive_state(task_id, events=events)
`:66`   op, role, input_ref, claude_barrier = _MAP.get(state, ("BLOCKED", "-", "-", True))
`:67-78` ★★既に 1つ 例外が 在る:
        if state == "READY_FOR_UPPER_REVIEW" and view.get("upper_reviews"):
            blockers, _ = W.completion_blockers(task_id, events=events)
            if not blockers:
                op, role, input_ref, claude_barrier = ("PROPOSE_COMPLETE", "GATE", …)
`:85`   return nlo   # {task_id, state, operation, actor_role, actor_id, input_ref, claude_barrier}
```

```
★★＝ ★『`_MAP` を 引いた 後に、★別の 記録を 見て ★結果を 差し替える』作りが ★★既に 1件 実在する。
★★＝ ★同じ 場所に 到達する ための 材料も 揃って いる:
     ・`task_id` が 引数に 在る ∴ ★CREATE payload を 読める（★Q2 の 実例と 同じ 形）
     ・`view` が 手元に 在る
★★∴ ★『参照できる 最小地点』は ★`dispatch.py:66〜78` の 区間に 実在します。
★★どこに 何を 置くかは ★私が 決めません。
```

**★現在の 実測（★なぜ 効いて いないか）:**

```
★`_MAP` の 鍵 = ★`state` ただ 1つ（`:66`）。
★`request_type` / `acquisition_method` / `knowledge_packet` を ★1つも 参照して いない。
★`next_legal_operation` の 本線 呼び手 = `twoder/operator.py:44` / `:146` / `:198`。
```

---

## Q4. INVESTIGATE を 実行できる 既存 actor / runtime / research 経路は 存在するか → **★PARTIAL**

**★実測 ―― ★実物を 読む 能力は ★既に 在り、★動いて います:**

```
`twoder/runtime_inspection.py::inspect` を `submit.py:615` が 呼ぶ。
   返り = {status, host_ref, observations, failed_observations, non_guarantee, environment_snapshot_ref}
`submit.py:622`  _rec("MEASURED_STATE", [o["human"] for o in _res["observations"]])   # ★逐語「now real, from the inspection」
`submit.py:623`  _rec("EGL_SOURCE_REFS", [r["raw_observation_id"] …])
`submit.py:624`  _rec("EGL_OBSERVATION_INGEST", {"egl_run_id": …, "refs": …})
★★＝ ★読み取り専用の 観測を 実行し ★EGL へ 取り込む 経路が ★実在し ★実際に 走って いる。
```

**★実測 ―― ★但し 3つ 足りません:**

```
★① ★観測は ★`OBSERVE_CURRENT_STATE` の 分岐でしか 起動しない（`submit.py:608-609`）。
     ＝ ★`research_focus_ref="OBSERVE_CURRENT_STATE"` が ★呼び出しに 直書き（`:611`）。
★② ★観測の 結果は ★`TRACE` と `knowledge_packet.provenance.measured_state` に 入る が
     ★★task の 成果(artifact)と しては 記録されない ＝ ★『納品』に なって いない。
★③ ★DW の actor 表(`dispatch.py:41-46`)= ★4役のみ
        CODING_WORKER→QWEN_LIVECODER ／ INDEPENDENT_AUDITOR→QWEN_AUDITOR
        MANAGER→CLAUDE ／ CLAUDE_SENIOR→CLAUDE
     ＝ ★★『調査する 役』は ★1つも 登記されて いない。
```

```
★★∴ ★実行する 力は 在る（EXISTS）／ ★役と 納品先が 無い（ABSENT）＝ ★合わせて ★PARTIAL。
★★新 actor が 要るかは ★私は 決めません（★ご指示どおり）。
```

---

## Q5. 調査結果を コード artifact では なく 正規成果と して 保存できる 既存記録面は あるか → **EXISTS**

**★実測 ―― ★候補が 3面 実在します（★どれも 既存・★新設 不要）:**

| 面 | 実測 | 根拠 |
|---|---|---|
| `record_process_event` | 任意の `payload` 辞書を task へ 追記。**語彙は `PROCESS_EVENT_KINDS` で 縛る**（現在9語） | workcell.py:250, :235-240 |
| ROADMAP 台帳 | `register_item` / `set_status(note=)` で ★長文を 追記し **`/api/resolve?id=ITEM-…&history=1` から 取り出せる**（★本日 私が 4回 実測） | roadmap_registry.py:107, resolve_view:368 |
| EGL 観測取り込み | `EGL_OBSERVATION_INGEST` ＋ `raw_observation_id` で 参照が 残る | submit.py:623-624 |

```
★★但し ―― ★`PROCESS_EVENT` は 逐語「★derive_state は無視」＝ ★★状態を 進めない。
   ＝ ★『記録は できる が ★それだけでは 完了に ならない』（★Q6 へ）。
```

---

## Q6. 新しい DW state を 増やさずに INVESTIGATE を 正常完了できるか → **★ABSENT（★いまの ままでは できない）**

**★実測 ―― ★完了の 門は 1つだけ で、★通れません:**

```
★完了へ 至る 唯一の 経路（`dispatch.py:67-78`）:
   state == "READY_FOR_UPPER_REVIEW" かつ upper_reviews が 在る かつ ★completion_blockers が 空
      → PROPOSE_COMPLETE
★`completion_blockers` の 実物（`workcell.py:337-350` 付近）:
   STATE_NOT_COMPLETABLE          state=… は COMPLETE 遷移不可
   ★IMPLEMENTATION_RUN_MISSING     implementation run + test_result が存在しない
   ★TEST_NOT_PASSED                最新 implementation の test_result が passed=True でない
   ★INDEPENDENT_AUDIT_MISSING      independent audit run が存在しない
   FINDING_DISPOSITION_MISSING / FINDING_DISPOSITION_OPEN / UPPER_REVIEW_MISSING
```

```
★★＝ ★★3つの blocker（実装走行 / 試験 passed / 独立監査）が ★★コード生成を 前提に して いる。
★★∴ ★調査だけの task は ★この 3つを ★★構造上 満たせない ＝ ★PROPOSE_COMPLETE へ 到達できない。
★★∴ ★『新 state を 増やさずに 閉じられるか』の 答えは ―― ★★いまの blocker のままでは ★ABSENT。

★★但し ★1点 実測を 添えます（★推論では ない）:
   ★`completion_blockers` は ★★関数で あり ★state 表では ない。
   ★∴ ★『新しい state を 増やす』のと『blocker の 条件を 変える』のは ★★別の 話です。
   ★★どちらを 採るかは ★私は 決めません。
```

---

## Q7. 古い task に HANDOFF CONTRACT が 無い 場合の 後方互換を、現行挙動を 変えず 実現できるか → **EXISTS**

**★実測:**

```
★`contract` は ★★既に 『無いのが 正常』の 設計:
   workcell.py:426  if contract is not None: payload["contract"] = contract   # ★無ければ 鍵を 置かない
   domain_dw.py:88  _c = (ev.get("payload") or {}).get("contract") or {}      # ★無ければ 空 辞書
★`knowledge_packet` の 読み出しも 同じ 形（`.get()` の 連鎖）＝ ★不在で 例外に ならない。
★★∴ ★『鍵が 無い 古い task』は ★★既に 全経路で 通って いる（★実測 561 task の 大半が この 形）。
```

**★新規と 既存の 識別（★ご指示で 未確定と された 点）―― ★実測で 引ける 手がかり:**

```
★CREATE event は ★`ts` を 持つ（`_append_event(task_id, "CREATE", …, ts)`）。
★∴ ★『契約の 鍵が 在るか / 無いか』そのものが ★★識別子に なり得る（★時刻を 使わずに 済む）。
★★但し ―― ★どちらを 使うかは ★★私は 決めません。
```

---

## Q8. Current Work 表示を 既存記録から 導出できるか → **★PARTIAL**

**★実測（`/api/state?task_id=…` を 実際に 引いた・`TASK-2DER-616AC70A`）:**

| 表示したい 行 | 既存の 欄 | 在るか |
|---|---|---|
| Goal | `goal` | **★在る** |
| Current stage | `dw_state` | **★在る** |
| Next legal action | `next_operation` | **★在る** |
| Authority | `taka_authority` | **★在る** |
| Missing information | `work.next_information_need` | **★在る** |
| Blocked by | `guard_block` | **★在る** |
| Evidence | `egl` | **★在る** |
| **Work kind** | `work_kind` | **★★無い** |
| **Deliverable** | `deliverable` | **★★無い** |
| **Stop at** | `stop_at` | **★★無い** |
| **Do not** | `do_not` | **★★無い** |

```
★★＝ ★10行のうち ★7行は ★今日 そのまま 出せる。
★★＝ ★出せない 4行は ★★Q1 で 載せる 契約 そのもの ＝ ★契約が 入れば 同時に 解ける。
```

---

## ★まとめ（★判定だけ）

| 問 | 判定 | 一言（★実測） |
|---|---|---|
| Q1 載せる 場所 | **EXISTS** | `knowledge_packet`（自由形式）と `contract`（有れば 足す）の 2つが 実在 |
| Q2 保持 | **EXISTS** | CREATE payload は 後段から 実際に 読めて いる（実例2件） |
| Q3 参照地点 | **EXISTS** | `dispatch.py:66-78` に ★同型の 差し替えが 既に 1件 在る |
| Q4 調査 actor | **PARTIAL** | 観測器は 実在・実動。★役の 登記と 納品先が 無い |
| Q5 記録面 | **EXISTS** | 3面（process_event / ROADMAP 台帳 / EGL 取り込み）。★但し 状態は 進まない |
| Q6 新 state 無しで 完了 | **★ABSENT** | 完了門の blocker 3つが コード生成を 前提に して いる |
| Q7 後方互換 | **EXISTS** | 契約不在が 既に 正常系。`.get()` 連鎖で 例外に ならない |
| Q8 表示 | **PARTIAL** | 10行中 ★7行は 今日 出せる。残り4行＝契約 そのもの |

## ★していないこと

```
★コード 0行 ／ 実装 0 ／ 設計案 0 ／ 「こう すれば よい」を ★1行も 書いて いない
★repo 変更 0（★`twoder@04f8b07` 不変）／ ★2DER への 投入 0 ／ ★常駐 停止の まま
★台帳の 直読 0（★source と `/api/state` と `/api/resolve` のみ）
★★決められる ことを 決めて いない ―― ★載せ先／分岐点／actor の 要否／blocker の 扱いは ★すべて 未決の まま 返します
★SELF_DEV_TOKEN = ★5/5
```
