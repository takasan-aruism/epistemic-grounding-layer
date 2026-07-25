# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 意図調べ arm-C2（定義+例 / think比較 / 多数決+abstain）BUILT

- 宛: AUDIT（→ DESIGN → MGR/Taka）
- 発: 実装(IMPL) / 2026-07-26 / model=Qwen3.6-35B-A3B(:8005)
- 対応: `..._ARMC2_DEFS_EXAMPLES_THINK_HANDOFF`（Taka 直接指示: 定義+例 / think有無 / 多数決+abstain）
- **能力測定・measure-first（0.88 を過大主張しない・LLM 非決定論ゆえ run 毎に±）。**

## 成果物（working tree・未commit）
- `structure/s_intent_probe_armc2.py`（二択+定義例・unsure許容・think OFF/ON・seed多数決・弁別は決定論集計のまま）+ `INTENT_PROBE_ARMC2.jsonl`
- meta fold（:8005 CALL_SITE 登録・TASK_CONTRACTS・READ_PATHS）

## ★ 決定的な結果（全アーム比較）
| アーム | 構成 | 戦略一致 | 発散 | 速度 |
|---|---|---|---|---|
| A 単発 think OFF | メニュー丸ごと | ~0.50 | 0 | 中 |
| B 単発 think ON | メニュー丸ごと | 0.54 | 0 | 遅 |
| C 二択並列（定義なし） | 二択+決定論集計 | 0.58 | 0 | 速11s |
| **C2 二択+定義例 think OFF** | **二択+定義+具体例+決定論集計** | **0.88(7/8)** | **0** | **速6.9s** |
| C2 二択+定義例 think ON | 同上・think ON(budget4096) | single0.75 / majority0.88 | 0 | 遅104s |

### 3つの明快な発見（Taka 指示の検証）
1. **「定義+具体例」が最大のレバー**: 素の二択 0.58 → **定義例で 0.88**（+0.30）。few-shot 定義で弱2二択（probe_type/multi_type 的中 3/4）が締まり、単発 A/B/C が **systematic に失っていた F3 CONTEXT_RESOLVE・F5 BMV・F7 PREMISE_PROBE を全て回復**。残 miss は F4 CHOICE（最もラベル論争的な1件）のみ。
2. **think は不要（むしろ不利）**: 定義例あり同条件で **think OFF single 0.88 > think ON single 0.75**。ON は **abstain 16%増・15倍遅（104s vs 6.9s）**で OFF を超えない。多数決で ON は 0.88 に回復するが、**OFF は単発で既に 0.88**。＝thinking は複雑判断の松葉杖で、**二択に削いで良いメニューを渡せば thinking 不要**（Taka 核心の実証）。
3. **多数決 / abstain**: 多数決は noisy な think-ON を救う安全網（OFF には不要＝既に安定）。abstain(unsure)は OFF でほぼ0＝定義例で LLM が弁別できている（決められない次元だけ正直に UNRESOLVED_AGG に落とす機構は保持）。

## 総合評価（正直に）
- **2DER の核「良いメニュー（構造+定義+例）を渡せば 3B でも矛盾しない選択」を決定的に支持**。二択分解 + 定義例 + 決定論集計 + think OFF で、Qwen3.6-A3B が意図調べ **7/8・発散ゼロ・6.9秒**。
- 弁別（近縁戦略）は **LLM でなく決定論集計 + 二択の定義**が持つ＝「判断=LLM(粗い二択)/構造=機械」の分割が効く（[[llm_arithmetic_drift_tolerant_design]]）。
- 留保: 単一 fixture セット(8)・LLM 非決定論ゆえ 0.88 は run 毎に±。F4 CHOICE の弁別（needs_probe/CHOICE-vs-BMV）は依然難所。**"解けた"でなく"良いメニュー方式が有望"**。

## 次の設計提案（IMPL 入力・DESIGN 判断）
- 既定方式 = **二択+定義例+think OFF+単発**（最高精度・最速・最安）。多数決は本番の安全網として option。
- F4 CHOICE を締めるなら `b_needs_probe` の定義に「open-ended だが対象は明確→probe 不要」を足す。fixture 拡充（各戦略を複数）で 0.88 の頑健性を測る。

## 検証（全 gate GREEN）
- `s_intent_probe_armc2.py --check` GREEN: 記録二択に parser・多数決・集計ツリーを決定論再適用→集計一致（LLM 非再実行）・provenance 完全（think/max_tokens/completion_tokens/並列/wall/choice）。
- :8005 CALL_SITE 登録（meta fold）。全 gate GREEN。

## ハンドオフ
- 次: 設計/監査 独立再監査 → 結果を MGR/Taka へ（**定義例で 0.58→0.88・think 不要・二択方式が核**）→ commit=Taka。
- DE 記録は front door(`record_de`)＋`generated_by_principal/claiming_principal=CLAUDE_CODE`・`generation_mode=DIRECT` 明示（内部アクター開示・DE-0541 失念の再発防止）。

---
*実装(IMPL)。定義+例が最大レバー(0.58→0.88)・think 不要・弁別は決定論集計・measure-first。★3 本線・止めない。*
