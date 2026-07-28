# 設計/監査 → MGR（写: Taka / IMPL）: **D-45 — 管理UI の実測。★6項目中4つは既に出ている。出ていないのは「通過した処理」と「欠損・失敗」の2つである**

- `BUILD_ROLE: 参照`（**調査のみ。★何も作っていない・UI を1行も変えていない・投入していない・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8` — `§12` を最大版で読んだ値）**
- **正典**: `PHASE2_DIRECTION_MANAGEMENT_UI_v1_0.md` / **受領**: `CC_MGR_2026-07-28_D45_PHASE2_START_MEASURE_EXISTING_UI.md`

## 0. ★結論
> **★管理UI は既に在り、6項目のうち★4つは既に出ている。**
> **出ていないのは ③「通過した処理」と ⑤「欠損・失敗・未確認」の★2つだけである。**
> **∴ Phase 2 は「UI を作る」ではなく★「2項目を足す」で足りる可能性が高い。** **★ただし実装案は書かない**（禁止3）。

---

## 1. ★UI は2つ在る（`PAGE` だけではなかった）
```
再現: grep -n "PAGE = \|/command\|u.path == \"/\"" twoder/webui.py
```
| 画面 | 実体 | 中身 |
|---|---|---|
| **`/`** | `webui.py:430-447` の HTML | **「2DER — 開発状況 (read-only)」**。ロードマップ（items 数・状態タイル）／完成予測／off-ramp フラグ／直近アクティビティ（DE・CHG・人間介入）／承認待ち |
| **`/command`** | **`webui.py:613 PAGE`** | **「2DER」**。入力欄＋`REFRESH STATE`／`RUN NEXT`／`RUN UNTIL BARRIER`、および結果カード群 |

**★MGR の見立て（`PAGE` が管理UI の実体）は当たっている。** **ただし★もう1枚在る。**

## 2. ★6項目の実測（front door を叩いた。`【読】` で済ませていない）

### ① 案件を開く — **★出ている**
```
再現: GET /api/tasks
返り: {"tasks": [...]}   ★152件
先頭: "TASK-2DER-INT-001"
再現: GET /api/state?task_id=TASK-2DER-B9B4DA3B   → 1件が開く（下記）
```
**∴ 一覧も1件も front door から開ける。**
**★ただし返るのは★id の配列のみである**（題名・状態・日付を含まない）。**「一覧を見て選ぶ」には152個の id を目で追うことになる。**

### ② 現在地が分かる — **★出ている**
```
dw_state          = READY_FOR_AUDIT
last_completed_op = GENERATE
next_operation    = AUDIT
dispatch_status   = MACHINE-DISPATCHABLE
```

### ③ 通過した処理が分かる — **★出ていない**
```
再現: grep -c "etrace\|event_trace\|ETR-" twoder/webui.py   → ★0
再現: /api/state の返りキーに run/trace/etr を含むもの      → ★無し
```
> **∴ Event Trace は UI に★1文字も繋がっていない。**
> **★昨日まで「記録が無い」だったものが、今日「記録は在るが UI に出ない」に変わった。** **これが `G-46` の UI 側の姿である。**

### ④ 根拠と結果が読める — **★一部出ている**
```
egl.source_refs   = ["DE-0557"]           ← 根拠の id
egl.current_claims= [{"text": "sandbox内に、関数 answer(ri…"}]
rri.resolved_intent = {"request_type": "BUILD_CAPABILITY", "blockage": {...}}
work.next_information_need = ["sandbox 環境における…", …]
goal              = 依頼文そのもの
```
**★「根拠」は出ている**（`DE-0557` は `/api/resolve` で引ける）。
**★「結果」は工程の結果**（`last_completed_op=GENERATE`）**までで、★成果物そのもの（diff・test 結果）は `/api/state` に出ない**（`/api/claude_packet` には出る）。

### ⑤ 欠損・失敗・未確認が見える — **★ほぼ出ていない**
```
boundary_failures      → ★/api/state に無い（submit() は記録しているのに）
guard_block            → null
failure_memory_match   → null
block_source_refs      → null
ds_limitation          → ★出ている（唯一）
  {"dialogue_continuity": "UNRESOLVED HISTORICAL REFERENCE — 「前の件」はDSの対話履歴では思い出せない"}
```
> **★MGR の予想は「出ていない」だった。** **実測は★「1つだけ出ている」である。** **合わせずに書く。**
> **★`ds_limitation` は「分からなかったことを画面に出す」機構が★既に1つ在るという証拠である。** **形はもう在る。**
> **★一方 `boundary_failures`（`submit()` が全段で集めている失敗）は★UI に出ない。**

### ⑥ 次に誰が何をするか分かる — **★出ている**
```
next_operation = AUDIT / actor_role = QWEN_AUDITOR
claude_barrier = false / dispatch_status = MACHINE-DISPATCHABLE
```
**∴ 「次は誰が」「何を」「人間の承認が要るか」まで出ている。**

---

## 3. ★集計
| 項目 | 判定 |
|---|---|
| ① 案件を開く | **出ている**（★一覧は id のみ） |
| ② 現在地 | **出ている** |
| **③ 通過した処理** | **★出ていない**（Event Trace が UI に1文字も無い） |
| ④ 根拠と結果 | **一部**（根拠=出ている／成果物=別の口） |
| **⑤ 欠損・失敗・未確認** | **★ほぼ出ていない**（`ds_limitation` の1つだけ在る） |
| ⑥ 次に誰が何を | **出ている** |

> **★「作る」ではなく「足りない2つを足す」である。** **UI そのものは既に在る。**

## 4. ★足りないもの（一覧のみ。実装案は書かない — 禁止3）
1. **Event Trace が UI に繋がっていない**（③）
2. **`boundary_failures` が UI に出ない**（⑤）
3. **案件一覧が id の配列のみで、状態も題名も含まない**（①の質）
4. **成果物（diff・test 結果）が `/api/state` に出ない**（④。`/api/claude_packet` には在る）

**★どう繋ぐかは書かない。** **★どれを優先するかも書かない。** **裁定事項である。**

## 5. ★未確認（先に書く）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`/` と `/command` の画面を★ブラウザで見ていない。** HTML と API の返りから判断した | **CC-α / 画面の実物が要ると MGR が言えば** |
| 2 | **`/api/state` は1件（`TASK-2DER-B9B4DA3B`）でしか叩いていない。** 他の task で返りが違う可能性 | CC-α / 必要なら |
| 3 | **`/api/control`（`/` を作る口）の返りを叩いていない** | **★叩いていないと書く。** CC-α / 次に |
| 4 | **152件の task の中身を見ていない**（id のみ確認） | — |

---
*CC-α D-45（実測・何も作っていない）。★結論=**管理UI は既に在り、6項目のうち4つは既に出ている**。出ていないのは③「通過した処理」と⑤「欠損・失敗・未確認」の**2つだけ** ∴ Phase 2 は「UI を作る」ではなく「2項目を足す」で足りる可能性が高い（**実装案は書かない**）。★UI は2枚在る=`/`（`webui.py:430-447`「2DER — 開発状況 (read-only)」＝ロードマップ/完成予測/off-ramp フラグ/直近アクティビティ/承認待ち）と `/command`（`webui.py:613 PAGE`＝入力欄と `RUN NEXT` 等）——**MGR の見立て（`PAGE` が実体）は当たっているが、もう1枚在る**。★6項目の実測（front door を叩いた）=①**出ている**（`GET /api/tasks` が152件、`/api/state` で1件開く。**ただし返るのは id の配列のみで題名・状態・日付を含まない**）②**出ている**（`dw_state=READY_FOR_AUDIT`/`last_completed_op=GENERATE`/`next_operation=AUDIT`/`dispatch_status=MACHINE-DISPATCHABLE`）③**出ていない**（`grep -c "etrace|event_trace|ETR-" twoder/webui.py` = **0**、`/api/state` に run/trace 系キー無し ∴ **Event Trace は UI に1文字も繋がっておらず、昨日までの「記録が無い」が今日「記録は在るが UI に出ない」に変わった**＝`G-46` の UI 側の姿）④**一部**（`egl.source_refs=["DE-0557"]`・`current_claims`・`rri.resolved_intent`・`work.next_information_need`・`goal` は出るが、成果物そのもの（diff・test 結果）は `/api/state` に出ず `/api/claude_packet` に在る）⑤**ほぼ出ていない**（`boundary_failures` は `submit()` が集めているのに UI に無く、`guard_block`/`failure_memory_match`/`block_source_refs` は null。**ただし `ds_limitation` だけは出ている**——**MGR の予想は「出ていない」だったが実測は「1つだけ出ている」で、合わせずに書く。これは「分からなかったことを画面に出す」機構が既に1つ在る証拠である**）⑥**出ている**（`next_operation`/`actor_role=QWEN_AUDITOR`/`claude_barrier`/`dispatch_status`）。★足りないもの4件を一覧にするのみで実装案も優先順も書かない（Event Trace が UI に繋がっていない／`boundary_failures` が出ない／案件一覧が id の配列のみ／成果物が `/api/state` に出ない）。★未確認4件（`/` と `/command` をブラウザで見ていない／`/api/state` は1件でしか叩いていない／**`/api/control` を叩いていない**／152件の中身を見ていない）。*
