# 実装 → 設計/監査: Build 8 — MIGRATION-3 第1号を front door へ投入した（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.1）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD8_SPEC_MIGRATION3_FIRST_SUBMIT.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD8_APPROVED.md`（写しで観測）/ `CC_OPERATING_POLICY.md` v1.1
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 0. ★1回しか見ていません（運用方針 §4-13）
**投入は1回だけです。1回の結果で「front door は我々の指示を扱える／扱えない」と断定しません。**

## 1. ★指定された起動方法は失敗しました【監査:IMPL】
実装源 §1-2 の指定:
```
cd /home/takasan && python3 twoder/submit.py "<指示文>"
```
**実行結果: 失敗（exit=1）。`submit()` に到達していません。**
```
ImportError: cannot import name 'eq' from 'operator'
(consider renaming '/home/takasan/twoder/operator.py' since it has the same name as the
 standard library module named 'operator' and prevents importing that standard library module)
```
**事実**: `python3 twoder/submit.py` はスクリプトのあるディレクトリ（`twoder/`）を `sys.path` の先頭に置くため、`twoder/operator.py` が標準ライブラリの `operator` を隠します。**import 時に落ちるため、台帳への書き込みは発生していません**（行数で確認: 1179 のまま）。

**本番コードは変更していません**（実装源 §4-5「変更が必要になったら止めて設計へ上げる」）。**`operator.py` の改名はしていません。**

### 1-1. 実際に使った起動方法
`twoder/submit.py` の docstring に記載されている形を使いました:
```
Usage:  python3 -m twoder.submit "<raw Taka input>"
```
```
cd /home/takasan && python3 -m twoder.submit "<指示文>"    → exit=0
```
**同じ `submit()` を通ります**（`-m` はスクリプトのディレクトリを `sys.path` に入れないため、`operator.py` の遮蔽が起きません）。
**投入は通算1回です**（失敗した方は `submit()` に到達していないため）。台帳の増加は **1行**（1179 → 1180）。

## 2. 投入した指示文（逐語・書き換えていません）
```
宛: 設計/監査(CC-α)
MIGRATION-PLAN-CHECK: twoder/webui.py:315 と twoder/build_planner.py:301 の record_plan について、
その書き込みの上流に依頼が存在するかをコードを読んで確認せよ。LLM は使わない。
出すもの: 各呼出の上流を辿った結果（file:line の連なり）と、依頼に相当する入力が在るか無いか。
判定・提案はしない。事実のみ。
```

## 3. ★予想と実際（実装源 §2）【監査:IMPL】
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| `RRI_REQUEST_TYPE.request_type` | `OBSERVE_CURRENT_STATE` | **`OBSERVE_CURRENT_STATE`** | **当たり** |
| `RRI_PREFLIGHT.triggered` | `False` | **`False`**（`decision: ALLOW`） | **当たり** |
| `DW_TASK_ID` | 返らない | **`null`** | **当たり** |
| `INTENT_STRATEGY.strategy` | `DIRECT` | **`DIRECT`**（`AUTO_CONFIRMED`） | **当たり** |

**4項目とも当たりました。外れた項目はありません。**

## 4. 返ってきた `TRACE`（実装源 §4-3 の指定項目・全部）
```
DS_INPUT_REF                : UTT-0750
RRI_REQUEST_TYPE            : OBSERVE_CURRENT_STATE / requires_current_state=true /
                              references_prior_work=false
RRI_PREFLIGHT               : gate=RRI-GATE-AMBIGUOUS-QUANT-001 / triggered=false / decision=ALLOW
INTENT_STRATEGY             : strategy=DIRECT / candidates=["DIRECT"] / status=AUTO_CONFIRMED /
                              facts_emitted=false / fact_trace=["SELF_CONTAINED_NO_FACTS"]
SELECTED_ACQUISITION_METHOD : RUNTIME_INSPECTION
DW_TASK_ID                  : null
ACTOR_ROLE                  : ACQUISITION
DISPATCH_RESULT             : RUNTIME_INSPECTION executed read-only + ingested 4 EGL observations
NEXT_LEGAL_OPERATION        : RUNTIME_INSPECTION executed -> observation ingested to EGL
                              (GPU task NOT auto-resumed; 2DER re-evaluates focus on next intent)
boundary_failures           : 2件
```
`TRACE` 全文は `scratchpad/b8.json` に保存しています。

## 5. ★食い違い（実装源 §3・書き換えず記録します）【監査:IMPL】
**指示文が求めたこと**: `webui.py:315` と `build_planner.py:301` の **コードを読んで**、`record_plan` の上流に依頼が在るかを報告する。

**2DER が実行したこと**: `SELECTED_ACQUISITION_METHOD = RUNTIME_INSPECTION` /
`DISPATCH_RESULT = "RUNTIME_INSPECTION executed read-only + ingested 4 EGL observations"`
＝ **実行時の状態を観測して EGL に4件取り込みました。**

**＝ 指示文が指定した対象（2つのソースコード位置の上流）に対する読み取りは行われていません。**
**私はこれを書き換えていません。強制的に task も作っていません**（`DW_TASK_ID` が `null` のまま）。**「食い違った」として記録し、設計/監査へ上げます。**

## 6. 記録された `origin`（受入④）【監査:IMPL】
```
utterance_id            : UTT-0750
origin                  : MACHINE_SUBMIT
ts_source               : DEFAULT
preceding_utterance_ref : UTT-0749
```
**`origin=MACHINE_SUBMIT` が記録されています。新しい除外規則は作っていません。**
**`ts_source=DEFAULT`**（CLI 入口は実時刻を渡していません）。

## 7. 本 SPEC の担当範囲（実装源 §5）
- **完了条件1（指示文が `submit()` を通った）**: 満たしました（`TRACE` が記録に残っています）。
- **完了条件2（返された routing に従った）**: **従いました**——`DW_TASK_ID` が返らなかったので task を作らず、`DISPATCH_RESULT` と違うことをせず、食い違いを §5 に記録しました。
- **完了条件3・4 は本 SPEC の範囲外**です。

## 8. 位置づけ（緩めません）
- **1件通っただけでは「移行した」と言いません。** 移行3条件のうち**条件1（直叩きが閉じている）と条件2（2DER が routing を決めている）は依然として未達**です。
- **本 BUILT が示せるのは「我々の指示が front door を通った」ことと「2DER が何と判定したか」だけです。**

## 9. commit
**していません**（MGR）。**本番コードは1行も変更していません。**

---
*IMPL BUILT（Build 8）。**実装源が指定した起動方法（`python3 twoder/submit.py`）は `twoder/operator.py` が標準ライブラリを隠すため import 時に失敗**（台帳書き込み無し・本番コードは変更せず）。docstring 記載の `python3 -m twoder.submit` で**1回だけ**投入。**予想4項目はすべて当たり**（OBSERVE_CURRENT_STATE / preflight 不発火 / DW_TASK_ID null / DIRECT）。**★食い違い: 指示は「コードを読んで報告」だが 2DER は RUNTIME_INSPECTION を実行して EGL に4件取り込んだ**——書き換えず記録した。`origin=MACHINE_SUBMIT` 記録済・`ts_source=DEFAULT`。1回しか見ていない。*
