開発者規律 確認済(v1.0)

# 【契約・1本】★証拠から 段を 決める ―― ★★`stage_from_evidence`（★★`CONNECTED` は 返さない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 03:5x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 03:30**（★出口＝`USED` が 0 から 動く ／ ★材料は 揃っている ／ ★中身も 指定）
**★この文書には 印の語を 説明として 書かない**

---

## 1. ★★材料は 既に 在る（★MGR が 数で 出した）

```
★`PLACED` の 材料 = ★受け取った 成果物 3件 ／ ★3件とも 中身が 同じ物が 在る（★sha で 言える＝★自己申告 0）
★`OBSERVED` の 材料 = ★部品が 記録に 出た（★6種）
★`USED` の 材料 = ★両側が 揃った 区間 8本
★★★足りないのは ★『★証拠から 段を 決めて ★1行 書く』所 ＝ ★★この契約 1本
```

## 2. ★★★`CONNECTED` を 返さない（★★嘘を 足さない）

```
★★いま ★`CONNECTED` の 材料が ★無い
★★∴ ★★★語は 残す（★`by_stage` の キーに 置く）／ ★★★値は 0 の まま
   ―― ★★『材料が 無い』を ★『繋がっていない』と 書かない
   ―― ★★『欄を 消す』も しない（★★0件が 欄ごと 消えると ★不在が 遵守に 見える）
```

## 3. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① `used` に 在る                         → ★`USED` ／ `why` は `"used"`
★★② `used` に 無く `observed` に 在る       → ★`OBSERVED` ／ `why` は `"observed"`
★★③ ①②に 無く `placed` が 真               → ★`PLACED` ／ `why` は `"placed"`
★★④ どれにも 当たらない                     → ★`stage` は None ／ `why` は None
★★⑤ ★`part_of` に 無い task                 → ★★`no_evidence` に 数える（★★捨てない）
★★⑥ `placed` が 偽                          → ★`PLACED` に しない
★★⑦ 証拠が 複数 在る                        → ★★★強い方を 採る（★`used` > `observed` > `placed`）
★★⑧ `by_stage` は ★★5語 全部 キーを 持つ（★`PLACED` / `CONNECTED` / `OBSERVED` / `USED` ／ 0でも 消さない）
★★⑨ 並びは ★`placed` の 順（★並べ替えない）
★★⑩ 同じ入力を 2回 渡して ★同じ
★⑪ キーは ★どの場合も 欠けない
```

## 4. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def stage_from_evidence(placed, observed, used, part_of):
    """証拠から段を1つ決める。材料の無い段は返さない。

    placed: {"task_id", "sha_matched"} の辞書の一覧。sha_matched は真偽。
    observed: 記録に出た部品名の一覧。文字列の一覧。
    used: 両側が揃った区間の受け手名の一覧。文字列の一覧。
    part_of: task_id をキー、部品名を値とする辞書。

    返り値は {"rows", "by_stage", "no_evidence"} の辞書。

    rows は placed と同じ順。各要素は {"task_id", "stage", "why"}。
      その task_id の部品名を part_of から引く。
      部品名が used に在れば stage は "USED"、why は "used"。
      無く observed に在れば stage は "OBSERVED"、why は "observed"。
      無く sha_matched が真なら stage は "PLACED"、why は "placed"。
      どれにも当たらなければ stage も why も None。
    by_stage は "PLACED" "CONNECTED" "OBSERVED" "USED" の4語を全部キーに持ち、その数を値にする。
      CONNECTED は材料が無いので常に 0。
    no_evidence は part_of に task_id が無い行の数。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 5. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import stage_from_evidence


def test_used_wins():
    """受け手名が used に在れば USED。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": True}], ["p"], ["p"], {"T1": "p"})
    assert r["rows"][0]["stage"] == "USED"
    assert r["rows"][0]["why"] == "used"


def test_observed_when_not_used():
    """used に無く observed に在れば OBSERVED。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": True}], ["p"], [], {"T1": "p"})
    assert r["rows"][0]["stage"] == "OBSERVED"
    assert r["rows"][0]["why"] == "observed"


def test_placed_when_only_sha_matched():
    """記録に出ていなくても sha が一致していれば PLACED。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": True}], [], [], {"T1": "p"})
    assert r["rows"][0]["stage"] == "PLACED"
    assert r["rows"][0]["why"] == "placed"


def test_no_evidence_gives_none():
    """どれにも当たらなければ stage も why も None。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": False}], [], [], {"T1": "p"})
    assert r["rows"][0]["stage"] is None
    assert r["rows"][0]["why"] is None


def test_sha_not_matched_is_not_placed():
    """sha が一致していなければ PLACED にしない。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": False}], [], [], {"T1": "p"})
    assert r["by_stage"]["PLACED"] == 0


def test_unknown_task_is_counted_as_no_evidence():
    """part_of に無い task は no_evidence に数える。"""
    r = stage_from_evidence([{"task_id": "T9", "sha_matched": True}], [], [], {"T1": "p"})
    assert r["no_evidence"] == 1
    assert r["rows"][0]["stage"] is None


def test_connected_is_always_zero():
    """CONNECTED は材料が無いので常に 0。語は残す。"""
    r = stage_from_evidence([{"task_id": "T1", "sha_matched": True}], ["p"], ["p"], {"T1": "p"})
    assert r["by_stage"]["CONNECTED"] == 0
    assert "CONNECTED" in r["by_stage"]


def test_by_stage_has_all_four_words():
    """4語すべてキーを持つ。0件でも欄を消さない。"""
    r = stage_from_evidence([], [], [], {})
    assert sorted(r["by_stage"].keys()) == ["CONNECTED", "OBSERVED", "PLACED", "USED"]
    assert set(r["by_stage"].values()) == {0}


def test_by_stage_counts_rows():
    """by_stage はその段の行数。"""
    placed = [{"task_id": "T1", "sha_matched": True}, {"task_id": "T2", "sha_matched": True}]
    r = stage_from_evidence(placed, ["q"], ["p"], {"T1": "p", "T2": "q"})
    assert r["by_stage"]["USED"] == 1
    assert r["by_stage"]["OBSERVED"] == 1


def test_order_is_the_placed_order():
    """並びは placed の順のまま。"""
    placed = [{"task_id": "T2", "sha_matched": True}, {"task_id": "T1", "sha_matched": True}]
    r = stage_from_evidence(placed, [], [], {"T1": "p", "T2": "q"})
    assert [x["task_id"] for x in r["rows"]] == ["T2", "T1"]


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = ([{"task_id": "T1", "sha_matched": True}], ["p"], [], {"T1": "p"})
    assert stage_from_evidence(*a) == stage_from_evidence(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = stage_from_evidence([], [], [], {})
    for k in ("rows", "by_stage", "no_evidence"):
        assert k in r
<<<2DER:END>>>

## 6. ★★足場（★Claude・★★口 0増）

```
★`placed` = ★受領の 記録（★`auto_total.received_rows` の ★sha 一致）
★`observed` = ★`direct_counts.by` の ★`X.called` の X
★`used` = ★両側が 揃った 区間の ★受け手名
★`part_of` = ★受領の 記録の ★task_id と 部品名
★★出す口 = ★既存 include に ★欄を 1つ ／ ★★記録に 1行（★段が 変わった 時だけ）
```

## 7. ★★受入（★★出口は 1つ）

```
★★① ★★★`USED` が ★0 から 動く（★★動かなければ ★理由を 数で）
★★② ★`by_stage` の 4語が 出る ／ ★★`CONNECTED` は 0（★★語は 消えていない）
★★③ ★`no_evidence` の 件数（★★0件でも 書く）
★★④ ★`why` が 行ごとに 出る（★★どの 材料で 決めたかが 引ける）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
★★⑦（★私）★★★`USED` が 動いても ★『使われている』と 書かない
   ―― ★★正しくは ★★『★両側の 記録が 揃った 部品が N 本』（★★語を 広げない）
```

## 8. ★★やらないこと

```
★★★材料の 無い 段を 埋めない（★`CONNECTED` を 推測で 立てない）
★★『段が 上がった』を ★★成果の 数に しない（★★記録が 増えただけ）
★★★片側 40 の 内訳（★MGR が 出した 13 / 18 ほか）は ★この契約で 触らない
```
