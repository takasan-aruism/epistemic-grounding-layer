# 宛: DESIGN（監査 CC）―― 契約作成の依頼: **適用サイクルの判断1つ**（＋★回帰1件の報告）

**依頼元: MGR ／ 2026-08-19 ／ Taka 指示「connector 本線接続へ継続」**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 0. ★先に報告 ―― `dry_run_apply` に**今朝と同じ回帰**が残っている

```
★実測（★使い捨ての git repo）:
   dry_run_apply(...)['writes'][0]
     current_sha256      = 5891b5b5…（★'hello\n' の sha）★正しい
     ★would_write_sha256 = 3a502851…（★★= diff の fingerprint）
     ★would_write_bytes  = 50（★= diff の 長さ）
   ★★`would_write_sha256 == artifact['fingerprint']` = ★True

★★∴ ★`dry_run_apply` は ★『diff を そのまま 書く』前提の まま。
   ★今日 `_apply_to_working` は ★『当てる』形に 直した（★commit 6c87b0b）が
   ★`dry_run_apply` は ★直していない（★MGR の 落ち度・★今朝の 回帰と 同型）。
★★かつ ★`writes` に ★重複が 入る（★`filenames` の a/ b/ 由来・★既報の 別件）。
★★∴ ★このまま 使うと ★『当てた後の 姿』を ★間違って 予告する。
★MGR は 直していない。
```

## 1. ★connector の現状（★実測）

```
`bridge_apply_connector(energize_token, workspace_dir, artifact, allowed_files, provenance,
                        recorder, task_id, ts)` … ★呼び手 ★0
   中身: token 検査 → fingerprint 再計算 → validate_artifact →
        check_diff_within_allowed → apply_patch_bounded → {'applied': True, 'result': …}
★★していないこと:
   ・★dry-run を 呼ばない
   ・★test/audit を 受け取らない
   ・★失敗時の rollback を しない（★`rollback_allowed` / `rollback_outcome` の 呼び手も ★0）
```

## 2. ★Taka が求めた1本の道（★逐語）

```
検証済みartifact → 許可された接続点 → ★dry-run → preimage/fingerprint確認 →
1差分だけ適用 → ★test/audit → 成功なら確定 → ★失敗ならrollback
```

## 3. ★契約にしてほしいもの（★純関数 1本）

**★足りない判断は「★この dry-run の結果で、適用へ進んでよいか」の1点。**

```
★材料（★既に 手元に 在る）:
   ・dry_run の 各 file の {filename, exists, current_sha256}
   ・★期待する 適用前の sha256（★preimage）
   ・allowed_files（★範囲）
★★注意（★DESIGN が 決める）: ★`would_write_sha256` は ★§0 の 回帰の ため
   ★★今は 信用できない ―― ★使わない 形に するか、★`dry_run_apply` の 是正を 先に するか。
★返り（★形は DESIGN が 決める）: ★進んでよいか ＋ ★理由の 語
★★副作用 0（★ファイル・git を 触らない）／ ★決定論。
```

## 4. ★DESIGN に判断してほしい点

```
★(あ) ★`dry_run_apply` の 是正を ★別契約に する（★`apply_unified_diff` を 使って
      ★『当てた後の sha』を 予告する 形へ）→ ★その後で サイクルを 組む
★(い) ★dry-run は ★『file が 在るか / 適用前の sha が 期待どおりか』だけを 見る 形に し、
      ★`would_write_*` は ★使わない（★= 今の 回帰に 触れずに 進める）
★(う) 別の 形
★★MGR の 観察（★決定ではない）: ★(い)なら ★1つの 閉塞に 2つ 増やさない。
   ★但し ★§0 の 回帰は ★残る ∴ ★別件として 記録し 後で 閉じる 必要が 在る。
```

## 5. ★サイクル本体は足場（★MGR が書く・★判断は書かない）

```
★組み立てるだけ ―― ★判断は すべて ★2DER の 部品が 持つ:
   dry-run の 可否   … ★今回 依頼する 部品
   戻してよいか      … ★`rollback_allowed`（★完成・呼び手 0）
   戻せたか＋語      … ★`rollback_outcome`（★完成・呼び手 0）
   未解消か          … ★`unresolved_rollback`（★配線済み）
   対応しているか    … ★`patch_correspondence`（★配線済み）
★test/audit の 合否は ★サイクルの 呼び手が 渡す（★サイクルは 判定しない）
```

## 6. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★file が 無い ／ ★適用前の sha が 期待と 違う（★他人が 触った）／
★allowed_files の 外の file が 混じる ／ ★空の 一覧 ／ ★重複した file（★§0 の 別件）／
★決定論 ／ ★理由の 語
```

## 7. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0 ／ 新台帳 0
★`dry_run_apply` の 回帰を ★直していない ／ connector を まだ 書いていない
★delegated energize・実 repo 適用に 進んでいない
★暴走 TASK TASK-2DER-32EDB6C4 は BLOCKED の まま 触っていない
```
