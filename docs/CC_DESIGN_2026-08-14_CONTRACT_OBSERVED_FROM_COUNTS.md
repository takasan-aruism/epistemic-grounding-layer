開発者規律 確認済(v1.0)

# 【契約・2DER へ投げる1件】★『通った』を **直接数えから** 出す ―― ★★`observed_from_counts`

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 14:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 裁定 14:00**「★今夜 私が 出した『通った』の 数は ★全部 親子由来 ＝ ★数として 成り立っていない ／ ★正本 §2.3 の `OBSERVED_EDGE` が ★事実上 空 ／ ★2DER に 書かせる」

**★★worker に 届くのは 3つだけ** ―― ★骨格 ／ ★封印試験 ／ ★共通テンプレート ∴ **★条件は 試験に 書いた**

---

## 1. ★★この関数の 仕事（★★1つだけ）

```
★★入れる物 = ★★①区間の 一覧（★経路表）／ ★★②`direct_counts.by`（★★既に 通った物＝★2DER が 書いた 数え上げ）
★★出す物   = ★★区間ごとに ★『通ったか』＋『何件か』
★★★親子（`parent_event_id`）を ★1回も 使わない
★★★LLM を 1回も 使わない ／ ★file も 時刻も 乱数も 触らない（★純粋な 突き合わせ）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 数え上げに 在る                 → ★`OBSERVED` ／ ★その件数
★★② 数え上げに 無い                → ★`NOT_OBSERVED` ／ ★★★件数は 0 を 置く（★★欄を 消さない）
★★③ 数え上げに 在るが 0            → ★`NOT_OBSERVED`（★★0 は 通っていない）
★★④ `component` か `function` が 空 → ★★`UNKNOWN` ／ ★件数 0（★★★捨てない＝★0件に 押し込まない）
★★⑤ 同じ区間が 2つ 在る            → ★★★両方 残す（★★潰さない・★重複も 事実）
★★⑥ 3つの 数の 合計 = ★★区間の 数（★★★取りこぼし 0）
★★⑦ 並び順 = ★★★渡された 順（★★人が 並べ替えない）
★★⑧ 同じ入力を 2回 渡して ★★同じ
★★⑨ 数え上げ側にだけ 在るキー       → ★★★触らない（★この関数の 仕事では ない）
★⑩ 4つの キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
OBSERVED = "OBSERVED"
NOT_OBSERVED = "NOT_OBSERVED"
UNKNOWN = "UNKNOWN"


def observed_from_counts(route_rows, counts):
    """経路表の区間ごとに「実際に通ったか」を、記録の直接数えから決める。

    route_rows: 区間の一覧。各要素は {"route_id": 文字列, "component": 文字列, "function": 文字列} の辞書。
    counts: "component.function" をキー、件数(整数)を値とする辞書。

    返り値は dict で、キーは rows / observed / not_observed / unknown。

    rows は 区間ごとの一覧。渡された順のまま。各要素は
      {"route_id": …, "key": "component.function", "count": 整数, "status": 語} の辞書。
    status は 次の3つの語のどれか。
      OBSERVED       … 件数が 1 以上
      NOT_OBSERVED   … 件数が 0、または counts にキーが無い
      UNKNOWN        … component と function のどちらかが 空、または 欄が無い

    UNKNOWN の行は key を "UNKNOWN.UNKNOWN"、count を 0 にする。
    observed / not_observed / unknown は それぞれの status の行数。
    3つの合計は route_rows の数と必ず等しい。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない・★★曖昧な `in` を 置かない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import observed_from_counts, OBSERVED, NOT_OBSERVED, UNKNOWN


def test_present_in_counts_is_observed():
    """数え上げに在れば OBSERVED。件数をそのまま出す。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 7})
    assert r["rows"][0]["status"] == OBSERVED
    assert r["rows"][0]["count"] == 7
    assert r["observed"] == 1


def test_absent_from_counts_is_zero_not_missing():
    """数え上げに無いときは 0 を置く。欄を消さない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}], {})
    assert r["rows"][0]["status"] == NOT_OBSERVED
    assert r["rows"][0]["count"] == 0
    assert r["not_observed"] == 1


def test_zero_count_is_not_observed():
    """件数が 0 なら通っていない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 0})
    assert r["rows"][0]["status"] == NOT_OBSERVED


def test_empty_field_is_unknown_and_kept():
    """欄が空の区間は捨てずに UNKNOWN として残す。"""
    r = observed_from_counts([{"route_id": "S01", "component": "", "function": "tick"}],
                             {"DW.tick": 5})
    assert r["rows"][0]["status"] == UNKNOWN
    assert r["rows"][0]["key"] == "UNKNOWN.UNKNOWN"
    assert r["rows"][0]["count"] == 0
    assert r["unknown"] == 1


def test_missing_field_is_unknown():
    """欄が無い区間も UNKNOWN。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW"}], {"DW.tick": 5})
    assert r["rows"][0]["status"] == UNKNOWN
    assert r["unknown"] == 1


def test_duplicate_segments_are_both_kept():
    """同じ区間が2つ在れば 2行とも残す。潰さない。"""
    rows = [{"route_id": "S01", "component": "DW", "function": "tick"},
            {"route_id": "S01", "component": "DW", "function": "tick"}]
    r = observed_from_counts(rows, {"DW.tick": 3})
    assert len(r["rows"]) == 2
    assert r["observed"] == 2


def test_three_numbers_sum_to_the_row_count():
    """3つの数の合計は 区間の数と等しい。取りこぼしを作らない。"""
    rows = [{"route_id": "A", "component": "X", "function": "a"},
            {"route_id": "B", "component": "Y", "function": "b"},
            {"route_id": "C", "component": "", "function": "c"}]
    r = observed_from_counts(rows, {"X.a": 2})
    assert r["observed"] + r["not_observed"] + r["unknown"] == 3
    assert len(r["rows"]) == 3


def test_order_is_the_given_order():
    """並び順は渡された順のまま。"""
    rows = [{"route_id": "Z", "component": "X", "function": "a"},
            {"route_id": "A", "component": "Y", "function": "b"}]
    r = observed_from_counts(rows, {})
    assert [x["route_id"] for x in r["rows"]] == ["Z", "A"]


def test_keys_only_in_counts_are_left_alone():
    """数え上げ側にだけ在るキーは この関数では扱わない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 1, "OTHER.thing": 99})
    assert len(r["rows"]) == 1
    assert r["observed"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    rows = [{"route_id": "S01", "component": "DW", "function": "tick"}]
    counts = {"DW.tick": 1}
    assert observed_from_counts(rows, counts) == observed_from_counts(rows, counts)


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = observed_from_counts([], {})
    for k in ("rows", "observed", "not_observed", "unknown"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★繋ぎ方（★★足場＝Claude・★★worker には 渡さない）

```
★★入力① = ★`route_table.ROUTE`（★手書き18）＋ ★`route_adopt.adopted_rows()`（★採用行）
★★入力② = ★★`observed_edges.direct_counts["by"]`（★★2DER が 書いた 数え上げ＝★既に 動いている）
★★出す口 = ★★`observed_edges` の 中に ★欄を 1つ（★★新しい include 名を 作らない）
   ―― ★★★理由 = ★★私は 本日 ★新しい語を 探して 見つけられなかった（★★同じ 探し方の 罠を 作らない）
★★★親子由来の 値は ★★消さない ／ ★★★鍵で 区別する（★MGR 受入③＝★消すと 比べられない）
   ―― ★★併記の 文（案）= ★★『★`observed_*`＝直接数え ／ ★`edge_*`＝親子の隣接から作った推定』
```

## 6. ★★受入（★MGR の 4点 ＋ ★私から 2つ）

```
★★① ★★`route18` の『通った』が ★★★直接数えから 出る（★★親子を 使っていない＝★実物で）
★★② ★★同じ問いを 2回 引いて 同じ（★★書き込みを またいで）
★★③ ★★親子由来の 値が ★★消えていない ／ ★★鍵の 1行で 区別できる
★★④ ★★LLM ★0回
★★⑤（★私）★★3つの 数の 合計 = ★★区間の 数（★★取りこぼし 0＝★機械で 検算）
★★⑥（★私）★★`NOT_OBSERVED` の 区間を ★★★名前で 並べる（★★『★何件』で 終わらせない）
   ―― ★理由 = ★★★空欄が 次に 落ちる 場所（★[[denominator-before-progress-claims]]）
```

## 7. ★★言い方

```
★★『経路表が 通った』と 書かない ―― ★★正しくは ★★『★18区間の うち ★通った a ／ ★通っていない b ／ ★不明 c』
★★★今夜 出した『通った』の 数は ★★『数として 成り立っていない』と 書く（★MGR 逐語＝★そのまま 引き継ぐ）
★★『直った』と 書かない ―― ★★★2人が 別々に 引いて 一致した 時だけ 閉じる（★本日 実際に 効いた 形）
```
