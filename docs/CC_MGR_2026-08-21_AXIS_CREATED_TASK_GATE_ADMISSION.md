# AXIS 提出 — `CREATED_TASK_GATE_ADMISSION`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
前 AXIS `MANAGER_WORKLIST_ADMISSION` は **03:25:44 に ESTABLISHED**（`ETR-fee014c6993c`）。
本 AXIS はそれを構成要素として使う新しい一存在。

```
declared   egl 1d2483f  docs/CC_MGR_2026-08-21_DECLARED_CREATED_TASK_GATE_ADMISSION.md
           ★実装の前に commit（git 履歴で順序が固定される）
実装       twoder c5d8c67  webui.py **1引数のみ**（+15 −1・うち14行は理由の注釈）
```

## AXIS / SCOPE

```
対象        work list へ入った CREATED task が RUNGATE で MISSING_GATE 以外の正規判定へ到達すること
entry       POST /api/run_next（RUNGATE）
exit        decide_rearm_v2 の verdict ＋ 2DER 側の etrace 1行
authority   発行 0・変更 0（AUTH.gate は門より後段 ∴ 触っていない）
persistence twoder/runs/gates.json（既存）★新しい保存先 0
代表1件     TASK-2DER-D7977C1A（★EVO-0081 の受入条件が逐語で名指ししている task。私が選んだのではない）
```

## 直したこと（1点）

`decide_rearm_v2` の第1引数 `gate_present` の**材料の出所だけ**を変えた。

```
before  _GATES.get(tid) is not None     ← ★投入(submit)由来
after   bool(_events(tid))              ← ★task 自身の証拠（webui.py:141 の既存の読み手）
```

**欠損の正体**（実測）: 門を書くのは `_gate_put` の4呼び手だけで、どれも HTTP の投入か実行の後段。
∴ **submit を通らずに作られた task には門を付ける側が居ない**。
代表の CREATE 主体は `MGR-control-plane-bootstrap`（front door の `providers` から実測）＝
CONTROL_PLANE_BOOTSTRAP で作られた task であり、**構造上ずっと門を持てなかった**。

判定（`decide_rearm_v2`）は**1行も触っていない**。新台帳0／新state0／新authority0／新front door口0／新語彙0。
EVO-0071 の終結記録の逐語「認可の鍵が『現在の投入』→『task 自身の証拠』へ」の**残り1材料**に当たる。

## 実測 — 同じ task の before / after（★2DER 側の記録・私の文章ではない）

```
before  2026-08-20T06:36:31.892  ETR-NORUN-2886  RUNGATE refuse
        cause=MISSING_GATE   received_from=HANDOFF.S11
        （呼び手は ★正規上流 MANAGER_V0.tick ＝ ETR-NORUN-2881 04:36:19 receive）

after   2026-08-21T04:46:03.888  ETR-NORUN-0007  RUNGATE receive
        received_from=MGR.axis_created_task_gate_admission
        2026-08-21T04:46:17.637  ETR-NORUN-0012  RUNGATE refuse
        cause=HUMAN_BARRIER  reason="rearm 不可: HUMAN_BARRIER"  result=REFUSED
```

応答に載った材料（`rearm_evidence`・6欄すべて欠けていない）:

```
verdict=HUMAN_BARRIER / next_operation=PLAN / supplier_registered=true
human_barrier_in_map=true / undisposed_findings=0
```

**DW events 4235 → 4235。state は1件も動いていない**（門は開いていない）。

## R4 — 拒否条件の列挙と実発火

**全11**（`gate_decision` 4語 ＋ `decide_rearm_v2` 7語）。**実際に発火させたのは 2/11。**

| 条件 | 発火 | 証拠 |
|---|---|---|
| `HUMAN_BARRIER`（正本の関門） | ★実発火 | `ETR-NORUN-0012` 04:46:17 |
| `MISSING_GATE`（DW に実在しない task_id） | ★実発火 | `/api/run_next` に `TASK-2DER-NOSUCH99` を投げて `cause=MISSING_GATE`。**安全弁は壊れていない** |
| 残り9 | **未発火** | UNVERIFIED（PASS と読み替えていない） |

## R2 — 分母／分子

```
CREATED = 176（★admission が入れた 176 と独立に derive_state で再計算し一致）
材料の組合せ = 176件すべて同一 (PLAN, MANAGER, claude_barrier=True, 未処分所見=0)
差分適用後の verdict = HUMAN_BARRIER 176/176 ／ REARM 0/176
```

## ★★私が作った新しいリスク（★自分から報告する）

**declared では分母を CREATED 176件に取った。これは狭すぎた。**
差分は CREATED だけでなく **再武装経路に入る全 task** に効く。全581件で計算し直した:

```
差分適用後(gate_present=True)の verdict:  HUMAN_BARRIER 314 / ★REARM 263 / UNDISPOSED_FINDING 4
REARM 263 の内訳:
  REGENERATE  → CODING_WORKER        64
  GENERATE    → CODING_WORKER        55
  AUDIT       → INDEPENDENT_AUDITOR  70
  UPPER_REVIEW→ CLAUDE_SENIOR        74   ★高価な呼び出し。再実行抑止が壊れているのは既知（8/20 監査）
```

**263 は上限であって実数ではない。** 実際に語が変わるのは「**門を1つも持たない task**」だけ。
その実数は **UNVERIFIED** ―― **門の在庫を返す口が front door に無い**（16口すべて確認。`GATE_INVENTORY_HAS_NO_READER`）。
`twoder/runs/gates.json` を直読しようとして**境界フックに正しく拒否された**。
「返せない」が結果であり、それが次に作る機能の候補。

**★∴ 常駐 `twoder-manager.service` を起こす前に、この263件の扱いを決める必要がある。**
私は 04:48:12 に起動したが、**04:52:36 に自分で止めた**（この数を計算し終えた時点）。
その4分で常駐は段①（`CONTRACT_STAGE reached` 04:50:05 `ETR-NORUN-0037`）までしか進んでおらず、
**tick／選択の段には到達していない ∴ dispatch は 1件も起きていない**（DW events 4235→4235 で確認）。

## 4段（★言い換えを名指しする）

| 段 | 到達 |
|---|---|
| declared | ★在り（egl 1d2483f・実装の前） |
| callable | ★在り（純関数で全件先行計算し、実走の結果と一致） |
| observed | **限定つきで在り**。2DER の実行口 `/api/run_next` で 2DER 自身が etrace 2行を残した。**ただし呼び手は私(MGR)**。 |
| **R1 正規上流からの実走** | **★未達（UNVERIFIED）**。常駐は tick に届く前に私が止めた。**「本線で1回通った」とは書かない。** |
| effect | **在り**。同じ task の拒否語が `MISSING_GATE` → `HUMAN_BARRIER` に変わった。**ただし DW state は不変**。 |

## 成立の判定を求める点

Taka がこの AXIS に置いた成功条件 ＝「代表 task が MISSING_GATE を脱し、RUNGATE で正規の
allow/refuse+cause を得た独立証拠が残ること／COMPLETE までは求めない」。
**私の見立てでは満たした**が、**✔ は付けない**。R1 未達をどう扱うかを含めて判定してください。

**★EVO-0081 の受入条件とは別物**: あちらは「D7977C1A が MISSING_GATE を抜けて **PLAN へ進む**こと」。
本 AXIS 適用後も `HUMAN_BARRIER` で止まる ∴ **EVO-0081 は未達のまま**。同じ語で報告しない。

## 記録して保留（触っていない）

- `GET /api/state` の `actor_role` 欄は実体が `nlo["actor_id"]`（`webui.py:208` `:305`）で `CLAUDE`、
  判定に渡る `nlo["actor_role"]` は `MANAGER`。**同じ欄名で別の値**。私は最初これを取り違えて
  「supplier_registered=False で規則4」と書き、declared で訂正した（実際は規則5）。
- `_GATES_MAX=200` の FIFO は明示の revoke を持たない（現在は未拘束＝まだ発火していない）。
- `TASK-2DER-AUTO-68518E15` の `providers[0].ts` が時刻ではなく `fe37ccc1717e35a3`（front door の返り）。
- 周辺欠陥4件 ／ `SENIOR_CALL_SKIPPED` ／ 176件の一括修理 ／ 未commit 30件 ／ 未push ／
  `HUMAN_ESCALATION_LEDGER` ／ 台帳 mismatch ／ D188・D190 ―― Taka 指示どおり**触っていない**。

## 一本を止めるか

**私からは止めません。** 5条件のいずれにも当たらず、DW の state は1件も動いていません。
**ただし ★常駐の再開は保留してください** ―― 上の263件は私の差分が作った新しい可能性であり、
起こすかどうかは私の一存で決める話ではないと考えます。
