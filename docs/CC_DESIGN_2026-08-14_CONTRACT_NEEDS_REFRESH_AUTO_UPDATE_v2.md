開発者規律 確認済(v1.0)

# 【契約 v2・★これを 投入する】★`needs_refresh` ―― ★★語を **3つ** に 直した（★巻き戻りを 外した）

宛: IMPL（★★投入するだけ・★1行も 書かない）／ 写: MGR ／ 発: DESIGN ／ 2026-08-14 04:1x ／ 台帳: `ITEM-2DER-EVO-0058`
差し替え元: `CC_DESIGN_2026-08-14_CONTRACT_NEEDS_REFRESH_AUTO_UPDATE.md`（★★中身は 触らない＝★新しい名前で 置く）
出所: **MGR 裁定 03:50**（★直す1点＝★列挙⑥『巻き戻り』を 外す ／ ★試験の 曖昧な `in` を 残さない）

**★★MGR の 理由（★★私より 一段 深い＝★そのまま 採る）**
> ★版の 文字列だけでは ★★前後が 分からない ＝ **★材料が 無い** ∴ **★語だけ 増やすと worker が 推測で 埋める**
> （★★存在しない 目印を 指す 指示＝[[llm-no-negation-in-instructions]] と 同じ害）

**★★私の 非（★先に 書く）**
> ★私は 列挙⑥に『巻き戻り』を 置きながら ★★試験を `in ("版が違う","巻き戻り")` に した
> ＝ ★★★どちらでも 通る ＝ **★worker には 列挙⑥が 存在しない**（★[[only-three-surfaces-reach-the-worker]]）
> ＝ ★★本日 自分で 何度も 言った 形を ★自分の 契約で やった。
> ★もう1つ ―― ★列挙⑧に『★`unknown` に 名前』と 書いたが ★★両側が 空なら ★名前は 無い ＝ ★★書き過ぎ。

---

## 1. ★★場合の 列挙（★★v2・★★7件＝★語は 3つ）

```
★① 全 repo が 同じ                     → ★`stale=False` ／ `changed=[]` ／ `reason="変化なし"`
★② 1 repo だけ 違う                    → ★`stale=True`  ／ `changed=[その名前]` ／ `reason="版が違う"`
★③ 複数 違う                           → ★`stale=True`  ／ ★★名前を 全部 昇順で（★件数だけに しない）
★★④ 記録が 空                          → ★`stale=True`  ／ ★★`reason="記録が無い"`（★『変化なし』と 混ぜない）
★★⑤ 現在の 版が 引けない repo が 在る    → ★★`unknown` に 名前 ／ ★`stale=True`
★★⑥ ★★記録の方が 新しい                → ★★★`reason="版が違う"`（★★★『巻き戻り』とは 書かない）
     ―― ★理由 = ★★前後を 決める 材料（★時刻・親子）が ★★`recorded` に 無い
     ―― ★★★戻す条件 = ★材料を 契約に 足せるように なったら ★『巻き戻り』を 戻す
★★⑦ 版は 同じ だが 未commit が 在る      → ★★`stale=False` ／ `dirty` に 名前
     ―― ★★『コードが 入った』の 鍵を ★1つに 保つ（★commit された 物だけ）
```

## 2. ★★骨格（★★これを そのまま 投入する）

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
    reason は 次の3つの語のどれか。
      変化なし / 版が違う / 記録が無い
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
```

## 3. ★★封印試験（★★1バイトも 変えない・★★曖昧な `in` を 残していない）

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


def test_recorded_newer_is_just_different():
    """記録の方が新しいときも「版が違う」と書く。前後を決める材料は渡していない。"""
    r = needs_refresh({"ds": "a2"}, {"ds": "a1"})
    assert r["stale"] is True
    assert r["reason"] == "版が違う"
    assert r["changed"] == ["ds"]


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

## 4. ★★実装役（IMPL）が やる事 ―― ★★★投入だけ

```
★★① ★★上の 骨格と 封印試験を ★front door から ★投入する（★★1行も 書かない）
★★② ★報告する物 = ★★(a)どの工程まで 行ったか ／ ★★(b)止まったなら ★工程名と ★理由（★★逐語）
     ／ ★★(c)Claude が 触った 回数（★★★0 が 最良）／ ★(d)所要 ／ ★★(e)`[Claude実装]` commit が ★3件の まま か
★★③ ★★詰まっても ★コードで 埋めない ―― ★★★契約を 直すのは ★私（DESIGN）
★★④ ★`JUDGE_REQUIRED` で 止まるのは ★意図された 終端 ＝ ★★★止まりを 失敗と 書かない
```

## 5. ★★言い方

```
★★『自動アップデートが できた』と 書かない ―― ★★正しくは ★★『★要否の 判定が 1本 通った』
★★『2DER が 書いた』と 書く 条件 = ★★★Claude が 触った 回数 0 ／ ★`[Claude実装]` commit が 増えていない
```
