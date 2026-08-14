開発者規律 確認済(v1.0)

# 【契約・★1本だけ】★記録**だけ**から 区間を 作る ―― ★★`segments_from_records`

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 17:0x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 16:5x**「★裁定3件 全部 受ける ／ ★★③が 本体 ／ ★次の 契約を ★1本だけ」

**★★★この関数は 経路表を 1回も 引かない**（★★引くと 循環する＝★既に 載っている 18 しか 出ない）

---

## 1. ★★両側の 証拠（★★確定は 揃った時だけ）

```
★★送りの 記録 = ★『★私は B へ 渡した』（★A が 書く）
★★受けの 記録 = ★『★私は A から 受け取った』（★B が 書く）★★★いま 0件＝★足場で 足す（★Claude）
★★★揃った時だけ ★確定 ／ ★片側は ★★第3の値で 残す（★★★捨てない）
   ―― ★[[instrument-not-inferencer-both-sides-required]]
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 送りと 受けが 揃う      → ★`BOTH`
★★② 送りだけ                → ★`SEND_ONLY`（★★0件に しない）
★★③ 受けだけ                → ★`RECEIVE_ONLY`（★★同上）
★★④ 同じ区間が 何回も        → ★★1行に まとめ ★件数を 持つ
★★⑤ 相手が 空／欄が 無い     → ★★区間に しない ／ ★★`skipped` に 数える（★★★消さない）
★★⑥ 自分から 自分へ          → ★★★残す（★潰さない＝★それも 事実）
★★⑦ 並び = ★件数の 多い順 ／ 同数は ★`from`,`to` の 昇順
★★⑧ 3つの 数の 合計 = ★★区間の 数（★★取りこぼし 0）
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★docstring は 短い＝★本日 実測で 決めた 形）

```
<<<2DER:SKELETON>>>
BOTH = "BOTH"
SEND_ONLY = "SEND_ONLY"
RECEIVE_ONLY = "RECEIVE_ONLY"


def segments_from_records(events):
    """記録だけから区間を作る。経路表は使わない。

    events: 辞書の一覧。各要素は "key"(自分)、"handed_to"(渡した相手)、
      "received_from"(受け取った相手) を持つ。無い欄は None。

    返り値は {"rows", "both", "send_only", "receive_only", "skipped"} の辞書。
    rows は {"from", "to", "count", "evidence"} の一覧。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない・★条件は ここに 在る）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import segments_from_records, BOTH, SEND_ONLY, RECEIVE_ONLY


def test_both_sides_make_one_confirmed_segment():
    """送りと受けが揃えば BOTH。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None},
          {"key": "B.b", "handed_to": None, "received_from": "A.a"}]
    r = segments_from_records(ev)
    assert r["rows"] == [{"from": "A.a", "to": "B.b", "count": 1, "evidence": BOTH}]
    assert r["both"] == 1


def test_send_only_is_kept():
    """送りだけでも 区間として残す。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None}]
    r = segments_from_records(ev)
    assert r["rows"][0]["evidence"] == SEND_ONLY
    assert r["send_only"] == 1
    assert r["both"] == 0


def test_receive_only_is_kept():
    """受けだけでも 区間として残す。"""
    ev = [{"key": "B.b", "handed_to": None, "received_from": "A.a"}]
    r = segments_from_records(ev)
    assert r["rows"][0] == {"from": "A.a", "to": "B.b", "count": 1, "evidence": RECEIVE_ONLY}
    assert r["receive_only"] == 1


def test_repeated_segment_is_one_row_with_a_count():
    """同じ区間が3回なら 1行で 件数 3。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None} for _ in range(3)]
    r = segments_from_records(ev)
    assert len(r["rows"]) == 1
    assert r["rows"][0]["count"] == 3


def test_missing_partner_is_skipped_and_counted():
    """相手が無い記録は 区間にしないが 数える。"""
    ev = [{"key": "A.a", "handed_to": None, "received_from": None}]
    r = segments_from_records(ev)
    assert r["rows"] == []
    assert r["skipped"] == 1


def test_empty_partner_is_also_skipped():
    """相手が空文字でも 同じ扱い。"""
    ev = [{"key": "A.a", "handed_to": "", "received_from": None}]
    r = segments_from_records(ev)
    assert r["rows"] == []
    assert r["skipped"] == 1


def test_self_to_self_is_kept():
    """自分から自分へも 残す。潰さない。"""
    ev = [{"key": "A.a", "handed_to": "A.a", "received_from": None}]
    r = segments_from_records(ev)
    assert r["rows"][0]["from"] == "A.a"
    assert r["rows"][0]["to"] == "A.a"


def test_sorted_by_count_then_names():
    """件数の多い順。同数なら from, to の昇順。"""
    ev = [{"key": "B.b", "handed_to": "C.c", "received_from": None},
          {"key": "A.a", "handed_to": "Z.z", "received_from": None},
          {"key": "A.a", "handed_to": "Z.z", "received_from": None}]
    r = segments_from_records(ev)
    assert [x["from"] for x in r["rows"]] == ["A.a", "B.b"]


def test_three_numbers_sum_to_the_row_count():
    """3つの数の合計は 区間の数と等しい。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None},
          {"key": "B.b", "handed_to": None, "received_from": "A.a"},
          {"key": "C.c", "handed_to": "D.d", "received_from": None},
          {"key": "E.e", "handed_to": None, "received_from": "F.f"}]
    r = segments_from_records(ev)
    assert r["both"] + r["send_only"] + r["receive_only"] == len(r["rows"])
    assert r["both"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None}]
    assert segments_from_records(ev) == segments_from_records(ev)


def test_result_has_all_five_keys():
    """5つのキーは どの場合も 欠けない。"""
    r = segments_from_records([])
    for k in ("rows", "both", "send_only", "receive_only", "skipped"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★★Claude・★★★これが 無いと この関数は 空を 返す）

```
★★★受け側の 1行 = ★★`received_from` を ★受け取った 側が 書く
   ―― ★★★いま 0件（★2026-08-12 から 変わっていない＝★★後退の 正体）
   ―― ★★書く場所 = ★★渡された 側の 入口（★★★送り側の `handoff_emit` と 対に する）
   ―― ★★★`route_table` から 引かない（★★引くと また 循環する＝★★これが 一番 大事）
★★行数を 報告し ★2DER の 実績に 数えない
```

## 6. ★★受入（★★★『進んだ』と 言える 条件・★数で）

```
★★① ★★`received_from` の 記録が ★★1件（★★★いま 0件）
★★② ★★`BOTH` の 区間が ★★1件（★★両側が 揃った＝★★★推測していない）
★★③ ★★その区間が ★★★経路表に 無い物（★★★新しく 見つけた＝★循環していない）
★★④ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増（★★`observed_edges` に 欄）
★★⑤ ★同じ問いを 2回 引いて 同じ
★★⑥（★私）★★`SEND_ONLY` と `RECEIVE_ONLY` の 件数を ★★両方 出す
   ―― ★理由 = ★★★片側だけの 物が どれだけ 在るかが ★次に 効く（★★0 に 押し込まない）
```

## 7. ★★言い方

```
★★『区間を 見つけた』と 書かない ―― ★★正しくは ★★『★両側 a ／ ★送りだけ b ／ ★受けだけ c』
★★★『自動アップデートが 動いた』と 書かない ―― ★★★経路表への 登録が 1件 出るまで
★★『調べる部品』を 6本目に しない ―― ★★★次に 数えるのは ★★『★表が 何行 増えたか』
```
