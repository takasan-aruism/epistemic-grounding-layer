# 【BUILD SPEC】`(B)` — **★根拠が在る時だけ ★やり直しを 1回 許す**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 22:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝Taka 裁定 (B)
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新しい state 0 ／ ★Claude の配線 ★上限6行**

---

## 1. ★★いまの形（★源・逐語 `dev-workcell/dw/workcell.py:196-204`）

```
v = ("%s" % ((pl.get("review") or {}).get("verdict") or "")).upper()
if   v == "PASS" and bool(view.get("last_test_passed")):  state = "READY_FOR_UPPER_REVIEW"
elif v == "FAIL" and _entry != "JUDGE_REQUIRED":          state = "READY_FOR_REGENERATE"
elif v == "FAIL":                                         state = "JUDGE_REQUIRED"   ← ★ここ
else:                                                     state = "JUDGE_REQUIRED"
```

**★変えるのは ★3番目の枝だけ。**（★1・2・4 は 1文字も触らない）

## 2. ★★なぜ 変えてよいか（★MGR の理由を そのまま 使う）

```
★やり直しの上限は ★『同じ情報で 繰り返しても 同じ物が出る』ために 在る。
★★上級監査の根拠は ★★前のやり直しの時に ★存在しなかった 新しい情報である
∴ ★★上限の理由が ★この場合には 当たらない。
★★★『1回だけ』の理由 = ★上級監査が 2回 同じことを言うなら ★それは 新しい情報ではない
∴ ★そこで 本当に 止める。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
上級監査の記録から、やり直しを1回 許してよいかを返す純関数 impl.may_retry_after_senior_fail を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
reviews = その走行に記録された上級監査の一覧（古い順）。各要素は dict で
          "verdict"（str）と "basis"（str）を持つことがある。
戻り値 = True または False。

★数えるのは1種類だけ ―― 「verdict を英大文字にすると "FAIL" であり、かつ
   basis が 中身のある str（空白だけでない）である」記録の個数。これを n とする。

読み方は4通り。上から順に、最初に当てはまった1つで決める。

(1) reviews が list でも tuple でもない → False
(2) n が 1 → True
(3) n が 0 → False
(4) n が 2 以上 → False
```

**★骨格**
```
<<<2DER:SKELETON>>>
def may_retry_after_senior_fail(reviews):
    # <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

**★封印試験（★9本・★fixture は 本日の実データの形）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

# ★実データの形(2026-08-07・上級監査の記録・根拠の長さは平均101字/最短0字)
WITH  = {"verdict": "FAIL", "basis": "成果物に思考の途中が残っている。実装だけを出すこと"}
EMPTY = {"verdict": "FAIL", "basis": ""}
PASS  = {"verdict": "PASS", "basis": "封印試験で8本中8本が通過している"}

def test_one_fail_with_basis_allows_one_retry():
    """★根拠が在る FAIL が1件 → 1回だけ許す"""
    assert impl.may_retry_after_senior_fail([WITH]) is True

def test_two_fails_with_basis_do_not_allow_retry():
    """★2回 同じことを言うなら 新しい情報ではない → 止める"""
    assert impl.may_retry_after_senior_fail([WITH, WITH]) is False

def test_fail_without_basis_does_not_allow_retry():
    """★根拠が空なら 今までどおり 留まる"""
    assert impl.may_retry_after_senior_fail([EMPTY]) is False

def test_whitespace_basis_counts_as_empty():
    assert impl.may_retry_after_senior_fail([{"verdict": "FAIL", "basis": "   "}]) is False

def test_pass_is_not_counted():
    assert impl.may_retry_after_senior_fail([PASS]) is False

def test_empty_fail_next_to_one_with_basis_still_allows_one():
    """★空の FAIL は 数に入らない（★本日 実在した形）"""
    assert impl.may_retry_after_senior_fail([EMPTY, WITH]) is True

def test_lowercase_verdict_is_counted():
    assert impl.may_retry_after_senior_fail([{"verdict": "fail", "basis": "x"}]) is True

def test_non_string_basis_is_not_counted():
    assert impl.may_retry_after_senior_fail([{"verdict": "FAIL", "basis": 1}]) is False

def test_non_list_is_false():
    for x in (None, "FAIL", {}, 3):
        assert impl.may_retry_after_senior_fail(x) is False, x
<<<2DER:END>>>
```

## 4. ★★配線（★上限6行）

```
★`workcell.py` の ★3番目の枝だけを 次の形にする:
     elif v == "FAIL":
         state = "READY_FOR_REGENERATE" if ★may_retry_after_senior_fail(view の upper_reviews) \
                 else "JUDGE_REQUIRED"
★★渡す物 = ★その走行に 記録された 上級監査の一覧（★古い順・★既に view に在る `upper_reviews`）。
★★★新しい state を 作らない。★1・2・4 の枝を 触らない。
★★★★上限を 超えると見えたら ★★そう返してください（★本日 IMPL が 8→18 で そうし、★MGR が 受けた）。
```

## 5. ★★受入（★口・欄・★id を 載せる物として）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★id = ★この契約を走らせた その走行（★報告に 書く）
★(3) ★口 = `GET /api/state?task_id=…` ／ ★欄 = `dw_state`
     ★id = ★★根拠が在る FAIL を1件 持つ走行（★報告に 書く）
     ★読める物 = ★★`READY_FOR_REGENERATE`（★`JUDGE_REQUIRED` から 動いた）
★★(4) ★★陰性（★これが無いと 全部 開いてしまう）=
     ★id = ★★根拠が空の FAIL を持つ走行（★本日 実在: `TASK-2DER-45DF63FE`）
     ★読める物 = ★★`JUDGE_REQUIRED` の まま（★動かない）
★(5) ★★根拠が やり直しの入力に 逐語で 入ること
     ★測り方 = ★★`handoff_len` − `sent.length`（★本日 35字で 実証した形）
★(6) ★Claude の配線行数 ／ ★(7) ★戻せる ／ ★(8) ★61本を走らせない ／ ★(9) ★commit しない
```

## 6. ★★私が 言っていないこと

```
★『これで 64件が 動く』―― ★★予告しません。★根拠が在る物だけが 動きます。
★『2回目も 許してよい』―― ★★許しません（★MGR の理由のとおり）。
★『(A) の3件の 出どころが 分かる』―― ★★(B) の後に ★ts で 引き直して 初めて 分かります。
★『上限を 当てた』―― ★★上限は 当てる物では ありません（★v1.16）。
```
