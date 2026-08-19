# 宛: Taka ―― `TASK-2DER-7D461717`: **★A でも B でもない ―― Qwen PLAN は呼ばれ、通った**

**2026-08-19 21:1x ／ 正規記録（DW 自身の accessor）から取得。★Claude の補完 0。**

---

## 0. 二択の答え

```
★A（試したが fail-closed） … ★違う
★B（一度も 呼ばれていない） … ★違う
★★実際 = ★★呼ばれた ＋ ★validate_plan を 通り ★PLAN が 記録された
```

## 1. 6項目の実測

| # | 求められた物 | 実測 |
|---|---|---|
| 1 | `run_until_barrier` の当該TASK結果 | **PLAN が 記録に 出た**（`CREATED → READY_FOR_IMPLEMENTATION` 遷移が 成立） |
| 2 | `planner_outcome` | **`recorded: True` 相当**（`dispatch.py:146` は `pres.get("recorded")` の時だけ `auto_served="QWEN_BUILD_PLANNER"` を返す） |
| 3 | BUILD_PLANNER actor の呼び出し記録 | **`PLAN identity = 2der-qwen-build-planner`**（出所 = `build_planner.py::DEFAULT_IDENTITY`） |
| 4 | Qwen 呼び出し記録 | **`plan_source = "QWEN_BUILD_PLANNER"`** ／ `provenance.trace_id=TRACE-cdf0714269` / `ds_input_id=UTT-4619` / `rri_request_id=RREQ-02320` / `egl_source_refs=["RECORD-2DER-EVO-0019"]` |
| 5 | plan record の有無 | **★在る**（`PLAN` event 1本・`implementation_packet` 24欄） |
| 6 | `validate_plan` の結果 | **★通った**（逐語「records it via the EXISTING `W.record_plan` **ONLY if valid**; otherwise it records NOTHING」∴ ★記録の存在が 合格の証拠） |

## 2. ★Qwen が書いた中身

```
requirement  「Create a pure function `diff_texts(old_text, new_text, filename) -> str` in `impl.py`
              that generates a unified diff string.」
target_file  impl.py            test_file  test_impl.py
test_command ["python3","-m","pytest","-q","test_impl.py"]
allowed_files ["impl.py","test_impl.py"]
★test_body   ★1906バイト（★完全な pytest module。先頭= `from impl import diff_texts` …）
test_plan    4件以上（変更なし／1行／複数行／離れた変更 …）
completion_criteria 5件
```

**★＝ 封印試験に相当する `test_body` を Qwen が書きました。Claude は 1バイトも書いていません。**

## 3. ★経路が丸ごと通った（記録の並び）

```
CREATE(2der-conductor)
 → PROCESS_EVENT(2der-runtime-supervisor / attempts=3 / failure_class=None)
 → ★PLAN(★2der-qwen-build-planner)
 → GENERATE(2der-generate-via-runner)
 → AUDIT(2der-adjudicator) → DISPOSE(2der-auto-dispose)
 → UPPER_REVIEW(claude-senior)          ★=Taka が 別枠で 維持と 決めた actor
 → REGENERATE → AUDIT → DISPOSE → UPPER_REVIEW(claude-senior)
```

```
★Claude DESIGN の 介在 = ★0（契約 0本 ／ skeleton 0 ／ test_body 0 ／ 実装 0）
★私が 叩いた run_next = ★0 ／ ★task を 手で 前進 = ★0
★指示後に 待ち行列を 並べ替えた = ★0（並べ替えは ご指示より 前）
```

## 4. ★まだ通っていない所（★補完しません）

```
★GENERATE の test_result = ★passed: false ／ returncode: null
   ＝ ★Qwen の PLAN は 通ったが ★実装が その 封印試験を まだ 通していない
   ＝ ★いま JUDGE_REQUIRED（★次= UPPER_REVIEW）
★これは ★PLAN の 問い（今回の 1点）とは 別の 停止点。★手を 出していません。
```

## 5. ★お知らせ（判断は仰ぎます・私は動きません）

待ち行列には **Claude DESIGN 由来 11件**が残っており、常駐が進めると各件で `claude-senior` が呼ばれます
（`should_call_senior` の guard は **生きています** ―― webui 起動 13:09:52 / guard commit 13:09:23）。
**止めるか流すかはご指示に従います。常駐は起動したままにしてあります。**
