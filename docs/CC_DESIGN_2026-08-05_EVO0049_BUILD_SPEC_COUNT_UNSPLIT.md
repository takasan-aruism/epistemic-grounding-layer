# 【BUILD SPEC】`EVO-0049` — **★『割れなかった』を数える（★4つの数だけ）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-05 18:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035` ／ 台帳: `ITEM-2DER-EVO-0049`
- **★v1.8 の宣言**: **★核は在る・1件**（`count_unsplit`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **8〜14行**（★記録を読んで渡す＋`/api/control` に1欄）
- **★予想は書かない**（★裁定の逐語。★数が出てから次を決める）
- **★新台帳0・★新エンドポイント0・★本文0**

---

## 1. ★分母と分子（★既に記録されている値だけ）

```
★分母 = ★`PROGRESS_ONLY` が False の投入（逐語 `submit.py:266` が ★既に記録している）
★分子 = ★そのうち ★`SPLIT_GATES` が ★1件で ★start=0 かつ end=text_len（逐語 `submit.py:346-349`）
★層別 = ★`DW_TASK_ID` の ★在る/無い（★契約入りは ★構造上ほぼ1用件 ∴ ★混ぜると ★分子が膨らむ）
★★∴ ★新しい欄を ★1つも作らない。★読み方を ★決めるだけ。
```

## 2. ★★契約（★そのまま封入できる形）

**★依頼文**
```
投入の記録から「割れなかった件数」を数える純関数 impl.count_unsplit を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
records = [ {"progress_only": bool, "dw_task_id": str|None,
             "text_len": int, "spans": [ {"start": int, "end": int}, ... ]}, ... ]
戻り値 = {"with_task": {"n": int, "unsplit": int},
          "without_task": {"n": int, "unsplit": int}}

・record が dict でない、または "spans" が list でない、または "text_len" が int でない
  → その record は ★数えない（★例外にしない）。
・progress_only が True の record は ★数えない。
・数える record のうち、dw_task_id が None でも空文字でもないものを "with_task"、
  そうでないものを "without_task" に入れる。
・n = その組に入った件数。
・unsplit = その組のうち、spans が ★ちょうど1件で、その1件の start が 0、end が text_len のもの。
  ★spans が 0件のもの、2件以上のものは unsplit に数えない。
  ★1件でも 全体を覆っていなければ unsplit に数えない。
・★4つの数だけを返す。★合計や割合は返さない。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def count_unsplit(records):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★10本・★span は 2026-08-05 の実測から）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# 実測(segment_candidates を実データで呼んだ値):
#   散文 51字 → 1件 [(0,51) PARAGRAPH]         = ★割れなかった
#   箇条書き   → 4件 [(0,11)(11,23)(23,34)(34,41)] = ★割れた
PROSE = {"progress_only": False, "dw_task_id": None, "text_len": 51,
         "spans": [{"start": 0, "end": 51}]}
BULLET = {"progress_only": False, "dw_task_id": None, "text_len": 41,
          "spans": [{"start": 0, "end": 11}, {"start": 11, "end": 23},
                    {"start": 23, "end": 34}, {"start": 34, "end": 41}]}
NOTE = {"progress_only": True, "dw_task_id": None, "text_len": 0, "spans": []}

def test_prose_counts_as_unsplit():
    v = impl.count_unsplit([PROSE])
    assert v["without_task"] == {"n": 1, "unsplit": 1}, v

def test_bullets_are_not_unsplit():
    v = impl.count_unsplit([BULLET])
    assert v["without_task"] == {"n": 1, "unsplit": 0}, v

def test_progress_notes_are_not_counted_at_all():
    """★我々の note 投入は ★分母に入らない"""
    v = impl.count_unsplit([NOTE, NOTE, NOTE])
    assert v == {"with_task": {"n": 0, "unsplit": 0},
                 "without_task": {"n": 0, "unsplit": 0}}, v

def test_task_id_splits_the_two_groups():
    a = dict(PROSE, dw_task_id="TASK-2DER-ABCD1234")
    v = impl.count_unsplit([a, PROSE])
    assert (v["with_task"]["n"], v["without_task"]["n"]) == (1, 1), v

def test_empty_string_task_id_goes_to_without_task():
    v = impl.count_unsplit([dict(PROSE, dw_task_id="")])
    assert v["without_task"]["n"] == 1, v

def test_one_span_not_covering_all_is_not_unsplit():
    """★1件でも ★全体を覆っていなければ 数えない"""
    v = impl.count_unsplit([dict(PROSE, spans=[{"start": 0, "end": 30}])])
    assert v["without_task"] == {"n": 1, "unsplit": 0}, v

def test_zero_spans_is_not_unsplit():
    v = impl.count_unsplit([dict(PROSE, text_len=0, spans=[])])
    assert v["without_task"] == {"n": 1, "unsplit": 0}, v

def test_broken_records_are_skipped_not_raised():
    v = impl.count_unsplit([None, "x", {"progress_only": False, "spans": "no"},
                            {"progress_only": False, "text_len": "5", "spans": []}])
    assert v == {"with_task": {"n": 0, "unsplit": 0},
                 "without_task": {"n": 0, "unsplit": 0}}, v

def test_empty_input_gives_four_zeros():
    assert impl.count_unsplit([]) == {"with_task": {"n": 0, "unsplit": 0},
                                      "without_task": {"n": 0, "unsplit": 0}}

def test_all_four_numbers_can_be_nonzero():
    """★肯定側(v1.10)=★4つとも 0 でない入力が 在る"""
    wt_u = dict(PROSE, dw_task_id="T1")
    wt_s = dict(BULLET, dw_task_id="T2")
    v = impl.count_unsplit([wt_u, wt_s, PROSE, BULLET])
    assert v == {"with_task": {"n": 2, "unsplit": 1},
                 "without_task": {"n": 2, "unsplit": 1}}, v
<<<2DER:END>>>
```

## 3. ★Claude の配線（★8〜14行と予告）

```
★(a) ★投入ごとの記録から ★3値(progress_only / dw_task_id / spans+text_len)を ★集めて渡す
★(b) ★`/api/control` の応答に ★`split_counts` を ★1欄 足す（★既存の集計の口・★新エンドポイント0）
★★★`/api/resolve` には ★足さない（★id 単位なので ★集計は載らない＝★2026-08-05 実測）
★★★★本文は ★1文字も出さない（★数だけ）
```

## 4. ★★これで分からないこと（★先に言う）

```
★★私は ★集計元に届くかを ★測れていない ―― ★実行結果の横読みは ★フックが拒否した（★正しい拒否）
   ∴ ★★『読めるか』は ★実装が ★最初に確かめること。★読めなければ ★『読めない』が結果であり
   ★それが ★次に作る読み出しである（規律3）。
★★★`unsplit` は ★『段0 が1候補しか出せなかった』であって ★『用件が1件だった』ではない。
   ★★1件の依頼が ★正しく1候補な場合も ★unsplit に入る ∴ ★★『割れなかった＝取りこぼし』と ★読まない。
★★★★fixture の span は ★実測だが、★`progress_only` / `dw_task_id` は ★記録の形から組んだ（★v1.9 の限界）
```

## 5. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★10本 全通
★(1) ★★集計元が ★読めるかを ★最初に確かめ、★逐語で書く（★読めなければ ★そこで止まる）
★(2) ★`/api/control` の応答に ★`split_counts` が ★出る（★4つの数のみ・★本文0）
★(3) ★★除外した件数を ★逐語で書く（★progress_only で外した数 ／ ★壊れていて外した数）
★(4) ★数を ★そのまま書く ―― ★★『多い』『少ない』と ★書かない（★裁定の逐語）
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数 ／★(7) ★戻せる ／★(8) ★61本を走らせない ／★(9) ★commit しない
★★★(10) ★出せなかったら『出せなかった』と書いて止まる
★★★★★予告を投入前に書く: ★行数 ／ ★(1) が読めるかどうかの ★見込みは ★書かない
```

## 6. 禁止

```
★合計・割合・順位を ★返す（★4つの数だけ）／ ★本文を ★出す
★`/api/resolve` に ★足す（★§3）／ ★新しい台帳・エンドポイントを作る
★壊れた record で ★例外を投げる ／ ★黙って ★分母に数える
★★数を見て ★『散文は稀』『多い』と ★書く（★受入(4)）
★勘定科目に触る（★`account_id` は UNCLASSIFIED のまま）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
