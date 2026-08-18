# 宛: Taka / 設計 / 監査 ―― F14 投入の単独走行: **A. manager が案件を拾っていない**

**Claude は F14 を実装していない。PLAN を供給していない。再投入していない。`run_next` を叩いていない。**

## 0. 判定

```
★★A. manager が 案件を 拾っていない
```

## 1. ①の確認 ―― 常駐 `twoder-manager` が処理対象として取得した記録

**取得していない。**

```
manager_v0._last_task() = ★None
manager_v0._queue()     = ★[]            （★空）
manager_v0.whose_turn() = checked ★0

★`_last_task()` の 実装（★docstring 逐語）:
   「★並びの 先頭で ★まだ 終わっていない 案件を 返す。★終わった 物は 並びから 落とす。」
   → ★中で `_queue()` を 読む。★`_queue()` が 空 ∴ ★何も 返さない。

常駐 twoder-manager.service = active / running（pid 926888・NRestarts 0）
   ＝★プロセスは 生きている。★対象が 無い。
```

## 2. ②の確認 ―― PLAN を機械供給しようとした実行証拠

**①で「拾っていない」と出たので②は本来不要だが、記録不足で D にしないため引いた。**

```
走行 ETR-7136019e0f2b（front door /api/etrace）＝ 事象 ★29件
★PLAN / build_planner / GENERATE を 名乗る 事象 = ★0件
★在るのは DISPATCH.next_legal_operation（＝★次に何かを 訊いただけ。★供給を 試していない）
末尾: SEAL.extract_contract → HANDOFF S09 → DW._append_event
      → DISPATCH.next_legal_operation → HANDOFF S12 / S16 / S01

∴ plan_template 成功/失敗 = ★試行の 記録なし
   build_planner が 呼ばれたか = ★呼ばれていない
   Qwen PLAN 生成 = ★なし ／ validation = ★なし
   fail-closed で barrier に 落ちたか = ★★「落ちた」のではなく ★★一度も 始まっていない
```

**TASK の現在地（front door `/api/state`）:**

```
dw_state = CREATED ／ next_operation = PLAN ／ actor_role = CLAUDE
claude_barrier = True ／ dispatch_status = "PENDING EXTERNAL ACTOR"
last_completed_op = CREATE
```

**`claude_barrier=True` は「PLAN に到達したら Claude の番」という `_MAP` の宣言であって、
「機械が試して落ちた」ではない。**（★私は最初これを C と読みかけた。★記録が否定した。）

## 3. 投入の記録（★Claude がしたこと＝投入と観測のみ）

```
POST /api/submit（front door・caller=MGR）
   raw = ★言葉だけ（★コード 0行・関数名 0・実装方法 0）
   進捗マーカー = item: ITEM-2DER-EVO-0079 / actor: MGR / stage: IMPLEMENT
返り:
   task_id = TASK-2DER-F295B318（★生成規則から 算出した id と 一致）
   request_type = MODIFY_EXISTING ／ acquisition_method = DW_IMPLEMENTATION
   next_legal_operation = PLAN ／ guard_block = None ／ failure_memory_match = None

GM 追跡（manager_v0.item_state("ITEM-2DER-EVO-0079")）:
   0分 task_ids 空
   2分 task_ids=["TASK-2DER-F295B318"] ／ dw=CREATED ／ next=PLAN
       ／ barrier=true ／ rthread=RTHREAD-522fd780
   12分 ★変化なし
```

**★β の追記口（`append_task_id`）は2件目も効いた** ―― GM が item_id 1つから TASK と RRI まで到達した。

## 4. 最終報告（4点）

```
★2DER 単独で 通過した段
    ① 受信（front door /api/submit）
    ② DS / RRI / EGL / SEAL（★S01〜S09 の 記録あり）
    ③ TASK 生成 ＋ ★item への task_ids 追記（★β の口）
    ④ RRI thread 生成（RTHREAD-522fd780）
    ⑤ dispatch が 次の 操作を 判定（PLAN）
    ＝★★投入から TASK 生成・GM 追跡可能な 状態までは 自走した

★最初の 停止点
    ★★常駐 manager の 案件取得（`_queue()` が 空 ∴ 投入した 案件が 待ち行列に 入らない）
    ＝★PLAN の 手前。★PLAN 機械供給は ★一度も 始まっていない。

★Claude が 必要だった段
    ★1つ = ★投入（front door を 叩く 手）
    ★それ以外で Claude が 触った段は ★0（★実装 0行・PLAN 供給 0・run_next 0・再投入 0）

★次に 機械化すべき 1箇所
    ★★front door への 投入が 常駐 manager の 待ち行列に 入る 経路
      （★front door `/api/submit` → `manager_v0._queue()` の 間が 繋がっていない）
    ★これが 繋がるまで、★何を 投入しても 常駐は 拾わない
      ＝★GM→Qwen→GM の 一周は ★開始点に 到達しない。
```

## 5. していないこと

```
★F14 を 実装していない（★Claude 実装 0行）
★PLAN を 供給していない ／ run_next を 叩いていない ／ 再投入していない
★推測で 埋めていない（★C と 読みかけたが ★記録が 否定した ∴ A に 訂正した）
★F15 / F16 / F1 / acceptance / 並列化 に 入っていない
```
