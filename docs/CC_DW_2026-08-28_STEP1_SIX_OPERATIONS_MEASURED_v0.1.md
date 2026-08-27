# DW 手1 — `domain_dw` 6 operation の実走結果 v0.1（★1行も直していない）

- 担当: DW（`DW_CLAUDE`） / 開発票: `ITEM-2DER-EVO-0137`
- 日付: 2026-08-28 07:4x〜08:0x
- 測ったHEAD: twoder `a90f56a` / dev-workcell `b003368` / egl `283d685`
- 形式: 実測表（分母つき）。★実装 0行 ／ 新台帳 0 ／ 新 state 0 ／ 新 ID 族 0
- 呼び方: すべて `manager_v0.to_domain(<op>)`（★本番と同じ入口。私が直接 module を叩いていない）

---

## 0. 結論（先に）

**6本とも返る。落ちたもの 0本。** ∴ 「DW が壊れている」は誤り。
**★但し 2本が『返るが 仕事をしていない』**（`submit_next_contract` 投函0 ／ `receive_finished` 受領0）。

★そして **brief §3-2 の前提（249件が Claude 判断待ち）は 実測で覆った**（§3）。

---

## 1. 6 operation（★分母 6 / 返る 6 / 落ちる 0）

| # | operation | 返る | 実測 | 何を返したか |
|---|---|---|---|---|
| 1 | `contract_with_precheck` | ✅ 0.01s | STOP路・GO路の両方 | STOP=`実装する名前が読めない(from impl import が無い)` ／ GO=骨格76B。★`precheck` 自身が逐語で「**計画が区間を名乗っていない(`serves_segment` が空)＝比べる相手が無い ∴ この検査は効いていない**」と自白する（`checked=0`） |
| 2 | `submit_next_contract` | ✅ 0.75s | pending **0** / already **88** / skipped **10** / held **1** / held_legacy **1** | **投函 0件**。skipped 10 は契約ブロックの形が壊れている物（`skeleton=2 tests=2 end=1` 等） |
| 3 | `receive_finished` | ✅ **387.38s** | looked **101** / received **0** / not_received **101**（★全件 `reason=empty`） | **受領 0件**。§2 に別掲 |
| 4 | `record_stages` | ✅ 2.94s | rows **191** / no_evidence **46** | PLACED **122** / CONNECTED **0** / OBSERVED **0** / USED **23** |
| 5 | `design_from_case` | ✅ 33.81s | steps 7件（`TASK-2DER-17240971`＝COMPLETE を選択） | roles **0** → `verify_material=CONDITION_NOT_MET(0,0)` / 出力4系統 names 0 / WorkUnit `completion=NO_COMPLETION_IN_DOCUMENT` / routing_lines 0 |
| 6 | `audit_case` | ✅ 27.85s | `TASK-2DER-D84215A8` | answer=**missed**（expected 9 / found 9 / missing 6）／ blind=true ／ FNR=**`no_denominator`** ／ 0017へ `INTV-0006` を記録 |

### ★1-1. 手5で **実施していない枝**（隠さない）
`design_from_case` は **COMPLETE 案件**で回した ∴ `/api/run_next` は `NONE` を返し、
**機械 dispatch の枝（GENERATE / AUDIT を実際に起こす経路）は 1回も通っていない。**
★理由=手1の指示が「1行も直さない・記録するだけ」であり、**在庫の TASK を私の判断で動かさない**ため。

---

## 2. ★`receive_finished` が 常時 頭詰まりを起こしている（★新発見・実測）

```
queue = 101件
1件あたり front door 2回        /api/state 3.38s ＋ /api/claude_packet 1.14s（実測）
∴ 1周 = 387.38s（実測）        ← ★manager_v0 の INTERVAL は 60秒
```

- **101件すべてが `reason=empty`**（成果物が 0バイト）＝ **受領できる物が 1件も無い。**
- かつ **queue から落ちない**：落とす条件は `(not _machine_turn(st)) and reason=="empty"` で、
  この101件は `READY_FOR_UPPER_REVIEW` 等＝`_machine_turn=True` ∴ **永久に残る。**
- ∴ **常駐は毎周 387秒を「必ず空で返る101件」に使っている。**
  `record_stages`(2.94s) → `receive_finished`(387s) → … の順なので、**後続の段が 1周60秒では回らない。**

★これは brief §5「触らない」に当たらない（`workcell.py` の状態機械ではない）が、
★**直すのは手3の配線より前か後か＝MGR の裁定事項**として上げる（§5）。

---

## 3. ★brief §3-2 の前提が 実測で覆った（★数と鍵つき）

brief:「**JUDGE_REQUIRED 139〜142 ＋ READY_FOR_UPPER_REVIEW 110 = 249件(36.7%)が Claude の判断を要する**」

**実測（DW 正本 `dev-workcell/dw/events.jsonl` を `W.derive_state` で全件畳んだ・700 TASK）:**

| state | 件数 | 次の operation | 次の actor | claude_barrier |
|---|---|---|---|---|
| JUDGE_REQUIRED | 142 | UPPER_REVIEW | CLAUDE_SENIOR | False（★barrier ではない） |
| READY_FOR_UPPER_REVIEW | 112 | — | — | — |
| └ うち **PROPOSE_COMPLETE**（upper_review 済 ＋ blockers 0） | **109** | **PROPOSE_COMPLETE** | **GATE** | **False** |
| └ うち CLAUDE_SENIOR が要る | **3** | UPPER_REVIEW | CLAUDE_SENIOR | False |
| COMPLETE | 103 | NONE | - | - |
| READY_FOR_AUDIT | 70 | AUDIT | INDEPENDENT_AUDITOR | False |
| READY_FOR_REGENERATE | 63 | REGENERATE | CODING_WORKER | False |
| DISPOSITION_REQUIRED | 60 | DISPOSE | MANAGER | True |
| READY_FOR_IMPLEMENTATION | 60 | GENERATE | CODING_WORKER | False |
| CREATED | 36 | PLAN | MANAGER | True |
| **PLANNING** | **50** | **★`_MAP` に行が無い → BLOCKED** | - | True |
| BLOCKED | 4 | BLOCKED | - | True |

**★front door でも同じ答えが返る（本番と同じ口で確認）:**
```
TASK-2DER-D84215A8  dw_state=READY_FOR_UPPER_REVIEW  next_operation=PROPOSE_COMPLETE  actor_role=GATE  blockers=[]
TASK-2DER-D256A411  同上
```

∴ **`READY_FOR_UPPER_REVIEW` 112件のうち 109件は Claude を待っていない。門が閉められる。**
∴ brief の「249件が Claude 判断待ち」は **鍵の取り違え**（state 名で数えており、`next_legal_operation` を引いていない）。

★**ただし『Claude 待ち』の正しい数は 私も断定しない**：`dispatch_once` は
`PLAN` / `DISPOSE` / `UPPER_REVIEW` に **機械 auto-serve の枝**（`RULE_TEMPLATE_PLAN` /
`QWEN_BUILD_PLANNER` / `MECHANICAL_DISPOSITION` / `TRIVIALLY_CLEAN_UPPER_REVIEW`）を持ち、
**どれが効くかは 実行時に登録された actors に依る** ∴ **state だけでは決まらない。**
∴ 手2 の `dw_summary` は **判定せず、`next_operation` と `actor_role` の数をそのまま出す。**

### ★3-1. `PLANNING` 50件は dispatch の表に行が無い
`workcell.STATES` は 13語だが `dispatch._MAP` は **9語しか持たない**。
`PLANNING` / `IMPLEMENTING` / `AUDIT_FAILED` / `REWORK` は **表に無い → `("BLOCKED","-","-",True)`**。
∴ **PLANNING 50 ＋ BLOCKED 4 = 54件(7.7%) が dispatch の対象外。**★これは「詰まり」の3つ目。

---

## 4. ★統括面の「前の数」（手2の受入で使う）

`/api/domains` の `cockpit` を **front door 経由で 1回**引いた（★所要 **約10分**）。

| Domain | 接続 |
|---|---|
| **dw** | **0 / 6**（★6欄すべて「状態を返す口が無い」） |
| esde | 4 / 6 |
| sysops | 3 / 6 |
| ledger | 1 / 6 |
| inference | 0 / 6 |
| structure | 0 / 6 |
| route_table | 0 / 6 |
| **合計** | **8 / 42** |

★**brief の「7 / 48（8 Domain × 6欄）」とは鍵が違う**：実行時の `DOMAIN_OPERATIONS` は
**7 Domain**（dw / esde / inference / ledger / route_table / structure / sysops）∴ 分母は **42**。
★私は brief の数を写さず、`/api/domains` から引き直した。

★併記: **`/api/domains` 自体が 約10分**かかる。★統括面が「見られない」原因はここにも在る（別件）。

---

## 5. ★上げる（MGR 裁定を仰ぐ・私は決めない）

1. **`receive_finished` の 387秒/周・受領0・queue が減らない**を、手3の配線より先に直すか。
   ★私の見立て=先。★但し「触らない」の線（状態機械）に触れずに直せるかは 設計判断。
2. **`PLANNING` 50件が `dispatch._MAP` に無い**件。★`_MAP` に行を足すのは **状態機械の変更に当たるか**。
3. **brief §3-2 の 249件**は 私の実測と食い違う ∴ **brief 側の数を訂正してよいか**（★私は brief を書き換えない）。

---

## 6. していないこと

- 実装 0行 ／ 契約本文 0 ／ 新台帳 0 ／ 新 state 0 ／ 新 ID 族 0
- TASK を1件も進めていない（`design_from_case` は COMPLETE 案件を選んだ・実測で state が動いていないことを確認）
- `dev-workcell/dw/workcell.py` を 1文字も触っていない
- brief の数を写していない（すべて引き直した）
