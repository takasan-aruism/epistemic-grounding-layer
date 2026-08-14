開発者規律 確認済(v1.0)

# 【契約・1本】★③投入の 機械化 ―― ★★`pending_contracts`（★★選ばない・★まだ投げていない物を 出すだけ）

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 23:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 裁定 23:02**（★③を 先に ／ ★②は 保留 ／ ★根拠＝★私が 出した 数：②は手番0減・③は 契約ごとに1回＝本日16回級）

**★★判断を 持たせない** ―― 「★どれを 投げるか」は **★Manager の 仕事**。この関数は **★『まだ 投げていない物』**だけを 出す。

---

## 1. ★★何を 鍵に するか（★★1つだけ・★決定論）

```
★★鍵 = ★★★骨格の `sha256`（★`contract_seal` が 既に 封印時に 作る＝★★新造 0）
   ―― ★『文書の 名前』を 鍵に しない（★★v2 で 名前が 変わる ／ 中身が 同じ 事も 在る）
   ―― ★『投入した か』は ★★記録から 引く（★★人の 記憶に 置かない）
★★★選ばない = ★★★並べるだけ（★優先順位を 付けない＝★Taka §2.3 と 同じ 線）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 骨格の sha が ★投入済みに 在る        → ★`already`
★② 無い                                  → ★`pending`
★★③ sha が 空／欄が 無い                 → ★★`skipped`（★★捨てない＝★数えて 名前も 残す）
★★④ 同じ sha の 文書が 2つ 在る          → ★★★2行とも 残す（★★潰さない＝★v1/v2 は 別の 文書）
★★⑤ 投入済みに 在るが 文書に 無い sha     → ★★触らない（★この関数の 仕事では ない）
★★⑥ 並びは ★★渡された 順（★並べ替えない）
★★⑦ 3つの 数の 合計 = ★★文書の 数（★★取りこぼし 0）
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

```
<<<2DER:SKELETON>>>
def pending_contracts(docs, submitted):
    """まだ投げていない契約を並べる。どれを投げるかは決めない。

    docs: {"name", "skeleton_sha"} の辞書の一覧。
    submitted: 既に投入した骨格の sha256 の一覧。

    返り値は {"rows", "pending", "already", "skipped"} の辞書。

    rows は docs と同じ順。各要素は {"name", "skeleton_sha", "status"}。
    status は "pending" / "already" / "skipped" のどれか。
      skeleton_sha が submitted に在れば "already"。無ければ "pending"。
      skeleton_sha が空、または欄が無ければ "skipped"。
    pending / already / skipped は それぞれの status の行数。
    3つの合計は docs の数と必ず等しい。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import pending_contracts


def test_not_submitted_is_pending():
    """投入済みに無ければ pending。"""
    r = pending_contracts([{"name": "a.md", "skeleton_sha": "aaa"}], [])
    assert r["rows"][0]["status"] == "pending"
    assert r["pending"] == 1


def test_submitted_is_already():
    """投入済みに在れば already。"""
    r = pending_contracts([{"name": "a.md", "skeleton_sha": "aaa"}], ["aaa"])
    assert r["rows"][0]["status"] == "already"
    assert r["already"] == 1


def test_empty_sha_is_skipped():
    """sha が空なら skipped。捨てずに数える。"""
    r = pending_contracts([{"name": "a.md", "skeleton_sha": ""}], [])
    assert r["rows"][0]["status"] == "skipped"
    assert r["skipped"] == 1


def test_missing_sha_field_is_skipped():
    """欄が無くても skipped。名前は残る。"""
    r = pending_contracts([{"name": "a.md"}], [])
    assert r["rows"][0]["status"] == "skipped"
    assert r["rows"][0]["name"] == "a.md"


def test_same_sha_twice_keeps_both_rows():
    """同じ sha の文書が2つ在れば2行とも残す。潰さない。"""
    docs = [{"name": "a.md", "skeleton_sha": "x"}, {"name": "a_v2.md", "skeleton_sha": "x"}]
    r = pending_contracts(docs, [])
    assert len(r["rows"]) == 2
    assert r["pending"] == 2


def test_sha_only_in_submitted_is_ignored():
    """投入済みにしか無い sha は扱わない。"""
    r = pending_contracts([{"name": "a.md", "skeleton_sha": "x"}], ["y"])
    assert len(r["rows"]) == 1
    assert r["pending"] == 1


def test_order_is_the_given_order():
    """並びは渡された順のまま。"""
    docs = [{"name": "z.md", "skeleton_sha": "1"}, {"name": "a.md", "skeleton_sha": "2"}]
    r = pending_contracts(docs, [])
    assert [x["name"] for x in r["rows"]] == ["z.md", "a.md"]


def test_three_numbers_sum_to_the_doc_count():
    """3つの数の合計は文書の数と等しい。"""
    docs = [{"name": "a.md", "skeleton_sha": "x"},
            {"name": "b.md", "skeleton_sha": "y"},
            {"name": "c.md", "skeleton_sha": ""}]
    r = pending_contracts(docs, ["y"])
    assert r["pending"] + r["already"] + r["skipped"] == 3
    assert r["pending"] == 1
    assert r["already"] == 1
    assert r["skipped"] == 1


def test_empty_docs_gives_zeros():
    """文書が無ければ3つとも 0。"""
    r = pending_contracts([], ["x"])
    assert r["rows"] == []
    assert r["pending"] == 0


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    d, s = [{"name": "a.md", "skeleton_sha": "x"}], ["y"]
    assert pending_contracts(d, s) == pending_contracts(d, s)


def test_result_has_all_four_keys():
    """4つのキーは どの場合も 欠けない。"""
    r = pending_contracts([], [])
    for k in ("rows", "pending", "already", "skipped"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★足場（★Claude・★★裏口を 作らない）

```
★★① `docs` = ★`egl/docs` の ★契約ブロック（`<<<2DER:SKELETON>>>`）を 持つ 文書
   ―― ★sha は ★★`contract_seal.extract_contract` が 出す 値を 使う（★★新造 0）
★★② `submitted` = ★★記録から（★`CREATE` の `payload["contract"]` の sha）
★★③ 投げるのは ★★★`/api/submit`（★★正式な 口＝★裏口を 作らない）
★★④ ★★1巡回で ★★★1件だけ 投げる（★★叩き続けない＝★Manager v0 と 同じ 作法）
★★⑤ 記録 = ★`event_trace` へ 1行（★新台帳 0）／ ★出す口 = ★既存 include に 欄
★★★止める条件 = ★同じ sha を ★★2回 投げない（★`already` に 入るので 自然に 止まる）
```

## 6. ★★受入（★★手番が いくつ 減ったかで 測る＝§14）

```
★★① ★`pending` の 件数と ★★名前が front door から 引ける
★★② ★★★人が 投げた 回数 = ★★0（★★1件でも 機械が 投げたら ★その数を 書く）
★★③ ★★同じ sha が ★2回 投げられていない（★`already` が 効いている 実物1件）
★★④ ★★`skipped` の 名前が 出る（★★★契約ブロックが 壊れている 文書が 見える）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 11本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増 ／ ★★裏口 0（★`/api/submit` を 使う）
★★⑦（★私）★★★次の 契約で ★MGR の 手番が ★1回 減った 事を ★数で 示す
   ―― ★★これが 効いていなければ ★★『減った』と 書かない（★§17）
```

## 7. ★★やらないこと

```
★★★どれを 投げるか 選ばない（★優先順位・重要度・期限＝★Manager の 仕事）
★★2件以上 まとめて 投げない（★1巡回 1件）
★★契約文書を ★機械に 書かせない（★★②は MGR 裁定で ★保留）
★★★『投入が 自動に なった』と 書かない ―― ★★人が 投げた 回数が ★0 に なるまで
```
