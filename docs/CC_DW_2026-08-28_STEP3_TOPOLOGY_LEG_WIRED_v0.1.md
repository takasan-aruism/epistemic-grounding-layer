# DW 手3 — 配線 1本目（Topology）と 2本目（自分の実行痕跡）v0.1

- 担当: DW（`DW_CLAUDE`） / 開発票: `ITEM-2DER-EVO-0137`
- 日付: 2026-08-28 08:1x〜08:3x
- 形式: **同じ口が 繋ぐ前と 後で 違う答えを 返すこと**（★指示 §6-3 の受入そのもの）
- 使った口: `to_domain("route_topology_report", force=True)`（★経路表 Domain の 読むだけの計器）

---

## 0. 前後（★同じ口・3回引いた）

| 時点 | DW 8 operation の GREEN | DW の欠け条件 合計 | 全体 verdicts | `UPSTREAM_DW_NO_OWNER` |
|---|---|---|---|---|
| **繋ぐ前** | **0 / 8** | **16** | UNWIRED 41 / PARTIAL 6 / GREEN 12 | **8** |
| **leg1 の後** | **2 / 8** | 14 | UNWIRED 39 / PARTIAL 6 / **GREEN 14** | **6** |
| **leg2 の後** | 2 / 8 | 9 | 同上 | 6 |
| **leg2 が常駐で走った後** | 2 / 8 | **8** | 同上 | 6 |

★保存則（`not_green == 各原因の合計`）は 3回とも `holds: true`。

### 行ごと（★前 → 後）
```
contract_with_precheck  missing=[authority,呼び手,記録,実行痕跡] → [呼び手]
submit_next_contract    missing=[authority,実行痕跡]             → [authority]
receive_finished        missing=[authority,実行痕跡]             → [authority]  ★常駐が新コードで1周した後に閉じた(08:34:13)
record_stages           missing=[authority,実行痕跡]             → [authority]
design_from_case        missing=[authority,呼び手]               → 変わらず
audit_case              missing=[authority,呼び手]               → 変わらず
dw_summary              UNWIRED  missing=[呼び手]                → ★GREEN
dw_escalations          UNWIRED  missing=[呼び手]                → ★GREEN
```

---

## 1. leg1 — 「呼べる」を「呼ばれている」にした

**欠損**: `dw_summary` / `dw_escalations` は 表に載って **呼べる**のに **呼び手が 0** だった
（＝ 手2 で作った口が、そのままでは **札だけ**になる）。
★これは `EVO-0120` が自分で踏んだ「**口を作った ≠ 呼ばれている**」と同じ型。

**やったこと**: `manager_v0.main()` の巡回に **呼び手を1つ**足した（★中身は1行も書かない）。
```
_dws = to_domain("dw_summary")
_dwe = to_domain("dw_escalations", limit=0)
_record({"action": "DW_STATE", …}, {state / tasks / backlog / human_decision_waiting /
                                     ready_to_close / escalations / receive_queue_len …})
```
★毎周 呼んでよい根拠 = 両方とも読むだけ・自分で `READ_ONLY_INSPECTION` の門を通る・実測 0.24s＋0.21s
（★`ledger_unassigned_report` を毎周に載せた時と同じ根拠）。
★`limit=0` = 一覧は出さない（**General は数だけ見る** ―― 正本 §8）。

### ★1-1. 「札だけ」で終わっていないことを実測した（★源泉が違う証拠）
`systemctl --user restart twoder-manager` の後、**常駐が自力で呼んだ**ことを ETRACE の件数で確認:
```
08:21:47 常駐 再起動
08:23〜08:29  dw_summary 5 / dw_escalations 1   （★私が手で呼んだ分だけ）
08:30:07      dw_summary 6 / dw_escalations 2   ← ★★常駐が 1周目で 呼んだ
```
★**source に書いただけでは数えない。件数が増えたことを証拠にした。**

---

## 2. leg2 — 自分の実行を「登記名」で残す（★計器が名前で取り違えていた）

**欠損**: `submit_next_contract` / `receive_finished` / `record_stages` は **毎周走っている**のに、
経路表は逐語「**実行痕跡が無い**」と出していた。

**原因（実測）**: 記録の `function` が `submit_contract` / `receive_artifact` で、
**登記名（`DOMAIN_OPERATIONS` の語）と別**だった。
★＝ `[[instrument-breaks-like-the-system]]`「**対応は名前でなく作用で取る**」の実例が、
★**私の Domain の側**に在った（計器の側だけの問題ではない）。

**やったこと（★既存の記録を1文字も変えない）**:
- 既存の `submit_contract` / `receive_artifact` の emit は **そのまま**（読み手が壊れる）
- **登記名の1行を足した**（`_dw_emit("submit_next_contract", …)` ほか）
- `contract_with_precheck` には **門（`READ_ONLY_INSPECTION`）と記録**を足した
  ★根拠 = この口は契約を組んで返すだけ（明細 +0 / thread +0 / file +0 / TASK +0。投げるのは `submit_next_contract`）

### ★2-0. これも「札だけ」で終わっていない（★常駐の実行で閉じた）
```
08:30:5x 常駐 再起動（★新しい domain_dw を読ませる）
08:31〜08:33  receive_finished 0    （★私が手で呼んでいない＝387秒かかるので呼ばない）
08:34:13      receive_finished 1    ← ★★常駐が 1周目で 登記名の記録を 残した
```
∴ `receive_finished` の `実行痕跡` が閉じ、**DW の欠け条件 合計は 16 → 8（半減）**。

### ★2-1. 挙動を変えていないことを「前と同じ数字」で確かめた
```
contract_with_precheck  GO 路: skeleton 76B / verdict=GO      （前と同じ）
contract_with_precheck  STOP 路: reason=precheck_stop         （前と同じ）
submit_next_contract    pending=0 / already=88                （前と同じ）
record_stages           PLACED 122 / CONNECTED 0 / OBSERVED 0 / USED 23（前と同じ）
```
★「エラーが出ない」を証拠にしていない（`[[verify-refactor-by-same-numbers-not-absence-of-error]]`）。

---

## 3. ★残った欠けと、それを私が閉じない理由（★上げる）

| operation | 残り | なぜ私が決めないか |
|---|---|---|
| `submit_next_contract` | `authority` | ★TASK を作る口 ∴ 当てる先は `AUTONOMOUS_TASK_CREATION`（**REQUIRES_APPROVAL**）に見える。門を当てると **投函が止まる** |
| `receive_finished` | `authority` | ★`_place_and_commit` が **git commit / push** する ∴ `COMMIT_PUSH`（**IRREVERSIBLE / REQUIRES_APPROVAL**）。門を当てると **2026-08-17 に Taka が明示許可した「機械が置いて commit する」が止まる** |
| `design_from_case` / `audit_case` | `authority` + `呼び手` | ★Worker を起こす / 0017 へ介入記録を書く ∴ 段が違う。★呼び手を作るのは **巡回に載せる＝ TASK を動かす**こと ∴ 私の一存で載せない |
| `contract_with_precheck` | `呼び手` | ★**呼び手が実在しない**（契約を組む側がまだ居ない）∴ **呼び手を捏造しない** |

★**どれも「1語足せば GREEN になる」が、GREEN にするために機械の効き目を止めるのは本末転倒** ∴ 裁定を仰ぐ。

---

## 4. ★経路表側の欠陥を1つ見つけた（★私は直さない＝他 Domain の内部）

`domain_route_table.route_topology_report` は **`if r["domain"] == "dw": cause = "UPSTREAM_DW_NO_OWNER"`** と
**domain 名で原因を固定**している。逐語の説明は「**dw は担当不在**」。

★**2026-08-28 から DW には担当が居る（本票）** ∴ **この原因名はもう事実でない。**
★かつ「原因」が **条件の欠け方から導かれず domain 名から決まる**ので、
★他 Domain と同じ欠け方をしていても **別の原因名が付く**（＝ 原因の集計が Domain 名に汚染される）。

★**Route/Topology 担当へ渡す。私は 1文字も直していない。**

---

## 5. していないこと

- `dev-workcell/dw/workcell.py` / `dispatch.py` —— **1文字も触っていない**
- `domain_route_table.py` —— **1文字も触っていない**（§4 は報告のみ）
- 既存の ETRACE の `function` 名 —— **1つも変えていない**（足しただけ）
- TASK を 1件も進めていない ／ 新台帳 0 ／ 新 state 0 ／ 新 ID 族 0
