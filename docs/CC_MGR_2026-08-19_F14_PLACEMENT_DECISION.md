# 宛: Taka / 設計 / 監査 ―― F14 の配置先: **既存主体へ接続可能（案A = route_worker）**

**新しい判断規則を作っていない。`function_table` の命名・`MIN_OCCURRENCES`・duplicate 判定・`authority`・`register` を変更していない。実装 0。**

## 0. 結論

```
★★3択の答え = ★「既存主体へ接続可能」
★★配置先 = ★`twoder/route_worker.py`（常駐 `twoder-route-worker.service`）
★新しい常駐は 要らない ／ ★新しい管理主体は 増えない
```

## 1. 判断材料（★すべて正本の逐語・2DER の面から取得）

### (a) `register` 自身が名乗る item ―― **経路表の item**

```
function_table.register() の 中:
    authority.gate_for_item("REGISTER_FUNCTION", ★"ITEM-2DER-EVO-0058")

台帳（/api/resolve）:
    ITEM-2DER-EVO-0058  status=DONE
    title = 「EXEC_ARCH を経路表にする(区間ごとに 誰から誰へ/渡す/返る/落ち方) 急ぐ」
```

**★2DER 自身が、機能表の登記を「経路表 item の権限」で判定している。**

### (b) `function_table` がどの正本・どの器に属するか（module docstring 逐語）

```
「★機能表(★正本 §25 段3)=★人体図鑑の裏側=★機能から索引できる形。」
「★append-only は ★route_adopt と 同じ器(★event_trace)。★新台帳0・口0増・新しい承認工程0。」
```

**★同じ正本（経路・機能管理システム）／★同じ器（event_trace）／★同じ作法（route_adopt）。**

### (c) `route_worker` の責務境界（module docstring 逐語）

```
「Route Worker —— ★経路表を 実態に 合わせ続ける 常駐（★Taka 正本 2026-08-14 §13）。」
「★一文定義: 2DER で実際に何がどこからどこへ通ったかを、★証拠付きで 観測・更新する 機構。」

★これが判断しないもの（★正本 §3）
   期待された機能か ／ 結果が正しいか ／ この機能は必要か ／
   他機能との連動が正しいか ／ 全体目的との整合性
```

**`run_stage3 → register` は §3 の禁止5項目のどれにも当たらない。**
命名は「**この部品は一覧のどれか／無いか**」＝**実際に何をしているかの記述**であり、
「必要か・正しいか・整合するか」ではない。**しかも命名は Qwen と既存規則が持つ**（worker は回して呼ぶだけ）。

### (d) 「Route Worker に Manager の責務を追加しない」の**適用範囲**（★逆向きだった）

```
route_worker 逐語:
 「★なぜ Manager から分けたか（★正本 §12 逐語「Route Worker に Manager の責務を追加しない」）
   2026-08-14: ★MGR が manager_v0 の 巡回に ★経路表の更新を 入れた ＝★逆向きの 混線。
   混ざると 片方が 止まったとき もう片方も 止まる ／
   §10 が 名指しした「Route Worker が Manager になる」入口。
   ∴ ★置き場所を 移した（★作り直していない＝中身は 同じ）。」

manager_v0.tick 逐語:
 「★経路表の更新は ★ここに置かない（★Taka 正本 §12＝★Route Worker の仕事）→ twoder/route_worker.py」
```

**★§12 が禁じているのは「Manager 側に表の更新を置くこと」。**
**表の更新を Route Worker に置くことは §12 が命じた方向そのもの。**
禁じられるのは逆 ―― **Route Worker に「必要か・正しいか」の判断を持たせること**。今回それは足さない。

### (e) 既に周期実行の責務を持つ主体（★全部確認した）

| 主体 | 周期実行 | 責務（逐語） | 機能表を置けるか |
|---|---|---|---|
| `manager_v0`（`twoder-manager.service`） | ○ | 「READY な案件を既存の実行口で barrier まで進める」（正本 §2.2） | **✗** ―― tick 逐語で**明示的に禁止**（§12） |
| `route_worker`（`twoder-route-worker.service`） | ○ | 「経路表を実態に合わせ続ける」（正本 §13） | **○** |
| `webui`（`twoder-webui.service`） | ―（要求応答） | front door | ✗（周期実行の主体ではない） |
| GM `item_state` / `whose_turn` | ✗ | 読み取り集約のみ（★v1 の指示） | ✗ |
| Domain Manager `domain_dw` | ✗ | 「案件1件を (2)→(6) へ通す」 | ✗ |

### (f) 案B（新常駐）を採らない理由

```
★新 service = ★新しい管理主体が 1つ 増える
★Taka 原則「一つの閉塞を 解消するために 新しい管理対象を 二つ以上 増やさない」
   → ★既存で 足りるなら ★1つも 増やさない
★上申条件② (新しい Manager / 台帳 / 外部接続口) に 触れ得る
★かつ (a)(b) から ★機能表は 経路表と 同じ item・同じ器・同じ作法 ∴ 分ける 理由が 無い
```

## 2. 最小実装案（★配置先が一意に決まったので出す・★実装していない）

**`twoder/route_worker.py` に、`refresh_route_table` と同型の1手を足す。**

```python
FUNCTION_REFRESH_EVERY = <秒>          # ★run_stage3 は Qwen を叩く=重い ∴ 経路と同じ 60秒では 回さない
_LAST_FUNCTION_REFRESH = [0.0]         # ★self_check と 同じ 形（SELF_CHECK_EVERY の 隣）

def refresh_function_table():
    """★機能表を 実態に 合わせ続ける 1手（★判断は 持たない＝既存を 呼ぶだけ）。
    ★命名        = Qwen（function_table.run_stage3 の 中・3seed 全会一致）
    ★採択の条件  = function_table.MIN_OCCURRENCES（＝2）
    ★重複の判定  = function_table の duplicate_of_existing
    ★権限        = function_table.register の 中の authority
    ★ここが 持つのは『回す』と『呼ぶ』だけ。"""
    out = {"asked": 0, "ready": 0, "registered": [], "error": None}
    try:
        from twoder import function_table as _FT
        from ds import etrace as _ET
        r = _use("run_stage3", _FT.run_stage3, limit=len(_FT.components()))   # ★既存
        out["asked"] = (r.get("funnel") or {}).get("asked", 0)
        ready = {n: cs for n, cs in (r.get("candidates") or {}).items()
                 if len(set(cs)) >= _FT.MIN_OCCURRENCES}                       # ★既存規則
        out["ready"] = len(ready)
        if not ready:
            return out                                   # ★何も 足さない（★0件を 作らない）
        ts = datetime.datetime.now().isoformat()
        rid = _ET.open_run("機能表の採択", ts, entry="function_table.register")
        #     ↑ ★★走行を 開いてから 呼ぶ。開かないと authority が evidence=UNVERIFIED
        #       → 層3(REQUIRES_TAKA) で 落ちる（★2026-08-14 実測 ／ ★2026-08-19 再現）
        for name, comps in ready.items():
            for c in sorted(set(comps)):
                votes = next((x["votes"] for x in r["rows"]
                              if x["component"] == c and x.get("new_name") == name), None)
                if votes is None:
                    continue                             # ★票が 無ければ 登記しない（★作らない）
                res = _FT.register(name, c, votes, ts=ts, run_id=rid,
                                   approver="ROUTE_WORKER")      # ★呼び手の 識別
                out["registered"].append({"name": name, "component": c,
                                          "approved": res.get("approved"),
                                          "reason": res.get("reason")})
    except Exception as ex:
        out["error"] = "%s: %s" % (type(ex).__name__, ex)
    return out
```

`main()` へは `self_check` と**同じ形**で1つ足す:

```python
        try:
            if time.time() - _LAST_FUNCTION_REFRESH[0] >= FUNCTION_REFRESH_EVERY:
                _LAST_FUNCTION_REFRESH[0] = time.time()
                fo = refresh_function_table()
                if fo.get("registered") or fo.get("error"):
                    _record(fo)                 # ★動いた時と 失敗した時だけ 1行（既存の作法）
        except Exception as ex:
            print("ROUTE_WORKER function_refresh_failed: %s: %s" % (type(ex).__name__, ex), flush=True)
```

### ★この案が増やさないもの

```
★新しい 判断規則 0（命名/2部品/全会一致/duplicate/authority は すべて 既存を そのまま 呼ぶ）
★新しい 台帳 0（★event_trace＝route_adopt と 同じ器）
★新しい service 0 ／ 新しい 管理主体 0 ／ 新しい 承認工程 0
★front door の 口 0増
```

### ★決めていないもの（★設計/Taka の裁定事項）

```
★`FUNCTION_REFRESH_EVERY` の 値。★run_stage3 は Qwen を 73〜76部品 × 3seed 叩く＝重い。
   ★経路側の INTERVAL=60 と 同じにしない。★self_check は 24h。私は 数字を 決めない。
```

## 3. 完了条件に対する現状

```
★完了条件=「Claude が 手で run_stage3 / register を 呼ばなくても 2DER 自身が 繰り返し 機能表を 育てられる 配置先が 確定すること」
★★確定した = ★route_worker（既存主体・新しい管理主体 0）
★ただし ★実装は していない ∴ ★まだ 育っていない（★次の 手番）
```

## 4. 報告

```
★結論              = ★既存主体へ接続可能（案A = route_worker）
★Taka 途中裁定      = 0
★Claude 判断        = 0（★候補選択・命名・採択判断を していない ／ 配置は 正本の 逐語で 決まった）
★新規判断規則       = 0
★新規実装           = ★0 行
★Claude が run_stage3 / register を 呼んだ回数 = ★各 0（今回）
★F15 / F16 / F1 / acceptance / 並列化 = 入っていない
```
