# 【契約・1本】★既に 在る 記録に **位置を 1つ 足す** ―― ★★`add_locator`（★★行を 作らない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-16 23:4x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語**（★『①だけ 開ける。★対象は `no_locator` 3件に 限定。★既存記録への 位置情報追加だけ。★3→0で 閉じる。★工具の 一般化は しない』）／ **MGR 23:19**（★場合 5つ ／ ★出してはいけない 結果 4つ）

---

## 0. ★★★受入 `3 → 0` は **そのままでは 成り立たない**（★★先に 実測を 出す）

```
★★MGR の 場合③ = ★『記録の 呼び出しが 2つ以上 → 止める』
★★★私の 実測（★3本の 実物を ast で 開いた）:
   ★`S01` `twoder/submit.py::submit`              … ★★`emit` が ★★5つ ／ ★`at` 無し ／ def 1行
   ★`S04` `rri/rri/request_type.py::classify_request_type` … `emit` 1つ ／ `at` 無し ／ def 1行
   ★`S08` `twoder/contract_seal.py::extract_contract`      … `emit` 1つ ／ `at` 無し ／ def 1行
★★★∴ ★場合③の ままだと ★`S01` は 止まる ＝ ★★★最良でも `3 → 1`（★★0 に ならない）

★★★救う 手 = ★★定義を **1つ 締める**（★★広げるのでは ない）
   ―― ★『記録の 呼び出し』＝ ★★★`received_from` を 含む `emit` だけ
   ―― ★実測 = ★★`S01` **1** ／ `S04` **1** ／ `S08` **1** ＝ ★★★3本とも 1つ
   ―― ★★これは ★★絞り込み ∴ ★★Taka の『工具の 一般化は しない』に ★触れない
★★★∴ ★この契約は ★その定義で 書く（★★書かなければ 受入が 成り立たない＝★先に 言う）
```

## 1. ★★何を するか（★★1つだけ）

```
★★`received_from` を 含む 記録の 行に ★★`at` の 欄を ★1つ 足す
★★★行を 作らない（★★無ければ 止める＝★★それは 計装＝★★★開いていない 側）
★★★他の 欄を 触らない ／ ★他の 関数に 当たらない ／ ★上書きしない
```

## 2. ★★場合の 列挙（★★MGR の 5つ ／ ★★出してはいけない 結果と 対）

```
★★① `received_from` を 含む 記録が 1つ ／ `at` 無し   → ★足す（`reason` は None）
★★② `at` が 既に 在る                                → ★★触らない（`already_has_at`）
★★③ `received_from` を 含む 記録が 2つ以上           → ★★止める（`multiple_records`・★選ばない）
★★④ 0 個                                             → ★★止める（`no_record`・★★行を 作らない）
★★⑤ その行の 形が 読めない                           → ★★止める（`unsupported_shape`・★拡張しない）
★★⑥ その関数が 無い                                  → ★止める（`function_not_found`）
★★⑦ 同じ入力を 2回 渡して ★同じ
★⑧ キーは ★どの場合も 欠けない

★★★出してはいけない 結果（★★試験で 縛る）
   ★(ア)★他の 関数の 行が 動く          ★(イ)★記録以外の 行が 動く
   ★(ウ)★`at` が 2つに なる              ★(エ)★止めた のに `after` が 空でない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def add_locator(before, function, at):
    """ある関数の、受け取ったことを残す行に、位置の欄を1つ足す。挙動は変えない。

    before: いまの本文。文字列。
    function: 位置を足す関数の名前。文字列。
    at: 入れる位置。"file::function" の形の文字列。

    返り値は {"after", "added", "reason"} の辞書。

    before の中に "def <function>(" で始まる行を探す。
    見つからなければ after は None、reason は "function_not_found"、added は空。
    その関数の本体を見る。本体とは、その def の次の行から、
    次の "def " で始まる行の手前まで。次の "def " が無ければ本文の最後まで。

    本体の中で "received_from" という文字を含む行を数える。
    0 行なら after は None、reason は "no_record"、added は空。行を作らない。
    2 行以上なら after は None、reason は "multiple_records"、added は空。どれかを選ばない。

    1 行のとき、その行に "at" という欄が既に在れば
      after は None、reason は "already_has_at"、added は空。上書きしない。

    その行の "received_from" の値は、二重引用符で囲まれた文字列である。
    その形でなければ after は None、reason は "unsupported_shape"、added は空。

    作れるときは、その行の "received_from" の値の閉じ引用符のすぐ後ろに
    次の文字をそのまま入れる。at の所だけ受け取った値に置き換える。

      , "at": "<at>"

    after はその1行だけが変わった本文。他の行は1文字も変えない。行数も変えない。
    added は変えた後のその1行を、前後の空白を落とした形で1つだけ入れた一覧。
    reason は作れたとき None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import add_locator


def test_adds_the_locator_field():
    """位置の欄を1つ足す。"""
    b = 'def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["reason"] is None
    assert '"at": "a.py::f"' in r["after"]


def test_the_line_count_does_not_change():
    """行を作らない。行数は変わらない。"""
    b = 'def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert len(r["after"].splitlines()) == len(b.splitlines())


def test_only_that_one_line_changes():
    """記録以外の行は1文字も変わらない。"""
    b = 'def f():\n    x = 1\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n    return x\n'
    r = add_locator(b, "f", "a.py::f")
    before_lines, after_lines = b.splitlines(), r["after"].splitlines()
    diff = [i for i in range(len(before_lines)) if before_lines[i] != after_lines[i]]
    assert len(diff) == 1
    assert "received_from" in before_lines[diff[0]]


def test_added_holds_just_the_changed_line():
    """added は変えた1行だけ。"""
    b = 'def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert len(r["added"]) == 1
    assert "received_from" in r["added"][0]


def test_existing_at_is_not_overwritten():
    """位置の欄が既に在れば触らない。"""
    b = 'def f():\n    emit("C", "g", {"received_from": "H.S01", "at": "old.py::f"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None
    assert r["reason"] == "already_has_at"
    assert r["added"] == []


def test_two_records_stop():
    """記録が2つ以上なら止める。どれかを選ばない。"""
    b = ('def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
         '    emit("C", "h", {"received_from": "H.S02"}, {}, "OK")\n')
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None
    assert r["reason"] == "multiple_records"


def test_no_record_stops_and_creates_nothing():
    """記録が無ければ止める。行を作らない。"""
    b = 'def f():\n    return 1\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None
    assert r["reason"] == "no_record"
    assert r["added"] == []


def test_unreadable_value_stops():
    """値が二重引用符の文字列でなければ止める。拡張しない。"""
    b = 'def f():\n    emit("C", "g", {"received_from": sender}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None
    assert r["reason"] == "unsupported_shape"


def test_missing_function_stops():
    """その関数が無ければ止める。"""
    b = 'def other():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None
    assert r["reason"] == "function_not_found"


def test_another_function_is_not_touched():
    """他の関数の記録は動かない。"""
    b = ('def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
         'def other():\n    emit("C", "z", {"received_from": "H.S09"}, {}, "OK")\n')
    r = add_locator(b, "f", "a.py::f")
    assert 'emit("C", "z", {"received_from": "H.S09"}, {}, "OK")' in r["after"]
    assert r["after"].count('"at"') == 1


def test_the_locator_field_appears_only_once():
    """位置の欄が2つにならない。"""
    b = 'def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"].count('"at"') == 1


def test_a_stopped_result_has_no_after():
    """止めたときは after を出さない。"""
    b = 'def f():\n    return 1\n'
    r = add_locator(b, "f", "a.py::f")
    assert r["after"] is None


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ('def f():\n    emit("C", "g", {"received_from": "H.S01"}, {}, "OK")\n', "f", "a.py::f")
    assert add_locator(*a) == add_locator(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = add_locator("", "f", "a.py::f")
    for k in ("after", "added", "reason"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★MGR・★★口 0増）

```
★対象 = ★★3本 だけ（`twoder/submit.py::submit` ／ `rri/rri/request_type.py::classify_request_type`
   ／ `twoder/contract_seal.py::extract_contract`）
★`at` = ★★`file::function`（★★実装が 名乗る 位置＝★推測しない）
★★門 = ★既に 在る `patch_is_record_only`（★v4）を そのまま 通す
★★★他の 関数に 当てない ／ ★★`no_receive` の 10本に 手を 出さない（★★開いていない）
```

## 6. ★★受入（★MGR の 3つ ＋ ★私から 1つ）

```
★★① `no_locator` ★3 → ★★0
★★② 6語の 合計 ＝ ★18（★★数が どこにも 消えない）
★★③ `linked` は ★★★予想を 固定しない（★★出た 語が 答え ／ ★`split_run` に なる 見込みも 書かない）
★★★④（★私）★★止まった 本数と 理由を ★名前で 出す
   ―― ★★3本 とも 通る 見込みだが ★★★通らなかった 時に ★『どれが どの語で 止まったか』が ★1回で 分かる
   ―― ★★★これが 無いと ★また 探し回る（★本日 1時間 探した 型）
```

## 7. ★★やらないこと

```
★★★行を 作らない（★無ければ 止める＝★★それは 計装＝★開いていない）
★★★どれかを 選ばない（★2つ以上 なら 止める）
★★★工具を 一般化しない（★未知の 形は `unsupported_shape` で 止める・★次の 版を 作らない）
★★`no_receive` の 10本を ★触らない
★★★『3本 直った』と 先に 書かない ―― ★★正しくは ★『★`no_locator` が ★N』
```
