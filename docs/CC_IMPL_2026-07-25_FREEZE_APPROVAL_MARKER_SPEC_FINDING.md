# 実装(IMPL) → 監査(AUDIT): CAND-48354b9a 凍結 marker の正確な filename/schema（FINDING・失敗予防）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl
- 契機: `CC_MGR_2026-07-25_2BR3_FREEZE_APPROVAL_ADJRESULT.md`（Taka 承認済み・CAND-48354b9a を v2 凍結）

## ★ 失敗予防 flag: filename の typo
MGR 文書は marker 先を **`FREEST_APPROVALS`** と表記（line 9, 20・2箇所）していますが、私の 2b-r3 機構が読むのは:

```
structure/FREEZE_APPROVALS.jsonl        ← 正(s_rthread_2br3.py: APPROVALS = os.path.join(STRUCT, "FREEZE_APPROVALS.jsonl"))
```

**`FREEST_APPROVALS` で authored すると `_load_approvals()` が読まず、v2 は silently 凍結されません**（no-auto-freeze の設計上、marker 不在＝凍結しないため RED にもならず「凍結されない」だけ）。正しいファイル名で投入してください。

## marker の正確な schema（`_load_approvals` が要求）
1 行 = JSON。有効化条件は **`approved_by == "Taka"` かつ `candidate_id` 非空**:

```json
{"candidate_id": "CAND-48354b9a", "approved_by": "Taka"}
```

- `#` 始まりの行はコメントとして無視。余分なフィールドは **loader が保持・無視**するので provenance を足せます（ADJRESULT §1 の「誰=Taka・いつ・どの候補」を満たすには例）:
```json
{"candidate_id": "CAND-48354b9a", "approved_by": "Taka", "approved_at": "2026-07-25", "adjresult_ref": "CC_MGR_2026-07-25_2BR3_FREEZE_APPROVAL_ADJRESULT.md"}
```
（`approved_at`/`adjresult_ref` は機構の解錠条件に影響せず、provenance 記録として残る。）

## 投入後の機構挙動（実装は ready）
- `python3 s_rthread_2br3.py` 再実行で: `build_v2` が承認済み QUALIFIED を v1 不変コピー + 新軸として **`ACCOUNT_AXES_v2.json`**（axis_id=`AX2-48354b9a`）を生成、**`ACCOUNT_MEMBERSHIP_v2.jsonl`**（axes_version=v2・負の制御相対 membership）を再計算。marker 内 candidate_id が現 QUALIFIED に一致する時のみ凍結。
- `--check`: no-auto-freeze 不変（marker 在るので v2 存在は GREEN）、byte 一致、I1 保存。

## 役割の確認（誰が marker を書くか）
- FREEZE_APPROVALS は REQUIRED_INPUTS/CANONICAL_STATES と同じ **authored 系ファイル**＝設計/承認チャネルの所掌と理解しています。私（IMPL）は marker を authored せず、**投入後の v2 生成・gate GREEN 化は即実行**します（DESIGN→IMPL handoff or marker 投入を待機）。もし私が marker を書くべきなら指示ください（Taka 承認は ADJRESULT で記録済みと理解）。

---
*実装(IMPL)。承認 marker の filename typo で silently 凍結漏れが起きるのを予防。★3 本線は止めていません。*
