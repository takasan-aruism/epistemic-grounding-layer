# 設計/監査 → 実装: 命名 consensus を drift-tolerant 決定論 consolidation に（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論（**LLM 再呼出なし**）
- 正本: `CC_MGR_2026-07-25_ACCOUNT_AXIS_NAMING_JUDGMENT_ADJRESULT.md`（②=drift-tolerant consolidation 採用）+ `s_account_axis_names.py` + 本 handoff
- 位置づけ: ★3 本線。命名機構は既に CONSISTENT、consensus 判定のみ精緻化。

## 0. 規律
- **LLM を再呼出しない**。既に `ACCOUNT_AXIS_NAMES.jsonl` に記録済みの `proposals`（3-seed）を**決定論で再 consolidation** するだけ（provenance の proposals は不変・consensus 結果のみ更新）。
- 幾何不変（v2/membership byte 不変）・id 正典・name 装飾・measure-first（共有核が立たなければ honest UNRESOLVED）。

## 1. consensus の精緻化（strict → drift-tolerant・決定論）
`_consensus(proposals)` を2段に:
1. **fast-path（従来）**: 正規化後 **完全一致 ≥2/3** → その名（`name_status="CONSENSUS_EXACT"`）。
2. **consolidation（新・drift 許容）**: fast-path 不成立時、
   - 各 proposal を **script-boundary トークン化**（連続する latin / katakana / kanji / digit の run を1トークン）。例「JSONLファイル解析CLI作成」→ `[JSONL, ファイル, 解析, CLI, 作成]`。
   - 3 proposal 横断で **各トークンの出現数**を数え、**≥2/3（=2件以上）に出るトークンのみ保持**。
   - 保持トークン ≥1 → **初出順に連結して consensus 名**（`name_status="CONSENSUS_CONSOLIDATED"`・`consolidated_tokens` を provenance に記録）。
   - 保持トークン 0（共有核なし）→ `UNRESOLVED_NO_CONSENSUS`（name=null・捏造しない）。
- 実測見込み: AX-72ead44e → `[Python,モジュール,実装]`（実装は 2/3）＝「Pythonモジュール実装」（不変）。AX2-48354b9a → `[JSONL,ファイル,解析,CLI]`（≥2/3）＝**「JSONLファイル解析CLI」**（命名成立）。

## 2. provenance（追記のみ）
- 各行に `name_status ∈ {CONSENSUS_EXACT, CONSENSUS_CONSOLIDATED, UNRESOLVED_NO_CONSENSUS}` と、consolidation 時は `consolidated_tokens` + 各トークンの出現数を記録。`proposals`/`sample_element_ids`/`model`/`seeds` は不変。

## 3. ゲート `s_account_axis_names.py --check`
- **consensus 決定論再判定**: 記録 `proposals` に §1 の2段規則を再適用 → `name`/`name_status`/`consolidated_tokens` が一致（**LLM 再実行せず**）。
- **幾何不変（最重要）**: v2/membership byte 不変（sha256 照合）不変。
- サンプル決定論・provenance 完全性・UNRESOLVED は name=null 不変。
- **script-boundary トークン化の決定論**（同 proposals→同トークン）を確認。

## 4. 受入（設計が独立再検証）
- AX2 が「JSONLファイル解析CLI」で命名成立（CONSENSUS_CONSOLIDATED）、AX-72ead44e 不変。
- consensus 再判定が記録 proposals に決定論適用（LLM 非再実行）・幾何 byte 不変・provenance に consolidated_tokens 記録。
- 全 gate GREEN。**共有核が立たない軸は honest UNRESOLVED**（measure-first 不変）。

## 5. 完了後
- `CC_IMPL_2026-07-25_NAMING_CONSENSUS_DRIFT_TOLERANT_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → commit=Taka（命名 stage + ACCOUNT_AXIS_NAMES + provenance を1コミット群）→ DE 起票。
- これで両軸 name 確定＝帳簿「見つける層」完成。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。LLM 再呼出なし・記録 proposals を決定論 consolidation・幾何不変・共有核なしは honest UNRESOLVED。★3 本線＝これ自体。*
