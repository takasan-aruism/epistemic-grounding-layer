# 設計/監査 → MGR/Taka: 意図調べ arm-C2 独立再監査 — **0.88 は能力値として無効（テスト汚染）**（FINDING）

- 宛: MGR / Taka（IMPL 宛の再作業指示は §6）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=FINDING
- 対象: `CC_IMPL_2026-07-26_INTENT_PROBE_ARMC2_DEFS_BUILT.md` + `structure/s_intent_probe_armc2.py` + `INTENT_PROBE_ARMC2.jsonl`
- 監査方法: 記録 raw から**集計ツリーを私が独立に再実装して再計算**（IMPL のコードを信用しない）+ prompt と fixture の突合 + arm-C との metric 突合。

## 0. 結論（一行）
**決定論部・provenance は健全（再現一致）。しかし「定義+例で 0.58→0.88」「think は不要」の2大結論はどちらも支持されない。0.88 は "答えが prompt に書いてある" ことの測定である。commit してよいが、能力値として報告してはならない。**

## 1. ★F-1（決定的）テスト汚染 — 8 fixture 中 7 個が、正解付きで prompt の中に入っている
各二択の「具体例」が、**その二択が判定する当の fixture そのもの**（逐語 or ほぼ逐語）＋**正解ラベル**になっていた。

| fixture | 依頼文 | prompt 内の例（正解付き） | 混入先の二択 |
|---|---|---|---|
| F1_DIRECT | Windows 10 の一般提供開始日は？ | 「Windows10 の発売日は?」→意味が通る／始められる | b_malformed, b_needs_probe |
| F2_DIRECT | 1024 は 2 の何乗ですか？ | 「1024 は 2 の何乗?」→1つに絞れる | b_determinacy |
| F3_CONTEXT | プーチンの今後の動向は？(ctx=ウクライナ戦争) | 「直前がウクライナ戦争の議論で『プーチンの今後は?』→文脈で絞れる」 | b_context |
| F4_CHOICE | プーチンの今後は？(ctx なし) | 同上の後半「文脈なしなら→絞れない」 | b_context |
| **F5_BMV** | 白樺の木材としての価値は？ | **（混入なし）** | — |
| F6_INTENT_PROBE | あれ、どこにあったっけ？ | 「あれどこにあったっけ?」→INTENT／「あれどこ?」→聞き返しが要る | b_probe_type, b_needs_probe |
| F7_PREMISE_PROBE | 以前作った Watcher 仕様ってどこ？ | 「以前作った Watcher 仕様どこ?」→PREMISE | b_probe_type |
| F8_DEFER | asdf ;; // @@@ | 「asdf ;; //」→不正形 | b_malformed |

- ＝**8 問中 7 問が答案用紙に答えを書いた状態での 7/8**。汎化の証拠にならない。
- **責任の所在: これは IMPL の逸脱ではなく、DESIGN handoff（＝私の役割の前任）が例文を逐語で指定したことに起因する。** IMPL は指示に忠実。設計側の欠陥。
- 唯一の救い: **非汚染の F5_BMV は arm-C で 0/3 → C2 で正解**。方式に何かある可能性は残るが、**証拠は n=1**。

## 2. ★F-2 metric が不揃い — 0.58 と 0.88 は別の量
- arm-C の `strategy_match` = `hit / (8 fixture × 3 seed = 24)` ＝ **seed 平均**。0.5833 = 14/24。
- arm-C2 の 0.88 = **seed 0 の1本だけ**（single）or 多数決、いずれも /8。
- **同じ metric（arm-C 式 seed 平均）に揃えると**: arm-C2 think OFF = **20/24 = 0.8333**、think ON = **20/24 = 0.8333**。
- ＝改善自体は実在する（0.58→0.83）が、**BUILT の比較表は異なる量を並べている**。

## 3. ★F-3 「think は不要・むしろ不利」は支持されない
- BUILT の根拠は single 0.88(OFF) vs 0.75(ON) ＝**seed 1本の点推定**。
- seed 平均に揃えると **OFF 0.8333 / ON 0.8333 で同点**。しかも **seed 一貫は ON の方が良い（7/8 vs OFF 6/8）**。
- 残る事実は精度でなく**コスト**: ON は wall 103.87s vs OFF 6.86s（**15倍**）、completion_tokens 平均 1230.8 vs 18.8（**65倍**）、abstain 16%。
- → **結論は「think は精度を上げないのでコストの安い OFF を既定にする」まで。「thinking は松葉杖だと実証された」とは言えない。**（[[llm-prompt-hygiene-not-budget]] の逆側の戒め：都合の良い点推定で物語を作らない）

## 4. F-4 変えた変数が2つある（定義+例の効果を分離できていない）
arm-C → C2 で、定義+例の追加**に加えて `b_probe_type` の A/B の並び順が反転**している（arm-C: A=PREMISE/B=INTENT、C2: A=INTENT/B=PREMISE。各自内部では整合）。LLM には選択肢位置バイアスがあるため、**「+0.30 は定義例のおかげ」という帰属は交絡している**。

## 5. F-5 「systematic に失っていた F3/F5/F7 を全回復」は誇張
arm-C 実測（seed 別）: F3 **2/3**・F7 **2/3**（元々ほぼ正解）・F1/F2/F8 3/3。本当に落ちていたのは **F4 0/3・F5 0/3・F6 1/3**。C2 が直したのは **F5・F6**、**F4 は依然 label 不一致**（OFF single では b_needs_probe が誤爆して PREMISE_PROBE、多数決では BMV）。**ただし F4 を "miss" と呼べるかは §5b で撤回する。**

## 5b. ★【追補・Taka 指摘 → 実データで支持】正解ラベル自体が揺れる。理由(根拠)を一級市民にせよ
Taka 指摘: 「厳密には正解か不正解か揺れるものがある。なぜそれにしたのか＝理由を入れると、集計者から見た正解/不正解の関係は揺れる。しかしその揺れは誤りではない。数学でない以上、説得力の方が重要な場合がある。」
記録 `note` を実読して**3つの独立した機構で支持された**:

**(a) 唯一の不一致 F4 は、モデルの方が説得力がある＝ラベルが疑わしい**
`「プーチンの今後は？」`(文脈なし) 期待=CHOICE。モデルは **think off/on 通算 6/6 seed で BMV**、理由=「複数可能性の比較」「不確実性の比較」「観点比較」「多視点比較」。CHOICE の定義は「主要 branch が**有限**でユーザは一つを選びたい」。「プーチンの今後」に有限の選択肢は存在しない。→ **モデルの理由が定義に照らして正しく、期待ラベルの方が誤りである可能性が高い。**（DE-0542 で既に「F4/F5 はラベル論争」と留保済＝一貫）。**§5 の "F4 は miss" は撤回し、"ラベル再検討対象" に格下げする。**

**(b) 理由は「空回りの答え」を暴く（ラベルだけでは不可視）**
F4 `b_probe_type` off s1 = **B(=前提/存在が怪しい)** なのに理由が **「プーチンの存在は確実」**＝答えと理由が真逆。原因は、適用条件を満たさない二択も無条件に全件発行しているため、モデルが**空の答え**を返すこと。ラベルだけ見れば単なる "B"。**理由があるから中身が空だと判定できる。**

**(c) 理由は誤りの"種類"を特定する（修正可能にする）**
F4 `b_needs_probe` off s0 = B、理由 **「未来は不確実」**。これは「聞き返しが要るか」を「答えが確実か」と読み違えている＝**prompt の欠陥が特定できる**。単なる×では「外した」で終わる。

**(d) 費用対効果 — 買うべきは thinking でなく根拠**
think ON は 1 呼出あたり **1230.8 tokens** を消費して精度ゼロ改善（§3）。一方 `note` は **18.8 tokens** で上記 (a)(b)(c) が全て観測できた。**「考えさせる(高価・不可視)」より「言わせる(安価・監査可能)」。** これは EGL の中核（根拠なき claim を認めない）と同型であり、**理由のない二択は EGL 的には主張してはならない形**である。

**(e) 揺れを許しつつ自動測定を失わない二階建て（feasibility-first の難点対処）**
難点: 正解が揺れると自動採点ができず、毎回人が読むのでは回らない。→
- **一階（機械・全件・無料）**: 従来のラベル一致。ただし意味を**「正しさ」から「前回からの変化検知(regression detector)」へ再定義**する。
- **二階（理由・不一致時のみ）**: ラベルが期待とズレた件だけ理由を読み、**別解(理由が通る) / 誤り / 空回り** に3分類。8件全部でなく揺れた1〜2件のみ。
- **書き戻し**: 別解と確定したら fixture に **「許容解＋なぜ許容か」** を追記（例: F4 = CHOICE も BMV も可・理由「選ばせる有限の選択肢が存在しないため」）。＝[[llm_arithmetic_drift_tolerant_design]] の「LLM 分類→機械 consolidation で徐々に固める」の実装。揺れを消さず、少しずつ結晶化する。

## 6. 健全と確認できたもの（rubber-stamp でなく実検証）
- `--check` GREEN。**私の独立再実装（集計ツリー・多数決）で aggregate が完全一致** → 決定論再現・provenance の主張は本物。
- 288 行 = 2 think × 8 fixture × 6 binary × 3 seed（欠損なし）。**parse OK 288/288・finish_reason 全て stop・発散 0**（think ON でも length なし＝prompt 衛生 OK）。
- 「LLM は二択のみ・弁別は決定論集計」の構造は保たれている。

## 7. 付随して発見（arm-C2 とは無関係・要対応）
- **F-6: `s11_ledger_flow.py --check` は RED**（rc=1、`twoder/submit.py` への行参照が 5 件 stale）。原因は front-door slice1b の submit.py 編集（commit 6c760e7 / 07-26 00:54）で行がずれたのに図側を更新していないこと。**＝resume doc の「全 gate ローカル GREEN」は不正確。**
- **F-7: meta gap は doc の記述どおり実在**（HEAD の LLM_INVOCATIONS / TASK_CONTRACTS が armc2 を各1件参照、`s_intent_probe_armc2.py` は HEAD に不在 → clean checkout で RED）。armc2.py 込みの commit で解消する。
- **F-8（罠）: `structure/s*.py` の一部は `--check` を黙って無視して本体実行する**（s2_extract は argv を int 化して例外、s4_edges/s6_contradictions/s1_* は再生成）。監査目的の一括 `--check` 掃引が**台帳を書き換える**。実際に私が踏み、10 台帳を HEAD から復元済（working tree は clean に戻した）。加えて **`s6_contradictions.py` は実行すると `KeyError: 'importers'` で落ちる**。

## 8. 決定（Taka GO 済 2026-07-26「OK。任せる」）
1. **commit する**（armc2.py + jsonl + 本 FINDING）。理由は meta gap の解消。ただし **DE には「汚染により能力値ではない」を明記**し、0.88 を能力主張として台帳に残さない。
2. **やり直し（IMPL へ）**: 例文を fixture と**素性の異なるものに差し替え**（held-out）、A/B 並び順は arm-C と揃えるか両方測る、fixture を各戦略 3 件以上に拡充、metric は **seed 平均に統一**。これで初めて「定義+例は効くのか」が測れる。
3. **理由(根拠)を一級市民にする（§5b）**: 各二択に1文の理由を必須化し、二階建て評価＋許容解の書き戻しを導入。F4 の期待ラベルは再検討対象。
4. **2 と 3 は 1 回のやり直しに統合**（3 が測定設計を変えるため別々に回すのは無駄）。→ handoff `CC_DESIGN_2026-07-26_INTENT_PROBE_ARMC3_HELDOUT_REASONS_HANDOFF.md`。
5. **F-6（s11 RED）と F-8（--check の罠 / s6 crash）** を別件として起票。

---
*DESIGN CC-α 独立再監査。決定論部は健全・結論は無効。measure-first ＝「効いた」より先に「測れているか」を疑う。★3 本線は止めない。*
