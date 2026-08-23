# 明細システム改修 ―― **DW 側から見た障害** v0.1（事前定義）

発: ESDE Evaluation 専任監査（Claude）／ 宛: MGR
根拠: Taka 指示 2026-08-23「変更が発生するたびに DW 寄りの目線で何が障害になるかを事前に定義して MGR に返せ」
基準資料: `TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1.md` / `CC_MGR_2026-08-23_DETAIL_LIFECYCLE_GAP_TABLE_v0.1.md`
台帳: `ITEM-2DER-EVO-0090`

**★これは障害の列挙であって設計案ではない。★実装 0 行。**

---

## 0. まず MGR の調査を支持する（★そのまま良いと言う）

- 分母つき（974明細 / 625thread / 557task）で、**相関と因果を分け、交絡まで名指し**している
- **別名 import の罠に1回落ちたことを書いている**（`grep "list_questions("` は `import ... as _LQ` を拾わない → import 文で数え直した）
- §15「明細が PLAN/worker へ 0件」は **私の側の鍵でも確認した**:
  **`dev-workcell` 配下に `rthread` / `question_id` / `request_thread` の参照は 0 件。**
  ∴ **DW は明細の存在自体を知らない。**

## ★★MGR の発見と私の発見が繋がる（★合成すると機構になる）

| 誰 | 見つけたもの |
|---|---|
| MGR | `EF6826DC` は **SPEC 0 / TEST 0**。`ED65242E` は SPEC 8 / TEST 6 |
| 私 | `build_planner.py:176` が **`MUST cover the missing-file case and the malformed-JSON case`** を全件に注入 |

**2つは同じ1つの機構の両端である:**

```
依頼に TEST 明細が 0 件
  → PLAN の prompt に残るのは ★固定要求だけ
  → Qwen は missing-file / malformed-JSON を書くしかない
  → ファイルを扱わない関数に config_path を発明
  → 実装と永久に不一致
依頼に TEST 明細が 6 件（ED65242E）
  → 固定要求が★上書きされる → 発明 0 件
```

∴ MGR の相関（TEST_MISSING で完了率 8% vs 32%）に **因果の経路が1本付く**。
∴ **`requirement_gaps` は「相関」から「producer の入力が空になる条件の検出器」へ格上げできる。**
★但し格上げの証明は未実施（UNVERIFIED）。★2件の対照だけで因果と言わない。

---

## 1. 障害（DW 側・実測つき）

### 障害1 — **DW に「部分」の辺が無い**（親子・所属）
- `create_task(task_id, project_id, goal, knowledge_packet, ts, manager_identity, contract, supersedes)`
  ―― **親を指す欄が無い**。`parent_task` / `part_of` / `subtask` の実装は 0 件。
- 唯一の task 間の辺は本日私が入れた `supersedes` だが、**意味は「置換」であって「部分」ではない**。
- **★流用してはいけない**。明細 N 件を task N 件にすると、`superseded_by()` が
  「置き換えられた」と「分割された」を区別できなくなる。
- **MGR へ返す問い**: 明細と task の対応は **1:1 / N:1 / 1:N のどれにするのか。**
  決めないまま明細を細かくすると、DW 側は **1 submission = 1 task** のまま変わらない。

### 障害2 — **契約が task 単位でしか成立しない**
- 契約 = `skeleton` 1つ + `immutable_tests` 1つ + `target_file` 1つ
- `ALLOWED_TARGET_FILES = ("impl.py",)` ―― **1 file 固定**（Taka 裁定で1件ずつ足す物）
- 明細ごとに SPEC/TEST が付いても、**それを収める契約の器が無い**
- **MGR へ返す問い**: 明細 13 件の TEST をどう1つの `immutable_tests` に畳むのか。
  畳まないなら **task を割る＝障害1 に戻る。**

### 障害3 — **部分完了を表せない**
- `STATES` 13語は**すべて task 全体の段**。「13明細のうち9件成立」を表す語が無い。
- `completion_blockers` も **task 全体が単位**（実測）。
- **MGR へ返す問い**: 明細単位の充足を state で表すのか、欄で表すのか。
  ★state を増やすなら Taka 裁定。★欄なら `derive_state` の view に足すだけで済む（★こちらが安い）。

### 障害4 — **PLAN の入力に明細が入らない**
- `_plan_prompt(goal, provenance)` ―― 受け取るのは **`goal`（raw_input 全文）と ID 群だけ**
- 明細が意味単位になっても、**PLAN からは全文しか見えない**
- 入力を変えると `EXECUTABLE_KEYS`（`requirement/target_file/test_file/test_body/test_command/allowed_files`）の
  検証と `contract_from_plan` の導出が連動して変わる
- **MGR へ返す問い**: PLAN に渡すのは「明細の集合」か「明細1件」か。
  ★前者なら prompt の変更だけ。★後者なら障害1・2・3 が全部起きる。

### 障害5 — **私が本日入れた門が明細を知らない**（★自分の物を先に挙げる）
- `dw/test_repair_gate.py` は **PLAN 1本の `test_body`** から `invalid_tests` / `preserve_tests` を出す
- 明細ごとに試験が付くと **`preserve_tests` の分母が変わり、門の判定が変わる**
- **★明細を細かくする前に、私の門の分母定義を直す必要がある。** 直さないと黙って誤判定する。

### 障害6 — **やり直しの粒度が未定義**
- 本日 Taka 裁定で `supersede`（設問ごと新ID）と `TEST_REPAIR`（試験だけ）の2つが在る
- 明細が単位になると **3つ目「明細1件だけ作り直す」** が要る／要らないが決まっていない
- **MGR へ返す問い**: 暫定原則（契約維持なら TEST_REPAIR / 契約が変わるなら supersede）に
  **明細差し替えを足すのか。**★Taka は「反例を実測してから固定する」と言っている ∴ 急がない。

### 障害7 — **原文は DW 側に残っている**（★これは good news）
- MGR §3: 明細は `submit.py:529` の `m[:200]` で **974件中295件(30%)が切断**
- **★但し DW の `CREATE payload["goal"]` は raw_input 全文を持つ**（実測: ED65242E の goal に全文）
- ∴ **切れた原文は DW から復元できる。** 明細側に `source_span` を後付けする材料は在る。
- **MGR へ返す**: 復元の起点は **DW の CREATE**。RRI 側だけ見ると「失われた」に見える。

### 障害8 — **書き手だけ増える型に入りかけている**
- MGR §14 実測: 明細の読み手は **ID解決・科目・表示 の3用途だけ／開発判断に使う読み手 0**
- 本日私が見た同型: `artifact_registry.supersedes`（読み手0）/ `function_table`（本線の呼び手0）/
  `planner_outcome`（応答にだけ載り台帳に残らない）
- **★明細を細かくするほど、読み手が付かないまま情報だけ増える。**
- **MGR へ返す**: 明細の欄を増やす時は **その欄を読む本線の1点を同時に決める。**
  ★私の本日の実装ではこれを守った（`supersedes` に `superseded_by()` を同時に付けた）。

---

## 2. 順序についての意見（★決めるのは Taka と MGR）

DW 側から見ると、**先に決めるべきは障害1（明細と task の対応）**である。
1 が決まらないと 2・3・4・6 は決められない（全部 1 の従属）。
5 は 1 が決まってから私が直す（★私の物なので私が持つ）。
7・8 は **いま守れる**（原文の起点を DW にする／欄を足す時に読み手を同時に決める）。

## 3. 私が監視するもの（Taka 指示「動きを監視しておく」）

- `TASK-2DER-EF6826DC`（BLOCKED・対照の失敗側）
- `TASK-2DER-ED65242E`（PLANNING・対照の成立側・TEST_REPAIR の実証待ち）
- ★両方が MGR の対照実験に使われている ∴ **私が状態を動かすと対照が壊れる。**
  **★Taka の明示指示が無い限り、この2件には触らない。**
