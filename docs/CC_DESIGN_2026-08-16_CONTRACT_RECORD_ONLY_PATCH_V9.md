開発者規律 確認済(v1.0)

# 【契約・1本】★足す 場所を **説明文の 後ろ** に する ―― ★★`record_only_patch` v8（★★v7 に 1文だけ）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-16 06:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **Taka 逐語**「★あ　でいいんじゃん？」／ **MGR 06:14**（★v7 は 3本 落ちた ／ ★依頼＝★1行だけ ／ ★★封印試験は 1バイトも 変えない）

---

## 0‑Z. ★★★あなたの 出した v9 の 文は **使えない**（★★先に 書く・★逐語で 突き合わせた）

```
★★あなたの 案（逐語）= 『★もう 記録が 在るかは ★`_ET.emit(` を 含み `received_from` を 含む 行で 決める
   ／ ★★ただの 文字列や 変数への 代入は 数えない』
★★★これは ★封印試験と ★真正面から 矛盾する。

★★封印試験（★逐語・★1バイトも 変えない と あなたが 書いた 物）:
   `b = 'def f():\n    x = {"received_from": "Z.z"}\n    return 1\n'`
   `assert r["reason"] == "already_recorded"`
   ―― ★★★これは ★『★ただの 代入』を ★★`already_recorded` に しろ、と ★書いてある

★★★∴ ★あなたの 文を 入れると ★この 試験は ★★永遠に 通らない
   ＝ ★★★『そもそも 成り立つか』が ★否（★★走らせる前に 分かる＝★★1走行を 使わずに 済む）

★★★そして ★骨格は ★既に 正しい（★逐語・17行目）:
   『見つかった関数の本体の中に既に "received_from" という文字が在れば … "already_recorded"』
   ―― ★★★仕様と 試験は ★一致している ∴ ★★★直すべきは ★仕様では なく ★実装
```

## 0‑Y. ★★★では 何を 1文 足したか（★★矛盾しない 形）

```
★★足した 文 = 『★探す 範囲は ★本体の 全行の まま。★足す 場所を どこに するかとは ★別に 決める。』
★★★狙い = ★★v7 で ★『足す 場所』の 規則を 入れた ＝ ★★実装が ★『探す 場所』も 一緒に 動かした 見込み
   ―― ★★★これは ★推測 ∴ ★★『そうだった』とは 書かない ／ ★★但し ★仕様の 側で ★両者を 分ける 事は できる
★★★試験は ★1バイトも 変えない（★15本・★v7 v8 と bytes 同一）
```

## 0‑A. ★★★v7 との 差 は **1文だけ**（★★数える）

```
★★足した 文 = ★★『★after は 行の 一覧を ★改行で 繋いだ 文字列に する。★行の 中身に 改行は 入れない。』
★★★封印試験 = ★★v7 と **bytes 同一**（★★15本 ／ ★私が `diff` で 確かめた）
★★★場合の 列挙・受入・やらない事 = ★変えていない

★★★これは 何回目か（★★隠さない）= ★★同じ 問いの **2回目**
   ―― ★★v1〜v6 は ★別の 問い（★足す 形 そのもの）＝ ★数に 混ぜない（★MGR と 一致）
   ―― ★★★3回目は ★押さない = ★★2回で 止めて ★台帳に 書く（★MGR の 線を ★私も 採る）
★★★落ちた 3本の うち ★1本は **既存の 試験**（`test_original_lines_are_all_kept`）
   ―― ★★∴ ★★★門は 効いた（★★私の 書き漏れを ★機械が 止めた＝★人が 見つけたのでは ない）
```

## 0. ★★★これは 万能化では ない（★先に 書く・★★Taka が 止めた 線を 自分で 引く）

```
★★私の 出す前の 問い（★本日 作った）= ★『★同じ形を 通すためか ／ ★新しい形を 通すためか』
★★★答え = ★★どちらでも ない = ★★★『★道具が ★自分の 約束を 破っていた』
   ―― ★約束（★v1 から 変えていない）= ★★『★元の 行は 1行も 消さず ★1行も 変えない』
   ―― ★★実際 = ★★★説明文の 前に 入れると ★★説明文が ★説明文で なくなる（`__doc__` が 消える）
      ＝ ★行は 変えていない が ★★★意味が 変わっていた（★★門 v4 も 通る＝★見ていない 面）
★★★∴ ★足す 規則は ★1つだけ ／ ★★対象も 増やさない ／ ★★新しい 語も 0
★★★v8 は 作らない ―― ★次に 別の 形が 出たら ★★台帳へ 例外として 置く（★Taka の 線）
```

## 1. ★★変える 所（★★1つだけ・★★v6 との 差分）

```
★★★足す 場所 = ★『本体の 先頭』 → ★★『★説明文が 在れば ★その 後ろ』
★★これ 以外は ★★v6 と 同じ（★引数 ／ 返り値 ／ 断る 理由の 語 ／ 足す 4行 の 中身）
```

## 2. ★★場合の 列挙（★★増えた 2つだけ 太字）

```
★① その関数が 無い                        → ★`function_not_found`
★② 既に 記録を 持つ                        → ★`already_recorded`
★③ `def` が 複数行                         → ★`"):"` の 次から
★④ 本体が 無い                             → ★`unsupported_shape`
★★★⑤ 説明文が 在る（★1行 ／ ★複数行 とも） → ★★★その 説明文の **後ろ** から
★★★⑥ 説明文が 閉じない                     → ★★`unsupported_shape`（★★推測で 足さない）
★⑦ 説明文が 無い                           → ★従来どおり 本体の 先頭
★⑧ 元の 行は 1行も 消えず 変わらない
★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個 ／ ★★v6 に 5行 足しただけ）

<<<2DER:SKELETON>>>
def record_only_patch(before, file, function, component, received_from):
    """ある関数の説明文の後ろに、受け取ったことを残す行だけを足した本文を作る。挙動は変えない。

    before: いまの本文。文字列。
    file: その本文の file 名。文字列。記録には使わない。
    function: 行を足す関数の名前。文字列。
    component: 記録に残す部品の名前。文字列。
    received_from: 記録に残す送り手の名前。文字列。

    返り値は {"after", "added", "reason"} の辞書。

    before の中に "def <function>(" で始まる行を探す。
    その def が1行で終わらないときは、"):" で終わる行を下に探し、その次の行から足す。
    "):" で終わる行が見つからなければ after は None、reason は "unsupported_shape"、added は空。
    見つからなければ after は None、reason は "function_not_found"、added は空。
    見つかった関数の本体の中に既に "received_from" という文字が在れば
      after は None、reason は "already_recorded"、added は空。
    本体とは、その def の次の行から、次の "def " で始まる行の手前まで。
    次の "def " が無ければ本文の最後まで。探すのはその全行。
    探す範囲は本体の全行のまま。足す場所をどこにするかとは別に決める。
    その関数に本体の行が1行も無ければ
      after は None、reason は "unsupported_shape"、added は空。

    足す場所は本体の先頭。ただし本体の先頭が説明文のときは、その説明文の次の行から足す。
    説明文とは、本体の最初の行の前後の空白を落とした形が三重引用符で始まるものを指す。
    その同じ行の中でもう一度三重引用符が出て終わっていれば、その行の次から足す。
    終わっていなければ、三重引用符を含む行を下に探し、見つかった行の次から足す。
    最後まで探しても見つからなければ after は None、reason は "unsupported_shape"、added は空。

    作れるときは、その足す場所に次の4行を、本体と同じ字下げで入れる。
    行の中身はこの通りにする。<component> <function> <received_from> <file> の所だけ受け取った値に置き換える。
    at には file と function を "::" で繋いだ文字列を入れる。これが実装の位置になる。

      # 受け取ったことを残す
      try:
          from ds import etrace as _ET; _ET.emit("<component>", "<function>", {"received_from": "<received_from>", "at": "<file>::<function>"}, {"ok": True}, "OK", fail_open=True)
      except Exception:
          pass

    この文を f 文字列で組み立てない。引用符が入れ子になって壊れる。
    決まった形の文字列を用意し、置き換えか連結で作る。

    after は行を足しただけの本文。元の行は1行も消さず、1行も変えない。
    after は行の一覧を改行で繋いだ文字列にする。行の中身に改行は入れない。
    added は足した行の一覧。前後の空白を落とした形。
    reason は作れたとき None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★v6 の 13本 ＋ ★★★足したのは 2本 ＝ ★15本）

<<<2DER:IMMUTABLE_TESTS>>>
import ast

from impl import record_only_patch


def test_docstring_stays_the_docstring():
    """説明文の後ろに足す。足した後も説明文が説明文のまま残る。"""
    b = 'def f():\n    """せつめい\n\n    つづき\n    """\n    return 1\n'
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    assert r["reason"] is None
    assert ast.get_docstring(ast.parse(r["after"]).body[0]) is not None


def test_no_docstring_inserts_at_the_top():
    """説明文が無ければ 本体の先頭に足す。"""
    b = "def f():\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    assert r["after"].splitlines()[1].strip() == "# 受け取ったことを残す"


def test_missing_function_gives_a_reason():
    """その関数が無ければ作らない。"""
    r = record_only_patch("def other():\n    pass\n", "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "function_not_found"
    assert r["added"] == []


def test_already_recorded_does_nothing():
    """既に記録を持つ関数には足さない。"""
    b = 'def f():\n    x = {"received_from": "Z.z"}\n    return 1\n'
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "already_recorded"


def test_multiline_def_inserts_after_the_closing_line():
    """def が複数行のときは "):" の次の行から足す。引数の途中に入れない。"""
    b = "def f(x,\n      y=None):\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    lines = r["after"].splitlines()
    assert lines[1].strip() == "y=None):"


def test_empty_body_is_unsupported():
    """本体が無い関数は扱えない。"""
    r = record_only_patch("def f():\n", "a.py", "f", "C", "X.y")
    assert r["after"] is None
    assert r["reason"] == "unsupported_shape"


def test_patch_is_created_with_a_reason_of_none():
    """作れたときは reason が None で added が空でない。"""
    r = record_only_patch("def f():\n    return 1\n", "a.py", "f", "C", "X.y")
    assert r["reason"] is None
    assert r["added"] != []


def test_original_lines_are_all_kept():
    """元の行は1行も消えず、1行も変わらない。"""
    b = "def f():\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    for line in b.splitlines():
        assert line in r["after"].splitlines()


def test_after_keeps_the_same_shape():
    """作った本文は形が変わらない。関数の数も return の数も同じ。"""
    b = "def f():\n    return 1\n"
    r = record_only_patch(b, "a.py", "f", "C", "X.y")
    assert r["after"].count("def ") == b.count("def ")
    assert r["after"].count("return") == b.count("return")


def test_added_lines_are_record_lines():
    """足したのは記録の行だけ。"""
    r = record_only_patch("def f():\n    return 1\n", "a.py", "f", "C", "X.y")
    assert "emit" in "".join(r["added"])


def test_component_and_sender_are_in_the_patch():
    """記録に残す名前が本文に入る。"""
    r = record_only_patch("def f():\n    return 1\n", "a.py", "f", "MYCOMP", "SEND.er")
    assert "MYCOMP" in r["after"]
    assert "SEND.er" in r["after"]


def test_added_is_empty_when_not_created():
    """作れなかったときは added が空。"""
    r = record_only_patch("def other():\n    pass\n", "a.py", "f", "C", "X.y")
    assert r["added"] == []


def test_at_carries_the_implementation_location():
    """at に file と function を :: で繋いだ位置が入る。"""
    r = record_only_patch("def f():\n    return 1\n", "rri/x.py", "f", "C", "X.y")
    assert "rri/x.py::f" in r["after"]


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ("def f():\n    return 1\n", "a.py", "f", "C", "X.y")
    assert record_only_patch(*a) == record_only_patch(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = record_only_patch("", "a.py", "f", "C", "X.y")
    for k in ("after", "added", "reason"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★MGR・★★手順は あなたの 書いた 順）

```
★①`git checkout` で ★今日 当てた ★6本を 戻す（★★手で 書き換えない＝`already_recorded` を 避ける）
★②v7 で 当て直す ／ ★③門 v4 ／ ★④`ast.get_docstring` で 確かめる ／ ★⑤commit
★★★私（DESIGN）は 当てない
```

## 6. ★★受入（★★あなたの 3つを そのまま ＋ ★私から 1つ）

```
★★①今日 当てた ★6関数 すべてで ★`ast.get_docstring` が ★None でない
★★②門 v4 を 通る
★★③`identity` が ★★4 の まま（★★減らさない＝★戻して 当て直すので ★一度 減りうる ∴ ★★最後に 4）
★★★④（★私）★★`unsupported_shape` が ★増えた 件数（★★説明文が 閉じない 形が 何本 在ったか）
   ―― ★★0 なら 0 と 書く（★★『全部 通った』を ★数で 確かめる）
★★⑤`skeleton_missing` = 0 ／ ★封印試験 ★15本 passed ／ ★★定数 0個
★★⑥`LLM 0回` ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★v8 を 作らない（★次の 形は ★台帳へ 例外）
★★★`task_id` / `run_id` を ★この契約で 足さない
   ―― ★理由 = ★★それは ★別の 話（★★走行の 番号を 両側に 載せる＝★あなたの 順の ②）
   ―― ★★★1つの 直しに 2つの 目的を 入れない（★★本日 私が 5回 踏んだ 型の 予防）
★★対象の 関数を 増やさない（★★計装は 止める＝★あなたの 裁定どおり）
```
