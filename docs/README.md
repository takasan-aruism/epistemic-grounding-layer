# EGL 設計書 SoR(docs/)

本ディレクトリは EGL の**設計書の正本置き場**。コード(`egl/`)と Run Ledger が実装の SoR であるのと対に、
設計判断の SoR はここに置く。`DESIGN_EVIDENCE_LEDGER.jsonl` / `REVIEW.md` はここの文書を根拠参照する。

## 文書マニフェスト(有効セット)
| ファイル | 内容 | 状態 |
|---|---|---|
| `initial-spec-v0.1.md` | 親文書(初期設計仕様)。責任分界・親原則 | ⛔ **PENDING**(Taka 提供) |
| `grounding-layer-unified-v0.2.md` | 統合設計書 v0.2 (Final)。v0.1 を SUPERSEDE | ⛔ **PENDING**(Taka 提供 or 依頼で再構成) |
| `amendment-v0.2.1.md` | Amendment(AM-1..) codegen-audit 実験由来 | ⛔ **PENDING**(Taka 提供) |
| `amendment-v0.2.2.md` | Amendment(AM-10..20)。GPT監査由来。RR-4' 凍結等 | ⛔ **PENDING**(Taka 提供 or 依頼で再構成) |
| `kickoff-decision-record.md` | Walking Skeleton (Phase 1a) 着手決定 | ✅ 収録済み |
| `PROJECT_GOAL.md` | 本線(2DER AUTONOMOUS RESEARCH LOOP v0)・ループ現在地・目的ドリフト記録。**一次資料からの再構成であり親文書の代替ではない** | 🟡 RECONSTRUCTED (Taka 未裁定) |

有効文書セット: v0.1 + v0.2 + v0.2.1 + v0.2.2 + Kickoff
(v0.2.1 RR-4'(a) 自動縮小は v0.2.2 SN-4 で凍結)

## 受け渡し方法
Taka は本番機に SSH で入れるので、原本を直接ここへ置く:
```
scp initial-spec-v0.1.md amendment-v0.2.1.md ... takasan@server:/home/takasan/egl/docs/
```
または SSH セッションでエディタ/heredoc で直接作成 → git add。
私(Claude Code)はローカルパスを Read できるので、置いてくれれば読める。

## PENDING の2択
- **推奨**: Taka が原本(v0.1 / v0.2 / v0.2.1 / v0.2.2)を scp = ゼロドリフト
- **代替**: v0.2 / v0.2.2 / Kickoff は Claude 側にチャット verbatim があるので、依頼あれば再構成書き出し(要・原本照合)。v0.1 / v0.2.1 は Claude 未保持=Taka 提供必須
