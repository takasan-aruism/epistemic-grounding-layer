# Phase 0 現状監査 — 役割兼務状況 (2026-07-13, ITEM-2DER-PARALLEL-OPS)

仕様書 §12 Phase 0 / §11 / AC-14 に基づく。**現状、単一の Claude Code セッションがほぼ全役割を兼務している**ことを明示する。
これは仕様書が是正しようとしている当の状態であり、直近の ITEM-0015 失敗（自分の実験を自分で判定→誤結論、外部指摘で撤回）の構造的原因でもある。

| 役割 | 現在の担当 | Claude兼務? | 分離の現状 |
|---|---|---|---|
| 受付 intake | Claude Code (Taka メッセージを読む) | **兼務** | 未分離 |
| 調査 research | Claude Code | **兼務** | 未分離（RRI-RESEARCH 未起動） |
| 計画 plan | Claude Code | **兼務** | 未分離（RRI-PLAN 未起動） |
| 計画監査 plan-audit | Claude Code (自己) + Taka (外部) | **兼務** | Claude 自己監査 = 独立性なし。実効監査は Taka |
| ID発行 | Python registry (roadmap/artifact/de、決定的) | 部分 | **分離済**（Claude が invoke、番号は決定的処理） |
| 実施 execution | Claude Code (bash/script) + live Qwen worker/auditor(seed分離) | **兼務** | DW 機械オペのみ別 actor、それ以外は Claude |
| 判定 judgment | Claude Code (自己) | **兼務** | **未分離＝最大の穴**（実施者が判定）。独立 Judge 不在 |
| EGL記録 | egl.de_admission (sole writer) | 部分 | **分離済**（Claude が invoke、書込は admission fn 独占） |
| CHG記録 | artifact_registry.record_change | 部分 | **分離済**（決定的） |
| 状態更新 | Claude (roadmap set_status) | **兼務** | 未分離 |
| commit | Claude (git、Taka 承認時) | **兼務** | 承認は Taka |
| rollback | Claude | **兼務** | 未分離 |

## 分離済み / 未分離のまとめ
- **分離済み（機構）**: ID発行・EGL admission・CHG記録（決定的 Python、sole-writer）、DW 機械オペ（Qwen worker≠auditor、seed分離）、人間承認（Taka）、外部是正（Taka）。
- **未分離（＝Claude 単一セッション兼務）**: 受付・調査・計画・計画監査・（Claude 主体の）実施・**判定**・状態更新・commit・rollback。
- **最大の構造的穴 = 判定の非独立**（AC-08 未達）。実施した Claude context が自分の結果を判定 → ITEM-0015 で誤結論を系が止められず、Taka の外部指摘を要した（DE-0241 に記録済み）。

## 次工程で分離すべき役割（優先順）
1. **判定 (INDEPENDENT JUDGE)** — 実施 context と別 context/別 task ID/別 output schema。AC-08。最優先。
2. **計画監査 (RRI-PLAN-AUDIT)** — 計画作成と別 worker。
3. **調査/計画 (RRI-RESEARCH / RRI-PLAN)** — 受付・実施から分離、複数並列。
4. **受付・状態更新 (DS)** — 実施・判定から分離。

## 移行期の兼務記録
本 slice の実施主体は単一 Claude Code セッションであり、上表の「兼務」列が現状。仕様完成までの移行期は、各役割を別 task/別 context/別 artifact に分けた場合はその都度 EGL 記録する（AC-14）。本監査自体が最初の兼務記録。
