開発者規律 確認済(v1.0)

# 【契約・1本】★`ignore` に **末尾一致** を許す ―― ★★`filter_ignored`（★★既存契約を 1バイトも 触らない）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 22:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 22:11**「★`ignore` は 道順の 完全一致で 効く ∴ ★番号つきの 道順(`rows.0.last_as_of`)は 除けていない ／ ★直す形＝末尾一致を 許す ／ ★★除いた物は 名前で 残す」

---

## 1. ★★なぜ 新しい 関数か（★★`unstable_keys` を 触らない）

```
★★`unstable_keys` は ★★通った（★13本 passed）＝ ★★★封印試験を 変えない（★本日 決めた 規律）
★★∴ ★★後ろで 絞る = ★`unstable_keys` の 返した `changed` を ★この関数に 通す
   ―― ★★★呼ぶ順 = ★`unstable_keys`（★ignore 無しで 呼ぶ）→ ★`filter_ignored`
   ―― ★★これで ★既存の 契約は ★1バイトも 変わらない
★★★語を 増やさない = ★型は 2つだけ（★完全一致 ／ ★★`*` で 始まる 末尾一致）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 完全一致 の型                     → ★除く
★★② ★`*` で 始まる 型                → ★★末尾一致で 除く（★例 `*.last_as_of`）
★③ どれにも 当たらない               → ★残す
★★④ ★`*` を 含まない 型は ★★完全一致だけ（★★途中一致に しない）
★★⑤ ★除いた物は ★★`removed` に ★名前で（★★★黙って 消えない）
★★⑥ ★★`kept` ＋ `removed` の 数 = ★★入力の 数（★★取りこぼし 0）
★★⑦ 並びは ★★入力の 順（★並べ替えない）
★★⑧ 型が 空                          → ★★全部 `kept`
★★⑨ 同じ道順が 2回 入力に 在る        → ★★★2回とも 残す（★潰さない）
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

```
<<<2DER:SKELETON>>>
def filter_ignored(paths, patterns=None):
    """道順の一覧から、型に当たる物を除く。除いた物も名前で返す。

    paths: 道順の文字列の一覧。例 "rows.0.last_as_of"。
    patterns: 型の文字列の一覧。渡されなければ空。

    型は2種類だけ。
      "*" で始まる型は、末尾一致で当たる。例 "*.last_as_of" は "rows.0.last_as_of" に当たる。
      "*" で始まらない型は、完全一致だけで当たる。

    返り値は {"kept", "removed", "checked"} の辞書。
    kept は当たらなかった道順。paths の順のまま。
    removed は当たった道順。paths の順のまま。
    checked は paths の数。kept と removed の数の合計と必ず等しい。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import filter_ignored


def test_exact_match_is_removed():
    """完全一致は除く。"""
    r = filter_ignored(["as_of", "x"], ["as_of"])
    assert r["kept"] == ["x"]
    assert r["removed"] == ["as_of"]


def test_suffix_pattern_removes_numbered_paths():
    """* で始まる型は末尾一致。番号つきの道順も除ける。"""
    r = filter_ignored(["rows.0.last_as_of", "rows.1.last_as_of", "rows.0.count"],
                       ["*.last_as_of"])
    assert r["kept"] == ["rows.0.count"]
    assert r["removed"] == ["rows.0.last_as_of", "rows.1.last_as_of"]


def test_plain_pattern_does_not_match_in_the_middle():
    """* を含まない型は完全一致だけ。途中一致にしない。"""
    r = filter_ignored(["rows.0.last_as_of"], ["last_as_of"])
    assert r["kept"] == ["rows.0.last_as_of"]
    assert r["removed"] == []


def test_nothing_matches_keeps_everything():
    """どれにも当たらなければ全部残す。"""
    r = filter_ignored(["a", "b"], ["zzz"])
    assert r["kept"] == ["a", "b"]
    assert r["removed"] == []


def test_empty_patterns_keeps_everything():
    """型が空なら全部残す。"""
    r = filter_ignored(["a", "b"])
    assert r["kept"] == ["a", "b"]
    assert r["removed"] == []


def test_removed_names_are_kept_not_just_counted():
    """除いた物は名前で残す。"""
    r = filter_ignored(["t.ts", "t.count"], ["*.ts"])
    assert r["removed"] == ["t.ts"]


def test_kept_plus_removed_equals_checked():
    """kept と removed の合計は checked と等しい。"""
    r = filter_ignored(["a.ts", "b.count", "c.ts"], ["*.ts"])
    assert len(r["kept"]) + len(r["removed"]) == r["checked"]
    assert r["checked"] == 3


def test_order_is_the_given_order():
    """並びは渡された順のまま。"""
    r = filter_ignored(["z", "a"], [])
    assert r["kept"] == ["z", "a"]


def test_duplicate_path_is_kept_twice():
    """同じ道順が2回在れば2回とも残す。潰さない。"""
    r = filter_ignored(["a", "a"], [])
    assert r["kept"] == ["a", "a"]
    assert r["checked"] == 2


def test_suffix_pattern_needs_the_dot():
    """*.ts は ts で終わる道順のうち、点の後が ts の物に当たる。"""
    r = filter_ignored(["x.ts", "parts"], ["*.ts"])
    assert r["removed"] == ["x.ts"]
    assert r["kept"] == ["parts"]


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a, b = ["a.ts", "b"], ["*.ts"]
    assert filter_ignored(a, b) == filter_ignored(a, b)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = filter_ignored([])
    for k in ("kept", "removed", "checked"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★口 0増・★★呼ぶ順を 変えるだけ）

```
★★① `unstable_keys(first, second)` を ★★`ignore` 無しで 呼ぶ
★★② 返った `changed` を ★`filter_ignored(changed, patterns)` に 通す
★★③ ★`observed_edges.self_check` に ★`kept` と ★★`removed` を ★★両方 出す
   ―― ★★★`removed` を 出さない形に しない（★★除いた物が 見えなくなる）
★★★`unstable_keys` の 封印試験は ★1バイトも 触らない
```

## 6. ★★受入（★★入ったかだけを 数で）

```
★★① ★★時刻の 欄（`*.last_as_of` ／ `*.as_of` ／ `*.ts`）が ★`kept` から 消える
★★② ★★その分が ★`removed` に ★★名前で 出る（★件数だけに しない）
★★③ ★★★`kept` に 残るのが ★★★数の 欄だけに なる
   ―― ★★これが 目的 = ★★時刻と 数が 混ざらない
★★④ ★`kept` の 件数（★★いま 10 → ★いくつに なったか）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増 ／ ★★`unstable_keys` は bytes 不変
```

## 7. ★★触らない（★MGR が OPEN_FINDING に した 物）

```
★★所要 = ★`observed_edges` 20.3/21.2秒 ／ `edge_measures` 16.5/5.3秒
   ―― ★★本線では ない ∴ ★★★私も 触らない（★§5 発見≠着手）
   ―― ★★但し ★1日1回に した 理由が これ である事は ★記録に 在る
```
