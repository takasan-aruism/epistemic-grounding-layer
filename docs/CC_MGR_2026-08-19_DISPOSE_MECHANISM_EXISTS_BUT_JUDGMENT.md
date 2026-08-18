# 宛: Taka / 設計 / 監査 ―― DISPOSE: **機構は在り・接続済み・正しく作動して「機械では処分できない」と判定**

**Claude は DISPOSE していない。`run_next` を叩いていない。所見を手で処分していない。**

## 0. 結論

```
★★DISPOSE の 既存機構 = ★在る（★しかも ★本線に 接続済み・★過去に 実績も 在る）
★★自動処分できたか   = ★できない（★★機構が 判定した 結果=★判断が 要る 所見だった）
★★自走距離           = ★0段 伸びた（★DISPOSITION_REQUIRED の まま）
★★次の停止点         = ★★DISPOSE ―― ★接続の 欠落では なく ★★所見の 中身が 判断を 要する
```

## 1. 四問への回答（★すべて 2DER / 正本の面から）

### ① `DISPOSITION_REQUIRED → DISPOSE` の正本上の供給主体

```
dw/dispatch.py::_MAP（★正本・9状態）
   DISPOSITION_REQUIRED -> ('DISPOSE', ★'MANAGER', 'LATEST_FINDINGS', ★True)
dw/dispatch.py:44 逐語
   "MANAGER": "CLAUDE",   # disposition = senior judgment (Claude barrier)
```

### ② 既存の disposition 判定器・処分記録口

**★両方在る。**

```
判定器 = dw/disposition.py（★ART-d084787ab0・owner=DW・2107B）
   docstring 逐語:
   「DW mechanical disposition (DE-0185). Deterministic ACCEPT/REJECT of audit findings from
     RECORDED DW state ONLY — no :8005, no code execution, no Qwen.」
   「Findings that need judgment (no mechanical reproduction signal) are NOT dispositionable and
     stay a Claude barrier. ★This is the seam that lets dispatch/operator auto-serve the DISPOSE
     barrier ONLY when it is rule-based — PLAN / UPPER_REVIEW / authority remain human decisions.」
   公開関数:
     mechanically_dispositionable(findings, view)
     reproduction_dispose_fn(findings, view)     … ACCEPT 再現する物 / REJECT 再現しない物
記録口 = dw/workcell.py::record_disposition ／ _latest_findings
試験   = test_auto_disposition.py（★ART-b1c8421851）
```

### ③ 過去に機械が DISPOSE した実績

**★在る。**

```
webui.py:597-599（★MANAGER actor の 中身）
    disp = DISP.reproduction_dispose_fn(findings, view)
    W.record_disposition(tid, disp, _now(), ★"2der-auto-dispose")
    return {"dispositions": disp, ★"auto": True}
走行記録に ★"MECHANICAL_DISPOSITION" の 語を 持つ 走行が 在る
    /home/takasan/twoder/runs/SUBMIT-3uIuwA.trace.json
```

### ④ 常駐 manager がそれを呼ぶ既存経路

**★在る。★接続済み。**

```
常駐 manager_v0.tick() → /api/run_until_barrier（front door）
   → webui の actors（★_machine_registry）= {CODING_WORKER, INDEPENDENT_AUDITOR,
        ★MANAGER, BUILD_PLANNER, CLAUDE_SENIOR}    ← ★MANAGER actor が 登録されている
   → dw/dispatch.py:117-123
        if op == "DISPOSE" and fn is not None:
            if DISP.mechanically_dispositionable(W._latest_findings(view), view):
                result = fn(task_id, view, nlo)
                return {..., "auto_served": ★"MECHANICAL_DISPOSITION"}
            # not mechanically dispositionable -> ★fall through to the Claude barrier
```

## 2. ★今回この機構が返した値（★実測・読み取りのみ）

```
task = TASK-2DER-4E2A58F2 ／ state = DISPOSITION_REQUIRED ／ 所見 = ★3件
★DISP.mechanically_dispositionable(findings, view) = ★★False
```

**所見3件（Qwen 監査が出した物・★category だけ写す。★私は中身を評価しない）:**

```
① category = requirement_not_implemented ／ severity = high
② category = self_report_primitive       ／ severity = medium
③ category = scope_expansion             ／ severity = low
```

**`disposition.py` が機械処分できる category は `_TEST_CATEGORIES = ('test_failure','failing_test','test_regression')`**
**か、明示の `reproduced` 真偽を持つ所見だけ。★3件ともどちらにも当たらない。**

**∴ 機構は「壊れて止まった」のではなく、★設計どおり fail-closed で Claude barrier へ落ちた。**

## 3. ★これは「接続の欠落」ではない（★前回までと型が違う）

```
これまでの 停止点（★F14 / manager queue）= ★口は 在るが ★誰も 呼んでいない（★接続の 欠落）
★今回の 停止点                            = ★口も 呼び手も 在り ★毎回 呼ばれている
                                            ★機構が「これは 判断が 要る」と ★判定した
```

**∴ 接続を1本足しても越えられない。**

## 4. ★Taka の裁定が要る（★私は決めない・★上申条件⑥「Taka 固有の価値判断」に当たる）

```
選べる 道は 3つ。★どれも 私の 一存では 決められない。

A. ★このまま Claude barrier を 維持する（★DE-0185 の 設計どおり）
   → ★DISPOSE は 恒久的に Claude が 要る 段として 残る
   → ★『Claude を 通常系から 外す』は ★ここで 頭打ち

B. ★機械処分できる 所見の 範囲を 広げる（★`_TEST_CATEGORIES` の 拡張 など）
   → ★★判断規則の 変更 ＝ ★上申条件① に 当たる
   → ★リスク: 判断が 要る 所見を 機械が 握り潰す（★fail-closed を 緩める）

C. ★DISPOSE の 供給主体を 別の 機械役へ 移す（★例: Qwen 監査とは 別の 判定役）
   → ★★_MAP（正本）の 変更 ＋ ★新しい 役 ＝ ★上申条件①② に 当たる
   → ★★正本 逐語「disposition = senior judgment (Claude barrier)」と 正面から 衝突する
```

**★私の見立て（★決定ではない）: A のまま置き、`UPPER_REVIEW` の停止点と合わせて Taka が一度に裁定するのが安い。**
**理由: B も C も「Claude を外す」ために fail-closed を緩める方向で、これは 2DER が繰り返し守ってきた線を跨ぐ。**

## 5. 最終報告（4点）

```
★DISPOSE 既存機構の 有無 = ★★在る（判定器 dw/disposition.py ／ 記録口 W.record_disposition
                              ／ 呼び手 dw/dispatch.py:117 ／ actor は webui に 登録済み
                              ／ 実績 SUBMIT-3uIuwA.trace.json に "MECHANICAL_DISPOSITION"）
★自動処分できたか         = ★★できない
                              （mechanically_dispositionable = False。所見3件が
                               test 系でも reproduced 明示でも ない＝★判断が 要る）
★Claude なしの 自走距離が 何段 伸びたか = ★★0段
★次の停止点               = ★★DISPOSE（★接続の 欠落では なく ★★所見の 中身が 判断を 要する）
                              ★その 先に UPPER_REVIEW_MISSING も 残っている（★今回 触っていない）
```

## 6. していないこと

```
★Claude の DISPOSE 判断 = ★0 ／ ★Taka 途中裁定 = ★0
★run_next を 叩いていない ／ 所見を 手で 処分していない
★_TEST_CATEGORIES を 広げていない ／ _MAP を 触っていない
★UPPER_REVIEW に 入っていない ／ 周辺 FINDING へ 脱線していない
★所見の 中身（★正しいか）を 評価していない ―― ★それは DISPOSE そのもの
```
