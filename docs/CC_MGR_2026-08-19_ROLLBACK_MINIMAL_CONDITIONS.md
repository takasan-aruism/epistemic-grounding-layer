# 宛: Taka / 設計 / 監査 ―― rollback の最小条件 ＋ **★私が今日入れた変更の回帰1件**

**実装 0。実 repo へ書き込み 0。`bridge_minter`/`bridge_reconciler` を走らせていない。**

---

## 0. ★★先に報告 ―― 私の今日の変更が reconciler の不変条件を壊した

**`bridge_reconciler.py:21-24` の逐語:**

```
Correspondence (matches the as-built bridge write primitive _apply_to_working, DE-0419):
  an APPLIED apply ★writes canonical diff bytes to each listed file, and
  ★sha256(on-disk bytes) == the event's fingerprint.
  So an APPLIED event is reflected in git ★iff each of its files hashes to that fingerprint;
  a ROLLED_BACK event means the file was restored (★should be clean vs HEAD).
```

**★実装も同じ（`_fold_expected` 93-106行）:**

```python
if outcome == 'APPLIED':      expected[fn] = fp        # ★fp = patch の fingerprint
elif outcome == 'ROLLED_BACK': expected[fn] = None     # ★HEAD と 同じ＝clean
```
→ 後段で **`sha256(on-disk)` と突き合わせる**（72行の helper）。

**★今日 私が `_apply_to_working` を「diff を当てる」形に変えた（commit `6c87b0b`）結果:**

```
on-disk = ★当てた後の テキスト（'world\n'）
fingerprint = ★diff の sha256
∴ ★sha256(on-disk) ≠ fingerprint
→ ★reconcile が APPLIED を「git に 反映されていない」と 判定 → ★IMBALANCED
→ ★`latest_balance_proof` が fresh を 返さない
→ ★★門(3) が 必ず 落ちる ＝ ★delegated energize は ★1件も mint できない
```

```
★今 動いている 物への 影響 = ★無い（★reconciler は 呼び手 0 ／ 実 repo energize は 未実行）
★但し ★Taka が いま 歩いている 道の ★真上に 在る
★★∴ 「当てる形」に 変えるなら ★correspondence も 併せて 直す 必要が 在る（★DESIGN 案件）
   （★候補: APPLIED の expected を ★『当てた後の テキストの sha256』に する ―― ★但し それは
     ★PATCH_APPLICATION に ★もう1つ 欄が 要る か、★reconciler が 自分で 当てて 比べる 必要が 出る）
★★私は 直していない（★勝手に 増やさない）。
```

---

## 1. ★clean repo 前提なら何が保証できるか

### ★A案（base_commit から復元）は **★既存の口が無い**

```
★`patch_bridge` は ★git を ★1度も 書かない（★`_head_commit` の `rev-parse` だけ＝★読み）
★`bridge_reconciler` は ★[BIND-1] 逐語「READ-ONLY BY CONSTRUCTION … ★no git write subcommands」
   `_READ_ONLY_GIT = {'rev-parse','status','ls-files','cat-file','rev-list','log','ls-tree'}`
★★∴ A案は ★`git checkout`/`restore` 等の ★★新しい 書き口を 作る ことに なる
   ＝★『shell 任意実行権を 作らない』『新しい 自由な 書き換え権限を 作らない』と 正面から 当たる
```

### ★B案（preimage 保持）は **★既存の口が在り、今日 実測で動いた**

```
`capture_preimage(workspace_dir, validated)` → `_RollbackPlan(entries=({filename, existed, preimage}, …))`
`_restore_preimage(workspace_dir, plan, energize)`
   … ★`_require_energize` ＋ ★`_confined_path`（DE-0420）で ★workspace の 外に 出ない
★今日の 実測（使い捨ての場）: preimage 不一致 → ROLLED_BACK ＋ ★'hello\n' へ 復元
                              文脈不一致       → ★書かず ROLLED_BACK
```

### ★clean 前提で保証できること（★B案の場合）

```
① ★対象ファイルは ★適用直前の bytes に 戻る（★clean なら ＝ HEAD の 内容）
② ★対象ファイル以外は ★1文字も 触らない（★plan は validated.filenames だけ）
③ ★workspace の 外に 出ない（★`_confined_path`）
④ ★rollback にも energize が 要る（★DE-0418「dual token」）
⑤ ★ROLLED_BACK が 記録に 残る（★`emit_patch_application`）
★★clean 前提なら ★①＝『HEAD と 同じ』∴ ★reconciler の「ROLLED_BACK ⇒ clean vs HEAD」と ★一致する
```

**★∴「実 repo energize の前提 ＝ clean working tree」は ★整合的で、★かつ 検査する口が 既に在る**
（`bridge_reconciler._dirty_files(repo_dir)` 逐語「Tracked + untracked working-tree changes vs HEAD/index,
via ★read-only porcelain」＝ `git status --porcelain`）。

---

## 2. ★dirty repo を許した場合に追加で必要なもの

```
★(a) ★A案は ★使えない ―― base_commit から 戻すと ★未コミットの 変更を ★破壊する
     （★unstaged / staged / untracked の 別を 問わず ★HEAD の 内容で 上書きに なる）
★(b) ★B案なら ★対象ファイルは 正しく 戻る（★適用直前の bytes ＝ dirty の まま 戻る）
     ★但し ★★reconciler と 食い違う:
        ROLLED_BACK の expected は ★None＝「clean vs HEAD」
        ★実際は ★dirty の まま ∴ ★IMBALANCED に なる
     → ★追加で 要る = ★reconciler の ROLLED_BACK 判定を 「★適用直前に 戻った」で 言える 材料
        （★= preimage の sha256 を 記録に 残す）
★(c) ★対象ファイル ★以外の dirty は ★どちらの案でも 触らない ∴ ★問題ない
★★∴ dirty を 許すと ★『preimage の sha256 を PATCH_APPLICATION に 載せる』が ★事実上 必須に なる
   （★bytes 本体では なく ★sha256 だけ ＝ Taka の「preimage bytes を SoR へ 保存する案は 最後の手段」を 守る）
```

---

## 3. ★rollback の最小実装（★MGR は実装しない・★語で書く）

```
★★核は ★1つ ―― ★`apply_patch_bounded` が ★`plan` を ★返す（★今は 内部で 捨てている）。
   現在（`patch_bridge.py:271-287`）:
       plan = capture_preimage(...)      # ★内部変数
       … 成功 … return {'schema_version','outcome','fingerprint','filenames'}   # ★plan 無し
   最小: ★返りに ★rollback の 手掛かりを 1欄 足す。
        ★案1（★軽い・clean 前提）: `rollback_ref` =
             [{'filename', 'existed', ★'preimage_sha256'}]  ―― ★bytes は 持たない
        ★案2（★確実）: `plan`（★bytes 入り）を そのまま 返す ―― ★呼び手が in-memory で 保持
        ★どちらを 採るかは ★DESIGN（★MGR は 選ばない）

★★2つ目 ―― ★rollback 失敗が ★今は 嘘に なる（★実物）:
       except Exception:
           try: _restore_preimage(...)
           except Exception:
               ★pass   # rollback needs the same energization; if absent, apply never wrote…
           emit_patch_application(..., ★'ROLLED_BACK', ...)   # ★戻せていなくても ROLLED_BACK と 書く
           raise
   ★★∴ ★『rollback 自体が 失敗した』を ★別の 語で 記録し ★fail-closed で Taka へ 上げる 必要が 在る。
   ★既存の 上申の 器 = `twoder/human_escalation_packet.py`
       （★REQUIRED_FIELDS = decision_point / options / recommended_option / uncertainty /
         default_if_undecided ／ 逐語「STRUCTURALLY forbids "please look at everything" dumps」）
   ★`_fold_expected` は APPLIED / ROLLED_BACK しか 見ない ∴ ★新しい 語は ★expected を 動かさない
     （★= 未知の 語は 安全側に 落ちる。★但し reconciler 側の 扱いは ★DESIGN が 決める）

★★3つ目 ―― ★test/audit 失敗で 戻す 手（★今 0）:
   ★誰が 呼ぶか = ★`bridge_apply_connector` の 呼び手（★今 0・既報）
   ★何を 呼ぶか = ★`_restore_preimage(workspace_dir, plan, energize)`（★既存）
   ★注意: ★energize は ★1回限り（BIND-3）∴ ★rollback 用に ★同じ token が 使えるかは ★未確認
          （★`_require_energize` は grant だけ 見る ∴ ★token は 使える 見込みだが ★実測していない）
```

---

## 4. ★実 repo energize を初めて1件試せる条件

```
★★前提（★MGR の 整理・★Taka が 決める）:
 ① ★clean working tree（★`_dirty_files(repo_dir)` が ★空）
    → ★既存の 読み取り口で 検査できる ／ ★dirty なら ★試さない（fail-closed）
 ② ★対象は ★allowed_files 1本だけ（★repo 全体を 渡さない）
 ③ ★approval token（scope・期限・repo_identity・realpath・allowed_files・
    rollback required・test/audit required）を ★Taka が 1回 発行
 ④ ★`apply_patch_bounded` が ★plan（または rollback_ref）を 返す（★§3 の 核）
 ⑤ ★rollback 失敗を ★別の 語で 記録し ★上申する 経路（★§3 の 2つ目）
 ⑥ ★★reconciler の correspondence を ★『当てる形』に 合わせる（★§0 の 回帰）
    ―― ★これが 無いと ★門(3) が 落ちて ★mint できない
 ⑦ ★connector の 呼び手（★今 0）

★★①②③ は ★既存の 口で 足りる。★④⑤⑥⑦ が ★不足（★どれも 接続と 1欄の 話・★新台帳 0）。
★★最も 早い 順（★MGR の 見立て・★決定ではない）: ⑥ → ④ → ⑤ → ⑦
   ★理由: ⑥ を 直さない 限り ★他を 全部 揃えても ★1件も 通らない。
```

---

## ★していないこと

```
★実装 0 ／ 実 repo へ 書き込み 0 ／ minter・reconciler を 走らせていない
★§0 の 回帰を ★直していない（★勝手に 増やさない）
★A案 / B案 を ★私が 決めていない ／ rollback の 案1/案2 を 選んでいない
★preimage bytes を SoR に 載せる 案を ★採っていない（★sha256 案は dirty を 許す 場合の 条件として 挙げただけ）
★新台帳 0 ／ shell 任意実行権 0 ／ allowed_files を 広げていない
```
