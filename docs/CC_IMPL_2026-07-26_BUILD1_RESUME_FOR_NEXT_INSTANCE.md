# 実装(IMPL) 自己引き継ぎ → 次の IMPL インスタンスへ: Build 1（前提曖昧ステージ）着手直前の状態（RESUME）

- 宛: 次の IMPL(coder) インスタンス / 発: 実装(IMPL) / 2026-07-26 / TYPE=RESUME
- 一行: **Build 1 の全資料を読み・役割合意済み・コード未着手。この直後から `rri/rri/preflight_gate.py` を N ゲート化する段階。**

---

## 0. あなたは誰か（30秒）
- あなたは **IMPL（coder）**。マルチインスタンス 2DER 開発の実装担当。
- **CC-α = DESIGN/AUDIT**（spec を書き・私の実装を独立再監査する別インスタンス）。**MGR = 管理**。**Taka = 人間**（commit 決定＋哲学・裁定を握る）。
- 通信は **`/home/takasan/egl/docs/CC_<FROM>_<date>_<topic>_<TYPE>.md`** の file drop のみ。FROM∈{MGR,DESIGN,AUDIT,IMPL}、TYPE∈{HANDOFF,FINDING,ADJREQ,ADJRESULT,STATUS,RESUME,BUILT}。
- topology: `coder(IMPL)─audit(AUDIT)─designer(DESIGN)─manager(MGR)`（隣接のみ・coder↔manager は直接やり取りしない）。**あなたが監視するのは DESIGN→IMPL と AUDIT→IMPL の inbound。**
- 標準ループ: DESIGN handoff → IMPL が working tree に実装＋`--check` GREEN → `CC_IMPL_*_BUILT.md` を drop → CC-α が独立再監査 → **commit=Taka**。
- 詳細は memory: [[claude_operates_2der]] [[instance_comms_protocol]] [[2der_monitoring_duty]] [[2der_repo_topology]] [[investigate_before_inventing]]。

---

## 1. 今の担当タスク = Build 1（前提曖昧ステージ）
**Taka が build GO 済**（「実際作ってみないとなんともいえん・やってみて」）。目的＝意図調べ(前者 ~0.78)の**一段手前**に、**決定論の曖昧検知ゲート**を置く。粘る弱点「指示語の指す先が無い」を LLM でなく機械で捕まえる。

### 必ずこの順で読め（正典・全て egl/docs）
1. **`CC_DESIGN_2026-07-26_AMBIGUITY_STAGE_BUILD1_HANDOFF.md`** ← ★本命 spec。
2. **`CC_DESIGN_2026-07-26_PREMISE_AMBIGUITY_AB_COMPARISON_FINDING.md` の §3b** ← ★訂正（古い数字で設計するな）。
3. **`CC_DESIGN_2026-07-26_BUILD1_CORRECTION_TO_IMPL_STATUS.md`** ← ★着手前訂正＋回帰コーパスの抽出レシピ。
4. `CC_MGR_2026-07-26_BUILD_GO_AMBIGUITY_STAGE_AND_BACK_SLICE.md`（GO の出所・Build 2 も規定）。
5. 私が置いた `CC_IMPL_2026-07-26_BUILD1_CLAIM_STATUS.md`（役割主張＋事前申告）。

### 既に済んでいること（あなたは繰り返さなくてよい）
- ✅ **役割合意**: Build 1 の実装は IMPL が取る／CC-α は AUDIT に回る（`..._CORRECTION_TO_IMPL_STATUS §0` で合意）。二重発明回避のため私が claim を落とした。
- ✅ **資産の実読**: `rri/rri/preflight_gate.py`(54行) / `twoder/submit.py:227-250`(3d段) / `input-clarity-prototype/data/patterns.jsonl`(様式) を読了。要点は下記 §2 に転記済み。
- ✅ **配線1点の許可取り**: NEXT_LEGAL_OPERATION の文面を gate 由来にする最小変更は CC-α が承認（`§2`）。条件つき（下記）。
- ❌ **コードは未着手。**

---

## 2. 実装スペック（再導出不要・全部ここにある）

### 成果物（handoff §「成果物」）
- `rri/rri/preflight_gate.py` の拡張（N ゲート化）
- `rri/rri/ambiguity_patterns.jsonl`（新規・様式は (A) 由来）
- 回帰セット（measurement harness。egl/structure 側に置くのが自然だが場所は任せる。**新 structure script は commit 同梱必須**＝meta self-heal hook）
- **完全決定論・`:8005` 不使用・LLM 呼出ゼロ。**

### (B) `rri/rri/preflight_gate.py` の現状（byte 単位で保存すべき既存挙動）
- 単一ゲート `RRI-GATE-AMBIGUOUS-QUANT-001`（数値主張+出典曖昧＝HBB-30）。
- `detect(raw_input, user_insists=None, failure_hits=None)` → dict。**既存キーを維持**: `gate_id`/`claim_pattern_id`/`triggered`/`decision`/`blocks_dw_escalation`/`proposed_egl_status`/`signals`/`basis`。
- 5決定: `CLARIFY_FIRST`/`HOLD_AS_WEAK_CLAIM`/`STRONGLY_DISCOURAGE_DW`/`ALLOW_WITH_WARNING`/`ALLOW`。
- **一般化**: 既存ゲートを**ゲート表の1エントリ**に移し、`detect()` は「登録全ゲートを順に回し最初に triggered を返す・無ければ ALLOW」に変更。**既存ゲートのロジックは不変**。

### submit.py 3d 段の制約（`twoder/submit.py:231` 前後）
- 呼び: `pg = PG.detect(raw_input, failure_hits=_fh)`。その後 `pg["triggered"] and pg["blocks_dw_escalation"]` の分岐で HOLD 記録し `return TRACE`。
- `NEXT_LEGAL_OPERATION` は**現状 quant 専用文が hardcode**（"ambiguous quantitative claim — concrete number + vague/missing source..."）。
- **要件（CC-α 確定）**: 「**submit.py の呼び出し契約（引数・戻り値の形）を変えない**」。**NEXT_LEGAL_OPERATION の文面を `pg` 由来にする最小1行変更は認める。** 条件:
  1. 変更は最小1点・**diff を BUILT に貼る**（隠さない）。
  2. **既存 HBB-30 の非回帰を最優先実証**（`twoder/regression/test_preflight_gate.py` GREEN ＋ quant ケースの文面が従来どおり）。
  3. 文面は **`clarification_slots` から構成し捏造しない**。

### (A) 様式 = `rri/rri/ambiguity_patterns.jsonl`（新規・1行1ゲート）
フィールド（handoff §2）: `pattern_id` / `ambiguity_type`(`REFERENT`/`PREMISE`/`SCOPE`…) / `description` / **`clarification_slots`**(★核=何を聞き返すか。NEXT_LEGAL_OPERATION をここから作る) / `possible_readings` / `rewrite_examples` / `false_positive_notes` / `observed_count` / `accepted_warning_count` / `ignored_warning_count` / `suppressed`(無視され続けた警告を自動抑制＝過剰聞き返しの構造的対処・**最初から有効化**) / `decision`(既定 `CLARIFY_FIRST`)。
- 様式の実物参考: `/home/takasan/input-clarity-prototype/data/patterns.jsonl`（**34パターンのデータは流用禁止**・様式だけ借りる）。

### ★★中核ルール — 表層一致だけで撃たない（handoff §3）
**我々の失敗は「指示語がある」ことでなく「指示語の指す先が無い」こと。** 実測（ユニーク298件/我々の3件）:

| 規則 | 誤発火 | 捕捉 |
|---|---|---|
| (A)34パターン表層 | 3.7% (11/298) | **0/3** |
| 指示語の表層のみ | 2.0% (6/298) | 3/3 |
| **文頭の裸の指示語（あれ/それ/例のやつ + 読点/空白）** | **0.0% (0/298)** | **3/3** |

- **発火条件 = `指示語の表層` AND `束縛先が無い`。**
- **`束縛先が無い` の決定論判定（★LLM にできない側）**:
  1. `detect()` に **`context` 引数を新設**（既定 `None`）。呼び出し側から直前文脈/直近の束縛可能対象を受ける。
  2. `context` が空/None → 束縛先なし。
  3. `context` があっても指示語を束縛しうる名詞句が無ければ束縛先なし（**判定規則は事前固定・記録・凝った照応解析はしない＝thin**）。
  4. **同一発話内で自己解決していれば撃たない**。★**BV3「この設計案の得失は？」で triggered=False を必ず確認**（fixture に在る）。

### 起こすパターン（証拠のあるものだけ・handoff §4）
- `AMB-REF-001` `ambiguity_type=REFERENT`: **文頭の裸の指示語で束縛先なし**。証拠＝IP1/IP2/IP3 が意図調べで 0〜1/3・`CONTEXT_RESOLVE` を選ぶ＝**文脈捏造3度目**（DE-0548。witness に DE-0545 も）。
  - `clarification_slots`: `["指示語が指す対象の一意な識別子（DE番号/ファイル名/タスクID等）"]`
- **これ以外を勝手に増やすな**（証拠なしに増やすと (A) の轍）。追加したければ**提案のみ**→ DESIGN→Taka 承認待ち。

### ★ context 未配線の正直な明記（絶対に守る・handoff §3 / CORRECTION §3）
- **現行 submit.py は `detect()` に文脈を渡していない。** 引数を足しても、渡さない限り**常に「束縛先なし」判定**になる。
- ＝**fixture 試験（context 明示）と実 front door（context 未配線）で挙動が変わる。**
- **BUILT に「front door からの context 配線は未実装」と明記。「動いた」と書くな。** 配線は Build 2（縦串）。

---

## 3. 測定（受入の核・handoff §5）
1. **捕捉**: IP1「あれ、どこにあったっけ？」/ IP2「それ、その後どうなった？」/ IP3「例のやつ、進んでる？」を段に通し **triggered=True になるか**（fixtures は `structure/s_intent_probe_armc3.py:58-60`。全て expected=INTENT_PROBE）。
2. **誤発火（★必ず dedup してから）**: **ユニーク298件**への発火率。**目標は率を上げることではない。**
3. **既存ゲート非回帰**: HBB-30 の5決定が従来どおり・`test_preflight_gate.py` GREEN。**これが最優先**。
4. **自己解決の非発火**: BV3「この設計案の得失は？」で triggered=False。
5. **意図調べとの重複**: 段で捕まえたら意図調べを呼ぶ必要が無くなるのか両方走るのか**を記録**（どちらでもよいが決めて書く）。

### ★回帰コーパスの正確な抽出レシピ（CC-α 指定・CORRECTION §1）
- ソース: **`ds/ds_events.jsonl`** の `record_type=UTTERANCE` かつ `speaker=USER`。
- **`開発エビデンスを登録` で始まる機械生成文字列（19件）を除外。**
- **その後 dedup** → 正典 = **ユニーク298件**。
- ⚠️ **478 のまま率を出すな**（重複35%で水増し＝CC-α が踏んだ穴。25.1% は artifact で撤回済み）。
- **数値を出す時は毎回「dedup 済み」と明記**（CC-α の依頼）。私はソースの正確な位置(`ds/ds_events.jsonl`)を未実読なので、**着手時に実在とフィールド名を確認**してから使え（[[investigate_before_inventing]]）。

---

## 4. 受入・規律（handoff §6-7 / CORRECTION）
- `--check` GREEN（決定論再現／パターン DB スキーマ検証／抑制カウンタ適用が決定論）。
- §3 の測定5項目すべて数値で。**捕まえられなければ「捕まえられなかった」と書く**（measure-first）。
- **既存 LIVE 挙動の非回帰実証が最優先**（新機能より既存を壊さないことが上）。
- **submit.py 未配線の事実を BUILT に明記。**
- cross-repo: **`rri` を触るので rri 単体で commit + push**（[[2der_repo_topology]]・片方だけ push しない）。**commit=Taka。**
- **完全決定論・LLM ゼロ**（曖昧を LLM に判断させない＝model は空白を埋める側に倒れる。3度の目撃）。
- **BUILT に一行**: 本 RESUME と `..._AB_COMPARISON_FINDING §3b` と `..._CORRECTION_TO_IMPL_STATUS` を読んだ旨（CC-α の依頼・読み違い再発防止）。
- DE 記録は front door `record_de` + `generated_by_principal`/`claiming_principal`="CLAUDE_CODE"・`generation_mode`="DIRECT"（忘れると UNKNOWN_PRINCIPAL 失敗）。

---

## 5. この後（Build 1 の外）
- **Build 2 = 後者の薄い縦串**（retrieve 1本 end-to-end／意図を故意に誤らせる注入試験／長文計測／メニュー LIVE 裏付け／probe→再開は返答を新依頼として再意図調べ／NOT_BUILT・BLOCK 必ず記録）。**Build 1 の BUILT+AUDIT の後**。spec は `CC_MGR_..._BACK_THIN_SLICE_DESIGN_DRAFT` + `..._REVIEW_FINDING`。
- **cheap-fix（意図調べ）は完了・CC-α 再監査 GREEN・Taka commit 待ち**。未 commit: `structure/s_intent_role_split_d2p2.py`・`INTENT_ROLE_SPLIT_D2P2.jsonl`・meta 3M。監査結果 `CC_DESIGN_2026-07-26_INTENT_CHEAP_FIX_REAUDIT_FINDING.md`（数値・規律 GREEN。私の「DEFER是正 +2件」は正しくは +1、CH1 はノイズ＝私が owned 済）。
- **未解決の Taka 裁定**: HBB-30 の「当初提案は記録より具体的だったかも」＝現存は 54行 preflight_gate.py と DE-0194 のみ、それ以上は repo 内に無い（`..._AB_COMPARISON_FINDING §7`）。無ければ現存を正典。

---

## 6. 繰り返してはいけない失敗（このセッションの教訓）
- CC-α に**過大主張を3回捕まった**（arm-C2 汚染 0.88／arm-D 過剰悲観／arm-D2' 選択役の取り違え）＋帰属 +2→+1。**規律＝見出しの前に指標を分解し・各部品が実際に効いたか検証し・負の結果を正直に・spin しない。**
- **measure-first**: 計器が弱い/負なら正直に。隠す・盛るは厳禁。
- **数字は dedup してから**（コーパス指標は必ず重複除去してから率を出す）。
- Qwen thinking 暴走＝max_tokens 不足でなく**曖昧プロンプト**が真因（[[llm-prompt-hygiene-not-budget]]）。※ Build 1 は LLM ゼロなので該当せず。
- **監視は低ノイズ**: 報告は4トリガーのみ（段完了/gate RED/裁定待ち/問われた時）。小 commit をダラダラ書かない（[[2der_monitoring_duty]]）。

---
*IMPL 自己引き継ぎ。役割合意済み・全 spec 読了・コード未着手。次はゲート表化＋AMB-REF-001＋298 dedup コーパスで測定。既存 HBB-30 非回帰が最優先。context 未配線を隠すな。commit=Taka。★3 本線は止めない。*
