# 2DER LLM Task 運行 仕様 v0.1（実態ベース）

2026-08-26 ／ instance=Inference Control ／ **GPT 版 v0.1 を差し替える**

---

## 0. GPT 版を捨てる理由（1行ずつ）

| GPT 版が「作れ」と言うもの | 2DER の現物 | 判定 |
|---|---|---|
| Task Contract | `handoff_contract.py`（`WORK_KIND` / `REQUIRED` / `QUESTIONS` マーカー） | **既に在る** |
| Worker Contract | `contract_seal.py`（`SKELETON` + `IMMUTABLE_TESTS` を封印） | **既に在る** |
| Acceptance Contract | 封印試験（`immutable_tests`）／`assemble_acceptance` ほか | **既に在る** |
| Ledger Write Contract | 封印 DETAIL・`complete_task`・`manager_v0._place_and_commit` | **既に在る** |
| Task 状態体系 8語 | `parallel_router.STATES` 14語 | **既に在る（別名を足すと道が2本になる）** |

∴ 4契約は **新規機構ではなく 既存機構の別名**。全体方針「一本の道にする」に逆行する。

**★ただし GPT 版が正しく指した点が1つある** ―― §8「**Worker が無い**」と「**Worker を起動する経路が無い**」を混同するな。本仕様はこれを **判定結果の語**として採用する。

---

## 1. この仕様の唯一の原則

### **Manager は LLM を呼ばない。**

理由は実測（LLMK-0001 / 0006）:

| 対象 | 実測 |
|---|---|
| `intent_strategy`（成立性の判定に相当） | 止まる確率 p = **0.80 / 0.50 / 0.40 / 0.20 / 0.10** ―― 0 にも 1 にも張り付かない |
| `request_type`（経路の判定） | **20%** が走行ごとに別の枝へ行く |

∴ **受付・成立性判定・配車を LLM にすると、入口が抽選になる。**
GPT 版 §5 の Manager 成立性判定（READY / INCOMPLETE / INVALID）は、実体が `intent_strategy` ＝ 抽選器である。
そこへ契約を足しても抽選は消えない。

**本仕様では、Manager の判定は全て「欄が在るか」「参照先が実在するか」の決定論とする。**
LLM は **測られる側 / 設計される側** であって、**運行する側ではない**。

---

## 2. Task の書き方（既存マーカーだけ・新語 0）

### 2.1 VERIFY（今使っている LLM が期待どおり動くか確認する）

```
<<<2DER:WORK_KIND>>>INVESTIGATE<<<2DER:END>>>
<<<2DER:REQUIRED>>>
instrument: s_llm_false_stop            ← 走らせる計器（実在する .py）
target: rri/rri/intent_strategy.py:_llm ← LLM_INVOCATIONS の caller と exact 一致
gate: stop                              ← 計器が受け取る門の名前
sample: front_door/task_index+state     ← 標本の出所（口の名前）
repeat: 3
prob: 10
record_to: ITEM-2DER-EVO-0107
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
false_stop_rate <= 0.02
stopped_every_run == stopped_at_least_once
<<<2DER:END>>>
```

`work_kind` は **既存の2語**（`IMPLEMENT` / `INVESTIGATE`）で足りる。VERIFY は `INVESTIGATE`、
納品は既存の `INVESTIGATION_REPORT`、正常終了は既存の `INVESTIGATION_RECORDED`。**語を1つも足さない。**

### 2.2 DESIGN（新機能が LLM を使うとき、使い方を設計して台帳へ返す）

```
<<<2DER:WORK_KIND>>>INVESTIGATE<<<2DER:END>>>
<<<2DER:REQUIRED>>>
caller: twoder/xxx.py:yyy       ← 呼び手（まだ無ければ PLANNED: と書く）
input: 何が入るか（1行）
output: 何を返させるか（1行）
closed_vocabulary: A|B|C        ← 出力語彙。無ければ NONE
downstream: どの分岐が変わるか   ← 無ければ NONE
record_to: ITEM-…
<<<2DER:END>>>
```

**Manager の成果物は設計文書ではなく `LLM_INVOCATIONS` に足りる行**とする
（`model` / `temperature` / `seed` / `max_tokens` / `timeout` / `system_prompt` / `schema_enforced` /
`prompt_source` / `answer_used` / `knowledge_refs`）。
新機能側が欲しいのは散文でなく **台帳の行**である。

---

## 3. 成立性判定（Manager の第一職責）— 全部 決定論

| 検査 | 方法（LLM 0回） | 結果 |
|---|---|---|
| 欄が全部在るか | `handoff_contract` の `REQUIRED` を読む | 欠け → **INCOMPLETE**（欠けた欄名をそのまま返す・**推測で埋めない**） |
| `target` が実在するか | `LLM_INVOCATIONS` の `caller` と exact 一致 | 無い → **INVALID** |
| `instrument` が実在するか | `egl/structure/<name>.py` の存在 | 無い → **WORKER_ROUTE_MISSING** |
| `acceptance` が式として読めるか | `immutable_tests` を決定論でパース | 読めない → **INCOMPLETE** |
| 全部 通る | | **READY** |

★**`WORKER_ROUTE_MISSING` と `INVALID` を混ぜない**。
前者は「作る対象が決まった」、後者は「依頼が壊れている」。意味が違う。

---

## 4. Worker

**VERIFY の Worker は 計器（決定論 Worker）である。** LLM Worker は起動しない。
LLM は **被験体**であって実行者ではない ―― ここが GPT 版と決定的に違う。

| work | Worker | 実体 |
|---|---|---|
| 誤停止・安定性の測定 | 決定論 Worker | `s_llm_false_stop.py`（`--gate` で門を差し替え・対照10本） |
| 呼出点の棚卸し | 決定論 Worker | `s_llm_invocations.py` |
| 分類・生成など**中身の仕事** | Qwen Worker / Claude Worker | `qwen_worker.py` / `senior_review.py`（`claude -p`） |

∴ **VERIFY モードは LLM Worker 無しで閉じる。** 「かなり大変」の大半はここで消える。
テスト計画を LLM に作らせる必要が無く、**計器を選ぶだけ**になるからである。

---

## 5. Acceptance

`immutable_tests` に書いた **数値式**で判定する（例 `false_stop_rate <= 0.02`）。
LLM の自己評価は使わない。計器の出力 JSON と式を突き合わせるだけ。

**★1回の走行を合否にしない。** 実測で、同じ標本・同じ経路の停止数が 2 → 4 → [3,1,1] と動いた。
∴ `repeat` を必須欄とし、acceptance は **反復後の集計値**に対して書く。

---

## 6. 記帳（Ledger Write）

計器の `--record ITEM-…` が **既存の封印 DETAIL 口**へ投函する（実装済み・`actor=2DER`）。
Manager も Worker も **台帳ファイルを直接編集しない**。

**★記帳できなければ COMPLETE にしない。** 既存の `complete_task` は門を通すので、そこへ乗せる。

---

## 7. 第一実証（今日の材料で そのまま通る1本）

| 欄 | 値 |
|---|---|
| instrument | `s_llm_false_stop` |
| target | `rri/rri/intent_strategy.py:_llm` |
| gate | `stop` |
| sample | front door（`task_index` + `state` の全文） |
| repeat / prob | 3 / 10 |
| acceptance | `false_stop_rate <= 0.02` |
| record_to | `ITEM-2DER-EVO-0107` |

**この1本は既に手で通っている**（測定・記帳とも）。足りないのは
**「Task を登録したら Manager が上の欄を読んで計器を起動する」1段だけ**である。

---

## 8. 正直に「大変」な所

1. **計器が無い VERIFY は通らない。** → `WORKER_ROUTE_MISSING` で止まり、**作る対象が名指しされる**。
   これは失敗ではなく、次に作る物が決まったということ。
2. **DESIGN の「不明」は不明のまま台帳へ入る。** `UNRESOLVED` / `UNVERIFIED` を既存語で書く。推測で埋めない。
3. **標本の口が無い対象は測れない。** 現状 front door から全文で取れるのは依頼文だけ。
   packet を要する呼出点（`judge_vllm` など）は **標本の口から作る必要がある**。

---

## 9. 保存則（この仕様に固有のものだけ）

1. **Manager は LLM を呼ばない**（受付・判定・配車は決定論）。
2. **VERIFY で LLM Worker を起動しない**（LLM は被験体）。
3. **acceptance は反復後の集計値に書く**（1走行を合否にしない）。
4. **新しい状態語・台帳・入口を作らない**（既存の 14 状態・封印マーカー・front door だけを使う）。
5. **`WORKER_ROUTE_MISSING` と `INVALID` を混ぜない**。
6. **不足欄は推測で埋めない**（欠けた欄名をそのまま返す）。
