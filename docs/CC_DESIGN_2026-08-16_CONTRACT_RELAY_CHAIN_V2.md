開発者規律 確認済(v1.0)

# 【契約・再発行】★5つが **一本に 結合するか** ―― ★★`relay_chain`（★★版上げでは ない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 21:1x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 21:00**（★詰まりの 原因が 確定 ／ ★門が 消えた 案件は もう 進められない ／ ★中身を 変えて 置き直して ほしい）

---

## 0. ★★★これは **版上げでは ない**（★先に 書く）

```
★★★中身は ★同じ ―― ★骨格 ／ ★場合の 列挙 ／ ★受入 ／ ★やらない事 は ★1つも 変えていない
★★変えたのは ★★試験の 説明文 ★1か所だけ（★★`linked。` → `linked とする。`）
★★★理由 = ★★投入の 鍵が ★『骨格 ＋ 封印試験 の 中身の sha256』（★`manager_v0.py` 逐語）
   ―― ★★∴ ★中身が 同じだと ★機械は ★『もう 投げた』と 数えて ★二度と 投げない
   ―― ★★★∴ ★鍵を 変えるためだけに ★1文字 動かした
★★★条件の 書き漏れでは ない ／ ★★新しい 形を 通すためでも ない
   ―― ★★本日 私は ★これを 取り違えて ★工具を v1→v6 まで 増築した（★Taka が 止めた）
   ―― ★★★∴ ★毎回 書く =『★同じ形を 通すためか ／ ★新しい形を 通すためか』＝ ★★今回は ★どちらでも ない（★運搬の 事故）
★★名前を 変えた 理由 = ★★『置いた 文書を 同じ名前で 差し替えない』（★Taka 常設）＝ ★★旧 `..._CONTRACT_RELAY_CHAIN.md` は ★そのまま 残す
```

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

## 3. ★★骨格（★★定数 0個 ／ ★★旧版と bytes 同一）

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
    run_id が None、空文字、または欄が無いものは、値が無いものとして扱う。
    値が無いもの同士を、同じ run_id とはみなさない。両方とも値が無いときは "linked" にしない。
    run_id は "linked" のときその値。それ以外は None。
    locator は locators から引いた値。無ければ None。
    by_status は6つの語を全部キーに持ち、その数を値にする。
    checked は expected の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★1か所だけ 説明文が 違う ／ ★assert は 全部 同じ）

<<<2DER:IMMUTABLE_TESTS>>>
from impl import relay_chain


def test_all_five_in_one_run_is_linked():
    """5つが同じ走行で揃えば linked とする。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, v, {"IR.mint": "rri/intent_record.py::mint"})
    assert r["rows"][0]["status"] == "linked"
    assert r["rows"][0]["run_id"] == "R1"
    assert r["rows"][0]["locator"] == "rri/intent_record.py::mint"


def test_both_sides_without_a_run_are_not_linked():
    """両側とも走行の番号が無いとき linked にしない。値が無いもの同士を一致とみなさない。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": None}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": None}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "split_run"
    assert r["rows"][0]["run_id"] is None


def test_both_sides_with_an_empty_run_are_not_linked():
    """空文字も値が無いものとして扱う。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": ""}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": ""}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "split_run"


def test_missing_run_field_is_treated_as_no_value():
    """欄が無くても値が無いものとして扱う。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint"}]
    v = [{"from": "H.S06", "to": "IR.mint"}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "split_run"


def test_one_side_without_a_run_is_not_linked():
    """片側だけ走行の番号が在っても linked にしない。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": None}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "split_run"


def test_a_real_value_still_links_when_mixed_with_missing_ones():
    """値の無いものが混ざっていても、実在の値で一致すれば linked。"""
    e = [{"from": "H.S06", "to": "IR.mint"}]
    s = [{"from": "H.S06", "to": "IR.mint", "run_id": None},
         {"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    v = [{"from": "H.S06", "to": "IR.mint", "run_id": "R1"}]
    r = relay_chain(e, s, v, {"IR.mint": "a.py::mint"})
    assert r["rows"][0]["status"] == "linked"
    assert r["rows"][0]["run_id"] == "R1"


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

## 6. ★★受入（★★旧版と 同じ ＋ ★再発行の 分 1つ）

```
★★① ★`by_status` の 6語が 出る（★★0件でも）
★★② ★★★`linked` が ★1本 出る（★★S06 を 実通過させた 後）
   ―― ★★0本なら ★★どの語で 止まっているかが 出る（★★★それが 次の 1手）
★★③ ★★`no_locator` の 件数（★★いま 85 前後の はず＝★★★0/86 と 突き合う）
★★④ ★★`split_run` が 出たら ★★★『揃った』と 書かない（★★同じ走行かを 見る 意味）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増 ／ ★★★source の 改変 0
★★★⑦（★再発行の 分）★★機械が ★これを ★自分で 投げた（★★★人が 投げ直していない）
   ―― ★★★MGR が 手で 投げた `TASK-2DER-E2F24135` は ★★この受入に 数えない
```

## 7. ★★やらないこと

```
★★★source を 触らない（★★工具を 増やさない＝★Taka 逐語）
★★候補を `locators` に 入れない（★★候補は 位置では ない）
★★★『プロトコルが 成立した』と 書かない ―― ★★正しくは ★★『★`linked` が N 本』
★★★これを『★v2』と 呼ばない ―― ★★中身は 同じ＝★★★呼び名で 版が 進んだように 見せない
```
