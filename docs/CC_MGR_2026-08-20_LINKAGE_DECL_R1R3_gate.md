# 連動性 宣言（★実装 前）―― R1〜R3 を 2DER が 破れない IMPLEMENT 条件に する

**2026-08-20 19:0x ／ ★第四は 停止の まま ／ `9EDC4F8A` 再実走 なし**

## 1. ★再利用できる 既存部品（★実測 ―― ★新設 0）

| 要る もの | 既存 | 根拠 |
|---|---|---|
| COMPLETE を 止める 口 | `dw.workcell.completion_blockers`（★関数 ／ ★state 表では ない） | `workcell.py:322` ／ 門は `dispatch.py:67-78` |
| 宣言の 置き場 | `record_plan` の `{"implementation_packet": …}` | `workcell.py:431-434` |
| 観測の 引き口 | `ds.etrace.resolve_task` → `run_ids` → `resolve_run` の `handed_to` | ★実測 `229A3CD1` = 147行 / 16辺 |
| 層 | `dw` は ★既に `ds.etrace` を 引く（`workcell.py:87,96`）／ `dw` は ★既に `twoder` を 引く（`dispatch.py:23,62`） | ★新しい 層飛ばしを 作らない |
| 試験の 注入 | `completion_blockers(task_id, events=…)` ★既存の 引数 | `workcell.py:322` |

**★新 state 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 Manager 機能 0。**

## 2. ★機械条件（★R1〜R3 を 1つの blocker に 落とす）

```
★宣言（PLAN の `implementation_packet.linkage`）に 次を 求める:
   required_edges : ["FROM -> TO", …]   ★1本以上（★R2 の 分母）
★観測: ★この task の etrace から 実際に 出た 辺の 集合

★blocker を 立てる 条件:
   ★① required_edges が 空 / 無い            → `LINKAGE_NO_DENOMINATOR`   （★R2 ―― ★0/0 は 成功で ない）
   ★② 宣言した 辺の うち ★1本でも 観測に 無い → `LINKAGE_EDGE_NOT_OBSERVED`（★R1・R3）

★★R1 が 自動的に 効く 理由 = ★辺は ★実際の 経路の `handed_to` からしか 出ない
   ∴ ★単体試験・直接呼び出し・sandbox だけ では ★1本も 出ない ＝ ★必ず 止まる。
★★R3 が 自動的に 効く 理由 = ★段の 内側の 門も ★『辺』と して 宣言させる
   ∴ ★『段に 到達した』だけでは ★宣言した 内側の 辺が 観測に 出ず ★止まる。
★★『PLAN 生成 ≠ PLAN recorded』は ★既存の 状態機械が 既に 強制して いる
   （★本日 `9EDC4F8A` で 実測 ―― parse OK/schema OK でも `recorded=False` → `CLAUDE_BARRIER`）。
```

## 3. 14項目 宣言

| # | 項目 | 宣言 |
|---|---|---|
| 1 | UPSTREAM | `dw.workcell.completion_blockers`（★既存 ／ ★呼び手は `dispatch.py:76`） |
| 2 | TRIGGER | COMPLETE 可否を 引いた とき |
| 3 | INPUT | `task_id` ／ PLAN event の `implementation_packet.linkage.required_edges` ／ etrace の 観測辺 |
| 4 | PRECONDITION | PLAN event が 在る こと（★無ければ 既存の 状態機械が 手前で 止める） |
| 5 | OUTPUT | blocker 0〜1本（`LINKAGE_NO_DENOMINATOR` / `LINKAGE_EDGE_NOT_OBSERVED`）＋ ★分母つきの text |
| 6 | DOWNSTREAM | `dispatch.py:67-78`（★blocker が 空で ない 限り `PROPOSE_COMPLETE` へ 行かない） |
| 7 | STOP | 宣言した 辺が ★すべて 観測に 在る ときだけ blocker を 立てない |
| 8 | FAILURE_ROUTE | etrace が 引けない → ★blocker を 立てる（★fail-closed ／ ★通さない） |
| 9 | RECHECK/RETRY/ESCALATE | ★状態を 持たない ∴ ★毎回 数える。★詰まれば 既存 escalation（`377c85c`）へ 落ちる |
| 10 | PERSISTENCE | PLAN payload（event log）／ etrace（file）★どちらも プロセス内記憶 0 |
| 11 | AUTHORITY | ★発行しない |
| 12 | EVIDENCE | blocker の text に ★`observed/required` の 数と ★欠けた 辺の 名前を 入れる |
| 13 | ROLLBACK | `git revert`（★blocker 1本の 追加のみ） |
| 14 | **ROUTE_STAGE** | **`S18`**（`run_next → PROPOSE_COMPLETE→close`）★経路表から 引けた ／ ★『通過』で 宣言 |

**★14項目 埋まった ∴ `DESIGN_HOLD` に ならない。**

## 4. ★後方互換（★これを 外すと 既存が 全部 止まる）

```
★`linkage` を ★持たない PLAN は ★★今までどおり 通す（★blocker を 立てない）。
   ―― ★実測 568 task の ほぼ 全部が 持たない。★遡って 効かせると ★2DER 全体が 止まる。
★★∴ ★門は ★『linkage が 在る PLAN』に だけ 効く ＝ ★新規から 段階的に 効く。
★★いつから 全 task 必須に するかは ★Taka の 決め事 ∴ ★私は 決めない。
```

## 5. ★受入試験（★すべて 機械証拠 ―― ★単体試験だけでは 成立に しない）

```
①単体試験だけ・正規上流 実走なし → ★観測辺 0 ∴ blocker が 立つ
②宣言 3本・観測 1本               → ★blocker が 立つ（★1/3 を text に 出す）
③expected=0 / observed=0          → ★`LINKAGE_NO_DENOMINATOR`
④Stage 到達済み・内側 validator 未通過 → ★内側の 辺が 観測に 出ない ∴ blocker
⑤PLAN 生成成功・recorded=False    → ★本日 `9EDC4F8A` の front door 実測を 証拠に する
⑥全 required が observed          → ★blocker が 立たない
★★①〜④⑥は ★`completion_blockers(task_id, events=…)`（★既存の 注入引数）で
   ★★実物の 関数を ★実 etrace の 観測に 対して 走らせる（★hermetic ／ ★stub を 作らない）。
```
