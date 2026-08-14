開発者規律 確認済(v1.0)

# 【契約・2DER へ投げる1件】★経路表に **問いを 立てる** ―― ★★`unregistered_keys`（★欠落起点）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 15:5x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語 15:4x**「★せっかく経路表を作ったのに、★これが足りなそうだ…が調査されていない。★なんのための経路表なのかさっぱりわからん。★いまだに、何かトラブルがあればそれを叩く、★モグラ叩きシステムでしかない」
＋ **正本 L827**（★欠落起点＝`STATIC_EDGE − Registered ROUTE_EDGE`）／ **MGR 15:38**（★受入4点）

---

## 1. ★★★私（設計/監査）の 非 ―― ★先に 書く

```
★★★Taka の 指摘は ★私にも 当たる
   ―― ★私は 本日 ★受入を 何度も 引いた ＝ ★★★どれも『★誰かが 出した 数の 検算』
   ―― ★★★経路表に ★私から 問いを 立てた 回数 = ★★0
   ―― ★★『★何が 起きたか』は 何度も 書いた ／ ★★★『★何が 載っていないか』は ★1度も 書いていない
★★★∴ ★監査が『壊れた物を 確かめる』側に 寄っていた（★★叩く側の 一部だった）
```

## 2. ★★★これは 正本に 在る 式（★★我々が 登記して 走らせていない）

```
★正本 L827 ＝ ★★『★コードでは 繋がっているが 経路表に 無いものは 何か』
★★MGR の 実測（15:3x）= ★記録に 出る `component.function` ★55 ／ ★経路表に 在る ★13
   → ★★★載っていない ★42件 ／ ★逆（経路表に 在るが 記録に 0件）★0件
★★★載っていない 42件に ★★今日 我々が 作った 物が 並ぶ
   ―― ★`MANAGER_V0.tick` ／ `FUNCTION_TABLE.index_lookup` ／ `STRUCTURE.s*` ／ `ROUTE_TABLE.adopt`
   ―― ★★★経路表を 作っている 当人が ★自分で 増やして ★自分で 登記していない
```

## 3. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 記録に 在り 経路表にも 在る       → ★出さない
★★② 記録に 在り 経路表に 無い        → ★★出す（★キー ＋ 件数）
★★③ 並び = ★★件数の 多い順 ／ ★同数なら ★キーの 昇順（★★人が 並べ替えない）
★★④ 件数 0 の キー                  → ★★出さない（★★記録に 出ていない ∴ 欠落では ない）
★⑤ 記録が 空                        → ★空の 一覧
★⑥ 経路表が 空                      → ★記録の 全キー
★★⑦ 経路表の 欄が 空／欠け           → ★★★その行は 照合に 使わない（★★登記済みとして 数えない）
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ 3つの キーは ★どの場合も 欠けない
```

## 4. ★★骨格（★★★docstring は 短い＝★本日 実測で 決めた 形）

```
<<<2DER:SKELETON>>>
def unregistered_keys(route_rows, counts):
    """記録に出るのに経路表に無いキーを出す。

    route_rows: {"component", "function"} を持つ辞書の一覧。
    counts: "component.function" をキー、件数を値とする辞書。

    返り値は {"rows", "unregistered", "checked"} の辞書。
    rows は {"key", "count"} の一覧。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 5. ★★封印試験（★★1バイトも 変えない・★★条件は ここに 在る）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import unregistered_keys


def test_registered_key_is_not_listed():
    """経路表に在るキーは出さない。"""
    r = unregistered_keys([{"component": "DW", "function": "tick"}], {"DW.tick": 5})
    assert r["rows"] == []
    assert r["unregistered"] == 0


def test_unregistered_key_is_listed_with_its_count():
    """経路表に無いキーは 件数つきで出す。"""
    r = unregistered_keys([], {"DW.tick": 5})
    assert r["rows"] == [{"key": "DW.tick", "count": 5}]
    assert r["unregistered"] == 1


def test_sorted_by_count_descending():
    """件数の多い順に並べる。"""
    r = unregistered_keys([], {"A.a": 1, "B.b": 9, "C.c": 5})
    assert [x["key"] for x in r["rows"]] == ["B.b", "C.c", "A.a"]


def test_same_count_is_sorted_by_key():
    """件数が同じなら キーの昇順。"""
    r = unregistered_keys([], {"B.b": 3, "A.a": 3})
    assert [x["key"] for x in r["rows"]] == ["A.a", "B.b"]


def test_zero_count_is_not_a_gap():
    """件数 0 のキーは 記録に出ていないので出さない。"""
    r = unregistered_keys([], {"A.a": 0})
    assert r["rows"] == []
    assert r["unregistered"] == 0


def test_empty_counts_gives_empty_rows():
    """記録が空なら 一覧も空。"""
    r = unregistered_keys([{"component": "DW", "function": "tick"}], {})
    assert r["rows"] == []


def test_empty_route_lists_everything():
    """経路表が空なら 記録の全キーが出る。"""
    r = unregistered_keys([], {"A.a": 2, "B.b": 1})
    assert r["unregistered"] == 2


def test_route_row_with_empty_field_does_not_register():
    """経路表の欄が空の行は 登記済みとして数えない。"""
    r = unregistered_keys([{"component": "", "function": "tick"}], {"UNKNOWN.tick": 4})
    assert r["unregistered"] == 1


def test_checked_is_the_number_of_keys_seen():
    """checked は 記録側のキーの数。"""
    r = unregistered_keys([{"component": "A", "function": "a"}], {"A.a": 1, "B.b": 2})
    assert r["checked"] == 2
    assert r["unregistered"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    rows = [{"component": "A", "function": "a"}]
    counts = {"A.a": 1, "B.b": 2}
    assert unregistered_keys(rows, counts) == unregistered_keys(rows, counts)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = unregistered_keys([], {})
    for k in ("rows", "unregistered", "checked"):
        assert k in r
<<<2DER:END>>>
```

## 6. ★★繋ぎ方（★★足場＝Claude）

```
★★入力① = ★`route_table.ROUTE` ＋ ★`route_adopt.adopted_rows()`
★★入力② = ★`observed_edges.direct_counts["by"]`（★★2DER が 書いた 数え上げ）
★★出す口 = ★★`observed_edges` の 中に ★欄を 1つ（★★新しい include 名を 作らない）
★★逆側（★経路表に 在るが 記録に 0件）= ★★★既に 在る `observed_from_counts` の `NOT_OBSERVED`
   ―― ★★同じ欄に 併記する（★★★2つ目の 部品を 作らない＝★昨日から 何度も 出た 型）
```

## 7. ★★受入（★MGR の 4点 ＋ ★私から 2つ）

```
★★① ★`unregistered` を ★★常に 出す（★件数 ＋ ★★名前 ＋ ★多い順）
★★② ★逆側も ★同じ欄に（★★いまは 0件 ∴ ★★★`0` と 書く＝★欄を 消さない）
★★③ ★MGR は ★毎回の 報告で ★この 2つの 数を 書く（★★『何が 起きたか』の 前に『★何が 載っていないか』）
★★④ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
★★⑤（★私）★★`checked` = ★★`direct_counts.by` の キーの 数（★★2つの 計器が 同じ物を 指す）
★★⑥（★私）★★★私も 毎回の 監査で ★この 2つの 数を 引く
   ―― ★★理由 = ★★★私の 非（§1）を ★言葉でなく ★手順で 塞ぐ
```

## 8. ★★言い方

```
★★★『経路表が 効いた』と 書かない（★MGR 逐語＝★これが 入るまで）
★★★『42件 直した』と 書かない ―― ★★42件は ★★『★登記していない』であって ★『壊れている』では ない
   ―― ★★次の 問いは ★★『★載せるべき物か ／ ★載せない物か』（★★★これは 別の 判断＝★今回は しない）
★★『モグラ叩きを やめた』と 書かない ―― ★★★機構が 毎回 出すように なって 初めて 言える
```
