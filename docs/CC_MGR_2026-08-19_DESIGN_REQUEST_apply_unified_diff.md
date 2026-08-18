# 宛: DESIGN（監査 CC）―― 契約作成の依頼: unified diff を**本当に当てる**純関数

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。この文書は要件だけです。**

---

## 1. 直したいこと（★1点）

```
`twoder/patch_bridge.py::_apply_to_working`（110-119行）が
★unified diff を ★当てずに ★diff の 文字列を ファイルへ 書いている。

   data = canonical['diff'].encode('utf-8')
   for filename in validated.filenames:
       path = _confined_path(workspace_dir, filename)
       if not os.path.isfile(path): raise FileNotFoundError(path)
       if expected_preimage is not None: … 検査 …
       ★open(path,'wb').write(data)      # ★diff を そのまま 書く

★MGR 実測（★使い捨ての場・2026-08-19）:
   適用前 'hello\n' → ★適用後 '--- a/target.txt\n+++ b/target.txt\n@@ -1 +1 @@\n-hello\n+world\n'
   ★期待は 'world\n'
```

## 2. ★契約経路の制約（★これに合わせて契約を書いてほしい）

```
★`domain_dw._place_and_commit` は ★`def X(` の X から ★`twoder/X.py` を 決める
   ＝★契約が 置けるのは ★★『新しい 1関数の ファイル』だけ。
★★既存の `patch_bridge.py` の 一部を 書き換えることは ★できない（★2026-08-19 実測・DESIGN も 確認済み）。

★∴ 契約の 対象は ★★純関数 1本 に してほしい:
     ★入力 = 元のテキスト ＋ unified diff のテキスト
     ★出力 = 当てた後のテキスト（★または 当てられない 理由）
     ★★副作用 0（★ファイルを 触らない ／ ★subprocess を 使わない ／ ★決定論）
★★名前・引数・返りの 形は ★DESIGN が 決める（★MGR は 決めない）。
```

## 3. 守ってほしいこと

```
★新しい patch 形式を 作らない ―― ★unified diff の 既存形式を そのまま 使う
   （★`canonical_diff_artifact` が 作る 形: schema_version='unified-diff-v1' /
     base_commit / fingerprint / diff。★`--- a/…` と `+++ b/…` を 必須と している）
★新台帳 0 ／ 新 ID 0 ／ front door の 口 0増
★★`patch_bridge` の 安全機構は ★1つも 触らない:
     allowed_files ／ throwaway 制約（`_mint_test_energize`）／ preimage ／
     rollback（`_restore_preimage`）／ provenance ／ recorder（PATCH_APPLICATION）
★実 repo 用の energize には ★触らない（★逐語「§3 design + Taka gate」＝★別裁定）
```

## 4. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★本体   … 'hello\n' ＋ diff(hello→world) → ★'world\n'（★diff 文字列を 返さない）
★大小   … 1行 ／ 複数行 ／ 末尾改行の 有無
★不一致 … 元のテキストが diff の 文脈と 合わない → ★当てない（★語で 返す・★fail-closed）
★空・None … diff が 空 ／ 元が 空 ／ `--- a/` `+++ b/` が 無い
★複数 hunk … `@@` が 2つ以上
★副作用 … ★ファイルを 開かない・書かない（★純関数）
★決定論 … 同じ入力で 同じ出力
```

## 5. ★MGR が先に言っておくこと（★隠さない）

```
★★この契約が 通っても ★Taka の 完了条件 1〜10 は ★まだ 満たせない。
★理由 = ★出来上がるのは ★`twoder/<name>.py` の ★純関数 1本。
   ★それを `_apply_to_working` から ★呼ぶ 配線が ★別途 要る。
★★配線は 契約経路では できない（★§2）＝★今夜 5回 出た 型「置いてある≠繋がっている」。
★★∴ 完了条件の 4・5（★適用後が 'world\n' ／ ★diff を 書き込まない）を 測るには
   ★配線 1箇所が 要り、★それには ★Taka の 一言が 要る（★前回 裁定 A と 同じ形）。
★MGR は ★勝手に 書かない。
```

## 6. 契約の形（★既存どおり）

```
`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs ／ 命名 = CC_DESIGN_2026-08-19_CONTRACT_<name>.md
→ ★置けば 常駐 `submit_next_contract` が 次の巡回で 自力で 投げる（★実証済み・3分）
```

## 7. MGR がしていないこと

```
★設計 0 ／ 実装 0 ／ 契約本文 0 ／ patch_bridge を 触っていない
★本番ファイル 0 ／ 実 repo energize に 触っていない
★配線を 勝手に していない
```
