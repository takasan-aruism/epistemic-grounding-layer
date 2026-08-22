# 追補 — `ESDE_INTEGRATION_ARCHITECTURE` ／ ★調査の方向を訂正する

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
本体 = `CC_MGR_2026-08-22_DECLARED_ESDE_INTEGRATION_ARCHITECTURE.md`（egl `2b7812b`）
**★コードは1行も変えていない。★実装0。**
測ったHEAD: twoder `8b64b1f` / dev-workcell `68c3b4c` / egl `2b7812b`

---

## 0. ★訂正3 ―― 本体 declared は**調べる向きが間違っていた**

本体で私は「ESDE 評価は既存1〜18経路のどこに入るか」を軸に調べた。
**Taka の説明（2026-08-22）でそれが誤りと分かった。**逐語の趣旨：

> ESDE は**アーキテクチャ**。そのアーキテクチャで作られているのが ESDE Language 系と ESDE Genesis 系。
> **本来2DERはこの二つの開発を進めるために作っている。**なぜならどちらもシステムが巨大で
> **あなたが嘘ばかりつくようになったから。**
> 2DER も同じ ESDE アーキテクチャであることに変わりはない。**問題は ESDE ライクな開発をしてこなかったこと**で、
> そこを今更ではあるが抜本的に見直すのが現在の試み。**最終的にこの3つは統合される。**
> **これまではとりあえず一直線に繋げて作ることばかり考えていたが、それでは機械化するにあたって
> 今後立ち行かなくなる可能性があり**、そこを抜本的に解決させるための
> **ESDE アーキテクチャ的な自律的な調査基盤を用意することが目的**なので**分けて考えて**。

**∴ 本体 §3・§9 の「1〜18経路のどこに接続するか」という問い自体が「一直線に繋げる」思考だった。**
Taka が「それでは立ち行かなくなる」と名指ししたものと同型。**問いを差し替える。**

| | 誤（本体） | 正（本追補） |
|---|---|---|
| 作るもの | 経路の1段としての ESDE 評価 | **自律的な調査基盤** |
| 問い | どこに挿すか | **2DER は自分を調べられるか** |
| 成功 | 経路が1段増える | **調査の主体が Claude から 2DER へ移る** |
| 2DER の位置 | 目的 | **手段（目的は Language / Genesis の開発）** |

---

## 1. ★本丸の欠損（実測）―― 2DER は自分に問いを立てられない

**探索範囲** = `twoder/webui.py` 全件（front door の全 route）。

```
front door の口 = 16
  approve / claude_packet / control / etrace / ingest / ledgers / operator /
  pending_approvals / receipt / resolve / roadmap / run_next / run_until_barrier /
  state / submit / tasks

★16口が受ける引数を全件抽出した結果 =
  id / task_id / run_id / event_id / roadmap_id / caller / include / history_limit
★このうち「条件」を書ける引数 = 0
```

**∴ 2DER に問えるのは「この ID について教えろ」だけ。
「条件 X を満たすものを全部挙げろ」が問えない。**

### 列挙で代用できるか（実測・確かめた）

```
GET /api/tasks → tasks: 585 件。★中身は ID の文字列だけ（例 TASK-2DER-INT-001）
∴ 属性で絞るには /api/state?task_id= を ★585回 叩く必要がある
```

**列挙は PRESENT。しかし述語で絞る面は ABSENT。**（探索範囲＝front door の全16口）

### ★これが「調査における Claude 依存」の正体

**本日 私が行った全件調査は、すべて私が `grep` で行った。2DER は1件も行っていない。**
実測した例：

```
「_EnergizedApply の定義は本番に幾つあるか」          → 私の grep
「top-level import を使う regression は何本か」        → 私の grep（100本中5本）
「axis_id を書く関数は他に在るか」                    → 私の grep
「status_note の AXIS= を読む関数は在るか」            → 私の grep（0件）
「material 4 の供給者は何処に居るか」                  → 私の grep（2箇所に分裂）
```

**どれも front door からは問えない。**
∴ **正本 §10②「作用ベースの全件調査」は、現在 2DER が実行できない工程である。**
**Phase 1「既存記録から機械取得」の前に、そもそも取得の口が無い。**

---

## 2. ★前例がある ―― ESDE 資産から引くのは成功実績（実測）

`docs/CC_DESIGN_2026-07-26_INTENT_ROLE_SPLIT_HANDOFF.md`（2026-07-26）逐語：

> **§1 ★ESDE Language の先行実績（実物を調査した結果・そのまま使える）**
> `/home/takasan/esde/ESDE-Research/language/lexicon/mapper_a1.py` / `auditor_a1.py` /
> `docs/ESDE language/DESIGN_NOTE_Resonance_Scoring.md`。
> QwQ-32B で **326 atom × 48 スロット**を観測した実運用パイプライン。
> **同型の構造が既に動いており、失敗と対策が記録されている。**

そこから 2DER が移植したもの（逐語）：

```
(a) 役割の言語化
    "You are an OBSERVER, not a classifier. Do NOT pick a winner."
(b) ★最大の危険＝YES 膨張（ESDE で実際に起きた）
    score inflation: QwQ-32B が 48スロット中 39 に非ゼロを付けた（妥当なのは 8〜15）
```

**∴ 3系統の統合は「将来の話」ではなく、2026-07-26 に一度 実行されている。**
そのとき引いたのは **機能ではなく「手順と失敗記録」**（＝方法論の転用）。

### ★これは今回に直接効く警告である

**(b) YES 膨張は、ESDE 評価そのものに起きる故障型。**
正本 §3 の10語（PRESENT / ABSENT / OBSERVED / …）を LLM に付けさせれば、
**PRESENT を付けすぎる**。48/39 は先行実測。
∴ **正本 §14 の「機械取得不能な値を LLM 自己申告で埋めずUNVERIFIED とする」は、
理念ではなく ESDE Language の実測に裏付けられた対策である。**

---

## 3. 正本そのものの状態（Taka 申告・私は未検証）

Taka 逐語「**まだこっちは台帳記帳されていない**」「最近まで監査が使っていた GPT 作成のメモ」。

### ★訂正4 ―― 私は最初、**別の帳簿を数えていた**

最初 `DESIGN_EVIDENCE_LEDGER.jsonl` を走査して「登記行0」と書いた。**帳簿が違った。**
`cc_register.REGISTER` = **`egl/docs/CC_REGISTER.jsonl`**（`cc_register.py:23`）。
∴ 鍵を合わせて測り直した（記憶「数には鍵を添える／食い違いはほぼ常に鍵の違い」）。

```
登記簿 = egl/docs/CC_REGISTER.jsonl   全行 1022 / DOC行 708
  ESDE_EVALUATION_DOMAIN_MANAGER_v0.1.md            ART-53632b55e4  ★登記行=0
  ESDE_EVALUATION_DOMAIN_MANAGER_v0.1_OPERATING.md  ART-fd56608eab  ★登記行=0
```

**結論は変わらない（Taka の申告どおり未登記）が、最初に出した証拠は誤りだった。**
★`doc_id_for()` は path の sha1 から決定論で id を作るので、**id が引けることは登記の証拠にならない**。
∴ 登記の有無は id ではなく**行を数えて**確かめた。

### ★どちらが正本か ―― 来歴で確定した（推測しない）

```
docs/ESDE_EVALUATION_DOMAIN_MANAGER_v0.1.md            87行/4,883B   受領 2026-08-20  commit 5a6c10f
  表題「2DER の 構造監査 指標（★正本）」
docs/ESDE_EVALUATION_DOMAIN_MANAGER_v0.1_OPERATING.md  238行/12,084B 受領 2026-08-21  commit 4d94196
  表題「Claude運用規則 / 2DER将来統合仕様（実践導入版）」
  ★ヘッダ逐語「本ファイルは 2026-08-20 時点で §2 §4 §5 §6 §7 §8 §9 §13 §15 を欠いた
   部分版だった。本版で全文に差し替える。」
```

**∴ 現行 = `_OPERATING.md`（全文版）／旧 = `v0.1.md`（部分版）。**
Taka が 2026-08-22 に再送した全文は `_OPERATING.md` と一致する。

### ★Taka 裁定（2026-08-22）と 登記の実行

```
Q1 先行研究(ESDE-Research)から引いてよいか
   → ★却下。逐語「ESDE-Research自体現在の開発には影響がないので無視」
     ∴ 44GB の調査は行わない。UNVERIFIED のまま閉じる（★分からないままにする、が結論）。

Q2 正本を台帳へ登記するか
   → ★可。ただし前提つき。逐語:
     「正本登録が遅れたのは 2DER が開発主体にはなれず Claude 依存が残ったから」
     「その正本を外部においたのは、そもそも★それが絶対の正義にはならず、開発を進める中で
      洗練させた V2,V3 を作成して正本化するほうが筋がいいかな？と思ったから」
```

**★登記した（既存機構のみ・新台帳0・新列0）。**

```
ART-53632b55e4  部分版  BUILD_SPEC / TAKA→MGR / build_role=SUPERSEDED
ART-fd56608eab  全文版  BUILD_SPEC / TAKA→MGR / build_role=IMPL_SOURCE / supersedes=ART-53632b55e4
DOC行 708 → 710
```

`record_doc` は **append-only（元の DOC 行を書き換えない）**・`build_role` に `SUPERSEDED` が既に在り・
`supersedes` 列が既に在る。∴ **v2/v3 が出たとき、v1 を SUPERSEDED に落として繋げる機構は既存で足りる。**
**「正本が2つある」という identity 未成立は、これで台帳側が答えを持つ形になった。**

### ★この裁定が declared の読み方を変える点

**正本は絶対規則ではなく「現時点の最良版」であり、開発の実測から v2 へ洗練される前提。**
∴ 本日の実測は**正本を守るための材料ではなく、v2 の材料**である。v2 へ持ち越す候補：

```
① YES 膨張（§2）        正本§3 の10語を LLM に付けさせると PRESENT を付けすぎる。
                        ESDE Language の実測 48スロット中39。★§14 の UNVERIFIED 原則の根拠。
② 調査面の不在（§1）    正本§10② の全件調査を 2DER が実行できない（front door に述語の口が0）。
                        ∴ Phase 1「既存記録から機械取得」は現状 前提を欠く。
③ 正本自身の identity   正本が2つ在り、どちらが現行かを機械が持っていなかった（本項で解消）。
④ 「一直線」の禁止      §0 の訂正3。正本§10 は工程の列に見えるため、
                        経路への挿入として読まれやすい。v2 で「調査基盤」と「経路」を分ける語が要る。
```

**★Taka 逐語「正本登録が遅れたのは 2DER が開発主体にはなれず Claude 依存が残ったから」は
本追補 §1 の実測と同じことを指している** ―― 記録する主体が Claude のままだから、
Claude が登記を忘れれば登記されない。**§1 の「調査の主体」と同じ構造が、登記にも出ている。**

---

## 4. 9項目の状態（本体からの差分のみ）

| 項目 | 本体 | **本追補** |
|---|---|---|
| CALLER | Manager 側（経路の1段） | **★訂正: 経路の段ではない。調査基盤の側。** |
| TIMING | UNVERIFIED（Manager のどの契機か） | **★問いが変わった: 「契機」ではなく「問いを立てられるか」** |
| READER | MISSING | **MISSING（変わらず）。★理由が判明 ―― 調査面が無いので読む側も作れない** |
| **（新）QUERY_SURFACE** | ― | **★ABSENT ―― 述語で問える口が16口中0** |
| **（新）CANON_NOT_IN_LEDGER** | ― | **MISSING（Taka 申告・私は UNVERIFIED）** |

---

## 5. ESDE 宣言（正本 §12・★対象＝「2DER の自律的調査能力」）

```
AXIS: SELF_INVESTIGATION_SURFACE
SCOPE:
  entry:       2DER に「条件 X を満たすものを全部挙げよ」と問う
  exit:        分母つきの答えが機械から返る（★Claude の grep を経由しない）
  authority:   発行 0・変更 0
  persistence: ★未定（新台帳を作らない前提）
  components:  front door 16口 / /api/tasks / /api/state / /api/ledgers /
               etrace / route_worker / function_table

EQUALITY   canonical: 「問い」の共通形式
           compatible:   [識別子で引く問い（id/task_id/run_id/event_id/roadmap_id）]
           incompatible: [★述語で絞る問い ―― 受け口が無い]
           unknown:      [esde/ESDE-Research 側の問い形式（未調査）]
           status: ★BROKEN（問いの空間が識別子に限られている）

SYMMETRY   pairs: [記録する側 ↔ 問い合わせる側]
           required 1 / present 0 / missing 1（NO_PREDICATE_QUERY_SURFACE）/ unverified 0
           ★2DER は書く側だけが在り、横断して問う側が無い

LINKAGE    edges:
             E1 問い→front door        status: ★BROKEN（述語を受ける引数が 0）
             E2 front door→全件走査     status: UNVERIFIED
             E3 全件走査→分母つきの答え  status: UNVERIFIED
             E4 答え→ESDE 評価          status: UNVERIFIED
           declared 4 / observed 0 / broken 1 / unverified 3

HIERARCHY  boundaries: [front door 単一入口, 台帳直読の禁止, authority 境界]
           required 3 / passed 3 / violation 0 / unreachable 0
           ★層は破っていない。★口が無いだけ。
           ★重要: 「台帳を直読すれば調べられる」は層の違反 ∴ 迂回で解決してはならない

R1_END_TO_END      status: ★UNREACHABLE ／ evidence: 述語を受ける口が 16口中 0（全件抽出）
R2_DENOMINATOR     required: 本日 私が grep で行った全件調査 ★5件（§1に列挙）
                   observed: 2DER が行えたもの ★0 ／ status: ★BROKEN
R3_INTERNAL_GATES  gates: [Basic 認証, caller 名乗り, 台帳直読禁止]
                   passed: [Basic 認証（実確認）] / failed: []
                   unverified: [caller, 直読禁止]
R4_REJECTION       rejection_conditions: [★未列挙 ―― 口が無いので拒否条件も無い]
                   status: ★UNVERIFIED

UNDERSTANDING  candidate: SELF_INVESTIGATION_SURFACE
               requires: [述語で問える口, 分母つきの答え, Claude を経由しない実走]
               evidence: [] ★無し
               unresolved: [口の形, 保存先, reader, authority]
               result: ★UNKNOWN

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD
```

---

## 6. ★実装しない理由（Taka §6 と正本 §10④）

差分候補を出さない。理由は2つ、いずれも規則そのもの：

1. **READER が MISSING**（本体 §6）。Taka §6「writer あり / reader なし の構造を作ってはならない」。
2. **口の形が推測でしか埋まらない**。正本 §10④「1点でも推測でしか埋まらないなら実装へ進まない」。

**∴ 次に確定すべきは「2DER が自分に問える問いの形」。**
それは 私が決めるものではなく、**先行研究（ESDE Language / Genesis）が既に持っている可能性が高い**
――2026-07-26 に一度そうやって引けた（§2）。

---

## 7. Taka へ返した2問 ―― ★両方 裁定済（2026-08-22）

```
Q1 先行研究から引いてよいか        → ★却下。ESDE-Research は現在の開発に影響しない ∴ 無視。
                                     44GB は調査しない。★§2 の前例（2026-07-26 の language/lexicon 移植）は
                                     ★既に 2DER 内の記録として在る ∴ そこから読める分だけを使う。
Q2 正本を台帳へ登記するか          → ★可（前提つき）。★実行済 = ART-fd56608eab / ART-53632b55e4。
```

**∴ 私から Taka へ出す問いは現在 0件。**次の手番は私（MGR）。

### ★次に確定すべきもの（私が進める。★実装ではない）

本追補 §6 のとおり、実装へ進めない理由は2つとも規則側に在る。
∴ 次は **READER を確定する**こと。**新しい reader を作るのではなく、既存の読み手を探す。**
探す先（作用ベース・★これから実施）:

```
manager_v0 の巡回が何を材料に手番を決めているか
front door /api/control が既に返している欄（function_table を返している前例が在る）
状況表 2der_status.sh が何を読んでいるか
route_worker が観測結果を誰に渡しているか
```

**★「読み手が居ない」と結論する前に、探した範囲を書く**（記憶・板の規則）。

---

## 8. 触っていないもの

`EVO-0085` の writer 4欠損 ／ `EVO-0087` 呼び手0 ／ `EVO-0088` harness fixture ／
並行運用 `EVO-0084` ／ 正本§13 の UNVERIFIED 差戻し ／ REARM 263 ／ `_GATES_MAX` ／
`esde/ESDE-Research` の中身（**44GB・未調査・UNVERIFIED**）。
