# BUILD SPEC — Build 10R: **webui を再起動して修理が効いていることを確認する（ここで止まる）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.7）**
- 権限: `CC_MGR_2026-07-27_RESTART_WEBUI_AND_REDO.md`（**Taka 直接発話「webui 再起動して受入やり直して」**）

---

## 0. ★着手前に見つけた3点（MGR の手順をそのまま実行できない）【監査:CC-α】

### 0-1. 再起動で効くのは Build 10 の修理だけではない — **8 commit がまとめて効く**
```
再現: cd /home/takasan/twoder && git log --since="2026-07-23 08:07" --oneline --name-only
88bfa31  webui: /api/run_next の応答に planner_outcome を載せる        ← Build 10 の修理
a68f0f3  ★Build 6/7: submit に段3e を配線 + 3d の応答生成に anchoring    submit.py / live_worker_runtime.py / runtime_supervisor.py
7b62d80  submit: preceding_utterance_ref と ts_source を渡す(retention 補修)
612b45e  submit: NEXT_LEGAL_OPERATION を preflight gate 由来に
6c760e7  submit: optional ts pass-through
38d1988  ★star3(B): ledger-backed token gate + wire 6 paths            approval_registry / gate4 / operator.py / live_worker_runtime.py 他
6686593  probe: conformance_probe
c1ffef5  seam: pkg_mirror
```
**∴ 動いている webui は、段3e（意図戦略）も retention 補修も token gate 配線も持っていない。**

**★裏取りが取れている**: **Build 9C の段1 応答に `INTENT_STRATEGY` が無かった**（IMPL 報告 §2）。**一方 Build 9B（CLI＝新しいプロセス）には有った。**
**∴ 「webui が古い」は、`planner_outcome` の欠落とは独立に、もう1つの証拠で裏づけられている。**

**★リスク**: `38d1988` は **token gate を6経路に配線**している。**再起動後、`/api/run_next` が token を要求して拒否する可能性がある。**
**その場合は「再起動で壊れた」のではなく「新しいコードの仕様」である。** **迂回しないこと。止めて上げること。**

### 0-2. ★同じ依頼文で PLAN を観測し直すことは、原理的にできない
- `TASK-2DER-D6A93450` は **`READY_FOR_IMPLEMENTATION` / `has_plan: True`** になった（Build 10 §3）。
- task id は **`sha1(raw_input)[:8]`**（`submit.py:405`）＝**依頼文が同じなら同じ task**。
- **∴ 同じ依頼文を投げても、`CREATED` の task は二度と現れない。** **PLAN 段は通らない。**

> **∴ MGR §2「9C と 10 の食い違いが新プロセスでどちらに一致するか」は、同じ入力では再検証できない。**
> **これは冪等な task 採番の帰結であり、欠陥ではない。** **ただし「実験の再実行ができない」という性質である。記録しておく。**

### 0-3. ★次の `run_next` は planner ではなく **worker を動かす**
```
dev-workcell/dw/dispatch.py:30
  "READY_FOR_IMPLEMENTATION": ("GENERATE", "CODING_WORKER", "IMPLEMENTATION_PACKET", False)
                                                                        ↑ claude_barrier = False
```
**∴ この task に `run_next` を打つと、Qwen の CODING_WORKER が起動し、sandbox でコードを生成する。**
**∴ MGR 手順4 をそのまま実行すると、「1段だけ」のつもりが worker の実行になる。**
**∴ 本 SPEC ではやらない。** **§3 で MGR に裁定を仰ぐ。**

---

## 1. やること（再起動と確認まで。ここで止まる）

| # | 手順 | 記録すること |
|---|---|---|
| **1** | **再起動前の状態を採る** | 旧 pid / 旧起動時刻（`ps -eo pid,lstart,etime,cmd`）／`twoder/webui.py` と `dev-workcell/dw/dispatch.py` の mtime |
| **2** | **停止 → 起動**。**既存の起動手順を使う**（`python3 -m twoder.webui 8770`。**新しい起動方法を作らない**） | **停止時刻・起動時刻・新 pid・使ったコマンドそのもの** |
| **3** | **新プロセスが修理を持つことを確認（2つの独立した証拠で）** | ① 新起動時刻 > ソース mtime<br>② **`/api/run_next` の応答に `planner_outcome` キーが在ること**（`None` でよい。**キーの有無が判定**）<br>③ **`/api/submit` の応答に `INTENT_STRATEGY` が在ること**（段3e が入った証拠・§0-1） |
| **4** | **止まる。** BUILT を出す | — |

### 1-1. 手順3 の②をどう確かめるか（★worker を動かさずに）
**`TASK-2DER-D6A93450` に `run_next` を打ってはならない**（§0-3・worker が動く）。
**代わりに、既に `CREATED` でない／存在しない task id を渡して拒否応答を得る:**
```
POST /api/run_next  body: {"task_id": "TASK-2DER-D6A93450"}   ← ★打たない
POST /api/run_next  body: {"task_id": "TASK-DOES-NOT-EXIST"}  ← ★これを使う
```
- **run-gate が `tid != gate["task_id"]` で `refused` を返す。** **`dispatched` は false、状態変更は無い**（`webui.py:571` 逐語: *"No dispatch, no state change."*）。
- **★その拒否応答に `planner_outcome` キーが在るかを見る。**
- **【未確認】** **拒否は `run-gate` の early return なので、S3 の行に到達しない可能性がある。** **その場合はキーが出ない。**
  **→ キーが出なかったら、それだけで「修理が入っていない」と結論しないこと。** **①と③で判定し、②は「判定できず」と書く。**

### 1-2. 手順3 の③（`INTENT_STRATEGY` の確認）
**`/api/submit` に同じ依頼文を1回投げ、応答に `INTENT_STRATEGY` が在るかを見る。**
- **task は既に `READY_FOR_IMPLEMENTATION` なので、`submit` は task を作り直さない**（冪等）。**進みもしない**（`submit` はループを進めない）。
- **∴ 安全である。**
- **依頼文は Build 9B/9C/10 と同一。1文字も変えない。**

---

## 2. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| 再起動そのもの | **成功する**（既存の起動コマンド） |
| ③ `INTENT_STRATEGY` の出現 | **★出る**（段3e が入るため。**これが「新しいコードが動いている」の主証拠**） |
| ② 拒否応答の `planner_outcome` キー | **★出ない方に賭ける**（run-gate の early return は S3 の行を通らないと読んだ） |
| token gate による拒否 | **起きない**（`/api/submit` と `refused` 応答は認可を要しないと読んだ）**【未確認】** |
| 状況表の「実行中プロセス」行 | **次ターンで「ソースより新しい起動」に変わる** |

**★外れたら「外れた」と書く。**

---

## 3. ★MGR への裁定要求（本 SPEC の範囲外・着手しない）
**`planner_outcome` が実際に理由を運ぶかは、PLAN が失敗しないと分からない。** **そして:**
1. **同じ依頼文では PLAN 段に戻れない**（§0-2）。
2. **この task を進めると worker が動く**（§0-3）。

**∴ 選択肢は3つある。私は (c) を推す。**
| | 案 | 評価 |
|---|---|---|
| (a) | 別の依頼文で新しい task を作り、PLAN を観測し直す | **可能。ただし「同じ入力の再検証」にはならない。** 依頼文が変われば planner の難易度も変わる |
| (b) | この task を進めて worker を動かす（＝ 成果物が出る） | **本 build の範囲を大きく超える。** ただし**優先度1（台帳を読む部品を 2DER に作らせる）の本線でもある。** **別 SPEC が要る** |
| **(c)** | **再起動と確認だけで止め、`planner_outcome` の実証は「次に PLAN が失敗したとき」に持ち越す** | **修理は入っている（①③で確認できる）。** **失敗を人工的に作らない。** **待てばいずれ出る** |

**【設計:CC-α】(c) を推す理由**: **失敗を再現するために入力を変えると、何が原因で失敗したのか分からなくなる。** **修理は「次に失敗したとき見える」ためのものであり、いま失敗を作る必要はない。**
**(b) は独立に価値があるが、それは Build 10 の受入ではない。** **混ぜない。**

---

## 4. やってはいけないこと
1. **`TASK-2DER-D6A93450` に `run_next` を打たない**（worker が動く）。
2. **`run_until_barrier` を使わない。**
3. **run-gate / token gate を回避しない。** **拒否されたら記録して止める。**
4. **依頼文を変えない。**
5. **本番コードを変更しない**（本件は再起動と観測のみ）。
6. **新しい起動方法を作らない。**
7. **トークンを文書・ログ・argv に出さない。**
8. **「作れるようになった」「良くなった」と書かない。**

---

## 5. 受入
1. **手順1〜3 の記録**（旧 pid / 旧起動時刻 / mtime / 停止時刻 / 起動時刻 / 新 pid / **使ったコマンドそのもの**）。
2. **①②③ の結果を個別に書く。** **②が判定できなければ「判定できず」と書く**（§1-1）。
3. §2 の予想と実際の表。**外れに「外れた」と書く。**
4. **★再起動した事実と時刻を明記する**（Taka の実サービスを止めたため）。
5. **`run_next` を `TASK-2DER-D6A93450` に打っていないことを明記する。**
6. **次のどちらかに丸を付ける（5回連続で欠落している項目）:**
   - [ ] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
   - [ ] **(B) 〇〇（経路名）を経て設計/監査へ届いた。**
7. **`twoder/ledger_query.py` を削除したか**（3回連続で記載が無い）。**未実施なら実施。実施済なら「実施済」と書く。**
8. 観測を書き、判定・評価・提案をしない。**commit しない。** BUILT 冒頭に「運用方針 確認済（版: v1.7）」と受領文書一覧。
9. **v1.5**: 「動く」と書くときは実行した再現コマンドと結果を併記する。

---

## 6. 位置づけ（緩めない）
- **再起動が成功しても「修理が効いた」と書かない。** **効くかどうかは、次に PLAN が失敗したときにしか分からない。**
- **8 commit がまとめて効く。** **∴ 再起動後に何かが変わっても、Build 10 の修理が原因とは限らない。** **切り分けが必要になる。**

---
*BUILD SPEC v1.0（★実装源）。Build 10R=webui を再起動し、修理が入っていることを確認して止まる。★着手前の発見3点: (1) 再起動で効くのは Build 10 だけでなく 8 commit——動いている webui は段3e も retention 補修も token gate 配線も持たない。裏取り=Build 9C の応答に `INTENT_STRATEGY` が無く、CLI の 9B には有った（`planner_outcome` の欠落とは独立の第2証拠）。`38d1988` の token gate 配線で run_next が拒否される可能性を先出し（迂回せず止める）。(2) ★同じ依頼文で PLAN を再観測することは原理的に不可能——task id は `sha1(raw_input)` で冪等、当該 task は既に `READY_FOR_IMPLEMENTATION`。∴ MGR §2 の再検証は同一入力ではできない（冪等採番の帰結であって欠陥ではないが、実験の再実行ができないという性質）。(3) ★次の `run_next` は planner でなく **CODING_WORKER** を起動する（`READY_FOR_IMPLEMENTATION → GENERATE / claude_barrier=False`）——MGR 手順4 をそのまま実行すると「1段だけ」のつもりが worker 実行になるので本 SPEC ではやらない。手順=再起動前の pid/起動時刻/mtime→既存コマンドで停止・起動→①起動時刻>mtime ②存在しない task への拒否応答に `planner_outcome` キーが在るか（early return で到達しない可能性を先出し・出なくても修理が無いと結論しない）③`/api/submit` 応答に `INTENT_STRATEGY` が在るか（主証拠）→止まる。予想=③は出る/②は出ない方に賭ける/token gate 拒否は起きない。★裁定要求=`planner_outcome` の実証は (a) 別入力で PLAN を観測 (b) worker を動かす (c) 次に PLAN が失敗したときに持ち越す——**(c) を推す**（失敗を人工的に作ると原因が分からなくなる。(b) は独立に価値があるが Build 10 の受入ではない）。禁止=当該 task に run_next を打たない・gate を迂回しない・新しい起動方法を作らない。受入6 は5回連続欠落のため二択、7 は `ledger_query.py` 削除の3回目の確認。再起動が成功しても「修理が効いた」と書かない。*
