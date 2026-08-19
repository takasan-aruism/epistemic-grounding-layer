# 宛: Taka / 設計 / 監査 ―― correspondence 回帰を解消: **完了条件7つ全成立**（判断ロジック 0行）

**実 repo 書き込み 0。使い捨ての git repo だけで実走。**

## 0. 結果（★Taka 指定の完了条件）

| # | 条件 | 実測 |
|---|---|---|
| ① | `PATCH_APPLICATION` に `post_apply_sha256` が残る | **★`{"t.txt": "e258d248fda94c…"}`** |
| ② | reconciler が APPLIED を BALANCED と判定 | **★BALANCED** |
| ③ | on-disk は `world\n` | **★`'world\n'`** |
| ④ | rollback 後は `hello\n` | **★`'hello\n'`** |
| ⑤ | ROLLED_BACK も BALANCED | **★BALANCED** |
| ⑥ | patch fingerprint の意味は不変 | **★`fingerprint == art['fingerprint']`（=diff の sha256）／ ★`post != fingerprint`** |
| ⑦ | 実 repo 書き込み 0 | **★成立**（すべて `/tmp/wire-*` 配下） |

## 1. 書いた足場（★判断は1行も書いていない）

### ① `patch_bridge`

```
_apply_to_working  … 当てた後の bytes の sha256 を ★返す（★従来は None）
apply_patch_bounded … その値を ★emit_patch_application へ 渡す
emit_patch_application … payload に ★`post_apply_sha256` を 1欄 足す
    ★filename ごとの dict ／ ★ROLLED_BACK では None
★★`fingerprint` の 意味は 1文字も 変えていない（★別名・別欄・別の意味）
```

### ② `bridge_reconciler`

```
_fold_expected … APPLIED の 期待値を ★`fingerprint` から ★`post_apply_sha256` へ
reconcile:145  … 比較を ★`patch_correspondence('APPLIED', fp, disk_sha, None)` へ 置き換え
                 （★2DER が 契約経路で 書いた 部品・★封印試験 13本）
★★ROLLED_BACK の 扱いは ★1文字も 変えていない（★`None` ＝ clean vs HEAD）
```

**★部品の規則（★docstring 逐語・★実測で全数確認）:**

```
1 不明な語        → False / "unknown_outcome"
2 APPLIED で post 無 → False / "no_post_apply_sha"
3 APPLIED         → disk == post なら True ／ 違えば False / "disk_differs"
4 ROLLED_BACK で head 無 → False / "no_head_sha"
5 ROLLED_BACK     → disk == head なら True ／ 違えば False / "not_restored"
```

## 2. ★変えていないもの（★Taka 指定）

```
patch fingerprint の 意味 ／ allowed_files ／ preimage ／ rollback ／ provenance ／
repo confinement（`_confined_path`）／ bridge_minter ／ authority ／ 実 repo energize ／
[BIND-1] read-only ／ [BIND-2] pull-type ／ `_READ_ONLY_GIT` の 許可名簿
```

## 3. ★開示（★隠さない）

```
★① `apply_patch`（★非 bounded の 方）の 返りが ★None → dict に 変わった。
   ★呼び手 0 を 確認済み（★2DER の 走査器）。★影響は 無いが ★挙動の 変化 ∴ 書き残す。
★② ★私の 試験の 作り方が 1回 誤った:
   ★最初 rollback を ★『既に 適用済み』の ファイルに 対して 走らせた
   → preimage が `'world\n'` ∴ ★復元先も `'world\n'`（★★部品は 正しく 動いていた）
   → ★⑤が IMBALANCED に 見えた。
   ★新しい repo で やり直したら ★④`'hello\n'` ／ ★⑤BALANCED。
   ★★『★1回の 観測で 断定しない』が 効いた（★実装の 欠陥では なかった）。
★③ `post_apply_sha256` を ★filename ごとの dict に した ―― ★Taka の 語は 単数だが
   ★`filenames` は 複数 在り得る ∴ ★file ごとに 持つ 形に した（★機械的な 判断）。
```

## 4. ★これで解けたこと／まだ残ること

```
★解けた: ★今朝 私が 作った 回帰（★APPLIED が 必ず IMBALANCED に なる）
        → ★門(3)（★reconciler の 残高証明）が ★通り得る 状態に なった
★残る（★今回は 触っていない）:
   ・rollback plan の 保持（★適用後に test/audit が 落ちた 時に 戻す 手）
   ・rollback 失敗を ★別の語で 記録し 上申する 経路
   ・delegated energize（★bridge_minter の 門(2) の 分岐）
   ・connector の 呼び手（★今 0）
   ・★実 repo への 適用（★energize が 構造的に 拒否・★Taka の 門）
```

## 5. していないこと

```
★判断ロジック 0行 ／ 実 repo 書き込み 0 ／ 実 repo energize に 触っていない
★rollback 保持・delegated energize・実 repo 適用に 進んでいない
★新台帳 0 ／ 新 ID 0 ／ 新しい 判断規則 0
```
