# 実 repo 反映 一本 ―― ★未確定事項の 一括調査（★止まらず 最後まで 追った ／ ★実装 0）

**2026-08-20 20:3x ／ ★Taka 指示「小刻みに上申するな。全部列挙して一括調査しろ」**
**★埋まった = 14 ／ ★埋まらない = 4（★最後に まとめて 上申）**

---

## 1. ★★埋まった もの（14件 ―― ★もう 聞きません）

| # | 未確定だった もの | ★確定した 答え（実測） |
|---|---|---|
| 1 | `task_id` の 出所 | approval token が 持つ（`grant_approval` 逐語） |
| 2 | `trace_id` の 出所 | `knowledge_packet.provenance.trace_id`（CREATE payload）。`build_planner:251` `qwen_worker:102` が 実際に 読む |
| 3 | `repo_realpath` | `os.path.realpath(repo_dir)`。`bridge_minter:79` が 自分で 計算し ★request と 一致を 要求 |
| 4 | `base_commit` | `patch_bridge._head_commit(target_repo_dir)` |
| 5 | `allowed_files` | `worker_output_to_artifact(…, files_changed, …)` の 1件（★単一 file 制約） |
| 6 | `fingerprint` | `canonical_diff_artifact(...)['fingerprint']` |
| 7 | **`token_id` は 誰が 作るか** | ★**呼び手が 先に 作る 自由な 識別子**。mint は ★`_token_id_consumed` で **単回使用だけ** 検査し、★`_EnergizedApply(token_id=request['token_id'])` に **そのまま 載せて 返す**（★生産者が 本番に 無いのは ★呼び手が 決める 値 だから） |
| 8 | **`repo_identity` は 誰が 作るか** | ★同じく **呼び手が 決める 名前**。`_mint_test_energize` の 既定は `'throwaway'`／`bridge_reconciler` は ★受け取って 写すだけ |
| 9 | **`item_id` は 逆引きできるか** | ★**走査で 可能**（実測：ROADMAP 148 item を 走査 → `D7977C1A` は `EVO-0080` `EVO-0081` に 逆引きできた）★但し §2-② |
| 10 | **`kind` の 位置ずれを どう 埋めるか** | ★**呼び手が 正規化する**。`event_log` は ★引数で 注入 ∴ DW の `{payload:{kind:…}}` を `{kind:…, payload:{…}}` に 決定論で 写せば よい。★`bridge_minter:126,148` は ★同じ `event_log` を reconciler へ 渡す ＝ ★1回 正規化すれば 両方に 効く |
| 11 | **書き込みの 縛り方** | `patch_bridge._require_energize`（逐語「A write is impossible without a genuine `_EnergizedApply` whose grant authorizes THIS workspace_dir」）＋ `_confined_path`（`../`・symlink の 脱出を 拒否） |
| 12 | **dry-run の 合否** | `dry_run_ok(files, expected_preimages, allowed_files)` → `{proceed, reason, names}`（★2DER が 書いた 部品） |
| 13 | **rollback の 合否** | `rollback_allowed(existed, post_apply_sha, disk_sha, preimage_sha)` → `{restore, reason}`（★本日 実走で `ROLLED_BACK` を 確認済み） |
| 14 | **再実走 と COMPLETE** | `run_until_barrier` → `dispatch:77` → `webui:1592` → `return_loop` → `propose_complete:597`（★blocker が 空の ときだけ 通す） |

```
★★＝ ★patch 側は ★★全部 揃って いる。★書き込み・確認・戻し・記録・再実走・完了 まで
   ★★部品も 判定も 実在し ★本日 throwaway で 一周 回して 確認済み。
```

---

## 2. ★★埋まらない もの（4件 ―― ★これだけ 上申します）

### ★① `attribution` / `authority_owner` / `granted_by` が **`TAKA` に ならない**

```
★実測 = `/api/approve` が 使う 承認者は ★`APPROVED_BY = "taka-credential"`（`webui:97`）
★mint  = ★`.upper() == 'TAKA'` を ★3欄すべてに 要求（★fail-closed allowlist ／ ★空も 拒否）
★★`"taka-credential"` → `"TAKA"` に 変換する 実装は ★★本番に **0件**（★全件検索）
★★さらに ★`HUMAN_APPROVERS = ("taka",)` ／ ★`INTERIM_APPROVERS = ("taka-credential",)`
   ＝ ★`taka-credential` は ★★『恒久の 人』では なく ★『暫定の 道』（逐語）
★★∴ ★『credential を 持つ 者』を『Taka 本人』と 同一視して よいかは ★★Taka の 価値判断。
   ★私が 読み替えると ★authority を 私が 決めた ことに なる ∴ ★しない。
```

### ★② `item_id` が **この task には 無い**

```
★実測 = ROADMAP 148 item の うち ★`task_ids` を 持つのは **6件** だけ。
★`D7977C1A` → `EVO-0080` `EVO-0081`（★逆引きできた）
★`9EDC4F8A` → ★★無し（★第四の task は どの item にも 紐付いて いない）
★★∴ ★『どの item の 権限で この repo を 変えるのか』が ★決まらない。
★★item を 立てる／既存 item に 紐付ける のは ★管理の 判断 ∴ ★私は 決めない。
```

### ★③ `expires_at` を **誰も 設定しない**

```
★実測 = `command_surface.issue_approval` の 引数に ★`expiry` が **無い**
   → `AUTH.grant_approval(..., approved_scope=…)` を ★expiry 抜きで 呼ぶ ∴ token の `expiry` は **`None`**
★mint  = 「adjudication has no expiry (fail-closed)」で ★拒否
★★∴ ★『裁定は 何分/何時間 有効か』は ★★Taka が 決める 値（★私が 決めると 安全境界を 私が 引く）。
```

### ★④ 裁定 event を **どこに 永続するか**

```
★実測 = ★`{kind, payload}` を そのまま 保存できる 本番面は ★★無い
   ・DW `record_process_event` … ★`kind` を ★payload の 中に 入れる ／ ★語彙 9語に 該当語 無し
   ・DS event stream            … ★`event_type` ＋ `run_meta`（★approval が 使って いる）
   ・human_escalation_ledger / EGL / ROADMAP … ★`kind` 欄 無し
★★但し ―― ★`event_log` は 注入 ∴ ★★『どこに 置くか』と『どう 読ませるか』は 分けられる。
   ★どの 面に 置いても ★呼び手が 正規化すれば mint は 読める（★§1-10 で 確定）。
★★∴ ★残る 判断は ★『どの 面を 正本と するか』の **1つだけ**（★語彙を 増やすか ／ 既存面に 載せるか）。
   ★これは ★authority 境界の 置き場 ∴ ★★Taka の 決め事。
```

---

## 3. ★設計案は 出しません（★ご指示どおり）

```
★★4件が 埋まって いない ∴ ★『全項目が 埋まった時だけ 設計案を 出せ』に 従い ★出しません。
★★但し ★4件は ★すべて ★★『値の 決定』か『置き場の 決定』で あって ★調査で 埋まる 物では ない:
   ①`taka-credential` を `TAKA` と 認めるか       … ★価値判断
   ②この task に どの item を 当てるか            … ★管理判断
   ③裁定の 有効期限を 何に するか                 … ★安全境界
   ④裁定を どの 面に 置くか                       … ★authority 境界
★★＝ ★★4つとも ★Taka 以外に 決められない。★調べ足りない のでは ない。
```

## 4. ★探した 範囲（★「無い」の 根拠）

```
★`TAKA` の 文字列（全件・`takasan` を 除外）→ ★変換実装 0件
★`grant_approval(` の 呼び手（全件）→ ★本番は `command_surface:69` の 1件のみ（★expiry を 渡さない）
★`task_ids` を 書く 関数（全件）→ `register_item` と `append_task_id` の 2つ
★`kind` を 読む 者（全件）→ `bridge_minter` 4箇所 ／ `bridge_reconciler` 4箇所 ＝ ★すべて **直下**
★`_require_energize` / `_confined_path` / `dry_run_ok` / `rollback_allowed` … ★実体を 読んだ
★対象 = twoder / dev-workcell（★`runs/` `regression/` を 除く）
```

## 5. ★していないこと

```
★実装 0 ／ コード 0行 ／ repo 変更 0 ／ 語彙追加 0 ／ 発行口 0 ／ 設計案 0
★`taka-credential` を 読み替えて いない ／ 有効期限を 決めて いない ／ item を 立てて いない
★SELF_DEV_TOKEN = ★5/5
```
