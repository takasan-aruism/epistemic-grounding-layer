開発者規律 確認済(v1.0)

# 【契約・1本】★『記録を 1行 足しただけ』を 検査する ―― ★★`patch_is_record_only`

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 08:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 裁定**（★(い)を採用・★但し★『既存の挙動を変えず 記録を1行足す』専用の★狭い型）／ **MGR 07:56**（★①先に 検査を 作る ／ ★中身も 指定）

**★★なぜ 検査が 先か** ―― ★門が 機械に 無いまま 型を 増やすと ★★『何でも 書ける 口』に なる（★Taka の 懸念）

---

## 1. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 前後が 同一                                   → ★`ok` True（★何も していない＝★★通す）
★★② 行を 足しただけ ／ 足した行が 許した 呼び出し   → ★`ok` True
★★③ 行が 消えた                                    → ★`ok` False ／ 理由 `"removed_line"`
★★④ 行が 変わった                                  → ★`ok` False ／ 理由 `"changed_line"`
★★⑤ 足した行が ★許した 呼び出しでも 決まった語でもない → ★`ok` False ／ 理由 `"not_allowed_line"`
★★⑥ 関数の 名前か 引数が 変わった／増減した          → ★`ok` False ／ 理由 `"def_changed"`
★★⑦ `return` の 数か 中身が 変わった                → ★`ok` False ／ 理由 `"return_changed"`
★★⑧ 理由は ★★★複数 出る（★★1つ目で 止めない＝★何が 悪いか 全部 見える）
★★⑨ `allowed_calls` が 空                          → ★決まった語だけ 許す
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 2. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def patch_is_record_only(before, after, allowed_calls=None):
    """変更が「記録を足しただけ」かを見る。挙動を変える変更は通さない。

    before: 変更前の本文。文字列。
    after: 変更後の本文。文字列。
    allowed_calls: 足してよい呼び出しの名前の一覧。渡されなければ空。

    返り値は {"ok", "reasons", "added_lines", "removed_lines", "changed_defs"} の辞書。

    行は改行で分ける。前後の空白を落としてから比べる。
    added_lines は after にだけ在る行の一覧。removed_lines は before にだけ在る行の一覧。
    changed_defs は "def " で始まる行のうち、前後で違うものの一覧。

    ok は次が全部成り立つときだけ True。
      removed_lines が空。
      before の行のうち位置が同じで中身が違うものが無い。
      added_lines の各行が、allowed_calls のどれかを含むか、
        "try" "except" "pass" "from" "import" のどれかで始まる。
      "def " で始まる行が前後で同じ。
      "return" で始まる行の一覧が前後で同じ。

    reasons は ok が False のときの理由の語の一覧。次の語を使う。当てはまるものを全部入れる。
      "removed_line" "changed_line" "not_allowed_line" "def_changed" "return_changed"
    ok が True なら reasons は空。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 3. ★★封印試験

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

## 4. ★★足場（★Claude）

```
★★入力 = ★`before`＝いまの file の 本文 ／ ★`after`＝2DER が 返した 本文
★★`allowed_calls` = ★★記録を 出す 関数の 名前だけ（★★★短い 一覧を 明示・★増やす時は 名指しで）
★★出す口 = ★既存 include に ★欄を 1つ
★★★この関数が True でも ★★置くのは 人（★Taka『コードは 人』の 線を 動かさない）
```

## 5. ★★受入

```
★★① ★`ok` と `reasons` が front door から 引ける
★★② ★★本日 私が 手で 書いた 4箇所を ★★★この検査に 掛けて ★`ok` True に なる
   ―― ★★★False なら ★検査が 厳しすぎる（★★そう 書く＝★検査を 疑う）
★★③ ★★挙動を 変える 変更（★`return` を 変える）が ★★★False に なる（★★実物1件）
★★④ ★`reasons` が ★★2つ以上 出る 例が 1件（★★1つ目で 止めていない）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
★★⑦（★私）★★★この検査が 通っただけで ★『安全に なった』と 書かない
   ―― ★★正しくは ★★『★記録だけの 変更か を 機械が 見るように なった』
```

## 6. ★★やらないこと

```
★★★狭い型（②）を ★この周で 作らない（★★門が 先＝MGR の 基本設計どおり）
★★置かない ／ commit しない（★人の線を 動かさない）
★★`allowed_calls` を ★★勝手に 広げない（★★増やす時は 名指しで 記録に 残す）
```
