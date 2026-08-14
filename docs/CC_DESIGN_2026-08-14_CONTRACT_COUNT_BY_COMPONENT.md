開発者規律 確認済(v1.0)

# 【契約・2DER へ投げる1件】★記録から **直接** 数える ―― ★★`count_by_component`

宛: MGR（★封入と 投入）／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 12:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 裁定 12:00**「★数える口は ★2DER に 書かせる（★純粋な 数え上げ ∴ ★契約に しやすい ／ ★Claude が 書いたら また 戻る）」

**★★MGR の 訂正を 受ける（★私の 1点）**
> ★安全弁が journal に 見当たらないのは ★★記録が 成功している から ＝ **★正しい 振る舞い**（★欠陥では ない）。
> ★私は ★不在を ★疑いの 側に 置いた ―― ★★『★鳴らない計器』と『★壊れた計器』を ★分けずに 書いた。

**★★worker に 届くのは 3つだけ** ―― ★骨格 ／ ★封印試験 ／ ★共通テンプレート ∴ **★条件は 試験に 書いた**

---

## 1. ★★なぜ この形か（★★親子を 使わない）

```
★★★壊れていた物 = ★辺の `count`（★`parent_event_id` の 隣接から 作る）
   ―― ★MGR の 一撃 = ★★`MANAGER_V0.tick` が ★★`count 1172` ／ `first_as_of 2026-07-28`
      ＝ ★★★本日 作った 部品が ★7月28日に 1172回 動く 事は ★無い
★★★∴ ★新しい口は ★★★親子を 1回も 使わない ＝ ★★行を そのまま 数えるだけ
★★★∴ ★純粋な 数え上げ ＝ ★★外に 何も 触らない（★file も 時刻も 乱数も 使わない）＝ ★契約に しやすい
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★① 空の 一覧            → ★`total=0` ／ `by={}` ／ `unknown=0`
★② 1件                  → ★その1件だけ
★③ 同じ組が 3件         → ★★1つの キーに ★3（★★別々に 並べない）
★④ 違う `function`      → ★★別の キー（★component が 同じでも 分ける）
★★⑤ 欄が 欠けた 行      → ★★★捨てない ＝ ★`UNKNOWN.UNKNOWN` で 数える ／ `unknown` に 1
★★⑥ 空文字の 欄        → ★★⑤と 同じ 扱い（★★『空』と『無い』を 別々に しない）
★★⑦ ★★by の 値の 合計 = ★★★total（★★取りこぼし 0＝★これが 一番 効く）
★★⑧ キーは ★★昇順（★同じ入力 → 同じ並び）
★★⑨ ★★同じ一覧を 2回 渡して ★★★同じ（★決定論）
★⑩ 3つの キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
UNKNOWN = "UNKNOWN"


def count_by_component(events):
    """記録の一覧を (component, function) ごとに数える。

    events: 記録の一覧。各要素は {"component": 文字列, "function": 文字列} の辞書。

    返り値は dict で、キーは total / by / unknown。

    total は 受け取った行の数。
    by は "component.function" をキー、件数を値とする辞書。キーは昇順に並べる。
    unknown は component と function のどちらかが 空、または 欄が無い 行の数。
      その行は by の中で "UNKNOWN.UNKNOWN" として数える。

    by の値の合計は total と必ず等しい。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 4. ★★封印試験（★★1バイトも 変えない・★★曖昧な `in` を 置かない）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import count_by_component, UNKNOWN


def test_empty_list():
    """空の一覧なら total は 0、by は空、unknown は 0。"""
    r = count_by_component([])
    assert r["total"] == 0
    assert r["by"] == {}
    assert r["unknown"] == 0


def test_one_row():
    """1件なら そのキーが1つだけ。"""
    r = count_by_component([{"component": "MANAGER_V0", "function": "tick"}])
    assert r["total"] == 1
    assert r["by"] == {"MANAGER_V0.tick": 1}
    assert r["unknown"] == 0


def test_same_pair_is_summed():
    """同じ組が3件なら 1つのキーに 3。"""
    rows = [{"component": "MANAGER_V0", "function": "tick"} for _ in range(3)]
    r = count_by_component(rows)
    assert r["by"] == {"MANAGER_V0.tick": 3}
    assert r["total"] == 3


def test_different_function_is_a_different_key():
    """component が同じでも function が違えば 別のキー。"""
    r = count_by_component([{"component": "DW", "function": "a"},
                            {"component": "DW", "function": "b"}])
    assert r["by"] == {"DW.a": 1, "DW.b": 1}


def test_missing_field_is_counted_as_unknown():
    """欄が無い行は 捨てずに UNKNOWN として数える。"""
    r = count_by_component([{"component": "DW"}])
    assert r["unknown"] == 1
    assert r["by"] == {"UNKNOWN.UNKNOWN": 1}
    assert r["total"] == 1


def test_empty_string_is_also_unknown():
    """空文字の欄も 欄が無いのと同じ扱い。"""
    r = count_by_component([{"component": "", "function": "tick"}])
    assert r["unknown"] == 1
    assert r["by"] == {"UNKNOWN.UNKNOWN": 1}


def test_sum_of_by_equals_total():
    """by の値の合計は total と等しい。取りこぼしを作らない。"""
    rows = [{"component": "A", "function": "x"},
            {"component": "A", "function": "x"},
            {"component": "B", "function": "y"},
            {"component": "B"},
            {}]
    r = count_by_component(rows)
    assert r["total"] == 5
    assert sum(r["by"].values()) == 5
    assert r["unknown"] == 2


def test_keys_are_sorted():
    """キーは昇順に並ぶ。"""
    r = count_by_component([{"component": "Z", "function": "z"},
                            {"component": "A", "function": "a"}])
    assert list(r["by"].keys()) == ["A.a", "Z.z"]


def test_same_input_twice_gives_the_same_answer():
    """同じ一覧を2回渡すと 同じ答えになる。"""
    rows = [{"component": "A", "function": "x"}, {"component": "B", "function": "y"}]
    assert count_by_component(rows) == count_by_component(rows)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = count_by_component([])
    for k in ("total", "by", "unknown"):
        assert k in r
<<<2DER:END>>>
```

## 5. ★★この関数を どこに 繋ぐか（★★足場＝Claude・★★worker には 渡さない）

```
★★入力 = ★`event_trace` の 行（★`observed_edges._events()` が 既に 読んでいる＝★★新しい 読み手を 作らない）
★★出す口 = ★★`GET /api/control?include=record_counts`（★口 0増・★既定では 計算しない）
★★★親子を 使わない ＝ ★`parent_event_id` を ★1回も 触らない
```

## 6. ★★受入（★★MGR の 3点 ＋ ★私から 2つ）

```
★★① ★★同じ問いを 2回 引いて ★★★同じ（★★★書き込みが 走っている 間でも）
★★② ★★`MANAGER_V0.tick` の 数が ★★本日の 実数と 合う（★★★1172 では ない）
★★③ ★★`observed_edges` に ★★鍵の 1行
   ―― ★逐語案 = 「★★この数は ★親子の 隣接から 作った 推定であって ★呼び出し回数では ない ／
      ★★書き込みが 走っている 間は ★過去の 行の 親が 入れ替わる（★止まっている 間は 動かない）」
★★④（★私）★★`total` = ★`events_read` と ★同じ数（★★2つの 計器が 同じ物を 指す）
★★⑤（★私）★★Claude が 書いた 実装行 = ★★★0（★★足場の 配線は 別に 行数を 報告する）
```

## 7. ★★言い方（★★MGR が 名指しした 物を そのまま 引き継ぐ）

```
★★★証拠に しない 数（★親子由来）= ★`route18` ／ `both_sided` ／ `OBSERVED_SEGMENT`
   ／ `OBSERVED_OWNER` ／ ★辺の `count`
   ―― ★★『区別力が 弱い』では なく ★★★『数として 成り立っていない』と 書く（★MGR 逐語）
★★★生きている 物 = ★`structure_runs` ／ `events_read` ／ ★`/api/etrace?task_id=` の 行
★★『安定している』と 書かない ―― ★★★止まっている 間に 測ったのかを 併記する
```
