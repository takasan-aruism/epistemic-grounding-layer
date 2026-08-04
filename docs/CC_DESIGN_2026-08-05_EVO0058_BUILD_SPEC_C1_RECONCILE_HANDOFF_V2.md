# 【BUILD SPEC v2】`EVO-0058` (C') — **★渡し方の事故を除外する `reconcile_handoff`**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-05 02:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035` ／ 基本設計: `CC_DESIGN_2026-08-05_EVO0058_BASIC_DESIGN_HANDOFF_RECORD.md` §3
- **★v1.8 の宣言**: **★核は在る・1件**（`reconcile_handoff`＝純関数）→ **★2DER 工程 1 になりうる**
- **★私の予告**: ★worker の行数は書かない ／ ★Claude の配線 **0〜4行**（★呼ぶだけ・★口を増やさない）
- **★v1 との関係**: ★差し替えない・追記しない（規律）。**★本書が実装源**
- **★v1 からの差は ★依頼文の④⑤の書き方だけ**: ★★試験は ★1本も緩めない・★1文字も変えない（★落ちた1本も ★残す）
- **★`enable_thinking=False` の1引数は ★入ったまま**（★戻さない・★MGR 条件）
- **★段3 の契約は ★1文字も変えない**（★未知の欄は `locate_failure` が無視する）
- **★走行 0（★私は）・★task 増 0・★commit 0**

---

## 1. ★L0 に「受け側」を足す（★MGR の問いへの答え・★行は増やさない）

```
★区間は ★1行のまま。★受け渡しは ★その行の ★属性である ∴ ★★欄を2つ足す（★行を増やさない・★表を2枚にしない）
```

```python
 # twoder/route_table.py の S14 の行に ★2欄 足す（★他の17行は "handoff": None, "receipt": None）
 {"id": "S14", ...,
  "handoff": ["RUNNER", "hand_to_worker"],          # ★渡した側の (component, function)
  "receipt": ["WORKER", "received_from_runner"]},   # ★受け取った側の (component, function)
```
```
★★`locate_failure` は ★この2欄を ★読まない（★未知の欄は無視）∴ ★★段3 の契約は ★1文字も変わらない
★★★`handoff` が None の行 = ★★『まだ配線していない』であって ★『切れている』ではない ―― ★§2 で ★語を分ける
```

## 2. ★★契約（★そのまま封入できる形。★封入は MGR）

**★依頼文**
```
受け渡しが無傷かを判定する純関数 impl.reconcile_handoff を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
route = [ {"id": str, "handoff": [str, str]|None, "receipt": [str, str]|None}, ... ]  ★この順が区間の順
events = [ {"event_id": str, "component": str, "function": str,
            "inputs": dict|str, "outputs": dict|str}, ... ]
戻り値 = {"segments": [ {"id": str, "link": str, "handed": int|None, "received": int|None} , ... ],
          "first_break": str|None, "broken": [str, ...]}

・inputs / outputs は dict でも JSON 文字列でもよい。文字列なら json で読む。
  ★読めなければ {} として扱う（★例外にしない）。dict でも文字列でもなければ {}。
・その行の「渡した event」= component と function が row["handoff"] と等しく、
  かつ outputs の "segment" が row["id"] と等しい event。★複数あれば ★最後のもの。
・その行の「受け取った event」= 同じ規則を row["receipt"] で。★複数あれば ★最後のもの。
・handed  = 渡した event の outputs["handoff_len"]（★無ければ None）
・received = 受け取った event の outputs["handoff_len"]（★無ければ None）
・link は NOT_WIRED / NO_EVENT / UNLINKED / PHANTOM / ALTERED / LINKED の★6語。★他の語を作らない。
  ★この順で ★最初に当たったもの:
    ① row["handoff"] が None または row["receipt"] が None → "NOT_WIRED"
    ② 渡した event も 受け取った event も 無い              → "NO_EVENT"
    ③ 受け取った event が 無い                              → "UNLINKED"
    ④ 受け取った event の inputs に "received_event_id" の ★キーが無い、
       ★または ★キーは在るが 値が None → "UNLINKED"
       （★★『無い』は ★2通りある。★どちらも ★ここで拾う。★⑤へ落とさない）
    ⑤ ★④に当たらなかった時だけ:
       その値と等しい "event_id" を持つ event が ★events の中に無い → "PHANTOM"
       （★★PHANTOM は ★『値を書いたが ★実在しない』の意味であって、
         ★『値を書かなかった』は ★PHANTOM ではない）
    ⑥ 両方の outputs["handoff_sha256"] が ★等しくない        → "ALTERED"
    ⑦ それ以外                                              → "LINKED"
・broken = link が "LINKED" でも "NOT_WIRED" でもない行の id を ★route 順に。
・first_break = broken の最初。★broken が空なら None。
・★events の並び順は結果を変えない（★順番は route が決める）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def reconcile_handoff(route, events):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```
```
★★★骨格に ★`<<<FILL: ここに実装>>>` を ★入れた ―― ★理由 = ★`request_template.py:58` 逐語
   「★示さないと ★骨格 全文が ★変更禁止になります」／ ★requirement は ★『FILL 部分だけを実装せよ』と命じる。
★★★★段3 の契約には ★これが ★無かった（★私の欠落）。★但し ★★『これが0字の原因』とは ★書かない
   （★FILL 無しで通った例が在る＝EVO-0053）。★★本件は ★足しておくだけである。
```

**★封印試験（★14本・★fixture は ★2026-08-05 の実測から取る）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

SHA = "3f22a2e42a3d6709"                       # ★実測(TASK-2DER-37D5DC9B)の先頭16字
HID = "ETR-6b785dedf935-0013"                  # ★実測: 送り手の event_id

R14 = {"id": "S14", "handoff": ["RUNNER", "hand_to_worker"],
       "receipt": ["WORKER", "received_from_runner"]}
R15 = {"id": "S15", "handoff": None, "receipt": None}
ROUTE = [R14, R15]

def _hand(sha=SHA, ln=7522, eid=HID):
    return {"event_id": eid, "component": "RUNNER", "function": "hand_to_worker",
            "inputs": '{"segment": "S14"}',
            "outputs": '{"segment": "S14", "handoff_len": %d, "handoff_sha256": "%s"}' % (ln, sha)}

def _recv(sha=SHA, ln=7522, rid=HID):
    return {"event_id": "ETR-6b785dedf935-0014", "component": "WORKER",
            "function": "received_from_runner",
            "inputs": '{"segment": "S14", "received_event_id": %s}' % (
                "null" if rid is None else '"%s"' % rid),
            "outputs": '{"segment": "S14", "handoff_len": %d, "handoff_sha256": "%s"}' % (ln, sha)}

def test_the_real_run_is_linked():
    """★2026-08-05 の実測(TASK-2DER-37D5DC9B)= 両側一致・LINKED"""
    v = impl.reconcile_handoff(ROUTE, [_hand(), _recv()])
    assert v["segments"][0]["link"] == "LINKED", v

def test_lengths_are_reported_from_both_sides():
    v = impl.reconcile_handoff(ROUTE, [_hand(), _recv()])
    assert (v["segments"][0]["handed"], v["segments"][0]["received"]) == (7522, 7522), v

def test_unwired_segment_is_not_called_broken():
    """★配線していない区間を ★『切れている』と言わない"""
    v = impl.reconcile_handoff(ROUTE, [_hand(), _recv()])
    assert v["segments"][1]["link"] == "NOT_WIRED" and v["broken"] == [], v

def test_no_event_when_wired_but_nothing_ran():
    v = impl.reconcile_handoff([R14], [])
    assert v["segments"][0]["link"] == "NO_EVENT", v

def test_unlinked_when_receiver_is_missing():
    v = impl.reconcile_handoff([R14], [_hand()])
    assert v["segments"][0]["link"] == "UNLINKED", v

def test_unlinked_when_receiver_quotes_nothing():
    v = impl.reconcile_handoff([R14], [_hand(), _recv(rid=None)])
    assert v["segments"][0]["link"] == "UNLINKED", v

def test_phantom_when_the_quoted_id_does_not_exist():
    """★受け手が ★作れない値を ★作った形（★捏造）"""
    v = impl.reconcile_handoff([R14], [_hand(), _recv(rid="ETR-does-not-exist-0001")])
    assert v["segments"][0]["link"] == "PHANTOM", v

def test_altered_when_the_fingerprints_differ():
    """★★本日の385字事故の型（★渡した物と 受け取った物が 違う）"""
    v = impl.reconcile_handoff([R14], [_hand(), _recv(sha="0000000000000000", ln=7137)])
    assert v["segments"][0]["link"] == "ALTERED", v

def test_altered_is_reported_in_broken_and_first_break():
    v = impl.reconcile_handoff(ROUTE, [_hand(), _recv(sha="0000000000000000")])
    assert (v["broken"], v["first_break"]) == (["S14"], "S14"), v

def test_linked_run_has_no_first_break():
    v = impl.reconcile_handoff(ROUTE, [_hand(), _recv()])
    assert v["first_break"] is None, v

def test_event_order_does_not_change_the_result():
    a = impl.reconcile_handoff(ROUTE, [_hand(), _recv()])
    b = impl.reconcile_handoff(ROUTE, [_recv(), _hand()])
    assert a == b, (a, b)

def test_broken_json_is_treated_as_empty_not_raised():
    bad = {"event_id": "X", "component": "RUNNER", "function": "hand_to_worker",
           "inputs": "not json", "outputs": "not json"}
    v = impl.reconcile_handoff([R14], [bad])          # ★例外にならないこと
    assert v["segments"][0]["link"] == "NO_EVENT", v  # ★segment が読めない ∴ 一致しない

def test_all_six_links_are_reachable():
    """★列挙の肯定側(v1.10)"""
    got = {impl.reconcile_handoff([R15], [])["segments"][0]["link"],
           impl.reconcile_handoff([R14], [])["segments"][0]["link"],
           impl.reconcile_handoff([R14], [_hand()])["segments"][0]["link"],
           impl.reconcile_handoff([R14], [_hand(), _recv(rid="ETR-nope-0001")])["segments"][0]["link"],
           impl.reconcile_handoff([R14], [_hand(), _recv(sha="ffff")])["segments"][0]["link"],
           impl.reconcile_handoff([R14], [_hand(), _recv()])["segments"][0]["link"]}
    assert got == {"NOT_WIRED", "NO_EVENT", "UNLINKED", "PHANTOM", "ALTERED", "LINKED"}, got

def test_link_is_never_outside_the_six():
    """★列挙の否定側(v1.10)"""
    for evs in ([], [_hand()], [_recv()], [_hand(), _recv()], [{"event_id": "Z"}]):
        for r in ([R14], [R15], ROUTE):
            for s in impl.reconcile_handoff(r, evs)["segments"]:
                assert s["link"] in ("NOT_WIRED", "NO_EVENT", "UNLINKED",
                                     "PHANTOM", "ALTERED", "LINKED"), s
<<<2DER:END>>>
```

## 2-b. ★★なぜ落ちたか（★私の書き方の欠陥・★先に書く）

```
★現物は ★14本中1本 落ちた = ★『一致0件の行で ★PHANTOM が返るが ★UNLINKED 期待』（MGR 実測）
★★原因 = ★★v1 の④「`received_event_id` が ★無い」の ★『無い』が ★2通りに読める:
   (あ) ★キー自体が 無い    (い) ★キーは在るが ★値が None
★★★fixture は ★(い)（`"received_event_id": null`）∴ ★(あ)だけと読むと ★④に当たらず ★⑤へ落ちて ★PHANTOM。
★★★★★私の欠陥である ―― ★同じ趣旨を ★段3 の契約では
   「★key が outputs に ★無い、または ★値が None」と ★2通り 明記していた（★そちらは ★通っている）。
   ∴ ★★書き分けを ★1箇所だけ ★怠った。★★試験は正しい ∴ ★試験は ★1本も触らない。
★★★★★★v2 で足したのは ★★意味ではなく ★★書き方だけ（★測る強さは ★1ミリも変わらない）
```

## 3. ★★この関数が答える問い（★答えない問いも書く）

```
★★答える = ★★『渡し方の事故だったか』 ―― ★★LINKED なら ★★渡し方は ★無傷であると ★除外できる。
★★★答えない = ★『なぜ0字か』。★受入(a) は ★★既に LINKED である（★B' の実測）
   ∴ ★★本件が通っても ★(a) の原因は ★出ない。★★それでも ★収穫である＝
   ★★★★『385字事故の型（ALTERED）ではない』と ★機械が ★言い切れる ＝ ★★候補が1つ ★消える。
★★★★★これを ★『言い当てた』と ★書かない（★MGR §3 の受入は ★区間と担当を ★言い当てること）
```

## 4. ★★担当の食い違い（§4(5)）は ★本件に入れない（★理由を書く）

```
★実測 = ★`etrace.emit` に ★担当（identity / actor_role）を ★残す欄が ★★無い（`ds/ds/etrace.py:95-96`）
★★∴ ★『実測の担当』を ★記録から取れない ―― ★component 名で代用すると ★★人が決めた対応表が要る＝★判断が混じる
★★★∴ ★本件では ★返さない（★規律9・★同時に増やさない）。★★『赤で出せる』と ★書かない。
★★★★戻る条件 = ★本件が通り、★(a) 以外の区間が ★1つ配線された時（★比べる相手が ★2つ以上になった時）
★★★★★いま足りないもの = ★emit に ★担当を1欄（★新しい台帳ではない・★既存関数の引数）
```

## 5. ★★読み出しの穴（★MGR の実測を ★受入に折り込む）

```
★MGR 実測 = ★`GET /api/etrace?task_id=` は ★★0件を返す（本日2回とも）／ ★`run_id` なら ★17件 返る
★★∴ ★本件の events は ★★`run_id` で集める。★受入(1) に ★どの run_id から取ったかを ★逐語で書かせる
★★★★『task_id から追えない』は ★★別の1件（★次に作る読み出し・★本件では作らない）
★★★★★危険 = ★1つの task が ★複数 run にまたがる（★実測: CREATE と RUNNER が ★別 run）
   ∴ ★★送りと受けが ★別 run に落ちると ★★PHANTOM に見える。★受入(3) で ★同一 run であることを ★確かめる
```

## 6. 受入

```
★(0) ★worker が書く（★Claude は本文0行）・★14本 全通
★(1) ★★実データで1回 呼ぶ = ★`TASK-2DER-37D5DC9B` の ★run（★`run_id` から集める・★どの run か逐語）
★(2) ★★`S14` が ★`LINKED` と出る（★B' の実測と ★一致する）
★(3) ★★送りと受けが ★同一 run であることを ★逐語で示す（★§5 の危険）
★(4) ★本日の詰まり4件を当て、★(b)(c)(d) は ★★`NOT_WIRED` と返ることを ★書く
     ★★★これは ★『言い当てられなかった』の ★機械版である ＝ ★★次に配線する区間の ★名指しになる
★(5) ★sha256 一致 ／★(6) ★Claude の配線行数（★0 なら 0）／★(7) ★戻せる ／★(8) ★61本を走らせない
★★★(9) ★出せなかったら『出せなかった』と書いて止まる
★★★★★予告を投入前に書く: ★(2) の結果 ／ ★(4) で `NOT_WIRED` になる件数
```

## 7. 禁止

```
★Claude が `reconcile_handoff` の中身を書く ／ ★段3 の契約を触る ／ ★2枚目の経路表を作る
★`NOT_WIRED` を ★`broken` に入れる（★未配線を ★断線と混ぜない）
★担当の食い違いを ★本件で判定する（★§4）／ ★component 名から担当を ★推定する
★『経路表が埋まった』『0字の原因が分かった』と書く（★§3）
★新しい台帳・計器・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
