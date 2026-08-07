# 【裁定＋BUILD SPEC】`commit を 2DER 側へ` — **★禁止は 一箇所だけ 在る（★全体では 空いている）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 監視 / 発: 設計/監査(CC-α) / 2026-08-08 01:0x / TYPE=裁定＋BUILD_SPEC
- **開発者規律 確認済（版: ★v1.18）** ／ 台帳: `ITEM-2DER-EVO-0035` ／ 効く先＝Taka 裁定 (a)
- **★核1（★純関数1つ）／ ★新台帳0 ／ ★新エンドポイント0 ／ ★Claude の配線 ★上限10行**

---

## 1. ★★先に 出す（★MGR の §2 を 1段 深くした）

```
★MGR は ★`build_planner` の禁止語（★モデルが書く PLAN 向け）を 確かめ、★『別の話』と 結論しました。★正しい。
★★但し ★もう1つ 在ります = ★★`twoder/bridge_reconciler.py:35-44`（逐語）:
     _READ_ONLY_GIT = frozenset({'rev-parse','status','ls-files','cat-file','rev-list','log','ls-tree'})
     def _git_read(...): """Sole subprocess entry point. Refuses any non-read-only git subcommand (fail-closed)."""
★★∴ ★『2DER は git に 書かない』は ★★設計意図として 明文で 在ります。

★★★★但し ★★守られているのは ★その1モジュールだけ です（★実測）:
     ★`twoder/artifact_registry.py:47` `_git(repo_abs, *args)` = ★★whitelist 無し（★何でも通る）
     ★`twoder/management_packet.py:18`                        = ★★whitelist 無し
★★★★★∴ ★★技術的には ★もう 書けます。★★『空いている』のであって『守られている』のでは ありません。
★★★★★★∴ ★本件は ★★穴を 黙って 使うのではなく、★★書いてよい口を 1つ 決めて 通す 形にします。
```

## 2. ★★決めてほしかった3点（★私の裁定）

```
★(a) ★層 = ★★`artifact_registry` の 中。
     ★理由 = (i) ★`before_commit`/`after_commit` を 持つ 当の場所 (ii) ★`_git` が 既に 在る（★依存を増やさない）
     ★★但し ★読み取りと 同じ関数で 通さない = ★★書く口を 1つ 分けて 置く（★`bridge_reconciler` の作法に倣う）
     ★★★残る限界（★書きます）= ★成果物を 置いているのは ★★Claude(IMPL) ∴ ★★呼ぶのは Claude のまま。
        ★『2DER が 置いて 2DER が commit する』には ★★置く行為を 先に 中へ入れる 必要が 在ります（★本件の外）。

★(b) ★メッセージ = ★★run_id ＋ 置いた物の名前 ＋ ★★`change_id` の3つ。
     ★★`change_id` を 足す理由 = ★戻す時に 引く鍵が `change_id` である ∴ ★git log から 台帳へ ★戻れる
       （★★逆引きが 1本 つながる）。★2つでは 戻れません。

★(c) ★失敗した時 = ★★MGR の見立てに 同意。★置いた物を 消さない・★`after_commit` を 空のまま。
     ★理由 = ★`complete=false` が 出る ∴ ★★『commit されていない』が 機械で 読める（★黙って失敗しない）。

★★★(d) ★★私から 1つ 足す（★安全）= ★★`git commit -a` を 使わない。
     ★理由（★実測）= ★本日 状況表は ★何度も『repo 未commit : ds:1 rri:1 egl:3 …』を出しました
     ∴ ★★他人の 未コミットの変更が 常に 在ります。★`-a` は ★それを 巻き込みます。
     ★★∴ ★★置いた その1本だけを add して commit する。
```

## 3. ★★契約（★核・★純関数1つ）

**★依頼文**
```
commit のメッセージを組み立てる純関数 impl.commit_message を作ってください。
本番モジュールを import せず、データは引数で受け取る純関数にしてください。標準ライブラリのみ。

■ 規則（これだけ。創作しない）
run_id    = str（例 "ETR-fbc0f7a8acc4"）
change_id = str（例 "CHG-0129"）
names     = 置いた物の名前の list（str のみを使う）
戻り値 = str。

★形は 次の1行に 固定する:
    "<names をカンマと空白で つないだ物> [run=<run_id>] [change=<change_id>]"

・run_id が str でない、または 中身が 空白だけ → ""
・change_id が str でない、または 中身が 空白だけ → ""
・names が list でも tuple でもない → ""
・names の中の str で 中身が 空白だけでない物を、出てきた順に 使う。1つも無ければ → ""
・名前の前後の空白は 取り除く。
```

**★骨格**
```
<<<2DER:SKELETON>>>
def commit_message(run_id, change_id, names):
    # <<<FILL: この行を 実装で 置き換える（★この行は 残さない）>>>
<<<2DER:END>>>
```

**★封印試験（★8本・★fixture は 本日の実物）**
```
<<<2DER:IMMUTABLE_TESTS>>>
import impl

RUN = "ETR-fbc0f7a8acc4"      # ★本日 通した1本(CHG-0129)の実物
CHG = "CHG-0129"

def test_one_name_gives_the_fixed_shape():
    got = impl.commit_message(RUN, CHG, ["revert_scope.py"])
    assert got == "revert_scope.py [run=ETR-fbc0f7a8acc4] [change=CHG-0129]", got

def test_two_names_are_joined_by_comma_and_space():
    got = impl.commit_message(RUN, CHG, ["a.py", "b.py"])
    assert got == "a.py, b.py [run=ETR-fbc0f7a8acc4] [change=CHG-0129]", got

def test_change_id_is_present_so_the_ledger_can_be_found_from_git():
    """★戻す時に 引く鍵が 入っていること"""
    assert "CHG-0129" in impl.commit_message(RUN, CHG, ["a.py"])

def test_surrounding_space_in_a_name_is_removed():
    assert impl.commit_message(RUN, CHG, ["  a.py  "]) == "a.py [run=ETR-fbc0f7a8acc4] [change=CHG-0129]"

def test_empty_names_gives_empty_string():
    """★名前が無いなら 空を返す（★呼び手が 止められる）"""
    assert impl.commit_message(RUN, CHG, []) == ""
    assert impl.commit_message(RUN, CHG, ["  "]) == ""

def test_missing_change_id_gives_empty_string():
    assert impl.commit_message(RUN, "", ["a.py"]) == ""
    assert impl.commit_message(RUN, None, ["a.py"]) == ""

def test_missing_run_id_gives_empty_string():
    assert impl.commit_message("", CHG, ["a.py"]) == ""

def test_non_list_names_gives_empty_string():
    for x in (None, "a.py", {}, 3):
        assert impl.commit_message(RUN, CHG, x) == "", x
<<<2DER:END>>>
```

## 4. ★★配線（★上限10行）

```
★(1) ★`artifact_registry` に ★★書く口を 1つ 置く（★読み取りの `_git` と 分ける）。
★(2) ★置いた その1本だけを `add` → ★`commit -m <commit_message(...)>`。★★`-a` を 使わない（★§2(d)）。
★(3) ★戻ってきた hash を ★`update_change_after_commit(change_id, after_commit=hash)` で 書く。
★(4) ★`commit_message` が ★空を返したら ★★commit しない（★fail-closed）。
★★★(5) ★★`bridge_reconciler` の `_READ_ONLY_GIT` を ★1文字も 触らない（★あの口は 読み取り専用の まま）。
```

## 5. ★★受入（★口・欄・★id）

```
★(1) ★8本 全通（★worker が書く・★Claude は本文0行）
★(2) ★口 = 変更の記録 ／ ★欄 = `after_commit` ／ ★id = ★次に置く成果物の `change_id`（★報告に 書く）
     ★読める物 = ★commit hash（★null ではない）
★(3) ★口 = `revert_scope` ／ ★欄 = `complete` ／ ★id = その走行の `run_id`
     ★読める物 = ★★`true`（★いまは false）
★★(4) ★★MGR が `git` を 1度も 叩かないこと（★本件の目的）
★★(5) ★★陰性 = ★★その commit に ★★置いた1本以外の file が 入っていないこと
     ―― ★`git show --stat` の対象が ★1本だけ（★`-a` を 使っていない証拠）
★(6) ★`DESTRUCTIVE_MARKERS` と ★`_READ_ONLY_GIT` が ★1文字も 変わっていないこと
★(7) ★Claude の配線行数（★上限10行）／ ★(8) ★戻せる ／ ★(9) ★61本を走らせない
```

## 6. ★★私が 言っていないこと

```
★『push も』―― ★★commit だけ（★MGR のとおり）。
★『2DER が 置いて 2DER が commit する』―― ★★置くのは まだ Claude です（★§2(a)）。
★『禁止語を 外した』―― ★★1文字も 外しません。★足すのは ★書いてよい口を 1つ です。
★『これで 戻せる』―― ★★1本だけ。★過去の196件は 戻せません。
```
