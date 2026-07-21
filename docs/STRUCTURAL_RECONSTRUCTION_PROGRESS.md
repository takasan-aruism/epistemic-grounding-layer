# 2DER 構造再構成 — 進行レポート（追記式）

- **status: IN_PROGRESS**（living document）
- **spec:** `docs/STRUCTURAL_RECONSTRUCTION_SPEC_v0.1.md`
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
| 2 | file-level extraction | Qwen 30並列 | ⬜ 未着手 |
| 2b | 再現性ゲート（10% 二重実行） | Qwen | ⬜ 未着手 |
| 3 | COMPONENT_INVENTORY | Qwen 25並列 | ⬜ 未着手 |
| 4 | EDGE_INVENTORY（中核） | Qwen + 決定論 | ⬜ 未着手 |
| 5 | HISTORY_EVENTS / フェーズ分割 | 決定論 + Qwen | ⬜ 未着手 |
| 6 | 統合・矛盾監査・系譜監査 | Qwen 3–5 + Claude | ⬜ 未着手 |
| 7 | TR-1..6 トレーサビリティ試験 | 決定論 | ⬜ 未着手 |

**LLM はまだ 1 トークンも使っていない。** 現時点の全数値は決定論的計算であり、再実行でバイト一致する。

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

生成スクリプト: `s1_manifest.py` / `s1_symbols.py` / `s1_reach.py` / `s1d_symgraph.py` / `s1e_executed.py`

未生成: `COMPONENT_INVENTORY` / `EDGE_INVENTORY` / `CLAIM_EVIDENCE_INDEX` / `HISTORY_EVENTS` / `CONTRADICTIONS` / `UNRESOLVED`

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

## §5. 次の一手

**Stage 2: file-level extraction（Qwen 30 並列）**。決定論層は出揃った。

投入前の確認事項:
- Qwen へ渡す `ast_facts` は SYMBOL_INDEX + SYMBOL_REACHABILITY から構成する（spec §3.1）。
- **配線の判定を Qwen にさせない**（spec §1.1 / §3.3 禁止事項 5）。U7 により、
  静的到達性ですら否定に使えない。LLM なら尚更である。
- 再現性ゲート（10% を seed 違いで二重実行）を同時に走らせる。

未決のまま進行中: §4 U5 の Taka 裁定 4 点。
