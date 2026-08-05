# 【指示】**★モデルに届く指示文 9本を「許可集合」に書き換える（Taka 指示・全数）**

- **宛: MGR** ／ 写: Taka / 設計・監査(CC-α) ／ **発: 監視** ／ 2026-08-05 20:5x ／ TYPE=指示（Taka 依頼）
- **開発者規律 確認済（版: v1.14）** ／ 親: `ITEM-2DER-EVO-0035`
- **★新台帳0・新計器0・新規則0・新エンドポイント0**（★既存の文字列を差し替えるだけ）
- **★走行 0・commit 0・実装 0行**（監視が読んで数え、案を書いた）

---

## 0. ★Taka 指示（逐語・要点）

```
これは全部「禁止」なので、★小型 LLM ほど「何をすればいいか」が弱くなります。
肯定形にすると、行動が一意になりやすいです。
「禁止」ではなく★「許可集合」を定義する方がさらに強くなります。
  ・使用可能な入力 ・使用可能な操作 ・使用可能な出力 ・証拠不足時の既定動作
の4つを肯定形で定義する方が、7B〜35B クラスでは一貫性が高くなる可能性があります。
★想定可能な指示文 全部ね。一箇所かえてもしゃーない
```

## 1. ★実測（★どれが本当にモデルへ届くか・出典つき）

| # | 場所 | 役 | 否定の数 |
|---|---|---|---|
| P1 | `twoder/qwen_worker.py:74-75` | worker | 3 |
| P2 | `twoder/generate_via_runner.py:116-120` | worker(requirement) | 1 |
| P3 | `twoder/build_planner.py:140-167` | planner | **★7** |
| P4 | `rri/rri/request_type.py:39-57` | 依頼種別の分類 | 4 |
| P5 | `rri/rri/research_intent.py:42-48` | 詰まりの分類 | 1 |
| P6 | `rri/rri/research_intent.py:60-67` | 調査要否 | 2 |
| P7 | `rri/rri/research_intent.py:76-84` | 解決要件 | 2 |
| P8 | `dev-workcell/dw/adapters.py:_CODER_SYSTEM` | coder | 3 |
| P9 | `dev-workcell/dw/adapters.py:_AUDITOR_SYSTEM` | auditor | 1 |

```
★合計 18 か所。★9本すべて system/user prompt として ★実際にモデルへ届く（呼び出し行で確認）
★BUILD SPEC の「依頼文」は ★届かない（contract_seal が抜くのは skeleton と immutable_tests だけ）
   ∴ ★本書は spec 本文を対象にしない（2026-08-05 の実測・v4〜v7 の空振りと同じ轍を踏まない）
```

---

## 2. ★書き換え案（★原文と同じ言語のまま。★言語は変えない＝変数を増やさない）

### P1 worker（`qwen_worker.py:74-75`）

```
現行: "Implement a Python function for this requirement: %s. Output ONLY the function in a single
       ```python code block. ★No tests, ★no explanation."
```
```
案:
"Implement a Python function for this requirement: %s.
ALLOWED INPUT: the requirement text above.
ALLOWED OPERATIONS: write one Python function definition.
ALLOWED OUTPUT: exactly one ```python code block whose entire content is that function definition.
IF THE REQUIREMENT IS INSUFFICIENT: output one ```python code block containing a single line
  `raise NotImplementedError(\"insufficient requirement\")`."
```

### P2 requirement テンプレ（`generate_via_runner.py:116-120`）

```
現行: 「以下の骨格の固定区間(import 等)を bytes 一致で保存したまま <<<FILL>>> マーカー部分★だけを実装し、
       同梱の immutable_tests を全て通すコードを impl.py として書け。」
```
```
案:
「ALLOWED INPUT: 下の skeleton と immutable_tests。
 ALLOWED OPERATIONS: skeleton の <<<FILL>>> 行を、実装コードで置き換える。
   skeleton の他の行は bytes 一致で維持する。
 ALLOWED OUTPUT: impl.py の全文（immutable_tests を通すもの）。
 情報が足りない場合: <<<FILL>>> を `raise NotImplementedError(\"insufficient spec\")` で置き換える。」
```

### P3 planner（`build_planner.py:140-167`）★最大の集中点

```
現行の否定（逐語・7か所）:
  "★Do not implement it; plan it."
  "target_workspace ... (a temporary/sandbox directory path; ★NEVER an existing project repo)"
  "already_satisfied ... items that need ★NOT be built"
  "Use ★ONLY the Python standard library."
  "★Do not commit, push, use the network, use sudo, or ★modify any existing repository."
```
```
案（★禁止5連を許可集合1つに畳む）:
"ALLOWED OPERATIONS: produce a plan document.
ALLOWED IMPORTS for the planned code: the Python standard library.
ALLOWED WRITE TARGETS: paths under the sandbox workspace given below.
ALLOWED EXTERNAL ACTIONS: none are part of this task; the plan describes code only.
target_workspace MUST be a path under the sandbox root provided.
already_satisfied: list items that are ALREADY AVAILABLE (the worker will reuse them).
IF A REQUIRED FIELD CANNOT BE DETERMINED: set it to the empty array/string and
  add one entry to \"unresolved_assumptions\" naming the missing input."
```

### P4 依頼種別の分類（`request_type.py:39-57`）

```
現行の否定: "(★not how to do it)" / "is ★NOT building the capability" /
            "★Do NOT upgrade an inspection request into a ..." / "★not by matching keywords"
```
```
案（★定義側を許可集合にする。判別文はそのまま残す）:
"You resolve WHAT THE USER IS ASKING FOR.
ALLOWED OUTPUT: exactly one of
  OBSERVE_CURRENT_STATE | BUILD_CAPABILITY | MODIFY_EXISTING | RESUME_PRIOR | DECIDE | OTHER.
CHOOSE OBSERVE_CURRENT_STATE when the request asks to find out / inspect / check a current state
  (including saving that single result).
CHOOSE BUILD_CAPABILITY when the request asks to make something possible repeatedly or for others
  (\"…できるようにして\" / \"make it possible to …\" / \"so others can …\").
BASIS: decide from what is asked. Put the deciding phrase in \"basis\".
IF THE REQUEST MATCHES NO DEFINITION ABOVE: return \"OTHER\"."
```

### P5 詰まりの分類（`research_intent.py:42-48`）

```
現行の否定: "★Do NOT propose a solution. Classify only."
```
```
案:
"ALLOWED OUTPUT: {\"classification\": one of knowledge|implementation|policy|mixed, \"basis\": string}.
ALLOWED OPERATIONS: assign one class and quote the deciding evidence in \"basis\".
IF THE FINDING MATCHES NO CLASS: return \"UNRESOLVED\"."
```

### P6 調査要否（`research_intent.py:60-67`）

```
現行の否定: "★Do NOT treat the finding's own missing_knowledge_hint as the proven root cause"
            "★Do NOT propose a solution."
```
```
案:
"ALLOWED INPUT: the finding and its blockage classification.
ALLOWED OPERATIONS: (1) list alternative non-research causes, (2) decide research_required from that list.
ALLOWED OUTPUT: {\"research_required\":bool, \"missing_knowledge_hint_is_root\":bool,
                 \"alternative_causes\":[...], \"why\":string}.
TREAT missing_knowledge_hint AS ONE CANDIDATE among the alternatives you list.
IF THE EVIDENCE IS INSUFFICIENT: set research_required=null and name the missing evidence in \"why\"."
```

### P7 解決要件（`research_intent.py:76-84`）

```
現行の否定: "★CRITICAL: do NOT propose a specific solution, object, schema, registry, or mechanism design."
            "Requirements describe WHAT must be known/retained, ★not HOW to build it."
```
```
案:
"ALLOWED OUTPUT: {\"decision_axes\":[...], \"missing_state_or_capability\":[...],
                  \"resolution_requirements\":[...]}.
EACH resolution_requirement IS A SENTENCE OF THE FORM
  \"<X> must be known\" or \"<X> must be retained\".
ALLOWED VOCABULARY for missing_state_or_capability: names that already appear in
  OPERATIONAL_FINDING or CURRENT_SYSTEM_STATE.
IF A REQUIREMENT CANNOT BE STATED IN THAT FORM: omit it and add the reason to \"decision_axes\"."
```

### P8 coder（`dw/adapters.py:_CODER_SYSTEM`）

```
現行の否定: "implements ★ONLY the narrow_goal" / "honouring ★forbidden_assumptions"
            "★Do NOT claim tests passed — you cannot run them here."
```
```
案:
"ALLOWED INPUT: the IMPLEMENTATION_PACKET.
ALLOWED SCOPE: the narrow_goal, limited to paths listed in in_scope.
ALLOWED OUTPUT: {\"diff\": unified diff string, \"problems\": [string]}.
TEST STATUS: tests run elsewhere; report observed problems in \"problems\".
IF THE PACKET IS INSUFFICIENT: return {\"diff\": \"\", \"problems\": [\"<missing input>\"]}."
```

### P9 auditor（`dw/adapters.py:_AUDITOR_SYSTEM`）★書き換え最小

```
現行は ★ほぼ許可集合の形（カテゴリ列挙＋出力形＋既定動作 "return []"）。
変更点は1つだけ: "If genuinely none, return []" →
  "IF NO FINDING MATCHES THE CATEGORIES ABOVE: return []."
```

---

## 3. ★測り方（★Taka の「1つだけ振る」と両立させる）

```
★9本を一度に替えると、効果の切り分けができない。
∴ 提案 = ★9本の書き換えを ★1つの変更として扱う（★否定ゼロ群 vs 現行）。
   ★契約と immutable_tests は ★1文字も変えない。
   ★同じ契約を ★複数回 走らせてから比べる（同一契約が 1〜18 に散る実測が在るため）。
★受入 = 「否定の数が 18 → 0」は ★機械で数えられる。★通過本数は ★分布で比べる（1走行で優劣を書かない）。
```

## 4. ★私が言っていないこと

```
・この書き換えで通過本数が上がる ―― ★予想は書かない（本日の裁定に従う）
・spec 本文の否定も直せ ―― ★spec は worker に届かない。本書の対象外
・言語を英語/日本語に統一しろ ―― ★変数を増やすので触らない
・9本で全部だ ―― ★私が確認したのは system/user prompt の定義箇所。
  ★動的に組み立てて渡している文が他に在る可能性は残る
```
