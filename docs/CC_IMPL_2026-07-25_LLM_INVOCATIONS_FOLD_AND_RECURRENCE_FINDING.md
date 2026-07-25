# 実装(IMPL) → 監査(AUDIT): LLM_INVOCATIONS 即時 fold 完了 + 再発防止の提案（FINDING）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論
- 契機: `CC_MGR_2026-07-25_LLM_INVOCATIONS_RED_RECURRENCE_HANDOFF.md`（宛 DESIGN/AUDIT）

## part 1（即時 fold）= 完了（working tree・未commit）
- committed(DE-0535)=231行・`s_record_tags` 未登録＝RED を確認。**working tree で再生成 → 232行・GREEN**（`s_record_tags` を MENTION_ONLY として fold）。
- `s_record_tags` が MENTION_ONLY なのは docstring の `:8005/GPU 不使用` 言及が起点＝**真の CALL_SITE でなくゲートが正しく検出**（MGR 注記どおり）。ゲートは緩めていません。
- これは私の RECORD_TAGS 成果の loose end でした（新 structure/ script 追加時の LLM_INVOCATIONS 再生成ルーチンを s_task_contract/s_rthread では実施したが今回漏らした）。自分の未完部分として fold。commit=Taka で確定。

## part 2（再発防止）への提案（設計判断は DESIGN・以下は IMPL からの入力）
### 根因の一般化
これは LLM_INVOCATIONS 固有でなく、**「他の structure/ script 集合を列挙/走査する meta 派生台帳」全般**の問題です。同型で **`TASK_CONTRACTS`（s_task_contract が全 s-stage を列挙）も新 script 追加で毎回 RED→手動 regen**（本セッションで2回実施）。∴ 対象は少なくとも LLM_INVOCATIONS + TASK_CONTRACTS。

### 最小案（推奨・ゲートを緩めず fold を自動化）
- **`structure/regen_meta.py`（or Makefile ターゲット）**: 「structure/ script 集合に依存する meta 派生」= s_llm_invocations / s_task_contract を**依存順で regen する単一エントリ**。structure/ に script を追加/変更する commit の前に1回回す（人手 or pre-commit 相当）。
  - 決定論ゆえ no-op なら差分ゼロ（安全に何度でも）。
  - 「どれが meta か」は明示リスト（増えたら1行追記）＝ un-accounted 化しない。
- 代替: 各 meta 生成器に `--check` が RED の時だけ「STALE: 新 script 未 fold」と**具体名を出す**（現状の REGEN_MISMATCH より原因が一目瞭然＝手動 fold の摩擦を下げる）。自動化でなく可視化案。
- **避けるべき**: 全 structure/ 生成器を無差別に pre-commit で回す（e5 埋め込み等 GPU/HF 依存の重い stage を巻き込む）。**meta 派生（AST 走査のみ・軽量）に限定**するのが要点。

## 依頼
- part 1 fold は commit=Taka で確定。part 2 の機構（regen_meta 単一エントリ / 可視化 / その他）を DESIGN が裁定 → handoff くれれば IMPL が最小実装します。
- 想定と実測: fold は完了、再発は meta 派生一般の問題（TASK_CONTRACTS も同型）と一般化して報告。

---
*実装(IMPL)。ゲートは緩めず fold を自動化する方向で提案。★3 本線は止めていません。*
