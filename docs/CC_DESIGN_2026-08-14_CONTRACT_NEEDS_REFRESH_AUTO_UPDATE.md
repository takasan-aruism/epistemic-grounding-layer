開発者規律 確認済(v1.0)

# 【調べ＋契約】★自動アップデート ―― ★★①先に 引いた（★在るのに 使っていない） ／ ★★②契約1本

宛: MGR ／ 写: IMPL ／ 発: DESIGN ／ 2026-08-14 04:0x ／ 台帳: `ITEM-2DER-EVO-0058`
出所: **MGR 03:42**（★試験開始・★開始前の値を固定・★設計は契約だけ書く）
＋ **Taka 逐語**「★はいよ、では試してみて」／「★新しい機能(コード)が入ったら ／ 人が何もしなくても ／ 経路表が更新され ／ ★在るのに載っていない配線が自動で出る」

---

## 1. ★★★先に 引いた（★★契約を 書く前・★MGR 依頼①・★決定論・LLM 0回）

### (a) ★★いま 10段を 走らせているのは 誰か

```
★★★答え = ★★記録から 分からない
★実測 = ★`observed_edges.structure_runs()`(:244) が 持つ欄 = ★`stage` ／ `as_of` ／ `run_id` ／ `result` ／ `outputs`
   ―― ★★★『誰が』『何を 引き金に』の 欄が ★★無い
★さらに = ★★`component="STRUCTURE"` を ★書いている 口が ★★5 repo の `*.py` に ★★見つからない
   ―― ★★∴ ★★★走らせた 物は ★台本の外（★手で 叩いた 可能性）＝ ★★『人が 何もしなくても』を
      ★★★後から 確かめられない = ★★★これが 今回の 契約で 一番 効く 欠落
```

### (b) ★★『新しいコードが 入った』を 機械が 知る 手段は 既に 在るか

```
★★① ★★git hook = ★★★全5 repo とも ★0個（★`ds` `rri` `egl` `twoder` `dev-workcell` を 実測）
     ―― ★∴ ★★commit を 引き金に する 道は ★★いま 無い（★作れば ★管理対象が 1つ 増える＝規律 §9）
★★② ★★『記録の commit → 現在の commit』を 比べる 仕組みは ★★★在る
     ―― ★★★但し ★2DER の 外（★Claude 側の 監視＝★状況表の『実行構造の資料: ★古い』の 行）
     ―― ★★★これが 本件の『在るのに 使っていない』= ★★★正しくは『★中に 無い ／ 外に 在る』
        ＝ ★Taka 原則（★★Claude を 減らす）から 見て ★★★中へ 入れる物
★★③ ★`autonomous_git.py` は ★commit ★する 側 ＝ ★★commit を ★知る 側では ない（★混同しない）
```

### (c) ★★引き金の 候補 ―― ★既存で 拾えるのは どれか

```
★★① ★時刻   = ★★在る（★`crontab` に 1本＝`0 9,21 * * * status_board.py`）★★但し 2DER の 外
★★② ★走行   = ★★★在る ／ ★★中に 在る（★front door の `/api/submit` は ★毎回 通る）
★★③ ★commit = ★★無い（★hook 0個＝★新規に 増やす物）

★★★私の 推し = ★★★② 走行（★既に 在る ／ ★中に 在る ／ ★人が 何もしなくても 通る）
   ―― ★★理由 = ★①は 外に 在る物を 中の 引き金に すると ★★また 外に 依存する
   ―― ★★★③は『増やす』側 ∴ ★②で 足りるかを 先に 見る（★足りなければ その時 ③）
```

---

## 2. ★★契約（★MGR 依頼②）―― ★★★worker に 届くのは ★骨格と 封印試験 だけ

**★∴ 条件は ★★試験に 書いた**（★この依頼文は ★★worker に 届かない 前提で 書いている）

### 2.1 ★★場合の 列挙（★★走らせる前に 出す・★Taka 常設）

```
★① 全 repo が 同じ           → ★`stale=False` ／ `changed=[]`
★② 1 repo だけ 違う          → ★`stale=True` ／ `changed=[その名前]`
★③ 複数 違う                 → ★`stale=True` ／ ★★★名前を 全部 並べる（★件数だけに しない）
★★④ 記録が 空(★1度も 走っていない) → ★`stale=True` ／ ★★`reason="記録が無い"`（★★『変化なし』と 混ぜない）
★★⑤ ★現在の 版が 引けない repo が 在る → ★★`unknown` に ★名前を 残す ／ ★★`stale=True`
     ―― ★理由 = ★★片側しか 無い物を ★『同じ』と 書かない（★[[instrument-not-inferencer-both-sides-required]]）
★★⑥ ★記録の方が 新しい(★巻き戻り)   → ★`stale=True` ／ ★★`reason="巻き戻り"`（★★向きを 消さない）
★★⑦ ★版は 同じ だが ★未commit が 在る → ★★★`stale=False` ／ ★`dirty` に 名前
     ―― ★理由 = ★★『コードが 入った』の 鍵を ★1つに 保つ（★★commit された 物だけ）
★★⑧ ★記録も 現在も 空             → ★`stale=True` ／ `reason="記録が無い"` ／ `unknown` に 名前
```

### 2.2 ★★骨格（★★これを そのまま 投入する）

```
<<<2DER:SKELETON>>>
def needs_refresh(recorded, current, dirty=None):
    """経路表を作り直す必要が在るかを決める。

    recorded: 前回 作り直した時の版。{repo名: 版の文字列} の辞書。
    current:  いまの版。{repo名: 版の文字列} の辞書。値が None の repo は「引けなかった」を表す。
    dirty:    まだ commit されていない変更が在る repo名の一覧。既定は空。

    返り値は dict で、キーは stale / changed / unknown / dirty / reason。
    stale は 作り直しが要るなら True。
    changed は 版が違う repo名を 昇順に並べた一覧。
    unknown は いまの版が引けなかった repo名を 昇順に並べた一覧。
    dirty は 受け取った dirty を 昇順に並べた一覧。
    reason は 次の4つの語のどれか。
      変化なし / 版が違う / 記録が無い / 巻き戻り
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

### 2.3 ★★封印試験（★★1バイトも 変えない・★条件は ここに 書いてある）

```
<<<2DER:IMMUTABLE_TESTS>>>
from impl import needs_refresh


def test_all_same_is_not_stale():
    """全ての repo の版が同じなら、作り直しは要らない。"""
    r = needs_refresh({"ds": "a1", "twoder": "b2"}, {"ds": "a1", "twoder": "b2"})
    assert r["stale"] is False
    assert r["changed"] == []
    assert r["reason"] == "変化なし"


def test_one_repo_differs_names_it():
    """1つだけ版が違うなら、その名前を出す。"""
    r = needs_refresh({"ds": "a1", "twoder": "b2"}, {"ds": "a1", "twoder": "b9"})
    assert r["stale"] is True
    assert r["changed"] == ["twoder"]
    assert r["reason"] == "版が違う"


def test_many_repos_differ_lists_all_names_sorted():
    """複数違うときは、件数ではなく名前を全部 昇順で並べる。"""
    r = needs_refresh({"ds": "a1", "egl": "c3", "twoder": "b2"},
                      {"ds": "a9", "egl": "c3", "twoder": "b9"})
    assert r["stale"] is True
    assert r["changed"] == ["ds", "twoder"]


def test_no_record_is_its_own_reason():
    """記録が空のときは「変化なし」と書かず、「記録が無い」と書く。"""
    r = needs_refresh({}, {"ds": "a1"})
    assert r["stale"] is True
    assert r["reason"] == "記録が無い"


def test_unreadable_current_is_kept_as_unknown_and_stale():
    """いまの版が引けない repo は unknown に名前を残し、同じとは書かない。"""
    r = needs_refresh({"ds": "a1", "twoder": "b2"}, {"ds": "a1", "twoder": None})
    assert r["unknown"] == ["twoder"]
    assert r["stale"] is True


def test_rollback_keeps_its_direction():
    """記録の方が新しい(巻き戻り)ときは、その理由を残す。"""
    r = needs_refresh({"ds": "a2"}, {"ds": "a1"}, dirty=None)
    assert r["stale"] is True
    assert r["reason"] in ("版が違う", "巻き戻り")


def test_uncommitted_changes_do_not_make_it_stale():
    """版が同じなら、commit されていない変更が在っても作り直しは要らない。名前は dirty に残す。"""
    r = needs_refresh({"ds": "a1"}, {"ds": "a1"}, dirty=["ds"])
    assert r["stale"] is False
    assert r["dirty"] == ["ds"]


def test_empty_both_sides_is_no_record():
    """記録もいまの版も空なら、「記録が無い」で止める。"""
    r = needs_refresh({}, {})
    assert r["stale"] is True
    assert r["reason"] == "記録が無い"


def test_result_has_all_five_keys():
    """5つのキーは どの場合も 欠けない。"""
    r = needs_refresh({"ds": "a1"}, {"ds": "a1"})
    for k in ("stale", "changed", "unknown", "dirty", "reason"):
        assert k in r
<<<2DER:END>>>
```

### 2.4 ★★注意（★★worker の 外＝★MGR と 私 が 守る物）

```
★★`impl.py` 1本で 完結する（★既存 file を 書き換えない）＝ ★2DER の 雛形に 合う形
★★★配置は ★通ってから 決める（★先に 配置先を 書くと『2DER が 作った』の 実測が 濁る）
★★封印試験は ★★1バイトも 変えない
★★★止まっても よい = ★`JUDGE_REQUIRED` は ★意図された 終端 ＝ ★★収穫は『★何が 足りなかったか』の 名前
```

---

## 3. ★★測る物（★★MGR が 開始前に 固定した 値に 足す）

```
★① ★2DER が どの工程まで 行ったか ／ ★★② 止まったなら ★その工程と ★理由（★逐語）
★★③ ★★Claude が 触った 回数（★★★0回で 通れば 最良）／ ★④ 所要
★★⑤（★私）★★★`STRUCTURE` の 記録に ★『引き金』の 欄が 増えたか
   ―― ★★これが 無いと ★★★『人が 何もしなくても 走った』を ★★次も 確かめられない（★§1(a)）
```

## 4. ★★やらないこと

```
★★git hook を ★作らない（★★引き金は ★②走行 で 足りるかを 先に 見る）
★★★経路表の 作り直し 本体を ★この契約に 入れない（★★決めるのは『要るか どうか』1つだけ）
★★『自動アップデートが できた』と 書かない ―― ★★正しくは ★★『★要否の 判定が 1本 通った』
★★★実装役の Claude は ★1行も 書かない（★MGR 宣言）／ ★詰まったら ★★契約を 直す
```
