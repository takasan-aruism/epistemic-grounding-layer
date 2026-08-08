# 【BUILD SPEC】`latest_test_result_v3` — **★規則を ★骨格の中へ 置く（★届く面で いちばん 使っていない所）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 14:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝4
- **★核1（★同じ関数・★新しい名前）／ ★新台帳0 ／ ★Claude の配線 ★上限3行 ／ ★assert は 1文字も 変えない**

---

## 1. ★★3標本とも 同じ1本で 落ちた 理由（★私の見立て・★源で 確かめた）

```
★落ちたのは ★★私が 足した1本 = `test_a_passing_run_is_chosen_even_when_a_later_run_failed`
★★同じ試験の中に ★こういう名前も 在ります = ★★`test_last_is_used_when_nothing_passed`
★★★名前だけを 規則として 読むと ―― ★★『last is used（最後を使う）』と 読めます。
   ★★`seen[-1]` を 書くと ★★9/10 が 通る ∴ ★worker は そこで 止まります。
★★★★これは ★`EVO-0049` で 5版6標本 続いた形と ★同じです
   ―― ★★あの時 効いたのは ★『名前に 条件を 1語 足す』でした。
★★★★★私は 逆を やっていました = ★★名前を 長くして ★肝心の語を 埋もれさせた
   （★8語 目でようやく `even_when_a_later_run_failed`）。
```

## 2. ★★今回 変える所（★2つだけ・★assert は 触らない）

```
★(1) ★★規則を ★★骨格の docstring に 置く。
     ★理由 = ★★依頼文は worker に 届かない（★規律 v1.18）。★届くのは 骨格・封印試験・共通テンプレート。
     ★★★その3つのうち ★★骨格は ★これまで ★1行も 規則を 持っていませんでした
        ―― ★★届く面で いちばん 使っていない所です。
     ★★骨格の 他の行は bytes 一致で 維持される（★共通テンプレートの 逐語）∴ ★docstring は 残ります。
★(2) ★★試験の名前を ★短くして ★規則そのものに する。
     ★`test_pick_passing_not_last` ／ `test_pick_last_passing_of_two` ／ `test_pick_last_when_none_passed`
     ★★fixture の名前も 意味の在る物に する（`PASSED_RUN` / `FAILED_RUN`）。
★★★assert の 中身は ★★1文字も 変えません（★通す条件を 緩めない）。
```

## 3. ★★契約

**★依頼文（★届かないと 分かっていますが 規律どおり 書きます）**
```
実行記録から、判定者に見せる試験の結果を取り出す純関数 impl.latest_test_result_v3 を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。
規則は 骨格の docstring に 書いてあります。そこに書いてある3通りの選び方を そのまま実装してください。
```

**★骨格（★★規則を 中に 置いた）**
```
<<<2DER:SKELETON>>>
def latest_test_result_v3(runs):
    """実行記録から、判定者に見せる試験の結果を1件選ぶ。

    runs は生成の記録が古い順に並んだ list。
    payload の中に test_result(dict) を持つ記録だけを見る。これを「見た記録」と呼ぶ。

    選び方は3通り。上から順に、最初に当てはまった1つで決める。
      1. 見た記録が1件も無い  -> 何も選ばない（found は False）
      2. 見た記録の中に passed が True の物が在る
         -> その中の いちばん後ろの1件を選ぶ（★後ろに失敗した記録が在っても、通った物を選ぶ）
      3. 上のどれでもない（1件も通っていない）
         -> 見た記録の いちばん後ろの1件を選ぶ

    選んだ1件から返す:
      passed          = その passed が bool ならその値、他は None
      artifact_sha256 = その artifact_sha256 が str で中身が在ればその値、他は None
      artifact_head   = その artifact が str ならその先頭200文字、他は None
      found           = 選べたら True、選べなければ False
    runs が list でも tuple でもない場合は、すべて None で found は False。
    """
    # <<<FILL: この行を 実装で 置き換える(この行は 残さない)>>>
<<<2DER:END>>>
```

**★封印試験（★10本・★assert は v2 と 同一・★名前だけ 変えた）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

PASSED_RUN = {"payload": {"test_result": {"passed": True,  "artifact_sha256": "bbb", "artifact": "def g():\n    pass\n"}}}
FAILED_RUN = {"payload": {"test_result": {"passed": False, "artifact_sha256": "aaa", "artifact": "def f():\n    pass\n"}}}
NO_TEST    = {"payload": {"note": "no test here"}}

def test_pick_passing_not_last():
    """通った記録の後ろに 落ちた記録が在っても、通った方を選ぶ"""
    r = impl.latest_test_result_v3([PASSED_RUN, FAILED_RUN])
    assert r["passed"] is True and r["artifact_sha256"] == "bbb", r

def test_pick_last_passing_of_two():
    r = impl.latest_test_result_v3([PASSED_RUN, {"payload": {"test_result": {"passed": True, "artifact_sha256": "ccc"}}}])
    assert r["artifact_sha256"] == "ccc", r

def test_pick_last_when_none_passed():
    r = impl.latest_test_result_v3([FAILED_RUN, {"payload": {"test_result": {"passed": False, "artifact_sha256": "ddd"}}}])
    assert r["artifact_sha256"] == "ddd" and r["passed"] is False, r

def test_found_is_true_when_a_test_result_exists():
    assert impl.latest_test_result_v3([FAILED_RUN])["found"] is True

def test_no_test_result_gives_found_false():
    r = impl.latest_test_result_v3([NO_TEST])
    assert r["found"] is False and r["passed"] is None, r

def test_artifact_head_is_the_first_200_chars():
    body = "x" * 500
    r = impl.latest_test_result_v3([{"payload": {"test_result": {"artifact": body}}}])
    assert r["artifact_head"] == "x" * 200, len(r["artifact_head"] or "")

def test_records_without_a_test_result_are_skipped():
    r = impl.latest_test_result_v3([PASSED_RUN, NO_TEST])
    assert r["artifact_sha256"] == "bbb", r

def test_non_bool_passed_is_none():
    r = impl.latest_test_result_v3([{"payload": {"test_result": {"passed": "yes"}}}])
    assert r["passed"] is None and r["found"] is True, r

def test_blank_sha_is_none():
    r = impl.latest_test_result_v3([{"payload": {"test_result": {"artifact_sha256": "   "}}}])
    assert r["artifact_sha256"] is None, r

def test_non_list_gives_found_false():
    for x in (None, "runs", {}, 3):
        assert impl.latest_test_result_v3(x)["found"] is False, x
<<<2DER:END>>>
```

## 4. ★★受入（★口・欄・★id）

```
★(1) ★10本 全通
★★(2) ★★v1.18 の確認 = ★`sent.text` に ★★`後ろに失敗した記録が在っても` が 在ること
     ―― ★★これは ★骨格の中の語 ∴ ★★届く面の語で 確かめます（★依頼文の語を 使いません）
     ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `sent.text` ／ ★id = その走行（★報告に 書く）
★(3) ★口 = 同上 ／ ★欄 = `artifact.name` と `found` ／ ★読める物 = `latest_test_result_v3` / true
★★(4) ★★3標本 走らせて ★何本 通ったかを 書く（★1走行で 版の優劣を 書かない＝本日の規律）
★(5) ★配線は ★呼び先の差し替えのみ（★上限3行）／ ★(6) ★戻せる ／ ★(7) ★61本を走らせない
```

## 5. ★★私が 言っていないこと

```
★『骨格に置けば 通る』―― ★★予告しません。★★届く面の中で ★使っていない所が 1つ 在った、までです。
★『v2 が 悪い』―― ★★assert は 同じです。★変えたのは ★★規則の 置き場所と 名前だけ。
★『名前が 原因だと 確かめた』―― ★★確かめていません（★3標本 同じ1本、という 実測が 在るだけ）。
   ★★もし v3 も 同じ1本で 落ちたら ―― ★★私の見立てが 誤りです。★その時は 私に 戻してください。
```
