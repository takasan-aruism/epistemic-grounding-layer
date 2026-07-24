# RRI 実装仕様 v0.1 — RTHREAD stage 1（保存則・総数のみ・口座なし）

- **起草:** CC-α 2026-07-24 / **正本入力:** `RRI_SPEC_MACHINE_v1_1.json`（CLAUDE_WEB）
- **★3 クローズ証跡（§3 precondition）:** commit `38d1988`（death#2/#4/#6/#7 closed・再走行 DIRECT 破断無し）。JSON の字面「E1→death#6→probe」は stale、実クローズは pkg_mirror(#6/#7)+配線(#4)+gate1b(#2)（`SYMBOL_RECONCILIATION.jsonl` 参照）。
- **矛盾規則:** 本仕様と JSON/実コードが食い違ったら halt して報告。本 v0.1 は各項に対応 JSON キーパスを引用する（トレーサビリティ）。
- **実装者:** 実装インスタンス（新フロー ANCHOR §1-1・working tree に `rri/rri/request_thread.py` を直接実装。Taka 裁定 2026-07-24：RRI も新フロー）。CC-α が書くのは本仕様・骨格・不変テスト・照合まで。※CLAUDE_WEB 指示 §2「実装＝Qwen submit」は §1-1 未反映だったため置換（`SYMBOL_RECONCILIATION` 系の矛盾解消）。

---

## §0. スコープ（stage 1 に厳密に絞る）

正本 `rollout.stages[0]`: **"conservation law inside one RTHREAD, totals only (no accounts)"**。

### 含む（v0.1）
| 対象 | JSON キーパス |
|---|---|
| RTHREAD event stream（1接触=1スレッド、sole writer） | `request_thread.unit` / `request_thread.sole_writer` |
| question 保存則（**総数のみ**） | `question_ledger.conservation_law` |
| 4 種 disposal（RESOLVED/OPEN_GAP/REJECTED/MERGED_INTO） | `question_ledger.disposal_types` |
| 状態機械 + 遷移 admission | `request_thread.state_machine` |
| projection（events → 状態/総数、byte-identical） | `request_thread.projection_fields` |
| OPEN_GAP delivery-duty（presented / THREAD_ACCEPTED exhaustive） | `question_ledger.open_gap_lifecycle` |

### 含まない（後段スライスへ明示除外）
- **口座（accounts）** と account 版 split/merge → `chart_of_accounts`（stage 2）。v0.1 では `account_id` は **`"UNCLASSIFIED"` 固定**（suspense のみ、口座計算なし）。
- **8 validators の RESOLVED guard 統合**（T34）→ 生成翼の restore は別スライス（`measured_baseline.wired_unentered_validators`）。v0.1 の RESOLVED guard に validator チェックは**入れない**。
- temperature/pipeline（`pipeline`）、semantic_index（layer 3）、divergence_ledger、THREAD_SPLIT/INVESTIGATION_HOP/LINK_CONFIRMED。

### ADJUDICATION_SENSITIVE（否認されると v0.1 が実質変わる裁定案）
- **#25**（RTHREAD = projection over events、fat record にしない）→ §1/§5 の設計そのもの。
- **#26**（RESOLVED = human acceptance with exhaustive residual enumeration）→ §4 の RESOLVED guard と THREAD_ACCEPTED。
- **#27**（OPEN_GAP delivery-duty・no cap・no timeout）→ §4 の AWAITING_HUMAN と RESOLVED 阻却。

---

## §1. モジュール構成

**新規 1 モジュール: `rri/rri/request_thread.py`**（sole writer。`request_thread.sole_writer`）

- event stream 置き場: **`rri/rri/rthread_events.jsonl`（追跡下）**。裁定21（rri_records の追跡化）達成済みを前提（Taka OK 2026-07-24）。`rri_records.jsonl` とは別ストリーム（sole writer 分離）。
- **first-class store は event stream のみ**（`architecture.first_class_stores`）。RTHREAD は **projection**（`architecture.rthread_status`）。fat record を作らない（#25）。
- 信頼フィールドは呼出側封印（G-1）。各 append 関数が `sealed_by` を registry から刻む。emitter 自己申告禁止。

### 公開関数署名（worker が実装。骨格は成果物3で固定）

```
open_thread(ds_thread_ref: str, ts: str) -> str
    # THREAD_OPENED を append。thread_id "RTHREAD-<8hex>" を mint して返す。sealed_by 刻む。

raise_question(thread_id: str, memo: str, ts: str, account_id: str = "UNCLASSIFIED") -> str
    # QUESTION_RAISED を append。question_id "Q-<8hex>" を mint して返す。id は rephrase を跨ぐ。

dispose_question(thread_id: str, question_id: str, disposal: str, ts: str,
                 reason_code: str | None = None, target_id: str | None = None) -> None
    # QUESTION_DISPOSED を append。disposal in {RESOLVED,OPEN_GAP,REJECTED,MERGED_INTO}。
    # REJECTED は reason_code 必須 / MERGED_INTO は target_id 必須。欠落は ValueError（fail-closed）。

present_gaps(thread_id: str, question_ids: list[str], ds_delivery_receipt: str, ts: str) -> None
    # GAP_PRESENTED を append（OPEN_GAP を DS 経由で人へ提示した受領）。

human_replied(thread_id: str, answer_refs: list[str], ts: str) -> None
    # HUMAN_REPLIED を append。DS 経由のみ（G-7）。

advance_state(thread_id: str, to_state: str, guard_evidence: dict, ts: str) -> None
    # STATE_ADVANCED を append。§4 の transitions に照合して admission。違法遷移は RThreadIllegalTransition。

accept_thread(thread_id: str, residual_gaps: list[dict], human_ref: str, ts: str) -> None
    # THREAD_ACCEPTED（人間の扉）。residual_gaps は全 OPEN_GAP を exhaustive に列挙
    # （各 {question_id, disposal in {DECLINED,TRANSFERRED}, target_id?}）。非網羅は RThreadResidualIncomplete。

project(thread_id: str) -> dict
    # events から projection を deterministic 再構成（§5）。直接書き禁止（DERIVED）。

check_conservation(projection: dict) -> None
    # raised == resolved+open_gap+rejected+merged を検査。不成立は RThreadConservationError（halt）。
```

例外階層（fail-closed・G-4 の UNRESOLVED とは別で、これは構造違反）:
`RThreadError` ← `RThreadIllegalTransition` / `RThreadConservationError` / `RThreadResidualIncomplete`。

---

## §2. Event schema（逐語・stage 1 分のみ）

`request_thread.event_types` から stage 1 に要る型。**sealed** は呼出側が registry から刻むフィールド（G-1）。

```json
{"type":"THREAD_OPENED",   "thread_id":"RTHREAD-<8hex>","ds_thread_ref":"","ts":"","sealed_by":""}
{"type":"QUESTION_RAISED", "thread_id":"","question_id":"Q-<8hex>","account_id":"UNCLASSIFIED","memo":"","ts":"","sealed_by":""}
{"type":"QUESTION_DISPOSED","thread_id":"","question_id":"","disposal":"RESOLVED|OPEN_GAP|REJECTED|MERGED_INTO","reason_code":null,"target_id":null,"ts":"","sealed_by":""}
{"type":"NARROWED",   "thread_id":"","before_count":0,"after_count":0,"basis":"","ts":""}
{"type":"EXPANDED",   "thread_id":"","expansion_trigger":{"reason":"","source_ref":""},"ts":""}
{"type":"GAP_PRESENTED","thread_id":"","question_ids":[],"ds_delivery_receipt":"","ts":""}
{"type":"HUMAN_REPLIED","thread_id":"","answer_refs":[],"ts":""}
{"type":"STATE_ADVANCED","thread_id":"","from":"","to":"","guard_evidence":{},"ts":"","sealed_by":""}
{"type":"THREAD_ACCEPTED","thread_id":"","residual_gaps":[{"question_id":"","disposal":"DECLINED|TRANSFERRED","target_id":null}],"human_ref":"","ts":""}
```

- `reason_code` は REJECTED のみ必須 / `target_id` は MERGED_INTO のみ必須（`question_ledger.disposal_types` + event_types 制約）。
- 新語彙禁止（G-6）: 上記 type / disposal 値以外を作らない。

---

## §3. 保存則（総数のみ・stage 1 の心臓）

`question_ledger.conservation_law`（**Taka 訂正 2026-07-24: 複式＝二次元**。旧「4種のみ」は記載欠陥で、初稿の第5項=suspense も次元取り違え）:

```
I1（処分次元）: raised_total == resolved + open_gap + rejected + merged + in_flight
                in_flight = 未処分の問いの数
I2（科目次元）: Σ_account balance(account) == raised_total
                全問いはちょうど1つの account_id を持つ（UNCLASSIFIED 含む）
```

- **I1・I2 とも毎 state transition で成立必須**。不成立は halt（fail-closed）。`advance_state` は append 前に `check_conservation(project(...))` で **I1/I2 両方**を通す。
- stage 1 は chart（複数 account の mining）を持たないが、**account 次元 I2 は stage 1 から持つ**（Taka の複式意図。初稿は I2 を潰していた）。
  - `raise_question` の account_id **default = `"DEFAULT"`**（RESOLVED 可）。`"UNCLASSIFIED"` は分類保留の特殊値。
  - `ADJUDICATION_SENSITIVE`: account_id の stage1 適用（default=DEFAULT / UNCLASSIFIED 特殊化）は CC-α の設計判断。Taka レビュー対象。
- **UNCLASSIFIED 出口規則**（分類できなかったものを実質解決と主張禁止）: UNCLASSIFIED の問いの処分は `OPEN_GAP`/`REJECTED`/`MERGED_INTO` のみ、**`RESOLVED` 不可**（`ADJUDICATION_SENSITIVE: 16` — v0.4 原文 OPEN_GAP のみからの小拡張）。
- **memo は保存則計算に使わない**（T24）。分業: 等式判定=machine、disposal/account 割当=上位（LLM/human）。
- projection に `in_flight_count`（I1 残余）＋ `per_account_balances{}`（I2）を持つ。`suspense_balance` は `per_account_balances["UNCLASSIFIED"]` の別名として残す（別次元なので両方要る）。

---

## §4. 状態機械 + 遷移 admission

`request_thread.state_machine`。states: `SOFT|NARROWING|AWAITING_HUMAN|RESOLVED|DISPATCHABLE|CLOSED`。

`advance_state(to, guard_evidence)` は **transitions テーブル**に (from=projection.status, to) の行が在り、その guards が guard_evidence で満たされる時のみ STATE_ADVANCED を append。無ければ `RThreadIllegalTransition`（T37）。

stage 1 で実装する guard（validator 系は除外）:
| from → to | guard（v0.1） |
|---|---|
| null → SOFT | thread_id minted（open_thread 済み） |
| SOFT → NARROWING | `classify_request_type` ok・`bind_context` ok（guard_evidence に ref） |
| NARROWING → NARROWING | candidate_space 減 **または** EXPANDED 記録あり（T1 の下地。総数版） |
| NARROWING → AWAITING_HUMAN | open_gaps 非空 **または** turn_count≥limit（FORCED・T8） |
| AWAITING_HUMAN → NARROWING | HUMAN_REPLIED あり（DS 経由） |
| NARROWING → RESOLVED | **全 question disposed・suspense==0 or 明示 OPEN_GAP・全 OPEN_GAP が presented 済み・THREAD_ACCEPTED（exhaustive）**（#26/#27） |
| RESOLVED → DISPATCHABLE | （後段）EGL consult + provenance。**v0.1 では手動 halt して「後段」と記録**（8 validators と同じく生成翼待ち） |
| * → CLOSED | human closes or superseded |

- **AWAITING_HUMAN に timeout 無し**（`state_machine.no_timeout`・#27）。auto-close/auto-nag 禁止。待機在庫は projection の派生ビューで見せる。
- RESOLVED は **unpresented OPEN_GAP が在る限り阻却**（T38）。declined question の再提起は `re_raised_after_decline` フラグ必須（T39）。

---

## §5. Projection（DERIVED・byte-identical）

`project(thread_id)` は event stream を先頭から畳んで再構成。**直接書き込み不可**（layer 2 = DERIVED、`architecture.layers[1]`）。

stage 1 の projection_fields（`request_thread.projection_fields` の部分集合）:
```
status, turn_count, open_gaps[], suspense_balance,
raised_total, resolved, open_gap, rejected, merged   # 保存則の内訳（総数）
```
- 同一 event 列から **何度畳んでも byte-identical**（T36）。非決定要素（時刻/乱数）を projection に入れない。

---

## §6. 不変テスト対応（発注側同梱・成果物3で実装）

各テストは「壊れたら赤くなる」を mutation check で一度示してから採用（G-T1）。

| テスト | 検査 | mutation（赤にする壊し方の例） |
|---|---|---|
| **T14** | 保存則が毎 transition で成立・不成立で halt | dispose を1件握り潰す → 等式崩れ → halt する？ |
| **T15** | disposal は4種・REJECTED は reason_code / MERGED は target_id 必須 | reason_code 無しで REJECTED → ValueError 出る？ |
| **T16** | merge が総数保存（旧 dispose MERGED_INTO + 新 raise） | merge で旧 id を消すだけ（新 raise せず）→ 総数減 → 赤？ |
| **T17** | split が総数保存（parent==sum children） | split で子の1件を落とす → 赤？ |
| **T18** | RESOLVED は suspense 0 or 明示 disposal | suspense>0 のまま RESOLVED 遷移 → reject される？ |
| **T25** | 1 contact event = 1 RTHREAD（会話ターンで増えない） | 同一 ds_thread の2ターン目で新 thread → 赤？ |
| **T36** | projection が events から byte-identical 再生成 | projection に wall_clock を混ぜる → 2回で不一致 → 赤？ |
| **T37** | 違法遷移は STATE_ADVANCED admission で reject | SOFT→RESOLVED を直接 → RThreadIllegalTransition？ |
| **T38** | unpresented OPEN_GAP があると RESOLVED 阻却 | present せず RESOLVED → reject？ |
| **T39** | declined 質問の再提起は re_raised_after_decline 必須 | フラグ無し再提起 → reject？ |
| **T40** | THREAD_ACCEPTED は全 residual gap を exhaustive 列挙 | 1件抜いて accept → RThreadResidualIncomplete？ |

- **G-T2**（trust field の machine 封印自体をテスト）: `sealed_by` が呼出側 registry 由来で、event 引数の自己申告でないことを検査。
- **G-T3 / T36**（DERIVED 再生成 byte-identical）。

---

## §7. claim ceiling

- v0.1 は **RTHREAD の帳簿（保存則＋状態＋projection）**まで。「依頼IDの容れ物」を machine で成立させる最小核。
- **含まない**: 8 validators の RESOLVED 統合（生成翼＝別スライス）／口座／temperature／pipeline／意味 index／divergence。RESOLVED→DISPATCHABLE は v0.1 では halt 記録（後段）。
- 実装は実装インスタンス（新フロー）。骨格＋不変テスト（T14-18/25/36-40）は成果物3で発注側（CC-α）が固定し、実装インスタンスには書かせない。
- rollout `termination_condition`（1件が SOFT→DISPATCHABLE を実走）は v0.1 の達成条件では**ない**（DISPATCHABLE は後段）。v0.1 の達成 = stage 1 保存則ラインが1スレッドで回り、T35 positive control（故意に1件落とすと保存則が赤）が通ること。
