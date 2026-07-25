# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): 意図調べ 3アーム比較（thinking ON + 二択並列分解）BUILT・measure-first

- 宛: AUDIT（→ DESIGN → MGR）
- 発: 実装(IMPL) / 2026-07-26 / model=Qwen3.6-35B-A3B(:8005)
- 対応: `..._RETEST_THINKING_ON_HANDOFF`（Arm B）+ `..._ARMC_PARALLEL_DECOMP_HANDOFF` / `..._PARALLEL_DECOMP_ADDENDUM`（Arm C・Taka核心）
- **能力測定であり成功宣言でない**（弱ければ弱いと言う）。

## 成果物（working tree・未commit）
- `structure/s_intent_probe_proto.py`（Arm A/B: 単発・config 行列 tight_off/tight_on/loose）+ `INTENT_PROBE_PROTO.jsonl`
- `structure/s_intent_probe_armc.py`（Arm C: 二択並列分解 + 決定論集計ツリー）+ `INTENT_PROBE_ARMC.jsonl`
- meta fold（LLM_INVOCATIONS に両 :8005 CALL_SITE 登録・TASK_CONTRACTS・READ_PATHS）

## 3アーム比較（同 8 fixture × 3 seed・決定論集計）
| Arm | 戦略一致 | 発散率 | probe recall | 誤probe | seed一貫 | 速度/コスト | 軸妥当 |
|---|---|---|---|---|---|---|---|
| A 単発 thinking OFF | 0.46–0.54 | 0.00 | 5/6 | 0/18 | 7/8 | 中 | 0.74 |
| B 単発 thinking ON | 0.54 | 0.00 | 3/6 | 3/18 | 6/8 | **遅 4m13s/72** | **0.85** |
| **C 二択並列+決定論集計** | **0.58** | **0.00** | **6/6** | 1/18 | 5/8 | **速 10.8s/144並列** | (二択ゆえ軸名なし) |

## ★ 核心的発見（Taka 仮説の検証・measure-first）
### (1) thinking ON は「賢さ」でなく「原子判断」を上げる（松葉杖仮説を裏付け）
- 軸妥当性 **0.74→0.85 改善**（原子的な軸判断は thinking で向上）。**しかし戦略一致は 0.54 で不変・probe は悪化**（recall 5/6→3/6, 誤probe 0→3）。
- ＝**複雑な戦略選択は thinking を足しても直らず、むしろノイズ増**。Taka「二択に削げば thinking 不要で正確」の前提（複雑判断は松葉杖では解けない）を実証。
- 副次: **tight+budget 6144 で thinking ON でも発散 0.00**（「thinking を切る」は過剰対策だった＝前回是正が正しい。発散真因は緩い prompt）。

### (2) Arm C は単発が systematic に失った細分を回復（Taka 核心思想の実証）
- **単発(A/B)が全滅していた細分が Arm C で回復**: F3 CONTEXT_RESOLVE **2/3**（A/Bは0）、F7 PREMISE_PROBE **2/3**（A/Bは0）。
- **probe recall 6/6（最良）**・**発散 0.00（tiny 二択は発散しない）**・**最速最安（144呼出を並列16で10.8s、Bの thinking 依存 4分の 1/23）**。
- ＝「LLM に細分させず二択に削ぎ、弁別を決定論集計で持つ」が、単発（thinking 有無問わず）が失う細分を**構造的に回復**。

### (3) Arm C の価値＝弱点の"局在化"（次のメニュー設計知見）
単発の失敗は不透明（なぜ間違えたか分からない）。Arm C は**どの二択が弱いかを特定**できる:
- **効く二択（信頼）**: `b_malformed` / `b_needs_probe`(probe有無・全問正確) / `b_context`(文脈依存) / `b_determinacy`(大半)。
- **弱い二択（要 sharpening）**:
  - `b_probe_type`（INTENT↔PREMISE）: F6/F7 とも `[B,A,A]` でノイズ＝「対象不明 vs 存在怪しい」の A/B framing が甘い。
  - `b_multi_type`（CHOICE↔BMV）: 一貫 B(BMV)寄り。
- **一部は"誤り"でなくラベル論争**: F5「白樺の木材価値」を Qwen は determinacy=A(絞れる)＝DIRECT と一貫判断（BMV とする私の expected が議論余地）。F4「プーチンの今後」を BMV とするのも妥当。→ **0.58 は C の質を過小評価**（数件は Qwen が妥当）。

## 総合評価（正直に）
- Taka 核心「二択に削ぐ＋決定論集計 > 単発（thinking 有無問わず）」= **方向として支持**。圧勝(0.58)ではないが、**単発が失う細分を回復・probe 全捕捉・発散ゼロ・最速最安・弱点を特定二択に局在化**。残弱点は**2つの弁別二択（probe_type / multi_type）**に絞れた＝次に締める場所が明確。
- **次の設計提案（IMPL 入力・DESIGN 判断）**: (a) `b_probe_type`/`b_multi_type` の A/B を鋭くする（「対象が名指しできるか？」「選択肢が3つ以内に列挙できるか？」等の具体二択）。(b) **binary ごとに seed 多数決**（seed一貫 5/8 の改善）。(c) 論争的 fixture ラベルの再検討（F4/F5）。

## 検証（全 gate GREEN）
- 両 `--check` GREEN: 記録 raw_output/二択に決定論パーサ・集計ツリーを再適用→一致（LLM 非再実行）・fixture 固定・provenance 完全（enable_thinking/max_tokens/reasoning=completion_tokens/並列数/wall 秒/sub-answers）。
- 両 :8005 CALL_SITE 登録（meta self-heal fold）。全 gate GREEN。

## ハンドオフ
- 次: 設計/監査 独立再監査 → 3アーム比較を MGR へ（Qwen 能力・thinking の効き所・二択分解の価値・次に締める二択）→ commit=Taka。
- DE 記録: 本結果を **front door(`record_de`)＋candidate に `generated_by_principal/claiming_principal=CLAUDE_CODE`・`generation_mode=DIRECT` 明示**で記録（内部アクター開示・DE-0541 失念の再発防止）。

---
*実装(IMPL)。二択に削ぐ＝thinking 不要で細分回復・弁別は決定論集計・measure-first(0.58 を過大主張しない)。★3 本線・止めない。*
