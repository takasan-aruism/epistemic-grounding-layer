開発者規律 確認済(v1.0)

# 【契約・1本】★『同じ問いを2回引いて動かない』を **機械に入れる** ―― ★★`unstable_keys`

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 22:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語**「★間違えの 報告を 聞くのが 私の 役割では なく ★★間違えの 正しい 手順を ★機械的に 2DER に 取り込む こと。★それも 正しい 手順で 登録し、★それを 報告する こと」

**★★入れる 手順** ―― 我々が **何度も 宣言して 一度も 機械に していない** もの:
> **★同じ問いを 2回 引いて ★動かない事を 確かめる**（★時刻の欄を 除く）

---

## 1. ★★これが 入ると 何が 変わるか（★1行）

```
★★★『★見ると 増える 計器』が ★★自動で 名指しされる（★人が 気づくのを 待たない）
   ―― ★本日 3件 出た（★索引の verify ／ git の [Claude実装] ／ ★食い違いの streak）
   ―― ★★どれも ★人が 偶然 2回 引いて 気づいた ＝ ★★★機構は 1つも 無い
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 2回が 同じ                     → ★`changed` は 空
★★② 値が 違う キー                → ★★★パスで 出す（★`"a.b.c"`）
★★③ 入れ子の 中の 違い            → ★★同じく パスで（★★1段で 止めない＝★本日の 型）
★★④ `ignore` に 在る パス          → ★除く（★★時刻の 欄）
★★⑤ 片方にしか 無い キー           → ★★変わったとして 出す（★★消えたも 変化）
★★⑥ 一覧の 中身が 違う            → ★そのパス
★★⑦ 並び順だけ 違う               → ★★★変わったとして 出す（★★潰さない）
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

```
<<<2DER:SKELETON>>>
def unstable_keys(first, second, ignore=None):
    """同じ問いの2回の答えを比べ、変わった所をパスで出す。判定の語は返さない。

    first: 1回目の答え。辞書。
    second: 2回目の答え。辞書。
    ignore: 除くパスの一覧。渡されなければ空。

    返り値は {"changed", "count", "compared"} の辞書。

    changed は変わった所のパスの一覧。昇順。
      パスは入れ子を "." で繋いだ文字列。例 "a.b.c"。
      一覧の中は番号で繋ぐ。例 "rows.0.count"。
      片方にしか無いパスも changed に入れる。
      並び順だけが違う一覧も、その位置のパスを changed に入れる。
      ignore に在るパスは changed に入れない。
    count は changed の数。
    compared は両方を合わせて見たパスの数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import unstable_keys


def test_same_answer_has_no_changed_keys():
    """2回が同じなら changed は空。"""
    a = {"x": 1, "y": "z"}
    r = unstable_keys(a, dict(a))
    assert r["changed"] == []
    assert r["count"] == 0


def test_changed_value_is_reported_by_path():
    """値が違えばパスで出す。"""
    r = unstable_keys({"x": 1}, {"x": 2})
    assert r["changed"] == ["x"]


def test_nested_change_is_reported_with_dots():
    """入れ子の中も点で繋いだパスで出す。"""
    r = unstable_keys({"a": {"b": {"c": 1}}}, {"a": {"b": {"c": 9}}})
    assert r["changed"] == ["a.b.c"]


def test_list_item_uses_its_index():
    """一覧の中は番号で繋ぐ。"""
    r = unstable_keys({"rows": [{"count": 1}]}, {"rows": [{"count": 2}]})
    assert r["changed"] == ["rows.0.count"]


def test_ignored_path_is_not_reported():
    """ignore に在るパスは出さない。"""
    r = unstable_keys({"as_of": "t1", "x": 1}, {"as_of": "t2", "x": 1}, ignore=["as_of"])
    assert r["changed"] == []


def test_ignore_only_removes_the_named_path():
    """ignore は名指しした所だけ除く。"""
    r = unstable_keys({"as_of": "t1", "x": 1}, {"as_of": "t2", "x": 2}, ignore=["as_of"])
    assert r["changed"] == ["x"]


def test_key_missing_on_one_side_is_a_change():
    """片方にしか無いキーも変化として出す。"""
    r = unstable_keys({"x": 1}, {})
    assert r["changed"] == ["x"]


def test_key_added_on_the_second_side_is_a_change():
    """2回目に増えたキーも変化。"""
    r = unstable_keys({}, {"y": 1})
    assert r["changed"] == ["y"]


def test_reordered_list_is_a_change():
    """並び順だけ違う一覧も変化として出す。潰さない。"""
    r = unstable_keys({"rows": ["a", "b"]}, {"rows": ["b", "a"]})
    assert r["count"] == 2


def test_changed_is_sorted():
    """changed は昇順。"""
    r = unstable_keys({"b": 1, "a": 1}, {"b": 2, "a": 2})
    assert r["changed"] == ["a", "b"]


def test_compared_counts_paths_from_both_sides():
    """compared は両方を合わせて見たパスの数。"""
    r = unstable_keys({"x": 1}, {"y": 1})
    assert r["compared"] == 2


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a, b = {"x": 1}, {"x": 2}
    assert unstable_keys(a, b) == unstable_keys(a, b)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = unstable_keys({}, {})
    for k in ("changed", "count", "compared"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★口 0増）

```
★★`GET /api/control?include=<欄>` を ★★2回 続けて 引き ／ ★`unstable_keys` に 通す
★★`ignore` = ★時刻の 欄（★`as_of` ／ `ts` ／ `events_read` の ような 増えて 当然の物）
   ―― ★★★`ignore` に 入れた パスは ★★名前で 記録に 残す（★★★黙って 除かない）
★★出す口 = ★同じ include に 欄を 1つ
```

## 6. ★★受入（★★入ったかだけを 数で）

```
★★① ★★`changed` が ★front door から 引ける
★★② ★★★本日 見つかった 3件が ★★機械で 名指しされる
   ―― ★`function_index` の 引いた回数 ／ ★`gap_streak` の `streak` ／ ★その他
★★③ ★★`ignore` に 入れた パスの 名前が ★記録に 残る（★★★除いた物が 見える）
★★④ ★★2回引いても `changed` 自体が 変わらない（★★★この検査が 自分を 汚さない）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 13本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★言い方（★Taka 逐語に 従う）

```
★★★間違いの 説明を 成果として 書かない ―― ★★『★機械に 入ったか』だけを 書く
★★『気をつける』と 書かない ―― ★★★機構が 名指しするか どうか
```
