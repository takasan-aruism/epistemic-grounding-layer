# 宛: Taka / 設計 / 監査 ―― delegated energize の最小設計（★実装 0・実 repo へ書き込み 0）

**Taka 裁定（2026-08-19 15:0x）を受けた材料整理。★MGR は実装していない。★実 repo に書いていない。**
**`bridge_minter` / `bridge_reconciler` を走らせていない。**

---

## ① ★delegated energize の正確な境界

### ★Taka が先に固定するもの（★`authority.grant_approval` で1回だけ）

**既存の返り（★実物・`authority.py:153-155`）:**

```python
token = {"approval_id": "APPROVAL-<sha1[:10]>", "action_type": …, "task_id": …,
         "operation_class": …, "approved_scope": approved_scope or [operation_class],
         "approved_by": …, "approved_at": ts, "single_use": True, "expiry": expiry}
```

**★Taka 指定の8つを、★どこに置くか（★新しい欄を作らない）:**

| 束縛 | 置き場 | 既存か |
|---|---|---|
| `repo_identity` | **`approved_scope`** の中 | ★既存欄（自由な一覧） |
| `repo_realpath` | **`approved_scope`** の中 | ★同上 |
| `allowed_files` | **`approved_scope`** の中 | ★同上 |
| authority ceiling | `authority.item_ceiling(item_id)` で別途照合 | **★既存関数** |
| `expiry` | **`expiry`** | **★既存欄**（`validate_approval` が検査） |
| `single_use` | **`single_use`** | **★既存欄**（`approval_consumed` が durable） |
| rollback required | **`approved_scope`** の中（語1つ） | ★既存欄 |
| test/audit required | **`approved_scope`** の中（語1つ） | ★既存欄 |

```
★`action_type` を ★energize 専用の 1語に する（★例: 'ENERGIZE_PATCH'）
   → ★`validate_approval` が ★action_type 一致を 見る ∴ ★他の 用途の token が 流用できない
   ＝★★『energize 専用 scope として 一意に 解釈できる』という Taka の 要求を ★既存の 検査で 満たす
★★新しい 台帳 0（★GRANT / CONSUMED は ★DS の event stream に 既に 残る）
```

### ★2DER が patch ごとに出すもの（★`ENERGIZATION_ADJUDICATION` 1件）

**★既存の門が読む欄を、★そのまま埋める（★形は変えない）:**

```
authority_owner  = 'TAKA'      ← ★権限の 所有者は Taka のまま（★2DER は 所有しない）
granted_by       = 'TAKA'      ← ★委任の 出所は Taka
attribution      = '2DER'      ← ★★ここだけが 現行と 違う（★§②の 1点）
★approval_id      = <Taka の token の approval_id>   ← ★★新しく 名指す（★委任の 連鎖）
item_id / repo_identity / repo_realpath / base_commit
★fingerprint      = ★実際の patch の canonical fingerprint（★見てから 書く）
allowed_files    = ★Taka の approved_scope の 範囲内
expires_at       = ★Taka の token の expiry を ★超えない
```

**★境界（★MGR が言い切れる形）:**

```
★2DER が できること = ★Taka が 切った 範囲の 中で ★実際の patch を 見て ★1件の 裁定を 書く
★2DER が できないこと:
   ・repo / allowed_files / ceiling / expiry を ★広げる（★token の scope 外は validate が 落とす）
   ・自分で token を 作る（★`grant_approval` の approved_by は Taka）
   ・fingerprint を 後から 変える（★門(2') が 突き合わせる）
   ・同じ token を 2回 使う（★`single_use` ＋ ★BIND-3 の token_id 消費＝★二重）
```

---

## ② ★`bridge_minter` の最小変更点 ―― **★1箇所（89-100行）**

**現行（★実物）:**

```python
if str(ap.get('authority_owner','')).upper() != 'TAKA': raise MintRefused('authority_owner != TAKA')
if str(ap.get('granted_by','')).upper()     != 'TAKA': raise MintRefused('granted_by != TAKA')
attribution = str(ap.get('attribution','')).upper()
if attribution != 'TAKA':                       # ★ここだけが 委任を 弾いている
    raise MintRefused('attribution must be TAKA …')
if attribution in _FORBIDDEN_ATTRIB: raise MintRefused(…)
```

**★最小変更（★語で書く・★実装しない）:**

```
★`authority_owner == 'TAKA'` と `granted_by == 'TAKA'` は ★そのまま（★変えない）
★`attribution` の 判定を ★2分岐に する:
   (a) 'TAKA'  → ★従来どおり 受理（★★既存経路は 1文字も 変わらない）
   (b) '2DER'  → ★次を ★すべて 満たす時だけ 受理:
        ・`ap['approval_id']` が 在る
        ・その token を ★`authority.validate_approval(token, 'ENERGIZE_PATCH', task_id, operation_class, now_ts)`
          が ★ok（★★既存関数・★新規 0）
             → action_type 一致 ／ ★expiry 内 ／ ★未消費（single_use）
        ・`approved_scope` に ★repo_identity / repo_realpath / allowed_files が 含まれる
        ・`authority.item_ceiling(item_id)` が ★この行為を 許す 段に 在る
        ・★`approved_scope` に ★rollback required と test/audit required の 語が 在る
   (c) それ以外 → ★従来どおり 拒否（★`_FORBIDDEN_ATTRIB` は ★そのまま 残す）
★★`consume_approval(token, ts)` を ★どこで 焼くかは ★設計の 判断（★MGR は決めない）
   ―― ★候補: mint 成功時 ／ ★PATCH_APPLICATION が APPLIED を 記録した 時
```

**★変えない門（★5つ）**: (1) 記録の実在 ／ (2') 同一中身束縛（`_BIND_MATCH = item_id/repo_realpath/base_commit/fingerprint` ＋ allowed_files 一致）／ (2'') 取消・失効 ／ (3) 残高証明（`bridge_reconciler`）／ (BIND-3) token_id 単一使用。

**★`_REQUIRED_REQUEST_KEYS`（10個）も変えない** ―― `item_id, task_id, trace_id, repo_identity, repo_realpath, base_commit, allowed_files, fingerprint, token_id, adjudication_id`。

---

## ③ ★rollback plan をどこまで保持すべきか

### ★現状（★実物・`patch_bridge.py:271-287`）

```python
plan = capture_preimage(workspace_dir, validated)   # ★内部の 変数
try:    _apply_to_working(...)
except: _restore_preimage(workspace_dir, plan, energize); emit(...'ROLLED_BACK'); raise
emit(...'APPLIED')
return {'schema_version':'apply-bounded-v1','outcome':'APPLIED','fingerprint':…,'filenames':…}
        # ★★plan は 返らない ＝ ★適用が 成功した 後は ★誰も 戻せない
```

**★`_RollbackPlan.entries[i]` の中身（★実測）:** `{'filename', 'existed', 'preimage'}`
**★`preimage` は ★bytes の 実体**（★測った例は 6 bytes）。

### ★保持の3案（★MGR は選ばない・★どれも新台帳 0）

```
★案1（★最小）: 返り値に ★`rollback_ref` だけ 足す
   … `preimage` の ★sha256 と ★filename / existed だけ。★中身は 持たない。
   ＋ 記録が 軽い ／ − ★戻すには ★元の bytes が 別途 要る（★git から 引く 前提）
★案2（★中）: 返り値に ★plan を そのまま 返す（★呼び手が 保持）
   ＋ 変更が 一番 小さい（★`return` に 1欄）／ − ★呼び手が 落ちたら 消える（★in-memory）
★案3（★重）: `PATCH_APPLICATION` の payload に ★preimage を 載せる
   ＋ ★SoR に 残る＝★プロセスが 落ちても 戻せる
   − ★★記録に ★ファイルの 中身が 入る（★大きさ・★秘密の 混入）★= 別の 危険

★★MGR の 観察（★決定ではない）:
   ・`repo_realpath` は ★git repo（★`_head_commit` で base_commit を 取っている）
   ・∴ ★`base_commit` が 在れば ★元の 内容は ★git から 引ける
   ・★案1 ＋「戻す時は base_commit から 取り直す」が ★記録を 汚さず 最も 軽い
   ・★但し ★未コミットの 変更が 在る repo では 成り立たない（★★要検証・★私は 確かめていない）
```

**★test/audit 失敗時の必須化（★Taka 指定）は、★`approved_scope` の語で表現できる**
（★§①の表）―― **★誰がそれを検査するかは ★設計の判断**（★候補: connector が適用後に確認）。

---

## ④ ★Taka が一度承認すれば以後どこまで無人で回るか

**★approval token 1つ（`task_id` + `operation_class` + `approved_scope` + `expiry`）で、★期限内・★消費前なら:**

```
★無人で 回る 範囲（★既存の 実装が すでに 持っている もの）:
   契約を 置く → 常駐が 自力で 投入 → PLAN(Qwen) → GENERATE(Qwen) → TEST →
   AUDIT(Qwen) → DISPOSE(77.6% は 機械) → UPPER_REVIEW(★headless claude・★29回→2回) →
   COMPLETE → ★機械が 部品を 置いて commit
   ＋ ★patch の 生成 → ★2DER が 裁定を 書く → ★mint → ★dry-run → ★1差分 適用 →
     ★test/audit → ★成功なら 確定 ／ ★失敗なら rollback
★★Taka が 呼ばれる 場面（★残る）:
   ・approval token の ★発行（★1回）
   ・★token の 期限切れ ／ ★scope 外の repo・ファイルに 触る 時
   ・★authority 層3（不可逆 / POLICY 外 / evidence≠OK）
   ・★上申条件8つ
★★`single_use=True` の まま だと ★1 patch ＝ 1 token ＝ ★Taka が 毎回 発行する
   ＝★★『一度承認すれば以後無人』に ★ならない。
★★∴ ★ここが ★★最後の 分かれ道（★Taka の 裁定が 要る 1点）:
     (あ) ★token を ★single_use の まま にし、★scope 内なら ★2DER が token を 再発行できる形
          → ★但し ★`grant_approval` の `approved_by` は ★Taka ∴ ★誰が 発行するかの 問題が 戻る
     (い) ★token を ★scope つき・期限つきの ★複数回 使用に する
          → ★`validate_approval` は ★`single_use` が False なら 消費を 見ない（★実物）
          ＝★★既存の 実装で ★そのまま 表現できる（★変更 0）
          → ★1回限り性は ★★BIND-3（token_id＝patch ごと）が ★引き続き 守る
★★MGR の 見立て（★決定ではない）: ★(い)。
   ★理由: ★`single_use` を False に しても ★patch ごとの 1回限りは ★BIND-3 が 別に 守る
          （★token_id は ★patch ごとに 違う）∴ ★安全性は 落ちない。
   ★★但し これは ★Taka の 価値判断 ∴ ★決めない。
```

---

## ★していないこと

```
★実装 0 ／ 実 repo へ 書き込み 0 ／ bridge_minter・bridge_reconciler を 走らせていない
★新台帳 0 ／ fingerprint 束縛を 外していない ／ allowed_files を repo 全体に 広げていない
★shell 任意実行権を 作っていない ／ _MAP / authority / disposition 規則を 変更していない
★rollback の 案を 選んでいない ／ consume の 場所を 決めていない ／ (あ)(い) を 決めていない
```
