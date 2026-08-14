開発者規律 確認済(v1.0)

# 【契約・1本】★対照を 置く ―― ★★`classify_changes`（★★どちらに 出たか だけを 返す）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 22:3x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 22:22**（★交絡＝『引く行為で 増える』と『その間に 常駐が 動いた』が 混ざる ／ ★A=2回続けて引く ／ ★B=同じだけ 待ってから引く ／ ★形は DESIGN 裁定）

---

## 1. ★★裁定（★★DESIGN）―― ★新しい 関数 1本

```
★★既存2本（`unstable_keys` ／ `filter_ignored`）は ★通った ∴ ★★★触らない（★封印試験を 変えない）
★★∴ ★★A と B の 結果を 受け取って ★分けるだけの 純関数を ★1本 足す
★★★語を 増やさない = ★★『引くと増える』『時間で動く』の 語を ★★★入れない
   ―― ★返すのは ★★★どちらに 出たか だけ（★`a_only` ／ `both` ／ `b_only`）
   ―― ★★意味（★どちらが 原因か）は ★★読む側の 仕事（★境界＝Taka §4）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① A だけに 出た 道順            → ★`a_only`
★② A にも B にも 出た            → ★`both`
★③ B だけに 出た                 → ★`b_only`（★★念の ため 型に 置く＝★MGR の ⑤）
★★④ 同じ道順が 何回 在っても      → ★★1行（★★集合として 扱う＝★★docstring に 明記）
★★⑤ 並びは ★★昇順（★★決定論）
★★⑥ 両方 空                      → ★rows 空 ／ ★3語とも 0
★★⑦ ★`by_kind` は ★★3語 全部 キーを 持つ（★★0件でも 欄を 消さない）
★★⑧ ★`checked` = ★相異なる 道順の 数（★★rows の 数と 等しい）
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

```
<<<2DER:SKELETON>>>
def classify_changes(a_changed, b_changed):
    """2つの一覧を比べ、道順がどちらに出たかを分ける。原因の語は返さない。

    a_changed: 続けて2回引いた時に変わった道順の一覧。
    b_changed: 同じだけ待ってから引いた時に変わった道順の一覧。

    返り値は {"rows", "by_kind", "checked"} の辞書。

    rows は道順ごとに {"path", "kind"}。path の昇順。
      kind は "a_only" / "both" / "b_only" のどれか。
      a_changed だけに在れば "a_only"。両方に在れば "both"。b_changed だけなら "b_only"。
      同じ道順が何回在っても1行にする。
    by_kind は "a_only" "both" "b_only" の3語を全部キーに持ち、その数を値にする。
    checked は rows の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import classify_changes


def test_only_in_a_is_a_only():
    """A だけに在れば a_only。"""
    r = classify_changes(["x"], [])
    assert r["rows"] == [{"path": "x", "kind": "a_only"}]
    assert r["by_kind"]["a_only"] == 1


def test_in_both_is_both():
    """両方に在れば both。"""
    r = classify_changes(["x"], ["x"])
    assert r["rows"] == [{"path": "x", "kind": "both"}]
    assert r["by_kind"]["both"] == 1


def test_only_in_b_is_b_only():
    """B だけに在れば b_only。"""
    r = classify_changes([], ["y"])
    assert r["rows"] == [{"path": "y", "kind": "b_only"}]
    assert r["by_kind"]["b_only"] == 1


def test_rows_are_sorted_by_path():
    """並びは道順の昇順。"""
    r = classify_changes(["z", "a"], [])
    assert [x["path"] for x in r["rows"]] == ["a", "z"]


def test_duplicates_collapse_to_one_row():
    """同じ道順が何回在っても1行。"""
    r = classify_changes(["x", "x"], ["x"])
    assert len(r["rows"]) == 1
    assert r["rows"][0]["kind"] == "both"


def test_by_kind_has_all_three_keys():
    """by_kind は3語すべてキーを持つ。0件でも欄を消さない。"""
    r = classify_changes([], [])
    assert sorted(r["by_kind"].keys()) == ["a_only", "b_only", "both"]
    assert set(r["by_kind"].values()) == {0}


def test_checked_equals_the_number_of_rows():
    """checked は rows の数。"""
    r = classify_changes(["x", "y"], ["y", "z"])
    assert r["checked"] == 3
    assert r["checked"] == len(r["rows"])


def test_mixed_case_counts_each_kind():
    """混ざっていても それぞれ数える。"""
    r = classify_changes(["a", "b"], ["b", "c"])
    assert r["by_kind"] == {"a_only": 1, "both": 1, "b_only": 1}


def test_empty_input_gives_empty_rows():
    """両方空なら rows も空。"""
    r = classify_changes([], [])
    assert r["rows"] == []
    assert r["checked"] == 0


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a, b = ["x", "y"], ["y"]
    assert classify_changes(a, b) == classify_changes(a, b)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = classify_changes([], [])
    for k in ("rows", "by_kind", "checked"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★口 0増）

```
★★A = ★同じ include を ★★続けて 2回 引く → ★`unstable_keys` → ★`filter_ignored`
★★B = ★1回 引く → ★★★A に かかったのと ★同じだけ 待つ（★引かずに）→ ★もう1回 引く
   → ★同じ2本に 通す
★★★待ち時間は ★★A の 実測を 使う（★★決め打ちしない＝★所要は 14〜25秒で 動く）
★★③ 2つの `changed` を ★`classify_changes` に 通す
★★④ 出す口 = ★`observed_edges.self_check` に ★欄を 1つ（★口 0増）
★★★A と B の 所要（秒）も ★一緒に 出す（★★待ち時間が 揃っていた事が 後から 引ける）
```

## 6. ★★受入（★★入ったかだけを 数で）

```
★★① ★`by_kind` の 3語が ★front door から 引ける
★★② ★★`a_only` に 出た 道順の ★★名前（★★『引く行為が 数に 入っている』候補＝★数だけに しない）
★★③ ★★`both` に 出た 道順の ★名前（★時間で 動く 候補）
★★④ ★★A と B の 所要が ★★★±20% 以内（★★★揃っていなければ ★この検査は 成り立たない
   ―― ★★揃っていない時は ★★その事を 出す＝★★★『結果』を 出さない）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 11本 passed ／ ★★定数 0個
★★⑥ ★★`unstable_keys` と `filter_ignored` が ★bytes 不変
★★⑦ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★言い方

```
★★★『引くと増える欄が N 件』と 書かない ―― ★★★`a_only` が N 件（★語を そのまま）
   ―― ★意味を 付けるのは ★読む側（★Manager）＝ ★境界を 越えない
★★『0件だった』を 成果に しない（★MGR 逐語）―― ★★A と B の 所要が 揃った かを 先に 見る
```
