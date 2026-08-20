# `mint_real_energize` 必須10欄 ―― ★出所の 全件照合（★実装 0 ／ ★DESIGN_HOLD）

**2026-08-20 20:1x ／ ★第一候補＝`authority.grant_approval`（`/api/approve`）／ ★実装しない**

---

## 0. ★探した 範囲

```
★`_REQUIRED_REQUEST_KEYS` の 10語 を ★1語ずつ ★本番コード 全件で 引いた
   （★`twoder` ／ `dev-workcell` ／ ★`runs/` `regression/` を 除く）
★併せて ★adjudication event 側の 必須欄（authority_owner / granted_by / attribution / expires_at）も 引いた
★approval token の 実体 = `authority.grant_approval` の 返り（★逐語で 確認）
```

---

## 1. ★★10欄の 出所（★approval由来 / patch由来 / Taka明示 / 欠落）

| # | 欄 | 分類 | 出所（★実測） |
|---|---|---|---|
| 1 | `item_id` | **★欠落** | ROADMAP に `item_id` は 在る が ―― ★`task_ids` を **書ける** 関数は `register_item`(新規)と `append_task_id` の 2つ。★**`task_id` から `item_id` を 逆引きする 関数は 本番に 無い** |
| 2 | `task_id` | **approval由来** | approval token に `task_id` が 在る（`grant_approval` 逐語） |
| 3 | `trace_id` | **patch由来（task 側）** | `knowledge_packet.provenance.trace_id`（CREATE payload）／ `build_planner:251` `qwen_worker:102` が 実際に 読んで いる |
| 4 | `repo_identity` | **★欠落** | 本番で **生産する 者が 無い**。`bridge_reconciler` は ★受け取って 写すだけ（`:132 :224 :248 :274`）／ `apply_cycle` は ★引数で 受ける |
| 5 | `repo_realpath` | **patch由来** | `os.path.realpath(repo_dir)`（`bridge_minter:79` が 自分で 計算し ★request と 一致を 要求） |
| 6 | `base_commit` | **patch由来** | `patch_bridge._head_commit(target_repo_dir)` |
| 7 | `allowed_files` | **patch由来** | `worker_output_to_artifact(…, files_changed, …)` の 1件 ／ PLAN の `allowed_files` |
| 8 | `fingerprint` | **patch由来** | `canonical_diff_artifact(...)['fingerprint']` |
| 9 | `token_id` | **★欠落** | 本番の 生産者 **0**。`_EnergizedApply.token_id` は ★mint の **返り** ／ `emit_patch_application` は ★`getattr(energize,'token_id')` で **読むだけ**。★request に 先に 要る 値の 出所が 無い |
| 10 | `adjudication_id` | **approval由来（★候補）** | `approval_id`（`APPROVAL-<sha1[:10]>`）を 充てられる ★但し §2 の 衝突 |

### ★adjudication event 側（★門2 が 見る 欄）

| 欄 | 分類 | 実測 |
|---|---|---|
| `authority_owner` | **★意味衝突** | mint は `== 'TAKA'` を 要求。approval は `approved_by = **"taka-credential"**`（`webui:97`）→ `.upper()` = `"TAKA-CREDENTIAL"` ≠ `"TAKA"` → **`MintRefused`** |
| `granted_by` | **★同上** | 同じ 値を 使う 限り 同じ 拒否 |
| `attribution` | **★同上** | ★fail-closed allowlist ＝ ★**`TAKA` 以外は すべて 拒否**（★空も 拒否） |
| `expires_at` | **★欠落** | `issue_approval` は `AUTH.grant_approval(..., approved_scope=…)` を **`expiry` を 渡さずに** 呼ぶ ∴ token の `expiry` は **`None`** → mint は 「adjudication has no expiry (fail-closed)」で **拒否** |

---

## 2. ★★意味衝突 ／ 責務衝突 ／ spoof ／ 永続性

### ★意味衝突（★2件・★どちらも 実測で 拒否に なる）

```
★① 識別子の 粒度が 違う
   ★approval  = 「★この task の ★この 操作種別を 許す」（task_id ＋ operation_class ＋ action_type）
   ★mint      = 「★この patch を 許す」（item_id ＋ repo_realpath ＋ base_commit ＋ fingerprint）
   ★★＝ ★patch が 1文字 変われば ★再裁定が 要る（`_BIND_MATCH` の 逐語「patch changes => re-adjudicate」）
   ★★approval は ★patch を 見て いない ∴ ★同じ token で ★別の patch を 通せて しまう。
   ★★＝ ★★これを そのまま 充てると ★安全性が 下がる（★私は 充てない）。

★② 主体の 表記が 違う
   ★approval  = `"taka-credential"`（★認証済み credential の 名前）
   ★mint      = `'TAKA'`（★人 そのもの）
   ★★＝ ★『credential を 持つ 者』と『Taka 本人』を ★同じ 語に すると ★意味が 潰れる。
```

### ★責務衝突

```
★`command_surface.INTERIM_APPROVERS = ("taka-credential",)` ―― ★逐語「★暫定の 道」。
★`is_human_approver`(★恒久の規則)は ★1文字も 触らない と 明記され、★`taka-credential` は
   ★★`HUMAN_APPROVERS` では なく ★`INTERIM_APPROVERS`(暫定)に 入って いる。
★★＝ ★approval の 承認者は ★『暫定で 人扱い』の 資格 ∴ ★★不可逆の 実 repo 変更の
   ★authority 源に 充てるのは ★層が 合わない（★階層性 violation に なる）。
```

### ★spoof 可能性

```
★approval 側 = ★★低い。★`APPROVED_BY` は ★webui の 定数で ★client body から 取らない
   （★逐語「approved_by = the AUTHENTICATED identity (taka), never taken from the client body (no spoofing)」）。
★mint 側     = ★★fail-closed allowlist ＋ `_FORBIDDEN_ATTRIB`（SELF/LLM/CLAUDE/AGENT/AUTO/MODEL/
   BRIDGE/RECONCILER/MINTER/SYSTEM）∴ ★自己発行は 構造上 通らない。
★★∴ ★spoof の 穴は ★見つからなかった。★危険なのは spoof では なく ★①の 粒度。
```

### ★再起動後の 永続性

```
★approval = ★DS event stream（`record_utterance` ＋ `record_dialogue_event(event_type=…, run_meta=token)`）
   ＝ ★file ∴ ★再起動後も 残る。★`approval_consumed` が `load_events()` で 読み直して いる（★単回使用の 保証）。
★★∴ ★永続性は ★問題 無い。
```

---

## 3. ★★判定 ―― DESIGN_HOLD（★出所不明が **3欄**）

```
★★欠落 = ★`item_id` ／ `repo_identity` ／ `token_id` ／（＋adjudication の `expires_at`）
★★意味衝突 = ★`authority_owner` / `granted_by` / `attribution`（★"taka-credential" ≠ "TAKA"）
★★∴ ★1欄でも 出所不明なら DESIGN_HOLD ―― ★★3欄 不明 ∴ ★DESIGN_HOLD。
★★私は ★欄を 埋めない ／ ★値を 決めない ／ ★実装しない。
```

## 4. ★今回の 調査の 自己評価

```
★★良かった 点 = ★『10欄を 1語ずつ 全件で 引く』と したので
   ★★『approval を adjudication に 充てる』が ★★2つの 理由で 成り立たない ことが
   ★実装前に 出た（★粒度 ／ ★主体の 表記）。
★★もし 欄を 数えずに 「approval が 在るから 使える」と 進んで いたら
   ★`MintRefused` を 実走で 踏んで から 気づいた（★今日 既に 同型を 2度 やって いる）。
★★不足 = ★`item_id` の 逆引きは ★『関数が 無い』ことまでは 確認した が
   ★★ROADMAP の 実データを 走査すれば 引けるかは ★試して いない（★UNVERIFIED）。
```

## 5. ★していないこと

```
★実装 0 ／ コード 0行 ／ repo 変更 0 ／ 語彙追加 0 ／ 発行口 0
★`taka-credential` を `TAKA` に 読み替えて いない ／ ★expiry を 決めて いない
★SELF_DEV_TOKEN = ★5/5
```
