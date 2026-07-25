# CC 管理(MGR) → 設計/監査(CC-α): LLM_INVOCATIONS RED を commit 跨ぎで残すな（HANDOFF）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-25 / TYPE=HANDOFF
- 事象: DE-0535 commit 後も `structure/s_llm_invocations.py --check` = **RED**（`s_record_tags.py` の MENTION_ONLY 呼出点が未登録）。

## 依頼
1. **即時**: LLM_INVOCATIONS を再生成→登録し `--check` GREEN 化 → DE 起票（DE-0523/0530 と同型の機械的 fold）。
2. **再発防止（本題）**: これは **5回目の同型**（新 structure/ script を足すたび LLM_INVOCATIONS が RED→手動 fold）。commit 境界を跨いで gate RED が残るのは integrity 上よくない。**LLM_INVOCATIONS 再生成を "structure/ script を追加/変更する commit の routine" に織り込む**（生成器を回してから commit、or pre-commit 相当の self-heal）。設計判断で最小実装を。

## 注意（過剰反応しない）
- s_record_tags.py は**決定論**（LLM 不使用）。RED の実体は "marker 文字列を含むだけの MENTION_ONLY 増分"。真の新規 CALL_SITE ではない。**ゲート自体は正しく検出している**ので、ゲートを緩めるのでなく **fold を自動化する**方向で。
- 本件は P2。★3 本線・帳簿完成は止めない。commit=Taka。
