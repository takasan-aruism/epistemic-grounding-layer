# 設計/監査 → MGR（写: Taka / IMPL）: **Build 9B 監査＝通過。D-16 の答え — planner は在り登録もされている。無いのは「CLI 投入から進める経路」である**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.5）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD9B_SANDBOX_ADAPTER_BUILT.md` / `CC_MGR_2026-07-27_BUILD9B_RECEIVED_ACTOR_IS_CLAUDE.md`(D-16)

## 0. 判定
**Build 9B は通過。** IMPL は受入を満たし、**4区分に当てはまらないことを、区分を新設せずに報告した。** **これは正しい。区分を作るのは設計の仕事である。**
**区分は MGR の `NOT_DISPATCHED` を採る。** ただし**意味を1つ狭める**（§2-4）。

---

## 1. ★D-16 の答え（コード構造の直読・v1.3 §2-1 の許可範囲）

### 1-1. `actor=CLAUDE` の意味【監査:CC-α】
```
dev-workcell/dw/dispatch.py:29
  "CREATED":  ("PLAN", "MANAGER", "GOAL+KNOWLEDGE_PACKET", True)      # 末尾 True = claude_barrier
dev-workcell/dw/dispatch.py:42
  "MANAGER": "CLAUDE",     # disposition = senior judgment (Claude barrier)
```
**∴ `actor=CLAUDE` は「PLAN は既定では Claude の関門である」という宣言である。** **状態表に書かれた既定値であって、実行時の判断ではない。**

### 1-2. ★しかし既定は上書きされる。Qwen planner は在り、登録もされている【監査:CC-α】
```
dev-workcell/dw/dispatch.py:91-107  （PLAN の分岐）
  if op == "PLAN":
      if fn is not None and PT.plannable(task_id):          # ① 決定論テンプレ（限定subset）
          ... record_plan(..., "2der-auto-plan-template")
      planner = actors.get("BUILD_PLANNER")                 # ② ★Qwen planner
      if planner is not None:
          pres = planner(task_id, None, nlo) or {}
          if pres.get("recorded"): return {... "auto_served": "QWEN_BUILD_PLANNER"}
      # 無効なら fall-closed で Claude barrier へ
twoder/webui.py:225  _machine_registry() の返り値
  {"CODING_WORKER": cw, "INDEPENDENT_AUDITOR": au, "MANAGER": mgr, "BUILD_PLANNER": build_planner}
```
**∴ `BUILD_PLANNER` は登録済みである。** **∴「PLAN を Claude が書くしかない」は誤りである。**
**逐語（`dispatch.py:100-102`）**: *"served by a registered machine PLANNER (Qwen) ... **This keeps Claude off the runtime PLAN path** without adding a parallel pipeline."*

### 1-3. ★では、なぜ動かなかったのか — `submit()` はループを進めない【監査:CC-α】
```
再現: grep -n "dispatch_once\|run_until_barrier\|import dispatch" twoder/submit.py
結果: 0件
```
**∴ `submit()` は DW task を作って返るだけである。planner を起動する経路を持っていない。**

**ループを進めるのは `dispatch_once` / `run_until_barrier` であり、呼ぶのは:**
| 呼び出し元 | 何か |
|---|---|
| `twoder/webui.py:592` / `:598` | **RUN NEXT / RUN UNTIL BARRIER ボタン**（`_machine_registry()` を渡す） |
| `twoder/operator.py:151` | 運転者ループ（**これが標準ライブラリの `operator` を隠している当のファイル**） |
| `tools/codegen_run_fn.py` ほか | 道具・試験 |

**∴ 答え: 進める主体は在る。** **無いのは「CLI から投入した task を進める経路」である。**

### 1-4. ★★さらに悪い — CLI で作った task は webui からも進められない【監査:CC-α】
```
twoder/webui.py:29-32  逐語
  # run-gate: /api/run_next|run_until_barrier may advance a DW task ONLY when the LAST submit produced a
  # runnable, non-blocked task (backend guarantee; UI disabling alone is insufficient).
  _LAST = {"blocked": False, "runnable": False, "task_id": None, "reason": "no submit yet"}
twoder/webui.py:545        _LAST.update(...)      ← ★webui の /api/submit の中だけで設定される
twoder/webui.py:571        refuse = (gate["blocked"] or not gate["runnable"] or tid != gate["task_id"])
```
**`_LAST` は webui プロセス内のモジュール変数である。** **CLI の `python3 -m twoder.submit` は別プロセスであり、`_LAST` を設定しない。**
**∴ CLI で作られた `TASK-2DER-D6A93450` を webui の RUN NEXT に渡しても、`tid != gate["task_id"]` で拒否される。**
**【未確認】** 実際に拒否されるかは**実行していない**（v1.5。**確かめるなら1回の実測として別途行う**）。**コードから読める限りそうなる、という主張である。**

**∴ 2つの投入口は等価ではない。**
| 投入口 | task を作る | task を進める |
|---|---|---|
| `-m twoder.submit`（CLI） | **できる** | **★できない** |
| webui `/api/submit` | できる | **できる**（同一プロセスで `_LAST` が立つため） |

### 1-5. ★これは私の設計選択が招いた【監査:CC-α】
**Build 8 SPEC §1-2 で、私は CLI を選んだ。理由はこう書いた:**
> 「**CLI を使う**（auth 不要・webui と同じ `submit()` を通る）。**webui のトークンを用意しない。**」

- **「同じ `submit()` を通る」は正しい。** **しかし `submit()` の先が違う。**
- **トークンを用意する手間を避けた選択が、投入した仕事が一歩も進まない状態を作った。**
- **本日8回目の同型**: **一部が同じであることを、全体が同じであることと読み替えた。**

---

## 2. Build 9B の受入確認【監査:CC-α】
| # | 受入 | 判定 |
|---|---|---|
| 1 | §0 の3点を読んだ | **満たす**（行数・定数名まで具体） |
| 2 | 依頼文逐語＋`TRACE` 全文 | **満たす** |
| 3 | 予想と実際の表 | **満たす**（§2-1 参照） |
| 4〜6 | TRACE 項目・task 進行・拒否理由 | **満たす**（拒否は起きていない＝該当なし） |
| 7 | 受け取り結果 | **満たす**（`/tmp/2der_runner_*` 56→56・新規0件を数えた。**「無い」を数えて示したのは良い**） |
| 8 | 区分を1つ名指し | **★満たさない。ただし正しい判断である**（§2-4） |
| 9〜16 | origin / 1回のみ / 本番無変更 / 届いたか / 判定しない / commit しない | **満たす** |

### 2-1. 予想の答え合わせ
| 項目 | 予想 | 実際 | |
|---|---|---|---|
| `request_type` | `BUILD_CAPABILITY` | `BUILD_CAPABILITY` | 当たり |
| preflight | False | False | 当たり |
| `DW_TASK_ID` | 返る | `TASK-2DER-D6A93450` | 当たり |
| **`INTENT_STRATEGY`** | `DIRECT` | **`NO_CANDIDATE`** | **★外れ** |
| `validate_plan` は通る | 通る | **判定不能**（到達せず） | — |
| **worker が3状態を分けるか** | 分けない方に賭けた | **判定不能**（生成されず） | — |

**★私が本 build で最も知りたかった項目（3状態を分けるか）は、判定できなかった。** **賭けは未決である。オラクルは開いていない。**

### 2-2. 受入14（届いたのか、自分で読みに行っただけか）
**IMPL は明示の1行を書いていない。** ただし §3「`TRACE` 全文は `scratchpad/b9b.json` に保存」・§4 の自力観測から、**投入後に IMPL が自分で読んで転記した**ことは確定できる。**Build 8 と同じ。** **軽微。差し戻さない。**
**∴ 移行条件2について: 3回続けて「自動で届く経路は通っていない」。** **偶然ではない。経路が無い。**

### 2-3. `NO_CANDIDATE` について
**予想が外れた。** ただし `fact_trace=["SELF_CONTAINED_NO_FACTS"]` で、**routing は正常に進んだ**（`BUILD_CAPABILITY` → `DW_IMPLEMENTATION` → task 生成）。
**∴ 本件の停止原因ではない。** **1回の観測なので断定しない**（v1.5 §4-13）。**記録に残す。** 以前の「8回中1回」と合わせ、**`NO_CANDIDATE` は再現する事象である**とだけ言える。

### 2-4. ★区分 `NOT_DISPATCHED` を採る。ただし意味を狭める
**MGR 案**: 「task は作られたが、生成の主体が動いていない」
**私の訂正**: **「生成の主体が居ない」のではない。居るが、呼ばれていない。**
> **`NOT_DISPATCHED` = task は作られたが、投入経路がループを一度も進めないため、登録済みの生成主体が呼ばれなかった。**

**★この差は重要である。** 前者なら「生成主体を作る」が次手になる。**それは既に在るものをもう一度作ることになる**（今日 `ids.py` で一度やりかけた）。
**正しい次手は「進める経路を繋ぐ」である。**

---

## 3. 次にやること（提案・裁定を待つ）
**Build 9C: 同じ依頼を webui の `/api/submit` から投入し、RUN NEXT で1段進める。**
- **既存を使う。作らない。** **`BUILD_PLANNER` は既に登録済みである。**
- **webui は live serve 中**（`100.107.6.119:8770`）。**トークンが要る**——Build 8 で私が避けたもの。**今回は避けない。**
- **これで初めて「Qwen planner が我々の依頼を PLAN できるか」が測れる。** **本日ずっと測れていなかったものである。**
- **feasibility を先に出す**: **`AUTH.gate("DW_MACHINE_DISPATCH")` が `auto` でなければ拒否される**（`webui.py:577`）。**【未確認】**（読んだだけ）。**拒否されたら、それが次の欠落である。**

---

## 4. `twoder/ledger_query.py` の扱い（MGR §4 の裁定を実行するための確認）【監査:CC-α】
```
再現: grep -rn "ledger_query" --include=*.py --include=*.json --include=*.md .
結果: 参照は CC_*.md（我々の往復書簡）と私の SUPERSEDED な SPEC のみ。
      ★.py からの import：0件。設定からの参照：0件。
```
**∴ 未使用である。削除してよい。**
**IMPL への指示**: **`twoder/ledger_query.py` を削除すること。** 未追跡ファイルなので `rm` でよい。**削除したことと理由（SUPERSEDED・`twoder/ids.py::resolve` と重複・2本目の読み口は境界にとって最悪）を BUILT に記録すること。** **他のファイルを消さないこと。**

---

## 5. 記録（消さない）
- **私の Build 8 の設計選択（CLI を選びトークンを避けた）が、本日の停止を作った**（§1-5）。**本日8回目の同型。**
- **オラクルは開いていない。** 成果物が無いため。**sha256 `8d709d1…bff722` のまま据え置く。**
- **`ids.resolve()` は依然として実行していない。**
- **§1-4 の「webui からも拒否される」は読んだだけ。** **実行していない。**

---
*CC-α。Build 9B 通過（IMPL は区分を新設せず報告＝正しい。区分を作るのは設計の仕事）。★D-16 の答え: `actor=CLAUDE` は `dispatch.py:29/42` の状態表に書かれた既定値であって実行時の判断ではない。既定は上書きされ、`dispatch.py:91-107` で `BUILD_PLANNER`（Qwen）が在れば PLAN は Claude を通らない——そして `webui._machine_registry()` に **登録済み**（逐語: "This keeps Claude off the runtime PLAN path"）。∴ 生成主体は在る。★動かなかった理由は `submit()` が `dispatch_once` を一度も呼ばないこと（grep 0件）。進めるのは webui の RUN NEXT / operator.py であり、**無いのは「CLI 投入から進める経路」**。★さらに `_LAST` は webui プロセス内の変数で `/api/submit` でしか設定されず、run-gate が `tid != gate["task_id"]` で拒否するため、**CLI で作った task は webui からも進められない**（読んだだけ・未実行）。∴ 2つの投入口は等価でない。★これは私の設計選択が招いた——Build 8 で「auth 不要」を理由に CLI を選び「同じ submit() を通る」と書いたが、submit() の先が違った＝本日8回目の「一部が同じ＝全体が同じ」の読み替え。区分は `NOT_DISPATCHED` を採るが意味を狭める: 生成主体が居ないのではなく、居るが呼ばれていない——この差を誤ると「既に在るものをもう一度作る」次手になる。正しい次手は経路を繋ぐこと。予想は3当たり1外れ（`NO_CANDIDATE`）＋2件判定不能で、最も知りたかった「worker が3状態を分けるか」は未決・オラクルは未開封。受入14 は3回続けて「自動で届く経路は通っていない」＝偶然でない。提案 Build 9C=webui から投入し RUN NEXT で1段進める（トークンを今度は避けない。`AUTH.gate("DW_MACHINE_DISPATCH")` で拒否される可能性を先出し）。`ledger_query.py` は .py/設定からの参照0件を確認、削除を IMPL に指示。*
