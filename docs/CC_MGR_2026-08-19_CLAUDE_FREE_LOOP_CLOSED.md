# 宛: Taka ―― **★★成立: `goal → Qwen PLAN → contract変換 → GENERATE → runner → TEST` が Claude DESIGN 0 で通った**

**2026-08-19 23:3x ／ `TASK-2DER-834D7DD2` ／ bootstrap commit `4a94ebd`**

---

## 0. ★結果（★正規記録・全欄）

```
★記録の 並び = CREATE → PROCESS_EVENT → ★PLAN → PROCESS_EVENT → ★GENERATE
              → PROCESS_EVENT → ★AUDIT → ★UPPER_REVIEW
★state = READY_FOR_UPPER_REVIEW → ★UPPER_REVIEW ★PASS
```

| 欄 | 値 |
|---|---|
| `PLAN identity` | **`2der-qwen-build-planner`** |
| `test_body` | **671B**／先頭 `from impl import remove_duplicates`（★Qwen が書いた封印試験） |
| `GENERATE.ok` / `.passed` / `.status` | **`true` / `true` / `"PASSED"`** |
| `reason` | **`""`**（★`no provenance supplied` は ★消えた） |
| `artifact_sha256` | **`3be434807c605606a52c06518a76df97247095516527e8cd7083f55931518e86`** |
| `last_test_passed` | **★`True`** |
| `AUDIT findings` | **★0件** |
| `UPPER_REVIEW` | **`PASS`** ／ identity=**`2der-auto-upper-review`** ／ `reviewer_class="MACHINE_TRIVIALLY_CLEAN_GATE"`（★逐語「no LLM; NOT authority approval」） |

```
★★＝ ★test が 実際に 走り ★通った。★成果物が 実在する（sha256 あり）。
★★＝ ★Claude は ★goal の 自然文 1つ しか 書いていない。
```

## 1. ★Claude が 書いた もの / 2DER が 作った もの

```
★Claude が 書いた = ★goal の 文 だけ
   「文字列の 一覧を 受け取り、重複を 取り除いて 元の 並びの まま 返す 純関数が 要る …」
★★2DER が 作った = requirement ／ test_plan ／ ★test_body(封印試験) ／ ★skeleton ／ ★実装
★★Claude DESIGN の 介在 = ★0 ／ 契約 0 ／ 骨格 0 ／ 封印試験 0 ／ 実装 0 ／ run_next 0
★上級監査も ★機械（`2der-auto-upper-review`・★LLM 0回）
```

## 2. ★ブートストラップで 私が した こと（★1点だけ・★開示）

**`twoder/generate_via_runner.py`（commit `4a94ebd`・★11行 追加・★削除 0）**

```python
if has_skel and has_tests:        # ★packet 経路
    ...
    _ce = read_create_event(packet.get("task_id"))          # ★ledger 経路(:289)と ★同じ アクセサ
    if _ce:
        provenance = ((_ce.get("payload") or {}).get("knowledge_packet") or {}).get("provenance")
                                                             # ★ledger 経路(:303)と ★同じ 場所
```

```
★新しい 値 0 ／ 新しい 判断 0 ／ 新しい 語 0 ／ 新しい 台帳 0 ／ 新しい 口 0
★無い ときは None の まま = ★runner 側の 門(DE-0301)で fail-closed（★捏造しない）
★接続前に 読み取りだけで 確認 = 5件とも provenance 実在（鍵 8〜9個）
```

## 3. ★これで 何が 変わったか（★対照）

| | 契約経路（Claude が骨格・封印試験） | goal 経路（Qwen 設計） |
|---|---|---|
| **前** | runner 動く（`9F26BF5F` exit=1） | **runner 一度も 動かない**（4件） |
| **後** | （未変更） | **★★runner 動く ／ test 通る ／ AUDIT 0件 ／ UPPER_REVIEW PASS** |

## 4. ★観測性の 小さな 傷（★直していない・★記録のみ）

```
★`artifact_head` が ★空 ／ `diff` が 0B ／ `run_id` が null
   ＝ ★成果物の 中身が 記録の 表からは 読めない（★sha256 は 在る）
★`runner_exit` / `runner_stdout_tail` が null
   ＝ ★成功時は その2欄を 載せない 設計（失敗時のみ :325-327 で 付く）
   ＝ ★『動いていない』と ★『成功した』が ★同じ null で 表れる（★紛らわしい）
★★どちらも ★次の 停止点の 候補 ∴ ★2DER へ 戻す 対象（★私は 直さない）。
```

## 5. ★次段階（★Taka 裁定どおり・★これから）

```
★実 repo 自己更新を ★SELF_DEV_TOKEN = 5 の 有限予算で 開始する。
★repo 変更は ★既存の patch / energize / rollback / reconciler / authority だけを 通す。
★1停止点（修正→検証→再実走→次停止点確認）= ★1 token。
★token = 0 で 停止し Taka へ 周回報告。★token は authority では ない。
★scope外 / rollback failure / authority ceiling超過 / 安全境界変更
   = ★残 token に 関係なく ★即停止・上申。
```
