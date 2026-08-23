# 台帳の統廃合 ②「登記簿から外す」 v0.1（実施記録）

**作成: Claude Code（MGR／台帳側）／ 2026-08-23**
**前提: `docs/CC_DESIGN_2026-08-23_LEDGER_CONSOLIDATION_SURVEY.md`（ESDE Evaluation 監査の調査・実装0行）**
**指示: Taka「簡単な方から積み上げる」**

## 0. ★調査で1件、前提が違っていた

監査の調査 §6 は「②『登記簿から外す』は **`_is_nonprod` の条件に足すだけ**」としていた。
★**当たらない。** 実測:
```
_is_nonprod の呼び手 = s10_ledger_registry.py:163,164 の2箇所だけ
  prod    = [k for k in chosen if not _is_nonprod(k)]     ← ★書き手の分類に使う
  nonprod = [k for k in chosen if _is_nonprod(k)]
```
★`_is_nonprod` は **書き手（.py）を本番/非本番に分ける**もので、**台帳の母数には効かない**。
母数を決めるのは `all_ledgers()` の除外3条件（`.jsonl` 以外 / `structure/` / `fixtures`・`problems`）。
∴ ★**足す先は `all_ledgers()`**。

## 1. 足した除外条件3つ（★ファイルは1バイトも消さない）
```python
if re.match(r"data_[a-z0-9_]+/", rel):            continue   # 実験ごとの作業ディレクトリ
if re.search(r"_rerun\d*\.jsonl$", rel):          continue   # 同じ物の再実行
if re.match(r"docs/SUBMIT_\d{4}-\d{2}-\d{2}/", rel): continue # 出荷した写し
```

## 2. 実測（★変更前を保存して差分を取った）

```
件数 56 → 46（★10本 減）
★母数から外れた10本（＝意図した10本ちょうど）:
  egl/data_acq_live/events.jsonl            egl/data_acq_task/events.jsonl
  egl/data_gate4/events.jsonl               egl/data_jrev0003/events.jsonl
  egl/data_sleepmode_acq/events.jsonl       egl/data_sleepmode_claim/events.jsonl
  egl/docs/BREAKAGE_LIST_2026-07-23_rerun.jsonl
  egl/docs/BREAKAGE_LIST_2026-07-23_rerun2.jsonl
  egl/docs/SUBMIT_2026-07-21/02_ledger/REVIEW_LEDGER.jsonl
  egl/docs/SUBMIT_2026-07-21/05_de/DE-0474_DE-0475.raw.jsonl
★増えた: なし
★残った46本で属性が変わったもの: 3件（すべて `rows` のみ＝台帳が動いているだけの再計測）
  ds/data/event_trace.jsonl / egl/data/events.jsonl / rri/rri/rthread_events.jsonl
```

## 3. 受入条件
| 条件 | 実測 | |
|---|---|---|
| 56 → 46（10本減） | **56 → 46** | ✅ |
| 外れたのは意図した10本だけ | **10本一致・増えた 0** | ✅ |
| 残り46本に意図しない属性変化なし | **`rows` の再計測 3件のみ** | ✅ |
| mismatch が増えない | **0 mismatch over 46**（変更前も 0） | ✅ |
| ★ファイルを消していない | **3本を目視確認・全部在る** | ✅ |

## 4. まだやっていないこと
- **①統合**（`DESIGN_EVIDENCE_LEDGER` 4→1 / `REVIEW_LEDGER` 4→1 / `audit_backlog` 4→1 ＝ 9本減）
  ★中身の移送が伴うので②の次
- **③保留20本**の棚卸し（何のために作ったかが分かるまで触らない）
