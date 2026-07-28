# BUILD SPEC — 管理UI に2項目を出す v1.0（★実装源）

- `BUILD_ROLE: ★実装源`（**本文書が実装の唯一の典拠**）
- **★宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-29
- **運用方針 確認済（版: `v2.8` — `§12` を最大版で読んだ値）**
- **正典**: `PHASE2_DIRECTION_MANAGEMENT_UI_v1_0.md`（Taka 逐語） / **発注**: `CC_MGR_2026-07-29_D49_UI_TWO_ITEMS_SPEC_REQUEST.md`
- **前提の実測**: `CC_DESIGN_2026-07-28_D45_UI_MEASURED.md`

---

## 0. ★先に — 受入条件がそのままでは満たせない（実測）
> **MGR 受入:「1件の依頼を UI で開いて6つが1画面で分かること。★本日の `ETR-f0fe8461c407` が使えるはずである」**

```
再現: GET /api/state?task_id=SUBMIT-zzzzzz
  → {"task_id": "SUBMIT-zzzzzz", "error": "no such task"}
根拠: webui.py:107 build_state は DW task が無ければ error を返して抜ける
根拠: webui.py:687 /command の JS は TASK が無ければ
      「現在 runnable な DW task はありません。」だけ出して return する
```
> **★`ETR-f0fe8461c407` は `OBSERVE_CURRENT_STATE` の依頼で、DW task を作っていない**（`task_id=None`）。
> **∴ その依頼は★UI で開けない。** **6項目のうち①が成立しない。**
> **∴ 受入に使うなら、★DW task を作る依頼でなければならない。**

**★これは本 SPEC で直さない。** **理由: 「DW task が無い依頼も開けるようにする」は★新しい口が要る**（MGR 条件2）。
**∴ MGR 条件2 に従い★「足りない」と書いて上げる**（§5）。

---

## 1. ★どちらの画面に足すか（実測で決めた）
```
再現: grep -n "fetch(\"/api" twoder/webui.py
  :651 /api/submit      （/command）
  :682 /api/run_next 等 （/command）
  :688 /api/state       （/command の load()）
  :690 /api/claude_packet（/command・claude_barrier のときだけ）
  :455 /api/approve     （/ の承認ボタン）
```
| 画面 | 性格 | 判定 |
|---|---|---|
| **`/`** | **集計**（ロードマップ・完成予測・直近アクティビティ） | **★足さない** |
| **`/command`** | **★1件の依頼を開く画面**（`/api/state` を叩き、カードを描く） | **★ここに足す** |

**★理由: Taka の完了像は「1件の依頼を開いて6つが分かる」である。** **`/command` がその画面である。**
**★そして `/command` は既に「条件付きで2つ目の口を叩く」形を持っている**（`claude_barrier` のとき `/api/claude_packet`）。**∴ 同じ形を使う。新しい機構を作らない。**

---

## 2. 実装（3箇所だけ）

### 2-1. `twoder/webui.py::build_state` — ★列挙に2キー足す（`G-46` を含む）
```python
# build_state の返り dict に追加（★既存キーを1つも変えない・追加のみ）
"etrace_run_id":      tr.get("ETRACE_RUN_ID"),      # ← G-46（③の前提）
"boundary_failures":  tr.get("boundary_failures"),  # ← ⑤（submit が全段で集めている）
```
- **★`TRACE` に既に在る値を載せるだけ。** **record を1件も増やさない**（MGR 条件3）。
- **★キー名は `submit.py` の記録名に合わせる。** 勝手に改名しない。

### 2-2. `/command` の JS — ★カードを2枚足す
```
③「通過した処理」カード:
   s.etrace_run_id が在れば /api/resolve?id=<etrace_run_id> を1回叩き、
   返った events を  ts / component / function / result  の4列で全件描く。
   ★truncated が true なら「打ち切られた: total N 件中 M 件」と画面に出す（隠さない）。
   ★etrace_run_id が無ければ「この依頼の run_id は記録に無い」と出す（空欄にしない）。

⑤「欠損・失敗・未確認」カード:
   次を1枚にまとめて出す。★どれも既に在るものである（新しい概念を作らない）:
     ・s.boundary_failures      （各 {system, gap}）
     ・s.ds_limitation          （既に出ている。このカードへ移す）
     ・s.guard_block / s.block_source_refs / s.failure_memory_match（既に在る）
   ★1件も無ければ「欠損・失敗の記録なし」と明示する。★空のカードを消さない。
```
- **★新しい endpoint を作らない**（`/api/resolve` は既存）。
- **★`claude_barrier` のときの `/api/claude_packet` と同じ「条件付き2回目の fetch」である。**

### 2-3. ★変えないもの
- **既存の4項目（①②④⑥）のカードを1行も変えない。**
- `/api/state` の**既存キーを1つも変えない・消さない**（追加のみ）。
- **`/` を変えない。** **新しい endpoint を作らない。** **`ids.py` を変えない。**
- **Event Trace の record を増やさない**（`emit` に触らない）。
- **RRI の系（`request_thread`）に触らない**（`G-55`・据え置き）。

---

## 3. 受入
| # | 条件 | 示し方 |
|---|---|---|
| **1** | **★DW task を作る依頼を1件、UI で開いて6項目が1画面で出る** | **★画面の実データを貼る**（各カードの中身） |
| **2** | ③ 通過した処理 | **event 列が全件出る。`truncated` の表示も含む** |
| **3** | ⑤ 欠損・失敗・未確認 | **`boundary_failures` が出る。1件も無ければ「記録なし」と出る** |
| **4** | **既存4項目が壊れていない** | **★実装前後で `/api/state` の既存キーの sha256 が一致**（新キー2つを除いて比較） |
| **5** | 非回帰 | **基準 91 passed / 7 failed。顔ぶれ diff も示す** |
| **6** | **★`ETRACE_RUN_ID` が無い依頼でも画面が壊れない** | **今日の `OBSERVE_CURRENT_STATE` 系で確認する。★「run_id は記録に無い」と出ればよい** |

### 3-1. ★投入について
- **★投入が要る**（DW task を作る依頼が要るため）。**★1回だけ。**
- **★文面は事前に MGR へ出して承認を得ること**（本 SPEC には書かない。**★私が文面を選ぶと、また routing を外す**——本日1度やっている）。
- **★webui を再起動してから**（本日2回踏んだ型）。**`cd /home/takasan` を明示**（v2.5 §4-17）。

---

## 4. ★事前に固定する予測（賭ける所と賭けない所を分ける）
| 項目 | 予測 | 根拠 |
|---|---|---|
| **③ が出るか** | **★出る方に賭ける** | `ETRACE_RUN_ID` は `submit.py:99` で TRACE に載り、`/api/resolve` の `ETR-` 分岐は front door で実測済 |
| **⑤ に `boundary_failures` が出るか** | **★予想しない** | **その依頼で境界失敗が起きるかは、依頼次第である。** 0件でも正常 |
| event の件数 | **★予想しない** | 依頼による |
| **既存4項目が壊れないか** | **★壊れない方に賭ける** | 追加のみで既存キーに触らないため |

---

## 5. ★足りないもの（MGR 条件2 に従い、作らずに上げる）
| # | 足りないもの | なぜ本 SPEC で作らないか |
|---|---|---|
| **1** | **DW task を作らない依頼を UI で開く手段** | **★新しい口が要る**（`build_state` は `webui.py:107` で DW task 前提。ここを変えると①の意味が変わる）。**★裁定事項** |
| **2** | **run_id を直接入れて event 列だけ見る手段** | 同上。**★今日の `ETR-f0fe8461c407` を画面で見るには、これが要る** |
| **3** | **submit ごとの trace（`runs/<key>.trace.json`）を読む口** | **★実測: webui は submit ごとに一意キーの trace も書いている**（`webui.py:541`。`key=(tid or "SUBMIT")+"-"+乱数`）。**∴ 過去分はディスクに残っているが、読む口が無い。** `G-31` の理解を1つ更新する材料 |

**★私は作らない。** **どれも「新しい口」であり、MGR 条件2 に触れる。**

---

## 6. ★止まってよい場所
| # | 条件 |
|---|---|
| 1 | **`etrace_run_id` を足しても `/api/state` に出ない** → **★私の見立てが外れた。報告する** |
| 2 | **既存キーの sha256 が変わった** → **★追加のみのはずが変えている。止めて報告** |
| 3 | **`/api/resolve` の返りが JS で描けない形だった**（event が list でない等）→ **繋げる細工をせず報告** |
| 4 | SPEC が2通りに読める |

## 7. ★未確認（引き継ぐ）
1. **`boundary_failures` が `/api/state` に載ることを、私は実行で確かめていない**（`submit.py` が集めていることと、`build_state` に無いことは実測済）。
2. **`/` 側に③⑤が要るかを判断していない**（Taka の完了像は1件の依頼＝`/command` と読んだ。**★別解釈が在りうる**）。
3. **画面をブラウザで見ていない**（HTML と API の返りから設計した。D-45 から引き継ぎ）。

---
*CC-α D-49 BUILD SPEC v1.0（実装源・宛 IMPL）。★先に受入条件の不成立を実測で示す=`GET /api/state?task_id=SUBMIT-zzzzzz` → `{"error":"no such task"}`（`webui.py:107` は DW task が無ければ error で抜け、`:687` の JS は「現在 runnable な DW task はありません」だけ出して return）∴ **`ETR-f0fe8461c407` は `OBSERVE_CURRENT_STATE` で DW task を作っておらず UI で開けない**ので、受入に使うなら DW task を作る依頼でなければならない——これは新しい口が要るので本 SPEC で直さず「足りない」と上げる。★どちらの画面に足すかは実測で決定=`/` は集計、**`/command` が1件の依頼を開く画面**（`/api/state` を叩きカードを描く）で Taka の完了像に合致し、しかも**既に「条件付きで2つ目の口を叩く」形（`claude_barrier` のときの `/api/claude_packet`）を持つ**ので同じ形を使い新しい機構を作らない。★実装は3箇所=①`build_state` の列挙に `etrace_run_id`(=`G-46`)と `boundary_failures` の2キーを追加（**TRACE に既に在る値を載せるだけで record を1件も増やさない**・キー名は `submit.py` の記録名に合わせる）②`/command` の JS にカードを2枚追加（③は `/api/resolve?id=<etrace_run_id>` を1回叩き `ts/component/function/result` を**全件**描き、`truncated` なら「打ち切られた」と画面に出し、`run_id` が無ければ「記録に無い」と出す＝空欄にしない／⑤は `boundary_failures`・`ds_limitation`・`guard_block`・`block_source_refs`・`failure_memory_match` を1枚にまとめ、**1件も無ければ「記録なし」と明示し空のカードを消さない**）③既存4項目のカード・`/api/state` の既存キー・`/`・`ids.py`・`emit`・RRI の系には触らない。★受入6件（DW task を作る依頼1件で6項目が1画面／event 全件と `truncated` 表示／`boundary_failures`／**既存キーの sha256 が新キー2つを除いて一致**／非回帰 91/7 と顔ぶれ diff／**`ETRACE_RUN_ID` が無い依頼でも画面が壊れない**）。投入は1回だけで、**文面は私が選ばず MGR の承認を得る**（私が選ぶとまた routing を外す——本日1度やっている）。★事前予測=③が出る方と既存が壊れない方に賭け、**⑤の件数と event 件数は予想しない**（依頼次第で0件でも正常）。★足りないもの3件を作らずに上げる=DW task を作らない依頼を開く手段／run_id を直接入れて event 列だけ見る手段（**今日の run を画面で見るにはこれが要る**）／**submit ごとの trace を読む口**——実測で `webui.py:541` は `key=(tid or "SUBMIT")+"-"+乱数` で submit ごとに一意キーの trace も書いており、**過去分はディスクに残っているが読む口が無い**（`G-31` の理解を更新する材料）。★止まってよい場所4件と未確認3件（`boundary_failures` が `/api/state` に載ることは実行未確認／`/` 側に③⑤が要るかは判断していない・別解釈が在りうる／画面をブラウザで見ていない）。*
