# 2DER 構造再構成 — 進行レポート（追記式）

- **status: PIPELINE_COMPLETE**（2026-07-22 Stage 8 / T-1・T-2・T-3 SATISFIED。§3.9）
  以降の追記は、この台帳を使う側の作業記録に限る。Stage を足さない。
- **spec:** `docs/STRUCTURAL_RECONSTRUCTION_SPEC_v0.2.md`（v0.1 を SUPERSEDE）
- **claim ceiling:** 本書は実測値と、その導出方法のみを記す。未計算の列については「未計算」と書く。
- **追記規約:** 各 Stage 完了ごとに §3 に追記する。**過去の記述を書き換えない。**
  訂正が必要な場合は取り消し線ではなく「§3.x で訂正」と追記し、訂正側に根拠を書く（append-only）。

---

## §1. 進捗サマリ

| Stage | 内容 | 手段 | 状態 |
|---|---|---|---|
| 1a | FILE_MANIFEST（全ファイル台帳） | 決定論 | ✅ 完了 2026-07-22 |
| 1b | SYMBOL_INDEX（AST / md / json 抽出） | 決定論 | ✅ 完了 2026-07-22 |
| 1c | REACHABILITY（module 単位 `wired`） | 決定論 | ✅ 完了 2026-07-22（**十分条件ではない。§4-U1**） |
| 1d | symbol 単位 到達可能性 | 決定論 | ✅ 完了 2026-07-22（§3.2。**U1 は部分的に閉じた。U7 が新規発生**） |
| 1e | `executed` 列（runs/ + events.jsonl） | 決定論 | ✅ 完了 2026-07-22（§3.2） |
| 2 | file-level extraction | Qwen 30並列 | ✅ 完了 2026-07-22（§3.3。**初回は計器不良で全破棄。I2**） |
| 2b | 再現性ゲート → **3シード合議** | Qwen | ✅ 完了 2026-07-22（§3.3。**単一シードは不採用。I3**） |
| 3 | COMPONENT_INVENTORY + ITEM_LADDER | 決定論 | ✅ 完了 2026-07-22（§3.4。**Qwen 不要だった**） |
| 4 | EDGE_INVENTORY（中核） | 決定論 | ✅ 完了 2026-07-22（§3.5。**TR-4 陽性対照 合格**） |
| 5 | HISTORY_EVENTS / フェーズ分割 | 決定論 | ✅ 完了 2026-07-22（§3.6。**Qwen 不要**） |
| 6 | 矛盾監査・系譜分類 | 決定論 | ✅ 完了 2026-07-22（§3.7。**7 種すべて機械化。Qwen 不要**） |
| 7 | TR-1..6 トレーサビリティ試験 | 決定論 | ✅ **全合格 / T-1 SATISFIED** 2026-07-22（§3.8） |
| 8 | 人間向けドキュメント 4 本 + 07-12 版 diff | 執筆（機械可読層の引用のみ） | ✅ **T-2 / T-3 SATISFIED** 2026-07-22（§3.9） |

Stage 1 の全数値は決定論的計算であり、再実行でバイト一致する。
Stage 2 以降は LLM（Qwen3.6-35B-A3B @ :8005）を使用する。**LLM 由来の行は
すべて `T3_DERIVED` かつ 3 シード合議を経たものに限る**（§3.3 / I3）。

---

## §2. 成果物の現況

### 機械可読層 `egl/structure/`（すべて DERIVED / regenerable、SoR ではない）

| ファイル | 行数 | 生成元 | 決定性 |
|---|---|---|---|
| `FILE_MANIFEST.jsonl` | 1,317 | git + filesystem | ✅ バイト一致 |
| `SYMBOL_INDEX.jsonl` | 1,215 | ast / regex | ✅ バイト一致 |
| `REACHABILITY.jsonl` | 427 | import グラフ BFS | ✅ バイト一致 |
| `SYMBOL_REACHABILITY.jsonl` | 2,122 | AST コールグラフ BFS | ✅ 決定論 |
| `EXECUTION_EVIDENCE.jsonl` | 96 | T2 実行痕跡スキャン | ✅ 決定論 |
| `FILE_EXTRACTION.jsonl` / `_S23` / `_S47` | 各 241 | Qwen seed 7/23/47 | 生 LLM 出力（**単体では採用不可**） |
| **`FILE_EXTRACTION_CONSENSUS.jsonl`** | **238** | 3 シード合議 | ✅ 採用可 |
| `UNRESOLVED.jsonl` | 1,081 | 合議で落ちた項目 | 隔離 |
| `COMPONENT_INVENTORY.jsonl` | 17 | 決定論 + 合議 | ✅ 決定論 |
| **`ITEM_LADDER.jsonl`** | **86** | 決定論 | ✅ 決定論 |
| **`EDGE_INVENTORY.jsonl`** | **1,313** | 決定論（AST 呼出点 + ゲート伝播） | ✅ 決定論 |
| `HISTORY_EVENTS.jsonl` | 682 | git + AST import 差分 | ✅ 決定論 |
| **`CONTRADICTIONS.jsonl`** | **182** | 導出層の機械的 join | ✅ 決定論 |
| `LINEAGE.jsonl` | 427 | 到達分類 + 命名規則 | ✅ 決定論 |
| `ITEM_LADDER.jsonl`（更新） | 86 | + CHG→DE→ART 連鎖 | 束縛 44→**58** |

生成スクリプト: `s1_manifest.py` / `s1_symbols.py` / `s1_reach.py` / `s1d_symgraph.py` /
`s1e_executed.py` / `s2_extract.py` / `s2b_consensus.py` / `s3_components.py` / `s3b_item_ladder.py` / `s4_edges.py` / `s5_history.py` / `s6_contradictions.py` / `s7_traceability.py`

未生成: `CLAIM_EVIDENCE_INDEX`

---

## §3. 実行ログ（追記部）

### §3.1 — 2026-07-22 Stage 1a/1b/1c 完了

#### 対象の確定

```
総ファイル数            1,317   (__pycache__ / .git 除く)
  T1_TRACKED             826    git 管理下
  T2_RUNTIME             491    実行時記録（executed 列の唯一の根拠源）
```

内訳（tier 別）:

| classification | T1 | T2 |
|---|---|---|
| runtime_trace | 4 | **341** |
| source | 247 | 31 |
| ledger | 217 | 42 |
| test | 147 | 10 |
| doc | 140 | 6 |
| artifact | 52 | 28 |
| event_store | – | 22 |
| archive | 14 | – |
| generated | 5 | 12 |

リポ別: egl 495/30、twoder 204/351、dev-workcell 76/109、rri 37/1、ds 14/1（T1/T2）。

#### 抽出量

```
SYMBOL_INDEX 対象   python 427 / markdown 146 / json 588 / jsonl 54
定義シンボル総数    2,122
Python 総 LOC       44,914
import 文総数       2,215
parse error         0
```

#### 【所見 F1】live path は 68 ファイル / 9,810 LOC

live entrypoint 4 本（`twoder/webui.py`, `twoder/submit.py`, `twoder/operator.py`,
`dev-workcell/dw/dispatch.py`）からの import グラフ BFS：

| 分類 | files | LOC |
|---|---|---|
| **LIVE_REACHABLE** | **68** | **9,810** |
| TEST_ONLY | 157 | 13,808 |
| ARCHIVE_OR_EXPERIMENT | 97 | 9,748 |
| SUPPORT_OFF_LIVE_PATH | 66 | 7,503 |
| STANDALONE_ENTRYPOINT | 19 | 2,738 |
| ORPHAN（呼び出し元も CLI も無い） | 20 | 1,307 |

**全 Python の 16% / LOC の 22% しか live path 上に無い。** 最大到達深度は 4。
live のリポ別内訳: twoder 36 / rri 16 / dev-workcell 7 / egl 7 / ds 2。

> 注: TEST_ONLY 157 / ARCHIVE_OR_EXPERIMENT 97 は「無駄」を意味しない。
> 分類であって評価ではない（spec §5 の 6 分類へ Stage 6 で写像する）。

#### 【所見 F2】既存監査文書 `twoder/audit/MISSING_EDGES.md`（07-12）は stale

同文書 §11 の記述:
> RRI formal validation/handoff suite — `iec.validate_iec`, `resolved_intent.…`,
> `research_axis.…`, `rdec.…`, `request_resolution.…`, `need_validation.…`,
> `approved_rq_set.…`. All implemented + individually tested, **all unwired**.

本計算での実測:
```
twoder/rri_formal.py            <- twoder/submit.py           (depth 1)
  rri/rri/approved_rq_set.py    <- twoder/rri_formal.py       (depth 2)
  rri/rri/iec.py                <- twoder/rri_formal.py
  rri/rri/rdec.py               <- twoder/rri_formal.py
  rri/rri/need_validation.py    <- twoder/rri_formal.py
  rri/rri/request_resolution.py <- twoder/rri_formal.py
  rri/rri/research_axis.py      <- twoder/rri_formal.py
  rri/rri/resolved_intent.py    <- twoder/rri_formal.py
  rri/rri/rq_candidate.py       <- twoder/rri_formal.py
```
→ **DE-0231（2026-07-13, "RRI formal-validation suite wired into submit forward path"）で塞がっている。**
監査文書が書かれた翌日である。

**意義:** 本パイプラインが、人手の as-built 監査が捉えていない変化を独立に再検出した。
spec §7 の TR-4（陽性対照）の予行として機能している。ただし正式な TR-4 は Stage 7 で実施する。

#### 【インシデント I1】自己参照による決定性破壊（修正済み）

Stage 1a の初回実装で、導出物 `FILE_MANIFEST.jsonl` を `egl/structure/` に置いた結果、
2 回目の走査が自分自身を対象に含め、行数が 1,317 → 1,318 に増加した。

- **同型の先例:** DE-0132「live-ledger self-referential reproducibility bug, fixed by pinning input snapshot」
- **修正:** `egl/structure/*.jsonl`（T3_DERIVED）を走査対象から除外（`s1_manifest.py`）。
- **検証:** 再実行でバイト一致を確認。
- **一般化:** 導出層は自身を観測対象にしてはならない。Stage 1e 以降も同じ除外を適用する。

---

### §3.2 — 2026-07-22 Stage 1d/1e 完了 ＋ **所見 F2 の訂正**

#### 1d: symbol 単位コールグラフ

```
定義シンボル            2,122
コールサイト           23,382
解決内訳
   3,115  13.3%  resolved_import        (import 経由で一意に解決)
   4,652  19.9%  resolved_local         (同一ファイル内定義)
   1,698   7.3%  resolved_by_name_unique(同名定義が1つ)
   3,811  16.3%  resolved_by_name_multi (同名定義が複数 → 全候補へ張る＝過剰近似)
  10,106  43.2%  unresolved             (組込み/標準ライブラリ/動的ディスパッチ)
```

`resolved_by_name_multi` は**意図的な過剰近似**である。よって symbol reach は **上限値**であり、
過小評価にはならない（真に呼ばれるものを取りこぼさない側に倒してある）。

```
到達シンボル            394 / 2,122  (18.6%)
到達シンボルを持つファイル   107
module 単位 LIVE            68
  両方一致                  53
  module-LIVE だが到達シンボル 0   15   ← ★
  symbol 到達だが module-LIVE でない 54   （内訳: 過剰近似由来。
        ARCHIVE_OR_EXPERIMENT 19 / TEST_ONLY 14 / SUPPORT 12 / STANDALONE 5 / ORPHAN 4）
```

#### 1e: `executed` 列（T2_RUNTIME のみ）

```
twoder/runs/*.json       337 files /   337 records   (うち submit トレース 117)
dev-workcell/events.jsonl  1 file  /   674 records
ds/ds_events.jsonl         1 file  / 1,008 records
rri/rri_records.jsonl      1 file  /   680 records
twoder/failure_recurrence  1 file  /   109 records
egl/data*/events.jsonl     7 files / 2,136 records
                                     -----------
                        parse 失敗 0 / 区別できる実行シグナル 96 種
```

submit 経路 117 トレース全件に現れるキー（＝毎回通る本線）:
`DS_INPUT_REF` / `DS_OUTPUT_PACKET_REF` / `RRI_CONTEXT_BINDING` / `RRI_RESOLVED_INTENT` /
`EGL_QUERY` / `EGL_SOURCE_REFS` / `EGL_OPEN_GAPS` / `MEASURED_STATE` /
`SELECTED_ACQUISITION_METHOD` / `DW_TASK_ID` / `NEXT_LEGAL_OPERATION` / `ACTOR_ROLE` / `DISPATCH_RESULT`（各 117/117）

---

#### 【訂正】所見 F2（§3.1）を訂正する

§3.1 の F2 は「`MISSING_EDGES.md`（07-12）の *RRI formal suite 全7本未配線* は stale で、
DE-0231 により配線済み」と記した。**これは module import 単位の観測であり、結論として不正確だった。**
正しくは以下である。

**5状態ラダー（RRI formal validation suite / `ITEM-2DER-EVO-0002`）**

| 状態 | 判定 | 機械的根拠 |
|---|---|---|
| `documented` | **YES** | `ITEM-2DER-EVO-0002` status=DONE、DE-0231 |
| `implemented` | **YES** | `rri/rri/{iec,resolved_intent,research_axis,rq_candidate,approved_rq_set,rdec,request_resolution,need_validation}.py` に validator 実体 |
| `wired` | **YES** | `twoder/submit.py:99` に `RF.run_formal_validation(formal_candidates, ts)` の呼び出しが実在 |
| `executed` | **NO** | **`RRI_FORMAL_VALIDATION` は 337 トレース中 0 件** |
| `proven` | **NO** | 実行が 0 である以上 acceptance artifact に紐づく実行証拠がない |

**なぜ実行されないか（一次資料）** — `twoder/submit.py:96-99`:

```python
# ITEM-2DER-EVO-0002: RRI formal-validation (Class-B, deterministic, no :8005). SKIPPED when no candidates
#    are supplied (default) => no behavior change. On HOLD ... do NOT proceed to DW.
if formal_candidates:
    from twoder import rri_formal as RF
    fv = RF.run_formal_validation(formal_candidates, ts)
```

`formal_candidates` は既定で空である。**コード自身のコメントが「既定でスキップ＝挙動変化なし」と明言している。**
配線は存在するが、その分岐に入る呼び出し元が存在しない。

**したがって:**
- `MISSING_EDGES.md`（07-12）の「RRI の契約検証は実行時に一度も走らない」という**主張は今も正しい**。
- 誤っていたのは同文書の**理由**（「未配線」）であり、正しい理由は**「配線済みだが既定で分岐に入らない」**。
- §3.1 F2 の「stale」判定は撤回する。私の観測粒度が粗かった。

> **この 1 件が本パイプラインの設計根拠そのものである。**
> `implemented / wired / executed` を「ある・ない」の一語に潰すと、この状態は表現できない。
> ROADMAP は DONE と言い、コードには呼び出しがあり、しかし一度も動いていない。
> spec §1.2（5状態を別々の機械的根拠から計算する）が実測で正当化された。

#### 【所見 F3】静的解析の限界を実測（→ U7）

`rri_formal.py` は `STAGES` テーブル経由の間接呼び出し（`fn(candidates, x)`）で validator を呼ぶ。
AST では解決できないため、symbol グラフ上では rri validator 8 本が「未到達」に出る。
**この 8 本が §3.2 の「module-LIVE だが到達シンボル 0」15 件のうち 8 件を占める。**
静的到達性は動的ディスパッチを越えられない。`executed` 列（T2）が唯一の裁定者である。

残り 7 件（`completion_flag_gate` / `control_surface_read` / `estimation_basis_binding` /
`foundation_forecast_report` / `human_escalation_ledger` / `reference_oracle` /
`unknown_variance_policy`）は Stage 3 で個別に判定する。

---

### §3.3 — 2026-07-22 Stage 2 / 2b 完了（**インシデント 2 件。設計を 1 つ変更**）

#### 【インシデント I2】スキーマ強制が効いていなかった — 計器の対照が無効だった

初回実行前のスモークテストはこうだった:

```
prompt : 'Return {"ok":true,"n":3} exactly.'
schema : {ok: boolean, n: integer}
result : {"ok":true,"n":3}   → 「guided_json OK」と判定した
```

**これは何も証明していない。** プロンプトに答えを書いてあるため、スキーマ強制が効いていても
いなくても同じ出力になる。**対照になっていない対照**を根拠に本番を回した。

正しい陰性対照（プロンプトが一切言及しないキーをスキーマが要求する）での再試験:

| 方式 | 出力 | 判定 |
|---|---|---|
| 制約なし | `{"colour":"Blue","why":"Rayleigh…"}` | — |
| `guided_json` | `{"colour":"Blue","why":"Rayleigh…"}` | **無視されている** |
| `response_format: json_schema (strict)` | `{"zzz_alpha":0,"zzz_beta":"zzz_gamma"}` | **強制が効く** |
| `extra_body.guided_json` | `{"colour":"Blue",…}` | 無視 |

→ **この vLLM ビルドでは `guided_json` は黙って無視される。**

**初回実行の結果は全破棄した。** 241 件中 OK 106 / ERROR 135（56%）。
しかも OK 106 件もスキーマに従っておらず、`evidence` が `"Lines 29-40 (…)"` という
自由文字列だった（要求は `{line_start:int, line_end:int}`）。仕様 §1.5（引用必須）も
§3.2（出力スキーマ固定）も満たしていない。

> **これは仕様が防ごうとしていた失敗形そのものである。** 「30 worker がもっともらしい要約を書く」
> 危険を指摘しておきながら、私自身が計器を検証せずに本番を回した。
> 先例: DE-0437「安全性検証には陽性対照テストも要る」。

#### 修正後の実行（`response_format/json_schema` strict、max_tokens 2600）

```
241 件  OK 232 / ERROR 9 (3.7%)
必須キー欠落                    0
evidence オブジェクト        4,407
  形式不正                      0
  ファイル範囲外(捏造引用)       1  = 0.02%
     (twoder/temporal_event_schema.py は 79 行、line 80 を引用 — オフバイワン 1 件のみ)
スループット  2,341 out-tok/s / 1.35 req/s / 壁時計 178.5s
              (usage の primitives から導出。GPU util からではない — PROCESS-01)
```

引用行の**実在検証**まで機械的に通した。

#### 【インシデント I3】再現性ゲート不合格 — 散文は再現しない、行範囲は再現する

同一 25 ファイルを seed 7 と seed 101 で二重実行:

| 指標 | 値 |
|---|---|
| `lifecycle_signal` 一致（5 値カテゴリ、偶然 20%） | **64%** |
| `actual_capabilities` 内容語 Jaccard | **中央値 0.51 / 平均 0.53 / 最小 0.29** |
| **`evidence` 行範囲の重なり** | **中央値 0.83 / 平均 0.74** |

**Qwen は「ファイルのどこが重要か」は安定して特定するが、「それを何と呼ぶか」は毎回変わる。**

→ **設計変更（確定）: 散文を真理の単位にしない。引用行範囲を単位とし、散文はラベルとして扱う。**
→ **単一シードの抽出は Component / Edge 層の根拠として不採用とする。**

#### 3 シード合議（seed 7 / 23 / 47、`s2b_consensus.py`）

採用規則: **同一フィールド内で 2/3 以上のシードが重なる行範囲を引用した項目のみ採用**
（重なり ≥ 0.5）。非採用は `UNRESOLVED.jsonl` へ隔離（破棄しない）。

```
合議済みファイル   238   (3 シード成功 218 / 2 シード 20 / 1 シード 3=隔離)
採用項目         3,460
不採用           1,078   (候補の 23.8%)
```

フィールド別の生存率 — **そのフィールドがどれだけ客観的かの実測値になっている**:

| フィールド | 採用 | 不採用 | 生存率 |
|---|---|---|---|
| `actual_capabilities`（コードが実際にすること） | 1,142 | 121 | **90.4%** |
| `claimed_capabilities` | 492 | 109 | 81.9% |
| `failure_modes` | 563 | 127 | 81.6% |
| `side_effects` | 325 | 86 | 79.1% |
| `capability_gap`（主張と実装の乖離） | 326 | 178 | 64.7% |
| `limitations` | 309 | 201 | 60.6% |
| `authority_checks` | 303 | 256 | **54.2%** |

`lifecycle_signal` は 3 値多数決で 238 件中 220 件に多数派が成立（no-majority 18 件）。
ただしこれは LLM の判断であるため、Stage 3 で決定論的シグナル
（到達可能性 / 実行痕跡 / 最終更新日）と突合し、食い違いは `CONTRADICTIONS.jsonl` に送る。

#### 消費実績（暫定予算に対して）

```
本番 3 シード + 再現ゲート  = 4 回の全走査相当
prompt_tok   2,420,000 (概算)   completion_tok  1,291,000
壁時計       約 9 分
暫定予算     生成 2,000,000 tok / 1,800 s  → 生成 64.6% 消費、時間 30% 消費
```

---

### §3.4 — 2026-07-22 Stage 3 完了（**本作業で最大の構造所見**）

Stage 3 は当初 Qwen 25 並列を想定していたが、**LLM を使わずに完了した**。
コンポーネント境界は既存 SoR（`twoder/audit/ARTIFACT_REGISTRY.component_owner`）を
種として拡張し（R3 に従い新分類を発明しない）、ラダーは 5 つの機械的根拠から計算した。
LLM 由来は `capability_gap` の引用のみで、それも 3 シード合議済みのものに限る。

#### コンポーネント別ラダー（17 コンポーネント）

`D/I/W/E/P` = documented / implemented / wired / executed / proven。`?` = UNRESOLVED。

| component | files | LOC | wired | 実行シグナル | ラダー | gaps |
|---|---|---|---|---|---|---|
| TEST | 157 | 13,808 | 0 | 0 | `YY---` | 0 |
| TWODER | 81 | 10,141 | 32 | 2,341 | `YYYY-` | 103 |
| EGL_EXPERIMENT | 57 | 6,486 | 0 | 0 | `YY---` | 72 |
| EGL | 18 | 2,928 | 7 | 665 | `YYYY-` | 23 |
| OTHER | 23 | 2,237 | 0 | 0 | `YY---` | 34 |
| ARCHIVE_DOCS | 11 | 2,113 | 0 | 0 | `YY---` | 12 |
| DW | 13 | 1,727 | 7 | 117 | `YYYY-` | 21 |
| EGL_AUTONOMY | 12 | 1,603 | 0 | 0 | `YY---` | 20 |
| RRI | 18 | 1,033 | 16 | 1,632 | `YYYY-` | 26 |
| DW_EXPERIMENT | 27 | 792 | 0 | 0 | `-Y---` | 4 |
| UI | 1 | 731 | 1 | – | `YYY?-` | 1 |
| DS | 3 | 236 | 2 | 1,708 | `YYYY-` | 2 |
| OPERATOR / AUTHORITY / AUDIT | 各1 | 559 | 各1 | – | `YYY?-` | 4 |

**`proven` 列は全 17 コンポーネントで NO。** `COMPLETION_DEFINITION_REGISTRY.jsonl` は
実質空（1 行）であり、CDEF-2DER-v1 の規則を満たす束縛が 1 件も存在しない。
`PROJECT_GOAL.md §4` の「0/7 flags SET」と独立に整合する。

##### 判定の訂正（実装時に自ら修正）

初版は UI / OPERATOR / AUTHORITY / AUDIT の `executed` を **NO** としていた。これは誤りである。
これらは専用の実行シグナル名前空間を持たず、活動が `twoder_runs` 配下に記録されて
TWODER に帰属されるだけで、「動いていない証拠」は存在しない。
**`NO` は、そのコンポーネントのシグナル空間が走査で覆われている場合にのみ主張できる。**
覆われていない場合は `UNRESOLVED_NO_SIGNAL_NAMESPACE` とする。修正済み。

#### 【所見 F4】DONE 67 件のうち 30 件が「テストからしか呼ばれない」★最大の所見

`ROADMAP_REGISTRY` の 86 ITEM を命名規約でファイルに束縛した（44 件解決）。
その上で live entrypoint からの到達性を見た結果:

```
DONE と申告               67
  ├ 配線あり (live 到達)   13
  ├ 配線なし               30   ← ★
  └ ファイル束縛が未解決    24   (命名規約外。TR-2 の残タスク)
```

**配線なし 30 件の内訳は、ほぼ `IMPL-PLATFORM` 系 22 子項目 + `PARALLEL-OPS` 系 4 +
`TEMPORAL` 系 2 + `OFFRAMP-DEP-FLAG-REGISTRY` である。**

実測した依存の形:

```
twoder/end_to_end_acceptance_harness.py (217 LOC)
   imported_by: ['twoder/regression/test_end_to_end_acceptance_harness.py']   ← テストのみ
twoder/parallel_router.py
   imported_by: ['twoder/end_to_end_acceptance_harness.py', 'test_parallel_router.py']
twoder/economy_operator.py
   imported_by: ['twoder/end_to_end_acceptance_harness.py', 'test_economy_operator.py']
twoder/egl_integration.py
   imported_by: [4 modules すべて同じ島の中, 'test_egl_integration.py']
```

**閉じた輪になっている。** 子モジュール群 → `end_to_end_acceptance_harness` → その回帰テスト。
`submit.py` / `webui.py` / `operator.py` / `dw/dispatch.py` のいずれからも到達しない。

`DE-0287` は「acceptance harness proving 35/35 ACs against real shipped modules」と記録している。
**その 35/35 は真である。ただし証明対象は、live path に接続されていないモジュール群である。**

一次資料 `DE-0250`（2026-07-13, 28 子項目の一括発行）の裁定文:
> Issue the full Proposal-A child set now (**registration only**); implement Tier-0 first,
> one slice at a time under approval

**「registration only」と明記されている。** 30 件は仕様どおり登録されたが、
その後 ROADMAP 上で DONE に遷移し、配線工程は行われないまま残っている。
すなわち **ROADMAP の DONE は「モジュールが存在し単体テストが通る」を意味しており、
「live path に接続されている」は意味していない。**

> これは §3.2 の RRI 事例（configured but never entered）と**同じ族の第 2 例**である。
> 1 例目は「配線済みだが分岐に入らない」、2 例目は「実装済みだがテストからしか呼ばれない」。
> どちらも `implemented` と `wired` と `executed` を一語に潰すと消える。

#### 前段 DE 分析との整合

`PROJECT_GOAL.md §6` の DE ブロック分析では、DE-0201–0250 の帯が
**essential=YES ゼロ / PLANNING 50%** だった。本 Stage の実測（DE-0250 で発行された
子項目群が live path に未接続）は、その帯の性格を独立に裏づけている。

---

### §3.5 — 2026-07-22 Stage 4 完了（EDGE_INVENTORY / spec v0.2 適用）

spec を **v0.2** に改訂した（`STRUCTURAL_RECONSTRUCTION_SPEC_v0.2.md`）。
主な改訂は C1（辺 status に 2 状態追加）/ C2（否定の主張規則）/ C3（採用単位を行範囲へ）/
C4（陰性対照の義務化）/ C5（フィールド別信頼度）/ C6（Wave 改訂）/ C7（authority 記録）。

#### 辺の全体像

```
コンポーネント間 呼出辺   1,313   (生の呼出点 2,912)

    812  TEST_ONLY_ISLAND            61.8%
    362  IMPLEMENTED_UNWIRED         27.6%
    113  LIVE                         8.6%
     17  WIRED_EXECUTION_UNRESOLVED   1.3%
      9  WIRED_UNENTERED              0.7%
```

**コンポーネント間の辺のうち、live path 上にあるのは 8.6% にすぎない。**
89.4% はテスト島か、呼出元を持たない実装である。

#### 【所見 F5】`WIRED_UNENTERED` 検出器が RRI 事例を独立に再発見（TR-4 陽性対照 合格）

「呼出点を囲む `if` 条件が、同一関数の引数であって既定値が falsy」という条件を
**ファイル間へ伝播**させる検出器を実装した（v0.2 §B）。既知の答えを与えずに走らせた結果:

```
gate-propagated files: 9
  twoder/rri_formal.py            <- gated by ['twoder/submit.py']
  rri/rri/approved_rq_set.py      <- gated by ['twoder/rri_formal.py']
  rri/rri/iec.py                  <- gated by ['twoder/rri_formal.py']
  rri/rri/need_validation.py      <- gated by ['twoder/rri_formal.py']
  rri/rri/rdec.py                 <- gated by ['twoder/rri_formal.py']
  rri/rri/request_resolution.py   <- gated by ['twoder/rri_formal.py']
  rri/rri/research_axis.py        <- gated by ['twoder/rri_formal.py']
  rri/rri/resolved_intent.py      <- gated by ['twoder/rri_formal.py']
  rri/rri/rq_candidate.py         <- gated by ['twoder/rri_formal.py']
```

**§3.2 で `executed`（実行痕跡 0/337）から判明した事実を、静的解析だけで再導出した。**
`TWODER→RRI` の辺 21 本のうち 9 本が `LIVE` から `WIRED_UNENTERED` へ正しく移動した（LIVE 21→12）。

これは spec §7 の **TR-4（文書とコードの矛盾検出 / 陽性対照）の合格**にあたる。
既知の欠陥を再検出できないパイプラインは、未知の欠陥も検出できない（DE-0437）。

##### 実装中に踏んだバグ（記録）

初版の検出器は 0 件を返した。原因は、`submit.py`→`rri_formal.py` が**同一コンポーネント内**の
呼出であるため辺として列挙されず、ガードが 1 段上に位置していたこと。
ローカルな呼出点の検査だけでは足りず、**ゲートの推移的伝播**が必要だった。
（同一コンポーネント内の呼出も収集し、伝播計算にのみ用いる形へ修正。）

#### 【所見 F6】T-3 の欠損辺を機械的に確定

`PROJECT_GOAL.md §3` の欠損辺（① ITEM選択 → ② DWタスク生成）について、辺台帳から:

```
task_selector.select_next の呼出元:
  TEST_ONLY_ISLAND      twoder/regression/test_task_selector.py
  IMPLEMENTED_UNWIRED   twoder/experiments/task_selector_authority_v0.1/eval_harness.py
  → LIVE な呼出元は 0

dw.workcell.create_task の LIVE な呼出元 (全2件):
  LIVE   twoder/submit.py:408
  LIVE   twoder/experiment_candidate.py:116
  → いずれも task_selector を経由しない
```

**選択機構は存在し、タスク生成機構も存在し、両者を繋ぐ呼出が 1 本も無い。**
DE-0347 の記述（`create_task-from-selected_item` producer が ABSENT）を、
呼出グラフから独立に確認した。

**T-3（producer 仕様の導出）に必要な材料は揃った:**
接続すべきは `task_selector.select_next(...)` の結果を `dw.workcell.create_task(...)` へ渡す
1 本の producer であり、その呼出形は **`submit.py:408` が既に行っているもの**と同じである。
新規機構ではなく、既存の 2 つの呼出面を繋ぐ配線である。

#### 系統間の辺（主要 9 コンポーネント）

| 辺 | LIVE | WIRED_UNENTERED | TEST_ONLY | UNWIRED | EXEC不明 |
|---|---|---|---|---|---|
| TWODER → EGL | 25 | – | 1 | – | – |
| TWODER → DW | 19 | – | 1 | 2 | – |
| UI → DW | 18 | – | – | – | – |
| UI → TWODER | 17 | – | – | – | – |
| TWODER → RRI | **12** | **9** | – | – | – |
| TWODER → DS | 11 | – | – | – | – |
| TWODER → AUTHORITY | – | – | 6 | 1 | 9 |
| OPERATOR → DW / TWODER | 各4 | – | – | – | – |
| OPERATOR → AUTHORITY | – | – | – | – | 5 |
| DW → TWODER | 3 | – | – | – | – |

`AUTHORITY` 宛の辺が `WIRED_EXECUTION_UNRESOLVED`（計 17）なのは U11 のとおり、
authority の実行が専用シグナル名前空間を持たないためである。**`NO` とは書かない**（v0.2 §C）。

---

### §3.6 — 2026-07-22 Stage 5 完了（HISTORY_EVENTS / フェーズ分割）

Stage 5 も **LLM 不要で完了した**。歴史を作文させず、5 リポ 682 commit を機械抽出し、
**フェーズ境界を「系統間の依存が新しく生まれた commit」で定義**した（主観的な章立てをしない）。

各 commit について、変更ファイルの AST import 集合を親 commit と差分し、
新しく現れたクロスコンポーネント依存を「辺の誕生」として記録した。

```
history events        682
edge-birth commits    142
```

#### 【所見 F7】中核系統間の配線は 2026-07-15 で完全に停止している ★

producer / consumer をともに中核（DS / RRI / EGL / DW / TWODER / EGL_AUTONOMY）に
限った辺の誕生を日別に取ると:

| 日 | commits | 辺の誕生 | 性格 |
|---|---|---|---|
| 07-05〜07-07 | 105 | 36 | 各系の骨格 + 4 系ループ初回クローズ |
| 07-08〜07-10 | 51 | **1** | HBB / AFE 実験期 |
| **07-11〜07-15** | **409** | **103** | **2DER 本体の配線期** |
| 07-16〜07-22 | 117 | **0** | bridge / energization / 実配備 |

```
最後の中核系統間の辺の誕生 : 2026-07-15
それ以降の commit          : 117 / 682 = 17%
それ以降に生まれた中核辺    : 0
```

**07-15 以降、新しい系統間接続は 1 本も生まれていない。**

##### 誤読しないこと

これは「07-15 以降の作業が無価値だった」という意味では**ない**。
07-17〜07-21 の bridge / energization / 実配備は、`PROJECT_GOAL.md §6` の実測で
essential=YES が 23 件集中する荷重帯である。ただしそれらは
**すでに存在する継ぎ目（TWODER→DW / TWODER→EGL）の内側を深掘りする作業**であり、
新しい系統間接続を作る作業ではなかった。

→ **「系を繋ぐ」フェーズは 07-15 に終わり、以後は「繋いだ中を固める」フェーズに移っている。**
→ そして `PROJECT_GOAL.md §3` の欠損辺 ①→② は、その「繋ぐフェーズ」の中で
   一度も着手されないまま、フェーズが終わった。

#### 【所見 F8】ROADMAP 登録の集中と、辺の誕生の質

```
07-12  commits=146  DE=88  ITEM=69  edge-birth=22
07-13  commits=145  DE=69  ITEM=41  edge-birth=46   ← 全期間で最多
```

**2 日間で全 commit の 43%、ITEM 参照の 100%（110/110）が集中している。**
07-13 は辺の誕生も最多（46）だが、§3.4 の所見 F4 のとおり、この日に
`DE-0250` で一括発行された IMPL-PLATFORM 子項目群は、現在
**`TEST_ONLY_ISLAND` として測定される**。

> **辺の誕生数は、live path の成長を意味しない。**
> 07-13 に生まれた辺の多くは、受入ハーネスとテストの内側で閉じている。
> これは `PROJECT_GOAL.md §6` の DE ブロック分析（DE-0201–0250 で essential=YES ゼロ）と整合する。

#### JREV（独立監査）の分布

```
07-05  JREV=11   07-06  JREV=4    07-18  JREV=3   07-19  JREV=1   07-21  JREV=3
07-07 〜 07-17   JREV=0（11 日間）
```

JREV は**立ち上げ期と bridge 期の両端にのみ存在**し、本体の配線期（07-11〜07-15）には
1 件も走っていない。最も多くの辺が生まれた期間に、独立監査が入っていない。

---

### §3.7 — 2026-07-22 Stage 6 完了（矛盾監査・系譜分類）

spec v0.1 §6.1 は矛盾 7 種のうち 5 種を機械計算、2 種を LLM に回す設計だった。
v0.2 で 6 種目を機械側へ移した。**本 Stage で残る 1 種も機械化できた。**

| 元の想定 | 機械化した方法 |
|---|---|
| 同一コンポーネントの記述不一致（LLM 判断） | **3 シードの `purpose_1line` 変種間の類似度**で測る（`difflib` 比。判断ではなく計測） |
| 同一権限を複数 store が主張（LLM 判断） | ledger ファイルへの `file_writes` を書き手コンポーネント別に集計 |

→ **Stage 2 以降、LLM は 1 度も必要にならなかった。**
本パイプラインで Qwen を使ったのは Stage 2（ファイル単位の記述抽出）のみである。

#### 矛盾 182 件

| 件数 | 深刻度 | 種別 |
|---|---|---|
| 74 | MED | `TESTED_BUT_NOT_ON_LIVE_PATH` |
| **30** | **HIGH** | **`ROADMAP_DONE_BUT_NOT_WIRED`** |
| 24 | MED | `ROADMAP_DONE_UNVERIFIABLE`（束縛不能） |
| 21 | LOW | `LIVE_CODE_TESTED_ONLY_INDIRECTLY` |
| 17 | LOW | `CODE_WITH_NO_CALLER` |
| 6 | MED | `DOC_CLAIMS_FILE_THAT_DOES_NOT_EXIST` |
| **5** | **HIGH** | **`LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST`** |
| 5 | LOW | `DESCRIPTION_UNSTABLE_ACROSS_SEEDS` |

#### 【自己訂正】「テストが無い」の判定を作り直した

初版は「`test_<module>.py` というファイルが存在しない」を根拠に
`LIVE_CODE_WITHOUT_TEST` を **26 件** 立てた。**これは命名規約の代理指標であって、
テストされていないことの証拠ではない。**（例: `dw/workcell.py` のテストは
`test_dw_gate.py` 等の名前で存在する。）

許容できる判定は「**いかなるテストファイルからも import されていない**」である。
作り直した結果 **26 → 5 件**。偽の主張を 5 分の 1 に減らした。

真に live かつテストから一度も import されない 5 件:

```
dev-workcell/dw/executor.py      ← RUN_COMMAND 実行器。コマンドを実際に走らせる本体
rri/rri/admission_request.py
rri/rri/residual_update.py
twoder/gpu_inspection.py
twoder/reference_oracle.py
```

> §3.4 の `executed=NO` 誤判定、§3.5 の検出器 0 件バグに続き、
> **本 Stage でも「測っているつもりで別のものを測っていた」事例が出た。**
> 3 度とも、代理指標をそのまま結論にしていた点が共通している。

#### 過小検出の明示

`STORE_WRITTEN_BY_MULTIPLE_COMPONENTS` は **0 件**だが、これは
「複数の書き手を持つ store が無い」ことを意味しない。
`file_writes` のリテラル解決率が低いため、**この手法では見えない**だけである。
（DE-0447 は EGL core と emit_api の二重台帳を実際に調査している。）
**0 件を「問題なし」と読んではならない。**

#### 系譜分類（spec §5 の 6 分類）

| 系譜 | files | LOC |
|---|---|---|
| test | 157 | 13,808 |
| unwired_support | 85 | 10,241 |
| experimental_branch | 97 | 9,748 |
| **core_path** | **48** | **6,874** |
| historical_residue | 20 | 1,307 |
| observability | 8 | 1,052 |
| safety_support | 9 | 955 |
| migration_handoff | 3 | 929 |

**本線（core_path + safety_support + observability + migration_handoff）= 68 files / 9,810 LOC。
全 Python 44,914 LOC の 21.8%。**
残り 78.2% は test / 実験枝 / 未配線 support / 歴史的残渣である。

うち **safety_support は 955 LOC（2.1%）にすぎない。**
「監査システムを作っていた」という印象と、実際にライブで安全側に効いているコード量は
一致しない。監査の重量は、コードではなく **プロセス（DE 484 件・JREV・GA）側に載っている**。

---

### §3.8 — 2026-07-22 Stage 7 完了（TR-1..6 全合格 / **T-1 SATISFIED**）

#### 【所見 F9】DW ループの実行ファネル ★最も具体的な「機能の実態」

TR-5 の不合格を追った結果、**`dev-workcell/events.jsonl` の 674 レコードが
Stage 1e の走査で丸ごと不可視だった**ことが判明した。DW は `phase` / `role` を
キーに使っており、私の走査キー一覧に無かった。

> **キー一覧それ自体が計器である。スキーマ不一致は「活動なし」と見分けがつかない。**
> §3.3 I2（`guided_json` 黙殺）と同型の失敗である。

修正後に見えた、DW 状態機械の実行実績:

```
PROCESS_EVENT   224
CREATE          147   ← タスク生成
PLAN            140
GENERATE         90
AUDIT            40
REGENERATE       13
DISPOSE          16
BLOCK             2
UPPER_REVIEW      1
COMPLETE          1   ← 完了
```

**タスク 147 件が生成され、COMPLETE に到達したのは 1 件。**

各段の通過率: CREATE→PLAN 95% / PLAN→GENERATE 64% / GENERATE→AUDIT 44% /
AUDIT→DISPOSE 40% / **全体 147→1 = 0.7%**。

これは「動くかどうか」ではなく「**どれだけ最後まで通るか**」の実測であり、
本調査で得られた最も具体的な機能の実態である。
`PROJECT_GOAL.md §3` の欠損辺（①→②）が塞がっても、
このファネルが変わらなければループは回らない。

> 注: COMPLETE=1 は「1 回しか完走していない」ことの記録である。
> DISPOSE 16 件が正常終了を含む可能性は排除していない（DISPOSE の内訳は未解析。§4-U13）。

#### U10 を部分的に閉じた

`CHG → DE → ART → file` の provenance 連鎖を辿り、ITEM 束縛を **44/86 → 58/86** に改善。

```
naming+CHG_DE_ART  19    naming  39    UNBOUND  28
```

残り 28 件は ROADMAP に DE 参照が無く、命名規約にも当たらない。**明示的 UNRESOLVED** とする。

#### トレーサビリティ試験の結果

| 試験 | 結果 | 実測 |
|---|---|---|
| TR-1 任意の機能 → 実装/呼出元/テスト/台帳 | **PASS** | 20/20 |
| TR-2 任意の ITEM → コードと実行記録 | **PASS** | 86/86（解決 58 + 明示 UNRESOLVED 28） |
| TR-3 任意の edge → 状態を証拠付きで | **PASS** | 1,313/1,313 |
| TR-4 文書とコードの矛盾検出（陽性対照） | **PASS** | 3/3 |
| TR-5 リポをまたぐデータフロー追跡 | **PASS** | 6/6 |
| TR-6 別 seed で結論一致 | **PASS** | 3,460/3,460（未通過 1,078 は隔離） |

**→ spec §0 の終了条件 T-1（機械可読層 + TR 全合格）を満たした。**

#### 【自己訂正 2 件】どちらも「基準ではなく計器が壊れていた」

1. **TR-1 が 16/20 だった原因は、判定式の欠陥。** 落ちた 4 件は
   `ds/ds/__init__.py` 等の**定義を 1 つも持たないファイル**だった。
   定義ゼロは正しい答えであって追跡失敗ではない。判定式を修正（定義を持つファイルから抽出）。
2. **TR-5 が 5/6 だった原因は、走査キーの欠落**（上記 F9）。
   到達性 5 ファイルはすべて満たしており、欠けていたのは `dw_events` の実行痕跡だった。

**いずれも基準を下げずに計器を直して合格させた。** これで自己訂正は通算 5 件
（executed=NO 誤判定 / 検出器 0 件 / テスト有無の代理指標 / TR-1 判定式 / 走査キー欠落）。
5 件すべてに共通するのは、**代理指標をそのまま結論にしていた**ことである。

---

### §3.9 — 2026-07-22 Stage 8 完了（人間向け 4 本 / **T-2・T-3 SATISFIED** → パイプライン終了）

出力（すべて `egl/docs/`、機械可読層の値のみを引用し、新たな判断を足していない）:

| 文書 | 行数 | 役割 |
|---|---|---|
| `2DER_SYSTEM_RECONSTRUCTION.md` | 218 | 総括。5 状態ラダー・矛盾 182 件・終了条件・裁定 6 点 |
| `2DER_END_TO_END_WIRING_MAP.md` | 125 | live entrypoint から実行器までの 1 往復 + 戻り経路 |
| `2DER_MAINLINE_AND_BRANCHES.md` | 135 | 本線 1 本と支流の内訳、フェーズ分割、何を畳むかの材料 |
| `2DER_MISSING_EDGES.md` | 164 | 欠損辺 ①→② と **T-3 の producer 仕様**。07-12 版を SUPERSEDE |

**T-3 の中身（`2DER_MISSING_EDGES.md §1`）。** 新規機構ではなく既存 2 面の配線である:
`task_selector.select_next()` の勝者 → `dw.workcell.create_task()`。
参照実装は live path に既にある（`twoder/submit.py:408` / `twoder/experiment_candidate.py:116`）。
満たすべき制約 3 点（`execution_admission` の再計算 / `authority.POLICY` の
`DW_MACHINE_DISPATCH` 範囲判定 / 全フィールドが resolvable な 2DER id）は
すべて**既存コードから機械的に導出**した。仕様を発明していない。

**07-12 版との diff（§3.3 相当）で撤回された主張がある。** 旧 `MISSING_EDGES.md` の
記述のうち、実測と一致しないものを撤回として明示し、旧版で正しかったもの・
改善したものも分けて記録した。**上書きせず、差分として残している。**

#### 終了条件

| 条件 | 状態 | 根拠 |
|---|---|---|
| T-1 機械可読層 + TR-1..6 | ✅ SATISFIED | §3.8 |
| T-2 人間向け 4 本が機械可読層を引用 | ✅ SATISFIED | 本節の 4 本 |
| T-3 欠損辺 producer 仕様の導出 | ✅ SATISFIED | `2DER_MISSING_EDGES.md §1` |

**反・支流条項（spec §0）の自己評価: 失敗していない。** 地図で終わらず producer 仕様まで
到達した。ただし **配線そのものは行っていない**（DE-0347 の severance class が
`CANONICAL_AUTHORITY_CONFLICT_REQUIRES_TAKA_DECISION` のため、Taka 裁定なしに着手不可）。

#### 記録すべき整地 1 件

Stage 3 のスクリプト 2 本（`s3_components.py` / `s3b_item_ladder.py`）が
`egl/` 直下に置かれたまま Stage 4〜7 が進んでいた。他の全 Stage スクリプトは
`egl/structure/` にある。本節の時点で `structure/` へ移動した。
パスはすべて絶対指定のため再実行結果は不変。

#### 過剰主張の予防（本節が主張しないこと）

- **「2DER の全体像が判明した」とは言えない。** 呼出点の 43.2% は未解決のままである
  （動的 import / 関数テーブル経由）。4 本の文書はいずれも §限界節でこれを明記している。
- **「①→② を繋げば自律ループが回る」とは言えない。** 実行ファネルは
  CREATE 147 → COMPLETE 1 である。接続と歩留まりは別問題として扱うこと。
- **`DISPOSE 16` の内訳は未分解**（U13）。ファネルの解釈には追加分解が要る。

---

## §4. 未解決 / 既知の限界（UNRESOLVED）

### 【U7】静的到達性は動的ディスパッチを越えられない ★最重要（U1 の後継）

`rri_formal.py:STAGES` のような関数テーブル経由の間接呼び出し（`fn(candidates, x)`）は
AST では解決不能。コールサイトの **43.2% が未解決**（大半は組込み/標準ライブラリだが、
動的ディスパッチもここに含まれる）。

- **帰結: `wired` を symbol 単位で「否定」してはならない。** 到達しなかったことは、呼ばれないことを意味しない。
- **`wired` の肯定は静的に可能、否定は不可能。** 否定側の裁定者は `executed`（T2）のみである。
- Stage 4 の EDGE_INVENTORY では、`wired=no` を主張する辺には
  **必ず `executed` 側の根拠を併記する**こと（§3.2 の RRI 事例がその型）。

### 【U1】`wired` は現状「必要条件」であり十分条件ではない ★部分的に解消（§3.2）

**状態: 部分解消。** Stage 1d により symbol 単位の到達可能性を得た。ただし U7 により
symbol 到達性は「否定」の根拠に使えない。したがって当初の懸念（module 単位は上限値）は
symbol 単位でも解消していない — **`wired` は依然として上限値である。**
実質的な裁定は Stage 1e の `executed` 列が担う。以下は当初の記述（保存）。

Stage 1c の到達可能性は **module import 単位**である。
`A.py` が `B.py` を import していても、`B` の当該関数が実行経路で呼ばれる保証はない。

- 影響: 所見 F1 の 68 ファイルは **上限値**である。symbol 単位ではこれより小さくなりうる。
- 対策: Stage 1d（symbol 単位到達可能性）を Qwen 投入前に実施する。
  ここを甘くすると、その上に載る Component / Edge / 系譜のすべてが甘くなる。
- **現時点で「68 ファイルが稼働中」と主張してはならない。**「68 ファイルが到達可能」までが言えること。

### 【U2】`introduced_by_de` の解決率 57%

826 T1 ファイル中 473 件のみ、初出 commit のメッセージから DE を解決できた。
残り 353 件は `ARTIFACT_REGISTRY` / CHANGE_LOG との突合が必要（Stage 5）。

### 【U3】`egl/docs/SUBMIT_2026-07-21/` にコードの複製がある

`patch_bridge.py` / `bridge_reconciler.py` / `runner_v0.2.3.py` 等が出荷束の展開物として
docs 配下に存在する。現分類では `ARCHIVE_OR_EXPERIMENT`。
Stage 6 の重複検出（同一 sha256 / 近接内容）で正式に扱う。

### 【U4】`executed` 列 ✅ 解消（§3.2）

Stage 1e で 6 系統・4,944 レコードを走査、96 種の実行シグナルを抽出した（parse 失敗 0）。
残課題は「シグナル → コンポーネント/辺」への写像であり、Stage 3/4 で行う。

### 【U5】Taka 裁定待ち 4 点（spec §10）

1. `ARTIFACT_REGISTRY.used_by_live_path`（210 件中 198 件が `unknown`）への計算値書き戻しの可否
2. 生成物の置き場所を `egl/structure/` とすることの可否（第 6 リポを作らない判断）
3. TERMINAL 条件 T-3（欠損辺 producer 仕様の導出）を必須とすることの可否
4. 予算上限（Qwen 生成トークン / 壁時計時間）

### 【U6】本作業自身が支流化するリスク

spec §0 の反・支流条項を参照。地図の完成を成功としない。
T-3（`PROJECT_GOAL.md §3` の欠損辺 ①→② の producer 仕様導出）に到達しなければ失敗として記録する。

---

### 【U13】DW ファネルの各段の意味が未解析

`DISPOSE 16` が正常終了・中断・棄却のいずれを含むかは未分解。
`COMPLETE 1` を「完走 1 回」と読むのは正しいが、
「成功したタスクは 1 件だけ」と読むのは現時点では**過剰主張**である。
`payload` の中身を解析すれば分解できる（未実施）。

### 【U10】ITEM→ファイル束縛 ✅ 部分解消（§3.8、44→58/86）。残り 28 件は明示 UNRESOLVED

以下は当初の記述（保存）。

命名規約（`ITEM-...-FOO-BAR` → `twoder/foo_bar.py`）で解ける分のみ。
DONE 24 件が未束縛のまま（`EVO-0001..0009` など、機能名で命名された初期 ITEM 群）。
TR-2（任意の ITEM → コードと実行記録）の合格には、これらを
`CHANGE_LOG.jsonl` / DE の `affected_artifact_ids` から解決する必要がある。

### 【U11】`executed` 列がコンポーネント粒度では粗すぎる

実行シグナルの名前空間は DS / RRI / EGL / DW の 4 系統しかなく、
twoder 内部のモジュール別実行は区別できない。§3.4 で 4 コンポーネントが
`UNRESOLVED_NO_SIGNAL_NAMESPACE` になった。ファイル/関数粒度の `executed` を
得るには、トレースのキー名とモジュールの対応表が要る（Stage 4 で辺ごとに解く）。

### 【U12】本パイプラインは 2DER の authority 方針を経由していない

`twoder/authority.py:POLICY` は `USE_VLLM_INFERENCE`（:8005 への任意の接触）を
**REQUIRES_APPROVAL** と分類している。Stage 2 の Qwen 呼び出しは Claude のスクリプトから
直接行われ、このゲートを通っていない。Taka の口頭指示（Qwen 使用の提案・Stage 続行指示）は
あるが、**2DER の機構としての承認記録は残っていない**。記録として明示する。

### 【U8】LLM 由来フィールドの信頼度は一様でない（§3.3）

`authority_checks` 54.2% / `limitations` 60.6% / `capability_gap` 64.7% は生存率が低い。
Stage 3 以降でこれらを**単独の根拠にしてはならない**。特に `authority_checks` は
`twoder/authority.py` の決定論的解析で置き換えるべきである（LLM 判断を残さない）。

### 【U9】計器検証を各 Stage の入口に義務化する（I2 の一般化）

LLM を使う Stage は、本番投入前に**陰性対照**（要求した制約が無ければ絶対に出ない出力を
要求する試験）を通すこと。「期待どおりの出力が出た」は制約が効いた証拠にならない。

---

## §5. 次の一手

**本パイプラインは Stage 8 で終了条件 T-1/T-2/T-3 をすべて満たした（§3.9）。
これ以上 Stage を足さない。** 地図の精度を上げる作業は支流である（spec §0）。

次に打つ手は**本作業の外**にあり、いずれも Taka 裁定を要する:

1. **①→② の producer 1 本を実装する**（`2DER_MISSING_EDGES.md §1` の仕様どおり）。
   DE-0347 の severance class により裁定必須。
2. **実行ファネルの分解**（CREATE 147 → COMPLETE 1 / `DISPOSE 16` の内訳、U13）。
   ①→② を繋ぐ前にこちらを見るべきか、は判断事項。
3. **`ROADMAP.status = DONE` の定義**（裁定 6 点の 6）。実測では live 接続を意味しない。
4. 裁定 6 点の残り（`used_by_live_path` 書き戻し / `egl/structure/` 配置 /
   予算 / `:8005` 接触の authority gate）。

（以下は各 Stage 着手前に記した予定。実績は §3.x を参照。）

```
2DER_SYSTEM_RECONSTRUCTION.md
2DER_END_TO_END_WIRING_MAP.md
2DER_MAINLINE_AND_BRANCHES.md
2DER_MISSING_EDGES.md     ← 07-12 版を SUPERSEDE、diff 併記
```

終了条件の現況: **T-1 SATISFIED** / T-2 未 / **T-3 は §3.5 F6 で材料が揃った**（未文書化）。

（以下は Stage 4 着手前に記した予定。実績は §3.5。）
**Stage 4: EDGE_INVENTORY（中核成果物）**。

Stage 3 の所見 F4 により、辺の分類は以下を区別できなければならない:

| status | 意味 | §3 での実例 |
|---|---|---|
| `LIVE` | 呼ばれ、実行痕跡がある | DS→RRI→EGL→DW（117/117 トレース） |
| `WIRED_UNENTERED` | 呼び出しはあるが分岐に入らない | RRI formal（§3.2） |
| `TEST_ONLY_ISLAND` | テスト/受入ハーネスからのみ到達 | IMPL-PLATFORM 22 子項目（§3.4） |
| `IMPLEMENTED_UNWIRED` | 呼び出し元なし | — |
| `MISSING` | 実装が無い | ① ITEM選択 → ② DWタスク生成（T-3 の対象） |

`WIRED_UNENTERED` と `TEST_ONLY_ISLAND` は当初の決定表（spec §4.2）に無かった。
**実測から生じた分類であり、spec を v0.2 で改訂する必要がある。**

未決のまま進行中: §4 U5 の Taka 裁定 4 点。暫定予算は Claude が置いた値のまま
（生成 200 万 tok / 1,800 s、現在 64.6% / 30% 消費。Stage 3 は LLM 不使用）。

---

### §3.10 — 2026-07-22 台帳登記簿 LEDGER_REGISTRY（Taka: 台帳がシステムの根幹 / AI 痴呆対策）

Taka の見立て「このシステムの根幹的重要性を持つのは台帳で、大半の開発は何かしら台帳に紐づく。
目的・作った prog・いつ を追えば何をしたかったか分かる。特定部分の深掘りで全体を忘れる AI 痴呆が
起きても思い出せるよう、全台帳情報を持つのは正しい」を仕組みに落とした。

**成果物:**
- `egl/structure/s10_ledger_registry.py`（決定論・再生成可能・`--check` / `--apply`）
- `egl/structure/LEDGER_REGISTRY.jsonl`（47 台帳の登記簿本体）
- `egl/docs/2DER_LEDGER_REGISTRY.md`（人間向け）
- 典拠 `DE-0489`（**de_admission.py 経由で ADMITTED** — 手書き append をやめ登記簿の書き手規律を dogfood）

**各台帳について機械的に集めたもの:** genesis（初出 commit の日付・sha・件名・DE/CHG id）/
作っているプログラム（本番書き手を strict=パスへの write 確認・loose=参照+書込み の 2 層で検出、
本番/テスト分離）/ 読み手 / live path から読まれるか / git 追跡か / SoR 宣言 / 放置日数 / 行数。
**purpose は発明せず、genesis 件名と writer docstring を raw のまま載せる。**

**実測（47 台帳）:** LIVE 21（うち git 追跡外 **11**）/ IDLE_HAS_WRITER 8 / ORPHAN 7 /
複製・出荷影 11。`--check` は現在 **0 mismatch**。

**最重要の発見（前回 §メモリの延長）:** 運用の一次台帳ほど git 追跡外にある。
`egl/data/events.jsonl`(2001) / `ds/ds_events.jsonl`(1008) / `rri/rri_records.jsonl`(680) /
`dev-workcell/events.jsonl`(674) はすべて `.gitignore` 下だが LIVE。**消えれば実行史が消える。**
耐久性の担保は Taka 裁定事項（DE-0186 で意図的な runtime state 扱いだが、バックアップ/封印は未定義）。

**書き手規律の質は台帳ごとにバラバラで、それが健全性に直結していた:**
- `DESIGN_EVIDENCE_LEDGER` → `de_admission.py` 単一（"ONLY sanctioned writer", CONFIRMED）→ 484 件で重複 0
- `ROADMAP/CHANGE_LOG/ARTIFACT` → それぞれ単一 registry モジュール（CONFIRMED）
- `REVIEW_LEDGER` / `audit_backlog` → **本番書き手ゼロ**（手で埋める前提のまま放置）

**恒久機構としての位置づけ:** `--check` は「宣言 sole 書き手 vs 本番複数」「live 読みだが真の書き手ゼロ」を
決定論で検出する。これを coverage-sweep 系の常設ゲートに載せれば、実験のたびに台帳が 1 本生えても
（禁止せずに）登記漏れ・書き手不在として検出できる。**統合＝台帳を減らすことではなく、台帳を登記すること。**

**過剰主張しないこと:** 書き手検出は静的解析であり `~`（参照+書込みありパス未確認）は確定でない。
動的パス構築は取りこぼす。ORPHAN 7 の「畳む/保存」は判断材料であって判断ではない（Taka 裁定）。
