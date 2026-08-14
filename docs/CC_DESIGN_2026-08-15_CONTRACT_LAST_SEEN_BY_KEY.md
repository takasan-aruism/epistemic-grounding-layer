開発者規律 確認済(v1.0)

# 【契約・1本】★『いつから 出ていないか』―― ★★`last_seen_by_key`（★★時計を 中で 呼ばない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 04:3x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 04:16**（★材料の 在りかを 先に 確かめてくれた ／ ★中身も 指定 ／ ★`gap_streak` v2 と 分けるかは 私が 決めてよい）

---

## 1. ★★私の 決め（★★分ける・★1本だけ）

```
★★`gap_streak` v2 と ★★分ける
★★理由 = ★★★鍵が 違う（★`gap_streak` は ★食い違いの 種類 ／ ★これは ★記録の `key`）
   ―― ★★1本に すると ★★2つの 鍵が 1つの 欄に 混ざる（★★本日 何度も 揉めた 形）
★★1周 1つ（★MGR の 作法を そのまま）
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 同じ `key` が 複数              → ★1行 ／ ★`last_ts` は ★最も 後ろ ／ ★`count` は 件数
★★② `ts` が 無い 行                 → ★★`no_ts` に 数える ／ ★★★`rows` には 入れない（★時刻が 決まらない）
★★③ `ts` が 空文字                  → ★★②と 同じ
★★④ `now` が None                   → ★★`age_seconds` は ★None（★★嘘を 足さない）
★★⑤ `now` が 在る                   → ★秒の 整数（★★切り捨て）
★★⑥ `now` が `last_ts` より 前       → ★★★負の まま 返す（★★0 に 丸めない）
★★⑦ 並びは ★★`key` の 昇順
★★⑧ 何も 無い                        → ★`rows` 空 ／ `checked` 0 ／ `no_ts` 0
★★⑨ 同じ入力を 2回 渡して ★同じ
★⑩ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個・★★時計を 中で 呼ばない）

<<<2DER:SKELETON>>>
def last_seen_by_key(events, now=None):
    """記録の key ごとに、最後に出た時刻と、そこからの経過を出す。今の時刻は中で取らない。

    events: {"key", "ts"} の辞書の一覧。ts は "2026-08-15T03:41:05.450933" の形の文字列。
    now: 今の時刻。同じ形の文字列。渡されなければ None。

    返り値は {"rows", "checked", "no_ts"} の辞書。

    rows は key ごとに {"key", "last_ts", "count", "age_seconds"}。key の昇順。
      last_ts はその key の ts のうち一番後ろのもの。文字列の大小で比べる。
      count はその key の行数。ts の無い行は数えない。
      age_seconds は now から last_ts を引いた秒数。小数点以下は切り捨てた整数。
        now が None なら None。now が last_ts より前なら負の数のまま。
    checked は events の数。
    no_ts は ts が無い、または空の行の数。その行は rows に入れない。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import last_seen_by_key


def test_latest_ts_is_kept():
    """同じ key が複数あれば一番後ろの ts を残す。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T01:00:00"},
          {"key": "A.a", "ts": "2026-08-15T03:00:00"}]
    r = last_seen_by_key(ev)
    assert r["rows"][0]["last_ts"] == "2026-08-15T03:00:00"
    assert r["rows"][0]["count"] == 2


def test_no_now_gives_none_age():
    """now が渡されなければ age_seconds は None。"""
    r = last_seen_by_key([{"key": "A.a", "ts": "2026-08-15T01:00:00"}])
    assert r["rows"][0]["age_seconds"] is None


def test_age_seconds_is_a_truncated_integer():
    """age_seconds は秒の整数。小数点以下は切り捨てる。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T01:00:00"}]
    r = last_seen_by_key(ev, now="2026-08-15T01:00:10.900000")
    assert r["rows"][0]["age_seconds"] == 10


def test_negative_age_is_kept():
    """now が last_ts より前なら負のまま返す。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T03:00:00"}]
    r = last_seen_by_key(ev, now="2026-08-15T02:00:00")
    assert r["rows"][0]["age_seconds"] == -3600


def test_missing_ts_is_counted_and_excluded():
    """ts が無い行は no_ts に数え、rows に入れない。"""
    r = last_seen_by_key([{"key": "A.a"}])
    assert r["no_ts"] == 1
    assert r["rows"] == []


def test_empty_ts_is_the_same():
    """ts が空文字でも同じ扱い。"""
    r = last_seen_by_key([{"key": "A.a", "ts": ""}])
    assert r["no_ts"] == 1
    assert r["rows"] == []


def test_count_excludes_rows_without_ts():
    """count は ts のある行だけ数える。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T01:00:00"}, {"key": "A.a"}]
    r = last_seen_by_key(ev)
    assert r["rows"][0]["count"] == 1
    assert r["no_ts"] == 1


def test_rows_are_sorted_by_key():
    """並びは key の昇順。"""
    ev = [{"key": "Z.z", "ts": "2026-08-15T01:00:00"},
          {"key": "A.a", "ts": "2026-08-15T01:00:00"}]
    r = last_seen_by_key(ev)
    assert [x["key"] for x in r["rows"]] == ["A.a", "Z.z"]


def test_checked_counts_every_row():
    """checked は渡された行の数。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T01:00:00"}, {"key": "B.b"}]
    r = last_seen_by_key(ev)
    assert r["checked"] == 2


def test_empty_input():
    """何も無ければ 3つとも空か 0。"""
    r = last_seen_by_key([])
    assert r["rows"] == []
    assert r["checked"] == 0
    assert r["no_ts"] == 0


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    ev = [{"key": "A.a", "ts": "2026-08-15T01:00:00"}]
    assert last_seen_by_key(ev, now="2026-08-15T02:00:00") == last_seen_by_key(ev, now="2026-08-15T02:00:00")


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = last_seen_by_key([])
    for k in ("rows", "checked", "no_ts"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★★入力 = ★記録の 行（★`key` と `ts`）／ ★`now` は ★★足場が 渡す（★★関数の 中で 時計を 呼ばない）
★★出す口 = ★既存 include に ★欄を 1つ
★★★`now` を 渡した 事を ★記録に 残す（★★渡さなければ `age_seconds` が None＝★それも 事実）
```

## 6. ★★受入

```
★★① ★`rows` が front door から 引ける（★`key` ／ `last_ts` ／ `count` ／ `age_seconds`）
★★② ★★`no_ts` の 件数（★★0件でも 書く）
★★③ ★★同じ問いを 2回 引いて ★★`last_ts` が 動かない（★★★引く 行為で 増えない）
★★④ ★★★MGR が 見込んだ 13本（★鍵を 替えた 時の 古い行）が ★★★名前で 出るか
   ―― ★★出れば ★見込みが 当たり ／ ★★出なければ ★★見込みが 外れ（★★そう 書く）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 12本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★消さない（★★『いつから 出ていないか』を 出すだけ＝★消すかは 別の 話・★MGR 逐語）
★★『古い』『死んでいる』と 書かない ―― ★★★秒数と 名前だけ（★判定は 上）
★★`gap_streak` と ★1本に しない（★★鍵が 違う）
```
