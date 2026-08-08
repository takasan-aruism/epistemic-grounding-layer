# 【BUILD SPEC】`latest_test_result_v2` — **★「最後の1件」でなく「通った回」を 拾う**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 09:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝4
- **★核1（★差し替え・★新しい名前）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限3行**

---

## 1. ★★何が 起きていたか（★実測）

```
★同じ task（`TASK-2DER-CC6DB126`）で ★2つの値が 食い違う:
     ★`GET /api/claude_packet` の `test_result` = ★★passed=True ／ sha `f7b63be9…` ／ artifact 3000字
     ★判定者に 渡っていた値                     = ★★passed=False ／ artifact_head 未提示
★★∴ ★★両者は 別の記録を 見ている。
★★★私の規則が ★『見た記録の いちばん後ろの1件を使う』と 書いていた
   ―― ★worker が 2回 生成し、★★2回目が 落ちていれば ★★通った1回目を 捨てます。
★★★★これは ★本セッションの 引き継ぎ記憶の1行目と 同じ型
   ―― ★逐語『★length だけで 成功試行が 捨てられる』。★★今回は『最後の1件だけで』でした。
```

## 2. ★★直す所（★1文だけ）

```
★旧: ★見た記録の ★いちばん後ろの1件を 使う。
★★新: ★★見た記録のうち ★passed が True の物が 在れば、★そのうち いちばん後ろの1件。
      ★無ければ ★見た記録の いちばん後ろの1件。
★★★他の欄の 取り出し方は ★1文字も 変えない。
```

## 3. ★★契約（★核・★純関数1つ・★新しい名前）

**★依頼文**
```
実行記録から、判定者に見せる試験の結果を取り出す純関数 impl.latest_test_result_v2 を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
runs = list。生成の記録が 古い順に 並んでいる。各要素は dict で "payload" を持つことがある。
       "payload" の中に "test_result"(dict) が 在ることがある。
戻り値 = {"passed": bool または None, "artifact_sha256": str または None,
          "artifact_head": str または None, "found": bool}

★見るのは、"payload" の中の "test_result" が dict である記録だけ。これを「見た記録」とする。

・runs が list でも tuple でもない → {"passed":None,"artifact_sha256":None,"artifact_head":None,"found":False}
・見た記録が 1件も 無い          → 同上（found=False）
・見た記録が 在る場合、★次の順で 1件を 選ぶ:
    ★その中で "passed" が True である記録が 在れば、★そのうち いちばん後ろの1件
    ★無ければ、★見た記録の いちばん後ろの1件
・選んだ1件から:
    "passed"          = その "passed" が bool ならその値、他は None
    "artifact_sha256" = その "artifact_sha256" が str で 中身が在ればその値、他は None
    "artifact_head"   = その "artifact" が str なら その先頭200文字、他は None
    "found"           = True
```

**★骨格**
```
<<<2DER:SKELETON>>>
def latest_test_result_v2(runs):
    # <<<FILL: この行を 実装で 置き換える(この行は 残さない)>>>
<<<2DER:END>>>
```

**★封印試験（★10本・★9本は 前の版と 同じ・★1本 足した）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

R_FAIL = {"payload": {"test_result": {"passed": False, "artifact_sha256": "aaa", "artifact": "def f():\n    pass\n"}}}
R_PASS = {"payload": {"test_result": {"passed": True,  "artifact_sha256": "bbb", "artifact": "def g():\n    pass\n"}}}
NOTEST = {"payload": {"note": "no test here"}}

def test_a_passing_run_is_chosen_even_when_a_later_run_failed():
    """★足した1本。★実物の形= worker が2回 生成し 2回目が落ちた(★通った回を 捨てない)"""
    r = impl.latest_test_result_v2([R_PASS, R_FAIL])
    assert r["passed"] is True and r["artifact_sha256"] == "bbb", r

def test_latest_passing_is_used_when_two_passed():
    r = impl.latest_test_result_v2([R_PASS, {"payload": {"test_result": {"passed": True, "artifact_sha256": "ccc"}}}])
    assert r["artifact_sha256"] == "ccc", r

def test_last_is_used_when_nothing_passed():
    r = impl.latest_test_result_v2([R_FAIL, {"payload": {"test_result": {"passed": False, "artifact_sha256": "ddd"}}}])
    assert r["artifact_sha256"] == "ddd" and r["passed"] is False, r

def test_found_is_true_when_a_test_result_exists():
    assert impl.latest_test_result_v2([R_FAIL])["found"] is True

def test_no_test_result_gives_found_false():
    r = impl.latest_test_result_v2([NOTEST])
    assert r["found"] is False and r["passed"] is None, r

def test_artifact_head_is_the_first_200_chars():
    body = "x" * 500
    r = impl.latest_test_result_v2([{"payload": {"test_result": {"artifact": body}}}])
    assert r["artifact_head"] == "x" * 200, len(r["artifact_head"] or "")

def test_records_without_a_test_result_are_skipped():
    r = impl.latest_test_result_v2([R_PASS, NOTEST])
    assert r["artifact_sha256"] == "bbb", r

def test_non_bool_passed_is_none():
    r = impl.latest_test_result_v2([{"payload": {"test_result": {"passed": "yes"}}}])
    assert r["passed"] is None and r["found"] is True, r

def test_blank_sha_is_none():
    r = impl.latest_test_result_v2([{"payload": {"test_result": {"artifact_sha256": "   "}}}])
    assert r["artifact_sha256"] is None, r

def test_non_list_gives_found_false():
    for x in (None, "runs", {}, 3):
        assert impl.latest_test_result_v2(x)["found"] is False, x
<<<2DER:END>>>
```

## 4. ★★配線（★上限3行）

```
★`senior_review.build_prompt` の 呼び先を ★`latest_test_result_v2` に 差し替える。
★★古い方は 消さない（★版の管理は Taka の「後の宿題」∴ ★名前で 分ける）。
★★★渡す欄も 判定の語の縛りも ★1文字も 変えない。
```

## 5. ★★受入（★口・欄・★id）

```
★(1) ★10本 全通（★worker が書く・★Claude は本文0行）
★(2) ★★対象は ★監視の指示どおり ★★記録側が `passed=True` の1件（★MGR が 選ぶ）
     ★口 = `GET /api/state?task_id=` ／ ★欄 = `upper_reviews[].payload.review.basis`
     ★読める物 = ★★試験の結果か sha256 か 中身に ★★『在る』方向で 触れていること
     ―― ★★『未提示』と 書かれていたら ★まだ 届いていません（★言及≠見た・★監視の指摘）
★★(3) ★★陰性 = ★★記録側が `passed=False` の task では ★今までどおり `False` が渡ること
     ―― ★★通っていない物を ★『通った』に 変えない（★★これが 混ざると 判定が 意味を失う）
★(4) ★新台帳0・新エンドポイント0 ／ ★(5) ★Claude の配線行数（★上限3行）
★(6) ★戻せる ／ ★(7) ★61本を走らせない
```

## 6. ★★私が 言っていないこと

```
★『これで 判定が PASS に なる』―― ★★判定者が 見た上で 決めます。
★『記録側と packet 側の 食い違いが 直る』―― ★★直りません（★別の1件・★名前だけ 置いてあります）。
★『CC6DB126 が 通る』―― ★★あの task は ★記録側が False ∴ ★対象に しません（★監視の指示）。
```
