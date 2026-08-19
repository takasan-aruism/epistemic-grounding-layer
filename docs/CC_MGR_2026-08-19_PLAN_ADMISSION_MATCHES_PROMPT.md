# 宛: Taka ―― **`build_planner` の既存要求と `validate_plan` の受入を一致させた**（配線1点）

**2026-08-19 ／ commit `25070d0`（`[Claude実装]`・足場のみ・★判断ロジック 0行）**
**★新しい test 規則 0 ／ 新しい LLM 判定 0 ／ 契約 0 ／ skeleton 0 ／ test_body 0 ／ 実装 0 ／ run_next 0**

---

## 1. ★既存判定器を再利用できるか → **★できた（新規作成 0）**

**同じ決定論の検査が ★2箇所に 既に 在りました:**

```
★`domain_dw.precheck_names:145`（★2DER が 書いた 側の 呼び手）
    m = re.search(r"^from\s+impl\s+import\s+([A-Za-z_][A-Za-z0-9_]*)", test_body, re.M)
    if not m: → {"verdict":"STOP","line":"★実装する 名前が 読めない(★from impl import が 無い)"}

★`contract_from_plan`（★2DER が 契約経路で 書いた 純関数）
    「from impl import」の 行が 無ければ → reason = "no_function_name"
```

**★採ったのは `contract_from_plan` の方**（★理由 = ★狭いから）:

```
★`precheck_names` は ★経路表の `differs` でも ／ ★import 失敗でも STOP に なる
  ＝★★今回 許可されていない 範囲まで 落ちる。
★`contract_from_plan` の `no_function_name` は ★★狙った 1条件 そのもの。
```

## 2. ★入れた物 ―― `twoder/build_planner.py`（★`W.record_plan` の 直前）

```python
from twoder.contract_from_plan import contract_from_plan as _CFP
_c = _CFP(plan.get("requirement") or "", plan.get("target_file") or "",
          plan.get("test_plan"), plan.get("test_body") or "")
if _c.get("reason") == "no_function_name":
    return {"recorded": False, "stage": "validation", "plan": plan, "validation": val,
            "reason": ["tests: test_body must import the code under test "
                       "(from impl import <name>) — contract_from_plan: no_function_name"]}
```

```
★落とすのは ★`no_function_name` の ★1条件だけ。
★★広げていない（★Taka 逐語）:
   ・`unexpected_target` / `no_test_function` 等では ★落とさない
   ・`import impl` 形式を ★新たに 許可しない（★B の 87件は ★別件）
   ・mock 禁止・helper 禁止 へ ★広げない
★`recorded: False` は ★既存の 失敗形と 同じ ∴ dispatch は ★既存どおり Claude barrier へ fail-closed
   （★新しい 分岐 0 ／ 新しい 語 0 ／ 新台帳 0）
```

## 3. ★埋めた齟齬（★これが 目的）

```
★`build_planner.py:162` の プロンプト（★逐語・★既に 在った 要求）
   「Import the code under test with "from impl import <name>" — the module is always impl」
★`validate_plan` の 受入（★変更前）
   tests_ok = test_plan と test_body と test_file が ★空でない ことだけ
★★＝ ★要求は 出していたが ★出力を 突き合わせていなかった。
★★今回で ★要求 と 受入 が ★同じ条件を 見る ように なった。
```

## 4. ★受入 1〜5（★実データ・★Qwen 再呼出し 0）

| # | 受入 | 結果 |
|---|---|---|
| 1 | `7D461717` 型（`from impl import`）→ PLAN 採択 | **★成立**（reason=`None`） |
| 2 | `EAACCE21` 型（自己定義 mock・import 無し）→ **記録前に拒否** | **★成立**（reason=`no_function_name`） |
| 3 | 同じ入力で決定論 | **★成立**（3回引いて同一） |
| 4 | Qwen 再呼出し / Claude 補完なし | **★成立**（記録済み PLAN を 純関数に 通しただけ） |
| 5 | Claude DESIGN 0 | **★成立** |

## 5. ★★再測定 ―― **`goal → Qwen PLAN → validate → contract変換` は ★成立**

**`TASK-2DER-3CF23D43`（★goal だけ 投入・★Claude DESIGN 0）**

```
★記録の 並び = CREATE → PROCESS_EVENT → ★PLAN → GENERATE → AUDIT → DISPOSE
              → UPPER_REVIEW → REGENERATE → AUDIT → DISPOSE → UPPER_REVIEW
★PLAN identity = ★2der-qwen-build-planner
★target_file = impl.py ／ test_file = test_impl.py ／ test_body = 1694B
★test_body に `from impl import` = ★有り ／ contract_from_plan reason = ★None
★★∴ ★受入検査を 通り ／ ★契約変換が 成立した
```

**★★`SPEC_INCOMPLETE_NO_CONTRACT` は ★消えた（★配線が 効いた 証拠）:**

```
★配線前(EAACCE21) … reason = ★"SPEC_INCOMPLETE_NO_CONTRACT"（★契約が 無い）
★★配線後(3CF23D43) … reason = ★★"no provenance supplied (hand-authored packet / bypass)"
★★＝ ★契約は 渡った（★packet 経路に 入った）。★停止点が ★1つ 先へ 進んだ。
```

### ★次の停止点（★1つだけ・★直していません）

**`twoder/generate_via_runner.py:282`（★逐語のコメント付き）**

```python
provenance = None   # J1: 実在位置は CREATE payload.knowledge_packet.provenance(ledger 経路のみ)
if has_skel and has_tests:          # ★packet 経路（★今回 ここに 入った）
    ...                              # ★provenance は ★None の まま
else:                                # ★ledger 経路
    provenance = payload.get("knowledge_packet", {}).get("provenance")
```

```
★★＝ ★packet 経路には ★provenance を 詰める 行が ★無い（★逐語「ledger 経路のみ」）。
★★但し ★PLAN の 中には provenance が ★在る
   （鍵 = ds_input_id / ds_thread_id / dw_task_id / egl_open_gaps / egl_source_refs / rri_intent_id …）
★★∴ ★『存在しない』のでは なく ★『その経路が 読んでいない』。
★★`generate_via_runner` は ★変更禁止 ∴ ★手を 出していません。
```

### ★10項目の到達

| # | 測る物 | 結果 |
|---|---|---|
| 1 | PLAN identity = qwen | **★成立** |
| 2 | `validate_plan` 通過 | **★成立** |
| 3 | 受入検査（`from impl import`） | **★成立**（reason=None） |
| 4 | skeleton / immutable_tests が packet に入る | **★成立**（★理由コードの 変化が 証拠） |
| 5 | `SPEC_INCOMPLETE_NO_CONTRACT` 消滅 | **★成立** |
| 6 | `runner_exit` 非 null | ★未到達（null） |
| 7 | `runner_stdout_tail` | ★未到達（null） |
| 8 | diff / artifact が実体 | ★未到達（`artifact_sha256=""`） |
| 9 | test 実走 | ★未到達 |
| 10 | Claude DESIGN 介在 | **★0** |

## 6. ★併せて記録する事実（★私の観測の誤りを含む）

```
★投入は クライアント側が 180秒で 切れたが ★サーバ側では 成立していた。
   ★1回目の 確認では 0件に 見え ★『入っていない』と 報告する 寸前だった
   ＝★★「front door の 200 は 入ったではない」の 裏返し
     ＝★★「応答が 無い」も 入っていない ではない。
★入口の Traceback は `/api/roadmap` の `BrokenPipeError`（★クライアント切断）
   ＝★今回の 変更とは 無関係。
```
