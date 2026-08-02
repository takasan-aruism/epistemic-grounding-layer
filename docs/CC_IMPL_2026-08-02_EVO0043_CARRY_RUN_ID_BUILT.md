# 【実測 / `EVO-0043`】**DW の段が痕跡に載った（5 → 7件）／混ざっていない** — ただし **EGL は出ていない**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 20:3x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0043_BUILD_SPEC_CARRY_RUN_ID.md` ／ 親 `ITEM-2DER-EVO-0035`

---

# 1. 変更（★Claude が書いた分。2DER の実績に数えない）

```
twoder/webui.py のみ ★+2 / -0（関数内 import 1行 ＋ set_run_id 1行）。ds/ds/etrace.py は 0行。
/api/ingest には足していない（陰性対照を残すため）。open_run は呼んでいない。_seq(EVO-0044)は触っていない。
```

## 1-1. ★SPEC と1点 違った（投入前に実測・予告に書いた）

```
SPEC §2 逐語:「ETRACE は webui.py:273 で既に import 済み（新しい import を足さない）」
★実測: :273 は ★etrace_view 関数の中の import ∴ handler からは見えない（足さないと NameError）。
∴ 分岐の中に関数内 import を1行 足した（module 先頭には足していない＝起動時の依存を増やさない）。
```

# 2. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | run に DW/EGL の event が出る | **○（DW のみ）** | `816D6F68`: **5件 → 7件**／component = `SUBMIT 1 / DS 1 / RRI 3 / DW 2`。`0E5E8675` も同じ。**EGL は0件**（§3） |
| (2) | 陰性対照: ingest 由来は `ETR-NORUN` | **○** | `?event_id=ETR-NORUN-0001` → `component: DW` / `function: _append_event` / **`run_id: None`** / `task_id: TASK-FLAGOFF` |
| (3) | 混ざっていない | **○** | `816D6F68` の run(`ETR-986a8828c470`) の task_id 内訳 = `{None: 5, TASK-2DER-816D6F68: 2}`／`0E5E8675` の run(`ETR-72359f4207e2`) = `{None: 5, TASK-2DER-0E5E8675: 2}`。**相手の task_id は 0件** |
| (4) | `ETRACE_RUN_ID` が無くても落ちない | **○（但し §4）** | 存在しない `TASK-2DER-NOSUCHTASK` で `run_next` → **http 200・`refused: true`**（500 にならない） |
| (5) | 戻せる | **○** | 手で2行を戻した版が `HEAD` と**バイト一致** |
| (6) | 行数 | **○** | §1（Claude +2 / 2DER 0行） |

# 3. ★EGL が出ていない（「出た」と書かない）

```
予告では DW と EGL の両方が出ると書いたが、★実測は DW だけ（EGL 0件）。
今回 進めた段は どちらの task も ★AUDIT である ∴ EGL を通る段を踏んでいない可能性が高い。
★私はそれ以上 測っていない【未確認】。「EGL も出る」とは書かない。
```

# 4. ★受入(4) は厳密には測れていない

```
`ETRACE_RUN_ID` を持たない task を front door から探したが 見つからなかった
（`TASK-2DER-GPU-SWITCH-001` も `ETR-e814f56897fd` を持っていた）。
∴ 代わりに ★TRACE 自体が無い task_id（存在しない id）で叩き、落ちないことを示した。
「値が None の時に落ちない」ことは ★この経路で示した（`_trace(tid) or {}` が None を吸う）。
```

# 5. 予告の当否（`evo0043_pre.txt`）

| 予告 | 結果 |
|---|---|
| webui.py +2行（関数内 import 込み） | **当たり** |
| SPEC の「import 済み」は誤りで足す必要が在る | **当たり**（§1-1） |
| **件数 20〜60件** | **★外れた。実測 7件**（+2） |
| **component = DW と EGL** | **★半分 外れ**（DW のみ・EGL 0件） |
| 陰性対照は `ETR-NORUN` のまま | **当たり** |
| 混ざらない（相手の task_id 0件） | **当たり** |

```
★件数を大きく見込んだのは EVO-0041 と同じ誤りである（1段で多数の event が出ると考えた）。
   実測では ★1段あたり DW 2件。★粒度はこれだけである。
```

# 6. 走行・戻し方

```
webui 再起動を確認（9項目 #5）: 起動 20:23:50 > webui.py 20:22:03。
task 増 0（既存2 task を再投入して進めた・sha1 一致）／走行は AUDIT 2回（front door 経由で :8005 を使用）。
commit していない。台帳を直読していない。
戻し方: webui.py の run_next 分岐に足した2行を消す。※ commit 後は `git checkout --` では戻らない。
★9項目 #9 の再判定（Claude が git log を漁る運用を畳めるか）は ★まだ畳まない——
   本件で載ったのは DW だけで、EGL は出ていない ∴ 「2日を全部 説明できる」に届いていない。
```
