開発者規律 確認済(v1.0)

# 【契約・2DER へ投げる1件】★Manager v0 の 芯 ―― ★★`decide_tick`（★★次の1手を 1つ 決める）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 06:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 裁定 06:09**「★★Manager v0 も ★2DER に 実装させる（★Claude が 書かない）」
＋ **Taka 正本** §2.2 / §2.3（★駆動装置・★判断を 持たせない）／ **BUILD SPEC** `…MANAGER_V0_DRIVE_THE_LAST_SUBMITTED_TASK.md` §2 の 列挙10件

**★★worker に 届くのは 3つだけ** ―― ★骨格 ／ ★封印試験 ／ ★共通テンプレート
**★∴ 条件は ★★試験に 書いた**（★この依頼文は ★★届かない 前提）

---

## 1. ★★なぜ この 切り出しか（★★worker が 書ける 形に する）

```
★★Manager v0 の 全体 = ★巡回（★HTTP を 叩く ／ ★寝る ／ ★systemd）＝ ★★`impl.py` 1本では 書けない
★★∴ ★★★芯だけを 出す = ★★『★いまの 状態を 見て ★次の1手を 1つ 決める』
   ―― ★★★ここが Manager の 全て（★残りは ★呼ぶ・寝る だけ＝★判断が 無い）
   ―― ★★外側（巡回・service）は ★★★この関数が 通ってから（★一度に 広げない）
★★★語は 3つ = ★`RUN` ／ `SLEEP` ／ `STOP`（★★増やさない）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す・★★優先順位も 決める）

```
★★★上から 順に 見る（★★当たった 時点で 止める＝★★★worker が 順番を 迷わないように 試験で 固定）
★① ★案件が 無い                     → ★`SLEEP` ／ reason=`案件なし`
★② ★その案件が 完了している           → ★`SLEEP` ／ reason=`完了`
★★③ ★同じ工程で ★2回 止まっている     → ★★`STOP` ／ reason=`同じ所で2回`（★★★叩き続けない）
★★④ ★入口から 答えが 返らない          → ★`SLEEP` ／ reason=`入口の答えが無い`（★★自分で 起こさない）
★⑤ ★門が 通した                     → ★`RUN` ／ reason=`進める`
★★⑥ ★門が 断った                     → ★`SLEEP` ／ reason=★★断った 語 そのもの
     ―― ★`NOT_RUNNABLE` ／ `TASK_MISMATCH` ／ `BLOCKED`（★★★言い換えない＝★門の 語を そのまま 残す）
★★⑦ ★違う工程で 2回 止まっている       → ★★進んでいる ∴ ★`RUN`（★★止まりの 数では なく ★同じ所か で 決める）
★★⑧ ★3つの キーは ★どの場合も 欠けない（★`action` ／ `task_id` ／ `reason`）
```

## 3. ★★骨格（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
RUN = "RUN"
SLEEP = "SLEEP"
STOP = "STOP"


def decide_tick(task, gate, stopped_at=None):
    """次の1手を1つ決める。

    task: 進められそうな案件。{"task_id": 文字列, "dw_state": 文字列} の辞書。案件が無ければ None。
    gate: 実行口の門の答え。{"allow": 真偽, "cause": 文字列} の辞書。入口から答えが返らなければ None。
    stopped_at: この案件がこれまでに止まった工程名の一覧。既定は空。

    返り値は dict で、キーは action / task_id / reason。
    action は RUN / SLEEP / STOP のどれか。
    task_id は 案件の id。案件が無ければ None。
    reason は 次の語のどれか。
      案件なし / 完了 / 同じ所で2回 / 入口の答えが無い / 進める / 門が返した cause の語

    次の順で見て、当たった時点で決める。
      1 案件が無い / 2 完了している / 3 同じ工程で2回止まっている /
      4 入口から答えが返らない / 5 門が通した / 6 門が断った
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない・★★曖昧な `in` を 置かない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import decide_tick, RUN, SLEEP, STOP


def test_no_task_sleeps():
    """案件が無ければ寝る。task_id は None。"""
    r = decide_tick(None, None)
    assert r["action"] == SLEEP
    assert r["task_id"] is None
    assert r["reason"] == "案件なし"


def test_completed_task_sleeps():
    """完了した案件は寝る。門が通していても RUN にしない。"""
    r = decide_tick({"task_id": "T1", "dw_state": "COMPLETE"}, {"allow": True, "cause": "OK"})
    assert r["action"] == SLEEP
    assert r["reason"] == "完了"


def test_stuck_twice_at_same_stage_stops():
    """同じ工程で2回止まっているなら、門が通していても止める。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": True, "cause": "OK"}, stopped_at=["GENERATE", "GENERATE"])
    assert r["action"] == STOP
    assert r["reason"] == "同じ所で2回"


def test_stuck_at_different_stages_still_runs():
    """違う工程で止まっているなら進んでいる。RUN を返す。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": True, "cause": "OK"}, stopped_at=["PLAN", "GENERATE"])
    assert r["action"] == RUN
    assert r["reason"] == "進める"


def test_no_answer_from_front_door_sleeps():
    """入口から答えが返らないときは寝る。自分で起こさない。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"}, None)
    assert r["action"] == SLEEP
    assert r["reason"] == "入口の答えが無い"


def test_open_gate_runs():
    """門が通したら RUN。task_id をそのまま返す。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": True, "cause": "OK"})
    assert r["action"] == RUN
    assert r["task_id"] == "T1"
    assert r["reason"] == "進める"


def test_not_runnable_keeps_the_gate_word():
    """門が断ったときは、門が返した語をそのまま reason に残す。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": False, "cause": "NOT_RUNNABLE"})
    assert r["action"] == SLEEP
    assert r["reason"] == "NOT_RUNNABLE"


def test_task_mismatch_keeps_the_gate_word():
    """別の案件を指していると門が言ったら、その語をそのまま残す。"""
    r = decide_tick({"task_id": "T2", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": False, "cause": "TASK_MISMATCH"})
    assert r["action"] == SLEEP
    assert r["reason"] == "TASK_MISMATCH"


def test_blocked_keeps_the_gate_word():
    """門が BLOCKED と言ったら、その語をそのまま残す。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": False, "cause": "BLOCKED"})
    assert r["action"] == SLEEP
    assert r["reason"] == "BLOCKED"


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = decide_tick({"task_id": "T1", "dw_state": "READY_FOR_IMPLEMENTATION"},
                    {"allow": True, "cause": "OK"})
    for k in ("action", "task_id", "reason"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★測る物（★★これが 目的＝★止まっても 失敗では ない）

```
★① 2DER が どの工程まで 行ったか ／ ★★② 止まったなら ★工程名と ★理由（★逐語）
★★③ ★★Claude が 書いた 行 = ★★★0（★★今回も 0 なら ★2件 連続）
★★④ ★★人／Claude が ★run 系の 口を 叩いた 回数（★★今回は まだ 0 に ならない＝★巡回が 無い）
★⑤ ★所要 ／ ★★⑥ 封印試験が 触られていない（★`immutable_tests_touched=false`）
```

## 6. ★★次（★★この関数が 通ってから）

```
★★① 巡回（★60秒・★1巡回 1案件 1回・★何もしなかった時も 1行）＝ ★★★足場 ∴ ★Claude が 書く
     ―― ★★理由 = ★HTTP と systemd は ★`impl.py` 1本に 収まらない（★★行数を 報告し 実績に 数えない）
★★② ★同じ試金石を ★★人が 1度も 叩かずに 通す ＝ ★★★そこで 初めて『主体移管』と 書く
```

## 7. ★★やらないこと

```
★★語を 増やさない（★`RUN` / `SLEEP` / `STOP` の 3つ）
★★門の 語を ★言い換えない（★`NOT_RUNNABLE` を『進めない』等に しない＝★★由来が 消える）
★★★複数案件の 優先順位を 入れない（★Taka §1.3）／ ★★入口を 起こす 判断を 入れない
★★『Manager が できた』と 書かない ―― ★★★いまは ★芯の 1関数
```
