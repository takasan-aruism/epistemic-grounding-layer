# 宛: Taka / 設計 / 監査 ―― G1/G2/G3 は本当に新規機能か（既存資産の調査・新規実装 0）

**G1 の実装を止めた。以下は調査のみ。**

## 1. 三問への回答（呼び手は機械で数えた）

### Q1「現在この案件は何を待っているか」―― **部分的にあり**

| 既存 | 呼び手 | 本線接続 |
|---|---|---|
| `rri/request_thread.raise_question` | **5**（★`submit.py` を含む） | **★あり**（投入時に問いが立つ） |
| `rri/request_thread.resolve_thread` | 2（`ids.py` / 自モジュール） | **△**（`ids.py` のみ） |
| `rri/intent_status_from_signals` | 1（`preflight_gate.py`） | 間接 |
| `dw` の `whose_turn`（2026-08-18） | 1（`manager_v0`） | **あり**（★TASK 層のみ） |
| 台帳の `note=next=` | ― | **散文**（未了27件中 ★欄なし14） |
| `roadmap_registry.is_blocked` | ― | **あり**（依存が全て DONE か） |

**実測**: task の state に `rthread_id` と `rthread_question_ids` が**必ず載っている**（今夜の全 task で確認）。
**∴ 「問いを立てる」は本線に在る。「誰待ちの語に畳む」ところが無い。**

### Q2「この案件を今進めてよいか」―― **既存機能あり・本線接続あり**

| 既存 | 呼び手 | 本線接続 |
|---|---|---|
| `rri/preflight_gate` | **8**（`route_table` `intent_strategy` `rri_formal` ほか） | **あり** |
| `rri/request_type.classify_request_type` | **4**（★`submit.py`） | **あり** |
| `webui` の門 ＋ `decide_rearm_v2`（2026-08-18） | ― | **あり**（今夜 実運転へ反映） |
| `authority.gate` / **`gate_for_item`** / **`item_ceiling`** | ― | **あり**（`webui` が `AUTH.gate` を呼ぶ） |

**∴ Q2 に不足なし。新規機能は要らない。**

### Q3「次にどこへ渡すか」―― **既存機能あり・本線接続あり**

| 既存 | 呼び手 | 本線接続 |
|---|---|---|
| `selected_acquisition_method`（front door の返り） | **2**（`webui.py` / `domain_dw.py`） | **★あり** |
| `rri/request_resolution.select_strategy` | 3（`rri_formal` / `run_rri_task`） | RRI 内部 |
| `to_domain` ＋ `DOMAIN_OPERATIONS`（2026-08-18） | 1（`manager_v0`） | **あり** |

**実測**: 今夜投げた**全依頼**で front door が `DW_IMPLEMENTATION` / `RUNTIME_INSPECTION` /
`OBSERVE_CURRENT_STATE` を返していた。**私は一晩それを使いながら「Q3 の機能は無い」と書きかけた。**

**∴ Q3 に不足なし。**

## 2. G1/G2/G3 の再判定

| | 判定 | 根拠 |
|---|---|---|
| **G1 `item_waiting_on`** | **★接続だけ必要** | 材料が**3か所に既に在る** ―― RRI の未解決問い（本線）／台帳 `next=`・`is_blocked`／TASK の `whose_turn`。**新しい判断は要らない。集約が無いだけ** |
| **G2 acceptance の機械照合** | **★GM に必要** | TASK 層は `completion_blockers` / `upper_review_gate.evidence` が在る。**ITEM 層の `acceptance` は散文のまま**で照合器が無い |
| **G3 上申8条件の機械判定** | **★不要（既存で足りる可能性が高い）** | `authority.gate_for_item(action_type, item_id, pre_authorized)` と `item_ceiling(item_id)` が**ITEM 単位で既に在る** ／ `command_surface.is_human_approver` / `may_approve` も在る。**「8条件」は Taka の運転規則であって、権限境界の機械判定は既に実装済み** |

## 3. GM の責務の再定義（Taka 提案を採る）

> **GM の責務は「既存判断の代替」ではなく、各 Domain・ITEM から情報を集約し Project 全体を管理すること。**

**今夜の調査はこれを支持する。**

```
Q1 待ち相手   RRI（問い）／ 台帳（next・依存）／ DW（手番）に ★分散して 在る
Q2 実行可否   RRI preflight ／ DW gate ／ authority に ★分散して 在る
Q3 渡し先     front door の acquisition ／ to_domain に ★在る
```

**∴ GM が作るべきは「判断器」ではなく「★集約面」。**
3問の答えは既にあり、**1か所から引けないだけ**。

## 4. 残る本当の不足 ―― **2件**

| # | 不足 | 種類 |
|---|---|---|
| **N1** | **ITEM 1件について、RRI の問い・台帳の `next`/依存・TASK の手番を1か所で返す集約** | **接続**（新判断 0） |
| **N2** | **ITEM の `acceptance` を機械照合できる形にする** | **新規**（GM に必要） |

**G1 → N1（接続のみ）／ G2 → N2（新規）／ G3 → 破棄（既存で足りる）。**
**残件 3件 → ★2件に減った。うち1件は接続だけ。**

## 5. 私の誤り（記録）

**G3 を「文書のみ・未実装」と書いた**（`CC_MGR_2026-08-19_GM_V1_SCOPE_LOCK.md` §2）。
実際は `authority.gate_for_item` / `item_ceiling` が**ITEM 単位で実装済み**。
**既存を引く前に「無い」と書いた** ―― 今夜13回目の同型。**`EVO-0076` の対象そのもの。**

## 6. していないこと

新規実装 0 ／ G1 の走行はこれ以上進めていない（`TASK-2DER-2303C0B1`）／
RRI・並列・経路表・機能表の高度化に入っていない。
