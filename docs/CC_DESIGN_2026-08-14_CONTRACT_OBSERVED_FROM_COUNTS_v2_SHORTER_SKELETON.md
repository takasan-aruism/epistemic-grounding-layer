開発者規律 確認済(v1.0)

# 【裁定・★異論あり ＋ 契約 v2】★同じ契約で もう1回は ★止める ―― ★★★798 が **2回とも 同じ**

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 14:3x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-14_CONTRACT_OBSERVED_FROM_COUNTS.md`（★中身は 触らない＝★新しい名前）
出所: **MGR 14:16**「★契約は 正しい ∴ ★worker の 失敗（★成果物が 空）／ ★同じ契約で もう1回 だけ 投げる ／ ★★異論が 在れば 止めてください」

---

## 1. ★★★訂正 ―― ★★成果物は 空では ない（★私が 記録から 引いた）

```
★★MGR 逐語 = 「★`artifact` の 長さ=★0 ＝ ★書けていない（★『書いたが 間違い』では ない）」
★★★実測（★私が `/api/etrace?task_id=TASK-2DER-C357EBA0` から 引いた）
   ★試行1 = ★★`artifact_len: 1920` ／ `added_lines: 39` ／ ★★`skeleton_missing: 798`
   ★試行2 = ★★`artifact_len: 2079` ／ `added_lines: 44` ／ ★★`skeleton_missing: 798`
   ★どちらも ★`immutable_tests_touched: false` ／ `exit: 2`

★★★∴ ★worker は ★書いている（★1920 / 2079 文字）
★★★∴ ★『書けていない』では なく ★★『★骨格の 798 バイトを 落として 書いた』
```

## 2. ★★★異論 ―― ★同じ契約の 再投入は ★止める

```
★★★理由 = ★★`skeleton_missing` が ★★2回とも ★★★798（★1バイトも 違わない）
   ―― ★★★これは ★揺れでは ない ＝ ★★決定論的に ★同じ所が 落ちている
   ―― ★★∴ ★もう1回 投げても ★★★同じ 798 が 落ちる 見込み
★★MGR の 裁定の 前提（★『1回目の 結果が 存在しない』）が ★★成り立たない
   ―― ★結果は ★2回 存在し ／ ★★2回とも 同じ（★★これは 情報＝★捨てない）
```

## 3. ★★見立て（★★★仮説と 書く・★3点しか 無い）

```
★★★骨格の docstring が 長いほど 落ちている（★★★3点のみ ∴ 断定しない）
   ★`count_by_component`      … docstring ★短い  → ★★一発で 通った（63秒・指摘0）
   ★`decide_tick` v2          … docstring ★長い  → ★1回 落ちて（`skeleton_missing 861`）から 通った
   ★`observed_from_counts`    … docstring ★最長  → ★★2回とも 落ちた（★798）
★★★落ちている 中身 = ★★定数3行 ＋ docstring（★`ImportError: cannot import name 'OBSERVED'`）

★★★私の 非 = ★★条件は ★試験に 書く と 決めておきながら
   ―― ★★docstring にも ★同じ条件を 書き足していた ＝ ★★★二重に 書いた
   ―― ★★worker には ★骨格も 試験も 両方 届く ∴ ★★長い docstring は ★★得では なく ★危険
```

## 4. ★★直す物 ―― ★★★骨格の docstring だけ（★試験は 1バイトも 変えない）

```
★★★変えない = ★★封印試験（★★★§5 は v1 と bytes 同一）／ ★関数名 ／ ★引数 ／ ★語3つ
   ―― ★理由 = ★★変えると ★★前の 2回と 比べられない（★実験が 成立しない）
★★★変える = ★docstring を ★★短くする（★★★条件は 試験が 持っている＝★重複を 消すだけ）
```

## 5. ★★骨格 v2（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
OBSERVED = "OBSERVED"
NOT_OBSERVED = "NOT_OBSERVED"
UNKNOWN = "UNKNOWN"


def observed_from_counts(route_rows, counts):
    """区間ごとに、記録の数え上げから「通ったか」を決める。

    route_rows: {"route_id", "component", "function"} の辞書の一覧。
    counts: "component.function" をキー、件数を値とする辞書。

    返り値は {"rows", "observed", "not_observed", "unknown"} の辞書。
    rows は渡された順のまま、各要素は {"route_id", "key", "count", "status"}。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 6. ★★封印試験（★★★v1 と bytes 同一＝★比べられるように 残す）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import observed_from_counts, OBSERVED, NOT_OBSERVED, UNKNOWN


def test_present_in_counts_is_observed():
    """数え上げに在れば OBSERVED。件数をそのまま出す。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 7})
    assert r["rows"][0]["status"] == OBSERVED
    assert r["rows"][0]["count"] == 7
    assert r["observed"] == 1


def test_absent_from_counts_is_zero_not_missing():
    """数え上げに無いときは 0 を置く。欄を消さない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}], {})
    assert r["rows"][0]["status"] == NOT_OBSERVED
    assert r["rows"][0]["count"] == 0
    assert r["not_observed"] == 1


def test_zero_count_is_not_observed():
    """件数が 0 なら通っていない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 0})
    assert r["rows"][0]["status"] == NOT_OBSERVED


def test_empty_field_is_unknown_and_kept():
    """欄が空の区間は捨てずに UNKNOWN として残す。"""
    r = observed_from_counts([{"route_id": "S01", "component": "", "function": "tick"}],
                             {"DW.tick": 5})
    assert r["rows"][0]["status"] == UNKNOWN
    assert r["rows"][0]["key"] == "UNKNOWN.UNKNOWN"
    assert r["rows"][0]["count"] == 0
    assert r["unknown"] == 1


def test_missing_field_is_unknown():
    """欄が無い区間も UNKNOWN。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW"}], {"DW.tick": 5})
    assert r["rows"][0]["status"] == UNKNOWN
    assert r["unknown"] == 1


def test_duplicate_segments_are_both_kept():
    """同じ区間が2つ在れば 2行とも残す。潰さない。"""
    rows = [{"route_id": "S01", "component": "DW", "function": "tick"},
            {"route_id": "S01", "component": "DW", "function": "tick"}]
    r = observed_from_counts(rows, {"DW.tick": 3})
    assert len(r["rows"]) == 2
    assert r["observed"] == 2


def test_three_numbers_sum_to_the_row_count():
    """3つの数の合計は 区間の数と等しい。取りこぼしを作らない。"""
    rows = [{"route_id": "A", "component": "X", "function": "a"},
            {"route_id": "B", "component": "Y", "function": "b"},
            {"route_id": "C", "component": "", "function": "c"}]
    r = observed_from_counts(rows, {"X.a": 2})
    assert r["observed"] + r["not_observed"] + r["unknown"] == 3
    assert len(r["rows"]) == 3


def test_order_is_the_given_order():
    """並び順は渡された順のまま。"""
    rows = [{"route_id": "Z", "component": "X", "function": "a"},
            {"route_id": "A", "component": "Y", "function": "b"}]
    r = observed_from_counts(rows, {})
    assert [x["route_id"] for x in r["rows"]] == ["Z", "A"]


def test_keys_only_in_counts_are_left_alone():
    """数え上げ側にだけ在るキーは この関数では扱わない。"""
    r = observed_from_counts([{"route_id": "S01", "component": "DW", "function": "tick"}],
                             {"DW.tick": 1, "OTHER.thing": 99})
    assert len(r["rows"]) == 1
    assert r["observed"] == 1


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    rows = [{"route_id": "S01", "component": "DW", "function": "tick"}]
    counts = {"DW.tick": 1}
    assert observed_from_counts(rows, counts) == observed_from_counts(rows, counts)


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = observed_from_counts([], {})
    for k in ("rows", "observed", "not_observed", "unknown"):
        assert k in r
<<<2DER:END>>>
```

## 7. ★★受入（★★★1つ 増える＝★見立てが 当たったかを 数で 見る）

```
★★① ★★`skeleton_missing` = ★★★0（★★798 が 消える＝★これが 見立ての 検算）
★★② ★★封印試験が 通る（★`immutable_tests_touched: false` の まま）
★★③ ★★★落ちた場合 ―― ★`skeleton_missing` の 数を ★書く
   ―― ★★また 798 なら = ★★★docstring の 長さは 原因では ない（★★見立てが 外れ＝★そう 書く）
   ―― ★★別の 数なら = ★★★短くして 減った（★★次は もっと 短く）
★★④ ★LLM の 呼び出し以外は 0（★★契約は 1本＝★割っていない）
★★⑤ ★★これでも 落ちたら ★★契約を ★★★小さく 割る（★MGR の 案に 同意＝★但し ★2回 同じ数の 後）
```

## 8. ★★MGR の 2つの 自己申告に ついて

```
★★①「★足場（`failed_tests`）は 1度も 効いていない」= ★★正しい ／ ★★私も 引けなかった（★`claude_packet` は null）
   ―― ★★今回 原因が 割れたのは ★`runner_stdout_tail`（★元から 在った 欄）＝ ★MGR の 逐語どおり
   ―― ★★★『作ったが 繋がっていない』を ★正直に 書いた事を ★記録に 残す
★★②「★`run_until_barrier` を 3回 続けて 叩いた」= ★★これは ★★★私の 契約(`decide_tick`)が 止める はずの 形
   ―― ★★`stopped_at` に 同じ工程が 2つ → ★`STOP`（★★叩き続けない）
   ―― ★★∴ ★★★Manager v0 が 本線に 入れば ★人が この形を 踏まない（★★人の 注意力に 戻さない）
```
