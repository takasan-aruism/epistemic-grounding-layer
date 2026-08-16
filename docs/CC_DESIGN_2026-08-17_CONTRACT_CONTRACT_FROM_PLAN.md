# 【契約・1本】★PLAN から **契約の 文字列を 組む** ―― ★★`contract_from_plan`（★★作らずに 使う）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-17 05:2x ／ 台帳: `ITEM-2DER-EVO-0067`
出所: **MGR 04:56**（★場合 5つ ／ ★出してはいけない 結果 3つ ／ ★★『私は 書かない』）／ **Taka 承認**（★逐語『OK』＝★契約の 中身を 2DER が 埋める）

---

## 0. ★★★あなたの ⑤の ままでは **全件 止まる**（★★先に 実測）

```
★★あなたの 入力 = ★`requirement` ／ `target_file` ／ `test_plan` ／ `completion_criteria`
★★あなたの ⑤ = ★『★関数名が 決められない → 止まる（★推測で 名前を 作らない）』
★★★私の 実測 = ★PLAN の 欄に ★★関数名の 欄は ★★★無い
   ―― ★探した 範囲 = ★`twoder/build_planner.py:38-52`（★PLAN の 欄の 全部）／ ★`dw/plan_template.py`
   ―― ★`function_name` ／ `func_name` ／ `"function"` = ★★0件
★★★∴ ★★どの PLAN も ★★⑤で 止まる ＝ ★★★受入（★新規 1件で 通す）は ★成り立たない

★★★救う 材料は 在る = ★★`test_body`
   ―― ★★`build_planner.py:162` 逐語 = ★『complete python source of a self-contained test that
      **imports/execs the tool**』
   ―― ★★`:308` 逐語 = ★`plan_ok` は ★`test_plan` ＋ ★`test_body` ＋ ★`test_file` を ★★必須に している
   ―― ★★★∴ ★`test_body` は ★★必ず 在り ／ ★★関数名を ★構文として 含んでいる
★★★∴ ★入力に ★`test_body` を 1つ 足す（★★推測では なく ★★★既に 在る 材料から 取り出す）
```

## 1. ★★★作らずに 使う（★★これが 設計の 芯）

```
★★`immutable_tests` = ★★★`test_body` を ★そのまま（★★1文字も 変えない ／ ★組み立てない）
   ―― ★理由 = ★★既に『完全な 試験の source』＝ ★★★作り直すと ★別物に なる
★★`skeleton` = ★★3つを 並べるだけ
   ―― ★①`def <名前>(<引数>):`   … ★★`test_body` から 取り出す
   ―― ★②`"""<requirement の 1行>"""` … ★★PLAN の 文を そのまま（★短く 1行）
   ―― ★③`<<<FILL: ここに実装>>>`  … ★★固定
★★★組めない 時は ★何も 返さない（★理由の 語だけ）
```

## 2. ★★場合の 列挙（★★あなたの 5つ ／ ★★①だけ 材料を 足した）

```
★★① 材料が 揃う                          → ★組む（`reason` は None）
★★② `requirement` が 空                  → ★`no_requirement`
★★③ `test_plan` が 0件                   → ★`no_test_plan`（★★試験の 無い 契約を 作らない）
★★④ `target_file` が `impl.py` 以外       → ★`unexpected_target`（★いまの 経路は 1ファイル）
★★★⑤ `test_body` から 名前が 取り出せない → ★`no_function_name`（★★★推測で 作らない）
★★⑥ `test_body` に `def test_` が 無い    → ★`no_test_function`（★★門が 弾く 物を 作らない）
★★⑦ 同じ入力を 2回 渡して ★同じ
★⑧ キーは ★どの場合も 欠けない

★★★出してはいけない 結果（★★試験で 縛る）
   ★(ア)`def test_` が 1つも 無い 封印試験を 出す
   ★(イ)骨格に `<<<FILL` が 無い
   ★(ウ)止まると 言いながら 中身を 返す
```

## 3. ★★骨格（★★定数 0個 ／ ★★★組み立てない）

<<<2DER:SKELETON>>>
def contract_from_plan(requirement, target_file, test_plan, test_body):
    """実装計画から、契約の文字列を組む。試験は作らず、渡された物をそのまま使う。

    requirement: 何を作るかの1文。文字列。
    target_file: 作る python ファイルの名前。文字列。
    test_plan: 試験の一覧。文字列の一覧。
    test_body: 試験の本文。完全な python の source。文字列。

    返り値は {"skeleton", "immutable_tests", "reason"} の辞書。

    requirement の前後の空白を落とした形が空なら
      skeleton と immutable_tests は None、reason は "no_requirement"。
    test_plan が空の一覧なら None を返し、reason は "no_test_plan"。
    target_file の前後の空白を落とした形が "impl.py" でなければ None を返し、
      reason は "unexpected_target"。
    test_body の中に "def test_" という文字が無ければ None を返し、
      reason は "no_test_function"。

    test_body の中から関数の名前と引数を取り出す。
    "from impl import " で始まる行を探し、その後ろの名前を関数の名前にする。
    その名前が無ければ None を返し、reason は "no_function_name"。
    次に、その名前の後ろに丸括弧が続く箇所を test_body の中から探す。
    最初に見つかった箇所の丸括弧の中を、括弧の対応を数えて取り出す。
    その中身をいちばん外側の読点で区切った数を、引数の数にする。中身が空なら0。
    見つからなければ None を返し、reason は "no_function_name"。

    作れるときは次を返す。
    immutable_tests は test_body をそのまま。1文字も変えない。
    skeleton は次の3行を改行で繋いだ文字列。
      1行目は "def " と名前と "(" と引数と "):" を繋いだもの。
        引数は a, b, c … の順に、引数の数だけ ", " で繋いだ名前にする。
      2行目は空白4つと三重引用符と requirement の1行と三重引用符。
      3行目は空白4つと "<<<FILL: ここに実装>>>"。
    reason は作れたとき None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import contract_from_plan

BODY = 'from impl import add_two\n\n\ndef test_it():\n    assert add_two(1, 2) == 3\n'


def test_it_builds_from_the_plan():
    """材料が揃えば組む。"""
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], BODY)
    assert r["reason"] is None
    assert r["skeleton"].startswith("def add_two(a, b):")


def test_the_tests_are_passed_through_unchanged():
    """試験は作らない。渡された物をそのまま返す。"""
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], BODY)
    assert r["immutable_tests"] == BODY


def test_the_skeleton_keeps_the_fill_marker():
    """骨格には埋める場所が残る。"""
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], BODY)
    assert "<<<FILL: ここに実装>>>" in r["skeleton"]


def test_the_requirement_becomes_the_docstring():
    """requirement が説明文になる。"""
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], BODY)
    assert "2つ足す" in r["skeleton"]


def test_an_empty_requirement_stops():
    """requirement が空なら止まる。"""
    r = contract_from_plan("  ", "impl.py", ["1と2で3"], BODY)
    assert r["skeleton"] is None
    assert r["reason"] == "no_requirement"


def test_an_empty_test_plan_stops():
    """試験の一覧が空なら止まる。試験の無い契約を作らない。"""
    r = contract_from_plan("2つ足す", "impl.py", [], BODY)
    assert r["skeleton"] is None
    assert r["reason"] == "no_test_plan"


def test_another_target_file_stops():
    """impl.py 以外なら止まる。"""
    r = contract_from_plan("2つ足す", "tool.py", ["1と2で3"], BODY)
    assert r["skeleton"] is None
    assert r["reason"] == "unexpected_target"


def test_a_body_without_a_test_function_stops():
    """def test_ が無ければ止まる。門が弾く物を作らない。"""
    body = "from impl import add_two\n\n\nx = add_two(1, 2)\n"
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], body)
    assert r["skeleton"] is None
    assert r["reason"] == "no_test_function"


def test_a_body_without_an_import_stops():
    """名前が取り出せなければ止まる。推測で作らない。"""
    body = "def test_it():\n    assert 1 == 1\n"
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], body)
    assert r["skeleton"] is None
    assert r["reason"] == "no_function_name"


def test_a_body_without_a_call_stops():
    """呼び出しが無ければ引数が決められない。止まる。"""
    body = "from impl import add_two\n\n\ndef test_it():\n    assert True\n"
    r = contract_from_plan("2つ足す", "impl.py", ["1と2で3"], body)
    assert r["skeleton"] is None
    assert r["reason"] == "no_function_name"


def test_a_call_with_no_argument_gives_no_parameter():
    """引数が無い呼び出しなら引数も無い。"""
    body = "from impl import ping\n\n\ndef test_it():\n    assert ping() is True\n"
    r = contract_from_plan("応答する", "impl.py", ["真を返す"], body)
    assert r["skeleton"].startswith("def ping():")


def test_a_nested_call_counts_the_outer_commas_only():
    """入れ子の読点は数えない。"""
    body = ('from impl import wrap\n\n\ndef test_it():\n'
            '    assert wrap({"a": 1, "b": 2}, [3, 4]) is None\n')
    r = contract_from_plan("包む", "impl.py", ["辞書と一覧"], body)
    assert r["skeleton"].startswith("def wrap(a, b):")


def test_a_stopped_result_has_no_content():
    """止まったときは中身を返さない。"""
    r = contract_from_plan("", "impl.py", ["x"], BODY)
    assert r["skeleton"] is None
    assert r["immutable_tests"] is None


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ("2つ足す", "impl.py", ["1と2で3"], BODY)
    assert contract_from_plan(*a) == contract_from_plan(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = contract_from_plan("", "", [], "")
    for k in ("skeleton", "immutable_tests", "reason"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★MGR・★★口 0増）

```
★入力 = ★PLAN が 既に 持つ 欄だけ（★`requirement` ／ `target_file` ／ `test_plan` ／ ★★`test_body`）
★★`test_body` を 足した 理由 = ★★§0（★関数名の 欄が 無い ／ ★`plan_ok` が 既に 必須に している）
★★出す先 = ★`twoder/request_template.py` が いま 空で 出している 所
★★★MGR は 骨格・封印試験を ★1行も 手で 書かない（★書いたら 実験が 不成立＝★あなたの 線）
```

## 6. ★★受入（★あなたの 1つ ＋ ★私から 2つ）

```
★★① ★新規 1件が ★材料 → PLAN → ★★2DER が 契約 → submit → Worker → Test/Audit を 通る
★★★②（★私）★止まった 時は ★★理由の 語が 出る（★6語の どれか）
   ―― ★★★通らなかった 時に ★『どこで 止まったか』が ★1回で 分かる（★★本日 1時間 探した 型の 予防）
★★★③（★私）★★`immutable_tests` が ★`test_body` と ★★bytes 同一
   ―― ★★これが 崩れたら ★★『組み立てている』＝★★★設計の 芯が 外れている
★★④ `skeleton_missing` = 0 ／ ★封印試験 15本 passed ／ ★★定数 0個
★★⑤ LLM 0回（★★この部品は 決定論）／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★試験を 組み立てない（★`test_body` を そのまま）
★★★名前を 推測しない（★取り出せなければ 止まる）
★★★万能な 変換器に しない（★まず 1本＝★`impl.py` だけ）
★★後付けの 口を 作らない（★Taka）
★★★『設計が 自動化された』と 書かない ―― ★★正しくは ★『★契約の 文字列を ★2DER が 組んだ 件数 ★N』
```
