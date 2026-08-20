# declared — AXIS = `CREATED_TASK_GATE_ADMISSION`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
**★これは実装の前に置く1枚**（ESDE 運転指示 §4⑤ ／ Taka 指示 2026-08-21 03:4x）。

前 AXIS `MANAGER_WORKLIST_ADMISSION` は **2026-08-21 03:25:44 に ESTABLISHED として閉じた**
（監査 `ETR-fee014c6993c`）。本 AXIS はその昇格した一存在を構成要素として使う。

---

## 0. 名称について

Taka 指示は「`CREATED_TASK_GATE_ADMISSION` あるいは既存正本に対応する名称」。
**既存正本に対応する名前は無い**ので前者を採る。探した範囲＝台帳 item の title 全件（front door
`/api/resolve`）と `egl/docs` の CC_* 文書名。最も近いのは `EVO-0071`（再武装経路）だが
**STATUS=DONE で閉じており**、その終結記録の逐語は「★認可の鍵が『現在の投入』→『task 自身の証拠』へ」。
**本 AXIS はその移行の“残り2材料”に当たる**（§3 の表）。

## 1. SCOPE

```
対象        work list に入った CREATED task が、RUNGATE で MISSING_GATE 以外の
            正規判定（allow または refuse+cause）に到達すること
entry       POST /api/run_next（RUNGATE。★2DER の実行口はこれ1つ）
exit        decide_rearm_v2 の verdict が MISSING_GATE 以外 ／ etrace 1行
            （RUNGATE receive → RUNGATE refuse|DISPATCH next_legal_operation）
authority   変更しない。AUTH.gate("DW_MACHINE_DISPATCH") はこの門より後段 ∴ 触らない
persistence twoder/runs/gates.json（既存・2026-08-15 から永続化）★新しい保存先 0
構成要素    webui._GATES/_gate_put/_gate_get ／ twoder/gate_decision.py ／
            twoder/decide_rearm_v2.py ／ dw.dispatch.next_legal_operation ／
            webui._machine_registry ／ twoder/task_findings.py
代表1件     TASK-2DER-D7977C1A
            ★私が選んだのではない。EVO-0081 の受入条件が逐語で名指ししている:
            「★受入は接続の存在ではなく D7977C1A が MISSING_GATE を抜けて PLAN へ進むこと」
範囲外      176件の一括修理 ／ COMPLETE まで進めること ／ 新しい gate 機構
```

## 2. 全件調査（作用起点・探した範囲を併記）

**探索範囲** = `ds rri egl dev-workcell twoder` の `*.py` 全件（`grep -rn`）。

| 問い | 実測 | 状態 |
|---|---|---|
| `MISSING_GATE` を返す物 | `twoder/decide_rearm_v2.py:26`（および旧 `decide_rearm.py:15`）の**2件のみ** | PRESENT |
| その本番呼び手 | `twoder/webui.py:1533`（`decide_rearm_v2`）**1件のみ**。旧 `decide_rearm` の本番呼び手は **0** | PRESENT |
| 門を**書く**物 | `webui._gate_put` **のみ**。呼び手4＝`:1452`(submit) `:1544`(REARM時) `:1597`(complete) `:1606`(dispatch後) | PRESENT |
| 門を**読む**物 | `webui._gate_get`（`:1515` `:1546`）＋ `_GATES.get(tid)`（`:1538`＝`gate_present` の材料） | PRESENT |
| 門の保存先 | `twoder/runs/gates.json`（`_GATES_FILE`）。上限 `_GATES_MAX=200`・超過分は**古い順に捨てる** | PRESENT |
| 門の在庫を**返す口** | front door の16口（`/api/` `/api/approve` `/api/claude_packet` `/api/control` `/api/etrace` `/api/ingest` `/api/ledgers` `/api/pending_approvals` `/api/receipt` `/api/resolve` `/api/roadmap` `/api/run_next` `/api/run_until_barrier` `/api/state` `/api/submit` `/api/tasks`）を全部見た。**門を返す口は0** | **ABSENT** |
| submit を通らない CREATE に門を付ける物 | **無い**（上の4呼び手は全て `webui.py` 内・全て HTTP 経由の投入か実行の後段） | **ABSENT** |

**★記録して保留（この AXIS では直さない）**: 「176件のうち何件が門を持つか」を出そうとして
`twoder/runs/gates.json` を直読しようとし、**境界フックに拒否された**（正しい作動）。
2DER に聞き直したが**門を返す口が無い** ∴ この数は **UNVERIFIED**。
「返せない」が結果であり、それが次に作る機能の候補（`GATE_INVENTORY_HAS_NO_READER`）。

## 3. 因果鎖（各点で 誰が作る／何を作る／どこに保存／誰が読む／無い時どう止まる／本線で呼ばれるか）

**① DW task の実体**
作る＝`/api/submit`（正規入口）**または** CONTROL_PLANE_BOOTSTRAP ／ 作る物＝DW event log の `CREATE` 行 ／
保存＝dev-workcell の event log ／ 読む＝`derive_state` `next_legal_operation` `tasks_to_enqueue` ／
無い時＝候補一覧に出ない ／ 本線＝`manager_v0` 段③ が `/api/tasks` で引く。
★代表1件の実測（front door `/api/resolve?id=TASK-2DER-D7977C1A`）:
`providers[0] = {phase:CREATE, role:MANAGER, identity:"MGR-control-plane-bootstrap", ts:2026-08-20T06:36:02}`
＝ **submit を通っていない**。`twoder/runs/TASK-2DER-D7977C1A.trace.json` も **不在**（探した範囲＝`twoder/runs/` の
`*.trace.json` 3608件）。

**② 門（gate）**
作る＝`_gate_put` のみ ／ 作る物＝`{task_id, blocked, runnable, reason}` ／ 保存＝`gates.json` ／
読む＝`_gate_get` と `_GATES.get(tid)` ／
**無い時どう止まるか（実測した停止の順）**:
`_gate_get` が `{task_id:None, runnable:False, reason:"この task の投入が記録に無い"}` を返す
→ `gate_decision` が `cause=NOT_RUNNABLE`
→ 再武装経路へ入る
→ `decide_rearm_v2(gate_present=False, ...)` → **`MISSING_GATE`**
→ `RUNGATE refuse`。
本線＝`/api/run_next` の冒頭（`webui.py:1515`）。

**③ 再武装判定（2DER 製・純関数）**
作る＝`twoder/decide_rearm_v2.py`（`TASK-2DER-2663D162` 由来）／ 判定は 2DER が持ち、足場は材料を渡すだけ ／
返りは `_d["rearm_evidence"]` として応答と `RUNGATE refuse` の etrace に載る ／
本線＝`webui.py:1523-1552`（`cause=="NOT_RUNNABLE"` の時だけ通る）。

**★材料6つの出所（EVO-0071 の終結記録「投入 → task 自身の証拠」への移行度）**

| # | 材料 | 現在の出所 | 由来 |
|---|---|---|---|
| 1 | `gate_present` | `_GATES.get(tid) is not None` | **★投入(submit)由来** |
| 2 | `gate_blocked` | `gate.get("blocked")`（同じ `_GATES`） | **★投入(submit)由来** |
| 3 | `next_operation` | `D.next_legal_operation(tid)` | task 自身の証拠 |
| 4 | `supplier_registered` | `actor_role in _machine_registry()` | task 自身の証拠 |
| 5 | `human_barrier_in_map` | `nlo["claude_barrier"]`（正本 `_MAP`） | task 自身の証拠 |
| 6 | `undisposed_findings` | `task_findings(tid)` | task 自身の証拠 |

**4/6 は既に移っている。残り 2/6（#1 #2）が投入由来のまま。#1 が MISSING_GATE の直接の材料。**

## 4. ESDE 宣言（実装前・§12 の全欄）

### EQUALITY（★identity rule 必須）
```
canonical形式  gate = {task_id, blocked, runnable, reason}（_gate_put が作り gates.json が持つ）
producer       webui._gate_put（4呼び手・すべて webui.py 内）
consumer       webui._gate_get → gate_decision ／ _GATES.get(tid) → decide_rearm_v2 の gate_present
★identity rule task_id の完全一致（gate_decision の TASK_MISMATCH がこの rule の実装）
compatible     DW の task identity と gate の identity は ★同じ task_id 空間に載っている
incompatible   ★gate 側の identity は「投入された task」の部分集合しか持てない
               ＝ DW に正規に存在する task でも gate 側には存在し得ない。
               両者を結ぶ規則（DW CREATE → gate 発行）が ★存在しない。
status         CONFLICT
```

### SYMMETRY
```
pairs          (a) submit → _gate_put            present
               (b) 非submit の DW CREATE → _gate_put   ★ABSENT
               (c) gate writer ↔ gate reader     present
               (d) gate 付与 ↔ gate 剥奪         付与=明示 / 剥奪=_GATES_MAX の FIFO のみ（明示の revoke 無し）
required 4 / present 2 / missing 1 / unverified 1
missing_ID     GATE_WRITER_FOR_NON_SUBMIT_CREATE
unverified_ID  GATE_REVOCATION_IS_ONLY_FIFO_EVICTION（★上限200は現在 172 で未拘束＝まだ発火していない）
```

### LINKAGE（declared する辺）
```
L1 admission → 選択          ★ESTABLISHED 済（前 AXIS・03:25:44 監査）
L2 選択 → RUNGATE receive    ★ESTABLISHED 済（ETR-NORUN-9955）
L3 RUNGATE → gate_decision   observed（cause=NOT_RUNNABLE）
L4 gate_decision → decide_rearm_v2  observed（ETR-NORUN-9960 cause=MISSING_GATE）
L5 DW CREATE → gate 発行     ★BROKEN（辺そのものが無い＝§4 SYMMETRY の missing と同一原因）
L6 decide_rearm_v2=REARM → _gate_put → allow   ★UNVERIFIED（本線で1度も発火していない）
declared 6 / observed 4 / broken 1 / unverified 1
```

### HIERARCHY
```
required 3  (1) 判定は 2DER 製の純関数が持つ・足場は材料を渡すだけ
            (2) authority は AUTH が持つ（門はその手前・authority を発行しない）
            (3) 門の保存は既存 runs/ の1ファイル（新台帳を作らない）
passed 3 / violation 0 / unreachable 0
★本 AXIS の変更後もこの3つを崩さないことを ★実装前に宣言する
```

## 5. 置く最小差分（★実装はまだしていない）

```
twoder/webui.py:1538  decide_rearm_v2 の第1引数だけ
  before:  _GATES.get(tid) is not None
  after :  bool(_events(tid))        # ← webui.py:141 に既にある既存の読み手
```

**なぜこれが「新しい gate 機構を作らない」に当たるか**
- 新しい判定を書かない（判定は 2DER 製 `decide_rearm_v2` のまま・1行も触らない）
- 新しい writer を作らない（門を発行するのは従来どおり `_gate_put` の `REARM` 分岐）
- 新しい保存先・新しい口・新しい語彙 0
- 変えるのは **足場が渡す材料の出所1つ**＝EVO-0071 終結記録の「投入 → task 自身の証拠」の残りを1つ進める

**安全弁が消えないこと**: `_events(tid)` が空＝DW に実在しない task_id は `gate_present=False` のまま
→ **MISSING_GATE で拒否され続ける**。守っていた本来の対象（存在しない task を走らせない）は残る。

**★正直に書く限界（この差分では満たせないもの）**
実装前に純関数で先に計算した（§5b）。代表 `D7977C1A` は差分適用後 **`HUMAN_BARRIER`** になる。
- **Taka がこの AXIS に置いた成功条件**（MISSING_GATE を脱し正規の allow/refuse+cause を得る）＝ **満たす**
- **EVO-0081 の受入条件**（PLAN へ進む）＝ **満たさない**。門の先の `HUMAN_BARRIER` は別の欠損。
**この2つを同じ語で報告しない。**

## 5b. R2 DENOMINATOR — 差分の影響範囲を実装前に確定（★純関数で先に計算）

`decide_rearm_v2` は純関数 ∴ **コードを変えずに「変えたらどうなるか」を全件計算できる**。
材料は `dw.dispatch.next_legal_operation` と `twoder/task_findings` から引いた（★`twoder/runs/` は読んでいない）。

```
分母 = DW の CREATED task 176件（★admission が work list へ入れた 176 と同値・独立に derive_state で再計算）
材料の組合せ = ★176件すべてが同一 (operation=PLAN, actor_role=MANAGER, claude_barrier=True, 未処分所見=0)
現状          verdict = MISSING_GATE   176 / 176
差分適用後    verdict = HUMAN_BARRIER  176 / 176
★REARM(門が開く) = 0 / 176
```

**∴ この差分で門が開く task は 1件も無い。** 監査の停止条件⑤（同一処理の暴走・無限反復）に
**当たらない**ことを実装前に数で示した。Taka 指示「176件を一括で直そうとしない」に対しては、
**差分の作用は 176件すべてで『拒否語が MISSING_GATE から HUMAN_BARRIER に変わる』だけ**で、
実走は代表1件しか行わないと宣言する。

**★同じ語で別の鍵（記録のみ・触らない）**
`GET /api/state` が返す `actor_role` は実体が `nlo["actor_id"]`（`webui.py:208` `:305`）で
代表は **`CLAUDE`**。一方 `decide_rearm_v2` に渡る材料は `nlo["actor_role"]` で **`MANAGER`**。
**同じ欄名で別の値**。私は最初この2つを取り違えて「supplier_registered=False で規則4」と書いた。
実際は `MANAGER ∈ _machine_registry()` ∴ `supplier_registered=True` で、効くのは
**規則5（`human_barrier_in_map=True`）**。判定語は同じだが**理由が違う**。

## 6. R4 — 拒否条件の全列挙（★実装後に1つずつ実際に発火させる）

`gate_decision` 4語 ＝ `BLOCKED` / `NOT_RUNNABLE` / `TASK_MISMATCH` / `OK`
`decide_rearm_v2` 7語 ＝ `MISSING_GATE` / `BLOCKED` / `HUMAN_BARRIER`(操作) / `HUMAN_BARRIER`(供給者) /
`HUMAN_BARRIER`(正本) / `UNDISPOSED_FINDING` / `REARM`
**合計 11。★前 AXIS で私は「門の拒否語は3つ」と書いて誤った（列挙が不完全だった）。今回は先に閉じる。**

## 7. DESIGN_HOLD の判定

**推測が残っている点＝0**。①代表 task の CREATE 主体、②門の有無、③門が無い時の停止順、
④`_machine_registry()` のキー、⑤`gate_present` の材料 ―― すべて実物から引いた。
∴ **DECISION = GO**（実装へ進む）。

## 8. 触らないと宣言するもの（Taka 指示 2026-08-21 逐語）

未commit 30件の一般整理 ／ 未push 全件処理 ／ `HUMAN_ESCALATION_LEDGER` ／ 台帳 mismatch ／ D188 / D190
／ `SENIOR_CALL_SKIPPED` ／ 周辺欠陥4件 ／ `_GATES_MAX` の FIFO ／ 176件の一括修理。
