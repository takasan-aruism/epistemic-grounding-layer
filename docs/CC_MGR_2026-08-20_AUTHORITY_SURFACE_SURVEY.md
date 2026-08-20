# 実 repo 反映の **authority 側** 調査 ―― ★全件検索・作用ベース（★実装 0 ／ ★停止して 返す）

**2026-08-20 20:0x ／ ★確定する 未確定値は 1つ ―― 「Taka の 裁定を どの 既存 記録面から `ENERGIZATION_ADJUDICATION` として 発行するのが 整合するか」**

---

## 0. ★探した 範囲（★「無い」と 言う 前に 書く）

```
★作用A『人が 承認/裁定を 書く』  = granted_by / authority_owner / adjudicat / approval / approve   … 全件
★作用B『authority を 検証する』  = authority.py の gate / validate_approval / consume            … 全件
★作用C『event を 永続化する』    = _append_event / record_utterance / record_dialogue_event /
                                   _append(jsonl) / open_escalation                              … 全件
★作用D『後から 引ける』          = /api/resolve / /api/pending_approvals / states() / load_events … 全件
★作用E『実 repo が 変わる』      = git add/commit / shutil.copy / place / _place_and_commit       … 全件（前回）
★対象 = twoder / dev-workcell / egl/egl / rri/rri / ds/ds（★`runs/` `regression/` を 除く＝本番のみ）
★★regression と sandbox 成果は ★正本判断に 使って いない。
```

---

## 1. ★★`mint_real_energize` が 求める 形（★実測・逐語）

```
★読み方: `for e in event_log: if e.get('kind') == 'ENERGIZATION_ADJUDICATION' and _p(e).get('adjudication_id')…`
         `_p(e) = e.get('payload')`
★★＝ ★`kind` は ★★event の 直下 ／ ★中身は `payload` の 中。
★payload に 要る 欄（★門 2/2' の 実測）:
   adjudication_id / authority_owner / granted_by / attribution / expires_at
   ＋ ★request と 一致すべき 4欄 = item_id / repo_realpath / base_commit / fingerprint
   ＋ allowed_files
★★`event_log` は ★★引数で 注入される ＝ ★出所を mint は 選ばない（★呼び手が 選ぶ）。
★同じ 約束を `bridge_reconciler` も 使う（`:246,:261,:264,:272` すべて `e.get('kind')`）。
```

---

## 2. ★候補（★作用で 引いた ―― ★名前で 引いて いない）

| 候補 | 誰が書く | authority の出所 | 何を保存 | どこに永続 | 誰が読む | 再起動後 | 正規API | **mint が そのまま 読めるか** |
|---|---|---|---|---|---|---|---|---|
| **① `authority.grant_approval`**（`/api/approve`） | webui → `CMDS.issue_approval` | **★認証済み identity**（逐語「approved_by = the AUTHENTICATED identity (taka), never taken from the client body (no spoofing)」） | `{approval_id, action_type, task_id, operation_class, approved_scope, approved_by, approved_at, single_use, expiry}` | **DS event stream**（`record_dialogue_event(event_type=…, run_meta=token)`） | `approval_registry` / `approval_consumed` | ★残る（file） | `/api/pending_approvals` | **★✕** ―― `kind` 欄が 無い（`event_type`）／ `repo_realpath` `base_commit` `fingerprint` `allowed_files` `attribution` を 1つも 持たない |
| **② DW `record_process_event`** | 任意（`identity` 付き） | ★**無い**（★逐語「これは authority では ない」＝ 私が 8/20 に 追加した 語の 注記） | `payload = {"kind": kind, **payload}` | **events.jsonl**（append-only） | `derive_process_trace` / 私の `_observed_edges_of` | ★残る | `/api/resolve` | **★✕（形）** ―― `kind` が **payload の 中**。mint は **直下**を 見る ／ **★語彙(9語)に `ENERGIZATION_ADJUDICATION` が 無い** |
| **③ `human_escalation_ledger`** | `open_escalation` / `resolve_escalation` | ★**人の 決定**（`user_decision`）★但し 呼び手が 名乗るだけ | `{event_type, human_escalation_id, parent_item_id, trigger_state, …, user_decision}` | `twoder/audit/HUMAN_ESCALATION_LEDGER.jsonl`（append-only） | `states()` / `aggregate()` | ★残る | ★`/api/resolve` 経由は 未確認（**UNVERIFIED**） | **★✕** ―― `kind` 欄 無し ／ patch 4欄 無し |
| **④ EGL `admit_design_evidence`** | `submit` 経路 | `decision_owner`（★必須欄） | `{observation, decision, decision_owner, …}` | `rri/DESIGN_EVIDENCE_LEDGER.jsonl` | `resolve_admission` | ★残る | `/api/resolve` | **★✕** ―― patch 4欄 無し |
| **⑤ ROADMAP `set_authority`** | `roadmap_registry` | `TIERS`（OBSERVE/REVERSIBLE/IRREVERSIBLE）＋`note` | item 行 | `twoder/audit/ROADMAP_REGISTRY.jsonl` | `resolve` / `history` | ★残る | **★`/api/resolve?id=ITEM-…&history=1`（★本日 6回 実測）** | **★✕** ―― `kind` 欄 無し ／ patch 4欄 無し |

**★★どの 候補も ★そのままでは mint が 読めない。★理由は 2つに 分かれる:**

```
★理由X（★形）= ★`kind` が 直下に 無い（①③④⑤）／ payload の 中に 在る（②）
★理由Y（★中身）= ★patch に 縛る 4欄（item_id / repo_realpath / base_commit / fingerprint）と
                 `allowed_files` `attribution` `expires_at` を ★★どの 面も 持って いない
★★∴ ★『発行口を どこに 置くか』の 前に ★★『patch に 縛られた 裁定』という 情報が
   ★2DER の どの 記録面にも ★存在しない ―― ★これが 本当の 欠落。
```

---

## 3. ★★3指標（★総合点に 潰さない ／ ★分母・分子・欠損 ID を 残す）

### 対称性（reader に 対する writer が 在るか）

```
★必須 counterpart = 5  ／ ★実在 counterpart = 2  ／ ★missing = 3
  ✔ PATCH_APPLICATION            reader=bridge_minter(3a) / bridge_reconciler   writer=patch_bridge.emit_patch_application
  ✔ RECONCILIATION_BALANCED/_IMBALANCED  reader=latest_balance_proof            writer=bridge_reconciler.emit_reconciliation
  ✘ ENERGIZATION_ADJUDICATION    reader=bridge_minter:50                        writer=★★0（全件検索）
  ✘ ENERGIZATION_REVOCATION      reader=bridge_minter:57                        writer=★★0（全件検索）
  ✘ ENERGIZED token 消費         reader=bridge_minter:66(token_id)              writer=★実 repo 経路が 動いて いない ∴ 0
★★欠損 ID = ENERGIZATION_ADJUDICATION / ENERGIZATION_REVOCATION / real-token PATCH_APPLICATION
```

### 連動性（declared / observed / broken）

```
★declared edge = 6
   Taka裁定 → adjudication record → mint_real_energize → source_to_patch → apply_cycle → 実repo
★observed edge = ★★0
★broken edge  = ★★4
   ✘ Taka裁定 → adjudication record      （★writer 0）
   ✘ adjudication → mint_real_energize   （★読む 形の 記録が 無い）
   ✘ mint → source_to_patch              （★source_to_patch の 本番 caller 0）
   ✘ source_to_patch → apply_cycle       （★apply_cycle の 本番 caller 0）
★★＝ 0/6。★1本も 通って いない。
```

### 階層性（境界が 正しい 層に 在るか）

```
★required boundary = 4 ／ ★passed = 3 ／ ★violation = 0 ／ ★unreachable = 1
  ✔ authority は Taka のみ（`attribution != TAKA` を fail-closed allowlist で 拒否）… 実装が 在る
  ✔ 自己発行の 禁止（`_FORBIDDEN_ATTRIB` に SELF/LLM/CLAUDE/AGENT/AUTO/MODEL/BRIDGE/RECONCILER/MINTER/SYSTEM）… 在る
  ✔ repo 変更責務は patch 層（`apply_cycle`／`patch_bridge`）に 在る … 在る
  ☐ ★『裁定を 与える 層』が ★★空（★人が 与える 口は ①に 在る が ★patch に 縛られない）
★★violation は 0 ―― ★★誰も 境界を 破って いない。★★破れない ので 誰も 通れて いない。
```

---

## 4. ★★DESIGN_HOLD（★ご指示どおり 停止）

```
★埋まらない 欄 = ★『patch に 縛られた 裁定（item_id / repo_realpath / base_commit / fingerprint /
   allowed_files / expires_at / attribution）を ★誰が 作るか』。
★★これは ★『どの 面に 置くか』の 話では ない ―― ★★その 情報を 作る 者が 居ない。
★★∴ ★私は 選ばない。★語彙も 増やさない。★実装しない。
```

---

## 5. ★今回の 調査は 良かったか（★ご指示の 自己評価）

**★良かった。★理由は 起点の 置き方を 変えた こと。**

```
★前回（外した とき）= ★『自分が 作った 部品(`source_to_patch`)の 呼び手』を 起点に 数えた
   → ★同じ 作用を 持つ 別の 機構（`_place_and_commit`）を ★丸ごと 見落とした。
★今回                = ★『実 repo が 変わる』『人が authority を 与える』という ★★作用を 起点に した
   → ★`_place_and_commit`（稼働中）を 発見 ／ ★`/api/approve`＝`authority.grant_approval`（稼働中）を 発見
   → ★さらに ★★形の 食い違い（`kind` が 直下か payload の 中か）まで 降りられた。
★★＝ ★『部品名で 引く』を やめ ★『作用で 引く』に した のが 効いた。
★★＝ ★不足して いた のは ★検索範囲では なく ★★検索の 起点 だった。
```

**★足りなかった 観測面（★正直に）:**

```
★③`human_escalation_ledger` が ★`/api/resolve` から 引けるかは ★★未確認（UNVERIFIED）。
   ★本日 私は `states()` を モジュール経由で 読んだ が ★正規 API 経由では 引いて いない。
```

## 6. ★していないこと

```
★`PROCESS_EVENT_KINDS` への 語追加 0 ／ authority 発行口の 実装 0
★`source_to_patch` 本線接続 0 ／ `apply_cycle` 本番接続 0
★実装 0 ／ コード 0行 ／ repo 変更 0 ／ 投入 0 ／ ★候補を 選んで いない
★SELF_DEV_TOKEN = ★5/5
```
