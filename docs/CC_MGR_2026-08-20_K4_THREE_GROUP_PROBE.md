# K4 要求 3群分割 ―― PLAN ＋ GENERATE実コード probe（★実装 0 ／ ★ESDE 形式）

**2026-08-20 22:5x ／ ★`build_planner.py` 未変更 ／ ★BOOTSTRAP 0 ／ ★`8020A9D6` 再投入 0 ／ ★実 repo 変更 0**

裁定 逐語:
> 「K4をBOOTSTRAPしない。現行taskは終端として保存。10段単一関数が失敗原因という仮説を未確定で置き、
> 要求を3群程度に分割する。**次回probeはPLANだけでなくGENERATE実コードまで含め、各群n=3で安定性を測る。
> 安定した群だけを後で合成する。**」

---

## 0. 終端 task の 保存（★state・履歴 不変）

```
TASK-2DER-B7082857 → _terminal_escalation → escalation=HUMAN / opened=True / id=HESC-3c5102b25ed2
人待ち = ['TASK-2DER-229A3CD1', 'TASK-2DER-9F26BF5F', 'TASK-2DER-B7082857']
★DONE/BLOCKED/削除に して いない。★events 18 ／ rework_count 2 の まま。
```

---

## 1. probe の 範囲（★前回と 変えた 点）

```
★前回 = PLAN(契約)まで。★GENERATE の 出力コードは probe 対象外だった。
★今回 = PLAN → contract_from_plan → ★qwen_worker.default_chat_fn で 実コード生成
        → ★immutable_tests を その場で pytest 実走 まで 通した。
★本番と 同じ seam を 使った（★REQUIREMENT_TEMPLATE = generate_via_runner:118）。
★記録に 残らない 経路で 直接 叩いた（★front door を 通して いない ―― LLM の 判断だけ 見る 試験）。
```

| 群 | 判定させる もの | 引数（★すべて 呼び手が 渡す） | 拒否語 | prompt sha256 |
|---|---|---|---|---|
| **G1** | path の 形（★世界状態 不要） | `target_file` | `no_target` `absolute_path` `path_traversal` `multi_file` | `f99a89c43f45…`(第2回) |
| **G1′** | 同上（★受入を 9件に 閉じた） | 同上 | 同上 | `0acd0711678e…` |
| **G2** | 許可一覧に 在るか ＋ 目印 一致 | `target_file` `allowed_files` `base_identity` `current_identity` | `unexpected_target` `no_base_identity` `base_identity_mismatch` | `c5072efcc375…` |
| **G3** | 本文が 空でないか | `requested_change` `acceptance_test` | `no_requested_change` `no_acceptance_test` | `2a0a792f5f0e…` |

---

## 2. ★★実測（★分母つき ／ ★総合点に 潰さない）

| 群 | n | PLAN取得 | 契約通過 | 生成到達 | **封印試験 PASS** | **端から端** |
|---|---|---|---|---|---|---|
| **G1**（★列挙 開いて いた） | 6 | 5/6 | 4/5 | 4 | **1/4** | **1/6** |
| **G1′**（★列挙 閉じた） | 3 | 3/3 | 3/3 | 3 | **3/3** | **3/3** |
| **G2** | 6 | 6/6 | 6/6 | 6 | **6/6** | **6/6** |
| **G3** | 6 | 6/6 | 5/6 | 5 | **5/5** | **5/6** |

```
★架空定数（module直下の 定数定義）= ★★0/10（★保存した 生成source 10本を 機械照合）
   ―― ★`58B716E4` の `src/main.py` / `abc123` は ★再発しなかった。
   ★効いた もの = ★6欄すべてを ★引数に した こと（★LLM に 世界状態を 発明させない）。
★試験の 発明 = G1(開) 依頼5件 → ★生成7件 ／ G1′(閉) 依頼9件 → ★★生成9件・発明0
★関数名 = G1′ は ★3/3 同一(`validate_relative_path`) ／ G2 第2回 3/3 同一(`validate_target`)
   ★G3 第1回は 揺れた(`validate_inputs` ×2 / `check_inputs` ×1)  → ★名の 安定は ★UNVERIFIED
```

---

## 3. ★★撤回 ―― `no_function_name` は K4 固有では ない

```
★第1回+第2回 で ★★G1 と G3 の 両方で 各1回 発生 = ★★2/12（≒17%）／ G1′ では 0/3
★★∴ ★K4 固有でも 群固有でも 無い。
★★実体 = ★planner が `test_body` に `from impl import <名>` を 書き落とす ★一般の 揺れ。
★以前 UNVERIFIED と して 置いた 論点（★8020A9D6 の 停止が K4 固有か 揺れか）を
   ★★分母つきで 解く: ★★揺れ側（★K4 固有では ない）。
```

---

## 4. ★★G1 が 落ちた 原因（★実物 ／ ★実装では なく 試験の 側）

```
★生成された 実装 = ★★規則どおり 正しい
     if any(c.isspace() for c in target_file): return {'ok': False, 'reason': 'multi_file'}
★生成された 試験 test_malformed_json:
     validate_relative_path('{"key": "value"}')   ← ★★空白を 含む
     assert res["ok"] is True                     ← ★★自分が 書いた 規則4 と 矛盾
★★∴ ★封印試験を 書くのも LLM ∴ ★列挙が 開いて いると ★LLM は 場合を 発明し
   ★その 発明が ★自分の 規則と 衝突する。★実装は 悪く ない。
★★私が 列挙したのは 5件。★planner は `test_missing_file` `test_malformed_json` を 足した。
★★＝ ★★依頼文の 穴（★私の 欠陥）。
```

### ★なぜ G2/G3 は 落ちなかったか（★段数では ない）

```
★G2/G3 の 入力 = 「一覧に 在るか」「等しいか」「空か」 ＝ ★★取り得る 場合が 閉じて いる
★G1 の 入力     = ★自由な 文字列 ＝ ★★開いて いる
★★∴ ★効いて いるのは ★段数(10→4)では なく ★★入力領域が 閉じて いるか。
★★証拠 = ★段数 4 の まま 受入を 9件に 閉じただけで ★★1/4 → 3/3。★コードは 1行も 変えて いない。
```

---

## 5. ESDE（★AXIS=`K4_CONTRACT_GENERATION` ／ ★after-probe）

```
EQUALITY : ★上流が 渡す 世界 ／ LLM が 受け取る 世界 ／ 下流が 期待する 世界
   ―― ★6欄を すべて 引数に した ∴ ★世界状態の 発明 = ★★0/10
   ★★status = ★ESTABLISHED（★probe 範囲に おいて）
SYMMETRY : required=4（G1 形式 / G2 許可+目印 / G3 非空 / ★合成）
   present=3（G1′ G2 G3 が 端から端まで 通った）／ missing=1（★合成は 未実施）
LINKAGE  : declared=6（goal→prompt→PLAN→contract→GENERATE→封印試験）
   observed=6（★G1′ G2 で 6/6 実走）／ broken=0
   ★但し ★★observed の 範囲は ★probe まで。★本線(front door→DW)は ★★未接続 ＝ ★R1 不成立
HIERARCHY: required=3（LLM に 判定させない／呼び手が 世界状態を 取る／検査を 消さない）
   passed=3 ／ violation=0
R1 END_TO_END : ★★不成立（★probe は 直接叩き ／ ★正規上流から 実走して いない）
R2 DENOMINATOR: ★§2 の とおり 分母つき（★0/0 は 1件も 無い）
R5 LLM_BOUNDARY: declared input ✔ ／ actual prompt ✔(sha256) ／ actual output ✔(10本 保存)
   ／ accepted output ✔(★封印試験 実走) ＝ ★★4証拠 揃った
UNDERSTANDING: `K4_CONTRACT_VALIDATOR` = ★★PARTIAL
   ―― ★群単位では ESTABLISHED ／ ★合成と 本線接続は ★UNKNOWN
```

---

## 6. ★★結論 と 次の 一手（★Taka 裁定を 要する 点つき）

```
★★安定した 群 = ★★G1′ / G2 / G3 の ★3群すべて（★G1 は ★列挙を 閉じた 形でのみ 安定）
★★合成の 前に 決める 必要が 在る 事:
   ★① 合成の 単位 ―― ★3群を ★1関数に 束ねるか ／ ★3関数の まま 呼び手が 順に 呼ぶか
      ★実測が 支持するのは ★★後者（★束ねると 入力領域が また 開く）
   ★② `no_function_name` 17% の 揺れ ―― ★再試行で 消える（★実測 2回目で 消えた）が
      ★★本線では 何回 再試行できるかを ★確認して いない ＝ ★UNVERIFIED
   ★③ ★本線接続（R1）―― ★probe は 直接叩き ∴ ★front door → DW からの 実走は ★未実施
★★DECISION = ★合成の 単位(①)を 決めてから 進む。★実装は して いない。
```

---

## 7. ★して いない 事（★宣言）

```
★`build_planner.py` を 変更して いない（★sha256 3b50886f… / HEAD 46fc24e の まま）
★BOOTSTRAP して いない ／ ★`8020A9D6` を 再投入して いない
★実 repo を 変更して いない ／ ★`_place_and_commit` を 呼んで いない
★門を 1つも 迂回・削除して いない ／ ★台帳を 直読して いない
★SELF_DEV_TOKEN = ★5/5（★消費 0 ―― ★全周が 閉じて いない）
```
