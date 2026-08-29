# hooks/claude/ — Claude Code の PreToolUse フック（★正本はここ）

★★2026-08-30 に ここへ 置いた（★担当 LEDGER・★指摘 MGR）。

## なぜ ここに 在るか

★実測（2026-08-30）= これらの 14本は `~/.claude/hooks/` に しか 無く、
`~` は **git repo では ない** ∴ ★**次に 消えても 誰も 気づかない**。

★`egl` に 置いた 理由 = ★これらが 守って いるのは `egl/docs/` の 規律そのもの
（`2DER_DEVELOPER_DISCIPLINE_v1.0.md` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3.md`）。
★★規則と それを 強制する 物を 別の repo に 置かない。
★`egl/hooks/README.md`（git hook 用）が 既に **「repo に 実体を 置き clone ごとに 有効化する」**
という 作法を 定めて いる ∴ ★新しい 置き場の 規則を 作って いない（★既存に 合わせただけ）。

## 生きて いるのは どちら か

| | 場所 | 役割 |
|---|---|---|
| ★実際に 走る | `~/.claude/hooks/*.sh` | ★Claude Code が 読むのは **こちら** |
| ★正本 | `egl/hooks/claude/*.sh` | ★消えた時に 戻す 先・★履歴が 残る 側 |

★★2つ 在る = ★ずれうる。★★ずれを 見つける 口は 既に 在る:

```
python3 twoder/regression/test_claude_hooks_tracked.py
```

★これは ★封印試験の 走者（`python3 -m twoder.regression_run`）が 拾う
∴ ★**新しい 監視の 仕組みを 増やして いない**。

## 直す 時の 順序

1. `~/.claude/hooks/<name>.sh` を 直す（★走るのは こちら ∴ 先に 効く）
2. `egl/hooks/claude/<name>.sh` へ 写す
3. commit する（★写さないと ★次に 消えた時 戻せない）

★★逆順に しない = ★repo だけ 直しても ★フックは 変わらない。

## 入って いる もの（14本・2026-08-30 時点）

★門（拒否する もの）= `2der_ledger_guard.sh`（台帳の 直読）/ `2der_write_guard.sh`（直接の 書き込み）/
`2der_git_add_guard.sh`（source の commit に 名乗りを 要求）/ `2der_note_form_guard.sh`（記帳文の 形）

★計器（状況表・板）= `2der_status.sh` / `2der_board.sh` / `2der_watch.sh` / `2der_watch_design.sh` /
`2der_a_metric.sh` / `2der_arch_fresh.sh` / `2der_gap_flow.sh` / `2der_layers.sh`

★その他 = `2der_role.sh`（役割の set）/ `2der_session_start.sh`（セッション開始時の 注入）

★`.bak` は 写して いない（★動いて いない ファイルを 正本に しない）。
