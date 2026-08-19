# 宛: Taka ―― **還流 完了 ／ 5番目 修正 完了 ／ ★Claude の 足場実装は ここで 終了**

**2026-08-20 ／ `twoder@4a7a033` ／ `ITEM-2DER-EVO-0080` = `DONE`**
**★SELF_DEV_TOKEN = ★5/5（★2DER の 1周が 閉じていない ∴ ★消費 0）**

---

## 1. ★★還流（★ご指示の 8項目・★front door から 実際に 引いて 確かめた）

**★先に 判ったこと ―― ★`TASK-…` の 記録面では 中身が 取り出せません。**

```
GET /api/resolve?id=TASK-2DER-D7977C1A            → record = {events: 4, state: CREATED} ★件数だけ
GET /api/resolve?id=TASK-2DER-D7977C1A&history=1  → history = ★0件
★★＝ ★CONTROL_PLANE_BOOTSTRAP を 打っても ★中身は 記録面から 引けない。
★理由 = ★`resolve` の `history` は ★ROADMAP 台帳 由来（`roadmap_registry.history`）。
★★∴ ★「打った」だけでは ★ご指示の「機械的に辿れる」を ★満たしません でした。
```

**★∴ ★引ける 面（ROADMAP 台帳）へ 登記しました。★新しい 台帳は 作っていません（★既存へ item 1件）。**

```
ITEM-2DER-EVO-0080  phase=PHASE-2DER-EVO-11(Interface transfer / Claude-Code off-ramp)
  authority = REVERSIBLE（★既存の 3語のみ・★新語 0）
  status    = DONE ／ history = 3行 ／ task_ids = [TASK-2DER-D7977C1A]
```

**★8項目の 取得可否（★`GET /api/resolve?id=ITEM-2DER-EVO-0080&history=1` の 実測）:**

| ご指示の項目 | 鍵 | 4点分 | 5点目 |
|---|---|---|---|
| bootstrap理由 | `BOOTSTRAP_REASON` | ★取れる | ― |
| commit SHA | `COMMIT_SHA` / `COMMIT_SHA_5TH` | ★`20195fa` | ★`4a7a033` |
| affected files | `AFFECTED_FILES` / `_5TH` | ★取れる | ★取れる |
| 変更前制約 | `CONSTRAINT_BEFORE` / `_5TH` | ★取れる | ★取れる |
| 変更後制約 | `CONSTRAINT_AFTER` / `_5TH` | ★取れる | ★取れる |
| authority=Taka裁定 | `AUTHORITY_GRANTED_BY: Taka` | ★取れる | ★取れる |
| 後方互換試験結果 | `BACKCOMPAT_TEST_RESULT` / `_5TH` | ★`PASS` | ★`PASS` |
| CONTROL_PLANE_BOOTSTRAP との対応 | `CPB_LINK_TASK` / `CPB_LINK_TRACE` | ★取れる | ★取れる |

**★加えて ―― ★`EXTERNAL_ACTOR: Claude(MGR) ★2DERの正規経路の外で source を直接変更した` を 逐語で 入れました。**
**★★＝ ★2DER の 記録面から「★これは 外部 bootstrap による 変更だ」と ★語で 取得できます。**

**★対応は 双方向です:**

```
ITEM-2DER-EVO-0080 → CPB_LINK_TASK: TASK-2DER-D7977C1A
TASK-2DER-D7977C1A の CONTROL_PLANE_BOOTSTRAP → roadmap_item: ITEM-2DER-EVO-0080
★共通の 鍵 = trace_id CPB-2026-08-20-TARGET-ALLOWLIST
```

---

## 2. ★★5番目の 修正（`twoder@4a7a033`）

```
★前 = contract_from_plan:69 ／ domain_dw.precheck_names:147 に ★`impl` が 逐語で 焼き付いていた
★後 = ★対象 file から 出した module 名で 照合する（`allowed_target_files.module_name_for`）
       ★`impl.py` → ★`impl` ∴ ★★従来の 呼び出しは 1文字も 変わらない
```

**★ご指定の 4条件・★すべて 実測:**

```
①★impl.py 完全互換
   回帰 7件 全一致（impl.py=None ／ patch_bridge.py・/etc/passwd・../x.py・空・a/../impl.py=unexpected_target
                    ／ "impl.py "（空白付き）=None）
   ★骨格の 文字列も 従来と 1文字も 同じ

②★module名 と import先 が 一致
   対象 route_precondition.py の とき
     from route_precondition import f  → ★通る（reason=None）
     from impl              import f  → ★★弾かれる（no_function_name）
   ★★＝ ★前は 「逆」だった（★誤りが 通り 正しいのが 弾かれた）。★向きが 直りました。

③★未許可 target は 従来どおり fail-closed
   /tmp/x.py ／ ../impl.py ／ C:\x.py ／ sub/impl.py ／ None ／ 数値 ／ 改行入り
   ★★7件 すべて unexpected_target

④★allowed target ／ path traversal ／ single-file 制約を 弱めない
   ★許可リストは ("impl.py",) の ままで ★1件も 足していない
   ★絶対path ／ ".." ／ repo外 ／ 複数file ／ allowed_files 検査 ／ PROD_REPO_ROOTS ／
     authority ／ rollback ／ reconciler ／ 安全境界 = ★★1文字も 触っていない

★★★5番目の 回帰 全件一致 = ★True
```

**★`precheck_names` の 倒し方（★念のため）:**

```
★`target_file` の 欄が 無い ／ 許可外の とき = ★従来どおり `impl` で 引く。
★★＝ ★「読めないなら 通す」では なく ★「従来の 厳しさを 保つ」方へ 倒しています。
```

---

## 3. ★私が 直した もの 1つ（★隠さず）

```
★`contract_from_plan` の docstring 1行が ★「from impl import で始まる行を探し」と 書いて あり、
  ★コードだけ 直すと ★説明が 嘘に なる ∴ ★その 1行を 実際の 動きに 合わせました。
★★対象 file を hash で 封じている 仕組みは ★探した 範囲（contract_seal.py ／ artifact_registry.py
  ／ twoder/*.py の 参照）に ★1件も 無い ことを 確かめてから 触りました。
```

---

## 4. ★★ここで 手を 止めます（★ご指示どおり）

```
★Claude に よる 足場実装 = ★★終了。
★以降は ★★すべて 2DER 自身へ:
   ・2件目の target の 追加
   ・配置先の 選択
   ・diff 生成
   ・gate 修理
   ・実 repo 反映
★Claude は 以後 ★観測 ／ 記録確認 ／ 安全上申 のみ。
```

**★1つだけ 運用の 事実を 申し送ります（★欠陥では ありません）:**

```
★`build_planner` の 許可リスト文言は ★import した ときに 1回 組み立てられます。
★★∴ ★2DER が 2件目を 足した ときは ★常駐を 1回 入れ直さないと ★依頼文だけ 古いままに なります。
★（★他の 4箇所は 呼ぶ たびに 読む ∴ ★すぐ 反映されます）
```

## 5. ★状態

```
★commit = 20195fa（4点）／ 4a7a033（5点目）★どちらも source のみ・[Claude実装] ・push 済
★台帳 file は add していません（★記録/文書と source を 混ぜない）
★常駐 = ★停止の まま ／ ★front door への 投入 = ★0 ／ ★実 repo への 反映 = ★0
★TASK-2DER-D7977C1A = ★CREATED（★events 4 ／ ★状態は 1つも 進めていない）
★新台帳 0 ／ 新権限 0 ／ 新 endpoint 0 ／ 新 state 語 0 ／ ★増えた 管理対象 = ★item 1件のみ
★SELF_DEV_TOKEN = ★5/5
```
