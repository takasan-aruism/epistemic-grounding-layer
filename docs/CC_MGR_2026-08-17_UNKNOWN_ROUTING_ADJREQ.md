# UNKNOWN → 専門Worker 振り分け（1件）／ ★DESIGN へ 独立検算の依頼

- 宛: **DESIGN（監査兼務）** ／ 写: Taka ／ 発: MGR ／ 2026-08-17 22:4x
- 台帳: `ITEM-2DER-EVO-0067`（★新台帳 0・新しい口 0・新規実装 0）
- 根拠: Taka 逐語「**7. 別主体が UNKNOWN母数・振り分け先・調査結果を独立検算する**」

---

## 0. ★あなたに頼むこと（3つだけ）

```
①UNKNOWN の 母数 5 を ★あなたが 自分で 引き直す（私の数を 見ないで）
②振り分け 9行に ★漏れた 組み合わせが 無いか
③Worker の 返却 8件の ★件数と 語（特に confidence）が 妥当か
→ 出す物 = 【一致 ／ 不一致 ／ ★あなたが 調べた 母数】
```

**★私の数を 検算の 入力に しない。**同じ口から 別々に 引いて 突き合わせてください。
（2026-08-17 は これでしか 見つからなかった欠落が 2件 出ています → `passed-materials-only-blindspot`）

---

## 1. ★母数の 引き方（私が 使った口）

```
GET /api/resolve?id=ITEM-2DER-EVO-0067&history=1&history_limit=0
  → 履歴 ★全件 49 ／ ★切った 0（history_meta で 確かめた）
  → 本文の `MATERIAL <名前> |` 行を 取る
  → v0.2 §18 の ★出力 9つ と 突き合わせる
     （§18 の 正本 = egl/docs/TAKA_2026-08-17_DOMAIN_DESIGN_ENGINE_v0.2.md）

結果 = required 11 ＝ ★known 6 ／ ★UNKNOWN 5
UNKNOWN 5 = dependencies ／ impact ／ unknowns ／ Work Units ／ evidence coverage
```

**★ここは 私が 一度 外した所です**（2 と書いて 実際 5）。原因＝**母集団を 自分の頭から 採った**。
∴ **§18 の 9つ から 採り直してください。**私の 5 を 写さないで。

---

## 2. ★Worker の 実体（実測・★新規実装 0）

| 役 | 実体 | 判定 |
|---|---|---|
| FAILURE | `failure_memory.load_records` / `recurrence_count` | ★在る |
| SUCCESS | `contract_progress` / `stage_from_evidence` | ★在る |
| ROUTE | `route_facts` / `relay_chain` / `callee_candidates` | ★在る |
| ENV | `dw.adjudicator.probe_environment` | ★一部 |
| EXTERNAL | ― | ★無い（口 0件） |

**★5役のうち 3役は「作る」でなく「既存部品に 役を 割り当てた」だけ。**

---

## 3. ★振り分け 9行（受入②・④）

```
dependencies       ROUTE     ASSIGNED
dependencies       FAILURE   ASSIGNED
impact             ROUTE     ASSIGNED
impact             SUCCESS   ASSIGNED
unknowns           FAILURE   ASSIGNED
unknowns           EXTERNAL  ★EXTERNAL_RESEARCH_REQUIRED / NOT_IMPLEMENTED
Work Units         ―         ★NO_WORKER_AVAILABLE
evidence coverage  SUCCESS   ASSIGNED
evidence coverage  ROUTE     ASSIGNED
```

- **★1件を 複数Worker へ 送れている**（4件が 2役ずつ）＝ 受入④
- **★無所属を 黙って 残していない**＝ `Work Units` を **語で** 出した ＝ 受入②
- **★振り分けの 規則は 私（MGR）が 書きました。**ここは 機械化していません。**この 9行が 検算対象です。**

---

## 4. ★Worker の 返却 8件（受入⑥ = 調査範囲・未調査範囲・根拠）

| UNKNOWN | 役 | 出所 | 調べた | 分かった事 | 確度 | ★調べていない事 |
|---|---|---|---|---|---|---|
| dependencies | ROUTE | `observed_edges.relay_chain` | 18/18 | 区間の依存は 18区間で 表せる | high | 口・台帳の依存は 経路表に 無い |
| dependencies | FAILURE | `failure_memory.load_records` | 7/7 | 依存に関する 失敗型 **0件** | high | ― |
| impact | ROUTE | `route_facts.one_sided` | 51/51 | 片側だけの区間 51本が 影響候補 | medium | ★変更→影響の **向きが 出せない** |
| impact | SUCCESS | `contract_progress` | 201/201 | 段が進んだ契約から 影響の実績を 引ける | **low** | ★影響範囲の **語が 無い** |
| unknowns | FAILURE | `failure_memory.load_records` | 7/7 | 未知に関する 失敗型 **0件** | high | ★「調べて0」であって「調べていない」ではない |
| unknowns | EXTERNAL | ― | **0 / 母数も 取れない** | ― | ― | ★口が 無い（NOT_IMPLEMENTED） |
| evidence coverage | SUCCESS | `contract_progress` | 201/201 | 網羅は `materials_used` が 部分的に 持つ | medium | ★未取得の材料は 表に 出ない（本日の型） |
| evidence coverage | ROUTE | `observed_edges.relay_chain` | 18/18 | 区間 18/18 が 根拠つき | high | ― |

---

## 5. ★`0件` の 4区分（★混ぜていない）

```
①全母集団を 調べて 該当0  → `unknowns`/FAILURE（★7 を 全部 調べて 0）
                            `dependencies`/FAILURE（★同上）
②取得できなかった          → `unknowns`/EXTERNAL（★口が 無い・母数すら 取れない）
③そのWorkerでは 扱えない    → `Work Units`（NO_WORKER_AVAILABLE）
④一部だけ 調べて 0         → ★今回 該当なし
```

**★`0件だから問題ない` とは 書いていません。**

---

## 6. ★私の 統合判定（★ここが いちばん 検算して ほしい）

```
★required へ 昇格 = 1件
   dependencies（★2役とも high ／ 18/18・7/7 と 全数）

★UNKNOWN のまま = 4件
   impact            ← 51本の 候補は 出たが ★向きが 出せない（ROUTE medium ／ SUCCESS low）
   unknowns          ← 内部は 全数調べて 0 ／ ★外部が 未実装
   evidence coverage ← ★未取得の材料が 表に 出ない（本日の 実害と 同じ型）
   Work Units        ← ★担当 Worker なし
```

**★特に 見て ほしい 3点**

```
①`impact`/SUCCESS の confidence=low は 妥当か（201件 全数 見て なお low と したのは
  ★「影響範囲」という 語が どの欄にも 無い から。★この理由で 合っているか）
②`dependencies` を required へ 昇格して よいか
  （★経路表の 18区間 だけで「依存」を 名乗ってよいか。★口・台帳の依存は 見ていない）
③振り分け 9行に ★漏れた 組み合わせが 無いか
  （例: `Work Units` に ENV や SUCCESS を 割り当てられないか＝★NO_WORKER_AVAILABLE は 早計でないか）
```

---

## 7. ★私が 確度を 保証できない所

- **振り分けの 規則は 人（私）が 書いた** ―― 受入③「人が UNKNOWN ごとの **調査内容** を 書かない」は 守った（調査内容＝Worker の 返り値）が、**どの役に 送るかは 私の 判断**。
- **`Work Units` の NO_WORKER_AVAILABLE は 探索を 尽くしていない** ―― 5役の 中に 見当たらなかった、まで。
- 受入⑤「独立可能な Worker は **並列実行できる 構造**」は **構造として 成立**（8件が 互いの 出力に 依存しない）だが、**今回 実際に 並列で 走らせては いない**。★「できる形」であって「やった」ではない。

---

## 8. 手番

**★次の 手番 = DESIGN。**上の ①②③ を 独立に 引いて、**一致 ／ 不一致 ／ 調べた母数** を返してください。
**★通ったら この1件は 閉じます。次工程へは 自動で 進みません**（Taka 逐語）。
