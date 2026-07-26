# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 意図調べ cheap fix（別解/DEFER是正/空入力reject/DE-0547）BUILT

- 宛: AUDIT（→ DESIGN → MGR/Taka）
- 発: 実装(IMPL) / 2026-07-26 / model=Qwen3.6-35B-A3B(:8005)
- 対応: `..._INTENT_CHEAP_FIX_HANDOFF`（別解書き戻し/DEFER定義是正/空入力入口reject/DE-0547）
- **★これは精度施策でなくラベル/定義の誤りの是正。数字は「緩めた分」を含む。見出しは(i)別解なし。**

## 成果物（working tree・未commit）
- `structure/s_intent_role_split_d2p2.py` + `INTENT_ROLE_SPLIT_D2P2.jsonl`（既存 d2p は不改変・比較用に残す）
- meta fold（:8005 CALL_SITE 登録）

## ★ 結果（(i)(ii) 併記・見出しは (i)）
| 指標 | 値 |
|---|---|
| **(i) 別解なし（唯一解基準・見出し）** | **0.7833 [47/60]** |
| (ii) 別解あり（許容解基準・**緩めた分込み**） | 0.9167 [55/60] |
| 接続（DF3込み・別解なし） | 0.746 [47/63] |
| 比較: arm-C3 / arm-D2' C（旧DEFER・DF3込・別解なし） | 0.5397 / 0.7143 |

- **(i) 0.78**（arm-D2' 0.71 から DEFER是正+DF3除外で改善）。**接続 0.746 が arm-D2' 0.714 と地続き**（DEFER是正で +2件・DF3 除外で母数 63→60）。
- **(ii) 0.92 は「別解込み」＝計器を緩めた結果**。(ii) だけを能力値として報告しない（★0 規律・arm-C2 汚染の轍を避ける）。

## §2 DEFER 定義是正の検証（★予測が当たったか・正直に）
新 DEFER=「不正形・解釈不能で、意味のある聞き返しすら組み立てられない」（旧の「文脈不足/要明確化」を削除）:
- ✅ **IP1/IP2 が DEFER から脱出**: arm-D2' では IP1/IP2 とも DEFER×3 だったが、本 fix で **DEFER が消滅**（旧定義の INTENT_PROBE 丸飲みを解消）。
- ✅ **DF1/DF2 は DEFER を維持**（狭めすぎで不正形を拾えなくなる副作用なし）: DF1=DEFER×3・DF2=DEFER×3。
- ⚠️ **ただし IP1/IP2 は INTENT_PROBE に clean には戻らない**: IP1=[INTENT_PROBE, CONTEXT_RESOLVE, PREMISE_PROBE]（1/3 のみ INTENT_PROBE）、IP2=[CONTEXT_RESOLVE, PREMISE_PROBE, PREMISE_PROBE]（0/3）。**CC-α の「6件回収」予測は部分的**——DEFER からは脱したが、INTENT↔PREMISE↔CONTEXT に散る（既知の指示語弱点 DE-0545 と整合）。**予測どおりでない点を silently 合わせず報告。**

## §3 空入力の入口 reject（Taka 判断）
- `is_empty_input()`: 空/空白/タブ改行/制御文字のみ → True。**LLM を1回も呼ばない**。**縦串から再利用可**な関数として実装。
- **DF3「   \t   」を FIXTURES から除外**（20件で測定）。DF1/DF2 は文字ありゆえ残す。
- negative control（--check）: 空白系→True・文字あり→False を assert。**空入力で LLM 呼出0** を実証。

## §4 DE-0547 是正
1. **MUTEX 規則2 撤回**: 基本形（C=員数制約付き1回観測）は mutex を使わない。規則2（DIRECT vs probe で DIRECT 落とす＝安全側）は正解を2件削った実績ゆえ**不採用**。
2. **(c) 選択役効率を候補≥2件のみで算出**（degenerate 是正）: **0.6667 [2/3]**。auto_confirmed_n=**57** を別途報告。**＝選択役は 60件中 3件しか動かず**、DE-0547 の「2つ目の LLM 役割は寄与薄・基本は自動確定」を再確認。
3. **呼び名を「役割分割」でなく「員数制約付き1回観測+決定論確定」**とした（何が効いたかの取り違え防止）。

## その他の実測
- **YES 平均 1.05・≥3 が 0**（員数強制が効き膨張なし）。**NO_CANDIDATE=0**（DEFER是正で「答えない」が消えた）。**順序一致 0.9833**。

## 検証（受入・全 gate GREEN）
- `--check` GREEN: 汚染ゲート（閾値4・機能語・negative control 実証）／空入力 reject の negative control（LLM 不使用）／記録から (i)(ii)(c) を決定論再計算し一致（LLM 非再実行）／acceptable_strategies の適用が決定論。
- DF1/DF2 が DEFER のまま・auto_confirmed_n と (c)(≥2限定) 分離・別解を勝手に増やしていない（§1 の4件のみ・基準記録）。:8005 CALL_SITE 登録。全 gate GREEN。

## ハンドオフ
- 次: 設計/監査 独立再監査（(i)(ii)分離・DEFER是正の部分的回収・空入力reject・(c)是正・選択役ほぼ不動）→ IP1/IP2 の INTENT↔PREMISE 散り（指示語弱点 DE-0545）の扱い。この後は縦串（back thin slice）。
- DE 記録は front door `record_de`+CLAUDE_CODE 開示。**「見出しは(i)0.78・(ii)0.92は別解込み・DEFER是正は部分的」を DE 本文に明記**。commit 時 script 同梱。

---
*実装(IMPL)。緩めた分(ii)と直した分を分離・見出しは(i)・DEFER是正は部分的回収を正直に・空入力はLLMに触らせない・選択役ほぼ不動を再確認。★3 本線・止めない。*
