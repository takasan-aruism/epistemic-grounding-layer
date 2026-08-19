# 宛: Taka / 設計 / 監査 ―― rollback 保持: **適用 → 判定 → 復元 → 記録 → BALANCED が閉じた**

**Claude 実装 0行（★今回は足場も書いていない）。実 repo 書き込み 0。**

## 0. 結果

```
★★適用後に test/audit が 落ちた 場面で ★元へ 戻し、★記録と 実体が ★一致する 一周が 閉じた。
   適用      → on-disk 'world\n' ／ PATCH_APPLICATION(APPLIED, post_apply_sha256)
   ★判定     → `rollback_allowed(...)` = {'restore': True}
   復元      → `_restore_preimage(ws, plan, ★同じ token)` → on-disk ★'hello\n'
   記録      → PATCH_APPLICATION(ROLLED_BACK, post_apply_sha256=None)
   ★★検算   → `bridge_reconciler.reconcile` = ★★BALANCED
```

## 1. 納品された部品（★2DER が書いた・★MGR は1行も書いていない）

```
twoder/rollback_allowed.py（★44行・commit ★a8d4d78「機械が 置いた=人の手 0」）
   def rollback_allowed(existed, post_apply_sha, disk_sha, preimage_sha)
   返り = {"restore", "reason"} ／ ★ファイルも git も 触らない ／ ★定数 0 ／ ★IO 0
   封印試験 ★13本 ／ 骨格 1315B・23行
```

### ★規則の実測（★全数）

| 場面 | 返り |
|---|---|
| 自分が当てたまま | **`{'restore': True}`** |
| **★他人が触った** | **`{'restore': False, 'reason': 'changed_by_other'}`** |
| 既に戻っている | `{'restore': False, 'reason': 'already_restored'}`（★冪等） |
| `post_apply_sha` が無い | `{'restore': False, 'reason': 'no_post_apply_sha'}` |
| `preimage` が無い | `{'restore': False, 'reason': 'no_preimage'}` |
| 元々無かった file が消えている | `{'restore': False, 'reason': 'already_restored'}` |
| 元々無かった file が在る | `{'restore': True}`（★戻す＝消す） |

**★MGR が挙げた危険（「適用後に誰かが触っていたら preimage を書き戻すとその変更を消す」）は、
★規則6 `changed_by_other` として ★fail-closed に入った。**

## 2. ★実走（★使い捨ての git repo・★1件）

```
plan = capture_preimage(ws, v)        # ★★呼び手が 先に 保持（★実測A のとおり patch_bridge を 変えずに 済んだ）
apply_patch_bounded(...)              # → 'world\n' ／ post_apply_sha256 が 記録に 残る
rollback_allowed(existed, post, disk, preimage) → ★{'restore': True}
_restore_preimage(ws, plan, ★同じ tok)  → ★'hello\n'
emit_patch_application(..., 'ROLLED_BACK', ..., post_apply_sha256=None)
reconcile(...) → ★★BALANCED
```

**★記録は `['APPLIED', 'ROLLED_BACK']` の2件。★実体は `'hello\n'`。★食い違い 0。**

## 3. ★今回わかったこと

```
★① 「plan 保持」に ★patch_bridge の 変更は ★要らなかった
   ―― ★呼び手が `capture_preimage` を 先に 呼べば よい（★実測A のとおり）
   ＝★★今回は ★Claude が 足場を 1行も 書いていない（★今日 初めて）
★② 「戻す」と「ROLLED_BACK を 記録する」は ★1組（★実測B）
   ―― ★記録を 落とすと reconciler が IMBALANCED に なる（★今日 実測済み）
★③ rollback に ★新しい token は 要らない（★`_require_energize` は grant だけ 見る）
```

## 4. ★残っていること（★今回は触っていない）

```
★(a) ★呼び手が 0 ―― ★この一周を ★誰も 本線から 呼んでいない
     （★`bridge_apply_connector` の 呼び手が 0・★既報）
     ＝★★今夜 8回目の「置いてある≠繋がっている」
★(b) ★rollback 自体が 失敗した 時に ★今も `'ROLLED_BACK'` と 記録される（★嘘・★既報・★別件）
★(c) ★test/audit の 結果を 誰が 渡すか（★connector の 呼び手）
★(d) delegated energize の 門(2) 分岐
★(e) 実 repo への 適用（★energize が 構造的に 拒否・★Taka の 門）
```

## 5. ★今日 2DER が増やした能力（★総括・★すべて Claude 実装 0行）

| 部品 | 状態 | 実走の証拠 |
|---|---|---|
| `requeue_decision` | **配線済み・稼働** | 常駐が自力で3件再取得 ／ COMPLETE 2件 |
| `should_call_senior` | **配線済み・稼働** | **`claude -p` 29回 → 2回** |
| `apply_unified_diff` | **配線済み** | hello → **world**（★diff を本当に当てる） |
| `patch_correspondence` | **配線済み** | APPLIED が **BALANCED**（★回帰を解消） |
| `rollback_allowed` | **★純関数として完成** | **★適用→判定→復元→記録→BALANCED**（★呼び手は 0） |
| `tasks_to_enqueue` ／ `dispose_decision` | 配置済み・未配線 | ― |

**★Claude が書いたのは足場の接続 ★4箇所だけ**（`346f074` / `e516007` / `6c87b0b` / `edf42cf`）
**―― どれも ★判断ロジック 0行。★今回（`rollback_allowed`）は ★足場すら 0。**

## 6. していないこと

```
★実装 0行 ／ 足場 0箇所（★今回）／ 実 repo 書き込み 0
★connector の 呼び手を 作っていない ／ rollback 失敗の 上申を 作っていない
★delegated energize・実 repo 適用に 進んでいない ／ 新台帳 0
```
