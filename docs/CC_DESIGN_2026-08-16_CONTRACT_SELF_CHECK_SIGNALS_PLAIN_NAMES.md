# 【契約・1本／★実名で 書き直した】★計器が **自分の 出力を 点検する** ―― ★★`self_check_signals`（★★合否を 出さない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-16 16:5x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 17:41**（★門が 止めた＝★指示語の 1語に 部分一致（★★その語を ここに 書かない＝★★書くと この文書も 止まる） ／ ★指示語を 実名に する＝★門を 迂回しない）／ **MGR 16:25**（★`self_check` に 検知を 2つ ／ ★場合を 先に 列挙 ／ ★出てはいけない 結果を 1つ）
／ **Taka 指示**（★『タイミングを 合わせて 入れる』＝★本線の 1手が 終わった 後）

---

## 0. ★★何を 拾うか（★★本日 実際に 起きた 2つだけ）

```
★★①『★照合の 結果が ★全件 同じ語』 ―― ★実物＝★★18/18 が `no_send`（★★鍵が 違っていた）
   ―― ★★★全部 同じ に なるのは ★『世界が そうだった』より ★『★引き方を 間違えた』方が 多い
★★②『★前回より 減った』 ―― ★実物＝★★その巡回の 値だけ 返す 欄で ★事実が 消えた（★本日 4件）
★★★どちらも ★★合否を 出さない ―― ★★出すのは ★『★こういう 形が 出た』という 事実だけ
   ―― ★★★重いか どうかは Manager が 決める（★本日 何度も 使った 線）
```

## 1. ★★★出てはいけない 結果（★★規律 v1.21 ／ ★★私の 本日の 非を 試験に する）

```
★★★『★対象が 0件 の 時に ★合格・通った と 読める 物を 出す』
   ―― ★実物＝★私は ★★存在しない 一覧を 回して ★『0件 だから 受入③は 満たす』と 書いた
   ―― ★★★空の 一覧への 検査は ★必ず 通る（★★不在が 遵守に 見える）
★★∴ ★この部品は ★★『調べた 数』を ★必ず 返す ―― ★★★`0 件だった` と `調べていない` を ★同じ 顔に しない
```

## 2. ★★場合の 列挙（★★走らせる前に 出す ／ ★★MGR の 8つ ＋ ★私の 1つ）

```
★★①-ア 全件 同じ語 かつ 件数 ≥ `min_count`   → ★`all_same` を 出す
★★①-イ 件数 0                                → ★★出さない（★★`checked` が 0 と 出る）
★★①-ウ 2語 以上                              → ★出さない
★★①-エ 件数が `min_count` 未満               → ★出さない（★偶然が 起きる 大きさ）
★★②-ア 前回 在り かつ 今回 < 前回            → ★`decreased` を 出す
★★②-イ 前回 に その名前が 無い                → ★出さない（★★比べる 相手が 無い）
★★②-ウ 同数                                  → ★出さない
★★②-エ 今回 に 無く 前回 に 在る              → ★★★`decreased` を 出す（★★★私が 足した＝★欄が 消えるのは 最大の 減り）
★★③ `by_signal` は ★2語 全部 キーを 持つ（★0件でも）
★★④ 並びは ★渡された 順
★★⑤ 同じ入力を 2回 渡して ★同じ
★⑥ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個 ／ ★★閾値は 呼び手が 渡す）

<<<2DER:SKELETON>>>
def self_check_signals(statuses, counts, previous, min_count):
    """計器の出力に、決まった形が出ていないかを見る。合否は決めない。

    statuses: 照合の結果の語の一覧。文字列の一覧。
    counts: 積み上げの欄のいまの値。名前をキー、数を値とする辞書。
    previous: 同じ欄の前回の値。名前をキー、数を値とする辞書。
    min_count: 全件同じ語を合図にするために必要な最小の件数。整数。

    返り値は {"rows", "by_signal", "checked"} の辞書。

    rows は出た合図の一覧。各要素は {"signal", "name", "detail"}。
    signal は "all_same" か "decreased" の2つの語のどれか。

    statuses の語がすべて同じで、statuses の件数が min_count 以上のとき
      signal は "all_same"、name は statuses の語、detail は statuses の件数にする。
      件数が min_count 未満のとき、語が2つ以上あるとき、件数が0のときは出さない。

    counts の名前ごとに previous と比べる。
      previous にない名前は出さない。
      previous に在り、counts に無いときは "decreased" を出し、detail は previous の値にする。
      両方に在り、counts の値が previous の値より小さいときは "decreased" を出し、
      detail は counts の値にする。同じか大きいときは出さない。
    decreased の並びは counts と previous を合わせた名前の、初めて現れた順。

    by_signal は "all_same" と "decreased" の2語を全部キーに持ち、件数を値にする。
    checked は {"statuses", "counts"} の辞書。実際に見た件数を入れる。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
from impl import self_check_signals


def test_all_same_word_is_a_signal():
    """全件同じ語で件数が足りていれば all_same。"""
    r = self_check_signals(["no_send"] * 3, {}, {}, 3)
    assert r["rows"][0]["signal"] == "all_same"
    assert r["rows"][0]["name"] == "no_send"
    assert r["rows"][0]["detail"] == 3


def test_empty_statuses_is_not_a_signal_and_checked_is_zero():
    """件数0では出さない。調べた数が0と分かる。0件と調べていないを同じ顔にしない。"""
    r = self_check_signals([], {}, {}, 3)
    assert r["by_signal"]["all_same"] == 0
    assert r["checked"]["statuses"] == 0


def test_checked_reports_the_number_actually_looked_at():
    """調べた数をそのまま返す。合図が出なくても数は出る。"""
    r = self_check_signals(["a", "b"], {"x": 1}, {"x": 1}, 3)
    assert r["checked"]["statuses"] == 2
    assert r["checked"]["counts"] == 1


def test_two_words_is_not_a_signal():
    """語が2つ以上なら出さない。"""
    r = self_check_signals(["no_send", "linked", "no_send"], {}, {}, 3)
    assert r["by_signal"]["all_same"] == 0


def test_below_min_count_is_not_a_signal():
    """件数が足りなければ出さない。"""
    r = self_check_signals(["no_send", "no_send"], {}, {}, 3)
    assert r["by_signal"]["all_same"] == 0


def test_min_count_is_taken_from_the_caller():
    """閾値は呼び手が渡す。部品は数を持たない。"""
    r = self_check_signals(["no_send", "no_send"], {}, {}, 2)
    assert r["by_signal"]["all_same"] == 1


def test_a_smaller_count_than_before_is_a_signal():
    """前回より減れば decreased。"""
    r = self_check_signals([], {"seg": 5}, {"seg": 9}, 3)
    assert r["rows"][0]["signal"] == "decreased"
    assert r["rows"][0]["name"] == "seg"
    assert r["rows"][0]["detail"] == 5


def test_no_previous_value_is_not_a_signal():
    """前回に無い名前は出さない。比べる相手が無い。"""
    r = self_check_signals([], {"seg": 5}, {}, 3)
    assert r["by_signal"]["decreased"] == 0


def test_the_same_count_is_not_a_signal():
    """同数なら出さない。"""
    r = self_check_signals([], {"seg": 5}, {"seg": 5}, 3)
    assert r["by_signal"]["decreased"] == 0


def test_a_bigger_count_is_not_a_signal():
    """増えたら出さない。"""
    r = self_check_signals([], {"seg": 9}, {"seg": 5}, 3)
    assert r["by_signal"]["decreased"] == 0


def test_a_name_that_disappeared_is_a_signal():
    """前回に在って今回に無い名前は decreased。欄が消えるのは最大の減り。"""
    r = self_check_signals([], {}, {"seg": 9}, 3)
    assert r["rows"][0]["signal"] == "decreased"
    assert r["rows"][0]["name"] == "seg"
    assert r["rows"][0]["detail"] == 9


def test_by_signal_has_both_words():
    """2語すべてキーを持つ。0件でも欄を消さない。"""
    r = self_check_signals([], {}, {}, 3)
    assert sorted(r["by_signal"].keys()) == ["all_same", "decreased"]
    assert set(r["by_signal"].values()) == {0}


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a = (["x", "x", "x"], {"s": 1}, {"s": 2}, 3)
    assert self_check_signals(*a) == self_check_signals(*a)


def test_result_has_all_three_keys():
    """3つのキーは どの場合も 欠けない。"""
    r = self_check_signals([], {}, {}, 3)
    for k in ("rows", "by_signal", "checked"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude・★★口 0増）

```
★`statuses` = ★`relay_chain` の 各行の `status`（★★いま 18件）
★`counts` / `previous` = ★★積み上げの 欄だけ（★★その場の 値の 欄は 渡さない＝★MGR の ②-エ）
★`min_count` = ★★呼び手が 渡す（★★部品に 数を 書かない）
★★出す先 = ★★既存の `self_check` 欄（★★新しい 欄を 作らない）
```

## 6. ★★受入（★MGR の 3つ ＋ ★私から 1つ）

```
★★① `self_check` に ★2つの 検知が 出る（★★`by_signal` の 2語が ★0件でも）
★★② ★★今日の 実物（★18/18 `no_send`）を 入れたら ★鳴る
   ―― ★★★但し ★★いまの 実物は ★`no_send` 0 ／ `no_receive` 12 ／ `no_locator` 2 ／ `linked` 4
      ＝ ★★★4語 在る ∴ ★★いま 入れても 鳴らない＝★★★それが 正しい（★★『鳴らない』を 失敗と 読まない）
   ―― ★★∴ ★②の 確かめ方 = ★★★当時の 18件を 手で 入れて 鳴るか（★★試験の 中で 縛る）
★★③ ★★0件を 入れても ★『合格』と 出ない ―― ★★`checked.statuses` が ★0 と 出る
★★★④（★私）★★`decreased` が 出た 時、★その名前が ★★積み上げの 欄か どうかを ★足場が 保証する
   ―― ★★★その場の 値の 欄を 渡すと ★毎回 鳴る（★★偽の 合図＝★本日 私が 出した 型）
```

## 7. ★★やらないこと

```
★★★合否の 語を 返さない（★`ok` ／ `passed` ／ `異常` を 作らない）
★★★閾値を 部品に 書かない（★呼び手が 渡す）
★★★『鳴らなかった＝正常』と 書かない ―― ★★正しくは ★『★N 件 調べて ★合図 0』
★★検知を 3つ目に 増やさない（★★本日 実際に 起きた 2つだけ＝★★型が 増えたら その時）
```
