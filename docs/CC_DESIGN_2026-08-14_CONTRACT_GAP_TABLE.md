開発者規律 確認済(v1.0)

# 【契約・1本】★Phase C ―― ★★`gap_table`（★食い違いを 並べる・★★語を 1つも 増やさない）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 21:0x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 20:48**（★材料4つを 先に 実数で 渡してくれた ／ ★条件5点 ／ ★★『新しい 観測は 1つも 要らない』）

**★★新しい 語を 作らない** ―― ★食い違いの 鍵は **★由来の 名前を そのまま** 使う（★★どこから 来た 数かが 消えない）

---

## 1. ★★4つの 食い違い（★MGR が 名前を 置き ／ ★私が 由来を 鍵に する）

```
★① 経路表に 在るのに 通っていない   → 鍵 ★`route18.not_observed`        （★いま 0件）
★② 通っているのに 経路表に 無い     → 鍵 ★`unregistered`                （★いま 55件）
★③ 契約は 在るのに 段階が 進まない  → 鍵 ★`contract_progress.CREATED`   （★いま 109件）
★④ 片側しか 記録が 無い             → 鍵 ★`route_facts.one_sided`       （★いま 21件）
★★★4つとも ★★必ず 行が 出る（★★0件でも 欄を 消さない＝★本日 何度も 効いた 形）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 4つの 鍵が ★★必ず 4行（★★0件でも）／ ★並びは §1 の 順
★★② `count` = ★★`names` の 数（★★★取りこぼし 0＝★機械で 検算できる）
★★③ 空の 入力 → ★4行 ／ ★count 0 ／ ★names 空
★★④ `route18` の ★`OBSERVED` の 行は ★入らない（★★`NOT_OBSERVED` だけ）
★★⑤ `contract_progress` は ★★`observed_stage` が ★`CREATED` の 行だけ（★他の段階は 入らない）
★★⑥ `observed_stage` が ★None の 行は ★★入らない（★★『記録が 無い』は ★別の 話）
★★⑦ 名前の 並びは ★★★渡された 順の まま（★★並べ替えない）
★★⑧ `total` = ★4つの count の 合計
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数1個・★条件は docstring に 全部）

```
<<<2DER:SKELETON>>>
GAPS = ("route18.not_observed", "unregistered", "contract_progress.CREATED", "route_facts.one_sided")


def gap_table(route18, unregistered, progress, facts):
    """4つの食い違いを1つの表に並べる。判定の語は返さない。

    route18: {"rows": [{"route_id", "status"}]} の辞書。
    unregistered: {"rows": [{"key"}]} の辞書。
    progress: {"rows": [{"task_id", "observed_stage"}]} の辞書。
    facts: {"one_sided": 文字列の一覧} の辞書。

    返り値は {"rows", "total"} の辞書。

    rows は GAPS と同じ順で必ず4行。各要素は {"gap", "count", "names"}。
    gap は GAPS の語。names は名前の一覧で、渡された順のまま。count は names の数。

    route18.not_observed の names は status が "NOT_OBSERVED" の行の route_id。
    unregistered の names は rows の key。
    contract_progress.CREATED の names は observed_stage が "CREATED" の行の task_id。
    route_facts.one_sided の names は one_sided をそのまま。

    total は4つの count の合計。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import gap_table, GAPS


def test_gaps_are_the_four_source_names():
    """鍵は由来の名前そのもの。4つ、この順。"""
    assert GAPS == ("route18.not_observed", "unregistered",
                    "contract_progress.CREATED", "route_facts.one_sided")


def test_empty_input_still_gives_four_rows():
    """空でも4行。0件でも欄を消さない。"""
    r = gap_table({"rows": []}, {"rows": []}, {"rows": []}, {"one_sided": []})
    assert [x["gap"] for x in r["rows"]] == list(GAPS)
    assert [x["count"] for x in r["rows"]] == [0, 0, 0, 0]
    assert r["total"] == 0


def test_not_observed_rows_are_picked():
    """route18 は NOT_OBSERVED の route_id だけ。"""
    r18 = {"rows": [{"route_id": "S01", "status": "OBSERVED"},
                    {"route_id": "S02", "status": "NOT_OBSERVED"}]}
    r = gap_table(r18, {"rows": []}, {"rows": []}, {"one_sided": []})
    assert r["rows"][0]["names"] == ["S02"]
    assert r["rows"][0]["count"] == 1


def test_unregistered_keys_are_taken_as_is():
    """unregistered は key をそのまま。"""
    r = gap_table({"rows": []}, {"rows": [{"key": "A.a"}, {"key": "B.b"}]},
                  {"rows": []}, {"one_sided": []})
    assert r["rows"][1]["names"] == ["A.a", "B.b"]


def test_only_created_stage_is_picked():
    """契約は CREATED の行だけ。"""
    pr = {"rows": [{"task_id": "T1", "observed_stage": "CREATED"},
                   {"task_id": "T2", "observed_stage": "TESTED"}]}
    r = gap_table({"rows": []}, {"rows": []}, pr, {"one_sided": []})
    assert r["rows"][2]["names"] == ["T1"]


def test_none_stage_is_not_picked():
    """observed_stage が None の行は入らない。"""
    pr = {"rows": [{"task_id": "T1", "observed_stage": None}]}
    r = gap_table({"rows": []}, {"rows": []}, pr, {"one_sided": []})
    assert r["rows"][2]["count"] == 0


def test_one_sided_is_taken_as_is():
    """one_sided はそのまま。"""
    r = gap_table({"rows": []}, {"rows": []}, {"rows": []},
                  {"one_sided": ["A.a>B.b", "C.c>D.d"]})
    assert r["rows"][3]["names"] == ["A.a>B.b", "C.c>D.d"]
    assert r["rows"][3]["count"] == 2


def test_names_keep_the_given_order():
    """名前は渡された順のまま。並べ替えない。"""
    r = gap_table({"rows": []}, {"rows": [{"key": "Z.z"}, {"key": "A.a"}]},
                  {"rows": []}, {"one_sided": []})
    assert r["rows"][1]["names"] == ["Z.z", "A.a"]


def test_count_equals_the_number_of_names():
    """count は names の数と必ず同じ。"""
    r = gap_table({"rows": [{"route_id": "S01", "status": "NOT_OBSERVED"}]},
                  {"rows": [{"key": "A.a"}]},
                  {"rows": [{"task_id": "T1", "observed_stage": "CREATED"}]},
                  {"one_sided": ["X>Y"]})
    for row in r["rows"]:
        assert row["count"] == len(row["names"])


def test_total_is_the_sum():
    """total は4つの count の合計。"""
    r = gap_table({"rows": [{"route_id": "S01", "status": "NOT_OBSERVED"}]},
                  {"rows": [{"key": "A.a"}]},
                  {"rows": [{"task_id": "T1", "observed_stage": "CREATED"}]},
                  {"one_sided": ["X>Y"]})
    assert r["total"] == 4


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ({"rows": []}, {"rows": [{"key": "A.a"}]}, {"rows": []}, {"one_sided": []})
    assert gap_table(*a) == gap_table(*a)


def test_result_has_all_two_keys():
    """2つのキーは どの場合も 欠けない。"""
    r = gap_table({"rows": []}, {"rows": []}, {"rows": []}, {"one_sided": []})
    for k in ("rows", "total"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★新造 0）

```
★★入力4つは ★★すべて ★同じ口（★`GET /api/control?include=observed_edges`）に 既に 在る
   ★`route18.direct` ／ `unregistered` ／ `contract_progress` ／ `route_facts`
★★出す口 = ★★同じ include に ★欄を 1つ（★口 0増 ／ ★新台帳 0）
★★★新しい 観測を 1つも 足さない（★MGR 逐語）
```

## 6. ★★受入

```
★★① ★4行が ★必ず 出る（★★0件の 行も 消えない）
★★② ★★いまの 実数と 合う = ★`route18.not_observed` 0 ／ `unregistered` 55 ／
     `contract_progress.CREATED` 109 ／ `route_facts.one_sided` 21 ／ ★★`total` 185
   ―― ★★★合わなければ ★★鍵の 違いを 先に 疑う（★数を 争わない＝★本日 3回 効いた）
★★③ ★★`count` = `names` の 数（★4行とも・★機械で 検算）
★★④ ★判定の語（★『駄目』『遅れている』『異常』）が ★★成果物に 0件
★★⑤ ★`skeleton_missing` = 0 ／ ★`ImportError` が 出ない（★定数1個の 検算）
★★⑥ ★封印試験 12本 passed ／ ★`immutable_tests_touched` = false
★★⑦ ★LLM 0回 ／ ★口 0増 ／ ★★新造の 観測 0
```

## 7. ★★言い方（★★★ここが Manager の 入口）

```
★★★この表は ★★『次に 何を すべきか』では ない ―― ★★『★食い違いが どこに 何件 在るか』
   ―― ★★候補に するのは ★Manager の 仕事（★Phase D）＝ ★★★この契約では やらない
★★『185件の 問題が 在る』と 書かない ―― ★★★食い違いは ★問題とは 限らない
   ―― ★例 = ★`unregistered` 55件の うち ★★載せるべき物か どうかは ★★まだ 誰も 決めていない
★★『Phase C が 終わった』と 書けるのは ★★4行が ★front door から 引けた 時
```
