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

## 4. ★★1件目の結果 ―― **2DER は 原因の在り処を 自分で 当てた。★repo に 届く 経路が 無い**

### ★2DER が 自力で 出した もの（★Claude は 原因も 直し方も 渡していない）

```
★PLAN identity = 2der-qwen-build-planner ／ 記録の 並び =
   CREATE → PROCESS_EVENT ×2 → ★PLAN → GENERATE → AUDIT → DISPOSE
   → UPPER_REVIEW → REGENERATE → AUDIT → DISPOSE
★runtime supervisor: attempts=4 ／ ladder 2048→4096→8192→8192
   finish_reasons ["length","length","length","stop"]（★3回 切れて 4回目で 完走）

★★scope（★逐語・★2DER が 書いた）:
  「Modify the ★packet construction and validation logic to inject or verify provenance keys
   (ds_input_id, ds_thread_id, dw_task_id, egl_open_gaps, egl_source_refs, rri_intent_id, etc.)
   and prevent runner execution when provenance is absent or malformed.」

★★steps（抜粋・逐語）:
  「Analyze the failure log to confirm the absence of provenance in the implementation packet.」
  「★Identify the ★packet construction point in the codebase.」
  「Implement logic to populate provenance fields from available sources …」

★test_body 先頭 = `from impl import validate_provenance`（★受入検査を 通る 形）
```

**★★＝ 私が 伏せていた 場所（`generate_via_runner` の ★packet 経路の 構築点）を
★2DER は 自分で 名指しした。★原因特定は ★到達した。**

### ★★到達できなかった所 ―― **★repo更新の 宛先が 構造上 存在しない**

```
★PLAN の 実際の 宛先:
   target_workspace   = ★"/sandbox/fix-provenance"
   target_file        = ★"impl.py"
   target_repositories= ★[]        files_expected = ["impl.py","test_impl.py"]
★★＝ 直す 対象は `twoder/generate_via_runner.py` なのに
   ★計画は ★sandbox の おもちゃ `impl.py` を 作る 話に なっている。
```

**★構造上の理由（★実測・逐語）:**

```
★`build_planner.PROD_REPO_ROOTS` =
   ('/home/takasan/egl','/home/takasan/ds','/home/takasan/rri',
    '/home/takasan/dev-workcell','★/home/takasan/twoder')
★`validate_plan` 逐語「workspace/scope: target_workspace %r is an existing project repo (forbidden)」
★★∴ ★『自分の repo を 直す PLAN』は ★記録され得ない（★fail-closed で 落ちる）
★加えて `contract_from_plan` は ★target_file が "impl.py" 以外を 受けない
★★∴ 2DER の 設計能力は ★sandbox の 単一ファイルに 閉じている。
```

### ★★もう1つ ―― **同じ欠陥が その修理経路を 塞いでいる**

```
★この 修理 task 自身の GENERATE / REGENERATE も
   reason = ★"no provenance supplied (hand-authored packet / bypass)"
   runner_exit = null ／ artifact_sha256 = ""
★★＝ ★provenance が 無いと GENERATE が 動かない ので
   ★★provenance を 直す task も ★GENERATE できない。
★★＝ ★自己開発ループが ★自分の 欠陥で 塞がっている（★循環が 閉じない）。
```

### ★段ごとの到達

| 段 | 結果 |
|---|---|
| 停止事実 → goal 化 | **★成立** |
| goal → 自力取得 | **★成立**（常駐が 待ち行列から 取得） |
| → 証拠取得・原因特定 | **★★成立**（★packet construction point を 自分で 名指し） |
| → PLAN | **★成立**（qwen ／ 受入検査を 通る test_body） |
| → 検査 | **★成立**（`validate_plan` 通過） |
| → GENERATE | **★不成立**（`no provenance supplied` ＝ ★直そうとしている 欠陥 そのもの） |
| → TEST/AUDIT | 実質 空振り（★runner 未起動） |
| → **repo更新** | **★★構造上 不能**（★宛先が sandbox に 固定・実 repo は 禁止） |
| → 再実走 | 未到達 |

## 4b. ★★欠けている能力（★証拠付き・★2つ）

```
★★① ★実 repo を 宛先に できない
   証拠 = `PROD_REPO_ROOTS` に twoder を 含む ／ `validate_plan` が forbidden で 落とす
        ／ `contract_from_plan` が target_file=="impl.py" 以外を 受けない
        ／ 実測 PLAN の target_workspace = "/sandbox/fix-provenance"
   ＝ ★repo更新→再実走の 循環が ★構造上 閉じない。

★★② ★修理経路が 修理対象に 依存している
   証拠 = 修理 task 自身の GENERATE/REGENERATE が ★同じ reason で 落ちる
   ＝ ★壊れている 部品を 使わないと ★その部品を 直せない。

★★③（★観測性）PLAN が 検査で 落ちた 場合 ★理由が 記録に 残らない
   証拠 = `build_planner` 逐語「records NOTHING」
   ＝ ★『走っていない』と『落ちた』が 見分けられない（★今回は 通ったので 顕在化せず）。
```

**★①②とも ★不可逆操作・安全境界・新しい設計判断に 当たる ∴ ★Taka への 上申事項。
★私は 直していません ／ 修正案も 書いていません。**

## 5. ★既知の未解決（★この運転の 外に 置いてある物）

```
★`7D461717` … JUDGE_REQUIRED ／ senior guard `no_progress_since_last_review` で 動かない
              ＝★状態変更なしでは 再実走できない（★触っていない）
★Claude DESIGN 由来 11件 … 待ち行列に 残っている。★除外には `block_task`（★不可逆）が 要る
              ＝★★Taka の 許可 待ち（★実行していない）
★古い CREATED 159件 … 無傷（★削除/BLOCKED/DONE/優先度変更 0）
★`import impl` 形式 87件（51%）… 契約変換を 通らない。★別件（★今回 広げない）
```
