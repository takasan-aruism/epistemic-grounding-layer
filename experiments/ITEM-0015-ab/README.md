# ITEM-2DER-EVO-0015 — coder-model live A/B (sleep/wake) evidence bundle

**この束は「誠実なループが回った成功例」ではない。** 実験計画の不備・誤判定・外部指摘による撤回・再実験での回復を
**分けて**記録するためのもの。生 evidence が一定期間 ID バックされていなかった事実も含めて残す。

## 失敗・回復のタイムライン（分類つき）

| # | フェーズ | 分類ラベル | DE |
|---|---|---|---|
| 1 | A/B 測定ハーネスが sleep level 2 + `/wake_up` のみ（`reload_weights` 無し）で設計された。level 2 は weights を破棄する仕様で、同一 weights 保持の swap には level 1 が正しい。 | **PROCEDURE_DESIGN_FAILURE** | (harness) |
| 2 | level-2 garbage を見て「sleep/wake は不採用 / GDN-hybrid の weight 復元バグ」と結論した。手順を検証せず既知 Issue との一致に寄せた。 | **PREMATURE_METHOD_REJECTION** | DE-0237 / DE-0238 |
| 3 | Taka が「level 2 は reload_weights が要る」「4 系統で切り分けよ」と指摘。**2DER 単独ではこの誤判定を停止できなかった**（DE の claim ceiling / gate は誤結論の DE-0237/0238 を admit した）。 | **EXTERNAL_CORRECTION_REQUIRED** | (Taka msg) |
| 4 | level-1 sleep/wake を実測 → 出力完全一致・正常。原因は **手順不備** と確定。誤結論を撤回。 | **RECOVERED_AFTER_ESCALATION** | DE-0239 |
| 5 | level-1 で A/B 再実測（実 Pass@1）。swap viable を実証。質は 3 タスク pilot（firm でない）。 | (recovery, MEASURED) | DE-0240 |

## 明示事項（要求どおり）
- **PROCEDURE_DESIGN_FAILURE**: 上記 #1。
- **PREMATURE_METHOD_REJECTION**: 上記 #2（DE-0237/0238 の含意）。
- **EXTERNAL_CORRECTION_REQUIRED**: 上記 #3。修正の起点は Taka であり系ではない。
- **RECOVERED_AFTER_ESCALATION**: 上記 #4-5。
- **2DER 単独では誤判定を停止できなかった**: DE admission は誤結論を通した。別視点（Taka）が要った。
- **生 evidence 未登録状態が存在していた**: DE-0237〜0240 は登録済みだったが、serve scripts と result JSON は 5 repo 外にあり path 参照のみ・ARTIFACT_ID 化されていなかった（本束で是正）。

## 収容物
- serve scripts: `serve_qwen36_ab_sleep.sh`(Qwen no-fp8-kv+sleep), `serve_qwen36_27b_ab_sleep.sh`(Coder), `serve_qwen36_nofp8_nosleep_iso.sh`(isolation)
- measurement scripts: `ab_measure.py`(level2, 失敗版), `ab_measure_l1.py`(level1), `ab_quality.py`(実 Pass@1), `live_0008.py`(先行の 0008 live harness)
- results: `result_ab_result.json`(0/3 garbage), `result_l1_result.json`(isolation), `result_ab_quality.json`(Pass@1)
- `KEY_LOGS.md`(verbatim 抜粋), `runtime_env.txt`, this `README.md`

## 結論（現時点）
- sleep/wake モデル切替は **level 1 で viable**（level 2 は不可 without reload_weights）。
- 35B-A3B vs 27B: 3 タスク pilot で 27B Pass@1=1.0 > 35B 0.667 だが 27B は 2.3x 遅く、**サンプル小・切替判断は firm でない**。bench「27B やや上」は弱く裏付け、未確定。
- **ITEM-0015 は IN_PROGRESS**。firm 化にはより大きな A/B が必要。production は fp8-kv/0.92/sleepなしで正常。
