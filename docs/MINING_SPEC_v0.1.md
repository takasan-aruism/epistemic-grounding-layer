# MINING_SPEC v0.1 — chart of accounts の決定論マイニング(2b-1: 安定性測定先行)

> **RTHREAD stage 2b。** 実 chart(account ラベル集合)を **DE ledger + rri_records から決定論クラスタリング**で出す。
> 初版が最も戒める「account を発明しない」の本体。起草: 設計/監査(CC-α)/ 正本: `RRI_SPEC_MACHINE_v1_1.json` chart_of_accounts.mining_spec_order。
> **LLM 不使用・決定論・byte一致再生成**(クラスタ命名の LLM は 2b-2 の別スライス、安定クラスタが在る時のみ)。

## §0. grounding(実測 2026-07-24・設計を左右する現実)
初版が挙げる決定論素性は、実データでは**強弱が大きく偏る**:
- **強い信号=ID 共起**: DE 全文の ID 参照 1346本(平均 2.6/DE)。※`relates_to` 構造化フィールドは 429/517 が空 → **全文正規表現(`(DE|RREQ|RINT|RSIG|UTT|DEV|ADM)-\d+`)で共起グラフを作る**(relates_to だけに頼らない)。
- **中**: DE band(claimed_status: OBSERVED196/IMPLEMENTED128/None175)。
- **弱い/退化**: repos touched(affected_artifact_ids の大半が repo 非解決=OTHER307)、request_type(rri INTENT.resolved は DW_IMPLEMENTATION153 が支配 + ユニーク末尾)。→ **含めるが低重み、支配させない**。
- **含意(正直に)**: クラスタは実質 ID 共起グラフに支配されうる。**「安定 chart が出ない」は失敗でなく正当な結論**(初版 rejected_alternative=「想像で account を捏造」の回避)。よって v0.1 は **chart 生成でなく『安定構造が在るかの測定』を第一目的**にする。

## §1. 決定論素性抽出(machine・free text は素性にしない)
各レコード(DE 517 + rri REQUEST/INTENT 対)から素性ベクトル:
- `cooc`: 参照 ID 集合(全文正規表現)。**主構造=共起グラフ**(node=record, edge=共有 ID 参照, weight=共有数)。
- `band`: claimed_status を {OBSERVED, IMPLEMENTED, LIVE/MEASURED, PROPOSED/PROVISIONAL, NONE, OTHER} に写像(離散)。
- `req_type`: rri INTENT.resolved の先頭トークン(DW_IMPLEMENTATION/WEB_RESEARCH/… / UNRESOLVED)。低重み。
- `blockage`: rri RESEARCH_SIGNAL の {research_required, acquisition_needed}(bool 対)。
- `repos`: affected_artifact_ids の repo prefix(解決時のみ、多くは欠損=UNRESOLVED)。低重み。
- **prose/memo/title/observation 本文は素性にしない**(初版: Jaccard 0.51 = ノイズ)。

## §2. クラスタリング(決定論・seed 付き)
- 素性ベクトルを固定エンコード(離散 one-hot + cooc グラフ隣接)。
- **k-means を固定 seed 集合 S={0,1,2,3,4} で実行**、各 seed は決定論(seed 由来の初期化 + 辞書順 tie-breaking)。K は {4,6,8,10} を走査し安定性最大の K を記録(K も勝手に決めない=測る)。
- 出力 `egl/structure/ACCOUNT_CHART_CANDIDATE.jsonl`: 各クラスタ = {cluster_id: `ACCT-<8hex>`(メンバ集合の決定論ハッシュ), members[], top_features[], **name: null**(命名は 2b-2)}。
- 加えて `ACCOUNT_CHART_STABILITY.json`: cross-seed agreement / negative-control agreement / 採用 K。

## §3. 受入(初版 acceptance の3条件・負の制御が load-bearing の核)
1. **byte一致再生成**(G-T3): 同一 seed・同一入力 → ACCOUNT_CHART_CANDIDATE.jsonl が byte 一致。
2. **負の制御(vacuous 検出=最重要)**: 入力素性をレコード間で固定 seed shuffle した「ノイズ入力」でクラスタリングし、**cross-seed agreement が実データより有意に低い(chance 水準へ崩れる)**ことを実測。**崩れなければ miner は vacuous**(ノイズに自信)→ RED。
3. **cross-seed agreement を測定・記録**: 実データの seed 間クラスタ一致度(best-match overlap / Rand 様指標)を数値で記録。
4. **判定(正直な出口)**: 実 agreement が負の制御を**明確に上回る**時のみ「安定 chart 候補あり」。上回らなければ **`chart_status = NO_STABLE_STRUCTURE`** を記録し **chart を捏造しない**(=正当な結論、2b-2 の LLM 命名に進まない)。

## §4. スコープ
- v0.1 = **2b-1 決定論クラスタリング + 安定性測定のみ**(LLM 不使用)。命名(2b-2, 3-seed consensus :8005)は**安定クラスタが在る時のみ**着手。
- account を UNCLASSIFIED 配下の sub-label として出す昇格規律(T22/T23)は 2c。
- **prose を素性にしない / 想像で account を作らない / NO_STABLE_STRUCTURE を失敗としない。**

## §5. 完了後
- `CC_IMPL_..._MINING_SPEC_BUILT.md` → 設計側が再監査(byte一致 + 負の制御が load-bearing + agreement 記録 + NO_STABLE 時の非捏造)→ CONSISTENT → commit=Taka → DE 起票。
- 結果が NO_STABLE_STRUCTURE なら、それ自体を DE 化(「決定論素性では chart が出ない」= stage2 の chart 前提への重要 finding、Taka 裁定候補)。
