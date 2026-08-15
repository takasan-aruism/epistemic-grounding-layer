開発者規律 確認済(v1.0)

# 【契約 v2】★②狭い型 ―― ★★`record_only_patch`（★★入力は 文字5つだけ・★★門は 置く直前に 通す）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 09:1x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-15_CONTRACT_RECORD_ONLY_PATCH.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 12:42 裁定**（★『門を worker の 場所へ 置く』案は 採らない ／ ★門は ★置く直前に 足場が 通す）／ **MGR 08:50**（★①の門が 実物を 通した ／ ★②の 中身も 指定 ／ ★足す 中身は 形が 固定）

**★★『狭い』の 実装** ―― ★★★自由文を 受け取らない（★文字5つ）／ ★足す 中身の 形は ★固定（★worker に 考えさせない）

---

## 1. ★★★私の 案は 採らない（★MGR 裁定・★先に 書く）

```
★★私の 案 = ★『門を 封印試験の 中に 埋める』
★★★採らない 理由（★MGR）= ★★worker の 隔離に ★もう1つ file を 送り込む 必要が 在る
   ―― ★★★新しい 機構が 要る ＝ ★規律 §9（★管理対象を 増やさない）に 反する
   ―― ★★機械が ★2回 手前で 止めた（★`extract_contract` が ★同じ 語で 拒否）＝ ★★止めたのが 正しい

★★★∴ ★門は ★★worker の 中では なく ★★『★置く 直前』に 通す（★★足場＝MGR が 配線する）
★★★私が 直すのは 2つだけ
   ★① 外の 部品を 読む 行を ★消す（★試験の 読み込みは ★`impl` 1本だけ）
   ★② 門を 呼ぶ 試験を ★★中身で 確かめる 形に 書き換える（★★形が 変わらない ／ ★元の行が 残る ／ ★足したのは 記録の行）

★★★門を 試験から 外しても ★門は 効く（★置く 直前に 通る）
   ―― ★★但し ★★★『試験が 守る』から『★配線が 守る』に 変わった ＝ ★★性質が 違う
   ―― ★★★配線を 外すと ★門が 消える ∴ ★★その 1行が 在る 事を ★受入に 入れる（★§6⑥）

```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① その関数が 在り ★記録が 無い          → ★`after` を 作る ／ ★`added` に 足した 行 ／ ★`reason` は None
★★② その関数が 無い                        → ★`after` は None ／ ★`reason` は `"function_not_found"`
★★③ その関数が 既に 記録を 持つ            → ★★何も しない ／ ★`reason` は `"already_recorded"`
★★④ 形が 扱えない                          → ★`after` は None ／ ★`reason` は `"unsupported_shape"`
★★⑤ 作れた時 ★`after` は ★★門を 通る（★`patch_is_record_only` が True）
★★⑥ ★★元の 行が 1行も 消えない ／ 変わらない（★★足すだけ）
★★⑦ 同じ 入力を 2回 渡して ★同じ
★★⑧ `added` は ★作れなかった 時 ★空
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個・★足す 中身の 形は 固定）

<<<2DER:SKELETON>>>
def record_only_patch(before, file, function, component, received_from):
    """ある関数の先頭に、受け取ったことを残す行だけを足した本文を作る。挙動は変えない。

    before: いまの本文。文字列。
    file: その本文の file 名。文字列。記録には使わない。
    function: 行を足す関数の名前。文字列。
    component: 記録に残す部品の名前。文字列。
    received_from: 記録に残す送り手の名前。文字列。

    返り値は {"after", "added", "reason"} の辞書。

    before の中に "def <function>(" で始まる行を探す。
    見つからなければ after は None、reason は "function_not_found"、added は空。
    見つかった関数の中に既に "received_from" という文字が在れば
      after は None、reason は "already_recorded"、added は空。
    その関数に本体の行が1行も無ければ
      after は None、reason は "unsupported_shape"、added は空。

    作れるときは、その関数の本体の先頭に次の3行を、本体と同じ字下げで入れる。
      # 受け取ったことを残す
      try:
      から始まり、etrace の emit を呼び、except で受け止めて pass で終わる形。
      emit には component と function と {"received_from": received_from} を渡す。

    after は行を足しただけの本文。元の行は1行も消さず、1行も変えない。
    added は足した行の一覧。前後の空白を落とした形。
    reason は作れたとき None。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験（★★門を 中に 埋めてある）

<<<2DER:IMMUTABLE_TESTS>>>
from impl import record_only_patch


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

## 5. ★★足場（★Claude）

```
★★★worker の 場所には 何も 送らない（★MGR 裁定）
★★`after` を 置く ★直前に ★`patch_is_record_only` を 通す（★★配線＝★足場 ／ ★行数を 報告し 実績に 数えない）
★★`before` = ★本番の file の 本文 ／ ★★`after` を ★★★置くのと commit は ★★人（★線は 動かさない）
```

## 6. ★★受入（★MGR の 4点 ＋ ★私から 2つ）

```
★★① `ds` / `rri` / `dev-workcell` の ★1本を ★2DER が 作った `after` で 埋める
★★② ★★その区間が ★両側に なる
★★③ ★★★私（Claude）が 手で 書いた 行 = ★★0
★★④ 既存の 試験が 通る
★★⑤（★私）★★★受け手の 名前を ★経路表から 引いていない
   ―― ★★`received_from` は ★★★呼び出し元から 渡す（★★`route_table` を 読まない）
   ―― ★理由 = ★★本日 実証した 循環（★表から 作った 物を 表で 確かめる 形に しない）
★★⑥（★私）★★★置く 直前に 門を 通す 1行が ★在る（★★配線が 守る 形に 変わった ∴ ★その行の 有無を 数える）
```

## 7. ★★やらないこと

```
★★★自由文を 受け取らない（★入力は 文字5つ）／ ★★足す 中身を worker に 考えさせない（★形は 固定）
★★置かない ／ commit しない（★★Taka『コードは 人』の 線を 動かさない）
★★★『既存コードを 2DER が 直せるように なった』と 書かない
   ―― ★★正しくは ★★『★記録を 足す 形だけ ／ ★門を 通った 物だけ ／ ★置くのは 人』
```
