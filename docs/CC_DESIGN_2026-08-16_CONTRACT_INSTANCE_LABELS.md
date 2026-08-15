開発者規律 確認済(v1.0)

# 【契約・1本】★どの 入口が 書いたかを **1語で 出す** ―― ★★`instance_labels`（★推測しない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-16 08:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 08:07**（★指示1＝`instance=` を 本文に 1語 受ける ／ ★台帳の 記入の 頭に 出す ／ ★受入＝★今回の 2入口を 実例に ★誤帰属 0）

---

## 0. ★★何が 起きたから これが 要るのか（★★実例を 先に）

```
★★2026-08-16 未明 = ★★`発: DESIGN` を 名乗る 文書が ★★2つの 入口から 出た
   ―― ★★★私（この入口）は ★2件とも ★書いていない
   ―― ★★MGR が 出所を 解いた（★別入口からの 本物）＝ ★★★人が 1件ずつ 解いた
★★★∴ ★次に 同じ事が 起きた 時に ★★人が また 解く = ★Claude が 減らない（★Taka §17）
★★★∴ ★書いた 側が ★★書く時に 名乗る（★★後から 復元しない＝★identity と 同じ 型）
```

## 1. ★★★『名乗っていない』と『知らない 名前』を **混ぜない**（★★これが 本体）

```
★★★本日 4回 出た 型 = ★★2つの 違う 事を ★1つとして 数える
★★∴ ★この部品も ★★★3語に 分ける:
   ★`declared`     … ★欄が 在り ／ ★★呼び手が 渡した 一覧の 中に 在る
   ★`unknown`      … ★★欄が 無い ／ 空（★★★推測しない・★★『たぶん DESIGN』を 作らない）
   ★`unregistered` … ★★欄は 在るが ★一覧に 無い（★★★語は そのまま 返す＝★消さない）
★★★`unknown` と `unregistered` を 同じ数に すると ―― ★★『登録の 漏れ』と『名乗りの 漏れ』が 見えなくなる
   ―― ★★直し方が 別（★前者＝一覧に 足す ／ ★後者＝呼び手に 名乗らせる）
★★★語の 一覧は ★呼び手が 渡す（★★部品に 書かない＝★正本を 2つに しない・★状態名の 教訓）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 欄が 在り 一覧に 在る          → ★`declared`
★★② 欄が 無い                      → ★`unknown` ／ ★`instance` は None
★★③ 欄が 空                        → ★`unknown`
★★④ 欄が 空白だけ                  → ★`unknown`
★★⑤ 欄は 在るが 一覧に 無い        → ★★`unregistered`（★語は そのまま）
★★⑥ 一覧が 空                      → ★★欄が 在れば すべて `unregistered`
★★⑦ 前後の 空白は 落とす
★★⑧ ★★★大文字小文字を 変えない（★★別名に しない＝★★勝手に 揃えない）
★★⑨ `by_status` は ★3語 全部 キーを 持つ（★0件でも）
★★⑩ 並びは ★渡された 順
★★⑪ 同じ入力を 2回 渡して ★同じ
★⑫ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個 ／ ★★入口の 名前を 1つも 書かない）

<<<2DER:SKELETON>>>
def instance_labels(rows, known):
    """記入ごとに、どの入口が書いたかを1語で出す。分からないものを推測しない。

    rows: 辞書の一覧。各要素は {"id", "instance"}。instance の欄は無いこともある。
    known: 使ってよい入口の名前の一覧。呼び手が渡す。

    返り値は {"rows", "by_status", "checked"} の辞書。

    rows は渡された順。各要素は {"id", "instance", "status"}。
    instance の欄が無い、値が空、または空白だけのときは
      status は "unknown"、instance は None。
    それ以外は前後の空白を落とした文字列を instance にする。大文字小文字は変えない。
      その文字列が known の中に在れば status は "declared"。
      無ければ status は "unregistered"。instance はその文字列のまま。
    by_status は "declared" "unknown" "unregistered" の3語を全部キーに持ち、その数を値にする。
    checked は rows の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import instance_labels


def test_known_name_is_declared():
    """一覧に在る名前は declared。"""
    r = instance_labels([{"id": "1", "instance": "DESIGN"}], ["DESIGN"])
    assert r["rows"][0]["status"] == "declared"
    assert r["rows"][0]["instance"] == "DESIGN"


def test_missing_field_is_unknown():
    """欄が無ければ unknown。推測しない。"""
    r = instance_labels([{"id": "1"}], ["DESIGN"])
    assert r["rows"][0]["status"] == "unknown"
    assert r["rows"][0]["instance"] is None


def test_empty_value_is_unknown():
    """空なら unknown。"""
    r = instance_labels([{"id": "1", "instance": ""}], ["DESIGN"])
    assert r["rows"][0]["status"] == "unknown"


def test_blank_value_is_unknown():
    """空白だけでも unknown。"""
    r = instance_labels([{"id": "1", "instance": "   "}], ["DESIGN"])
    assert r["rows"][0]["status"] == "unknown"
    assert r["rows"][0]["instance"] is None


def test_unknown_name_is_its_own_word():
    """一覧に無い名前は unregistered。unknown と混ぜない。"""
    r = instance_labels([{"id": "1", "instance": "WATCHER"}], ["DESIGN"])
    assert r["rows"][0]["status"] == "unregistered"
    assert r["rows"][0]["instance"] == "WATCHER"


def test_empty_known_makes_everything_unregistered():
    """一覧が空なら、欄が在るものは全て unregistered。"""
    r = instance_labels([{"id": "1", "instance": "DESIGN"}], [])
    assert r["rows"][0]["status"] == "unregistered"


def test_surrounding_spaces_are_dropped():
    """前後の空白は落とす。"""
    r = instance_labels([{"id": "1", "instance": "  DESIGN  "}], ["DESIGN"])
    assert r["rows"][0]["status"] == "declared"
    assert r["rows"][0]["instance"] == "DESIGN"


def test_case_is_kept_as_it_is():
    """大文字小文字を変えない。別名にしない。"""
    r = instance_labels([{"id": "1", "instance": "design"}], ["DESIGN"])
    assert r["rows"][0]["instance"] == "design"
    assert r["rows"][0]["status"] == "unregistered"


def test_by_status_has_all_three_words():
    """3語すべてキーを持つ。0件でも欄を消さない。"""
    r = instance_labels([], ["DESIGN"])
    assert sorted(r["by_status"].keys()) == ["declared", "unknown", "unregistered"]
    assert set(r["by_status"].values()) == {0}


def test_rows_keep_the_given_order():
    """並びは渡された順のまま。"""
    given = [{"id": "B"}, {"id": "A", "instance": "DESIGN"}]
    r = instance_labels(given, ["DESIGN"])
    assert [x["id"] for x in r["rows"]] == ["B", "A"]


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    g = [{"id": "1", "instance": "DESIGN"}]
    assert instance_labels(g, ["DESIGN"]) == instance_labels(g, ["DESIGN"])


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = instance_labels([], [])
    for k in ("rows", "by_status", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★①`/api/submit` の 本文の `instance` を ★そのまま 台帳の 欄へ 渡す（★★中身を 直さない）
★②記入の 頭に 出す（★★既存の 記入の 頭＝★新しい 欄を 作らない）
★★`known` = ★★呼び手が 渡す（★★★入口の 一覧の 正本は ★1つだけ＝★どこに 置くかは ★MGR）
★★出す口 = ★既存 include に ★欄を 1つ
```

## 6. ★★受入（★★★いま 0 が 出るのが 正しい）

```
★★① `by_status` の 3語が 出る（★★0件でも）
★★★② ★★いま 引くと ★★ほぼ 全部 `unknown` の はず
   ―― ★理由 = ★★★まだ 誰も 名乗っていない（★★これから 名乗った 分だけ 減る）
   ―― ★★★『0 / N』を 隠さない（★identity 1/87 と 同じ 書き方）
★★③ ★★今回の 2入口を 実例に する
   ―― ★★この入口が 名乗れば ★`declared` ★1
   ―― ★★もう一方が 名乗れば ★`declared` ★2 ／ ★名乗らなければ ★`unknown` の まま
   ―― ★★★『誤帰属 0』は ★★★`unknown` が 0 に なって 初めて 言える（★★いま 言わない）
★★④ `unregistered` が 出たら ★★★一覧に 足すか 決める（★★★勝手に 揃えない）
★★⑤ `skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★名乗っていない 記入を 推測で 埋めない（★★『たぶん DESIGN』を 作らない）
★★★大文字小文字を 揃えない（★★★勝手に 揃えると ★別物が 1つに 潰れる＝★本日の 型）
★★入口の 名前を ★部品に 書かない（★★正本を 2つに しない）
★★★『誤帰属が 消えた』と 書かない ―― ★★正しくは ★★『★`unknown` が ★N 件』
```
