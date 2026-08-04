# 【BUILD SPEC v7】`EVO-0058` 段3 — **★どの区間で止まったかを返す。★言えない区間は言えないと返す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 20:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1/v2 との関係**: ★差し替えない・追記しない（規律）。**★本書が実装源**
- **★v5 からの差は ★1文だけ**（★`candidates[0]` が ★id であることの明示）。★★否定文を ★1つも足さない
- **★v6 は ★採らない**（★否定を3つ足した版。★別の所が崩れた＝★§0）
- **★v4 からの差は2行の削除だけ**: ★worker が ★満たせない要求を ★依頼文から ★消した（★試験も骨格も ★1文字も変えていない）
- **★字数削りではない**: ★9回すべて `actor_role='CODING_WORKER'`（MGR 実測）＝ ★worker が受け取るのは ★planner が畳んだ1段落
  ∴ ★★契約の字数は ★無関係。★字数が減るのは ★結果であって ★目的ではない。

### ★消した2行と、★なぜ worker に届く必要が無いか

| 消した行（逐語） | ★なぜ worker に届く必要が無いか |
|---|---|
| ★試験は \`import impl\` と書いてください。 | ★これは ★契約の書き手向けで、★`contract_seal` の import 検査が ★機械で見ている ―― ★worker の固定 prompt は ★逐語「★No tests, no explanation」∴ ★書けと書くなを ★同時に言っていた |
| ★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。 | ★これは ★runner 向けで、★`qwen_worker.py` に ★`skeleton` の出現は ★0件（`run()` が読むのは `requirement` だけ）∴ ★見せられていない物を ★保存しろと言っていた |

```
★★機能は落ちない=★(A)の検査は ★機械に残る／★(B)の骨格は ★契約に残る（★消したのは ★worker への指示文だけ）
```

- **★v3 からの差**: ★規則①（`result` が OK/PASSED でない → 失敗）を ★★実測の失敗記録で縛った（★1本 追加）
- **★私の欠陥（2つめ・★先に書く）**: ★v3 の19本は ★★`result` を ★丸ごと無視する実装でも ★全通する。
  ★私が確かめた（★捨て実装で `bad = False` にして19本 走らせ ★全通）。
  ★★原因は v2 と ★同じ種類＝★依頼文に書いた規則を ★試験で縛っていない（v1.11）。★2回 続けて踏んだ。
  ★★★塞げたのは ★MGR が ★実測の失敗記録（`TASK-2DER-51E58279`）を ★持ってきたからである。
- **★v2 からの差**: ★`actor` と `segment` が **★route 由来である**ことを ★試験で縛った（★4本 追加）
- **★私の欠陥（★先に書く）**: ★v2 の走行（`TASK-2DER-AC2E300E`）は ★13本 全通したが、
  ★成果物は ★`actor` を ★4箇所とも `"2DER"` の ★決め打ちにしていた（★MGR が成果物を読んで実測）。
  ★★依頼文には「★その行の actor」と書いたが ★★試験で1本も縛っていなかった ＝ ★本日 何度も踏んだ同型（v1.11）。
  ★★★走行は捨てる。★成果物が悪かったのではなく ★★私の契約が ★測っていなかった。
- **★v1.8 の宣言**: **★核は在る・1件**（`locate_failure`＝★純関数）→ **★この単位の 2DER 工程は 1 になりうる**
- **★私の予告**: ★worker の行数は **書かない**（★本日 外し続けたため）／★Claude の配線 **0〜4行**（★呼ぶだけ・★台帳の note に書く）
- **★走行 0（★私は）・★task 増 0・★commit 0**

---

## 1. ★先に測った（★段3 の前提を1つ訂正する）

**★裁定の逐語**:「★S11(run-gate の refused)は★既に埋まっている(EVO-0053 で cause を返す形にした)」

```
★私が実物を見た（`twoder/webui.py:807-818` 逐語）:
   `_ETRACE.set_run_id(...)` は ★在る（★run に繋ぐだけ）
   `_gd(gate, tid)` → `refused` を ★HTTP 応答で返す
   ★★しかし ★`emit(...)` は ★1行も無い（`grep -n "emit" webui.py` の結果に ★run-gate の行は出ない）
★★★∴ ★S11 で埋まったのは ★★『応答に理由が載る』であって ★★『実行記録に残る』ではない。
   ★`locate_failure` は ★実行記録しか見ない ∴ ★★S11 は ★依然 見えない。
★★★★★∴ ★受入(2)（run-gate の refused）は ★『返らない』になる ―― ★★これを ★先に予告する（★後から言い訳にしない）。
★★★★★★これは ★段3 を止める理由にはならない（★『返らない』と返せることが ★段3 の仕事である）。
```

**★もう1つ、逆に増えた区間**:
```
★S14 は ★段2 で ★実行記録に出るようになった（★実測・下の §2）
★★但し ★MGR の逐語どおり ★『1/4 埋まった』と書く（★空(0/None)と workspace 無しは ★再現できていない）
```

## 2. ★★fixture（★実測・2026-08-04 19:2x・★front door `/api/etrace?task_id=`）

```
★TASK-2DER-98D5F072（★段2 v2 の位置・★成功）
  DW/_append_event phase=CREATE        result=OK
  DW/_append_event phase=PROCESS_EVENT result=OK
  DW/_append_event phase=PLAN          result=OK
  ★RUNNER/run_minimal_slice            result=OK
     outputs={"status":"PASSED","classification":"CANONICAL_DISPATCH","artifact_len":★36,"workspace":true}
  DW/_append_event phase=GENERATE      result=OK
  DW/_append_event phase=PROCESS_EVENT result=OK
  DW/_append_event phase=AUDIT         result=OK

★TASK-2DER-83CA5708（★段2 v1 の位置）— ★RUNNER の outputs だけ違う:
     outputs={"status":★null,"classification":"CANONICAL_DISPATCH","artifact_len":★null,"workspace":true}

★★TASK-2DER-51E58279（★2026-08-04T21:06:46・★本番で初めて捉えた失敗・MGR 実測）
     inputs ={"target_file":"impl.py","skeleton_len":35,★"tests_len":5263}
     outputs={"status":"FAILED","classification":"CANONICAL_DISPATCH",★"artifact_len":★1,"workspace":true}
     result =★FAILED
   ★★★『空(0)』ではなく ★★『1文字』だった ＝ ★受け取り側では0字に見えていたが ★生成側は1文字 返している。
   ★★★★但し ★★因果は ★確かめていない【未確認】=★契約が大きい(5263)から止まったのかは ★まだ言えない。
      ★★★★★1文字が ★何だったかは ★`EVO-0059`(worker の raw 出力)で決まる。★本件では ★決めない。
```

```
★★★ここから読める ★重要な2つ:
 (a) ★★記録の順は ★区間の順ではない ―― ★RUNNER が ★DW/GENERATE より ★先に出る
     （★generate が返ってから DW が GENERATE を append するため）
     ∴ ★★『最後に出た event = 最後に通った区間』は ★誤り。★順番は ★route が決める。
 (b) ★★`result` は ★『呼べた』であって ★『成功した』ではない
     ―― ★83CA5708 は ★artifact_len が null でも ★result=OK。
     ∴ ★★result だけを見る関数は ★何も見つけられない。★outputs も見る必要が在る。
★★★★★★★但し ★83CA5708 の null は ★★計器の置き場所の誤り（v1）であって ★成果物の欠落ではない。
   ∴ ★これを『事故(4) を当てた』と ★書いてはいけない（★計器が自分を数える形になる）。
   ★fixture としては ★『null の記録を LOCATED にする』ことの検査に ★だけ 使う。
```

## 3. ★★契約（★そのまま封入できる形。★封入は MGR）

**★依頼文**
```
実行記録から「どの区間で止まったか」を突き止める純関数 impl.locate_failure を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
route = [ {"id": str, "component": str|None, "function": str|None,
           "phase": str|None, "actor": str, "require_nonnull": [str, ...]}, ... ]
        ★この並び順が ★区間の順である。
events = [ {"component": str, "function": str,
            "inputs": dict|str, "outputs": dict|str, "result": str|None}, ... ]
戻り値 = {"verdict": str, "segment": str|None, "actor": str|None, "actor_known": bool,
          "last_observed": str|None, "candidates": [str, ...]}

・inputs / outputs は dict でも JSON 文字列でもよい。文字列なら json で読む。
  ★読めなければ {} として扱う（★例外にしない）。dict でも文字列でもなければ {}。
・照合: route の行と event が一致するのは、component と function が等しく、
  かつ 行の phase が None でなければ inputs の "phase" とも等しい時。
  ★行の component か function が None なら ★何とも一致しない（＝観測が無い区間）。
・行の「失敗」= その行に一致した event の ★どれか1つでも 次のどちらかに当たる時:
    ① result が "OK" でも "PASSED" でもない
    ② 行の require_nonnull に挙げた key が outputs に ★無い、または ★値が None
・last_observed = 一致が1つ以上ある行のうち ★route 順で ★最後の行の id。無ければ None。
・candidates = 一致が0の行の id を ★route 順に並べたもの。★但し:
  一致が1つ以上在るなら ★★「一致した行のうち route 順で ★最初の行」より ★後ろの行だけ。
  （★その行より前に一致が無い区間は ★この記録では言えない＝別の記録に在る ∴ ★候補にしない）
  一致が1つも無いなら ★全部。
・verdict は NO_EVIDENCE / LOCATED / BOUNDED / NO_FAILURE の★4語。★他の語を作らない。
  ★この順で ★最初に当たったもの:
    ① 一致が1つも無い        → "NO_EVIDENCE"
    ② 失敗した行が在る        → "LOCATED"（segment = ★route 順で ★最初に失敗した行の id）
    ③ candidates が空でない   → "BOUNDED"（segment は None）
    ④ それ以外                → "NO_FAILURE"（segment は None・candidates は []）
・actor:
    LOCATED     → その行の actor。actor_known は True。
    BOUNDED     → candidates[0] の行の actor。actor_known は ★False。
                  （★candidates[0] は ★id の文字列。★その id を持つ route の行から引く）
    それ以外     → actor は None。actor_known は False。
・★events の並び順は ★結果を変えない（★順番は route が決める）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def locate_failure(route, events):
<<<2DER:END>>>
```

**★封印試験（★20本・★fixture は §2 の実測。★意図ごとに1本）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

R09 = {"id": "S09", "component": "DW", "function": "_append_event", "phase": "CREATE",
       "actor": "Claude", "require_nonnull": []}
R11 = {"id": "S11", "component": None, "function": None, "phase": None,
       "actor": "Claude", "require_nonnull": []}          # ★応答には出るが 記録には残らない区間
R12 = {"id": "S12", "component": "DW", "function": "_append_event", "phase": "PLAN",
       "actor": "2DER", "require_nonnull": []}
R13 = {"id": "S13", "component": "DW", "function": "_append_event", "phase": "GENERATE",
       "actor": "2DER", "require_nonnull": []}
R14 = {"id": "S14", "component": "RUNNER", "function": "run_minimal_slice", "phase": None,
       "actor": "2DER", "require_nonnull": ["artifact_len"]}
R15 = {"id": "S15", "component": None, "function": None, "phase": None,
       "actor": "2DER", "require_nonnull": []}
R16 = {"id": "S16", "component": "DW", "function": "_append_event", "phase": "AUDIT",
       "actor": "2DER", "require_nonnull": []}
ROUTE = [R09, R11, R12, R13, R14, R15, R16]

def _dw(phase):
    return {"component": "DW", "function": "_append_event",
            "inputs": '{"phase": "%s", "role": "MANAGER"}' % phase,
            "outputs": "{}", "result": "OK"}

def _runner(art_len, status):
    return {"component": "RUNNER", "function": "run_minimal_slice",
            "inputs": '{"target_file": "impl.py", "skeleton_len": 19, "tests_len": 229}',
            "outputs": ('{"status": %s, "classification": "CANONICAL_DISPATCH", '
                        '"artifact_len": %s, "workspace": true}' % (status, art_len)),
            "result": "OK"}

# TASK-2DER-98D5F072 の実測(記録の順そのまま = RUNNER が GENERATE より先)
OK_EVENTS = [_dw("CREATE"), _dw("PROCESS_EVENT"), _dw("PLAN"),
             _runner("36", '"PASSED"'), _dw("GENERATE"), _dw("PROCESS_EVENT"), _dw("AUDIT")]
# TASK-2DER-83CA5708 の実測(RUNNER の outputs だけ違う)
NULL_EVENTS = [_dw("CREATE"), _dw("PROCESS_EVENT"), _dw("PLAN"),
               _runner("null", "null"), _dw("GENERATE"), _dw("PROCESS_EVENT"), _dw("AUDIT")]

# TASK-2DER-51E58279 の実測(2026-08-04T21:06:46) — ★本番で初めて捉えた失敗
# ★artifact_len は 1(★None ではない) ∴ ★規則②は当たらない。★規則①だけで LOCATED になる形
FAILED_EVENTS = [_dw("CREATE"), _dw("PROCESS_EVENT"), _dw("PLAN"),
                 {"component": "RUNNER", "function": "run_minimal_slice",
                  "inputs": '{"target_file": "impl.py", "skeleton_len": 35, "tests_len": 5263}',
                  "outputs": ('{"status": "FAILED", "classification": "CANONICAL_DISPATCH", '
                              '"artifact_len": 1, "workspace": true}'),
                  "result": "FAILED"}]

def test_result_failed_is_located_even_when_artifact_len_is_present():
    """★実測(TASK-2DER-51E58279)。★artifact_len=1 は None でないので ★規則②は当たらない。
    ★規則①(result が OK でも PASSED でもない)だけで ★S14 が特定できること。
    ★これが無いと ★result を ★丸ごと無視する実装が ★全通する(★2026-08-04 に確認済)"""
    v = impl.locate_failure(ROUTE, FAILED_EVENTS)
    assert (v["verdict"], v["segment"]) == ("LOCATED", "S14"), v

def test_null_artifact_len_is_located_at_s14():
    v = impl.locate_failure(ROUTE, NULL_EVENTS)
    assert v["segment"] == "S14", v

def test_null_artifact_len_verdict_is_located():
    assert impl.locate_failure(ROUTE, NULL_EVENTS)["verdict"] == "LOCATED"

def test_located_returns_actor_and_marks_it_known():
    v = impl.locate_failure(ROUTE, NULL_EVENTS)
    assert (v["actor"], v["actor_known"]) == ("2DER", True), v

def test_healthy_run_is_not_located():
    v = impl.locate_failure(ROUTE, OK_EVENTS)
    assert v["segment"] is None, v

def test_healthy_run_is_bounded_not_a_failure():
    assert impl.locate_failure(ROUTE, OK_EVENTS)["verdict"] == "BOUNDED"

def test_blank_segments_are_all_candidates_in_route_order():
    assert impl.locate_failure(ROUTE, OK_EVENTS)["candidates"] == ["S11", "S15"]

def test_s11_is_a_candidate_not_a_failure():
    """★MGR 裁定: S11(run-gate の refused)は ★位置特定できないのが正解。
    ★候補として返り、★失敗にはしない（★返らないことを失敗にしない）"""
    v = impl.locate_failure(ROUTE, OK_EVENTS)
    assert "S11" in v["candidates"] and v["segment"] != "S11", v

def test_bounded_actor_is_returned_but_not_known():
    v = impl.locate_failure(ROUTE, OK_EVENTS)
    assert (v["actor"], v["actor_known"]) == ("Claude", False), v

def test_last_observed_follows_route_order_not_event_order():
    """★実測: RUNNER は記録上 GENERATE より先に出る。★それでも last_observed は S16"""
    assert impl.locate_failure(ROUTE, OK_EVENTS)["last_observed"] == "S16"

def test_shuffling_events_does_not_change_the_result():
    """v1.12: ★邪魔な自由度(記録の順)を振って ★動かないことを見る"""
    a = impl.locate_failure(ROUTE, OK_EVENTS)
    b = impl.locate_failure(ROUTE, list(reversed(OK_EVENTS)))
    assert a == b, (a, b)

def test_no_evidence_when_nothing_matches():
    v = impl.locate_failure(ROUTE, [])
    assert v["verdict"] == "NO_EVIDENCE" and v["last_observed"] is None, v

def test_no_failure_when_every_segment_has_evidence():
    route = [R09, R12, R13, R14, R16]          # ★観測が無い S11 / S15 を外す
    v = impl.locate_failure(route, OK_EVENTS)
    assert v["verdict"] == "NO_FAILURE" and v["candidates"] == [], v

def test_all_four_verdicts_are_reachable():
    """★列挙の肯定側(v1.10)"""
    got = {impl.locate_failure(ROUTE, [])["verdict"],
           impl.locate_failure(ROUTE, NULL_EVENTS)["verdict"],
           impl.locate_failure(ROUTE, OK_EVENTS)["verdict"],
           impl.locate_failure([R09, R12, R13, R14, R16], OK_EVENTS)["verdict"]}
    assert got == {"NO_EVIDENCE", "LOCATED", "BOUNDED", "NO_FAILURE"}, got

def test_actor_follows_the_route_when_the_route_changes():
    """v1.12: ★route の actor だけ振る。★戻り値の actor も ★同じだけ動くこと
    （★2026-08-04 の走行で ★actor を "2DER" と決め打ちした成果物が ★13本 全通したため）"""
    alt = [dict(r, actor="XX-" + r["actor"]) for r in ROUTE]
    a = impl.locate_failure(ROUTE, NULL_EVENTS)["actor"]
    b = impl.locate_failure(alt, NULL_EVENTS)["actor"]
    assert (a, b) == ("2DER", "XX-2DER"), (a, b)

def test_bounded_actor_also_follows_the_route():
    alt = [dict(r, actor="YY-" + r["actor"]) for r in ROUTE]
    assert impl.locate_failure(alt, OK_EVENTS)["actor"] == "YY-Claude"

def test_actor_is_not_claimed_when_nothing_is_located():
    """★NO_EVIDENCE と NO_FAILURE では ★主体を名乗らない"""
    a = impl.locate_failure(ROUTE, [])
    b = impl.locate_failure([R09, R12, R13, R14, R16], OK_EVENTS)
    assert (a["actor"], a["actor_known"], b["actor"], b["actor_known"]) == (None, False, None, False), (a, b)

def test_segment_ids_come_from_the_route_too():
    """★id も ★route 由来であること（★actor と同じ種類の決め打ちを塞ぐ）"""
    alt = [dict(r, id="Z" + r["id"]) for r in ROUTE]
    assert impl.locate_failure(alt, NULL_EVENTS)["segment"] == "ZS14"

def test_verdict_is_never_outside_the_four():
    """★列挙の否定側(v1.10)"""
    broken = [{"component": "RUNNER", "function": "run_minimal_slice",
               "inputs": "not json", "outputs": "not json", "result": None}]
    for evs in ([], OK_EVENTS, NULL_EVENTS, broken, [_dw("CREATE")]):
        assert impl.locate_failure(ROUTE, evs)["verdict"] in (
            "NO_EVIDENCE", "LOCATED", "BOUNDED", "NO_FAILURE")

def test_broken_json_is_treated_as_empty_not_raised():
    broken = [{"component": "RUNNER", "function": "run_minimal_slice",
               "inputs": "not json", "outputs": "not json", "result": "OK"}]
    v = impl.locate_failure(ROUTE, broken)      # ★例外にならないこと
    assert v["segment"] == "S14", v             # ★outputs が読めない = artifact_len が無い = 失敗
<<<2DER:END>>>
```

## 4. ★依頼文の規則 → 試験の対応表（v1.13）

| 依頼文の規則 | 縛る試験 |
|---|---|
| 文字列の JSON を読む／読めなければ {} | `test_broken_json_is_treated_as_empty_not_raised` |
| component/function が None の行は一致しない | `test_healthy_run_points_at_the_first_blank_segment`（S15） |
| 失敗①（result が OK/PASSED でない） | **`test_result_failed_is_located_even_when_artifact_len_is_present`**（★実測）／ `test_verdict_is_never_outside_the_four` の `broken` |
| 失敗②（require_nonnull が None） | `test_null_artifact_len_is_located_at_s14` |
| last_observed は route 順 | `test_last_observed_follows_route_order_not_event_order` |
| candidates は last_observed より後ろだけ | `test_healthy_run_points_at_the_first_blank_segment` |
| 4語・この順 | `test_all_four_verdicts_are_reachable` ＋ `..._never_outside_the_four` |
| ★actor は ★route の行から引く（★決め打ちでない） | `test_actor_follows_the_route_when_the_route_changes` ／ `test_bounded_actor_also_follows_the_route` ／ `test_actor_is_not_claimed_when_nothing_is_located` |
| ★segment の id も ★route から引く | `test_segment_ids_come_from_the_route_too` |
| ★S11 は候補であって失敗でない | `test_s11_is_a_candidate_not_a_failure` ／ `test_blank_segments_are_all_candidates_in_route_order` |
| actor と actor_known | `..._actor_and_marks_it_known` ／ `..._actor_is_returned_but_not_known` |
| 並び順は結果を変えない | `test_shuffling_events_does_not_change_the_result` |

## 5. ★Claude の配線（★0〜4行と予告）

```
★口を増やさない。★`/api/etrace?task_id=…` は ★既に在る（★段1 で使った）。
★★成果物は `twoder/locate_failure.py` へ ★無改変で置く（★sha256 で照合）。
★★★受入(1) の 4件は ★実装が ★1回ずつ手で呼び、★結果を ★台帳の note に書く。
★★★★★∴ ★配線 0行も 在りうる。★0 なら 0 と書く（★水増ししない）。
★★★★★★18行の route を ★ファイルに置くのは ★本件では やらない（★管理対象を2つ増やさない）。
   ★畳む条件 = ★段3 が通り、★同じ 18行を ★2回以上 手で打つことになった時。★その時に ★MGR へ上げる。
```

## 6. 受入（★MGR が固定した3点を そのまま）

```
★(1) ★worker が `locate_failure` を書く（★Claude は本文0行・★実行記録で確認）／★(2) ★20本 全通
★(3) ★★本日の実事故4件に ★段1 の 18行の表を route として当て、★1件ずつ 逐語で書く:
      (a) GENERATE が0字（TASK-2DER-6F0FDAAB）
      (b) run-gate の refused（cause=NOT_RUNNABLE）
          ★★★MGR 裁定（逐語）=★『位置特定できない』が★正しい答え＝★unknown/候補 で返ることを受入にする
          ★★★★（★返らないことを★失敗にしない）
      (c) JUDGE_REQUIRED（TASK-2DER-68AB3AA4）
      (d) 空の artifact
    ★★★各件について ★verdict / segment / last_observed / candidates[0] / actor / actor_known を ★全部 書く
    ★★★★★『返らない』ものは ★★『返らない』と書く（★埋めたように書かない）
    ★★★★★★(a)(c)(d) の3件は ★区間 ID が ★返ること（★MGR 裁定）／ ★(b) だけが ★候補で返る
★(4) ★★主体を ★同時に返している（★actor と actor_known が ★4件とも 出る）
★(5) ★sha256 一致 ／ ★(6) ★Claude の配線行数（★0 なら 0）／★(7) ★戻せる ／★(8) ★61本を走らせない
★★★★(9) ★出せなかったら ★『出せなかった』と書いて ★止まる（★捏造した事故を作らない）
★★★★★予告を投入前に書く: ★(3) の 4件で ★返ると思う verdict（★4件分）
```

## 7. ★★これで分からないこと（★先に言う・★空欄を消さない）

```
★S03 S04 S05 S08 S10 ★S11 S15 は ★実行記録が ★1件も無い ∴ ★★候補としてしか出ない。
★★特に ★S11 は ★EVO-0053 で ★応答には理由が載るようになったが ★★記録には残らない（★§1 の実測）。
★★★MGR 裁定（逐語）=★経路表の S11 は ★『埋まっている』ではなく ★★『応答には出る／記録には残らない』が正しい。
★★★★『応答に在る理由を ★実行記録にも残す』は ★★別の1区間 ＝ ★段2 の候補に戻す。★いま着手しない（規律9・ACTIVE は段3）。
★★★∴ ★『どの区間で止まったか』は ★★埋まっている区間の分だけ 言える。★それが 本件の全部である。
★★★★★★『経路表が埋まった』『止まった場所が分かるようになった』とは ★★書かない。
   ★書いてよいのは ★★『ここまでは言える、その先は記録が無い』だけ。
★★★★★★★★空欄を ★消さない（★裁定の逐語=★空欄が ★次に落ちる場所を名指しし続ける）。
```

## 8. 禁止

```
★Claude が `locate_failure` の中身を書く ／ ★空欄の区間を route から消す
★`actor` / `segment` を ★引数から引かずに ★文字列で決め打ちする（★2026-08-04 の走行で ★実際に起きた）
★event の並び順に頼る実装にする（★§2(a) の実測に反する）
★`result` だけで失敗を決める（★§2(b) の実測に反する）
★83CA5708 の null を ★『事故(4) を当てた』と書く（★計器が自分を数える）
★18行の route を ★新しいファイル・台帳に置く（★本件では やらない・★§5 に畳む条件を書いた）
★5語目の verdict を作る ／ ★1つの assert に2つの意図を入れる
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
