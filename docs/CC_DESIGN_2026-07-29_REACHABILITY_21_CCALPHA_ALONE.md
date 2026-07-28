# 設計/監査 → MGR（写: Taka / IMPL）: **到達性21件 — CC-α 単独の判断（★独立検算ではない）**

- `BUILD_ROLE: 参照`（**判断の公開のみ。何も作っていない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8`）**

## 0. ★これは検算ではない（先に書く）
```
手順(MGR): ①CC-α は書かない → ②IMPL が独立に出す → ③その後 CC-α が出す
実際      : ★IMPL は出していない（D-49 の作業が続いたため）
私の側    : ★2026-07-28 に判断を書き終え、共有しない場所（scratchpad）に封をして保持した
```
> **∴ 私は手順を守った。** **★しかし相手が出していない以上「2者独立一致」は成立しない。**
> **∴ これは★CC-α 単独の判断である。** **検算として数えないこと。**
> **★IMPL が後から出すなら、私のものを読んだ後になる。** **∴ 一致しても弱い証拠である。**
> **★MGR「宙に浮かせない」に従い、閉じるために出す。**

---

## 1. ★封をした判断（2026-07-28 に書き終えた原文・1文字も変えていない）

作成: 2026-07-28 / 発: 設計/監査(CC-α)
★この時点で IMPL の到達性文書は1文字も読んでいない。
★判断基準: 「front door からの依頼処理（submit()／webui／機械の自動投入）から呼ばれるか」

## 実測（呼び手の import 行数・打ち切り無し）
```
counterfactual_runner  0    live_worker_runtime 4    runtime_supervisor 7
select_and_create      0    experiment_candidate 1   codegen_run_fn     0
de_submit_route        3(s_de_route_equiv のみ)      s_de_route_equiv   0
s_retention_repair_a   0    run_rri_task        0    run_esde_task      0
workflow               2(run_task.py / demo)
live_worker_runtime の呼び手: counterfactual_runner / run_oracle_guarded / webui:233 / webui:277
runtime_supervisor の呼び手: qwen_worker / dw.adapters / reference_oracle / build_planner×2 / webui:233
experiment_candidate の呼び手: submit.py:325（★acquisition 枝の中）
```

## 判断（21件）
| # | 場所 | 判断 | 根拠 |
|---|---|---|---|
| 1 | `ds/run_ds_benchmark.py:63` | **到達しない** | 呼び手0。単体ベンチマークスクリプト |
| 2 | `egl/docs/report/ai_work_system_loop_demo.py:116` | **到達しない** | デモ。呼び手0 |
| 3 | `egl/docs/evidence/select_and_create_v0.3_qwen_accepted.py:57` | **到達しない** | 証跡ファイル。呼び手0 |
| 4 | `egl/structure/de_submit_route.py:46` | **到達しない** | 呼び手は `s_de_route_equiv` のみ＝構造再構成の道具。依頼経路でない |
| 5 | `egl/structure/s_de_route_equiv.py:107` | **到達しない** | 呼び手0 |
| 6-9 | `egl/structure/s_retention_repair_a.py:41,43,45,48` | **到達しない**（4件） | 呼び手0。retention 補修の実験 |
| 10 | `dev-workcell/run_rri_task.py:167` | **到達しない** | 呼び手0。手動実行スクリプト |
| 11 | `dev-workcell/run_esde_task.py:167` | **到達しない** | 呼び手0。手動実行スクリプト |
| 12 | `twoder/counterfactual_runner.py:48` | **到達しない** | 呼び手0 |
| 13 | `twoder/live_worker_runtime.py:197` | **★到達する** | `webui.py:233,277` から import される＝webui 経路に在る。**機械が自分で submit する経路** |
| 14 | `twoder/tools/codegen_run_fn.py:70` | **到達しない** | 呼び手0 |
| 15 | `twoder/select_and_create.py:80` | **到達しない** | 呼び手0（モジュールを import する本番コードが無い） |
| 16 | `twoder/select_and_create.py:150` | **到達しない** | 同上。加えて同ファイル内の別 `create_task` |
| 17 | `twoder/submit.py:450` | **★到達する** | `submit()` 本体（段4 ROUTING） |
| 18 | `twoder/submit.py:503` | **★到達する** | CLI `__main__`＝入口そのもの |
| 19 | `twoder/experiment_candidate.py:116` | **★到達する** | `submit.py:325` の acquisition 枝から呼ばれる |
| 20 | `twoder/runtime_supervisor.py:222` | **★到達する** | `webui.py:233` / `qwen_worker` / `dw.adapters` / `build_planner` から import＝本番経路に在る |
| 21 | `twoder/webui.py:536` | **★到達する** | `/api/submit`＝入口そのもの |

## 集計
```
到達する   : 6  （live_worker_runtime / submit.py:450 / submit.py:503 / experiment_candidate / runtime_supervisor / webui:536）
到達しない : 15
```

## ★実行しなければ分からない件（推測で埋めない）
- **#13 と #20 は「import される」までしか確かめていない。** **実際にその行が走るかは、条件分岐（機械が自分で投入する条件）に依存する。**
  → **★「import 経路は在る。実際に走ったかは実行しなければ分からない」が正確である。**
- **#19 は `submit.py:325` が `gate["allowed"]` の中に在る。** **∴ gate が閉じていれば走らない。** **走ったかは実行しなければ分からない。**
- **#15/#16（`select_and_create`）は呼び手0 だが、`python3 -m` で直接起動される可能性を排除していない。**

## ★自己申告
- 本日、到達性で1回外している（`egl/core.append_event` を「到達しない」と誤判定）。**∴ 上の「到達しない」15件は、同じ誤り方をしうる。**
- **特に危ういのは #4（`de_submit_route`）** — `egl/structure` 配下だが、名前は「DE 投入経路」であり、**過去に本番投入に使われた可能性を私は排除していない。**

---
*CC-α。到達性21件の判断を公開する。★これは検算ではない——手順（CC-α は書かない→IMPL が独立に出す→その後 CC-α）に対し **IMPL は出しておらず**、私は 2026-07-28 に判断を書き終えて共有しない場所に封をして保持していた ∴ 手順は守ったが「2者独立一致」は成立せず、**CC-α 単独の判断**である（IMPL が後から出すなら私のものを読んだ後になるので一致しても弱い証拠）。MGR の「宙に浮かせない」に従い閉じるために出す。★判断=**到達する6件**（`live_worker_runtime:197`／`submit.py:450`／`submit.py:503`(CLI `__main__`)／`experiment_candidate:116`／`runtime_supervisor:222`／`webui:536`）／**到達しない15件**（ベンチマーク・デモ・証跡ファイル・`egl/structure` の道具4件・手動実行スクリプト2件・呼び手0の4件）。★推測で埋めなかった点=`live_worker_runtime` と `runtime_supervisor` は「import される」までしか確かめておらず**実際にその行が走るかは実行しなければ分からない**／`experiment_candidate` は `gate["allowed"]` の中に在るので gate が閉じていれば走らない／`select_and_create` は呼び手0だが `python3 -m` で直接起動される可能性を排除していない。★自己申告=**本日、到達性で1回外している**（`egl/core.append_event` を「到達しない」と誤判定し MGR が採って裁定を2回訂正した）∴ 上の「到達しない」15件は同じ誤り方をしうる。**特に危ういのは `de_submit_route`**——`egl/structure` 配下だが名前は「DE 投入経路」であり、過去に本番投入に使われた可能性を排除していない。*
