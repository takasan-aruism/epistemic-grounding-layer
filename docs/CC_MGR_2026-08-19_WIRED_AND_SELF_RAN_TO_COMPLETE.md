# 宛: Taka / 設計 / 監査 ―― **配線1箇所で自走が繋がり、2件が COMPLETE へ到達**

**Claude は queue へ手で追加していない（★1点の例外は §5 に開示）。`run_next` 0。UPPER_REVIEW 代行 0。**

## 0. 結論

```
★★完了条件（本線呼び手が 1以上に なり、実走で 1件 再取得・前進）= ★★成立
★★実際には 想定を 超えた:
   ・常駐が ★3件を 自力で 再取得（2591EF9D → 6AC3EA20 → 4E2A58F2）
   ・★2件が ★COMPLETE まで 到達
   ・うち 1件は ★headless claude（identity="claude-senior"）が UPPER_REVIEW を 実施
```

## 1. 実走（★常駐 pid 1546391・★1分ごと・★私は触っていない）

```
0分  queue [2591EF9D]  ／ 6AC3EA20 READY_FOR_UPPER_REVIEW ur[]
                        ／ 2591EF9D READY_FOR_UPPER_REVIEW ur[2der-auto-upper-review]
3分  ★2591EF9D = ★COMPLETE
6分  queue [★6AC3EA20]                      ← ★★常駐が 自力で 次を 拾った
7分  ★6AC3EA20 ur = [★"claude-senior"]      ← ★★headless claude -p が UPPER_REVIEW を 実施
9分  ★6AC3EA20 = ★COMPLETE
12分 queue [★4E2A58F2]                      ← ★★さらに 次を 自力で 拾った
15分 queue []                               ← 一巡 終わり
```

**★7分の `claude-senior` が決定的**: `senior_review.py` の `subprocess(['claude','-p',…])` が
**人の操作なしで走り、`W.record_upper_review(..., "claude-senior")` を書き、state が前進した。**
**★Taka も 対話型 MGR も この経路に居ない。**

## 2. 直した物（★足場1箇所・★判断は1行も書いていない）

```python
from twoder.requeue_decision import requeue_decision as _RQ   # ★2DER が 契約経路で 書いた 部品
from twoder.domain_dw import DONE_INDEX                        # ★定数の 出所を 正した(遅延 import)
...
r = _use("requeue_decision", _RQ, tid, _s.get("next_operation"), tid in q, tid in done)
if not r["requeue"]:
    continue
_queue_add(tid); return tid
```

**変更していない物**: `_machine_turn`（143行の呼び出しも）／ `done`・`received` の意味 ／ queue ／ FIFO ／ DW `_MAP` ／ `receive_finished`。

## 3. ★訂正 ―― 第一原因は私の前回の診断と違った

```
★前回の 私の 結論 =「③ `tid in done` が 原因」→ ★★誤り。

★実測: 定数 `DONE_INDEX` は `_last_task()` の 154行で 使われているのに
   ★`manager_v0` に 定義も import も 無い（★定義は `domain_dw` のみ）
   → ★毎回 NameError → `except Exception: pass` で 握り潰され
   → ★★自己修復は ★一度も 動いていなかった。

★`tid in done` の 混同は ★実在の 欠陥だが ★そこまで 実行が 届いていなかった
   ＝★★『コードに 在る ≠ 動く』の 型（★今夜 何度も 出た）。
★★私は「除外条件を 消去法で 潰した」と 報告したが、
   ★★そもそも ループが 動いていない 可能性を 潰していなかった。
```

## 4. ★数（★正規面から）

```
★2591EF9D: PLAN→GENERATE→TEST→AUDIT(所見0)→UPPER_REVIEW(★機械 auto-pass)→★COMPLETE
           ＝★★Claude を 一度も 使わず COMPLETE（★今夜 初）
★6AC3EA20: …→AUDIT(所見3)→DISPOSE(★Claude ブートストラップ 1回)
           →UPPER_REVIEW(★headless claude-senior)→★COMPLETE
★4E2A58F2: ★常駐が 拾った（★観測の 範囲では ここまで）
```

## 5. ★開示（★隠さない）

```
① ★私が `_last_task()` を 1回 呼んだ（★接続の 動作確認）。
   ★その 副作用で queue へ 1件 入った（★機械自身の 関数だが ★呼んだのは 私）。
   ★以後は 触っていない。★6分・12分の 再取得は ★常駐が 自力で した もの。
② ★常駐を 再起動した（pid 926888 → ★1546391）。
   ★旧プロセスは 2026-08-17 起動＝★古いコードを 保持していた（★ソースに在る≠動く）。
③ ★commit メッセージの バッククォートが シェルに 解釈され 1語（定数名）が 欠けた（346f074）。
   ★amend は push 済み履歴の 書き換えに なるので ★戻した。★全文は この文書に 残す。
```

## 6. ★次の課題（★Taka の指摘どおり）

```
★今夜 4回 出た 型:
   機械は ★作る・試す・置く・commit する まで できる ／ ★★配線だけ できない
★今回 私が 書いたのは ★その 専用能力が 無い ための ★代役 1回分。
★Taka 逐語の 方向:
 「将来的には もっと 狭く、★正本で 許可された 接続点に、★検証済み部品を 1本だけ 配線する
   ★専用能力 として 作る 方が 2DER らしい」
★★これは ★B（自由な 既存ファイル 書き換え）とは 別物 ―― ★接続点を 正本が 先に 許可する 形。
★★未着手（★今回は 触らない）: tasks_to_enqueue / dispose_decision の 配線。
```

## 7. していないこと

```
★判断ロジック 0行 ／ 新しい 状態・判断規則・queue 0
★run_next 0 ／ UPPER_REVIEW 代行 0 ／ DISPOSE 代行 0（★ブートストラップ 1回は 別記録済み）
★tasks_to_enqueue / dispose_decision の 配線に 触っていない
```
