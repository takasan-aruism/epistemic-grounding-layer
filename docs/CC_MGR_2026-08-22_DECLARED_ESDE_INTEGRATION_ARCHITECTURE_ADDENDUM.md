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

**★私が実測した（UNVERIFIED のまま置かない）。**
探索範囲 = `egl/docs/*ESDE_EVALUATION*` 全件 ＋ `DESIGN_EVIDENCE_LEDGER.jsonl` 全行。

```
docs/ESDE_EVALUATION_DOMAIN_MANAGER_v0.1.md            doc_id=ART-53632b55e4  ★登記行=0
docs/ESDE_EVALUATION_DOMAIN_MANAGER_v0.1_OPERATING.md  doc_id=ART-fd56608eab  ★登記行=0
```

**∴ Taka の申告は正しい。file としては PRESENT、台帳登記は ABSENT（分母＝台帳全行を走査した上での 0）。**
★`doc_id_for()` は path の sha1 から決定論で id を作るので、**id が引けることは登記の証拠にならない**。
∴ 登記の有無は id ではなく**行を数えて**確かめた。

**∴ 正本は現在 2DER の持ち物ではない。**
本日 私と監査が正本を根拠に判定を下してきたが、**その根拠は 2DER の外に在る。**
（記憶「台帳に載らないものは 2DER でない」と同型。）

**★併せて実測: 正本は2つある**（`.md` と `_OPERATING.md`）。**どちらが正本かは UNVERIFIED。**
正本 §4 の対等性でいう **identity rule が正本自身について未成立**。

**★ここでは登記しない**（Taka の指示は調査と declared のみ）。**MISSING として立てる。**

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

## 7. Taka へ返す2問（★私が決めない）

```
Q1  調査基盤の「問いの形」を、先行研究（ESDE Language / Genesis）から引いてよいか。
    ★2026-07-26 に language/lexicon から引いた前例が在る（成功例・§2）。
    引くのは機能でなく ★手順と失敗記録。
    ★esde/ESDE-Research は 44GB / 43,069 files ∴ 探す範囲を絞る指示が要る。

Q2  正本（ESDE Evaluation Domain Manager v0.1）を台帳へ登記するか。
    現在 2DER の外に在る。★私と監査は本日ずっと これを根拠に判定してきた。
```

---

## 8. 触っていないもの

`EVO-0085` の writer 4欠損 ／ `EVO-0087` 呼び手0 ／ `EVO-0088` harness fixture ／
並行運用 `EVO-0084` ／ 正本§13 の UNVERIFIED 差戻し ／ REARM 263 ／ `_GATES_MAX` ／
`esde/ESDE-Research` の中身（**44GB・未調査・UNVERIFIED**）。
