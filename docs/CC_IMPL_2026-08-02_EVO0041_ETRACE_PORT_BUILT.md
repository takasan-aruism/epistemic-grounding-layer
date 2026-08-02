# 【実測 / `EVO-0041`】**実行の痕跡が front door から読めた** — `ETR-a91cb47c2e22` は 5 event

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 15:0x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0041_BUILD_SPEC_ETRACE_PORT.md` ／ 親 `ITEM-2DER-EVO-0035`

---

# 1. 変更（★Claude が書いた分。2DER の実績に数えない）

```
twoder/webui.py のみ ★+13 / -0（etrace_view 11行[docstring 2行含む] ＋ GET の分岐 2行）
ds/ds/etrace.py は 0行（触っていない）。POST は作っていない。MAX_EVENTS も変えていない。
resolve_run の戻りは そのまま載せた（整形・要約・切り詰めなし）。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | `?run_id=ETR-a91cb47c2e22` が `resolved: true` と `events` | **○** | **`count: 5` / `total: 5` / `truncated: false`**・応答 4,173字（5,511 bytes） |
| (2) | 今日の作業と突き合う | **○** | ENTRY の `raw_input` に **`impl.render`** が在る（§3 逐語） |
| (3) | 陰性対照 | **○** | `{"run_id": "ETR-000000000000", "resolved": false, "trace": null, "read_only": true}` / http=200。**空 dict でも 500 でもない** |
| (4) | `?event_id=` で1件 | **○** | `ETR-a91cb47c2e22-0001` → `resolved: true` / `function: ENTRY` / `run_id: ETR-a91cb47c2e22` |
| (5) | 書いていない（total 不変） | **○** | 連続で叩いて **total = 5 / 5** |
| (6) | 戻せる | **○** | 手で2箇所を戻した版が `d01b5b3~1` と**バイト一致** |
| (7) | 行数 | **○** | §1（Claude +13 / 2DER 0行） |

# 3. 逐語（受入(2) の実体）

```
"function": "ENTRY", "inputs": "{\"entry\": \"submit()\", \"raw_input\": \"(v10) 2DER の開発状況ページ(GET /)に、
人間が読むための4つを足す関数 impl.render を作ってください。\n本番モジュールを import せず、データは引数で
受け取る純関数にしてください。標準ライブラリのみ。★骨…
```

```
event の欄: event_id / parent_event_id / run_id / trace_id / task_id / ts / component / function /
            inputs / outputs / handed_to / result / error / truncated
```

# 4. 予告の当否（`evo0041_pre.txt`）

| 予告 | 結果 |
|---|---|
| webui.py +10行前後 | **ほぼ当たり**（実測 +13） |
| **total 30〜200件** | **★外れた。実測 5件**（`truncated: false` は当たり） |
| ENTRY に `impl.render` が在る | **当たり** |
| 陰性対照は `resolved:false` / `trace:null` | **当たり** |
| `event_id` で1件 引ける | **当たり** |
| total 不変 | **当たり** |

```
★外れ方の中身: 1回の submit で 段ごとに event が出ると見込んだが、実測は 5件だった。
   ∴ 「どの段を通ったか」を細かく追える粒度ではない。これは口の欠陥ではなく 記録の粒度である。
   ★私はそれを直していない（実装源の範囲外）。
```

# 5. 走行

```
webui 再起動を確認（9項目 #5）: 起動 14:57:30 > webui.py 14:56:54。
走行 0・task 増 0・:8005 を叩いていない・台帳を直読していない・commit していない。
戻し方: ① webui.py の etrace_view を消す ② GET の分岐2行を消す。※ commit 後は `git checkout --` では戻らない。
★9項目 #9 の廃止（Claude が git log と .md を漁って「いつ・何が動いたか」を答える運用）は、
   SPEC の指定どおり ★まだ畳まない（1本 通っただけ・実際に台帳側で答えられた時に畳む）。
```
