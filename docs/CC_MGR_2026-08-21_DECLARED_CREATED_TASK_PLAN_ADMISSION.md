# declared — AXIS = `CREATED_TASK_PLAN_ADMISSION`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
**★これは実装の前に置く1枚。★コードはまだ1行も変えていない。**
**★ESDE 運転指示 §4⑤ に従い、実装の前に渡します** ―― 影響範囲が 210件あり、うち 176件が LLM 呼出になるため。

```
item        ITEM-2DER-EVO-0081 の1件のみ(1 AXIS = 1 item)
前 AXIS     CREATED_TASK_GATE_ADMISSION = 2026-08-21 06:12:34 ESTABLISHED(監査 ETR-425b05f96936)
            ★本 AXIS はそれを構成要素として使う(門を抜けた先の話)
測ったHEAD  twoder c5d8c67 / dev-workcell 68c3b4c / egl 1107dfd
```

---

## 1. SCOPE

```
対象        TASK-2DER-D7977C1A が HUMAN_BARRIER を抜けて PLAN へ進むこと
            (★EVO-0081 の受入条件の逐語:「D7977C1A が MISSING_GATE を抜けて PLAN へ進むこと」)
entry       POST /api/run_next(RUNGATE)→ decide_rearm_v2 → dw.dispatch.dispatch_once
exit        dispatch_once が PLAN を機械で処理し W.record_plan が走る
            = dw_state が CREATED → READY_FOR_IMPLEMENTATION に変わる
            (★または BUILD_PLANNER が fail-closed で barrier に落ちたという記録が残る)
authority   発行 0・変更 0。_MAP は正本 ∴ 1文字も変えない
persistence 既存 DW event log のみ。★新しい保存先 0
構成要素    twoder/decide_rearm_v2.py(判定・触らない) / webui.py の材料5〜6番目 /
            dw/dispatch.py:_MAP・dispatch_once / dw/plan_template.py / twoder/build_planner.py /
            dw/disposition.py / dw/upper_review_gate.py / webui._machine_registry
範囲外      COMPLETE まで進めること / worker のコード品質 / _MAP の書き換え /
            前 AXIS の REARM 263件(別 AXIS・保留のまま)
```

## 2. 全件調査（作用起点・探した範囲を併記）

**探索範囲** = `ds rri egl dev-workcell twoder` の `*.py` 全件（`grep -rn "claude_barrier"`）。

| 問い | 実測 | 状態 |
|---|---|---|
| `claude_barrier` を**作る**物 | `dw/dispatch.py:66` の `_MAP.get(state, ...)` **のみ**（例外は `:77` の `PROPOSE_COMPLETE` 1件） | PRESENT |
| `claude_barrier` を**読む**物 | `dispatch.py:163`（dispatch 自身の barrier）／ `webui.py:209`(表示) ／ **`webui.py:1555`（decide_rearm_v2 の材料5）** ／ `manager_v0.py:642`(whose_turn) | PRESENT |
| PLAN を**機械が**処理する経路 | `dispatch_once` に **2つ**。`plan_template.plannable`（決定論）と **`BUILD_PLANNER`（Qwen）** | PRESENT |
| その2つは barrier の**前**か | **前**。`dispatch.py:124-150` → `:163` が barrier | PRESENT |
| 失敗時 | **fail-closed**。無効な PLAN は「何も記録せず」barrier に落ちる（`:150` 逐語） | PRESENT |
| `BUILD_PLANNER` の登記 | `_machine_registry()` のキーに**在る**（実測: BUILD_PLANNER / CLAUDE_SENIOR / CODING_WORKER / INDEPENDENT_AUDITOR / MANAGER） | PRESENT |
| 供給元 Qwen | `:8005` HTTP=200 / model=`Qwen3.6-35B-A3B`（実測 2026-08-21 06:31） | PRESENT |

## 3. 因果鎖 ―― どこで止まっているか

```
① 門           _gate_get → gate_decision → cause=NOT_RUNNABLE
② 再武装判定   decide_rearm_v2(材料6つ)
                 規則5: human_barrier_in_map=True → ★HUMAN_BARRIER で refuse
③ dispatch     ★ここへ来ない(②で return する)
                 来ていれば: PLAN → plannable? → BUILD_PLANNER? → 駄目なら barrier
```

**★止まっている点は②。**`dispatch_once` が持つ「この task を機械が処理できるか」という**事実**は、
**一度も計算されない**。②が使うのは `_MAP` の**宣言**（state 単位・task 単位ではない）。

## 4. ESDE 宣言（実装前）

### EQUALITY（★identity rule 必須）
```
問い           「この task は人が手を動かさないと進まないか」
権威A(宣言)    _MAP.claude_barrier ―― ★state 単位。CREATED なら一律 True
               producer=dw/dispatch.py:66 / consumer=decide_rearm_v2 の材料5
権威B(事実)    dispatch_once の自動処理3枝 ＋ fail-closed barrier ―― ★task 単位
               producer=plan_template.plannable / build_planner / disposition / upper_review_gate
               consumer=dispatch_once 自身
★identity rule 両者とも task_id で引くが ★粒度が違う(state 単位 vs task 単位)
               ∴ 同じ task で ★A=True かつ B=処理できる が両立する
incompatible   ★Aを先に読むと B が永久に計算されない(順序が非対称)
status         CONFLICT
```

### SYMMETRY
```
pairs   (a) barrier を立てる ↔ barrier を降ろす
        (b) 機械が処理できるかを問う ↔ その答えを門へ返す
required 4 / present 2 / missing 2
missing_ID  ①MACHINE_CAPABILITY_HAS_NO_READER_AT_THE_GATE
              (dispatch は答えを持つが 門へ返す口が無い)
            ②NO_TASK_LEVEL_BARRIER_LOWERING
              (_MAP は state 単位で立てるだけ・task 単位で降ろす対が無い)
```

### LINKAGE（declared する辺）
```
L1 門 → decide_rearm_v2            observed（前 AXIS で ESTABLISHED）
L2 decide_rearm_v2 → dispatch_once ★BROKEN(規則5 で return する ∴ 辺が繋がらない)
L3 dispatch_once → plan_template   UNVERIFIED(本線で到達したことが無い)
L4 dispatch_once → BUILD_PLANNER   UNVERIFIED(同上)
L5 BUILD_PLANNER → W.record_plan   UNVERIFIED(同上)
declared 5 / observed 1 / broken 1 / unverified 3
```

### HIERARCHY
```
required 3  (1) 判定は 2DER 製の純関数が持つ・足場は材料を渡すだけ
            (2) _MAP は正本 ∴ 書き換えない
            (3) 機械が処理できるかの判断は dispatch が持つ(門が持ち直さない)
passed 3 / violation 0 / unreachable 0
★本 AXIS の変更後もこの3つを崩さないことを実装前に宣言する
```

## 5. 置こうとしている最小差分（★まだ置いていない）

前 AXIS と**同じ形**＝**足場が渡す材料の出所を1つ変える**。判定は触らない。

```
webui.py の decide_rearm_v2 第5引数
  before:  bool(_nlo0.get("claude_barrier"))                 ← _MAP の宣言(state 単位)
  after :  bool(_nlo0.get("claude_barrier")) and not <この op に登記された機械が在るか>
```

`<…>` は**新しい判断を書かない**。既存の物を引くだけ：
- `PLAN` → `plan_template.plannable(tid)` **または** `_machine_registry()` に `BUILD_PLANNER` が在る
- `DISPOSE` → `disposition.mechanically_dispositionable(...)`
- `UPPER_REVIEW` → `upper_review_gate.trivially_clean(tid)`

**★これは「barrier を無くす」ではない。** `dispatch_once` は依然 fail-closed で、機械が作れなければ
`dispatched=False / reason=CLAUDE_BARRIER` を返して止まる。**変えるのは「試す前に断るのをやめる」ことだけ。**

## 6. R2 DENOMINATOR ―― 影響範囲を実装前に確定（★read-only で全件計算）

```
分母 = DW に event を持つ task 581
  claude_barrier=False  371  … 規則5 は元から効かない=★この差分の影響を受けない
  claude_barrier=True   210  … 内訳 PLAN 176 / DISPOSE 31 / BLOCKED 3
                              ★UPPER_REVIEW は 0 件(=auto-PASS の危険は この AXIS には無い)

210 件を dispatch_once に通したら何が起きるか(既存述語を read-only で評価):
  ★BUILD_PLANNER(Qwen)が呼ばれる      176   ← 結果は予測不能・fail-closed
  ★MECHANICAL_DISPOSITION(決定論)      7    ← LLM 0回
  barrier に落ちる(無害・現状と同じ)     24
  op が NONE/BLOCKED(dispatch 即終了)   3
  RULE_TEMPLATE_PLAN                    0    ← plannable は 176件 全部 False
```

**★正直に書くリスク**: **176件が Qwen 呼出になる**（`build_planner` は 8192 tokens 必要＝過去実測）。
ただし **1周1件・3.4〜3.6分間隔の直列**であり burst ではない（前 AXIS で監査が使った判定基準と同じ）。
`:8005` は稼働中（HTTP=200 / `Qwen3.6-35B-A3B`）。

**★前 AXIS の REARM 263件とは別物**（あちらは `gate_present`、こちらは `human_barrier_in_map`）。
**足し合わせない。**前 AXIS の 263件は保留のまま、常駐は現在 inactive。

## 7. R4 — 拒否条件の全列挙（★実装後に発火させる）

`decide_rearm_v2` 7語 ＋ `gate_decision` 4語 ＝ **11**（前 AXIS で 3/11 発火済み）。
本 AXIS で新たに関わるのは **規則5(`HUMAN_BARRIER`／正本)** と、その先の
`dispatch_once` の停止語 **`CLAUDE_BARRIER` / `NO_MACHINE_ACTOR` / `NONE` / `BLOCKED`**（＝4語）。
**合計 15。★「門の拒否語は3つ」と書いて誤った前科があるので、先に閉じておく。**

## 8. DESIGN_HOLD の判定 ―― ★私は GO と書かない

**推測が残っている点が1つある**：

```
★UNVERIFIED  D7977C1A に対して BUILD_PLANNER が有効な PLAN を作れるか。
              確かめるには BUILD_PLANNER を実際に呼ぶしかないが、それは
              ★W.record_plan を書く副作用を持つ ∴ 門の外で叩けば
              「停止した 2DER を迂回して Claude が代行する」(正本 §11 の禁止9件の1つ)に当たる。
              ∴ ★門を通してからでないと測れない = 鶏と卵。
```

∴ **DECISION = 監査に問う**。私の見立ては「この UNVERIFIED は**実装前に解消できない種類**であり、
`dispatch_once` が fail-closed である以上、通して測るのが正しい」ですが、
**それを私一人で決めない**（210件・176 LLM 呼出の影響範囲があるため）。

## 9. 監査に判定してほしい3点

```
①この declared 自体が成立し得るか(§4⑤)
②§8 の UNVERIFIED を「通してから測る」で進めてよいか。それとも先に別の手が要るか
③§5 の材料に BUILD_PLANNER の「登記の有無」を使うのは妥当か
  ―― 登記されている＝作れる ではない(fail-closed で落ちる)。
  ★私は「試す資格が在るか」を材料にしたつもりだが、語が「機械が在るか」に見える。
  ★1つの語に2つの意味を持たせていないか、そちらの目で見てほしい。
```

## 10. 触っていないもの

前 AXIS の REARM 263件 ／ `_GATES_MAX` ／ `SENIOR_CALL_SKIPPED` ／ 周辺欠陥4件 ／
未commit 30件 ／ 未push ／ `HUMAN_ESCALATION_LEDGER` ／ 台帳 mismatch ／ D188・D190 ／
EVO-0082 の DISPOSE（私の別の手番・この AXIS の外）。

---

# 追記 v2 — 監査の GO 条件を満たし、HIERARCHY の選択を明記する

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
監査の返し = `2026-08-21T10:35:37 ETR-3c14f4b61438` **判定=declared は成立し得る(GO 可・条件1つ)**

## v2-1. 監査の GO 条件を満たした（★残っていた UNVERIFIED は消えた）

監査の指摘は正しかった。`build_plan(:216)` と `validate_plan(:282)` は
`make_dw_planner_actor(:351)` とは**別の関数**で、`W.record_plan(:384)` を通らない。
**代表1件で実測した（★実装は 0 行のまま）:**

```
build_plan("TASK-2DER-D7977C1A")   ok=True / stage=built / reasons=[] / 61.4s
                                   runtime_recovery: attempts=3 ladder 2048→4096→8192 RECOVERED
validate_plan(plan, task_id=...)   ★valid=True
  checks: schema_complete=true / provenance_ok=true / workspace_scope_ok=true
          tests_ok=true / completion_ok=true / no_unauthorised_destructive=true
  reasons: []
plan の中身(抜粋):
  objective    Fix false-positive CLOSED-NEGATIVE detection caused by substring matching
               without word boundaries.
  target_file  impl.py / test_file test_impl.py / test_command ['python3','-m','pytest','-q','test_impl.py']
  completion_criteria  "Requests with 'safety' or 'deliverable' are not blocked." ほか
```

**★依頼の本旨と一致している**（D7977C1A の goal は「`safety` の中の `afe`、`deliverable` の中の `live` が
偶然当たって CLOSED-NEGATIVE の復活と誤判定される」＝語の境界問題）。

**∴ §8 の UNVERIFIED は解消。門を通せば `make_dw_planner_actor` が同じ plan を
`W.record_plan` で記録し、`CREATED → READY_FOR_IMPLEMENTATION` に進む見込みが立った。**
（★「進む」と断定はしない。本線で通していない。）

## v2-2. ★訂正 ―― 「副作用0」は監査も私も外していた

**実測: `build_plan` を1回呼ぶごとに DW event が1件増える。**

```
1回目  DW events 4235 → 4236
2回目  DW events 4236 → 4237
増えた行  TASK-2DER-D7977C1A / PROCESS_EVENT / identity=2der-runtime-supervisor
          RUNTIME_SUPERVISOR outcome=RECOVERED attempts=3
          ladder=[2048,4096,8192] finish_reasons=[length,length,stop]
state     CREATED のまま(2回とも)
```

出所は `build_plan` が LIVE 経路で `RS.run_with_recovery(..., dw_record=True, egl_admit=True)`
を呼ぶこと（`build_planner.py:250-258` 逐語）。**設計どおりの記録**であって事故ではない。
∴ 正確には **「副作用0」ではなく「★state を動かさない PROCESS_EVENT を1件書く」**。
成果物（plan）は記録していないので、監査が示した線（代行実装＝記録に成果物を残すこと）には当たらない。
**★`egl_admit=True` の側の増分は UNVERIFIED** ―― EGL 台帳の直読は境界フックが拒否し（正しい作動）、
行数を返す口が無い。`GATE_INVENTORY_HAS_NO_READER` と同型の欠落。

## v2-3. ★監査が投げた HIERARCHY の選択 ―― **(ア) を採る**。理由は好みではなく実測

```
(ア) 足場が渡す材料を変える（webui.py の decide_rearm_v2 第5引数）
(イ) _MAP の CREATED 行の claude_barrier を False にする（1語・2026-08-07 の前例と同じ形）
```

**★(イ) は安全でない。実測で示す。**
`_MAP["CREATED"]` を False にすると、PLAN の2枝（`plannable` / `BUILD_PLANNER`）が
どちらも成立しなかった周で `dispatch.py:163` の barrier を**通過**し、
`fn = actors["MANAGER"]` ＝ `webui.py:608` の **`mgr` アダプタが PLAN の文脈で呼ばれる**。
`mgr` の中身は `W._latest_findings(view)` → `W.record_disposition(...)` **専用**（DISPOSE 用）で、
**PLAN の task に disposition を書く**。**新しい壊れ方を1つ作ることになる。**

**★(ア) は正本を骨抜きにしない。** `_MAP.claude_barrier` は `dispatch.py:163` で**依然として効く**。
(ア) が消すのは **門が持っている 2つ目の・より粗い写し**だけで、正本そのものの効力は
dispatch 側に残る。`BUILD_PLANNER` が作れなければ `:163` が `CLAUDE_BARRIER` で止める。
これは declared §4 HIERARCHY の required(3)「機械が処理できるかの判断は dispatch が持つ
（門が持ち直さない）」を**壊すのではなく回復する**。

**★2026-08-07 の前例との違い**: あのときは `CLAUDE_SENIOR` という**役が登記された**ので
`_MAP` の宣言そのものが古くなった＝1語で直すのが筋。今回は **`_MAP` の宣言は正しいまま**
（CREATED は原則 人の関門）で、**門が正本より早く・粗く適用しているのが問題**。∴ 直す場所が違う。

## v2-4. ★語の訂正（監査の問③）

監査の指摘どおり、§5 の `<この op に登記された機械が在るか>` は「**機械が在るか**」と読める。
意図は「**試す資格が在るか**」。以後この語で書く。実装の中身は変えない
（`supplier_registered` が「試す資格」、「作れるか」は `dispatch_once` が実際に試して fail-closed）。

## v2-5. DECISION

**GO**。残る推測 0。置く差分は §5 のまま（材料1つ・判定は触らない・`_MAP` は 1文字も変えない）。
実装後、代表1件を正規の実行口に通し、結果を同じ item（EVO-0081）で監査へ返す。
