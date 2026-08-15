開発者規律 確認済(v1.0)

# 【契約・1本】★機械が **自分で 処分できた 割合** ―― ★★`dispositionable_counts`

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-16 02:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **私の 受入**（2026-08-15 22:3x ★『指摘の 分類が 3語の 中に 入った 回数』）／ **MGR 02:06**（★②`linked` を 1本 出すには ★契約が 1本 要る＝★DESIGN の 番）

---

## 0. ★★★受入の ために 作った 契約では ない（★先に 書く）

```
★★★私の 検算 = ★『★`linked` の 話が 無くても ★これを 置いたか』
   ―― ★★答え = ★★はい（★★私が ★昨夜 22時台に ★★自分の 受入として 先に 書いた 数＝★台帳に 在る）
   ―― ★★∴ ★★★計器を 動かす ために 作った 物では ない
★★★『部品を 増やさない』の 線 = ★守る ―― ★★これは ★★既存の 判定の **写しでは ない**
   ―― ★`dev-workcell` の `mechanically_dispositionable` = ★★1件を ★その場で 決める
   ―― ★★★この部品 = ★★何件が そうだったかを ★後から 数える（★決めない）
   ―― ★★★∴ ★同じ 事を 2回 書かない
```

## 1. ★★何を 数えるか（★★1つだけ）

```
★★★機械が 自分で 処分できた 件数 ／ ★人を 待った 件数
   ―― ★理由 = ★★これが ★★★『Claude を 呼ぶ 回数が 減ったか』の 数（★Taka 17条）
★★★語を 部品に 書かない = ★★決められる 分類の 一覧は ★呼び手が 渡す
   ―― ★理由 = ★★正本は `dev-workcell` 側（★★状態名の 手書きを 廃した のと 同じ 形）
   ―― ★★★部品が 語を 持つと ★正本が 2つに なる（★昨夜 潰した 型）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① その案件の 指摘が ★全部 決められる       → ★`machine`
★★② ★1つでも 決められない                    → ★★`needs_human`
★★③ ★指摘が 0件                              → ★★★`no_findings`（★★`machine` に 数えない）
★★④ ★`reproduced` が 真偽                     → ★★分類に 関係なく 決められる
★★⑤ ★`reproduced` が 無い / None              → ★分類で 見る
★★⑥ ★分類が 渡された 一覧に 無い              → ★決められない
★★⑦ ★分類の 一覧が 空                        → ★★`reproduced` だけで 決まる
★★⑧ ★`by_category` は ★渡された 語を 全部 キーに 持つ（★0件でも 消さない）
★★⑨ 並びは ★案件が 初めて 出た 順
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個 ／ ★★★3語を 書かない）

<<<2DER:SKELETON>>>
def dispositionable_counts(tasks, categories):
    """機械が自分で処分できた案件の数を数える。決めるのではなく、後から数える。

    tasks: 辞書の一覧。各要素は {"task_id", "findings"}。
      findings は辞書の一覧。各要素は {"category", "reproduced"}。
      findings が空の案件も渡される。reproduced は True か False か None。欄が無いこともある。
    categories: 分類の名前の一覧。この中に在る分類は機械が決められる。

    返り値は {"rows", "totals", "by_category", "checked"} の辞書。

    1件の指摘が「決められる」のは次のどちらか。
      reproduced が True か False である。
      その指摘の category が categories の中に在る。
    rows は tasks と同じ順。各要素は {"task_id", "status", "n_findings", "n_decidable"}。
      status は次の3つの語のどれか。
        "no_findings"  … その案件の指摘が0件。
        "machine"      … 指摘が1件以上あり、全部が決められる。
        "needs_human"  … 指摘が1件以上あり、1つでも決められない。
    totals は "machine" "needs_human" "no_findings" の3語を全部キーに持ち、その案件数を値にする。
    by_category は categories の語を全部キーに持ち、指摘の中に出てきた分類も足す。
      値はその分類の指摘の件数。
    checked は指摘の総数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import dispositionable_counts


def test_all_decidable_is_machine():
    """全部決められれば machine。"""
    t = [{"task_id": "T1", "findings": [{"category": "test_failure", "reproduced": None}]}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["rows"][0]["status"] == "machine"
    assert r["totals"]["machine"] == 1


def test_one_undecidable_makes_it_need_human():
    """1つでも決められなければ needs_human。"""
    t = [{"task_id": "T1", "findings": [{"category": "test_failure", "reproduced": None},
                                        {"category": "requirement_not_implemented"}]}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["rows"][0]["status"] == "needs_human"
    assert r["rows"][0]["n_decidable"] == 1
    assert r["rows"][0]["n_findings"] == 2


def test_no_findings_is_its_own_word():
    """指摘0件の案件は no_findings。machine に数えない。"""
    t = [{"task_id": "T1", "findings": []}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["rows"][0]["status"] == "no_findings"
    assert r["totals"]["no_findings"] == 1
    assert r["totals"]["machine"] == 0


def test_reproduced_true_is_decidable_whatever_the_category():
    """reproduced が真偽なら分類に関係なく決められる。"""
    t = [{"task_id": "T1", "findings": [{"category": "anything", "reproduced": True}]}]
    r = dispositionable_counts(t, [])
    assert r["rows"][0]["status"] == "machine"


def test_reproduced_false_is_also_decidable():
    """False も決められる。値が在ることが大事。"""
    t = [{"task_id": "T1", "findings": [{"category": "anything", "reproduced": False}]}]
    r = dispositionable_counts(t, [])
    assert r["rows"][0]["status"] == "machine"


def test_missing_reproduced_field_falls_back_to_category():
    """欄が無ければ分類で見る。"""
    t = [{"task_id": "T1", "findings": [{"category": "test_failure"}]}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["rows"][0]["status"] == "machine"


def test_unknown_category_is_not_decidable():
    """一覧に無い分類は決められない。"""
    t = [{"task_id": "T1", "findings": [{"category": "requirement_not_implemented"}]}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["rows"][0]["status"] == "needs_human"


def test_empty_categories_leaves_only_reproduced():
    """分類の一覧が空なら reproduced だけで決まる。"""
    t = [{"task_id": "T1", "findings": [{"category": "test_failure"}]}]
    r = dispositionable_counts(t, [])
    assert r["rows"][0]["status"] == "needs_human"


def test_by_category_keeps_every_given_word():
    """渡された語は0件でもキーを持つ。"""
    r = dispositionable_counts([], ["test_failure", "failing_test"])
    assert sorted(r["by_category"].keys()) == ["failing_test", "test_failure"]
    assert set(r["by_category"].values()) == {0}


def test_by_category_also_counts_words_that_appear():
    """出てきた分類も足す。"""
    t = [{"task_id": "T1", "findings": [{"category": "requirement_not_implemented"}]}]
    r = dispositionable_counts(t, ["test_failure"])
    assert r["by_category"]["requirement_not_implemented"] == 1
    assert r["by_category"]["test_failure"] == 0


def test_rows_keep_the_given_order():
    """並びは渡された順のまま。"""
    t = [{"task_id": "B", "findings": [{"category": "x"}]},
         {"task_id": "A", "findings": [{"category": "x"}, {"category": "y"}]}]
    r = dispositionable_counts(t, [])
    assert [x["task_id"] for x in r["rows"]] == ["B", "A"]
    assert r["checked"] == 3


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    t = [{"task_id": "T1", "findings": [{"category": "test_failure"}]}]
    assert dispositionable_counts(t, ["test_failure"]) == dispositionable_counts(t, ["test_failure"])


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = dispositionable_counts([], [])
    for k in ("rows", "totals", "by_category", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★`tasks` = ★案件ごとに ★その案件の 指摘を まとめた 物
   ―― ★★★指摘が 0件の 案件も 入れる（★★入れないと ★`no_findings` が ★永遠に 出ない）
   ―― ★★これは ★私が 書いた 直後に ★自分で 見つけて 直した（★成り立たない 分岐を 置かない）
★★`categories` = ★★★`dev-workcell` の 正本から 引く（★★部品にも 足場にも 語を 書かない）
★★出す口 = ★既存 include に ★欄を 1つ
★★★語の 正本は 1つ = ★`dw/disposition.py`（★状態名を `_MAP` に 一本化した のと 同じ 形）
```

## 6. ★★受入

```
★★① ★`totals` の 3語が 出る（★★0件でも）
★★② ★★★`needs_human` の 件数 = ★★『Claude を 呼んだ 回数』の 数（★★いま 1件以上 の はず）
★★③ ★★`by_category` に ★★`requirement_not_implemented` が 出る
   ―― ★★★これが ★昨夜 止まった 分類（★★実物と 突き合う＝★検算）
★★④ ★★★この数を ★時間で 並べて ★`needs_human` が 減れば ★★Claude が 減った と 数で 言える
   ―― ★★1回の 値では 何も 言わない（★★★『減った』は 2点 以上 必要）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 13本 passed ／ ★★定数 0個 ／ ★★★3語が 骨格に 無い
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
★★★⑦（★今夜の 分）★★この 契約が 走る ことで ★★`RUNNER.hand_to_worker → WORKER.received_from_runner` が
   ★1回 通る = ★★`linked` が ★1本 出るか が 分かる（★★出なければ ★どの語で 止まったかが 出る）
   ―― ★★★但し ★★これは ★副産物 = ★★★『linked を 出すために 置いた』と 書かない
```

## 7. ★★やらないこと

```
★★★分類の 語を 部品に 書かない（★★正本を 2つに しない）
★★★処分を 決めない（★★決めるのは `dev-workcell` ／ ★これは 数えるだけ）
★★『機械化率』と 呼ばない ―― ★★正しくは ★★『★`machine` N 件 ／ ★`needs_human` M 件』
★★★1回の 値で『減った』『増えた』と 書かない（★★2点 以上）
```
