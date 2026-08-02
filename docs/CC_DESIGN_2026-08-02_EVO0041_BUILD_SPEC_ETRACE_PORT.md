# 【BUILD SPEC】`EVO-0041` — **★口を1本 足すだけ（`GET /api/etrace`）。★記録は既に毎回 書かれている**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 14:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§5）** ／ **★3値 確認済（★§1）** ／ 親: `ITEM-2DER-EVO-0035`
- **★裁定の在り処**: `ITEM-2DER-EVO-0041` の `status_note`（逐語:「★GET /api/etrace?run_id=… を★1本 足すだけ」「★完了条件=…実際の run_id で中身が返り、それが今日の作業の1つと突き合わせられること」）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★3値

| 問い | 3値 | ★逐語・実測 |
|---|---|---|
| 実行の痕跡は在るか | **★在る** | `submit.py:99-101` が **どの入口からでも** `ETRACE.open_run` を通す（逐語「★入口ごとの注意書きで防がず、どの入口から入っても必ず通るここに置く」）／`/api/state` から実物が引けた: **`ETR-a91cb47c2e22`**(A64D0C6D) `ETR-d0e422e71593`(112D3FA7) `ETR-7e5a1f08055e`(DE042DE9) |
| 読む関数は在るか | **★在る** | `ds/ds/etrace.py:160 resolve_run` / `:170 resolve_event`。★`_read_all` 逐語「**読み取り専用。ファイルを "r" でしか開かない**」／**見つからなければ `None`**（★空 dict を返さない＝**陰性対照は既に満たされている**） |
| front door の口は在るか | **★無い** | `webui.py` に `/api/etrace` が無い（★調査1 で `LEDGER_REGISTRY` 参照0件と同型） |

```
★★∴ ★作るのは ★口1本だけ。★記録も読み関数も ★★既に在る（★9項目 #4）。
```

## 2. やること（★1箇所・★`/api/resolve` と同じ流儀）

```python
# webui.py — ★`/api/resolve` の隣（:667 付近）に1分岐
        if u.path == "/api/etrace":                    # EVO-0041: 実行の痕跡を読む(読み取り専用)
            return self._send(etrace_view(q.get("run_id", [""])[0], q.get("event_id", [""])[0]))

# 関数は resolve_view と同じ形（★新しい応答の形を作らない）
def etrace_view(run_id, event_id):
    from ds import etrace as ETRACE          # ★submit.py:99 と同じ import（同一プロセスで実績あり）
    if event_id:
        ev = ETRACE.resolve_event(event_id)
        return {"event_id": event_id, "resolved": ev is not None, "event": ev, "read_only": True}
    tr = ETRACE.resolve_run(run_id) if run_id else None
    return {"run_id": run_id, "resolved": tr is not None, "trace": tr, "read_only": True}
```
```
★`resolve_run` の戻りは ★そのまま載せる（`events` / `count` / `total` / `truncated`・★`MAX_EVENTS=500`）
★★★中身を作らない・整形しない・要約しない（★`reason` を捨てた本日の事故と同型を避ける）
★★戻し方: ★足した2箇所を消す。★可逆
```

## 3. 受入

```
★(1) ★`GET /api/etrace?run_id=ETR-a91cb47c2e22` が ★`resolved: true` と ★`events` を返す
     ★`count` / `total` / `truncated` を ★逐語で書く
★(2) ★★今日の作業と突き合う: ★上記 run は ★`TASK-2DER-A64D0C6D`(S-3 の成功走行)のもの
     ★★`ENTRY` の `raw_input` に ★`impl.render` が在ることを ★逐語で確かめる
     ★★★これが「★接続され実行痕跡が出た」の実体（★モジュールが在るだけは BUILT 止まり）
★(3) ★★陰性対照: ★`?run_id=ETR-000000000000`(存在しない) → ★`resolved: false` かつ ★`trace: null`
     ★★空 dict を返さない・★500 にしない
★(4) ★`?event_id=` でも1件 引ける（★(1) の `events[0].event_id` を使う）
★(5) ★★書いていないこと: ★叩く前後で ★同じ run の `total` が ★変わらない
★(6) ★戻せる ／ ★(7) ★Claude が書いた行数（★2DER の実績に数えない）
★★★★★予告を投入前に書く: ★変更行数 ／ ★(1) の `total` の見込み
```

## 4. ★先に言う（★実装が踏みうるもの）

```
★① ★`event_trace.jsonl` は ★`ds/.gitignore` 配下（`etrace.py:13` 逐語）∴ ★消えていれば ★`total: 0`。
   ★★その時は「★0 件だった」と書く（★口が壊れていると書かない）
★② ★応答が大きくなりうる（★1 run 最大 500 event）∴ ★字数を測って書く
★③ ★`from ds import etrace` が webui のプロセスで通るかは ★submit.py が同じ import を
   ★同一プロセスで使っている ∴ ★通る見込み。★通らなければ ★★import を書き換えず ★そのまま報告すること
```

## 5. ★9項目（私の分）
```
1 置いたなら読めるか＝★`GET /api/etrace`（★受入(1)）／2 書く口＝★既に在る（`emit`）★足さない
3 理由を捨てない＝★`resolve_run` の戻りを ★そのまま載せる（★整形しない）
4 作っていないのでは＝★★記録も読み関数も ★既に在る。★口だけ無い
5 走ったか＝★★受入(2) がまさにそれ（★実際の run で中身が出るまで）
6 名前＝★`run_id` / `event_id`（★`etrace.py` の既存の欄名。★改名しない）
7 依頼と試験の矛盾＝★成果物を作らない ∴ 該当なし
8 計器が自分を数えないか＝★★叩いた瞬間の run は数えない（★受入(5) で total 不変を見る）
★9 増える代わりに廃止＝★★「Claude が git log と .md を漁って『いつ・何が動いたか』を答える運用」
   ★★★但し ★1本 通っただけでは畳まない——★受入(2) が通り、★実際に台帳側で答えられた時に畳む
```

## 6. 禁止
```
★新しい台帳・新しい記録・新しい `emit` を足す ／ ★POST を作る（★読み取り専用）
★`resolve_run` の戻りを整形・要約・切り詰める ／ ★`MAX_EVENTS` を変える
★見つからない時に ★空 dict を返す（★「無い」と「空」を混ぜない）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
