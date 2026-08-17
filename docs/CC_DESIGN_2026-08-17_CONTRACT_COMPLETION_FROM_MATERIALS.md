# 【契約・1本】★材料から **4つの一覧を作る** ―― ★★`completion_from_materials`（★★口を叩かない純関数）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-17 19:0x ／ 台帳: `ITEM-2DER-EVO-0067`
出所: **MGR 18:52**（★Taka 指示＝最初の1件は「Domain 完了条件の生成」だけ ／ ★場合5つ ／ ★出してはいけない結果4つ ／ ★「私は中身を書かない」）
開発者規律 確認済（2DER_DEVELOPER_DISCIPLINE_v1.0）／ 運用 v0.3 確認済

---

## 0. ★先に確かめた（★前提を疑わずに書くのが本日の穴だったので）

```
★材料の口 = ★`GET /api/control` の ★既定では ★observed_edges は ★★空(0欄)
   ―― ★これを見て『材料が無い』とは書かない(★私の前科)
   ―― ★実物 = ★`webui.py:968` ★`if "observed_edges" in _want`
      ＝ ★★`?include=observed_edges` で ★名指しした時だけ 計算する(★重い物は既定で計算しない設計)
★★∴ ★材料は 在る。★但し ★★『既定の1発では出ない』＝ ★呼び手は include を付ける
★★★実測(★include を付けて引き直した) = ★observed_edges ★56欄 ／ ★★7つ とも 在る
   ―― ★`gap_table`(2) ／ `unregistered`(3) ／ `route_facts`(5) ／ `self_check_signals`(5)
      ／ `relay_chain`(11) ／ `contract_versions`(5) ／ `identity`(4) ★＋ `end_numbers`(12)
   ―― ★★あなたの『7つとも口から引ける』は ★正しい(★私も別に引いて一致)
★★★この契約は ★口を叩かない ＝ ★材料は ★呼び手が引いて ★辞書で渡す(★MGR 指示の芯)
   ―― ★理由 = ★口の形が変わっても ★この部品は壊れない ／ ★試験が外部に依存しない
```

## 1. ★★設計の芯（★これだけは崩さない）

```
★★①作らない = ★★文言を1文字も生まない。★出す名前は ★★材料に在った名前だけ
   ―― ★『完了条件を書く』のではなく ★★『材料に在る物を4つに仕分ける』
★★②隠さない = ★★使った材料の ★名前と件数を必ず返す(★総数・取得数・未取得数)
★★③埋めない = ★★欠けたら ★名前を出して止まる(★推測で補わない)
★★④決定論 = ★LLM 0回 ／ ★同じ入力は同じ出力 ／ ★並びは昇順で固定
```

## 2. ★★場合の列挙（★あなたの5つ ／ ★走らせる前に宣言）

```
★★① 材料が揃う                    → ★4つの一覧 ＋ ★内訳を出す
★★② 材料が1つでも欠ける            → ★`missing_material`（★欠けた名前を昇順で）
★★③ 材料が空(0件)                 → ★★止まらない = ★空の一覧を返す
      ★★材料が取れなかった(値が無い) → ★★`material_unavailable`
      ―― ★★『0件』と『取れなかった』は ★★別の語(★あなたの③)
★★④ 上限つきの材料                → ★★総数・取得数・未取得数を併記(★黙って切らない)
★★⑤ 同じ材料から2回                → ★★同じ答え
★★⑥（★私が足した1つ）仕分けの語が4つ以外 → ★`unknown_role`（★その名前を出す）
      ―― ★理由 = ★★これが無いと ★知らない語を ★どれかの一覧に ★黙って落とす
```

## 3. ★★出してはいけない結果（★あなたの4つ ／ ★★試験で縛る）

```
★(ア) 人が書いた文言が混ざる   → ★試験『出力の要素は全部 入力に在った名前』
★(イ) 材料の名前が出ない      → ★試験『内訳に全ての材料名が在る』
★(ウ) 上限で黙って切る        → ★試験『未取得数が出る』
★(エ) 欠けた材料を埋めて進む   → ★試験『止まった時は中身を返さない』
```

## 4. ★★骨格（★★定数 0個 ／ ★★口を叩かない）

<<<2DER:SKELETON>>>
def completion_from_materials(materials, required):
    """材料を4つの一覧に仕分ける。名前は材料に在る物だけを使い、文言を足さない。

    materials: 名前 -> 材料 の辞書。材料は {"items": 一覧, "total": 整数} の辞書か None。
      items の要素は {"name": 文字列, "role": 文字列} の辞書。
    required: 必ず在るべき材料の名前の一覧。

    返り値は {"expected", "prohibited", "prechecks", "completion",
    "materials_used", "reason", "names"} の辞書。7つのキーはどの場合も欠けない。

    次の順に調べ、当たった時点で止まる。
      1. required の名前で materials に無い物があれば reason は "missing_material"。
      2. materials の値が None の物があれば reason は "material_unavailable"。
      3. items の role が4つの語のどれでもなければ reason は "unknown_role"。
    4つの語は "expected" と "prohibited" と "precheck" と "completion"。
    止まった時は expected と prohibited と prechecks と completion と materials_used を
    None にし、names に該当する名前を昇順で入れる。
    1 と 2 に当たる名前は材料の名前、3 に当たる名前は items の name。

    止まらない時は reason を None、names を空の一覧にして次を作る。
    expected は role が "expected" の name を昇順に並べた一覧。
    prohibited は "prohibited"、prechecks は "precheck"、completion は "completion" で同じ。
    同じ名前が複数あればその数だけ並べる。
    materials_used は 材料の名前 -> {"total", "used", "not_fetched"} の辞書。
      used は items の数。total は材料の "total"。
      not_fetched は total から used を引いた数。負になるときは0。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 5. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import completion_from_materials


def m(items, total=None):
    return {"items": items, "total": len(items) if total is None else total}


A = {"gap": m([{"name": "g1", "role": "expected"},
               {"name": "g2", "role": "prohibited"}]),
     "route": m([{"name": "r1", "role": "precheck"},
                 {"name": "r2", "role": "completion"}])}


def test_it_sorts_the_materials_into_four():
    """材料が揃えば4つに仕分ける。"""
    r = completion_from_materials(A, ["gap", "route"])
    assert r["reason"] is None
    assert r["expected"] == ["g1"]
    assert r["prohibited"] == ["g2"]
    assert r["prechecks"] == ["r1"]
    assert r["completion"] == ["r2"]


def test_every_name_came_from_the_materials():
    """出す名前は材料に在った物だけ。文言を足さない。"""
    r = completion_from_materials(A, ["gap", "route"])
    out = r["expected"] + r["prohibited"] + r["prechecks"] + r["completion"]
    assert sorted(out) == ["g1", "g2", "r1", "r2"]


def test_the_material_names_are_always_reported():
    """使った材料の名前が出る。"""
    r = completion_from_materials(A, ["gap", "route"])
    assert sorted(r["materials_used"]) == ["gap", "route"]
    assert r["materials_used"]["gap"]["used"] == 2


def test_a_capped_material_shows_what_was_not_fetched():
    """上限つきなら未取得数が出る。黙って切らない。"""
    d = {"gap": m([{"name": "g1", "role": "expected"}], total=10)}
    r = completion_from_materials(d, ["gap"])
    assert r["materials_used"]["gap"]["total"] == 10
    assert r["materials_used"]["gap"]["used"] == 1
    assert r["materials_used"]["gap"]["not_fetched"] == 9


def test_not_fetched_is_never_negative():
    """総数が取得数より小さくても負にしない。"""
    d = {"gap": m([{"name": "g1", "role": "expected"}], total=0)}
    r = completion_from_materials(d, ["gap"])
    assert r["materials_used"]["gap"]["not_fetched"] == 0


def test_an_empty_material_is_not_an_error():
    """0件は空の一覧。止まらない。"""
    d = {"gap": m([])}
    r = completion_from_materials(d, ["gap"])
    assert r["reason"] is None
    assert r["expected"] == []
    assert r["materials_used"]["gap"]["used"] == 0


def test_an_unavailable_material_is_a_different_word():
    """取れなかった材料は0件と別の語。"""
    d = {"gap": None}
    r = completion_from_materials(d, ["gap"])
    assert r["reason"] == "material_unavailable"
    assert r["names"] == ["gap"]


def test_a_missing_material_stops():
    """材料が欠けたら止まる。推測で埋めない。"""
    r = completion_from_materials({"gap": m([])}, ["gap", "route"])
    assert r["reason"] == "missing_material"
    assert r["names"] == ["route"]


def test_missing_names_are_sorted():
    """欠けた名前は昇順。"""
    r = completion_from_materials({}, ["route", "gap"])
    assert r["names"] == ["gap", "route"]


def test_an_unknown_role_stops():
    """知らない仕分けの語では止まる。黙って落とさない。"""
    d = {"gap": m([{"name": "g1", "role": "somethingelse"}])}
    r = completion_from_materials(d, ["gap"])
    assert r["reason"] == "unknown_role"
    assert r["names"] == ["g1"]


def test_missing_is_checked_before_unavailable():
    """調べる順は決まっている。"""
    r = completion_from_materials({"gap": None}, ["gap", "route"])
    assert r["reason"] == "missing_material"


def test_a_stopped_result_has_no_content():
    """止まったときは中身を返さない。"""
    r = completion_from_materials({}, ["gap"])
    assert r["expected"] is None
    assert r["prohibited"] is None
    assert r["prechecks"] is None
    assert r["completion"] is None
    assert r["materials_used"] is None


def test_the_lists_are_sorted():
    """並びは昇順で固定。"""
    d = {"gap": m([{"name": "b", "role": "expected"},
                   {"name": "a", "role": "expected"}])}
    r = completion_from_materials(d, ["gap"])
    assert r["expected"] == ["a", "b"]


def test_duplicates_are_kept():
    """同じ名前が2つあれば2つ並ぶ。数を変えない。"""
    d = {"gap": m([{"name": "a", "role": "expected"},
                   {"name": "a", "role": "expected"}])}
    r = completion_from_materials(d, ["gap"])
    assert r["expected"] == ["a", "a"]


def test_same_input_twice_gives_the_same_answer():
    """同じ材料から2回作ると同じ答えになる。"""
    assert completion_from_materials(A, ["gap", "route"]) == completion_from_materials(A, ["gap", "route"])


def test_result_has_all_seven_keys():
    """7つのキーはどの場合も欠けない。"""
    r = completion_from_materials({}, ["gap"])
    for k in ("expected", "prohibited", "prechecks", "completion",
              "materials_used", "reason", "names"):
        assert k in r


def test_no_required_material_still_works():
    """必ず在るべき材料が無い指定でも動く。"""
    r = completion_from_materials(A, [])
    assert r["reason"] is None
    assert sorted(r["materials_used"]) == ["gap", "route"]
<<<2DER:END>>>

## 6. ★★足場（★MGR ／ ★口 0増）

```
★材料を引くのは ★★呼び手(★`?include=observed_edges` を付ける ／ ★§0 の実測)
★★この部品は ★口を1つも叩かない = ★試験が外部に依存しない = ★★いつ走らせても同じ
★★MGR は 骨格・封印試験を ★1行も手で書かない(★書いたら実験が不成立)
```

## 7. ★★受入（★あなたの3つ ＋ ★私から2つ）

```
★★① 機械が4つを生成する(★実案件1件)
★★② 別主体(★私)が ★同じ材料から独立に検査し ★『一致 ／ 不一致 ／ ★調べた母数』を出す
★★③ 人が内容を書いていない
★★★④(★私) ★止まった時は ★理由の語が出る(★4語のどれか)＋ ★★名前が出る
   ―― ★『どこで止まったか』が1回で分かる(★本日1時間探した型の予防)
★★★⑤(★私) ★`materials_used` に ★★全ての材料名が出る
   ―― ★これが崩れたら ★★分母を隠している = ★設計の芯が外れている
★★⑥ `skeleton_missing` = 0 ／ ★封印試験 17本 passed ／ ★定数 0個 ／ ★LLM 0回
```

## 8. ★★やらないこと

```
★★★完了条件の文言を生成しない(★仕分けるだけ ／ ★生成は次の話)
★★★材料を この部品の中から引かない(★純関数を壊さない)
★★見積り ／ 分割 ／ 資源管理は 作らない(★Taka=後)
★★★『Domain Manager が設計できるようになった』と書かない
   ―― ★正しくは ★『★材料から4つを ★機械が仕分けた件数 ★N ／ ★人が書いた文言 ★0』
```
