# 宛: Taka ―― **自己開発ループ 周回まとめ（★1枚）**

**2026-08-19 深夜 ／ ★Claude が 与えた 設計・実装・原因 = ★0**

---

## 1. ★周回した 4件（★すべて goal だけ 投入）

| task | 投入した 停止事実 | 2DER が 自力で 出した 物 | 止まった 所 |
|---|---|---|---|
| `3CF23D43` | （通常の goal） | PLAN(qwen) ／ `from impl import` 付き test_body ／ ★契約変換 成立 | **`no provenance supplied`** |
| `76070397` | ↑の 停止事実 | PLAN(qwen) ／ ★scope 逐語「Modify the **packet construction** …」／ steps「Identify the **packet construction point** in the codebase」 | **同上** |
| `1A9EEBD3` | Taka の `SELF_DEV_TOKEN` 要件（逐語） | PLAN(qwen) ／ 要件4点とも 文面に 出た ／ `SelfDevBudget` class | **同上** |
| `02BAA787` | ↑3件が 同じ所で 止まった 事実 | （観測中） | （観測中） |

## 2. ★★到達した こと（★これは 事実として 大きい）

```
★★2DER は ★私が 伏せた 原因の 在り処を ★自分で 名指しした。
   逐語（`76070397` の PLAN・★2DER が 書いた）:
     scope 「Modify the ★packet construction and validation logic to inject or verify
             provenance keys (ds_input_id, ds_thread_id, dw_task_id, …)」
     steps 「★Identify the ★packet construction point in the codebase.」
★★＝ 停止事実 → 証拠取得 → 原因特定 → PLAN → 検査 まで ★Claude 0 で 到達。
★★＝ 『2DER は 設計できる』は ★もう 仮説では ない。
```

## 3. ★★止まる 所は ★毎回 同じ ―― **3回 再現**

```
GENERATE / REGENERATE:
  reason = "no provenance supplied (hand-authored packet / bypass)"
  runner_exit = null ／ runner_stdout_tail = null ／ artifact_sha256 = "" ／ diff = 0B
★★＝ runner が 一度も 動いていない ＝ ★試験が 一度も 走っていない。
```

## 4. ★★欠けている 能力（★証拠付き・★3つ・★1つ目が 最小）

```
★★① runner が 動かない（★最小・★これが 全部を 止めている）
   証拠 = 3件 とも 同じ reason ／ runner_exit=null
   従属する もの = ★実装 ／ ★試験 ／ ★『既存機構を 探索する』手順
     （★探索は PLAN の step に 書かれるが ★実行するのは 実装段 ∴ ★0回 しか 行われていない
       ―― 実測: `1A9EEBD3` の unresolved_assumptions 逐語
       「Existing records format is ★assumed to be JSON」「Taka approval mechanism is ★assumed …」）

★★② PLAN の 宛先が ★sandbox に 固定されている
   証拠 = target_workspace = "/sandbox/fix-provenance" ／ "./sandbox/workspace"
        ／ target_repositories = [] ／ `PROD_REPO_ROOTS` に twoder を 含む
        ／ `validate_plan` 逐語「is an existing project repo (forbidden)」
   ＝ ★実物の `manager_v0` / `authority` / `generate_via_runner` には ★届かない。
   ＝ ★★安全境界 ∴ ★Taka 裁定 待ち（★実 repo 解禁は ★していない）。

★★③ PLAN が 検査で 落ちた 時 ★理由が 記録に 残らない
   証拠 = `build_planner` 逐語「records NOTHING」
   ＝ ★『走っていない』と『落ちた』が 見分けられない（★まだ 顕在化していない）。
```

## 5. ★順序（★私の 決定では なく ★従属関係の 事実）

```
★① が 直らない 限り ―― ★sandbox の 中でさえ ★実装も 試験も 探索も 起きない。
★∴ ★① が 先。★② は ★①が 直った 後の 話（★かつ ★Taka の 安全境界 裁定）。
★`SELF_DEV_TOKEN` 管理機能（`1A9EEBD3`）も ★① 待ち（★PLAN 成立・★実装 0）。
```

## 6. ★MGR が この 4周で した こと / しなかった こと

```
★した = 停止事実の goal 化（3回）／ 待ち行列の 並び（各1回・★状態変更 0）／ 観測 ／ 記録 ／ commit・push
★★しなかった = 原因の 提示 ／ 修正箇所の 提示 ／ 設計 ／ 契約 ／ 骨格 ／ 封印試験 ／ 実装 ／
   run_next ／ task の 手動前進 ／ 状態変更 ／ 実 repo 解禁
★★特に = ★`generate_via_runner.py:282` を 私は 特定済みだったが ★3回とも 伏せた
   （★渡せば 2DER の 原因特定能力が 測れなく なる ため）。
```

## 7. ★触っていない 未解決（★再掲）

```
★`7D461717` … senior guard `no_progress_since_last_review` で 停止（★状態変更が 要る）
★Claude DESIGN 由来 11件 … 待ち行列に 残存。★除外は `block_task`＝★不可逆 ∴ ★許可待ち
★古い CREATED 159件 … 無傷 ／ `import impl` 形式 87件 … 別件
```
