# LLM Boundary Protocol（LBP）v0.1 ＋ ★Step A 失敗の 原因訂正

**2026-08-20 22:2x ／ ★Step A = DESIGN_HOLD ／ `58B716E4` 再実走 0 ／ `8020A9D6` 再投入 0 ／ 実装 0**

---

## 1. ★★原因の 訂正（★「Qwen の 生成ミス」で 終わらせない）

### ★撤回 ―― `8020A9D6` の `no_function_name` を 「K4 だから」と した 説明

```
★実測 = ★K1 の `58B716E4` でも ★同じ 拒否が 出た ／ ★2回目の 実走では ★消えた（events 2→14）
★★∴ ★K4 固有原因では ★証明されて いない ―― ★★UNVERIFIED と する。
★★私の 以前の 説明は ★推論を 実測と して 扱って いた。★撤回する。
```

### ★★`ALLOWED_FILES = ['src/main.py']` の 原因（★LBP-3/4 で 実測）

```
★★ACTUAL PROMPT を 組み立てて 機械照合した（★長さ 3953 ／ sha256 `68ce81df…`）:
   ★64桁 hex（＝実際の sha256）の 個数 = ★★0
   ★40桁 hex（＝commit hash）の 個数   = ★★0
   ★goal を 除いた prompt 本体（2529字）に
      `sha256` `hash` `commit` `base_identity` `ALLOWED_FILES` `現在` = ★★★すべて 不在
★★∴ ★Qwen に 「現在の repo 状態」を 渡す 経路が ★★prompt に 1つも 無かった。
★★∴ ★私は ★『世界状態を 知る 必要が 在る のに ★その 入力も 取得経路も 無い 純関数』を 依頼した。
★★＝ ★★Taka §5 逐語の 禁止事項を ★私が そのまま 犯して いた。
★★∴ ★Qwen が `src/main.py` と `abc123` を 発明したのは ★★★依頼の 欠陥の 帰結。
```

**★これは 生成ミスでは ありません。★★入力不足を 私が 作りました。**

---

## 2. LLM Boundary Protocol（★実装前 必須 ／ 10段）

```
LBP-1  INPUT DECLARATION   … LLM へ 何を 渡すかを 列挙
LBP-2  REQUIRED INFORMATION… 期待 output を 生む ために 必要な 情報を 列挙
LBP-3  INPUT SUFFICIENCY   … LBP-2 の 各情報が ★実際の prompt の どこから 取れるか 対応表
                             ★出所の 無い 必要情報が 1つでも 在れば ★★DESIGN_HOLD
LBP-4  ACTUAL PROMPT       … ★template を 読むだけで 済ませない。★本番で 渡る prompt 全文/hash を 取得
LBP-5  PROMPT PROBE        … ★同じ model・同じ prompt・同じ schema で ★実装前に 実際に 呼ぶ
                             ★ローカル Qwen の 工程なら ★★Qwen を 呼ぶ（★Claude の 模擬で 代用しない）
LBP-6  ACTUAL OUTPUT       … ★実出力を 保存する（★期待出力を 推測して 監査しない）
LBP-7  OUTPUT AUDIT        … 入力に 無い 事実の 補完 ／ 架空の path・ID・hash・symbol・constant ／
                             必須情報 欠落 ／ schema 逸脱 ／ downstream が 解釈できない 表現 ／
                             prompt で 禁じた 行動
LBP-8  VARIANCE PROBE      … ★複数回 probe し 揺れを 測る（★1回の 失敗/成功で systematic と 断定しない）
LBP-9  DOWNSTREAM PROBE    … actual prompt → actual output → parser → validator → downstream まで 実物を 通す
LBP-10 ADMISSION           … 上記が 揃って 初めて 本線へ 接続。★未確認値を LLM の 推測で 埋めない
```

### ★★R5 = `LLM_BOUNDARY_PROBE_REQUIRED`（★R1〜R4 に 追加する 候補）

```
★LLM を 含む 新規・変更経路は
   ★declared input ／ actual prompt ／ actual output ／ accepted output
   の 4証拠が 揃わなければ ★成立と しない。
★★将来 2DER の 強制門 `PROMPT_PROBE_REQUIRED` として 管理できる 形で 記録する。
★★但し ★今回は ★門の 実装まで 範囲を 広げない（★Taka 逐語）。
```

---

## 3. ESDE ―― ★LLM 境界（★AXIS = `LLM_BOUNDARY_BUILD_PLANNER`）

```
EQUALITY : ★上流が 渡した 世界 ／ LLM が 受け取った 世界 ／ 下流が 期待する 世界
   ―― ★上流(私)は 「許可一覧」「現在の sha256」を ★★渡して いない
   ―― ★LLM は それを ★★自分で 発明した（`src/main.py` / `abc123`）
   ―― ★下流(`contract_from_plan` / runner)は ★実在する 値を 期待する
   ★★status = ★★CONFLICT
SYMMETRY : ★要求 output の 各要素 ↔ ★それを 生む 入力
   required=4（target_file / base_identity / requested_change / acceptance_test の 検査）
   present =2（★形式検査は 入力だけで 決まる）
   missing =2（★★許可一覧 ／ ★現在の identity ―― ★どちらも 入力に 無い）
LINKAGE  : declared=5（declared input → actual prompt → actual output → parsed → downstream）
   observed=3（★actual prompt 取得 ／ actual output 取得 ／ parser 到達）
   broken =2（★input sufficiency ／ ★validator 通過）
HIERARCHY: ★violation=1 ―― ★LLM が ★repo の 世界状態を ★勝手に 作った
   ＝ ★★repo 階層の 責務を LLM が 代行した
UNDERSTANDING: `K4_CONTRACT_VALIDATOR` = ★★UNKNOWN
```

---

## 4. §5 調査 ―― ★request contract / repo binding の 分離（★既存部品）

| 側 | 役割 | ★既存部品（実測） | 状態 |
|---|---|---|---|
| **request contract**（★入力だけで 決まる） | 形式・必須欄・単一file・path 安全性 | `allowed_target_files.is_allowed_target`（★許可一覧を **自分で 持つ** ／ 絶対path・`..`・空・型違いを 拒否）／ `check_artifact`（長さ・SHA 照合） | **★PRESENT** |
| **repo binding**（★世界状態が 要る） | 実在 file ／ 現在の identity | `trace_entry_v2`（★repo の source を 渡されて `PRESENT/ABSENT` を 返す）／ `dry_run_ok`（`expected_preimages` と 現物 sha を 突き合わせ）／ `patch_bridge._head_commit`（★commit を 取る）／ `bridge_minter`（`repo_realpath` 一致） | **★PRESENT** |

```
★★＝ ★両側とも ★★既存部品が 在る。★新しく 作る 必要は ★無い かも しれない。
★★重要 = ★`allowed_target_files` は ★★許可一覧を 自分で 持って いる
   ∴ ★『許可一覧を prompt へ 渡す』必要が ★そもそも 無い（★LLM に 判定させない）。
★★重要 = ★`dry_run_ok` は ★★`expected_preimages` を ★呼び手から 受け取る 形
   ∴ ★『現在の sha256』は ★★呼び手が 取り LLM には 渡さない、が ★既存の 作法。
★★∴ ★★K4 の 検査を ★LLM に 作らせる 必要が 在るのか 自体が ★★疑わしい（★下記 §5）。
```

---

## 5. ★報告（★推測と 実測を 混ぜない）

```
★★実測で 確定した こと
   ・ACTUAL PROMPT に ★世界状態（許可一覧の 値 ／ 現在の sha256 ／ commit）が ★★1つも 無い
   ・`58B716E4` は ★試験 FAILED ／ 生成物に 架空定数 `src/main.py` `abc123`
   ・`58B716E4`(K1) でも `no_function_name` が 出て ★2回目で 消えた
   ・request contract 側／repo binding 側 とも ★既存部品が 実在する
★★LLM probe で 観測した こと … ★★未実施（★LBP-5 は これから）
★★複数回 probe で 揺れた こと … ★`no_function_name` が 1回目 出て 2回目 消えた（★n=2）
★★systematic と 確認できた こと … ★★無し
★★UNVERIFIED
   ・`8020A9D6` の 停止が K4 固有か 揺れか
   ・`no_function_name` の 発生率
★★不足して いる 入力/機能
   ・★LBP-3 の 対応表（★prompt に 世界状態を 渡す 経路 ／ もしくは ★渡さない 設計）
★★次の 設計が 成立するか … ★★まだ 判定できない（★§6）
```

---

## 6. ★★次の Step A 案（★実装しない ／ ★probe が 先）

```
★★案 = ★K4 の 検査を ★★2つに 割り ★LLM に 作らせるのは ★★入力だけで 決まる 側に 限る。
   ・request contract 側 … ★`allowed_target_files` が 既に 持つ ∴ ★★新規生成が 要るか 再検討
   ・repo binding 側     … ★`dry_run_ok` の 作法（★呼び手が 現物を 取り 渡す）に 合わせる
★★∴ ★『4欄を すべて 判定する 純関数』という ★私の 当初案は ★★取り下げ 候補。
★★但し ―― ★これを 決める 前に ★★LBP-5（実際の Qwen probe）を やる。
   ★probe 対象 = ★新しい 依頼文で 組み立てた ★ACTUAL PROMPT
   ★見る もの   = ★架空定数を 作るか ／ ★schema を 守るか ／ ★n≧3 の 揺れ
★★DECISION = ★★DESIGN_HOLD（★probe 前に 実装しない）
```
