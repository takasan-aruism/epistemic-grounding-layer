開発者規律 確認済(v1.0)

# 【契約・1本】★受け手の 候補を **並べる** ―― ★★`callee_candidates`（★★選ばない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 17:5x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 16:44**（★13件中 6件は 機械が 出した ／ ★残り 7件は『どの関数が 受け手か』の 材料が 要る ／ ★次の契約の 種）

**★★私の 手番の 取り違え を 先に 書く** ―― ★台帳は `next=DESIGN` だったのに ★私は『待ちは 無い』と 書いた（★Taka の 指摘で 気づいた）。★★手番は 台帳の `next=` を 読む、を ★また 外した。

---

## 1. ★★何を 材料に するか（★★循環しない 物だけ）

```
★★★使わない = ★送り手が 書いた `handed_to`（★★経路表 由来＝★MGR が 2回 踏んだ 循環）
★★★使う = ★★送り手の source の ★渡す 行の 近くに 在る ★呼び出し
   ―― ★理由 = ★★『渡した 直後に 呼んでいる 物』が ★受け手の 候補
   ―― ★★これは ★source から 出る ＝ ★★経路表を 1回も 引かない
★★★選ばない = ★候補を 並べるだけ（★★どれが 受け手かは ★Manager が 決める）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 近くに 呼び出しが 在る            → ★名前と 行番号を 出す
★★② 無い                              → ★★空の 一覧（★★『不明』と 書かない）
★★③ 複数 在る                         → ★★★全部 出す（★★潰さない・★絞らない）
★★④ 同じ名前が 複数回                 → ★1行に まとめ ★件数を 持つ
★★⑤ 点つきの 呼び出し（`a.b()`）      → ★★そのまま 出す（★★点で 切らない）
★★⑥ 範囲の 外                         → ★★見ない（★★`span` で 決まる）
★★⑦ 目印の 行が 無い                  → ★空の 一覧 ／ ★`marker_found` は False
★★⑧ 並びは ★★行番号の 順（★近い順では ない＝★決定論）
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def callee_candidates(lines, marker, span=10):
    """渡す行の近くに在る呼び出しを並べる。どれが受け手かは決めない。

    lines: source の行の一覧。文字列の一覧。1行目が添字 0。
    marker: 渡す行を見つけるための文字列。その文字を含む最初の行を目印にする。
    span: 目印の行から下に何行まで見るか。既定は 10。

    返り値は {"rows", "marker_found", "marker_line", "checked"} の辞書。

    marker を含む行が無ければ marker_found は False、marker_line は None、rows は空。
    在れば marker_found は True、marker_line はその行の添字。

    目印の行の次の行から span 行までを見る。lines の終わりで止める。
    その範囲の各行から、丸括弧の開きの直前に在る名前を取り出す。
    名前は英数字と下線と点でできた並び。点は切らずにそのまま入れる。
    def で始まる行は取り出さない。

    rows は {"name", "line", "count"} の一覧。name の初めて現れた行番号の順に並べる。
      line はその名前が初めて現れた行の添字。count は範囲の中で現れた回数。
    checked は実際に見た行の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import callee_candidates


def test_finds_a_call_after_the_marker():
    """目印の下に在る呼び出しを出す。"""
    lines = ["def f():", "    handoff('S04')", "    classify_request_type(x)", "    return 1"]
    r = callee_candidates(lines, "handoff(")
    assert r["marker_found"] is True
    assert r["rows"][0]["name"] == "classify_request_type"
    assert r["rows"][0]["line"] == 2


def test_no_marker_gives_empty():
    """目印が無ければ空。marker_found は False。"""
    r = callee_candidates(["def f():", "    return 1"], "handoff(")
    assert r["marker_found"] is False
    assert r["marker_line"] is None
    assert r["rows"] == []


def test_no_call_after_marker_gives_empty_rows():
    """目印の下に呼び出しが無ければ空の一覧。"""
    r = callee_candidates(["    handoff('S04')", "    x = 1"], "handoff(")
    assert r["marker_found"] is True
    assert r["rows"] == []


def test_all_calls_are_returned():
    """複数在れば全部出す。絞らない。"""
    lines = ["    handoff('S04')", "    a(x)", "    b(y)"]
    r = callee_candidates(lines, "handoff(")
    assert [x["name"] for x in r["rows"]] == ["a", "b"]


def test_repeated_call_is_one_row_with_a_count():
    """同じ名前が複数回なら 1行で件数を持つ。"""
    lines = ["    handoff('S04')", "    a(x)", "    a(y)"]
    r = callee_candidates(lines, "handoff(")
    assert len(r["rows"]) == 1
    assert r["rows"][0]["count"] == 2


def test_dotted_name_is_kept_whole():
    """点つきの名前は切らずにそのまま出す。"""
    lines = ["    handoff('S04')", "    mod.sub.fn(x)"]
    r = callee_candidates(lines, "handoff(")
    assert r["rows"][0]["name"] == "mod.sub.fn"


def test_def_line_is_not_taken():
    """def で始まる行からは取り出さない。"""
    lines = ["    handoff('S04')", "def g(x):", "    a(y)"]
    r = callee_candidates(lines, "handoff(")
    assert [x["name"] for x in r["rows"]] == ["a"]


def test_span_limits_the_range():
    """span を超えた行は見ない。"""
    lines = ["    handoff('S04')", "    a(x)", "    b(y)"]
    r = callee_candidates(lines, "handoff(", span=1)
    assert [x["name"] for x in r["rows"]] == ["a"]
    assert r["checked"] == 1


def test_rows_are_in_line_order():
    """並びは行番号の順。"""
    lines = ["    handoff('S04')", "    z(x)", "    a(y)"]
    r = callee_candidates(lines, "handoff(")
    assert [x["name"] for x in r["rows"]] == ["z", "a"]


def test_end_of_file_stops_the_range():
    """行の終わりで止まる。"""
    r = callee_candidates(["    handoff('S04')", "    a(x)"], "handoff(", span=99)
    assert r["checked"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    lines = ["    handoff('S04')", "    a(x)"]
    assert callee_candidates(lines, "handoff(") == callee_candidates(lines, "handoff(")


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = callee_candidates([], "handoff(")
    for k in ("rows", "marker_found", "marker_line", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★★`lines` = ★送り手の file の 本文（★★S01〜S16 の 渡す 所）
★★`marker` = ★その 区間の 渡す 行を 指す 文字（★例 `handoff("S04")`）
★★出す口 = ★既存 include に ★欄を 1つ
★★★経路表を 1回も 引かない（★★循環しない＝★本日 2回 踏んだ 所）
```

## 6. ★★受入

```
★★① ★★残り 7件（★`DS.UTTERANCE` ／ `DS.phase1` ／ `RRI.preflight_gate` ／ `RRI.request_type` ／
   `RUNGATE.refuse` ／ `RUNNER.run_test` ／ `SUBMIT.ENTRY`）に 掛けて ★★候補の 件数を 出す
★★② ★★候補が ★0件の 区間が 何本か（★★0 を 隠さない＝★★『材料が 出ない』も 結果）
★★③ ★★候補が ★複数の 区間が 何本か（★★★1つに 絞れない事を 隠さない）
★★④ ★★経路表を 引いていない（★★実装に `route_table` の 語が 0件）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★どれが 受け手かを 決めない（★★Manager の 仕事＝★事実と 意味を 混ぜない）
★★候補を ★1つに 絞らない（★★絞ると ★選択に なる）
★★★『受け手が 分かった』と 書かない ―― ★★正しくは ★★『★候補が N 件 出た』
```
