# EGL SoR 契約レポート — AB-0005(test isolation)+ DE-0006(H5/H6)

日付: 2026-07-05  対象: `/home/takasan/egl`  commit: `e7c9cac`(AB-0005)+ `1e86a01`(DE-0006)

## 0. 一行結論
SoR(source of truth)の根幹を強化した。**counters.json という第2 SoR を廃止**し、id を event log からのみ導出する単一 SoR に。前提として **test が canonical SoR を汚さない隔離**を先行させ、H5 の「log だけから id が復元される」検証を信用できる状態にした。SoR 契約試験 9/9・enforce 13/13・RC-3/RC-4 無退行。

## 1. なぜこの順序か(Taka 順序裁定 / DE-0011)
`test_enforce.py` が canonical SoR(`data/events.jsonl`)を上書きする状態で H5(counters 廃止・**event log だけからの id high-water 復元**)を検証すると、「log だけから id が正しく復元される」という当の主張を、**log を汚すテストで確かめる循環**になり検証が非信用。M4(partial-update reject)も SoR 根幹。よって test isolation を SoR 系変更(DE-0006〜)の**前提として先行**させた。

## 2. AB-0005 — test isolation(commit e7c9cac)
- `core.DATA` を env `EGL_DATA_DIR` で差し替え可能化。試験は egl を import する**前**に隔離 temp dir を向ける。
- **操作的証拠(主張でなく実測)**: test 13/13 PASS かつ `data/events.jsonl` が試験**前後で sha256 バイト同一** = canonical SoR 未汚染。
- これで H5 検証をクリーンな harness 上で行える前提が整った。

## 3. DE-0006 — H5/H6(commit 1e86a01)

### 3.1 何を変えたか
| 項目 | 従来(as-coded の欠陥) | 修正 |
|---|---|---|
| **H5** SoR | `counters.json` = events から導出不能な**第2 SoR**。喪失で high-water 不明 → id 衝突 → merge 事故 | **counters.json 廃止**。`append_event(new_prefix=)` が **log high-water から id を採番**。id が存在する ⟺ その id を刻む event が log に存在。high-water は log 再スキャンからの帰結 |
| 採番と書込 | `new_id()` で先に採番 → 後で event 書込。採番後クラッシュで high-water 過小 → 衝突(counters.json と同型故障の再導入) | **id-in-append**: 採番と書込を不可分に。`SELF` 番兵で自己 alias(source_id 等)も同一 event 内で解決。`new_id` 単独 API を撤去 |
| **H6** 並行 | `new_id`/append に lock なし → 並行 run で id 衝突 | 採番+書込を **`fcntl.flock` の同一 critical section** に。並行 run を跨プロセス直列化 |

### 3.2 実装が炙り出した設計事項
id-in-append にすると **candidate ↔ relation の相互参照 cycle**(candidate.evidence_relations ↔ relation.to_id)が顕在化した。調査の結果 **`relation.to_id` はどこからも読まれていない**(gate1/build_packet は candidate 起点で `evidence_relations → from_id`=fragment のみ辿る)= vestigial と判明。→ relation を **`to_id=None` で candidate 生成前に先行生成**し cycle を断った。未読フィールドのため model 上無害・正当。

## 4. 証明 — SoR 契約試験(`test_sor.py`, 9/9 PASS)
| test | 内容 |
|---|---|
| T1a/b/c | H5: counters.json 不在 / id は log high-water から連番 / high-water は log 由来のみ |
| T2a/b | H5: log 再スキャンで high-water 復元(counters.json 無しで next id 一致、衝突なし) |
| T3 | H5: 事前採番 API(`new_id`)が存在しない = id は event と不可分 |
| **T4a/b** | **H6: 並行 4プロセス×30=120 採番で object_id / event_id 衝突ゼロ** |
| T5 | RC-3 不変: id-in-append 後も view は log から決定的再構築 |

### H6 lock の load-bearing 性を counter-factual で実証
lock を no-op に差し替えて同じ並行採番を実行:
> **lock 無効: 120 採番 → 51 uniq(69 衝突/lost write)。lock 有効(T4): 120/120。**
> = lock は飾りでなく必要。DE-0009 の counter-factual 方法論を H6 に適用した。

無退行: `run.py`/`run2.py` exit 0、`test_enforce.py` 13/13、**RC-3/RC-4 PASS**。

## 5. Provenance
- ENGINEERING_FORCED / test-verified。**H6 は counter-factual で load-bearing 確認済**。
- ただし **独立敵対レビューは未実施** → `JUDGE_VERIFIED` は騙らない。次の honesty gate = 独立レビュー。

## 6. 正直な留保 — DE-0006 の content-hash 観測は未実装(AB-0006)
DE-0006 は「observation は content_hash 据置(content-addressed)/連番は claim・gap 系のみ」と記すが、本実装は**全 object 一律 log-monotonic 連番**とし、content-hash 観測を分離した。理由:
1. 観測を content-addressed 化すると同一内容→同一 id の **idempotent create** と **CS-1 dedup 意味論**への波及がある。
2. 原文「据置」の解釈が曖昧(「content_hash を維持」か「content_hash 案は保留」か)。
3. H5/H6 の単一 SoR 目的は一律連番で達成済。

→ **AB-0006(AWAITING_TAKA_CLARIFICATION)** に切出し、DE-0012 note に「意図的に未実装」と明記。

## 7. 台帳
- `DESIGN_EVIDENCE_LEDGER.jsonl`: **DE-0011**(順序裁定)/ **DE-0012**(H5/H6 実装 OPERATIONAL evidence)
- `audit_backlog.jsonl`: **AB-0005** RESOLVED / **AB-0006**(content-hash 要否, Taka 確認待ち)

## 8. 残作業
```
✅ AB-0005  test isolation
✅ DE-0006  H5/H6
   AB-0006  content-hash 観測の要否 ← Taka 確認待ち(1問: 「据置」の意図)
   DE-0007  M4 (partial-update を append_event が schema 完全性で構造 reject)
   DE-0008  L4 (validation_mode derive-or-UNRESOLVED + 過去 event に correction 追記)
            ⚠️ 本系初の RETRACTION/correction 運用例 → event 形式を DE に残す(Taka forward req)
   独立敵対レビューを build-out に当てる(honesty gate)
   §5.3 refactor
```
