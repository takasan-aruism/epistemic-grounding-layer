# 明細システム 現状対応表 v0.1 — TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1 §14 への回答

**作成: Claude Code（MGR）／ 2026-08-23**
**基準資料: `egl/docs/TAKA_2026-08-23_LEDGER_DETAIL_DESIGN_MEMO_v0.1.md`**

## 0. 調べ方（探した範囲を先に書く）

- **現物のみ**。記憶で書いていない。各項目に file:line か front door の実測を付けた。
- 探した範囲 = `twoder` / `rri` / `ds` / `egl` / `dev-workcell` の `*.py`、front door の口、
  `rri/rri/rthread_events.jsonl`（【直読】と明記して集計）、`egl/structure/LEDGER_REGISTRY.jsonl`。
- **別名 import を数え落とす罠に1回落ちた**。`grep "list_questions("` は
  `from ... import list_questions as _LQ` 経由の呼び手を拾わない。
  ∴ **import 文で数え直した**（下の⑭は数え直した後の値）。

---

## 1. 対応表（§14 の15項目）

| # | 項目 | 判定 | 実測 |
|---|---|---|---|
| 1 | 現在の明細schema | **部分的に存在** | `QUESTION_RAISED` の欄は6つ: `thread_id / question_id / account_id / memo / ts / sealed_by`。**974件**。原文位置・親request・関係の欄は**無い** |
| 2 | 明細生成処理 | **部分的に存在** | `submit.py:422-541`。分割は `segment_candidates.is_bullet` の1規則のみ（行頭 `- ` `・` `*` `1.`）。**625 thread 中546(87%)が明細1件のまま** |
| 3 | 原文保持方法 | **部分的に存在** | `submit.py:529` が `m[:200]` で**切って保存**。**974件中295件(30%)が200字で切断**。今日足した `QUESTION_TYPED` は `source_text` 全文＋`source_span` を持つ（33件のみ） |
| 4 | source/evidence保存機能 | **部分的に存在** | 仕組みは在るが**明細に繋がっていない**。`handoff_contract.investigation_report` が `evidence_refs`(OBS-…) を返し、`runtime_inspection.ingest_to_egl` が EGL へ入れるが、**RTHREAD の明細には1件も紐付いていない**（`rthread_events` に evidence 系の欄が0） |
| 5 | 勘定科目付与 | **既に存在（ただし機能していない）** | `account_gate.decide` / `decide_with_llm` / `approve_account`。実測: 明細974件中 **UNCLASSIFIED 758(78%)**、提案645件のうち **NOT_DECIDED 639(99.1%)**、**処分済0件** |
| 6 | embedding利用 | **既に存在（明細には未接続）** | `egl/structure/s_account_axes.py`（軸ごとの density=cosine、anisotropy 補正つき）、`s_rthread_2br3.py`。**科目軸の生成に使われており、明細への自動割当には繋がっていない** |
| 7 | annotation | **既に存在** | `QUESTION_ANNOTATED` **915件**（`phase / actor / done_when`）。ただし内容が壊れている: 段の最多が **`PROCESS_EVENT` 341件**（DW の phase であって段ではない）、同型の行に別の段が付く（ED65242E の #19/#20/#22=AUDIT に対し #21=GENERATE） |
| 8 | findingとの関係 | **存在しない** | finding は DW の `AUDIT` payload に在る。`rthread_events` に finding を指す欄は**0**。明細↔finding の辺は無い |
| 9 | task/item/artifact等との関連付け | **部分的に存在** | 方向が**片側だけ**。TRACE が `RTHREAD_ID` / `RTHREAD_QUESTION_IDS` を持つ（task→明細）。明細→task は今日の `QUESTION_TYPED.parent_request_id` のみ（33件）。ART-/ITEM-/ETR- への辺は**0** |
| 10 | 類似task検索 | **部分的に存在** | `submit.py:84 _best_resume_match`＝**漢字の重なり率**（threshold 0.3）。embedding は使っていない。対象は「active な task の goal」であって**明細ではない** |
| 11 | template/learning相当 | **部分的に存在** | `request_template.build`（次の依頼文の雛形）、`failure_memory.jsonl` 7行、`failure_recurrence.jsonl` 624行、`plan_template.plannable`。**いずれも task 単位で、明細から学んでいない**。task type 別の必要情報テンプレートは**存在しない** |
| 12 | UIから取得可能な情報 | **既に存在（2026-08-23 に追加）** | `GET /api/rthread?task_id=` が `thread_id / projection / questions / typed` を返す。画面は種別・原文・する・ゴールを表示。**それ以前は UI から明細を1件も引けなかった** |
| 13 | 明細を後から更新・追記する既存経路 | **既に存在** | `annotate_question` / `propose_account` / `dispose_question` / `record_typed`(今日) / front door `POST /api/rthread_add`(今日)。**append-only で id 単位に追える**。ただし `dispose_question` の実行は**0件** |
| 14 | 明細を読むconsumer | **部分的に存在（用途が3つだけ）** | `request_thread` を import する file は**12箇所／6用途**。①`ids.py` = ID解決 ②`account_candidates.py`＋`egl/structure/s_ledger_account_*.py` = 科目 ③`manager_v0.py:796` = 報告 ④`webui.py` = 表示 ⑤`submit.py` = 書き込み ⑥regression。**開発判断に使う読み手は0** |
| 15 | 明細情報がPLAN/RRI/回答へ再利用される経路 | **★存在しない** | `build_planner.py` / `dw/plan_template.py` / `live_worker_runtime.py` / `generate_via_runner.py` の**4本すべてで明細への参照が0件**。worker に届く面は骨格・封印試験・共通テンプレートの3つだけで、明細は**1バイトも渡らない** |

---

## 2. 最大の欠落 — 循環が閉じていない

§2 が想定する循環はこうである。

```
依頼 → 明細化 → 不足情報の発見 → 追加情報取得 → 明細の充足
     → 処理 → 結果・失敗・判断の追記 → 類似案件へ再利用
```

実測で存在する辺と、存在しない辺:

```
依頼 ──✅──> 明細化(974件)
明細化 ──❌──> 不足情報の発見        （明細に「足りない」を立てる欄が無い）
明細化 ──❌──> 処理                  （PLAN/worker への参照が 0件）
処理   ──❌──> 明細への追記          （finding/test/artifact を明細へ書く経路が無い）
明細   ──❌──> 類似案件へ再利用      （類似判定は task の goal どうしで、明細を見ていない）
明細   ──✅──> 科目（ただし78%が未分類）
明細   ──✅──> 表示（2026-08-23 に開通）
```

**明細は書かれているが、読み手が「ID解決・科目・表示」の3つしかなく、開発の判断に1件も使われていない。**
現状の明細は台帳ではなく **write-only のログ**である。

---

## 3. §5「原文は必ず保持する」への違反（実測）

- `submit.py:529` が `m[:200]` で**保存時に切っている**。§5 逐語「**保存データそのものを切断してはならない**」に反する。
- 実測 **974件中295件(30%)** が切断済み。既に失われた原文は**復元できる**（親 task の CREATE payload に原文が残っているため）が、明細側からは戻れない。
- 原文位置（`source_span`）・親request・明細順序は、今日足した `QUESTION_TYPED`(33件) にしか無い。

---

## 4. §7「勘定科目」への現状

- 機構は在る（`account_gate` + LLM 投票 + `approve_account` + embedding 軸生成）。
- しかし**結果が出ていない**: UNCLASSIFIED 78% / 提案の99.1%が NOT_DECIDED / 処分0件。
- **仮説（未検証）**: 事実・変更・仕様・試験・制約・ゴールを**同じ科目軸で分類させている**ため決まらない。
  今日 `kind` が付いたので、「科目を問うのは `CHANGE`/`SPEC` だけ」に絞る実験が ED65242E で可能。
- embedding は**科目軸の生成**に使われており、**明細への自動割当には接続されていない**（§7 が求める4機能のうち「新しい意味群の発見」だけが実装済み）。

---

## 5. §11/§12「類似task統合・必要情報テンプレート」への現状

- 類似判定は `_best_resume_match`＝**漢字の重なり率 0.3**。embedding も明細も使っていない。
- 「同型 task 100件で SPEC が97件必要だった」という**集計の母数が存在しない**。
  ただし今日の `kind` で母数を作れる: **ED65242E(SPEC 8/TEST 6) と EF6826DC(SPEC 0/TEST 0)** の
  対照が既に取れており、**SPEC 0 の依頼は worker が形を発明して2周失敗した**（台帳に記録あり）。
- ∴ §12 のテンプレートは、**`kind` の分布を task 横断で数えるところから始められる**。

---

## 6. §15 の問いへの、現時点での答え

> 散在している明細・科目・調査・証拠・関連ID・類似task・再利用機能を、
> どのように一つの Detail Lifecycle として接続すれば、本来想定していた台帳システムになるのか。

**新しい schema を作る前に、欠けている「辺」を3本つなぐのが先である**（欄を増やす話ではない）。

| 優先 | つなぐ辺 | 根拠（実測） | 新しい台帳/state/ID |
|---|---|---|---|
| 1 | **明細 → 処理**（PLAN/worker が明細を読む） | 下流4本で参照0件。worker に届く面が3つしか無く明細が入っていない | 0（既存の packet に載せるだけ） |
| 2 | **処理 → 明細**（finding / test結果 / artifact を明細へ追記） | 追記経路は既にある（`annotate_question` と同じ作法）。使われていないだけ | 0（`QUESTION_*` を1つ足す既存作法） |
| 3 | **明細 → 類似**（`kind` の分布で task type を数える） | 対照実験（ED65242E vs EF6826DC）が既に台帳に在る | 0（数えるだけ） |

**この3本が通るまで、局所的な欄追加は本実装へ入れない**（§15 逐語）。

---

## 7. 未確認（UNVERIFIED として残すもの）

- `egl/structure/s_rthread_2br3.py` / `s_account_axes.py` が**いま動いているか**は未確認（ソースに在る ≠ 動く）。実行の記録を front door から引けていない。
- `dispose_question` が0件なのは「使っていない」のか「使えない」のかを分けていない（UNCLASSIFIED の問いは `RESOLVED` 処分ができない出口規則が在るため、**構造的に詰んでいる可能性**がある）。
- 明細974件のうち、原文が復元可能な件数（親 task が現存する件数）を数えていない。
