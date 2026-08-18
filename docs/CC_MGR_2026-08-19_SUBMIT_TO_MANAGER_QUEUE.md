# 宛: Taka / 設計 / 監査 ―― `/api/submit` → `manager_v0._queue()` の既存接続（★実装 0行）

**Claude はコードを書いていない。queue へ手で追加していない。`run_next` を叩いていない。**

## 0. 結論

```
★★自走経路は ★既に 完成していて ★動いている。
★★欠けていたのは 経路では なく ★★入口の 種類。

  ★契約文書を 置く 投入 → ★常駐が 拾う（★実績 76件）
  ★goal だけの 投入      → ★常駐は 拾わない（★口が 無い）
```

## 1. 四問への回答（★すべて 2DER の面・正規APIから）

### ① `manager_v0._queue()` の正規な供給元

```
_queue()      … runs/manager_queue.json を 読む（★file・★再起動で 忘れない）
_queue_add(t) … ★書く 唯一の 関数
QUEUE_FILE    = /home/takasan/twoder/runs/manager_queue.json
docstring 逐語「★投入した 順に 1件ずつ(★先入れ先出し)=★★優先順位を 付けない
                =★『どれが 重要か』は 決めない(★Taka 正本 §2.3)」
★現在値: _queue() = []  ／ _last_task() = None
```

### ② 過去に queue へ入った TASK はどの正規経路から入ったか

```
_queue_add の 呼び手 = ★manager_v0 の 内部 2箇所 だけ
   166行 … 並びへ 戻す（★進行中の 案件）
   176行 … _set_last_task(tid)  ← ★入口

_set_last_task の 外部からの 呼び手 = ★1箇所 だけ
   ★domain_dw.py:240
       res = _call("/api/submit", {"raw": d["raw"], "caller": "MANAGER_V0.submit_contract"})
       if res.get("task_id"):
           _set_last_task(res["task_id"])   # ★★投げた 案件を ★次の 巡回で 進める
```

**∴ queue に入るのは「★機械が 自分で 投げた 契約」だけ。**

### ③ `/api/submit` はその供給経路を通っているか

```
★通る。★ただし ★呼び手が `MANAGER_V0.submit_contract` の 時だけ 240行に 到達する。
★私(MGR)が front door を 外から 叩いた 投入は ★同じ 240行を 通らない
   ＝★task_id は 返るが ★誰も `_set_last_task` を 呼ばない
   ＝★★昨夜の TASK-2DER-F295B318 が CREATED の まま だった 理由（★判定 A の 内訳）。
```

### ④ 「TASK 作成 → manager 対象化」の口は在るか

**★在る。しかも常駐が毎周回している。**

```
manager_v0.main()   while True:
    record_stages()          … どこまで 来たかを 証拠から 記録
    receive_finished()       … 終わった 物の 成果物を 受け取る
    ★submit_next_contract() … ★置かれた 契約を 1件 投げる(★選ばない)
    tick()                   … ★並びの 先頭を run_until_barrier まで 進める
    sleep(INTERVAL)

★契約の 置き場 = CONTRACT_DOCS_DIR = ★/home/takasan/egl/docs
★実測（★読み取りのみ・投入していない）:
    契約文書 85件 ／ ★already(投入済み) 76 ／ skipped 9 ／ ★pending ★0
```

**★常駐は生きていて、契約を毎周探している。いま `pending = 0` ∴ 投げる物が無い ∴ queue が空。**

## 2. 最小欠落（★1つだけ）

```
★★front door への「goal だけの 投入」を manager の 待ち行列へ 載せる 口が 無い。
★在るのは ★契約文書経路（骨格＋封印試験）だけ。
```

## 3. ★完了条件に対する結果

```
★「front door へ goal を 1件 投入 → 常駐が 自力で 取得」= ★★不成立
   理由 = ★上の 最小欠落（★昨夜 TASK-2DER-F295B318 で 実測済み・24分 変化 0）
★Claude が run_next を 叩いた   = ★0
★Claude が queue へ 手で 足した = ★0
★Claude 実装                    = ★0 行
```

## 4. ★「2DER に実装 TASK として投入する」が今できない理由（★循環）

```
★goal 投入 → 常駐が 拾わない（★今回の 欠落 そのもの）
   ＝★★『この欠落を 直す 依頼』を goal で 投げても ★同じ 壁で 止まる = ★循環する
★★唯一 生きている 自走の 入口 = ★契約文書を egl/docs に 置くこと
   → 常駐 submit_next_contract が 拾い → /api/submit → task_id → _set_last_task
   → queue → tick → run_until_barrier（★全段 常駐が 自力で 回す）
★★但し 契約 = 骨格 ＋ ★封印試験（＝★完全な python source）
   ∴ ★Claude は 書けない（★今回の 逐語「Claude 自身はコードを書かない」）
★★契約を 書く 役は ★DESIGN（★実測 2026-08-18: 契約通過率 ★DESIGN 6/6 ／ ★MGR 4/9
   ＝★『出してはいけない結果』の 欄の 有無が 差 ∴ ★依頼文を 書く 役を DESIGN へ 移管済み）
```

**∴ 次の1手は「DESIGN へ契約作成を依頼する」。★MGR 文書の宛先は設計・監査（正本どおり）。**

**契約の中身（★私が決めない・DESIGN が骨格と封印試験を書く）に必要な要件はこれだけ:**

```
★front door が TASK を 作った 時、その task_id が manager の 待ち行列に 載ること。
★既存の `_queue_add` / `_set_last_task` を 使う（★新しい queue を 作らない）。
★優先順位を 付けない（★先入れ先出し＝正本 §2.3）。
★契約文書経路の 既存動作（domain_dw:240）を 壊さない。
★新しい Manager 0 ／ 新しい 判断規則 0 ／ 新台帳 0。
★★責務境界（★front door が manager の file を 書くのか、manager が front door に 訊きに行くのか）は
   ★私が 決めない = ★設計の 裁定事項。
```

## 5. 主指標

```
★★Claude なしの 自走距離が 1段 伸びたか = ★★伸びていない（★今回 実装 0・投入 0）
★ただし ★今回 確定した 事実:
    ①「manager は 拾わない」の 原因が ★呼び手の 違い（240行に 到達しない）と 特定できた
    ②★自走経路 4段（record_stages / receive_finished / submit_next_contract / tick）は
      ★既に 全部 常駐が 回している = ★★作る物は 少ない
    ③ 契約文書経路の 実績 = ★76件 投入済み ＝★★この経路は 実際に 動いた 事が 在る
```

## 6. していないこと

```
★実装 0 行 ／ queue へ 手で 追加 0 ／ run_next 0 ／ 再投入 0
★新しい queue 0 ／ 新しい Manager 0 ／ 新しい 判断規則 0
★責務境界を 私が 決めていない
★F14 実装 / 機能表 / acceptance / F15 / F16 に 戻っていない
```
