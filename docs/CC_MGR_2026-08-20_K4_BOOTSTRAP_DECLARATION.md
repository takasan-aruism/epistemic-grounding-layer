# K4（既存file 局所変更）成立 ―― ★BOOTSTRAP 前の 宣言（★裁定 ④ に 従い ★実装前に commit）

**2026-08-20 21:2x ／ ★実装 0 ／ ★`8020A9D6` 再投入 0**

---

## 0. ★裁定の 反映（★逐語 → 何を するか）

```
①CHANGE_KIND は ★PLAN の 正式な 宣言値。★既存欄から 推定しない。★下流は 同じ 値を 読む（★再推定 禁止）
②今回は ★K1 と K4 のみ。★K2/K3 は 調査結果を 保持。★K5 は ★★入口で KNOWN_UNSUPPORTED として 拒否
   （★下流まで 流して REFUSED_MULTI_FILE に しない）
③K4 の 対象 = `target_file` ＋ `base identity(commit/hash)` ＋ `requested_change` ＋ `acceptance_test`
   ★行番号を 正本に しない。★変更箇所と 変更後 diff は ★成果物と して 観測する
④★自己参照の 最後の 既存file変更 のみ ★一回限りの BOOTSTRAP を 許可（★通常の Claude 代行では ない）
⑤BOOTSTRAP を 成功と しない。★2DER 自身に 新しい K4 task を 1件 実走させて 初めて K4=SUPPORTED
```

---

## 1. ★変更前の 因果鎖（★端から 端まで ／ ★実測）

| # | 点 | 誰が作る | 何を作る | どこに保存 | 次に誰が読む | 無い/不正なら | 本線で 呼ばれるか |
|---|---|---|---|---|---|---|---|
| 1 | PLAN schema | `build_planner._plan_prompt` | Qwen へ の 鍵の 一覧 | ― | Qwen | ― | ✔ |
| 2 | PLAN validate | `build_planner.validate` | `STRUCTURED_KEYS`(11) ＋ `EXECUTABLE_KEYS`(6) の 検査 | ― | `record_plan` | `recorded=False` | ✔ |
| 3 | **契約** | `contract_from_plan` | `skeleton` ＋ `immutable_tests` | ― | `domain_dw.contract_with_precheck` → GENERATE | **★K4 は `no_function_name`（実走で 取得）** | ✔ |
| 4 | GENERATE | `qwen_worker` | **sandbox の `target_file` を 全文 生成** | sandbox | `run_test` | 骨格検査 ／ 試験 | ✔ |
| 5 | TEST | runner | `test_result` | event log | AUDIT | `passed=False` | ✔ |
| 6 | AUDIT | `QWEN_AUDITOR` | findings | event log | DISPOSE | blocker | ✔ |
| 7 | authority | `bridge_minter.mint_real_energize` | `_EnergizedApply` | ― | `apply_cycle` | `MintRefused`(4条件) | **★本番 caller 0 ／ ★欠陥A** |
| 8 | APPLY | `apply_cycle` → `patch_bridge` | 実 file 変更 | working tree | git | `_require_energize` / dry-run | **★本番 caller 0** |
| 9 | rollback | `patch_bridge:298` | 復元 ＋ `ROLLED_BACK` | working tree | ― | `rollback_allowed` | ★APPLY 内 |
| 10 | COMPLETE | `completion_blockers` → `propose_complete` | COMPLETE event | event log | ― | blocker | ✔ |

```
★★K4 が 止まる 点 = ★#3（★契約）。★#7/#8 は ★別の 欠損（★A/B ／ caller 0）。
```

---

## 2. ★★BOOTSTRAP の 範囲（★一回限り ／ ★最小）

```
★★変更対象 file = ★★`twoder/build_planner.py` ★★1件のみ
★base identity:
   ★repo   = `/home/takasan/twoder`
   ★HEAD   = `46fc24e3def45bf90997efdd5725277b4f20840d`
   ★sha256 = `3b50886f0f6b1819d8c2c6a33131cc12b4f84448adaa1fdb75d1f4b41e4a0277`
   ★行数   = 386
★★触らない file（★宣言）:
   `contract_from_plan.py`(sha256 `3c457b0a…`) ／ `apply_cycle.py` ／ `patch_bridge.py` ／
   `bridge_minter.py` ／ `qwen_worker.py` ／ `workcell.py` ／ `webui.py`
```

### ★BOOTSTRAP で 入れる 変更（★3点 ／ ★diff の 形）

```
★(a) `STRUCTURED_KEYS` に ★`change_kind` を 1語 足す（★11 → 12）
★(b) `_plan_prompt` に ★`change_kind` の 行を 足す
     ―― ★語彙 = `NEW_FUNCTION`(=K1) ／ `MODIFY_FILE`(=K4)
     ―― ★K4 の ときは ★`base_identity` `requested_change` `acceptance_test` も 宣言させる
★(c) `validate` に ★分岐を 足す
     ・`change_kind` 欠落            → `recorded=False`（★既存と 同じ 形）
     ・`change_kind` が 語彙外        → 同上
     ・`MULTI_FILE` 等 K5 相当         → ★`KNOWN_UNSUPPORTED` で ★★入口 拒否
     ・`NEW_FUNCTION`                 → ★★従来の 検査を そのまま（★1文字も 変えない）
     ・`MODIFY_FILE`                  → ★★`contract_from_plan` を 呼ばず
                                        ★2DER が 作った ★K4 契約器を 呼ぶ
★★★`contract_from_plan` の 検査を ★1文字も 消さない（★K1 では 従来どおり 効く）
```

### ★★前提（★BOOTSTRAP の 前に 2DER が 作る）

```
★K4 契約器 = ★2DER に ★★K1（新規関数）と して 作らせる ―― ★★通常経路で 作れる。
   ★入力 = `target_file` / `base_identity` / `requested_change` / `acceptance_test`
   ★出力 = `{"ok", "reason"}`（★★行番号を 正本に しない）
   ★配置 = `_place_and_commit` が ★`twoder/<関数名>.py` へ（★稼働中の 経路）
★★∴ ★BOOTSTRAP は ★★『既に 実在する 関数を 呼ぶ 1行＋schema 2点』に 縮む。
```

---

## 3. authority / rollback / 受入試験

```
★authority = ★BOOTSTRAP 自体は ★Taka 裁定 ④（★本メッセージ）。★real repo の patch 経路は 使わない
   （★`build_planner.py` は ★私が 直接 編集する ―― ★★これが 『一回限り』の 意味）
★rollback  = ★`git revert <bootstrap commit>` 1回。★触る file が 1件 ∴ ★戻す 範囲が 確定して いる
★受入試験（★BOOTSTRAP 直後に 私が 実走する）:
   ①`change_kind` 欠落 → `recorded=False`
   ②語彙外 → `recorded=False`
   ③K5 相当 → ★入口で `KNOWN_UNSUPPORTED`
   ④`NEW_FUNCTION` → ★★従来と 同じ 結果（★K1 の 回帰）
   ⑤`MODIFY_FILE` → ★K4 契約器が 呼ばれる
★★但し ―― ★これらは ★★『BOOTSTRAP の 成功』では ない（★裁定 ⑤）。
```

---

## 4. ★★変更後に 2DER 自身が 行う 再実証（★これが 成功条件）

```
★2DER に ★新しい K4 task を 1件 投入し ★次を 実走で 通す:
   PLAN(change_kind=MODIFY_FILE) → contract → GENERATE → TEST → AUDIT → authority
   → APPLY → real repo 変更 → post-test → declared/observed 照合 → COMPLETE 判定
★★この 一周が 通って 初めて ★K4 = SUPPORTED。
★★R4（★拒否も 実際に 発火させる）:
   change_kind 欠落 ／ base identity 不一致 ／ target_file 不正 ／ acceptance test 失敗 ／
   authority なし ／ apply 失敗 ／ declared edge 不足
```

---

## 5. ★★既に 判って いる 阻害要因（★隠さない）

```
★#7/#8 = ★`mint_real_energize` と `apply_cycle` の 本番 caller 0 ／ ★欠陥A(class identity)
★★∴ ★『APPLY → real repo 変更』は ★★K4 の 契約が 通っても ★まだ 到達しない。
★★∴ ★裁定 ⑤ の 一周は ★★A/B の 修理が 済むまで 完結しない。
★★A/B の 修理（`bridge_minter.py:26`）自体が ★K4 ∴ ★★『K4 が 成立したら A/B を K4 で 直す』
   という 順序に なる ―― ★★これが 本件の 出口。
```

---

## 6. ESDE 宣言（★変更前 ／ ★AXIS=`K4_ENABLEMENT`）

```
EQUALITY : ★change_kind を ★PLAN / contract / generator / test / artifact / apply が ★同じ値で 読むか
           → ★現状 ★★どこにも 存在しない ＝ ★CONFLICT
SYMMETRY : required=4(K1契約↔K1配置 ／ K4契約↔K4適用 ／ 拒否↔受理 ／ apply↔rollback)
           present=2 ／ missing=2（★K4契約 ／ K4適用の 本番 caller）
LINKAGE  : declared=10（§1 の 10点）／ observed=8 ／ broken=2（★#3 K4契約 ／ #7-#8 caller 0）
HIERARCHY: required=5 ／ passed=5 ／ violation=0 ／ unreachable=1（★#7 authority へ 到達できない）
R1〜R4   : ★BOOTSTRAP 後に 測る（★いまは 未実施）
UNDERSTANDING: `SAFE_EXISTING_FILE_MODIFICATION` = ★UNKNOWN
DECISION : ★★GO（★但し ★Step A → Step B → Step C の 順序を 守る）
```

---

## 7. ★実行順序（★この 宣言の commit 後）

```
★Step A ―― ★2DER に ★K4 契約器を ★K1 として 作らせる（★通常経路 ／ ★BOOTSTRAP では ない）
★Step B ―― ★私が ★`build_planner.py` を ★一回限り BOOTSTRAP（★§2 の 3点のみ）
           ★★Step A で 出来た 関数名が 確定してから ★具体の diff を ★もう一度 宣言して commit する
★Step C ―― ★2DER に ★新しい K4 task を 1件 実走させる（★裁定 ⑤ ／ ★R4 の 拒否も 発火）
★★どこか 1つでも 実証不能なら ★DESIGN_HOLD。★`8020A9D6` は ★まだ 再投入しない。
```
