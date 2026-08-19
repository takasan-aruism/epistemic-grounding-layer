# 宛: Taka ―― **★★配置先は 選べない ―― ★契約変換が `impl.py` 以外を 受けない（★9回の 型の 根）**

**2026-08-20 07:1x ／ ★実装 0 ／ ★実 repo 書き込み 0 ／ ★外部 diff 本番生成 ★未実施**
**★SELF_DEV_TOKEN = ★5/5 ／ ★HEAD `twoder 24c649a` 不変 ／ ★常駐 停止のまま**

---

## 1. ★配置の 依頼に 対して 出てきた もの

```
★`TASK-2DER-B686EA09`
★requirement 逐語「Implement the function ★generate_unified_diff(...) ★in impl.py …」
★★target_file = ★"impl.py"
★steps は ★7段とも ★実装と 試験の 話 ―― ★『既存 component の 責務を 比べる』段は ★無い
★GENERATE ★passed=True ／ artifact ★1674B ／ AUDIT ★0件 ／ UPPER_REVIEW ★PASS（機械）
```

```
★★＝ ★配置先は ★選ばれなかった。★同じ 関数を ★もう一度 sandbox に 作った だけ。
★★＝ ★『適切な 既存 file が 無い』という ★判断も 残っていない。
```

## 2. ★★原因は ★判断の 失敗では なく ★★構造上の 不能（★実測で 確定）

**★`contract_from_plan` の 仕様（★逐語・★2DER が 契約経路で 書いた 正本）:**

> 「★`target_file` の 前後の 空白を 落とした 形が ★"impl.py" でなければ ★None を 返し、
>  reason は ★"unexpected_target"。」

**★★実測（★私が 4通り 引いた・★純関数・副作用 0）:**

| `target_file` | 契約は 作れるか |
|---|---|
| `impl.py` | **★作れる**（reason=None） |
| `patch_bridge.py` | **★★unexpected_target** |
| `apply_unified_diff.py` | **★★unexpected_target** |
| `twoder/patch_bridge.py` | **★★unexpected_target** |

```
★★＝ ★`impl.py` 以外を 宛先に した 計画は ★契約が 作られない
   → ★`SPEC_INCOMPLETE_NO_CONTRACT` → ★runner が 動かない → ★成果物が 出ない。
★★＝ ★2DER は ★★構造上 ★`impl.py` 以外の file を ★作れない。
★★＝ ★ご指示の「配置先を 1つ 選べ」は ★2DER には ★実行不能な 依頼だった。
   （★選んでも ★その 宛先では ★1バイトも 作れない）
```

## 3. ★★これが 今夜 9回の 型の 根

```
★今夜 何度も 出た「★作れる ／ 繋がらない」―― ★原因は ★2DER の 読み違いでは なかった。
★★`impl.py` しか 宛先に できない ∴ ★成果物は ★必ず ★sandbox の 単一 file に なる。
★★∴ ★どんな 依頼も ★『sandbox に impl.py を 作る』に 収束する。
★★∴ ★本線の どの file にも ★1バイトも 届かない ―― ★構造として そう なっている。
★（★併せて ★`_place_and_commit` は ★`def X(` の X から `twoder/X.py` を 決める ＝
   ★★新規 file しか 置けない ／ ★安全経路は ★新規 file の 差分を 受けない
   ＝ ★★両側から 挟まれている）
```

## 4. ★★ご裁定の 手順が 進めない 箇所（★正確に）

```
★ご裁定 ①「2DER 自身に 既存 file を 1つ 選ばせる」
   → ★★選んでも ★契約変換が 拒否する ∴ ★★実行不能。
★ご裁定 ②「MGR が before/after から diff を 1回 生成」
   → ★★after（★既存 file に 追加した 完成 source）が ★2DER からは 出てこない。
   ★★MGR が 自分で 合成すれば ★『修理コードを 書かない』に 反する ∴ ★していません。
★★∴ ★②に 進めません。
```

## 5. ★★上申（★1点だけ・★私は 案を 出しません）

```
★★`contract_from_plan` の ★`target_file == "impl.py"` 制約を どう するか。
   ・★これは ★2DER が 契約経路で 書いた 正本（★私は 触っていない）
   ・★これを 変えない 限り ★2DER の 成果は ★本線の どの file にも 届かない
   ・★変える なら ★誰が どう 変えるか（★2DER に 直させる にも ★同じ 制約が 効く）
★★＝ ★★これも 自己参照（★制約を 直す 成果物も ★impl.py にしか 作れない）。
★★∴ ★Taka の 裁定が 要る。★私は 実装も 迂回も しません。
```

## 6. ★していないこと

```
★実装 0 ／ 配置先の 指定 0 ／ after source の 合成 0
★外部 diff の 本番生成 ★未実施（★許可された 1回は 使っていない）
★`contract_from_plan` 未変更 ／ `_place_and_commit` 0 ／ 直接 write 0 ／ git 操作 0
★`_GATES` 0 ／ `gates.json` 0 ／ authority / rollback / reconciler の 迂回 0
★実 repo 書き込み 0（★`twoder` HEAD `24c649a` 不変）／ ★常駐 停止のまま
★SELF_DEV_TOKEN = ★5/5（★`D7977C1A` は ★`CREATED` の まま ＝ ★成功条件 未達）
```
