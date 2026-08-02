# 【処置案 ＋ 実測】`TASK-2DER-A64D0C6D` — **★3件とも REJECTED。★原因は監査に依頼文が渡っていないこと**

- **宛: MGR** / 写: IMPL / Taka / 発: 設計/監査(CC-α) / 2026-08-02 07:0x / TYPE=処置案
- **開発者規律 確認済（版: v1.3）** ／ **★走行 0・★task 増 0・★commit 0**（★成果物は scratchpad で動かした）
- **★裁定の在り処**: `ITEM-2DER-EVO-0027` の `status_note`（逐語:「★手番=設計/監査(処置案を書く)→MGR が承認して ingest」「★実データでの再確認は設計が前回と同じ手順で行うこと」）

---

## 1. ★実データでの再確認（★前回と同じ手順・★3件とも直った）

```
★手順: ★`test_result.artifact`(2099字) を scratchpad で exec し、★`/api/roadmap` と `/api/control` の実データを渡した
★sha256 を本文から再計算 → ★`artifact_sha256` と ★一致（★書き直していない証拠）
```

| # | 前回（1671字） | ★今回（2099字） |
|---|---|---|
| ① 対応表6語 | **★14件が英語のまま**（PLANNED 3/PROPOSED 10/DROPPED 1） | **★★0件**（`完了`73 `予定`3 `提案`10 `進行中`5 `取り下げ`1） |
| ② summary の書式 | `'ITEM-… 完了 PHASE-…'` **不一致** | **★`'[完了] EGL admission in the forward path'` 一致** |
| ③ phase の欄 | `title_ja`/`status_ja` **無い** | **★在る**（`title_ja='Forward-path grounding'` / `status_ja='提案'`） |

```
★他も維持: ★`counts` = {roadmap_done: 73, control_done: 75}（★食い違う2つが両方 出る）
   ★`asof` ／ ★`source_ids` 103件 ／ ★`only_incomplete=True` で 92→19件 ／ ★`full` は4行
★★★∴ ★依頼文を満たしている。★★試験も10本 全通。
```

## 2. ★処置案（★3件とも `REJECTED`。★根拠は依頼文の逐語）

| finding_id | 監査の言い分 | ★判定 | ★根拠（★依頼文の逐語） |
|---|---|---|---|
| `AF-…-run-0` | `control` を突き合わせ/マージしていない（high） | **REJECTED** | 「**`control["roadmap"]["status_counts"]["DONE"]` だけを使う。**」★突き合わせるなと書いてある |
| `AF-…-run-1` | `source_ids` は要求外の追加（medium） | **REJECTED** | 戻り値の形に「**`"source_ids": [str,...]`**」が明記／★封印試験 `assert "I1" in v["source_ids"] and "P1" in v["source_ids"]` |
| `AF-…-run-2` | `source_ids` は dead code（low） | **REJECTED** | 同上。★受入(3)「**いつ時点・台帳ID**」の台帳IDが ★これである |

**★MGR がそのまま ingest できる形（`webui.ingest`:408-409 逐語 `result["finding_dispositions"]`）**
```json
{"finding_dispositions": [
 {"finding_id": "AF-qwen3.6@8005#auditor-seed101-run-0", "verdict": "REJECTED",
  "basis": "依頼文逐語『control[\"roadmap\"][\"status_counts\"][\"DONE\"] だけを使う。』∴ 突き合わせを書かないのが仕様どおり"},
 {"finding_id": "AF-qwen3.6@8005#auditor-seed101-run-1", "verdict": "REJECTED",
  "basis": "依頼文の戻り値の形に source_ids が明記。封印試験 test_page_shows_asof_and_source_ledger_ids が要求している"},
 {"finding_id": "AF-qwen3.6@8005#auditor-seed101-run-2", "verdict": "REJECTED",
  "basis": "同上。source_ids は受入(3)『いつ時点・台帳ID』の台帳ID そのもの"}]}
```
```
★予告: ★全 REJECTED ＋ 試験 ok ∴ ★`READY_FOR_UPPER_REVIEW` へ動く見込み
   ★`workcell.py:177` 逐語コメント:「★全 REJECTED + tests ok = ★false positive、code は妥当」
★★外れたら ★外れたと書く（★1回の観測で断定しない）
```

## 3. ★★原因（★逐語・★これが本体）

```
★`webui.py:378` 逐語:
   ar = auditor.audit({"diff": g.get(★"diff"), "test_result": tr, "task_id": tid, "ts": TS})
★`adapters.py:132-136`（QwenAuditor.audit）逐語 — ★監査に渡る文面:
   "AUDIT this implementation against its ★packet."
   "★IMPLEMENTATION_PACKET:\n{context.get('implementation_packet')}"   ← ★★呼び手が渡していない ＝ ★null
   "DIFF:\n{context.get('diff')}"                                      ← ★★`wr["diff"]` は None
   "TEST_RESULT:…"   "RELEVANT_FAILURE_PATTERNS:\n{…}"                 ← ★これも渡していない ＝ None
★★★∴ ★監査は「★packet と突き合わせろ」と言われながら ★★packet を ★1文字も受け取っていない。
★★★★∴ ★3件の指摘は ★監査の怠慢ではなく ★★与えていないものを見なかっただけである。
```

**★★もう1つ（★今日の変更の副作用・★良い方）**
```
★`diff` は None・`artifact_head` は違反時だけ ∴ ★★今日 `test_result.artifact` を足すまで、
   ★通った走行の監査は ★★コードを1文字も見ずに findings を書いていた【★実測: 上記2箇所の逐語】。
★★★今回は ★★初めて ★コードを見て書かれた findings である（★だから具体的で、★だが要件が無いので外れた）。
```

## 4. ★次の1件の提案（★増やさない・★ACTIVE 化は MGR が決める）

```
★`webui.py:378` の呼び出しに ★`"implementation_packet": ip` を ★1つ足す（★`gen()` が既に `ip` を持っている）。
★★新しい台帳・エンドポイント・状態語・役割を ★作らない。★引数1つ。
★★★増える代わりに畳むもの: ★★「監査の指摘を人が毎回 依頼文と突き合わせて却下する」運用。
★★★★★私は着手しない（★ACTIVE でない）。★★MGR が決める。
```

## 5. ★私が確かめていないこと
```
★`relevant_failure_patterns` を渡すと何が変わるかは ★測っていない【★未確認】
★`implementation_packet` を渡した監査が ★実際に精度を上げるかは ★測っていない【★未確認】——★やってみるまで分からない
```
