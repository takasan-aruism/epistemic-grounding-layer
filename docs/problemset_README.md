# Adjudicator Efficacy 問題セット v0.1(sealed fixtures)

対象実験: DW_ADJUDICATOR A/B efficacy試験(GPT実験計画準拠)
本パッケージの範囲: **10問の問題本体・注入欠陥・封印ground truth・単一欠陥性QA・ハッシュ封印**のみ。
preregistration文書の作成とDS→RRI→EGL登録はClaude Codeの担当工程であり本パッケージに含まない。

## 問題一覧

| ID | Level | class | 注入箇所 | 期待routing |
|----|-------|-------|---------|------------|
| Q01 | 1 | CODE_DEFECT | src/solution.py 戻り値 | REGENERATE |
| Q02 | 1 | ORACLE_DEFECT | tests期待値(add(2,3)==6) | ORACLE_ISOLATION_JUDGE_REQUIRED |
| Q03 | 2 | EXECUTION_DEFECT | runner.json 誤script path | RUNTIME_RETRY |
| Q04 | 2 | INDETERMINATE | evidence(stdout/stderr/runner identity欠損) | SAFE_STOP_JUDGE_REQUIRED |
| Q05 | 3 | CODE_DEFECT | cli.py missing-file握り潰し | REGENERATE |
| Q06 | 3 | ORACLE_DEFECT | testがstderrでなくstdoutを検査 | ORACLE_ISOLATION_JUDGE_REQUIRED |
| Q07 | 4 | EXECUTION_DEFECT | setup.shがfixtures/を破壊 | ENV_REPAIR_RETRY |
| Q08 | 4 | INDETERMINATE | fixture/artifact hash欠損+結果不一致 | SAFE_STOP_JUDGE_REQUIRED |
| Q09 | 5 | CODE_DEFECT | stats.py 平均の分母=全行数 | REGENERATE |
| Q10 | 5 | ORACLE_DEFECT | expected_result.json 平均を4件で計算 | ORACLE_ISOLATION_JUDGE_REQUIRED |

class分布: CODE×3 / ORACLE×3 / EXECUTION×2 / INDETERMINATE×2。各問の注入は一種類のみ(qa_report.jsonで機械確認済み)。

## 語彙の固定

classification: CODE_DEFECT / ORACLE_DEFECT(subtype=TEST_IMPLEMENTATION_DEFECT) /
EXECUTION_DEFECT / INDETERMINATE

routing: REGENERATE / ORACLE_ISOLATION_JUDGE_REQUIRED / RUNTIME_RETRY /
ENV_REPAIR_RETRY / SAFE_STOP_JUDGE_REQUIRED / DIAGNOSTIC_REQUEST / DISPOSE

terminal(Stage 2): REGENERATED_THEN_PASS / CODE_UNCHANGED_ORACLE_ISOLATED /
PASS_AFTER_ENV_REPAIR_CODE_UNCHANGED / SAFE_STOP_JUDGE_REQUIRED_CODE_UNCHANGED

採点は expected_routing への一致を正、allowed_routing_alternatives への一致を条件付き正
(集計時は別列)、それ以外を誤りとする。

## harness契約(実行側が守ること)

1. **sealed/ は問題ごとに存在し、worker / adjudicator / judge いかなるLLM contextにも
   入れてはならない。** sealed/ には ground_truth.json と baseline(正解実装 / 正解oracle /
   正解runner / 正解setup)が入っている。採点コードのみが読む。
2. Stage 1(classifier/routing isolation): worker生成なし。CODE/ORACLE/EXECUTION問題は
   shipped workspace(注入済み)を runner.json 通りに決定論実行し、その結果evidenceを
   adjudicatorへ渡す。INDETERMINATE問題(Q04/Q08)は実行せず
   evidence/stage1_evidence_packet.json をそのまま渡す(証拠欠損の決定論的再現)。
3. Stage 2(full loop): shipped workspaceをinitial artifactとして固定し、rework〜terminal
   stateまで回す。Q04/Q08のstage 2注入機構はground_truth.jsonの
   stage2_injection_mechanism を参照。
4. A/Bで変更してよいのは DW_ADJUDICATOR フラグのみ。task packet / prompt / model /
   seed / runner / tests / retry / token policy / workspace初期状態 / oracleは固定。
5. workspace_manifest.json(Q07/Q08/Q09/Q10)はadjudicatorへ渡してよい証拠である
   (EXECUTION_DEFECT判別の正当な材料)。
6. 実行順・問題間の情報持ち越し禁止(問題ごとに独立context)。

## 封印(seal)の意味

sealed_manifest.json は全ファイルのSHA-256と、その整列結合のハッシュ(seal_root)を持つ。
登録時に seal_root をEGLへ記録すること。実行後のground truth改変・fixture差し替えは
seal_rootの不一致として検出できる。**ground truthの事後変更・都合の良い再解釈を禁止する**
(preregistrationの実体はこのコミットメント)。

## QA(単一欠陥性の機械確認)

qa_report.json に全20 runの結果を保存済み(ALL_OK=true)。確認内容:
- 各問題のshipped(注入)状態が、期待したcheckだけで失敗する
  (例: Q09はaverage_mainのみ失敗、他10 checkはPASS)
- sealed/baselineへ差し替えると全checkがPASSする(欠陥が注入物のみに由来する証明)
- INDETERMINATE問題はコード・oracleとも健全で、欠損はevidence側にのみ存在する

## 既知の設計判断

- Q5/Q9は実JSONL課題に近い題材だが、ground truth未確定の実課題そのものは混ぜていない
  (実課題はOBSERVATIONAL-JSONL-01として別枠、GPT計画通り)。
- Q05(CODE: 本物のmissing file誤処理)とQ07(EXECUTION: 環境がfixtureを消した)は
  表面症状が似るよう意図的に設計してある。判別材料はworkspace_manifest.jsonと
  setup実行証拠であり、これがadjudicatorの弁別力を測る対になる。
- Q09とQ10は同一課題・同一fixtureで、欠陥の側だけが違う対(code vs oracle)。
  平均値の再計算可能性が弁別の鍵。
