開発者規律 確認済(v1.0)

# 【契約・1本】★⑥Pull の 差分 ―― ★★`route_facts`（★★事実量だけ・★裁定しない）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 19:5x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 19:37**（★条件5点）／ **Taka 逐語**「★パーセンタイルや 比率など ★事実量を 返すところまで ／ ★『異常』と 裁定するのは ★上へ 渡した方が 境界が きれい」

**★★★『異常』『少なすぎる』『おかしい』の 語を ★1つも 使わない**（★★裁定は Manager の 仕事）

---

## 1. ★★投入前の 確認（★MGR 条件⑤・★★先に 書く）

```
★★(あ) ★骨格の 定数 = ★★★0個（★★本日 2件 落ちた 原因＝★先頭の 定数）
★★(い) ★★試験が 期待する 値の 決め方が ★骨格に 在るか
   ―― ★`one_sided` の 条件 ／ `asymmetry` の 式 ／ ★★`percentiles` の 取り方（★順位法）
   ―― ★★★どれも 骨格の docstring に 1行ずつ 書いた（★★これが 無いと worker が 推測で 埋める）
```

## 2. ★★4問を 1本で（★★4本 作らない）

```
★問1 ★片側だけ                        → ★`one_sided`（★何本か ／ ★どこか）
★問2 ★前は 観測・今は 非観測           → ★`disappeared`（★何本か ／ ★どこか）
★問3 ★送りと 受けの 数の ずれ           → ★`asymmetry`（★差 ／ ★比）
★問4 ★通過数の 分位                    → ★`percentiles`（★min / p50 / p90 / max）
★★★どれも 事実量 ―― ★★『多い』『少ない』を ★言わない
```

## 3. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 送りが 0                → ★`one_sided` に 入る
★② 受けが 0                → ★`one_sided` に 入る
★③ 両方 1以上              → ★`one_sided` に 入らない
★★④ 両方 0                 → ★★`one_sided` に 入る（★★★片側すら 無い＝★0件に 押し込まない）
★★⑤ `previous` が None      → ★`disappeared` は ★空（★★『無い』と『渡されていない』を 混ぜない）
★★⑥ 前に 在って 今 無い      → ★`disappeared` に ★名前
★★⑦ 今 在って 前に 無い      → ★★★`disappeared` に 入れない（★★問いは 片方向）
★★⑧ 比の 分母が 0           → ★★`ratio` は ★`None`（★★0 で 埋めない）
★★⑨ 行が 0本               → ★`percentiles` は ★★全部 `None`（★★0 と 書かない）
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 4. ★★骨格（★★定数 0個・★★条件は docstring に 1行ずつ）

```
<<<2DER:SKELETON>>>
def route_facts(rows, previous=None):
    """区間の事実量を出す。経路表は使わない。判定の語は返さない。

    rows: {"from", "to", "send_count", "receive_count"} の辞書の一覧。
    previous: 前回の rows。渡されなければ None。

    返り値は {"total", "one_sided", "disappeared", "asymmetry", "percentiles"} の辞書。

    total は rows の数。
    one_sided は send_count と receive_count のどちらかが 0 の行の "from>to" の一覧。昇順。
    disappeared は previous に在って rows に無い "from>to" の一覧。昇順。previous が None なら空。
    asymmetry は行ごとの {"key", "diff", "ratio"} の一覧。rows と同じ順。
      diff は send_count と receive_count の差の絶対値。
      ratio は 小さい方 ÷ 大きい方。大きい方が 0 なら None。
    percentiles は send_count と receive_count の合計を並べた
      {"min", "p50", "p90", "max"}。順位法で取る。
      昇順に並べ、p50 は上から 0.5、p90 は 0.9 の位置を切り上げた順位の値。
      rows が空なら 4つとも None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 5. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import route_facts


def test_send_zero_is_one_sided():
    """送りが 0 なら片側だけ。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 0, "receive_count": 5}])
    assert r["one_sided"] == ["A.a>B.b"]
    assert r["total"] == 1


def test_receive_zero_is_one_sided():
    """受けが 0 なら片側だけ。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 5, "receive_count": 0}])
    assert r["one_sided"] == ["A.a>B.b"]


def test_both_sides_present_is_not_one_sided():
    """両方 1以上なら 片側だけには入らない。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 2, "receive_count": 3}])
    assert r["one_sided"] == []


def test_both_zero_is_still_one_sided():
    """両方 0 の行も 片側だけに入れる。0件に押し込まない。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 0, "receive_count": 0}])
    assert r["one_sided"] == ["A.a>B.b"]


def test_no_previous_gives_empty_disappeared():
    """previous が渡されなければ disappeared は空。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 1}])
    assert r["disappeared"] == []


def test_disappeared_lists_what_is_gone():
    """前に在って今無い区間を名前で出す。"""
    prev = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 1},
            {"from": "C.c", "to": "D.d", "send_count": 1, "receive_count": 1}]
    now = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 1}]
    r = route_facts(now, prev)
    assert r["disappeared"] == ["C.c>D.d"]


def test_new_segment_is_not_disappeared():
    """今在って前に無い区間は disappeared に入れない。"""
    prev = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 1}]
    now = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 1},
           {"from": "E.e", "to": "F.f", "send_count": 1, "receive_count": 1}]
    r = route_facts(now, prev)
    assert r["disappeared"] == []


def test_asymmetry_diff_and_ratio():
    """差は絶対値、比は 小さい方÷大きい方。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 10, "receive_count": 2}])
    assert r["asymmetry"][0]["key"] == "A.a>B.b"
    assert r["asymmetry"][0]["diff"] == 8
    assert r["asymmetry"][0]["ratio"] == 0.2


def test_ratio_is_none_when_the_larger_is_zero():
    """大きい方が 0 なら 比は None。0 で埋めない。"""
    r = route_facts([{"from": "A.a", "to": "B.b", "send_count": 0, "receive_count": 0}])
    assert r["asymmetry"][0]["ratio"] is None
    assert r["asymmetry"][0]["diff"] == 0


def test_percentiles_by_rank():
    """合計を昇順に並べ、順位法で取る。"""
    rows = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 0},
            {"from": "C.c", "to": "D.d", "send_count": 1, "receive_count": 1},
            {"from": "E.e", "to": "F.f", "send_count": 2, "receive_count": 1},
            {"from": "G.g", "to": "H.h", "send_count": 6, "receive_count": 4}]
    r = route_facts(rows)
    assert r["percentiles"]["min"] == 1
    assert r["percentiles"]["max"] == 10
    assert r["percentiles"]["p50"] == 2
    assert r["percentiles"]["p90"] == 10


def test_empty_rows_gives_none_percentiles():
    """行が無ければ 4つとも None。0 と書かない。"""
    r = route_facts([])
    assert r["percentiles"] == {"min": None, "p50": None, "p90": None, "max": None}
    assert r["total"] == 0


def test_unknown_names_are_treated_the_same():
    """知らない名前でも同じに扱う。外の表を引かない。"""
    r = route_facts([{"from": "ZZZ.zzz", "to": "QQQ.qqq", "send_count": 1, "receive_count": 1}])
    assert r["one_sided"] == []
    assert r["total"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    rows = [{"from": "A.a", "to": "B.b", "send_count": 1, "receive_count": 2}]
    assert route_facts(rows) == route_facts(rows)


def test_result_has_all_five_keys():
    """5つのキーは どの場合も 欠けない。"""
    r = route_facts([])
    for k in ("total", "one_sided", "disappeared", "asymmetry", "percentiles"):
        assert k in r
<<<2DER:END>>>
```

## 6. ★★受入

```
★★① ★★判定の語（★『異常』『少なすぎる』『おかしい』）が ★★★成果物に 0件
★★② ★★外の表を 引いていない（★★`test_unknown_names_are_treated_the_same` が 通る ／
   ★★★成果物に `import` が 0行）
★★③ ★★`skeleton_missing` = 0 ／ ★`ImportError` が 出ない（★★定数 0個の 検算）
★★④ ★封印試験 14本が 通る ／ ★`immutable_tests_touched` = false
★★⑤ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増（★★`observed_edges` に 欄）
★★⑥（★私）★★`one_sided` の 件数を ★front door から 引く
   ―― ★★いまの 見込み = ★★★大きい（★`HANDOFF.S12` は 送り 62,721 ／ 受け 0）
   ―― ★★★但し ★『多い』と 書かない ＝ ★数と 名前だけ 出す
```

## 7. ★★閉じ方（★MGR の 宣言に 同意）

```
★★⑥が 通ったら ★★`Route System CLOSED` を ★台帳に 1行
   ★その時に 出す 数 = ★①〜⑦＋取得可能 の ★8つ ／ ★未登録が 何件に なったか ／
     ★人が 叩いた 回数 ／ ★`[2DER実装]` と `[Claude実装]` の 件数
★★★閉じるまで ★Manager Phase（★Expected の 機械化）に ★手を つけない
   ―― ★★これは ★本日 私が やった 失敗（★★本線を 閉じないまま 次を 推した）の 裏返し
```
