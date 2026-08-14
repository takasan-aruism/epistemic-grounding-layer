開発者規律 確認済(v1.0)

# 【契約 v3】★`patch_is_record_only` ―― ★★注釈の行 と ★呼び出しの続きの行 を 許す

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 08:5x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `…_PATCH_IS_RECORD_ONLY_v2.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 08:30**（★実物の 差分で 落ちた ／ ★足す 2行を 名指し ／ ★★『同じ試験に 3回目』では なく ★新しい事実への 1回目）

**★★門が 効いている 事も 数で 出ている** ―― ★挙動を 変える 差分（`removed_line` / `changed_line` / `return_changed` / 引数を 増やす）は ★★弾いた

---

## 1. ★★足す 2行（★★MGR の 名指しを そのまま）

```
★(あ) ★`#` で 始まる 行は 許す
   ―― ★理由 = ★★実物の 差分には ★必ず 入る（★★理由を 書くのが 我々の 規律）
★(い) ★許した 呼び出しが 始まった 後の ★閉じるまでの 行は 許す（★★続きの 行）
   ―― ★理由 = ★★1つの 呼び出しが 複数行に なると ★2行目が ★『含まない 行』に 見える
```

## 2. ★★試験の 足し方（★★★既存 12本は 1バイトも 変えない）

```
★★新しく 足すのは ★★★2本だけ（★(あ)と(い)に 1本ずつ）
★★理由 = ★★★足した 2行の 検算に なる ／ ★★それ以外を 足すと ★前の 走行と 比べられない
```

## 3. ★★骨格 v3

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
      added_lines の各行が、次のどれかに当てはまる。
        allowed_calls のどれかを含む。
        "try" "except" "pass" "from" "import" のどれかで始まる。この判定は allowed_calls が空でも働く。
        "#" で始まる。
        続きの行である。
      "def " で始まる行の一覧が前後で同じ。
      "return" で始まる行の一覧が前後で同じ。

    続きの行とは、added_lines を after の並び順で見たとき、
    allowed_calls のどれかを含む行が現れてから、丸括弧の開きと閉じの数が釣り合うまでの間に在る行のこと。

    reasons は ok が False のときの理由の語の一覧。次の語を使う。当てはまるものを全部入れる。
      "removed_line" "changed_line" "not_allowed_line" "def_changed" "return_changed"
    changed_line は、removed_lines と added_lines の両方が空でないときに入れる。
    ok が True なら reasons は空。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★★既存 12本は v2 と bytes 同一 ／ ★末尾に 2本だけ 足した）

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


def test_comment_line_is_allowed():
    """# で始まる行は許す。理由を書く行は必ず入る。"""
    b = "def f():\n    return 1\n"
    a = "def f():\n    # 受け取ったことを残す\n    return 1\n"
    r = patch_is_record_only(b, a)
    assert r["ok"] is True


def test_continuation_lines_are_allowed():
    """許した呼び出しが複数行に渡るとき、続きの行も許す。"""
    b = "def f():\n    return 1\n"
    a = ('def f():\n'
         '    emit_record(\n'
         '        {"segment": "S08"},\n'
         '    )\n'
         '    return 1\n')
    r = patch_is_record_only(b, a, allowed_calls=["emit_record"])
    assert r["ok"] is True
    assert "not_allowed_line" not in r["reasons"]
<<<2DER:END>>>

## 5. ★★受入

```
★★① ★★★14本 全部 通る（★12＋2）
★★② ★★足した 2本が ★★★v2 では 落ちる（★★足した 2行の 検算＝★★片方だけ 通っても 意味が 無い）
   ―― ★★確かめ方 = ★v2 の 実装に この 2本を 当てる（★★★通ってしまったら ★私の 見立てが 外れ）
★★③ ★★実物の 差分（★本日 手で 書いた 4箇所）に 掛けて ★`ok` True
★★④ ★★挙動を 変える 差分は ★★今までどおり False（★★門が 緩んでいない＝★実物1件）
★★⑤ ★`skeleton_missing` = 0 ／ ★★定数 0個 ／ ★★既存 12本が bytes 不変
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 6. ★★言い方

```
★★★『3回目』と 書かない ―― ★★新しい 事実（★実物で 落ちた）への ★1回目（★MGR の 判断に 同意）
★★『門が 甘くなった』と 書かない ―― ★★★挙動を 変える 差分は ★弾いたまま（★受入④で 見る）
★★★これが 通っても ★『既存コードを 触れるように なった』と 書かない ―― ★★★狭い型（②）は ★まだ 無い
```
