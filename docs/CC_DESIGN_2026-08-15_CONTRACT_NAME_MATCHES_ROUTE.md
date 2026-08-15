開発者規律 確認済(v1.0)

# 【契約・1本】★埋める **前に** 割れを 出す ―― ★★`name_matches_route`

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 16:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 15:47**（★契約2本 ／ ★埋める 前に 割れを 出す）／ **私の 設計**（★15件 増やしてから 気づく 形に しない）

---

## 1. ★★何を 見るか（★★1つだけ）

```
★★埋めようと している 受け渡しの ★★実装の 名前 と ／ ★経路表が 持つ 名前 が ★同じか
★★★実物 = ★経路表 `RRI.request_type`（★351件）／ ★実装 `RRI.classify_request_type`（★2件）
   ―― ★★★埋めた 後に 見えた ＝ ★★今回の 割れ
★★★判定の 語を 返さない = ★★『同じ』『違う』の 事実だけ（★★どちらを 正とするかは Manager）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 経路表の 名前と 実装の 名前が 同じ        → ★`same`
★★② 違う                                    → ★★`differs`（★両方の 名前を 返す）
★★③ 経路表に その区間が 無い                → ★★`not_in_route`（★★『違う』と 混ぜない）
★★④ 実装の 名前が 空                        → ★★`unknown`（★★推測しない）
★★⑤ 経路表に 同じ `from` が 複数 在る        → ★★★全部 返す（★★潰さない＝★どれと 比べたかが 見える）
★★⑥ 並びは ★渡された 順
★★⑦ ★`by_status` は ★★4語 全部 キーを 持つ（★0件でも 欄を 消さない）
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def name_matches_route(plans, route_rows):
    """埋める前に、実装の名前が経路表の名前と同じかを出す。どちらが正しいかは決めない。

    plans: {"from", "to"} の辞書の一覧。from は送り手の名前、to は実装の名前。
    route_rows: {"from", "to"} の辞書の一覧。経路表が持つ名前。

    返り値は {"rows", "by_status", "checked"} の辞書。

    rows は plans と同じ順。各要素は {"from", "to", "route_to", "status"}。
      route_rows の中から from が同じ行を探す。
      1つも無ければ status は "not_in_route"、route_to は None。
      to が空、または欄が無ければ status は "unknown"、route_to は None。
      見つかった行の to と 同じなら status は "same"。
      違うなら status は "differs"。route_to にはその行の to を入れる。
      同じ from の行が複数在るときは、to が一致する行が在れば "same"、無ければ "differs" とし、
      route_to には見つかった行の to を昇順に並べた一覧を入れる。
    by_status は "same" "differs" "not_in_route" "unknown" の4語を全部キーに持ち、その数を値にする。
    checked は plans の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import name_matches_route


def test_same_name_is_same():
    """名前が同じなら same。"""
    r = name_matches_route([{"from": "H.S04", "to": "RRI.x"}], [{"from": "H.S04", "to": "RRI.x"}])
    assert r["rows"][0]["status"] == "same"


def test_different_name_returns_both():
    """違えば differs。経路表の名前も返す。"""
    r = name_matches_route([{"from": "H.S04", "to": "RRI.classify"}],
                           [{"from": "H.S04", "to": "RRI.request_type"}])
    assert r["rows"][0]["status"] == "differs"
    assert r["rows"][0]["route_to"] == "RRI.request_type"


def test_not_in_route_is_its_own_status():
    """経路表に無い区間は not_in_route。differs と混ぜない。"""
    r = name_matches_route([{"from": "H.S99", "to": "X.y"}], [{"from": "H.S04", "to": "RRI.x"}])
    assert r["rows"][0]["status"] == "not_in_route"
    assert r["rows"][0]["route_to"] is None


def test_empty_to_is_unknown():
    """実装の名前が空なら unknown。推測しない。"""
    r = name_matches_route([{"from": "H.S04", "to": ""}], [{"from": "H.S04", "to": "RRI.x"}])
    assert r["rows"][0]["status"] == "unknown"


def test_missing_to_field_is_unknown():
    """欄が無くても unknown。"""
    r = name_matches_route([{"from": "H.S04"}], [{"from": "H.S04", "to": "RRI.x"}])
    assert r["rows"][0]["status"] == "unknown"


def test_multiple_route_rows_are_all_returned():
    """同じ from の行が複数在れば 全部返す。潰さない。"""
    route = [{"from": "H.S04", "to": "B.b"}, {"from": "H.S04", "to": "A.a"}]
    r = name_matches_route([{"from": "H.S04", "to": "Z.z"}], route)
    assert r["rows"][0]["status"] == "differs"
    assert r["rows"][0]["route_to"] == ["A.a", "B.b"]


def test_match_among_multiple_is_same():
    """複数在っても 一致する行が在れば same。"""
    route = [{"from": "H.S04", "to": "B.b"}, {"from": "H.S04", "to": "A.a"}]
    r = name_matches_route([{"from": "H.S04", "to": "A.a"}], route)
    assert r["rows"][0]["status"] == "same"


def test_by_status_has_all_four_words():
    """4語すべてキーを持つ。0件でも欄を消さない。"""
    r = name_matches_route([], [])
    assert sorted(r["by_status"].keys()) == ["differs", "not_in_route", "same", "unknown"]
    assert set(r["by_status"].values()) == {0}


def test_order_is_the_given_order():
    """並びは渡された順のまま。"""
    plans = [{"from": "Z", "to": "z"}, {"from": "A", "to": "a"}]
    r = name_matches_route(plans, [])
    assert [x["from"] for x in r["rows"]] == ["Z", "A"]


def test_checked_counts_plans():
    """checked は plans の数。"""
    r = name_matches_route([{"from": "A", "to": "a"}, {"from": "B", "to": "b"}], [])
    assert r["checked"] == 2


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    p, q = [{"from": "A", "to": "a"}], [{"from": "A", "to": "a"}]
    assert name_matches_route(p, q) == name_matches_route(p, q)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = name_matches_route([], [])
    for k in ("rows", "by_status", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★★`plans` = ★これから 埋める 受け渡しの 一覧（★`record_only_patch` に 渡す 値と 同じ）
★★`route_rows` = ★`route_table.ROUTE` ＋ ★採用行
★★出す口 = ★既存 include に ★欄を 1つ
★★★埋める 前に 通す（★★後から 見る 形に しない＝★今回の 反省）
```

## 6. ★★受入

```
★★① ★★`by_status` の 4語が 出る（★★0件でも）
★★② ★★★今回 割れた 1件が ★`differs` で 出る（★★検算＝★★実物で 確かめる）
★★③ ★★残り15本を 掛けた 時の ★`differs` の 件数（★★★埋める 前に 分かる）
★★④ ★判定の語（★『間違い』『直すべき』）が ★★0件（★★どちらを 正とするかは Manager）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★名前を 直さない（★★出すだけ＝★直すのは 別の 判断）
★★『どちらが 正しいか』を 決めない（★Manager の 仕事＝★事実と 意味を 混ぜない）
★★★`differs` を『間違い』と 書かない ―― ★★別名かも しれない（★★旧名を 消さない 方針と 同じ）
```
