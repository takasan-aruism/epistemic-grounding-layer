# 設計プラン: RTHREAD stage 2 — accounts(科目)導入

- 起草: 設計/監査(CC-α)/ 2026-07-24 / 正本: `RRI_SPEC_MACHINE_v1_1.json`
- rollout stage 2 定義(初版): **"accounts introduced; LLM assigns, machine balances"**

## §0. 仕様の拘束(憶測禁止の核)
初版が最も強く戒めるのは **「account は MINED であって imagined ではない」**(chart_of_accounts.source / rejected_alternative=「Claude が事例を想像して A-E 表を捏造」した過去の antipattern)。よって:
- **account 名を私が発明しない。** 実 chart は DE ledger(現512) + rri_records(680) の決定論クラスタリングから出す(= MINING_SPEC・別 deliverable)。
- 分業(question_ledger.division_of_labor):**LLM** = 「その問いはどの account か」「account を split/merge するか」(価値判断・G-2)。**machine** = balance 等式 / per-axis 残差 / 総保存。
- event model(spec event_types):account は **`QUESTION_RAISED` の `account_id|UNCLASSIFIED` フィールド**に載る(別 ASSIGN イベントではない)。
- 未分類は **UNCLASSIFIED**(suspense)に置ける。balance 常時可視、RESOLVED では 0 か明示処分。
- 語彙(G-6)/ 封印(G-1)/ chart は DERIVED・versioned・never SoR(G-5)。

## §1. stage 2 が要求する新規要素(spec 由来)
1. **chart of accounts**(有効な account_id 集合)= MINING_SPEC で決定論生成。DERIVED/versioned。
2. **chart 検証**: `raise_question` の account_id は「chart の要素 or UNCLASSIFIED」でなければ machine が拒否(off-chart=unaccounted)。
3. **suspense 決着規律**: UNCLASSIFIED balance を RESOLVED guard で machine が検査(現状は self-report `suspense_settled` を信じているだけ=G-1 違反の芽)。
4. **昇格 / explosion valve**(T22/T23): 新 account 提案は UNCLASSIFIED 配下の sub-label、N スレッド再発で昇格。新 account は「memo で表現できない理由」の記録必須。account 数ハードキャップ。
5. **統計**: frequency / co-occurrence / resolution_rate / temperature_consumption / gap_rate / rejection_rate(human 可視の first-class stat)。

## §2. 私が下す設計判断(ADJUDICATION_SENSITIVE として明記)
- **D1(suspense_balance 再定義・correctness fix、私の担当):** 現 `suspense_balance = UNCLASSIFIED に raise された数`(処分しても減らない=永遠に0にできない)。→ **「UNCLASSIFIED かつ未 dispose-out の問い数」**へ再定義し、RESOLVED で 0 到達可能に。F-1 と同型の「恒等式でなく実残高」化。
- **D2(chart 検証は machine):** account の妥当性は factual(chart メンバか)→ machine-only(G-2)。どの account かは LLM(value)。
- **D3(I2 の load-bearing 化):** account 次元の保存を「全 raised 問いが chart∪{UNCLASSIFIED} の丁度1 account に属し、off-chart/欠落があれば halt」で load-bearing に。現状 partition 恒等式を、chart 照合で実効化。
- **スコープ外(初版どおり後段):** split/merge(T16/T17)=stage④、semantic index=stage⑤。stage 2 に混ぜない。

## §3. スライス分割(案)
- **stage 2a(機械核):** chart 検証 + D1 suspense 決着 + D3 I2 load-bearing。**imagined account を使わず** UNCLASSIFIED + 極小の固定テスト chart(2要素)だけで機構を検証。production 変更=`raise_question`/`project`/`advance_state`/新 `check_account_conservation`。テスト=I2 load-bearing / suspense 決着 / off-chart 拒否 / T24(memo は算術に使わない)。
- **stage 2b(MINING_SPEC v0.1):** DE ledger + rri_records の決定論クラスタリングで実 chart 生成。受入3条件=byte一致再生成 / 陰性対照(shuffle 入力で安定クラスタ無し)/ シード跨ぎ一致。**別 deliverable。**
- **stage 2c:** 昇格/explosion valve(T22/T23) + 統計。

## §4. Taka 判断が要る fork
**スライス順序**(§5 の質問)。それ以外(D1-D3)は上記のとおり設計側で確定・明記で進める。
