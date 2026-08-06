# 【BUILD SPEC】`①上級監査の自動化` — **★まず ★『機構が受ける語か』を ★閉じる（★実データの陰性が 在る）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 01:0x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.15）** ／ 台帳: `ITEM-2DER-EVO-0035`
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限4行**
- **★fixture は 実データ（★規律 v1.9）／ ★陽性・陰性の対も 実データ（★規律 v1.10）**

---

## 1. ★★測ったこと（★私が 自分で 引いた・★伝聞に 乗らない）

```
★(a) ★止まる所（★逐語 `dev-workcell/dw/dispatch.py` の `_MAP`）:
     "READY_FOR_UPPER_REVIEW": ("UPPER_REVIEW", ★"CLAUDE_SENIOR", "TASK+RUNS+TEST_RESULT", ★True)
     "JUDGE_REQUIRED":         ("UPPER_REVIEW", ★"CLAUDE_SENIOR", "TASK+RUNS+TEST_RESULT", ★True)
     ★末尾の True = ★claude_barrier（★ここで 機械が 止まる）

★(b) ★呼べない理由（★逐語 `twoder/webui.py:463`）:
     return {"CODING_WORKER": cw, "INDEPENDENT_AUDITOR": au, "MANAGER": mgr, "BUILD_PLANNER": build_planner}
     ★★`CLAUDE_SENIOR` が ★登記されていない ∴ ★2DER から 呼べない。

★(c) ★★受け口は ★もう 在る（★逐語 `webui.py:475-476`）:
     elif op == "UPPER_REVIEW": W.record_upper_review(task_id, ★result["review"], TS, "claude-senior")

★(d) ★★機構が 受ける語は ★2語だけ（★逐語 `dev-workcell/dw/workcell.py:196-204`）:
     v = review["verdict"].upper()
     v == "PASS" かつ last_test_passed → READY_FOR_UPPER_REVIEW（★完了 gate へ）
     v == "FAIL"                      → READY_FOR_REGENERATE または JUDGE_REQUIRED
     ★それ以外（INDETERMINATE / 空 / 知らない語 / PASS だが試験未通過）→ ★★JUDGE_REQUIRED

★(e) ★★手本は 在る（★COMPLETE 6件 すべてに 上級監査の記録・★実データ）
```

## 2. ★★実データの 陰性（★★これが 本 SPEC の 芯です）

```
★`TASK-2DER-156778F6` には ★上級監査が ★2件 記録されている（★逐語）:
   ★1件目: {"verdict": ★"APPROVED", "basis": "…"}
   ★2件目: {"verdict": ★"PASS",     "basis": "…（★verdict は機構が受ける2語のうち PASS）…
             ★前回 APPROVED と書いて JUDGE_REQUIRED へ落ちたのは 機構の欠陥ではなく ★語の誤り
             = ★fail-closed が 正しく働いた"}
★★∴ ★★『知らない語を 書くと 黙って JUDGE_REQUIRED へ落ちる』は ★★実際に 起きている。
★★★∴ ★上級監査を 機械が 書くようにすると、★この失敗は ★人手より 増える。
   ★★だから ★★最初に 閉じるのは ★『語が 機構に 通じるか』である。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
上級監査の結果が「機構が受け取れる語」を持つかを判定する純関数 impl.is_known_verdict を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
review = 任意の値
戻り値 = True または False。

読み方は4通り。上から順に、最初に当てはまった1つで決める。

(1) review が dict でない → False
(2) review["verdict"] が str でない、または欄が無い → False
(3) その値の前後の空白を除き、英大文字に直した物が "PASS" または "FAIL" → True
(4) (1)(2)(3) のどれにも当てはまらない → False

★状態は見ない。★試験が通ったかも見ない。★この関数が答えるのは「語が通じるか」だけ。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def is_known_verdict(review):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★8本・★fixture は `TASK-2DER-156778F6` の実物）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

def test_pass_is_known_when_verdict_is_pass():
    """★実データの陽性: 2件目の記録(★受け入れられた)"""
    assert impl.is_known_verdict({"verdict": "PASS", "basis": "MGR の上位レビュー"}) is True

def test_approved_is_unknown_when_verdict_is_approved():
    """★実データの陰性: 1件目の記録(★JUDGE_REQUIRED へ落ちた実例)"""
    assert impl.is_known_verdict({"verdict": "APPROVED", "basis": "MGR の上位レビュー"}) is False

def test_fail_is_known_when_verdict_is_fail():
    assert impl.is_known_verdict({"verdict": "FAIL", "basis": "x"}) is True

def test_lowercase_is_known_because_the_machine_uppercases_it():
    """★機構は .upper() してから比べる ∴ 小文字も通じる"""
    assert impl.is_known_verdict({"verdict": "pass", "basis": "x"}) is True

def test_surrounding_spaces_are_ignored():
    assert impl.is_known_verdict({"verdict": "  FAIL  ", "basis": "x"}) is True

def test_missing_verdict_field_is_unknown():
    assert impl.is_known_verdict({"basis": "x"}) is False

def test_non_string_verdict_is_unknown():
    assert impl.is_known_verdict({"verdict": 1, "basis": "x"}) is False

def test_non_dict_is_unknown():
    assert impl.is_known_verdict(None) is False
<<<2DER:END>>>
```

## 4. ★★配線（★上限4行）／ ★★私が 決めないこと

```
★配線 = ★上級監査の結果を `ingest` へ渡す ★前に 1回 通す。
        ★False なら ★渡さず、★理由を 欄に 残す（★黙って JUDGE_REQUIRED へ 落とさない）。
★★★私が 決めないこと（★基本設計＝MGR / Taka）:
   ★(i) ★`CLAUDE_SENIOR` を ★何が 担うか（★Qwen か ★Opus か）
        ―― ★Taka 逐語『そこは 2DER が 呼び出して処理を行う。3Claude はそこに関係しない』
           『開発中に Opus を呼ぶな、と言っているのではない』
        ∴ ★★『2DER 自身が 呼ぶ』ことだけが 決まっており、★★何を 呼ぶかは ★決まっていません。
   ★(ii) ★`_MAP` の ★claude_barrier を True→False に するか（★★登記が 済むまでは ★True のまま＝fail-closed）
★★★★先例 = ★`BUILD_PLANNER` が ★同じ穴（★登記されていない担当）を ★同じ形で 埋めています
   ∴ ★★新しい型を 作らず ★5つ目を 同じ形で 足せば 足ります。
```

## 5. ★★受入（★MGR が 測る・★私は 形だけ 出す）

```
★(1) ★8本 全通（★worker が書く・★Claude は本文0行）
★(2) ★★どの口の どの欄で 読めるか（★本日の学び・★先に 1つ 書く）=
     ★`GET /api/resolve?id=TASK-…` の ★`artifact.name` が ★`is_known_verdict` ／ ★`found` が true
★(3) ★陰性が 実データである こと= ★`APPROVED` で False（★§2 の 1件目）
★(4) ★sha256 一致 ／ ★(5) ★Claude の配線行数（★上限4行）
★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない ／ ★(9) ★twoder 配下で python を動かさない
```

## 6. ★★私が 言っていないこと

```
★『これで 上級監査が 自動化される』―― ★★していません。★閉じるのは ★語の1点だけ。
★『CLAUDE_SENIOR を 登記してよい』―― ★★決めていません（★§4(i) は MGR / Taka）。
★『barrier を 外してよい』―― ★★外しません（★登記が 済むまで True）。
★『上級監査は 一度も 行われていない』―― ★★誤りでした。★COMPLETE 6件 すべてに 記録が 在ります。
```
