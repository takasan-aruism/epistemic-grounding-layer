# PROJECT_GOAL — 2DER は何を完成させたかったのか

- **status: RECONSTRUCTED / PROPOSED**（Taka 未裁定）
- **authored_by: CLAUDE_CODE (INSPECTION_ONLY)** — 2026-07-22
- **claim ceiling: 本書は「一次資料にこう書かれている」ことのみ主張する。目的そのものを新たに定義しない。**
- **本書は `initial-spec-v0.1.md`（親文書）の代替ではない。** 親文書は `docs/README.md:9` で `⛔ PENDING(Taka 提供)` と記載されたまま、2026-07-22 現在も存在しない（`find /home/takasan -iname 'initial-spec*'` → 0 件）。責任分界の一次規定は依然として不在である。

根拠: DESIGN_EVIDENCE_LEDGER.jsonl 全 484 件の分類、5 リポ 676 commit（2026-07-04〜07-22）、`twoder/audit/ROADMAP_REGISTRY.jsonl` 281 レコード、および下記に明示した各文書。

---

## §1. 本線（main theme）

`docs/2DER_TECHNICAL_SPECIFICATION.md:5`（2026-07-10, Taka v0-direction authority）:

> **2DER AUTONOMOUS RESEARCH LOOP v0**（既存資産を機械接続し manual relay を減らす; **self-improvement claim ではない**）

**本線は自律実行ループである。監査機構ではない。**
監査（JREV / GA / Energization / Gate4）は、このループを安全に回すための従属機構として導入された。

上位の動機は `docs/AI_WORK_SYSTEM_OVERVIEW.md`（2026-07-06）:

> 単一の高性能AIに調査・判断・実装・監査・記憶をすべて任せるのではなく、AIの仕事を複数の責任系へ分解し、長期的な研究・開発を壊れにくくするための AI work system である。

対応表（同文書が「本システム全体の最も短い説明」と自称するもの）:

| 人間の介入 | 機構化先 |
|---|---|
| 「あの件だよ」 | DS |
| 「そういう意味じゃない」 | RRI |
| 「前に逆だっただろ」 | EGL |
| 「本当に？懐疑的に見て」 | DW |

名称定義は文書ではなく台帳にある — `DE-0077`（2026-07-07, Taka 裁定）:
> **2DER** = DS / DW / EGL / RRI の 4 責任系から構成される統合 AI work architecture の総称。

---

## §2. 権限の分離（不変則）

`docs/2DER_TECHNICAL_SPECIFICATION.md:22-29`:

| layer | role | 実体 |
|---|---|---|
| WORKER | solve / generate / detect / reconstruct | Qwen3.6-35B-A3B |
| SUPERVISOR | retain / validate / track / open_gaps | **EGL SoR** |
| SENIOR INVESTIGATOR | read-only 調査 | Claude Code |
| AUTHORITY | final disposition | Taka |

> **不変則:** WORKER の生成物は SUPERVISOR で validated evidence にならない。SENIOR INVESTIGATOR は read-only 監査・提案・spec 準備はできるが objective 変更・branch 閉鎖・evidence 昇格はできない。AUTHORITY のみが不可逆 program 判断を持つ。

補強: `AI_DEVELOPMENT_ARCHITECTURE_EGL_RRI_DS_DW_v0_1.md:124,214` — 「EGL は Global Knowledge の採用責任を持つ」「DW は Knowledge Admission を行わない」。
コード強制: `egl/gates.py:2-3` — 「CU-1: LLM は DB write 権限を持たない → 本モジュール(コード)のみが受理を書く」。

**役務の主体 = 2DER / 権限（evidence 昇格）の主体 = EGL / 不可逆判断の主体 = Taka。**
「番人が実行者に奉仕する」「実行者が番人に奉仕する」と上下を述べた文は、いずれの文書にも**記載なし**。関係はすべて権限分離の形で書かれている。

---

## §3. ループの現在地（本書の中核）

```
■ 2DER AUTONOMOUS RESEARCH LOOP v0     状態          根拠
  ① ITEM 選択                          実装済・島     task_selector.py / DE-0347
  ② → DW タスク生成                    ✗ ABSENT      DE-0347  ←←← 唯一の欠損辺
  ③ Worker 実行                        ✅ live       DE-0300 (実Qwen slice) / runner v0.2.3 DE-0470
  ④ 検証 / patch 適用                  ✅ live       DE-0438 (初回 energization) / DE-0487 (回帰全緑)
  ⑤ EGL admission                      ✅ live       DE-0190
  ⑥ ループ閉じ (close_loop)            ✅ live       DE-0176
  ⑦ → ① へ                            ✗            ② が無いため回らない
```

**欠損辺の一次記録 — `DE-0347`（2026-07-17, 実測）:**

> `task_selector / execution_admission / routing_delivery` の島は **intentional READ-ONLY boundary**（git: 導入 commit db258b7/554fa43/2167557 以降、呼び出し元が追加されていない）。未接続の半分 = **ITEM選択 → DW実行 を繋ぐ producer が ABSENT**（`create_task-from-selected_item` は存在しない）。
> Severance class = `CANONICAL_AUTHORITY_CONFLICT_REQUIRES_TAKA_DECISION`

独立確認（2026-07-22）: `task_selector` の呼び出し元は regression テストと `execution_admission.py` のみ。`routing_delivery.py:*` は "READ-ONLY delivery packets ... without launching a worker"。

対応する未着手 ITEM:

| item | status |
|---|---|
| `ITEM-2DER-EVO-0010` Controlled autonomous RD enablement | **PLANNED**（未着手） |
| `ITEM-2DER-OFFRAMP-LIVE-WORKER-RUNTIME` (D. sandbox + local worker) | IN_PROGRESS |
| `ITEM-2DER-EVO-0018` Cost-governed envelope widening | PLANNED |
| `ITEM-2DER-EVO-0019` Independent audit layer | PLANNED |
| `ITEM-2DER-EVO-0015` Qwen3.6-27B FP8 coder 比較 | IN_PROGRESS |

> **要約: ② 以外は全て通っている。2DER は「Taka が与えた仕事を実行して閉じる」ことはできるが、「次に何をやるか自分で選んで着手する」ことだけができない。supervised executor と autonomous loop を分ける辺が、ちょうど 1 本残っている。**

---

## §4. 完成の定義（done）

プロジェクト全体の「Why が満たされた」条件は**文書に記載なし**。存在するのは capability フラグ集合のみ。

`experiments/temporal-provenance/COMPLETION_DEFINITION_v1.json`（2026-07-14, approved_by: Taka, 根拠 DE-0275, `sha256:b935ce10…`）:

```
CDEF-2DER-v1 rule:
A flag is SET only when its bound acceptance artifact exists
AND (for CLASS-N/H) a JREV verdict references it.
```

必須 7 フラグ: `FLAG-PHASE10-AUDIT-ENVELOPE` / `FLAG-PHASE10-TIER1-CORE` / `FLAG-TEMPORAL-FOUNDATION` / `FLAG-ECONOMY-OPERATOR` / `FLAG-LIVE-BENCHMARK` / `FLAG-MODEL-ROUTING-READY` / `FLAG-E2E-ACCEPTANCE`

**現在: 0/7 SET**（DE-0283 実測）。ロードマップ登録簿では 86 ITEM 中 67 が DONE だが、**プロジェクト自身の完成定義では 0/7 である。**

さらに `2DER_CURRENT_FUNCTIONALITY_INVENTORY_ja.md:133` — その完成ゲート自体が production では backing ledger 空/欠落のため**実質 no-op**。

→ **開いている課題: 完成定義とロードマップ DONE 判定が別々の尺度で動いており、突合されていない。**

---

## §5. 目的のドリフト記録（supersede 裁定なし）

| 日 | 一次資料 | 目的の対象 |
|---|---|---|
| 07-05 | `grounding-layer-design-v0.1.md:2-7` | AI が**何を根拠に語るか**（知識） |
| 07-06 | `AI_WORK_SYSTEM_OVERVIEW.md` | AI の仕事を **4 責任系へ分解**（作業） |
| 07-10 | `2DER_TECHNICAL_SPECIFICATION.md:5` | **manual relay を減らす**（運用の手数） |
| 07-12 | `SUPERVISED_AUTONOMY_DESIGN_ja.md:13-15` | **より低コストに、より高パフォーマンス**（Claude のコスト） |
| 07-14 | `2DER_OFFRAMP_SPEC.md:3-6` | **報告・承認・git・実装の 4 窓口を Claude から移譲** |
| 07-20 | `S0.md:10-11` | **handoff 置換**（報告物） |

不変だった核: 「単一 AI に全部やらせない / 自分で作って自分で正しいと判断させない / 根拠なき claim を通さない」。(07-05〜07-20 で一貫)

移動した点: **対象が「知識 → 作業 → 運用 → Claude 自身 → 報告物」と段階的に降りている。** 後段文書は前段を明示 SUPERSEDE していない。移行の是非を裁定した文書は**記載なし**。

---

## §6. 実測: 開発資源はどこに入ったか

DE 484 件の分類（2026-07-22, Claude Code による分類。分類自体は判断であり MEASURED ではない）:

| カテゴリ | 件数 | 比率 |
|---|---|---|
| AUDIT | 116 | 24.0% |
| GROUNDING | 68 | 14.0% |
| PLANNING | 64 | 13.2% |
| BRIDGE | 44 | 9.1% |
| LEDGER | 43 | 8.9% |
| WORKER | 36 | 7.4% |
| RUNTIME | 31 | 6.4% |
| INFRA | 26 | 5.4% |
| META_PROCESS | 19 | 3.9% |
| UI | 15 | 3.1% |
| **SCHEDULER** | **11** | **2.3%** |
| WATCHER | 10 | 2.1% |

番人系 (AUDIT+GROUNDING+LEDGER+META) **51.0%** / 実行系 (RUNTIME+SCHEDULER+WORKER+BRIDGE+UI+WATCHER) **43.4%**。
「これが無くても 2DER は動くか」判定: **essential=YES 115件 (23.8%) / NO 344件 (71.1%)**。

**§3 の欠損辺（① → ②）を担う SCHEDULER カテゴリが、全カテゴリ中で最小の投資（2.3%）である。**

### 荷重を持つ 3 帯と、2 つのコブ

| DE 帯 | 性格 | essential=YES |
|---|---|---|
| DE-0001–0050 | EGL 構造コア | **32** |
| DE-0101–0150 | ★コブ1: HBB/AFE frame 実験 (AUDIT 48%) | 10 |
| DE-0151–0200 | 2DER 本体誕生 (submit/conductor/UI/failure-memory) | **22** |
| DE-0201–0250 | ロードマップ登録の空転 (PLANNING 50%) | **0** |
| DE-0301–0350 | ★コブ2: adjudicator efficacy (AUDIT 42%) | 4 |
| DE-0401–0450 | bridge energization + 実配備 | **23** |

**コブ 1・コブ 2 はいずれも CLOSED-NEGATIVE で閉じた**（DE-0112「no added value over skepticism」、DE-0323「measurement-not-identifiable」）。

これは既知の所見と一致する — **retention > detection**: 新しい検出器を作る系（detection）は繰り返しネガで閉じ、失敗履歴の再接続（retention）と gate 系だけが実欠陥を回収している。
**「監査が多いこと」自体が脱線なのではない。bridge 周りの監査は荷重を持っている（DE-0401–0450）。脱線の実体は、detection を作る実験に DE 100 件分を投じたことである。**

---

## §7. 本書が主張しないこと（non-goals）

- 本書は目的を**新たに定義しない**。§1–§5 はすべて既存文書の引用である。
- §6 の分類は Claude Code の判断であり、MEASURED ではない。件数と比率のみが機械的。
- §3 の「唯一の欠損辺」は、DE-0347 の記録と 2026-07-22 の呼び出し元調査に基づく。**それ以外の辺に欠損が無いことは主張しない**（CDEF-2DER-v1 が 0/7 である以上、各辺の品質水準は別問題）。
- 本書は `initial-spec-v0.1.md` の不在を埋めない。責任分界の一次規定は依然 Taka 提供待ちである。

## §8. Taka 裁定を要する点

1. §5 の目的移動を **正式な supersession として記録するか**、それとも並存目的として扱うか。
2. §4 の二重尺度（ROADMAP DONE 67件 vs CDEF-2DER-v1 0/7）をどちらに寄せるか。
3. §3 の欠損辺 ① → ② を次工程に置くか（DE-0347 の severance class は `CANONICAL_AUTHORITY_CONFLICT_REQUIRES_TAKA_DECISION` であり、Taka 裁定なしには接続できない）。
4. `initial-spec-v0.1.md` を提供するか、不在のまま進むことを明示的に許諾するか。
