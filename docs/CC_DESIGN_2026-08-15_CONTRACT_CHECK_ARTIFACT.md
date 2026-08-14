開発者規律 確認済(v1.0)

# 【契約・1本】★成果物の **受領だけ** ―― ★★`check_artifact`（★★配置・接続は 入れない）

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-15 00:2x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 23:54**（★⑧成果物の 受領だけ ／ ★★配置・接続は 入れない）

---

## 1. ★★この関数の 仕事は 1つ（★★段を 混ぜない）

```
★★受領 = ★★『★受け取った 中身が ★記録と 一致するか』★だけ
★★★配置（★file に 置く）／ ★接続（★呼び手を 足す）／ ★使用 = ★★★入れない
   ―― ★理由 = ★Taka 正本 §9 ＝ ★★作った／置いた／繋いだ／使われた を ★同一視しない
   ―― ★★本日 我々が 4回 混同した 所 ∴ ★★関数の 段でも 分ける
```

## 2. ★★場合の 列挙（★★走らせる前に 出す）

```
★★① 中身が 在り ★記録の sha と 一致        → ★受け取れる ／ ★長さを 出す
★★② 中身が 空                              → ★受け取れない ／ 理由 `"empty"`
★★③ 中身が None                            → ★受け取れない ／ 理由 `"empty"`
★★④ 記録の sha が 空 か None                → ★受け取れない ／ 理由 `"no_recorded_sha"`
★★⑤ sha が 一致しない                      → ★受け取れない ／ 理由 `"sha_mismatch"`
     ―― ★★★両方の 値を 返す（★★どちらが 違うかを 人が 見られる）
★★⑥ 大文字小文字が 違うだけ                → ★★一致として 扱う（★16進の 表記ゆれ）
★★⑦ 受け取れる 時の 理由                    → ★`None`
★★⑧ 同じ入力を 2回 渡して ★同じ
★⑨ キーは ★どの場合も 欠けない
```

## 3. ★★骨格（★★定数 0個）

<<<2DER:SKELETON>>>
def check_artifact(artifact, recorded_sha):
    """受け取った中身が記録と一致するかだけを見る。置く・繋ぐ・使うは見ない。

    artifact: 受け取った中身。文字列。空や None も来る。
    recorded_sha: 記録に残っている sha256。16進の文字列。空や None も来る。

    返り値は {"receivable", "reason", "length", "computed_sha", "recorded_sha"} の辞書。

    receivable は受け取れるなら True、そうでなければ False。
    reason は受け取れるとき None。受け取れないときは次の語のどれか。
      "empty" … artifact が空、または None。
      "no_recorded_sha" … recorded_sha が空、または None。
      "sha_mismatch" … 計算した sha256 が recorded_sha と違う。
    length は artifact の文字数。artifact が None なら 0。
    computed_sha は artifact を utf-8 にして sha256 を取った16進の文字列。
      artifact が空か None なら None。
    recorded_sha は受け取った値をそのまま入れる。
    大文字小文字だけが違う sha は同じものとして扱う。
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

## 4. ★★封印試験

<<<2DER:IMMUTABLE_TESTS>>>
import hashlib

from impl import check_artifact


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_matching_sha_is_receivable():
    """sha が一致すれば受け取れる。"""
    r = check_artifact("abc", _sha("abc"))
    assert r["receivable"] is True
    assert r["reason"] is None
    assert r["length"] == 3


def test_empty_artifact_is_not_receivable():
    """中身が空なら受け取れない。"""
    r = check_artifact("", _sha("abc"))
    assert r["receivable"] is False
    assert r["reason"] == "empty"
    assert r["length"] == 0


def test_none_artifact_is_not_receivable():
    """中身が None でも同じ。"""
    r = check_artifact(None, _sha("abc"))
    assert r["receivable"] is False
    assert r["reason"] == "empty"
    assert r["length"] == 0


def test_missing_recorded_sha_is_not_receivable():
    """記録の sha が無ければ受け取れない。"""
    r = check_artifact("abc", "")
    assert r["receivable"] is False
    assert r["reason"] == "no_recorded_sha"


def test_none_recorded_sha_is_not_receivable():
    """記録の sha が None でも同じ。"""
    r = check_artifact("abc", None)
    assert r["reason"] == "no_recorded_sha"


def test_mismatch_returns_both_values():
    """一致しなければ両方の値を返す。"""
    r = check_artifact("abc", "0" * 64)
    assert r["receivable"] is False
    assert r["reason"] == "sha_mismatch"
    assert r["computed_sha"] == _sha("abc")
    assert r["recorded_sha"] == "0" * 64


def test_uppercase_sha_still_matches():
    """大文字小文字だけの違いは同じものとして扱う。"""
    r = check_artifact("abc", _sha("abc").upper())
    assert r["receivable"] is True


def test_computed_sha_is_none_when_empty():
    """中身が空なら computed_sha は None。"""
    r = check_artifact("", "x")
    assert r["computed_sha"] is None


def test_length_counts_characters():
    """length は文字数。"""
    r = check_artifact("abcd", _sha("abcd"))
    assert r["length"] == 4


def test_same_input_twice_gives_the_same_answer():
    """同じ入力を2回渡すと 同じ答えになる。"""
    a, b = "abc", _sha("abc")
    assert check_artifact(a, b) == check_artifact(a, b)


def test_result_has_all_five_keys():
    """5つのキーは どの場合も 欠けない。"""
    r = check_artifact(None, None)
    for k in ("receivable", "reason", "length", "computed_sha", "recorded_sha"):
        assert k in r
<<<2DER:END>>>

## 5. ★★足場（★Claude）

```
★★入力 = ★`GET /api/claude_packet?task_id=…` の ★`test_result.artifact` と ★`artifact_sha256`
★★出す口 = ★既存 include に ★欄を 1つ（★口 0増）
★★★受け取れた 物を ★★自動で 置かない（★配置は 別の 段＝★この契約に 入れない）
```

## 6. ★★受入

```
★★① ★受け取れた 件数 ／ ★受け取れない 件数（★★理由の 語ごとに）
★★② ★★`sha_mismatch` が 出た 時は ★★両方の 値が 記録に 残る
★★③ ★★本日 配置した 5件が ★★★`receivable` に なる（★★過去分で 検算できる）
★★④ ★★★置いた 件数を ★この欄に 混ぜない（★★受領と 配置を 分けた 実物）
★★⑤ ★`skeleton_missing` = 0 ／ ★封印試験 11本 passed ／ ★★定数 0個
★★⑥ ★LLM 0回 ／ ★新台帳 0 ／ ★口 0増
```

## 7. ★★やらないこと

```
★★★置かない ／ ★繋がない ／ ★使ったかを 見ない（★★段を 混ぜない＝★Taka 正本 §9）
★★『受け取れた』を ★『使われている』と 書かない
```
