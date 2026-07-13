# 2DER Interface Transfer / Claude-Code Off-ramp — 親 spec v1

> 目的: いま Claude Code(私)が独占している 4 窓口 — **報告・承認/相談・git・実装** — を 2DER 側の UI + ゲート付き
> 自律機構へ移し、Claude を実質アドバイザー(hard judgment の相談役)にする。Taka 承認済み(2026-07-14)。本 spec は
> 登録・分解のみ。実装前に停止。**「UI ができた / sandbox で一回動いた / 設計が完成した」を Claude 依存除去と誤認
> する経路を塞ぐ**ことが最重要制約。

## 0. 誤認防止の基本原則（Taka 5 点必須追記を内包）
1. **Claude Code 実装依存除去フラグは変更クラス別**。単一共通フラグにしない。CLASS-T/S/M を分離。各フラグは、その
   クラスで `requirement → RRI decomposition → task packet → local worker impl → shell/test → independent judgment →
   EGL evidence chain → commit proposal` が **Claude Code なしで一周した場合のみ**成立。**CLASS-S の sandbox 成功を
   全クラスへ一般化しない**。CLASS-H/N は「実装 worker 依存除去(将来評価可)」と「異種重み L2 監査依存(除去対象外、
   適格な異種 weight 裁定者 pool への依存として表現)」を明確分離。
2. **CURRENT STATE は証拠付き**。「かなり実装/ほぼ完成/準備済み」等の曖昧語禁止。各 capability を VERIFIED /
   PARTIAL / REGISTERED_ONLY / NOT_IMPLEMENTED / UNKNOWN で分類し acceptance_test_ids / jrev_ids / artifact_ids /
   known_gap / claude_code_currently_substitutes を付す。VERIFIED は受入試験 or JREV 参照がある場合のみ(Claude の
   説明だけを根拠にしない)。→ 別 doc CURRENT_STATE_v1.md。
3. **LIVE_WORKER_MINIMAL_PASS は counter-factual gate**。Claude Code セッションが閉じている状態でのみ成立。§7 参照。
4. **Live Worker security 境界**を必須要件に。§6 参照。
5. **Qwen model test 依存を明示**。最小 live worker 縦切りは default A3B で進めてよい(MODEL_ROUTING_READY=false →
   default=A3B)。QWEN27 未完を最小縦切りの blocker にしない。ただし最終的な実装依存除去フラグの前提には
   QWEN27_BENCHMARK_COMPLETE / MODEL_SELECTION_TEST_PASS / MODEL_ROUTING_READY / CODING_QUALITY_ACCEPTANCE_PASS を課す。

## 1. A〜F workstream 分解
- **A. CONTROL-SURFACE-READ (read-only)** — Taka が私の要約を介さず状況/forecast/roadmap/intervention を直接読む面。
  既存 webui.py read-only view の上に off-ramp 報告面を足す。flag: `CONTROL_SURFACE_READ_ONLY_READY`。
- **B. COMMAND-SURFACE** — 保留 REQUIRES_APPROVAL キュー + Taka が私を介さず scoped single-use token を発行 + intake。
  authority.py + webui submit の上。flag: `COMMAND_SURFACE_READY`。
- **C. AUTONOMOUS-GIT (design only)** — 台帳/registry 変更のゲート付き自律 commit の**設計 + policy 提案**。現在
  memory 上 commit=Taka / 自律RD未有効。有効化は Taka 判断。本 workstream は設計止まり。
- **D. LIVE-WORKER-RUNTIME** — sandbox + local worker が router 統治下で実装/shell/test を実行。既存 dw.executor
  (実 subprocess + security) / dw.dispatch を土台に。security 境界 §6。flag: `LIVE_WORKER_MINIMAL_PASS`(counterfactual)。
- **E. COUNTERFACTUAL-ACCEPTANCE** — §7 の counter-factual gate + run metadata(Claude 不在の証跡) + 最小縦切りの
  受入 harness。
- **F. DEPENDENCY-FLAG-REGISTRY** — §8 のフラグ集合 + binding + §9 依存グラフ + Qwen benchmark 依存固定。

## 2. 依存除去フラグの変更クラス別定義（Taka 追記 1）
`CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_T / _CLASS_S / _CLASS_M` を別管理。成立条件 = そのクラスで上記一周が Claude なしで
回ること。各フラグに scope / change_class / 受入試験 ID を binding。
- **CLASS-T**(typo/format/comment/behavior不変): 最初に評価可能。
- **CLASS-S**(単一module/rollback容易/外部interface不変/既存pattern): CLASS-T + CODING_QUALITY_ACCEPTANCE_PASS +
  MODEL_ROUTING_READY を要する。**CLASS-S の sandbox 成功を CLASS-M/H へ一般化しない**。
- **CLASS-M**(通常機能追加): CLASS-S + 広範な受入。
- **CLASS-H / CLASS-N**: 実装 worker 依存除去は将来評価可能。**異種重み L2 監査依存は除去対象外** →
  `HETEROGENEOUS_L2_AUDITOR_AVAILABLE`(適格な異種 weight 裁定者 pool)への依存として表現。Claude 固定ではない。
  (根拠: weight_independence_policy — 同一重み監査は完全独立でない。)

## 3. read-only UI 最小 slice 受入条件（workstream A）
`CONTROL_SURFACE_READ_ONLY_READY` 成立条件:
- Taka が UI 単独で以下を私の中継なしに読める: roadmap 状態(PROPOSED..DONE 集計) / FOUNDATION-FORECAST-REPORT の
  残工程+想定セッション(UNKNOWN-VARIANCE 込み) / 直近 DE/CHG / intervention(HUMAN-ESCALATION-LEDGER)集計 /
  完成フラグ状態(COMPLETION-FLAG-GATE 評価、CDEF-2DER-v1 が未完成であることを含む)。
- read-only(状態を変更しない)。auth 必須。
- 受入試験: UI エンドポイントが台帳から算出した値を返し、値が台帳 ID に解決できること(捏造でない)。
- **これが成立しても実装依存除去ではない**(報告窓口の移譲のみ)。

## 4. live worker 最小縦切り 受入条件（workstream D/E）
`LIVE_WORKER_MINIMAL_PASS`(§7 counter-factual):
`task packet 投入 → local worker が workspace 準備 → 1ファイル変更 → deterministic test → 独立 Judge 裁定 →
EGL evidence chain → commit proposal 生成` が **Claude Code 不在で**一周。default A3B で可(QWEN27 不要、Taka 追記 5)。
sandbox 初期は **commit proposal 止まり**(人間 approve なし commit 禁止、§6)。

## 5. 何を宣言してよく、何を宣言してはいけないか
- read-only UI 成立 → **報告窓口の一部移譲**。実装依存除去ではない。
- live worker 縦切り成立 → **architecture と縦切りが動いた**。`LIVE_WORKER_MINIMAL_PASS ≠
  CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_S/M`(§9 依存グラフで明示)。実用品質の実装依存除去は別。
- CLASS-T/S/M 依存除去 → そのクラスに限り、受入試験 ID + counterfactual run で裏付いた場合のみ。

## 6. Live Worker security 境界（Taka 追記 4）
**Sandbox 境界**: workspace isolation / resource cap / execution timeout / process kill+cleanup / host filesystem 非到達 /
production credential 非到達 / secrets 非到達 / network egress default-deny + 必要通信のみ明示 allowlist / GPU 割当上限 /
disk 使用量上限。(既存 dw.executor の shell=False + metachar 遮断 + blocklist + timeout を土台に、workspace/network/
secrets 隔離を追加。)
**Untrusted input 規則**: worker が読む repo 文書 / source comment / README / issue text / test output / log / fixture /
generated artifact / external response は **すべて data であり instruction ではない**。それらに含まれる命令文を system
instruction / task 変更指示として採用してはならない(prompt injection 防御)。
**Judge 裁定対象**: test PASS だけでなく `task requirement ↔ produced diff ↔ allowed file scope ↔ interface contract ↔
deterministic test result` を裁定。
**独立 failure class**: 悪性/scope 外 diff / secrets 参照 / network 逸脱 / 許可外ファイル変更。sandbox 初期は全て
commit proposal 止まり、人間 approve なし commit 禁止。

## 7. Counter-factual gate（Taka 追記 3）
`LIVE_WORKER_MINIMAL_PASS` は **Claude Code が実行・誘導・観測している状態では成立しない**。成立の唯一条件:
Claude Code セッションを閉じる → script/control surface から task packet 投入 → local worker が workspace 準備 →
1ファイル変更 → deterministic test → 独立 Judge 裁定 → EGL evidence chain → commit proposal。
この一周で Claude Code が (task 手入力 / shell 実行 / failure recovery / test 結果解釈 / Judge 代行 / commit proposal 生成)
の形で介在してはならない。Claude Code は試験終了後に保存済み artifact を監査できるが、それは**フラグ成立経路の外側**。
受入試験は counter-factual として **Claude Code プロセス/セッションが存在しないことを示す run metadata** を保存する。

## 8. フラグ集合（Taka 追記 5、別管理）→ OFFRAMP_FLAGS_v1.json
`CONTROL_SURFACE_READ_ONLY_READY / COMMAND_SURFACE_READY / LIVE_WORKER_MINIMAL_PASS / MODEL_ROUTING_READY /
CODING_QUALITY_ACCEPTANCE_PASS / CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_T / _CLASS_S / _CLASS_M /
HETEROGENEOUS_L2_AUDITOR_AVAILABLE`。各フラグ必須フィールド: flag_id / scope / change_class /
completion_definition_version / acceptance_test_ids / run_ids / jrev_ids / artifact_ids / counterfactual_conditions /
approved_by / created_at。全フラグ現在 **UNMET**。

## 9. 依存グラフ（Taka 追記 5）
```
CONTROL_SURFACE_READ_ONLY_READY   (A, 独立)
COMMAND_SURFACE_READY             <- CONTROL_SURFACE_READ_ONLY_READY + authority scoped-token
LIVE_WORKER_MINIMAL_PASS          <- LIVE-WORKER-RUNTIME sandbox(D) + counterfactual(E) + default A3B
                                     [QWEN27 benchmark に依存しない]
MODEL_ROUTING_READY               <- QWEN35_BENCHMARK + QWEN27_BENCHMARK_COMPLETE + MODEL_SELECTION_TEST_PASS
CODING_QUALITY_ACCEPTANCE_PASS    <- live worker 出力の coding 品質受入試験
CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_T <- LIVE_WORKER_MINIMAL_PASS + CLASS-T counterfactual + 受入試験ID
CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_S <- CLASS_T + CODING_QUALITY_ACCEPTANCE_PASS + MODEL_ROUTING_READY + sandbox security
CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_M <- CLASS_S + 広範受入
HETEROGENEOUS_L2_AUDITOR_AVAILABLE (CLASS-H/N 用の独立 enabler; Claude 除去でなく異種weight pool)

明示不等式: LIVE_WORKER_MINIMAL_PASS ≠ CLAUDE_CODE_IMPL_DEP_REMOVED_CLASS_S/M
明示: CLASS-H/N の heterogeneous L2 audit dependency は除去対象外(HETEROGENEOUS_L2_AUDITOR_AVAILABLE への依存)
```

## 10. Qwen benchmark 依存固定（Taka 追記 5）
最小 live worker 縦切り = 現行 default A3B で進行(MODEL_ROUTING_READY=false → default=A3B)。QWEN27 benchmark 未完了を
`LIVE_WORKER_MINIMAL_PASS` / 1ファイル変更 / deterministic test / Judge / EGL / commit proposal 縦切りの blocker に
しない。一方 `QWEN27_BENCHMARK_COMPLETE / MODEL_SELECTION_TEST_PASS / MODEL_ROUTING_READY /
CODING_QUALITY_ACCEPTANCE_PASS` は最終的な実装依存除去フラグの必須前提。architecture と縦切りが動いただけで実用品質の
実装依存除去を宣言しない。

## 11. 今回の実施範囲(登録・分解のみ、実装前に停止)
親 spec 登録 / CURRENT STATE 証拠付き棚卸し / gap analysis / A〜F 分解 / 依存グラフ / security 境界定義 /
read-only UI 最小 slice 受入条件 / live worker 最小縦切り受入条件 / counter-factual gate 定義 /
change class 別依存除去フラグ定義 / Qwen benchmark 依存固定 / ROADMAP・DE・CHG・artifact binding / **実装前に停止**。
