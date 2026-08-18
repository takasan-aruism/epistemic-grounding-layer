# 宛: Taka / 設計 / 監査 ―― EVO-0077 β 実測（★1件だけ・実測値のみ）

**結論: ITEM → TASK → RRI thread が★人の記憶なしで一本につながった。**

## 0. 引いた値（すべて front door と既存 API から）

```
入口     : POST /api/submit  （★本文の鍵は `raw`。★`raw_input` では ValueError=★私が 1度 間違えた）
走行     : ETR-9c212273aee1
item     : ITEM-2DER-EVO-0077 （★既存。★新 item を 作っていない）
```

| 段 | 引いた口 | 値 |
|---|---|---|
| ① submit | `/api/submit` の `status_note` | `actor=MGR stage=RECORD via=front_door run=ETR-9c212273aee1` |
| ② task 生成 | `/api/resolve?id=TASK-2DER-3BD206A0` | `resolved=true` |
| ③ task_ids append | `/api/resolve?id=ITEM-2DER-EVO-0077` | **`task_ids = ["TASK-2DER-3BD206A0"]`** |
| ④ item_state | `manager_v0.item_state(item_id)` | `task_turns` が **★UNKNOWN でなくなった** |
| ⑤ TASK state | `/api/state?task_id=…` | `dw_state = CREATED` |
| ⑥ rthread_id | 同上 | **`RTHREAD-206fd571`** |

**★入口は ITEM の id ★1つだけ。**②〜⑥はすべて①が返した値を順に渡しただけで、
**私が 記憶から 補った 値は 0 個。**

### ④ の中身（実測）

```json
task_turns = [{"task_id":"TASK-2DER-3BD206A0","state":"CREATED",
               "operation":"PLAN","actor_role":"MANAGER","who":"CLAUDE"}]
```

**前回（2026-08-19 早い時刻）の実測は `task_turns = null`（★task_ids が 空）。**
∴ **④は「空だから引けない」から「引けた」へ変わった。**

## 1. 走行の経過（★2回 引いた・同じ問い）

```
 0分  事象= 17    最後= RRI/preflight_gate   task_ids=[]                     task 在り=False
 2分  事象= 1330  最後= HANDOFF/S12          task_ids=["TASK-2DER-3BD206A0"] task 在り=True
```

**★0分の時点で「効いていない」と結論しかけた。** 走行が `preflight_gate` で 2分 動かず、
私は front door の CPU（424秒中 7分20秒＝実働中）を見て**待つ側へ倒した**。
**1回の観測で断定していたら、通っている物を「通らない」と報告していた。**

## 2. 何を作ったか（★Taka 裁定 β の逐語条件に対して）

| β の条件 | 実際 |
|---|---|
| 新台帳 0 | **0**（`ROADMAP_REGISTRY.jsonl` のみ） |
| 新 ID 0 | **0**（id の採り方は `submit.py:638` の既存式をそのまま使う＝★再計算しない） |
| replace 禁止・append のみ | `append_task_id` は `cur + [task_id]`。**既存行を書き換えない**（`set_status` と同じ作法） |
| 過去履歴は移行しない | **触っていない**（散文2件はそのまま） |
| 成功/失敗を問わず残す | 削除経路を作っていない |
| `submit.py` からだけ呼ぶ | 呼び手は **2箇所のみ**（`submit.py:670` / `753`） |
| 進捗マーカー付きだけ | `if _prog and _prog.get("item")` で囲んである |

**commit `bc254ef`**（`[Claude実装]` / `CLAUDE_IMPL=1` / source のみ・記録と混ぜず）→ push 済み。

## 3. ★まだ埋まっていない欄（隠さない）

### (a) `item_state` の `rri_thread` は **今も null**

```
★理由=★item_id から RRI thread を 直接 引く 口は ★今も 無い
★ただし ITEM→TASK→RRI は ★つながった（★TASK の state が rthread_id を 持つ）
∴ 「引けない」ではなく「★item_state が まだ その道を 通っていない」
```

**私は直していない。**（v1 は読み取り集約のみ・新しい判断規則を作らない、という Taka の指示の内側に留める）

### (b) ★試していないこと

```
★冪等（同じ依頼文を 2回）=★未測定。★コードは 冪等（既出なら None）だが ★走らせていない
★契約経路（submit.py:753 側）=★未測定。★契約投入は マーカーを 持たない＝★α の 話
★過去 27件 =★埋めていない（★遡らない）
★acceptance 照合 =★入っていない
```

## 4. ★私の手番で起きた事故（記録として残す）

```
① submit.py を ★私が 壊した（構文エラー）
   原因=★挿入位置。659行は `try:` の 内側（except は 661行）
   =★構造の 中に 別の 構造を 差し込んだ
   直し方=★git checkout で 戻し、★アンカーを `_rec("DW_TASK_ID", <task>)` の 直後へ 変えた
   ★`None` を 記録する 4箇所には 入れていない（★作らなかった 時に 足すと 嘘になる）

② 投入の 鍵を `raw_input` と 決め打ち → ValueError
   ★口の 実物（webui.py:1377 `SUB.submit(b.get("raw",""))`）を 読んで 直した

③ front door の 再起動が ★権限の 分類器に 拒否された
   ★迂回しなかった。★Taka に 1行だけ 依頼して 実行してもらった
   ★再起動前の 記録は 取ってある: pid 1421718 / 入口 200・0.10秒 /
     未処理 TASK-2DER-GPU-SWITCH-001 = READY_FOR_AUDIT
   ★再起動後: pid 1490956 / 入口 200・0.026秒
```

**①〜③はいずれも「ソースに在る≠動く」の別の顔。**

## 5. α へは進んでいない

```
★契約投入 全般へ item マーカーを 要求する α には ★入っていない
★α の 是非は この 1本の 実測を 見て Taka が 別途 裁定する（★逐語）
```
