# 【A】実装 → 設計/監査: **★「書くか」で見ると、★61本が向き先を逃がしていません。★うち23本は台帳/登記簿のモジュールを import します（★書くとは言いません）**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-30 / TYPE=FINDING
- **運用方針 確認済（版: v2.8）**
- **契機**: `CC_MGR_2026-07-30_D109B_THREE_NOT_TWO_MY_PREDICATE_WAS_WRONG.md`（★判定基準を「HTTP」から「★書くか」へ）/ `CC_DESIGN_2026-07-30_D109_…WITHOUT_HTTP.md`（★`test_rri_formal.py`）
- **★1本も走らせていません。★harness を書き換えていません。★2本/3本を移していません。★台帳を直読していません。**
- **★ソースだけで確かめました**（★`exit 0` を根拠にしません・D-107 §1）。

## 0. ★私は判定しません。★母数を出します
> **★MGR が判定基準を「★書くか」に替えました。** **★その基準で、★まだ評価されていない範囲が在ります。**
> **★「3本で足りる」とも「足りない」とも書きません。** **★数と名前を出します。**

---

## 1. ★独立に同じ結論に着きました（★別の探し方で）
```
CC-α の探し方: ★実 submit() を呼ぶ本（★9本）→ ★逃がしていないのは ★test_rri_formal.py の1本
私の探し方  : ★書き込み口の呼び名 8種で探した
  submit( / append_event( / ingest( / register( / record_change( / _append_event( / open(…,"a") / write_text(
  → ★逃がしていない本の中で当たったのは ★test_rri_formal.py の1本（★同じ）
```
> **★別の探し方で同じ1本に着きました。** **★CC-α の指摘を、私も確かめられました。**

## 2. ★しかし母数が違います（★まだ誰も出していない数）
```
★総数                                   : ★98本
★向き先を逃がしている（EGL_DATA_DIR / DW_DATA_DIR / mkdtemp / TemporaryDirectory）: ★37本
★逃がしていない                          : ★61本
```
| **★∴** | **★「書くか」で見るべき対象は★61本 在ります**（★9本ではありません） |
|---|---|
| **★私が評価できたのは** | **★呼び名8種だけ**（§1）。**★これは「書く道」の全部ではありません** |
| **★∴ 私は「1本だけです」と書きません** | **★探した範囲がそれだけ、という意味です** |

> **★今日 私は同じ形で2回 転びました**（★`8770` だけ探した／★ネットワークだけ見た）。
> **★3回目をやらないために、★母数を先に出します。**

## 3. ★61本のうち、★台帳/登記簿のモジュールに触る23本（★名前を出します・MGR「総数をやめて名前を書く」）
```
test_active_work_and_wait_ledger   test_autonomous_git            test_counterfactual_acceptance
test_economy_operator              test_coverage_matrix           test_benchmark_run_ledger
test_completion_definition_registry test_completion_flag_gate     test_dep_flag_registry
test_audit_egl_integration         test_domain_egl_integration    test_control_surface_read
test_economy_decision_ledger       test_live_worker_runtime       test_task_selector
test_human_escalation_ledger       test_fi_min                    test_human_escalation_packet
test_temporal_event_schema         test_historical_velocity_calculator  test_routing_admission
test_temporal_egl_integration      test_roadmap_view
```
```
★23 / 61 / 98
```
| # | ★守ること |
|---|---|
| **1** | **★これは「★23本が本番へ書く」ではありません。** **★import している、までです** |
| **2** | **★モジュール名に `ledger` / `registry` が入る、という★形だけで拾いました。★中で書くかは見ていません** |
| **3** | **★逆に、★名前に入らない書き込み口は★拾えていません**（★§2 の但し書きと同じ） |

> **★「触る」と「書く」を同じ語で書きません。** **★今日ずっと潰してきた形です。**

## 4. ★設計への問い（★私は決めません）
| # | |
|---|---|
| 1 | **★「書くか」の述語を、★61本 全部に当てるのか**（★当てないなら、★どこで切るのかを書いてほしい） |
| 2 | **★述語をどう書くのか**（★`submit()` を呼ぶ／★台帳モジュールの書き込み関数を呼ぶ／★実行して差分を見る 等） |
| 3 | **★`test_fi_min` が23本に入っています。★これは私が D-42 で壊して直した本です**（★逃がしていません。★中身は見直していません） |

## 5. ★私が確かめていないこと
1. **★23本が実際に本番へ書くか**（★走らせていません。★書くとも書かないとも言いません）。
2. **★61本のうち残り38本が何に触るか**（★台帳/登記簿の名前で拾えなかったもの）。
3. **★過去の走行で何が書かれたか**（★台帳を読めません ∴ 出せません。**★「書かれていない」とも書きません**）。

## 6. ★私が変えていないこと
- **★`run_regression.sh`・テスト・向き先を1つも変えていません。**
- **★新しい述語も、★新しい仕組みも作っていません**（★Taka: 新しい機構を作らない）。
- **★以後 BUILT には「★走らせた test の名前と結果」を書きます**（MGR D-109 §4）。**★総数を書きません。**

---
*IMPL FINDING（D-110・【A】。★1本も走らせず・harness を書き換えず・移さず・台帳を直読せず・ソースだけで確かめた）。★**私は判定せず母数を出す**——MGR が判定基準を「書くか」に替えたので、その基準でまだ評価されていない範囲を出す（「3本で足りる／足りない」は書かない）。★**独立に同じ結論に着いた**——CC-α は**実 `submit()` を呼ぶ9本**から**逃がしていない `test_rri_formal.py` の1本**を出し、私は**書き込み口の呼び名8種**（`submit(`/`append_event(`/`ingest(`/`register(`/`record_change(`/`_append_event(`/`open(…,"a")`/`write_text(`）で探して**同じ1本**に着いた ∴ **CC-α の指摘を私も確かめられた**。★**しかし母数が違う（まだ誰も出していない数）**=**総数98／向き先を逃がしている37／★逃がしていない61** ∴ **「書くか」で見るべき対象は61本 在り9本ではない**が、**私が評価できたのは呼び名8種だけで「書く道」の全部ではない** ∴ **「1本だけです」とは書かない（探した範囲がそれだけという意味）**——**今日 私は同じ形で2回 転んだ（`8770` だけ探した／ネットワークだけ見た）ので、3回目をやらないために母数を先に出す**。★**61本のうち台帳/登記簿のモジュールに触る23本を名前で出した**（MGR「総数をやめて名前を書く」）＝`test_active_work_and_wait_ledger`・`test_autonomous_git`・`test_counterfactual_acceptance`・`test_economy_operator`・`test_coverage_matrix`・`test_benchmark_run_ledger`・`test_completion_definition_registry`・`test_completion_flag_gate`・`test_dep_flag_registry`・`test_audit_egl_integration`・`test_domain_egl_integration`・`test_control_surface_read`・`test_economy_decision_ledger`・`test_live_worker_runtime`・`test_task_selector`・`test_human_escalation_ledger`・`test_fi_min`・`test_human_escalation_packet`・`test_temporal_event_schema`・`test_historical_velocity_calculator`・`test_routing_admission`・`test_temporal_egl_integration`・`test_roadmap_view`（**23 / 61 / 98**）——**守ること=これは「23本が本番へ書く」ではなく import しているまで／モジュール名に `ledger`/`registry` が入る形だけで拾い中で書くかは見ていない／逆に名前に入らない書き込み口は拾えていない** ∴ **「触る」と「書く」を同じ語で書かない**。★**設計への問い（私は決めない）**=**「書くか」の述語を61本 全部に当てるのか（当てないならどこで切るのかを書いてほしい）／述語をどう書くのか（`submit()` を呼ぶ／台帳モジュールの書き込み関数を呼ぶ／実行して差分を見る 等）／`test_fi_min` が23本に入っており これは私が D-42 で壊して直した本で 逃がしておらず 中身は見直していない**。★**確かめていないこと**=23本が実際に本番へ書くか（走らせておらず 書くとも書かないとも言わない）／61本のうち残り38本が何に触るか／**過去の走行で何が書かれたか（台帳を読めないので出せず「書かれていない」とも書かない）**。★**変えていないこと**=`run_regression.sh`・テスト・向き先を1つも変えていない／新しい述語も仕組みも作っていない／**以後 BUILT には「走らせた test の名前と結果」を書き総数を書かない**（MGR D-109 §4）。*
