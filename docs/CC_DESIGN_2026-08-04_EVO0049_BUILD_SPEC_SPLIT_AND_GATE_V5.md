# 【BUILD SPEC v5】`EVO-0049` — **★(a)(b)(c) を1本に。★癖を振る対照を入れた**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 13:3x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.12）** ／ 親: `ITEM-2DER-EVO-0035` ／ 方針: `ITEM-2DER-EVO-0057`
- **★v1〜v4 との関係**: ★差し替えない・追記しない。**★本書が実装源**
- **★私の予告**: ★段0 の試験 **13本**（★11→13）／★段3 の試験 **7本**（★不変）／★Claude の配線 **11行**
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★(c) 作り直しの口 — **★無い。★但し閉塞ではない**（★既に台帳へ回答済・再掲）

```
★`workcell.create_task:368` 逐語『if _read_events(task_id): raise WorkflowViolation(task already exists)』
   ＝ ★同一 task の作り直しは ★機構が禁じている（★追記式の台帳に CREATE を2つ作らない＝★仕様）
★`submit.py:503` 逐語『dw_task = "TASK-2DER-" + sha1(raw_input)[:8]』＝ ★task_id は ★依頼文から決まる
★★∴ ★依頼文を1文字でも変えれば ★別 task が立つ ＝ ★これが正規の「やり直し」
★★★本件は ★依頼文を直す ∴ ★新しい task が ★自然に立つ ＝ ★口を追加しない
★★★★`68AB3AA4`(JUDGE_REQUIRED)は ★そのまま残す（★失敗の記録・★消さない・遡って直さない）
```

## 2. ★(a) 段3 の依頼文 — **★段0 と同じ2文を足す**（★試験7本と骨格は1文字も変えない）

```
明細が原文を過不足なく覆っているかを検査する純関数 impl.check_conservation を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ）
text_len = 原文の長さ（int）
spans = [ {"start": int, "end": int}, ... ]（★順不同でよい）
戻り値 = {"ok": bool, "covered": int, "missing": [[int,int],...], "overlap": [[int,int],...]}

・covered = 重複を除いて覆われた文字数。
・missing = 覆われていない範囲を start 順に。★無ければ []。
・overlap = 2回以上 覆われた範囲を start 順に。★無ければ []。
・ok は ★missing == [] かつ overlap == [] の時だけ True。
・spans が空で text_len が 0 なら ok は True（covered 0・missing []・overlap []）。
・★start >= end の span は ★無視する（★エラーにしない・★covered に数えない）。
```

```
★★★足したのは ★2文だけ（★『骨格は1文字も変えずに残し、その続きに実装の本体を書いてください』
   ★『試験は import impl と書いてください。2DER が作る成果物は必ず impl.py です』）
★★★★★v2 で ★括弧書きに圧縮したのが ★空の成果物を生んだ（★実測: 依頼文 587字 → 段0 は 1005字）
```

**★骨格（★v2 のまま）**
```
<<<2DER:SKELETON>>>
def check_conservation(text_len, spans):
<<<2DER:END>>>
```

**★封印試験（★v2 の7本を ★1文字も変えない）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl


def test_full_cover_is_ok():
    v = impl.check_conservation(10, [{"start": 0, "end": 5}, {"start": 5, "end": 10}])
    assert v["ok"] is True
    assert v["missing"] == []
    assert v["overlap"] == []
    assert v["covered"] == 10

def test_missing_range_is_reported():
    v = impl.check_conservation(10, [{"start": 0, "end": 4}])
    assert v["ok"] is False
    assert v["missing"] == [[4, 10]]

def test_overlap_range_is_reported():
    v = impl.check_conservation(10, [{"start": 0, "end": 6}, {"start": 4, "end": 10}])
    assert v["ok"] is False
    assert v["overlap"] == [[4, 6]]

def test_missing_and_overlap_together():
    v = impl.check_conservation(10, [{"start": 0, "end": 6}, {"start": 4, "end": 8}])
    assert v["missing"] == [[8, 10]]
    assert v["overlap"] == [[4, 6]]

def test_empty_input_is_ok():
    v = impl.check_conservation(0, [])
    assert v["ok"] is True
    assert v["covered"] == 0

def test_degenerate_span_is_ignored():
    a = impl.check_conservation(10, [{"start": 0, "end": 10}])
    b = impl.check_conservation(10, [{"start": 0, "end": 10}, {"start": 7, "end": 3}])
    assert a == b

def test_order_does_not_matter():
    a = impl.check_conservation(10, [{"start": 0, "end": 5}, {"start": 5, "end": 10}])
    b = impl.check_conservation(10, [{"start": 5, "end": 10}, {"start": 0, "end": 5}])
    assert a == b
<<<2DER:END>>>
```

## 3. ★(b) 段0 の試験 — **★2本 足す（11→13）。★他の11本は1文字も変えない**

**★足す理由（★実測）**
```
★実データの癖を数えた: ★`★` が ★REAL_A に3個・REAL_B に6個＝★計9個
★★worker は ★その癖に合わせた（★MGR 実測の逐語『if "★" in segment: kind = "BULLET"』）
★★★∴ ★v1.12 の対照＝★癖を振る。★`★` を外して ★結果が変わらないことを縛る
★★★★★併せて ★依頼文の規則②（★行頭が - ・ * / 数字+. / 数字+`)`）を ★直接 縛る1本を置く
```

**★足す2本**
```python
def test_star_is_not_what_decides_bullet():
    """★v1.12: 実データの癖(★)を振る。★を外しても kinds が変わらないこと。"""
    plain = REAL_B.replace("★", "")
    k1 = [c["kind"] for c in impl.segment_candidates(REAL_B)["candidates"]]
    k2 = [c["kind"] for c in impl.segment_candidates(plain)["candidates"]]
    assert k1 == k2, (k1, k2)

def test_bullet_without_star_is_still_bullet():
    """★依頼文の規則②を直接 縛る。★を1つも含まない入力で確かめる。"""
    t = "- 一つ目\n- 二つ目\n3) 三つ目"
    kinds = [c["kind"] for c in impl.segment_candidates(t)["candidates"]]
    assert kinds.count("BULLET") >= 3, kinds
```

**★段0 の封印試験（★13本・★全文）**
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
<<<2DER:END>>>
```

## 4. ★★投入前に私が測った（★申告でなく実測）

```
★段0(13本): ★`extract_contract` → ★通る（13本）／★`extract_progress` → ★None
★段3(7本) : ★v2 で確認済（★試験7本・通る）
★★★∴ ★『投入して弾かれる』も ★『台帳が書き換わる』も ★起きない
```

## 5. ★★私の不備（★本日7回目・★数える）

```
★①fixture が実形式でない ②列挙の肯定側なし ③verdict の許容語を書かず ④assert に2つの意図
★⑤依頼文が曖昧 ⑥実物がマーカーを含んでいた ★⑦★依頼文を圧縮して ★必須の2文を落とした
★★★⑦の形=★①〜⑤と同じ『★書かなかった』。★但し ★『短くしよう』として落とした点が ★新しい。
★★★★★私が次からやること=★契約を ★2本以上 出す時は、★★依頼文の ★共通部分を ★1文字ずつ突き合わせる
   （★本件では ★段0 1005字 vs 段3 587字 で ★差が2文だった）。★★規則は増やさない＝★手順として守る。
```

## 6. 受入（★v3/v4 を引き継ぐ・★1つ差し替え）
```
★(1) worker が2件を書く（★Claude は本文0行）／★(2) ★段0 13本・段3 7本 全通
★(3) 保存則が機械で出る ／★(4) 門の判定が明細ごとに出る
★(5) 4つの対照の結果を全部 書く（★陽性は実物に無ければ『無い』と書いて作らない）
★(6) 配線行数 ／★(7) 戻せる ／★(8) 61本を走らせない ／★(9) 出せなければ『出せなかった』と書いて止まる
★(10) 落ちたら『どの読み方で落ちたか』を逐語で書いて止まる（★依頼文を直さない）
★★★(11) ★差し替え＝★『骨格が空でないこと』ではなく ★★『依頼文に ★本体を書けという指示が在ること』を
     ★封入前に確かめる（★段0 と ★段3 の依頼文を ★突き合わせる）
```

## 7. 禁止（★v1〜v4 を引き継ぐ）
```
★試験の ★既存分（段0 の11本／段3 の7本）を変える ／ ★骨格を変える ／ ★依頼文の ★他の行を触る
★fixture を ★実物以外に差し替える ／ ★マーカーを別の文字に置換する
★既存資産を作り直す ／ ★段0 で割る ／ ★4軸の LLM 測定 ／ ★段2 の分岐
★同一 task の作り直しの口を ★新設する（★§1・★依頼文を変えれば足りる）
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
```
