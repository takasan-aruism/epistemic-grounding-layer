# 実測 — 正本§10② の「作用ベース全件調査」を 2DER 自身がどこまで実行できるか

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
Taka 指示（2026-08-22）「Claude が今日行った実調査を標本にして ①②③ に分類せよ」
**★新API 0・新Manager 0・新台帳 0・実装 0。**
測ったHEAD: twoder `8b64b1f` / dev-workcell `68c3b4c` / egl `f1565fa`
**★測定時刻 2026-08-22 11:46〜12:20**（★下記 §0 の理由により、値は**時点の値**）

---

## 0. ★先に ―― この標本の答えは「時点の値」である

監査が 2026-08-22 に実測して確定させたこと（`ITEM-2DER-EVO-0083` 履歴・逐語要旨）：

```
★私(監査)が『正解例にしてよい』と書いた4件を いま再測した。
  ①ts 逆行 = 03:2x 時点 ★848/4300（★02:00 の値は 843/4275）★分母も分子も動いた
  ③regression の top-level = ★100本中 ★0本（★02:00 の値は 5本）
     ★あなたの 8b64b1f で5本とも直った ∴ ★『5本』はもう存在しない
★∴ 4件のうち2件が ★1時間で古くなった。
★一致は ★時点の一致であって ★不変の事実ではない。
```

**∴ 本測定の「今日の答え」欄は、その時刻に測った値である。**
本書の目的は答えの保存ではなく、**その問いを 2DER に立てられるかの分類**なので、
値が動いても分類は動かない。**ただし §1 Q2 の「5本」は既に 0本であることを明記する。**

---

## 1. 分母 ―― 2DER が答えられる面（★サーバー自身に列挙させた）

`GET /api/control?include=__probe__` を投げて **サーバーが返した available をそのまま採った**
（★私の記憶で書かない）。

```
include で名指しできる面 = ★14
  route_table / plus_minus / authority_summary / anatomist / static_edges /
  route_edge_votes / route_table_view / question_reviews / route_edge_votes_v2 /
  edge_measures / observed_edges / function_table / function_index / function_first

既定で返る欄 = ★10
  read_only / generated_from / roadmap / forecast / recent_de / recent_chg /
  interventions / completion / offramp_flags / resolvable

★分母 = 24面 ＋ 他15口（state / tasks / resolve / etrace / ledgers / roadmap ほか）
```

### ★面の性格（実際に引いて測った）

| 面 | 行を返すか | 実測 |
|---|---|---|
| `route_table` | ○ | 18行。欄 = `id / component / function / phase / value / rule` |
| `route_table_view` | ○ | 228行（hand 18 / machine 210）。欄 = `route_id / source / target / kind / origin` |
| `function_table` | ○ | list 9 / not_in_list 22 / undecided 110 |
| `observed_edges` | **△** | `edges = 1444` に対し **返るのは `top_rows` 30 のみ** |
| `static_edges` | **×** | **2,926 candidate を数えているが 個別の辺を返す欄が 0（集計のみ）** |
| `authority_summary` | × | total 208。集計のみ |
| `anatomist` | × | `question=Q5_BROKEN_LINKS` / `total_segments 18` |
| `edge_measures` | × | orphan_modules / dead_split / hidden_edges / route18_reproducible の集計 |
| `function_first` | ○ | `linked_rows 5` / `without_any_ids 79`（total_functions 146） |
| `plus_minus` | **―** | **★`null` が返った**（語は available に在る）。★UNVERIFIED として記録 |

**★どの面も述語を受けない。面ごと丸ごと返るか、返らないか。**
（追補2 §3 で確定済 ―― 16口・引数18種のうち結果を条件で絞れるものは 0）

### ★static_edges が自分で書いている限界（逐語）

```
counted_kinds     = ['import', 'from import']
not_counted_kinds = ['function call', 'class 利用', 'endpoint 呼び出し', 'subprocess',
                     'shell 呼び出し', 'service 呼び出し', 'repo 間参照', '既存 runtime 記録',
                     'OBSERVED_EDGE(★その辺を実際に通過した記録=★正本§2.3・★まだ測っていない)']
not_counted_note  = 「まだ数えていない(★0件ではない=★件数は出さない)」
not_counted_where_else =
  「★'function call' は ★別の器(egl/structure/s4_edges.py → EDGE_INVENTORY)で
    ★1,336件 数えている(★2026-08-14 実測) ／★この static_edges では ★まだ数えていない
    =★★数は 9 のまま(★器が違う ∴ 動かさない)」
```

**★これは重要 ―― 呼び出し 1,336件は 既に測ってある。2DER の口に繋がっていないだけ。**

---

## 2. 標本 ―― 今日 私が実際に行った調査 15件

**選び方**: 本日の declared 3枚（本体 / 追補1 / 追補2）で**私が証拠として引用した調査**を全件。
各件について、**実際に front door へ当てた**（当てられなかったものは理由を書く）。

| # | 問い | 今日の答え | 分類 | ③の欠落 |
|---|---|---|---|---|
| Q1 | `_EnergizedApply` の定義は本番に幾つあるか | 1（`patch_bridge.py:46`） | **③** | 観測データ |
| Q2 | regression 100本中 top-level import は何本か | 5 → **★現在 0** | **③** | query入口 |
| Q3 | `axis_id` を書く関数は他に在るか | 在る（`approve_account.py:44` ほか） | **③** | 観測データ |
| Q4 | `status_note` の `AXIS=` を読む関数は在るか | 0 | **③** | **identity** |
| Q5 | material 4 の供給者は何処に居るか | 2箇所に分裂 | **③** | **scope定義** |
| Q6 | `ENERGIZATION_ADJUDICATION` の writer 呼び手は何件か | 0 | **②** | （query入口） |
| Q7 | `principal_of` の production caller は何件か | 0 | **③** | query入口 |
| Q8 | DEAD_APPROACH 門はこの依頼文を止めるか | BLOCK 0 /「formal」で1 | **③** | query入口 |
| Q9 | front door の口と引数の全件 | 16口 / 引数18種 / 述語0 | **②** | （query入口） |
| Q10 | 文書 X の台帳登記行は何件か | 0（登記前） | **③** | query入口 |
| Q11 | 正本2つのうち現行はどちらか | `_OPERATING`（来歴から） | **③** | **identity** |
| Q12 | 581 task の RUNGATE 判定分布 | REARM 263 ほか | **②** | （query入口） |
| Q13 | `function_table` の記録数と origin | list 9 / not_in_list 22 / undecided 110 | **①** | ― |
| Q14 | 本日の twoder commit の new_file 内訳 | 機械2 / Claude5 | **③** | 観測データ |
| Q15 | `observed_edges` を読む側の全件 | 4箇所 | **③** | query入口 |

### 集計

```
① 2DER 既存機能だけで取得可能   ★1 / 15  ( 7%)
② 一部取得可能                  ★3 / 15  (20%)
③ 取得不能                      ★11 / 15 (73%)
```

### ③ 11件の欠落の内訳

```
query入口   ★5   Q2 Q7 Q8 Q10 Q15
観測データ  ★3   Q1 Q3 Q14
identity    ★2   Q4 Q11
scope定義   ★1   Q5
index       ★0
```

**★index の欠落は 0件。**足りないのは索引ではなく、**口・データ・語**。

---

## 3. 各件の実測（★何を当てて何が返ったか）

### ① 取得可能（1件）

**Q13** `GET /api/control?include=function_table` → `list / not_in_list / undecided` が行で返る。
**★front door だけで完結。Claude を経由しない。**

### ② 一部取得可能（3件）

**Q6**（`ENERGIZATION_ADJUDICATION` の writer 呼び手）
`include=observed_edges` は `from / to / count / first_run_id / last_as_of` の行を持つ。
**しかし `edges = 1444` に対し `top_rows` は 30 のみ。**
∴ 上位30に入る辺なら答えられる。入らなければ答えられない。**上位30に入らないことが「0件」と区別できない。**
★記憶「不在が遵守に見える」と同じ形。

**Q9**（front door の口と引数）
`include.available` が **14面を自己申告で返す** ＝ **部分的な自己記述は在る**。
**しかし route（口）の一覧は返らない。**引数の一覧も返らない。
∴ 「面」は自己記述できるが「口」はできない。

**Q12**（581 task の RUNGATE 判定分布）
`GET /api/tasks` → **585 ID**。`GET /api/state?task_id=` → **28欄**
（`dw_state / next_operation / actor_role / claude_barrier / dispatch_status / upper_reviews` ほか）。
**★rearm の判定語は返らない**（`split_gates` は別概念）。材料の一部は取れるが `supplier_registered`
は server 内部（`_machine_registry`）で外に出ない。
∴ **585回叩いて材料の一部**まで。**判定は出ない。**

### ③ 取得不能（11件）― 欠落の種別ごと

#### (a) query入口が無い（5件）― ★データは在るのに問えない

**Q7** `principal_of` の caller 数 ／ **Q15** `observed_edges` を読む側
→ 呼び出し辺は **`egl/structure/s4_edges.py → EDGE_INVENTORY` に 1,336件 既に在る**（static_edges 自身の申告）。
**front door の 24面のどれにも出ていない。**
**★これが最も安い欠落 ―― 新しい観測は要らない。**

**Q2** top-level import の本数
→ `static_edges` は `by_kind {import 1862, from_import 1064}` を持つが
**①個別の辺を返さない ②`sys.path` 操作の有無を数えていない**。
`by_flag {is_test 776}` は近いが repo/ディレクトリで絞れない。

**Q8** DEAD_APPROACH 門が止めるか
→ 判定器 `failure_memory._mentions_dead_revival` を**非破壊で叩く口が無い**。
`/api/submit` に投げれば分かるが **task を作る＝破壊的**。
★今日 私は module を直接 import して聞いた。**front door からはできない。**

**Q10** 文書 X の登記行は何件か
→ `GET /api/ledgers` は**台帳ごと**の `{ledger_id, path, repo, rows, liveness, role, purpose}` を55件返す。
**文書ごとの登記行は返らない。**

> **★ここで規律フックが直読を止めた。その文言が本測定の方法そのものだった（逐語）:**
> 「台帳の中身は 2DER に聞いてください。**答えられないなら『答えられなかった』が結果であり、
> それが次に作る読み出し機能です**」
>
> **★私の非違**: 本日それ以前に、私は `CC_REGISTER.jsonl` を python で直読して 1022 行と数えた。
> **境界違反だった。**
> **★未解決の食い違い**: front door は同台帳を **`rows: 216`** と申告する。**216 対 1022。**
> **★直読で解消しない。UNVERIFIED として残す。**（鍵の違いの可能性が高い）

#### (b) 観測データが無い（3件）― ★そもそも測っていない

**Q1** class 定義の数 → `not_counted_kinds` に **`'class 利用'`** が明記。逐語「まだ数えていない(★0件ではない)」。
**Q3** どの関数がどの語を書くか → 「識別子の書き手」を測る面が 24面に無い。
**Q14** commit の new_file 内訳 → `recent_chg` は `CHG-0199` 等**10件**。git の diff 統計を持つ面が無い。

#### (c) identity が無い（2件）

**Q4** `AXIS=` の読み手
→ **`AXIS` は `status_note` の自由文**であり、機械の語ではない（追補1 §2 で確定：読む関数 0件）。
∴ **問いを立てる語が存在しない。**口を作っても引く鍵が無い。

**Q11** 正本2つのうち現行はどちらか
→ **★本日 監査が実測した defect がここに直撃する（逐語要旨）:**
```
artifact_registry.all_active() = ★222件。最新 ART-2bc1a6f4d5 を front door で引くと ★resolved=True
∴ この計器は登記済み/未登記を判別できる。
★その上で ★4件が引けない = ART-53632b55e4 / ART-fd56608eab / ART-8cc35a5a50 / ART-afe2c9fda5
  ★4件とも ★resolved=False / record=None
```
**∴ 私が追補1で「登記した」と書いたものは、front door の正規面では成立していない。**
`cc_register` は `egl/docs/CC_REGISTER.jsonl`（front door 申告 **`role: IDLE`**）へ書き、
`artifact_registry` とは**別の登記簿**。
**★しかも両者が `ART-` という同じ形の ID を使う**
（`cc_register._META` 逐語「doc_id の計算式は `artifact_registry.artifact_id_for()` の実読・**重複であることを隠さない**」）。

**★これは正本 §4 対等性の CONFLICT である。**
```
EQUALITY   canonical: ART-<sha1(repo|path)[:10]>
           producer A: artifact_registry（front door が resolve する・222件）
           producer B: cc_register    （front door が resolve しない・role=IDLE）
           identity rule: ★同一の式 ∴ ★ID を見ても どちらの登記簿か分からない
           status: ★CONFLICT
```
**★私の「登記した」という報告を訂正する ―― 文書登記簿には入った（DOC行 708→711）が、
front door が引く正規面には入っていない。**

#### (d) scope 定義が無い（1件）

**Q5** material 4 の供給者は何処に居るか
→ `route_table` の 18行の欄は `id / component / function / phase / value / rule` **だけ**。
**監査も独立に実測して同じ結論**（逐語）:
> 「route_observed() の rows は ★18行 / 欄は ★component / function / id / phase / rule / value の6つ。
> **★from も to も producer も consumer も actor も authority も observed_count も ★無い。**」

∴ **経路表が「供給者」という概念を持っていない。**口でもデータでもなく、**枠が無い**。
（`route_table_view` は `source / target` を持つ 228行が在るが、**それは辺であって供給者ではない**。）

---

## 4. ESDE 宣言（正本§12）

```
AXIS: SELF_INVESTIGATION_CAPABILITY_MEASURED
SCOPE:
  entry:       今日 Claude が grep で答えた問いを、front door だけで再現しようとする
  exit:        ①②③ に分類し、③ の欠落を種別に割る
  authority:   発行 0・変更 0
  persistence: 新規 0
  components:  /api/control 24面 / state / tasks / ledgers / resolve / etrace

EQUALITY   canonical: 「2DER に立てられる問い」
           compatible:   [面ごと丸ごと引く問い（24面）, 識別子で引く問い]
           incompatible: [述語で絞る問い, 呼び出し辺を引く問い, 判定器を非破壊で叩く問い]
           unknown:      [plus_minus が null を返す理由]
           status: ★BROKEN
           ★別件で CONFLICT を1件検出 = ART- を2つの登記簿が同じ式で発番（§3-c Q11）

SYMMETRY   pairs: [測る側 ↔ 引く側]
           required 24 / present ★9（行を返す面）/ missing ★14（集計のみ・null）/ unverified 1（plus_minus）
           ★static_edges = 2,926 数えて 0 行返す ＝ ★測る側だけ在り 引く側が無い の典型

LINKAGE    edges:
             E1 s4_edges EDGE_INVENTORY(1,336件) → front door   status: ★BROKEN（繋がっていない）
             E2 static_edges の集計 → 個別の辺                  status: ★BROKEN（行を返さない）
             E3 observed_edges 1444辺 → 返る行 30               status: ★BROKEN（上位30で切れる）
             E4 判定器(failure_memory / decide_rearm_v2) → 非破壊の口  status: ★ABSENT
             E5 cc_register の ART- → front door の resolve      status: ★BROKEN（resolved=False）
           declared 5 / observed 0 / broken 4 / absent 1

HIERARCHY  boundaries: [front door 単一入口, 台帳直読の禁止, authority 境界]
           required 3 / passed 2 / violation ★1 / unreachable 0
           ★violation = 私が本日 CC_REGISTER.jsonl を直読した（§3-a Q10）。★自己申告する。

R1_END_TO_END      status: ★BROKEN
                   evidence: 15件中 front door だけで完結したのは ★1件（Q13）
R2_DENOMINATOR     required 15 / observed ★1 / partial ★3 / status: ★BROKEN
R3_INTERNAL_GATES  gates: [Basic認証, include 語の検査, 台帳直読の禁止]
                   passed: [Basic認証(実確認), include 語の検査(★未知語 __probe__ で実発火)]
                   failed: [] / unverified: [caller の扱い]
R4_REJECTION       rejection_conditions:
                     ①未知の include 語 → 「その語は無い: __probe__」★実発火させた
                     ②認証なし → 401 ★実発火させた（Bearer で 401 / Basic taka で 200）
                     ③台帳直読 → 規律フックが停止 ★実発火した（★意図せず・§3-a）
                   actually_rejected: [①②③ とも実発火] / status: ★OBSERVED

UNDERSTANDING  candidate: SELF_INVESTIGATION_CAPABILITY
               requires: [述語の口, 呼び出し辺の露出, 判定器の非破壊口, AXIS の identity,
                          経路表の供給者欄]
               evidence: [①1件のみ]
               unresolved: [216 対 1022 の食い違い, plus_minus の null]
               result: ★REJECTED（★『現状ほぼ実行できない』を確認した ＝ 必要条件の不成立を確定）

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD（★実装しない ―― Taka 指示）
```

---

## 5. ★この測定が示すこと（★私の意見でなく数から）

```
① 正本§10② を 2DER が実行できる割合 = ★1/15（7%）
② ③11件のうち ★index の欠落は 0 ―― 足りないのは 口(5) / データ(3) / 語(2) / 枠(1)
③ ★最も安いのは Q7/Q15 型 ―― 呼び出し辺 1,336件は ★既に測ってある。口に繋がっていないだけ。
④ ★最も高いのは Q5 型 ―― 経路表に「供給者」という枠が無い。口を作っても入れる欄が無い。
⑤ ★identity の2件(Q4/Q11) は口を作っても解けない。★引く鍵が無い / ★鍵が衝突している。
```

**∴ 追補2 §6 で書いた「述語の口が律速」は、内訳を見ると正確ではない。**
**口だけ作っても 15件中 5件しか動かない。**

---

## 6. 触っていないもの

`EVO-0085` writer 4欠損 ／ `EVO-0087` 呼び手0 ／ `EVO-0088` harness fixture ／
並行運用 `EVO-0084` ／ 正本§13 の UNVERIFIED 差戻し ／ REARM 263 ／ `_GATES_MAX` ／
`esde/ESDE-Research`（Taka 裁定により無視）。

**★新API 0・新Manager 0・新台帳 0・コード変更 0行。**
