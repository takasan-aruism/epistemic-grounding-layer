# 2DER GDW運用設計 — ESDE Domain Manager / Worker構成 素案 v0.1

**著者: Taka（2026-08-24）／ 記録: Claude Code（CC_ALPHA・逐語・要約せず全文）**
**★本書は設計思想であり、現在の2DER実装との一致は未確認（§14 に調査指示あり）。**

## 0. 目的

2DERの自動化を、個別機能が勝手に動く構成ではなく、

General Manager → Domain Manager → Worker

の3層構造で管理する。

略称を GDW（General / Domain / Worker） とする。

今回の対象DomainはESDE。

現在のESDEには、計器・TASK scope・required/enforced/observed・finding・UI表示などの部品が形成されつつある。しかし、これらを誰が管理し、いつ実行し、結果を誰が判断するかがまだ一つの構造になっていない。

このまま個々の自動化を追加すると、各機構が独立して発火し、後から全体統制を加えることになる。

したがって今後は、ESDE関連の自動化を原則として

```
General Manager
      ↓
ESDE Domain Manager
      ↓
ESDE Worker
      ↓
観測・構造化・評価
      ↓
台帳明細
      ↓
ESDE Domain Manager
      ↓
General Manager / UI
```

へ統合する。

## 1. GDWの基本責務

**General Manager**

2DER全体の管理層。当面は高度な判断能力を持たせなくてよい。初期の役割は、

* Domain Managerの状態を集約する
* Domainごとの未処理件数・finding・異常・進捗を保持する
* UIへまとめて表示する
* Domain間のhandoffを管理する
* 人間裁定が必要なものだけ上げる

程度でよい。General Manager自身がESDE構造化・台帳分類・DW実装等を行わない。
現段階では、各Domain Managerの情報を束ねる管理面として成立すればよい。

## 2. ESDE Domain Manager

ESDE Domain全体の責任主体。単なるESDE Workerの起動係ではない。
現在2DERが持っているESDE関連情報を集約して管理する。対象には少なくとも以下を含む。

* ESDE正本 / ESDE概念・指標 / TASK-scoped ESDE / scope
* required source / observed / enforced / relation set
* refs / resolved / providers / ESDE_EVALUATION
* finding / handoff / 過去の測定 / 測定器
* 未評価TASK / 再評価対象 / 計器のversion
* UNVERIFIED / NOT_EVALUATED / ESDE Workerの実行結果

Domain Managerが「ESDEに関する現在状態」を一元的に説明できることを目標とする。

## 3. ESDE Domain Managerが判断すること

### 3.1 何を測るか
TASKや明細の変更を観測し、
ESDE評価がまだ無い / 前回評価後に入力が変わった / finding修理後なので再評価が必要 /
requiredが追加された / PLAN・contractが変化した / relation setが変化した
等からESDE Workerの実行要否を判断する。

### 3.2 どのWorkerへ渡すか
将来的には複数Workerを想定できる（Relation / Required / Structure Evaluation / Finding / Recheck）。
ただし初期実装では細分化しすぎない。まずは1つの **ESDE Structure Worker** で開始してよい。

### 3.3 結果をどう扱うか
正常な測定結果として登録 / UNVERIFIEDとして保持 / finding化 / 再測定 /
他Domainへhandoff / General Managerへ通知 / 人間裁定へ上申 を決める。
**Worker自身が勝手に修理を始めない。**

## 4. ESDE Worker

Workerは実働担当。基本的には勝手に働いてよい。
ただし自由に設計を変更してよいという意味ではない。
Domain Managerから与えられた対象と既存規則に従って、

```
対象取得 → 関係集合取得 → 必要情報収集 → ESDE構造化
→ 指標計測 → finding抽出 → 証拠付き結果を返す
```

を行う。**結果は必ず台帳へ残す。**

## 5. 自動実行の基本原則

**安全な観測・分類・評価は先に実行し、結果を台帳へ登録する。**
毎回人間へ「実行してよいですか」と聞かない。これは2DER主体化のために重要。

自動実行できるのは主として: 読み取り / 関係集合の投影 / 計測 / 分類 / finding生成 /
evidence記録 / UNVERIFIED記録 / 再評価 / handoff提案。

**Manager判断を必要とする**: state変更 / 正本変更 / authority変更 / requiredの新規定義 /
code修正 / destructive operation / findingの処分 / Domain境界を越える操作。

## 6. ManagerとWorkerの境界

**重要原則: Workerは事実を作る。Managerは意味と次の行動を決める。**

```
Worker: 「TASK-X の refs 7件中2件が unresolved」
Domain Manager: 「EQUALITY finding として登録する」

Worker: 「required 14 / observed 6 / unknown 4」
Domain Manager: 「unknownが残るので再評価待ち。blockingにはしない」

Worker: 「修理後の再測定で violation 8→2」
Domain Manager: 「findingを再評価し、必要なら解消候補とする」
```

**Workerが自分の測定結果を根拠に、自分で規則を変更してはいけない。**

## 7. 台帳明細との関係

ESDE結果は独立した分析ログではなく、TASKの情報として台帳明細へ接続する。
TASK配下には、元依頼 / FACT / CHANGE / SPEC / TEST / CONSTRAINT / GOAL /
Evidence / refs / ESDE required / observed / finding / ESDE evaluation 等が共存する。

ESDE Domain Managerは、明細から必要情報を読み、Workerの結果を再び明細へ返す。これにより

```
TASK → 明細 → ESDE → 追加の構造情報 → 明細 → PLAN / DW
```

という循環を形成する。

## 8. General Managerとの関係

当面のGeneral ManagerはESDEの中身を理解しなくてもよい。
ESDE Domain Managerが以下のようなsummaryを返せればよい。

```
ESDE Domain
対象TASK       42
評価済み       31
未評価         11
UNVERIFIED      7
finding         9
FOUNDATION       2
再評価待ち       3
人間裁定         1
Worker稼働       1
```

General Managerは、ESDEが正常に動いているか / backlogが増えていないか /
人間裁定があるか / 他Domainへのhandoffがあるか だけを見ればよい。

## 9. UI

UIではGDW構造をそのまま可視化する。将来的にはManagerタブで、

```
General Manager
ESDE Domain
  状態: ACTIVE
  Worker: 1
  未評価: 11
  findings: 9
  裁定待ち: 1
Ledger Domain
  ...
DW Domain
  ...
```

と表示する。ESDE Domainを開けば、現在実行中Worker / 対象TASK / 最新ESDE評価 /
findings / backlog / 再評価予定 / handoff を見られる。
TASK詳細からは、そのTASKにscopeされたESDE評価だけを表示する。

## 10. 初期Worker構成

最初からWorkerを細分化しない。初期は **ESDE Structure Worker** 一つでよい。

責務: TASK relation set取得 / required取得 / observed取得 / refs確認 / providers確認 /
equality / symmetry / hierarchy / linkage / finding候補 / ESDE_EVALUATION生成。

作業量やauthorityが分離できることが実測された段階でWorkerを分割する。

## 11. 将来のDomain構成

```
General Manager
├─ Ledger Domain Manager   └─ Ledger Operations Worker
├─ ESDE Domain Manager     └─ ESDE Structure Worker
├─ DW Domain Manager       ├─ Planning Worker ├─ Generate Worker └─ Audit Worker
├─ Research Domain Manager └─ Research Worker
└─ UI / Observation Domain
```

ただし現時点でこの構成を一括実装しない。**ESDE Domainを最初の実証Domainにする。**

## 12. 今回の実装範囲

1. ESDE Domain Managerの既存情報源を全件調査
2. 現在scratchpadにあるESDE計器を正式配置
3. ESDE Structure Workerとして呼べる形へ整理
4. Domain Managerが対象TASKを選択
5. Workerが自動測定
6. 結果を既存台帳へ登録
7. Domain Managerが結果を管理
8. General Managerがsummaryを取得
9. UIにDomain状態を表示

ここまで。**了解・創造等のESDE概念追加は別案件。**

## 13. 完了条件

```
General Manager → ESDE Domain Manager → ESDE Structure Worker
→ TASK-scoped evaluation → 台帳 → ESDE Domain Manager → General Manager → UI
```

が1本、**人間による途中操作なしで通れば成立。さらに最低2 TASKで再現する。**
この段階では、General Manager自身が高度な判断をする必要はない。

## 14. Claudeへのレビュー依頼

本書は設計思想であり、現在の2DER実装との一致は未確認。Claudeは実装前に、
既存Manager / manager_v0 / ESDE_EVALUATION / egl/structure / request_thread /
TASK relation set / ETRACE / refs / providers / roadmap / authority / UI / existing workers
を**全件調査**する。そのうえで、

1. 既に存在するもの
2. 名前だけ違う同等機構
3. 接続するだけでよいもの
4. 本当に新規実装が必要なもの
5. GDW構造と衝突する現行実装
6. Domain ManagerとWorkerのauthority境界

を報告する。**勝手に実装へ進まず、調査結果を台帳へ登録してTakaへ提示する。**

## 15. 位置づけ（Taka 逐語）

> この構成なら、今の「5つのClaudeを担当別に並列稼働」している状態を、そのまま将来のGDWへ写せます。
> 今はあなたが実質General Managerで、各ClaudeがDomain Manager兼Workerになっている。
> それを段階的に、Taka → General Manager → Domain Manager → Worker へ置換していく設計です。
> ここを先に正本化しておくと、今後の自動化で「この処理は誰が勝手に動かしていいのか」が
> かなり整理されるはずです。
