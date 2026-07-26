# BUILD SPEC — Build 1: 前提曖昧ステージ（P1〜P4）

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- 宛: IMPL（coder） / 写: MGR / Taka
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / TYPE=BUILD_SPEC / v1.0
- 権限: Taka 承認「この枠で Build 1/2 を進めて」（MGR 経由）
- **統合元（すべて `BUILD_ROLE: 参照` に格下げ。読む必要はあるが作る源ではない）**:
  `CC_MGR_..._PREMISE_AMBIGUITY_STAGE_DESIGN_DRAFT`(叩き) / `CC_DESIGN_..._PREMISE_AMBIGUITY_AB_COMPARISON_FINDING`(**§3b 訂正含む**) / `CC_DESIGN_..._RECOGNITION_RESOLVER_ARCHITECTURE_v0_2`(v0.2.1) / `CC_DESIGN_..._AMBIGUITY_STAGE_BUILD1_HANDOFF` / `CC_DESIGN_..._BUILD1_CORRECTION_TO_IMPL_STATUS` / `CC_DESIGN_..._BUILD1_P1P4_ADDENDUM_HANDOFF`
- 本 SPEC は**自己完結**。統合元を追わなくても作れるように書いてある。

## 0. 表記規約（Taka 指示）
**【監査】**=私が一次情報で検証済（根拠併記）/ **【設計】**=私の提案・未測定 / **【伝聞】**=他者報告で私は未検証 / **【未確認】**=未決。
**【設計】を【監査】として引用しない。BUILT でも同じ規約を使うこと。**

## 1. 目的（何を作るのか・一行）
**接地していない前提のまま走り出すのを、機械で止める。** 認識固定（観測不能）は追わない。**入力が「在る」と仮定しているものが実際に接地するかを、決定論で確かめる。**

## 2. スライス（★まとめて出さない）
| スライス | 内容 | 状態 |
|---|---|---|
| **1a** | **P2 参照の前提**（指示語 ∧ 束縛先なし） | IMPL 実装中 |
| **1b** | **P3 文脈の前提**（context 空なら文脈依存解釈を除外） | 未着手・軽い |
| **1c** | **P4 存在の前提**（台帳照合）＋ 出口 `SUPERSEDE` | 未着手・本命 |
| — | **P1 出典の前提** | **【監査】既に LIVE。触らない**（非回帰確認のみ） |

**理由**: 本日、効果の帰属を3回誤った（DEFER 是正「+2件」は実は最大1件 / 役割分割 0.4603 は DESIGN の spec バグ込み / 「25.1% 過剰発火」は重複由来で実は 3.7%）。**同時に入れると、どれが効いたか永久に分からない。**
**1a と 1b は同時に出してよいが、指標は必ず分離して報告すること。**

## 3. 挿し込み位置（2種類ある・混ぜない）
- **P1 / P2 / P4 = front door の「手前ゲート」** — `rri/rri/preflight_gate.py`。意図調べより前。**走り出すのを止める。**
  - **【監査】** front door の 3d 段（ROUTING の直前）で LIVE。`twoder/submit.py:231` を実読して確認。
- **P3 = 意図調べ「内部」の候補合法性フィルタ** — 戦略候補から `CONTEXT_RESOLVE` を落とす。**入力は止めない。**

## 4. 段の一般化（既存 LIVE を壊さない — 最優先）
- 現行1ゲート（`RRI-GATE-AMBIGUOUS-QUANT-001`）を**ゲート表の1エントリに移す**。`detect()` は**登録順に全ゲートを回し、最初に triggered したものを返す**。**完全決定論（`:8005` 不使用・LLM ゼロ）。**
- **`submit.py` から見た契約（引数と戻り値のキー）を変えない**: `gate_id` / `claim_pattern_id` / `triggered` / `decision` / `blocks_dw_escalation` / `proposed_egl_status` / `signals` / `basis` を維持。
- **例外1点（IMPL の指摘を採用）**: `NEXT_LEGAL_OPERATION` は現状 quant 専用文が hardcode。referent/existence gate の聞き返しを返すため、**3d 段で `pg` 由来の文面を使う最小1点の変更を認める。** 条件: **diff を BUILT に貼る / 既存 quant ケースの文面が従来どおりであること / 文面は `clarification_slots` から構成し捏造しない。**
- **★受入の最優先事項 = 既存 HBB-30 ゲートの非回帰**（`twoder/regression/test_preflight_gate.py` GREEN）。**新機能より既存を壊さないことが上。**

## 5. パターン DB の様式（`rri/rri/ambiguity_patterns.jsonl` 新設）
input-clarity のスキーマを移植（**データは移植しない**・§6）。1行1ゲート:
`pattern_id` / `ambiguity_type`(REFERENT/PREMISE/CONTEXT/SOURCE) / `description` / **`clarification_slots`**（★聞き返し文をここから構成し捏造しない） / `possible_readings` / `false_positive_notes` / `decision` / **`observed_count` / `accepted_warning_count` / `ignored_warning_count` / `suppressed`**（無視され続けた警告を自動抑制＝過剰聞き返しの構造的対処。**最初から有効化**）

## 6. ★(A) input-clarity の34パターンは流用しない — 理由を取り違えないこと
- **【監査・訂正済】不採用の理由は「過剰発火するから」では“ない”。** 私が当初報告した「実478発話で25.1%過剰」は**重複35%による水増しで誤り**。**ユニーク298件では 3.7%** であり過剰ではない。
- **【監査】唯一の不採用理由 = 我々の失敗を 0/3 で全く捕まえないこと**（`あれ/それ/例のやつ` が34パターンに含まれない）。
- ＝**「危険だから外す」ではなく「今日の問題を解かないから足りない」。BUILT に 25% と書かないこと。**

## 7. 検出規則（★表層一致だけで撃たない）
**我々の失敗は「指示語がある」ことではなく「指す先が無い」こと。**

**【監査】実測**（ユニーク298件 / 我々の3件）:

| 規則 | 誤発火 | 捕捉 |
|---|---|---|
| (A)34パターン表層一致 | 3.7% (11/298) | **0/3** |
| 指示語の表層一致のみ | 2.0% (6/298) | 3/3 |
| **文頭の裸の指示語（あれ/それ/例のやつ + 読点/空白）** | **0.0% (0/298)** | **3/3** |

表層で当たった6件は `前の件を優先して進めて` 等＝**文脈から指す先を解決できる可能性が高い**。**表層だけで撃つと、解決できるものまで止める。**

### P2（1a）の発火条件
`指示語の表層` **AND** `束縛先が無い`。後半の判定:
1. `context` 引数を新設（既定 `None`）。
2. `context` が空/None → 束縛先なし。
3. `context` があっても指示語を束縛しうる名詞句が無ければ束縛先なし。**判定規則は事前固定・記録。凝った照応解析はしない（thin）。**
4. **同一発話内で自己解決している場合は撃たない。**`この設計案の得失は？`（BV3）で非発火を必ず確認。

### ★既知の落とし穴（BUILT に必ず明記）
- **【監査】`submit.py` は現在 `preflight_gate.detect()` に文脈を渡していない。** 引数を足しても、**呼び出し側が渡さない限り常に「束縛先なし」判定**になる。
- ＝**fixture 試験（context 明示）と実 front door（context 未配線）で挙動が変わる。**
- **「front door からの context 配線は未実装」と BUILT に書くこと。「動いた」と書かない。** 配線は Build 2。

## 8. P3（1b）— 文脈の前提
- **規則**: `context` が空（None / 空文字 / 空白のみ）なら **`CONTEXT_RESOLVE` を候補集合から決定論で除外**。
  - 根拠: 定義が「**直前の文脈に**支配的な解釈があり文脈で絞れる」＝文脈が無いなら**定義上あり得ない**。
- **LLM を一切呼ばない。** 除外は集計側。**除外したこと・理由・除外前の候補集合を記録**（隠さない）。
- **測る**: **【監査】DE-0548 で IP1 seed1 / IP2 seed0 が `CONTEXT_RESOLVE` を選んでいた。これが消えるか。** 消えた後どこへ行くかも報告。
- **★注意【設計】**: これは**正答を増やすとは限らない**（あり得ない選択肢を消すだけ）。**増えなければ増えなかったと書く。**

## 9. P4（1c）— 存在の前提（本命）
「以前作った X」「先週決めた Y」「その6倍の導出」。**LLM に疑わせず、機械が台帳に当たる。**

### (a) 3状態。`UNKNOWN` を `NOT_FOUND` に潰さない
| 状態 | 意味 | 出口 |
|---|---|---|
| `GROUNDED` | 接地した（**証拠つき**: 台帳ID/ファイルパス/行） | 通す |
| `NOT_FOUND` | **探した上で無い**（探索条件を記録） | `CLARIFY_FIRST` or `SUPERSEDE` |
| **`UNKNOWN`** | 探索が決着しない | **`UNKNOWN` のまま返す。「無い」と言わない** |

**「存在しない」と誤って言うことは、答えないことより有害。迷ったら `UNKNOWN`。**

### (b) 探索を固定・記録・反証可能に
- 探索対象を**script 内の定数で明示固定**（"全部を探す" にしない）: `DESIGN_EVIDENCE_LEDGER.jsonl`(observation/decision) / `structure/FILE_MANIFEST.jsonl` / `docs/*.md`。
- 返り値に**実行した検索を含める**: `{"state":"NOT_FOUND","queries":[...],"searched":[...],"hits":0}`。
- ＝**EGL の「根拠なき claim を認めない」を、我々自身の判定に適用する。**

### (c) `NOT_FOUND` を簡単に出させない（名前のゆらぎ対策）
- **異なる表記の照会を最低3通り試し、全て 0 hit の時のみ `NOT_FOUND`。1つでも部分一致があれば `UNKNOWN`。**
- **綴り一致で auto-collapse しない。**

### (d) ★射程は「記録の規律」に等しい（BUILT に必ず明記）
- **【監査】** HBB-30 で「導出は存在しない」と言えたのは、**台帳が『約6倍は DECLARED/UNVERIFIED prior』と明示記録していたから**（DE-0106 を実読）。
- **記録の無い対象は `UNKNOWN` にしかならない。**「台帳照合で存在確認ができる」と一般化して書かない。

### (e) 出口 `SUPERSEDE` を追加
- 「主張は DECLARED/UNVERIFIED のまま**保持**。**掘りに行かない**。後続実測が上書きする経路を開く」。**否定でも盲信でもない第三の道。**
- **既存5決定（`ALLOW`/`ALLOW_WITH_WARNING`/`CLARIFY_FIRST`/`HOLD_AS_WEAK_CLAIM`/`STRONGLY_DISCOURAGE_DW`）の挙動は不変。**

## 10. 測定（★数値を出す前に必ず dedup）
- **回帰セットの正典 = ユニーク298件**: `ds/ds_events.jsonl` の `record_type=UTTERANCE` ∧ `speaker=USER` → **`開発エビデンスを登録` で始まる機械生成19件を除外** → **dedup**（元 478 には重複35%）。
- **1a**: IP1/IP2/IP3 の捕捉 / BV3 非発火 / 誤発火率 / 既存 HBB-30 非回帰。
- **1b**: IP1 seed1・IP2 seed0 の `CONTEXT_RESOLVE` が消えるか / 消えた後どこへ行くか / 全体一致の増減。
- **1c**: PP1「以前作った Watcher 仕様ってどこ？」PP2「先週決めた方針のメモある？」PP3「君が言ってた予備の鍵はどこ？」で発火 / **D1・D2・D3 で非発火** / **HBB-30 の入力を `hbb_candidates.json` を検索対象に含めた場合と除いた場合の両方**（★**除いた時が本番**。含めれば当たるのは当然）。

## 11. 受入
1. `--check` GREEN（決定論再現／パターン DB のスキーマ検証／抑制カウンタの適用が決定論）。
2. **既存 HBB-30 ゲートの非回帰を実証**（最優先）。
3. **スライスごとに指標を分離**して報告。
4. **§7 の context 未配線**、**§9(d) の射程限界**を BUILT に明記。
5. 数値は**すべて dedup 済みか明記**。
6. **効かなければ効かないと書く。** P3 は正答を増やさない可能性、P4 は `UNKNOWN` だらけになる可能性がある。**それでよい。**
7. cross-repo: `rri` を触るので **rri 単体で commit + push**。
8. commit=Taka。DE は front door `record_de` + `generated_by_principal`/`claiming_principal`=`CLAUDE_CODE`・`generation_mode`=`DIRECT`。

## 12. 明示的に作らないもの
- **LLM に曖昧かどうかを判断させる**（**【監査】model は空白を埋める側に倒れる＝3度の目撃**）。
- **LLM に別 frame を生成させる / 比較させる**（v0.2 §9）。
- **(A) の34パターンの流用**（§6）。
- **証拠のないパターンの追加**。増やしたい候補があれば**提案のみ**して DESIGN→Taka の承認を待つ。

---
*BUILD SPEC v1.0（★実装源）。IMPL はこの1本だけから作る。統合元は全て参照。表記規約【監査】/【設計】/【伝聞】を BUILT でも使うこと。*
