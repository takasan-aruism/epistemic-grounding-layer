# 2DER / RRI 明細連動型 ESDE 管理 — 設計 v0.2（★実測反映版）

**発: 監視（3Claude の外部・以下 CC_ALPHA） ／ 宛: Taka ・ ESDE Evaluation 専任監査 ／ ✔ は付けていません**
**原案: Taka「設計素案 v0.1」（2026-08-23・GPT との議論を経たもの）**
**★コードは1行も変えていない。★新しい Manager / Worker / 台帳 / ID / 経路 / state を1つも作っていない。**
測ったHEAD: egl `a78ff78` / twoder `09a7462` / rri `f7d0ac0` / dev-workcell `ffe36a7`
測った時刻: 2026-08-23 17:0x〜17:3x

---

## 0. この版で変わったこと（v0.1 → v0.2）

| # | 変更 | 根拠 |
|---|---|---|
| 1 | **既存正本3本との関係を明記した** | 素案は `ESDE_EVALUATION_DOMAIN_MANAGER_v0.1`（8/20）・その `_OPERATING`（8/21）・`CC_MGR_2026-08-22_DECLARED_ESDE_INTEGRATION_ARCHITECTURE`＋追補2本（8/22）に**1つも触れていなかった** |
| 2 | **§17 の16項目を実測で埋めた** | 下記 §3 |
| 3 | **「明細を主入力面にする」の前提が現状では成立しないことを数で示した** | 構造化明細は **635スレッド中 1本**にしか無い（§4） |
| 4 | **DESIGN_HOLD が機構として存在しないことを実測** | `DESIGN_HOLD` の語はコード上 **0件**（§3-12） |
| 5 | **Taka 裁定を記録** | ESDE Research（44GB）は**既存研究として分離**。今回は ESDE 理論そのもので開発を構造化する。融合は将来（§2） |
| 6 | **並行改修の注意を明記** | 台帳・明細は**本日も改修が進行中**。本書の数値は**測った時刻の値**（§8） |

---

## 1. 位置づけ ―― 既存正本との関係（★素案の最大の欠落）

素案は「既存構造へ適合させることを前提とする」と書きながら、**既に在る ESDE 正本と、その統合設計を参照していない**。
本 v0.2 は素案を捨てず、**既存3本の続きとして接続する**。

```
① ESDE_EVALUATION_DOMAIN_MANAGER_v0.1.md（8/20・Taka 受領）★指標の正本
     対称性 / 連動性 / 階層性 を 分母・分子・欠損ID で 測る。総合点に潰さない。
     §6 に 導入順序①〜⑥ が既に在る（①済 ②一部済 ③〜⑥ 未）
     §7「次に決めること = 階層性の required boundary を どこから 機械取得するか」で止まっている

② 同 _OPERATING.md（8/21・12KB）運用規則

③ CC_MGR_2026-08-22_DECLARED_ESDE_INTEGRATION_ARCHITECTURE.md ＋ 追補2本（883行）
     IDENTITY / CALLER / TIMING / INPUT / OUTPUT / STORAGE / READER / AUTHORITY / TEST の9項目を実測
     ★結論 = DESIGN_HOLD（GO条件12件中 5件のみ充足）
     ★追補2 で「READER が MISSING」を撤回 = `domain_dw.record_stages` という前例が本線で回っている
```

**★素案の4処理（CONCEPTUALIZE / MEASURE / INTERPRET / DIRECT）と、正本の3指標（対称性・連動性・階層性）は
競合しない。**3指標は **MEASURE の中身**であり、素案は**その外側の運転**を定義している。
∴ **v0.2 では「素案＝運転の型」「正本＝測り方の型」として重ねる**。差し替えない。

**★素案が新しく持ち込んだ本質的な主張は1つ:**
> ESDE 管理は**主経路の19番目の工程ではなく、外側から追う Control Plane**である。

これは正本にも declared にも無い視点で、**採用に値する**。理由は §6 で実測に基づいて述べる。

---

## 2. Taka 裁定の記録（2026-08-23）

**逐語:**
> ESDE Research は既存研究。今回の ESDE はアリズム哲学を実践的に導入する ESDE 理論そのもの。
> そしてその理論を使って開発を構造化するというのが今回の目的。Research は将来的な融合目的。分けてよし。

**∴ 本設計の範囲:**

```
★範囲内   ESDE 理論を 2DER の開発構造化に適用する（＝本書）
★範囲外   /home/takasan/esde/ESDE-Research（44GB / 43,069 files）
           ＝ 既存研究。将来の融合対象。今回は調査しない。
★∴ declared 本体 §11b の `ESDE_RESEARCH_ASSETS_UNSURVEYED` は
    「未調査」ではなく「★裁定により範囲外」として閉じる。
```

**★併せて記録する私の誤り:** 私は本日、`egl/egl/esde_stream.py` を見て「ESDE という語が2つの別物を指している」と
Taka に報告した。**これは MGR が 8/22 に書いて Taka が既に訂正した論点の蒸し返しだった**
（declared 本体 §0 訂正1 =「同一原理の複数世代が同居しているのであって CONFLICT ではない」）。
**既存の declared を読む前に報告したのが原因。**本書 §1 の欠落と同じ型である。

---

## 3. §17 の16項目 ―― 実測（★推測で埋めない）

| # | 項目 | 状態 | 実測 |
|---|---|---|---|
| 1 | 明細の writer / reader | **PRESENT** | writer=`rri.request_thread.record_typed` **1つ** ／ reader=`list_typed` `list_questions` `project` ＋ front door の明細UI（8/23 `3d3b7bb`） |
| 2 | 明細 ledger の正本性 | **PRESENT** | `rri/rri/rthread_events.jsonl` rows=**3,350** / liveness=**LIVE** / role=**CANONICAL**（8/23 `4400945` の登記再生成で 55→56冊・rthread=CANONICAL） |
| 3 | 後付け annotation の既存経路 | **PRESENT** | `annotate_question` **920件** ／ `record_typed` **132件** ／ `record_actor` **36件**。いずれも append。**上書きしない** |
| 4 | account assignment | **PRESENT** | `QUESTION_ACCOUNT_PROPOSED` **645件** ／ 段1（決定論・`account_gate.decide`）＋段2（3seed 合議）／ 2層の科目 = **カテゴリ6・詳細52**（8/23 `a78ff78`） |
| 5 | relation / related ID | **PARTIAL** | `QUESTION_TYPED.refs` = **12 / 132件**。抽出は `twoder/detail_refs.extract_refs`、実在確認は `twoder/ids.py`。**relation の意味（`derived_from` 等）は持っていない**＝素案 §6.5 は未実装 |
| 6 | source / evidence の既存保存 | **PARTIAL** | `source_text` **132/132** ・`source_span` **132/132** ＝ **原文と位置は在る**。**外部 source（URL / retrieved_at / evidence text）の欄は無い**＝素案 §6.4 の一般調査側は未実装 |
| 7 | unresolved / gap | **PARTIAL** | `kind=UNVERIFIED` **4件** ／ `OPEN_GAP` は `twoder/requirement_gaps.py` `submit.py` `webui.py` `rri/request_thread.py` に在る（段3・8/23 `87d0cc3`）／ **`present_gaps` の本線呼び手は 0**（呼ぶのは `egl/docs/audit_rthread_stage1.py` のみ＝監査用） |
| 8 | measures | **PRESENT（★欠陥つき）** | front door `/api/control?include=` の **14面**に `edge_measures` `static_edges` `observed_edges` が在る。**★既知欠陥**＝`static_edges` は 2,926 candidate を数えるが個別の辺を返す欄が **0**／`observed_edges` は 1,444辺に対し返るのは **top_rows 30 のみ**（declared §11） |
| 9 | ESDE 正本 | **PRESENT（★未受入）** | `ESDE_EVALUATION_DOMAIN_MANAGER_v0.1.md`（8/20）＋`_OPERATING.md`（8/21）。**★但し状況表の「Taka にしか出せない件」に載ったまま＝受入が閉じていない** |
| 10 | ESDE 評価結果を保存できる既存 event | **PRESENT（候補2つ）** | ①`ETRACE` の `CONTRACT_STAGE`（`domain_dw.record_stages` の前例・新台帳0）②`function_table`（`register↔revoke` の対称性・単一writer・front door に reader） |
| 11 | RRI へ不足情報を戻す既存経路 | **PARTIAL** | 段3 `OPEN_GAP`（8/23 実装・「依頼に書かれていないものを数えて人へ返す」）が最も近い。**`present_gaps` は本線に呼び手が無い** |
| 12 | PLAN / HOLD へ作用できる既存経路 | **★ABSENT（HOLD）／ PRESENT（別形）** | **★`DESIGN_HOLD` の語はコード上 0件**＝機構として存在しない（文書の語である）。代わりに `completion_blockers` が `workcell` `upper_review_gate` `dispatch` `senior_review` `return_loop` ほか **11ファイル**に在る |
| 13 | COMPLETE 前に評価を差し込める既存経路 | **PRESENT** | `completion_blockers` ＋ `LINKAGE_EDGE_NOT_OBSERVED`（`dev-workcell/dw/workcell.py`）＝**連動性の欠損で完了を止める門が既に在る** |
| 14 | UI が既に読める面 | **PRESENT** | `/api/control?include=` の **14面**（`route_table` `plus_minus` `authority_summary` `anatomist` `static_edges` `route_edge_votes` `route_table_view` `question_reviews` `route_edge_votes_v2` `edge_measures` `observed_edges` `function_table` `function_index` `function_first`）＋ 明細UI（段1/2/3・誰が書いたか）＋ `self_check.json` |
| 15 | 類似 task / embedding / account cluster | **PRESENT** | `s_embed_axes`（e5-small・CPU・決定論）＋ 2層の科目（母数644・カテゴリ6/詳細52・命名 英57/日56 成立・`--check` GREEN） |
| 16 | template / reuse / learning 相当 | **PARTIAL** | `failure_memory` の照合が最も近い＝**633回発火・41回 BLOCK**（本線 `submit.py` `webui.py` `preflight_gate.py`）。**★但し「型」として完全な記録は 7件中 2件のみ**（§5）。task テンプレート化・必要情報予測は**無い** |

**★CONFLICT（declared から継承・未解消）**

```
TWO_REGISTRIES_SHARE_THE_ART_ID_FORMULA
  twoder/audit/ARTIFACT_REGISTRY.jsonl（front door が resolve・222件）と
  egl/docs/CC_REGISTER.jsonl（role=IDLE・resolve されない）が
  ★同じ 'ART-'+sha1(repo|path)[:10] を発行する ∴ id を見てもどちらの登記簿か分からない
```

---

## 4. ★素案の中心前提は、現状では成立しない

素案 §5「**明細は ESDE の主入力面**」。これを実測した。

```
THREAD_OPENED              635 本
QUESTION_RAISED            979 件
QUESTION_ANNOTATED         920 件
QUESTION_ACCOUNT_PROPOSED  645 件
★QUESTION_TYPED（構造化明細）132 件 ／ ★スレッドの異なり = 1

★∴ 構造化明細を持つ依頼は 635本中 ★1本（0.16%）。
```

構造化明細の中身（その1本）:

```
kind   SPEC 32 / FACT 28 / TEST 24 / CHANGE 23 / CONSTRAINT 13 / GOAL 8 / UNVERIFIED 4
       ★素案 §6.2 の6語と ★完全に一致（＋UNVERIFIED）＝ 語彙は既に実装されている
kind_basis   132 / 132（★根拠の欄は全件埋まっている）
source_span  132 / 132（★原文の位置は全件在る）
refs          12 / 132
goal          26 / 132
action        38 / 132
recorded_by  ACTOR_RECORDED 36件 ・ 全て `claude-mgr`
```

**∴ 読み方は2つに分かれる。**

```
★良い方  素案 §6.2〜§6.3 が要求する欄は ★もう在る。設計ではなく ★運用が1本しか無い。
★悪い方  ESDE が明細を主入力にすると、いまは ★1依頼しか見られない。
          残り634本は QUESTION_RAISED / ANNOTATED どまりで ★kind を持たない。
```

**★∴ v0.2 の判断: 明細を主入力面にする方針は維持する。ただし「明細が育つのを待つ」設計にしない。**
初期の ESDE は**明細が無い依頼でも測れる面**（§3-8 の `edge_measures` / `observed_edges` /
`function_table` / 経路表）を主入力とし、**明細は在る時に精度を上げる補助入力**として扱う。
明細が全依頼に行き渡った時点で主従を入れ替える。

---

## 5. ★「失敗の型を拾う」は、勘定科目では成立しない（実測）

素案の出発点（Taka）は「**台帳から破綻を拾い、ESDE 的に調査して内部で解決する**」だった。
勘定科目を経路にできるかを実測した。

```
2層の科目 58本のうち 失敗系の語を持つもの     ★0 / 58
明細 645件のうち 失敗系の語を含むもの          33件（5%）
その33件の行き先                              ★13本の科目に散在
   契約定義8 / データ統合ツール7 / 入力検証3 / 独立検証3 / 監査調査2 …
```

**理由は構造的:** 勘定科目の軸は「**何の作業についての依頼か**」で切れている。
「うまくいったか / 落ちたか」は**直交する別の軸**であり、どれだけ細かく割っても失敗系の科目は出ない。
**明細の本文は依頼文であって結果ではない**ため。

**★失敗は既に別の場所に在る:**

```
twoder/failure_recurrence.jsonl  ★633行  照合の発火記録（BLOCK 41 / WARNING 592）
                                 期間 2026-07-11 〜 2026-08-23（★今日まで生きている）
                                 発火した型 FAIL-001 292 / FAIL-002 167 / DEAD-scheduler 33 / DEAD-afe-detector 8
twoder/failure_memory.jsonl         7行  失敗の型そのもの
twoder/failure_classifier_schema.py      6クラス（EXECUTION / DESIGN / KNOWLEDGE / TEST / RESOURCE / UNKNOWN）
```

**★但し「型」として完全なのは 7件中 2件だけ:**

```
FAIL-001 / FAIL-002   ★誤解・正しく・部位・fix_ref・audit_ref・regression_ref・post_fix_result・match_signal が全て在る
                      ★この2件が 発火 633回のうち 459回を占める
DEAD-* 5件            ★欄が全て空（誤解も 正しくも 部位も 証拠も None）
                      ★status は CLOSED_NEGATIVE / WEAK_NEGATIVE / AUDITED_AND_REJECTED /
                        NOT_CONFIRMED / CONFOUNDED_DEMOTED ＝「この道は行き止まりだった」という
                        ★実験の結論であって 失敗の型ではない
                      ★BLOCK 41回は この5件が出している
```

**★分類の記録（`failure_classification_id`）は 55冊すべてで 0件。**
`manager_v0.py:160-168` は本線で分類レコードを組んで `escalation_router.route()` に渡すが、
**`selected_class` は常に `FAILURE-UNKNOWN`**。逐語:

> ★`FAILURE-UNKNOWN` = ★原因を 決めつけない。★私は 失敗の 種類を ★推測しません。

`escalation_router.py` には**書き込みが1行も無い**（`Deterministic, hermetic` と逐語）。
∴ 判定器は書かない設計で、呼び手が残すのは `failure_class` **1語だけ**。

**★これが ESDE の最初の具体的な仕事になる:**
6クラスのうち5つが一度も選ばれないのは、**「どの証拠が揃えばその型を名乗ってよいか」という規則が
まだ書かれていないから**である。分類器の欄（`supporting_evidence_ids` / `required_missing_evidence`）は
そのために既に用意されている。

**★同時に、原理的な分かれ目が在る（★私の判断で決めない）:**
FAIL-001/002 が実演している4点（`fix_ref` + `audit_ref` + `regression_ref` + 責任部位）は
**「直した後」でないと揃わない**。失敗した瞬間には存在しない。
∴ **型を名乗るのを「直った後」に限るなら現状の設計は正しく、蓄積が0なのは「まだ直っていない失敗が
型を持てない」だけ**である。ESDE が欲しいのが「**いま壊れている所**」なら、必要なのは分類器ではなく
**直る前の失敗に付けられる別の指標**になる。**この線引きは評価の型そのもの＝ESDE の定義に属する。**

---

## 6. ★「経路の外側の Control Plane」を採用する理由（実測）

素案 §2〜§3 の主張を、実測が支持する。

```
①正本が 明示的に 分業を切っている
   `route_worker` 冒頭の逐語 =「★これが判断しないもの: 期待された機能か / 結果が正しいか /
    この機能は必要か / ★他機能との連動が正しいか / 全体目的との整合性 ―― どれも Manager の仕事」
   正本§12 逐語 =「Route Worker に Manager の責務を追加しない」
   ∴ ★ESDE が扱う対象は 経路の観測者の仕事ではないと 既に決まっている

②前例が 既に 経路の外で 回っている
   `domain_dw.record_stages()` = Manager 巡回の記録段（INTERVAL=60）で
   front door から observed_edges を引き、2DER 製の判定器 `stage_from_evidence` で決め、
   ETRACE へ `CONTRACT_STAGE` として残す。★何も止めない・何も承認しない。
   ★IDENTITY/CALLER/TIMING/INPUT/OUTPUT/STORAGE/READER/AUTHORITY の8要素が揃っている

③自分の計器を疑う機構も 既に 外側に 在る
   `route_worker.self_check()` = 同じ問いを2回引いて動いた欄を名指しする（14面）
   判定は `twoder/unstable_keys.py`（★2DER が書いた）／ reader = `webui.py:1087`
```

**∴ ESDE Manager を 1〜18 の19番目に置かない、という素案の判断は正しい。**
**★そして「新しい機構を作る」問題ではない ―― `record_stages` と同じ形を取る問題である。**

---

## 7. 残る決定点（★私が決めない）

declared の DESIGN_HOLD は解けていない。**未達は3つに減った。**

| 項目 | 状態 | 何が決まれば進むか |
|---|---|---|
| **OUTPUT** | UNVERIFIED | 正本 §2 の `分母 / 分子 / 欠損ID` を**どの欄の形で**載せるか。`CONTRACT_STAGE` 方式（ETRACE の kind を1つ足す）か `function_table` 方式か |
| **AUTHORITY_EFFECT** | UNVERIFIED | ESDE 結果が**何を止める / 進める**か。★declared §7 の見立て（初期は「止めない・記録するだけ」）は**まだ Taka 裁定を受けていない** |
| **型を名乗る時点** | ★新規（本書 §5） | 失敗の型は「直った後」だけか、「直る前」にも別指標で付けるか |

**★併せて、正本 §7 が残した宿題も未着手:**
> 次に決めること = **階層性の `required boundary` を どこから 機械取得するか**

本書の実測では、この一覧は**機械に存在しない**（declared §6 でも「私が手で5件挙げた＝UNVERIFIED」）。
∴ **3指標のうち階層性だけが、いまも人の手に依存している。**

---

## 8. ★並行改修の注意（Taka 指示によりメモ）

**台帳・明細は本日も改修が進行中である。本書の数値は測った時刻の値であり、既に動いている可能性がある。**

本日（2026-08-23）明細まわりに入った変更:

```
rri   f6cbb9c  QUESTION_TYPED（構造化明細の後付け記録）
rri   b7f5268  QUESTION_TYPED に refs を載せる（段2）
rri   18a648c  list_questions(thread_id) を足す（明細の読み口）
rri   178cd9a  明細の台帳に「誰が書いたか」を残す（ACTOR_RECORDED）
twoder 384351c 要求構造化器: 長文依頼を意味単位の明細へ
twoder 3965665 明細 段1/段2: 保存時の切断をやめる／参照を実在の確認つきで持つ
twoder 87d0cc3 明細 段3: 依頼に書かれていないものを数えて人へ返す／OPEN_GAP
twoder e95cbe6 段3 の UI が出ていなかった件を直す
twoder 3d3b7bb 画面に「誰が書いたか」を出す
egl   b20b27d  明細システム改修の DW 側障害を事前定義
egl   8cf897c  台帳変更の影響面を全件調査（93箇所/23ファイル・直触だけ10本）
```

**∴ 本書が依存する欄（`kind` / `refs` / `source_span` / `recorded_by` / `OPEN_GAP`）は
すべて本日追加されたものであり、仕様が固まっていない。**
**★v0.3 に進む前に、この改修が落ち着いたことを確認する。**

**★併せて計器の注意:**
- front door `/api/ledger_rows` は **1回 500行が上限**。ただし `total` / `offset` を返すので**黙って切ってはいない**（ページで全件引ける）。
- **登記簿の `rows` は登記時の値**であり現在値ではない（実測: `failure_recurrence` は登記簿 143 に対し現在 **633**）。私は本日これを一度誤って現在値として報告した。

---

## 9. 次の一手（★候補・優先順位は付けない）

```
(あ) OUTPUT を決める     `record_stages` と同じ形で、正本§2 の 分母/分子/欠損ID を
                          ETRACE の kind 1つに載せられるか実測する（★実装0で確認できる）
(い) 階層性の boundary    正本§7 の宿題。機械に一覧が無い＝ここだけ人依存が残っている
(う) 失敗の型の時点        本書§5 の分かれ目。ESDE の定義に属するため Taka / 設計の裁定が要る
(え) 明細の普及           構造化明細 1/635。ESDE の精度はここに比例する
(お) 既知の CONFLICT 解消  ART- id が2つの登記簿で衝突（declared から未解決）
```

---

## 10. していないこと

```
★実装 0行 ／ 新しい Manager / Worker / 台帳 / ID / 経路 / state 0
★既存仕様の書き換え 0 ／ 素案の差し替え 0（重ねただけ）
★ESDE-Research（44GB）の調査 0（★Taka 裁定により範囲外）
★DESIGN_HOLD の解除 0（★declared の判断を引き継ぐ）
★評価・優先順位付け 0（§9 は候補の列挙であり順位ではない）
```
