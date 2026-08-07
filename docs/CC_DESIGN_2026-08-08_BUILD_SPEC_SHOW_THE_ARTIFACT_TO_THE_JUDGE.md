# 【訂正＋BUILD SPEC】`判定者に 成果物を 見せる` — **★私の源の読みが 誤りでした**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 08:2x / TYPE=訂正＋BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝4
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限6行**

---

## 1. ★★私の誤り（★先に・★逐語で）

```
★私は 03:5x に 書きました = 『★登記は 在るが ★呼ぶ枝が 無い』『★fn は 一度も 呼ばれない』
★★誤りです。★★実測（★いま 私が 引いた）:
     ★`dispatch.py:35-36` = ★"READY_FOR_UPPER_REVIEW" / "JUDGE_REQUIRED" の 末尾が ★★`False`
       ―― ★★`claude_barrier` は ★★もう False に 変わっていました（★IMPL が 入れた）。
     ∴ ★barrier を 抜け、★`result = fn(task_id, view, nlo)` に ★★到達します。
★★★私が やったこと = ★`trivially_clean` の 分岐だけを 読み、★★`_MAP` の 現在の値を 確かめなかった。
★★★★∴ ★『ソースを 読んだ』は ★★『いまの値を 読んだ』では ありません。
   ―― ★本日の規律『ソースに在る ≠ 動く』の ★★裏側（★『ソースに無い ≠ 動かない』）を ★私が 踏みました。
★★★★★MGR は ★確かめずに 承認した と 書いていますが ―― ★★源を 誤って 出したのは ★私です。
```

## 2. ★★本当の原因（★MGR の実測が 正しい）

```
★上級監査は ★★11回 走っていた（★identity=`claude-senior` × 11・★03:10:31〜03:16:12）。
★★毎回 ★中身の在る FAIL を 返している。★判定者の 逐語:
   「★成果物の存在・内容を示す記録が ★★一件も無く、完了させてよい根拠が 実行記録に無いため」
★★★私が 源で 確かめた = ★★判定者に 渡している材料は ★6つだけ（★逐語 `senior_review.build_prompt`）:
     task_id ／ state ／ last_test_passed ／ rework_count ／ completion_blockers ／ findings
   ―― ★★成果物（artifact）も ★その sha も ★試験の 詳細も ★★1つも 渡していません。
★★★★∴ ★★判定者は 正しい。★見えない物を『在る』とは 言えません。
```

## 3. ★★材料は 在る（★取りに行ける）

```
★`view` には ★`generate_runs` が 在ります（★逐語 `workcell.completion_blockers`:
   `gen_with_test = [g for g in view["generate_runs"] if (g.get("payload") or {}).get("test_result") is not None]`）
★★∴ ★その payload の `test_result` から ★`passed` / `artifact_sha256` / `artifact` が 取れます
   ―― ★★新しい口も 新しい欄も 要りません。
```

## 4. ★★契約（★核・★純関数1つ）

**★依頼文**
```
実行記録から、判定者に見せる試験の結果を取り出す純関数 impl.latest_test_result を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
runs = list。生成の記録が 古い順に 並んでいる。各要素は dict で "payload" を持つことがある。
       "payload" の中に "test_result"(dict) が 在ることがある。
戻り値 = {"passed": bool または None, "artifact_sha256": str または None,
          "artifact_head": str または None, "found": bool}

★見るのは、"payload" の中の "test_result" が dict である記録だけ。これを「見た記録」とする。

・runs が list でも tuple でもない → {"passed":None,"artifact_sha256":None,"artifact_head":None,"found":False}
・見た記録が 1件も無い          → 同上（found=False）
・見た記録が 在る場合、★いちばん後ろの1件を使う:
    "passed"          = その test_result の "passed" が bool ならその値、他は None
    "artifact_sha256" = その test_result の "artifact_sha256" が str で 中身が在ればその値、他は None
    "artifact_head"   = その test_result の "artifact" が str なら その先頭200文字、他は None
    "found"           = True
```

**★骨格**
```
<<<2DER:SKELETON>>>
def latest_test_result(runs):
    # <<<FILL: この行を 実装で 置き換える(この行は 残さない)>>>
<<<2DER:END>>>
```

**★封印試験（★9本）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

R1 = {"payload": {"test_result": {"passed": False, "artifact_sha256": "aaa", "artifact": "def f():\n    pass\n"}}}
R2 = {"payload": {"test_result": {"passed": True,  "artifact_sha256": "bbb", "artifact": "def g():\n    pass\n"}}}
NOTEST = {"payload": {"note": "no test here"}}

def test_latest_of_two_is_used():
    r = impl.latest_test_result([R1, R2])
    assert r["passed"] is True and r["artifact_sha256"] == "bbb", r

def test_found_is_true_when_a_test_result_exists():
    assert impl.latest_test_result([R1])["found"] is True

def test_no_test_result_gives_found_false():
    r = impl.latest_test_result([NOTEST])
    assert r["found"] is False and r["passed"] is None, r

def test_artifact_head_is_the_first_200_chars():
    body = "x" * 500
    r = impl.latest_test_result([{"payload": {"test_result": {"artifact": body}}}])
    assert r["artifact_head"] == "x" * 200, len(r["artifact_head"] or "")

def test_records_without_a_test_result_are_skipped():
    r = impl.latest_test_result([R2, NOTEST])
    assert r["artifact_sha256"] == "bbb", r

def test_non_bool_passed_is_none():
    r = impl.latest_test_result([{"payload": {"test_result": {"passed": "yes"}}}])
    assert r["passed"] is None and r["found"] is True, r

def test_blank_sha_is_none():
    r = impl.latest_test_result([{"payload": {"test_result": {"artifact_sha256": "   "}}}])
    assert r["artifact_sha256"] is None, r

def test_empty_list_gives_found_false():
    assert impl.latest_test_result([])["found"] is False

def test_non_list_gives_found_false():
    for x in (None, "runs", {}, 3):
        assert impl.latest_test_result(x)["found"] is False, x
<<<2DER:END>>>
```

## 5. ★★配線（★上限6行）

```
★`senior_review.build_prompt` に ★3行 足す ―― ★`latest_test_result(view.get("generate_runs"))` の
  ★`passed` / ★`artifact_sha256` / ★`artifact_head` を ★そのまま 並べる。
★★既存の6つは ★1つも 消さない（★追加のみ）。
★★★判定の 語の縛り（`PASS`/`FAIL` を 1行目）は ★1文字も 変えない。
```

## 6. ★★受入（★口・欄・★id）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/state?task_id=` ／ ★欄 = `upper_reviews[].payload.review.basis`
     ★id = ★`TASK-2DER-CC6DB126`（★11回 走った当の task・★報告に 書く）
     ★読める物 = ★★次の判定の 根拠が ★★『記録が 無い』★以外 に なること（★MGR の受入）
★★(3) ★★『1つの task に 何回 呼んだか』= `upper_reviews` の件数 を 併記すること
     ―― ★★上限は 置かない（★MGR 裁定(2)）。★但し ★数は 出す。
★(4) ★★陰性 = ★★試験の記録が 無い task では ★`found=False` が 渡り、
     ★判定者が ★『記録が 無い』と 言えること ―― ★★空を『在る』に 変えない。
★(5) ★新台帳0・新エンドポイント0 ／ ★(6) ★Claude の配線行数（★上限6行）
★(7) ★戻せる ／ ★(8) ★61本を走らせない
```

## 7. ★★私が 言っていないこと

```
★『これで PASS に なる』―― ★★なりません。★判定者が ★見た上で 決めます。
★『11回は 無駄だった』―― ★★材料が 空である事を ★11回 言い当てています。
★『上限を 置く』―― ★★置きません（★MGR 裁定(2)・★原因を 隠すため）。
★『v3 を 先に』―― ★★順序は 変えません（★本件 → v3）。
```
