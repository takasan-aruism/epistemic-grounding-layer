# 宛: Taka ―― **★「安全な単独自己開発実行口」は ★存在した（欠落ではない）＋ 2DER が 分離を 自力設計**

**2026-08-19 23:5x ／ ★常駐 停止のまま ／ ★SELF_DEV_TOKEN = 5/5（消費 0）**

---

## 1. ★答え ―― **在る。★新しい口を 作っていない**

```
★★`MANAGER_V0_ONCE=1 python3 -m twoder.manager_v0`（★既存・:457-458）
```

**★危険な 経路を 通らない 根拠（★ソース・★3点）:**

```
★`_place_and_commit` の 呼び手 = `domain_dw.py:383`（★`receive_finished` の 中）★1箇所だけ
★`receive_finished` の 呼び手 = `manager_v0.main():438`（★常駐ループ）★のみ
★`MANAGER_V0_ONCE` は ★`tick()` だけを 1回 走らせる ＝ ★`receive_finished` を ★呼ばない
★runner の 作業場 = `tempfile.mkdtemp("2der_runner_")` 逐語「★isolated 作業域(実 repo でない)」
```

**★★実走で 裏を取った（★ソースに 無い＝起きない、も 実測する）:**

```
★tick 1回で 終端(JUDGE_REQUIRED)まで 到達
★★twoder HEAD = `3dd7d02` ―― ★実行の 前後で ★不変（★commit 0 ／ push 0）
★常駐 = inactive の まま ／ run_next 0 ／ 手動前進 0
```

## 2. ★★2DER が 自力で 出した 分離設計（★逐語）

**`TASK-2DER-16D40E39`（★私は 直し方も 修正箇所も 与えていない）**

```
★scope 「Implement a ★routing gatekeeper component to ★intercept commit paths,
        ★detect existing files, and ★enforce pipeline segregation
        ★without modifying the official pipeline internals.」

★requirement 「… provides a ★`route_commit_request(source_code, target_dir)` function.
        This function must parse the source code to identify the ★target filename and
        function signature, ★check if the file already exists in the target directory,
        and return a ★routing decision. ★If the file is new, it sho…」

★steps 「Implement routing logic: ★new files trigger direct placement,
         ★existing files trigger ★official pipeline routing.」

★★prohibited_actions（★2DER 自身が 書いた 禁止事項）:
   「★Directly modifying existing files in twoder/.」
   「★Bypassing the official pipeline for existing files.」
   「★Committing directly to the repository.」
```

**★★＝ ご指示の 分離（新規配置 / 既存file更新）を ★2DER が 自分で 設計した。
★★＝ しかも ★自分が 起こした 実害の 再発禁止を ★自分の 禁止事項に 書いた。**

## 3. ★★runner が 実際に 走り、★試験が 落ちた（★これは 正常な 開発の 停止点）

```
★GENERATE   runner_exit = ★1 ／ artifact_sha256 = ★2358ba146bdd7ae5（★成果物 実体あり）
★REGENERATE runner_exit = ★1 ／ artifact_sha256 = ★e2c20a9c3cdf7771
★AUDIT findings = 1件（category = `test_failure`）

★★runner_stdout_tail（★逐語・★2DER 自身の 封印試験が 落ちた 中身）:
   E  AssertionError: assert 'direct_placement' == 'official_pipeline'
   FAILED test_impl.py::test_malformed_json_source
   FAILED test_impl.py::test_signature_mismatch_handling
   ★2 failed, 3 passed in 0.01s
```

```
★★＝ ★『壊れていて 動かない』のでは ない。★『動いて 2件 落ちた』。
★★＝ ★これが ★次に 2DER へ 戻す べき ★通常の 停止点（★私は 直さない）。
```

## 4. ★到達点と 未到達点（★正確に）

| 段 | 結果 |
|---|---|
| 停止事実 → goal 化 | **★成立** |
| ★常駐を 使わない 単独実行 | **★成立**（既存口・HEAD 不変で 実証） |
| 原因調査 → 分離の 設計 | **★成立**（★2DER が 自力・★上の 逐語） |
| PLAN → 検査 | **★成立** |
| GENERATE → runner → TEST | **★走った**（★2 failed / 3 passed） |
| 実 repo 反映 | **★未実施**（★target_workspace = `./sandbox/twoder_router`） |
| 分離の 実装 | **★未完**（★試験 2件 落ち） |

**★2DER が 自分で 書いた 未解決点（逐語）:**

```
「Exact internal API of the ★official pipeline components.」
「Precise path structure of the sandbox workspace.」
★＝ ★実物の API を 知らない まま 設計している（★repo を 読む 手立てが 無い ため）。
```

## 5. ★私が した こと / していない こと

```
★した = 調査 ／ goal 投入（★観測事実だけ）／ 待ち行列を 1件に する（データのみ）／
        既存口 `MANAGER_V0_ONCE` を 1回 実行 ／ 各回 HEAD 確認 ／ 記録
★★していない = 設計 0 ／ 実装 0 ／ 修正案 0 ／ 契約 0 ／ 骨格 0 ／ 封印試験 0 ／
        run_next 0 ／ 手動前進 0 ／ `_place_and_commit` の 改造 0 ／ 常駐 再開 0
★SELF_DEV_TOKEN = ★5/5（★消費 0）
```

## 6. ★次に 戻すべき 停止点（★私の 提案では なく ★記録が 示す 1つ）

```
★『2DER 自身の 封印試験が 2件 落ちている』
   `assert 'direct_placement' == 'official_pipeline'` ／ malformed_json ／ signature_mismatch
★★これは ★2DER へ 戻す 通常の 停止点 ∴ ★Claude は 直さない。
```
