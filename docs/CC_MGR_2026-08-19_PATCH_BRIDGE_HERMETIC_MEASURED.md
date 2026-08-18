# 宛: Taka / 設計 / 監査 ―― `patch_bridge` 実測: **安全機構は動く／適用の中身が patch ではない**

**新規実装 0行。本番ファイルに触れていない。使い捨ての場（`/tmp` 配下）で1件だけ実走した。**

## 0. 結論

```
★★完了条件（★既存ファイルへ ★限定差分が 1件 ★安全に 適用され ★rollback 可能な 証拠が 残る）
   = ★★不成立

★成立した 部分（★4つ）= ★境界・拒否・rollback・記録
★★成立しなかった 1点 = ★★『差分を 適用する』ところが ★patch 適用に なっていない
   ＝★ファイルに ★diff の 文字列 そのものが 書き込まれる
```

## 1. 実走（★1件・使い捨ての場）

```
場 = /tmp/pb-hermetic-lr1nwnrp（★_mint_test_energize が 認めた 使い捨て）
適用前 target.txt = 'hello\n'
diff = "--- a/target.txt\n+++ b/target.txt\n@@ -1 +1 @@\n-hello\n+world\n"
artifact = canonical_diff_artifact(diff, "abc123")
   → 鍵 = schema_version / base_commit / fingerprint / diff
apply_patch_bounded(..., energize=token, expected_base, expected_fingerprint, repo_identity)
   → 返り = {"schema_version":"apply-bounded-v1","outcome":"APPLIED",
             "fingerprint":"c65e6256…","filenames":["target.txt","target.txt"]}
   → 記録 = PATCH_APPLICATION（outcome APPLIED / fingerprint / base_commit / filenames /
             token_id / repo_identity / repo_realpath）

★★適用後 target.txt = ★'--- a/target.txt\n+++ b/target.txt\n@@ -1 +1 @@\n-hello\n+world\n'
★期待は 'world\n' ／ ★実際は ★diff の 文字列 そのもの
```

**★実装（`_apply_to_working` 110-119行）:**

```python
data = canonical['diff'].encode('utf-8')
for filename in validated.filenames:
    path = _confined_path(workspace_dir, filename)
    if not os.path.isfile(path): raise FileNotFoundError(path)
    if expected_preimage is not None: … 検査 …
    open(path,'wb').write(data)          # ★★diff を そのまま 書く（★patch を 当てていない）
```

**★読んで疑い、★走らせて確定した**（★1回の観測で断定していない）。

## 2. ★動いた安全機構（★4つ・★どれも実測）

| # | 検査 | 結果 |
|---|---|---|
| ① | **実 repo を使い捨てと偽れるか** | **★拒否** ―― `not a throwaway (resolved path outside temp root): /home/takasan/twoder` |
| ② | **`allowed_files` の外** | **★拒否** ―― `validate_artifact` が `ValueError: target.txt` |
| ③ | **preimage 不一致 → rollback** | **★成立** ―― `ValueError: preimage` → 記録 `('PATCH_APPLICATION','ROLLED_BACK','patch-bridge')` → **★中身が `'hello\n'` へ戻った** |
| ④ | **記録（証拠）** | **★成立** ―― `outcome` / `fingerprint` / `base_commit` / `filenames` / `token_id` / `repo_identity` / `repo_realpath` |

**★①は Taka の懸念に直接答える** ―― `_mint_test_energize` の逐語:

```
「TEST-ONLY energization minter (Taka 2026-07-18 §1-1) — the ONLY sanctioned _EnergizedApply source…
  Canonical repos live outside the temp root …, so a real repo — passed directly OR via a symlink
  under /tmp — resolves outside the temp root and is ★REFUSED (attack (g) blocked).
  ★There is NO real-repo minter here; that is a ★§3 design + ★Taka gate.」
```

**∴ 本番へ当てる能力は「実装漏れ」ではなく ★設計として Taka の門の向こうに置かれている。**

## 3. ★停止点（★最初の1つだけ）

```
★★`_apply_to_working` の 書き込みが ★patch 適用では なく ★diff の 上書き。
★これを 本線の 配線に 使うと ★★対象ファイルが 破壊される。
★∴ ここが 最初の 停止点。★私は 直していない。
```

## 4. ★併せて出た差（★修理していない・★別件）

```
★(a) `filenames` に 重複が 入る = ["target.txt","target.txt"]
     （★`a/` と `b/` の 両方から 拾うため。★実害は 未確認）
★(b) ★2つの 境界検査が 食い違う:
        validate_artifact(art, ("target.txt",), …)      → ★通る
        check_diff_within_allowed(diff, ("target.txt",)) → ★★ValueError: Path 'target.txt' not allowed
     ＝★同じ「allowed_files」という 名前で ★別の 突き合わせ方を している（★★鍵が 違う の 型）
★どちらも ★今回の 停止点では ない ∴ ★触っていない。
```

## 5. ★次の設計へ渡す材料（★私は設計しない）

```
★契約経路で 作られた 検証済み部品 → patch_bridge → 既存本線 を 繋ぐには、
  ①★`_apply_to_working` が ★本当に patch を 当てること（★今回の 停止点）
  ②★実 repo 用の energize（★逐語「§3 design + Taka gate」＝★Taka の 門）
  ③★`recorder` に ★DW の 記録口を 渡すこと（★`workcell.py:243` が
     『PATCH_APPLICATION は patch_bridge が 適用/rollback を 記録する EMIT 側』と 既に 書いている）
  ④★(b) の 境界検査の 食い違いを どちらに 揃えるか
★★①②が 揃うまで 本線には 繋がらない。
```

## 6. していないこと

```
★実装 0行（★Claude は コードを 1行も 書いていない ―― ★既存関数を 呼んだだけ）
★本番ファイル 0（★書き込みは すべて /tmp 配下の 使い捨て）
★patch_bridge を 直していない ／ 本線へ 繋いでいない ／ 試験を 追加していない
★(a)(b) を 修理していない ／ 新台帳 0 ／ 新 ID 0
```
