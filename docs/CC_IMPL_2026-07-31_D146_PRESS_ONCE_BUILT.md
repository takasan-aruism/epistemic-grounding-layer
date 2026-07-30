# 【BUILT】D-146 — `run_next` を1回だけ押した（★コード0行）。**★PLAN が provenance で止まり、Runtime へは到達しない**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 01:5x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）** ／ **実装源**: `CC_DESIGN_2026-07-31_D146_BUILD_SPEC_PRESS_ONCE.md`
- **受領した MGR 文書**: **無し** ／ **`:8005` は呼ばれていない（★0件。★私も 2DER も）**

---

# 0. ★5行（正典の形）
```
Last PASS   : run_next は受理された（refused ではない）。★planner が実際に呼ばれ、★失敗理由が返った
First FAIL  : E-3 — ★新しい ARUN-/OBS- は生まれていない（ARUN-00966・OBS-00967 とも resolved=false）
原因        : PLAN が provenance 検査で fail-closed。不足3件＝trace_id / rri_request_id / rri_intent_id。
              ★D-144 で私が書いた観測経路の knowledge_packet に、★BUILD 経路が入れている provenance が
              入っていないためである（submit.py:435-437 が mint しているものを、観測経路は持たない）
修正内容    : ★無し（コード0行。★押しただけ）
次回確認箇所: 観測経路の packet に、★既存の `rri.intent_record.mint` で rri_request_id / rri_intent_id と
              trace_id を入れる ★1件（★新しい ID 族を作らない。★私は実施していない）
```

---

# 1. ★受入（★1条件に1つの印）

| # | 受入 | 印 | 実測 |
|---|---|---|---|
| **E-1** | 押した結果 | **○（取得できた）** | `dispatched=false` ／ `refused` は**返っていない**（キー自体が無い＝gate は拒否していない）／`reason="CLAUDE_BARRIER"` ／ `nlo.operation=PLAN` `actor_id=CLAUDE` `claude_barrier=true` |
| **E-2** | task の状態変化 | **★変化なし** | **押す前**: `CREATED` / `CREATE` / `PLAN` / `CLAUDE` / `barrier=true` / `PENDING EXTERNAL ACTOR`<br>**押した後**: **★全項目 同じ** |
| **E-3** | **Task → Runtime が流れたか（★核心）** | **★流れていない** | `ARUN-00966` → **`resolved=false`** ／ `OBS-00967` → **`resolved=false`**（★基準値から1件も増えていない） |
| **E-4** | PLAN が動いたなら、誰が作ったか | **★該当なし** | `claude_packet.implementation_packet_ref` が**無い**（`workflow_state=CREATED`）＝**★PLAN は記録されていない** ∴ `plan_source` も `runtime_recovery` も**存在しない**（★「測って0」ではなく「PLAN が起きていない」） |
| **E-5** | 副作用 | **★増えていない** | `tasks = 157`（基準 157 と同じ） |

## 1-1. ★planner は呼ばれた（★これが今回いちばんの収穫）
```
planner_outcome = {"recorded": false, "stage": "provenance", "plan": null,
  "reason": ["missing required provenance field: trace_id",
             "missing required resolvable id: rri_request_id",
             "missing required resolvable id: rri_intent_id"]}
```
- **★`planner_outcome` が `null` ではない＝`BUILD_PLANNER` は実際に呼ばれ、★呼ばれた上で fail-closed した。**
- **★失敗理由が捨てられずに応答へ載っている**（`CLAUDE_BARRIER` の一語に潰されていない）。
- **★`:8005` は0件**。`build_plan` が **LLM 呼び出しの前に provenance を検証する**設計どおりで、**★推測ではなく実測**（押した区間 JST 01:49:10〜01:49:30 の completion 要求 **0件**）。

---

# 2. ★区別して書く（★2通りに読める所を潰す）
```
★「Task → Runtime の配線が壊れている」ことは★示していない。
★示したのは「★PLAN の手前で止まるので、★Runtime へ到達しない」である（NOT_REACHED であって FAILED ではない）。
★D-146 の目的（押していないだけなのか、流れないのか）には答えが出た:
   → ★押しても流れない。★ただし理由は Task→Runtime ではなく、★その手前の PLAN の入力不足である。
```

---

# 3. ★私が行った操作（★全件）
```
★POST /api/run_next?task_id=TASK-2DER-0C458F38 を ★1回（01:49:16.553 → 01:49:16.940 / 0.39秒）
★応答は全文 保存（-o /dev/null を使っていない）
★コードを1行も変えていない  ★webui を再起動していない  ★再投入していない（submit 0回）
★他の task を押していない   ★止まった所を直していない・迂回していない  ★commit していない
★:8005 を自分で叩いていない ★61本の非回帰は走らせていない（★テストは0本＝走らせていない）
```

---
*IMPL → 設計/監査（写: MGR / Taka）。D-146＝`run_next` を `TASK-2DER-0C458F38` に**1回だけ押した確認（コード0行）**。**受理はされた（`refused` なし）／`BUILD_PLANNER` は実際に呼ばれた／しかし PLAN は provenance 検査で fail-closed し、`reason` は `trace_id`・`rri_request_id`・`rri_intent_id` の不足3件**。結果として **task の状態は前後で完全に不変（CREATED/CREATE/PLAN/CLAUDE/barrier=true）、`ARUN-00966`・`OBS-00967` はどちらも `resolved=false`＝新しい取得は1件も起きていない、`implementation_packet_ref` は無い（PLAN 未記録ゆえ `plan_source`/`runtime_recovery` は存在しない）、`tasks` は 157 のまま**。**`:8005` は0件**（provenance は LLM 呼び出しの前に検証される設計どおり・実測）。**★「Task→Runtime の配線が壊れている」ことは示していない——示したのは「PLAN の手前で止まるので Runtime へ到達しない」（NOT_REACHED であって FAILED ではない）。** 原因は **D-144 で私が書いた観測経路の knowledge_packet に、BUILD 経路（`submit.py:435-437`）が mint している provenance が入っていない**ことであり、次回確認箇所は **既存の `rri.intent_record.mint` でその3つを入れる1件**（★新しい ID 族を作らない・★私は実施していない）。*
