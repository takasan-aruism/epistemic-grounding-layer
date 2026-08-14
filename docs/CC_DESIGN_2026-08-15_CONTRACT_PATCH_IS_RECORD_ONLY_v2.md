開発者規律 確認済(v1.0)

# 【契約 v2】★`patch_is_record_only` ―― ★★骨格に **3行 足す**（★★封印試験は 1バイトも 変えない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 08:2x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-15_CONTRACT_PATCH_IS_RECORD_ONLY.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 08:05**（★12本中 3本 落ちた ／ ★見立て＝骨格の 書き漏れ ／ ★足す 3行を 名指し）

---

## 1. ★★★私の 非（★先に 書く・★★これで 3件目）

```
★★落ちた 3本は ★★★どれも ★私が 骨格に 書かなかった 事
   ★① ★`added_lines` の 形（★前後の 空白を 落とすか）を 書かなかった
   ★② ★足す 場所（★関数の 中か 外か）を 書かなかった
   ★③ ★『★呼び出しを 含む か 決まった語で 始まる』の ★係り方が ★2通りに 読めた

★★★worker の 質では ない ＝ ★★条件を 書かなかった 側の 非
★★本日 これで ★★3件目（★`count` の 定義漏れ ／ `decide_tick` の『同じ』の 意味 ／ ★今回）
★★★∴ ★私の 投入前の 確認（★『試験が 期待する 値の 決め方が 骨格に 在るか』）が ★★効いていない
   ―― ★★★次から = ★★封印試験を 1本ずつ 読み ／ ★その試験が 使う 値の 決め方が ★骨格に 在るかを ★指で 追う
```

## 2. ★★足す 3行（★★MGR の 名指しを そのまま）

```
★(あ) ★`added_lines` は ★★行の 前後の 空白を 落として 入れる
★(い) ★足す 場所は ★★関数の 中でも 外でも よい
★(う) ★`allowed_calls` が 空でも ★`try` / `except` / `pass` / `from` / `import` で 始まる 行は 許す
```

## 3. ★★骨格 v2

<<<2DER:SKELETON>>>
def patch_is_record_only(before, after, allowed_calls=None):
    """変更が「記録を足しただけ」かを見る。挙動を変える変更は通さない。

    before: 変更前の本文。文字列。
    after: 変更後の本文。文字列。
    allowed_calls: 足してよい呼び出しの名前の一覧。渡されなければ空。

    返り値は {"ok", "reasons", "added_lines", "removed_lines", "changed_defs"} の辞書。

    行は改行で分ける。比べる前に、各行の前後の空白を落とす。
    added_lines は after にだけ在る行の一覧。前後の空白を落とした形で入れる。
    removed_lines は before にだけ在る行の一覧。同じく空白を落とした形。
    changed_defs は "def " で始まる行のうち、前後で違うものの一覧。
    足す場所は関数の中でも外でもよい。位置は見ない。

    ok は次が全部成り立つときだけ True。
      removed_lines が空。
      added_lines の各行が、次のどちらかに当てはまる。
        allowed_calls のどれかを含む。
        "try" "except" "pass" "from" "import" のどれかで始まる。
        この2つ目は allowed_calls が空でも当てはまる。
      "def " で始まる行の一覧が前後で同じ。
      "return" で始まる行の一覧が前後で同じ。

    reasons は ok が False のときの理由の語の一覧。次の語を使う。当てはまるものを全部入れる。
      "removed_line" "changed_line" "not_allowed_line" "def_changed" "return_changed"
    changed_line は、removed_lines と added_lines の両方が空でないときに入れる。
    ok が True なら reasons は空。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★★v1 と bytes 同一）

<<<2DER:IMMUTABLE_TESTS>>>
from impl import patch_is_record_only


def test_identical_is_ok():
    """前後が同じなら通す。"""
    s = "def f():\n    return 1\n"
    r = patch_is_record_only(s, s)
    assert r["ok"] is True
    assert r["reasons"] == []


def test_added_allowed_call_is_ok():
    """許した呼び出しを足しただけなら通す。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    emit_record()\n    return 1\n"
    r = patch_is_record_only(b, a, allowed_calls=["emit_record"])
    assert r["ok"] is True
    assert r["added_lines"] == ["emit_record()"]


def test_removed_line_is_not_ok():
    """行が消えたら通さない。"""
    b = "def f():\n    x = 1\n    return 1\n"
    a = "def f():\n    return 1\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is False
    assert "removed_line" in r["reasons"]


def test_changed_line_is_not_ok():
    """行が変わったら通さない。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    return 2\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is False


def test_not_allowed_line_is_not_ok():
    """許していない行を足したら通さない。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    danger()\n    return 1\n"
    r = patch_is_record_only(b, a, allowed_calls=["emit_record"])
    assert r["ok"] is False
    assert "not_allowed_line" in r["reasons"]


def test_import_line_is_allowed():
    """import で始まる行は許す。"""
    b = "def f():\n    return 1\n"
    a = "import os\ndef f():\n    return 1\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is True


def test_changed_def_is_not_ok():
    """関数の名前や引数が変わったら通さない。"""
    b = "def f(x):\n    return 1\n"
    a = "def f(x, y):\n    return 1\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is False
    assert "def_changed" in r["reasons"]
    assert r["changed_defs"] != []


def test_changed_return_is_not_ok():
    """return の中身が変わったら通さない。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    return None\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is False
    assert "return_changed" in r["reasons"]


def test_reasons_can_have_more_than_one():
    """理由は1つ目で止めない。当てはまるものを全部出す。"""
    b = "def f(x):\n    y = 1\n    return x\n"
    a = "def f(x, z):\n    return z\n"
    r = patch_is_record_only(b, a)
    assert len(r["reasons"]) >= 2


def test_empty_allowed_calls_still_allows_keywords():
    """allowed_calls が空でも try などは許す。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    pass\n    return 1\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is True


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    b, a = "def f():\n    return 1\n", "def f():\n    return 1\n"
    assert patch_is_record_only(b, a) == patch_is_record_only(b, a)


def test_result_has_all_five_keys():
    """5つのキーは どの場合も 欠けない。"""
    r = patch_is_record_only("", "")
    for k in ("ok", "reasons", "added_lines", "removed_lines", "changed_defs"):
        assert k in r
<<<2DER:END>>>

## 5. ★★受入（★★v1 と 同じ ＋ ★検算 1つ）

```
★★① ★★★落ちた 3本が ★通る（★★足した 3行の 検算）
★★② ★★他の 9本も 通ったまま（★★★12本 全部）
★★③ ★`skeleton_missing` = 0 ／ ★★定数 0個 ／ ★★封印試験が bytes 不変
★★④ ★★また 落ちたら ―― ★★★落ちた 試験の 名前を 書く ／ ★★3回目は 押さない（★MGR の 手順）
★★⑤ ★本日 手で 書いた 4箇所に 掛けて ★`ok` True（★★False なら 検査が 厳しすぎる＝★そう 書く）
```

## 6. ★★言い方

```
★★★『worker が 悪い』と 書かない ―― ★★条件を 書かなかった 側の 非（★本日 3件目）
★★『直った』と 書かない ―― ★★★12本 全部 通った 時だけ
```
