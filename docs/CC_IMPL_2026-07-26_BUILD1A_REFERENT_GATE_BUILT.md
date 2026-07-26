# 実装 → 設計/監査: Build 1a（P2 参照の前提）— N ゲート化 + AMB-REF-001 実装（BUILT）

- 宛: DESIGN/AUDIT（CC-α） / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-26 / TYPE=BUILT / スライス=**1a のみ**（1b/1c 未着手・指標は混ぜていない）
- 実装源: `CC_DESIGN_2026-07-26_BUILD1_SPEC_AMBIGUITY_STAGE.md`（v1.0・★実装源）
- 表記規約は SPEC §0 に従う。**【監査】=私が一次情報で検証 /【設計】=未測定の提案 /【伝聞】=他者報告で私は未検証**

## 0. 読了申告（SPEC §11-4 / CORRECTION §4 の依頼）
実読した: **BUILD_SPEC v1.0**（実装源）/ `..._BUILD1_CORRECTION_TO_IMPL_STATUS`（§1 訂正・§2 配線1点の許可・§3 落とし穴）/ `..._AMBIGUITY_STAGE_BUILD1_HANDOFF` / `..._BUILD1_P1P4_ADDENDUM_HANDOFF` / `..._RECOGNITION_RESOLVER_ARCHITECTURE_v0_2`。
- **正直に**: `..._AB_COMPARISON_FINDING` の **§3b は直接読んでいない**。その内容は CORRECTION §1 と BUILD SPEC §6 の再掲で受け取った。**「25.1%」は撤回済みであり本書のどこにも成果として書いていない**。(A) 不採用の理由は「過剰発火」ではなく **「我々の失敗を 0/3 で捕まえないこと」**と理解している。
- **数値はすべて dedup 済み**（後述）。

## 1. 作ったもの（3 repo・SPEC は rri のみ想定だったので★注意）
| repo | ファイル | 内容 |
|---|---|---|
| `rri` | `rri/preflight_gate.py`（改修） | 単一ゲート → **ゲート表**。`detect(..., context=None)` 新設。`next_legal_operation()` 追加 |
| `rri` | `rri/ambiguity_patterns.jsonl`（新規） | `AMB-REF-001` 1行。様式は (A) から移植・**データは移植せず** |
| `twoder` | `submit.py`（**許可済み1点変更**） | `NEXT_LEGAL_OPERATION` を `pg` 由来に |
| `egl` | `structure/s_ambiguity_stage_build1.py`（新規） | 測定ハーネス（`--check` 実装） |
| `egl` | `structure/AMBIGUITY_STAGE_BUILD1.jsonl`（新規） | 測定結果台帳 |

**★ SPEC §11-7 は「`rri` を触るので rri 単体で commit + push」だが、実際は `rri` / `twoder` / `egl` の 3 repo に跨る。** 各 repo 個別に commit + push が必要（[[2der_repo_topology]]）。**commit=Taka。**

## 2. 既存 LIVE の非回帰（★SPEC §11-2 最優先）— 【監査】GREEN
- `twoder/regression/test_preflight_gate.py`: **13/13 PASS**（改修前と同数・同項目。submit.py 変更後に再実行して再確認）。
- 5決定すべて従来どおり: `CLARIFY_FIRST` / `STRONGLY_DISCOURAGE_DW` / `ALLOW_WITH_WARNING` / `ALLOW`(clear source) / `ALLOW`(abstract)。
- **非発火時の戻り値の形も不変**: どのゲートも triggered しない場合、**quant ゲートの ALLOW 結果をそのまま返す**設計にしたので、`gate_id` も `signals["clear_source_present"]` も従来と同じ（テスト3/5が依存している）。
- **`NEXT_LEGAL_OPERATION` の quant 文面は逐語一致**をハーネスで assert（`next_legal_operation_verbatim: True`）。

### 許可済み1点変更の diff（SPEC §4 例外1点・条件「diff を貼る」）
```diff
-        _rec("NEXT_LEGAL_OPERATION",
-             "%s (gate %s): ambiguous quantitative claim — concrete number + vague/missing source. RRI holds "
-             "before DW/acquisition; provide a clear source (author/title/venue/url) to proceed. proposed EGL "
-             "status=%s" % (pg["decision"], pg["gate_id"], pg["proposed_egl_status"]))
+        _rec("NEXT_LEGAL_OPERATION", PG.next_legal_operation(pg))   # Build 1a: 文面は gate 由来(quant は従来文を逐語保持)
```
- quant ゲートの文面は `next_legal_operation()` 内に**逐語で保持**（移動しただけ・生成していない）。
- 新ゲートの文面は **`clarification_slots` から構成**（捏造していない）。呼び出し契約（引数・戻り値のキー）は不変。

## 3. 測定（★すべて dedup 済み・1a のみ）
コーパスは独立に再現した【監査】: `ds/ds_events.jsonl` の `record_type=UTTERANCE` ∧ `speaker=USER` = **478** → `開発エビデンスを登録` 始まり **19件除外** → 459 → **dedup → ユニーク298件**。CC-α の正典値と一致。テキスト欄は `raw_text`。

| 指標 | 結果 |
|---|---|
| **M1 捕捉** | IP1 / IP2 / IP3 いずれも `triggered=True` = **3/3** |
| **M2 自己解決の非発火** | BV3「この設計案の得失は？」= **非発火** |
| **M3 誤発火率** | **0/298 = 0.00%**（dedup 済） |
| **M4 既存ゲート非回帰** | **GREEN**（上記 §2） |
| **M5 束縛先 AND** | context を与えると IP1/IP2/IP3 が**発火しなくなる**・空白のみの context では発火 = AND が効いている |
| `--check` | **GREEN**（スキーマ検証 / 抑制カウンタ決定論 5/5 / 2回走らせて直列化完全一致 / 非回帰 / fixture） |

D1/D2/D3・BV1・CH1・PP1/PP2/PP3 も**非発火**（PP系は P4=1c の領域なので 1a では撃たないのが正）。

### ★★3-1. この 0.00% を規則の手柄にしてはいけない（分解した結果）
**指標を分解したところ、M3 の 0.00% は BIND-RULE-001（束縛先の有無）の成果ではない。**

- ユニーク298件のうち、**`あれ` / `それ` / `例のやつ` を文中のどこかに含む発話は 0件**。
- ゆえに **SURF-RULE-001 の時点で 0件**であり、**束縛先条件は corpus 上で1件も判定していない（落とした件数 = 0）。**
- ＝ **「表層のみ 2.0% → 裸の指示語 0.0%」という改善は、私の実装した3語では再現しない。** 私の3語では両方 0.0% で、**AND 条件は実データで一度も検証されていない**。効いているのは fixture 上だけ（M5）。

**帰属**: M3 = 0.00% は「規則が賢い」証拠ではなく「**この3語が我々の実発話に出てこない**」という事実。**過剰発火しないことは示せたが、束縛先条件が有効であることは実データでは示せていない。**

### 3-2. M1 = 3/3 の射程（自己申告）
IP1/IP2/IP3 は **AMB-REF-001 を起こす根拠にした当の3文**。決定論で確実に捕まるのは設計どおりだが、**一般化の証拠にはならない**（3語の完全一致で撃っているため）。**意図調べで 0〜1/3 だったものが手前で 3/3 になった**のは事実だが、それは「LLM に当てさせるのをやめた」効果であって「規則が広く効く」ことの証明ではない。

## 4. ★確認したい点（DESIGN へ・私の側の数値が合わない）
**SPEC §7 の表「指示語の表層一致のみ = 2.0% (6/298)」を再現できませんでした。**
- 私の3語（`あれ`/`それ`/`例のやつ`）: **0/298**。
- 表層集合を広げて（`これ`/`例の件`/`前の件`/`この件`/`その件`/`あの件`/`さっきの`/`先ほどの`）測っても **2/298**。当たった2件は SPEC §7 が例示している **`前の件を優先して進めて`** と **`前の件のQwenとCoderの切替タスクをそのまま進めて`** そのものです。
- ＝ **6件を出した表層集合が分かりません。** どちらが正しいかを断定しません（私の集合が狭い可能性が高い）。**6/298 を出した際の指示語リストを教えてください。**
- **これは設計判断に効きます**: 対象が `前の件` 型まで含むなら、束縛先条件は実データで意味を持ち（2件を文脈で救える）、私の実装は**狭すぎ**ます。3語だけなら束縛先条件は当面 fixture 専用の機構です。
- SPEC §12「証拠のないパターンを増やさない」に従い、**表層集合の拡張は提案のみで実装していません**。

## 5. ★既知の落とし穴（SPEC §7 の明記義務）
- **【監査】`twoder/submit.py` 3d 段は `PG.detect()` に `context` を渡していない**（実読して確認・引数を足しただけで呼び出し側は未変更）。
- ＝ **実 front door では常に「束縛先なし」判定**になる。fixture 試験（context 明示）と挙動が変わる。
- **「front door からの context 配線は未実装」。「動いた」とは書かない。** 配線は Build 2。
- なお `ds_events.jsonl` の UTTERANCE には **`preceding_utterance_ref` フィールドが既にある**【監査】。Build 2 の context 配線の材料になり得る（未使用・提案のみ）。

## 6. 私が決めた定数（★DESIGN の確認が要る・spec に指定が無かった箇所）
1. **`AUTO_SUPPRESS_IGNORED_THRESHOLD = 3`** — 「無視され続けた警告を自動抑制」の閾値。SPEC に数値指定が無いので私が置いた。規則: `suppressed=True` **または**（`ignored_warning_count >= 3` **かつ** `accepted_warning_count == 0`）。**一度でも採用された警告は抑制しない。** `detect()` は純関数でカウンタを書き戻さない（更新は別経路）。
2. **BIND-RULE-001 の名詞句判定**: `DE-\d+` / 漢字2字以上 / カタカナ3字以上 / 英数3字以上、ストップワード `直前・文脈・会話・上記・以下・今回・前回` を除外。**凝った照応解析はしない（thin）** の指示に沿った最小規則。パターン DB に文字列で記録済み＝後から反証可能。
3. **段の順序**: 段で `triggered` した入力は 3d 段で `return TRACE` となり**意図調べに到達しない＝両方は走らない**（既存 preflight の挙動をそのまま継承）。SPEC 統合元 handoff §5.5 の「どちらにしたか記録せよ」への回答。

## 7. 未着手（宣言）
- **1b（P3 文脈の前提）**: 未着手。`CONTEXT_RESOLVE` の候補除外は意図調べ側（`s_intent_role_split_d2p2.py`）の改修＋ :8005 での再測定が要るため、1a とは別に出す。
- **1c（P4 存在の前提 + `SUPERSEDE`）**: 未着手。
- **P1**: 触っていない（非回帰確認のみ）。

---
*IMPL BUILT（1a のみ）。非回帰 13/13 GREEN・`--check` GREEN・捕捉 3/3・誤発火 0/298（dedup 済）。ただし **0.00% は束縛先条件の成果ではなく、3語が実発話に出てこないだけ**であり AND 条件は実データ未検証。§4 の 6/298 の出所を確認したい。context 未配線。commit=Taka・3 repo 個別 push が必要。*
