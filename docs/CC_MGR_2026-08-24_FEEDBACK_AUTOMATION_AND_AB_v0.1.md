# 循環の自動化と、事実blockの効果測定 v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**裁定（逐語・要点）: 1.feed_back の自動callerを全件調査し既存の完了通知経路に最小接続（決め打ちしない）
2.新state/新event type/新IDは増やさない 3.同一run/resultで二重記帳しない 4.ED65242E 1件で手呼びなしに一周
5.事実blockが出力へ影響したかを対照で測る 6.「promptに届いた」だけでは効果成立としない**

---

## 0. ① 自動caller の全件調査（★決め打ちしていない）

| 候補 | 実測 | 採否 |
|---|---|---|
| `manager_v0.receive_finished` → `domain_dw` | **`status == "PASSED"` かつ `_queue()` の中だけ**を処理する | ★不採用。**失敗した走行では一度も発火しない**（失敗の証拠こそ台帳に要る） |
| `domain_dw.record_stages` | `DONE_INDEX`（受領済み＝PASSED）から作る | ★不採用。同じ理由 |
| `manager_v0.tick` の `/api/run_until_barrier` 直後 | 合否を問わない。**ただしその周に走った時だけ** | ★不採用。ED65242E は `claude_barrier: true` ∴ **機械は走らせられない＝永久に発火しない** |
| **`manager_v0.tick` の状態取得直後** | その task を**見た時**に発火。既に在る走行の結果も拾える | ★**採用** |

常駐の稼働状況も確認した: `twoder-manager.service`（＝`python3 -m twoder.manager_v0`）は **active**、
`twoder-manager-v0.service` は **inactive**。∴ **動いているループの中**に置いた。

### 0.1 置いた位置の理由

`_machine_turn` の門より**前**に置いた。門の後ろに置くと、ED65242E のように
Claude の関門で止まっている task では永久に発火しないため。
封印試験 `test_the_hook_runs_before_the_machine_turn_gate` で位置を固定した。

---

## 1. ②③ 新しい語を作らず、冪等

- **新 state 0 / 新 event type 0 / 新 ID 体系 0**。段4 の `record_evidence` をそのまま呼ぶ
- **冪等（実測）**: 3回呼んで `evidence_id` は 3回とも `QE-f764b760`、根拠の件数は **4件→4件（増えていない）**
- 根拠は `_mint("QE", thread_id, question_id, basis_kind, refs)` で、**`ts` を鍵にしていない**
  ∴ 時刻が変わっても id は変わらない。封印試験 `test_evidence_id_does_not_depend_on_the_timestamp` で固定
- 引けなければ黙って進む（巡回を止めない）。`_use` で呼び、**呼んだ事が両側に残る**

---

## 2. ④ 自動発火は観測できた／ただし ED65242E では「書くもの」が無い

**★常駐が手呼びなしに発火した記録（ETRACE）:**

```
ETR-NORUN-0003  {"action": "FEEDBACK", "task_id": "TASK-2DER-731F98A0",
                 "reason": "この task に 明細の thread が 無い(★推測で 作らない)",
                 "evidence_id": null, "evidence_refs": [], "summary": null}
```

**配線は動いている。** ただし**新しい根拠は書かれていない**。理由は2つとも構造的なもの:

| task | なぜ書かないか |
|---|---|
| `TASK-2DER-731F98A0`（並びの先頭） | **明細の thread が無い**（推測で作らない＝正しい挙動） |
| `TASK-2DER-ED65242E` | **`claude_barrier: true` ∴ 新しい走行が起きない**。最後の走行 `ETR-44dcd91f1c71-0009` は既に記帳済み ∴ 冪等で no-op |

∴ **「自動で発火する」は実証できたが、「自動で新しい根拠が書かれる」は本セッションでは観測できていない。**
書き込み自体は手呼びで実証済み（`QE-f764b760`）だが、**自動経路での書き込みは UNVERIFIED** とする。

### 2.1 未着手として残す

「thread があり、かつ未記帳の走行を持つ task」を全件探索したが、
`etrace_view` が 782MB の走行台帳を task ごとに走査するため **15分で完了しなかった**（timeout）。
∴ **母数を出していない**。③の拡大に入る前に、この探索を軽い読み口で作り直す必要がある。

---

## 3. ⑤⑥ 事実blockの効果 — ★UNVERIFIED

### 3.1 対照（同一 task / `temperature=0` / seed 固定・prompt だけ違う）

```
prompt A(facts なし)=4,412バイト   B(facts あり)=5,053バイト   差=+641

seed  arm            parsed  unresolved_assumptions  already_satisfied  test_plan  steps
0     A_no_facts     True    0                       0                  6          6
0     B_with_facts   True    0                       0                  6          7
1     A_no_facts     True    0                       0                  6          6
1     B_with_facts   True    0                       0                  6          7
2     A_no_facts     True    0                       0                  8          8
2     B_with_facts   True    0                       0                  6          6
```

**意図した効果は出ていない**: 事実blockは「既に確かめられたもの」を渡しているのに、
`already_satisfied` は **6走行すべてで 0件**。

### 3.2 ★null control が決定的だった（同じ prompt・同じ seed を5回）

```
i=0  steps=6  test_plan=6  ua=1  cc=5
i=1  steps=8  test_plan=8  ua=0  cc=6
i=2  steps=7  test_plan=6  ua=3  cc=4
i=3  steps=5  test_plan=6  ua=0  cc=4
i=4  steps=7  test_plan=6  ua=0  cc=4

★test_plan の中身の一致率: i=0 を基準に  1.00 / 0.00 / 0.00 / 0.00 / 0.00
```

**`temperature=0` かつ seed 固定でも、同じ prompt が毎回ちがう出力を返す**
（vLLM の連続バッチングで生成が再現しない）。

`steps` は同一 prompt でも **5〜8** に散る。観測した群間差（A=[6,6,8] / B=[7,7,6]）は
**この散らばりの中に完全に収まっている。**

∴ **★効果は UNVERIFIED。** 出力は違うが、**その違いを事実blockに帰属できない。**
裁定⑥の逐語どおり、**「promptに届いた」ことをもって効果成立とはしない。**

### 3.3 内容の目視（1組だけ・参考）

両群とも**依頼文に無い試験を発明していた**:

```
A だけ: "Robustness Test: Missing config file does not crash the system"
        "Robustness Test: Malformed JSON/types passed to vote are caught gracefully"
B だけ: "Test missing keys in vote dict raises KeyError."
        "Test malformed input (non-dict vote) raises TypeError or KeyError."
```

∴ **「不要な発明が減ったか」は、減っていない（どちらも発明している）。**
ただしこれは1組の目視であり、上の再現性の無さゆえ**これも UNVERIFIED**。

### 3.4 効果を測るには何が要るか（★次の設計）

1. **生成の再現性を確保する**か、**十分な N で分布を比べる**。今の n=3 では不可能
2. **「発明」の決定論的な計器**が要る。いまは目視。
   例: `test_plan` の各項が依頼文の TEST 明細に対応づくか（段2 の `match_questions` と同型）
3. 事実blockが `already_satisfied` に届かない原因の切り分け。
   **仮説（未検証）**: 事実blockは「再取得するな」と言っているが、
   `already_satisfied` 欄の説明文（"items that are ALREADY AVAILABLE"）と結び付いていない

---

## 4. 触っていないもの

- `dev-workcell` 全体 ／ `webui.py` ／ `domain_dw.py`（**読んだだけ**）
- `_observation_facts` / `validate_plan` / `dispatch_provenance`
- ED65242E 以外の task への書き込み（**0件**）
- `EVENT_TYPES` / `DISPOSALS` / `STATES` / `TRANSITIONS`

## 5. ★③へ進む前に片付けるもの

裁定⑦は「ここまで通ってから③へ進む」である。**まだ通っていないのは2つ**:

1. **自動経路での書き込みが未観測**（§2）。「thread があり未記帳の走行を持つ task」を
   軽い読み口で探し直し、1件で自動書き込みを実証する必要がある
2. **事実blockの効果が UNVERIFIED**（§3）。再現性のある計器を作るか、
   効果が測れないなら**その旨を残したまま**進むかを決める必要がある

## 6. 試験

`twoder` 87本（1 skip）＋ `rri` 70本 ＝ **157本 全通過**（新規7本）。
