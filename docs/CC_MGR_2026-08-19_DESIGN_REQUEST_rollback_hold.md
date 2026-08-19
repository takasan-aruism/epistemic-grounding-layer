# 宛: DESIGN（監査 CC）―― 契約作成の依頼: 適用後 rollback の可否を決める純関数

**依頼元: MGR ／ 2026-08-19 ／ Taka 指示「次は rollback plan 保持へ進んで」**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 1. ★今日の実測（★使い捨ての git repo・★2件とも 新しい 事実）

### ★実測A ―― 適用後に**同じ token で戻せる**（★前回「未実測」と書いた点）

```
plan = capture_preimage(ws, v)        # ★呼び手が ★先に 取れる
apply_patch_bounded(...)              # → on-disk = 'world\n'
_restore_preimage(ws, plan, ★同じ tok) # → ★戻せた = 'hello\n'
★∴ ★rollback 用に ★新しい token は 要らない（★`_require_energize` は grant だけ 見る）
★∴ ★`capture_preimage` を ★呼び手が 先に 呼べば ★plan は ★今でも 保持できる
   （★`apply_patch_bounded` が 返さなくても 済む＝★★patch_bridge を 変えずに 済む 可能性）
```

### ★実測B ―― **戻しただけでは記録と食い違う**（★これが設計を変える）

```
戻した後に reconcile を 引いた:
   balanced = ★False
   orphans_event_without_git = (('t.txt', 'e258d248…'),)   # ★APPLIED の 記録が 残ったまま
★∴ ★『戻す』だけでは ★足りない ―― ★★戻した事を ★ROLLED_BACK として 記録する まで が 1組。
★記録の口は ★既存（`emit_patch_application(..., 'ROLLED_BACK', ..., post_apply_sha256=None)`）
```

## 2. ★契約にしてほしいもの（★純関数 1本）

**★判断が要るのは「★戻してよいか」の1点。**

```
★危険（★MGR が 見つけた）:
   適用した 後に ★誰かが その file を ★別の 理由で 変えた 場合、
   ★preimage を そのまま 書き戻すと ★★その変更を 消す。
★∴ ★戻す前に ★『いま disk に 在るのは ★自分が 当てた 物か』を 確かめる 必要が 在る。
   ★材料は ★既に 在る:
       post_apply_sha256（★今日 記録に 入れた）／ 現在の disk の sha256 ／
       preimage の sha256（★`_RollbackPlan.entries[i]['preimage']` から 出せる）／
       existed（★元々 file が 在ったか）
★★入力・返り・名前の 形は ★DESIGN が 決める（★MGR は 決めない）。
★★副作用 0（★ファイルを 触らない ／ ★git を 呼ばない）／ ★決定論。
```

## 3. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★戻してよい   … disk == post_apply_sha256（★自分が 当てた ままだ）
★★戻さない    … disk が post_apply_sha256 と 違う（★★他人が 触った=★fail-closed）
★戻す必要なし … disk == preimage の sha（★★既に 元に 戻っている＝二度 戻さない・★冪等）
★空・None    … post_apply_sha256 が 無い ／ preimage が 無い ／ disk が 無い（★file が 消えた）
★existed=False … ★元々 無かった file（★戻す＝★消す）を どう 扱うか
★大小        … file 1本 ／ 複数本
★決定論      … 同じ 入力で 同じ 出力
★語で 返す   … ★なぜ 戻さないかを ★理由の 語で（★今日の 部品と 同じ 作法）
```

## 4. ★契約の対象（★契約経路の制約）

```
★`_place_and_commit` は `def X(` から `twoder/X.py` を 決める ＝ ★純関数 1本だけ 置ける。
★∴ 契約は ★純関数 1本。★配線（★呼ぶ場所）は ★別途（★今夜 7回 出た 型）。
```

## 5. ★MGR が先に言っておくこと（★隠さない）

```
★① 「plan 保持」は ★★実測A により ★patch_bridge を 変えずに 済む 見込み
   （★呼び手が `capture_preimage` を 先に 呼べば よい）。
   ★但し ★`apply_patch_bounded` が 返す 形に した 方が 落ちにくいかは ★DESIGN の 判断。
★② ★実測B により ★『戻す』と『ROLLED_BACK を 記録する』は ★1組。
   ★記録の口は 既存 ∴ ★新しい 記録は 作らない。
★③ ★rollback 自体が 失敗した 時に ★今は `'ROLLED_BACK'` と 書かれる（★嘘・★既報）。
   ★★今回の 依頼には ★含めていない（★1つの 閉塞に 2つ 増やさない）。★別件のまま。
★④ ★test/audit の 結果を 誰が 渡すかは ★connector の 呼び手（★今 0）＝★別件。
★⑤ ★preimage の bytes を SoR に 保存する 案は ★採っていない（★Taka の「最後の手段」を 守る）。
```

## 6. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0
★patch_bridge / bridge_reconciler を 今回 触っていない
★delegated energize・実 repo 適用に 進んでいない ／ 新台帳 0
```
