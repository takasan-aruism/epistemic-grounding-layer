開発者規律 確認済(v1.0)

# 【契約・1本】★Phase B ―― ★★`contract_progress`（★Expected と Observed を **分けて** 出す）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 20:4x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 20:19**（★条件6点 ／ ★名前案 ／ ★★『契約が 出たら 即 投入する＝私は 待たない』）
**★Taka 逐語**「★先に 進める ／ ★あなたの ペースだと 一生 終わらない」

**★語は 新しく 作らない** ―― ★運転規則 §9 の 7語を そのまま 使う

---

## 1. ★★投入前の 確認（★本日 落とした 2つを 先に 潰す）

```
★★(あ) ★骨格の 定数 = ★★1個（★`STAGES` のみ＝★MGR 条件④の 上限）
   ―― ★★★試験が それを import して 中身を 確かめる ＝ ★★落とせない 形に する
★★(い) ★★試験が 期待する 値の 決め方を ★全部 骨格に 書いた
   ―― ★順序は `STAGES` の 並び ／ ★『最も 進んだ 物』の 意味 ／ ★記録が 無い時 ／
      ★知らない語の 扱い ／ ★`by_stage` は 7語 全部 持つ
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 記録が 1件も 無い 契約        → ★`observed_stage` は ★`None` ／ ★`no_record` に 1
★② 記録が 1段階だけ              → ★その段階
★★③ 複数段階が 在る              → ★★`STAGES` の 並びで ★最も 進んだ 物
★★④ 記録の 並び順が 逆            → ★★★答えは 変わらない（★★並び順では なく ★語で 決める）
★★⑤ 知らない語                  → ★★`unknown_stage` に 数える ／ ★★★順序判定に 使わない（★捨てない）
★★⑥ 契約に 無い task の 記録      → ★★触らない（★この関数の 仕事では ない）
★★⑦ ★★`by_stage` は ★★★7語 全部 キーを 持つ（★★0件でも 欄を 消さない）
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数1個・★条件は docstring に 全部）

```
<<<2DER:SKELETON>>>
STAGES = ("CREATED", "TESTED", "AUDITED", "PLACED", "CONNECTED", "OBSERVED", "USED")


def contract_progress(contracts, records):
    """契約ごとに、記録から見て どの段階まで来たかを出す。判定の語は返さない。

    contracts: {"task_id", "name"} の辞書の一覧。これが Expected。
    records: {"task_id", "stage"} の辞書の一覧。これが Observed。

    返り値は {"rows", "by_stage", "no_record", "unknown_stage"} の辞書。

    rows は contracts と同じ順。各要素は
      {"task_id", "expected_name", "observed_stage"}。
    observed_stage は その task_id の records のうち STAGES で最も後ろにある語。
      records が1件も無ければ None。STAGES に無い語は使わない。
    by_stage は STAGES の7語を全部キーに持ち、その段階に居る契約の数を値にする。
    no_record は observed_stage が None の契約の数。
    unknown_stage は STAGES に無い語を持つ records の数。
    contracts に無い task_id の records は数えない。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import contract_progress, STAGES


def test_stages_are_the_seven_words_in_order():
    """段階の語は7つ、この順。"""
    assert STAGES == ("CREATED", "TESTED", "AUDITED", "PLACED", "CONNECTED", "OBSERVED", "USED")


def test_no_record_gives_none():
    """記録が無い契約は None。no_record に数える。"""
    r = contract_progress([{"task_id": "T1", "name": "a"}], [])
    assert r["rows"][0]["observed_stage"] is None
    assert r["no_record"] == 1


def test_single_record_is_that_stage():
    """記録が1件ならその段階。"""
    r = contract_progress([{"task_id": "T1", "name": "a"}], [{"task_id": "T1", "stage": "TESTED"}])
    assert r["rows"][0]["observed_stage"] == "TESTED"


def test_furthest_stage_wins():
    """複数在れば最も進んだ物。"""
    rec = [{"task_id": "T1", "stage": "CREATED"},
           {"task_id": "T1", "stage": "PLACED"},
           {"task_id": "T1", "stage": "TESTED"}]
    r = contract_progress([{"task_id": "T1", "name": "a"}], rec)
    assert r["rows"][0]["observed_stage"] == "PLACED"


def test_record_order_does_not_matter():
    """記録の並び順を逆にしても答えは同じ。"""
    a = contract_progress([{"task_id": "T1", "name": "a"}],
                          [{"task_id": "T1", "stage": "USED"}, {"task_id": "T1", "stage": "CREATED"}])
    b = contract_progress([{"task_id": "T1", "name": "a"}],
                          [{"task_id": "T1", "stage": "CREATED"}, {"task_id": "T1", "stage": "USED"}])
    assert a == b
    assert a["rows"][0]["observed_stage"] == "USED"


def test_unknown_stage_is_counted_and_not_used():
    """知らない語は数えるが 順序判定に使わない。"""
    rec = [{"task_id": "T1", "stage": "CREATED"}, {"task_id": "T1", "stage": "ZZZ"}]
    r = contract_progress([{"task_id": "T1", "name": "a"}], rec)
    assert r["rows"][0]["observed_stage"] == "CREATED"
    assert r["unknown_stage"] == 1


def test_record_for_unknown_task_is_ignored():
    """契約に無い task の記録は数えない。"""
    r = contract_progress([{"task_id": "T1", "name": "a"}], [{"task_id": "T9", "stage": "USED"}])
    assert r["rows"][0]["observed_stage"] is None
    assert r["no_record"] == 1
    assert r["unknown_stage"] == 0


def test_by_stage_has_all_seven_keys():
    """by_stage は7語すべてキーを持つ。0件でも欄を消さない。"""
    r = contract_progress([], [])
    assert list(r["by_stage"].keys()) == list(STAGES)
    assert set(r["by_stage"].values()) == {0}


def test_by_stage_counts_contracts():
    """by_stage はその段階に居る契約の数。"""
    con = [{"task_id": "T1", "name": "a"}, {"task_id": "T2", "name": "b"}]
    rec = [{"task_id": "T1", "stage": "PLACED"}, {"task_id": "T2", "stage": "PLACED"}]
    r = contract_progress(con, rec)
    assert r["by_stage"]["PLACED"] == 2
    assert r["by_stage"]["USED"] == 0


def test_rows_keep_the_given_order():
    """rows は contracts と同じ順。"""
    con = [{"task_id": "T2", "name": "b"}, {"task_id": "T1", "name": "a"}]
    r = contract_progress(con, [])
    assert [x["task_id"] for x in r["rows"]] == ["T2", "T1"]
    assert r["rows"][0]["expected_name"] == "b"


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    con = [{"task_id": "T1", "name": "a"}]
    rec = [{"task_id": "T1", "stage": "AUDITED"}]
    assert contract_progress(con, rec) == contract_progress(con, rec)


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = contract_progress([], [])
    for k in ("rows", "by_stage", "no_record", "unknown_stage"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★新造 0＝★MGR が 既に 探した）

```
★★Expected の 源（★★どれも 既存＝★作らない）
   ★① ★`contract_seal.py:39 extract_contract`（★骨格＋封印試験を 決定論で 抽出・封印）
   ★② ★`CREATE` イベントの `payload["contract"]`
   ★③ ★`generate_via_runner.py:32 read_create_event(task_id)`（★★task ごとに 引ける）
★★Observed の 源 = ★`event_trace`（★★段階の 語に 対応する 記録）
★★出す口 = ★★`observed_edges` か `/api/control` の ★★既存 include に 欄（★★口 0増）
```

## 6. ★★受入

```
★★① ★★7語 全部が ★`by_stage` に 出る（★★0件でも 欄が 在る）
★★② ★★`CREATED` と `USED` の 件数を ★両方 出す
   ―― ★★★これが 規則 §9 の『★2DER が コードを 書いた ≠ 実運用で 使われている』の 数
★★③ ★判定の語（★『遅れている』『駄目』）が ★★成果物に 0件
★★④ ★`skeleton_missing` = 0 ／ ★`ImportError` が 出ない（★★定数1個の 検算）
★★⑤ ★封印試験 12本 passed ／ ★`immutable_tests_touched` = false
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増 ／ ★★新造の 機構 0（★§8）
★★⑦（★私）★★`USED` が ★0件でも ★★★そう書く（★★0を 隠さない＝★今日の 比 2DER 6 : Claude 14 と 同じ扱い）
```

## 7. ★★言い方

```
★★『Phase B が 終わった』と 書かない ―― ★★★Expected と Observed が ★1つの表に 並ぶまで
★★★『2DER が 書いた』と『★使われている』を ★同じ数に しない（★★規則 §9）
★★『遅れている』と 書かない ―― ★★段階の 語と 件数だけ（★裁定は 上）
```
