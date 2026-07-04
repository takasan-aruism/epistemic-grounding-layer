# EGL build-out G1 レポート — enforce 群の構造強制化

日付: 2026-07-05  対象: `/home/takasan/egl`  commit: `a736938`(裁定確定)+ `734bcf8`(G1 実装)

## 0. 一行結論
walking skeleton の差別化機構は「driver の正直さ」で通っていた(DE-0005)。今回それを**構造で強制**に組み替え、**DE-0009 の counter-factual/注入層テストで証明**した(Challenge Set C 13/13 PASS)。既存 run/run2/verify 無退行。

## 1. 背景(なぜ G1 が必要だったか)
Phase 1a walking skeleton は shape を貫通したが、独立敵対レビュー(DE-0005)が**差別化機構の中核 3つ(SC-2/GC-7/dedup)が構造未強制**であることを露呈した。著者(Claude Code)は過去ターンで「構造ブロック」と過大報告していた。REVIEW §5 は裁定として「**enforce を先・refactor を後**」に build-out 順を組み替えた。本 G1 はその enforce 先群。

## 2. 実装した enforce(as-coded)

| id | 重大度 | 従来(as-coded の欠陥) | G1 の修正 |
|---|---|---|---|
| **H1** | BLOCKER | `gate3_authority` が `SearchConclusion.status`(driver が渡す引数)をそのまま信用。leg の FAILED event を一切見ない → 偽の不在が作れた | `gate3` が **leg event(SearchRun)から COMPLETED leg の source_kind を再収集**し `evaluate_coverage` を再評価。`scon.status`/`coverage_result` は非参照。`mk_search_leg` が `(leg_plan_id, source_kind)` を event payload に記録(再導出の一次資料) |
| **H3** | HIGH | `decide(finding, gate2, importance)` が gate2/importance を本体で未使用(dead)。同 claim_key の矛盾 2 claim が両方 ACCEPT され得た | gate2 に既存衝突があれば **`CONFLICT_REVIEW_REQUIRED`**(claim を書かず decision のみ)。`importance=REQUIRED_FOR_RESOLUTION` は **PARTIAL では埋めさせない**(SUPPORTED 要求, M5) |
| **H4** | HIGH | `gc7_lint` が `run.py` の孤立 demo でしか呼ばれず curate 未接続。しかも self-report の `scope_echo` キーだけ見るので省略で素通り | **curate の gate 連鎖に接続**(候補が既存 Claim を根拠に引く場合に発火)。判定次元に**構造 scope キーも算入**し省略素通りを封鎖 |
| **M3** | MED | `gate1` が dangling nobs/source で `None` 添字 → crash | **clean-fail(DEFER)**。dangling を明示メッセージで返す |
| **AB-0003** | BUG(data-integrity) | `apply_outcome` が全受理 claim に `bootstrap:True` 一律付与 → benchmark B(自律化原料)を汚染 | **teacher_signal 由来で導出**。ABSENCE(adjudicator 無)は `bootstrap=False` |

新 outcome: `CONFLICT_REVIEW_REQUIRED`(H3)/ `GC7_BLOCKED`(H4)。

## 3. 証明 — Challenge Set C(`test_enforce.py`, DE-0009)
DE-0009 の2故障型を**独立に**張った:
- **(1) counter-factual gate test**: gate 出力を反転して outcome が変わることを要求 → 不変なら dead gate(H3/H4 検出)
- **(2) 注入層原則**: 試験入力を試験対象の境界より下(leg event)から注入 → `scon.status`(driver 引数)経由でないので wrong-source を検出(H1)

**13/13 PASS**。本命は **T1c**:
> `SearchConclusion.status="COMPLETED"` の**嘘を固定したまま** leg event だけ反転すると、outcome が `ACCEPT → ABSENCE_BLOCKED_SC2` に変わる。
> = 判定が driver 引数でなく **leg event に依存する一次証拠**。DE-0005 で過大報告した「構造ブロック」に、今回はテスト通過という裏付けがついた。

| test | 内容 |
|---|---|
| T1a/b/c | H1: leg 注入 + counter-factual(scon.status の嘘は不変) |
| T2a/b/c | H3: gate2 dedup/conflict(claim_key を変えれば ACCEPT に戻る=live) |
| T3a/b | H3/M5: importance バー(SUPPORTING なら同 finding で ACCEPT) |
| T4a/b | H4: GC-7 curate 接続(踏み込まなければ通過=live) |
| T5 | M3: dangling clean-fail |
| T6a/b | AB-0003: bootstrap stratify(positive=True / ABSENCE=False) |

無退行: `run.py`/`run2.py`/`verify_rebuild.py` 全 exit 0、**RC-3/RC-4 PASS**。

## 4. Provenance(この系の第一の禁忌への自己適用)
- 本 build-out の provenance は **ENGINEERING_FORCED / test-verified**。
- DE-0009 の counter-factual/注入試験を独立チェックとして通過 = **単なる driver 正直リプレイではない**。
- ただし **独立敵対レビュー(DE-0005 を捕えた別セッション agent 相当)はこの G1 に未実施**。よって `JUDGE_VERIFIED` は騙らない。**次の honesty gate = 独立レビュー**。

## 5. 未実装(次段 / §5.2〜)
- **独立敵対レビュー**を G1 に当てる(次の honesty gate)
- **H5/H6 = DE-0006**: counters.json 廃止・id-in-append・lock 同一 critical section
- **M4 = DE-0007**: `append_event` が partial-update を schema 完全性で構造 reject
- **L4 = DE-0008**: validation_mode 既定廃止 derive-or-UNRESOLVED + 過去 event に correction 追記
- **AB-0005**(TEST_INFRA): `test_enforce.py` が canonical SoR(`data/`)を上書き → 別 data dir 化
- その後 §5.3 refactor(mk_candidate / search.py / Axis / Adjudicator Protocol)

## 6. 台帳
- `DESIGN_EVIDENCE_LEDGER.jsonl`: **DE-0010**(G1 OPERATIONAL evidence)
- `audit_backlog.jsonl`: **AB-0005**(test isolation)
