# 全件調査 — UPPER_REVIEW は「聞いた判断」を次に活かしているか

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
Taka 指示（2026-08-22 17:1x）6項目 ／ **★件数削減は目的にしない**（Taka 逐語）
**★実装 0・コード変更 0行。**
測ったHEAD: twoder `96677bd` / dev-workcell `68c3b4c` / egl `ef9ab45`

**探索範囲（★先に固定）** = `twoder / dev-workcell / ds / rri / egl` の `*.py` **全件**
＋ front door `/api/tasks`（585）→ `/api/state?task_id=`（**585件 全件**）

**Taka の成功条件** =
> 「一度Claudeへ聞いた**意味のある判断**が、**その場限りで消えず**、**次回の判断コストを下げる循環**が存在すること」

---

## 0. 結論（先に）

```
★同一 task の中には 循環が ★在る（PRESENT・OBSERVED）
★task を跨ぐ循環は ★無い（ABSENT）
★『知識/規則/能力』へ昇格する経路は ★無い（ABSENT）

★分母つき: 保存されている判断 ★1,103件。
  そのうち 次回の判断コストを下げるのに使われるのは
  ★『同一 task の 直近1件』だけ（`generate_via_runner` 逐語「★直近の1件だけ見る」）。
```

---

## 1. ① 何を条件に呼ぶか ―― **3層ある**（PRESENT / OBSERVED）

```
第1層  dw/dispatch.py:35,36  _MAP
       "READY_FOR_UPPER_REVIEW" → ("UPPER_REVIEW", "CLAUDE_SENIOR", "TASK+RUNS+TEST_RESULT", ★False)
       "JUDGE_REQUIRED"         → 同上
       ★barrier が False ∴ :163 で止まらず ★機械 dispatch へ進む
       ★CLAUDE_SENIOR は _machine_registry に在る ∴ fn is not None

第2層  dw/dispatch.py:155-161  ★決定論の門（LLM 0）
       if op == "UPPER_REVIEW" and fn is not None:
           if URG.trivially_clean(task_id):
               URG.auto_pass_review(...)   → auto_served="TRIVIALLY_CLEAN_UPPER_REVIEW"
           # non-trivial -> fall through

第3層  twoder/webui.py:659-668  ★抑制器（★呼ばない判断）
       should_call_senior(last_review_ordinal, input_ordinals)
         1. last_review_ordinal is None      → call=True  "first_time"
         2. input_ordinals が空              → call=★False "no_input_record"
         3. max(input) > last_review         → call=True  "input_changed"
         4. どれでもない                      → call=★False "no_progress_since_last_review"
       ★呼ばない時は state を動かさない（逐語「★呼ばない=★state を 動かさない」）
```

**★①の答え**: 「状態が UPPER_REVIEW」だけでは呼ばない。**決定論の自動合格**と
**「前回のレビュー以降に新しい入力が無ければ呼ばない」**の2つの抑制が既に在る。

---

## 2. ② レビュー前に過去の同型判断を検索する経路 ―― **★ABSENT**

**探索範囲** = `twoder/senior_review.py` 全文 ＋ 上記 repo の `*.py` 全件。

```
senior_review.py の import = ★json / subprocess / twoder.latest_test_result  ★この3つだけ

build_prompt(task_id, view) が渡す値（★全欄）:
  task_id / state / last_test_passed / rework_count / completion_blockers /
  findings / record_test_passed / artifact_sha256 / artifact_head
  逐語「★渡す物は 記録に在る値だけ(★申告を混ぜない)。★返す形を1行で縛る。」
```

**∴ 渡るのは「その task の今の値」だけ。**
**他 task の過去レビューを引く呼び出しは ★0件**（分母＝上記 repo の `*.py` 全件）。
索引も類似検索も無い。

---

## 3. ③ レビュー結果が何処に保存されるか ―― **PRESENT（★新台帳0・既存の器）**

```
Claude 経路  senior_review.make_actor → W.record_upper_review(task_id, review, ts, "claude-senior")
             → DW events（phase="UPPER_REVIEW" / payload.review = {verdict, basis}）
             ★語が PASS/FAIL でなければ ★何も記録せず recorded=False（fail-closed → barrier のまま）

機械 経路    dw/upper_review_gate.auto_pass_review → ★同じ器に PASS ＋ 検査した invariants
```

### ★実測（front door 経由・分母 585 task 全件）

```
upper_review を持つ task = ★245 / 585
保存されている review    = ★1,103 件
  verdict 内訳 = FAIL ★940 / PASS 161 / PLACEHOLDER 1 / APPROVED 1
  basis が空でない = ★1,098 / 1,103
  basis の異なり数 = ★1,003  →  ★重複 95
    最頻の重複 ×91 = 「ITEM-2DER-EVO-0009 deterministic trivially-clean gate (no LLM); NOT authority ap…」
      ★これは ★機械の定型文（第2層の自動合格）＝ Claude の判断ではない
    残りの重複 = ★4件程度（例 ×3 / ×2）
```

**∴ 判断は消えていない。1,103件が器に残っている。**
**∴ 同じ文面を何度も聞いてはいない（重複のほとんどは機械の定型文）。**

---

## 4. ④ 保存結果を次回 誰が読むか ―― **PRESENT（5箇所）／★但し用途が偏る**

| 読み手 | 何を読むか | 用途 |
|---|---|---|
| `dw/workcell.py:198` | 全件 | view を組み立てる |
| `dw/workcell.py:215` | `payload.review` を `may_retry_after_senior_fail` へ | **★basis は「空か否か」だけ**見る（後述） |
| `dw/workcell.py:363` | 有無 | `UPPER_REVIEW_MISSING` blocker |
| `twoder/webui.py:661` | **`_ordinal` だけ** | 抑制器 `should_call_senior` の材料 |
| `twoder/manager_v0.py:148,156` | **`basis` を連結** | escalation の `detail` へ（★人へ上げる） |
| **`twoder/generate_via_runner.py:182`** | **`basis` の本文** | **★次の生成 prompt へ入れる** |

### ★`may_retry_after_senior_fail` は中身を読まない（逐語で確認）

```python
verdict.upper() != "FAIL" → skip
isinstance(basis, str) でなければ skip
basis.strip() が空なら skip           # ★★空かどうか だけ
meaningful_fail_count を数える
```
**∴ 「根拠が書かれているか」を数えるだけ。★何が書かれているかは読まない。**

---

## 5. ⑤ 同型判断を再利用する機構 ―― **同一 task 内は PRESENT／task 跨ぎは ★ABSENT**

### ★在るもの（同一 task 内）

```
(a) generate_via_runner.py:181-184  逐語
    「裁定 2026-08-07(3): ★直前の上級監査の指摘も次へ渡す(★新しい欄を作らない=同じ _prev に足す)」
    _ur = next((e for e in reversed(W._read_events(task_id)) if e.get("phase")=="UPPER_REVIEW"), None)
    _bs = ((_ur.payload or {}).get("review") or {}).get("basis") or ""
    if _bs.strip(): _prev += "\n上級監査の指摘: " + _bs.strip()
    ★★= Claude の判断が ★次の生成の材料になる ＝ ★『次回のコストを下げる循環』の実体

(b) should_call_senior（①第3層）
    ★入力が増えていなければ ★呼ばない ＝ ★同じ判断を買い直さない

(c) upper_review_gate.trivially_clean
    ★決定論で済む形は ★そもそも Claude を呼ばない
```

### ★無いもの（task を跨ぐ）

```
★他 task の過去レビューを引く経路          = 0（§2）
★類似・同型を判定する機構                  = 0（探索範囲の *.py 全件に similarity/索引の実体なし）
★『前にこう判断した』を prompt に入れる経路 = 0（build_prompt の全欄が その task の値・§2）
```

**★重要な限定（逐語）**: `generate_via_runner` は
「**★直近の1件だけ見る**」＝ **同一 task の中でも 過去の全レビューは使わない。**

**∴ 1,103件のうち 実際に次へ渡るのは「その task の最新1件」のみ。**

---

## 6. ⑥ Knowledge / Rule / Capability への昇格経路 ―― **★ABSENT**

**昇格先の器は 実在する。だが upper_review から供給されていない。**

```
候補1  twoder/function_table.register（能力の登記・authority を通す・append-only・revoke と対称）
       ★本番の呼び手 = ★0（探索範囲の *.py 全件。webui は view/index を読むだけ）
候補2  twoder/failure_memory の DEAD_APPROACH（★submit の門を実際に動かしている）
       ★upper_review から record する呼び出し = ★0
候補3  ESDE 正本の UNDERSTANDING（ESTABLISHED 判定）
       ★upper_review 結果を材料にする経路 = ★0
```

### ★manager_v0 が FAIL を集めた先（逐語）

```python
_sig = {"error": "senior review FAIL x%d; machine will not retry (...)", "detail": _basis}
_cls = {"failure_classification_id": "FCLS-" + tid[-8:] + "-" + str(len(_rvs)),
        "candidate_classes": [{"class": "FAILURE-UNKNOWN", "confidence": 0.0, ...}],
        "selected_class": "FAILURE-UNKNOWN"}
# ★★`FAILURE-UNKNOWN` = ★原因を 決めつけない(★escalation_router 逐語 "no_cause_fixation")。
#   ★私は 失敗の 種類を ★推測しません。
```

**∴ FAIL が 940件 積み上がっても、行き先は `FAILURE-UNKNOWN` の escalation（＝人）。
規則にも能力にも語彙にもならない。**
（★これは「原因を決めつけない」という**正しい規律**の帰結でもある ―― 欠陥と決めつけない。）

---

## 7. Taka の成功条件に対する判定

> 「一度Claudeへ聞いた意味のある判断が、その場限りで消えず、次回の判断コストを下げる循環が存在すること」

| 部分 | 判定 | 根拠 |
|---|---|---|
| 判断が保存される | **PRESENT** | 1,103件 / basis 非空 1,098 |
| その場限りで消えない | **PRESENT** | DW events に append-only で残る |
| **次回のコストを下げる循環** | **★部分的 PRESENT** | ★同一 task のみ（basis→再生成 ／ ordinal→呼ばない ／ 決定論門） |
| **task を跨ぐ循環** | **★ABSENT** | 過去レビューを引く経路 0 |
| **知識/規則/能力への昇格** | **★ABSENT** | 供給する呼び出し 0（器は3つとも実在） |

**★∴ 成功条件は「同一 task の中でだけ」成立している。**

**★分母で言うと**: 保存 1,103 → 次に渡るのは **各 task の最新1件のみ**。
`upper_review` を持つ task が 245 ∴ **再利用され得るのは最大 245件 / 1,103件（22%）**、
**残り 858件（78%）は 保存されているが 二度と読まれない。**
（★「読まれない」＝ §4 の読み手6箇所のうち、本文を次へ渡すのは
`generate_via_runner` の1つだけで、それが見るのは「直近の1件」だから。）

---

## 8. ESDE 宣言（正本§12）

```
AXIS: UPPER_REVIEW_KNOWLEDGE_CYCLE
SCOPE:
  entry:       2DER が Claude(senior) に判断を求める
  exit:        ★その判断が 次回の判断コストを下げる
  authority:   発行 0・変更 0（★調査のみ）
  persistence: 新規 0
  components:  dispatch._MAP / upper_review_gate / should_call_senior / senior_review /
               W.record_upper_review / workcell / may_retry_after_senior_fail /
               generate_via_runner / manager_v0 / escalation_router

EQUALITY   canonical: 判断の器 = DW events の phase="UPPER_REVIEW" / payload.review{verdict,basis}
           compatible:   [Claude 経路(claude-senior), 機械経路(trivially_clean auto_pass)]
                         ★同じ器・同じ欄に載る＝対等
           incompatible: []
           unknown:      [PLACEHOLDER 1 / APPROVED 1 ―― ★語彙外の verdict が2件在る]
           status: ★PRESENT（★但し unknown 2件は UNVERIFIED）

SYMMETRY   pairs: [書く↔読む, 呼ぶ↔呼ばない, 判断↔再利用, 蓄積↔昇格]
           required 4 / present ★2 / missing ★2
             ✔ 書く↔読む     record_upper_review ↔ 6箇所の読み手
             ✔ 呼ぶ↔呼ばない should_call_senior が両方を返す（理由つき）
             ✘ 判断↔再利用   ★task を跨ぐ再利用が 0
             ✘ 蓄積↔昇格     ★1,103件 蓄積 ↔ 昇格 0

LINKAGE    E1 状態→呼ぶ判断           OBSERVED（3層・§1）
           E2 呼ぶ→Claude 実行        OBSERVED（headless セッション実測済）
           E3 実行→保存              OBSERVED（1,103件）
           E4 保存→同一 task の次手   OBSERVED（generate_via_runner・★直近1件のみ）
           E5 保存→別 task の判断     ★ABSENT
           E6 保存→規則/能力への昇格   ★ABSENT
           declared 6 / observed 4 / absent 2

HIERARCHY  boundaries: [authority を増やさない, 原因を決めつけない, 判断は記録から作る]
           required 3 / passed 3 / violation 0
           ★`FAILURE-UNKNOWN` は 規律の遵守であって 欠陥ではない

R1_END_TO_END      OBSERVED（★但し exit=「次回のコストを下げる」は ★同一 task に限る）
R2_DENOMINATOR     保存 1,103 ／ 次へ渡り得る 最大 245（22%）／ ★二度と読まれない 858（78%）
R3_INTERNAL_GATES  gates [_MAP, trivially_clean, should_call_senior, PASS/FAIL 語の検査]
                   passed [] / failed [] / unverified ★4（★本調査では撃っていない）
R4_REJECTION       ★未列挙・未発火 ／ status: ★UNVERIFIED

UNDERSTANDING  candidate: UPPER_REVIEW_KNOWLEDGE_CYCLE
               requires: [保存, 同一 task の再利用, ★task 跨ぎの再利用, ★昇格経路]
               evidence: [前2つは OBSERVED]
               unresolved: [後2つが ABSENT]
               result: ★UNKNOWN（★ESTABLISHED にしない）

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD（★実装しない ―― 本件は調査指示）
```

---

## 9. ★件数削減を目的にしていない（Taka 逐語）

本書は **UPPER_REVIEW を減らす提案をしていない。**
測ったのは「**聞いた判断が次に効いているか**」だけ。
79件（`next_operation=UPPER_REVIEW`）の扱いは **別 AXIS**として据え置く。

## 10. 触っていないもの

`EVO-0084` の常駐起動（★ESTABLISHED 済・Taka 判断待ち）／`EVO-0085` writer 4欠損 ／
`EVO-0087` R4② 未発火 ／ ESDE 統合（EVO-0083）／ 正本§13 の UNVERIFIED 差戻し。
