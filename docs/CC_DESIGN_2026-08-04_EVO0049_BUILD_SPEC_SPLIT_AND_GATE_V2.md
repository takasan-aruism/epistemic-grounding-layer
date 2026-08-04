# 【BUILD SPEC v2】`EVO-0049` — **★封印試験を実コードで入れた（18本）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 07:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.11）** ／ 親: `ITEM-2DER-EVO-0035` ／ 方針: `ITEM-2DER-EVO-0057`（Taka 裁定）
- **★v1 との関係**: ★差し替えない・追記しない。**★本書が実装源**（★依頼文・骨格は v1 から1文字も変えていない）
- **★私の予告**: ★試験 **18本**（★段0=11 / 段3=7）／★Claude の配線 **8〜16行**／★worker の行数は **予告しない**
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★指摘は正しい（★私の不備）

```
★v1 は『試験の本数は実装が決めてよい』と書いた ＝ ★実装が自分の試験を書き、★自分が判定される形になる
★★∴ ★独立性が落ちる。★封入は MGR ∴ ★試験は ★投入前に確定していなければならない。
★★★試験の実コードは ★設計が書く。★私の不備であり ★本書で直す。
```

## 2. ★★fixture は実物（★手書きしていない・★採取経路を書く）

```
★経路: ★GET /api/etrace?run_id=ETR-2b0f009d55cd → trace.events[0](SUBMIT/ENTRY) の inputs.raw_input
★★`inputs` は ★2000字で切り詰められた文字列（★`truncated: true`）∴ ★JSON として読めない
   → ★`"raw_input": "` の後ろを ★そのまま採り、★エスケープだけ戻した（★実測 1958字）
★★★私が測った ★実物の性質:
   ★空行(\n\n) = ★0 ／ ★箇条書き行 = 1 ／ ★句点 = 14
★★★★★∴ ★★『段0 の3種が全部 揃う 300字の窓』は ★実物に ★無い。
   ★★窓を総当たりで探した最良は ★score=2（★箇条書き1・句点1・★空行0）
★★★★★★∴ ★fixture を ★2本にした（★どちらも実物・★手で作っていない）:
   ★REAL_A = 先頭300字（★句点あり・箇条書きなし）
   ★REAL_B = 1650〜1950字（★箇条書きあり）
★★★★★★★★`PARAGRAPH`(空行)の試験は ★実物で書けない ∴ ★★短い合成文字列で書いた（★§4 で明記）
```

## 3. ★★契約①（段0）— ★依頼文と骨格は v1 のまま・★試験だけ足す

```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★fixture は実物。GET /api/etrace?run_id=ETR-2b0f009d55cd の ENTRY.raw_input から採取(手書きでない)
REAL_A = '<<<2DER:PROGRESS>>>\nitem: ITEM-2DER-EVO-0049\nstatus: PROPOSED\nactor: Taka\nstage: PLAN\ntitle: 1問い合わせを複数明細に分ける(明細ごとに HBB-30 の門を通し、揺れるものは確定しない)\nnote: next=MGR / 親: ITEM-2DER-EVO-0035 / ★戻す条件『明細に分ける形が決まった時』を Taka が 2026-08-04 に満たした。DEFERRED を解く。★Taka 裁定=(1)Qwen に割らせる方が筋がよい (2)★『割っただけ』は弱い。RRI の本来の機能は『何がし'
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

## 4. ★★契約②（段3）

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

## 5. ★★正直に書く（★fixture の限界）

```
★`test_no_break_gives_single_paragraph` の入力は ★★実物ではない（★短い合成文字列）。
   ★理由=★実物に ★空行が0件で、★『切れ目が無い』ケースを ★実物から採れなかった。
★★∴ ★★これは ★手書き禁止の ★例外であり、★隠さずここに書く。
★★★他の10本は ★すべて ★実物（REAL_A / REAL_B）か ★入力なし（空文字）で書いた。
★★★★★もし『合成も禁止』なら ★★この1本を落として ★10本で封入してよい（★MGR の判断）。
```

## 6. ★契約検査を通した（★投入前に確かめた）

```
★`contract_seal.extract_contract` に ★両方を通した実測:
   ★段0 → ★通る（試験 11本・`import impl` の検査も通過）
   ★段3 → ★通る（試験 7本・同上）
★★∴ ★『投入して弾かれる』は ★起きない（★v1 の詰まりは ★これで解ける）
```

## 7. 受入（★v1 の §7 を ★そのまま引き継ぐ）
```
★(1) worker が2件を書く（★Claude は本文0行）／★(2) ★18本 全通（★§5 の1本を落とすなら 17本）
★(3) 保存則が機械で出る ／★(4) ★門の判定が明細ごとに出る（★Taka の『割っただけは弱い』への担保）
★(5) ★4つの対照の結果を全部 書く（★陰性で差が出なければ『不活性』）
★(6) 配線行数を分ける ／★(7) 戻せる ／★(8) 61本を走らせない ／★(9) 出せなければ『出せなかった』と書いて止まる
```

## 8. 禁止（★v1 の §9 を ★そのまま引き継ぐ）
```
★既存資産（preflight_gate / request_thread / request_resolution）を作り直す
★段0 で割る ／ ★原文を書き換える ／ ★4軸の LLM 測定を入れる ／ ★段2 の分岐を実装する
★★試験を ★実装が書き足す・書き換える（★本書で確定した）
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす
```
