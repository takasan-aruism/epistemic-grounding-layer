# 2DER SYSTEM RECONSTRUCTION（総括 / 実測 2026-07-22）

- **目的:** 1,317 ファイル / 5 リポ / 484 DE / 682 commit から、2DER の実態を証拠付きで再構成する
- **status:** 機械可読層 = **T-1 SATISFIED**（TR-1..6 全合格）/ 本書 = T-2
- **spec:** `STRUCTURAL_RECONSTRUCTION_SPEC_v0.2.md` ／ **実行記録:** `STRUCTURAL_RECONSTRUCTION_PROGRESS.md`
- **claim ceiling:** 本書のすべての数値は `egl/structure/*.jsonl` の行に対応する。
  導出物であり SoR ではない。SoR と矛盾したら SoR が勝つ。

## 姉妹文書

| 文書 | 内容 |
|---|---|
| `2DER_END_TO_END_WIRING_MAP.md` | 実際の呼出グラフ（行番号つき） |
| `2DER_MAINLINE_AND_BRANCHES.md` | 本線 1 本と支流、フェーズ分割 |
| `2DER_MISSING_EDGES.md` | 欠けている辺（07-12 版を SUPERSEDE） |
| `PROJECT_GOAL.md` | 本線の再構成（開発史から） |

---

## §1. 一枚での答え

```
2DER の本線は「自律実行ループ」であり、監査機構ではない。
  典拠: 2DER_TECHNICAL_SPECIFICATION.md:5 (2026-07-10, Taka v0-direction authority)

ループは ② を除いて全部通っている。
  ① ITEM 選択 → ② DW タスク生成 → ③ 実行 → ④ 検証 → ⑤ EGL admission → ⑥ 閉じ → ①
                    ↑ここだけ無い

繋がっていないものの方が多い。
  Python 44,914 LOC のうち live path は 9,810 LOC (21.8%)
  コンポーネント間 1,313 辺のうち LIVE は 113 (8.6%)

そして、繋がっている部分の歩留まりは低い。
  DW タスク CREATE 147 → COMPLETE 1
```

---

## §2. 規模と分布

```
ファイル              1,317   (T1_TRACKED 826 / T2_RUNTIME 491)
Python                  427 files / 44,914 LOC / 定義 2,122
コンポーネント間の辺   1,313
DE                      484
commit                  682   (5 リポ, 2026-07-04 〜 07-22 = 18 日)
```

| 系譜 | LOC | 比率 |
|---|---|---|
| 本線（core + safety + observability + handoff） | 9,810 | **21.8%** |
| test | 13,808 | 30.7% |
| unwired_support | 10,241 | 22.8% |
| experimental_branch | 9,748 | 21.7% |
| historical_residue | 1,307 | 2.9% |

**ライブで安全側に効いているコード（safety_support）は 955 LOC = 2.1%。**
監査の重量はコードではなくプロセス（DE 484 件 / JREV / 承認ゲート）に載っている。

---

## §3. 5 状態ラダー — 本作業の中心的成果

2DER の混乱の最大原因は、`documented / implemented / wired / executed / proven` が
「ある / ない」の一語に潰れていることだった。本作業は 5 列を**別々の機械的根拠から計算**した。

| 状態 | 根拠源 |
|---|---|
| `documented` | md 内のシンボル参照索引 |
| `implemented` | Python AST の定義存在 |
| `wired` | live entrypoint 4 本からの到達可能性 |
| `executed` | T2_RUNTIME の実行痕跡のみ（4,944 レコード） |
| `proven` | `CDEF-2DER-v1`（Taka 承認, DE-0275）の規則をそのまま適用 |

### 一語に潰すと消える 2 つの状態（実測で発見）

**① `WIRED_UNENTERED` — 配線済みだが分岐に入らない**

```
ITEM-2DER-EVO-0002 (RRI formal validation)
  documented YES / implemented YES / wired YES / executed NO / proven NO
  submit.py:97  `if formal_candidates:`  既定は空
  RRI_FORMAL_VALIDATION = 0 / 337 トレース
```

**② `TEST_ONLY_ISLAND` — 実装済みだがテストからしか呼ばれない**

```
ROADMAP DONE 67 件のうち 30 件
  子モジュール → end_to_end_acceptance_harness → その回帰テスト、で閉じた輪
  DE-0287 の「35/35 ACs pass」は真。証明対象が live path 外なだけ
  DE-0250 の裁定文は「registration only」と明記していた
```

→ **`ROADMAP.status = DONE` は「モジュールが存在し単体テストが通る」を意味しており、
「live path に接続されている」を意味していない。**

### `proven` は全コンポーネントで NO

`COMPLETION_DEFINITION_REGISTRY.jsonl` は実質空（1 行）。
CDEF-2DER-v1 の規則（bound acceptance artifact + JREV verdict）を満たす束縛が 0 件。
`PROJECT_GOAL.md §4` の「0/7 flags SET」と独立に整合する。

---

## §4. 矛盾 182 件（全種機械計算）

| 件数 | 深刻度 | 種別 |
|---|---|---|
| 74 | MED | `TESTED_BUT_NOT_ON_LIVE_PATH` |
| **30** | **HIGH** | `ROADMAP_DONE_BUT_NOT_WIRED` |
| 24 | MED | `ROADMAP_DONE_UNVERIFIABLE`（ID 束縛不能） |
| 21 | LOW | `LIVE_CODE_TESTED_ONLY_INDIRECTLY` |
| 17 | LOW | `CODE_WITH_NO_CALLER` |
| 6 | MED | `DOC_CLAIMS_FILE_THAT_DOES_NOT_EXIST` |
| **5** | **HIGH** | `LIVE_CODE_NOT_IMPORTED_BY_ANY_TEST` |
| 5 | LOW | `DESCRIPTION_UNSTABLE_ACROSS_SEEDS` |

HIGH の 5 件（live かつ、いかなるテストからも import されない）:
```
dev-workcell/dw/executor.py   ← RUN_COMMAND 実行器。実際にコマンドを走らせる本体
rri/rri/admission_request.py
rri/rri/residual_update.py
twoder/gpu_inspection.py
twoder/reference_oracle.py
```

---

## §5. 方法（再現手順）

```bash
cd egl/structure
python3 s1_manifest.py       # FILE_MANIFEST     1,317
python3 s1_symbols.py        # SYMBOL_INDEX      1,215
python3 s1_reach.py          # REACHABILITY        427
python3 s1d_symgraph.py      # SYMBOL_REACHABILITY 2,122
python3 s1e_executed.py      # EXECUTION_EVIDENCE   96
python3 s2_extract.py 7 FILE_EXTRACTION.jsonl      # Qwen（唯一の LLM 工程）
python3 s2b_consensus.py     # 3 シード合議        238
python3 s3_components.py     # COMPONENT_INVENTORY  17
python3 s3b_item_ladder.py   # ITEM_LADDER          86
python3 s4_edges.py          # EDGE_INVENTORY    1,313
python3 s5_history.py        # HISTORY_EVENTS      682
python3 s6_contradictions.py # CONTRADICTIONS      182
python3 s7_traceability.py   # TR-1..6
```

**Stage 1 の全出力は再実行でバイト一致する（決定性検証済み）。**
LLM を使ったのは Stage 2（ファイル単位の記述抽出）のみ。
構造の判定（配線・到達性・5 状態・矛盾・系譜）はすべて決定論である。

### 設計原則（GPT 提案からの逸脱点）

| # | 原則 |
|---|---|
| R1 | **LLM に配線を主張させない。** `calls`/`called_by`/`reads`/`writes` は Qwen の入力であり出力ではない |
| R2 | 5 状態を判断させず、5 つの独立した機械的根拠から計算する |
| R3 | 機械可読層は DERIVED / regenerable。SoR にしない（DE-0447 の二重台帳を再生産しない） |
| C2 | **`NO` はシグナル空間が被覆されている場合のみ主張してよい** |
| C3 | LLM 出力の真理の単位は散文ではなく**引用行範囲**。3 シード合議を必須とする |
| C4 | LLM Stage の入口で**陰性対照**を義務化する |

---

## §6. 本作業自身の失敗記録（5 件）

**すべて「代理指標をそのまま結論にしていた」ことが原因である。**

| # | 失敗 | 症状 | 修正 |
|---|---|---|---|
| I1 | 導出物を走査対象に含めた | 1,317 → 1,318 で決定性が壊れた（DE-0132 同型） | `structure/*.jsonl` を除外 |
| I2 | **計器の対照が無効だった** | `guided_json` が黙殺される vLLM 上で 241 件を回し全破棄。OK 106 件もスキーマ非準拠 | 陰性対照で再検証 → `response_format/json_schema` |
| I3 | 単一シードを採用単位にしていた | 散文 Jaccard 0.51 / 行範囲 0.83 | 採用単位を行範囲へ。3 シード合議 |
| — | `executed=NO` の誤判定 | シグナル名前空間を持たない 4 コンポーネントを「動いていない」とした | `UNRESOLVED_NO_SIGNAL_NAMESPACE` |
| — | テスト有無を命名規約で判定 | 「無テスト」26 件と誤報 | import 関係で判定 → 5 件 |
| — | 走査キーの欠落 | `dev-workcell/events.jsonl` 674 件が丸ごと不可視 | `phase`/`role` を追加 → **ファネルが見えた** |

**I2 と最後の 1 件は同型である。計器（スキーマ強制／キー一覧）が効いていないとき、
出力は「正常」と見分けがつかない。**

---

## §7. 終了条件の現況

| 条件 | 状態 |
|---|---|
| **T-1** 機械可読層 + TR-1..6 全合格 | ✅ **SATISFIED** |
| **T-2** 人間向け 4 本、各主張が機械可読層を引用 | ✅ 本書で充足 |
| **T-3** 欠損辺 ①→② の producer 仕様が edge inventory から導出されている | ✅ `2DER_MISSING_EDGES.md §1` |

### 反・支流条項の自己評価

本作業は「地図を作って終わる」ことを成功としないと定めた（spec §0）。
T-3 に到達したため、**この条件では失敗していない**。
ただし **配線そのものは行っていない**。実装は Taka 裁定事項である。

---

## §8. Taka 裁定を要する 6 点

1. `ARTIFACT_REGISTRY.used_by_live_path`（210 件中 198 件 `unknown`）への計算値書き戻しの可否
2. 生成物の置き場所を `egl/structure/` とすることの可否
3. T-3 を必須条件とし続けるか
4. 予算上限（現在は Claude の暫定値: 生成 200 万 tok / 1,800 s。実消費 129 万 tok / 約 9 分）
5. 本パイプラインの `:8005` 接触を `authority.gate("USE_VLLM_INFERENCE")` 外で継続してよいか
6. **`ROADMAP.status = DONE` の定義。** 実測では live 接続を意味しない。
   定義を明文化するのか、DONE 30 件を降格するのか

## §9. 次に打つ手（本書の推奨）

**① → ② の producer 1 本。** 新規機構ではなく、既存 2 面の配線である
（`2DER_MISSING_EDGES.md §1`）。DE-0347 の severance class が
`CANONICAL_AUTHORITY_CONFLICT_REQUIRES_TAKA_DECISION` であるため、Taka 裁定なしには着手できない。

**ただし、繋いでも回るとは限らない。** CREATE 147 → COMPLETE 1 のファネルは
①→② とは別問題である。**接続と歩留まりを混同しないこと。**
