# 【BUILD SPEC】`EVO-0048` — **`?task_id=` は DW の段しか拾えない。★run_id も一緒に返す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 22:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.5）** ／ **★9項目 確認済（★§5）** ／ **★3値 確認済（★§1）** ／ 親: `ITEM-2DER-EVO-0035`
- **★裁定の在り処**: `ITEM-2DER-EVO-0048` の `status_note`
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★3値（★先に測った）

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| event に `task_id` は在るか | **★在る** | `etrace.py:110` 逐語 `"trace_id": trace_id, ★"task_id": task_id, "ts": _now()` |
| 全段が `task_id` を持つか | **★★持たない** | 実測（`ETR-986a8828c470` / `ETR-6ac2535ce2b1`）: `task_id` 内訳 = **`{None: 5, TASK-…: 2}`** ＝ **`task_id` が入るのは DW の `_append_event` だけ**（`workcell.py:98` 逐語 `task_id=task_id`）。SUBMIT / DS / RRI / EGL は **`None`** |
| task で引く関数は在るか | **★無い** | `etrace.py` の公開関数は `open_run` / `current_run_id` / `set_run_id` / `pop_failures` / `emit` / `resolve_run` / `resolve_event` の7つだけ |

```
★★∴ ★裁定の逐語「既存 resolve を呼ぶ」は ★そのままでは実現できない——★task で引く関数が ★無い。
★★★1つ足す（★`resolve_run` と ★同じ形にする。★新しい台帳・新しい記録は ★作らない）。
★★★★★そして ★`?task_id=` だけでは ★DW の段しか出ない ∴ ★★run_id も一緒に返し、★呼び手が続きを引けるようにする。
```

## 2. やること（★2箇所）

### 2-1. `ds/ds/etrace.py` — `resolve_run` の直後に1関数
```python
def resolve_task(tid):
    """task_id の event を ★run をまたいで集める。該当が無ければ ★None（空 dict を返さない）。
    ★注意: task_id が入るのは DW だけ ∴ 併せて ★run_ids を返し、呼び手が続き(SUBMIT/DS/RRI/EGL)を引けるようにする。"""
    evs = [e for e in _read_all() if e.get("task_id") == tid]
    if not evs:
        return None
    total = len(evs)
    return {"task_id": tid, "events": evs[:MAX_EVENTS], "count": min(total, MAX_EVENTS),
            "truncated": total > MAX_EVENTS, "total": total,
            "run_ids": sorted({e.get("run_id") for e in evs if e.get("run_id")})}
```

### 2-2. `twoder/webui.py` — `etrace_view` に分岐を1つ
```python
def etrace_view(run_id, event_id, ★task_id):
    ...
    ★if task_id:
    ★    tt = ETRACE.resolve_task(task_id)
    ★    return {"task_id": task_id, "resolved": tt is not None, "task_trace": tt, "read_only": True}
# GET の行に引数を1つ
            return self._send(etrace_view(q.get("run_id",[""])[0], q.get("event_id",[""])[0], ★q.get("task_id",[""])[0]))
```
```
★応答の形は ★`/api/resolve` と同じ流儀（`resolved` + 本体 + `read_only`）。★整形・要約しない
★★戻し方: ★足した関数1つと分岐1つを消す。★可逆
```

## 3. 受入

```
★(1) ★`GET /api/etrace?task_id=TASK-2DER-E2675F0E` が ★`resolved: true` と ★`events` を返す
     ★`total` と ★`run_ids` を ★逐語で書く（★run_ids が ★2件以上なら「段が散っていた」の実証）
★(2) ★★出た段(phase)を ★全部 列挙する。★`GENERATE`/`AUDIT`/`DISPOSE`/`UPPER_REVIEW` が
     ★出たか出なかったかを ★★そのまま書く（★出なければ「出なかった」と書く。★推測しない）
★(3) ★陰性対照: ★`?task_id=TASK-2DER-NOSUCH` → ★`resolved: false` / ★`task_trace: null`（★空 dict にしない）
★(4) ★既存の `?run_id=` と `?event_id=` が ★従来どおり動く（★1件ずつ叩いて示す）
★(5) ★書いていない（★叩く前後で ★同じ task の `total` が不変）
★(6) ★戻せる ／ ★(7) ★Claude が書いた行数（★2DER の実績に数えない）
★★★★★予告を投入前に書く: ★変更行数 ／ ★(1) の `total` と `run_ids` の件数の見込み
```

## 4. ★先に言う（★これで「2日を説明」に届くとは書かない）

```
★`task_id` を持つのは ★DW だけ ∴ ★本件で まとまるのは ★DW の段である。
★★SUBMIT/DS/RRI/EGL は ★`run_ids` を辿らないと出ない ＝ ★2回 引く必要がある。
★★★∴ ★親 `EVO-0035` の受入『この2日を台帳だけで説明できる』に ★届いたかは ★★本件だけでは決まらない。
★★★★受入(2) の結果を見てから ★MGR が判定すること（★私は「届く」と書かない）。
```

## 5. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/etrace?task_id=`（★受入(1)）／2 書く口＝★既存の `emit`。★足さない
3 理由を捨てない＝★`run_ids` を返す（★「DW しか無い」を隠さない）
4 作っていないのでは＝★`task_id` 欄は ★既に在る（`etrace.py:110`）。★無いのは ★引く関数だけ
5 走ったか＝★受入(1)(2) は ★実在の task で測る／6 名前＝★`task_id`（★既存欄。★改名しない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし／8 計器＝★受入(5) で total 不変
★9 増える代わりに廃止＝★★`EVO-0041` で保留した「Claude が git log を漁る運用」の ★再判定材料になる。
   ★★但し ★§4 のとおり ★本件だけでは畳めない。★★畳むと書かない
```

## 6. 禁止
```
★新しい台帳・新しい記録・新しい `emit` を作る ／ ★`resolve_run` / `resolve_event` の戻りを変える
★見つからない時に空 dict を返す ／ ★`MAX_EVENTS` を変える ／ ★整形・要約・切り詰め
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
