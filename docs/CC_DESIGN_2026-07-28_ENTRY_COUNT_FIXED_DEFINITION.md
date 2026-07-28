# 設計/監査 → MGR（写: Taka / IMPL）: **入口の独立計数（母数を固定）— ★32件。加えて、2者の計数を必ず食い違わせる罠が2つ在る**

- `BUILD_ROLE: 参照`（**計数のみ。何も作っていない・投入していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8` — `§12` を最大版で読んだ値）**
- **受領**: `CC_MGR_2026-07-28_D44_FINAL_PHASE1_REPORTED.md` §3（母数を1つに決めて2者独立に数える）

## 0. ★母数の定義（これを固定する。IMPL は★このコマンドをそのまま使うこと）
```bash
# 対象: ds rri egl dev-workcell twoder の *.py
# 一致: 行内に submit( / create_task( / record_utterance( の呼び出し形
# 除外: 定義行(def …) / test_ を含むパス / /regression/ / /experiments/
# ★グループ化しない。★打ち切りを使わない。
grep -rn --include=*.py -E "(^|[^a-zA-Z_0-9])(submit|create_task|record_utterance)\(" \
     ds rri egl dev-workcell twoder 2>/dev/null \
  | grep -v "test_" | grep -v "/regression/" | grep -v "/experiments/" \
  | grep -vE "def (submit|create_task|record_utterance)\("
```

## 1. ★私の計数
```
★総件数 32 / 確認 32 / 打ち切り無し
  submit(             13
  create_task(        10
  record_utterance(    9
```
**★32行すべてを先行文書と本文書で全掲載している**（打ち切っていない）。**IMPL は行単位で照合できる。**

## 2. ★2者の計数を必ず食い違わせる罠（先に出す）
> **★この2つを知らずに数えると、2者は絶対に一致しない。** **一致しない原因が「見落とし」なのか「罠」なのかを判別できなくなる。**

| # | 罠 | 実物 |
|---|---|---|
| **1** | **`submit` は 2DER の関数だけではない** | `egl/structure/s2_extract.py:144` **`futs = {ex.submit(work, k): k …}`** ← **★`ThreadPoolExecutor.submit`。無関係** |
| **2** | **`submit()` は JavaScript にも在る** | `twoder/webui.py:637` `<button onclick="submit()">送信</button>` / `:650` `async function submit(){…}` ← **★ブラウザ側。Python の入口ではない** |

**その他の非呼び出し**（同じ定義に必ず入る。**★除外していない。分類しているだけ**）:
```
egl/egl/core.py:122            コメント（「submit() の外からも呼ばれる」）
twoder/counterfactual_runner.py:5   docstring
twoder/select_and_create.py:91      コメント
twoder/submit.py:98            文字列リテラル  entry="submit()"
```

## 3. ★分類（32行 → 実際の Python 呼び出し）
| 種別 | 件数 | 内訳 |
|---|---|---|
| **★実際の呼び出し** | **21** | 下記 |
| 罠（別物の `submit`） | 3 | `s2_extract.py:144` / `webui.py:637` / `webui.py:650` |
| コメント・docstring・文字列 | 4 | `core.py:122` / `counterfactual_runner.py:5` / `select_and_create.py:91` / `submit.py:98` |
| **★別関数の同名呼び出し** | 4 | `select_and_create.py:150`（**★`workcell.create_task` ではなく同ファイル内の別 `create_task`**）／`egl/docs/evidence/…:57`（同上・証跡ファイル）／`s_retention_repair_a.py` の4行のうち… |

**★21件の内訳（`submit` 8 / `create_task` 6 / `record_utterance` 7）:**
```
submit          : de_submit_route:46 / s_de_route_equiv:107 / counterfactual_runner:48 /
                  live_worker_runtime:197 / codegen_run_fn:70 / runtime_supervisor:222 /
                  webui:536 / submit.py:503（CLI __main__）
create_task     : run_rri_task:167 / run_esde_task:167 / ★dw/workflow.py:37 /
                  select_and_create:80 / submit.py:450 / experiment_candidate:116
record_utterance: run_ds_benchmark:63 / ai_work_system_loop_demo:116 /
                  s_retention_repair_a:41,43,45,48 / authority:125 / intervention:76 / submit.py:108
                  （★9行。上記のうち benchmark・demo・structure の6行は依頼経路ではない）
```

## 4. ★私の判定（決めない。数と分類だけ）
1. **★`create_task` の実呼び出し6件に `dw/workflow.py:37` が入っている。** **`G-50`（13番目）は本計数でも再現した。**
2. **★`submit` の実呼び出しは8件。** **私が前回「8」と書いた数と一致する**（alias 7 + CLI 1）。
3. **★総件数32は、罠と非呼び出しを含む機械的な数である。** **意味のある数は21、依頼経路に限れば更に小さい。**
   > **★どの数を「入口の数」と呼ぶかは、私が決めることではない。** **3つの数（32 / 21 / 依頼経路のみ）をそのまま出す。**

## 5. ★予測を先に固定する（IMPL の計数が出る前に書く）
| 予測 | 根拠 |
|---|---|
| **IMPL が §0 のコマンドをそのまま使えば★32になる** | 決定論。**★ならなければ、環境か除外条件が違う** |
| **IMPL が前回と同じ `-F "submit("` を使えば★32にならない** | 前回24。**★母数が違うだけで、どちらも誤りではない** |
| **罠2件（`ex.submit` / JavaScript）に IMPL が気づくか** | **★予想しない。** 気づかなくても、行単位で照合すれば私の分類と突き合わせられる |

## 6. ★未確認
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`s_retention_repair_a.py` の4行が「別関数」か「同じ `phase0.record_utterance`」か** — **★同じである（実読）。** ただし `egl/structure` 配下＝依頼経路ではない | — |
| 2 | **`select_and_create.py:150` の `create_task` が同ファイル内の別関数であること** | **★実読で確認済**（`:80` が `_workcell.create_task` を呼ぶラッパ） |
| 3 | **この計数も1回である** | **★2者一致が基準**（MGR 裁定 B）。**私1人では閉じない** |

---
*CC-α。★MGR §3（母数を1つに固定して2者独立に数える）を実施。**母数の定義をコマンドとして固定**し（`submit(`/`create_task(`/`record_utterance(` の呼び出し形・`def` 行と `test_`・`/regression/`・`/experiments/` を除外・グループ化しない・打ち切り無し）、**総件数32 / 確認32 / 打ち切り無し**（`submit(` 13 / `create_task(` 10 / `record_utterance(` 9）を全32行掲載した。★**2者の計数を必ず食い違わせる罠を2つ先に出す**=①`egl/structure/s2_extract.py:144` の `ex.submit(work, k)` は **`ThreadPoolExecutor.submit` で無関係** ②`twoder/webui.py:637,650` の `submit()` は **JavaScript でブラウザ側**——これを知らずに数えると2者は絶対に一致せず、不一致の原因が「見落とし」か「罠」か判別できなくなる。他にコメント/docstring/文字列リテラルが4行（除外せず分類しただけ）。★分類=32行のうち**実際の Python 呼び出しは21**（罠3・コメント等4・別関数の同名呼び出し4）。★判定=`create_task` の実呼び出し6件に `dw/workflow.py:37` が入り **`G-50`(13番目)は本計数でも再現**／`submit` の実呼び出しは8件で私の前回の「8」と一致（alias 7＋CLI 1）／**総件数32は罠と非呼び出しを含む機械的な数で、意味のある数は21、依頼経路に限れば更に小さい——どの数を「入口の数」と呼ぶかは私が決めることではないので3つの数をそのまま出す**。★予測を IMPL の計数が出る前に固定=同じコマンドを使えば32になる（決定論。ならなければ環境か除外条件が違う）／前回と同じ `-F "submit("` なら32にならない（前回24。母数が違うだけでどちらも誤りではない）／罠2件に IMPL が気づくかは**予想しない**。★未確認=`s_retention_repair_a.py` の4行は同じ `phase0.record_utterance` だが `egl/structure` 配下で依頼経路ではない（実読）／`select_and_create.py:150` は同ファイル内の別関数（実読で確認済）／**この計数も1回であり、2者一致が基準なので私1人では閉じない**。*
