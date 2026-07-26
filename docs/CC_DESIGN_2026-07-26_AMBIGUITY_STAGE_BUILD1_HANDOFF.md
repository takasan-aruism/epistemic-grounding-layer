# 設計/監査 → 実装: Build 1 — 前提曖昧ステージ（preflight_gate の N ゲート化 + 束縛先の有無で撃つ）（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=HANDOFF
- 正典: `CC_MGR_2026-07-26_BUILD_GO_AMBIGUITY_STAGE_AND_BACK_SLICE.md`（Taka「実際作ってみないとなんともいえん・やってみて」＝build GO）+ `CC_DESIGN_2026-07-26_PREMISE_AMBIGUITY_AB_COMPARISON_FINDING.md`（**§3b の訂正を必ず読むこと**）
- 成果物: `rri/rri/preflight_gate.py` の拡張 + `rri/rri/ambiguity_patterns.jsonl`（新規）+ 回帰セット
- **完全決定論。`:8005` を使わない。LLM 呼出ゼロ。**

## 0. ★前提の訂正（古い数字で設計しないこと）
比較 FINDING §3 で「(A) は 25.1% 過剰発火」と書いたが、**これは重複35%による水増しで誤り**。**ユニーク298件では 3.7%**。
- **(A) の不採用理由は「過剰発火」ではなく「我々の失敗を 0/3 で全く捕まえない」の一点。**
- **回帰セットは必ず重複除去したユニーク集合を使う**（率を出す前に dedup）。

## 1. 段の一般化（既存 LIVE を壊さない）
`rri/rri/preflight_gate.py` は **front door の 3d 段（ROUTING の直前）で LIVE**（`twoder/submit.py:231`）。
- 現行の 1 ゲート（`RRI-GATE-AMBIGUOUS-QUANT-001`＝数値主張+出典曖昧）を**ゲート表の1エントリに移す**。
- `detect()` を「**登録された全ゲートを順に回し、最初に triggered したものを返す**」に変更。
- **★`submit.py` 側の呼び方・戻り値の形は一切変えない**（新規配線ゼロ）。既存キー（`gate_id`/`claim_pattern_id`/`triggered`/`decision`/`blocks_dw_escalation`/`proposed_egl_status`/`signals`/`basis`）を**維持**。
- **既存 HBB-30 ゲートの挙動は byte 単位で不変であること**を回帰テストで示す（`twoder/regression/test_preflight_gate.py` が通り続ける）。**新機能で既存を壊さない。**

## 2. 様式の移植（(A) input-clarity のスキーマ）
`rri/rri/ambiguity_patterns.jsonl` を新設。1行1ゲート。フィールド:
- `pattern_id` / `ambiguity_type`（`REFERENT` / `PREMISE` / `SCOPE` …）/ `description`
- **`clarification_slots`**（★核: **何を聞き返せばよいか**。`NEXT_LEGAL_OPERATION` の文面をここから構成し、**聞き返し文を捏造しない**）
- `possible_readings` / `rewrite_examples` / `false_positive_notes`
- **`observed_count` / `accepted_warning_count` / `ignored_warning_count` / `suppressed`**（無視され続けた警告を自動抑制＝過剰聞き返しの構造的対処。**最初から有効化**）
- `decision`（この gate が triggered した時に返す決定。既定 `CLARIFY_FIRST`）

## 3. ★★検出規則 — 表層一致だけで撃たない（本 Build の中核）
**我々の失敗は「指示語がある」ことではなく「指示語の指す先が無い」ことである。**

実測（ユニーク298件・我々の3件）:

| 規則 | 誤発火 | 捕捉 |
|---|---|---|
| 指示語の表層一致のみ | 2.0% (6/298) | 3/3 |
| **文頭の裸の指示語（あれ/それ/例のやつ + 読点/空白）** | **0.0% (0/298)** | **3/3** |

- 表層で当たった6件は `前の件を優先して進めて` 等＝**文脈から指示先を解決できる可能性が高い**。**表層だけで撃てば、解決できるものまで止める。**
- **∴ 発火条件 = `指示語の表層` AND `束縛先が無い`。**

### `束縛先が無い` の決定論判定（★ここが LLM にできない部分）
1. **呼び出し側から `context`（直前の文脈/直近の束縛可能対象）を受け取る引数を新設**する。既定 `None`。
2. `context` が空/None → **束縛先なし**。
3. `context` があっても、**指示語を束縛しうる名詞句が含まれない**なら束縛先なし（**判定規則は事前固定・記録**。凝った照応解析はしない＝thin）。
4. **同一発話内で自己解決している場合は撃たない**（例: `この設計案の得失は？` は直後に対象がある）。**BV3「この設計案の得失は？」で誤発火しないことを必ず確認**（fixture に在る）。

### ★実運用での注意（必ず BUILT に書くこと）
- **現行 `submit.py` は `preflight_gate.detect()` に文脈を渡していない。** 引数を足しても、**呼び出し側が文脈を渡さない限り「常に束縛先なし」と判定される**。
- ＝**Build 1 の時点では、fixture 試験（context 明示）と実 front door（context 未配線）で挙動が変わる。**
- **この差を隠さず、BUILT に「front door からの context 配線は未実装」と明記**すること。配線は Build 2（縦串）で扱う。**「動いた」と書かないこと。**

## 4. パターンは我々の証拠から起こす（(A) の34件は流用しない）
最小限、以下の1クラスから開始（**証拠のあるものだけ**）:
- `AMB-REF-001` `ambiguity_type=REFERENT`: **文頭の裸の指示語で、束縛先が無い**（証拠: IP1/IP2/IP3 が意図調べで 0〜1/3、`CONTEXT_RESOLVE` を選ぶ＝文脈捏造3度目・DE-0548）
  - `clarification_slots`: `["指示語が指す対象の一意な識別子（DE番号/ファイル名/タスクID等）"]`
  - `possible_readings`: 例を記録
- **これ以外のパターンを勝手に増やさない。**追加したいものがあれば**提案のみ**して DESIGN→Taka の承認を待つ（証拠なしにパターンを増やすと (A) の轍を踏む）。

## 5. 測定（受入の核）
1. **捕捉**: IP1「あれ、どこにあったっけ？」/ IP2「それ、その後どうなった？」/ IP3「例のやつ、進んでる？」を段に通し、**triggered=True になるか**（今まで意図調べで 0〜1/3 だったものを、手前で確実に捕まえられるか）。
2. **誤発火（★必ず dedup してから）**: **ユニーク298件**の実発話に対する発火率。**目標は「発火率を上げること」ではない。**
3. **既存ゲートの非回帰**: HBB-30 の5決定が従来どおり。`test_preflight_gate.py` GREEN。
4. **自己解決ケースの非発火**: `この設計案の得失は？`（BV3）で triggered=False。
5. **意図調べ側との重複確認**: 段で捕まえた場合、**意図調べを呼ぶ必要がなくなるのか、それとも両方走るのか**を明示（設計上どちらでもよいが、**どちらにしたかを記録**すること）。

## 6. 受入
1. `--check` GREEN（決定論再現／パターン DB のスキーマ検証／抑制カウンタの適用が決定論）。
2. §5 の5項目すべてを数値で報告。**捕まえられなければ「捕まえられなかった」と書く。**
3. **既存 LIVE 挙動の非回帰を実証**（これが最優先。新機能より既存を壊さないことが上）。
4. **`submit.py` 未配線の事実を BUILT に明記**（§3 の注意）。
5. cross-repo: `rri` を触るので **rri 単体で commit + push**（[[2der_repo_topology]]・片方だけ push しない）。

## 7. 規律
- **完全決定論・LLM ゼロ**。曖昧かどうかを LLM に判断させない（**model は空白を埋める側に倒れる**＝3度の目撃）。
- **measure-first**: 誤発火が高ければ高いと報告し、規則を緩めない。
- **数字を出す前に必ず dedup**（§0）。
- commit=Taka。DE は front door `record_de` + `CLAUDE_CODE` 開示。★3 本線は止めない。

---
*DESIGN CC-α。段は既に LIVE・壊さず N ゲート化。撃つ条件は「指示語がある」でなく「指す先が無い」。束縛先の有無は機械にしか判定できない。数字は dedup してから。*
