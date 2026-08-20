# 宛: Taka ―― **P1 実装前 3点 確認（★実測・★コード 0行）**

**2026-08-20 15:1x ／ ★repo 変更 0 ／ 実装 0 ／ 投入 0 ／ `twoder@04f8b07` 不変**

---

## ★① Stage 6 の 出力を Stage 8 まで 保持する 最小既存面 = **★`knowledge_packet` でも `contract` でも ありません**

**★ご指定の 二択が ★成り立ちません。★理由を 実測で 示します。**

```
★`knowledge_packet` と `contract` は ★★Stage 8 の 分岐の ★中で 作られて います:
   submit.py:642  _obs_kp   = {...}          ← ★OBSERVE 分岐(:608)の 中
   submit.py:715  kp        = {...}          ← ★BUILD 分岐(:682)の 中
   submit.py:723  _contract = extract_contract(raw_input)   ← ★同じく BUILD 分岐の 中
   submit.py:743  W.create_task(..., kp, ..., contract=_contract)   ← ★Stage 9

★★∴ ★Stage 8 に 着いた 時点では ★どちらも ★まだ 存在しません。
★★∴ ★「Stage 6 で 書けて Stage 8 で そのまま 読める」を ★満たしません（★両方とも）。
```

**★実際に 満たして いる 面は ★1つ 在ります（★実測）:**

```
submit.py:33-36   def _rec(k, v): _T()[k] = v          ← ★TRACE 辞書へ 書く
submit.py:26-30   _T() は thread-local の 辞書
★Stage 6 が 書く: submit.py:472  _rec("INTENT_STRATEGY", {strategy, candidates, status, consensus, reason, …})
★Stage 8 が 読む: ★同じ submit() 呼び出しの 中 ∴ ★そのまま 読めます
   （★実例 = :485  if IST.stops_before_action(_istrat) …  ＝ ★★既に Stage 6 の 値で 分岐して いる）

★★永続も されて います:
   webui.py:1443  _atomic_write(RUNS / f"{key}.trace.json", json.dumps(tr, …))
   webui.py:1445  _atomic_write(RUNS / f"{tid}.trace.json", json.dumps(tr, …))
   ＝ ★submit ごと ＋ task ごとに ★TRACE 全体が 保存される。
   ＝ ★`/api/state` は ★この `tr` から 全欄を 組み立てて いる（webui.py:205-232）。
```

```
★★∴ ★答え = ★★`TRACE`（`_rec` / `submit.py:33`）。
★★＝ ★新しい 欄 0 ／ 新しい 台帳 0 ／ 新しい 口 0 で ★Stage 6 → Stage 8 を 運べます。
★★＝ ★`knowledge_packet` は ★Stage 9 以降（DW へ 渡す とき）に 意味を 持つ 面 で あって
      ★Stage 8 の 判断材料には ★時系列上 使えません。
★★どちらを 使うかは ★私は 決めません ―― ★★『二択が 成り立たない』という 実測だけを 返します。
```

---

## ★② `runtime_inspection.inspect` の 結果を 後から API で 成果本体と して 取得できる 既存面 → **EXISTS（★2面）**

**★実測 ―― ★観測の 本体は ★既に 個別 id で 引けます:**

```
★実際に 引いた（`TASK-2DER-81F60030`）:
   GET /api/state?task_id=…  → egl.source_refs = ★4件 ['OBS-05775','OBS-05776', …]
   GET /api/resolve?id=OBS-05775 → ★resolved=True
      {observation_id, acquisition_run_id, source_id, raw_content_hash: "sha256:6dd8179a…",
       raw_blob_ref: "blob://sha256:…", …}
★★＝ ★観測 1件ごとに ★id ／ ★内容 hash ／ ★本体への 参照(blob) が ★正規 API から 取れる。
```

| 面 | 取得の 仕方 | 判定 |
|---|---|---|
| **EGL 観測**（`OBS-…`） | `GET /api/resolve?id=OBS-xxxxx` ★本体 hash と blob 参照つき | **EXISTS** |
| **TRACE**（`{tid}.trace.json`） | `GET /api/state?task_id=…` が ★`RUNTIME_INSPECTION_RESULT` を含む `tr` から 組み立て | **EXISTS** |
| ROADMAP 台帳 | `GET /api/resolve?id=ITEM-…&history=1`（★本日 5回 実測） | EXISTS |
| PROCESS_EVENT | 追記は できる が ★逐語「derive_state は無視」＝状態を 進めない | ★本体の 唯一の 置き場に しない（★ご指示どおり） |

```
★★∴ ★『後から 成果本体を 機械的に 取れる 既存面』は ★EGL 観測(OBS-…)と TRACE の ★2つ。
★★どちらを 成果本体の 置き場に するかは ★私は 決めません。
```

---

## ★③ Stage 8 で「調査完了」を 返す 既存の response 形 → **★EXISTS（★流用できます・★新設 不要）**

**★実測 ―― `/api/submit` は ★★既に 観測結果を 返して います（webui.py:1457-1476）:**

```
返り の 欄（★逐語）:
   task_id / request_type / acquisition_method / next_legal_operation / trace_key /
   deferred_active_tasks / deferred_summary /
   ★measured_state          ← 観測の 人が 読める 値
   ★egl_source_refs         ← 観測 id の 一覧（★②で 引ける）
   ★host_ref                ← どの 機械を 見たか
   ★non_guarantee           ← 逐語「single snapshot ≠ capability」
   ★runtime_inspection_status ← 観測の 成否
   failure_memory_match / guard_block / blocked / progress_write / rri_preflight
★★＝ ★『調査を 実行し ／ 結果を 返し ／ 保証の 範囲も 添える』形が ★★既に 在り ★動いて います。
★★＝ ★組み立ては ★全部 `tr.get(...)` ＝ ★TRACE から 引くだけ（★record を 1件も 増やして いない）。
```

**★足りない ものを 実測で 挙げます（★推測では ありません）:**

```
★① `deliverable` / `work_kind` / `stop_at` の 欄が ★返りに 無い
   ―― ★①で 見た とおり ★TRACE に 書けば ★同じ 作り方で 返せます（★`tr.get(...)` を 1行 足す形）。
★② 観測の 起動が ★`OBSERVE_CURRENT_STATE` に 縛られて いる
   ―― submit.py:611  research_focus_ref="OBSERVE_CURRENT_STATE"  ★呼び出しに 直書き。
★③ `INVESTIGATION_REPORT`（question / verdict / evidence_refs / observed_value / needs_design）を
   ★作る 者が ★居ない ―― ★観測器が 返すのは `observations` / `failed_observations` で あって
   ★M1〜M16 の 形では ない。
★★∴ ★『返す 形』は 流用できる。★『中身を M1〜M16 に 組む 段』が ★★実測で 不在。
```

---

## ★まとめ（★判定だけ・★決めて いません）

| 問 | 判定 | 一言 |
|---|---|---|
| ① 保持面 | **CONFLICT** | ★二択が 成り立たない。★Stage 8 時点で kp も contract も ★未生成。★実在する 面は `TRACE`(`_rec`) |
| ② 成果の 取得面 | **EXISTS** | ★EGL 観測(`OBS-…` を `/api/resolve` で 本体 hash つき)と TRACE の 2面 |
| ③ 応答の 形 | **EXISTS（流用可）** | `/api/submit` が 既に 観測結果＋非保証を 返す。★不足は 3つ（欄3つ／起動の 直書き／M1〜M16 を 組む 段） |

## ★次に 私が するべきこと（★ご指示の 確認）

```
★ご指示 =「この3点だけ 調査して ★問題なければ ★Claude に P1 を bootstrap 実装させて 構いません」
★★問題が 1つ 出ました = ★①（★二択が 成り立たない）。
★★∴ ★私は ★実装に 進んで いません。
★★理由 = ★『どちらを 使うか』が ★前提ごと 変わる ため
      ―― ★`TRACE` を 使う のは ★ご指定の 二択の どちらでも ない ∴ ★私の 判断で 選ぶのは ★越権です。
★★お伺いしたいのは 1点だけ:
   ★★Stage 6 → Stage 8 の 保持面を ★`TRACE`(`_rec`) と して よいか。
   （★`knowledge_packet` は ★Stage 9 で DW へ 渡す とき 併せて 載せる か どうかも ★併せて）
```

## ★していないこと

```
★コード 0行 ／ 実装 0 ／ 設計案 0 ／ repo 変更 0 ／ 投入 0 ／ 常駐 停止の まま
★★『どれを 使うか』を 1つも 決めて いません
★SELF_DEV_TOKEN = ★5/5
```
