# 宛: Taka / 設計 / 監査 ―― F14: 機能表側の最小 worker 責務（★設計のみ・実装0）

**新しい機能表・新しい分類器・新しい判断規則を作っていない。Claude は候補選択・命名・採択判断をしていない。**

## 0. 二つの問いへの答え

```
★問1「run_stage3 を 定期実行・継続実行する 既存の 常駐が 在るか」   → ★★無い
★問2「採択条件 成立後に function_table.register() を 呼ぶ 既存責務が 在るか」→ ★★無い
```

### 根拠（実測）

```
常駐 service（systemd --user・すべて active/running）:
    twoder-manager.service      「READY な案件を既存の実行口で barrier まで進める」
    twoder-route-worker.service 「経路表を実態に合わせ続ける／Taka 正本 §13」
    twoder-webui.service        「front door (:8770)」

★`run_stage3` の 呼び手 = ★0
   （唯一の 一致は function_table.py:154＝★自分の 本体内の open_run 行）
★`function_table.register` の 呼び手 = ★0

★route_worker が function_table に 触れる 唯一の 箇所 = `SELF_CHECK_INCLUDES`（103-107行）
   ＝ self_check の 対象一覧。逐語「★これが 見つける物 = ★『見ると 増える 計器』」
   ＝ ★読むだけ。★育てる 手は 持っていない。
```

**∴ 接続すべき既存の呼び手が無い。**

## 1. 同型の既存作法（★経路表側・いま動いている）

```
route_worker.main()          while True:
  └ refresh_if_needed()      … 引き金は 2DER の `needs_refresh`（★人が 判断しない）
      └ refresh_route_table()
          segs       = front door /api/control?include=observed_edges → segments_from_records.rows
          registered = route_adopt.route_table_view() の hand+machine の (source,target)
          for sg in segs:
              if sg["evidence"] != "BOTH": skip          ← ★既存の 成立条件
              if pair in registered:       skip          ← ★二重登録しない
              rid = _ET.open_run(...)                    ← ★1巡回で 1本だけ 開く
              route_adopt.adopt(v)                       ← ★権限の規則(authority)に 掛かる
  └ sleep(INTERVAL = 60)
```

**実績: machine 206 → 207（2026-08-19・★常駐が 3分後に 自力で 採択）。**

## 2. 機能表側の最小 worker 責務（★不足分だけ・新しい規則 0）

```
refresh_function_table():                                  # ★同型。名前だけ 対応させる
    r     = function_table.run_stage3(limit=len(function_table.components()))
            #   ↑ ★既存。命名は Qwen3.6-35B-A3B・3seed 全会一致・prompt_version=menu_vote_v1
    ready = {name: comps for name, comps in r["candidates"].items()
             if len(set(comps)) >= function_table.MIN_OCCURRENCES}     # ★既存規則(=2)
    if not ready:
        return                                              # ★何も 足さない(★0件を 作らない)
    rid = etrace.open_run("機能表の採択", ts, entry="function_table.register")
            #   ↑ ★★走行を 開いてから 呼ぶ。開かないと authority が
            #     evidence=UNVERIFIED → 層3(REQUIRES_TAKA) で 落ちる（★2026-08-19 実測・★2026-08-14 既出）
    for name, comps in ready.items():
        for c in comps:
            votes = <r["rows"] の 該当行の votes をそのまま>   # ★票は 作らない・写すだけ
            function_table.register(name, c, votes, ts=ts, run_id=rid, approver=<常駐の識別>)
            #   ↑ ★既存。中で authority.gate_for_item("REGISTER_FUNCTION","ITEM-2DER-EVO-0058")
```

### ★不足しているのは4点だけ

| # | 不足 | 同型の既存作法 |
|---|---|---|
| **(1)** | 常駐から `run_stage3` を回す1手 | `refresh_route_table` が `/api/control` を引く手 |
| **(2)** | 条件成立時に `register` を呼ぶ1手 | `route_adopt.adopt(v)` の呼び出し |
| **(3)** | **走行を開いてから呼ぶ** | `rid = _ET.open_run(...)`（★1巡回で1本） |
| **(4)** | 1巡回あたりの上限（`run_stage3` は Qwen を叩く＝重い） | 「★1巡回で 1本だけ 開く」の節度 |

**★新しい判断規則 0** ―― 命名(Qwen)／`MIN_OCCURRENCES=2`／3seed 全会一致／`duplicate_of_existing`／
`authority` の層判定／`register` はすべて**既存のものをそのまま呼ぶだけ**。

### ★これで F14 が解ける理由（★機構は往復で前進する）

```
run_stage3 は 最初に 条件成立した 1件で 停止する（★実測: asked 7 で 停止）
  → 採択されると 次の走行では その名前が `duplicate_of_existing` として 飛ばされ ★より先へ 進む
  → 常駐が これを 繰り返せば 母数の 後方（★我々の component は 47番目）にも 到達する
∴ ★足りないのは「繰り返す 手」だけ。★篩でも 規則でも ない。
```

## 3. ★置き場所（★私は決めない＝設計の裁定事項）

| 案 | 中身 | 論点 |
|---|---|---|
| **A** | `route_worker` に1手足す | 正本 §12 逐語「**Route Worker に Manager の責務を追加しない**」。機能表は `function_table` docstring 逐語「★機能表(★正本 §25 段3)=★人体図鑑の裏側」＝経路表の裏側だが**責務は別**。抵触するかは設計の判断 |
| **B** | 新しい常駐を1つ立てる | **★新しい管理対象が1つ増える**（上申条件②に触れ得る） |

**どちらも「新しい判断規則」は増えない。増えるのは実行の場所だけ。**

## 4. 完了条件 → **★不成立**

```
★完了条件=「Claude が run_stage3 も register() も 手で 呼ばず、
            新しい component 1件が function_table の machine 行へ ★自動追加される」
★結果 = ★不成立。★今回 私は どちらも 呼んでいない ∴ machine 行は 増えていない。
★自動循環が 止まった段 = ★★常駐に 機能表側の 1手が 無い
   （★段2 `run_stage3` の 呼び手 0 ／ ★段4 `register` の 呼び手 0 ―― ★両方）
```

## 5. 報告

```
★Taka 途中裁定        = 0
★Claude 判断          = 0（★候補選択・命名・採択判断を していない）
★新規判断規則         = 0
★新規実装             = ★0 行（★設計のみ）
★Claude が run_stage3 を 呼んだ回数 = ★0（今回）
★Claude が register を 呼んだ回数   = ★0（今回）
★F15 / F16 に 入っていない
```

## 6. していないこと

```
★実装 0 ／ 新 service 0 ／ 新しい機能表 0 ／ 新しい分類器 0 ／ 新しい判断規則 0
★置き場所（案A/案B）を 私が 決めていない
★F1 / acceptance / RRI / 並列化 に 入っていない
```
