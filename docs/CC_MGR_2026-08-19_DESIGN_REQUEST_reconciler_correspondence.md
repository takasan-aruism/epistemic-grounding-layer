# 宛: DESIGN（監査 CC）―― 契約作成の依頼: **APPLIED の correspondence 1点だけ**

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 1. ★直したいこと（★1点・★これは私が作った回帰）

```
★`patch_bridge._apply_to_working` は ★今日から ★unified diff を ★本当に 当てる（★commit 6c87b0b）
   → on-disk = ★『当てた後の ファイル内容』（★'world\n'）
★`bridge_reconciler` は ★APPLIED を こう 判定する（★実装・145行）:
       if _file_sha(repo_dir, fn) == fp:   covered.add(fn)      # ★fp = ★patch fingerprint
       else:                                ew_git.append(...)  # ★event claims applied; disk bytes disagree
★★`fp` は ★diff 本体の sha256 ∴ ★この 等式は ★必ず 偽
   → ★IMBALANCED → `latest_balance_proof` が fresh を 返さない → ★門(3) が 落ちる
   → ★★delegated energize が ★1件も mint できない
★★今 動いている 物への 影響 = ★無い（★reconciler は 呼び手 0 ／ 実 repo energize 未実行）
```

## 2. ★四問の確認結果（★すべて実物）

### ① `PATCH_APPLICATION` に「適用後ファイル sha256」の欄が在るか → **★無い**

**`emit_patch_application`（`patch_bridge.py:248-256`）の payload ―― ★7欄:**

```
outcome / fingerprint / base_commit / filenames / token_id / repo_identity / repo_realpath
★『適用後の 内容』を 表す 欄は ★1つも 無い。
```

### ② 既存記録から適用後の期待値を決定論で再構成できるか → **★できない（★材料が1つ足りない）**

```
再構成に 要る もの = ★『適用前の 内容』＋『★diff 本文』
   ・適用前 … ★取れる（★`base_commit` が 在り、★read-only の git 許可名簿に
              ★`cat-file` / `ls-tree` が 在る＝`_READ_ONLY_GIT`）
   ・★diff 本文 … ★★どの 記録にも 無い（★PATCH_APPLICATION は ★fingerprint しか 持たない）
★∴ ★reconciler だけでは ★再構成できない。
```

### ③ 新しい bytes 保存台帳なしで判定可能か → **★可能（★2つの道が在る）**

```
★道A（★欄を 増やさない）… ★『符号』で 見る
   APPLIED     ⇒ ★その file は ★HEAD と 違う（＝dirty vs HEAD）
   ROLLED_BACK ⇒ ★その file は ★HEAD と 同じ（＝clean vs HEAD・★★今の 実装の まま）
   ★材料は ★既存の `_dirty_files`（`git status --porcelain`・read-only）だけ
   − ★弱い: ★『APPLIED と 書いてあり ★実際 変わっている』は 言えるが
            ★『★その patch で 変わった』とまでは 言えない

★道B（★欄を 1つ 足す）… ★『適用後の sha256』を 記録する
   `emit_patch_application` の payload に ★1欄（★例: `post_apply_sha256`）
   ★= ★`_apply_to_working` が 書いた bytes の sha256
   ＋ ★強い: ★`_file_sha` と ★そのまま 突き合わせられる（★145行の 形が 変わらない）
   − ★記録が 1欄 増える（★★但し ★bytes 本体では ない ／ ★新台帳では ない）
```

**★どちらも ★Taka の3禁を守る:**
```
★新しい「fingerprint」の 意味を 作らない（★道B は ★別名の 欄）
★patch fingerprint を file hash として 再利用しない（★どちらも しない）
★新しい bytes 保存台帳を 作らない（★どちらも 作らない）
```

### ④ ROLLED_BACK の「clean vs HEAD」と同じく、APPLIED にも意味の違わない既存鍵が在るか → **★在る（＝道A）**

```
★`_dirty_files(repo_dir)` 逐語「Tracked + untracked working-tree changes vs HEAD/index,
   via ★read-only porcelain」
★ROLLED_BACK 側は ★既に この鍵を 使っている（`_fold_expected` → `fp is None` → dirty なら orphan）
★∴ ★APPLIED 側にも ★同じ鍵（★dirty/clean）が ★そのまま 使える＝★意味が ずれない
```

## 3. ★修正対象（★1点だけ）

```
★`bridge_reconciler` の ★APPLIED の 対応関係のみ。
★変えない: ROLLED_BACK の 判定 ／ orphan の 概念 ／ [BIND-1] read-only ／ [BIND-2] pull-type ／
          `_dirty_files` ／ `_head` ／ `latest_balance_proof` の 形 ／
          ★`patch_bridge` 側の preimage / fingerprint / allowed_files / energize（★1つも 触らない）
★★道A なら `patch_bridge` は ★1文字も 変えない
★★道B なら `emit_patch_application` に ★1欄 足す（★DESIGN が 決める）
★docstring の correspondence 記述（21-24行）も ★実装に 合わせて 直してほしい
   （★★『ソースに在る≠動く』の 逆＝★『書いてある物が 古い』を 残さない）
```

## 4. ★契約の対象（★契約経路の制約に合わせる）

```
★`_place_and_commit` は `def X(` から `twoder/X.py` を 決める ＝ ★純関数 1本だけ 置ける。
★∴ 契約は ★純関数 1本に してほしい:
     入力 = ★記録から 取れる 値（★outcome ／ filenames ／ 適用後 sha256 または dirty 集合 …）
     出力 = ★その file が ★対応しているか ＋ ★理由の 語
     ★副作用 0（★git を 呼ばない ／ ★ファイルを 開かない）／ ★決定論
★名前・引数・返りの 形は ★DESIGN が 決める。
★★配線（`reconcile` の 145行から 呼ぶ）は ★契約経路では できない ∴ ★別途（★今夜 既出の 型）。
```

## 5. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★Taka 指定の 受入:
   ・Hermetic で hello → world を patch 適用 → ★reconciler が ★BALANCED
   ・on-disk が ★diff 本文でなく ★'world\n'
   ・★rollback 後は ★既存どおり BALANCED
★MGR から 追加（★過去の 失敗の型）:
   ・★空・None … PATCH_APPLICATION が 0件 ／ filenames が 空 ／ 欄が 欠けている
   ・★順序    … APPLIED の後に ROLLED_BACK ／ その逆 ／ 同じ file に 複数回
   ・★大小    … file 1本 ／ 複数本
   ・★他 repo … `repo_identity` が 違う event を 数に 入れない（★既存の bound_here/bound_other）
   ・★決定論  … 同じ入力で 同じ出力
   ・★非回帰  … ROLLED_BACK の 判定が ★今までどおり
```

## 6. ★MGR が先に言っておくこと（★隠さない）

```
★① この回帰は ★私が 作った（★commit 6c87b0b・★足場の 接続 1箇所）。
   ★当てる形に した こと 自体は ★Taka の 指示どおり ／ ★correspondence を 併せて 見ていなかったのが 私の 落ち度。
★② 道A / 道B の 選択は ★DESIGN（★MGR は 選ばない）。
   ★但し ★道B を 採ると ★`patch_bridge` にも 1欄 増える ∴ ★『修正対象は reconciler 1点』の 逐語と
   ★形式上 ぶつかる。★その判断も ★DESIGN に 委ねる。
★③ `manager` は 稼働中 ∴ ★契約を 置けば ★常駐が 次の巡回で 自力で 投げる。
★④ 完了条件の うち ★『reconciler が BALANCED と 判定』は ★配線後で ないと 測れない
   （★純関数が 出来ても ★`reconcile` が 呼ばなければ 変わらない）＝★★今夜 6回 出た 型。
```

## 7. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0 ／ 回帰を 自分で 直していない
★delegated energize に 入っていない ／ rollback 保持に 入っていない
★preimage / fingerprint / allowed_files / energize の 安全境界を 1つも 変えていない
```
