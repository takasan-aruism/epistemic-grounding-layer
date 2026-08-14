開発者規律 確認済(v1.0)

# 【契約・1本】★契約文書の 判定 ―― ★★`classify_contract_doc`（★理由に **印の数** を 使う）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 00:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 23:54**（★⑦ `VALID` / `INVALID` / `UNKNOWN` ／ ★`INVALID` の 理由に 印の数を 使う）
**★★この文書には 印の語を 説明として 書かない**（★本日 私の 文書が 除外された 原因）

---

## 1. ★★入力は **数** にする（★★文字列を 渡さない）

```
★★★理由 = ★印の 語を 引数や 試験に 書くと ★★その文書自身の 印が 増える
   ―― ★★本日 実際に 起きた（★私の 文書が `skipped` に 入った）
★★∴ ★★★数えるのは 足場 ／ ★この関数は ★★数だけを 受け取る
   ―― ★`begin_skeleton` ／ ★`begin_tests` ／ ★`end_marks` の ★3つの 整数
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 1 / 1 / 2                 → ★`VALID`（★2つの 塊が 各1つ ／ 閉じが 2つ）
★★② 0 / 0 / 0                 → ★`UNKNOWN`（★★契約文書では ない＝★★★壊れている とは 書かない）
★★③ 2 / 1 / 2                 → ★`INVALID` ／ ★理由に ★★数
★★④ 1 / 2 / 2                 → ★`INVALID` ／ ★理由に 数
★★⑤ 1 / 1 / 1                 → ★`INVALID`（★片方が 閉じていない）
★★⑥ 1 / 1 / 3                 → ★`INVALID`（★閉じが 多い）
★★⑦ 1 / 0 / 1                 → ★`INVALID`（★片方だけ 在る）
★★⑧ 0 / 1 / 1                 → ★`INVALID`（★同上）
★★⑨ 整数でない／負            → ★`UNKNOWN`（★★数えられていない＝★判定しない）
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def classify_contract_doc(begin_skeleton, begin_tests, end_marks):
    """契約文書の形を、印の数だけで判定する。文字列は受け取らない。

    begin_skeleton: 骨格の開始印の数。整数。
    begin_tests: 試験の開始印の数。整数。
    end_marks: 終了印の数。整数。

    返り値は {"status", "reason", "counts"} の辞書。

    status は "VALID" / "INVALID" / "UNKNOWN" のどれか。
      3つとも 0 なら "UNKNOWN"。契約文書ではないという意味。
      3つのどれかが整数でない、または負なら "UNKNOWN"。
      begin_skeleton が 1、begin_tests が 1、end_marks が 2 なら "VALID"。
      それ以外は "INVALID"。
    reason は "VALID" と "UNKNOWN" のとき None。
      "INVALID" のときは "skeleton=x tests=y end=z" の形の文字列。x y z は受け取った数。
    counts は {"begin_skeleton", "begin_tests", "end_marks"} の辞書で、受け取った値をそのまま入れる。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import classify_contract_doc


def test_one_one_two_is_valid():
    """1 と 1 と 2 なら VALID。"""
    r = classify_contract_doc(1, 1, 2)
    assert r["status"] == "VALID"
    assert r["reason"] is None


def test_all_zero_is_unknown():
    """3つとも 0 なら UNKNOWN。契約文書ではない。"""
    r = classify_contract_doc(0, 0, 0)
    assert r["status"] == "UNKNOWN"
    assert r["reason"] is None


def test_two_skeletons_is_invalid_with_counts():
    """骨格の印が2つなら INVALID。理由に数が入る。"""
    r = classify_contract_doc(2, 1, 2)
    assert r["status"] == "INVALID"
    assert r["reason"] == "skeleton=2 tests=1 end=2"


def test_two_tests_marks_is_invalid():
    """試験の印が2つでも INVALID。"""
    r = classify_contract_doc(1, 2, 2)
    assert r["status"] == "INVALID"
    assert r["reason"] == "skeleton=1 tests=2 end=2"


def test_one_end_is_invalid():
    """閉じが1つなら INVALID。"""
    r = classify_contract_doc(1, 1, 1)
    assert r["status"] == "INVALID"


def test_three_ends_is_invalid():
    """閉じが3つでも INVALID。"""
    r = classify_contract_doc(1, 1, 3)
    assert r["status"] == "INVALID"


def test_only_skeleton_is_invalid():
    """片方だけ在れば INVALID。"""
    r = classify_contract_doc(1, 0, 1)
    assert r["status"] == "INVALID"


def test_only_tests_is_invalid():
    """試験だけ在っても INVALID。"""
    r = classify_contract_doc(0, 1, 1)
    assert r["status"] == "INVALID"


def test_negative_is_unknown():
    """負の数は UNKNOWN。数えられていないという意味。"""
    r = classify_contract_doc(-1, 1, 2)
    assert r["status"] == "UNKNOWN"


def test_non_integer_is_unknown():
    """整数でなければ UNKNOWN。"""
    r = classify_contract_doc("1", 1, 2)
    assert r["status"] == "UNKNOWN"


def test_counts_are_returned_as_given():
    """counts は受け取った値をそのまま入れる。"""
    r = classify_contract_doc(1, 1, 2)
    assert r["counts"] == {"begin_skeleton": 1, "begin_tests": 1, "end_marks": 2}


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    assert classify_contract_doc(2, 1, 2) == classify_contract_doc(2, 1, 2)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = classify_contract_doc(0, 0, 0)
    for k in ("status", "reason", "counts"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude）

```
★★数えるのは 足場（★文書を 読んで 3つの 数を 出す）／ ★判定は この関数
★★出す口 = ★`observed_edges.auto_submit` の 中に ★欄を 1つ（★口 0増）
★★`INVALID` の 文書は ★★名前と 理由を 出す（★★★捨てない）
```

## 6. ★★受入

```
★★① ★`VALID` / `INVALID` / `UNKNOWN` の 件数が front door から 引ける
★★② ★★`INVALID` の 理由に ★★数が 入る（★★『壊れている』だけで 終わらせない）
★★③ ★★本日 除外された 6件が ★どれに 入るかが 名前で 出る
★★④ ★★★この文書 自身が ★`VALID` に なる（★★★説明に 印の語を 書かなかった 検算）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 13本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★文字列を 受け取らない（★★印の語を 引数にも 試験にも 書かない）
★★『壊れている』と 書かない ―― ★★`INVALID` ＋ ★数
★★★契約文書を 直さない（★直すのは 書いた 人＝★いまは Claude）
```
