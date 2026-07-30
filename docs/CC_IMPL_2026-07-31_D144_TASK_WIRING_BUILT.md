# 【BUILT】D-144 — 観測の経路で Task を作る配線（★task は出来た。★trace から task へ辿れず停止）

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 01:2x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）** ／ **実装源**: `CC_DESIGN_2026-07-31_D144_BUILD_SPEC_TASK_WIRING.md`
- **受領した MGR 文書**: **無し** ／ **★2DER 優先原則の例外**（正典で IMPL が書くと明示）。**★2DER の担当工程に数えない。★1/8 は動かない**
- **`:8005` を使った**（★私は0件。**★投入が 2DER 内部で4件 呼んだ**）

---

# 0. ★止まった（正典の5行）
```
Last PASS   : Task の生成（A-1・A-2）— task_id=TASK-2DER-0C458F38 / resolved=true / events=1 / state=CREATED
              依頼一覧 156 → 157（★+1。2件以上ではない）
First FAIL  : A-3 — 新しい trace_key `TASK-2DER-0C458F38-vhDl1Q` が resolve できない（resolved=false）
原因        : webui.py:661 が trace_key を `(tid or "SUBMIT") + "-" + 乱数` で作る。★task が出来た途端に
              prefix が `SUBMIT-` から外れ、D-140 で足した `SUBMIT-` 分岐に載らない。★さらに `TASK-` 分岐へ
              入り、その合成 id には event が無いので None になる。★D-144 が D-140 の前提を外した形である
修正内容    : `twoder/submit.py` ★1箇所のみ（13挿入・1削除／`gpu`・`nvidia` は diff に0件）。
              ★A-3 の修正は submit.py の外（webui.py か ids.py）になるため、★SPEC §6 に従い実施していない
次回確認箇所: 新形式の trace_key（`TASK-…-<乱数>`）を既存 resolve で解けるようにする ★1件（★どちらのファイルを
              直すかは設計判断。★私は決めない）
```

---

# 1. ★受入（★1条件に1つの印）

| # | 受入 | 印 | 示し方 |
|---|---|---|---|
| **A-1** | task が1件 作られる | **○** | 応答 `task_id = TASK-2DER-0C458F38`（第2試行は `null`） |
| **A-2** | その task が引ける | **○** | `/api/resolve?id=TASK-2DER-0C458F38` → `resolved=true` / `events=1` / `state=CREATED` |
| **A-3** | **trace から task へ辿れる** | **★×** | `/api/resolve?id=TASK-2DER-0C458F38-vhDl1Q` → **`resolved=false`**（`dw_task_ref` 以前に record が無い） |
| **A-4** | **task から観測へ辿れる** | **○（★口を選ぶ必要が在る）** | **`/api/state?task_id=` の `egl.source_refs` → `OBS-00963`〜`00966`**、**`OBS` record 経由で `ARUN-00962`〜`00965` へ1段**。**★ただし `/api/resolve?id=<task_id>` 自体は3キーのみで観測へ届かない** |
| **B-1** | GPU 固有を書いていない | **○** | diff 全体を大文字小文字無視で走査 → **`gpu`／`nvidia` は0件**（打ち切り無し） |
| **B-2** | 1箇所だけ | **○** | **変更は `twoder/submit.py` のみ／hunk は `@@ -377 +377,13 @@` の1つ／13挿入・1削除** |
| **C-1** | 後方互換（既存 ID 10件） | **○** | **全10件 不変**（`resolved` も record キー数も。`SUBMIT-zOlryQ` 14 / `SUBMIT-_ayfew` 14 も不変） |
| **C-2** | 後方互換（既存経路） | **○** | diff の hunk は 377行の1つのみ。**`BUILD_CAPABILITY`/`MODIFY_EXISTING` 経路（433行以降）に diff 無し**（★投入して確かめていない・diff で示した） |
| **D-1** | 再利用できることを GPU 以外の1語で示す | **○** | **`listening_ports`**（Network）が **同じ `_CATALOG`**（`runtime_inspection.py:28-34`）に在り、**`build_request` が `list(_CATALOG.keys())` で同じ `inspect()` 経路に載せている**（46行）。**★実装も実行もしていない** |

---

# 2. 接続できた配線 / まだ切れている配線

**★接続できた**
```
submit（観測の経路） → DW task           TASK-2DER-0C458F38（CREATE 1件・state=CREATED・dev-workcell/events.jsonl に記録）
task → 観測                              /api/state の egl.source_refs → OBS-00963〜00966 → ARUN-00962〜00965
```
**★まだ切れている**
```
trace_key → task        ★A-3。新形式 `TASK-…-<乱数>` が resolve できない（★今回の First FAIL）
resolve(task) → 観測    ★`/api/resolve?id=<task_id>` は task_id/events/state の3キーのみ。★観測へは /api/state が要る
RRI の record ID        ★TRACE に無いまま（判定値のみ）。★今回の対象外
```

---

# 3. ★先に言われていた副作用（観測して記録する・直さない）
| | 前（第2試行） | 後（今回） |
|---|---|---|
| 依頼一覧 | 156 | **157（★+1。★2件以上ではない）** |
| 応答の `runnable` | `false` | **★`true`**（★RUN NEXT が押せる状態になった。**★私は押していない**） |
| `webui` が書く trace | `runs/<trace_key>.trace.json` のみ | **★`runs/<task_id>.trace.json` も書くようになった**（`webui.py:663-664`・既存の分岐） |
| task の状態 | — | **CREATED（PLAN 待ち）のまま残る** |

**★注意（読み違え防止に1行だけ）**: `/api/state` の `egl.current_claims` に「GPU使用率: 両GPUとも約0.92 (92%)」という文が出るが、**★これは `DE-0072`/`DE-0170`/`DE-0171` 由来の claim であって今回の実測ではない。★実測に GPU 使用率は無い（変わらず取得不能）。**

---

# 4. ★Runtime Inspection は他の監視項目へ再利用できる状態か
> **★共通入口としては載っている。★ただし選別は効いていない。**
> `_CATALOG` は4種（`gpu_memory` / `running_containers` / `top_memory_processes` / `listening_ports`）で **GPU 専用ではなく**、今回作った Task の配線も **GPU 固有語を1つも含まない**（B-1）。
> **★`build_request` が `list(_CATALOG.keys())` で毎回 全件を要求する**（`runtime_inspection.py:46`）＝**★依頼内容による選別は働いていない。★今回 直していない**（設計の調査 #4 のとおり記録のみ）。

---

# 5. ★人・Claude が行った操作（★全件）
| 区分 | 操作 | 時刻 |
|---|---|---|
| 実装 | `twoder/submit.py` 1箇所（13挿入・1削除） | 01:0x |
| 運用操作 | **webui 再起動**（旧 PID 3923096 → 新 PID 3932995 / 01:08:41）。**操作者=IMPL／理由=`submit.py` の変更を本番へ反映／既存運用（引き継ぎ §4-1）／★2DER の担当に数えない／★run-gate は初期化された**（今回は投入で立て直るため結果に影響なし） | 01:08 |
| テスト | C-1（基準値10件）／A-1〜A-4／B-1・B-2・C-2・D-1 | 01:08〜01:12 |
| 開始操作 | **`POST /api/submit` ★1回**（sha1 `0c458f38…`・54字・第1/第2試行と一致） | 01:09:04 |
| していないこと | **★`run_next` を押していない**（SPEC §4 の指示どおり。★今回の対象は Task の生成まで）／★GPU を自分で測っていない／★コマンドを選んでいない／★再投入していない／★止まった所を直していない・迂回していない／**★commit していない** | |

**受理の確認**: receipt `last_recv_at = 2026-07-31T01:09:04.434285`（★私の POST `01:09:04.429024` の直後）／`recv_count 72→73`。

---
*IMPL → 設計/監査（写: MGR / Taka）。D-144 の配線。**修正は `twoder/submit.py` 1箇所のみ（13挿入1削除・`gpu`/`nvidia` は diff に0件・既存 `create_task` を流用し id の採り方も BUILD 経路と同じ sha1 方式＝新しい生成方式なし）。** 受入は **A-1○（`task_id=TASK-2DER-0C458F38`）／A-2○（`resolved=true`・`events=1`・`CREATED`）／★A-3×（新 trace_key `TASK-2DER-0C458F38-vhDl1Q` が `resolved=false`）／A-4○（`/api/state` の `egl.source_refs`→`OBS-00963〜66`→`ARUN-00962〜65`、ただし `resolve(task)` 自体は3キーで届かない）／B-1○／B-2○／C-1○（基準値10件 全件不変）／C-2○／D-1○（`listening_ports` が同じ `_CATALOG`・同じ経路）**。**First FAIL の原因は `webui.py:661` の `(tid or "SUBMIT")`——task が出来ると trace_key の prefix が `SUBMIT-` から外れ、D-140 で足した分岐に載らず、`TASK-` 分岐では event が無く None になる＝D-144 が D-140 の前提を外した形。** 修正は `submit.py` の外（`webui.py` か `ids.py`）になるため **SPEC §6 に従い実施していない**。副作用は記録どおり **依頼一覧 156→157（+1）・`runnable` が false→true（RUN NEXT が押せる状態／★押していない）・`runs/<task_id>.trace.json` も書かれるようになった・task は CREATED のまま残る**。**Runtime Inspection は共通入口としては載っている（`listening_ports` など4種・GPU 固有語なし）が、`build_request` の全件要求により選別は効いていない（今回 直していない）。** 次回確認箇所は**新形式 trace_key を既存 resolve で解けるようにする1件**（どのファイルを直すかは設計判断）。**★`/api/state` の `current_claims` に出る「GPU使用率 92%」は `DE-0072`/`0170`/`0171` 由来の claim であって今回の実測ではない（実測に使用率は無い）。***
