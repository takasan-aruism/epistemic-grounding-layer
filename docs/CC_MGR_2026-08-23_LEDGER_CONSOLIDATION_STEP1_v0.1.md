# 台帳の統廃合 ①「統合」 v0.1（実施記録・★安全な2件のみ）

**作成: Claude Code（MGR／台帳側）／ 2026-08-23**

## 0. ★統合の基準（Taka 裁定 2026-08-23・逐語）

> 台帳統合の基準は「**同名か**」ではなく、**同一 schema・同一意味・同一 authority・同一 consumer
> として扱えるか** とする。

> **台帳数を減らすこと自体はゴールにしない。**

## 1. 実施したもの（46 → 41 ／ ★5本減）

| 組 | 判定 | 実測の根拠 |
|---|---|---|
| **`DESIGN_EVIDENCE_LEDGER`** 4 → 1 | **統合した** | 非 egl 3本が持つ `DE-0001`〜`DE-0012` の **12件が全部 egl 版に在る**（front door で 941行を全件走査・**欠落0件**）。`rri` ⊃ `dw` ⊃ `ds` の入れ子で、egl がさらに上位集合 |
| **`REVIEW_LEDGER`** 4 → **2** | **★統合しない** | `egl`＝**JREV 系**（`bundle_verdict`/`claim_ceiling`/`property_verdicts`）、`dev-workcell`＝**DWREV 系**（`review_id`/`target`/`findings`）。★**schema も意味も別** ∴ 両方残す。★空の `ds`/`rri`（0行）だけ外した |
| **`audit_backlog`** 4 → 4 | **★触らない** | 下記 §3 |

★**ファイルは1バイトも消していない**（母数から外すだけ・5本を目視確認）。

## 2. 受入条件
| 条件 | 実測 | |
|---|---|---|
| 46 → 41（5本減） | **46 → 41** | ✅ |
| 外れたのは意図した5本だけ | **一致・増えた0** | ✅ |
| `audit_backlog` を1本も外していない | **4本とも残っている** | ✅ |
| `REVIEW_LEDGER` が2本残っている | **egl 11行 / dev-workcell 2行** | ✅ |
| 残り41本に意図しない属性変化なし | **`rows` の再計測 1件のみ**（`ds/data/event_trace.jsonl`） | ✅ |
| mismatch が増えない | **0 over 41** | ✅ |
| ファイルを消していない | **5本を目視確認** | ✅ |

## 3. ★`audit_backlog` を保留した理由（Taka 裁定）

移送しようとした3行のうち **`GAP-RRI-4` が同一 ID で内容が違った**。

```
egl 版:  class=OPEN_GAP   status=OPEN                       source=Registration Directive v0.3 §6
rri 版:  class=ADDRESSED  status=ADDRESSED_STRUCTURE        source=RRI Context Binding (DE-0003)
         note="directive §6 GAP-RRI-4 の structure 部分を解消。"
```

★**単純重複ではない。`OPEN_GAP → ADDRESSED` の状態遷移履歴である可能性がある。**
∴ **上書き・単純追記・片方破棄のいずれも、reader semantics 確認前には行わない**（Taka 逐語）。

### 別 AXIS で確認すること（5項目）
1. 同一 ID 複数行をどう読むか
2. 最新状態の決定規則
3. writer authority
4. consumer が期待する schema
5. append-only の意味

★衝突しなかった `GAP-DS-2` / `GAP-DS-3` も、**この AXIS の結論が出るまで移送しない**（一緒に扱う）。

## 4. 統廃合の到達点
```
56 → 46（②実験の作業物を母数から外す・2026-08-23）
46 → 41（①安全な統合2件・本書）
★当初の候補「56→37」には合わせない ―― ★基準を満たさない統合をしないため
残る候補: audit_backlog 4→1（保留） / ③7月停止の20本（何のために作ったかが分かるまで触らない）
```
