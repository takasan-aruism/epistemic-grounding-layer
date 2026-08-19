# 宛: Taka ―― **安全経路の 調査: ★口は 在る ／ ★不足は 1つ（★差分を 作る 段）**

**2026-08-20 07:0x ／ ★調査のみ ／ ★実装 0 ／ ★投入 0 ／ ★実 repo 書き込み 0**
**★SELF_DEV_TOKEN = ★5/5 ／ ★HEAD `twoder 24c649a` 不変 ／ ★常駐 停止のまま**

---

## 1. ★★『2DER 生成 artifact を 安全な 実 repo 更新経路へ 渡す 既存の 口』は **★在る**

```
★`twoder/bridge_minter.py::mint_real_energize(request, event_log, repo_dir, now_ts=None)`
★★門は 3つ（★逐語）:
  (1) 「a real ★ENERGIZATION_ADJUDICATION event EXISTS in the injected event log and
       matches this exact request」
  (2) 「authority == Taka: ★authority_owner == 'TAKA' AND ★granted_by == 'TAKA' AND
       attribution is NOT self-/model-authored (★self-energization refused)」
  (3) 「the reconciler proves a ★FRESH balance (bridge_reconciler.latest_balance_proof),
       and that proof is for the request's base_commit。★None/imbalanced/stale => refuse」
★★＝ ★実 repo 用の 発行口は ★実在し ★3つの 門で 守られている。
```

**★★但し ―― ★本線に 呼び手が 無い（★実測）:**

```
★`mint_real_energize` の 呼び手 = ★`twoder/regression/verify_minter_B.py` ／
                                 ★`twoder/regression/verify_throwaway_first.py`
★★＝ ★回帰試験 だけ。★本線（webui / manager / dispatch）からの 呼び出し = ★★0件。
★（★`patch_bridge` 逐語「There is ★NO real-repo minter here; that is a §3 design + ★Taka gate.」
   ＝ ★patch_bridge 自身は 実 repo を 受けない ／ ★受ける のは ★minter の 側）
```

## 2. ★★適用の 一周も 実在する（★今夜 実走 済み）

```
★`apply_cycle(workspace_dir, artifact, allowed_files, energize, recorder, task_id, ts,
              repo_identity, test_passed, expected_base=None, expected_fingerprint=None)`
★★＝ ★安全検査 → 適用 → 失敗時 rollback → 記録 まで ★1本に なっている。
★内部で 呼ぶ 2DER 製 部品 = `dry_run_ok` / `rollback_allowed` / `rollback_outcome`
★`bridge_reconciler` が ★git↔記録の 均衡を 判定（★`patch_correspondence` / `unresolved_rollback`）
★★今夜 これらは ★Hermetic で ★A/B/C まで 実走 確認済み（★2026-08-19）。
```

## 3. ★★不足は 1つ ―― **★差分を 作る 段が 無い**

```
★`patch_bridge.validate_artifact` の 実物:
   tokens = ★artifact['diff'].split()
   filenames = ★`a/` `b/` で 始まる token から 採る
★★＝ ★安全経路が 受け取るのは ★★unified diff（★丸ごとの source では ない）。

★★一方 ―― ★2DER の 本線 GENERATE が 作るのは ★丸ごとの source
   （★実測: `test_result.artifact` は ★`def …:` から 始まる ★完全な module ／
     ★今夜 4件とも そう ―― `remove_duplicates` `scan_repository` `analyze_artifact` 等）

★★差分を 作る 部品の 有無（★走査）:
   ・`apply_unified_diff.py` … ★★『当てる』側（逐語「diff_text の前後の空白を落とすと空 …」）
   ・`difflib.unified_diff` を ★作る ために 使う 箇所 = ★★0件
   ・repo 直下の diff/patch 系 file = `apply_unified_diff` / `patch_bridge` /
     `patch_correspondence` / `patch_is_record_only` / `record_only_patch`
     ＝ ★★どれも ★『判定』か『当てる』側 ―― ★★『作る』側は ★無い。
```

```
★★∴ ★不足は ★1つ ―― ★★『いまの file と 2DER が 作った source から ★unified diff を 作る』段。
★★（★これが 無い ため ★安全経路の 入口に ★渡す 物が 用意できない）
```

## 4. ★★経路の 全体（★どこまで 埋まっているか）

| 段 | 既存 | 状態 |
|---|---|---|
| 2DER 生成 artifact | ★`GENERATE.test_result.artifact`（★丸ごとの source） | **★在る** |
| **→ 差分** | ― | **★★無い（★不足 1つ）** |
| → 安全検査 | `validate_artifact` / `dry_run_ok` / `allowed_files` | ★在る |
| → 実 repo 反映 | `apply_cycle` ＋ `mint_real_energize`（★3門） | ★在る（★但し ★本線に 呼び手 0） |
| → rollback 可能 | `capture_preimage` / `_restore_preimage` / `rollback_outcome` | ★在る（★実走済み） |
| → 均衡確認 | `bridge_reconciler` / `latest_balance_proof` | ★在る（★実走済み） |
| → 再実走 | `/api/submit` | ★在る |

## 5. ★★参考（★決定ではない・★事実の 指摘）

```
★今夜 2DER は ★『差分を 作る』課題を ★3回 計画している:
   `TASK-2DER-7D461717` … `diff_texts(old_text, new_text, filename) -> str`
      ★PLAN 成立 ／ ★封印試験 1906B ／ ★実装は provenance で 止まった（★その後 私が 接続）
   `TASK-2DER-EAACCE21` … `create_unified_diff(before, after, filename)`
      ★PLAN 成立 ／ ★契約変換で 止まった（`from impl import` 無し）
   `TASK-2DER-3CF23D43` … 同種
★★＝ ★不足 §3 は ★2DER が ★既に 3回 設計を 出している 対象。
★★＝ ★『作れない』のでは なく ★『本線に 繋がっていない』（★今夜 8回 出た 型）。
```

## 6. ★★上申（★1つ・★私は 案を 出しません）

```
★★不足は ★1つに 絞れた ―― ★『source → unified diff』の 段。
★★これを どう 埋めるか:
   ・★2DER に 作らせる（★過去 3回 PLAN は 出ている）
   ・★但し ★作った 物を ★本線に 繋ぐ には ★実 repo への 反映が 要る
     ＝ ★★`mint_real_energize` の 3門（★特に (2) authority == Taka）が 要る
★★∴ ★★卵と鶏: ★『差分を 作る 部品』を ★実 repo へ 入れる ためにも ★差分が 要る。
★★これを 解く 一手は ★Taka の 裁定 事項（★私は 実装も 迂回も しません）。
```

## 7. ★していないこと

```
★実装 0 ／ 新しい sandbox 補助関数 0 ／ 投入 0
★`_place_and_commit` 0 ／ `_GATES` 書き込み 0 ／ `gates.json` 手書き 0
★rollback / reconciler / authority の 迂回 0 ／ run_next 0
★実 repo 書き込み 0（★`twoder` HEAD `24c649a` 不変）／ ★常駐 停止のまま
★`308C68D4` の 5 failed は ★追っていない（★Taka 指示どおり）
★SELF_DEV_TOKEN = ★5/5
```
