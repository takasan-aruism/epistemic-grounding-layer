# 設計/監査 → 実装: 意図調べ arm-D「役割分割」— 選別役(YES/NO) と 選択役 を分ける（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=HANDOFF / model=Qwen3.6-35B-A3B(:8005)
- 正典: **Taka 指示（2026-07-26）**「『前提を疑え』にはあまり意味がない。効果を狙うなら**役割を分けること**。4軸→§9 7択メニューがあるなら、**一つずつ『この内容に○○は一致するか？』を YES/NO で聞く**。次に**担当を変えて**『YES の中から最も当てはまるものを選べ。理由も述べよ』。**二つの異なる役割**になるので、その役割の中で最適解を選ぶ方向に調整できる。LLM はもっぱら良い方向に進もうとするのでこの手のやり方の方が筋がいい」+ ESDE Language A1 パイプライン（下記 §1・**Taka 示唆により実物を調査済**）
- 成果物: `structure/s_intent_role_split.py` + `INTENT_ROLE_SPLIT.jsonl`
- **前提: `s_intent_dialogue_probe.py` の採点式は流用しないこと**（正規表現が Qwen でなく抽出可否を測っていた・DE-0545）。

## 0. なぜこれが効くはずか（我々の実測とつながる）
arm-C3 再監査の最大の発見は「**不一致 29 件中 15 件(52%)は、期待戦略を出す二択が正答していたのに、上流の短絡で参照されなかった**」だった（DE-0544）。短絡型決定木という**集計設計**がボトルネックだった。
**役割分割は木を丸ごと捨てる**: 7 戦略を**それぞれ独立に**判定するので、上流の 1 個の誤りが下流の正答を殺す直列構造が**構造的に消える**。＝「LLM を強くするのでなく集計を強くする」の具体形。

## 1. ★ESDE Language の先行実績（実物を調査した結果・そのまま使える）
`/home/takasan/esde/ESDE-Research/language/lexicon/mapper_a1.py` / `auditor_a1.py` / `docs/ESDE language/DESIGN_NOTE_Resonance_Scoring.md`。
QwQ-32B で **326 atom × 48 スロット**を観測した実運用パイプライン。**同型の構造が既に動いており、失敗と対策が記録されている。**

### (a) 役割の言語化（そのまま踏襲する）
> **"You are an OBSERVER, not a classifier. Do NOT pick a winner."**

選別役に**勝者を選ばせない**ことを prompt で明示している。Taka 指示の「役割を分ける」の実装形。

### (b) ★最大の危険＝YES 膨張（ESDE で実際に起きた）
> score inflation: QwQ-32B が **48 スロット中 39 に非ゼロ**を付けた（妥当なのは 8〜15）。

**7 戦略を YES/NO で聞けば Qwen は YES を付けすぎる。これは推測でなく先行実績。** ESDE の対策をそのまま移植せよ:
1. **既定は NO**（"DEFAULT IS 0. When in doubt, 0."）
2. **員数の明示**（"TARGET: at least 30 of 48 slots should be 0" / "A typical word genuinely resonates with only 8-15 slots"）→ 本件では **「典型的には 7 つのうち YES は 1〜2 個。3 個以上 YES なら付けすぎ」**
3. **出力前の自己点検を prompt に書く**（"SELF-CHECK before outputting: Count your zeros"）→ **「YES の数を数えよ。3 以上なら、根拠が具体的でない YES を NO に落とせ」**
4. **弱い YES を許さない**（"If you cannot state a concrete reason, use 0"）→ **理由を 1 文で言えない YES は NO**
- ESDE の是正実績: nz_mean **38.7 → 13.6**、OK 率 78.4% → **97.3%**。**プロンプト規律だけでここまで動いた。**

### (c) 監査役は「検出のみ・修正しない」
> **"detection works, correction fails with same model. Auditor only flags; Writer re-observes with constraints."**

同一モデルに直させると失敗する。**監査役は flag だけ立て、選別役が制約付きで観測し直す**（§4）。

### (d) ★正直な相違点（Taka に判断いただく点）
ESDE は当初 **binary membership（所属する/しない）**だったが、**連続値 0-10 の共鳴度に置き換えた**（2026-02-15 Taka 承認）。理由は「score 2-3 = 弱いが実在する共鳴」を binary が壊すため。
→ **今回の YES/NO は、ESDE が一度捨てた形式**にあたる。ただし 48 スロットと 7 戦略では粒度が違い、7 なら binary で足りる可能性は十分ある。**両方を測る**（§2 arm-D1/D2）。

## 2. 実装（2 ロール・LLM 呼出は独立させる）

### ロール1 = 選別役（Screener）
- §9 の **7 戦略それぞれについて独立に 1 呼出**（会話履歴を共有しない・並列可）。
- 問い: 「依頼:「{req}」{ctx}\nこの依頼に **{戦略名} = {戦略の定義1文}** は一致するか。」→ **YES / NO** + **理由1文（40字以内）**。
- **prompt に §1(b) の 4 点を必ず入れる**（既定NO・員数・自己点検・理由なきYES禁止）。
- **戦略名だけでなく定義を毎回同梱**（名前だけだと語感で決まる）。
- **arm-D1 = YES/NO** / **arm-D2 = 0-10 の当てはまり度**（§1(d)。D2 は上位を候補とする）。同一 fixture で両方測る。

### ロール2 = 選択役（Selector）
- **別呼出・別 system prompt**。ロール1 の内部過程は見せない。**YES になった候補（戦略名＋定義＋ロール1の理由）だけ**を渡す。
- 問い: 「依頼:「{req}」{ctx}\n次の候補のうち、**最も当てはまるもの1つ**を選び、理由を1文で。」
- **構造的制約（決定論で強制）**: 選択役の出力が **NO だった戦略なら無効**（記録し `SELECTOR_OUT_OF_SET`）。＝選択役は候補集合の外に出られない。
- **候補0個** → `NO_CANDIDATE`（捏造で埋めない）。**候補1個** → 選択役を呼ばず確定（コスト削減・記録に明示）。

### ロール3 = 監査役（Auditor・検出のみ）
**まず決定論の pre-screen（コード。LLM を使わない）**:
- `YES_INFLATION`: YES ≥ 3
- `NO_CANDIDATE`: YES = 0
- `CONTRADICTORY_YES`: 排他のはずの組が同時 YES（例 DEFER と DIRECT、DIRECT と BMV）
- `REASONLESS_YES`: 理由が空/定型
→ flag が立った件のみ、**選別役に制約付きで再観測させる**（監査役は直さない・ESDE §1(c)）。再観測は**1回まで**、初回と再観測の**両方を記録**（隠さない）。

## 3. 測定（arm-C3 と比較可能に）
- 同 fixture（`s_intent_probe_armc3.FIXTURES` 21件を**そのまま import**）× 3 seed。
- **metric は seed 平均**（arm-C 0.5833 / arm-C2 0.8333(汚染) / arm-C3 0.5397 と同一物差し）。
- **必ず報告**: YES 数の分布（膨張の実測）／`SELECTOR_OUT_OF_SET` 件数／`NO_CANDIDATE` 件数／flag 別再観測の前後／arm-D1 vs D2／wall・呼出数。
- **汚染ゲートを必ず載せる**: 例文・定義に fixture 依頼文の連続**4文字**以上が出たら RED（`s_intent_probe_armc3.contamination_violations` と同型。**閾値は 5 でなく 4**。BV2「〜の是非は」が 5 では抜けた実績・DE-0544）。`EXCLUDE_WORDS` に機能語を明示列挙。negative control で RED になることを実証。
- **A/B 順序バイアス対策**: 選択役の候補提示順を**正順/逆順の両方**で測る（position bias 0.6481＝35%答えが変わる実績・DE-0544）。

## 4. 受入
1. `--check` GREEN（汚染ゲート＋negative control／記録から選別・選択・集計を決定論再計算・LLM 非再実行／provenance 完全）。
2. **ロール分離の証跡**: 呼出が別で履歴非共有であることが記録から確認できる（record_type を role1/role2/audit で分ける）。
3. `SELECTOR_OUT_OF_SET` が決定論で検出・記録されている。
4. YES 膨張の実測値を出す（**膨張していたら「していた」と正直に**。ESDE では起きた）。
5. :8005 CALL_SITE 登録（meta fold）。**commit 時に新 script を必ず同梱**（未同梱=clean checkout RED・DE-0543 実績）。

## 5. 規律
- **measure-first**。arm-C3(0.5397) を下回っても隠さない。**役割分割が効かなかったならそう書く。**
- 数字を能力主張にしない。**arm-C2 の 0.83 とは絶対に並べない**（あれは汚染値）。
- **「良い方向に進もうとする」性質の利用がこの設計の要**（Taka）。選別役には「観測者であり決定者でない」役割を、選択役には「候補内で最善を選ぶ」役割を与え、**各役割の中で最適化させる**。役割をまたいだ指示（「前提を疑え」等）は入れない。
- commit=Taka。DE は front door `record_de` + `CLAUDE_CODE` 開示。★3 本線は止めない。

---
*DESIGN CC-α。木を捨て役割を分ける。ESDE の先行実績(観測者宣言・YES膨張対策・監査は検出のみ)を移植。binary か連続値かは両方測る。*
