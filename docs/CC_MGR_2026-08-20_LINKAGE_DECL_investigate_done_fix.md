# 連動性 宣言（★実装 前）―― ⑥ INVESTIGATE の 空虚成功 を 直す

**2026-08-20 18:3x ／ ★対象は 1点だけ ―― `submit.py` の `_done8 = bool(_refs8)`**
**★第四の 門 ／ 調査機能 ／ RRI ／ Manager ／ 経路表へ ★広げない。**

## 1. 直す もの（★実測で 発火済み）

```
★現状(`submit.py:601`)  _done8 = bool(_refs8)          # ★証拠が 1件でも 在れば 完了
★実測(本日 18:2x)      問い 10 ／ 行 10 ／ 全て UNVERIFIED ／ evidence 0
                       → stop_at_reached = "INVESTIGATION_RECORDED"
★実測(本日 18:1x)      問い 0 ／ 行 0 ／ evidence 4
                       → stop_at_reached = "INVESTIGATION_RECORDED"   ★★1問も 無いのに 完了
```

## 2. 14項目 宣言

| # | 項目 | 宣言 |
|---|---|---|
| 1 | UPSTREAM | `submit.py` の Stage8 INVESTIGATE 分岐（★既存 ／ 新設 しない） |
| 2 | TRIGGER | `work_kind == "INVESTIGATE"` で 観測が 終わった 直後 |
| 3 | INPUT | `contract7["questions"]`（宣言された 問い）／ `investigation_report` の 行 ／ `egl_source_refs` |
| 4 | PRECONDITION | `investigation_report` が 返って いる こと |
| 5 | OUTPUT | `INVESTIGATION_COUNTS`（★分母つきの 数）／ `STOP_AT_REACHED` ／ `NEXT_LEGAL_OPERATION` |
| 6 | DOWNSTREAM | `/api/submit` の 応答（`stop_at_reached` ／ `investigation_report`）★既存の 欄 |
| 7 | STOP | ★下記 §3 の 3条件を すべて 満たす ときだけ `INVESTIGATION_RECORDED` |
| 8 | FAILURE_ROUTE | 満たさない → `STOP_AT_REACHED=None` ＋ ★理由を 語で 返す（`no_question` / `row_count_mismatch` / `verdict_missing`）。例外 → 既存の `INVESTIGATION_FAILED`（★変えない） |
| 9 | RECHECK/RETRY/ESCALATE | ★状態を 持たない ∴ ★毎回 その場で 数える |
| 10 | PERSISTENCE | TRACE（★既存）／ ★新しい file 0 |
| 11 | AUTHORITY | ★発行しない |
| 12 | EVIDENCE | `INVESTIGATION_COUNTS` の 数 ／ `stop_at_reached` ／ 応答の `investigation_report` |
| 13 | ROLLBACK | `git revert`（★この 分岐の 判定 3行のみ ∴ 他へ 影響 0） |
| 14 | **ROUTE_STAGE** | **★CONFLICT** ―― Stage8 は 経路表 `S08`＝`contract_seal` を 指す（★2026-08-20 実測）。★段を 作らない。★★『到達』では なく『通過』で 宣言する（★R3） |

**★14項目 埋まった ∴ `DESIGN_HOLD` に ならない。**

## 3. 成立条件（★存在では なく ★分母つきの 数）

```
★① questions > 0
★② rows == questions            （★宣言した 問いの 数と 報告の 行数が 一致）
★③ すべての 行に verdict が 在り ★5語(EXISTS/PARTIAL/ABSENT/CONFLICT/UNVERIFIED)の いずれか
★★この 3つを すべて 満たす ときだけ `INVESTIGATION_RECORDED`。
★★`evidence_refs` の 有無は ★成立条件に 入れない（★Taka 逐語）。
★★UNVERIFIED は 回答と して 数える。★但し ★`resolved == 0` の ときは
   ★`unresolved` を 立て ★文面に 『調査不能』を 逐語で 出す（★明示する）。
```

## 4. ★★1つ 残る 曖昧さ（★私が 決めない ／ ★数は 両方 出す）

```
★受入②「QUESTIONS 10件・回答0件 → 正常完了しない」の ★『回答0件』の 読みが 2通り 在る:
   ★読みA = ★行が 0（★報告が 組めなかった）      → ★私の ②で 落ちる
   ★読みB = ★行は 在るが すべて UNVERIFIED       → ★『UNVERIFIED も 回答と して 数えてよい』と 衝突
★★∴ ★私は ★読みA で 実装し、★読みB の 場合は ★`resolved=0` と `unresolved=true` を
   ★数と して 出して ★判定は Taka に 返す（★勝手に 決めない）。
★★どちらに するかは ★1行で 切り替わる ―― ★ご裁定を いただければ 即 直せる。
```
