# 【BUILD SPEC】`EVO-0043` — **★混ざらないことを先に測った。★呼ぶのは既存の `set_run_id` 1本**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 20:2x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§5）** ／ **★3値 確認済（★§1）** ／ 親: `ITEM-2DER-EVO-0035`
- **★裁定の在り処**: `ITEM-2DER-EVO-0043` の `status_note`（逐語:「★実装の前に必ず測ること=thread-local の寿命で ★別 task の run と混ざらないか(混ざるなら実装を止めて報告する)」）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★★MGR が指定した「先に測る」件 — **★混ざらない**

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| 別 task の run と**混ざるか** | **★混ざらない** | `webui.py:13` 逐語 `from http.server import BaseHTTPRequestHandler, ★ThreadingHTTPServer` ／ `:1139` 逐語 `★ThreadingHTTPServer((bind, port), H).serve_forever()` ＝ **★リクエストごとに新しいスレッド**。`etrace.py:29` 逐語 `_LOCAL = ★threading.local()` ∴ **★各リクエストの開始時点で `run_id` は空**。前のリクエストの値は**引き継がれない** |
| 繋ぐ材料は在るか | **★在る** | `set_run_id`（`etrace.py:73`・**呼び手0件**）／`_trace(tid)` の `ETRACE_RUN_ID`（`webui.py:94-96`・`/api/state` で実物を3件 確認済） |
| いま何が起きているか | **★書かれてはいる** | front door 実測: `?event_id=ETR-NORUN-0001` → **DW/`_append_event`**、`-0050` → **EGL/`append_event`**、いずれも **`run_id: None`** |

```
★★∴ ★実装を止める条件（★混ざる）には ★当たらない。★進めてよい。
★★★★但し ★これは「★スレッドが使い回されない」ことに依っている。★実装は ★受入(4) で ★実際に確かめること
   （★ソースに在る≠動く）。
```

## 2. やること（★1箇所・★1行）

```python
# webui.py:776 の直後（★run-gate の判定より前でも後でもよいが、★dispatch より前）
            if u.path in ("/api/run_next", "/api/run_until_barrier"):
                ★ETRACE.set_run_id((_trace(tid) or {}).get("ETRACE_RUN_ID"))   # EVO-0043: 同じ run に繋ぐ
```
```
★`ETRACE` は ★`webui.py:273` で ★既に import 済み（★新しい import を足さない）
★`ETRACE_RUN_ID` が ★無ければ `None` が入り、★従来どおり `ETR-NORUN` へ落ちる（★悪化させない＝裁定の逐語）
★★★`etrace.py:73-77` 逐語: `set_run_id` は ★`_LOCAL.run_id` と `_LOCAL.stack` を置くだけ。★新しい run を始めない
★★戻し方: ★この1行を消す。★可逆
```

## 3. ★陰性対照（★裁定の指定・★効いているのが この1本だと言えるように）

```
★`/api/ingest`（★Claude が PLAN / DISPOSE / UPPER_REVIEW を書く口）には ★★足さない。
★★∴ ★ingest 由来の DW の event は ★`ETR-NORUN` のままであること を確かめる。
★★★これが「★この1本が効いている」の対照になる（★両方 直すと ★どちらが効いたか言えない）
```

## 4. 受入

```
★(1) ★1回の投入 → ★`run_next` を1回 → ★`GET /api/etrace?run_id=<その run>` に
     ★★`component: "DW"` または `"EGL"` の event が ★出る（★出た component を ★全部 書く）
     ★★★前後の件数を書く（★繋ぐ前は 5件だった＝本日の実測）
★(2) ★★陰性対照: ★`/api/ingest` 経由で進めた分の event は ★`ETR-NORUN` のまま
     ★★`?event_id=ETR-NORUN-…` で ★1件 引いて示す
★(3) ★★★混ざっていないこと: ★2つの task を ★交互に進め、★それぞれの run に ★相手の task_id の event が
     ★1件も無い（★`event.task_id` で照合する）——★★これが §1 の「実際に確かめる」
★(4) ★`ETRACE_RUN_ID` が無い task で ★`run_next` しても ★落ちない（★`ETR-NORUN` へ行くだけ）
★(5) ★戻せる ／ ★(6) ★Claude が書いた行数（★2DER の実績に数えない）
★★★★★予告を投入前に書く: ★変更行数 ／ ★(1) で増える件数の見込み ／ ★出ると思う component
```

## 5. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/etrace`（★EVO-0041 で通した口をそのまま使う）
2 書く口＝★既に在る（`emit`）。★足さない
3 理由を捨てない＝★`ETRACE_RUN_ID` が無い時に ★黙って成功にしない（★`ETR-NORUN` に落ちたと分かる）
4 作っていないのでは＝★★`set_run_id` は ★最初から在る。★呼び手が0件なだけ
5 走ったか＝★★受入(1)(3) がそれ（★実際に2 task 動かして確かめる）
6 名前＝★`ETRACE_RUN_ID` / `set_run_id`（★既存の名前。★改名しない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし
★8 計器が自分を数えないか＝★★`/api/etrace` を叩く行為は ★event を増やさない（★EVO-0041 の受入(5) で total 不変を確認済）
★9 増える代わりに廃止＝★★`EVO-0041` で ★保留した「Claude が git log を漁る運用」を ★★再判定する。
   ★★★但し ★本件が通っても ★前半+DW/EGL が出るだけ ∴ ★★「2日を全部 説明できる」に届いたかは ★別に測ること
```

## 6. 禁止
```
★`/api/ingest` にも足す（★陰性対照が消える）／ ★`etrace.py` を書き換える（★呼ぶだけ）
★`open_run` を後続で呼ぶ（★新しい run が立ち ★1回の投入が2つに割れる）
★`_seq` の重複（`EVO-0044`）を ★ついでに直す（★1件のために2件 直さない・★後回し済み）
★新しい台帳・エンドポイント・状態語を作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
