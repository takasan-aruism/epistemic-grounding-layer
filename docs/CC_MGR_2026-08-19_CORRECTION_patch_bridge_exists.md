# 宛: Taka / 設計 / 監査 ―― ★訂正: 「配線は構造上できない」は言い過ぎだった

**MGR の前報 `CC_MGR_2026-08-19_WIRING_CANNOT_GO_THROUGH_CONTRACT.md` を訂正する。**
**DESIGN の指摘（2026-08-19 07:34・`ITEM-2DER-EVO-0019` 履歴）を、MGR が自分で確かめた。**

## 0. 訂正の中身

```
★私が書いたこと     = 「★配線は 契約経路では ★構造上 できない」
★正しい 切り分け:
   ①「★契約経路では ★既存ファイルの 一部を 書き換えられない」= ★★正しい（★DESIGN も 実物で 確認）
   ②「★★配線する 口が そもそも 無い」          = ★★誤り
       → ★`twoder/patch_bridge.py` が ★既に 在る
★★∴ 正しい形は「★口は 在る ／ ★契約経路に 繋がっていない」= ★★切ってある。
```

## 1. MGR 自身の実測（★DESIGN の言を鵜呑みにしていない）

```
★twoder/patch_bridge.py = ★在る ／ ★15,376 B ／ ★公開関数 ★11本

  validate_artifact(artifact, allowed_files, expected_base, expected_fingerprint)
  apply_patch(workspace_dir, artifact, allowed_files, energize, expected_base, expected_fingerprint)
  canonical_diff_artifact(diff_text, base_commit)
  dry_run_apply(workspace_dir, validated)
  capture_preimage(workspace_dir, validated)
  emit_patch_application(recorder, task_id, validated, outcome, ts, identity, token_id, …)
  apply_patch_bounded(workspace_dir, artifact, allowed_files, recorder, task_id, ts, energize, …)
  worker_output_to_artifact(worker_diff, files_changed, base_commit)
  capture_provenance(target_repo_dir, allowed_files)
  ★check_diff_within_allowed(diff_text, allowed_files)
  ★bridge_apply_connector(energize_token, workspace_dir, artifact, allowed_files, provenance, …)

★★呼び手 = ★0（★2DER の 走査器 `route_candidates_v2`・★同一 repo の import も 含めて 数えた）
```

**★`allowed_files` で触ってよい範囲を縛る形、★dry-run、★preimage 取得、★rollback 記録まで揃っている。**
**＝★Taka が「将来こう作るべき」と言った『正本で許可された接続点に検証済み部品を1本だけ配線する専用能力』に、★形として既に近い。**

## 2. ★これは今夜5回目の同じ型

```
①経路表の 区間が 在る ≠ 通っている
②機能表に 口が 在る   ≠ 収穫が 在る
③部品が 在り 試験に 通り commit されている ≠ 呼ばれている
④機械は 作る・試す・置く・commit まで できる ≠ 配線できる
⑤★★配線の 口(patch_bridge)が ★在る ≠ ★繋がっている   ← ★今回
★★同型の 既知例 = `autonomous_git`（★「口が無い」のではなく ★切ってある）
```

## 3. ★私の誤りの型（★記録として残す）

```
★私は「★契約経路で できない」を 確かめた 時点で
  ★「★配線は できない」へ ★広げて 書いた。
★★探した 範囲 = ★契約経路の 1本だけ。★他の 口を 探していない。
★★『無い』と 書く前に 探した 範囲を 書く ―― ★書いたが ★範囲が 狭かった。
★DESIGN が 別の 口を 見つけた ＝★★2人で 引くと 片方の 穴が 埋まる（★監査は2人1組の 実例）。
```

## 4. ★選択肢（★DESIGN 提示・★MGR は決めない）

```
(あ) 今回だけ 足場を 人が 書く              … ★★既に 実施済み（Taka 裁定 A・★成立・2件 COMPLETE）
(い) patch_bridge を 契約経路へ 繋ぐ        … ★新しい 部品 0 ／ ★但し ★動くかの 確認から
(う) (あ)で 進め ／ (い)を ★別 item で 測る … ★DESIGN の 推し ／ ★MGR も 同意
```

**★MGR の見立て（★決定ではない）: (う)。**
**理由: (あ) は既に完了し実走で成立した ∴ 閉塞は解けている。(い) は「1つの閉塞に2つ増やさない」の外で、**
**★次の主体移管（★Claude を配線からも外す）の本体 ∴ ★独立して測る価値がある。**

**★但し (い) は「動くか未確認」から始まる**（★DESIGN も MGR も走らせていない ／ 試験 `test_patch_bridge` も無い）。

## 5. していないこと

```
★patch_bridge を 走らせていない ／ 繋いでいない ／ 試験を 書いていない
★新台帳 0 ／ 新 ID 0 ／ 実装 0行（★§4(あ)の 足場1箇所は 別記録・commit 346f074）
★(い) を 勝手に 始めていない
```
