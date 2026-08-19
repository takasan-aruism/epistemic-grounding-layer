# 宛: Taka / 設計 / 監査 ―― **サイクルが閉じた**（A/B/C 全成立・★判断ロジック 0行）

**実 repo 書き込み 0。connector の本線配線はしていない。暴走 TASK は BLOCKED のまま未接触。**

## 0. 結果（★Hermetic・★3ケース）

| ケース | stage | on-disk | 記録 | reconciler | fresh |
|---|---|---|---|---|---|
| **A** test PASS | `CONFIRMED` | `'world\n'` | `[APPLIED]` | **BALANCED** | **True** |
| **B** test FAIL → rollback 成功 | `ROLLED_BACK` | **`'hello\n'`** | `[APPLIED, ROLLED_BACK]` | **BALANCED** | **True** |
| **★C** test FAIL → rollback 失敗 | `ROLLBACK_FAILED` | `'world\n'` | `[APPLIED, ★ROLLBACK_FAILED]` | **★IMBALANCED** | **★False** |

```
★B の 判断: rollback_allowed{'restore': True} → rollback_outcome{'ROLLED_BACK', escalate: False}
★C の 判断: rollback_allowed{'restore': True} → ★_restore_preimage を 落として 実験
            → rollback_outcome{'ROLLBACK_FAILED', 'restore_raised', ★escalate: True}
            → ★★虚偽 ROLLED_BACK = ★0
            → reconciler 未解消 = (('t.txt', 'rollback_failed_unresolved'),)
            → ★latest_balance_proof ★fresh=False ＝★★次の energize が 止まる 材料
```

## 1. ★必ず確認する項目（★Taka 指定）

| 項目 | 実測 |
|---|---|
| `dry_run_apply` 出力を**無加工**で `dry_run_ok` へ | **★3ケースとも `proceed=True`** |
| filename 集合が**全段で一致** | **★`['t.txt']`**（dry-run / preimage / 記録 / apply後） |
| fingerprint / post_apply_sha256 / preimage / provenance の意味 | **★不変** |
| allowed_files | **★不変** |
| 実 repo 書き込み | **★0**（すべて `/tmp/cyc*` 配下） |
| 暴走 TASK | **★BLOCKED のまま未接触** |

## 2. 書いた足場（★`twoder/apply_cycle.py`・commit `c21ede0`）

```
★判断は 1つも 書いていない ―― ★2DER の 部品の 返りを ★そのまま 使うだけ:
    dry_run_ok          … 進んでよいか
    rollback_allowed    … 戻してよいか
    rollback_outcome    … 戻せたか ＋ 記録に 書く 語
    （unresolved_rollback / patch_correspondence は ★`bridge_reconciler` が 呼ぶ）
★test / audit の 合否は ★呼び手が 渡す（★サイクルは 判定しない＝Taka 逐語）
★段の 並びは Taka 指定の とおり:
    patch → dry_run_apply → dry_run_ok → apply_patch_bounded → test/audit
    → PASS: APPLIED 維持 → reconcile
    → FAIL: rollback_allowed → restore → rollback_outcome
            → ROLLED_BACK / ★ROLLBACK_FAILED → reconcile
```

### ★1 patch = 1 file に限った理由（★私の新しい規則ではない）

```
逐語（`worker_output_to_artifact:311`）:
   「files_changed must be a list/tuple of ★exactly one filename」
★∴ ★既存の 制約に 合わせた。★複数 file は `REFUSED_MULTI_FILE` で 受けない
   （★合議の 規則を ★私が 作らない ため）。
```

## 3. ★開示（★隠さない）

```
★私の 試験の 組み方が 1度 誤った ―― ★C で 適用時に energize を 渡さず
   `TypeError: not an _EnergizedApply` で 落ちた。
   → ★正規の token で 適用し ★`_restore_preimage` だけを 落とす 形へ 組み直した。
   ★★部品の 欠陥では なく ★私の 手順の 誤り（★今日 2度目・★どちらも 試験側）。
```

## 4. ★今の状態

```
★配線済み・稼働: requeue_decision ／ should_call_senior ／ apply_unified_diff ／
                patch_correspondence ／ unresolved_rollback
★サイクルに 組み込み済み: dry_run_ok ／ rollback_allowed ／ rollback_outcome
★配置済み・未配線: tasks_to_enqueue ／ dispose_decision
★★`apply_cycle` は ★まだ 本線から 呼ばれていない（★Taka 指示どおり）
```

## 5. ★別件（★記録のみ・★直していない）

```
★`would_write_sha256` が diff の fingerprint（★`dry_run_ok` は 見ない ∴ サイクルに 影響なし）
★create / delete が `canonical_diff_artifact` で 拒否される
   ＝★Repo 自己更新の ★未実装能力（★Taka 裁定で 別件記録のみ）
```

## 6. 次

```
connector 本線配線 → delegated energize → 初回 real-repo 1件
```
