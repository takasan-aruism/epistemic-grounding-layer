# 設計/監査 → MGR（写: Taka / IMPL）: **Build 9C 監査 — 私の賭けは外れた。そして IMPL の区分 (b) も成り立たない。planner は呼ばれている。捨てられているのは「失敗の理由」である**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.6）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD9C_WEBUI_ADVANCE_BUILT.md` / `CC_MGR_2026-07-27_D18_APPROVED_FIX_INSTRUMENT_FIRST.md`

## 0. 判定
**Build 9C は通過。** 作法（1回ずつ・依頼文不変・gate 迂回なし・1段で停止・トークン非記録）はすべて守られている。
**★ただし §4 の区分 (b)「planner がそもそも呼ばれず」は、観測から言えない。** **訂正する（§2）。**
**★私の賭け（`auto_served: QWEN_BUILD_PLANNER`）は外れた。** **先に書く。**

---

## 1. 私の予想の答え合わせ（外れ2件・両方とも私の確認不足）
| 項目 | 予想 | 実際 | 原因 |
|---|---|---|---|
| `DW_TASK_ID` は**新しい** task | 新規 | **Build 9B と同一** | **★私が採番規則を読んでいなかった** |
| `auto_served` | `QWEN_BUILD_PLANNER` | **無し（`CLAUDE_BARRIER`）** | §2 |

### 1-1. task id が同一になる理由【監査:CC-α】
```
twoder/submit.py:405
  dw_task = "TASK-2DER-" + hashlib.sha1(raw_input.encode()).hexdigest()[:8].upper()
```
**∴ task id は依頼文だけから決まる。** **投入口に依存しない。**
**∴ 同じ依頼文を投げ直しても task は増えない（冪等）。これは良い設計である。**
**∴ IMPL の「なぜ同一になるかは判定材料が不足」は正しい報告であり、答えはこれである。**
**★私は「新しい task が返る」と予想した。採番規則は `submit.py` に1行で書いてあった。読めば分かることだった。** **予想を固定する前に決定論で確定する、をまた守れていない。**

---

## 2. ★区分 (b) の訂正 — **planner は呼ばれている**【監査:CC-α】

### 2-1. 登録は無条件である
```
twoder/webui.py:304-306
  from twoder import build_planner as BP
  build_planner = BP.make_dw_planner_actor(chat_fn=_planner_chat_fn(), ts=TS)
  return {"CODING_WORKER": cw, "INDEPENDENT_AUDITOR": au, "MANAGER": mgr, "BUILD_PLANNER": build_planner}
twoder/build_planner.py:286-303
  def make_dw_planner_actor(...):
      def fn(task_id, view=None, nlo=None): ...
      return fn                      # ★None を返す経路が無い
```
**推論の連鎖（観測から）:**
1. 段2 は **正常な JSON を返した**（`dispatched: false / reason: CLAUDE_BARRIER`）。**例外なら 500 になる。**
2. ∴ `_machine_registry()` は正常終了した。∴ `webui.py:305` は実行された。
3. ∴ `actors["BUILD_PLANNER"]` は callable である（`make_dw_planner_actor` は必ず関数を返す）。
4. ∴ `dispatch.py:104` の `if planner is not None:` は**真**である。
5. **∴ planner は呼ばれた。**

**∴「planner がそもそも呼ばれず」は成り立たない。**

### 2-2. ★では、なぜ観測できないのか — 戻り値が2つの場合を区別しない
```
dev-workcell/dw/dispatch.py:104-107
  planner = actors.get("BUILD_PLANNER")
  if planner is not None:
      pres = planner(task_id, None, nlo) or {}
      if pres.get("recorded"):  return {... "auto_served": "QWEN_BUILD_PLANNER"}
      # invalid / provenance-rejected plan -> fall through to the Claude barrier (fail-closed)
dev-workcell/dw/dispatch.py:123-126
  if nlo["claude_barrier"] or fn is None:
      _emit_pending(task_id, nlo, ts)
      return {"dispatched": False, "reason": "CLAUDE_BARRIER" if nlo["claude_barrier"] else "NO_MACHINE_ACTOR",
              "nlo": nlo, "pending_actor": role}
```
**★`pres` は、`recorded` が偽なら、その場で捨てられる。** **barrier の戻り値に一切入らない。**

**∴ 返ってきた `CLAUDE_BARRIER` は、次のどちらでも同じ形になる:**
| | |
|---|---|
| (i) planner が登録されていない | `CLAUDE_BARRIER` |
| (ii) **planner が呼ばれ、失敗し、理由が捨てられた** | **`CLAUDE_BARRIER`（同一）** |

**∴ IMPL が (b) と書いたのは、観測できないものを区別したことになる。** **報告としては過剰である。**
**∴ ただしこれは IMPL の落ち度というより、経路が観測を潰していることの帰結である。** **差し戻さない。**

### 2-3. ★★理由は作られている。捨てられているだけである
```
twoder/build_planner.py:292-300
  def fn(task_id, view=None, nlo=None):
      built = build_plan(...)
      if not built["ok"]:
          return {"recorded": False, "stage": built["stage"], "reason": built["reasons"], "plan": None}
      val = validate_plan(...)
      if not val["valid"]:
          return {"recorded": False, "stage": "validation", "reason": val["reasons"], "plan": plan,
                  "validation": val}
```
**∴ 「何が足りなかったか」は `reason` として必ず作られている。**
**∴ 我々が本日ずっと欲しがっていた観測（外れ方 (a) の `reasons`）は、生成されて、捨てられていた。**

**参考**: `:8005` は待ち受け中である【実】(`ss -ltn | grep 8005` → LISTEN)。**∴ 「Qwen が居ないから失敗した」ではない可能性が高いが、断定しない。理由が見えないため。**

---

## 3. ★本日3つ目の同型である（これが本質）
| 箇所 | やっていること |
|---|---|
| `runtime_inspection.build_request` | 該当が無いとき「無い」を返さず、`_CATALOG` **全件**にフォールバックする |
| **`dispatch_once` の PLAN 分岐** | **planner が失敗したとき理由を返さず、`CLAUDE_BARRIER` にフォールバックする** |

**どちらも「失敗した」を、正常に見える別の結果に置き換えている。**
**∴ 本日の第一原則（存在／非存在を決定論で分け、それぞれ別の分岐へ渡す）に、ディスパッチャ自身が違反している。**
**∴ そして両方とも、我々が「機能が無い」と誤読する原因になっている。** **今日それを2回やった。**

### 3-1. 区分の訂正案
**IMPL が使うべきだった名前は (b) ではなく、次である:**
> **`PLANNER_OUTCOME_DISCARDED` — planner は呼ばれたが、その結果が経路上で捨てられるため、成否も理由も観測できない。**

---

## 4. ★次の一手（提案・裁定を待つ）— 2行の修理で、見えるようになる

**`dispatch.py` の barrier 戻り値に `pres` を載せる。**
```python
# 現在: pres を捨てて barrier へ落ちる
# 提案: pres を保持し、barrier の戻り値に planner_outcome として載せる（dispatched は False のまま）
```
| | |
|---|---|
| **性質** | **修理である。新機能ではない。** **失敗の理由を捨てているのは欠陥である**（MGR が `TODAY` ハードコードに与えた判断と同型） |
| **挙動の変更** | **無い。** `dispatched` も `reason` も `nlo` も変えない。**フィールドを1つ増やすだけ** |
| **境界への寄与** | **★寄与する。** これが無い限り、**優先度1（台帳を読める仕組みを経路で作る）は永久に測れない。** 失敗しても理由が返らないため |
| **非回帰の要点** | `CLAUDE_BARRIER` の `reason` 文字列を変えない（既存 assert が見ている可能性）。**追加のみ** |

**★これを先にやるべきだと考える。** **優先度1 を進める前提条件だからである。**
**MGR の優先度（1 台帳を読める仕組み）を変えるのではなく、その1歩目がこれになる、という提案である。**

---

## 5. Build 9C の受入確認【監査:CC-α】
| # | 受入 | 判定 |
|---|---|---|
| 1〜4 | 段0/段1/段2 の逐語・`derive_state` | **満たす** |
| 5 | `auto_served` を名指し | **満たす**（「無し」と書いた） |
| 6 | 拒否理由を逐語で全部 | **満たす**（段0 の `reason` を全文。段2 は `reason` が `CLAUDE_BARRIER` のみで、それ以上が返っていない＝§2-2） |
| 7 | PLAN が記録された場合の中身 | **該当なし** |
| 8 | sandbox の増減 | **★書かれていない。** 軽微（PLAN 未到達なので sandbox は作られようがない） |
| 9〜11 | 予想と実際・本番無変更・1回ずつ | **満たす** |
| 12 | **届いたのか自分で読みに行っただけか** | **★また書かれていない。3回連続** |
| 13〜16 | 判定しない・commit しない・版・再現コマンド | **満たす** |
| **§7 併記の `ledger_query.py` 削除** | **★BUILT に記載が無い。** 実施したか不明 | **要確認** |

### 5-1. 受入12 について（3回連続で欠落）
**私は3回同じ項目を SPEC に書き、3回とも書かれていない。**
**∴ 項目の書き方に問題があると考える。** **「1行書く」では実行されない。**
**次の SPEC では、答えの選択肢を2つ用意して、どちらかに丸を付ける形にする。**
**事実としては、3回とも IMPL が自分で読んで転記している。** **自動で届く経路は無い（`2DER_MECHANISM_MAP.md` §5 N5 に記載済）。**

---

## 6. 私の誤り（消さない）
1. **賭けを外した。** `auto_served: QWEN_BUILD_PLANNER` に賭けたが、そもそも観測できない形だった。**「賭けが成立しない」ことを見抜けなかった。**
2. **task 採番規則を読まずに「新しい task」と予想した。** `submit.py:405` の1行。**本日、予想の前に決定論を確定する規律を自分で書いておきながら、また守れていない。**
3. **`ids.resolve()` は依然として実行していない。** オラクルは未開封（sha256 `8d709d1…bff722`）。
4. **§2 の「planner は呼ばれた」は推論である。** 実行して確かめていない。**§4 の修理が入れば、推論ではなく観測になる。**

---
*CC-α Build 9C 監査。通過（作法は全て遵守）。★私の賭け（auto_served=QWEN_BUILD_PLANNER）は外れ、task id の予想も外れた——採番は `submit.py:405` で `sha1(raw_input)[:8]` の決定論、投入口に依存せず冪等。読めば分かる1行を読まずに予想した（本日書いたばかりの規律をまた守れていない）。★IMPL の区分 (b)「planner がそもそも呼ばれず」を訂正: `webui.py:305` の登録は無条件で `make_dw_planner_actor` は必ず関数を返し、段2 が正常 JSON を返した以上 `_machine_registry()` は成功している ∴ planner は呼ばれた。★観測できない理由は `dispatch.py:104-107` が `pres` を `recorded` 偽なら捨て、barrier の戻り値 `{dispatched:false, reason:"CLAUDE_BARRIER", nlo, pending_actor}` に一切載せないこと——(i)未登録 と (ii)呼ばれて失敗 が同じ形になる。★そして `build_planner.py:292-300` は失敗時に `reason`(build 段/validation 段の reasons) を必ず作っている＝我々が本日ずっと欲しがっていた観測は、生成されて捨てられていた。:8005 は待ち受け中（実測）。★本日3つ目の同型: `runtime_inspection` の全件フォールバックと同じく、ディスパッチャが「失敗」を正常に見える別の結果に置き換えている＝第一原則にディスパッチャ自身が違反。区分名は `PLANNER_OUTCOME_DISCARDED`。★次の一手=`dispatch.py` の barrier 戻り値に `pres` を載せる修理（挙動不変・フィールド追加のみ・`reason` 文字列を変えない）。これが無い限り優先度1は永久に測れないので、優先度1の1歩目にすることを提案。受入=8(sandbox 増減)と12(届いたか)が欠落、12 は3回連続なので次の SPEC では二択に丸を付ける形に変える。`ledger_query.py` 削除の記載も無く要確認。*
