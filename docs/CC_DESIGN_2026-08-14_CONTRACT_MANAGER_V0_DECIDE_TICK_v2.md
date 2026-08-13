開発者規律 確認済(v1.0)

# 【契約 v2 ＋ ★記録への 要求】★`decide_tick` ―― ★★順序を **平らに 開いた** ／ ★★★『どの試験が 落ちたか』が 記録に 無い

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 06:3x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-14_CONTRACT_MANAGER_V0_DECIDE_TICK.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 06:19**「★`JUDGE_REQUIRED` で 止まった ＝ ★契約を 直す（★コードを 書かない）」

---

## 1. ★★私が 引いた（★★申告を 読む前・★記録から）

```
★★試行1 = ★`skeleton_bytes_ok=true` ／ `skeleton_missing=0` ／ ★`added_lines=29`
          ／ ★`immutable_tests_touched=false` ／ ★★`passed=false, exit=1`（★★試験の 不合格）
★★試行2 = ★★`skeleton_bytes_ok=false` ／ ★★`skeleton_missing=615` ／ ★`added_lines=21`
          ／ ★`immutable_tests_touched=false` ／ ★★`passed=false, exit=2`（★★★読み込めなかった）

★★★∴ ★2回とも ★封印試験は 触っていない（★★契約は 壊されていない）
★★★∴ ★試行2 は ★★骨格を 丸ごと 落とした（★615 bytes＝★定数3行＋docstring）
```

## 2. ★★★記録に 足りない物（★★これが 今回の『何が 足りなかったか』）

```
★★残っているのは ★★`passed=false` と ★`exit=1` ★だけ
★★★どの試験が 落ちたかが ★★記録に 無い
   ―― ★★∴ ★★★契約を 直す 材料が 無い ＝ ★私は ★どこが 違ったかを ★知らない
   ―― ★★★∴ ★私は ★推測で 直さない（★★本日 ずっと 守ってきた 形）

★★★要求（★小さい・★記録側）= ★★落ちた 試験の ★★名前を 残す
   ★`pytest` の 出力から ★★`FAILED test_impl.py::<名前>` の 行だけ 拾って ★★outputs に 足す
   ―― ★★★全文を 残さない（★重くしない）／ ★★名前だけ（★★1行 × 落ちた数）
   ―― ★★`exit=2`（読み込めない）の 時は ★★★`収集できず` と 1語（★空に しない）
   ★★これが 入るまで = ★★★次に 落ちても ★また 目隠しに なる
```

## 3. ★★契約の 直し（★★★推測に 依らない 1点だけ）

```
★★★直す物 = ★docstring の ★★順序の 書き方（★★散文 → ★★平らな 場合分け）
   ―― ★根拠 = ★[[llm-nesting-must-become-flat-cases]]（★★字下げ・散文の 順序は 先頭へ 持ち上がる）
   ―― ★★これは ★『どの試験が 落ちたか』を 知らなくても ★★言える 直し
★★★変えない物 = ★★封印試験（★★1バイトも）／ ★語 3つ ／ ★関数の 形
   ―― ★理由 = ★★試験を 変えると ★★★前の走行と 比べられない（★実験が 成立しない）
```

## 4. ★★骨格 v2（★★これを そのまま 投入する）

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

    上から順に見て、当たったところで返す。

    その1 task が None のとき
      action は SLEEP。task_id は None。reason は "案件なし"。

    その2 task の dw_state が "COMPLETE" のとき
      action は SLEEP。reason は "完了"。

    その3 stopped_at の中に 同じ工程名が 2つ以上 在るとき
      action は STOP。reason は "同じ所で2回"。

    その4 gate が None のとき
      action は SLEEP。reason は "入口の答えが無い"。

    その5 gate の allow が 真のとき
      action は RUN。reason は "進める"。

    その6 それ以外のとき
      action は SLEEP。reason は gate の cause の値をそのまま入れる。

    task_id は その1 を除いて task の task_id を入れる。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 5. ★★封印試験（★★v1 と **1バイトも 同じ**＝★★比べられる ように 残す）

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

## 6. ★★順番（★★★これを 守る）

```
★★★① 先に ★§2 の 記録（★落ちた 試験の 名前）を 入れる
   ―― ★★理由 = ★★入れずに 投げると ★★また『落ちた』しか 残らない = ★★★同じ 目隠しを 繰り返す
★★② その上で ★§4/§5 を 投入する
★★③ ★また 落ちたら = ★★★今度は ★名前が 出る ∴ ★★そこを 直す（★★推測で 直さない）
```

## 7. ★★受入

```
★★① ★★落ちた 試験の 名前が ★記録から 引ける（★★実物 1件）
★★② ★`immutable_tests_touched` が ★★false の まま（★★2回とも そうだった＝★維持）
★★③ ★★`skeleton_bytes_ok` が ★true（★★試行2 の 615 bytes 欠けが 再発しない）
★★④ ★Claude が 書いた 実装行 = ★★★0（★★記録側の 1行は ★足場 ∴ ★行数を 報告し 実績に 数えない）
★★⑤ ★★止まっても ★失敗と 書かない ―― ★★収穫は ★『落ちた 試験の 名前』
```

## 8. ★★言い方

```
★★『worker の 出来が 悪い』と 書かない ―― ★★★私は ★どの試験が 落ちたかを ★知らない
★★『契約を 直した』と 書かない ―― ★★正しくは ★★『★順序の 書き方を 平らに した ／ ★試験は 変えていない』
```
