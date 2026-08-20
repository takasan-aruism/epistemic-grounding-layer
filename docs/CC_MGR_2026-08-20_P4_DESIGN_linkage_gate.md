# 第四 ★設計のみ ―― 連動性検証を 2DER 自身の 強制門に する（最小）

**2026-08-20 17:3x ／ ★Taka 許可＝★設計まで。★実装は 別裁定 ∴ ★コード 0行・repo 変更 0**
**★対象は 1点だけ ―― ★IMPLEMENT 前後の 連動性検証を 2DER の 強制門に する こと。**

---

## 0. 先に ―― ★調べた 未確定値（★§7 に 従い 名指し）

```
★① declared を 置ける 既存点は 在るか
★② observed を ★task 単位で 引ける 既存面は 在るか   ← ★これが 無ければ ★DESIGN_HOLD だった
★③ 門を 掛ける 既存の 強制点は 在るか
★★この 3つ だけ 調べた。★他へ 広げて いない。
```

---

## 1. ★実測（★既存で 足りる ／ ★新規 0）

| 要る もの | 既存に 在るか | 実測の 根拠 |
|---|---|---|
| **declared の 置き場** | **在る** | `build_planner` の PLAN 受入検査（`:360` `:364` `:381` が `{"recorded": False, "stage": "validation", "reason": [...]}` で **既に fail-closed**）。宣言は PLAN の `implementation_packet`（既存 payload） |
| **IMPLEMENT 開始前の 門** | **在る** | ★同じ `validation`。★`recorded=False` なら ★PLAN が 記録されず ★`READY_FOR_IMPLEMENTATION` に ならない ＝ ★**GENERATE へ 進めない** |
| **COMPLETE 前の 門** | **在る** | `dw.workcell.completion_blockers()`（★関数 ／ ★state 表では ない）。★空でない 限り `PROPOSE_COMPLETE` に 到達しない（`dispatch.py:67-78`） |
| **observed（task 単位）** | **在る（★2段引き）** | `etrace.resolve_task(tid)` → `run_ids` → `etrace.resolve_run(rid)`。★実測（`229A3CD1`）＝ **147行 / 16辺**、★`HANDOFF.S01`〜`S10` が **実際に 出た** |
| **observed（辺の 集計）** | 在る | `observed_edges.handed_edges()`（★但し **全体で 畳む** ∴ ★task 単位には 使わない） |
| authority | 在る | `twoder.authority.TIERS`（`OBSERVE`/`REVERSIBLE`/`IRREVERSIBLE`）★新設 0 |
| rollback | 在る | `apply_cycle` の rollback ／ `git revert` |
| audit | 在る | `record_audit` / `completion_blockers` の `INDEPENDENT_AUDIT_MISSING` |

**★★∴ 新しい 台帳 0 ／ 新しい authority 0 ／ 新しい state 0 ／ 新しい Manager 機能 0 で 足ります。**

---

## 2. ★★見つかった 制約（★隠さない ―― ★設計を 縛る）

```
★★制約①（★逐語）= `etrace.resolve_task` の docstring
    「★task_id が 入るのは ★★DW だけ」
   ∴ ★task_id だけでは ★上流(S01〜S08)の 辺が 引けない。
   ★★但し ★`run_ids` が 併せて 返る ∴ ★2段引きで 届く（★実測 16辺）。
   ★★∴ ★門は ★『resolve_task → run_ids → resolve_run』の 2段を 使う（★新しい 口を 作らない）。

★★制約②= `handed_edges()` は ★全体で 畳む（★key=(from,to)）∴ ★task 単位の 判定に 使わない。
   ★使うと ★『誰かの 走行で 通った』を ★『この task で 通った』と 誤判定する（★私が 今日 /api/state で 踏んだ 型）。

★★制約③= `ROUTE_STAGE` を 引けない 段が ★実在する（★escalation ／ routing ／ contract_from_plan ／ diff ／ patch）。
   ∴ ★門は ★`ROUTE_STAGE=ABSENT` を ★★不合格に しない（★不合格に すると ★既存の 正常系が 全部 止まる）。
   ★代わりに ★`ABSENT` と 書いて ある ことを 要求する（★空欄を 許さない）。
```

---

## 3. ★設計（★最小 ―― ★2つの 門だけ）

### 門A ―― IMPLEMENT 開始前（★既存 `build_planner` の validation に 1条件 足す）

```
条件: PLAN の implementation_packet に ★`linkage` が 在り ★14の 鍵が すべて 埋まって いる こと。
      ★値は ★実値 ／ `ABSENT` ／ `UNVERIFIED` ／ `CONFLICT` の いずれか（★空文字・None は 不可）。
不合格の 出し方: ★既存と 同じ 形 = {"recorded": False, "stage": "validation",
                                   "reason": ["linkage: <欠けた鍵>"]}
結果: ★PLAN が 記録されない → ★READY_FOR_IMPLEMENTATION に ならない → ★GENERATE へ 進めない。
★★＝ ★新しい 停止点を 作らない（★既存の fail-closed を 使うだけ）。
```

### 門B ―― COMPLETE 前（★既存 `completion_blockers` に 1本 足す）

```
条件: ★declared（PLAN の `linkage.observed_expect`）に 書かれた 辺が
      ★observed（resolve_task → run_ids → resolve_run の handed_to）に ★すべて 在る こと。
不合格: ★blocker を 1本 立てる（★id 例 `LINKAGE_DECLARED_NOT_OBSERVED`）。
結果: ★`completion_blockers` が 空で ない → ★`PROPOSE_COMPLETE` に 到達しない。
★★＝ ★新しい state を 作らない（★blocker は 関数 ∴ 語を 1つ 足すだけ）。
★★＝ ★単体試験 PASS / artifact 生成 / LLM の 自己申告は ★条件に 入れない（★Taka 逐語）。
```

---

## 4. ★14項目 宣言（★この 門 自体に ついて）

| # | 項目 | 宣言 |
|---|---|---|
| 1 | UPSTREAM | 門A=`build_planner`（PLAN 受入検査）／ 門B=`dw.workcell.completion_blockers` |
| 2 | TRIGGER | 門A=PLAN を 記録しようと した とき ／ 門B=COMPLETE 可否を 引いた とき |
| 3 | INPUT | 門A=`plan.implementation_packet.linkage` ／ 門B=`task_id`＋PLAN の `linkage` |
| 4 | PRECONDITION | 門A=PLAN が 組めて いる ／ 門B=`resolve_task` が 引ける |
| 5 | OUTPUT | 門A=`{"recorded": False, "reason": ["linkage: …"]}` ／ 門B=blocker 1本 |
| 6 | DOWNSTREAM | 門A=`dispatch`（`READY_FOR_IMPLEMENTATION` に ならない）／ 門B=`dispatch:67-78`（`PROPOSE_COMPLETE` へ 行かない） |
| 7 | STOP | 門A=14鍵が 揃えば 通す ／ 門B=declared の 辺が すべて observed なら 通す |
| 8 | FAILURE_ROUTE | 引けない とき（`resolve_task` が None 等）= ★**通さない**（fail-closed）。★理由を 語で 出す |
| 9 | RECHECK/RETRY/ESCALATE | 門は ★毎回 その場で 判定（★状態を 持たない）∴ ★条件が 揃えば ★次の 周で 自動的に 通る。★詰まったら 既存 escalation（`377c85c`）へ 落ちる |
| 10 | PERSISTENCE | `linkage` は PLAN payload（★event log）／ observed は etrace ＝ ★どちらも file。★プロセス内記憶 0 |
| 11 | AUTHORITY | ★発行しない。★既存 `TIERS` を 使うだけ |
| 12 | EVIDENCE | 門A=`recorded=False` と `reason` ／ 門B=blocker id ＝ ★どちらも `/api/resolve` から 引ける |
| 13 | ROLLBACK | 条件を 外す＝`git revert`。★既存 task へ 遡って 効かせない（★下記 §5） |
| 14 | **ROUTE_STAGE** | 門A=**`S12`**（`dispatch → PLAN`）／ 門B=**`S18`**（`PROPOSE_COMPLETE → close`）★経路表から 引けた |

**★★14項目 すべて 埋まりました ∴ `DESIGN_HOLD` に なりません。**

---

## 5. ★後方互換（★これを 外すと 既存が 全部 止まる）

```
★`linkage` を 持たない ★既存 task は ★★今までどおり 通す。
   ―― ★理由 = ★実測 566 task の ★ほぼ 全部が `linkage` を 持たない。
   ―― ★門を 遡って 効かせると ★★2DER 全体が 止まる（★移管どころでは ない）。
★★∴ ★門は ★『`linkage` が 在る PLAN』に だけ 効く ＝ ★新規から 段階的に 効く。
★★『いつから 全 task に 必須に するか』は ★★Taka の 決め事 ∴ ★私は 決めない。
```

---

## 6. ★私が 決めて いない こと（★実装の 前に 要る 裁定）

```
★① ★実装を Claude が やるか ★2DER に 返すか（★Taka 逐語=★別裁定）。
★② ★`linkage` を ★いつから 全 task 必須に するか（★後方互換の 切り替え時期）。
★③ ★門B の 照合を ★『declared の 辺が すべて observed』と するか
     ★『1本でも 通れば よい』と するか（★厳しさの 度合い ―― ★私は 前者で 書いたが ★決めて いない）。
```

## 7. ★していないこと

```
★コード 0行 ／ repo 変更 0 ／ 実装 0 ／ 投入 0
★Manager 機能・RRI・経路表・監査全般・P1 の 修理へ ★1つも 広げて いない
★新しい 台帳 0 ／ 新しい authority 0 ／ 新しい state 0
★SELF_DEV_TOKEN = ★5/5
```
