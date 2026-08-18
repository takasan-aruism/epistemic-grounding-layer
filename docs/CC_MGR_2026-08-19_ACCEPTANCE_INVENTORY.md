# 宛: Taka / 設計 / 監査 ―― acceptance 棚卸し（★測定のみ・照合器は作っていない）

**新しい acceptance 形式を作っていない。照合器の実装に入っていない。**

## 0. 結論を先に

```
★★現在の 既存データだけで 機械的に 完了判定できる item = ★0 / 34
```

## 1. 母数（★鍵を添える）

```
★鍵=『status が DONE でも DROPPED でも ない』   → ★34 件
   内訳 = PROPOSED 20 ／ DEFERRED 9 ／ PLANNED 3 ／ IN_PROGRESS 2
   出所 = roadmap_registry.items()（143件・★item_id の重複 0＝最新1件/id）
   全体 = DONE 108 ／ DROPPED 1
```

**★以前の「未了 27」とは鍵が違う。** 今回の 34 は上の定義。
**どの切り方でも同じ数になると思ってはいけない**（★繰り返し出ている型「鍵が違う」）。

## 2. 分類（★規則は私が決めた＝鍵を添える）

**規則（上から順に、先に当たった1つ）:**

```
① acceptance が falsy                                  → 「なし」
② 型が str でない（list/dict）                          → 「構造化済み」
③ 引ける id を含み、その kind が TASK/ART/DE/CHG/RUN     → 「実行証拠へ 直接参照可能」
④ 人手を名指しする語 (approval|approve|Taka|human|承認)  → 「人間解釈が 必要」
⑤ 残り                                                 → 「散文のみ」
```

| 分類 | 件数 |
|---|---|
| ① acceptance なし | **21** |
| ② 散文のみ | **3** |
| ③ 構造化済み | **0** |
| ④ 実行証拠へ 直接参照可能 | **0** |
| ⑤ 人間解釈が 必要 | **10** |

### ★「0件」の中身（★0件は 欠落を 隠す ∴ 理由を書く）

**③ 構造化済み = 0** ―― acceptance が入っている 13件は**全部 `str`**。長さは
`80,80,80,80,95,97,141,149,217,681,908,1140,1333` バイト。

**④ 実行証拠へ直接参照可能 = 0** ―― ★「id が無いから」ではない。

```
★引ける id を 含む item = ★2件（EVO-0018 / EVO-0019）
   その id = AMEND-2DER-SUPERVISOR-AUDIT-001 → ★resolved=True
   ★ただし kind = "AMENDMENT" = ★文書 であって ★実行証拠(TASK/ART/DE/CHG/RUN)ではない
★引けない id を 含む item = EVO-0015（EXEC-ECON-SWAP-COST-001 → resolved=False）
★私の 正規表現が `ITEM-bound` を id と 誤検出した（★規則の穴・修正済み）
```

## 3. ★3分割（Taka 指定の切り口）

| 切り口 | 件数 | item |
|---|---|---|
| **接続だけで済む** | **0** | ★該当なし |
| **構造化が必要** | **7** | EVO-0010 / EVO-0015 / EVO-0018 / EVO-0019 / PARALLEL-OPS / PARALLEL-OPS-DECOMPOSITION / OFFRAMP-LIVE-WORKER-RUNTIME |
| **人間判断として残す** | **6** | IMPL-PLATFORM / OFFRAMP / ★VLLM-RUNTIME-PROFILER / QWEN35-A3B-CONCURRENCY-BENCHMARK / QWEN27-CONCURRENCY-BENCHMARK / MODEL-SELECTION-TEST |
| **★そもそも条件が無い** | **21** | 照合の対象にならない（★先に acceptance を書く必要） |

`7 + 6 + 21 = 34`。

**「接続だけで済む」が 0 の根拠**: acceptance の本文が**既存の口の述語を名指ししている件が1つも無い**。
番号付きの条件（`1 … 2 … 3 …`）は在るが、**どの口で引くかは書かれていない**。

## 4. ★測って出た欠陥（本線では直していない）

### (a) acceptance 欄に「完了条件でないもの」が入っている

```
★4件の 本文が ★バイト単位で 完全一致（80B・sha1=3f35e2a1）:
   ITEM-2DER-IMPL-PLATFORM-VLLM-RUNTIME-PROFILER
   ITEM-2DER-IMPL-PLATFORM-QWEN35-A3B-CONCURRENCY-BENCHMARK
   ITEM-2DER-IMPL-PLATFORM-QWEN27-CONCURRENCY-BENCHMARK
   ITEM-2DER-IMPL-PLATFORM-MODEL-SELECTION-TEST

本文 = "GATED: no live run without a scoped ITEM-bound approval token (no bare boolean)."
```

**これは「完了の条件」ではなく「着手の門の条件」。** 欄の使われ方がずれている。
**∴ この4件は acceptance 照合器を作っても照合できない**（照合すべき条件が入っていない）。

### (b) 既に構造化された acceptance の型が別の所に在る

```
AMEND-2DER-SUPERVISOR-AUDIT-001 の 欄に ★`min_acceptance_before_PLANNED` が 在る
★新しい 形式を 作る前に ★これを 見る（★既存を 読んでから 作る）
```

### (c) 証拠側の欄は在るが、ほぼ空

| 欄 | 値が在る item |
|---|---|
| `artifact_ids` | 11 / 34 |
| `evidence_de_ids` | 7 / 34 |
| `task_ids` | **1 / 34**（★今夜 β で 埋めた 1件） |
| `change_ids` / `wiring_evidence` / `wiring_state` | **0 / 34** |

**∴ acceptance を構造化しても、照合する相手（証拠側）が別途 空。** 両側が要る。

## 5. ★経路表について（Taka の問いへの回答）

**無視していた。正確には ―― 経路表に私の作業の区間が最初から無い。**

```
★実測（走行 ETR-9c212273aee1・事象 1330件）
   出た HANDOFF = S01 S02 S03 S04 S05 S06 S08 S09 S12 S16      ← ★10 / 18
   出ていない   = S07 S10 S11 S13 S14 S15 S17 S18
   ★台帳(roadmap_registry)を 名乗る 事象 = ★0
```

**18区間はすべて「1件の依頼が走る道」**（人 → submit → DS/RRI/EGL → DW → dispatch → run → close）。
**区間が存在しないもの:**

```
★① MGR が 読む（/api/state・/api/resolve・item_state の 集約）
★② 台帳へ 書く（★今夜 足した `append_task_id` を 含む）
★③ MGR → Taka の 報告 ／ MGR → 設計・監査 の 文書
```

**∴ 今夜の作業は、経路表から見ると「起きていない」。**
**同型が既出**: 「経路表に Domain 区間 0」（2026-08-18 実測）。

**区間を足すかは設計の話 ∴ 私は足していない。**（新しい管理対象を勝手に増やさない）

## 6. 別件として登記した

```
ITEM-2DER-EVO-0078 = 同じ `actor_role` という 名前で 口ごとに 別の 値が 出る
   status=PROPOSED ／ task_ids=[] （★進捗マーカーだけの 投入=★task を 作っていない）
   ★Taka 指示どおり 本線では 直していない
```

## 7. していないこと

```
★acceptance 照合器の 実装 0 ／ 新しい acceptance 形式 0
★acceptance 本文を 1件も 書き換えていない
★α 0 ／ 過去27件の 遡及 0 ／ 冪等性 0 ／ 契約経路の 一般化 0
★webui.py を 触っていない
```
