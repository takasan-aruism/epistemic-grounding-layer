# declared — AXIS = `AUDIT_CHECK_IS_NOT_MECHANIZED` ／ 経験が次に効くまでを一周にする

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済（`2DER_DEVELOPER_DISCIPLINE_v1.0` / **ESDE 正本 v0.1**）
**★実装の前に置く1枚。★コードは1行も変えていない。★新台帳0・新Manager0。**
item: `ITEM-2DER-EVO-0083` ／ 測ったHEAD: twoder `96677bd` / dev-workcell `68c3b4c` / egl `380cb27`

**Taka 指示（2026-08-22 21:5x）逐語の要点**
```
常駐はまだ上げない。196件・81件を一斉に流す前に 本線 AUDIT_CHECK_IS_NOT_MECHANIZED を閉じる。
★目的は Claude 呼出回数を減らすことではない。
★一度発生した 問題・診断・対照・上級判断・解決 が 台帳へ残り、
  ★次の同型案件で 再利用されるところまでを ★2DER の一周として扱うこと。
★新しい Knowledge 台帳や Manager を作らない。
★既存の task/event/finding/review/progress/能力表 の どこまでで循環を表現できるかを 先に確定する。
★実装前ケース表を作る。
★TAKA_DECISION_PROVENANCE の穴は記録するが この本線と混ぜない。
```

**★遵守**: 本書は **Claude 呼出削減を目的にしていない**。測るのは**経験が次に効くか**だけ。
`TAKA_DECISION_PROVENANCE` は §8 に**参照だけ**置き、本線に混ぜない。

**探索範囲（★先に固定）** = `twoder / dev-workcell / ds / rri / egl` の `*.py` 全件
＋ front door 経由の `TASK-2DER-817D52EB` の**全記録41件**（`/api/etrace` `truncated:False`）

---

## 1. 標本 ―― `817D52EB` で実際に起きたこと（実測・時刻つき）

```
20:09  CREATED → PLAN 試行（planner が落ちる／別件で記録済）
20:34  PLAN 成立（2der-qwen-build-planner）
20:49:51  GENERATE   hand_to_worker  handoff_len=3121  sha=3c44df…
20:49:55  ★test failure  run_test {passed:false, failed_tests:["test_impl.py::test_basic_logic"]}
          run_minimal_slice {status:FAILED, artifact_len:2545}
20:51:13  ★AUDIT      → finding 1件
20:51:17  ★DISPOSE
20:51:26  ★UPPER_REVIEW → claude-senior / verdict=FAIL
20:53:34  ★REGENERATE hand_to_worker  handoff_len=★3547  sha=★5248c9…
20:53:47  ★再度 同じ test failure  failed_tests=["test_impl.py::test_basic_logic"]
20:53:49  AUDIT → 20:53:51 DISPOSE →（現在 JUDGE_REQUIRED）
```

---

## 2. ① 何が台帳に保存されたか ―― **41件。内訳を全件で数えた**

```
component  DW 13 / RUNGATE 9 / DISPATCH 9 / RUNNER 6 / WORKER 4
function   _append_event 13 / receive 9 / next_legal_operation 9 /
           hand_to_worker 2 / received_from_runner 4 / run_test 2 / run_minimal_slice 2

★41件の全 event に現れる欄を集めた（★これが「保存されている物」の全部）:
  added_lines / artifact_len / at / classification / exit / failed_tests / handoff_len /
  handoff_sha256 / immutable_tests_touched / key_note / operation / passed / phase /
  prompt_len / received_event_id / received_from / role / run_id / segment /
  skeleton_bytes_ok / skeleton_len / skeleton_missing / status / target_file / task_id /
  test_command / test_status / tests_len / workspace
```

**★保存されている（PRESENT）**
- **失敗の署名** = `failed_tests: ["test_impl.py::test_basic_logic"]`（`RUNNER.run_test`・**2回とも**）
- **上級判断の本文** = `payload.review.basis`（`claude-senior` / `FAIL`）
- 生成物の大きさ = `artifact_len` 2545 → 3548
- 渡した物の**指紋** = `handoff_sha256` / `handoff_len`

**★保存されていない（ABSENT）**
- **★handoff の本文**。残るのは `len` と `sha256` だけ。
  ∴ **「何を渡したか」は台帳から復元できない。**
- **★生成された code / test の本文**（`artifact_len` のみ）
- **★失敗の理由**（`failed_tests` は名前だけ。assert の内容は `stdout` にあるが event に無い）

---

## 3. ② 次の REGENERATE が何を読んだか ―― **source 逐語で確定**

`twoder/generate_via_runner.py:166-184`（**全文を読んだ**）:

```python
for _e in reversed(W._read_events(task_id) or []):          # ★task_id で閉じている
    if _e.get("phase") not in ("GENERATE", "REGENERATE"): continue
    _tr = (_e.get("payload") or {}).get("test_result") or {}
    if _tr.get("passed"): break                             # ★前回が通っていたら 1文字も足さない
    _ls = [l[:200] for l in (_tr.get("runner_stdout_tail") or _tr.get("stdout") or "").splitlines()
           if l.startswith("FAILED ") or l.strip().startswith("E ")][:15]   # ★15行まで
    if _ls: _prev = "\n### 前回 落ちた試験:\n" + "\n".join(_ls)
    break                                                    # ★★直近の1件だけ見る
_ur = next((e for e in reversed(W._read_events(task_id) or []) if e.get("phase") == "UPPER_REVIEW"), None)
_bs = (((_ur or {}).get("payload") or {}).get("review") or {}).get("basis") or ""
if _bs.strip(): _prev += "\n上級監査の指摘: " + _bs.strip()
```

**★読んだ物（全部）**
1. **直近1件**の GENERATE/REGENERATE の `test_result` から `FAILED `/`E ` 行を**最大15行**
2. **直近1件**の UPPER_REVIEW の `review.basis`

**★読まなかった物**
- 同じ task の**それ以前**の周（逐語「★直近の1件だけ見る」）
- **他 task の経験**（`W._read_events(task_id)` ＝ **task_id で閉じている**）
- finding / disposition / audit の内容

---

## 4. ③ Claude の FAIL 理由が次の生成条件へ渡ったか ―― **渡った（★但し中身は追えない）**

**★実測（指紋の差分）**
```
GENERATE   handoff_len 3121  sha 3c44df3fd9e0a101a2e113592e66e7343cbb79b70010a05da3d1b7c16ba2d5f3
REGENERATE handoff_len ★3547  sha ★5248c9480d868d49c236ccc9d773341fb62703bfff01642de901096eebb07d02
           差 = ★+426 バイト / ★sha が変わった
prompt_len 3521 → ★3947（★+426・同じ差）
```

**∴ 何かが足された。§3 の source と突き合わせると `_prev`（前回落ちた試験 ＋ 上級監査の指摘）以外に
足す箇所は無い ∴ ★渡ったと言える。**

**★但し限界を明記する ―― これは「渡ったこと」の証拠であって「何が渡ったか」の証拠ではない。**
handoff の本文が保存されていない（§2）ため、**426 バイトの中身は台帳から復元できない**。
∴ 状態語は **PRESENT（渡った）＋ UNVERIFIED（中身）**。

---

## 5. ④ 同型失敗で過去判断を検索する経路 ―― **★ABSENT**

### finding は「何が失敗したか」を持っていない（実測）

```
finding = {"task_id":"TASK-2DER-817D52EB", "finding_id":"TF-7D52EB",
           "category":"test_failure", "reproduced":null, "disposed":"REMAINS"}
★finding の欄 = category / disposed / finding_id / reproduced / task_id  ―― ★5つだけ
rounds = [{ordinal:4322, categories:{test_failure:1}, test_status:"failed"},
          {ordinal:4327, categories:{test_failure:1}, test_status:"failed"}]
```

**`finding_id = "TF-" + task_id の末尾6` ∴ ★task に紐づくだけ。失敗の中身を1文字も持たない。**
**∴ 同型を引く鍵が存在しない。**（`category` は `test_failure` の1語だけで、全ての試験失敗が同じ値）

### 検索の口も無い（既測・再掲）

```
front door 16口 / 引数18種のうち 結果を条件で絞れる物 = ★0
（`CC_MGR_2026-08-22_MEASURE_2DER_SELF_INVESTIGATION_CAPABILITY.md`・監査が独立に支持）
```

**∴ ④ = ABSENT。**過去の同型判断を引く経路は、鍵も口も無い。

---

## 6. ⑤ どの段で経験が捨てられているか ―― **★4箇所（全部 実測）**

```
捨てる段①  handoff の本文を保存しない（§2）
            → 「何を渡したか」が消える。★次に同じ物を渡したいとき 再現できない。
捨てる段②  finding が内容を持たない（§5）
            → 「何が失敗したか」が finding から消える。
              ★署名は event(RUNNER.run_test.failed_tests) に在るのに finding に写らない。
捨てる段③  読む範囲が task_id で閉じている（§3）
            → ★他 task の経験は 1文字も入らない。
捨てる段④  直近1件しか見ない（§3 逐語「★直近の1件だけ見る」）
            → ★同じ task の中でも 2周前の経験は捨てる。
              ★実測= 20:53 の REGENERATE は 20:49 の失敗だけを見た。
```

**★重要（設計に効く）**: 捨てているのは**材料ではない**。
**材料は `event` に在る**（`failed_tests` も `basis` も保存されている）。
**捨てているのは「それを次に引くための鍵」と「引く範囲」だけ。**

---

## 7. 既存構造で循環をどこまで表現できるか（★Taka の問い・新台帳を作らない）

| 既存構造 | いま持っている物 | 循環に足りるか |
|---|---|---|
| **event** | `failed_tests`（署名）／`review.basis`（判断）／`handoff_sha256`（指紋） | **★材料は足りる**（本文以外） |
| **finding** | `finding_id / category / disposed / reproduced / task_id` | **★鍵を置く場所は在る。値が無い** |
| **review** | `verdict` ＋ `basis`（本文） | **★判断は足りる** |
| **task** | `dw_state` / 遷移 | 足りる |
| **progress** | item 単位の note（MGR / 監査） | 人の面。機械の循環には使えない |
| **能力表 `function_table`** | `FN-sha1(name)` / register↔revoke / authority / front door に reader | **★「既知の失敗型」を登記する器として使える。★但し本番の呼び手 0** |

**★結論（実装しない・確定だけ）**
```
①循環に必要な材料は ★既存の event に全部 在る。
②足りないのは ★(a) 失敗の署名を finding に写すこと
              ★(b) その署名で引ける口
③新しい台帳は ★要らない。★finding と function_table が既に器を持っている。
★これは『表現できるか』の確定であって ★実装案ではない。
```

---

## 8. `TAKA_DECISION_PROVENANCE` の扱い（★Taka 指示どおり 混ぜない）

```
★記録だけする。★本線に混ぜない。★別 AXIS へ昇格させない。
実測（2026-08-22 21:2x・EVO-0084 に記帳済）:
  ・/api/approve は実在し client body からの詐称は塞がっている
  ・★但し Basic 認証の token を MGR が持つ ∴ ★MGR 自身が「Taka の承認」を鋳造できる
  ・★鋳造していない
  ・関連既知欠損: principal_of は 's=="taka"' のみ真 / taka-credential は UNKNOWN_PRINCIPAL / 本番呼び手 0
★本 AXIS は Taka authority を必要としない ∴ ★この穴で止めない。
```

---

## 9. ★実装前ケース表（Taka 指定の9件 ＋ 実測から足した2件）

**★設計の前に列挙する。★列挙を閉じる**（記憶「列挙が開くと試験を発明して自分の規則と矛盾する」）。

| # | ケース | 入力の形 | 期待する挙動（★まだ実装しない） |
|---|---|---|---|
| C1 | **初回失敗** | 署名 S、過去に S の記録 0件 | 過去を引かない。S を記録する |
| C2 | **同型失敗2回目** | 署名 S、過去に S が1件 | 過去の S を引ける |
| C3 | **Claude 判断あり** | 同型に `review.basis` が在る | その basis を引ける |
| C4 | **Claude 判断なし** | 同型は在るが review 0件 | 判断が無いことを「無い」と返す（★空欄にしない） |
| C5 | **過去に同型判断あり** | S 一致 かつ basis 在り | 引いた事実を記録に残す（★引いたことも証拠） |
| C6 | **過去判断と今回条件が不一致** | S は一致だが 前提が違う | ★流用しない。不一致を名指しする |
| C7 | **再生成で解消** | S が消える | S を「解消済」として閉じる（★消さない・追記） |
| C8 | **再生成しても同一失敗** | S が2回以上 続く | ★同じ手を繰り返さない。回数を出す |
| C9 | **反例発生** | 過去 PASS の S が今回 FAIL | ★過去判断を無効化せず ★両方を残して CONFLICT にする |
| **C10** | **署名が取れない** | `failed_tests` が空／`stdout` のみ | ★推測で署名を作らない。UNVERIFIED |
| **C11** | **同一 task 内の2周前** | 同じ task に S が3回 | ★「直近1件だけ」を超えるか否かを ★先に決める |

**★C10 と C11 は実測から足した** ―― C10 は `run_test` の欄が `failed_tests` だけの周が在り得るため、
C11 は §6 捨てる段④（直近1件だけ見る）が**同じ task 内でも経験を捨てている**ため。

---

## 10. ESDE 宣言（正本§12）

```
AXIS: EXPERIENCE_REUSE_CYCLE
SCOPE:
  entry:       ある task で 失敗と判断が起きる
  exit:        ★次の同型案件が その判断を引ける（★Claude 呼出の増減は exit にしない）
  authority:   発行 0・変更 0（★Taka authority を必要としない）
  persistence: ★新台帳 0（既存 event / finding / review / function_table のみ）
  components:  RUNNER.run_test / workcell.finding / senior_review / generate_via_runner /
               function_table / front door の 24面

EQUALITY   canonical: 失敗の署名（★いまは「無い」）
           compatible:   [event の failed_tests（署名の材料が在る）]
           incompatible: [finding（category 1語のみ・★全ての試験失敗が同じ値）]
           unknown:      [stdout の assert 本文（event に無い）]
           status: ★BROKEN（★材料は在るが 共通の鍵が無い）

SYMMETRY   pairs: [失敗を記録する↔引く, 判断を書く↔読む, 渡す↔渡した物を復元する]
           required 3 / present ★1 / missing ★2
             ✔ 判断を書く↔読む   record_upper_review ↔ generate_via_runner（★直近1件・同一 task 限り）
             ✘ 失敗を記録↔引く   ★引く鍵が無い（§5）
             ✘ 渡す↔復元         ★handoff 本文が無い（§2）

LINKAGE    E1 失敗→event 記録              OBSERVED（run_test 2回）
           E2 event→finding                OBSERVED（★但し署名は写らない）
           E3 finding→次の周               ★ABSENT（generate_via_runner は finding を読まない）
           E4 review→次の生成              ★OBSERVED（handoff +426B / sha 変化・§4）
           E5 経験→★別 task               ★ABSENT（task_id で閉じている）
           E6 経験→能力表への登記          ★ABSENT（function_table の本番呼び手 0）
           declared 6 / observed 3 / absent 3

HIERARCHY  boundaries: [新台帳を作らない, 判定を機械に書かせない, 台帳直読を使わない]
           required 3 / passed 3 / violation 0
           ★本調査は front door と source のみで行った

R1_END_TO_END      status: ★BROKEN ／ evidence: 同じ失敗が2回起きたが 1回目の経験は
                   ★直近1件として渡っただけ で ★引く鍵は作られなかった
R2_DENOMINATOR     event 41/41 走査 ／ finding の欄 5/5 ／ front door 24面
R3_INTERNAL_GATES  gates: [test_result.passed の分岐, basis 空の分岐, phase の絞り]
                   passed: [] / failed: [] / unverified: ★3（★本調査では撃っていない）
R4_REJECTION       ★未発火 ／ status: UNVERIFIED

UNDERSTANDING  candidate: EXPERIENCE_REUSE_CYCLE
               requires: [署名の鍵, 引く口, ケース表11件の網羅]
               evidence: [材料は event に在る（§7）]
               unresolved: [鍵と口が無い（§5）]
               result: ★UNKNOWN

CREATION   status: NOT_EVALUATED
DECISION   ★DESIGN_HOLD（★実装しない ―― 本件は調査＋ケース表の指示）
```

---

## 11. 触っていないもの

常駐（★上げていない）／194・196・81 の消化 ／ `EVO-0085` writer 4欠損 ／ `EVO-0087` R4② ／
`EXECUTABILITY_YIELD`（UNKNOWN のまま）／ `TAKA_DECISION_PROVENANCE`（§8 に記録のみ）。

**★新API 0・新Manager 0・新台帳 0・コード変更 0行。**
