# 宛: Taka / 設計 / 監査 ―― 判定3 の是正: **A〜D ＋ unknown 全成立**（判断ロジック 0行）

**実 repo 書き込み 0。暴走 TASK は BLOCKED のまま未接触。**

## 0. 結果（★Taka 指定の完了条件）

| # | 条件 | 実測 |
|---|---|---|
| A | APPLIED のみ → BALANCED | **`balanced=True` ／ proof=BALANCED ／ fresh=True** |
| B | APPLIED → ROLLED_BACK → BALANCED | **`balanced=True` ／ proof=BALANCED ／ fresh=True** |
| **C** | APPLIED → ROLLBACK_FAILED → **BALANCED でない** | **`balanced=★False`** |
| C | 専用欄に未解消理由 | **`(('t.txt', 'rollback_failed_unresolved'),)`** |
| C | 次の energize 不可 | **proof=★IMBALANCED ／ `latest_balance_proof` ★fresh=False** |
| **D** | 正常な ROLLED_BACK を append → 回復 | **`balanced=True` ／ fresh=True**（★append-only で解消） |
| ★ | unknown outcome は fail-closed | **`balanced=False` ／ `(('t.txt','unknown_outcome'),)` ／ fresh=False** |
| ★ | 実 repo 書き込み 0 | **成立**（すべて `/tmp/wire3-*` 配下） |

**★C の `fresh=False` が ★`bridge_minter` 門(3)の材料**
（逐語「(3) the reconciler proves a FRESH balance … ★None/imbalanced/stale => ★refuse」）
**＝ rollback に失敗して不可逆になった直後は、★次の energize が止まる。**

## 1. 書いた足場（★判断ロジック 0行・★1箇所）

```
reconcile … file ごとに PATCH_APPLICATION.outcome を ★記録順に 並べて
            ★`twoder/unresolved_rollback.py`(★2DER が書いた・封印試験14本)へ 渡すだけ
ReconResult … ★`unresolved_rollback_failures`（(filename, reason) の 組）を ★1欄 追加
              ★`orphans_event_without_git` へ 押し込まない（★DESIGN 裁定=(い)）
balanced   … `not ew_git and not gw_event ★and not unresolved`
emit_reconciliation … payload にも ★1欄（★理由が 門(3)の 材料へ 届く）
```

## 2. ★開示（★隠さない）

```
★私は 1度 誤った ―― ★新しい欄を ★既定値なしの欄より 前に 置き、
  `TypeError: non-default argument 'baseline' follows default argument …` で ★読み込みが 落ちた。
  → ★末尾へ 移して 直した。★実装の 欠陥では なく ★私の 置き場所の 誤り。
★★『1回で 通らない』ことが 早く 分かる 形（★import で 落ちる）だった＝★fail-closed が 効いた。
```

## 3. ★変えていないもの

```
APPLIED / ROLLED_BACK の 意味 ／ ROLLBACK_FAILED を ROLLED_BACK 扱いしない ／
patch fingerprint ／ post_apply_sha256 ／ preimage ／ provenance ／
bridge_minter ／ authority ／ connector ／ delegated energize ／
[BIND-1] read-only ／ [BIND-2] pull-type
```

## 4. ★今日 2DER が増やした能力（★総括）

| 部品 | 状態 |
|---|---|
| `requeue_decision` | **配線済み・稼働**（自力再取得・COMPLETE 2件） |
| `should_call_senior` | **配線済み・稼働**（`claude -p` 29回 → 2回・★今も ur=1〜2） |
| `apply_unified_diff` | **配線済み**（hello → world） |
| `patch_correspondence` | **配線済み**（APPLIED が BALANCED） |
| `rollback_allowed` | 純関数完成（★適用→判定→復元→記録→BALANCED を実測） |
| `rollback_outcome` | 純関数完成（★虚偽 ROLLED_BACK 0・fail-closed） |
| **`unresolved_rollback`** | **★配線済み**（★判定3 を是正） |
| `tasks_to_enqueue` ／ `dispose_decision` | 配置済み・未配線 |

**★Claude が書いたのは 足場 ★5箇所**（`346f074` / `e516007` / `6c87b0b` / `edf42cf` / `d71ba4e`）
**―― どれも ★判断ロジック 0行。**

## 5. 次（★Taka の順序どおり・★未着手）

```
connector 本線接続 → delegated energize → 初回 real-repo 1件
★`rollback_allowed` / `rollback_outcome` は ★まだ 呼び手 0（★connector が それを 担う）
```
