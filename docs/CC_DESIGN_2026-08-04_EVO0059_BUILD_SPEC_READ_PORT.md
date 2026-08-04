# 【BUILD SPEC】`EVO-0059` — **★読む口を作る。★raw は残っていない（先に言う）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 23:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は在る・1件**（`explain_empty_generation`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **5〜9行**（★`resolve_view` に1欄・EVO-0052 と同じ形）
- **★走行 0（★私は）・★task 増 0・★commit 0**

---

## 1. ★★題を1つ訂正する（★実測・★先に言う）

**本件の題**「★worker の raw 出力を front door から読めるようにする」は **★達成できない**。

```
★`runtime_supervisor.py:194-196` の ★逐語コメント:
      「retain the FULL Execution Events (Contract v0.2, ★compact metadata —
        ★★no prompt/response text) in the existing DW SoR」
★★∴ ★残っているのは ★メタデータだけで、★★応答本文は ★どこにも残っていない。
★★★∴ ★『1文字が何だったか』は ★★この記録からは ★永久に出ない。
★★★★★★但し ★『★なぜ空だったか』は ★出る（★下の §2）。★★本件はそれを取りに行く。
★★★★★★★題を『raw を読む』のままにすると ★出ないものを受入にすることになる ∴ ★MGR に ★題の訂正を求める。
```

## 2. ★★記録は既に在る（★実測・★何を作らなくてよいか）

```
★`_persist_dw`（`runtime_supervisor.py:183-202`）は ★★既存の DW SoR に ★PHASE_MARK を1本 積む:
   payload = {"kind": ★"RUNTIME_SUPERVISOR", "outcome":…, "failure_class":…, "attempts":…,
              "event_ids":[…], "ladder":[…], "finish_reasons":[…],
              ★"execution_events": [ ★attempt ごとの全欄 ], "finding":…}
★event の外側（`workcell.py:76-78` 逐語）= {"task_id","phase":"PROCESS_EVENT","role":"RUNTIME",
   "identity":"2der-runtime-supervisor","run_id","ts","payload":{…}}
★★attempt 1件の中身（`build_event` 逐語・★本件で効く欄だけ）:
   ★`actor_role`（CODING_WORKER / AUDITOR / PLANNER …）★`attempt_index`
   ★`parse_status`（OK / FAIL / ★EMPTY）★`schema_validation_status`（OK / FAIL / N/A）
   ★`content_length`（★= len(content)）★`reasoning_tokens` ★`finish_reason` ★`failure_class_candidate`
★★★∴ ★作るのは ★★読む口であって ★記録ではない（★MGR の逐語と一致）。★新しい台帳を作らない。
```

**★★ここから、`outcome=RECOVERED` と空の成果物の食い違いの ★第一候補が出る**
```
★`supervised_text_call` は ★worker だけでなく ★planner も auditor も呼ぶ（★どれも `task_id` を渡す）
★★∴ ★同じ task に ★複数の actor の記録が ★混ざって積まれる。
★★★∴ ★『RECOVERED』が ★worker のものとは限らない ―― ★★`actor_role` で分けないと ★読み違える。
★★★★★∴ ★本件の核は ★★`actor_role` で分けることを ★中心に置く（★受入(2) はこれで説明が付く見込み）。
★★★★★★★【未確認】= ★私は ★実物の記録を見ていない（★読む口が無いのが ★本件の理由）。★候補であって ★結論ではない。
```

**★もう1つ、記録が無いことも在りうる**
```
★`_persist_dw:185-186` 逐語 = `if not task_id or not ts: return None`
★★∴ ★task_id か ts が欠けた呼び出しは ★★何も残さない。★『記録は在るはず』と ★決めつけない。
★★★∴ ★核の戻り値に ★★`found`（在るか無いか）を ★必ず置く（★無いことを ★無いと言える形）。
```

## 3. ★★契約（★そのまま封入できる形。★封入は MGR）

**★依頼文**
```
生成が空だった理由を実行記録から説明する純関数 impl.explain_empty_generation を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
events = [ {"payload": {...}, ...}, ... ]     ★DW の実行記録。payload 以外の欄は見ない。
actor_role = str|None                          ★None なら全部の actor を対象にする。
戻り値 = {"found": bool, "attempts": int, "outcome": str|None, "failure_class": str|None,
          "why_empty": str, "per_attempt": [ {...}, ... ]}

・対象にする payload は ★payload["kind"] == "RUNTIME_SUPERVISOR" のものだけ。
・その payload の ★"execution_events"（配列）を ★events の並び順に ★全部 つなげる。
  ★配列が無い・配列でないなら ★その payload は ★飛ばす（★例外にしない）。
・actor_role が None でなければ、★attempt の "actor_role" が ★等しいものだけ残す。
・attempts = 残った attempt の件数。found = attempts > 0。
・outcome / failure_class = ★残った attempt を1件でも持つ payload のうち ★最後のものの
  "outcome" / "failure_class"。★1件も無ければ どちらも None。
  ★★他の actor しか居ない payload の outcome を ★混ぜない。
・per_attempt = 残った attempt を ★"attempt_index" の小さい順に並べ、各要素は
  {"attempt_index","parse_status","schema","content_length","finish_reason","failure_class_candidate"}。
  ★"schema" には "schema_validation_status" の値を入れる。★欄が無ければ None。
・why_empty は NO_RECORD / BOTH_EMPTY / CONTENT_EMPTY / EXTRACTED_EMPTY / NOT_EMPTY の★5語。
  ★他の語を作らない。★per_attempt の ★最後の1件だけを見て、★この順で ★最初に当たったもの:
    ① 残った attempt が0件            → "NO_RECORD"
    ② parse_status == "EMPTY"          → "BOTH_EMPTY"
    ③ content_length == 0              → "CONTENT_EMPTY"
    ④ schema == "FAIL"                 → "EXTRACTED_EMPTY"
    ⑤ それ以外                          → "NOT_EMPTY"
  ★content_length が None のときは ③に当たらない（★0 と None を同じにしない）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def explain_empty_generation(events, actor_role="CODING_WORKER"):
<<<2DER:END>>>
```

**★fixture について（★v1.9 を守れない・★理由を書く）**
```
★実物の記録は ★取れない ―― ★★front door に ★読む口が無いことが ★本件そのものだから。
★★∴ ★fixture は ★手書きではなく ★★書き手のコードの逐語から ★機械的に組み立てた形にした
   （`_persist_dw:189-198` の payload と `build_event:161-180` の戻り値）。
★★★受入(1) が通った時点で ★★実物と ★突き合わせ、★違えば ★★実物に合わせる（★私の写しを正としない）。
```

**★封印試験（★14本・★意図ごとに1本）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def _att(i, actor="CODING_WORKER", parse="OK", schema="OK", clen=120, fr="stop", fcc=None):
    return {"execution_event_id": "EE-%d" % i, "actor_role": actor, "attempt_index": i,
            "parse_status": parse, "schema_validation_status": schema,
            "content_length": clen, "finish_reason": fr, "failure_class_candidate": fcc,
            "reasoning_tokens": None, "max_tokens": 1024}

def _pm(atts, outcome="EXHAUSTED", fc=None):
    return {"task_id": "TASK-2DER-51E58279", "phase": "PROCESS_EVENT", "role": "RUNTIME",
            "identity": "2der-runtime-supervisor", "run_id": None, "ts": "2026-08-04T21:06:46",
            "payload": {"kind": "RUNTIME_SUPERVISOR", "outcome": outcome, "failure_class": fc,
                        "attempts": len(atts), "execution_events": atts, "finding": None}}

def test_no_record_when_there_is_nothing():
    v = impl.explain_empty_generation([])
    assert (v["found"], v["why_empty"]) == (False, "NO_RECORD"), v

def test_other_kinds_of_events_are_ignored():
    other = {"payload": {"kind": "SOMETHING_ELSE", "execution_events": [_att(0)]}}
    assert impl.explain_empty_generation([other])["found"] is False

def test_both_empty_is_named():
    v = impl.explain_empty_generation([_pm([_att(0, parse="EMPTY", clen=0)])])
    assert v["why_empty"] == "BOTH_EMPTY", v

def test_content_empty_is_distinguished_from_both_empty():
    """★content は空だが reasoning には在った形（★parse_status は EMPTY にならない）"""
    v = impl.explain_empty_generation([_pm([_att(0, parse="OK", schema="FAIL", clen=0)])])
    assert v["why_empty"] == "CONTENT_EMPTY", v

def test_extracted_empty_when_there_was_content():
    v = impl.explain_empty_generation([_pm([_att(0, parse="OK", schema="FAIL", clen=800)])])
    assert v["why_empty"] == "EXTRACTED_EMPTY", v

def test_healthy_run_is_not_empty():
    """★陰性対照（★MGR 受入(3)）: 成功した走行では ★空だと言わない"""
    v = impl.explain_empty_generation([_pm([_att(0)], outcome="FIRST_TRY")])
    assert v["why_empty"] == "NOT_EMPTY", v

def test_missing_content_length_is_not_treated_as_zero():
    v = impl.explain_empty_generation([_pm([_att(0, parse="OK", schema="OK", clen=None)])])
    assert v["why_empty"] == "NOT_EMPTY", v

def test_only_the_asked_actor_is_counted():
    """★★MGR 受入(2): 監査の記録を ★worker の答えに混ぜない"""
    evs = [_pm([_att(0, actor="AUDITOR")]), _pm([_att(0, parse="EMPTY", clen=0)])]
    v = impl.explain_empty_generation(evs, actor_role="CODING_WORKER")
    assert v["attempts"] == 1, v

def test_outcome_does_not_leak_from_another_actor():
    """★★『RECOVERED なのに成果物が空』の食い違いは ★これで説明が付く形"""
    evs = [_pm([_att(0, parse="EMPTY", clen=0)], outcome="EXHAUSTED"),
           _pm([_att(0, actor="AUDITOR")], outcome="RECOVERED")]
    v = impl.explain_empty_generation(evs, actor_role="CODING_WORKER")
    assert v["outcome"] == "EXHAUSTED", v

def test_none_actor_takes_everyone():
    evs = [_pm([_att(0, actor="AUDITOR")]), _pm([_att(0)])]
    assert impl.explain_empty_generation(evs, actor_role=None)["attempts"] == 2

def test_per_attempt_is_ordered_by_attempt_index():
    v = impl.explain_empty_generation([_pm([_att(2), _att(0), _att(1)])])
    assert [a["attempt_index"] for a in v["per_attempt"]] == [0, 1, 2], v

def test_the_last_attempt_decides():
    """★梯子を登った末に空になった形（★最後の1件で決める）"""
    v = impl.explain_empty_generation([_pm([_att(0, clen=500), _att(1, parse="EMPTY", clen=0)])])
    assert v["why_empty"] == "BOTH_EMPTY", v

def test_broken_execution_events_do_not_raise():
    bad = {"payload": {"kind": "RUNTIME_SUPERVISOR", "execution_events": "not a list"}}
    assert impl.explain_empty_generation([bad])["found"] is False

def test_why_empty_is_never_outside_the_five():
    cases = ([], [_pm([])], [_pm([_att(0)])], [_pm([_att(0, parse="EMPTY", clen=0)])],
             [_pm([_att(0, schema="FAIL", clen=0)])], [_pm([_att(0, schema="FAIL", clen=9)])])
    for c in cases:
        assert impl.explain_empty_generation(c)["why_empty"] in (
            "NO_RECORD", "BOTH_EMPTY", "CONTENT_EMPTY", "EXTRACTED_EMPTY", "NOT_EMPTY")
<<<2DER:END>>>
```

## 4. ★依頼文の規則 → 試験の対応表（v1.13）

| 依頼文の規則 | 縛る試験 |
|---|---|
| kind が RUNTIME_SUPERVISOR のものだけ | `test_other_kinds_of_events_are_ignored` |
| execution_events が配列でなければ飛ばす | `test_broken_execution_events_do_not_raise` |
| actor_role で絞る | `test_only_the_asked_actor_is_counted` ／ `test_none_actor_takes_everyone` |
| ★outcome を他の actor から混ぜない | `test_outcome_does_not_leak_from_another_actor` |
| per_attempt は attempt_index 順 | `test_per_attempt_is_ordered_by_attempt_index` |
| 5語・この順・最後の1件で決める | `..._never_outside_the_five` ／ `test_the_last_attempt_decides` ／ 各語1本 |
| content_length の None と 0 を分ける | `test_missing_content_length_is_not_treated_as_zero` |
| 陰性対照（成功した走行） | `test_healthy_run_is_not_empty` |

## 5. ★Claude の配線（★5〜9行と予告・★EVO-0052 と同じ形）

```python
# webui.py resolve_view() — ★`eff` の隣に1欄 足すだけ（★新しい口を作らない）
    gen = None                                    # EVO-0059: 生成が空だった理由(worker の成果物を呼ぶだけ)
    if rid and rid.startswith("TASK-2DER"):
        from twoder.explain_empty_generation import explain_empty_generation as EG
        gen = EG(_events(rid))
    return {..., "generation": gen, "read_only": True}
```
```
★★新しいエンドポイントを作らない・★新しい台帳を作らない（★MGR 受入(4)）
★★★`_events(rid)` は ★`webui.py:87-91` に ★既に在る（★DW の読み口をそのまま使う）
```

## 6. 受入（★MGR の6点 ＋ 私の2点）

```
★(0) ★worker が書く（★Claude は本文0行）・★14本 全通
★(1) ★`GET /api/resolve?id=TASK-2DER-51E58279` の応答に ★attempt ごとの failure_class が ★出る
★(2) ★`outcome` と ★空の成果物の ★食い違いが ★説明できる
     ★★私の候補=★actor_role の混在（★§2）。★★違ったら ★★『候補は外れた』と書く（★合わせに行かない）
★(3) ★成功した走行では ★従来どおり読める（★陰性対照・★`why_empty == "NOT_EMPTY"`）
★(4) ★新しい台帳を作らない ／★(5) ★行数を分ける（★worker / Claude）／★(6) ★戻せる
★★(7) ★★`found` が False の時に ★『記録が無い』と ★言えている（★`_persist_dw` が書かない場合が在る・★§2）
★★(8) ★★fixture を ★実物と突き合わせ、★違えば ★実物に合わせて ★差分を書く（★§3・v1.9 を守れなかった分）
★★★(9) ★出せなかったら ★『出せなかった』と書いて ★止まる
★★★★★予告を投入前に書く: ★`why_empty` に ★何が出ると思うか（★1語）
```

## 7. ★★これで分からないこと（★先に言う）

```
★★『1文字が何だったか』は ★★出ない（★§1・★本文は残っていない）。★出るのは ★★『なぜ空か』の分類だけ。
★★★∴ ★本件が通っても ★★『raw が読めるようになった』とは ★書かない。
★★★★もし ★分類でも足りず ★本文が要ると分かったら、★それは ★★別の1区間（★記録する側を変える話）＝ ★いま着手しない。
★★★★★★`why_empty` は ★★原因ではなく ★★形の名前である。★『★なぜ content が空だったか』は ★まだ言えない。
```

## 8. 禁止

```
★Claude が `explain_empty_generation` の中身を書く ／ ★新しいエンドポイント・台帳を作る
★`content_length` の None を 0 として扱う ／ ★6語目を作る ／ ★actor をまたいで outcome を混ぜる
★記録する側（`_persist_dw` / `build_event`）を ★本件で変える（★読む口だけ）
★『raw が読めるようになった』『1文字が何か分かった』と書く
★受入(2) の候補に ★結果を合わせに行く ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
