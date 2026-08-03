# 【BUILD SPEC】`EVO-0053` — **★拒否の理由を正す。★並行は直さない**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入は MGR） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 02:1x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.10）** ／ **★9項目 確認済（★§7）** ／ 親: `ITEM-2DER-EVO-0035`
- **★v1.8 の宣言**: **★核は在る**（2026-08-03 22:3x に実測で宣言済・MGR が採用）
- **★私の予告**: ★worker **10〜18行**／★Claude の配線 **6〜10行**
- **★走行 0・★task 増 0・★commit 0**

---

## 1. ★誤った理由文が出る仕組み（★逐語・★これが本件）

```
★`webui.py:814` refuse = (gate["blocked"] or not gate["runnable"] or tid != gate["task_id"])
★`webui.py:816` reason = (gate["reason"] ★or f"task {tid} is not the current runnable submit task ({gate['task_id']})")
★★∴ ★3つの理由を ★1つの bool に潰し、★`gate["reason"]` が ★空の時は
   ★★原因を確かめずに ★『id が違う』の文面を出す。
★★★本日の実物(MGR 実測・逐語)=
   『task TASK-2DER-156778F6 is not the current runnable submit task (★TASK-2DER-156778F6)』
   ＝ ★同じ id を並べて『違う』と言っている。★実際の原因は ★`runnable: False`。
```

## 2. ★分担
```
★worker : ★`gate_decision(gate, requested_task_id)` ★1関数だけ（★純関数）
★Claude : ★配線のみ ＝ ★`:814-818` を ★`gate_decision` の戻りに置き換える
★★★Claude は ★中身を1文字も書かない
```

## 3. ★★契約（★そのまま封入できる形。★封入は MGR）

**★依頼文**
```
走行の許可を判定する純関数 impl.gate_decision を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
★骨格(SKELETON)は1文字も変えずに残し、その ★続きに実装の本体を書いてください。
★試験は `import impl` と書いてください。2DER が作る成果物は必ず impl.py です。

■ 規則（これだけ。創作しない）
gate = {"blocked": bool, "runnable": bool, "task_id": str|None, "reason": str}
requested_task_id = str
戻り値 = {"allow": bool, "cause": str, "reason": str|None}

・cause は BLOCKED / NOT_RUNNABLE / TASK_MISMATCH / OK の★4語のいずれか。★他の語を作らない。
・★調べる順番は この順で、★最初に当たったものを cause にする:
    ① blocked が True                  → "BLOCKED"
    ② runnable が False                → "NOT_RUNNABLE"
    ③ gate["task_id"] != requested_task_id → "TASK_MISMATCH"
    ④ どれでもない                      → "OK"
・allow は cause が "OK" の時だけ True。
・reason は gate["reason"] が空でなければ その値。空なら cause に応じた1行を作る:
    BLOCKED        → "submit was blocked"
    NOT_RUNNABLE   → "no runnable task in the current submit context"
    TASK_MISMATCH  → "requested <requested_task_id> but current is <gate['task_id']>"
    OK             → None
・★TASK_MISMATCH の文面には ★両方の id を入れる（★同じ id を並べない＝②で先に止まるため）。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def gate_decision(gate, requested_task_id):
<<<2DER:END>>>
```

**★封印試験（★7本・★v1.9 と v1.10 を守る）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_the_real_case_from_today_is_not_a_mismatch():
    """★本日 実際に踏んだ入力(v1.9=実データから採る)。★同じ id なのに mismatch と言われた形"""
    g = {"blocked": False, "runnable": False,
         "task_id": "TASK-2DER-156778F6", "reason": ""}
    v = impl.gate_decision(g, "TASK-2DER-156778F6")
    assert v["cause"] == "NOT_RUNNABLE", v
    assert v["allow"] is False
    assert "156778F6" not in (v["reason"] or "") or "requested" not in (v["reason"] or "")

def test_all_four_causes_are_reachable():
    """★列挙は全部 通ること(v1.10 の対・肯定側)"""
    got = set()
    got.add(impl.gate_decision({"blocked": True, "runnable": True, "task_id": "T", "reason": ""}, "T")["cause"])
    got.add(impl.gate_decision({"blocked": False, "runnable": False, "task_id": "T", "reason": ""}, "T")["cause"])
    got.add(impl.gate_decision({"blocked": False, "runnable": True, "task_id": "T", "reason": ""}, "U")["cause"])
    got.add(impl.gate_decision({"blocked": False, "runnable": True, "task_id": "T", "reason": ""}, "T")["cause"])
    assert got == {"BLOCKED", "NOT_RUNNABLE", "TASK_MISMATCH", "OK"}, got

def test_cause_is_never_outside_the_four():
    """★列挙外を作らないこと(v1.10 の対・否定側)"""
    for g, r in (({"blocked": True, "runnable": False, "task_id": None, "reason": "x"}, "T"),
                 ({"blocked": False, "runnable": True, "task_id": None, "reason": ""}, "T"),
                 ({"blocked": False, "runnable": False, "task_id": "T", "reason": "y"}, "T")):
        assert impl.gate_decision(g, r)["cause"] in ("BLOCKED", "NOT_RUNNABLE", "TASK_MISMATCH", "OK")

def test_order_blocked_wins_over_mismatch():
    v = impl.gate_decision({"blocked": True, "runnable": False, "task_id": "T", "reason": ""}, "U")
    assert v["cause"] == "BLOCKED"

def test_allow_only_when_ok():
    ok = impl.gate_decision({"blocked": False, "runnable": True, "task_id": "T", "reason": ""}, "T")
    ng = impl.gate_decision({"blocked": False, "runnable": True, "task_id": "T", "reason": ""}, "U")
    assert ok["allow"] is True and ok["reason"] is None
    assert ng["allow"] is False

def test_existing_reason_is_kept():
    """★理由が既に在るなら 捨てない(★作り直さない)"""
    v = impl.gate_decision({"blocked": True, "runnable": False, "task_id": "T",
                            "reason": "dead-approach BLOCK"}, "T")
    assert v["reason"] == "dead-approach BLOCK"

def test_mismatch_message_names_both_ids():
    v = impl.gate_decision({"blocked": False, "runnable": True, "task_id": "T-CUR", "reason": ""}, "T-REQ")
    assert "T-REQ" in v["reason"] and "T-CUR" in v["reason"]
<<<2DER:END>>>
```

## 4. ★Claude が書く配線（★行数を申告）

```python
# webui.py:814-818 を置き換える
                    from twoder.gate_decision import gate_decision as _gd   # ★置いた成果物
                    _d = _gd(gate, tid)
                    if not _d["allow"]:
                        return self._send({"refused": True, "blocked": gate["blocked"],
                                           "runnable": gate["runnable"], "dispatched": False,
                                           "reason": _d["reason"], ★"cause": _d["cause"], "task_id": tid})
```
```
★★`cause` を ★1欄 足す（★理由の分類が ★機械で読める）。★既存の欄は ★消さない・改名しない
```

## 5. ★★これで直らないこと（★裁定の逐語を守る）

```
★★『並行が直った』と ★書かない。★`_LAST` は ★`webui.py:32` の ★プロセス内 dict 1つのままで、
   ★他者の投入で ★許可が奪われることは ★変わらない。
★★★直るのは ★★「なぜ拒否されたかが正しく分かる」だけ。★回数も減らない。
★★★★★次に測るべきこと=★`cause` の内訳（★どの理由で何回 拒否されたか）。★但し ★本件では ★数えない（★増やさない）
```

## 6. 受入
```
★(1) ★worker が書く（★Claude は本文0行・★実行記録で確認）／★(2) ★7本 全通
★(3) ★★本日の入力で ★`cause == "NOT_RUNNABLE"`（★`TASK_MISMATCH` ではない）
★(4) ★4語すべてが出る／★列挙外が出ない
★(5) ★`/api/run_next` の応答に ★`cause` が出る（★実際に1回 拒否させて逐語を持ち帰る）
     ★★拒否させる手が無ければ ★『無い』と書いて ★止まる（★捏造した対照を作らない）
★(6) ★sha256 一致 ／ ★(7) ★行数を分ける ／ ★(8) ★戻せる ／ ★(9) ★61本を走らせない
★★★★★予告を投入前に書く: ★worker の行数 ／ ★(3) で出ると思う cause
```

## 7. ★9項目（私の分）
```
1 置いたなら読めるか＝★受入(5) は ★front door の応答で見る
2 読めるなら書けるか＝★書く側（`_LAST` の更新）は ★本件では触らない（★§5）
3 理由を捨てない＝★★`test_existing_reason_is_kept` で ★既存の理由を ★捨てない縛りを置いた
4 作っていないのでは＝★判定は ★既に `:814` に1行で在る。★無いのは ★★理由の切り分けだけ
5 走ったか＝★受入(5) は ★実際に拒否させて測る
6 名前＝★`blocked` / `runnable` / `task_id` / `reason`（★既存欄）＋★`cause`（★新語だが ★状態語でなく ★応答の欄）
★7 依頼と試験の矛盾＝★依頼文の「4語」を ★肯定側1本＋否定側1本の ★対で縛った
8 計器が自分を数えないか＝★受入(3) は ★本日の実データを fixture にする（★作文でない）
★9 増える代わりに廃止＝★★「拒否の理由を ★人が推測する」運用を畳む。
   ★★但し ★§5 のとおり ★並行は残る ∴ ★「run-gate を直した」と ★書かない
```

## 8. 禁止
```
★Claude が `gate_decision` の中身を書く ／ ★`_LAST` の持ち方を変える（★並行は範囲外）
★`cause` に5語目を作る ／ ★既存の `reason` を ★上書きする（★在るなら残す）
★『並行が直った』『run-gate を直した』と書く ／ ★捏造した拒否を作る
★新しい台帳・エンドポイントを作る ／ ★61本を走らせる ／ ★commit する
★`twoder` 配下で python を動かす（★`operator.py` の罠）
```
