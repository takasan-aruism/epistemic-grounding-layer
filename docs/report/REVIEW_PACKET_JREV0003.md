# EGL JREV-0003 裁定 依頼パケット(独立レビュー用)

日付: 2026-07-05  対象 commit: `954308e`(R6 Phase 1a / DE-0026)+ `2e13a6a`(実弾デモ / DE-0027)
依頼先: 独立レビュー(GPT / 別重み。IR-2: 独立性は local swap でなく別 API で調達)

---

## 0. これは判定ではなく依頼です(かつ、初のコード攻撃 *実行* 済み)

著者(Claude Code)は**自分の修正を JUDGE_VERIFIED と宣言しません**。本パケットは R6 remediation
(DE-0026)と grounding 実弾デモ(DE-0027)を提示し、**property 毎の裁定を依頼**します。

**レビューの分業(JREV-0002 §0 で確立、本 JREV で初めて *実行* 段階に到達):**
- **attacker = 別セッションの local agent**(DE-0005 で有効性を実証した独立敵対経路)。本 JREV では
  local agent が §5 attack checklist を**実弾で実行済み**——結果は §3。これが JREV-0002 §0 が
  「初のコード敵対レビューは実行主体=local agent」と設定した分業の初回発火。
- **adjudicator = GPT**。§3 の attack 結果 + 本パケットを一次資料に verdict を裁定する。
- attacker(local agent)・author(Claude Code)・adjudicator(GPT)は三者別主体。

判定は JREV-0001/0002 と同形式(property-level + evidence_basis 併記)で `REVIEW_LEDGER.jsonl` に
JREV-0003 として記録してください。

---

## 1. JREV-0003 が見るもの

| 対象 | 内容 | DE |
|---|---|---|
| R6 remediation | `derive_validation_mode` を source_class 単独 → (source_class, observation_kind) 対へ。DECLARED=PRIMARY+DECLARATION 同一観測 / SPECIFIED=PRIMARY+(DECLARATION\|SPECIFICATION) / else UNRESOLVED。MEASURED/REPRODUCED は未導出 | DE-0026 |
| grounding 実弾デモ | 取得境界未実装ゆえ実機観測(nvidia-smi/ps)を手投入し grounding を通した。R6/GC-7/ABSENCE が実データで作動 | DE-0027 |

---

## 2. property 再判定表(著者要求は REQUESTED)

| component/property(atomic) | JREV-0002 | remediation 後の証拠 | 著者要求 | 残る非保証 |
|---|---|---|---|---|
| L4/validation_mode_derivation | NOT_VERIFIED(R6) | test_sor T8a-h(DECLARED=PRIMARY+DECLARATION、**T8f counter-factual**=同一 PRIMARY で kind 反転→DECLARED→UNRESOLVED、NEGATIVE+MEASUREMENT→UNRESOLVED)。source_class 単独穴を閉塞 | **source_class-only 穴の閉塞のみ**(property 全体の VERIFIED は要求しない) | observation_kind 自体が RD self-report / MEASURED・REPRODUCED 未導出 |
| L4/observation_kind_gating | (新 property) | derive が (source_class, observation_kind) 同一観測対を要求。継ぎ合わせ gaming を封鎖(§5-A で実弾確認) | VERIFIED 候補(狭い保証) | kind 詐称は単一プロセス検出不能 |
| GROUNDING_DEMO/real_data_pipeline | (新) | demo_machine_ai.py が実機観測で evidence→claim / R6 mode / GC-7 / ABSENCE を通行(DE-0027)。§3-E で構造的 load-bearing を実弾確認(E4=嘘 conclusion を Gate3 が上書き) | **通行実証のみ**(取得実装ではない) | Gate4 finding は driver-injected / 取得境界未実装 |
| GATE0/polarity_wellformedness | (F/JREV-0003 新・修正済) | §3-F で local agent が fail-open を検出 → DE-0028。Gate0 enum 検査 + derive fail-closed。test_adversarial F群 8本(未知 polarity→Gate0 reject & UNRESOLVED、正規系不変) | VERIFIED 候補(fail-closed) | polarity ラベル自体は RD 供給(正規値〈POSITIVE 等〉の詐称は source_class/kind と同型 leaf self-report) |

**evidence_basis: test-verified(counter-factual T8f 含む)+ §3 の local-agent コード攻撃実行結果。**
**GPT の evidence_basis は「attack 結果 + パケットに対する adjudication」(§0 分業。GPT は repo 直接アクセスなし)。**

---

## 3. コード攻撃 実行結果(local agent, 実弾)

別セッションの local agent が §5 を isolated `EGL_DATA_DIR` で実行(canonical data/ 非汚染)。probe:
`scratchpad/probe_abcd.py` / `probe_e.py` / `probe_f.py`。

| attack | 実出力(要点) | verdict |
|---|---|---|
| A 継ぎ合わせ | PRIMARY/MEAS + SECONDARY/DECL → UNRESOLVED、PRIMARY/UNSPEC + SECONDARY/DECL → UNRESOLVED、対照 PRIMARY/DECL 同一観測 → DECLARED | **DEFENSE_HELD**(同一観測 pair 要求 gates.py:111) |
| B GENERATED+DECL | PRIMARY/UNSPEC+GENERATED/DECL → UNRESOLVED、PRIMARY/DECL+GENERATED/DECL → UNRESOLVED(正当宣言があっても汚染で fail-closed) | **DEFENSE_HELD**(`all(c!="GENERATED")`) |
| C MEASUREMENT 正当性 | PRIMARY/MEAS POS→UNRESOLVED、NEG→UNRESOLVED、PRIMARY/REPRO→UNRESOLVED、対照 PRIMARY/SPEC NEG→SPECIFIED、PRIMARY/SPEC POS→UNRESOLVED | **DEFENSE_HELD**(MEASURED/REPRODUCED 未昇格) |
| D 空/不正/back-compat | 空→UNRESOLVED、dangling→UNRESOLVED(no crash)、R6前 observation(kind 欠落)→UNRESOLVED(安全側 downgrade)、ABSENCE→ValueError | **DEFENSE_HELD**(clean-fail) |
| E demo が driver-honest-replay か | E1: kind を DECLARATION に変えると UNRESOLVED→DECLARED に flip(真に導出)。E2: known_omissions を空にすると GC-7 が pass(block は実データ駆動)。E3: leg を FAILED にすると ABSENCE→ABSENCE_BLOCKED_SC2。**E4: 嘘の COMPLETED conclusion を手forge しても Gate3 が leg event から coverage 再導出し SEARCH_INCOMPLETE で block**(DE-0005 の穴が閉じている実証) | **構造的に load-bearing**(replay ではない) |
| F その他(§4外) | polarity 欠落/typo('NEGATVE')/None/garbage が **POSITIVE→DECLARED 分岐へ素通り**。enum 検証も Gate0 必須項目にもなっていない | **NEW_DEFECT(§4外)** |

**demo の soft spot(宣言済み hole #4 内)**: C1 の Gate4 finding は driver-injected で、C1 statement が
`port 8005` を主張するが adjudicated fragment(VLLM_PROC[1])に 8005 は無い=軽度の過大主張。宣言済み hole #4
(Gate4 driver-injected)の範囲だが、demo が穴に寄りかからないよう **statement/scope から port 8005 を除去**
(fragment が支持する tp/kv-cache/max-model-len のみ主張)して是正済み。

**F の帰結と remediation(DE-0028)**: 証拠の壁は破らない(依然 PRIMARY+DECLARATION が必要)。損害は *誤ラベル*
——mistyped NEGATIVE が positive DECLARED に再分類され、R5/R6 が築いた polarity 特異性が未知値で迂回される。
モジュール自身の原則「既定値の存在自体が誤り」に反し、未知 polarity が最特権分岐へ倒れていた。**修正=fail-closed**:
(1) `gates.gate0_schema` に polarity enum 検査を追加(未知/欠落/typo を DEFER で上流 reject)、(2)
`derive_validation_mode` で polarity ∉{POSITIVE,NEGATIVE} を UNRESOLVED へ(二重防御)。counter-factual
`test_adversarial` の F 群 8 本(未知 polarity→UNRESOLVED / Gate0 reject、正規系不変)。test_adversarial **22/22**。

**overall(local agent)**: R6 fix は宣言 scope 内で **sound**、demo は **構造的に load-bearing**。§4外の新規欠陥は
F 1件のみで、証拠バーは破らない labeling/robustness gap。→ 修正済(DE-0028)。

---

## 4. 残る非保証(著者の自認リスト = 過大報告していないかの検査面)

`egl/contracts.py` gates.derive_validation_mode の non_guarantees(R6 実装後の残余):
- **observation_kind の真正性**: R6 で DECLARED/SPECIFIED を『PRIMARY+明示宣言/規定 観測』に限定し
  source_class 単独導出の穴は閉じたが、observation_kind 自体も RD 供給ラベル。**種別詐称(MEASUREMENT を
  DECLARATION と偽る)は単一プロセスでは検出不能**(source_class 真正性と同型の leaf self-report、根が一段下へ)。
- **MEASURED/REPRODUCED 未導出**: measurement/reproduction 観測は現状 UNRESOLVED へ倒す。Activity/run type と
  Measurement schema/Reproduction link を入力に持つ mode candidate 導出は F3a フル(Phase 1b)。
- **demo は driver-injected**: Gate4 finding は著者が手で与える(実運用は別セッション/人間の対話ステップ)。
  取得境界(retrieval/LegIntent)は未実装ゆえ証拠は手投入。demo は grounding *層* の通行試験であって
  取得の実装ではない。
- **back-compat**: R6 以前の NormalizedObservation は observation_kind を持たない(§5-D で挙動を実弾確認)。

---

## 5. attack checklist(local agent が実弾実行)

- **A. 継ぎ合わせ(cross-source stitching)**: PRIMARY(UNSPECIFIED)+ 別 source の DECLARATION を混ぜて
  DECLARED を得られるか。著者主張=同一観測要求で封鎖。
- **B. GENERATED+DECLARATION**: GENERATED を DECLARATION 標識しても contamination で UNRESOLVED に倒れるか。
- **C. MEASUREMENT 正当性**: MEASUREMENT+PRIMARY→UNRESOLVED、NEGATIVE+MEASUREMENT→UNRESOLVED を確認。
- **D. 空/不正/back-compat**: evidence なし・dangling relation・observation_kind 欠落(R6 前 event)で
  crash/誤ラベルが出ないか。
- **E. demo が driver-honest-replay か(DE-0005 型)**: validation_mode=UNRESOLVED は真に導出か(kind を
  DECLARATION に変えれば DECLARED に flip するか)、GC-7 block は本物か(known_omissions を空にすれば通るか)、
  ABSENCE は構造か(leg を FAILED にすれば block するか)。counter-factual を実行。
- **F. その他**: 上記 §4 の宣言に**載っていない**未保証性質。見つかれば恒久対策/自認リストの穴。

---

## 6. 著者が主張しないこと(明示)

- L4/validation_mode_derivation 全体の VERIFIED は要求しない。**source_class-only 穴の閉塞のみ**。
  observation_kind self-report と MEASURED/REPRODUCED 未導出は残る。
- R6 は Phase 1a 安全側。MEASURED/REPRODUCED を賢く導出する能力は**無い**(意図的に UNRESOLVED へ倒す)。
- demo は**取得(retrieval)の実装ではない**。証拠は手投入、Gate4 finding は driver-injected。
- kind 詐称・source_class 詐称は単一プロセスでは**検出不能**(prevention は騙らない)。

---

## 7. 依頼する出力

`REVIEW_LEDGER.jsonl` へ **JREV-0003**(同形式):
- property 毎の verdict + evidence_basis(counter-factual / **コード敵対レビュー実行**(§3)/ 設計レビューの別を明記)。
- §4 の非保証のうち**著者が過小評価しているもの**があれば指摘。
- §3 の attack が1つでも §4 の外に confirmed defect を出せば、DE 起票 → 修正 → JREV-0004。

台帳: DE-0026(R6)/ DE-0027(demo)/ `egl/contracts.py` / REVIEW_LEDGER.jsonl JREV-0001・0002。
関連: REVIEW_PACKET_JREV0002.md。
