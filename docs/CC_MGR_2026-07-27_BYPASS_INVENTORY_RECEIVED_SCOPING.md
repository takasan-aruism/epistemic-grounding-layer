# CC 管理(MGR): 直叩き棚卸しを受領 — **閉塞の順序は「書き」から**（HANDOFF・短く）

- `BUILD_ROLE: 参照` / 宛: DESIGN/AUDIT(CC-α) / 写: IMPL / Taka / 発: MGR / 2026-07-27 02:55 / TYPE=HANDOFF
- 対象: `CC_IMPL_2026-07-27_FRONT_DOOR_BYPASS_INVENTORY_STATUS.md`（未監査）

## 1. 受領
- **LIVE な直叩き 20 箇所**（`de_admission` 2 / `dw.workcell` 18）。**判定できない 10 箇所は `UNKNOWN` のまま**＝推測で埋めていない。**正しい。**
- **IMPL が自分の計器の欠陥（status を symbol 単位で出していて設問に答えていなかった）を自分で見つけ、初版を採用せず作り直した。** 受領する。
- **棚卸しのみで閉塞の提案をしなかったのは指示どおり。**

## 2. ★MGR の scoping（DESIGN が裁定すること・私は決めない）
IMPL が付けた **読み／書きの別**が効く。**「侵入」として問題なのは書きである**——読みは front door を通らなくても記録を汚さない。

**提案（DESIGN 裁定を求む）: 閉塞の第一対象を「書き」5箇所に絞る。**
| file:line | callee |
|---|---|
| `twoder/live_worker_runtime.py:140` | `admit_design_evidence` |
| `twoder/runtime_supervisor.py:218` | `admit_design_evidence` |
| `twoder/webui.py:315` | `record_plan` |
| `twoder/build_planner.py:301` | `record_plan` |
| `twoder/experiment_candidate.py:116` | `create_task` |

- **読み 15箇所は後回し**（閉じる理由が弱いなら**閉じないと決めてよい**。**「全部塞ぐ」を目的にしない**）。
- **`UNKNOWN` 10箇所は `UNKNOWN` のまま扱う。** 判定材料が無いまま分類しない。
- **既存資産を作り直さない**（`twoder/submit.py` は既にある）。

## 3. 順番
1. **Build 4 の監査（D-5）が先。** それが出るまで閉塞に着手しない。
2. **DESIGN は §2 の裁定だけ先に出してよい**（設計判断のみ・実装しない）。
3. 閉塞の実装は **2DER 移行が本線になってから。**

---
*MGR。棚卸し受領（LIVE 直叩き 20・UNKNOWN 10 は埋めない・IMPL が自分の計器欠陥を見つけて作り直した）。scoping 提案=閉塞の第一対象は「書き」5箇所、読み15は後回しで閉じないと決めてよい（全部塞ぐを目的にしない）。裁定は DESIGN。着手は Build 4 の監査(D-5)の後。*
