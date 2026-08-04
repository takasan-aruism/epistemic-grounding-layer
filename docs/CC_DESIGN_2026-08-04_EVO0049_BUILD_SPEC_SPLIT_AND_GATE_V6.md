# 【BUILD SPEC v6】`EVO-0049` — **★規則③を縛る。★v1.13 の対応表を付ける**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 14:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035` ／ 方針: `ITEM-2DER-EVO-0057`
- **★v1〜v5 との関係**: ★差し替えない・追記しない。**★本書が実装源**
- **★変えるのは ★段0 の試験だけ**（★13→16本）。★段3（依頼文 v5 版・骨格・試験7本）は **★1文字も変えない**
- **★私の予告**: ★段0 16本 ／ ★段3 7本 ／ ★Claude の配線 **11行**（★v5 のまま・★既に入っている）
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★★v1.13 の対応表（★規則1つ＝試験1本・★機械が数えられる形）

| # | ★依頼文の規則（逐語） | ★縛る試験 |
|---|---|---|
| R1 | 空行（`\n\n` 以上）で区切れる範囲 → `"PARAGRAPH"` | `test_all_three_kinds_appear_when_all_markers_present` |
| R2 | 行頭が `-` `・` `*` または 数字+`.` / 数字+`)` → `"BULLET"` | **★`test_bullet_without_star_is_still_bullet`** |
| **R3** | **`。！？` の直後で区切れる範囲 → `"SENTENCE"`** | **★`test_sentence_kind_is_produced_by_punctuation`**（★本書で追加） |
| R4 | ①②③は その印が**実際に在る所**だけで範囲を作る | `test_no_break_gives_single_paragraph` |
| R5 | 候補は text 全体を覆う（欠落を作らない） | `test_conservation_sum_equals_text_len` |
| R6 | 半開区間・重複しない | `test_no_overlap_and_no_gap` |
| R7 | 1つも見つからなければ 1件の `"PARAGRAPH"` | `test_no_break_gives_single_paragraph` |
| R8 | text が空なら `[]` | `test_empty_gives_no_candidates` |
| R9 | `text_len` は常に `len(text)` | `test_text_len_is_always_len` |
| R10 | kind は3語のいずれか（他を作らない） | `test_kind_never_outside_three_words` |
| R11 | 原文を1文字も変えない・写しを返さない | `test_original_text_is_reconstructable` / `test_result_carries_no_copy_of_the_text` |
| R12 | 決定論（同じ入力で同じ出力） | `test_deterministic_across_three_calls` |

```
★★対照（★規則ではなく ★測り方）: ★v1.12 の癖振り＝`test_star_is_not_what_decides_bullet`
★★★陽性対照＝`test_positive_control_one_line_many_sentences_splits`（★本書で追加）
★★★★★実物の被覆＝`test_real_text_splits_into_two_or_more` / `test_real_bullet_text_yields_a_bullet_kind`
★★★★★★★★合計 ★16本（★12規則 + 対照4本のうち ★重複を除いた実数）
```

## 2. ★足す3本（★他の13本は1文字も変えない）

```python
def test_sentence_kind_is_produced_by_punctuation():
    """★規則③(。！？ の直後で区切る→SENTENCE)を直接 縛る。★を1つも含まない入力で確かめる。"""
    t = "一つ目の用件です。二つ目の用件です。三つ目の用件です。"
    kinds = [c["kind"] for c in impl.segment_candidates(t)["candidates"]]
    assert kinds.count("SENTENCE") >= 3, kinds

def test_positive_control_one_line_many_sentences_splits():
    """★陽性対照: 実物(REAL_A)は1行に句点が3つ在る。★2用件以上に割れること。
    ★2026-08-04 の走行では ここが1件のままだった(=割れなかった)。"""
    line = [l for l in REAL_A.splitlines() if sum(l.count(c) for c in "。！？") >= 2][0]
    cands = impl.segment_candidates(line)["candidates"]
    assert len(cands) >= 2, cands
    assert any(c["kind"] == "SENTENCE" for c in cands), cands

def test_all_three_kinds_appear_when_all_markers_present():
    """★段落・箇条書き・句点が混ざった入力で ★3種すべてが出ること。"""
    t = "前置きの段落です。\n\n- 箇条書き一つ目\n- 箇条書き二つ目\n\n文が二つ。続きの文です。"
    kinds = set(c["kind"] for c in impl.segment_candidates(t)["candidates"])
    assert kinds == {"PARAGRAPH", "BULLET", "SENTENCE"}, kinds
```

**★陽性対照の入力は ★実物**（★`REAL_A` の中から ★句点2つ以上の行を ★機械で選ぶ）＝ **★作っていない**。
★実測: `REAL_A` の句点は **★227 / 240 / 284** の3箇所で、**★同一行に在る**。

## 3. ★段0 の封印試験（★16本・★全文）

```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★fixture は実物。GET /api/etrace?run_id=ETR-2b0f009d55cd の ENTRY.raw_input から採取(手書きでない)
REAL_A = '<<<2DER:' + 'PROGRESS>>>\nitem: ITEM-2DER-EVO-0049\nstatus: PROPOSED\nactor: Taka\nstage: PLAN\ntitle: 1問い合わせを複数明細に分ける(明細ごとに HBB-30 の門を通し、揺れるものは確定しない)\nnote: next=MGR / 親: ITEM-2DER-EVO-0035 / ★戻す条件『明細に分ける形が決まった時』を Taka が 2026-08-04 に満たした。DEFERRED を解く。★Taka 裁定=(1)Qwen に割らせる方が筋がよい (2)★『割っただけ』は弱い。RRI の本来の機能は『何がし'
REAL_B = '8) / 陽性=わざと2用件を1文に詰めた入力が割れるか / 再現=3シードで収束するか(命名 DE-0537 と同じ手) / 保存則=欠落0 / ★fixture は rri_records の★実物から取る。★手書き禁止(2026-08-03 に手書き fixture が台帳の実形式と違い『試験は通り実データで落ちた』事故) / ★worker に渡せる純関数=段0(正規化と候補列挙)と段3(保存則の検査)の2件 ∴ 着手前に『渡せる塊が在るか』に答えられる(Taka 裁定 v1.8) / ★副次効果=『前提が足りない』を調査の引き金にできれば、research_signal の★14語固'


def test_empty_gives_no_candidates():
    assert impl.segment_candidates("")["candidates"] == []

def test_text_len_is_always_len():
    for t in ("", "abc", REAL_A):
        assert impl.segment_candidates(t)["text_len"] == len(t)

def test_no_break_gives_single_paragraph():
    v = impl.segment_candidates("切れ目のない一続きの文字列")
    assert len(v["candidates"]) == 1
    assert v["candidates"][0]["kind"] == "PARAGRAPH"

def test_real_text_splits_into_two_or_more():
    assert len(impl.segment_candidates(REAL_A)["candidates"]) >= 2

def test_real_bullet_text_yields_a_bullet_kind():
    kinds = [c["kind"] for c in impl.segment_candidates(REAL_B)["candidates"]]
    assert "BULLET" in kinds, kinds

def test_conservation_sum_equals_text_len():
    v = impl.segment_candidates(REAL_A)
    assert sum(c["end"] - c["start"] for c in v["candidates"]) == v["text_len"]

def test_no_overlap_and_no_gap():
    cs = sorted(impl.segment_candidates(REAL_A)["candidates"], key=lambda c: c["start"])
    assert cs[0]["start"] == 0
    for x, y in zip(cs, cs[1:]):
        assert x["end"] == y["start"]

def test_kind_never_outside_three_words():
    for t in (REAL_A, REAL_B, "a"):
        for c in impl.segment_candidates(t)["candidates"]:
            assert c["kind"] in ("PARAGRAPH", "BULLET", "SENTENCE"), c

def test_original_text_is_reconstructable():
    cs = sorted(impl.segment_candidates(REAL_A)["candidates"], key=lambda c: c["start"])
    assert "".join(REAL_A[c["start"]:c["end"]] for c in cs) == REAL_A

def test_result_carries_no_copy_of_the_text():
    for c in impl.segment_candidates(REAL_A)["candidates"]:
        assert set(c) == {"start", "end", "kind"}, c

def test_deterministic_across_three_calls():
    r = [impl.segment_candidates(REAL_A) for _ in range(3)]
    assert r[0] == r[1] == r[2]

def test_star_is_not_what_decides_bullet():
    """★v1.12: 実データの癖(★)を振る。★を外しても kinds が変わらないこと。
    ★変われば『★の有無で決めている』=癖に合わせている。"""
    plain = REAL_B.replace("★", "")
    k1 = [c["kind"] for c in impl.segment_candidates(REAL_B)["candidates"]]
    k2 = [c["kind"] for c in impl.segment_candidates(plain)["candidates"]]
    assert k1 == k2, (k1, k2)

def test_bullet_without_star_is_still_bullet():
    """★依頼文の規則②(行頭が - ・ * / 数字+. / 数字+))を直接 縛る。★を1つも含まない入力で確かめる。"""
    t = "- 一つ目\n- 二つ目\n3) 三つ目"
    kinds = [c["kind"] for c in impl.segment_candidates(t)["candidates"]]
    assert kinds.count("BULLET") >= 3, kinds

def test_sentence_kind_is_produced_by_punctuation():
    """★規則③(。！？ の直後で区切る→SENTENCE)を直接 縛る。★を1つも含まない入力で確かめる。"""
    t = "一つ目の用件です。二つ目の用件です。三つ目の用件です。"
    kinds = [c["kind"] for c in impl.segment_candidates(t)["candidates"]]
    assert kinds.count("SENTENCE") >= 3, kinds

def test_positive_control_one_line_many_sentences_splits():
    """★陽性対照: 実物(REAL_A)は1行に句点が3つ在る。★2用件以上に割れること。
    ★2026-08-04 の走行では ここが1件のままだった(=割れなかった)。"""
    line = [l for l in REAL_A.splitlines() if sum(l.count(c) for c in "。！？") >= 2][0]
    cands = impl.segment_candidates(line)["candidates"]
    assert len(cands) >= 2, cands
    assert any(c["kind"] == "SENTENCE" for c in cands), cands

def test_all_three_kinds_appear_when_all_markers_present():
    """★段落・箇条書き・句点が混ざった入力で ★3種すべてが出ること。"""
    t = "前置きの段落です。\n\n- 箇条書き一つ目\n- 箇条書き二つ目\n\n文が二つ。続きの文です。"
    kinds = set(c["kind"] for c in impl.segment_candidates(t)["candidates"])
    assert kinds == {"PARAGRAPH", "BULLET", "SENTENCE"}, kinds
<<<2DER:END>>>
```

## 4. ★段3（★v5 のまま・★1文字も変えない）

```
★依頼文・骨格・試験7本 とも ★v5 の通り。★本書では ★触らない。
```

## 5. ★★投入前に私が測った

```
★段0(16本): ★`extract_contract` → ★通る（16本）／★`extract_progress` → ★None
★★∴ ★『投入して弾かれる』も ★『台帳が書き換わる』も ★起きない
```

## 6. ★★私の不備（★本日8回目・★同じ単位で3回目）

```
★この単位だけで ★3回=(1)規則②を縛らず→『★』依存 (2)依頼文の2文が落ち→本体が空 (3)規則③を縛らず→句点で割らない
★★★3回とも ★同じ形=★『依頼文に書いた規則を ★試験に写していない』
★★★★★v1.11(書いたら縛れ)では ★足りなかった=★『どれを縛ったか ★数えられない』
★★★★★★∴ ★v1.13 の対応表（★§1）＝ ★規則に ★番号を振り、★試験名を ★1対1で並べる。
   ★★これで ★『縛っていない規則』が ★★表の空欄として ★機械で見える。
★★★★★★★★私が次からやること=★契約を書いたら ★§1 の表を ★先に作る（★試験を書く前に）。
   ★★表に空欄が在るまま ★SPEC を出さない。
```

## 7. 受入（★v5 を引き継ぐ・★1つ足す）
```
★(1) worker が2件を書く（★Claude は本文0行）／★(2) ★段0 16本・段3 7本 全通
★(3) 保存則が機械で出る ／★(4) 門の判定が明細ごとに出る
★(5) 4つの対照の結果を全部 書く
★★★(5-b) ★★陽性対照が ★通ること（★前回は ★失敗した）＝ ★`test_positive_control_…` が ★落ちないこと
★(6) 配線行数 ／★(7) 戻せる ／★(8) 61本を走らせない ／★(9) 出せなければ『出せなかった』と書いて止まる
★(10) 落ちたら『どの規則で落ちたか』を ★§1 の R番号で書いて止まる（★依頼文を直さない）
★(11) 封入前に ★§1 の表に ★空欄が無いことを確かめる（★規則と試験が1対1）
```

## 8. 禁止（★v1〜v5 を引き継ぐ）
```
★段0 の既存13本／段3 の7本を変える ／ ★骨格・依頼文を触る（★v5 版が正）
★陽性対照の入力を ★手で作る（★実物から機械で選ぶ）
★既存資産を作り直す ／ ★段0 で割る ／ ★4軸の LLM 測定 ／ ★段2 の分岐
★半端な配線を live にする（★MGR の裁定どおり ★規則③が入るまで再起動しない）
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
```
