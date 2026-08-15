開発者規律 確認済(v1.0)

# 【契約・1本】★5つが **一本に 結合するか** ―― ★★`relay_chain`（★★工具では ない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 19:4x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語**「★本線は ★`Component → Implementation locator → SEND/RECEIVE event → Route` という ★2DER 内部プロトコルを 成立させる こと」／ **MGR 19:22**（★工具は 閉じた ／ ★次は 実通過）

**★★これは 工具では ない** ―― ★source を 1文字も 触らない ／ ★★記録を 突き合わせるだけ

---

## 1. ★★何を 見るか（★★Taka 指定の 5つ）

```
★① `Expected logical component`   … ★経路表が 期待する 受け手の 名前
★② `Observed implementation locator` … ★実装が 自分で 名乗った 位置（★`file::function`）
★③ `SEND`                          … ★渡した 記録
★④ `RECEIVE`                       … ★受け取った 記録
★⑤ `run_id`                        … ★同じ 走行か
★★★『結合した』= ★★5つが ★★同じ 1本の 走行で 揃った 時だけ
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 5つとも 揃う ／ ★`run_id` が 同じ          → ★`linked`
★★② 5つとも 在るが ★`run_id` が 違う           → ★★`split_run`（★★『揃った』に しない）
★★③ `RECEIVE` が 無い                          → ★`no_receive`
★★④ `SEND` が 無い                             → ★`no_send`
★★⑤ ★実装の 位置が 無い                        → ★★`no_locator`（★★★候補は 位置では ない）
★★⑥ 経路表に その区間が 無い                    → ★`not_expected`
★★⑦ 複数 当てはまる                            → ★★★上から 最初の 1つ（★★順序を 試験で 固定）
★★⑧ ★`by_status` は ★★6語 全部 キーを 持つ（★0件でも 消さない）
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def relay_chain(expected, sends, receives, locators):
    """区間ごとに、5つが同じ走行で揃ったかを見る。source は見ない。

    expected: {"from", "to"} の辞書の一覧。経路表が期待する区間。
    sends: {"from", "to", "run_id"} の辞書の一覧。渡した記録。
    receives: {"from", "to", "run_id"} の辞書の一覧。受け取った記録。
    locators: to をキー、"file::function" の文字列を値とする辞書。実装が名乗った位置。

    返り値は {"rows", "by_status", "checked"} の辞書。

    rows は expected と同じ順。各要素は {"from", "to", "status", "run_id", "locator"}。
    status は次の6つの語のどれか。上から順に見て、当たったところで決める。
      "not_expected"  … from と to の組が expected に無い。この関数では起きない。
      "no_send"       … その組の sends が1件も無い。
      "no_receive"    … その組の receives が1件も無い。
      "no_locator"    … locators に to が無い、または値が空。
      "split_run"     … sends と receives は在るが、run_id が同じ組み合わせが1つも無い。
      "linked"        … 同じ run_id を持つ sends と receives の組が在る。
    run_id は "linked" のときその値。それ以外は None。
    locator は locators から引いた値。無ければ None。
    by_status は6つの語を全部キーに持ち、その数を値にする。
    checked は expected の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import relay_chain


def test_all_five_in_one_run_is_linked():
    """5つが同じ走行で揃えば linked。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, v, {"IR.mint": "rri/intent_record.py::mint"})
    assert r["rows"][0]["status"] == "linked"
    assert r["rows"][0]["run_id"] == "R1"
    assert r["rows"][0]["locator"] == "rri/intent_record.py::mint"


def test_different_run_id_is_split_run():
    """走行が違えば揃ったことにしない。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R2"}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "split_run"
    assert r["rows"][0]["run_id"] is None


def test_missing_receive():
    """受け取りが無ければ no_receive。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, [], {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "no_receive"


def test_missing_send():
    """渡しが無ければ no_send。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, [], v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "no_send"


def test_missing_locator():
    """実装の位置が無ければ no_locator。候補は位置ではない。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, v, {})
    assert r["rows"][0]["status"] == "no_locator"
    assert r["rows"][0]["locator"] is None


def test_empty_locator_is_also_missing():
    """位置が空文字でも no_locator。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, v, {"IR.mint": ""})
    assert r["rows"][0]["status"] == "no_locator"


def test_send_missing_wins_over_receive_missing():
    """両方無いときは no_send。順序は上から。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    r = relay_chain(e, [], [], {})
    assert r["rows"][0]["status"] == "no_send"


def test_by_status_has_all_six_words():
    """6語すべてキーを持つ。0件でも欄を消さない。"""
    r = relay_chain([], [], [], {})
    assert sorted(r["by_status"].keys()) == [
        "linked", "no_locator", "no_receive", "no_send", "not_expected", "split_run"]
    assert set(r["by_status"].values()) == {0}


def test_rows_keep_the_expected_order():
    """並びは expected の順のまま。"""
    e = [{"from": "B", "to": "b"}, {"from": "A", "to": "a"}]
    r = relay_chain(e, [], [], {})
    assert [x["from"] for x in r["rows"]] == ["B", "A"]


def test_checked_counts_expected():
    """checked は expected の数。"""
    r = relay_chain([{"from": "A", "to": "a"}, {"from": "B", "to": "b"}], [], [], {})
    assert r["checked"] == 2


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    e = [{"from": "A", "to": "a"}]
    s = [{"from": "A", "to": "a", "run_id": "R"}]
    assert relay_chain(e, s, s, {"a": "x.py::a"}) == relay_chain(e, s, s, {"a": "x.py::a"})


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = relay_chain([], [], [], {})
    for k in ("rows", "by_status", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★`expected` = ★`route_table.ROUTE` ＋ 採用行 ／ ★`sends` `receives` = ★記録
★`locators` = ★記録の `at`（★★実装が 自分で 名乗った 物だけ＝★★候補を 入れない）
★★出す口 = ★既存 include に ★欄を 1つ
★★★source を 1文字も 触らない（★★工具では ない）
```

## 6. ★★受入

```
★★① ★`by_status` の 6語が 出る（★★0件でも）
★★② ★★★`linked` が ★1本 出る（★★S06 を 実通過させた 後）
   ―― ★★0本なら ★★どの語で 止まっているかが 出る（★★★それが 次の 1手）
★★③ ★★`no_locator` の 件数（★★いま 85 前後の はず＝★★★0/86 と 突き合う）
★★④ ★★`split_run` が 出たら ★★★『揃った』と 書かない（★★同じ走行かを 見る 意味）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増 ／ ★★★source の 改変 0
```

## 7. ★★やらないこと

```
★★★source を 触らない（★★工具を 増やさない＝★Taka 逐語）
★★候補を `locators` に 入れない（★★候補は 位置では ない）
★★★『プロトコルが 成立した』と 書かない ―― ★★正しくは ★★『★`linked` が N 本』
```
