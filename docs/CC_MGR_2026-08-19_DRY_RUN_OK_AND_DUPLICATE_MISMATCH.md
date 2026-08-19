# 宛: Taka（★裁定が要る） / 設計 / 監査 ―― `dry_run_ok` 完成 ＋ **★重複で噛み合わない1点**

**実装 0。実 repo 書き込み 0。サイクル本体は書いていない。**

## 0. 納品された部品（★2DER が書いた・★MGR は1行も書いていない）

```
twoder/dry_run_ok.py（★68行・commit ★cdeb007・封印試験 14本）
   def dry_run_ok(files, expected_preimages, allowed_files)
   返り = {"proceed", "reason", "names"}
   ★逐語「dry-run の結果で適用へ進んでよいかを言う。★当てた後の姿は見ない。」
```

**★規則8つ（★全数実測・★全部 期待どおり）:**

| 規則 | 実測 |
|---|---|
| 進んでよい | `{'proceed': True}` |
| files 空 | `False / 'no_files'` |
| allowed 空 | `False / 'no_allowed_files'` |
| **★重複** | **`False / 'duplicate_file' / names=['t.txt']`** |
| 範囲外 | `False / 'outside_allowed'` |
| file が無い | `False / 'missing_file'` |
| 期待値が無い | `False / 'no_expected_preimage'` |
| **preimage 不一致** | **`False / 'preimage_mismatch'`** |

**★`would_write_*` を1つも見ていない** ―― DESIGN の「★(い)だが『回避』ではない」の意味は、
**dry-run の役割を「★書く前に、当てられる状態か」に絞った**ことだと読める（★私の解釈・★契約本文は読んでいない）。

## 1. ★噛み合わない1点（★実測）

```
★実物の `dry_run_apply` の 返りを ★そのまま 渡す
   → ★{'proceed': False, 'reason': 'duplicate_file', 'names': ['t.txt']}
★重複を 落として 渡す
   → ★{'proceed': True}

★原因: `validate_artifact` が `a/` と `b/` の 両方から filename を 拾う ∴ ★同じ名前が 2つ
   （★今夜 3回 別件として 記録済み）
★★一方 `_apply_to_working` は ★`dict.fromkeys` で ★重複を 落として 適用する
   （★今日 私が 入れた・★当てる形では 2回目が 必ず 文脈不一致に なるため）
★★∴ ★パイプラインが 不整合:
     ★適用側 = 重複を 落とす ／ ★dry-run の 門 = 重複を 拒否する
```

## 2. ★選択肢（★MGR は決めない・★Taka 裁定）

```
(あ) ★サイクル（足場）が 重複を 落としてから `dry_run_ok` に 渡す
     ＋ 変更は 足場 1行 ／ ＋ ★`_apply_to_working` と 揃う
     − ★『重複が 在る』という 既存の 欠陥を ★門の 手前で 消す
(い) ★`validate_artifact` / `dry_run_apply` の 重複を 直す
     ＋ ★根本（★1箇所で 直る 見込み）
     − ★別件を 1つ 開ける（★Taka 原則「1つの 閉塞に 2つ 増やさない」に 触れる）
     − ★`validate_artifact` は ★安全境界の 一部（★`filenames` は 記録にも 出る）
(う) ★重複を そのまま 拒否として 扱う
     − ★★今の パイプラインでは ★1件も 適用できない（★実測）
```

**★MGR の見立て（★決定ではない）: (あ)。**
**理由: `_apply_to_working` が 既に 同じ扱いを している ∴ ★足場が 揃えるだけ。**
**★重複そのものは ★今夜 既に 3回 記録済み ∴ ★隠すことには ならない。**

**★但し ★注意（★私が 一存で 決めない 理由）:**
```
★`dry_run_ok` の 規則3「重複 → 拒否」は ★DESIGN が ★意図して 入れた fail-closed。
★足場が 黙って 落とすと ★その 意図を 打ち消す 面が 在る。
```

## 3. ★サイクル本体（★まだ書いていない・★形だけ示す）

```
★判断は すべて ★2DER の 部品が 持つ:
   dry-run の 可否 … ★`dry_run_ok`（★完成）
   戻してよいか   … ★`rollback_allowed`（★完成・呼び手 0）
   戻せたか＋語   … ★`rollback_outcome`（★完成・呼び手 0）
   未解消か       … ★`unresolved_rollback`（★配線済み）
   対応しているか … ★`patch_correspondence`（★配線済み）
★足場が するのは ★順に 呼ぶ ことだけ:
   capture_preimage → dry_run_apply → ★dry_run_ok → apply_patch_bounded
   → ★test/audit の 合否は ★呼び手が 渡す（★サイクルは 判定しない）
   → 成功なら 確定 ／ ★失敗なら rollback_allowed → _restore_preimage → rollback_outcome → 記録
```

## 4. ★残っている回帰（★別件・★直していない）

```
★`dry_run_apply.would_write_sha256` が ★diff の fingerprint（★『当てた後』では ない）
   ★`dry_run_ok` は ★この欄を 見ない ∴ ★今の サイクルは ★影響を 受けない
   ★但し ★他の 誰かが 使えば 誤る ∴ ★記録に 残す
★`validate_artifact` の filename 重複（★§1）
```

## 5. していないこと

```
★実装 0 ／ 判断ロジック 0行 ／ 実 repo 書き込み 0 ／ サイクル本体 0
★(あ)(い)(う) を 選んでいない ／ 回帰を 直していない
★delegated energize・初回 real-repo に 進んでいない
★暴走 TASK TASK-2DER-32EDB6C4 は BLOCKED の まま 触っていない
```
