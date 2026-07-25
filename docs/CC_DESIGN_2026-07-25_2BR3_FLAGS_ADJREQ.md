# 設計/監査 → MGR: 2b-r3 再監査の2 flag 裁定要求（ADJREQ）

- 宛: MGR
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / TYPE=ADJREQ
- 対応: `CC_IMPL_2026-07-25_RTHREAD_2b-r3_REFREEZE_BUILT.md`
- escalation 判定: flag1=DESIGN 推奨あり（MGR 確認で足りる可能性）/ flag2=governance＝human 要（Taka）

## 再監査 verdict: 2b-r3 **機構は CONSISTENT**（独立検証済）
- `s_rthread_2br3.py --check` GREEN（byte一致 / 4陰性対照 load-bearing: 候補検出・退化除外・no-auto-freeze・I1 / I1 保存 908==908）。
- **no-auto-freeze 実証**: v2・FREEST_APPROVALS 不在（機械は凍結しない）。承認 marker 投入時のみ v2、marker 無しで v2=RED。
- **絶対閾値定数ゼロ**（既存 `R.MARGIN`/`R.DIV_TH` 再利用のみ・負の制御相対）。
- INTENT-collapse（div=0.0065）を `RESIDUAL_LOW_DIVERSITY` で正しく除外。
- → **機構そのものは承認可**。以下2点が commit を阻む。

## Flag 1: QUALIFIED 2件が record-kind 偏重（DE-0521 との緊張）
実測（fresh 再確認）:
| candidate | n | silhouette | sub_sil | margin | diversity | kind_purity | 性質 |
|---|---|---|---|---|---|---|---|
| CAND-29580ee0 | 120 | 0.379 | 0.228 | **0.151(明確)** | 0.967 | 0.992(99%REQ) | "BOUNDED-PATCH-BRIDGE" 実装要求＝**話題として coherent**（kind と相関する本物の topic） |
| CAND-98f1a155 | 370 | 0.100 | 0.034 | **0.066(薄い)** | 0.981 | 0.905(DE偏重) | corpus の41%・拡散した DE 塊＝**catch-all 近似**（trivial 構造の再浮上疑い） |

- **論点**: §2 の「本物」判定は kind-直交性を課していない。DE-0521(record-kind=trivial)を踏まえると DE 塊は trivial かも。但し patch-bridge のような「kind と相関する本物の話題」を殺さない配慮も要る。
- **DESIGN 推奨 = (a)**: 機構は現状維持。**両候補は性質が違う**（29580ee0=明確 margin の real topic / 98f1a155=薄 margin の near-blob）。blunt な「kind-pure→降格」ガードは real topic(29580ee0)を誤って殺すので不可。**#3 の人間承認ゲートが kind 判断の正しい場所**——機械は kind_purity/margin を証拠付きで surface 済み、Taka が承認時に「これは本物か kind 塊か」を判断すればよい（機械は既に propose のみで停止）。
- (b) 精緻な kind-blob ガード（「cluster が単一 record-kind の大半を占める＝塊」なら降格。薄 margin の 98f1a155 は落ち、29580ee0 は残る）は propose queue が塊で溢れた時に別途小改修で。**今は不要**。
- **MGR へ**: (a) で確定してよいか。DE-0521 に触れるので必要なら Taka 最小確認。

## Flag 2: corpus drift（系統的・commit blocker）＝human 裁定要
- **根因（重要）**: `s_embed_axes` の埋め込み corpus = `rri_records.jsonl`(698) **＋ `DESIGN_EVIDENCE_LEDGER.jsonl`(528)**。つまり**DE を admit するたびに corpus が成長し snapshot が drift する**。本セッションの DE-0525..0531 追記が主因。
- **実測**: committed membership=908 / 現 corpus≈916。`s_embed_axes --check` / `s_account_axes --check` が今 **REGEN_MISMATCH RED**（環境 drift・2b-r3 が原因でない・committed 不触・.npy は derived）。
- **影響**: 2b-r3 は stale な membership(908) の上で候補を出している。clean commit するとstale 候補を固定化する。
- **DESIGN 推奨（要 Taka 承認）**:
  1. **即時**: 2b-r1→r2→r3 を現 corpus に一括再生成し commit=Taka で snapshot 整合（決定論・機械的。私が nod で実行可）。
  2. **恒久**: **corpus-snapshot pin 規律**を導入（2b パイプラインは pin された corpus 版に対して回し、DE ledger 成長では自動 RED しない。再baseline は意図的にのみ）。あるいは**より根本的に「DE ledger を埋め込み corpus から外すか」**（監査証跡を解析入力にする是非）＝設計判断。
- **MGR へ / Taka へ**: (1) 即時再baseline を承認するか、(2) 恒久策は pin 規律か corpus 定義見直しか。ここは governance ゆえ Taka 裁定。

## 保留中
- **2b-r3 commit は保留**（flag2 の再baseline 前にstale 候補を固定しないため）。
- 承認が出れば: 再baseline 実行 → flag1 方針で候補確定 → commit=Taka → DE 起票。
- 不変: sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない。

---
*DESIGN CC-α。ADJREQ。機構は健全、2 flag のみ裁定要。過剰主張より正直な保留。*
