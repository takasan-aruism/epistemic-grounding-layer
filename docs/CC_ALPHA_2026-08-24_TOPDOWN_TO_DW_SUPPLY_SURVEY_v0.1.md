# Top-Down ESDE → DW 知識供給経路 全件調査 v0.1（実装0）

- 起票: CC_ALPHA(監視) 2026-08-24
- 親: `ITEM-2DER-EVO-0104`
- Taka 指示: 「まだ新規実装しない」「既存機構を全件調査」「欠損だけを報告して裁定を求める」

---

# 0. 結論 —— 欠損は **1区間だけ**

鎖 6区間のうち **5区間は既に在る**。落ちているのは **真ん中の1つ**。

```
TASK → knowledge requirement → packet candidate → applicability gate → selected packet → DW → Qwen
 ✅        ✅                    ✅               ✅                  ❌ ここ        ✅    ❌
```

★正確には欠損は **2か所**だが、**性質が違う**:

- **(A) 知識要求 ↔ packet を結ぶ機械の鍵が無い**（★選べない ―― これが本体）
- **(B) DW は packet を受け取るが Qwen へ渡していない**（★渡し口の最後の1本）

---

# 1. 区間表（★Taka 指示⑤⑥）

| # | 区間 | 判定 | 既存機構 | 実際の呼び手 | 保存場所 | identity の鍵 | authority | 不足 |
|---|---|---|---|---|---|---|---|---|
| 1 | **TASK → knowledge requirement** | **EXISTS** | `build_state` の `work.next_information_need` / `rri.research_focus` / `egl.open_gaps` / `request_gaps` | front door `/api/state`（live） | `runs/<task>.trace.json` | `task_id` | `READ_ONLY_INSPECTION` | ★**自然文のみ**。分類 id が付かない |
| 2 | **→ packet candidate** | **EXISTS** | `artifact_registry.all_active()` + `artifact_kind` | 私の probe / 既存呼び手多数 | `twoder/audit/ARTIFACT_REGISTRY.jsonl` | `ART-…` | 既存 | ★候補化はできる（下記実測） |
| 3 | **→ applicability gate** | **EXISTS** | `domain_esde.esde_packet_applicable` / `stale_packet_gate` | `to_domain('esde_packet_applicable')`（本線） | packet ファイル | `packet_id` ⇄ path ⇄ `ART-…`（1対1） | `ESDE_KNOWLEDGE_LEG`／判定は門なし | — |
| 4 | **→ selected packet** | ★**MISSING** | — | — | — | ★**無い** | — | ★**要求と packet を結ぶ鍵が無い**（§2） |
| 5 | **→ DW** | **EXISTS** | `dw/workflow.run_standard_workflow(…, knowledge_packet, …)` / `run_task.run(…, knowledge_packet_path, …)` | `W.create_task(task_id, …, knowledge_packet, …)` | DW の task 記録 | `task_id` | 既存 | ★**path で受ける**＝ART で受ける口ではない |
| 6 | **→ Qwen** | ★**PARTIAL** | `QwenCoder.generate(implementation_packet)` | `dw/adapters.py:98` | — | — | `DW_MACHINE_DISPATCH` | ★**worker には渡っていない**（§3） |

---

# 2. ★欠損(A) —— 要求と packet を結ぶ鍵が無い

## 2.1 実測（TASK-2DER-C032596E）

| 測ったもの | 値 |
|---|---|
| TASK の知識要求 | **7件**（`work.next_information_need`） |
| 例 | 「具体的なバグ内容」「修正すべき箇所」…… ★**日本語の自然文** |
| artifact 全件 | **328** |
| → `artifact_kind='generated_result'` | **5** |
| → 開いて packet と判定できた | **1**（`ART-532f176b08` / `domain='Python runtime / import resolution'`） |
| ★要求と `domain` の機械照合 | **0件一致** |

★**候補の母数は機械で作れる（328 → 5 → 1）。手書きの対応表は要らない。**
★しかし **選べない** —— 片方は日本語の自然文、片方は英語の `domain` 文字列で、**共通の鍵が無い**。

★この 0件一致は**正しい**（このタスクに Python import の知識は要らない）。
★問題は「合わなかった」ことではなく **「合うかどうかを機械で言えない」**こと。

## 2.2 既存の分類 id は使えなかった

| 候補の鍵 | 実測 |
|---|---|
| 勘定科目（`effective_account_of`） | `{"Q-7b6a89bd": "UNCLASSIFIED"}` ★**未分類** |
| `build_packet` の引数に account/concept/topic/tag | ★**1つも無い** |
| `EVIDENCE_BACKED_SECTIONS` | `known_failures` / `constraints` / … ★**分類の欄では無い** |

∴ **TASK 側にも packet 側にも、共通の分類 id が無い。**

## 2.3 ★これが「最後の欠損」

Taka 指示⑧「**選択根拠を後から説明できなければ成立扱いにしない**」に照らすと、
いま packet を選べば **根拠は私の判断**になり、機械では説明できない。∴ **成立扱いにしない。**

---

# 3. ★欠損(B) —— DW は受け取るが Qwen へ渡していない

```
run_standard_workflow(task_id, project_id, goal, knowledge_packet, implementation_packet, …)
  ├─ W.create_task(task_id, project_id, goal, knowledge_packet, …)          ← ★記録される
  ├─ worker.generate(implementation_packet)                                  ← ★knowledge_packet が 無い
  └─ ctx = {…, "relevant_failure_patterns": knowledge_packet.get("related_failure_patterns", [])}
        → auditor.audit(ctx)                                                 ← ★監査役には 一部だけ届く
```

`QwenCoder.generate` が送るのは逐語 `IMPLEMENTATION_PACKET:\n{json.dumps(implementation_packet)}` のみ。

∴ **knowledge packet は DW に入り、監査役に一部届き、コーディング worker には 1バイトも届かない。**

★なお `knowledge_packet.get("related_failure_patterns")` は
**`knowledge_packet_provenance` の schema に無い欄**（`EVIDENCE_BACKED_SECTIONS` に含まれない）。
∴ DW が期待する packet と、私が永続化した packet は **別の形**。★これも同一性の分岐候補。

---

# 4. ★大量に流さない設計（Taka 指示⑧）について

現状はむしろ逆で、**0バイトしか流れていない**。
∴ 「絞る」より先に「**1本だけ通す**」が要る。

★通すとしても、`implementation_packet` に丸ごと入れる形にはしない —
**選ばれた packet の `ART-…` と、使う section だけ**を渡すのが最小。
（★実装は裁定後。ここでは書かない。）

---

# 5. ★裁定を求める点 —— 欠損(A) の埋め方だけ

**新台帳・新state・新ID族・新検索器を作らずに、要求と packet を結ぶ鍵をどう与えるか。**

私が実測から見た選択肢（★どれも私は決めない）:

1. **packet 側に既存 id を持たせる** —— `parent_requirement_id` は既に在る（今回 `ITEM-2DER-EVO-0104`）。
   ★TASK は ROADMAP item に繋がり得る ∴ **item を鍵にする**案。
   ★但し実測 = このタスクは `roadmap.linked=false`（★繋がっていない TASK が在る）。
2. **勘定科目を鍵にする** —— 既存の `LCAT-`/`LDET-` を packet に持たせる。
   ★但し実測 = 当該 thread は `UNCLASSIFIED`（★分類が付いていない）。
3. **`domain` 文字列の突き合わせを LLM に任せる** —— ★選択根拠が説明できなくなる ∴ 指示⑧に反する。
4. **要求側に分類を付ける口を既存機構から探す** —— ★本調査では見つからなかった（§2.2）。

★**1 と 2 は「鍵は在るが値が入っていない」**。∴ 欠損は *機構* ではなく **母数の充填**かもしれない。
★そこを確かめるのが次の一手だが、**どちらを正とするかは設計判断** ∴ 裁定を求める。

---

# 6. やっていないこと（★Taka 指示どおり）

- 新規実装 **0行**
- Qwen への本番投入 **なし**
- 新しい検索器 / 新台帳 / 新state / 新ID族 **なし**
- 手書きの TASK→Packet 対応表 **作っていない**
- packet の選択 **していない**（★根拠を機械で説明できないため成立扱いにしない）
