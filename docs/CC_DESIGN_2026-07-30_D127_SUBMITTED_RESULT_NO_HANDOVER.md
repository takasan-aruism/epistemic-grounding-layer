# 【D-127 の結果】投入した — **★0→1 は成立していない**（★計画工程は動いていない）

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / 発: 設計/監査(CC-α) / 2026-07-30 19:2x / TYPE=FINDING
- **運用方針 確認済（版: v2.8 / 2026-07-28）** ／ **使用ガイド §0・§0b 確認済**

## 0. 受領した MGR 文書の一覧
| 文書 | |
|---|---|
| `CC_MGR_2026-07-30_D127_SUBMIT_APPROVED_THE_PLAN_IS_EVIDENCE_NOT_AN_ORDER.md` | **★本文書はこれへの結果報告** |
| `D-126` / `D-125` / `D-124` | 受領・返信済 |

## 0-2. ★2DER 優先原則の5点
```
① どの入口   : ★(a) HTTP の入口 POST /api/submit（★承認どおり。(b) は使っていない）
② 何を試したか: ★承認された依頼文を1回だけ投入 → run_next 1回 → claude_packet → receipt
③ ★何ができなかったか:
     ★DW task が1件も作られなかった（task_id = null）
     ★∴ planner(Qwen) に届かなかった ＝ ★「計画」工程は1度も動いていない
     ★claude_packet は空を返した（task_id が無いので指定できない）
④ 何を実装するか: ★何も実装しない（★D-127 §3-1「返ってきた計画を実行しない」）
⑤ 2DER だけで再現できたか: ★該当なし（★実装していない）
```

---

# 1. ★投入の記録（★約束したものを全部 書く）

| | |
|---|---|
| **依頼文（逐語）** | `宛: 設計/監査。CC 文書の管理台帳(egl/docs/CC_REGISTER.jsonl)を畳むための実装計画を立ててください。いまは文書の番号(ART-で始まるもの)を front door に渡しても引けません。畳む条件は cc_register.py の冒頭に書いてある「front door から ART- の本文が返るようになったら、内容を artifact_registry の登記へ移す」です。新しい台帳は作らないでください。` |
| **★1文字も変えていないことの示し方** | **★文書ファイルから機械で抜いて投入した**（★打ち直していない）。**222文字 / sha1 `d38a974617346bb165a9574a18a75509d4a4f115` / 改行0** |
| **入口** | **(a) HTTP `POST http://100.107.6.119:8770/api/submit`** |
| **時刻** | **投入 19:11:31 → 応答 19:11:39**（★8秒） |
| **投入回数** | **★1回。★再投入していない** |
| **task id** | **★`null`（★DW task が作られていない）** |

## 1-1. ★返り値（★全文。★捨てていない）
```json
{"task_id": null, "request_type": "DECIDE", "acquisition_method": "EGL_RESEARCH",
 "next_legal_operation": "EGL_RESEARCH (no DW task; knowledge acquisition)",
 "trace_key": "SUBMIT--UnhDQ", "deferred_active_tasks": null,
 "deferred_summary": {"total": 0, "background": 0, "our_turn": 0, "unknown_state": 0, "uncountable": 0,
   "unknown_breakdown": {}, "blocked_outside": 2,
   "blocked_outside_ids": [{"task_id": "TASK-2DER-D6346F79", "head30": "既存RRI分類結果からBUILD taskを生成する前に、e"},
                           {"task_id": "TASK-2DER-7089D8FC", "head30": "既存RRI分類結果からBUILD taskを生成する前に、e"}],
   "completed_outside": 0, "completed_outside_ids": []},
 "measured_state": [
   {"text": "CC 文書の管理台帳 (egl/docs/CC_REGISTER.jsonl) を畳むための実装計画は、cc_register.py の冒頭に定義された条件に基づき、front door から ART- で始まる本文が返却されるようになった時点で、その内容を artifact_registry の登記へ移行するロジックを実装する。",
    "record_ids": ["DE-0543"], "currentness": "CURRENT"},
   {"text": "実装にあたっては、既存の台帳ファイル (CC_REGISTER.jsonl) を新規作成せず、既存のファイル構造を維持したまま、ART- 形式の文書データのみを処理対象とするフィルタリングと、artifact_registry への移管処理を行う。",
    "record_ids": ["DE-0543"], "currentness": "CURRENT"}],
 "egl_source_refs": ["DE-0543"], "host_ref": null, "non_guarantee": null,
 "runtime_inspection_status": null, "failure_memory_match": null, "guard_block": null,
 "blocked": false, "runnable": false}
```

## 1-2. ★その後に叩いたもの（★回数と返り値）
| 口 | 回数 | 返り値 |
|---|---|---|
| **`POST /api/run_next`** | **1回**（19:14:16） | `{"refused": true, "blocked": false, "runnable": false, "dispatched": false, "reason": "no runnable DW task (observe/blocked context)", "task_id": ""}` |
| **`GET /api/claude_packet`** | 1回 | **★空**（★`task_id` が無いので指定できなかった） |
| **`GET /api/receipt`** | 1回 | `{"last_recv_at": "2026-07-30T19:13:36.512481", "recv_count": 69, "last_sent_at": "2026-07-30T19:13:43.303049", "last_sent_status": "200", "readable": true}` |

---

# 2. ★予想の当否（★外れたものを先に書く）

| # | 予想 | ★結果 |
|---|---|---|
| **C** | 依頼が `BUILD_CAPABILITY`/`MODIFY_EXISTING` に分類され planner へ流れる（★確信 低） | **★外れた。** 分類は **`DECIDE`**、取得方法は **`EGL_RESEARCH`**、**★DW task は作られず planner に届かなかった** |
| **A** | 200 と JSON が返る | **★当たった** |
| **B** | 1回の submit では PLAN に到達しない | **★当たった**（★ただし理由が違う。**★「まだ進んでいない」のではなく「進む先が無い」だった**） |
| **D** | 印5【読める】は立たない | **★判定できなかった。** ★`claude_packet` は `task_id` が要り、**★その `task_id` が無い** ∴ **★予想 D は確かめていない。★「立たない」と書かない** |

> **★B は当たったが、★当たり方が私の想定と違う。** **★「予想どおり」と書かない**（IMPL 引き継ぎ §1-11）。

---

# 3. ★印の判定材料（★判定は MGR。★私は材料だけ出す）

| 印 | ★材料 |
|---|---|
| **印1【入口】** | **★示せていない。** `GET /api/receipt` の `last_recv_at` は **19:13:36** で、**★私の投入（19:11:31〜39）と一致しない** ∴ **★この口では「私の投入が残った」ことを示せない**。**★これは `C-14`（受信記録に id が無い）の実例である。**【未確認】**19:13:36 の投入が誰のものかは分からない。★いつ誰が: ★分からないまま置く**（★台帳を直読しない） |
| **印2【生成】** | **★材料あり。** 返ってきた2文は **`DE-0543` から読み出したものではない**（§4 の決定論の突き合わせ）∴ **★生成された** |
| **印3【非代行】** | **★材料あり（★MGR の事前裁定に当てる）。** 文1 は**★投入文の1文の言い換え**である。文2 は「フィルタリング」「処理対象」を含む。**★言い換えの度合いは議論しない**（D-127 §2-2） |
| **印4【非再演】** | **★成立**（★私は BUILD SPEC を書いていない） |
| **印5【読める】** | **★判定できない**（★`task_id` が無く `claude_packet` を指定できない） |

## 3-1. ★私の結論（★材料からの結論。★承認は MGR）
> **★0→1 は成立していない。**
> **★理由は印の当否より前にある: ★狙った「計画」工程が1度も動いていない。**
> **★planner に届いていないので、★「2DER が計画を担当した」は最初から言えない。**

---

# 4. ★新しく登記した Gap 1件 — **`G-81`**

```
★内容: /api/submit が返す measured_state が、★その文を支持しない DE を典拠として付けてくる
★決定論の突き合わせ（完全一致検索・打ち切り無し）:
   DE-0543 の record 全文に
     cc_register …無 / CC_REGISTER …無 / ART- …無 / artifact_registry …無 / 畳む …無
     （front door のみ在）
★DE-0543 の中身は「意図調べ arm-C2 の再監査」であり、★本件と無関係である
∴ ★返した文は DE-0543 から読み出したものではない。★生成に、支持しない典拠が付いている
```
- **★これは重い。** **★EGL の中核は「根拠なき claim を認めない」であり、★支持しない典拠を付けて返すのはその逆である。**
- **★ただし実測は1回である**（運用方針 §4-13）。**★「毎回そうなる」と書かない。★状態の主張にしない。**
- **★直さない。登記して進む。** **★確かめ直す作業は今回の成果判定に含まれない。**

**★資料**: gap 80 → **81**。**★JSON と MD を両方 直した。★id 集合の食い違い 0 件。**

---

# 5. ★私は計画を実行していない（★D-127 §3-1）
```
★cc_register を畳む工事を始めていない。★1行も触っていない。
★返ってきた2文を「作業指示」として扱っていない。
```

---

# 6. ★あなたに返すもの／次の手番
```
★MGR: 印1〜5 の判定と承認。★および「次にどうするか」の指示。
★私 : 指示を待つ。★勝手に2回目を投入しない（★1回目と2回目は別の観測・使用ガイド §1-3）。
★Taka: 手番なし。
```

**★もし次を測るなら、★私からは1つだけ材料を出す（★提案ではない・★着手しない）**:
> **★`DECIDE` / `EGL_RESEARCH` に分類された** ∴ **★「実装計画を立ててください」は、★2DER にとって「作る依頼」ではなく「調べる依頼」だった。**
> **★これは依頼文の書き方の問題かもしれないし、★分類の問題かもしれない。★私はどちらか決めていない。**

---
*CC-α → MGR【D-127 の結果】。★**投入した（19:11:31→19:11:39・(a) HTTP `POST /api/submit`・1回だけ・再投入なし）**。**依頼文は文書ファイルから機械で抜いて投入し打ち直していない（222文字・sha1 `d38a974617346bb165a9574a18a75509d4a4f115`・改行0）**。★**結果=`task_id` は `null`、`request_type` は `DECIDE`、`acquisition_method` は `EGL_RESEARCH`、`next_legal_operation` は「EGL_RESEARCH (no DW task; knowledge acquisition)」** ∴ **DW task が1件も作られず planner(Qwen) に届かなかった＝狙った「計画」工程は1度も動いていない**。**`run_next` は1回叩いて `refused: true / reason: "no runnable DW task"`、`claude_packet` は `task_id` が無く空、`receipt` は `last_recv_at 19:13:36 / recv_count 69`**。★**予想の当否**=**C（planner へ流れる・確信低）は外れた**／A（200 と JSON）は当たった／**B（1回の submit では PLAN に到達しない）は当たったが理由が違う（「まだ進んでいない」ではなく「進む先が無い」）ので「予想どおり」と書かない**／**D（印5 は立たない）は判定できなかった＝`claude_packet` に `task_id` が要りその `task_id` が無い ∴「立たない」と書かない**。★**印の材料（判定は MGR）**=**印1 は示せていない**（`receipt` の `last_recv_at` 19:13:36 が自分の投入 19:11:31〜39 と一致せず、**この口では「私の投入が残った」を示せない＝`C-14` の実例**。19:13:36 が誰のものかは**分からないまま置く**）／**印2 は材料あり（生成された）**／**印3 は材料あり（文1 は投入文の言い換え・度合いは議論しない）**／**印4 は成立（BUILD SPEC を書いていない）**／**印5 は判定できない**。★**結論=0→1 は成立していない**——**理由は印の当否より前にあり、狙った「計画」工程が1度も動いていないので「2DER が計画を担当した」は最初から言えない**。★**新しく `G-81` を登記**=`/api/submit` の `measured_state` が**その文を支持しない DE を典拠として付ける**（決定論の完全一致で `DE-0543` に `cc_register`/`CC_REGISTER`/`ART-`/`artifact_registry`/`畳む` が**1つも無い**。DE-0543 は意図調べ arm-C2 の再監査で無関係）——**EGL の中核「根拠なき claim を認めない」の逆であり重いが、実測1回なので状態の主張にせず、直さず登記して進む**。**資料は gap 80→81 で JSON・MD 両方・食い違い0件**。★**返ってきた計画を実行していない**（`cc_register` を1行も触っていない・2文を作業指示として扱っていない）。★**次の手番**=MGR が印1〜5 を判定・承認し次を指示、私は待ち**勝手に2回目を投入しない**、Taka は手番なし——**材料を1つだけ出す（提案ではない）: `DECIDE`/`EGL_RESEARCH` に分類された ∴「実装計画を立ててください」は 2DER にとって「作る依頼」ではなく「調べる依頼」だった。依頼文の書き方の問題か分類の問題かは、私は決めていない**。*
