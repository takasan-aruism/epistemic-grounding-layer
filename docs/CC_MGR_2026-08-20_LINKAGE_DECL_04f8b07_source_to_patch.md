# 連動性 照合 ―― `04f8b07` 生成source → unified diff → `apply_cycle`

**2026-08-20 17:1x ／ ★指示書 §13 第二 ／ ★実装 0 ／ repo 変更 0**
**★結論を 先に: ★★declared / observed 不一致 ∴ ★COMPLETE に しない。★但し ★復旧対象では ない（★§9 判断）。**

---

## 1. 14項目（★取得できない 欄は 想像で 埋めない）

| # | 項目 | declared | observed（実測） |
|---|---|---|---|
| 1 | **UPSTREAM** | **★ABSENT** ―― ★私は 上流を 決めずに 部品を 置いた | **★呼び手 0件**（`source_to_patch` / `apply_generated_source` / `source_to_artifact` / `make_diff_body` すべて 本番 0） |
| 2 | **TRIGGER** | **★ABSENT** | ― |
| 3 | INPUT | `workspace_dir, target_relative_path, new_source, base_commit, energize, recorder, task_id, ts, repo_identity, test_passed` | 同左（★署名で 確認） |
| 4 | PRECONDITION | 対象 file が workspace に 在る ／ `energize` は 呼び手が 用意 ／ 実 repo なら Taka 裁定 | 実測済（`TARGET_MISSING` が 返る ／ 実 repo は throwaway minter が 拒否） |
| 5 | OUTPUT | `{stage, artifact, reason, cycle}` ＋ `PATCH_APPLICATION` 記録 | 実測済（`CONFIRMED` / `APPLIED`） |
| 6 | **DOWNSTREAM** | `apply_cycle` → `emit_patch_application` → recorder | **★上流が 居ない ∴ ★本番では 1度も 届いて いない** |
| 7 | STOP | `cycle.stage == "CONFIRMED"` | 実測済（throwaway で file が 実際に 書き換わった） |
| 8 | FAILURE_ROUTE | `TARGET_MISSING` / `NO_DIFF` / `ROLLED_BACK` | 実測済（`test_passed=False` → `ROLLED_BACK`・中身は 元の まま） |
| 9 | **RECHECK/RETRY/ESCALATE** | **★ABSENT** ―― ★宣言して いない | ― |
| 10 | PERSISTENCE | 自前の 永続 0（★`recorder` を 呼び手が 渡す 前提） | 同左 |
| 11 | AUTHORITY | ★発行しない。`energize` は 引数。実 repo は `bridge_minter` の Taka 門 | 実測済（実 repo 2件を 渡すと 拒否） |
| 12 | EVIDENCE | `PATCH_APPLICATION` 記録 ／ artifact fingerprint | 実測済（`394f3b24…`） |
| 13 | ROLLBACK | `apply_cycle` の rollback ／ `git revert 04f8b07` | 実測済（`ROLLED_BACK`） |
| 14 | **ROUTE_STAGE** | **★ABSENT** ―― 経路表 18行に `source_to_patch` も `apply_cycle` も 出ない | 同左（★段を 作らない） |

## 2. ★照合の 結論

```
★★上流から 呼ばれて いない ＝ ★★連動は 成立して いない。
★『関数が 在る』『throwaway で 一周 回った』は ―― ★指示書 §5 逐語 ―― ★証拠に しない。
★★∴ ★`04f8b07` は ★COMPLETE に しない。
```

## 3. ★では 直すのか ―― **★直しません（★理由を 実測で）**

```
★指示書 §2-B = ★復旧対象は 「★それが 在る ため 2DER へ 仕事を 渡せない」もの に 限る。
★指示書 §12 の 終了条件 7つ を 1つずつ 当てた:
   ①正規入口から 渡せる          … ★`source_to_patch` の 有無に 依らない
   ②2DER が 工程を 進められる    … ★依らない（PLAN→GENERATE→AUDIT は 動いて いる）
   ③進行不能 task が 全体を 止めない … ★依らない（★`377c85c` で 解消済）
   ④正規停止・再試行・上申       … ★依らない
   ⑤経路表・連動性を 無視できない … ★依らない
   ⑥declared/observed 不一致で COMPLETE に できない … ★依らない
   ⑦正規記録から 確認できる      … ★依らない
★★∴ ★これが 無くても ★主体移管は できる。
★★∴ ★指示書 §9 に 従い ★★移管後へ 送る。★いま 上流を 足すのは ★新機能追加。
★★∴ ★指示書 §14「全部 直してから 渡す」を しない。
```

## 4. ★残す 事実（★隠さない）

```
★`04f8b07` は ★『部品は 在る が 本番の 呼び手が 0』の 状態で 残る。
★★これは ★`mint_real_energize` ／ `escalation_router`(★接続前)と ★同じ 型。
★★∴ ★移管後の 2DER が ★最初に 拾える 形で ★ここに 明記して 残す。
★★私は ★上流を 想像で 決めない（★配置先を Claude が 指定しない=★既存の 裁定）。
```
