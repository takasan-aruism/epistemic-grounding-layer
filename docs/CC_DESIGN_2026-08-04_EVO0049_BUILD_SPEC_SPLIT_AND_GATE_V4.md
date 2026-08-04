# 【BUILD SPEC v4】`EVO-0049` — **★fixture がマーカーを含んでいた（★私の不備）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 08:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.11）** ／ 親: `ITEM-2DER-EVO-0035` ／ 方針: `ITEM-2DER-EVO-0057`
- **★v1〜v3 との関係**: ★差し替えない・追記しない。**★本書が実装源**。★依頼文は **v3 のまま**（★1行 足した版）、★骨格も不変
- **★私の予告**: ★試験 18本（★本数は不変）／★Claude の配線 **11行**／★worker の行数は書かない
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★実装の指摘は正しい（★私が測った実測）

```
★私の fixture(REAL_A)は ★実物ゆえに ★`<<<2DER:PROGRESS>>>` を ★中に含んでいた。
★★測った結果:
   ★`contract_seal.extract_contract` → ★通る（★試験11本・REAL_A も無傷）＝ ★契約は壊れない
   ★★`progress_seal.extract_progress` → ★★`ValueError: progress missing required field(s): item,actor,stage`
★★★∴ ★台帳は ★書き換わらない（★fail-closed）が、★★投入そのものが ★落ちる。
★★★★★∴ ★『そのまま封入すれば通る』は ★★成立しない ―― ★実装の指摘どおり。
```

## 2. ★★採る手（★実装の提案を ★そのまま採用・★私が測って確かめた）

```python
# ★ソース上だけ分ける（★実行時は同じ文字列）
REAL_A = '<<<2DER:' + 'PROGRESS>>>\nitem: ITEM-2DER-EVO-0049\n...'
```

**★私が測った実測（★3点とも）**
```
★`extract_progress` → ★None（★拾われない）
★`extract_contract` → ★通る（★試験 11本）
★★`REAL_A` が ★実行時に ★実物と ★完全一致 → ★True
★★★∴ ★★実データのまま・★パーサに拾われない・★試験の意味も変わらない
```

**★他の手を採らない理由**
```
★(a) fixture を ★マーカーの無い箇所に ★差し替える → ★★実物の性質（★段落・箇条書き）が ★変わる
★(b) ★マーカーを ★別の文字に置換する → ★★実データでなくなる（★手書き禁止の趣旨に反する）
★★★∴ ★(実装の提案) が ★唯一 ★3つとも満たす
```

## 3. ★★私の不備（★本日6回目・★数える）

```
★①fixture が実形式でない ②列挙の肯定側なし ③verdict の許容語を書かず ④assert に2つの意図
★⑤依頼文が曖昧（v3 で直した）★⑥本件＝★★実物を fixture にしたら ★実物がマーカーを含んでいた
★★★★★共通の形が ★変わった=①〜⑤は『★書かなかった』。★★⑥は『★実物を使ったがゆえに起きた』。
   ★★∴ ★『実物から取れ』という規律 v1.9 は ★正しいが、★★『実物はマーカーを含みうる』が ★抜けていた。
★★★★★★★私が次からやること=★fixture を作ったら ★★`extract_progress` と `extract_contract` の ★両方に
   ★通してから SPEC に載せる（★片方だけ通して安心しない）。★★本件で ★実際にそうした（★§2 の3点）。
★★★★★★★★★規則は増やさない=★v1.9 の中の ★手順として ★私が守る。
```

## 4. ★契約①の試験（★v2 の18本のうち ★1行だけ ★ソース表記を変えた）

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
<<<2DER:END>>>
```

★★★★★★★契約②（段3）の試験は **v2 のまま**（★マーカーを含まない ∴ ★変更なし）

## 5. 受入（★v3 の §4 を引き継ぐ・★1つ足す）
```
★(1) worker が2件を書く（★Claude は本文0行）／★(2) ★18本 全通
★(3) 保存則が機械で出る ／★(4) 門の判定が明細ごとに出る
★(5) 4つの対照の結果を全部 書く（★陽性は実物に無ければ『無い』と書いて作らない）
★(6) 配線行数 ／★(7) 戻せる ／★(8) 61本を走らせない
★(9) 出せなければ『出せなかった』と書いて止まる
★(10) ★18本のどれかが落ちたら ★『どの読み方で落ちたか』を逐語で書いて止まる（★依頼文を直さない）
★★★★(11) ★★★封入の前に ★MGR が ★`extract_progress` に通して ★None を確かめること
     ＝ ★私の申告（★§2）を ★信じずに ★自分で測る（★1行で済む）
```

## 6. 禁止（★v1〜v3 を引き継ぐ）
```
★fixture を ★実物以外に差し替える ／ ★マーカーを ★別の文字に置換する（★実データでなくなる）
★試験の ★本数・意図を変える ／ ★依頼文（v3 版）・骨格を触る
★既存資産を作り直す ／ ★段0 で割る ／ ★4軸の LLM 測定 ／ ★段2 の分岐
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす
```
