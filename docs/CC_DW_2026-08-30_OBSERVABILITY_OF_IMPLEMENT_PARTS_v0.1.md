# EVO-0006 追補 — 「動いたか」ではなく「いまの2DERから観測できるか」 v0.1

- 担当: DW（`DW_CLAUDE`） / 親: `ITEM-2DER-EVO-0006` / 2026-08-30
- 指示: Taka 2026-08-30「実行証拠を取得できるかの観点で12部品を再整理／4種類の記録方式が局所か全体か／
  Capability Map の `EXECUTED=UNVERIFIED` が未実行証拠か観測手段欠落かを既存情報だけで区別できるか」
- ★**新しい記録口・ledger・state・ID・共通emit を1つも実装していない。**
- 出所の鍵: 名乗る名前は **source から ast** ／ 実行は **ETRACE**（共有・env非依存）と **DW events**（env依存・新運転系を明示）

---

## 1. 12部品の観測可能性（★5区分）

| # | 能力名 | 実行証拠 | 取得元 | 実際の鍵（component / function） | Capability名との対応方法 | 現在の実行証拠 |
|---|---|---|---|---|---|---|
| **区分1 直接取得できる**（2件） |
| 1 | `contract_from_plan` | ○ | ETRACE | `contract_from_plan` / **`called`** | 部品名＝component。★function は `called` 固定 | 総397（08-29:15 / 08-30:16） |
| 2 | `check_artifact` | ○ | ETRACE | `check_artifact` / **`called`** | 同上 | 総27,477（08-29:75 / 08-30:9） |
| **区分2 別名の対応付けが要る**（2件） |
| 3 | `contract_seal` | ○ | ETRACE | **`SEAL` / `extract_contract`** | ★source の `emit` 第1・第2引数（ast で取得）以外に対応表は無い | 総343,276 |
| 4 | `live_worker_runtime` | ○ | ETRACE | **`RUNNER.run_test` / `WORKER.received_from_runner` / `RUNNER.hand_to_worker` / `RUNNER.run_minimal_slice`** | 同上。★1部品が**4つの鍵**に分かれる | 573 / 1,084 / 595 / 601 |
| **区分3 別の記録系を辿れば取得できる**（2件） |
| 5 | `generate_via_runner` | ○ | **DW events の `identity`** | `2der-generate-via-runner` | ★ETRACE には出ない。★module名→identity名の対応表は無い（`_` と `-` の差も含む） | 新運転系 今日9 |
| 6 | `build_planner` | ○ | **DW events の `identity`** | `2der-qwen-build-planner` | 同上。★`qwen` が名に入り module名から機械で導けない | 新運転系 今日9 |
| **区分4 現在の既存記録からは観測できない**（6件） |
| 7 | `apply_unified_diff` | ✗ | — | — | — | **観測不能** |
| 8 | `bridge_reconciler` | ✗ | — | — | — | **観測不能** |
| 9 | `source_to_patch` | ✗ | — | — | — | **観測不能** |
| 10 | `apply_cycle` | ✗ | — | — | — | **観測不能** |
| 11 | `test_repair_gate` | ✗ | — | — | — | **観測不能** |
| 12 | `patch_correspondence` | ✗ | — | — | — | **観測不能** |
| **区分5 観測方法をまだ調査できていない**（0件） | — | — | — | — | — | ★12件すべてに4つの鍵を当てた |

### ★区分4の6件 — 「何が存在しないため観測不能か」
```
① 自分で emit しない         … ast で全走査し emit 呼出 0箇所
② _use 経由でも呼ばれない     … component=部品名 / function=called の記録が 0件
③ DW events にも出ない       … identity に対応する語が無い
∴ ★記録する口そのものが存在しない
```
★**「実行されていない」ではない。**★呼び手は12/12在り（呼び手数 2〜16）、
★**動いても記録に出ない**ので、実行の有無は**現在の既存情報からは判定できない**。

---

## 2. 4種類の記録方式は局所問題か（★答え: 全体に効く）

**Capability Map（101能力）の実行判定は、たった1つの鍵で決まっている。**

```
capability_map._observed():
    by = observed_edges.direct_counts.by        ← 唯一の出所
    fn = k.split(".", 1)[1]                     ← ★component を捨て function 名だけを鍵にする
    counts[fn] = ...
→ EXECUTED = YES if counts.get(name) else UNVERIFIED
proof.proof_source = "observed_edges.direct_counts"   （★count が 0 の時は UNVERIFIED）
```

∴ **区分2・3・4の部品は、Capability Map の鍵では原理的に拾えない。**
- 区分2（別名）: function 名が違う → 拾えない
- 区分3（DW events）: ETRACE に無い → 拾えない
- 区分4（口が無い）: どこにも無い → 拾えない

★**局所問題ではない。**★12部品で見つけた4方式は、**同じ判定器が101能力すべてに当たっている**。

★★但し**逆方向は未測定**: `EXECUTED=YES` の93件が、**同名衝突で YES になっていないか**は測っていない
（function 名だけで数えるので、別 component の同名関数があれば YES になり得る）。★これは過大の可能性であり、**私は測っていない**。

---

## 3. ★Taka の問いへの答え

> **「Capability Map の `EXECUTED=UNVERIFIED` が、未実行証拠なのか観測手段欠落なのかを、既存情報だけで区別できるか」**

### ★答え: **区別できない。**

**理由（実測）:**
1. 判定の出所は **1つだけ**（`observed_edges.direct_counts`、function 名鍵）。
2. その鍵で 0 でも、**私の12部品では 6/12 が別の鍵で実行を確認できた** ＝ 0 は「動いていない」を意味しない。
3. **各能力が「どこに記録するか」を宣言した欄が、既存情報に存在しない。**
   - `entry` は在る（`to_domain('esde_relation_status')` ＝ **呼び方**）
   - `proof.proof_source` は在るが、**事後に埋まる値**であり、count が 0 なら `UNVERIFIED` になる
     ＝ **「どこを見るべきだったか」ではなく「見て無かった」しか書けない**
4. 実測: `EXECUTED=UNVERIFIED` の **8件**（`esde_relation_status` と `inference_*` 7件）は、
   **4つの鍵すべてで 0**。★だからといって「未実行」とは言えない ―― **区分4と同じ形かもしれず、区別する材料が無い。**

### ★MGR へ返す「不足しているもの」（★1つだけ）

> **能力ごとの「記録先の鍵」の宣言が無い。**

- 在るもの: `entry`（どう呼ぶか）／ `module`（どこに在るか）／ `proof_source`（事後に何で見つけたか）
- **無いもの**: `records_at`（**この能力が動いたら、どの component / function / identity に出るか**）
- これが在れば、`EXECUTED=UNVERIFIED` は **①宣言された鍵に記録が無い＝未実行の証拠**と
  **②鍵の宣言that自体が無い＝観測手段の欠落**に**機械で分かれる**。
- ★私は実装しない（新しい欄・記録口・ID を作らない指示）。**不足の名指しまで。**

---

## 4. していないこと

- 新しい記録口 / ledger / state / ID / 共通 emit 方式 —— **1つも実装していない**
- `EXECUTED=YES` 93件の同名衝突 —— **未測定**（過大の可能性だけ指摘）
- `EVO-0008` / `EVO-0009` の手番 —— **止めていない**（本書は `EVO-0006` の追補）
- 12部品以外への横展開 —— **していない**（Capability Map への影響は「同じ判定器が当たる」ことの確認に留めた）
