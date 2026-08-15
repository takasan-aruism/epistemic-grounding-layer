開発者規律 確認済(v1.0)

# 【契約・1本】★②狭い型 ―― ★★`record_only_patch`（★★入力は 文字5つだけ・★★門を 試験に 埋める）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 09:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 08:50**（★①の門が 実物を 通した ／ ★②の 中身も 指定 ／ ★足す 中身は 形が 固定）

**★★『狭い』の 実装** ―― ★★★自由文を 受け取らない（★文字5つ）／ ★足す 中身の 形は ★固定（★worker に 考えさせない）

---

## 1. ★★門を 試験の 中に 埋める（★★これが 一番 大事）

```
★★封印試験の 中で ★`patch_is_record_only(before, after)` が ★True に なる 事を 確かめる
★★★∴ ★この関数が ★門を 通らない 物を 作ったら ★★★自分の 試験で 落ちる
   ―― ★★門を 人が 後から 掛ける 形に しない（★★人が 忘れたら 通ってしまう）
   ―― ★★本日 何度も 出た 形（★★機構に 入っていない 規則は 守られない）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① その関数が 在り ★記録が 無い          → ★`after` を 作る ／ ★`added` に 足した 行 ／ ★`reason` は None
★★② その関数が 無い                        → ★`after` は None ／ ★`reason` は `"function_not_found"`
★★③ その関数が 既に 記録を 持つ            → ★★何も しない ／ ★`reason` は `"already_recorded"`
★★④ 形が 扱えない                          → ★`after` は None ／ ★`reason` は `"unsupported_shape"`
★★⑤ 作れた時 ★`after` は ★★門を 通る（★`patch_is_record_only` が True）
★★⑥ ★★元の 行が 1行も 消えない ／ 変わらない（★★足すだけ）
★★⑦ 同じ 入力を 2回 渡して ★同じ
★★⑧ `added` は ★作れなかった 時 ★空
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個・★足す 中身の 形は 固定）

<<<2DER:SKELETON>>>
def record_only_patch(before, file, function, component, received_from):
    """ある関数の先頭に、受け取ったことを残す行だけを足した本文を作る。挙動は変えない。

    before: いまの本文。文字列。
    file: その本文の file 名。文字列。記録には使わない。
    function: 行を足す関数の名前。文字列。
    component: 記録に残す部品の名前。文字列。
    received_from: 記録に残す送り手の名前。文字列。

    返り値は {"after", "added", "reason"} の辞書。

    before の中に "def <function>(" で始まる行を探す。
    見つからなければ after は None、reason は "function_not_found"、added は空。
    見つかった関数の中に既に "received_from" という文字が在れば
      after は None、reason は "already_recorded"、added は空。
    その関数に本体の行が1行も無ければ
      after は None、reason は "unsupported_shape"、added は空。

    作れるときは、その関数の本体の先頭に次の3行を、本体と同じ字下げで入れる。
      # 受け取ったことを残す
      try:
      から始まり、etrace の emit を呼び、except で受け止めて pass で終わる形。
      emit には component と function と {"received_from": received_from} を渡す。

    after は行を足しただけの本文。元の行は1行も消さず、1行も変えない。
    added は足した行の一覧。前後の空白を落とした形。
    reason は作れたとき None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★門を 中に 埋めてある）

<<<2DER:IMMUTABLE_TESTS>>>
from impl import record_only_patch
from patch_is_record_only import patch_is_record_only


def test_missing_function_gives_a_reason():
    """その関数が無ければ作らない。"""
    r = record_only_patch("def other():\n    pass\n", "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "function_not_found"
    assert r["added"] == []


def test_already_recorded_does_nothing():
    """既に記録を持つ関数には足さない。"""
    b = 'def f():\n    x = {"received_from": "Z.z"}\n    return 1\n'
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "already_recorded"


def test_empty_body_is_unsupported():
    """本体が無い関数は扱えない。"""
    r = record_only_patch("def f():\n", "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "unsupported_shape"


def test_patch_is_created_with_a_reason_of_none():
    """作れたときは reason が None で added が空でない。"""
    r = record_only_patch("def f():\n    return 1\n", "a.py", "f", "C", "X.y")
    assert r["reason"] is None
    assert r["added"] != []


def test_original_lines_are_all_kept():
    """元の行は1行も消えず、1行も変わらない。"""
    b = "def f():\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    for line in b.splitlines():
        assert line in r["after"].splitlines()


def test_after_passes_the_gate():
    """作った本文は門を通る。門をこの試験の中で確かめる。"""
    b = "def f():\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    g = patch_is_record_only(b, r["after"], allowed_calls=["emit"])
    assert g["ok"] is True


def test_component_and_sender_are_in_the_patch():
    """記録に残す名前が本文に入る。"""
    r = record_only_patch("def f():\n    return 1\n", "a.py", "f", "MYCOMP", "SEND.er")
    assert "MYCOMP" in r["after"]
    assert "SEND.er" in r["after"]


def test_added_is_empty_when_not_created():
    """作れなかったときは added が空。"""
    r = record_only_patch("def other():\n    pass\n", "a.py", "f", "C", "X.y")
    assert r["added"] == []


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ("def f():\n    return 1\n", "a.py", "f", "C", "X.y")
    assert record_only_patch(*a) == record_only_patch(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = record_only_patch("", "a.py", "f", "C", "X.y")
    for k in ("after", "added", "reason"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude）

```
★★`patch_is_record_only` を ★★worker の 場所から 読めるように 置く（★★import できる形）
   ―― ★★これは ★配線＝★足場 ／ ★★行数を 報告し ★2DER の 実績に 数えない
★★`before` = ★本番の file の 本文 ／ ★★`after` を ★★★置くのと commit は ★★人（★線は 動かさない）
```

## 6. ★★受入（★MGR の 4点 ＋ ★私から 2つ）

```
★★① `ds` / `rri` / `dev-workcell` の ★1本を ★2DER が 作った `after` で 埋める
★★② ★★その区間が ★両側に なる
★★③ ★★★私（Claude）が 手で 書いた 行 = ★★0
★★④ 既存の 試験が 通る
★★⑤（★私）★★★受け手の 名前を ★経路表から 引いていない
   ―― ★★`received_from` は ★★★呼び出し元から 渡す（★★`route_table` を 読まない）
   ―― ★理由 = ★★本日 実証した 循環（★表から 作った 物を 表で 確かめる 形に しない）
★★⑥（★私）★★門を 通らない `after` を 作ったら ★★★自分の 試験で 落ちる（★★§1 の 検算）
```

## 7. ★★やらないこと

```
★★★自由文を 受け取らない（★入力は 文字5つ）／ ★★足す 中身を worker に 考えさせない（★形は 固定）
★★置かない ／ commit しない（★★Taka『コードは 人』の 線を 動かさない）
★★★『既存コードを 2DER が 直せるように なった』と 書かない
   ―― ★★正しくは ★★『★記録を 足す 形だけ ／ ★門を 通った 物だけ ／ ★置くのは 人』
```
