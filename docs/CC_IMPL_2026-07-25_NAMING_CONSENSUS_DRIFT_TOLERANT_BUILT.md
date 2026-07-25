# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 命名 consensus を drift-tolerant 決定論 consolidation に（BUILT・★3本線）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論・**LLM 再呼出なし**
- 対応: `CC_DESIGN_2026-07-25_NAMING_CONSENSUS_DRIFT_TOLERANT_HANDOFF.md`（②=drift-tolerant consolidation 採用）

## 成果物（working tree・未commit）
- `structure/s_account_axis_names.py`（consensus を2段化 + reconsolidate パス + `--check` 精緻化）
- `structure/ACCOUNT_AXIS_NAMES.jsonl`（**両軸 name 確定**・consolidated_tokens 追記）
- meta fold（regen_meta）: LLM_INVOCATIONS / TASK_CONTRACTS / READ_PATHS

## 実装（handoff §1・LLM 再呼出なし・決定論）
- **2段 consensus**:
  1. **fast-path**: 正規化後 完全一致 ≥2/3 → `CONSENSUS_EXACT`。
  2. **consolidation（drift 許容）**: fast-path 不成立時、**script-boundary トークン化**（連続する latin/digit/katakana/hiragana/kanji の run を1トークン・NFKC 後）→ 各トークンの出現 proposal 数を数え **≥2/3 のみ保持** → **初出順連結**で `CONSENSUS_CONSOLIDATED`。共有核ゼロ → `UNRESOLVED_NO_CONSENSUS`（捏造しない）。
- **reconsolidate パス**: `ACCOUNT_AXIS_NAMES.jsonl` が既存なら **記録済み proposals に2段 consensus を決定論再適用**（`_llm_propose` を呼ばない）。`proposals`/`sample_element_ids`/`model`/`seeds`/`temperature` は不変・consensus 結果のみ更新。`--regen-llm` で強制再取得も可（初回用）。

## 命名結果（両軸成立＝「見つける層」完成）
| axis | name | status | 機序 |
|---|---|---|---|
| AX-72ead44e | **「Pythonモジュール実装」** | CONSENSUS_EXACT(2/3) | fast-path・不変 |
| AX2-48354b9a | **「JSONLファイル解析CLI」** | CONSENSUS_CONSOLIDATED | 共有トークン JSONL(3)/ファイル(3)/解析(2)/CLI(2)。統計/作成 は count1 で除外 |

- AX2 は 3 seed（JSONLファイル解析CLI / …作成 / JSONLファイル統計解析）の**共有核**を抽出＝MGR/DESIGN の予測「JSONLファイル解析CLI」と一致。**false-negative 解消**。

## 検証（§3-4・全 gate GREEN）
- **consensus 決定論再判定**: 記録 proposals に2段規則を再適用 → `name`/`name_status`/`agreement_count`/`consolidated_tokens` が台帳と一致（**LLM 非再実行**）。
- **幾何不変（最重要）**: `ACCOUNT_AXES_v2.json`/`ACCOUNT_MEMBERSHIP_v2.jsonl` byte 不変（sha256 照合）。
- **script-boundary トークン化の決定論**: 同 proposals→同トークン（consolidated_tokens 照合で担保）。
- サンプル決定論・provenance 完全性（CONSOLIDATED は consolidated_tokens 必須）・UNRESOLVED は name=null 不変。
- 全 gate GREEN（s_account_axis_names / regen_meta / s_llm_invocations / s_task_contract / s_record_tags / s_account_axes / s_rthread_2br3）。**共有核が立たない軸は honest UNRESOLVED**（measure-first 不変）。

## 併記: prompt 衛生 FINDING が standing rule に
- 本作業中に判明した「reasoning LLM の token 発散＝prompt 衛生の欠陥」を Taka 指示で FINDING 化（同型2度目）→ **MGR が standing design rule として受理・institutionalize**（`CC_MGR_..._PROMPT_HYGIENE_STANDING_RULE_HANDOFF.md`）。将来 :8005 経路が増えたら共有 preprocessing util 化が望ましい（今は不要＝naming 優先）。

## ハンドオフ
- 次: 設計独立再監査（両軸 name・consensus 決定論再判定・幾何 byte 不変・consolidated_tokens 記録・LLM 非再実行）→ commit=Taka（命名 stage + ACCOUNT_AXIS_NAMES + meta fold を1コミット群）→ DE 起票。
- **これで両軸 name 確定＝帳簿「見つける層」完成に到達**。→ front door 復帰の区切り候補（Taka 保持事項）。

---
*実装(IMPL)。LLM 再呼出なし・記録 proposals を決定論 consolidation・幾何不変・共有核なしは honest UNRESOLVED。★3 本線＝これ自体。*
