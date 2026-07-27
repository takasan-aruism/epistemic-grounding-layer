# 実装 → 設計/監査: Build 18 — **worker が成果物を出し、受け取りました**（`impl.py` / `test_impl.py`）。**ただし `test_result` は `FAILED`（`RUNNER_FAILED`）**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-28_BUILD18_SPEC_REGENERATE.md` v1.0
- **受領した文書**: 上記 / `CC_MGR_2026-07-28_BUILD18_APPROVED.md` / `CC_MGR_2026-07-28_INCIDENT_RUNAWAY_WORKER_ARTIFACT.md`（写しで観測）
- **本文書は観測を書きます。成果物の中身を評価しません。**

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- **webui pid `2746222` / 起動 `2026-07-27 23:59:33`**
- ソース mtime: `authority.py` 23:24:27 / `generate_via_runner.py` 23:24:27 / `qwen_worker.py` 07-15 23:35:49
- [x] **起動がソースより新しい** / [ ] 古い（→ 止めた）
- ※実装源は `dev-workcell/dw/qwen_worker.py` を想定していましたが、**実在は `twoder/qwen_worker.py`** でした（探索して確認）。

## 投入回数
- **本 task への通算投入回数: ★4回目**（Build 13 / Build 14 / Build 17 / **本 build**）
- **今回の理由**: 再起動後の run-gate 立て直し（常設手順）。**同一文なので task を新設しない。**
- **返った `task_id` = `TASK-2DER-21F64D9D`（★同一を確認）** / 依頼文 2411 字・**1文字も変えていません**

## 経路（★どちらに入ったか）
- [x] **通常の生成** / [ ] 同じコードの再実行（EXECUTION_DEFECT） / [ ] 判定材料が不足

**判断材料（そのまま貼ります・私の解釈ではありません）:**
```
新しい sandbox が1つ作られた           : /tmp/2der_runner_ghaiakgs   （57 → 58）
その中に新規ファイルが書かれた         : ws-8cff562b1d/impl.py（01:42 作成） / test_impl.py（01:40 作成）
regenerate payload の artifact_sha256  : b6b9c154bf4f943927a0111f77da112009ed52e86ca2d0c6ddc7ad1db93ed08f
保全した impl.py の sha256             : b6b9c154bf4f943927a0111f77da112009ed52e86ca2d0c6ddc7ad1db93ed08f   ★一致
```
**∴ 台帳に記録された成果物の sha256 と、私が受け取った `impl.py` の sha256 が一致しています。**

---

## 1. `/api/run_next` の応答（要点・**全文は `egl/docs/BUILD18_run_next_response.json` に保存**）
```
所要 80.3 秒
dispatched : true / reason : null
nlo        : operation=REGENERATE / actor_role=CODING_WORKER / actor_id=QWEN_LIVECODER
state      : dw_state=READY_FOR_AUDIT / last_completed_op=REGENERATE / next_operation=AUDIT
```

## 2. 実行前後の `derive_state`
```
実行前: READY_FOR_REGENERATE
実行後: READY_FOR_AUDIT   （regenerate_runs=1 / rework_count=1 / last_test_passed=False）
```

## 3. ★`REGENERATE` の run payload（逐語・全文・要約も切り詰めもしていません）
```json
{
 "task_id": "TASK-2DER-21F64D9D",
 "phase": "REGENERATE",
 "role": "WORKER",
 "identity": "2der-generate-via-runner",
 "run_id": "SLICE-TASK-2DER-21F64D9D",
 "ts": "2026-07-11T09:00:00",
 "payload": {
  "diff": null,
  "test_result": {
   "status": "FAILED",
   "ok": false,
   "reason": "RUNNER_FAILED",
   "artifact_sha256": "b6b9c154bf4f943927a0111f77da112009ed52e86ca2d0c6ddc7ad1db93ed08f"
  },
  "resolved_findings": [],
  "remaining_findings": []
 },
 "_ordinal": 730
}
```
**実装源 §2-3 が名指しした項目のうち:**
- **`diff`**: **`null`**（有りません）
- **`problems`**: **★キー自体が payload に存在しません**（Build 14 では在りました）
- **`contract_source`**: **★キー自体が payload に存在しません**（Build 14 でも在りませんでした）
- **`artifact_sha256`**: **空でない値が入りました**（Build 14 は `""`・Build 12 は `null`）

### 3-1. Build 14 との差（事実のみ・評価しません）
| | Build 14（GENERATE） | **Build 18（REGENERATE）** |
|---|---|---|
| `reason` | token gate の3件の不一致（`action_type` / `task_id` / `operation_class`） | **`RUNNER_FAILED`** |
| `artifact_sha256` | `""` | **`b6b9c154…`** |
| sandbox の中身 | **0 ファイル** | **★`impl.py` / `test_impl.py` ほか計8ファイル** |
| 所要 | （即時） | **80.3 秒** |

**∴ Build 14 で出ていた token gate の3件の不一致は、今回の記録には現れていません。**

## 4. 受け取り（実装源 §1-⑤）
- **保全先**: `dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/`
- **既存ディレクトリは在りませんでした**（上書きしていません。作成前に確認済）
- **`MANIFEST.json` 全文**:
```json
{
 "TASK_ID": "TASK-2DER-21F64D9D",
 "source_sandbox_abspath": "/tmp/2der_runner_ghaiakgs",
 "received_at": "2026-07-28T01:54:01.882788",
 "sandbox_count_before": 57,
 "sandbox_count_after": 58,
 "files": [
  {"relative_path": "ws-8cff562b1d/.pytest_cache/.gitignore", "sha256": "3ed731b65d06150c138e2dadb0be0697550888a6b47eb8c45ecc9adba8b8e9bd", "bytes": 37},
  {"relative_path": "ws-8cff562b1d/.pytest_cache/CACHEDIR.TAG", "sha256": "37dc88ef9a0abeddbe81053a6dd8fdfb13afb613045ea1eb4a5c815a74a3bde4", "bytes": 191},
  {"relative_path": "ws-8cff562b1d/.pytest_cache/README.md", "sha256": "73fd6fccdd802c419a6b2d983d6c3173b7da97558ac4b589edec2dfe443db9ad", "bytes": 302},
  {"relative_path": "ws-8cff562b1d/.pytest_cache/v/cache/nodeids", "sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945", "bytes": 2},
  {"relative_path": "ws-8cff562b1d/__pycache__/impl.cpython-313.pyc", "sha256": "38d4fc995092dbec9303b2acbb331bfc69fa4cdfc8586da4a24546fa5ae9e54e", "bytes": 1516},
  {"relative_path": "ws-8cff562b1d/__pycache__/test_impl.cpython-313-pytest-9.0.3.pyc", "sha256": "1c421e11557d7ab096bec6a718c84b94e59b5ed1fefc5194286f7f3ea81b2c34", "bytes": 3944},
  {"relative_path": "ws-8cff562b1d/impl.py", "sha256": "b6b9c154bf4f943927a0111f77da112009ed52e86ca2d0c6ddc7ad1db93ed08f", "bytes": 1299},
  {"relative_path": "ws-8cff562b1d/test_impl.py", "sha256": "3458567194083aba5097c1f35363f726e8a5bf855bfccfc7433127831f1f0d78", "bytes": 1637}
 ]
}
```

### 4-1. 成果物のファイル名と行数（**中身は貼っていません・評価していません**）
```
ws-8cff562b1d/impl.py                      23 行
ws-8cff562b1d/test_impl.py                 43 行
ws-8cff562b1d/.pytest_cache/.gitignore      2 行
ws-8cff562b1d/.pytest_cache/CACHEDIR.TAG    4 行
ws-8cff562b1d/.pytest_cache/README.md       8 行
ws-8cff562b1d/.pytest_cache/v/cache/nodeids 1 行
ws-8cff562b1d/__pycache__/*.pyc            （テキストではありません・2件）
```
- **`.pytest_cache` が在ります**＝**sandbox 内で pytest が動いた形跡です**（事実のみ。何が起きたかは調べていません）。
- **★保全した成果物を実行していません。** **`CC_MGR_2026-07-28_INCIDENT_RUNAWAY_WORKER_ARTIFACT.md` を写しで観測した後なので、明記します。**

## 結果の区分（1つに丸）
- [x] **SANDBOX_ARTIFACT_READY（成果物が出て、受け取れた）**
- [ ] GENERATION_FAILED / [ ] SKELETON_VIOLATION / [ ] TOKEN_GATE_BLOCKED / [ ] ARTIFACT_LOST

**★ただし区分が重なっています。** **`GENERATION_FAILED` の説明「テストが通らなかった」も同時に成り立ちます**（`test_result.status = FAILED`）。**片方だけ丸を付けて他方を消すと事実が落ちるので、重なりを明記します。** **どちらを正とするかは設計/監査の判断です。**

## 5. 予想と実際（実装源 §3）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| `dispatched` / actor | `true` / `CODING_WORKER` | **`true` / `CODING_WORKER`（`QWEN_LIVECODER`）** | **当たり** |
| 経路 | 通常の生成 | **通常の生成**（新規ファイル＋sha256 一致） | **当たり** |
| **`run_runner` への到達** | **到達する** | **★成果物が書かれ `artifact_sha256` が記録された** | **当たり** |
| **sandbox にファイルが出るか** | **出る** | **★出た（8ファイル）** | **当たり** |
| **`test_result.status`** | **`PASSED` にならない** | **`FAILED`（`RUNNER_FAILED`）** | **当たり** |
| **held-out** | 判定不能の可能性が高い | **判定不能**（`PASSED` でないため検査以前） | **当たり** |

**6項目すべて当たりました。外れはありません。**

## 6. 守った禁止事項
- **成果物の中身を評価していません。テストを足していません。修正していません。★実行もしていません。**
- **オラクルを開封していません。**
- **配置・登記・配線をしていません**（保全のみ）。
- **1段だけです**（`run_next` 1回。`AUDIT` へ進んでいません）。
- **手で書いていません。** `problems` / `reason` は逐語です。
- **`run_until_barrier` を使っていません。token を迂回していません。**
- **他の2 task に触っていません。新しい task を作っていません**（同一 id を確認）。
- **本番コードを1行も変更していません。**
- **`/tmp` を1件も消していません**（数えただけ。`G-17` 調査中）。
- **`CC_REGISTER.jsonl` に試験行を書いていません。**
- **`twoder/runs/*.trace.json` を読んでいません。**
- **既存の保全ディレクトリを上書きしていません**（作成前に不在を確認）。

## 7. 位置づけ（実装源 §6・緩めません）
- **「2DER が作れるようになった」とは書きません。** **1回・1件です。**
- **供給したテストが通っても依頼を満たした証拠にはならない、という条件は変わりません。** **そもそも今回は `PASSED` ではありません。**
- **1回の観測です。常態を判定していません。**

## 8. commit
**していません**（MGR）。**本 build で本番ファイルの変更はありません。** **保全ディレクトリ（`dev-workcell/contracts/out/...-regen/`）が新規に増えています。**

---
*IMPL BUILT（Build 18・**SANDBOX_ARTIFACT_READY**）。鮮度確認→`READY_FOR_REGENERATE` を確認→同一文（2411字・1文字も変えず・通算4回目）を再投入し `task_id` 同一を確認→`run_next` 1回。★`dispatched:true` / `CODING_WORKER`(`QWEN_LIVECODER`) で 80.3 秒、**新しい sandbox `/tmp/2der_runner_ghaiakgs` に `impl.py`(23行) / `test_impl.py`(43行) ほか計8ファイルが書かれ、その場で保全した**（`dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/`・既存不在を確認・MANIFEST 全文掲載）。★台帳の `artifact_sha256=b6b9c154…` と保全した `impl.py` の sha256 が一致 ∴ 経路は「通常の生成」。**ただし `test_result` は `FAILED` / `reason="RUNNER_FAILED"`**、`diff` は `null`、`problems` と `contract_source` はキー自体が payload に無い。Build 14 で出ていた token gate の3件の不一致は今回の記録に現れていない。状態は `READY_FOR_AUDIT`（rework_count=1 / last_test_passed=False）。★区分は重なっている——`SANDBOX_ARTIFACT_READY` に丸を付けたが `GENERATION_FAILED` の「テストが通らなかった」も同時に成り立つので明記し、どちらを正とするかは設計/監査に委ねる。★保全した成果物を実行していない（runaway worker の INCIDENT を観測した後なので明記）。`.pytest_cache` が在り sandbox 内で pytest が動いた形跡がある（事実のみ・調べていない）。予想6項目すべて当たり・外れなし。実装源が指した `dev-workcell/dw/qwen_worker.py` は実在せず `twoder/qwen_worker.py` だった。成果物が出ても「作れるようになった」とは書かない。*
