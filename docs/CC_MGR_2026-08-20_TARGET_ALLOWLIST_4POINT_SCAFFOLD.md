# 宛: Taka ―― **足場修理 4箇所 完了 ／ ★5番目の結合で 上申（1件だけ）**

**2026-08-20 ／ `twoder@20195fa` push 済 ／ ★SELF_DEV_TOKEN = ★5/5（★1周が 閉じていない ∴ 消費 0）**

---

## 1. ★やったこと（★ご裁定「4箇所まで」の 範囲内・★足場のみ）

**★新しく 作った file は 1つ。★中身は「許可された file 名かを 答える」だけ。**

```
twoder/allowed_target_files.py（★新規 75行）
  ALLOWED_TARGET_FILES = ("impl.py",)        ★← 今は 1件だけ。★増やしていません。
  is_allowed_target()   … 絶対path ／ ".." ／ 空 ／ リスト外 = ★すべて False
  test_file_for()       … X.py -> test_X.py
  module_name_for()     … X.py -> X
```

**★4箇所は「自分で `impl.py` と 比べる」のを やめて、★この 1つに 聞く 形に しました。**

| # | 場所 | 前 | 後 |
|---|---|---|---|
| ① | `contract_from_plan` | `target_file != "impl.py"` なら 拒否 | 許可リストに 聞く（★拒否語 `unexpected_target` は **不変**） |
| ② | `generate_via_runner:174` | `target_file` を `"impl.py"` に **固定** | 計画の 値。★許可外は `impl.py` へ 落とす |
| ③ | `generate_via_runner:179` | `allowed_files` を **固定** | 対象 file と その 試験 file の 2件 |
| ④ | `build_planner` の 依頼文 | 逐語で `"impl.py"` と 書いていた | 許可リストから 組み立て（★今は 1件 ∴ ★文面は 従来と 同じ） |

## 2. ★実測（★数字）

```
★従来どおり 動くか（★回帰 7件）
   impl.py        → reason=None（★通る）
   patch_bridge.py / /etc/passwd / ../x.py / 空 / 型違い → ★unexpected_target
   ★★全件 一致 = True
★runner（★6ケース）
   ★未許可の 値を 何を 入れても → target=impl.py ／ test=test_impl.py（★fail-closed）
★依頼文
   MUST be exactly one of: "impl.py" — the runner creates only that file
   ★★＝ ★従来と 1文字も 変わらない
```

**★★∴ ★いま この commit は ★挙動を 1つも 変えていません（★足場だけ）。**

## 3. ★1件 足したら 4箇所が 揃って 動くか（★出荷 file は 変えず、★その場で 試した）

```
仮に "route_precondition.py" を 足した とき
 ① 許可     = True ／ 試験 file = test_route_precondition.py ／ module = route_precondition
 ② 契約     = 通る（skeleton = def precondition_of(segment_id):）
 ③ runner   = target=route_precondition.py ／ test=test_route_precondition.py
 ④ 依頼文   = MUST be exactly one of: "impl.py", "route_precondition.py"
★★＝ ★4箇所とも 揃って 動く。
```

---

## 4. ★★上申（★1件だけ）―― **5番目の結合が 残っており、★足した 瞬間に 「逆」に なります**

**★これは ご裁定の 4箇所の 外 ∴ ★私は 触っていません。**

```
★場所 = contract_from_plan:69 と domain_dw の
        ^from\s+impl\s+import\s+   ★← "impl" が 逐語で 焼き付いている

★実測（★route_precondition.py を 対象に した とき）
  封印試験が  from impl              import f  と 書いて ある → ★通ってしまう（reason=None）
  封印試験が  from route_precondition import f  と 書いて ある → ★★拒否される（no_function_name）
```

**★平たく 言うと ―― ★「間違った 書き方が 通り、★正しい 書き方が 弾かれる」状態に なります。**
**★そのまま 進むと ―― ★作る file は `route_precondition.py` なのに ★試験は `impl` を 読みに行く**
**★∴ ★試験は 必ず 落ちます（★しかも 契約の 段では 誰も 気づかない）。**

```
★★今は 無害です。★許可リストが ("impl.py",) の 1件だけ ∴ ★ずれようが ない。
★★危険に なるのは ―― ★★リストに 2件目を 足した その 瞬間から。
★★∴ ★順序を 逆に できません:
     ×  2件目を 足す → 後で import 検査を 直す
     ○  ★import 検査を 直す → ★その 後で 2件目を 足す
```

**★ご裁定を 仰ぎたいのは 1点だけです ―― ★この5番目を どちらで 直すか。**

| 案 | 中身 | 私の 見立て |
|---|---|---|
| **あ** | ★5番目も 足場と して 私が 直す（★4箇所 → 5箇所へ 1つ 拡張） | 決定論・1関数・`impl.py` では 挙動不変。★**最短** |
| **い** | ★5番目の 修理も 2DER 自身に 戻す | ★但し ★2DER は いま `impl.py` しか 作れない ∴ ★★自分の 検査器を 直す 経路が 無い（★自己参照） |

**★私は「あ」を 推します。★理由は「い」だと 前回と 同じ 自己参照の 壁に 当たる ためです。**
**★但し ―― ★これは 新しい 設計判断 ∴ ★★勝手には 進めません。**

---

## 5. ★もう1つ ご報告（★欠陥では ありません・★運用の 事実）

```
★build_planner の 許可リスト文言は ★import した ときに 1回だけ 組み立てられます。
★★∴ ★リストに 足した ときは ★常駐を 1回 入れ直さないと ★依頼文だけ 古いままに なります。
★（★他の 3箇所は 呼ぶ たびに 読む ∴ ★すぐ 反映されます）
```

## 6. ★触っていないもの（★逐語）

```
PROD_REPO_ROOTS ／ authority ／ rollback ／ reconciler ／ 安全境界 ／ allowed_files 検査 ／
live_worker_runtime の path 結合 ／ apply_cycle の 1file 制限 ／ 経路表 ／ 状態機械
★新しい 台帳 = 0 ／ 新しい 権限 = 0 ／ 新しい 外部接続口 = 0 ／ 新しい 管理対象 = ★0
★複数 file 対応 = ★していない ／ 任意 path 対応 = ★していない ／ repo 外 = ★禁止のまま
```

## 7. ★記録・状態

```
★正規記録 = TASK-2DER-D7977C1A へ CONTROL_PLANE_BOOTSTRAP を 1件 追記
   status = SCAFFOLD_DONE_ENTRY_NOT_ADDED ／ ★状態は CREATED の まま（★進めていない）
★commit  = 20195fa [Claude実装] ／ ★source 4件のみ（★台帳 2件は add せず）／ push 済
★常駐    = ★停止の まま ／ ★front door 投入 = ★0 ／ ★実 repo への 反映 = ★0
★SELF_DEV_TOKEN = ★5/5（★全周が 閉じた ときだけ 1消費 ∴ ★まだ 消費 0）
```

## 8. ★途中で 私が 壊し、★すぐ 直した もの（★隠さず 記録）

```
★build_planner の 依頼文で ★文字列の 足し算(+)を 途中に 入れた ため
  ★書式指定(%)が ★最後の 断片だけに かかり ★TypeError で 落ちた。
★★原因 = ★% は + より 先に 効く。★同型の 再発を 防ぐため ★逐語で コメントに 残した。
★★直し方 = ★目印を 置いて ★% の 後で 差し替える 形に した。
★★現在 = ★依頼文は 正常に 出る（★長さ 2539・★"impl.py" を 含む）。
```
