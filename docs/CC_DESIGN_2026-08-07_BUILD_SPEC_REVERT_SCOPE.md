# 【BUILD SPEC】`戻せる（先）` — **★欄は既存・★但し `task_id` の欄は ★在りません**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-07 23:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝Taka「戻すのが先」
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新しい欄0 ／ ★Claude の配線 ★上限8行**

---

## 1. ★★実装可能性を 先に 出す（★feasibility-first）

```
★MGR の (3)「`task_id ↔ change_id` を1本 結ぶ」／ ★受入「task_id を1つ与えると 出る」について:

★★実測（★逐語 `twoder/artifact_registry.py:136-142`）= ★`record_change` が 書く欄は 次のとおり:
     change_id / ★trace_id / ★de_id / affected_artifact_ids / tests_run / live_trace /
     authority_status / gpu_or_8005_touched / before_commit / after_commit / recorded_at
★★★∴ ★★`task_id` の欄は ★★在りません。

★★★★∴ ★『欄は既存・新しい欄0』を 守るなら、★★鍵は `trace_id` か `de_id` に なります。
   ★`task_id` → `trace_id` は ★★別の口が 持っています（★`GET /api/etrace?task_id=` ／ ★本日 私が 使いました）
   ∴ ★★2段で 引けば 成立します（★欄を 足さずに 済む）。
★★★★★これを 先に 出すのは ―― ★★後で「出せません」と言わないためです。
   ★★『新しい欄を1つ足す』を 選ぶなら ★それは MGR の裁定であり、★本 SPEC の外です。
```

## 2. ★★契約（★核・★純関数1つ）

**★依頼文**
```
変更の記録から、戻すための範囲を組み立てる純関数 impl.revert_scope を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
changes = 変更の記録の一覧（古い順）。各要素は dict で、次の欄を持つことがある:
          "change_id"(str) / "trace_id"(str) / "before_commit"(str) / "after_commit"(str)
          / "affected_artifact_ids"(list)
key     = str。trace_id と突き合わせる値。
戻り値 = {"change_ids": list, "before_commit": str または None,
          "after_commit": str または None, "artifact_ids": list, "complete": bool}

★対象にするのは、"trace_id" が key と 文字ごとに等しい記録だけ。

・changes が list でも tuple でもない → {"change_ids": [], "before_commit": None,
  "after_commit": None, "artifact_ids": [], "complete": False}
・"change_ids" = 対象の "change_id" のうち str である物を、出てきた順に並べる。
・"before_commit" = 対象のうち "before_commit" が str である ★最初の物。無ければ None。
・"after_commit"  = 対象のうち "after_commit"  が str である ★最後の物。無ければ None。
・"artifact_ids" = 対象の "affected_artifact_ids" に入っている str を集め、
                   重複を除き、名前順に並べる。
・"complete" = before_commit と after_commit が どちらも str であり、
               かつ artifact_ids が 1件以上ある時だけ True。それ以外は False。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def revert_scope(changes, key):
    # <<<FILL: この行を 実装で 置き換える（★この行は 残さない）>>>
<<<2DER:END>>>
```

**★封印試験（★9本）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

C1 = {"change_id": "CHG-1", "trace_id": "TRACE-a", "before_commit": "aaa",
      "after_commit": "bbb", "affected_artifact_ids": ["ART-2", "ART-1"]}
C2 = {"change_id": "CHG-2", "trace_id": "TRACE-a", "before_commit": "bbb",
      "after_commit": "ccc", "affected_artifact_ids": ["ART-1"]}
OTHER = {"change_id": "CHG-9", "trace_id": "TRACE-z", "before_commit": "zzz",
         "after_commit": "yyy", "affected_artifact_ids": ["ART-9"]}

def test_one_change_gives_its_range():
    r = impl.revert_scope([C1], "TRACE-a")
    assert r["before_commit"] == "aaa" and r["after_commit"] == "bbb", r

def test_two_changes_span_from_first_before_to_last_after():
    """★戻す範囲は 最初の before から 最後の after まで"""
    r = impl.revert_scope([C1, C2], "TRACE-a")
    assert (r["before_commit"], r["after_commit"]) == ("aaa", "ccc"), r

def test_artifact_ids_are_merged_deduped_and_sorted():
    r = impl.revert_scope([C1, C2], "TRACE-a")
    assert r["artifact_ids"] == ["ART-1", "ART-2"], r

def test_other_key_is_not_included():
    r = impl.revert_scope([C1, OTHER], "TRACE-a")
    assert r["change_ids"] == ["CHG-1"], r

def test_complete_is_true_when_both_ends_and_a_file_exist():
    assert impl.revert_scope([C1], "TRACE-a")["complete"] is True

def test_complete_is_false_when_after_is_missing():
    """★片端が欠けた記録は 戻す範囲にならない（★現状 24/196 しか両端が無い）"""
    c = dict(C1); c["after_commit"] = None
    assert impl.revert_scope([c], "TRACE-a")["complete"] is False

def test_complete_is_false_when_no_artifact_is_named():
    """★何を変えたかが空なら 戻せない（★現状 直近3件は 0〜1件）"""
    c = dict(C1); c["affected_artifact_ids"] = []
    assert impl.revert_scope([c], "TRACE-a")["complete"] is False

def test_unknown_key_gives_empty_and_incomplete():
    r = impl.revert_scope([C1, C2], "TRACE-nothing")
    assert r["change_ids"] == [] and r["complete"] is False, r

def test_non_list_gives_empty_and_incomplete():
    for x in (None, "TRACE-a", {}, 3):
        r = impl.revert_scope(x, "TRACE-a")
        assert r["complete"] is False and r["change_ids"] == [], x
<<<2DER:END>>>
```

## 3. ★★配線（★上限8行）

```
★(1) ★成果物を 置く経路から ★`record_change` を 呼ぶ（★呼ぶのをやめた所を 呼び直すだけ）。
★(2) ★`before_commit` を 必ず 埋める（★現状 24/196）。`after_commit` は commit 後に
     ★`update_change_after_commit` で 閉じる。
★(3) ★`affected_artifact_ids` に ★置いた物の id を 入れる（★現状 直近3件は 0〜1件）。
★★★(4) ★★遡って 過去の記録を 埋めない（★実物と違う形を 作らない・★本日の (A) と 同じ作法）。
```

## 4. ★★受入（★口・欄・★id を 載せる物として）

```
★(1) ★9本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = `GET /api/resolve?id=TASK-…` ／ ★欄 = `artifact.name` と `found`
     ★id = ★この契約を走らせた その走行（★報告に 書く）／ ★読める物 = `revert_scope` ／ `found=true`
★(3) ★★これ以後に 置いた成果物 1本について、★`complete` が ★True に なること
     ★id = ★その成果物を 置いた走行（★報告に 書く）
★★(4) ★★陰性 = ★★過去の記録（★2026-07-22 以前）の `complete` が ★False の まま であること
     ―― ★埋めていないのだから False で 正しい。★ここが True に なったら ★遡って 書いている。
★(5) ★Claude の配線行数 ／ ★(6) ★戻せる ／ ★(7) ★61本を走らせない ／ ★(8) ★commit しない
```

## 5. ★★私が 言っていないこと

```
★『task_id で 引ける』―― ★★引けません（★§1）。★引けるのは `trace_id`。★2段で 繋ぐ話です。
★『過去の196件が 戻せるようになる』―― ★★なりません。★これから置く物だけです。
★『版の管理』―― ★★本件では やりません（★Taka「明細管理と一緒・後の宿題」）。
★『目印の残った3本を 直す』―― ★★単独で 直しに行きません（★Taka「全件直す、的な動きは不要」）。
   ★但し ★本 SPEC の骨格では ★★『この行は 残さない』と 書きました（★次からは 残りません）。
```
