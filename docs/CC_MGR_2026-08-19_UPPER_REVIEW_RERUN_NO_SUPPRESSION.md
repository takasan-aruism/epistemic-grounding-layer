# 宛: Taka / 設計 / 監査 ―― **同一 TASK へ `claude -p` が 29回**: 構造原因は「進展を止める条件が無い」

**Taka 裁定(あ)により `twoder-manager.service` を停止した（★資源保護であって TASK の合否判定ではない）。**
**修正していない。`apply_unified_diff` の試験失敗にも `patch_bridge` にも戻っていない。**

## 0. 停止前の記録（★Taka 指定の値・すべて正規面）

```
task_id             = TASK-2DER-32EDB6C4
state               = JUDGE_REQUIRED
last_test_passed    = False
generate count      = 1
regenerate count    = 1
rework_count        = 1
upper_reviews count = ★29
最初の upper_review = 2026-08-19T07:58:55
最後の upper_review = 2026-08-19T08:13:46
queue               = []（★記録時） ／ last_task = TASK-2DER-32EDB6C4
```

**停止後: `ActiveState=inactive` ／ `MainPID=0`。**

## 1. ★決定的な観測 ―― 29回は「3つの分」に固まっている

```
2026-08-19T07:58 … ★ 5 回
2026-08-19T08:05 … ★12 回
2026-08-19T08:13 … ★12 回
```

**★1分に12回＝1回の巡回の中で12回呼んでいる**（★毎分1回ずつ呼んでいたのではない）。

## 2. ★構造原因（★1つ・正本から確定）

**`dev-workcell/dw/dispatch.py::run_until_barrier`（174-185行）逐語:**

```python
def run_until_barrier(task_id, actors, ts, ★max_ops=12):
    """Loop dispatch_once until a Claude/human barrier, COMPLETE, or BLOCKED. …
       THIS is the outer loop — deterministic Python over persisted state, NOT Claude."""
    for _ in range(max_ops):
        step = dispatch_once(task_id, actors, ts)
        …
        if not step["dispatched"]:
            break
```

**★止まる条件は `dispatched` が偽の時だけ ―― ★『状態が進んだか』を見ていない。**

```
JUDGE_REQUIRED → _MAP は ('UPPER_REVIEW','CLAUDE_SENIOR',…,★claude_barrier=False)
   ＝★barrier では ない ∴ dispatch は 毎回 ★成功する（dispatched=True）
   → CLAUDE_SENIOR actor = `claude -p` が 走り record_upper_review を 書く
   → ★state は JUDGE_REQUIRED の まま（★試験が 通っていない ため 進めない）
   → ★ループの 停止条件に 当たらない
   → ★★max_ops=12 まで 呼び続ける
★★12 と 実測の 12 が 一致する。
```

## 3. ★四問への回答

### ① `JUDGE_REQUIRED → UPPER_REVIEW` を dispatch 可能とする既存条件

```
`_MAP["JUDGE_REQUIRED"] = ("UPPER_REVIEW","CLAUDE_SENIOR","TASK+RUNS+TEST_RESULT", ★False)`
＋ `dispatch.py:155` の trivially_clean 自動PASS を 通らなかった 場合
→ ★163行の barrier に 落ちない（★claude_barrier=False かつ fn が 在る）
→ ★168行の 機械 dispatch で CLAUDE_SENIOR が 呼ばれる
```

### ② `record_upper_review` 後に同じ state へ留まる条件

```
★試験が 通っていない 時（`last_test_passed=False`）。
★根拠: `/api/ingest` 側にも 同じ 不変条件が 書かれている（webui.py:637 逐語）
   「PASS と 書いて 止まる 状態を 作らない」＝ PASS but last_test_passed is false は ★拒否。
∴ ★上級監査を 何回 実施しても ★試験が 通るまで JUDGE_REQUIRED から 出られない。
```

### ③ 同一 state / 同一 evidence / 同一 artifact への再 dispatch を抑止する既存機構

**★無い。**

```
探した範囲（★すべて実物を読んだ）:
   `run_until_barrier`   … 停止条件は `dispatched` が偽の時だけ（★進展を見ない）
   `dispatch_once`       … DISPOSE / PLAN / UPPER_REVIEW の 各分岐に 実施済み判定が 無い
   `upper_review_gate`   … trivially_clean の 自動PASS だけ（★再実行の 抑止では ない）
   `senior_review`       … 呼ばれたら 必ず `claude -p` を 起動する（★前回の 結果を 見ない）
★`fingerprint` / `input_hash` に 相当する 突き合わせは ★どこにも 無い
```

### ④ rework 上限と upper_review 再実行上限は別管理か

```
★rework は 管理されている … `view["rework_count"]`（★実測=1）
★upper_review の 再実行は ★管理されていない … ★上限も カウンタも 無い
   ＝★★別管理どころか ★★片方が 存在しない
★実測が それを 示す: rework_count=1 ／ generate=1 ／ regenerate=1 に対し ★upper_reviews=29
```

## 4. ★判定 = **B（再実行抑止そのものが存在しない）**

```
★A（在るが未接続）では ない ―― ★探した範囲に 抑止の 部品が 1つも 無い
★C（判定不能）でも ない  ―― ★正本の 12 と 実測の 12 が 一致し ★因果が 閉じている
```

## 5. ★設計へ上げる「不足している最小の状態/鍵」（★MGR は設計しない）

```
★不足しているのは ★『同じ物を もう一度 出したか』を 言える 1つの 鍵。
★材料は ★既に 記録に 在る（★新しい 台帳は 要らない）:
     state ／ last_test_passed ／ 最新 generate/regenerate の 番号
     ／ `_latest_findings` の 内容 ／ artifact の sha
★★前例が 同じ repo に 在る:
     `route_adopt` の 採用行 … `input_hash` / `prompt_version` / `vote_run_id` を 持つ
     `patch_bridge`         … `fingerprint` で 同一物を 判定する
     `_append_index`        … `task_id` で 重複を 弾く
★★∴「前と同じ入力なら 呼ばない」は ★2DER が 既に 3箇所で やっている 作法。
   ★UPPER_REVIEW にだけ 無い。
```

## 6. ★もう一つの事実（★これが 29回で 止まった 理由）

```
★最後の呼び出しは 08:13:46。★以後 4時間 増えていない（★私が 12:20 に 確認）。
★理由は ★抑止が 働いたからでは なく ―― ★★task が queue から 落ち、
  ★自己修復が 拾わなかった から（★試験が 通っていない ∴ 受領されず、
  ★`_last_task()` は 呼ばれた 時だけ 動く）。
★★∴ 止まったのは ★偶然に 近い。★同じ形は ★いつでも 再発する。
```

## 7. ★開示（★隠さない）

```
★記録取得のため `_last_task()` を 呼んだ ―― ★副作用で queue へ 1件 戻った。
   ★呼んだ 時点では service は まだ 動いていた ∴ ★理論上 もう1巡回 走り得た。
   ★実測では upper_reviews は 29 の まま 増えていない。
   ★その後 直ちに service を 停止した（★現在 inactive）。
★停止後は ★コードを 書いていない ／ queue を 編集していない ／ run_next 0 ／ 再投入 0。
```

## 8. していないこと

```
★修正 0 ／ 実装 0 ／ 新台帳 0 ／ 新 ID 0
★apply_unified_diff の 試験失敗を 直していない ／ patch_bridge に 戻っていない
★service を 再開していない
```
