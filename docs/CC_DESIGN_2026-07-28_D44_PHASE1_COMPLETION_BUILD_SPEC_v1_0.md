# BUILD SPEC — Event Trace Phase 1 完了条件 v1.0（★実装源）

- `BUILD_ROLE: ★実装源`（**本文書が実装の唯一の典拠**）
- **★宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-28
- **運用方針 確認済（版: `v2.7` — `§12` を最大版で読んだ値）**
- **正典**: `EVENT_TRACE_PHASE1_COMPLETION_CRITERIA_v1_0.md`（Taka 逐語）
- **裁定**: `CC_MGR_2026-07-28_D44_PHASE1_COMPLETION_WORK.md` / `..._EGL_SECOND_LEDGER_RULING_ADD.md`

---

## 0. ★本 build の合否は1行
> **Taka ②:「同一の CLI 依頼で DS→RRI→EGL を同一 `trace_id` で追跡できる」**
> **★今日は `SUBMIT → DS → RRI` の3件で終わった。** **EGL には書いたのに記録されなかった。**
> **∴ ①を実装し、★投入して確かめる。「はず」を書かない。**

---

## 1. ★台帳の全数（MGR 条件5 — 「全部でいくつか」を先に出す）

### 1-1. 走査（★`head` / `limit` / `-m` を1つも使っていない。件数を先に出した）
```
再現（4系すべて。除外条件を明記）:
  grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(|\.open\([\"'](a|w)[\"']\)" --include=*.py <repo> \
    | grep -v "test_\|/regression/\|/experiments/\|run_.*benchmark"
  （egl のみ追加除外: demo_ / /structure/ / /docs/）

件数:  ds=2   rri=2   egl=15   dev-workcell=10        ★合計 29（先に数えた）
```

### 1-2. ★台帳と唯一の書き手（29行を1つ残らず分類した結果）
| 系 | 台帳 | 唯一の書き手 | 依頼経路から到達 | 合流点 |
|---|---|---|---|---|
| DS | `ds_events.jsonl` | `ds/ds/phase0.py:57` | **○** | **①** |
| DS | `event_trace.jsonl` | `ds/ds/etrace.py:120` | ○ | **記録機構自身（対象外）** |
| RRI | `rri_records.jsonl` | `rri/rri/intent_record.py:53` | **○** | **②** |
| RRI | `rthread_events.jsonl` | `rri/rri/request_thread.py:73` | **✗（呼び手0）** | — （`G-45`） |
| EGL | `DESIGN_EVIDENCE_LEDGER.jsonl` | `egl/egl/de_admission.py:167` | **○** | **③** |
| EGL | `egl/data/events.jsonl` | `egl/egl/core.py:119` | **○** | **★⑤（本 build で追加）** |
| EGL | autonomy 5台帳（`PROBLEM_LOG`/`INVESTIGATIONS`/`AUTONOMY_LEDGER`/`PROBLEMS`/`HANDOFFS`） | `egl/autonomy/*` 5箇所 | **✗**（`twoder` 等からの import が0） | — |
| DW | `events.jsonl` | `dev-workcell/dw/workcell.py:81` | **○** | **④** |
| DW | authorization 台帳 | `dev-workcell/dw/authorization.py:46` | **✗（呼び手0）** | — （`G-45`） |
| DW | **`pending_actor.jsonl`** | `dev-workcell/dw/dispatch.py:162` | **★○（到達する）** | **★無い**（`G-41`） |

**台帳を書かないもの**（29行の残り）: ロックファイル（`egl/core.py:44`）／`RESULT_PACKET`・`KNOWLEDGE_PACKET` の json（成果物）／手動実行スクリプトの一時ファイル（`run_rri_task.py` ほか）／各種 `*.json` 出力。

### 1-3. ★結論（数で答える）
```
台帳          : 12
依頼経路から到達: 7   （ds_events / event_trace / rri_records / DE ledger / egl events / dw events / pending_actor）
  うち 合流点が在る : 4   （①②③④）
  うち 記録機構自身 : 1   （event_trace）
  うち 合流点が無い : 2   （egl/data/events.jsonl ← ★本 build の①、pending_actor.jsonl ← G-41）
```
> **★本 build で⑤を加えると、残る未カバーは `pending_actor.jsonl` の1つだけになる。**
> **★そしてそれは「進行経路に run が無い」（`G-41`）と同じ根であり、MGR 裁定で本 build の範囲外である。**
> **★∴「全部押さえたか」の答え: 本 build 後、依頼経路の台帳7つのうち★6つが押さえられ、残り1つは理由付きで範囲外である。**

### 1-4. ★この走査の限界（先に書く）
1. **動的 import / `exec` / 文字列組み立てによる書き込みは見ていない。**
2. **`grep` の正規表現に当たらない書き方（例: `Path.write_bytes` / `csv.writer` / `shutil`）は見ていない。** **★IMPL の再走査で当たったら、それは私の漏れである。**
3. **★この走査は 2026-07-28 18:4x に私が1回だけ行ったものである。** **Taka ⑤は「流用しない」を求めている ∴ IMPL は★独立にやり直すこと**（§4-⑤）。**2つの独立な計数が一致するかが証拠になる。**

---

## 2. 実装

### 2-1. ★合流点⑤（Taka ①）
```
場所: egl/egl/core.py::append_event  … events.jsonl への append の直後
形  : 他の合流点と同じ。fail-closed。
```
| # | 条件 |
|---|---|
| 1 | **★⑤専用の形を作らない。**①〜④と同じ `emit` 呼び出しにする |
| 2 | **★`append_event` の引数・返り値・保存内容を1つも変えない。** **EGL の object graph に何も足さない** |
| 3 | **`component="EGL"` / `function="append_event"`。** `inputs` に `event_type` / `object_type` / `new_prefix`、`outputs` に採番された `object_id` |
| 4 | **★`_idlock()` の中に入れない。** append の後、ロックを出てから emit する（**ロック保持時間を延ばさない**。`H6: 並行採番の直列化` を壊さない） |
| 5 | **★`egl/egl/contracts.py` の `GUARD_CONTRACTS["core.append_event"]` に1行足す**: 「Event Trace へ emit する（fail-closed）」。**★契約表に書かないと、次の誰かが「なぜここで止まるのか」と外す** |

### 2-2. ★fail-closed の形（Taka 裁定・全合流点）
- **他の4つと同じ。** **「止める」ではなく「記録できなかったことを結果として返す」。**
- **★`core.append_event` は `submit()` の外からも呼ばれる**（EGL 自身のパイプライン）。**その場合は例外を送出してよい**——**★ただし「Event Trace に書けなかったため中断した」と分かるメッセージにすること。** **黙って別の例外に見せない。**

### 2-3. ★変えないもの
- `webui.py` を変えない。endpoint を足さない。
- `ids.py` を変えない。
- 合流点①②③④の実装を1行も変えない。
- **`twoder` 自身の台帳9つに手を出さない**（`G-48`・据え置き）。
- **進行経路の run（裁定 B）／`_emit_pending` への emit を含めない。**
- **`rthread_events` / `dw/authorization` を塞がない**（`G-45`）。

---

## 3. ★本 build に含めないが、宙に浮いている裁定（★MGR の注意を要する）
> **Taka の完了条件5件は、次の2件を★含んでいない。** **∴ 私が黙って入れると混ざり、黙って落とすと失われる。** **明示して MGR に預ける。**

| # | 宙に浮いた裁定 | 状態 |
|---|---|---|
| **1** | **`G-46`（`ETRACE_RUN_ID` を webui から読めるように）** | **MGR の旧順序では①だった。** **Taka の5件に無い。** **★②は CLI で満たせるので本 build に不要** |
| **2** | **合流点④（DW）の fail-closed 化**（Taka 逐語「記録失敗時は fail-closed で」） | **MGR の旧順序では②だった。** **Taka の5件に無い。** **★未実装のまま残る** |

**★私は本 build に含めない**（混ぜない規律／禁止5の趣旨）。**★MGR が別段として立てること。** **忘れると、Taka の裁定が1つ実装されないまま残る。**

---

## 4. 受入（Taka ①〜⑤）

| # | 条件 | 示し方 |
|---|---|---|
| **①** | `acquisition` 系の EGL 書き込みが合流点を通る | **`core.append_event` に emit が在ることの差分＋契約表の1行** |
| **②** | **★同一 CLI 依頼で DS→RRI→EGL を同一 run で追跡できる（合否）** | **§5 の文面で CLI 投入1回 → `ETRACE_RUN_ID` を貼る → `GET /api/resolve?id=ETR-…` の全 event を貼る → ★`component` に `EGL` が現れることを示す。現れなければ「現れなかった」と書く** |
| **③** | 打ち切り出力を完全性の証拠に使わない | **★`head`/`limit`/`-m`/`tail` を1つも使っていないことを、コマンドごと貼る** |
| **④** | 総件数・確認件数・打ち切り有無を必須記録 | **★各走査に「総N件 / 確認N件 / 打ち切り無し」を書く。一致しないなら理由を書く** |
| **⑤** | **12入口と全書き込み経路を打ち切りなしで★再走査** | **§4-1** |
| 追 | 既存の判断結果・返り値・保存内容が不変 | **`/api/claude_packet` と `/api/state` の sha256 前後一致＋非回帰（基準 91 passed / 7 failed・顔ぶれ diff）** |

### 4-1. ★⑤の走査（過去を1つも流用しない）
```
(a) 入口の再走査 — submit() の呼び手 / create_task の呼び手 / record_utterance の呼び手
    ★総件数を先に出す。前回は「12入口」だったが、★前回に合わせない。違えば違うと書く。
(b) 全書き込み経路の再走査 — 5repo の open(a|w) / write_text / open("a")
    ★総件数を先に出す。★出た行を1つ残らず分類する（合流点 / 合流点の内側 / 台帳を書かない / 未カバー）
(c) ★私（設計）の §1 の計数と突き合わせる
    一致 → 2つの独立な計数が一致した、と書く
    不一致 → ★どちらが正しいかを確かめ、私の誤りなら「設計の計数が誤り」と書く
```
> **★(c) が最も価値が高い。** **本日、私の計数は2回誤った**（`head -8` / `0` の false negative）。**独立な計数で当たること自体が証拠である。**

---

## 5. ★投入（1回だけ。文面は事前記録）
```
宛: 設計/監査(CC-α)
2DER の front door を CLI から通したとき、DS・RRI・EGL のどこまで記録が残るかを知りたい。
記録に残っている事実だけで、追跡が途切れる箇所を挙げてください。
```
- **★前回と同一文面**（MGR 承認済。`OBSERVE_CURRENT_STATE` に入り EGL 取得系を通ることが★実測で分かっている）。**1文字も変えない。**
- **★1回だけ。** 満たせなくても2回目を投入しない。
- **★webui の再起動は不要**（CLI 経路のため）。**ただし `cd /home/takasan` を明示してから実行する**（v2.5 §4-17）。

### 5-1. ★事前に固定する予測（賭ける所と賭けない所を分ける）
| 項目 | 予測 |
|---|---|
| **EGL の event が出るか** | **★出る方に賭ける。** 根拠: 前回の同一文面が `EGL_OBSERVATION_INGEST` を記録しており、その経路が `core.append_event` を通ることをコードで確認した。**外れたら「外れた」と書く** |
| **EGL の event が何件出るか** | **★予想しない。** 観測数に依存し、私は数えていない |
| `request_type` | **★予想しない**（受入項目に routing が無い） |
| **親子が1本に繋がるか** | **★繋がる方に賭ける。** 根拠: 前回3件が繋がった。**繋がらなければ繋げる修正をせず事実を書く** |

## 6. ★止まってよい場所
| # | 条件 |
|---|---|
| 1 | **§1 の計数と、あなたの再走査の件数が違った** → **★合わせない。両方書いて報告** |
| 2 | **`_idlock` の外で emit すると `object_id` が取れない**（設計の見落とし）→ **★中に入れず報告** |
| 3 | **EGL の event が出なかった** → **★私の予測が外れた。繋げる修正をせず報告** |
| 4 | **fail-closed にすると EGL 自身のテストが落ちる** → **★報告。落ちる件数と名前を書く** |
| 5 | SPEC が2通りに読める |

## 7. ★未確認（引き継ぐ）
1. **`DW_IMPLEMENTATION` 枝で `core.append_event` が走らないこと**（コード読みのみ）→ **★受入で「走らない依頼で走らない」ことも確かめる**（MGR 条件3）。
2. **1回の取得系依頼で `append_event` が何回走るか**（`run_id` 無し event の増加量）。
3. **§4-1 の `0` false negative の原因**（特定していない）。

---
*CC-α D-44 BUILD SPEC v1.0（実装源・宛 IMPL）。★合否は Taka ②「同一の CLI 依頼で DS→RRI→EGL を同一 run で追跡できる」で、今日は `SUBMIT→DS→RRI` の3件で終わり EGL には書いたのに記録されなかった ∴ ①を実装して**投入して確かめる。「はず」を書かない**。★MGR 条件5（全部でいくつか）に数で答えた=`head`/`limit`/`-m` を1つも使わず件数を先に出し（ds=2 / rri=2 / egl=15 / dev-workcell=10 の**計29行**）、29行を1つ残らず分類した結果、**台帳12・依頼経路から到達7**（`ds_events`/`event_trace`/`rri_records`/DE ledger/`egl/data/events.jsonl`/dw `events.jsonl`/`pending_actor.jsonl`）で、うち合流点が在るのが4（①②③④）、記録機構自身が1、**合流点が無いのが2**（`egl/data/events.jsonl`＝本 build の①、`pending_actor.jsonl`＝`G-41` で範囲外）∴ **本 build 後、依頼経路の台帳7つのうち6つが押さえられ残り1つは理由付きで範囲外**。走査の限界（動的 import/`exec`/正規表現に当たらない書き方は見ていない／本走査は CC-α が1回行っただけで Taka ⑤の「流用しない」に従い IMPL が独立にやり直すこと）を明記。★実装=合流点⑤を `egl/egl/core.py::append_event` の append 直後に他と同じ形・fail-closed で置き、引数/返り値/保存内容を1つも変えず、**`_idlock()` の中に入れない**（ロック保持時間を延ばさず `H6: 並行採番の直列化` を壊さない）、**`egl/egl/contracts.py` の `GUARD_CONTRACTS["core.append_event"]` に「Event Trace へ emit する(fail-closed)」を1行足す**（契約表に書かないと次の誰かが「なぜ止まるのか」と外す）。`core.append_event` は `submit()` の外からも呼ばれるので例外送出でよいが「Event Trace に書けなかったため中断した」と分かるメッセージにする。★**宙に浮いた裁定2件を明示して MGR に預ける**=`G-46`（`ETRACE_RUN_ID` を webui から）と**合流点④の fail-closed 化（Taka 逐語）**はどちらも Taka の5件に含まれず、黙って入れると混ざり黙って落とすと失われるので本 build に含めず MGR が別段として立てること（忘れると Taka の裁定が1つ実装されないまま残る）。★受入=①emit の差分＋契約表の1行／②CLI 1回投入で `ETRACE_RUN_ID` と全 event を貼り **`component` に `EGL` が現れることを示す。現れなければ「現れなかった」と書く**／③`head`/`limit`/`-m`/`tail` を1つも使っていないことをコマンドごと貼る／④各走査に「総N件/確認N件/打ち切り無し」を書き一致しないなら理由／⑤入口と全書き込み経路を**過去を流用せず再走査**し、**CC-α の §1 の計数と突き合わせて一致なら「2つの独立な計数が一致した」、不一致ならどちらが正しいか確かめ CC-α の誤りなら「設計の計数が誤り」と書く**（本日 CC-α の計数は `head -8` と `0` の false negative で2回誤っており、独立な計数で当たること自体が証拠）。★投入は前回と同一文面（MGR 承認済・`OBSERVE_CURRENT_STATE` で EGL 取得系を通ることが実測済）を1文字も変えず1回だけ、`cd /home/takasan` を明示（v2.5 §4-17）。★事前予測=EGL の event が出る方と親子が繋がる方に賭け（根拠を明記）、件数と `request_type` は予想しない。★止まってよい場所5件（計数の不一致は合わせず両方書く／`_idlock` の外で `object_id` が取れないなら中に入れず報告／EGL の event が出なければ CC-α の予測外れとして繋げる修正をせず報告／fail-closed で EGL のテストが落ちたら件数と名前を書く／2通りに読める）。★未確認3件。*
