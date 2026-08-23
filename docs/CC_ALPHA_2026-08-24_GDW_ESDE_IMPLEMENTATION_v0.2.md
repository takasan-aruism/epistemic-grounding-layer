# GDW-ESDE 実装指示 v0.2（★実測反映版）

**発: 監視（CC_ALPHA・3Claude の外部） ／ 宛: Taka ・ MGR ／ ✔ は付けていません**
**原案: Taka 提示の GPT案 v0.2（2026-08-24）／ 正本: `TAKA_2026-08-24_GDW_OPERATION_DESIGN_v0.1.md`（`ART-da5a15e434`）**
**★コードは1行も変えていない。★新しい Manager / Worker / 台帳 / ID / 経路 / state を1つも作っていない。**
測ったHEAD: twoder `e63fe92` / egl `8db638b` / rri `998c25b` / ds `79b9c2e` ／ 対応 item: `ITEM-2DER-EVO-0099`

---

## 0. この版で変わったこと（GPT案 → v0.2）

| # | 変更 | 実測の根拠 |
|---|---|---|
| 1 | **§0 の前提は既に満たされている** | `ESDE_EVALUATION` の SoR は **`ds/data/event_trace.jsonl`**（ETRACE の1 component）。**ESDE専用 JSONL は元々作っていない** |
| 2 | **明細へ載せる口を名指しした** | `record_evidence` は **`question_id` を要求する**＝TASK単位では載らない。**新規明細を立てるのは `raise_question`** |
| 3 | **既存語彙で表現できる範囲を確定** | `EVIDENCE_BASIS_KINDS` に `LOCAL_MEASUREMENT` / `LOCAL_CODE_OBSERVATION`、`EVIDENCE_VALIDATION_MODES` に `MEASURED` / `OBSERVED` / **`UNRESOLVED`** が既に在る |
| 4 | **provenance は追加不要** | `recorded_by` / `recorded_via` が `record_evidence` と `record_actor` に既に在る |
| 5 | **§8 の前提を訂正** | **`authority.py` に Domain の語は 0行**。「Workerが勝手に実行しない8種」は**機械の門としては存在しない**（＝人の規律） |
| 6 | **§9 は「無い」で確定** | **management domain 相当は既存語彙に無い**。追加前に設計として報告する（＝本書） |
| 7 | **§12 の既知実測を訂正** | GPT案の `hierarchy passed 2` は私の三面照合の値。**Worker の測り方では passed の定義が変わる**（§12） |
| 8 | **§14 の答えを全部入れた** | 下記 §1 |

---

## 1. 実装前チェック（GPT案 §14）の答え ―― ★全部 実測

```
①ESDE_EVALUATION の SoR      ★ds/data/event_trace.jsonl（ETRACE の component）
                              ★専用台帳は無い ∴「新ESDE専用台帳を作らない」は既に満たされている
②request_thread への接続      ★口は2つだけ
                                raise_question(thread_id, memo, ts, account_id)   … 明細を1件 立てる
                                record_evidence(thread_id, question_id, evidence_refs,
                                                basis_kind, validation_mode, ts,
                                                source_span, evidence_text, retrieved_at,
                                                recorded_by, recorded_via)        … 根拠を付ける
                              ★record_evidence は question_id を要求する
                              ＝★TASK単位では載らない。★必ず 明細1件を先に立てる
③evidence / refs / supersede / actor
                              evidence   ✔ basis_kind 9語 / validation_mode 6語
                              refs       ✔ QUESTION_TYPED の refs（kind + resolved 付き）
                              actor      ✔ recorded_by / recorded_via（ACTOR_VIAS = front_door / direct）
                              supersede  ✔ 明細側は typed_id の後勝ち projection が既に版管理
                                          （list_typed 逐語「同じ typed_id が2度在れば後の行が効く」）
                                          ＋ twoder/supersede_seal.py ほか5モジュール
④二重保存は必要か             ★不要。ETRACE が正本、明細は projection の入口
                              ★GPT案 §0「正本と表示projectionを混同しない」と一致
⑤Domain Manager が持つのは    ★状態（集約）。データ本体は TASK台帳
⑥UI は既存 projection で足りるか
                              ★足りる。webui._esde_for が scope 分離済で軸ごとに返す
                              ★TASK詳細に esde 欄が既に出ている（commit 894b305）
```

---

## 2. GPT案の各節に対する 実測の当て（★変更点のみ）

### §0 保存先の原則 ―― **前提は既に満たされている**
`ESDE_EVALUATION` は ETRACE に書かれており、**ESDE専用 JSONL は存在しません**。
∴「新しい ESDE 専用 JSONL を先に作らない」は**守る対象ではなく、既にそうなっている**。

**残る作業は「TASK明細から辿れる projection の成立」だけ**であり、その口は **既に在る**
（`/api/rthread?task_id=` の `esde` 欄）。**移送も削除も不要。**

### §5 明細の粒度 ―― **新しい kind を作らずに済む**
```
ESDE evaluation   → ETRACE(正本) ＋ 明細から refs で指す
ESDE finding      → raise_question で 明細1件（memo に finding_id と what）
                    ＋ record_evidence(basis_kind=LOCAL_MEASUREMENT,
                                       validation_mode=MEASURED,
                                       evidence_refs=[ETR-…])
ESDE required     → ★既存の QUESTION_TYPED の kind=SPEC/CONSTRAINT/GOAL が そのまま required
                    ＝★新しく作らない（v0.1 resolver 設計 §3）
UNVERIFIED        → validation_mode=UNRESOLVED（★既存語）
```
**★足りない語が1つだけ在る**：`ACTOR_ACTIONS` は `RAISE / ANNOTATE / PROPOSE_ACCOUNT / DISPOSE / STRUCTURE` の5語で、
**ESDE の測定に当たる語が無い**。`STRUCTURE` で代用するか1語足すかは**裁定が要る**（§4）。

### §8 authority ―― **★門は存在しない**
```
authority.py に Domain の語 = ★0行
現在の Manager/Worker 分離 = ★モジュール境界 と docstring の逐語 のみ
∴ GPT案の「Workerが勝手に実行しない8種」は ★人の規律であって 機械は止めない
```
**候補として挙がっている `READ / OBSERVE / MEASURE / CLASSIFY / RECORD_EVALUATION /
PROPOSE_FINDING / PROPOSE_HANDOFF` は、`authority.POLICY`(24件) に1つも無い。**
∴「既存authorityで表せるか」の答えは **表せない**。**7語を足すか、規律のまま行くかは裁定**（§4）。

### §9 Domain の語 ―― **★management domain 相当は無い**
```
既存 DOMAINS 16件 = ★開発領域（API / DATABASE / CONTAINER / DEPLOYMENT …）
GDW の Domain      = ★管理の単位（ESDE / Ledger / DW / Research）
★既存語彙に management domain 相当は 無い
```
**∴ GPT案の「無ければ追加前に設計として報告する」に該当する。本書がその報告。**

**★併せて記録**：`domain_dw.py` の `DOMAIN_OPERATIONS` / `DOMAIN_MODULES` は
`{"dw": …, "route_table": …}` で、**これは既に management domain の側**である。
つまり**2つの `Domain` が既に同居している**（今日5例目の「同じ語が別物を指す」）。

### §10 常駐 ―― **接続点は1行**
```python
# manager_v0.main() の巡回（INTERVAL=60）は 5段
record_stages() → receive_finished() → feedback_one() → submit_next_contract() → tick()
```
**`to_domain()` は汎用**（判定は `twoder/get_domain` という2DER製の純関数へ外出し済、
対応表は `DOMAIN_OPERATIONS` / `DOMAIN_MODULES` の2つだけ、`NO_DOMAIN` なら呼ばない）。
∴ **ESDE を足すのは表に1行ずつ。`to_domain` は1文字も触らない。**

---

## 3. 実装範囲（★新規実装が必要なのは 2点だけ）

```
★(A) ESDE Domain Manager 本体   twoder/domain_esde.py（★domain_dw.py と同形）
      責務= 未評価/再評価TASKの選別 ／ Worker へ task_id を渡す ／ 結果の扱いを決める
            ／ Domain summary を返す
      ★持つのは 状態だけ。TASK固有結果は TASK台帳が正本

★(B) ESDE Structure Worker      egl/structure/s_esde_evaluate.py に --task が既に在る
      ＝★実体はほぼ在る。★足りないのは「結果を明細へ戻す」1段
         raise_question + record_evidence を呼ぶだけ（★新しい口を作らない）

★接続するだけ= DOMAIN_OPERATIONS / DOMAIN_MODULES に1行 ／ 巡回に1行 ／ UI は既に出る
```

---

## 4. ★裁定が要る点（私は決めない・3件）

```
①『Domain』の語        ESDE を management domain として どこに登記するか
                        （既存 DOMAINS 16件は 開発領域で 粒度が違う）
②authority の門         「Workerが勝手に実行しない8種」を POLICY に足すか 規律のままか
                        ★足すなら 7語程度の追加 ／ 足さないなら 機械は止めない
③ACTOR_ACTIONS         ESDE の測定に当たる語が無い。STRUCTURE で代用するか 1語足すか
```

**②が特に効きます** ―― GPT案 §8 は「Workerが勝手に実行しない」を前提にしていますが、
**いまの 2DER には それを止める門が無い**。**規律のままなら、Worker が越えても機械は気づきません。**

---

## 5. 完了条件（GPT案 §13 に 実測を足したもの）

| # | 条件 | 現状 |
|---|---|---|
| 1 | 計器が scratchpad 依存でない | **★済**（`s_esde_evaluate.py` / `ART-1a882c44e2` / `--check` GREEN） |
| 2 | task_id だけで測れる | **★済**（`--task TASK-…`） |
| 3 | TASK固有結果が TASK台帳から辿れる | **未**（Worker が明細へ戻す1段が無い） |
| 4 | actor/provenance が残る | **口は在る**（`recorded_by` / `recorded_via`）／ 使っていない |
| 5 | 再評価履歴が残る | **★済**（ETRACE は追記型・明細は typed_id の後勝ち） |
| 6 | 現在有効版を projection できる | **★済**（`_esde_for` が軸ごとに最新を返す） |
| 7 | Domain Manager が自動発火を管理 | **未**（(A) が無い） |
| 8 | Worker 自身は修理しない | **★済**（finding は handoff 先を書くだけ） |
| 9 | General は summary のみ | **未**（Domain summary の口が無い） |
| 10 | UI で TASK明細→ESDE を辿れる | **★済**（`/api/rthread` の `esde` 欄） |
| 11 | 無関係な SYSTEM/REPO 評価を混ぜない | **★済**（scope 分離・commit `894b305`） |
| 12 | 新 ESDE 専用台帳を作らない | **★元々作っていない**（SoR は ETRACE） |
| 13 | 最低2TASK で人手なし実走 | **未** |

**★13件中 7件は既に満たしている。残るのは 3 / 7 / 9 / 13 の4件で、
そのうち 3 と 9 は「既存の口を呼ぶだけ」。**

---

## 6. 最初の実走（GPT案 §12）―― ★1点 訂正

GPT案が挙げた既知実測のうち **`hierarchy passed 2`** は、
私が**三面照合（required 14 を enforced と突き合わせた）** で出した値です。
**Worker の `--task` は required の分母だけを出し、enforced との照合は別段**なので、
**同じ数にはなりません。**（`s_esde_evaluate.axis_task` の逐語:
「enforced の照合は別段(この計器は分母を出す)」）

**∴ 再測定で数が違っても、それは計器の誤りではありません。**
比べるなら **relation set 66 / equality 7-5-2 / linkage observed 7 / blockers 2** の4つです。

---

## 7. していないこと

```
★実装 0行 ／ 新しい Manager / Worker / 台帳 / ID / 経路 / state 0
★DOMAINS への追加 0 ／ to_domain への追加 0 ／ authority への追加 0
★ACTOR_ACTIONS への追加 0 ／ 常駐への配線 0 ／ blocking 0
★GPT案の差し替え 0（重ねて 実測を当てただけ）
```
