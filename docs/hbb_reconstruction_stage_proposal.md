# HBB / 2DER roadmap 更新案 — reconstruction stage を独立機能として扱う

**status: `PROPOSAL — AWAITING_TAKA`(未実装。Taka の go 待ち。勝手に実装へ進まない。自律RD は未有効。self-improvement claim なし。)**
Refs: DE-0114 / `measurement_instruments_3.json` (DETECTION_RECONSTRUCTION_SPLIT) / `HBB_GPT_v2_report.md` / `docs/hbb_sealed_report.md` GPT 節.

## 1. なぜ(根拠)

GPT rubric-v2(DETECTION / RECONSTRUCTION の 2 独立軸、3 番目の独立 scorer)で SEALED を再採点した結果、
**全 arm 共通に DETECTION ≫ RECONSTRUCTION** が観測された。最大信号は **DETECTION→RECONSTRUCTION の急落**で、
skepticism(B)で最も急(H0: DET 1.455 → RECON 0.545)。

- B は強い **detection gate**(現 frame の帰結的欠陥を正しい locus で指摘する)。
- しかし B も他 arm も **reconstruction**(歴史的 breakthrough と構造同値な代替 frame の構築 = subject/level/distinction の変更 + 次手がそこから follow)を確実には完了しない。
- **robust hard-core は N=13 closure(DE-0115)で固定 = {HBB-08, HBB-10, HBB-30}**(2 軸 consensus で no arm が REC2 到達、全て detected-not-reconstructed)。`hbb_hard_core_fixed.json`。
  ※ closure 前の暫定 {03,08,11} は破棄。HBB-03 は B が hint-assisted で再構成到達のため hard-core 外(`hbb_final_report.md` §caveat)。
- **DE-0115 更新**: 2 軸 consensus では `C-unique_AA={HBB-05}` / `D-unique_AA={HBB-01,HBB-05}`(≠0)、H_primary は WEAKLY CONFIRMED。ただし engine の AA-unique 再構成は **H1 hint-assisted で、autonomous H0 ではない**。→ 未解決は「**autonomous(H0)reconstruction**」であり、これが reconstruction stage / scheduler の狙う欠落。

→ 従来の単一軸 Reach はこの detection/reconstruction 境界を曖昧化していた(DE-0114 で load-bearing から除外済)。
**reconstruction は検出とは別種の、現状どの arm も未達な段階**である、というのが 2 次元計測が出した中心所見。

## 2. 提案(案。実装ではない)

HBB / 2DER のパイプラインを **2 段に分けてモデル化**することを提案する:

1. **Detection stage** — 既存の arm(skepticism B / AFE C / Formal D / retrieval F)。現 frame の欠陥を検出する gate。B が強いことは既に示された。
2. **Reconstruction stage** — **独立機能**として切り出す。役割は「検出済みの欠陥に対し、歴史的 breakthrough と構造同値な代替 frame を構築する」こと。detection の下流だが detection では代替されない。

含意:
- reconstruction を **独立の計測対象**にする(DETECTION_RECONSTRUCTION_SPLIT は既にその計器)。
- reconstruction を **独立の設計対象**にする(独立 arm もしくは stage としての候補)。detection を強めても reconstruction は上がらない、という所見がこの分離を要請する。
- 成功規準(DD-ARCH-8 系)との整合: 2DER の目的は Taka を FORCED_OUT_OF_SCOPE 介入から解放すること。hard-core の reconstruction 未達は「AI 単独で frame を正せていない」局面の実測であり、reconstruction stage はその欠落を名指す。

## 3. 明示的な非主張・境界(over-claim 防止)

- **実装しない。** これは DD-ARCH 候補の提示に留まる。reconstruction stage を今 build しない。
- **能力向上を主張しない**(self-improvement claim なし)。所見は「reconstruction が未達段階である」ことであり、「解けた」ではない。
- **自律RD は未有効。** 本案は Taka の判定を経て初めて設計フェーズに入りうる。
- **scorer 規律を維持**: reach/complementarity は 2 次元 × 複数 scorer 一致でのみ claim(MULTI_SCORER_CONSENSUS)。
- **未消化の external handoff**(依然 open):
  - GPT / Claude raw-API arm(local Qwen 以外の実行)。
  - HBB-04 / HBB-30 の GPT による T0 採点(Claude は当事者につき除外)。
  - `hbb_sealed_report.md` の GPT / Claude-chat 独立 cross-review。
- **本案が依拠する GPT 採点の限界**(deviation_log 参照): human-level arm blindness 非完全、target_map 後付け形式化、ALT_UNTESTED は candidate のみ。Formal D は部分 compiler(5/8 probe; L/Ω/boundary は SOURCE_GAP)。SEALED split は skepticism-favorable な metric-artifact 型に偏る可能性(未統制)。

## 4. Taka への確認事項(判定待ち)

1. reconstruction stage を独立機能として設計フェーズに進めてよいか(go / hold)。
2. 進める場合、独立 **arm** として測るか、既存 arm の下流 **stage** として測るか。
3. reconstruction の成功規準を DD-ARCH-8(FORCED_OUT_OF_SCOPE 頻度→0)にどう接続するか。
4. 先に external handoff(raw-API arm / HBB-04・30 の GPT 採点 / 独立 cross-review)を消化してから設計に入るか。
