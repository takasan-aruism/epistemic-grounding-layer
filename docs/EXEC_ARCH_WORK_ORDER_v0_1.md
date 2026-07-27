# 2DER Execution Architecture 現状記録・継続更新基盤 作業指示書（v0.1・逐語保存）

- **種別**: 常設・正典。**Taka から受領した作業指示書（GPT 起草）を逐語で保存したもの。**
- **受領**: 2026-07-27 / MGR 経由 / **要約で置き換えない。実施の根拠はこの全文。**
- **Taka 追記（逐語）**: **「どっかで途中まで作ってるなんかがあるよ。」**
- **段取りと MGR の追加条件**: `CC_MGR_2026-07-27_EXEC_ARCH_WORK_ORDER_RELAY.md`

---

## 1. 目的

現在の2DERには、個別仕様書、Capability、Functional Edge、Ledger、EventStore、RRI、DW、Task Selector、各repoの実装など、多数の構成要素が存在する。

一方で、以下を一つの資料から確認できる状態にはなっていない。

* ユーザー入力をどの実装が受けるか
* どのPythonファイル・関数・CLIが起動するか
* どの処理がどの処理を呼ぶか
* 各段階でどのLLMが起動するか
* LLMへ何の情報が渡されるか
* どの正典・台帳・仕様書が読み込まれるか
* 判断結果がどこへ書き戻されるか
* RRI、Task Selector、DW、EGL、EventStore等が実際にどう接続されているか
* 何が現在LIVEで、何がBUILT、DECLARED、PLANNED、UNKNOWNなのか
* 現在作ろうとしている未実装経路が、既存構造のどこへ追加される予定なのか

この欠落により、資料や実装自体は存在していても、次のセッションや別担当LLMから再発見されず、過去に作成した機能・接続・判断が事実上失われる問題が生じている可能性がある。

本作業では、2DERの現行システムを実装現物から調査し、正式な「Execution Architecture」として記録する。

本書は理想設計書ではなく、まず現状の事実を完全に記述することを目的とする。

その上で、既知の未実装構想および今後追加予定の経路を、現行事実と混同しない形で併記する。

---

## 2. 最重要原則

### 2.1 現物優先

仕様書や過去報告だけで接続状態を確定しないこと。

以下を実際に確認すること。

* Pythonファイル
* CLI entrypoint
* import
* 関数呼出し
* API呼出し
* subprocess
* shell script
* systemd、tmux、cron等の起動経路
* schema
* test
* repository間接続
* EventStoreへのemit
* Ledgerへの書込み
* 実行ログ

「仕様上存在する」と「実行時に呼ばれている」を分離すること。

### 2.2 状態を混同しない

すべての要素と接続に、最低限以下の状態を付与すること。

* LIVE — 正式経路から現在実行され、実証されている
* BUILT — 実装と単体試験は存在するが、正式経路へ未接続
* WIRED_UNPROVEN — 接続コードは存在するが、実動証拠が不十分
* DECLARED — 仕様・Registry・Edge等に宣言されているが、実装未確認
* PLANNED — 今後実装することが明示されている
* UNKNOWN — 存在・状態・接続を確認できない
* DEPRECATED — 旧経路または使用停止済み
* CONTRADICTED — 仕様・実装・報告間に矛盾がある

推測で状態を昇格させないこと。

### 2.3 既知と未知を同じ地図へ載せる

未実装や不明点を資料から除外しないこと。

ただし、現行実装と未実装構想は明確に分離する。

例：

```
CURRENT:
RRI ResolutionArtifact
→ 接続先なし
PLANNED:
RRI ResolutionArtifact
→ Development Context Builder
→ Design Planner
→ Task Selector
→ DW
```

UNKNOWNは欠陥ではなく、調査対象として正式に記録すること。

### 2.4 新しい正本を無断で作らない

本作業は新しい台帳体系を増やすものではない。

既存の正本、Registry、Ledger、EventStoreとの関係を確認し、文書の正式配置先を決定すること。

新規ファイルを作る場合も、既存の文書体系内で最も妥当な場所へ置くこと。

---

## 3. 対象範囲

最低限、以下の全repoを調査対象とする。

```
/home/takasan/egl
/home/takasan/twoder
/home/takasan/rri
/home/takasan/ds
/home/takasan/dev-workcell
```

必要に応じて、以下も確認する。

* 起動用shell script
* systemd unit
* tmux session
* runner設定
* model endpoint設定
* vLLM関連設定
* Claude Code用handoff
* machine-readable spec
* Capability Registry
* Functional Edge Graph
* DESIGN_EVIDENCE_LEDGER
* EventStore
* task selector
* return_loop
* validators
* emit_api
* worker
* CLI command
* test harness
* repository間adapter

---

## 4. 成果物

正式成果物として、最低限次の二つを作成すること。

### 4.1 人間向けExecution Architecture

候補ファイル名：`2DER_EXECUTION_ARCHITECTURE_v0_1.md`

名称と配置場所は既存文書体系を調査した上で確定すること。

### 4.2 機械可読版

候補ファイル名：`2DER_EXECUTION_ARCHITECTURE_v0_1.json`

または既存運用に適する場合はYAML。

人間向け資料だけでは、将来の自動context loadingや検証に使用できないため、機械可読版を必須とする。

Markdownと機械可読版の内容が乖離しない生成・検証方法を併記すること。

---

## 5. 人間向け資料の必須構成

### 5.1 Executive Summary

* 現在の2DERの正式な実行入口
* 現在LIVEな主要経路
* BUILTだが未接続の主要機能
* 最大の未接続箇所
* 現在進めようとしている追加経路
* Execution Architecture上の最大リスク

### 5.2 Repository Map

各repoについて記載する。

```
repo名 / 役割 / 正本として保持する情報 / 主要entrypoint / 主要Python package /
外部から呼ばれる入口 / 他repoを呼ぶ出口 / 主な状態保存先 / 現在の状態
```

単なるディレクトリ一覧にはしないこと。

### 5.3 Runtime Entry Points

実際にシステムを起動する入口をすべて列挙する（shell script / CLI / Python module / API server / worker process / cron・systemd / manual Claude Code operation）。

各入口について：

```
entrypoint_id / 起動コマンド / 実体ファイル / 最初に実行される関数 / 入力 / 出力 /
常駐・単発 / 呼び出す次段 / 状態 / 証拠
```

### 5.4 End-to-End Execution Flows

用途別に、実行経路を追跡する。最低限、以下を確認すること。

1. ユーザー要求受付
2. RRI thread生成
3. 質問生成
4. ユーザー回答反映
5. RESOLVED判定
6. Task Selector
7. DW task作成
8. worker実行
9. validator
10. rollback
11. EventStore記録
12. Ledger更新
13. return_loop
14. 上級監査
15. 完了判定

各フローは以下の形式で記述する。

```
Stage A
file.py:function()
  ↓ input schema
Stage B
file.py:function()
  ↓ API/subprocess/import
Stage C
...
```

経路が途中で切れている場合は、そこで明示的に停止させる。

```
RRI RESOLVED
↓
NO PROVEN LIVE EDGE
↓
BUILT / UNWIRED
```

存在しない接続を補完して描かないこと。

### 5.5 Python Module and Function Map

```
module_id / repo / file path / 主要class・function / 責務 / 入力schema / 出力schema /
呼出元 / 呼出先 / 副作用 / 読込対象 / 書込対象 / LLM使用有無 / 現在状態
```

すべてのPythonファイルを機械的に羅列する必要はないが、正式実行経路上のファイルは漏らさないこと。

未使用ファイル、孤立モジュール、旧実装候補も別表にすること。

### 5.6 LLM Invocation Map

```
invocation_id / 呼出元ファイル・関数 / 利用モデル / endpoint / system prompt source /
user・context input source / schema / temperature等の主要設定 / timeout・retry /
出力validator / 失敗時処理 / 結果保存先 / 状態
```

特に以下を明確にする。

* LLMへ渡される資料は何か
* どのコードがその資料を選ぶか
* LLM自身が資料を探すのか
* Python側がcontextを構築するのか
* 出力が自由文か構造化JSONか
* LLM自己申告が完了証拠として使われていないか

### 5.7 Mandatory Read Paths

各実行段階で、必ず参照されるべき資料と、実際に参照されている資料を分けて記載する。

```
stage / required_by_design / actually_loaded / loader implementation / evidence / gap
```

例：

```
DESIGN_STAGE
required_by_design:
- Capability Registry
- Functional Edge Graph
- relevant DE records
- repository snapshot
actually_loaded:
- handoff log only
result:
CONTEXT_GAP
```

これにより、「資料は存在するが実行時に読まれていない」問題を検出すること。

### 5.8 Write-back and Canonical Store Map

各出力がどこへ書き戻されるかを整理する。最低限以下を区別する。

* 実行観測 / 設計判断 / 要求と質問 / Capability状態 / Edge状態 / 未解決事項 / failure / audit / commit / artifact

形式：

```
information class / canonical store / writer implementation / reader implementation /
retention / conflicting store / status
```

EventStore、EGL、DESIGN_EVIDENCE_LEDGER、RTHREAD等の責務重複や不明確箇所を明示すること。

### 5.9 State Machine Map

主要state machine（RRI / task / DW / worker / validation / audit / rollback / completion）について、

```
states / transitions / transition owner / guard / evidence / write location / caller
```

を示す。複数のstate machineが同一概念を別名で保持している場合は矛盾として記録すること。

### 5.10 Current / Planned / Unknown Overlay

同じ図または同じ表の中で、CURRENT（現在実装されている経路）/ PLANNED（追加予定の経路）/ UNKNOWN（調査不能または未決定の経路）を区別する。

今回の検討対象として、少なくとも以下の構想をPLANNED候補として記載すること。

```
RRI
↓ Development Context Builder
↓ Knowledge Dispatcher
↓ Environment / Repository / Failure / Technical Knowledge Loaders
↓ Design Planner
↓ Design Adjudicator
↓ DW Plan Builder
↓ Admission
↓ Task Selector / DW
```

ただし、これは確定仕様として扱わない。現行実装との差分、必要な新規Capability、再利用可能な既存Capability、未決事項を記載すること。

### 5.11 Gap and Contradiction Register

以下を一覧化する。

* 仕様にはあるが実装がない
* 実装はあるが仕様にない
* BUILTだが本線未接続
* 呼出元がない
* 読込経路がない
* 書戻し先が不明
* 正本が重複している
* stateが競合している
* 古いhandoffと現行実装が矛盾する
* testはあるがLIVE証拠がない
* contextがLLM任せになっている
* LLM出力が未検証で次段へ渡る
* 同一機能の重複実装候補

各項目に以下を付ける。

```
gap_id / 説明 / 影響 / 証拠 / 現在状態 / 推奨対応 / 優先度 / authority route
```

---

## 6. 機械可読版の最低schema

```json
{
  "architecture_id": "2DER-EXECUTION-ARCHITECTURE",
  "version": "0.1",
  "generated_from": { "repositories": [], "commits": [], "documents": [] },
  "entrypoints": [],
  "components": [],
  "llm_invocations": [],
  "edges": [],
  "read_paths": [],
  "write_paths": [],
  "state_machines": [],
  "canonical_stores": [],
  "execution_flows": [],
  "gaps": [],
  "planned_extensions": [],
  "unknowns": []
}
```

各componentとedgeには最低限以下を持たせる。

```json
{
  "id": "", "repo": "", "file": "", "symbol": "",
  "status": "LIVE|BUILT|WIRED_UNPROVEN|DECLARED|PLANNED|UNKNOWN|DEPRECATED|CONTRADICTED",
  "evidence": [], "last_verified_commit": ""
}
```

Edgeには追加で以下を持たせる。

```json
{
  "from": "", "to": "",
  "mechanism": "import|call|api|subprocess|file|event|manual",
  "input_schema": "", "output_schema": "", "runtime_proven": false
}
```

---

## 7. 調査方法

### 7.1 最初にrepoを固定する

全repoについて `git status -sb` / `git rev-parse HEAD` / `git log -1 --oneline` を記録する。**調査中に変更を加えないこと。**

### 7.2 静的調査

`find` / `rg` / `tree` / `git grep` を最低限行う。検索対象例：

```
if __name__ == "__main__" / argparse / click / typer / FastAPI / Flask / uvicorn /
subprocess / requests / httpx / emit / EventStore / RTHREAD / TaskSelector /
return_loop / validator / worker / Claude / Qwen / OpenAI / vllm / completion / chat/completions
```

### 7.3 動的確認

安全なread-onlyまたは既存test範囲で、実際の呼出し経路を確認する（test実行 / `--help` / dry-run / log確認 / monkeypatch等によるcall capture / EventStoreの実行証拠確認）。

**本番変更や新規writeを伴う確認は行わない。必要なら事前にTakaへエスカレーションすること。**

### 7.4 仕様との照合

実装確認後に仕様、Ledger、handoffと比較する。**先に仕様を読んで実装をその通りに解釈しないこと。**

---

## 8. 更新方式

この資料を一度作って終わりにしない。

今後Capability、Edge、entrypoint、LLM call、正本、state machineを変更する際は、Execution Architecture更新を変更完了条件に含める案を提示すること。

最低限、次の運用を設計する。

```
コード変更 → Architecture diff生成 → 既存Execution Architectureとの矛盾検査 → 資料更新 → commit
```

可能であれば、以下の自動検査案を作る。

* 記録されたfile/symbolが存在するか
* 記録されたedgeが静的に確認できるか
* commit hashが古くないか
* 新しいLLM invocationが未登録でないか
* 新しいentrypointが未登録でないか
* BUILTからLIVEへの昇格に実行証拠があるか
* PLANNEDを誤ってCURRENTに表示していないか

ただし、この自動化自体の実装は本作業の必須範囲ではない。設計案と最小検証方法を提示すること。

---

## 9. 禁止事項

* 理想的な将来構成を、現在構成として記載しない
* ファイル名や関数名を推測で書かない
* 仕様書に書いてあるだけでLIVEとしない
* importが存在するだけでFunctional Edge成立としない
* test greenだけで本線接続済みとしない
* LLMの自己申告を証拠にしない
* 調査中に接続修正を始めない
* 新しいLedgerやRegistryを勝手に追加しない
* UNKNOWNを文章で曖昧化しない
* 全体図を綺麗に見せるために、切れた経路を補完しない

---

## 10. 完了条件

1. 全対象repoのcommitが記録されている
2. 正式entrypointが特定されている
3. 主要Python実行経路がfile/function単位で追跡されている
4. LLM invocation箇所が一覧化されている
5. 各段階のread pathとwrite-back pathが記載されている
6. RRIからDWまでの現在経路が、切断箇所を含めて描かれている
7. LIVE、BUILT、PLANNED、UNKNOWNが明確に分離されている
8. EventStore、EGL、各Ledger、RTHREADの責務が比較されている
9. 現在計画中のDevelopment Context / Knowledge Dispatcher構想が、現行との差分として記録されている
10. Gap and Contradiction Registerが作成されている
11. Markdownと機械可読版が作成されている
12. 再現可能な調査コマンドと証拠が記録されている
13. 既存の正式文書体系へ登録する場所が決定されている
14. commit前にTakaへ内容を提示し、承認を得ている

---

## 11. 最終報告形式

最終報告では以下のみを簡潔に提示する。

```
A. 作成したファイル
B. 調査対象commit
C. 現在の正式実行経路
D. 最大の切断箇所
E. BUILTだが未接続の主要要素
F. 仕様と実装の主要矛盾
G. PLANNEDとして追加した将来経路
H. UNKNOWNとして残した事項
I. 推奨する次の一手
J. commit候補
```

**コードや接続の修正には進まず、まず資料を完成させて提示すること。**

---

*（原文末尾の補足）最初は「完全な現状記録」を優先し、将来構想はPLANNEDとして重ねる形にしています。これなら、調査の途中でまた新設計へ脱線しにくくなります。*
