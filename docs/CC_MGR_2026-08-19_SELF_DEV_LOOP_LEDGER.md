# 宛: Taka ―― **2DER 自己開発ループ 実走台帳**（★停止点を開発入力へ戻す運転）

**開始 2026-08-19 22:36 ／ ★Taka 運転変更「停止を Claude の仕事開始条件にしない」**

---

## 0. この文書の役割

```
★★測るのは ★個別バグの 修正では ない。
★★測るのは ★『人が goal を 与えた後、2DER が 自分の 停止点を 次の 開発課題へ 変換し、
   repo更新・再実走まで 循環できるか』。
★1件 解消する ごとに ★次の 停止点を ★次の 入力へ 戻す。
★Claude が 代行しないと 進まない 箇所に 当たったら ★代行せず 停止し、
   ★『自己開発ループの どの能力が 欠けているか』だけを 証拠付きで 書く。
```

## 1. ★Claude(MGR) の役割（★この運転では 4つだけ）

```
① 2DER が どこまで 自力で 進んだかの 観測
② 正規記録による 事実確認
③ ★自己開発ループそのものの 欠落の 特定
④ 不可逆操作・安全境界・新しい設計判断の Taka への 上申
★禁止 = 設計者・実装者・問題解決者に なること ／ 先回りして 修正案・契約・test_body・
        skeleton・実装を 書くこと ／ Claude DESIGN への 復帰（★例外は Taka の 明示許可のみ）
```

## 2. ★実走 1件目

| 欄 | 値 |
|---|---|
| task | **`TASK-2DER-76070397`**（2026-08-19 22:36:57） |
| 戻した停止事実 | `GENERATE`/`REGENERATE` が `reason="no provenance supplied (hand-authored packet / bypass)"` で失敗／`runner_exit=null`／`artifact_sha256=""` ＝ **runner が一度も動いていない** |
| 出所 | `TASK-2DER-3CF23D43`（★その前の実走） |
| 渡した物 | **観測事実だけ**（理由の語 ／ 一つ前は `SPEC_INCOMPLETE_NO_CONTRACT` だった差分 ／ PLAN の packet に provenance が在る事と鍵名） |
| **渡していない物** | **★原因 ／ ★直し方 ／ ★触る file ／ ★骨格 ／ ★封印試験 ／ ★実装** |
| MGR が触った物 | **待ち行列の並び 1回だけ**（★状態変更 0 ／ 他 task 未接触） |

**★MGR が 伏せた事実（★意図的・★開示）:**

```
★私は 既に `generate_via_runner.py:282` の packet 経路が provenance を 詰めていない事を
  ★特定していた（★2026-08-19 の 前段で 実測済み）。
★★これを goal に 書かなかった。
   理由 = 書くと ★『Claude が 原因を 特定し 2DER に 手を 動かさせる』形に なり、
   ★『2DER が 自分で 原因特定まで 到達できるか』が ★測れなくなる ため。
★★∴ この1件の 結果は ★2DER の 原因特定能力の 実測に なる。
```

## 3. ★先に開示する危険（★断定ではない・★見に行く点）

```
★`validate_plan` は `target_workspace` が ★既存の project repo だと ★不合格に する
   逐語「workspace/scope: target_workspace %r is an existing project repo (forbidden)」
★★もし これが 効くと ★2DER は 『自分の repo を 直す PLAN』を ★構造的に 立てられない。
★★それが 本当なら ★それが 『自己開発ループの 欠落』の ★第一候補。
★★但し ★1回の 観測で 断定しない ―― ★実際に 何が 出るかを 見る。
```

## 4. ★観測欄（★追記していく）

| 段 | 見る物 | 1件目の結果 |
|---|---|---|
| 停止事実 → goal 化 | task が立つか | **★成立**（`CREATED`） |
| goal → 自力取得 | 常駐が拾うか | （観測中） |
| → PLAN | identity ／ `target_file` ／ `target_workspace` ／ `scope` | （観測中） |
| → 検査 | `validate_plan` ／ 受入検査 | （観測中） |
| → GENERATE | `runner_exit` ／ artifact | （観測中） |
| → TEST/AUDIT | 合否 | （観測中） |
| → **repo更新** | 実 repo に 届くか | （観測中） |
| → 再実走 | 元の停止が 消えるか | （観測中） |

## 5. ★既知の未解決（★この運転の 外に 置いてある物）

```
★`7D461717` … JUDGE_REQUIRED ／ senior guard `no_progress_since_last_review` で 動かない
              ＝★状態変更なしでは 再実走できない（★触っていない）
★Claude DESIGN 由来 11件 … 待ち行列に 残っている。★除外には `block_task`（★不可逆）が 要る
              ＝★★Taka の 許可 待ち（★実行していない）
★古い CREATED 159件 … 無傷（★削除/BLOCKED/DONE/優先度変更 0）
★`import impl` 形式 87件（51%）… 契約変換を 通らない。★別件（★今回 広げない）
```
