# 宛: Taka ―― **「仕事種別」と「納品形式」を 分ける ★最小差分案 と ★影響範囲**

**2026-08-20 06:0x ／ ★設計調査のみ ／ ★実装 0 ／ ★投入 0 ／ ★既存コード 変更 0**
**★SELF_DEV_TOKEN = ★5/5 ／ ★常駐 停止のまま ／ ★DISPOSE 0**

---

## 0. ★★納品形式を 固定している 本体（★実物・★1箇所）

```
★`dw/workcell.py::completion_blockers`（★COMPLETE を 阻む 理由・★全7種）:
   ① STATE_NOT_COMPLETABLE      … state が COMPLETE/BLOCKED/JUDGE_REQUIRED
   ★② IMPLEMENTATION_RUN_MISSING  … 逐語「implementation run + test_result が存在しない」
   ★③ TEST_NOT_PASSED             … 逐語「最新 implementation の test_result が passed=True でない」
   ★④ INDEPENDENT_AUDIT_MISSING   … 逐語「independent audit run が存在しない」
   ⑤ FINDING_DISPOSITION_MISSING
   ⑥ FINDING_DISPOSITION_OPEN
   ⑦ UPPER_REVIEW_MISSING
★`dispatch.py:75-77` ―― ★`blockers` が 空の ときだけ `PROPOSE_COMPLETE`(GATE) が 出る。
★`workcell.py:520` ―― `propose_complete` 逐語「Manager は COMPLETE を *提案* するだけ。
   gate が event log を見て決める。★bypass 経路は無い。」
```

```
★★＝ ★②③④ が ★すべての task に ★無条件で 課される。
★★＝ ★『何を する 仕事か』に 関係なく ★『artifact ＋ 通った 試験 ＋ 独立監査』が ★完了の 必要条件。
★★＝ ★ここが ★『仕事種別と 納品形式の 同一視』の ★実体（★1関数・★3条件）。
```

## 1. ★★使える 既存の 部品（★調べて 出た もの）

| 部品 | 実物 | 使い道 |
|---|---|---|
| `STATES` 13語 | `CREATED / PLANNING / READY_FOR_IMPLEMENTATION / IMPLEMENTING / READY_FOR_AUDIT / AUDIT_FAILED / DISPOSITION_REQUIRED / READY_FOR_REGENERATE / REWORK / READY_FOR_UPPER_REVIEW / JUDGE_REQUIRED / COMPLETE / BLOCKED` | ★`_MAP` が 使うのは ★9語 ∴ ★★4語（PLANNING / IMPLEMENTING / AUDIT_FAILED / REWORK）は ★空いている |
| `PHASES` 10語 | `CREATE / PLAN / GENERATE / AUDIT / DISPOSE / REGENERATE / UPPER_REVIEW / COMPLETE / BLOCK / ★PROCESS_EVENT` | ★`PROCESS_EVENT` は 逐語「★state に影響しない」＝ ★記録だけを 残せる |
| `create_task(..., ★contract=None)` | `workcell.py:411` | ★入口で 種別を 添える 余地（★既存の 引数） |
| `completion_blockers` | ★上記7種 | ★★ここを 種別で 分けるのが 最小 |
| `ITEM.acceptance` / `status_note` / `task_ids` | ★実在 | ★報告・観測の 成果の 置き場 |
| `RESULT_PACKET(contracts/out/)` | `propose_complete` の 出力 | ★完了の 証拠物（★artifact とは 別） |

## 2. ★★最小差分案（★★変更は ★1関数・★1引数）

```
★★(1) `create_task` の ★既存引数 `contract` の 隣に ★仕事種別を 1つ 記録する
      （★新しい 台帳 0 ／ ★新しい 記録面 0 ―― ★CREATE の payload に 1語 入るだけ）
★★(2) `completion_blockers` が ★その 1語を 見て ★②③④ を ★課すか 課さないかを 決める
      ・IMPLEMENT             → ★②③④ を 課す（★従来どおり・★変更なし）
      ・OBSERVE / INVESTIGATE / DECIDE / DESIGN / VERIFY / REPORT
                              → ★②③ を 課さない ／ ★④は 種別で 決める（★下表）
★★それ以外は ★触らない ―― `_MAP` も `STATES` も `propose_complete` も `RESULT_PACKET` も そのまま。
```

### ★種別ごとの 完了条件（★案・★artifact 生成なしで 完了できるか）

| 仕事種別 | 完了に 要る もの（★案） | artifact 無しで 完了 | 既存で 表せるか |
|---|---|---|---|
| **OBSERVE** | ★観測値が 記録に 在る（`MEASURED_STATE` / EGL ingest）＋ `UPPER_REVIEW` | **★可** | ★観測は 既に ingest される（`submit.py:601-627`） |
| **INVESTIGATE** | ★調べた 範囲と 出所が 記録に 在る ＋ `UPPER_REVIEW` | **★可** | ★`provenance` / `egl_source_refs` が 既に 在る |
| **DECIDE** | ★判断と 根拠が 記録に 在る ＋ `UPPER_REVIEW` | **★可** | ★`EGL_RESEARCH` 経路は 在る が ★出口が 無い（★§4 ①） |
| **DESIGN** | ★設計文書（骨格 or 案）が 記録に 在る ＋ `UPPER_REVIEW` | **★可** | ★`contract_seal` の 形が 既に 在る |
| **IMPLEMENT** | ★②③④ ★従来どおり | ★不可（★意図どおり） | ★変更なし |
| **VERIFY** | ★検証の 対象・手順・結果が 記録に 在る ＋ `UPPER_REVIEW` | **★可** | ★`test_result` の 形は 在る が ★対象が 他 task |
| **REPORT** | ★報告文が 記録に 在る ＋ `UPPER_REVIEW` | **★可** | ★`status_note` / `RESULT_PACKET` が 在る |

```
★★共通 = ★どの 種別も ★`UPPER_REVIEW`（⑦）と ★`DISPOSE`（⑤⑥）は ★残す
   ＝ ★『検査を 外す』のでは なく ★『実装の 証拠を 求めない』だけ。
★★＝ ★迂回でも 無効化でも ない（★Taka の 禁止に 触れない）。
```

## 3. ★★影響範囲（★実測・★触る 場所と 触らない 場所）

```
★★触る = ★2箇所だけ
   ・`dw/workcell.py::create_task`  … ★既存引数の 隣に 1語（★署名の 追加 1つ）
   ・`dw/workcell.py::completion_blockers` … ★②③④ の 前に ★種別の 分岐 1つ
★★触らない =
   ・`_MAP`（★9行）／ `STATES`（★13語）／ `PHASES`（★10語）… ★1語も 増やさない
   ・`propose_complete` / `RESULT_PACKET` … ★そのまま（★bypass を 作らない）
   ・`request_type.py` の 6語 … ★★増やすかは ★別問題（★§4 ②）
   ・経路表 / `name_matches_route` / `precheck_names` / authority / scope … ★不変

★★呼び手の 影響（★実測が 要る 点）:
   ・`create_task` の 呼び手 = ★`submit.py:659`(観測) と ★`:696 付近`(実装) の ★2箇所
   ・`completion_blockers` の 呼び手 = ★`dispatch.py:75` ／ ★`build_state`（webui）
   ・★既定値を 「IMPLEMENT」に すれば ★既存の 全 task は ★挙動が 変わらない（★後方互換）
```

## 4. ★★不足（★この 案でも 埋まらない もの・★2つ）

```
★★① DECIDE の 出口 ―― ★`EGL_RESEARCH` は ★DW task を 作らない（`submit.py:762-768`）
   ∴ ★`completion_blockers` を 直しても ★DECIDE は ★そもそも task に ならない。
   ＝ ★『判断を 記録して 次へ 繋ぐ』には ★DECIDE も task に する 判断が 要る。
   ★★これは ★経路の 変更 ∴ ★Taka の 裁定 事項（★私は 決めない）。

★★② 入口の 語が 3つ 足りない ―― `INVESTIGATE` / `VERIFY` / `REPORT` は
   ★`request_type.py:17` の 6語に 無い（`DESIGN` も 無い ＝ ★計4語）。
   ∴ ★種別を 記録できても ★入口で 判別できない。
   ★★語を 増やすか、★依頼文に 明示させるか、★別の 方法か ―― ★これも 裁定 事項。
```

## 5. ★★成功条件に 対する 見通し（★断定しない）

```
★ご指定の 成功条件 = ★『1件の OBSERVE または REPORT 依頼が、sandbox 実装物を 作らず、
   記録だけを 成果と して 正常完了できる こと』
★★OBSERVE なら ―― ★§2 の 2箇所で ★届く 見込み
   （★観測は 既に ingest され、★task も 既に 作られている ∴ ★あとは 完了条件だけ）
★★REPORT なら ―― ★§4 ② が 先に 要る（★入口に 語が 無い）
★★∴ ★最初の 1件は ★OBSERVE で 試すのが ★最短（★但し ★実装は していません）
```

## 6. ★していないこと

```
★実装 0 ／ 修正 0 ／ 投入 0 ／ sandbox 成果物 0 ／ 新しい 状態機械 0
★新しい 状態語 0 ／ phase 0 ／ 台帳 0 ／ 分類器 0 ／ 配線 0
★既存コード 変更 0 ／ DISPOSE 0 ／ 常駐 再開 0 ／ ★SELF_DEV_TOKEN 消費 0（★5/5）
★`ITEM.acceptance` 構造化案は ★保留の まま（★追加設計していない）
★★『閉じる』と 断定していない ―― ★§5 は ★見通しと 明記した
```
