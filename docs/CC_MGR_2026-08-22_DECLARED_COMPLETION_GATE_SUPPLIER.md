# declared — AXIS = `COMPLETION_GATE_HAS_NO_REGISTERED_SUPPLIER`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
**★実装の前に置く1枚。★コードは1行も変えていない。**
item: `ITEM-2DER-EVO-0086` の1件のみ ／ 測ったHEAD: twoder `065325e` / dev-workcell `68c3b4c` / egl `aa26caf`

**★昇格先（監査 01:01:58 逐語）**: 成立すれば **`CLAUDE_FREE_LOOP` の最後の構成要素**。

---

## ① AXIS 宣言

```
対象      2DER が自力で dw_state=COMPLETE に到達すること
入口      POST /api/run_next または /api/run_until_barrier
出口      dw_state=COMPLETE（return_loop.complete_and_close が走る）
authority 発行 0・変更 0。★AUTH も _machine_registry も触らない
保存先    既存 DW event log のみ。★新しい保存先 0
構成要素  webui.py(:1494 門検査 / :1596-1620 拒否 / :1637 完了分岐 / :1651 _gate_put) ／
          gate_decision.py ／ decide_rearm_v2.py ／ dw.dispatch.next_legal_operation ／
          _machine_registry ／ return_loop.complete_and_close
範囲外    門そのものの構造 ／ _place_and_commit ／ EVO-0085 の writer ／ 並行運用
```

## ② 全件調査 ―― 依頼先の制約 と 接続先の契約（板の規則）

**探索範囲** = `twoder dev-workcell ds rri egl` の `*.py` 全件。

### ★確定1: 材料4の**意図**（逐語）

`decide_rearm_v2.py:8` 逐語 ―― **「`supplier_registered`: その操作の供給者が登記されているか。真偽値。」**

### ★確定2: 「その操作の供給者」は **2箇所に分かれている**

| op | 供給者 | 所在 |
|---|---|---|
| GENERATE / REGENERATE | `cw` | `_machine_registry`（`webui.py:654`） |
| AUDIT | `au` | 同上 |
| DISPOSE | `mgr` ＋ `mechanically_dispositionable` | 同上 ＋ `dispatch.py:117` |
| PLAN | `plan_template` / `BUILD_PLANNER` | `dispatch.py:128-149` |
| UPPER_REVIEW | `claude_senior` ＋ `trivially_clean` | 同上 ＋ `dispatch.py:155` |
| **PROPOSE_COMPLETE** | **`return_loop.complete_and_close`** | **`webui.py:1637`** |

**足場が材料4に渡しているのは `_machine_registry` だけ**（`webui.py` の rearm 分岐）。
∴ **`webui.py:1637` の供給者を見落とす。**

### ★確定3: `PROPOSE_COMPLETE` は正本が「人の関門ではない」と言っている

`dispatch.py:77` 逐語 ―― `op, role, input_ref, claude_barrier = ("PROPOSE_COMPLETE", "GATE", "OBSERVED+PROPOSED_CLAIMS", False)`
∴ `claude_barrier=False`。**規則5は通る。詰まるのは規則4だけ。**
かつ この行に入る条件は `state == "READY_FOR_UPPER_REVIEW" and view.get("upper_reviews")` かつ **`blockers` が空**。
∴ **`PROPOSE_COMPLETE` が出ている時点で、完了条件は既に満たされている。**

### ★確定4: 門は呼び出し1回につき1度（前日の訂正を引き継ぐ）

`webui.py:1494` 逐語 `if u.path in ("/api/run_next", "/api/run_until_barrier"):`
∴ 両方の口が門を共有。`PROPOSE_COMPLETE` が呼び出しの先頭に来ると必ず拒否。
`complete_and_close` の呼び手は `webui.py:1637` の1つだけで、**門の後ろ**。

### ★確定5: R2 影響範囲（実装前に read-only で全件計算）

```
分母 = DW に event を持つ task 590
現状      HUMAN_BARRIER 315 / REARM 271 / UNDISPOSED_FINDING 4
材料修正後 HUMAN_BARRIER 294 / REARM 292 / UNDISPOSED_FINDING 4
★判定が変わる = 21件。★全部が (PROPOSE_COMPLETE, GATE, HUMAN_BARRIER → REARM)
★PROPOSE_COMPLETE 以外で変わる = ★0件
```

**21件が完了目前で止まっていた**（`next_legal_operation` が `PROPOSE_COMPLETE` を返す＝blockers 空）。

## ③ 因果鎖

```
① run_next/run_until_barrier   門を1度見る（:1494 → :1514）
② gate_decision                gate が無い/runnable でない → NOT_RUNNABLE
③ 再武装                        decide_rearm_v2 に材料6つを渡す
④ 規則4                        supplier_registered=False ← ★ここで止まる（欠損）
⑤ webui:1637                   PROPOSE_COMPLETE の完了分岐 ← ★到達しない
⑥ complete_and_close           ← ★到達しない
⑦ dw_state=COMPLETE            ← ★到達しない
```

**止まっている点は④の1つだけ。⑤〜⑦は実在し、`16D37B68` で1回通っている**
（★ただしそれは PLAN〜完了が同じ呼び出しに収まった1件。**本線の observed には数えない**）。

## ④ DESIGN_HOLD 判定

**推測が残る点 ＝ 0。**①〜⑤すべて source と実測から引いた。∴ **DECISION = GO**。

## ⑤ ESDE 宣言

```
EQUALITY   問い = 「この操作の供給者は居るか」
           権威A = _machine_registry（dispatch が呼ぶ actor の表）
           権威B = webui.py:1637（front door が自分で駆動する完了分岐）
           ★identity rule = op の文字列
           incompatible = 材料4は ★Aだけを見る ∴ B が在っても偽になる
           status = ★CONFLICT（同じ問いに答えを持つ場所が2つ・材料は片方だけ）
SYMMETRY   required 2 = (a)供給者を作る側 ↔ 登記する側  (b)完了を駆動する側 ↔ 門を開ける側
           present 0 / missing 2 = GATE_NOT_IN_MACHINE_REGISTRY /
                                   COMPLETION_DRIVER_BEHIND_ITS_OWN_GATE
LINKAGE    declared 7（①〜⑦）/ observed 3（①②③）/ broken 1（④）/ unverified 3（⑤⑥⑦）
HIERARCHY  required 3 (1)門を足場が上書きしない (2)authority を増やさない
                      (3)判定(decide_rearm_v2)は 2DER 製・足場は材料を渡すだけ
           passed 3 / violation 0
UNDERSTANDING  候補 = SELF_COMPLETING_TASK。★まだ ESTABLISHED にしない。
               要件 = ④が塞がり ⑦が正規上流から1回通ること。
CREATION   NOT_EVALUATED
DECISION   GO
```

## ⑥ 置く最小差分（★まだ置いていない）

**判断を書かない。既存の2つの事実を1つの表にまとめ、両方がそれを見る形にする。**

```
twoder/webui.py
  ★追加1（定数1つ）  _FRONT_DOOR_SERVED_OPS = ("PROPOSE_COMPLETE",)
                      # front door が自分で供する op。★:1637 の分岐と同じ事実に名前を付けただけ
  ★変更1（:1637）    if _nlo["operation"] == "PROPOSE_COMPLETE":
                      → if _nlo["operation"] in _FRONT_DOOR_SERVED_OPS:
  ★変更2（材料4）    str(_nlo0.get("actor_role")) in _reg0
                      → str(_nlo0.get("actor_role")) in _reg0
                         or str(_nlo0.get("operation")) in _FRONT_DOOR_SERVED_OPS
```

- **判定（`decide_rearm_v2`）は1行も触らない**
- **`_machine_registry` を触らない**（あれは dispatch が呼ぶ**実体の表**。GATE には実体が無い ∴ 足すと `fn(...)` を呼びに行く）
- **門（`gate_decision`）を触らない**
- **authority を触らない**
- 新語彙は**定数1つだけ**。★新しい判断ではなく、**`:1637` に既に在る事実へ名前を付け、重複した文字列を1箇所に寄せる**もの
  ＝ SYMMETRY の「供給者の表が2つ」を **1つに戻す**

## ⑦ R4 — 拒否条件の全列挙（★実装後に発火させる）

`gate_decision` 4 ＋ `decide_rearm_v2` 7 ＝ **11**。監査が 01:01:58 に **11/11 全件実発火済み**（純関数・副作用0）。
**実装後に私が実発火させるのは、経路として意味が変わる2つ**：

```
①PROPOSE_COMPLETE で REARM → 完了まで到達する（52892ED3）
②PROPOSE_COMPLETE 以外は 判定が変わらない（対照）
③実在しない task_id は MISSING_GATE のまま（安全弁）
```

## ⑧ 触っていないもの

EVO-0085 の writer 4欠損 ／ `merge_records`（UNVERIFIED・repo 未配置）／ 並行運用 EVO-0084 ／
`_place_and_commit` ／ `SENIOR_CALL_SKIPPED` ／ REARM 263 ／ `_GATES_MAX` ／ 未commit 30件。
