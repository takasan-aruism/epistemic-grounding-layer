# BUILD SPEC — Event Trace 第一段階 v1.0（★実装源）

- `BUILD_ROLE: ★実装源`（**本文書が実装の唯一の典拠。他の CC_* 文書から実装しない**）
- **★宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-28
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **正典**: `EVENT_TRACE_PHASE1_WORK_ORDER_v1_0.md`（Taka 逐語）
- **裁定**: `CC_MGR_2026-07-28_D42_RULINGS_A_B_AND_TEXT_APPROVED.md`（A/B・依頼文・投入順）
- **承認**: `CC_MGR_2026-07-28_D42_BUILD_SPEC_APPROVED.md`
- **草案**: `CC_DESIGN_2026-07-28_D42_EVENT_TRACE_PHASE1_SPEC.md`（**本文書が優先する**）

### ★改訂1（2026-07-28・MGR 承認後。★隠さずに書く）
| # | 変更 | 理由 |
|---|---|---|
| **1** | **宛先を `MGR` → `IMPL` に訂正** | **★私の誤りだった。** 私は「規律上 MGR が IMPL へ渡す」と書いたが**逆で、MGR こそ IMPL へ直接指示しない**（`mgr-writes-only-to-design-audit`）。**SPEC を IMPL に渡すのは設計/監査である** |
| **2** | **§0-1 を追加**（完了条件3件の格上げ） | MGR 承認 §3。**「注記」ではなく「完了条件」である** |
| **3** | **`G-40` を登録**（`ds` に置いたのは妥協である旨） | MGR 裁定 §2 |
| — | **§1〜§4 の技術内容は1文字も変えていない** | **承認された内容を、渡す前に書き換えない** |

---

## 0-1. ★完了条件（3件。満たさなければ受領されない）
| # | 条件 | 出典 |
|---|---|---|
| **1** | **`event_trace.jsonl` を `LEDGER_REGISTRY` に登記する**（目的／作成プログラム／書き手／読み手）。**★登記が無ければ受領しない。「どこにも登記されていない運用台帳」を1つも増やさない** | 本文書 §1-4 / MGR 承認 §3-1 |
| **2** | **合流点④ fail-open の4条件を全部満たす**（`dropped_before: N` を次に成功した `emit` が載せる／書けなければ `stderr`／`G-38` 登録／**SPEC 本文 §2-5 への明記**）。**★注記ではない。完了条件である** | 本文書 §2-5 / MGR 承認 §3-2 |
| **3** | **受入⑦(c) の全走査を省かない**（合流点を通らずに書ける関数が無いことを、出た行を1つ残らず4分類して示す）。**★これが本 build の合否である。省いたら不合格** | 本文書 §3-3 / MGR 承認 §3-3 |

## 0-2. ★`ds` に置いたのは妥協である（`G-40`・実装前に読むこと）
> **概念的な持ち主は EGL である**（EGL は既に「実行の証拠」を持つ）。
> **採れないのは `ds → egl` の辺が実行順に逆行するからである。**
> **∴ ★良い置き場所を選んだのではない。辺の向きの制約に負けた結果である。**
> **∴ ★いま動かさない。** 動かすなら別の裁定である。
> **★実装者へ: 「なぜ対話記録の repo に実行トレースが在るのか」の答えはここに在る。** **再導出しないこと。**

---

## 0. 合否の1行
> **Taka:「入口ごとの注意事項で防ぐのではなく、★どの入口から入っても同じ記録機構を必ず通る構造に直すべきです。」**

**★設計: 入口を数えて塞がない。「全員が必ず通る関数」の内側に置く。** 入口は増える（実測12）。**合流点は5つで固定である。**

---

## 1. ★置き場所の確定（裁定 B の4条件）

### 1-1. 依存方向の実測【監査:CC-α】
```
再現: 5repo × 5repo の総当たりで `from <pkg>` / `import <pkg>` を計数
      （test_ / regression / experiments / structure / probe / tools / docs を除外）

  dw     -> twoder : 3 箇所   ← ★既存の逆転（下位が上位を import している）
  twoder -> ds     : 8
  twoder -> rri    : 10
  twoder -> egl    : 13
  twoder -> dw     : 25
  （★ds / rri / egl から他repo への import は 0 = 3つとも葉である）
```
**★既存の逆転の実体**（`G-39` として登録する。本 build では直さない）:
```
dev-workcell/dw/dispatch.py:23    from twoder import execution_economy as EE
dev-workcell/dw/adapters.py:139   from twoder import runtime_supervisor as RS
dev-workcell/dw/adjudicator.py:180 from twoder import failure_resource_precheck as FRP
```

### 1-2. ★測っても決まらなかったこと（先に書く）
> **`ds` / `rri` / `egl` は互いを1つも import していない。**
> **∴ 「3つの葉のうちどれが下位か」は、★import では決まらない。** **測定では settle できない。**
> **∴ 別の測れる基準を使った**（下記）。**★「感覚で選んだ」ではないことを明示する。**

**使った基準 = 実行順（`twoder/submit.py` の段構成。コードで確認できる）**
```
段1   DS   phase0.record_utterance          ← ★最初
段3a  EGL  answer_question
段3b-e RRI  classify_request_type / intent_strategy
段4   EGL/DW  forward_admission / create_task
```
> **∴ `ds` は実行順で最初である。** **∴ `ds` に置けば、新しい辺は★すべて「後の段 → 前の段」になる。**
> **∴ 逆転を作らない。**

### 1-3. ★確定
| | |
|---|---|
| **モジュール** | **`/home/takasan/ds/ds/etrace.py`**（**版管理下**＝条件1 ✓） |
| **記録先** | **`/home/takasan/ds/data/event_trace.jsonl`**（`ds/.gitignore` が `data/` を無視＝条件4 ✓） |
| **新 repo** | **作らない**（`ds` は既存 repo＝条件3 ✓） |
| **逆転** | **作らない**（§1-2＝条件2 ✓） |

**★4条件すべてを満たす。**

**★新しく生じる辺（3本。すべて後→前）**: `rri → ds` / `egl → ds` / `dw → ds`
**★`twoder → ds` は既存**（8箇所）。

**★対案と、採らなかった理由**（選定で結論を作っていないことを示す）:
| 案 | 採らない理由 |
|---|---|
| `egl/` に置く | **EGL は「実行の証拠」を既に持っており概念的には最も自然**（`EXECUTION_EVIDENCE.jsonl`）。**★しかし `ds → egl` の辺が生じ、実行順で「前の段 → 後の段」になる＝条件2 に触れる** |
| `twoder/` に置く | **葉3つが最上位を import する＝明確な逆転。** 条件2 に触れる |
| 新 `etrace/` | **6つ目の repo または版管理外。** 条件1 または3 に触れる |

**★MGR への1点**: **`ds` はもともと対話記録の repo であり、実行トレースの持ち主として自然ではない。**
**条件2 を満たす唯一の案が `ds` だったという理由で選んでいる。** **概念的な持ち主を変えたいなら、それは裁定事項である。**

### 1-4. ★台帳登記（孤児にしない）
- **`event_trace.jsonl` を `LEDGER_REGISTRY` に登記すること**（目的／作成プログラム／書き手／読み手）。
- **★これを省くと「どこにも登記されていない運用台帳」が1つ増える。** **本日の型を繰り返さない。**

---

## 2. 実装

### 2-1. `ds/ds/etrace.py`（新規・依存ゼロ）
```python
# 使ってよい import: json, os, sys, hashlib, uuid, threading, datetime, pathlib のみ。
# ★他 repo を1つも import しない（葉であり続けるため）。

def open_run(raw_input, ts, entry) -> str
    # 合流点⓪でのみ呼ぶ。run_id = "RUN-" + sha1(raw_input + ts + uuid4().hex)[:12]
    # ★内容から導かない — 同一文面の2回目を別物として区別できることが G-31 の要求だから。

def emit(component, function, inputs, outputs, result, error=None,
         run_id=None, handed_to=None, trace_id=None, task_id=None) -> str | None
    # 1行 append。返りは event_id（失敗時 None）。

def span(component, function, inputs)      # context manager。親子スタックを積む。

def current_run_id() -> str | None         # thread-local
```

**保存する項目（12項目・過不足なく）**
| キー | 値 |
|---|---|
| `event_id` | `"EV-" + run_id[4:] + "-%04d" % seq`（**★順序が id に入る**） |
| `parent_event_id` | §2-2 |
| `run_id` | `open_run` が発行（**Session ID 相当**） |
| `trace_id` | **既存の `provenance.trace_id`。判明時に渡す。★既存の値を1つも変えない** |
| `task_id` | 判明時のみ。**推測しない** |
| `ts` | 実 wall-clock ISO（`datetime.now().isoformat()`） |
| `component` | `SUBMIT` / `DS` / `RRI` / `EGL` / `DW` |
| `function` | 関数名 |
| `inputs` / `outputs` | **実値。上限 2000 文字で切り、切ったら `"truncated": true` を併記** |
| `handed_to` | **分かる場合のみ。★不明は `null`。推測して埋めない** |
| `result` | `"OK"` / `"ERROR"` |
| `error` | `{"type": …, "msg": …}` または `null` |

### 2-2. ★親子の決め方（記録関数のみが決める）
```
parent_event_id =
  ① thread-local スタックの頂上（開いている span が在れば）
  ② 無ければ、同一 run_id の最後の event の event_id
  ③ 無ければ null（root）
```
- **★呼び手は親を渡さない。** **`emit` の引数に `parent_event_id` を置かない**（渡せなくする）。
- **★②が要る理由**: CLI で投入し後から webui が DW を進めると**プロセスが違いスタックが繋がらない**。

### 2-3. ★合流点5つ（入口ではない）
| # | 合流点 | 失敗時 | 記録 |
|---|---|---|---|
| **⓪** | `twoder/submit.py::submit()` **先頭** | **fail-closed** | `open_run` + `ENTRY` |
| **①** | `ds/ds/phase0.py::record_utterance` / `record_dialogue_event` | **fail-closed** | `DS_WRITE` |
| **②** | `rri/rri/intent_record.py` の append（`:53` の `open("a")`） | **fail-closed** | `RRI_WRITE` |
| **③** | `egl/egl/de_admission.py`（自ら "The ONLY sanctioned writer" と宣言） | **fail-closed** | `EGL_WRITE` |
| **④** | `dev-workcell/dw/workcell.py::_append_event`（`_events_path()` を書きで使う唯一の箇所） | **★fail-open** | `DW_WRITE` |

### 2-4. ★fail-closed の形（裁定 A / ⓪①②③）
> **「本処理を止める」ではなく「★記録できないことを本処理の結果として返す」。**
```
emit が失敗 → submit() は既存の _fail(system="ETRACE", what="…") を呼び、TRACE を返して停止。
★新しい概念を作らない。既存の boundary_failures と同じ形。
```

### 2-5. ★fail-open の形（裁定 A / ④）— **穴を見える場所に置く**
> **★合流点④（DW `_append_event`）は fail-open である。**
> **理由: worker 実行中に止めると成果物が失われる**（Build 18 で成果物が消える経路を実際に見た）。

**★条件（これが無ければ実装完了としない）:**
1. **失敗時はカウンタを1増やす**（プロセス内）。**次に成功した `emit` が `"dropped_before": N` を必ず載せる。**
2. **カウンタも書けない場合は `stderr` に1行出す。**
3. **`G-38`「合流点④は fail-open。取りこぼしが起きうる」を Gap Register に登録する**（**本文書提出と同時に登録済**）。
4. **★本 SPEC 本文（本節）に書いてあること自体が条件である。** **後から読む者が穴の在処を1行で知れるように。**

### 2-6. ★変えてはいけないもの（禁止②の実行）
- **既存関数の引数・返り値・保存内容を1つも変えない。** 記録は**内側の副作用**。
- **DW の `phase` / `role` / `state` / `PROCESS_EVENT_KINDS` を1つも増やさない。**
- **`record_utterance` の返り値に `event_id` を足さない。**
- **`provenance.trace_id` の値を変えない。**
- **∴ 既存の読み手（`derive_state` / `ids.resolve` / `/api/*`）は1行も変えない。**

### 2-7. ★やらないこと
1. 新しい RRI 判断ロジックを作らない。4軸・7戦略・EGL 仕様・DW 仕様を書き換えない。
2. **第二段階を先取りしない**（関数内部の全分岐・「呼ばれなかった処理」は範囲外。裁定②が Taka に上がっている最中）。
3. **記録先を2つ作らない**（「CLI 用」「webui 用」を作った時点で失敗）。
4. **入口に注意書きを足すことを解にしない。**
5. `rthread_events.jsonl` を復活させない（`G-33`）。
6. **`dw → twoder` の既存逆転を直さない**（`G-39`。範囲外）。

---

## 3. 受入（Taka 6件 + MGR ⑦）

### 3-1. 投入（★MGR 承認済の文面。1文字も変えない）
```
2DER の実行イベント記録について、DS・RRI・EGL・DW のどこまで進んだかを
1件の依頼として追跡できるようにしたい。現状で追跡が途切れる箇所を、
記録に残っている事実だけで挙げてください。
```
> **★投入順: CLI を先に、webui を後に**（裁定）。**★2回だけ。** **文面を変えない。**

### 3-2. 判定表
| # | 条件 | 示し方 |
|---|---|---|
| ① | CLI / webui 各1件 | 実行ログ |
| ② | 両方とも同じ形式で残る | **2つの `run_id` の event 列を貼る** |
| ③ | `trace_id` で DS→RRI→EGL→DW が追える | **★CLI 側（1件目）で満たす。** join 結果を貼る |
| ④ | **既存の判断結果・返り値・保存内容が不変** | **★投入前に `/api/claude_packet` と `/api/state`（既存 task）を保存 → 実装後に再取得 → 差分ゼロを示す。** **加えて `twoder/regression/` を実行し、失敗が `G-13` の既知3件から★増えていないことを示す** |
| ⑤ | 記録失敗時の扱いを明示 | §2-4 / §2-5 |
| ⑥ | 実データを貼る | 上記すべて実値 |
| **⑦** | **記録を通さずに投入できる経路が無い** | **§3-3（★省略禁止。本 build の合否）** |

### 3-3. ★⑦ の示し方（3つ。入口の列挙では示さない）
```
(a) 合流点が唯一の書き手であることの再実測:
    grep -rn "_events_path" --include=*.py dev-workcell/dw
    grep -rn "open(\"a\")\|open('a')" --include=*.py rri/rri ds/ds egl/egl

(b) §1-1 の12入口それぞれが、合流点⓪〜④のどれを通るかの表（12行。空欄を作らない）

(c) ★全走査 — 合流点を通らずに DS/RRI/EGL/DW の台帳に書ける関数が無いこと:
    grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(|\.write\(" --include=*.py \
      ds/ds rri/rri egl/egl dev-workcell/dw twoder \
      | grep -v "test_\|/regression/\|/experiments/\|/structure/\|/probe/"
    → 出た行を1つ残らず分類する:
       [合流点である] / [合流点の内側から呼ばれる] / [台帳を書かない(一時ファイル等)] / [★抜け道]
    → ★「抜け道」が1件でも在れば、その時点で不合格。件数と場所を報告する。
```
> **★(c) で「抜け道 0」と書くには、全行を分類した表を添えること。** **「見た範囲で無い」は不可**（`G-32`）。

### 3-4. ★事前に固定する予測（決定論で分かる分だけ）
> **同一文面なので `task_id = sha1(raw_input)[:8]` は2回とも同じ。**
> **∴ 2件目（webui）の `create_task` は `already exists` で例外になり、`submit.py:434` の `except: pass` が握り潰す。**
> **∴ ★2件目は DW task を作らない。これは不具合ではなく設計どおりである。**
> **∴ 受入③は1件目（CLI）で満たし、2件目は「DW task を作らない」ことを実測で示す。**
> **★後から「失敗した」と誤読しないため、実行前に固定する。**

### 3-5. ★実行前の必須手順（見落としやすいもの）
1. **★webui を再起動すること。** **現在のプロセスは13時間前起動でソースより古い**（状況表）。**再起動しないと実装が作用しない**（本日 Build 10 と同型）。
2. **★①の投入前に、④のための「実装前スナップショット」を取ること。** 順序を逆にすると比較対象が消える。

---

## 4. ★未確認（「全部見た」と書かない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **合流点②③（RRI/EGL）の唯一性は `grep` 1回で見ている** | **IMPL / 受入⑦(a)(c) で確定する** |
| 2 | **`egl/autonomy/*` と `twoder/probe/*` が独自に台帳を書いていないか** | **IMPL / 受入⑦(c) の全走査に含める（★除外しない）** |
| 3 | **12入口のうち③④⑤⑥は実行を見ていない**（`grep` のみ） | IMPL / 受入⑦(b) |
| 4 | **`ds` が実行トレースの持ち主として妥当か**（条件2 を満たす唯一案という理由で選んだ） | **MGR / 裁定事項として残す** |
| 5 | `threads` が空になる原因（`G-37`） | 据え置き（MGR 裁定で本線外） |

---
*CC-α D-42 BUILD SPEC v1.0（実装源）。★置き場所を4条件で確定=依存方向を5×5総当たりで実測し（`dw→twoder` 3箇所＝**既存の逆転**を発見し `G-39` 登録／`twoder→ds,rri,egl,dw`／**ds・rri・egl は互いを1つも import しない＝3つとも葉**）、★「3つの葉のうちどれが下位か」は import では決まらず測定で settle できないので、別の測れる基準＝`submit.py` の実行順（段1 DS → 段3a EGL → 段3b-e RRI → 段4 DW）を使い、**`ds` が実行順で最初**ゆえ `ds` に置けば新しい辺（`rri→ds`/`egl→ds`/`dw→ds` の3本）がすべて「後の段→前の段」になり逆転を作らない ∴ **モジュール `ds/ds/etrace.py`（版管理下＝条件1）／記録先 `ds/data/event_trace.jsonl`（`data/` は gitignore 済＝条件4）／新 repo 作らず（条件3）／逆転なし（条件2）で4条件すべてを満たす**。対案は `egl/`（概念的には最も自然だが `ds→egl` が前→後になり条件2 に触れる）・`twoder/`（葉が最上位を import＝明確な逆転）・新 `etrace/`（6つ目の repo か版管理外）で、いずれも不可。★MGR への1点=`ds` は本来対話記録の repo で実行トレースの持ち主として自然ではなく、条件2 を満たす唯一案という理由で選んでいるので、概念的な持ち主を変えるなら裁定事項。★`event_trace.jsonl` を `LEDGER_REGISTRY` に登記すること（省くと未登記の運用台帳が1つ増える）。★実装=依存ゼロの `etrace.py`（`open_run`/`emit`/`span`/`current_run_id`）、`run_id` は `sha1(raw_input+ts+uuid4)` で**内容から導かない**（同一文面の2回目を区別できることが `G-31` の要求）、`event_id` は `run_id`+連番で順序を id に入れ、**親は記録関数のみが決め呼び手は渡せない（引数に置かない）**——①スタック頂上→②同一 `run_id` の最後の event→③null（②が要るのは CLI 投入を後から webui が進めるとプロセスが違いスタックが繋がらないため）。★合流点は入口でなく5つ（⓪`submit()` 先頭／①DS の2関数／②RRI `intent_record` の唯一の `open("a")`／③EGL `de_admission`／④DW `_append_event`）。⓪①②③は **fail-closed**＝「止める」でなく既存の `_fail(system,what)` で「記録できなかった」を結果として返す（新概念を作らない）。**④は fail-open**（worker 実行中に止めると成果物が失われる。Build 18 で実見）——ただし黙らせず、①失敗をカウントし次に成功した `emit` が `dropped_before: N` を必ず載せる ②それも書けなければ stderr に1行 ③`G-38` を登録（提出と同時に登録済）④**本節に書いてあること自体が条件**（後から読む者が穴の在処を1行で知れるように）。★変えてはいけないもの=既存関数の引数・返り値・保存内容／DW の `phase`/`role`/`state`/`PROCESS_EVENT_KINDS`／`record_utterance` の返り値／`provenance.trace_id` の値 ∴ 既存の読み手は1行も変えない。★受入=承認済の文面を1文字も変えず **CLI を先に webui を後に2回だけ**投入し、③は CLI 側で満たす。④は投入前に `/api/claude_packet`・`/api/state` のスナップショットを取り差分ゼロと `twoder/regression/` の失敗が `G-13` の既知3件から増えないことで示す。**⑦は入口の列挙では示さず** (a)合流点が唯一の書き手であることの再実測 (b)12入口がどの合流点を通るかの12行表（空欄を作らない） (c)**全走査**——`open(a|w)`/`write_text`/`write` を5repo で洗い出し**出た行を1つ残らず[合流点]/[合流点の内側]/[台帳を書かない]/[抜け道]に分類**し、抜け道が1件でも在れば不合格。「見た範囲で無い」は不可（`G-32`）。★事前に固定する予測=同一文面ゆえ2件目の `create_task` は `already exists` で握り潰され **2件目は DW task を作らない。不具合でなく設計どおり**——実行前に固定する。★実行前の必須手順=webui を再起動すること（現行プロセスは13時間前起動でソースより古く、再起動しないと実装が作用しない＝本日 Build 10 と同型）／④のスナップショットを投入前に取ること（順序を逆にすると比較対象が消える）。★未確認5件（合流点②③の唯一性は grep 1回のみ／`egl/autonomy`・`twoder/probe` を全走査に含め除外しない／12入口のうち4つは実行未確認／**`ds` が持ち主として妥当かは MGR 裁定事項**／`G-37` 据え置き）。*
