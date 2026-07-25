# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 勘定科目の命名（2b-2）BUILT・★3本線

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / model=Qwen3.6-35B-A3B(:8005)・**初の実 CALL_SITE**
- 対応: `CC_DESIGN_2026-07-25_ACCOUNT_AXIS_NAMING_2b2_HANDOFF.md`（LLM 3-seed consensus・id正典/name装飾/幾何不変）

## 成果物（working tree・未commit）
- `structure/s_account_axis_names.py`（決定論サンプリング + :8005 3-seed consensus + provenance + `--check`）
- `structure/ACCOUNT_AXIS_NAMES.jsonl`（別 versioned 台帳・sole-writer=本 stage。v2 に name を足さない＝frozen 不変）
- meta fold（regen_meta）: LLM_INVOCATIONS(実 CALL_SITE 登録) / TASK_CONTRACTS / READ_PATHS

## 命名結果（§7 明記・DESIGN/MGR が妥当性判断）
| axis_id | name | status | 3-seed proposals |
|---|---|---|---|
| AX-72ead44e | **「Pythonモジュール実装」** | CONSENSUS(2/3) | Pythonモジュール新規作成 / Pythonモジュール実装 / Pythonモジュール実装 |
| AX2-48354b9a | **UNRESOLVED_NO_CONSENSUS**（name=null） | 1/3 | JSONLファイル解析CLI / JSONLファイル解析CLI作成 / JSONLファイル統計解析 |

- AX-72ead44e（patch_bridge 実装依頼の反復・114 REQUEST）は 2/3 一致で命名成立。
- AX2-48354b9a（JSONL 系データ処理 CLI・28件）は **3 seed が主題は一致（JSONL 解析）だが正規化厳密一致 <2/3** → **measure-first で正直に null**（捏造しない）。※観察: consensus 判定が「正規化後の完全一致 ≥2/3」ゆえ、意味が同じでも語尾揺れ（"CLI"/"CLI作成"/"統計解析"）で未成立。緩めるかは DESIGN 判断（私は spec §3 通り厳密実装・独断で緩めない）。

## ★ Taka のコーチングで根因是正（prompt 品質）
初回 thinking が **AX-72ead44e で 8192 tok でも終端せず発散**。Taka 指摘「qwen への指示が曖昧＝どんな指示か確認せよ」で実プロンプトを確認 → 原因判明:
- 全12サンプルが **gen-nonce ハッシュ以外バイト同一**（repeated_fixture の patch_bridge 反復）+ **"Your module MUST" で途中切断** ＝ノイズ+12重複+不完全文で reasoning が発散。
- **修正**: `_clean()`（`# gen-nonce` 行除去 + 空白正規化 + CLIP=220）+ **重複除去**して代表 content を bullet 提示。→ **thinking が ~3083 tok で正常終端**（モードでなく prompt が原因だった）。budget は観測に余裕をみて MAX_TOKENS=6144、truncation は握り潰さず明示エラー（空名を作らない）。

## 検証（§6 ゲート・record-occurrence 型）
- **幾何不変（最重要）GREEN**: `ACCOUNT_AXES_v2.json`/`ACCOUNT_MEMBERSHIP_v2.jsonl` が命名生成時から byte 不変（header に sha256 記録・--check で再計算照合）。命名は別台帳＝v2 を触らない。
- **サンプル決定論**: sample_element_ids が固定 K=12・margin_over_null 降順/element_id 昇順で再現（LLM 不使用で検証）。
- **consensus 記録再判定**: 記録 proposals に ≥2/3 規則を再適用 → name/status/agreement 一致（**LLM を再実行せず**）。
- **provenance 完全性**: model/endpoint/seeds/temperature/max_tokens/proposals/agreement/sample_ids/prompt_id 全記録。UNRESOLVED は name=null。
- ※ LLM 出力は非決定論ゆえ **name テキストの byte 再現は要求しない**（naming=record-occurrence 型・spec §6）。
- 全 gate GREEN（s_account_axis_names 含む10 stage）。

## LLM_INVOCATIONS（初の実 :8005 CALL_SITE）
- `s_account_axis_names.py:_llm_propose` が `record_class=CALL_SITE`・`endpoint=:8005`・`model=Qwen3.6-35B-A3B`・`gate_ref=USE_VLLM_INFERENCE`・`status=GATED`・`failure_handling=UNRESOLVED` として登録。DE-0536 の hook/regen_meta が commit 境界で fold（手動不要）。

## ハンドオフ
- 次: 設計/監査 独立再監査（幾何 byte 不変 / サンプル決定論 / consensus 記録再判定 / provenance 完全 / UNRESOLVED 正直 null）。
- **命名妥当性の判断**（"Pythonモジュール実装" が本物の話題名か・AX2 の UNRESOLVED を受容するか / consensus 厳密性を緩めるか）→ 必要なら MGR 経由で最小 set を Taka へ。
- commit=Taka → DE。想定と実測: 1/2 命名成立・1 UNRESOLVED（measure-first・捏造ゼロ）を silently 合わせず記録。

---
*実装(IMPL)。id正典/name装飾/幾何不変を厳守。prompt 発散は Taka コーチングで根因(曖昧prompt)是正。★3 本線＝これ自体。*
