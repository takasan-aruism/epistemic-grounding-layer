# 「根拠(evidence)」がコードとして何をしているか ―― 全件調査（★実装0行）

作成: Claude Code (MGR) / 2026-08-25 / ITEM: `ITEM-2DER-EVO-0094`

## 1. ★語彙（閉じた列挙・`rri/rri/request_thread.py:264-270`）

```
EVIDENCE_BASIS_KINDS      9語  AI_INFERENCE / EXTERNAL_RESEARCH / EXTERNAL_SPECIFICATION /
                               LOCAL_CODE_OBSERVATION / LOCAL_MEASUREMENT / LOCAL_REPRODUCTION /
                               HUMAN_DECLARATION / MIXED_BASIS / UNRESOLVED
EVIDENCE_VALIDATION_MODES 6語  DECLARED / SPECIFIED / OBSERVED / MEASURED / REPRODUCED / UNRESOLVED
EVIDENCE_NEEDS_REF        5語  ★この basis を名乗るなら evidence_refs が要る(空なら ValueError)
```

## 2. ★書き手が「していること／していないこと」（逐語）

`record_evidence` の docstring 逐語：

> **これが すること＝ 既に在る証拠の id を明細に結ぶだけ。**
> **これが しないこと＝ 証拠を作らない ／ 中身を言い換えない ／ 新しい ID 体系を作らない。**

★**evidence は「証拠そのもの」ではなく「証拠への参照を明細に結ぶ行」**です。

**粒度は語ではなく形で分ける**（逐語）：
- `question_id` が在る → **その明細1件の根拠**
- `question_id` が `None` → **その依頼(thread)全体の根拠（明細まで絞れなかった）**

## 3. ★書き手 全4箇所（5repo走査・試験を除く）

| # | 場所 | 何を根拠にしているか | 粒度 |
|---|---|---|---|
| ① | `submit.py:546` | **人が hold へ返した回答**（`HUMAN_DECLARATION` / `DECLARED` / refs 空） | 依頼 |
| ② | `detail_feedback.py:98` | **走行の要約**（`run["event_id"]` = ETRACE の1件・`LOCAL_MEASUREMENT` / `MEASURED`） | 依頼 |
| ③ | `detail_feedback._attach_per_detail` | **試験1本の合否**（`test_name: PASSED/FAILED`） | **★明細** |
| ④ | `s_esde_evaluate.py:405/413` | **ESDE 評価の要約**（405=評価全体 / 413=finding 1件ごと） | 依頼＋明細 |

★**明細粒度を書けるのは ③ と ④ の finding だけ**。

## 4. ★★③ が明細へ降ろす条件（＝唯一の鍵）

`_attach_per_detail` は **`TEST_PROVENANCE` の宣言**だけを見ます。降りない場合の逐語：

```
"宣言が 無い(★推測で 明細へ 結ばない=依頼粒度の 1行が 受け持つ)"
"宣言は 在るが 1つも 明細に 解決できない"
"他の 試験が 落ちている 走行で この 試験の 合否は 名指しで 分からない ∴ 書かない"
```

★**推測で `question_id` を割り当てない**のが設計の中核です。

★出所も1つに固定されています（逐語）：**TRACE の `TEST_PROVENANCE` 欄ではなく `RAW_INPUT` をその場で読む**
―― 入口を再起動しないと欄が増えないため。**過去の依頼にもそのまま効く**作りです。

## 5. ★★実データ（351行 全件）

```
evidence 行 351
 ├─ ★明細粒度   ★5   （一意の明細 5）
 └─ 依頼粒度    346

書き手: MANAGER_V0.feedback_one 159 / MANAGER_V0.tick 80 /
        DOMAIN_LEDGER.w2_evidence 67 / ESDE_WORKER 33 / Claude Code (MGR) 5 /
        ESDE_PROBE 5 / TAKA 2
経路  : front_door 308 / direct 43

basis_kind      : LOCAL_MEASUREMENT 347 (98.9%) / LOCAL_CODE_OBSERVATION 2 / HUMAN_DECLARATION 2
validation_mode : MEASURED 314 / UNRESOLVED 33 / OBSERVED 2 / DECLARED 2
refs の接頭辞    : ETR- 309 / TASK- 38 / ART- 35   （refs が空の行 2）

evidence_text の形: 走行の要約など 315 / ESDE 評価の要約 33 / ★試験1本の合否 3
```

**書き手 × 粒度**（★明細粒度はここだけ）：

```
DOMAIN_LEDGER.w2_evidence   ★明細  3
Claude Code (MGR)           ★明細  2
（他は全て 依頼粒度）
```

★**ESDE の finding 経路（④の413行目）は実績0件** ―― `ESDE_WORKER` は依頼粒度33件のみ。

## 6. ★★天井 ―― 宣言の被覆は **0.5%**

```
TRACE(依頼文が在る) 1,473
 ├─ ★宣言が在る   ★7  (0.5%)   ← TASK-2DER-813D7F46 系 5 + BD10E532 ほか
 ├─ 宣言が無い    1,466 (99.5%)
 └─ 宣言が壊れている  0
```

★**宣言が無い 1,466 TASK は、どれだけ走らせても明細粒度に降りません**（推測で結ばない設計ゆえ）。
★∴ **「明細粒度 0.3%」はバグではなく、宣言が 0.5% しか無いことの写しです。**

## 7. ★降ろせた場合の上限

```
依頼粒度 346行 / thread 228本（1本あたり 最大25 / 中央1）
★その thread が持つ明細 合計 394（最小0 / 最大27 / 中央1）
★= 依頼粒度の根拠を明細へ降ろせれば ★最大 394 明細が根拠を持ち得る
```

★ただし**降ろす鍵が無い**（＝どの明細の試験かを決定論で引けない）ので、**降ろすには宣言が要ります**。

## 8. ★結論（★推測を足していない）

1. **evidence は「証拠を作る」機構ではなく「既に在る証拠 id を明細に結ぶ」機構**
2. **明細粒度に降りる道は `TEST_PROVENANCE` 宣言ただ1つ**
3. **宣言の被覆が 0.5%（7/1,473）** ∴ 明細粒度が 0.3% なのは**設計どおりの帰結**
4. **上限は 394 明細**（依頼粒度の根拠を持つ thread の明細総数）

## 9. ★やっていないこと

- **実装 0行**・**書き込み 0**
- 推測で `question_id` を割り当てて**いない**
- 宣言を**書き足していない**（依頼文側の変更は別の裁定）
