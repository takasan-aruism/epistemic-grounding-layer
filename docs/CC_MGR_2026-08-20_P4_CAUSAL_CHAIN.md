# 第四 ―― ★起点から 終点までの ★一本の 因果鎖（★実測 ／ ★コード 0行）

**2026-08-20 19:2x ／ ★Taka 指摘「門の関数が正しいかは見たが、材料が本線で供給されるかと門まで到達するかを確認していなかった」**
**★これを 埋めるまで ★コードを 書かない。★1点でも 不明なら ★DESIGN_HOLD。**

---

## 1. 因果鎖（★各点 6問 ―― 誰が作る / 何を作る / どこに保存 / 次に誰が読む / 無い場合 / 本当に呼ばれるか）

| # | 点 | 誰が作る | 何を作る | どこに保存 | 次に誰が読む | 無い場合 | この経路で 呼ばれるか |
|---|---|---|---|---|---|---|---|
| 1 | USER REQUEST | 人 | `raw` | ― | `submit()` | ― | ★呼ばれる（実測） |
| 2 | RRI 分類 | `rri.request_type.classify_request_type`（LLM） | `request_type` 6語 | TRACE | `submit` の routing | `OTHER` へ倒す | ★呼ばれる（`submit.py:302`） |
| 3 | RRI 門 | `preflight_gate.detect` | `decision` 4語 | TRACE | routing | ― | ★呼ばれる（`:388`） |
| 4 | RRI 戦略 | `intent_strategy.resolve_consensus`（LLM） | 戦略 7語 | TRACE | `_HOLD` 判定 | ― | ★呼ばれる（`:470`）★**hold なら ここで return** |
| 5 | HANDOFF CONTRACT | **私（`handoff_contract.build`）** | 7欄＋`questions`＋`required_questions` | **TRACE** | Stage8 分岐 | `UNDETERMINED` | ★呼ばれる（`:549`）★**但し 4 の hold より 後** |
| 6 | CREATE | `submit`（BUILD/MODIFY 分岐） | `{project_id, goal, knowledge_packet, contract?}` | **event log** | `generate_via_runner` / `domain_dw` | ― | ★呼ばれる |
| 7 | **PLAN schema** | **`build_planner._plan_prompt`（Qwen へ の 指示）** | JSON の 鍵の 集合 | ― | `validate` | ― | ★呼ばれる |
| 8 | **PLAN validate** | `build_planner.validate` | `STRUCTURED_KEYS`＋`EXECUTABLE_KEYS` の 検査 | ― | `record_plan` | **`recorded=False` → Claude barrier** | ★呼ばれる |
| 9 | **PLAN recorded** | `build_planner:384` **または** `webui:674`（Claude ingest） | `{"implementation_packet": plan}` | **event log** | `webui:542`（GENERATE の 入力） | `READY_FOR_IMPLEMENTATION` に ならない | ★呼ばれる（実測 `9EDC4F8A`） |
| 10 | **linkage declared** | **★★誰も 作らない** | ― | ― | `completion_blockers` | **★`None` → 後方互換で 素通り** | **★★本線では 生まれない** |
| 11 | GENERATE | `webui` の `cw` → `generate_via_runner` | artifact ／ `test_result` | event log | AUDIT | ― | ★呼ばれる（`QWEN_LIVECODER`・実測） |
| 12 | observed edges | 各段の `_HO("Sxx")` ＋ `etrace.emit(handed_to=…)` | 辺 | **etrace file** | `_observed_edges_of` | 空集合 → fail-closed | ★出る（実測 15〜16本） |
| 13 | AUDIT | `QWEN_AUDITOR` | findings | event log | DISPOSE | blocker | ★呼ばれる |
| 14 | DISPOSE | CLAUDE actor | disposition | event log | UPPER_REVIEW | blocker | ★呼ばれる |
| 15 | UPPER_REVIEW | `CLAUDE_SENIOR` | verdict | event log | `derive_state` | blocker | ★呼ばれる |
| 16 | JUDGE_REQUIRED | `derive_state`（FAIL×2＋`may_retry=False`） | 終端 state | ― | ― | ― | ★到達した（実測） |
| 17 | **completion_blockers** | `dw.workcell.completion_blockers` | blocker 一覧 | ― | `dispatch:76` ／ `propose_complete:597` ／ `webui:196` | ― | **★`JUDGE_REQUIRED` は `:338` で 早期 return ＝ ★到達しない** |
| 18 | PROPOSE_COMPLETE | `dispatch:77` が 選び `webui:1592-1596` → `return_loop.complete_and_close` → **`propose_complete:597`** | COMPLETE event | event log | ― | `WorkflowViolation` | ★`READY_FOR_UPPER_REVIEW` かつ blocker 空の ときだけ |

---

## 2. ★★これで 何が 分かるか（★実装前に 分かって いたはずの こと）

```
★★① 10 が 空白 ―― ★`linkage` を ★作る 者が 本線に 居ない。
   ★PLAN を 書くのは ★Qwen（7）で、★その 鍵は ★`_plan_prompt` と `STRUCTURED_KEYS`/`EXECUTABLE_KEYS` が 決める。
   ★実測 = `STRUCTURED_KEYS`(objective/scope/target_workspace/target_repositories/…)
          `EXECUTABLE_KEYS`(requirement/target_file/test_file/test_body/test_command/allowed_files)
   ★★どちらにも `linkage` は ★無い。
   ★∴ 9 で 保存される packet に `linkage` は ★入らない。
   ★∴ 17 の 私の blocker は ★`_declared_linkage → None` ＝ ★後方互換で ★素通り。
★★② 17 へ 到達しない ―― ★`JUDGE_REQUIRED` は `:338` で 早期 return。
   ★∴ ★終端に 落ちた task では ★blocker が ★1本も 評価されない。
★★∴ ★★R1〜R3 の 門は ★本線で ★一度も 発火しない。
   ★これは ★『門が 壊れて いる』のでは なく ★『材料が 供給されず ／ 門まで 到達しない』。
★★私は これを ★実装前に 調べて いなかった。★調べる 対象を ★門の 内側に 限って いた。
```

## 3. ★★DESIGN_HOLD（★次の 実装へ 進まない）

```
★埋まらない 欄が ★1つ 在る ―― ★#10「誰が `linkage` を 作るか」。
★★候補は 2つ しか 無い（★実測 ―― `record_plan` の 本線 呼び手は この 2つだけ）:
   ★(あ) `build_planner`  … `_plan_prompt` に 鍵を 足し `STRUCTURED_KEYS` に 加える
                            → ★Qwen が 書く ／ ★validate が 欠落を 止める（★8 が 既に fail-closed）
   ★(い) `webui:674`      … Claude ingest 経路で 足す
                            → ★Claude が 書く ＝ ★★主体移管に 逆行する
★★どちらに するかは ★設計判断 ∴ ★私は 決めない。
★★また ★#17 へ 到達しない 問題（`JUDGE_REQUIRED` の 早期 return）は
   ★『門を どこに 置くか』の 話 ＝ ★これも 設計判断。
★★∴ ★★DESIGN_HOLD。★コードを 書かない。
```

## 4. ★私が 今回 学んだ 手順（★次から これを 先に やる）

```
★★『何が 在るか』では なく ★★『一周の 因果』を 先に 全部 書く。
★各点で ★誰が作る / 何を作る / どこに保存 / 次に誰が読む / 無い場合 / ★本当に この経路で 呼ばれるか。
★★1点でも 不明なら ★DESIGN_HOLD。★『門を 作れば 効く』と ★局所だけを 見ない。
```
