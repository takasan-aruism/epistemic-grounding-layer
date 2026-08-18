# 宛: DESIGN（監査 CC）―― 契約作成の依頼: goal 投入の TASK を manager の待ち行列へ載せる

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。この文書は要件だけです。**

---

## 1. 直してほしいこと（★1点だけ）

```
front door へ ★goal として 投入され TASK が 生成された 後、
その TASK が ★既存の manager の 待ち行列（_queue）へ 入らない。
```

## 2. 現在地（★すべて 2DER の正規面から取得した実測値・2026-08-19 04:19）

```
manager_v0._queue()      = []
manager_v0._last_task()  = None
manager_v0.whose_turn()  = checked 0
契約文書（egl/docs）      = pending 0 ／ already 76 ／ skipped 9
常駐 twoder-manager.service = active/running（pid 926888・NRestarts 0）
```

### 自走経路は★既に完成していて動いている

```
manager_v0.main()   while True:
    record_stages()
    receive_finished()
    ★submit_next_contract()      ← ★契約文書経路（実績 76件）
    tick()                        ← ★並びの 先頭を run_until_barrier まで 進める
    sleep(INTERVAL)
```

### 待ち行列へ入る唯一の外部経路

```
domain_dw.py:240
    res = _call("/api/submit", {"raw": d["raw"], "caller": "MANAGER_V0.submit_contract"})
    if res.get("task_id"):
        _set_last_task(res["task_id"])      # → _queue_add(tid) → runs/manager_queue.json
```

**∴ `/api/submit` は通るが、★呼び手が `MANAGER_V0.submit_contract` の時だけ240行に到達する。**
**外から goal で叩いた投入は到達せず、`task_id` は返るが誰も `_set_last_task` を呼ばない。**

### 実証（★昨夜の実測・判定 A）

```
TASK-2DER-F295B318（goal 投入・request_type=MODIFY_EXISTING・next=PLAN）
    → ★24分間 dw_state=CREATED の まま ／ _queue()=[] ／ PLAN 供給の 試行記録 ★0件
    ＝★機械が 試して 落ちたのでは なく ★★一度も 始まっていない
```

## 3. 要件（★Taka 逐語）

```
★新 queue を 作らない
★新 Manager を 作らない
★優先順位規則を 作らない
★既存 `_queue_add` / `_set_last_task` を 再利用する
★既存の 契約文書経路を 壊さない
★goal 投入で 生成された TASK だけを、正規に manager の 対象へ 渡せること
```

## 4. ★DESIGN が決めること（★MGR は決めていません）

```
★front door が manager 内部 file を 直接 操作する 設計にするか、
★manager が front door 側から 取得する 設計にするか
   → ★既存の 責務境界・正本から ★DESIGN が 決める
```

**判断材料として、MGR が引いた正本の逐語を並べます（★解釈は付けません）:**

```
manager_v0 module docstring（正本 §2.2）
   「台帳／task の状態を引く → 既存規則が runnable と判定した案件を、
     既存の正式な実行口で barrier まで進める」
manager_v0 module docstring（同 §2.3）
   ★これが持たないもの: 設計の良し悪し／コードの内容／★優先順位／権限境界／
     不可逆の承認／未知の例外への創作的対処
_queue() docstring
   「★投入した 順に 1件ずつ(★先入れ先出し)=★★優先順位を 付けない
     =★『どれが 重要か』は 決めない(★Taka 正本 §2.3)」
manager_v0.tick docstring
   「★経路表の更新は ここに置かない（★Taka 正本 §12＝Route Worker の仕事）」
route_worker module docstring（正本 §12 逐語）
   「Route Worker に Manager の責務を追加しない」
Taka 常設制約
   「★入口は 一つ＝webui 経路（/api/submit・/command）。CLI は BYPASS」
   「一つの閉塞を解消するために新しい管理対象を二つ以上増やさない」
```

**MGR が触れた既存の関連事実（★参考・★決定ではありません）:**

```
・`_queue_add` / `_set_last_task` は `manager_v0` にあり、`domain_dw` が import して使っている
・`QUEUE_FILE = /home/takasan/twoder/runs/manager_queue.json`
・front door の 口は 18本。★item / task を 追記する 口は 無い（2026-08-18 実測）
・front door は ★単一障害点（落ちると commit が 0）
```

## 5. 契約に必要なもの（★形式は既存どおり）

```
`<<<2DER:SKELETON>>>` … 骨格
`<<<2DER:IMMUTABLE_TESTS>>>` … 封印試験（★完全な python source）
`<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs （★CONTRACT_DOCS_DIR）
命名   = CC_MGR_2026-08-19_CONTRACT_<name>.md （★既存76件と同じ形）
→ ★置けば 常駐 `submit_next_contract` が ★次の巡回で 自力で 投げる（★人は 何もしない）
```

**★MGR は骨格も封印試験も書きません。**（★実測 2026-08-18: 契約通過率 ★DESIGN 6/6 ／ ★MGR 4/9。
差は「出してはいけない結果」の欄の有無 ∴ 依頼文を書く役を DESIGN へ移管済み。）

**★封印試験に必ず書いてほしい観点（★過去の失敗の型から。★試験の中身は DESIGN が決める）:**

```
★大小 … 空の 待ち行列 ／ 既に 同じ id が 在る 場合（★重複を 作らない）
★順序 … 先入れ先出しが 保たれるか（★優先順位を 付けない）
★空・None … task_id が None / 空文字 の 時（★front door は ★拒否も 200 を 返す）
★既存経路 … 契約文書経路（domain_dw:240）が ★壊れていないこと
★冪等 … 同じ TASK が 二度 載らないこと
```

## 6. 受入（★MGR が front door と GM の正規面で確認します）

```
① goal を front door へ ★1件 投入
② TASK が 生成される
③ ★Claude は queue に 触らない・run_next を 叩かない
④ ★常駐 manager が その TASK を ★自力で 取得する
⑤ `_queue()` / `_last_task()` / `whose_turn()` の 正規面で 取得を 確認
⑥ 少なくとも ★PLAN 処理の 開始地点まで 自走する
```

**⑥より先で止まった場合、MGR は穴埋めせず、その地点を次の自走停止点として報告します。**

## 7. MGR がしていないこと

```
★設計 0 ／ 実装 0 ／ 契約本文 0 ／ 責務境界の 決定 0
★queue へ 手で 追加 0 ／ run_next 0 ／ 再投入 0
```
