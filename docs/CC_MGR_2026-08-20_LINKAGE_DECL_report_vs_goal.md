# 連動性 宣言（★実装 前）―― REPORT成立 と GOAL成立 を 分ける

**2026-08-20 18:4x ／ ★Taka 裁定で 固定された 規則を そのまま 実装する（★私は 規則を 足さない）**

## 1. 固定された 判定規則（★Taka 逐語）

```
questions == 0                        → INCOMPLETE
rows != questions                     → INCOMPLETE
verdict 不足                           → INCOMPLETE
rows == questions かつ resolved == 0   → ★UNRESOLVED（★成功では ない ／ ★正常に 停止 ／ needs_design）
rows == questions かつ resolved >  0   → REPORT_RECORDED

★二層:
  REPORT成立 = 問いと 行と verdict が 揃った
  GOAL成立   = ★必須質問が ★必要な 証拠つきで 解決された
★★この 二つを 混ぜない。
```

## 2. 14項目 宣言

| # | 項目 | 宣言 |
|---|---|---|
| 1 | UPSTREAM | `submit.py` Stage8 INVESTIGATE 分岐（★既存）／ `handoff_contract.build`（★必須質問の 読み取り） |
| 2 | TRIGGER | 観測が 終わり 調査表が 組まれた 直後 |
| 3 | INPUT | `questions` ／ `required_questions`（★新マーカー）／ `investigation_report` の 行 |
| 4 | PRECONDITION | `investigation_report` が 返って いる |
| 5 | OUTPUT | `INVESTIGATION_COUNTS` ／ **`INVESTIGATION_RESULT`**（3語）／ **`INVESTIGATION_GOAL`** ／ `STOP_AT_REACHED` |
| 6 | DOWNSTREAM | `/api/submit` 応答（★`investigation_result` ／ `investigation_goal` を 追加・★`tr.get` のみ） |
| 7 | STOP | `REPORT_RECORDED`→`INVESTIGATION_RECORDED` ／ `UNRESOLVED`→`INVESTIGATION_UNRESOLVED` ／ `INCOMPLETE`→`None` |
| 8 | FAILURE_ROUTE | `INCOMPLETE` は 理由を 語で（`no_question` / `row_count_mismatch` / `verdict_missing`）／ 例外は 既存の `INVESTIGATION_FAILED`（★変えない） |
| 9 | RECHECK/RETRY/ESCALATE | ★`UNRESOLVED` は **失敗では ない** ∴ ★再試行へ 自動で 進めない。★`needs_design` と 不足を 数で 返す |
| 10 | PERSISTENCE | TRACE（★既存）／ ★新 file 0 ／ ★新 DW state 0 |
| 11 | AUTHORITY | ★発行しない |
| 12 | EVIDENCE | `INVESTIGATION_COUNTS` の 数 ／ `INVESTIGATION_GOAL.unresolved_required` ／ `stop_at_reached` |
| 13 | ROLLBACK | `git revert`（★分岐の 判定と マーカー 1つのみ） |
| 14 | **ROUTE_STAGE** | **★CONFLICT**（Stage8 は 経路表 `S08`＝`contract_seal` を 指す）★段を 作らない ／ ★『通過』で 宣言（R3） |

**★14項目 埋まった ∴ `DESIGN_HOLD` に ならない。**

## 3. 必須質問の 指定（★既存の マーカー作法を そのまま 使う）

```
<<<2DER:REQUIRED>>>
M1
M2
M8
<<<2DER:END>>>

★照合は ★語境界（`\bM1\b`）＝ ★`M1` が `M10` に 誤って 当たらない（★決定論）。
★必須指定が 無い ときは ★GOAL を 判定しない（`achieved = None`）＝ ★勝手に 合否を 作らない。
```

## 4. ★★到達できない 守り（★前回の 続き ―― ★隠さない）

```
★`rows != questions` と `verdict_missing` は ★`investigation_report` が 問いと 1:1 で 行を 作り
  ★必ず 5語の verdict を 入れる ため ★★今日の 経路では 発火しない。
★★∴ ★守りは 置く が ★『働いた 証拠』は ★UNVERIFIED の まま 残す（★前回と 同じ 扱い）。
```
