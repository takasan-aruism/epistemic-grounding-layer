# EGL Walking Skeleton — Batched Review(Taka 用)

日付: 2026-07-05  対象: `/home/takasan/egl`(Drop1/Drop2 + component 分解)

## 0. 方法(この review 自体が今日の主題の実践)
本 review = **独立敵対レビュー(別セッションの general-purpose agent)+ 著者自己レビュー**の統合。
今日実証した通り「別視点は自己盲点を超える」——独立パスが、著者(私)が見落とした構造的欠陥を掘り当てた。
**私が過去ターンで報告した主張のうち、過大だったものを本 review で訂正する。**

## 1. 正直な見出し
- **歩いた**: 2滴貫通、全 object 型が流れ、**RC-3 は本物**(view は events から決定的再構築)、outcome の分岐(ACCEPT/EVIDENCE_INSUFFICIENT/ABSENCE/BLOCKED)は正しくルートする。
- **しかし**: 差別化機構の中核 3つ(**SC-2 / GC-7 / dedup**)は、**構造で強制されておらず「driver の正直さ」で通っていただけ**。独立レビューが露呈。

## 2. 私の過去報告の訂正(最重要)
| 私が言った | 実際(独立レビュー) |
|---|---|
| 「ABSENCE を **SC-2 が構造ブロック**」 | ❌ gate3 は `SearchConclusion.status` を**そのまま信用**。status は driver が渡す引数。leg の FAILED event を gate は一切見ていない。負テストが通ったのは run2 が正直に COMPLETED/INCOMPLETE を渡したから(**driver 正直性のテストであって構造強制のテストではなかった**)。**H1 = BLOCKER** |
| 「**GC-7 が飛躍を遮断**」 | ❌ `gc7_lint` は `run.py` の**スタンドアロンdemo**でしか呼ばれず、`curator.curate` の gate 連鎖に**未接続**。しかも scope_echo の自己申告キーだけ見るので、キーを省けば素通り。**H4 = HIGH** |
| 「dedup 全走査(CS-1)」 | ❌ `gate2` は候補集合を計算するが `decide()` は `gate2` を**本体で一切参照しない**(dead)。同 claim_key の矛盾する2 claim が両方 ACCEPT され得る。**H3 = HIGH** |
| 「CU-1 を**構造で強制**」(COMPONENTS seam2) | ⚠️ 過大。`apply_outcome` は public で outcome 引数を再検証せず、`append_event` に型ガードもない。**規律では成立、構造では未強制**。**M1 = MEDIUM** |

→ 「コードが正しい値を計算して、それを捨てている」型の欠陥(H1/H3)= **まさにこの層が防ぐべき失敗モードを、実装が犯していた**。自己レビューでは気づけなかった。

## 3. 独立レビュー findings(重大度順・全て CONFIRMED)
| id | 欠陥(1行) | 重大度 | 処分 |
|---|---|---|---|
| H1 | SC-2 が自己申告 status を信用、leg event を再導出しない → 偽の不在が作れる | BLOCKER | **build-out 即修正** |
| H2 | cited conclusion が候補の gap/scope に束縛されない(Xの不在をYの調査で証明可) | HIGH | build-out 即修正 |
| H3 | gate2/importance を計算して decide が無視(dedup/conflict 非機能) | HIGH | build-out 即修正 |
| H4 | GC-7 が curate に未接続 + 省略で素通り | HIGH | build-out 即修正 |
| H5 | `counters.json` が events から導出不能な**第2の SoR**。喪失で ID 衝突→merge 事故 | HIGH | **Taka 裁定**(UUID化 or log から high-water 復元) |
| H6 | `new_id`/append に lock なし → 並行 run で ID 衝突 | HIGH(並行時) | build-out(並行前に) |
| M1 | CU-1 は規律であって構造でない | MED | build-out(write guard) |
| M2 | RD 供給の `polarity` が制御分岐(Gate4/GC-1 を skip) | MED | build-out(H1 と併せ) |
| M3 | dangling nobs/source で clean-fail でなく **crash**(None 添字) | MED | build-out 即修正(小) |
| M4 | `build_view` の shallow merge → nested 部分更新で兄弟キー喪失(潜在 RC-3 バグ) | MED | **Taka 裁定**(「event は nested を完全形で持つ」を契約化 or deep-merge) |
| M5 | importance が dead(H3 と同根、必須claimの審査バーが上がらない) | MED | build-out |
| M6 | 全 ABSENCE が `claim_key="ABSENCE:documents()"` に潰れる | MED | build-out(H3 有効化前提) |
| L1-L5 | GC-8 過剰ブロック/scale O(N·M)/RC-4 テスト弱い/hardcoded policy/ts 境界 | LOW | 一部 Taka 裁定(L4) |

## 4. Taka 裁定が要る点(著者では決められない)
- **H5**: ID を UUID/content-based にするか、event log から high-water を復元するか。「SoR は1ファイル」を守るなら後者。
- **M4**: event-sourcing を「常に完全 object を書く(coarse)」で固定するか、deep-merge にするか。RC-3 の正しさの前提。
- **L4 hardcoded**: ABSENCE TTL=14日 / 全受理 claim に `bootstrap:True` 一律付与(非bootstrapにも)/ validation_mode 既定 `DECLARED` / reopen plan が常に `COV-TECH-STANDARD`。

## 5. build-out 順の**組み替え提案**(COMPONENTS の順を上書き)
(a) の当初順は「refactor 先(mk_candidate/search.py)」だった。**独立レビューを受けて逆にする**:
1. **構造強制を先に**(H1 coverage を leg event から再導出 / H3 decide に gate2・importance を効かせる / H4 GC-7 を curate に接続 / M3 dangling guard)。これらは小さく、**skeleton の「実証」を「実際に強制」に変える**。
2. H5/M4 は Taka 裁定後に SoR 契約を確定。
3. その後に refactor(mk_candidate / search.py / Axis / Adjudicator Protocol)。

理由: 現状 skeleton は **shape は通したが enforce はしていない**。refactor で綺麗にする前に、**enforce を入れないと 2滴の operational stream の解釈が「driver が協力した」に留まる**。

## 6. 実際に成立しているもの(as-coded)
- **RC-3**(counters.json の留保付き=H5)/ **CU-1 は今日のコードでは成立**(Claim を書くのは apply_outcome のみ、gates は read-only)/ pipeline shape / GC-1・GC-4(relation+fragment の2 hop)/ outcome 分岐 / event log = 正本。

## 7. 総評
walking skeleton の**本来の目的(shape 貫通・型違い2本・コードから seam 抽出)は達成**。だが**差別化機構の enforce は未達**で、私の「構造ブロック」報告は過大だった。独立レビューがそれを捕えた=**今日の主題(別視点監査)の、我々自身の成果物での再実証**。
→ 推奨: **§5 の順で H1/H3/H4/H5 を最初の build-out**にする(小さく、実証を本物にする)。その後 refactor。

---
付記: 本 review の独立パスは別セッション agent(53k tokens)。これ自体が AM-13/AM-14(別視点・extraction independence)の運用実例であり、DESIGN_EVIDENCE_LEDGER に DE-0005 として記録。
