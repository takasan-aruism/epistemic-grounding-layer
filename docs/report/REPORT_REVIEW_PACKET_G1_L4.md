# EGL build-out G1〜L4 独立レビュー用パケット

日付: 2026-07-05  対象 commit 範囲: `5bd7643`(skeleton)→ `1a982e7`(AB-0007)
レビュー方針: **DE-0014**(Taka 裁定)。drop 毎でなく **G1〜L4 を一括**で見る。

---

## 0. レビュアーへの依頼(mandate)

このパケットは、build-out 系列(G1 enforce 群 + SoR 契約 DE-0006/0007/0008 + AB-0007)に**独立敵対レビュー**を当てるための地図です。著者(Claude Code)による自己申告は信用しないでください。DE-0005 で、著者は「構造ブロック」を過大報告し、それを独立レビューが捕えました。**同じ目で、今回の系列を疑ってください。**

### レビューの唯一の観点(Taka 指定)
> **各 enforcement は「信用の根(root of trust)」をどこへ移したか。その移動先の根は、書込権限で守られているか。それとも self-report を一段下へずらしただけか。**

全 drop が同型の「信用の根の移動」を含むため、連鎖(例: leg event → 誰が source_kind を書くか → 取得ラッパー → …)は**一括でないと追えません**。§2 の表と §3 の連鎖トレースがレビューの出発点です。**§4 に、著者が自認する『根がまだ self-report に落ちている箇所』を先に開示します**——ここを潰せるか(=著者の自認が甘くないか)が主戦場です。

このレビューが通れば、本 build-out 系列に**初の JUDGE_VERIFIED** が付きます。現状は全 drop が `ENGINEERING_FORCED / test-verified` 止まりです。

---

## 1. 事実基盤(as-coded、レビューの一次資料)

- **唯一の log 書き手**: `events.jsonl` を追記するコードは `core.append_event`(core.py:113)**のみ**。他に直接書く経路は無い(grep 確認済)。= 書込権限境界は1関数。
- **SoR**: `data/events.jsonl`(append-only 正本)。`state.sqlite` は導出 view(RC-3 で決定的再構築)。
- **テスト**: `test_enforce.py`(enforce 群 13 件)/ `test_sor.py`(SoR 契約 23 件)。両者 `EGL_DATA_DIR` で canonical SoR と隔離(AB-0005)。
- **試験文化**: DE-0009 の counter-factual(出力反転で outcome 変化を要求)+ 注入層原則(境界より下の層から注入)。H6 lock にも適用(lock 無効化で 120採番→51 uniq を実測)。

---

## 2. 信用の根の移動表(レビューの核)

| drop | 欠陥時の根 | 移動後の根 | 書込権限で守られているか | 残る攻撃面(§4 で詳述) |
|---|---|---|---|---|
| **H1** SC-2 | `SearchConclusion.status`(driver 引数=summary 自己申告) | leg event(per-leg の kind+status)を gate3 が再導出 | △ 部分的 | leg の `source_kind`/status は RD 供給。**leaf self-report が取得境界に残存** |
| **H3** dedup | 無(dead code、両 ACCEPT) | `gate2` の claim_key 衝突走査 + importance | ○ decide→apply_outcome(sole writer) | `claim_key` は RD の scope 由来。**identity gaming**(軸を足して key を割る) |
| **H4** GC-7 | 無(未接続)/ scope_echo 自己申告 | 構造 scope キー ∩ ground の known_omissions | △ 部分的 | `known_omissions` は ground claim の RD 自己申告。**未宣言なら vacuous** |
| **M3** dangling | (crash) | clean-fail(DEFER) | — 堅牢化のみ | (根の移動ではない) |
| **AB-0003** bootstrap | 一律 True(無意味) | `finding.teacher_signal` 由来導出 | ○ apply_outcome | `teacher_signal` は Finding で True 固定(35B 移行時に要再設計) |
| **DE-0006** id | `counters.json`(第2 SoR、喪失で衝突) | event log high-water(単一 SoR)、id-in-append | **◎ 完全** log=書込境界、lock 内採番 | append_event bypass(現存せず)/ lock 喪失(counter-factual 済) |
| **DE-0007** M4 | driver 正直性(partial で兄弟喪失) | `_check_complete_revision`(validator) | **◎ 完全** sole writer 内 | **2段以深の nested partial**(guard は1段) |
| **DE-0008** L4 mode | 自己申告 `validation_mode`(既定 DECLARED=捏造) | `derive_validation_mode`(provenance 導出) | △ 部分的 | `source_class` は RD 供給。**leaf self-report が取得境界に残存**(H1 と同型) |
| **DE-0008/AB-0007** correction/completion | (append-only 訂正機構が無い) | `CORRECTION`/`COMPLETION` event(sole writer, 完全 revision) | **◎ 完全** | (機構自体は保護済。適用の妥当性を問う) |

**◎=根が書込境界そのものへ移った(最強) / △=根を leaf 自己申告へ一段下げた(改善だが未完) / ○=根は sole writer 内だが導出入力に RD 依存**

---

## 3. 根の連鎖トレース(一括でないと追えない部分)

### H1(coverage の根)
`curate` → `gate3_authority` → `_derive_checked_kinds(con, plan)` → `by_type(Run)` で `leg_plan_id==plan and status=="COMPLETED"` の `source_kind` を収集 → `evaluate_coverage` 再評価。**`scon.status`/`coverage_result` は非参照**。
- 移動: summary(scon.status)→ per-leg fact(各 leg の kind+status)。RD は「complete」と一言で主張できず、**必須 kind ごとに COMPLETED leg を実在させる**必要がある。
- **根の底**: leg の `source_kind`/status を書くのは `mk_search_leg`(pipeline.py:67)で、**値は RD が引数で渡す**。→ 偽の不在を作るには「実際には確認していない kind の COMPLETED leg を捏造する」必要がある。**この捏造を防ぐのは未実装の取得ラッパー**(実 fetch 成功時のみ leg を COMPLETED で書く層)。skeleton の `simulate_fail` はその stub。
- **レビュー質問**: gate3 が leg を見ているのは本物か(T1c で実証: scon.status の嘘を固定し leg 反転で outcome 変化)。だが「leg 自体の捏造」は防げていない——著者はこれを §4-A で自認。**この自認は正しいか、それとも gate3 に他の穴があるか?**

### L4(validation_mode の根)— H1 と同型
`apply_outcome` → `derive_validation_mode(con, candidate)` → grounds を辿り `src["source_class"]`(gates.py:91)を収集 → PRIMARY 到達で DECLARED / ABSENCE は SC-2 coverage 由来で SPECIFIED / else UNRESOLVED。**候補の自己申告 validation_mode は不使用**。
- 移動: 自己申告(既定 DECLARED の捏造)→ provenance 導出。**既定値の捏造は完全に消えた**(導出不能は UNRESOLVED)。
- **根の底**: `source_class` を書くのは `mk_source`(pipeline.py:10)で、**値は RD が引数で渡す**。→ GENERATED を PRIMARY と偽れば DECLARED が導出される。**この偽装を防ぐのも未実装の取得/分類ラッパー**。
- **レビュー質問**: H1 と L4 は**同一の未完(取得境界の leaf self-report)を共有**。この2つを別々に見ると「provenance 導出=解決」と誤読しやすい。一括で見ると「両者とも根は source の RD ラベルに落ちる」ことが見える——これが Taka が一括を要求した理由。**この共有欠陥の射程は他の drop にも及ぶか?**

### H3(dedup の根)
`decide(finding, gate2, importance)` が gate2 の `dup_conflict_candidate_ids`(同 claim_key の既存 Claim)があれば `CONFLICT_REVIEW_REQUIRED`(claim を書かない)。`claim_key` は `core.claim_key`= ESTABLISHED_AXES の scope 部分集合から生成。
- **根の底**: claim_key は RD の scope 由来。**ESTABLISHED_AXES に無い軸を足しても key は不変だが、ある軸に偽の値を入れれば key が割れて衝突を回避できる**(identity gaming)。
- **レビュー質問**: T2 は claim_key 一致で CONFLICT・不一致で ACCEPT を実証(gate2 が live)。だが「意図的に key を割って二重 ACCEPT」は防げるか?ESTABLISHED_AXES の選定は健全か?

### DE-0006 / DE-0007 / CORRECTION(◎ の根)
- **id**: `append_event` が `_idlock` 内で `_high_water(log)` から採番し、同一 critical section で書込。**根 = log そのもの = 書込境界**。id が存在する ⟺ event が存在する。H6 lock は load-bearing を counter-factual で実証(§5)。
- **completeness**: `_check_complete_revision` が append_event の lock 内(SELF 置換後・書込前)で UPDATE/CORRECTION/COMPLETION の完全 revision を要求。**根 = validator = sole writer 内**。
- **correction/completion**: 原 event 不変、後続 event で訂正/完結、provenance(from/to)を残す。**根 = append-only + sole writer**。
- **レビュー質問**: これらは根が書込境界へ移った最強例。破るには append_event bypass(現存せず)か lock 喪失(実証済で load-bearing)。**bypass 経路を1つでも見つけられるか?** M4 は1段 nested までしか見ない——**2段以深の partial を通せるか?**(§4-B で自認)

---

## 4. 著者が先に開示する未完(ここを潰せるかが主戦場)

正直開示。レビュアーはこれらが「本当に列挙し尽くされているか」「各々の射程を過小評価していないか」を疑ってください。

- **§4-A 取得境界の leaf self-report(H1・L4 共有)**: coverage(H1)と validation_mode(L4)の根は、最終的に RD が書く `source_kind` / `source_class` に落ちる。実 fetch を検証する取得ラッパーが未実装。**現状の保証は「RD は summary を主張できず、consistent な primitive を実在させねばならない」まで**——primitive 自体の真正性は未保証。次の根の移動先はここ。
- **§4-B M4 は1段 nested まで**: `_check_complete_revision` は top-level + 1段 nested の superset のみ検査。2段以深の partial は RMW 規律で担保するが構造強制ではない(deep validation は MOR-1 待ち)。
- **§4-C H4 の known_omissions は自己申告**: ground claim が omission を宣言しなければ gc7 は vacuous pass。omission の構造的導出(second-extraction/AM-15 相当)は MOR 待ち。
- **§4-D provenance ラベルの正直さ**: 全 drop は `ENGINEERING_FORCED / test-verified`。counter-factual/注入試験は通すが、独立レビューは今まさに初回。**このレビュー前に JUDGE_VERIFIED を名乗っていない**(台帳で確認可)。

---

## 5. テスト証拠の棚卸し(counter-factual を含む)

| 試験 | 件数 | 決定的な counter-factual / 注入 |
|---|---|---|
| `test_enforce.py`(enforce 群) | 13/13 | **T1c**: scon.status の嘘を固定し leg 反転→outcome が ACCEPT⇄ABSENCE_BLOCKED_SC2(判定は leg 依存)。T2c/T3b/T4b も反転で outcome 変化=gate live |
| `test_sor.py`(SoR 契約) | 23/23 | **H6**: lock 無効化で 120採番→51 uniq(69衝突)、有効で 120/120。T6/T7: partial(top/nested)reject・完全は通る。T8: UNRESOLVED counter-factual。T9/T10: 原 event 不変(append-only)・from/to provenance |
| `verify_rebuild.py` | RC-3/RC-4 PASS | id-in-append・完全 revision・correction 後も view は log から決定的再構築 |

全系列を通して `run.py`/`run2.py` 無退行。

---

## 6. レビュー attack checklist(推奨)

1. **§4-A の射程**: leaf self-report(source_kind/source_class)に根が落ちる drop を H1・L4 以外に見つけられるか。
2. **append_event bypass**: sole-writer 境界を回避して log/state を変える経路はあるか。
3. **M4 深いネスト**: 2段以深の partial update を通し、兄弟喪失を再現できるか。
4. **identity gaming(H3)**: claim_key を割って矛盾2 claim を両 ACCEPT させられるか。ESTABLISHED_AXES は健全か。
5. **H1 leg 捏造**: gate3 の再導出を、偽 COMPLETED leg で騙せるか(=取得ラッパー不在の実害)。
6. **derive の穴(L4)**: PRIMARY 判定・ABSENCE→SPECIFIED の導出に、provenance 無しで concrete mode が付く経路はあるか。
7. **correction/completion の悪用**: CORRECTION/COMPLETION で不正な state 遷移(例: REJECT 済 claim の status 復活)を作れるか。M4 guard はそれを許すか。
8. **試験の自己欺瞞**: counter-factual が「本当に根を検査しているか」、それとも driver 正直リプレイに退化していないか。

---

## 7. 判定ゲート

- レビューが上記を潰し、confirmed な欠陥が **§4 の自認範囲に収まる**なら → build-out 系列に**初の JUDGE_VERIFIED**。§4 は既知・許容の未完として backlog 化。
- レビューが **§4 の外**に confirmed 欠陥を出すなら → 著者の自認が甘かった証拠。DE 起票 → 修正 → 再レビュー。DE-0005 と同じ手順。

台帳: DE-0010(G1)/ DE-0011(順序)/ DE-0012(H5/H6)/ DE-0014(本レビュー方針)/ DE-0015(M4)/ DE-0016(L4+correction 形式)/ DE-0017(AB-0007)。
関連レポート: `REPORT_BUILDOUT_G1.md`(enforce 詳細)/ `REPORT_SOR_CONTRACT.md`(H5/H6 詳細)。
