開発者規律 確認済(v1.0)

# 【契約 v2 ＋ ★私の 見立ての 訂正】★★骨格から **定数を 外す** ―― ★落ちているのは そこ

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 17:5x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-14_CONTRACT_SEGMENTS_FROM_RECORDS.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 17:38**「★同じ 落ち方が 2件目 ／ ★走行を またいで 数えたら ★形が 出た」

---

## 1. ★★★私の 見立ての 訂正（★先に 書く）

```
★★私は 14:3x に 書いた = ★『★docstring が 長いほど 落ちている（★★仮説と 書く・★3点しか 無い）』
★★★今回 = ★docstring は ★短い（★v2 の 形）／ ★★それでも 落ちた ＝ ★★★見立ては ★一部 外れ

★★★走行を またいで 数え直す（★★MGR の 逐語『★形が 出た』）
   ★`needs_refresh`          … 定数 ★0個 → ★★通った
   ★`unregistered_keys`      … 定数 ★0個 → ★★通った
   ★`count_by_component`     … 定数 ★1個 → ★★通った（★一発63秒）
   ★`decide_tick`            … 定数 ★3個 → ★★1回 落ちて（★861）から 通った
   ★`observed_from_counts`   … 定数 ★3個 → ★★2回 落ちた（★798）→ ★docstring を 削って 通った
   ★`segments_from_records`  … 定数 ★3個 ＋ ★短い docstring → ★★★落ちた（★★★今回）
★★★∴ ★効いていたのは ★★『骨格の 総量』であって ★docstring だけでは ない
   ―― ★★定数3行も ★骨格の 一部 ＝ ★★★worker が 落とすのは ★いつも ★先頭の 定数
```

## 2. ★★直す（★★★定数を 骨格から 外す）

```
★★★語は 文字列の まま ★★封印試験に 書く（★★試験が 語を 固定する＝★機構に 通じる 語は 変わらない）
★★∴ ★worker が 書くのは ★★関数 1つだけ ＝ ★★★落とす 物が 無い
★★★これは 本日の 原則の 延長 = ★★『★骨格を 小さく する』（★条件は 試験に 在る）

★★★封印試験は 変える（★★★前の 走行と 比べられなく なるが ★★合格した 版が 無い ∴ ★失う物が 無い）
   ―― ★★合格版が 在る 契約では ★試験を 変えない（★★この 区別を 残す）
```

## 3. ★★骨格 v2（★★★定数 0個・★docstring 短い）

```
<<<2DER:SKELETON>>>
def segments_from_records(events):
    """記録だけから区間を作る。経路表は使わない。

    events: 辞書の一覧。各要素は "key"(自分)、"handed_to"(渡した相手)、
      "received_from"(受け取った相手) を持つ。無い欄は None。

    返り値は {"rows", "both", "send_only", "receive_only", "skipped"} の辞書。
    rows は {"from", "to", "count", "evidence"} の一覧。
    evidence は "BOTH" / "SEND_ONLY" / "RECEIVE_ONLY" のどれか。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★★import は 関数 1つだけ）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import segments_from_records


def test_both_sides_make_one_confirmed_segment():
    """送りと受けが揃えば BOTH。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None},
          {"key": "B.b", "handed_to": None, "received_from": "A.a"}]
    r = segments_from_records(ev)
    assert r["rows"] == [{"from": "A.a", "to": "B.b", "count": 1, "evidence": "BOTH"}]
    assert r["both"] == 1


def test_send_only_is_kept():
    """送りだけでも 区間として残す。"""
    ev = [{"key": "A.a", "handed_to": "B.b", "received_from": None}]
    r = segments_from_records(ev)
    assert r["rows"][0]["evidence"] == "SEND_ONLY"
    assert r["send_only"] == 1
    assert r["both"] == 0


def test_receive_only_is_kept():
    """受けだけでも 区間として残す。"""
    ev = [{"key": "B.b", "handed_to": None, "received_from": "A.a"}]
    r = segments_from_records(ev)
    assert r["rows"][0] == {"from": "A.a", "to": "B.b", "count": 1, "evidence": "RECEIVE_ONLY"}
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

## 5. ★★受入（★★★見立ての 検算を 兼ねる）

```
★★① ★★`ImportError` が ★出ない（★★★import する 名前が 1つ だけ）
★★② ★★`skeleton_missing` = ★★0
★★③ ★★★落ちた場合 ―― ★理由を 書く
   ―― ★★また 骨格が 落ちたなら = ★★★定数では なかった（★見立てが また 外れ＝★そう 書く）
   ―― ★★試験の 不合格なら = ★★★中身の 話（★★形の 話は 終わり）
★★④ ★LLM 呼び出し以外 0 ／ ★契約は 1本（★割っていない）
★★⑤（★私）★★これが 通ったら ★★『骨格に 定数を 置かない』を ★★★契約の 書き方に 足す
```

## 6. ★★足場（★★★Claude・★これが 無いと この関数は 空を 返す）

```
★★★`received_from` を ★受け取った側が 書く 1行（★★いま 0件＝★2026-08-12 から 変わっていない）
★★★`route_table` から 引かない（★★引くと また 循環）／ ★行数を 報告し ★実績に 数えない
```

## 7. ★★言い方

```
★★★『docstring が 原因だった』と ★書かない（★★私の 見立ては ★一部 外れ＝★★今 訂正した）
★★『2件目も 落ちた』で 止めない ―― ★★★同じ 落ち方が 2件 ＝ ★★形が 見えた（★これは 収穫）
★★★『自動アップデートが 動いた』と 書かない ―― ★★経路表への 登録が 1件 出るまで
```
