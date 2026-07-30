# 【D-131/132 の結果】2回目を投入した — **★planner に届き、Qwen が PLAN を作った。★PLAN で止めた**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-30 19:4x / TYPE=FINDING
- **運用方針 確認済（版: v2.8）**
- **受領**: `D-131`（文案 承認）／`D-132`（投入してよい・DS/入口は「示せない」に訂正）
- **2DER 優先原則**: ①(a) HTTP `POST /api/submit` ②承認文案を1回投入→`run_next` ③**★今回は「できなかったこと」なし** ④実装しない ⑤該当なし ／ **★`:8005`（GPU）を使った**

---

## 1. ★まず私の訂正（★消さない）

```
★私は作業中に「planner_outcome が null ∴ 規則テンプレートが PLAN を作った」と判断した。★誤りである。
★コードを読み直すと、planner_outcome は RULE_TEMPLATE 経路でも QWEN 成功経路でも★返り値に載らない
  （dev-workcell/dw/dispatch.py:100-117 の2つの return は、どちらも planner_outcome キーを持たない）
∴ ★null は「テンプレートが作った」の証拠にならない。★私は無いものを証拠に使った。
★正しい確定方法: ★計画そのものに書かれた出所を読む → plan_source = "QWEN_BUILD_PLANNER"
  （★規則テンプレートなら "RULE_TEMPLATE_2DER_EVO_0007" になる。plan_template.py:44 実読）
```

---

## 2. ★投入の記録

| | |
|---|---|
| 依頼文 | **文書から機械で抜いた**（167字 / sha1 `b11764b344f5d75864182188086eae0547980e5a` / 改行0）。**★1文字も変えていない** |
| 入口・回数 | **(a) HTTP `POST /api/submit`・★1回だけ**（19:31:13 → 19:31:24） |
| **★投入直後の `receipt`**（★他の口を叩く前） | `last_recv_at: 2026-07-30T19:31:13.080517` ／ `recv_count: 70` ／ `last_sent_status: 200` |
| 分類 | **`request_type: MODIFY_EXISTING`** ／ `acquisition_method: DW_IMPLEMENTATION` ／ `next_legal_operation: PLAN` ／ **`task_id: TASK-2DER-B11764B3`** ／ `runnable: true` |
| `run_next` | **★2回**。①19:32:03 `{"refused": true, …"task  is not the current runnable submit task"}`（★`task_id` を付けていなかった）②19:32:13→19:32:34 **`dispatched: true`** |
| 結果の状態 | `dw_state: READY_FOR_IMPLEMENTATION` ／ **`last_completed_op: PLAN`** ／ `next_operation: GENERATE` ／ `actor_role: QWEN_LIVECODER` |
| **★止めた** | **★`GENERATE` を叩いていない。★成果物を production に入れていない**（D-129 §3-3） |

### 2-1. ★予想の当否
| # | 予想 | 結果 |
|---|---|---|
| **E** | `BUILD_CAPABILITY` に分類される | **★外れた。★実際は `MODIFY_EXISTING`**（★分岐条件は満たしたが、★私が名指しした語ではない。**★「当たった」と書かない**） |
| **F** | **最も外れそう**＝`requires_current_state` で `OBSERVE` 側へ逸れる | **★逸れなかった**（★私が「外れる筋」と名指しした方が起きなかった） |
| G | E が通れば planner に届く | **★届いた** |
| H | 印5 は立たない見込み／`task_id` が出れば判定はできる | **★判定できた。★しかも立った**（§3） |

---

## 3. ★印1〜5 の材料（★判定は MGR）

| 印 | ★材料 |
|---|---|
| **印1【入口】** | **★示せる。** ①`receipt` の `last_recv_at 19:31:13.080517` が投入時刻と一致（★投入直後に他の口を叩く前に読んだ＝D-128 §3-2 が効いた）②**★さらに強い証拠**: `GET /api/resolve?id=ETR-fdf52322e5bf` が `component:"SUBMIT" function:"ENTRY" ts:2026-07-30T19:31:13.080700` と**★依頼文そのもの**を返す ③**★DS も示せる**: `GET /api/resolve?id=UTT-1010` が `speaker:"USER"` と `raw_text`＝依頼文を返す |
| **印2【生成】** | **★立つ材料。** `implementation_packet_ref` は**呼ぶ前に存在しなかった**。**`plan_source: "QWEN_BUILD_PLANNER"`**（★既存の口から読み出した値ではない） |
| **印3【非代行】** | **★立つ材料（★決定論の完全一致）。** 計画に在って**投入文に無い**もの: `steps` **7/7件**・`test_plan` **4/4件**・`completion_criteria` **4/4件**・`prohibited_actions` **5/5件**・`unresolved_assumptions` **2/2件**・`target_workspace`・`test_ids.py`。**★段取り・順序・対象を含む**（D-127 §2-2 の「立つ」側の条件） |
| **印4【非再演】** | **★立つ。** 私は**この目標の BUILD SPEC を書いていない**。**★計画の中身を1行も渡していない**（渡したのは目標と廃止条件のみ） |
| **印5【読める】** | **★立つ。★既存の口で実際に引いた**: `GET /api/claude_packet?task_id=TASK-2DER-B11764B3` → `implementation_packet_ref` に計画の全文（objective / scope / steps / test_plan / completion_criteria / prohibited_actions / unresolved_assumptions）。**★新しい口を作っていない** |

### 3-1. ★私は「1/8 になった」と書かない
**★判定は D-125 の手続きどおり、あなたが承認する。** **★私は材料を出した。**
**★1つだけ自分から弱める材料を出す**: **★`prohibited_actions` に「Modify existing repositories」が入っているのは、★サンドボックス保証が計画側にも現れたものであり、★Qwen の独創ではない可能性がある**（★テンプレート由来かは確かめていない。**★いつ誰が: あなたが必要と判断したら私が**）。

---

## 4. ★2DER が返した中身で、注意すべき点（★直さない・登記もしない・報告だけ）
```
★EGL は DE-0525 / DE-0526 を典拠に返し、★DE-0525 を「SUPERSEDED」と自分で区別した（★1回目の G-81 とは違う挙動）
★boundary_failures を2件 正直に返した:
   DS reconstruct_snapshot failed: HTTP Error 400 ／ 「前の件」は DS の履歴では解けない
★open_gaps を3件 返し、「DE-0526 の中身が無いので実装手順を特定できない」と★自分で書いた
```

---
**決めたこと**: **①2回目は planner に届き、Qwen が PLAN を作った（`plan_source: QWEN_BUILD_PLANNER`）。PLAN で止め、`GENERATE` は叩いていない ②印1〜5 の材料は5つとも出た（判定は MGR） ③私は作業中に `planner_outcome: null` を根拠にテンプレート説を採ったが誤りで、計画の `plan_source` を読んで訂正した。**
