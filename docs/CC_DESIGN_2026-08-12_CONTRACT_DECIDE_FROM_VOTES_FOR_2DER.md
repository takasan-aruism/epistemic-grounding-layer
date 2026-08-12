開発者規律 確認済(v1.0)

# 【契約・2DER へ投げる1件】★票から 結論を 決める 純関数（★`decide_from_votes`）

宛: MGR（★封入と 投入は MGR）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-12 14:30 ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語**「★ついでなんでどうぞ。★★Claude体制を徐々になくす」／ MGR 契約（14:1x）

**★★worker に 届くのは 3つだけ** ―― ★骨格 ／ ★封印試験（★名前と docstring 込み）／ ★共通テンプレート。
**★∴ 条件は ★★試験に 書いた**（★下の依頼文は ★★worker に 届かない前提で 書いている）。

---

## 1. ★★場合の 列挙（★★走らせる前に 出す・★Taka 常設）

```
★① 3票 全会一致              → ★OK ／ final=その語 ／ disagreement=0
★② 3票 2対1                  → ★OK ／ final=NOT_DECIDED ／ disagreement=1
★③ 3票 1対1対1               → ★OK ／ final=NOT_DECIDED ／ disagreement=2
★★④ 2票 同じ（★期待3）       → ★★INCOMPLETE ／ ★★final=NOT_DECIDED ／ ★★★確定させない（★本命）
★⑤ 1票だけ                   → ★INCOMPLETE ／ final=NOT_DECIDED
★⑥ 0票                       → ★INCOMPLETE ／ votes_got=0
★⑦ 期待数を 5 にした時（★3票）→ ★INCOMPLETE
★★⑧（★私が 1つ 足す）★期待5 で ★5票 3対2 → ★OK ／ NOT_DECIDED ／ disagreement=2
   ―― ★理由 = ★★⑦だけだと ★`expected` が ★★『満たない側』しか 通らない
```

## 2. ★★骨格（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
NOT_DECIDED = "NOT_DECIDED"
OK = "OK"
INCOMPLETE = "INCOMPLETE"


def decide_from_votes(votes, expected=3):
    """票の一覧から結論を1つ決める。

    votes: 各票の答え(文字列)の一覧。
    expected: 期待する票数(既定3)。

    返り値は dict で、キーは votes_got / final / disagreement / status。
    votes_got は受け取った票の数。
    final は決まった語、または NOT_DECIDED。
    disagreement は最多数でない票の数。
    status は OK または INCOMPLETE。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 3. ★★封印試験（★★1バイトも 変えない・★条件は ここに 書いてある）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import decide_from_votes, NOT_DECIDED, OK, INCOMPLETE


def test_three_votes_all_same_decides():
    """3票が全て同じなら決まる。disagreement は 0。"""
    r = decide_from_votes(["ROUTE", "ROUTE", "ROUTE"])
    assert r["votes_got"] == 3
    assert r["final"] == "ROUTE"
    assert r["disagreement"] == 0
    assert r["status"] == OK


def test_three_votes_two_to_one_does_not_decide():
    """3票が2対1なら決めない。多数派の語を final にしない。"""
    r = decide_from_votes(["ROUTE", "BORROW", "BORROW"])
    assert r["votes_got"] == 3
    assert r["final"] == NOT_DECIDED
    assert r["disagreement"] == 1
    assert r["status"] == OK


def test_three_votes_all_different_does_not_decide():
    """3票が全て違うなら決めない。disagreement は 2。"""
    r = decide_from_votes(["ROUTE", "BORROW", "NOT_DECIDED"])
    assert r["votes_got"] == 3
    assert r["final"] == NOT_DECIDED
    assert r["disagreement"] == 2
    assert r["status"] == OK


def test_two_votes_same_is_incomplete_and_does_not_decide():
    """票が期待数に満たないとき、2票が同じでも決めない。status は INCOMPLETE。"""
    r = decide_from_votes(["ROUTE", "ROUTE"])
    assert r["votes_got"] == 2
    assert r["final"] == NOT_DECIDED
    assert r["status"] == INCOMPLETE


def test_one_vote_is_incomplete():
    """1票だけなら INCOMPLETE で、決めない。"""
    r = decide_from_votes(["ROUTE"])
    assert r["votes_got"] == 1
    assert r["final"] == NOT_DECIDED
    assert r["status"] == INCOMPLETE


def test_no_votes_is_incomplete():
    """票が無いなら votes_got は 0 で INCOMPLETE。"""
    r = decide_from_votes([])
    assert r["votes_got"] == 0
    assert r["final"] == NOT_DECIDED
    assert r["status"] == INCOMPLETE


def test_expected_five_with_three_votes_is_incomplete():
    """期待数を5にすると、3票では INCOMPLETE になる。"""
    r = decide_from_votes(["ROUTE", "ROUTE", "ROUTE"], expected=5)
    assert r["votes_got"] == 3
    assert r["final"] == NOT_DECIDED
    assert r["status"] == INCOMPLETE


def test_expected_five_with_five_votes_split_does_not_decide():
    """期待数5で5票が3対2なら、票は揃っているが決めない。disagreement は 2。"""
    r = decide_from_votes(["ROUTE", "ROUTE", "ROUTE", "BORROW", "BORROW"], expected=5)
    assert r["votes_got"] == 5
    assert r["final"] == NOT_DECIDED
    assert r["disagreement"] == 2
    assert r["status"] == OK
<<<2DER:END>>>
```

## 4. ★★測る物（★★これが 目的＝★★止まっても 失敗では ない）

```
★① 2DER が ★どの工程まで 行ったか（★CREATE / PLAN / GENERATE / AUDIT / …）
★★② 止まったなら ★★止まった工程と ★理由（★逐語）
★★③ ★★Claude が 触った回数（★★0回で 通れば 最良）
★④ 所要
★★★止まった時に ★Claude が 代わりに 書かない ―― ★書くなら
   ★★『2DER は ここで 止まり ／ 私が 書いた』と ★分けて 記録する（★MGR 禁止条項）
```

## 5. ★注意

```
★★`impl.py` 1本で 完結する（★既存ファイルを 書き換えない）＝ ★2DER の 雛形に 合う形
★★配置は Claude が 行う（★規律 §1＝★検査して 配置するだけ）―― ★★但し ★今回は
   ★★★通ってから 決める（★★先に 配置先を 書くと ★『2DER が 作った』の 実測が 濁る）
★★封印試験は ★★1バイトも 変えない（★変えたら 契約が 壊れる）
```
