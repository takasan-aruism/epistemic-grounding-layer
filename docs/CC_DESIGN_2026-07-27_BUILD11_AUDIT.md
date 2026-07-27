# 設計/監査 → MGR（写: Taka / IMPL）: **Build 11 監査 — S3 は実証された。S1 は実証されていない。そして `auto_served` は4つ目の捨て場所だった（私の数え落とし）**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.7）**
- **受領した文書**: `CC_IMPL_2026-07-27_BUILD11_NEW_TASK_THROUGH_PLAN_BUILT.md`

## 0. 判定
**通過。** 各1回・依頼文不変・`run_until_barrier` 不使用・worker へ進まず停止・本番無変更。**定型見出しも両方埋まった**（後述 §5）。
**★ただし「修理の実証」は、私が意図した範囲の一部しか成立していない。** **IMPL の落ち度ではなく、私の SPEC の書き方の帰結である。**

---

## 1. ★何が実証され、何が実証されていないか【監査:CC-α】

```
再現: sed -n '100,120p' dev-workcell/dw/dispatch.py
      sed -n '596,600p' twoder/webui.py
```

| 修理 | 実証されたか | 根拠 |
|---|---|---|
| **S3**（webui が応答に載せる） | **★実証された** | `webui.py:597-599` は `"planner_outcome": step.get(...)` を**無条件に置く**。∴ **キーが応答に在ること＝S3 が動いていること** |
| **S1**（dispatch が barrier に載せる） | **★実証されていない** | 成功パスの early return（`auto_served` を返す2本）は **`planner_outcome` を含まない**。∴ `step.get("planner_outcome")` は `None` を返す。**値 `null` は「S1 が動いた結果」ではなく「キーが無いときの既定値」である** |
| **S2**（`run_until_barrier` の trace） | **実証されていない** | `run_until_barrier` を使っていないため |

> **∴ `planner_outcome: null` は、S1 が入っていても入っていなくても同じ値になる。**
> **∴ 今回の観測は S3 のみを実証した。** **S1/S2 は依然として「PLAN が失敗したとき」にしか確かめられない。**

### 1-1. これは私の設計の限界である
**Build 10 SPEC §2-1 で、私は `planner_outcome` を「barrier の戻り値に載せる」とだけ書いた。** **成功パスに載せる指示をしていない。**
**IMPL はそのとおりに実装した。** **∴ 仕様どおりであり、差し戻さない。**
**∴ Build 11 SPEC §3 で私が「成功しても失敗しても、キーが在れば修理は実証される」と書いたのは、正確ではなかった。** **実証されるのは S3 だけである。** **訂正する。**

---

## 2. ★`auto_served` は4つ目の捨て場所だった（Build 10 で私が数え落とした）【監査:CC-α】

```
twoder/webui.py:597-599  /api/run_next の応答
  {"dispatched", "reason", "nlo", "state", "planner_outcome"}      ← ★auto_served が無い
dev-workcell/dw/dispatch.py:100-101 / :114-116
  return {... "auto_served": "RULE_TEMPLATE_PLAN"}      ← dispatch は返している
  return {... "auto_served": "QWEN_BUILD_PLANNER"}      ← dispatch は返している
```

**∴ `auto_served` は dispatch が返しているのに、webui が転送していない。**
**∴ IMPL が書いた「`auto_served`: `None`／外れ」は、正しくは「判定不能」である。** **値が `None` なのではなく、応答に無い。**
**∴ 私の予想「`QWEN_BUILD_PLANNER`」は、当たりでも外れでもない。**

**★Build 10 の設計で、私は「捨てている場所は3つある」と数えた。** **`auto_served` を見落としていた。**
**同じ関数の、同じ return 文を読みながら、探していたキーだけを見ていた。**

---

## 3. ★誰が PLAN を書いたかは、新しい実行なしで確定できる【設計:CC-α】

```
dev-workcell/dw/dispatch.py:99    W.record_plan(task_id, packet, ts, "2der-auto-plan-template")
twoder/build_planner.py:301       W.record_plan(task_id, plan, ts, identity)
twoder/build_planner.py:286       identity=DEFAULT_IDENTITY = "2der-qwen-build-planner"
```
**∴ DW の `PLAN` イベントに記録された identity が、書き手を一意に決める。**
**∴ `TASK-2DER-B9B4DA3B` の `PLAN` イベントの identity を見れば、Qwen が書いたのか決定論テンプレかが分かる。** **投入も dispatch も要らない。**

**【設計:CC-α】推論としては Qwen である可能性が高い**（`PT.plannable` は「source-grounded bounded reproduction candidate」限定であり、本件のアダプタ作成依頼は該当しないと読める）。**しかし推論である。** **identity を見るまで書かない。**

---

## 4. 次にやること（提案・裁定を待つ）
| # | 件 | 大きさ |
|---|---|---|
| **A** | **`TASK-2DER-B9B4DA3B` の `PLAN` イベントの identity を出す** | **極小。** 実行不要。**誰が PLAN を書いたかが確定する** |
| **B** | **S4: `auto_served` を `/api/run_next` の応答に載せる**（追加のみ・S3 と同型の修理） | 小。**次から「誰が書いたか」が毎回見える** |
| **C** | **S1 を成功パスにも載せる**（`planner_outcome` を成功時も運ぶ） | 小。**ただし「失敗理由を捨てない」が目的なので、成功時は不要とも言える。** **私は B を優先すべきと考える** |

**【設計:CC-α】推奨は A → B。** **C は見送ってよい**（成功時に運ぶ値は「成功した」以上の情報を持たない）。

---

## 5. 受入の確認【監査:CC-α】
| # | 受入 | 判定 |
|---|---|---|
| 到達経路 | **(A) に丸** | **★満たす。7回目にして初めて。** 定型見出しに変えた効果である |
| 持ち越し | **`ledger_query.py` 実施済** | **★満たす。5回目にして初めて。** **削除の根拠（参照ゼロ確認）と、未追跡ゆえ git 履歴に残らないことまで書かれている。良い** |
| 1〜5 | 依頼文・応答・`planner_outcome`・`auto_served`・`derive_state` | **満たす** |
| 6 | 予想と実際 | **満たす**（ただし `auto_served` の判定は §2 で訂正） |
| **7** | **プロセス起動時刻とソース mtime を並べて記載** | **★書かれていない。** 10R の教訓として入れた項目。**軽微だが、次も落ちるなら定型見出しに移す** |
| 8〜12 | 当該 task 不干渉・本番無変更・1回ずつ・判定しない・commit しない | **満たす** |

### 5-1. ★形式を変えたら書かれた（記録する）
**「到達経路」は受入項目として6回連続で落ち、定型見出しにしたら1回で書かれた。**
**`ledger_query.py` は4回連続で落ち、定型見出しにしたら書かれた。**
> **∴ 同じ抜けが続くときは、規律を強めるのではなく、形式を変える。**
**受入7 も次に落ちたら定型見出しへ移す。**

---

## 6. 位置づけ（緩めない）
- **PLAN が2本記録された（`D6A93450` と `B9B4DA3B`）。** **しかし「2DER が作れるようになった」とは書かない。** **PLAN は計画であって成果物ではない。**
- **planner は揺れる**（9C=barrier / 10・11=成功）。**3回の観測で「常に成功する」とは言わない。**
- **`planner_outcome` が失敗理由を運ぶかは、依然として未確認である。**

## 7. 私の誤り（消さない）
1. **「捨てている場所は3つ」と数えて、`auto_served` を見落とした**（§2）。**同じ return 文を読みながら、探していたキーだけを見ていた。**
2. **「成功しても失敗しても修理は実証される」は正確でなかった**（§1-1）。**実証されるのは S3 だけである。**
3. **オラクルは未開封**（sha256 `77af566…`）。**`ids.resolve()` は未実行。** **成果物はまだ生成されていない。**

---
*CC-α Build 11 監査。通過（各1回・依頼文不変・worker へ進まず停止・本番無変更・定型見出し両方記入）。★実証されたのは S3 のみ——`webui.py:597` は `planner_outcome` を無条件に置くのでキーの存在が S3 の実証になるが、成功パスの early return は `planner_outcome` を含まないため値 `null` は `.get()` の既定値であり、**S1 は入っていても入っていなくても同じ値になる**。∴ Build 11 SPEC §3 の「成功しても失敗しても修理は実証される」は不正確であり訂正する（私の SPEC が成功パスへの搭載を指示しなかった帰結で、IMPL は仕様どおり）。★`auto_served` は4つ目の捨て場所——dispatch は返しているのに webui が転送していない ∴ IMPL の「外れ」は正しくは「判定不能」で、私の予想は当たりでも外れでもない。**Build 10 で「捨てている場所は3つ」と数えたとき、同じ return 文を読みながら見落としていた**。★誰が PLAN を書いたかは新しい実行なしで確定できる=`record_plan` の identity が `2der-auto-plan-template` か `2der-qwen-build-planner` かで一意（推論では Qwen だが identity を見るまで書かない）。提案 A(identity を出す・極小)→B(`auto_served` を応答に載せる)、C(成功時も planner_outcome を運ぶ)は見送り推奨。★受入=到達経路が7回目、`ledger_query` 削除が5回目にして初めて記入された——**同じ抜けが続くときは規律を強めず形式を変える**（受入7 のプロセス鮮度も次に落ちたら定型見出しへ）。PLAN は2本記録されたが計画であって成果物ではなく、planner は3回中2回成功で揺れる。*
