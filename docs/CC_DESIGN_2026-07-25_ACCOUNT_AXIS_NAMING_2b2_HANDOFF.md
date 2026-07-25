# 設計/監査 → 実装: 勘定科目の命名（2b-2）spec HANDOFF

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / CPU e5 pin は不使用（命名は content テキストのみ）
- 正本: `CC_MGR_2026-07-25_ACCOUNT_AXIS_NAMING_2b2_HANDOFF.md`（方式=LLM 3-seed consensus・:8005 開放）+ 本 handoff
- **:8005 使用可**（Taka が USE_VLLM_INFERENCE 開放）。model=**Qwen3.6-35B-A3B(:8005)**。**初の実 CALL_SITE**。
- 位置づけ: ★3 本線。scope = **v2 凍結棚2つのみ**（AX-72ead44e / AX2-48354b9a）。RESIDUAL/未凍結候補は命名しない。

## 0. 絶対規律
- **id が正典・name は装飾（後で変えられる）。命名で凍結メンバーシップ/軸幾何を一切変えない**（`ACCOUNT_AXES_v2.json` / `ACCOUNT_MEMBERSHIP_v2.jsonl` は **byte 不変**）。
- **measure-first・捏造ゼロ**: consensus 未成立は `UNRESOLVED_NO_CONSENSUS`（無理に付けない）。
- LLM 出力は揺れ許容（name テキスト）。**構造（対象軸・サンプル選択・consensus 判定）は決定論**（[[llm_arithmetic_drift_tolerant_design]]）。

## 1. 命名は別 versioned 台帳（v2 幾何を触らない）
- **`structure/ACCOUNT_AXIS_NAMES.jsonl`**（新・sole-writer=命名 stage）に axis_id 参照で name を記録。**凍結 artifact(v2) に name フィールドを足さない**理由=「name は後で変えられる装飾／v2 は不変」を byte で担保（frozen file を可変 name で汚さない）。
- 1 行 = provenance 込み（§4）。

## 2. 決定論サンプリング（LLM 前・固定）
- 各 v2 凍結軸について `ACCOUNT_MEMBERSHIP_v2.jsonl` から**その軸に所属する要素**を取得。
- **代表サンプル**: `margin_over_null`（その軸への density − null）**降順**、tie-break=`element_id` 昇順 で **上位 K=12**（`min(12, n_members)`）。＝最も軸中心に近い代表。
- 各サンプルの**実 content**を抽出（REQUEST=`content.raw_input`、INTENT=`content.resolved`）。サンプル `element_id` 群を記録（再現可能）。

## 3. LLM 3-seed consensus（:8005・非決定論部はここだけ）
- prompt（固定・記録）: 「以下は同一カテゴリに分類された依頼群です。このまとまりを表す簡潔なカテゴリ名（日本語・10〜15文字・体言止め）を1つだけ出力。名前のみ、説明不要。」+ サンプル content（番号付き）。
- **seed = 0,1,2 の3回**実行（seed 固定・temperature 固定・記録）。各 seed の提案名を取得。
- **正規化**（比較用・決定論）: 前後空白除去・全角/半角統一・句読点除去。
- **consensus**: 正規化名が **≥2/3 一致 → その名を採用**（採用名は最頻の原表記）。一致無し → `UNRESOLVED_NO_CONSENSUS`。

## 4. provenance schema（`ACCOUNT_AXIS_NAMES.jsonl` 1 行）
```json
{"axis_id":"AX2-48354b9a","axes_version":"v2","name":"<採用名 or null>",
 "name_status":"CONSENSUS|UNRESOLVED_NO_CONSENSUS",
 "model":"Qwen3.6-35B-A3B","endpoint":":8005",
 "seeds":[0,1,2],"proposals":{"0":"...","1":"...","2":"..."},
 "agreement_count":2,"sample_element_ids":[...],"prompt_id":"axis-name-v1","sampled_k":12}
```

## 5. LLM_INVOCATIONS（初の実 CALL_SITE）
- 命名 stage の :8005 呼出を **真の CALL_SITE として LLM_INVOCATIONS に登録**（MENTION_ONLY でなく）。DE-0536 の hook/`regen_meta` が commit 境界で fold（手動不要）。

## 6. ゲート `structure/s_account_axis_names.py --check`
- **幾何不変（最重要）**: `ACCOUNT_AXES_v2.json` / `ACCOUNT_MEMBERSHIP_v2.jsonl` が byte 不変（命名で変わったら RED）。
- **サンプル決定論**: 固定 K・固定ソートで sample_element_ids が再現（LLM 無しで検証可）。
- **consensus 判定の正当性**: 記録された `proposals` に §3 の ≥2/3 規則を適用した結果が `name`/`name_status` と一致（**LLM を再実行せず**、記録済み proposals に対し決定論再判定）。
- **provenance 完全性**: model/seeds/sample_ids/proposals/agreement を全行記録。UNRESOLVED は name=null。
- ※ LLM 出力は非決定論ゆえ **name テキストの byte 再現は要求しない**。--check は「決定論の封筒＋記録の完全性」を検証（naming は record-occurrence 型）。

## 7. 受入（設計が独立再検証）
- v2 幾何/membership byte 不変（命名が geometry を触っていない）。
- sample_element_ids が決定論再現・consensus 規則が記録 proposals に正しく適用・UNRESOLVED は正直に null。
- `ACCOUNT_AXIS_NAMES.jsonl` sole-writer 分離・LLM_INVOCATIONS に実 CALL_SITE 登録・全 --check GREEN。
- 命名結果（2棚の name か UNRESOLVED）を BUILT に明記 → 設計/MGR が妥当性を見る（"本物の話題名か塊か"の最終判断が要れば MGR 経由で Taka）。

## 8. 完了後
- `CC_IMPL_2026-07-25_ACCOUNT_AXIS_NAMING_2b2_BUILT.md`（宛 AUDIT/DESIGN）→ 設計独立再監査 → commit=Taka → DE。
- 想定と実測がズレたら silently 合わせず記録（consensus 不成立も正当な結果）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。id正典・name装飾・幾何不変・consensus未成立はUNRESOLVED。★3 本線＝これ自体。*
