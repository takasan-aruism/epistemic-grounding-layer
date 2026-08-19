# 宛: Taka ―― **`target_file="impl.py"` 固定の 調査 ＋ ★最小契約拡張の 定義（★実装 0）**

**2026-08-20 07:2x ／ ★実装 0 ／ ★実 repo 書き込み 0 ／ ★SELF_DEV_TOKEN = ★5/5**

---

## Q1 ★この 固定は 何を 防いでいるか

```
★`contract_from_plan` は ★`target_file` を ★★等値検査に しか 使っていない（★実測）:
   使用箇所 = ★docstring ／ ★`if target_file.strip() != "impl.py":` の 1行 ★だけ
   骨格の 組み立て = `line1 = f"def {func_name}({params_str}):"` ／ `line2 = requirement` ／
                    `line3 = '<<<FILL: ここに実装>>>'`
★★＝ ★骨格の 生成に ★file 名は ★1文字も 使われていない。
★★∴ ★この 固定が 防いでいるのは ★★『後段が 扱えない 値を 早い 段で 弾く』こと（★整合の 前倒し）。
```

## Q2 ★skeleton 生成は 任意 file でも 成立するか → **★成立する**

```
★上記の とおり ★file 名に 依存しない ∴ ★★任意の file 名でも 骨格は 作れる。
```

## Q3 ★★後段は 任意 file 名を 扱えるか（★★ここが 本題）

| 後段 | 実物 | 任意 file 名を 扱えるか |
|---|---|---|
| **`generate_via_runner:174`** | ★`"target_file": ★"impl.py"`（★★固定値） | **★★扱えない（★計画の target_file を ★読んでいない）** |
| **`generate_via_runner:179`** | ★`"allowed_files": ★["impl.py", "test_impl.py"]`（★★固定値） | **★★扱えない** |
| `generate_via_runner:105` | prompt 逐語「ALLOWED OUTPUT: ★impl.py の全文」 | ★文面が 固定 |
| **`build_planner:162`** | prompt 逐語「Import the code under test with ★"from impl import \<name\>" — ★the module is ★always impl」 | **★★扱えない（★封印試験が `impl` を import する）** |
| `live_worker_runtime:29` | `path = os.path.join(workspace, ★target)` | ★★扱える（★但し ★下の Q4 参照） |
| `patch_bridge.validate_artifact` | ★diff の `a/` `b/` から 採り ★`allowed_files` と 突き合わせ | ★★扱える（★file 名 非依存） |
| `apply_cycle` | ★`len(validated.filenames) != 1` で 拒否 | ★★扱える（★1 file 限定は 既に 在る） |

```
★★＝ ★『この一点』では ★なかった。★★固定は ★4箇所（★contract_from_plan ／ runner の 2行 ／ planner の prompt）。
★★＝ ★`contract_from_plan` の 1行だけ 外しても ★runner が ★impl.py を 書き ★封印試験は
   ★`from impl import` の まま ∴ ★★何も 変わらない。
```

## Q4 ★境界は どこに 在るか（★path traversal / 複数 file / 実 repo 直接）

```
★path traversal … ★`live_worker_runtime:29` は ★`os.path.join(workspace, target)`
   ＝ ★★`target` が `../..` を 含めば ★workspace の 外へ 出る。
   ★★∴ ★現状 ★traversal を 実際に 止めているのは ★★`impl.py` 固定 その ものである。
   （★★これが ★最も 重要な 発見 ―― ★固定を 外すと ★境界が 1つ 消える）
★複数 file … ★`apply_cycle` が ★`filenames != 1` を 拒否 ／ `worker_output_to_artifact` 逐語
   「files_changed must be a list/tuple of ★exactly one filename」＝ ★既に 在る
★実 repo 直接 … ★`validate_plan` の `PROD_REPO_ROOTS`（egl/ds/rri/dev-workcell/twoder）＝ ★既に 在る
★適用の 範囲 … ★`allowed_files` ＋ `check_diff_within_allowed` ＝ ★既に 在る
```

## Q5 ★『任意文字列』が 要るか → **★要らない**

```
★★『既存 repo 内の ★許可済み 1 file』に 限れば 足りる。
★理由 = ★Q4 の とおり ★traversal を 止めていたのは ★固定値 その もの ∴
   ★★許可リストに すれば ★同じ 強さの 境界を ★明示的に 持てる（★暗黙 → 明示）。
```

---

## ★★最小契約拡張の 定義（★★定義のみ・★実装していない）

```
★★① 許可の 形 = ★★『既存 repo 内の 相対 path の ★明示リスト』
   ・★リストに 無い 値は ★fail-closed（★従来と 同じ 拒否語 `unexpected_target` を 使う）
   ・★`impl.py` は ★リストの 既定要素 ∴ ★★従来経路は ★1文字も 変わらない（★後方互換）
   ・★path は ★`..` を 含まない ／ ★絶対 path で ない ／ ★1つだけ（★複数は 拒否）

★★② 値の 流し先（★★固定値を 計画の 値に 差し替える 3箇所）
   ・`generate_via_runner:174` の `"target_file"`
   ・`generate_via_runner:179` の `"allowed_files"`（★target と その 試験 file の 2件のみ）
   ・`build_planner:162` の prompt の ★module 名（★`from <module> import` に する）
   ★★＝ ★どれも ★『固定値を ★計画の 値に する』だけ ―― ★新しい 判断は 足さない。

★★③ 触らない もの
   ・`apply_cycle` の ★1 file 制限 ／ `worker_output_to_artifact` の ★exactly one
   ・`allowed_files` の 検査 ／ `check_diff_within_allowed`
   ・`validate_plan` の `PROD_REPO_ROOTS` ／ authority ／ rollback ／ reconciler
   ・`_place_and_commit`（★今回 使わない）
```

---

## ★★上申（★1点・★★ご裁定と 実測の ずれ）

```
★ご裁定 逐語 =「★この一点だけ CONTROL_PLANE_BOOTSTRAP として MGR が 最小変更してよい」
★★実測 = ★『この一点』は ★★4箇所（★§Q3）。
★★かつ ★§Q4 の とおり ★固定を 外すと ★★traversal を 止めていた 暗黙の 境界が 1つ 消える
   ∴ ★許可リストを ★同時に 入れないと ★安全性が 下がる。
★★∴ ★私が 触る 範囲が ★ご裁定の 想定より ★広い ―― ★★勝手に 広げず 裁定を 仰ぎます。
★（★『2DER が 既存 file を 安全に 対象化できる ための 足場』と 読めば ★§②の 3箇所も
   ★足場に 含まれる と 解せます が ―― ★私は 決めません）
```

## ★していないこと

```
★実装 0 ／ 修正 0 ／ `contract_from_plan` 未変更 ／ `generate_via_runner` 未変更
★`build_planner` 未変更 ／ 許可リスト 未作成 ／ 投入 0
★実 repo 書き込み 0（★`twoder` HEAD `24c649a` 不変）／ ★常駐 停止のまま
★外部 diff の 本番生成 ★未実施 ／ ★`D7977C1A` は ★`CREATED` の まま
★SELF_DEV_TOKEN = ★5/5
```
