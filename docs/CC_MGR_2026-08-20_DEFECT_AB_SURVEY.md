# 構造欠陥 A / B ―― ★調査（★実装 0 ／ ★設計まで ／ ★DESIGN_HOLD 判定つき）

**2026-08-20 20:5x ／ ★§1 調査 → §2 因果鎖 → §3 R1〜R4 → §4 ESDE before → §5 最小修理の 設計**

---

## ① 調査範囲（★作用ベース ／ ★検索方法を 併記）

```
★1 bare `from patch_bridge` / `import patch_bridge`   … `grep -rn` 全件（twoder/dev-workcell/ds/rri/egl）
★2 `from twoder import patch_bridge` / `twoder.patch_bridge` … 同上（★`/home/takasan` 全体）
★3 `_EnergizedApply(` の 生成箇所                      … 全件
★4 `isinstance(..._EnergizedApply` / `_require_energize` … 全件
★5 `sys.path.insert|append` の 本番 全箇所             … 全件（★`/test` `regression` `runs` を 除く）
★6 `sys.path` へ `twoder` を 足す 箇所                 … 全件
★7 twoder 直下と stdlib の 名前衝突                    … ★`sys.stdlib_module_names` と ★機械照合
★8 `mint_real_energize` / `apply_cycle` / `source_to_patch` の 本番 caller … 全件
★9 `token_id` の 生成→渡し→検査→消費                 … 全件
★★`runs/` は 横読み禁止 ∴ 触れて いない。
```

### ★実測（★数）

| 項目 | 実測 |
|---|---|
| bare import（本番） | **1件のみ** ―― `twoder/bridge_minter.py:26 from patch_bridge import _EnergizedApply`（他は `regression/` 5件と `egl/docs/SUBMIT_…` の 複製） |
| package import | **2件** ―― `source_to_patch.py:85` / `apply_cycle.py:22`（どちらも `from twoder import patch_bridge as PB`） |
| `_EnergizedApply(` 生成 | **2件** ―― `patch_bridge.py:74`（throwaway）／ `bridge_minter.py:159`（real） |
| `isinstance` 検査 | **2件** ―― `patch_bridge.py:79`（`_require_energize`）／ `patch_bridge.py:355` |
| `_require_energize` 呼び | **2件** ―― `patch_bridge.py:100` `:243`（★書き込み到達 経路 すべて） |
| **`sys.path` に twoder を 足す 本番コード** | **★★0件**（`build_planner.py:69` は `PROD_REPO_ROOTS`＝★禁止先の 一覧 ／ `route_observed.py` は grep の 引数） |
| **stdlib 名前衝突** | **★★1件のみ ―― `twoder/operator.py`**（`sys.stdlib_module_names` と 機械照合） |
| 本番 caller | `mint_real_energize` **0**（★1件は `source_to_patch` の コメント）／ `apply_cycle` **1**（`source_to_patch:123`）／ `source_to_patch` **0** |

---

## ② 修理前の 因果鎖（★6項目 ／ ★推測で 埋めない）

| # | 点 | 誰が作る | 何を作る | どこに保存 | 次に誰が読む | 無い/不正なら | 本線で 呼ばれるか |
|---|---|---|---|---|---|---|---|
| 1 | adjudication | **★0（writer 無し）** | `{kind, payload}` | ★未定 | `bridge_minter:50` | `MintRefused` | **★呼ばれない** |
| 2 | reconciliation | `bridge_reconciler.reconcile` | `ReconResult` | ― | `emit_reconciliation` | ★例外 | **★本番 caller 0** |
| 3 | proof | `emit_reconciliation` | `RECONCILIATION_BALANCED` | recorder 次第 | `latest_balance_proof` | 門(3) 拒否 | **★本番 caller 0** |
| 4 | **mint** | `bridge_minter.mint_real_energize` | `_EnergizedApply`(**bare 側 class**) | ― | `apply_cycle` | `MintRefused` | **★本番 caller 0 ／ ★本番 path では import 不能** |
| 5 | artifact | `source_to_patch.source_to_artifact` | `{schema, base_commit, fingerprint, diff}` | ― | `apply_cycle` | 語で 返す | **★本番 caller 0** |
| 6 | **apply** | `apply_cycle` → `patch_bridge` | 実 file 変更 | working tree | git | **★`_require_energize` が `TypeError`（欠陥A）** | `source_to_patch:123` から 1件（★その 上流が 0） |
| 7 | 記録 | `emit_patch_application` | `PATCH_APPLICATION` | recorder | `bridge_minter:66,120` ／ reconciler | ★記録 無し | ★apply 内から 2件 |
| 8 | rollback | `patch_bridge:298` | `ROLLED_BACK` 記録＋復元 | working tree | 同上 | `rollback_allowed` が 語で 止める | ★apply 内から |

```
★★埋まらない 点 = ★#1（writer 0 ／ 保存先 未定）
★★∴ ★§2 の 時点で ★DESIGN_HOLD の 条件を 1つ 満たして いる（★但し §5 の 修理対象は A/B ∴ 分けて 扱う）
```

---

## ③ R1〜R4（★修理前に 適用）

```
★R1 END-TO-END CONTACT … ★正規上流から 実走 → ★★不成立（#1 writer 0 ∴ 上流が 無い）
★R2 DENOMINATOR       … ★required=8 / observed=6 / broken=2（★§4）
★R3 INTERNAL GATE     … ★`_require_energize` は ★到達したが ★通過して いない（TypeError）
★R4 GATE ENUMERATION  … ★★実施済（★5条件を 1つずつ 発火させ ★期待どおりの 理由で 拒否を 確認）
   ①裁定なし → `no ENERGIZATION_ADJUDICATION event`
   ②attribution 不一致 → `authority_owner != TAKA`
   ③expiry 無し → `adjudication has no expiry (fail-closed)`
   ④proof 無し → `no fresh reconciler balance-proof`
   ⑤energize が 別 class → `TypeError: not an _EnergizedApply`
★★『正常系が 通った』だけでは 完了に して いない。
```

---

## ④ ESDE 3指標 ―― **before**（★総合点に 潰さない）

```
Symmetry : required=6 / present=4 / missing=2
   missing_ID = ENERGIZATION_ADJUDICATION(writer) / ENERGIZATION_REVOCATION(writer)
   ★別枠: 本番 caller を 持つ counterpart = 1/6
Linkage  : declared=8 / observed=6 / broken=2
   broken_ID = E1(Taka authority→adjudication record) / E6(energize token→apply)
Hierarchy: required=5 / passed=4 / violation=1 / unreachable=0
   violation_ID = H5(新規file配置 と 既存file変更 の 責務差の 混同 ―― ★観測者の 認識)
```

---

## ⑤ A/B 最小修理の **設計**（★実装しない ／ ★差分宣言つき）

### ★A の 原因（★1行）

```
`bridge_minter.py:26  from patch_bridge import _EnergizedApply`
   ―― ★これ **1件だけ** が ★bare import（★本番の 他 2件は package import）
   ★★∴ ★module object が 2つに 割れ ★class identity が 一致しない。
```

### ★修理案（★条件を すべて 満たす）

```
★変更 = ★`bridge_minter.py:26` を ★`from twoder.patch_bridge import _EnergizedApply` に 揃える。★1行。
★★これで 満たす 条件:
   ✔ sys.path 追加で 解決して いない（★むしろ ★twoder を path に 足す 必要が 消える）
   ✔ authority を 弱めて いない（★門は 1つも 触らない）
   ✔ mint の 門を 迂回して いない
   ✔ `isinstance` を 削って いない（★★型を 揃える 側で 直す）
   ✔ token を 偽造して いない
   ✔ throwaway 特例／task ID 特例／Claude 専用経路を 作って いない
   ✔ 新規file配置 と 既存file変更 の 責務を 混同して いない（★触るのは import 1行）
★★B は ★A を こう 直せば ★★自動的に 消える（★twoder を path に 足さなく なる ∴ `operator` を 食わない）。
   ★`twoder/operator.py` の 改名は ★★しない（★呼び手が 居る 可能性 ／ ★今回の 修理に 不要）。
```

### ★変更後の 因果鎖 **差分宣言**（★変わる点だけ）

| # | 点 | 変更前 | 変更後 |
|---|---|---|---|
| 4 | mint | `_EnergizedApply` は **bare 側 class** ／ 本番 path で import 不能 | **package 側 class** ／ **本番 path で import 可能** |
| 6 | apply | `_require_energize` が `TypeError` | **同一 class ∴ 通過する（★予測 ―― ★実走で 確認する）** |

```
★★変わらない 点 = 1,2,3,5,7,8（★8点中 6点 不変）
★★新 state 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 file 0
```

### ★予想外の 影響点（★調べた ―― ★DESIGN_HOLD しない 根拠）

```
★`bridge_minter` を import して いる 本番コード = ★★0件（★§1-8 実測）
   ∴ ★この 変更で 壊れる 本番の 呼び手は ★居ない。
★`regression/` の 5件は ★bare `import patch_bridge as pb` で ★自分で path を 足して 動く 形
   ―― ★★それらは `pb._EnergizedApply` を ★自分の 側で 使う ∴ ★影響を 受けない。
   ★★但し ★`regression/gate_s4_energization.py:53` は ★`isinstance(tok, pb._EnergizedApply)` を 見て いる
     ＝ ★★mint が package 側 class を 返すと ★★この 回帰は False に なり得る（★★要 実走確認）。
★★∴ ★★実装前に ★この 回帰 1件の 挙動を 確かめる 必要が 在る（★§6 で 2DER に 渡す ときの 受入条件に 入れる）。
```

---

## ⑥ ★判定 ―― **GO（★但し 実装主体は 2DER）**

```
★A/B の 原因は ★実走で 再現済み ／ ★修理は ★import 1行 ／ ★影響範囲は 全件検索で 確定
★予想外の 影響点 = ★1件 見つかった が ★★調査可能 ∴ ★DESIGN_HOLD に しない（★受入条件へ 入れる）
★★∴ ★§6 に 従い ★2DER へ IMPLEMENT として 渡す。
★★#1（adjudication writer）は ★★A/B とは 別の 欠損 ∴ ★この 修理では 閉じない（★隠さず 残す）
```
