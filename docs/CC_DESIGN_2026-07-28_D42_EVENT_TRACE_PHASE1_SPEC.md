# 設計/監査 → MGR（写: Taka / IMPL）: **D-42 Event Trace 第一段階 SPEC — ★入口を塞がない。「必ず通る関数」に置く**

- `BUILD_ROLE: 参照`（**本文書は SPEC。★実装源ではない。まだ IMPL へ渡さない — 裁定 A/B と依頼文の承認が先**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC(草案)
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **正典**: `EVENT_TRACE_PHASE1_WORK_ORDER_v1_0.md` / **受領**: `CC_MGR_2026-07-28_D42_EVENT_TRACE_PHASE1_SPEC_REQUEST.md`

---

## 0. ★合否の1行に対する設計の答え
> **Taka: 「入口ごとの注意事項で防ぐのではなく、どの入口から入っても同じ記録機構を必ず通る構造に直すべきです。」**

**★設計の答え: 入口を数えて塞がない。「全員が必ず通る関数」の内側に置く。**
> **入口は増える。** **合流点は増えない。**
> **∴ 記録関数を★合流点の内側に置けば、「記録しない入口」は★作れない。** **新しい入口を後から足しても、自動的に記録される。**

**★これが「注意書きで防ぐ」との違いである。** **注意書きは入口の数だけ必要になる。合流点は4つで固定である。**

---

## 1. 先に解いた3つ（実物で）

### 1-1. Q1 — ★入口は「CLI と webui の2つ」ではない。実測で少なくとも12
```
再現: grep -rn "SUB.submit|S.submit|submit\.submit" --include=*.py 全5repo | grep -v test
再現: grep -rn "create_task\(" --include=*.py 全5repo | grep -v "def create_task" | grep -v test
再現: grep -rn "record_utterance\(" --include=*.py 全5repo | grep -v "def record_utterance" | grep -v test
```
| 層 | 入口 | 場所 |
|---|---|---|
| **submit() を呼ぶ** | ① CLI | `twoder/submit.py:485 __main__` |
| | ② webui | `twoder/webui.py:536` |
| | ③ **live_worker_runtime** | `twoder/live_worker_runtime.py:197`（**★機械が自分で投入する**） |
| | ④ **runtime_supervisor** | `twoder/runtime_supervisor.py:222`（同上） |
| | ⑤ counterfactual_runner | `twoder/counterfactual_runner.py:48` |
| | ⑥ codegen_run_fn | `twoder/tools/codegen_run_fn.py:70` |
| | ⑦ **EGL のラッパ** | `egl/structure/de_submit_route.py:46` |
| | ⑧ 同 | `egl/structure/s_de_route_equiv.py:107` |
| **submit() を通らず DW へ** | ⑨ | `twoder/select_and_create.py:80` |
| | ⑩ | `twoder/experiment_candidate.py:116` |
| | ⑪ | `dev-workcell/run_rri_task.py:167` / `run_esde_task.py:167` |
| **submit() を通らず DS へ** | ⑫ | `twoder/intervention.py:76` / `twoder/authority.py:125` |

> **★∴ 「CLI と webui に記録を足す」は、10個の抜け道を残す。**
> **★∴ 入口を列挙して塞ぐ方式は、この時点で失敗である。** **MGR の Q1 の懸念は当たっていた。**

### 1-2. Q2 — ★DW `events.jsonl` は記録先にできない（裁定①は成り立たない）
**MGR の指摘（`task_id` 前の段階が入らない）より★強い理由が在る:**
```
再現: sed -n '319,322p' dev-workcell/dw/workcell.py

def create_task(task_id, project_id, goal, knowledge_packet, ts, manager_identity, contract=None):
    if _read_events(task_id):
        raise WorkflowViolation(f"task {task_id} already exists")
```
> **★`task_id` を鍵にしたイベントを1件でも先に書くと、`create_task` は★永久に拒否する。**
> **∴ 受付・DS登録・RRI開始を `events.jsonl` に書いた瞬間、その依頼は★DW に入れなくなる。**
> **∴ これは「不便」ではなく★本番停止である。** **回避するには `create_task` を書き換えることになり、禁止①「DW 仕様を書き換えない」に触れる。**

**★副次的にもう1つ:** `derive_state` は未知の phase を無視するため、`CREATE` が無いまま `ids.resolve("TASK-…")` が `state=CREATED` を返す。**存在しない task が一覧に現れる**＝禁止②「既存の保存内容を変えない」に触れる。

> **∴ 結論: 既存では足りない。★足りないのは「`task_id` が決まる前の段階を保持できる器」と「`submit()` を通らない入口も通る位置」の2つである。**
> **∴ 共通の Event Trace 記録先を★1つだけ新設する必要が在る**（裁定 B）。

**★ただし DW `events.jsonl` を捨てない。** **provenance は既にそこに在り（`【実】`）、`trace_id` で join する**（§2-5）。**二重記録にしない。**

### 1-3. Q3 — ★親子は設計で決める（実装に委ねない）
| 項目 | **決め方（決定論。LLM を使わない）** |
|---|---|
| **`run_id`** | **合流点⓪で1回だけ発行**。`"RUN-" + sha1(raw_input + ts + uuid4().hex)[:12]`。**★内容から導かない**——同じ文面の2回目を別物として区別できることが `G-31` の要求だから |
| **`event_id`** | `"EV-" + run_id[4:] + "-%04d" % seq`。`seq` は run 内の単調増加。**★順序が id に入る** |
| **`親 event_id`** | **★次の順で決める（上から）**: ①同一スレッドの「開いている event」の最内（thread-local スタックの頂上）／②スタックが空なら**同一 `run_id` の最後の event**／③それも無ければ `null`（root） |
| **決める主体** | **★記録関数のみ。** 呼び手は親を渡さない。**渡せないようにする**（引数に持たない） |

**★②が要る理由**: **CLI で投入し、後から webui が DW を進める場合、プロセスが違うのでスタックが繋がらない。** **`run_id` を記録に持たせ、そこから引く。**

---

## 2. 設計

### 2-1. 記録機構は1つ。関数も1つ
```
etrace.emit(component, function, inputs, outputs, result, error=None, run_id=None) -> event_id
etrace.open_run(raw_input, ts, entry) -> run_id      # 合流点⓪でのみ呼ぶ
etrace.span(component, function, inputs)             # context manager（親子スタックを積む）
```
- **★依存ゼロ**（`json` / `os` / `pathlib` / `threading` / `hashlib` / `uuid` のみ）。**どの層からも import できるようにするため。**
- **★記録先は1ファイル。** **「CLI 用」「webui 用」を作らない**（禁止④）。

### 2-2. ★置く場所 = 合流点4つ（入口ではない）
| # | 合流点 | 根拠（★唯一性を実測） | 何を記録するか |
|---|---|---|---|
| **⓪** | **`twoder/submit.py::submit()` の先頭** | 入口①〜⑧が★全てここへ合流する（§1-1） | `open_run` + `ENTRY` event |
| **①** | **`ds/ds/phase0.py::record_utterance` / `record_dialogue_event`** | **DS への書き込みはこの2関数のみ**（`_read`/`_append` は内部） | `DS_WRITE` event |
| **②** | **`rri/rri/intent_record.py` の append**（`:53` が唯一の `open("a")`） | **実測: `rri_records.jsonl` を開く箇所は1つ** | `RRI_WRITE` event |
| **③** | **`egl/egl/de_admission.py`** | **自ら「The ONLY sanctioned writer of `DESIGN_EVIDENCE_LEDGER.jsonl`」と宣言**（`:1`） | `EGL_WRITE` event |
| **④** | **`dev-workcell/dw/workcell.py::_append_event`** | **実測: `_events_path()` を書きで使うのは `:79` の1箇所のみ＝★events.jsonl の唯一の書き手** | `DW_WRITE` event |

> **★これで「入口の列挙」は受入条件でなくなる。** **⑦は「合流点が唯一であること」で示す**（§4）。
> **★新しい入口が後から増えても、合流点を通る限り記録される。** **これが Taka の1行への答えである。**

### 2-3. ★既存を変えない（禁止②）
- **既存の関数の★引数・返り値・保存内容を変えない。** 記録は**副作用として内側で行う**。
- **`_append_event` の payload に何も足さない。** **DW の `phase`/`role`/`state` を1つも増やさない。**
- **`record_utterance` の返り値に `event_id` を足さない。**
- **∴ 既存の読み手（`derive_state` / `ids.resolve` / `/api/*`）は★1行も変えなくてよい。** **これを実測で示す**（§4-④）。

### 2-4. 保存する12項目
| 項目 | 値 |
|---|---|
| `event_id` / `parent_event_id` | §1-3 |
| `run_id` | §1-3（**Session ID 相当**） |
| `trace_id` | **既存の `provenance.trace_id`。判明した時点で `LINK` event として記録する**（**★既存の値を変えない**） |
| `ts` | 実 wall-clock ISO |
| `component` / `function` | `DS`/`RRI`/`EGL`/`DW`/`SUBMIT` と関数名 |
| `inputs` / `outputs` | **★要約でなく実値。ただし上限 2000 文字で切り、切った事実を `truncated: true` で残す** |
| `handed_to` | 次に呼ぶ合流点の名（分かる場合のみ。**推測しない。不明は `null`**） |
| `result` | `OK` / `ERROR` |
| `error` | 例外の型と文字列（無ければ `null`） |

### 2-5. ★二重記録にしない
**DW `events.jsonl` は今のまま。** **Event Trace 側は `run_id` と `trace_id` と `task_id` を持つので、★join で1本になる。**
**∴ provenance を Event Trace に複写しない。** **`ds_input_id` も複写しない。**

---

## 3. ★裁定を仰ぐ（私は決めない）

### 3-A. 記録失敗時に本処理をどう扱うか
| | **fail-closed（記録できなければ本処理を止める）** | **fail-open（記録できなくても本処理を続ける）** |
|---|---|---|
| **根拠** | **RRI 正典 §3「根拠を保存せずに進めない」** | 記録は観測であって判断ではない |
| **帰結（良）** | **★「記録が無い実行」が構造上存在しなくなる。** Taka の1行を完全に満たす | 記録機構の不具合が本番を止めない |
| **帰結（悪）** | **★ディスク満杯・権限・ロック競合で 2DER 全体が止まる。** **記録機構が新しい単一障害点になる** | **★「記録の無い実行」が再び生まれる。** **今日直したはずの `G-36` が形を変えて戻る** |
| **実例（本日）** | — | **★`/tmp` に 1,000万ファイルが在った日が在る。** そのとき fail-closed なら 2DER は完全停止していた |

**【設計:CC-α】★私は fail-closed を推す。ただし条件付きで:**
> **「本処理を止める」ではなく「★記録できないことを本処理の結果として返す」。**
> **具体: `emit` が失敗したら `submit()` は `BOUNDARY_FAILURE` を返して停止する**（既存の `_fail(system, gap)` と同じ形＝**新しい概念を作らない**）。
> **∴ 落ちるのでなく、★「記録できなかった」が結果になる**（使用ガイド §0-3 と同じ形）。
> **★ただし合流点④（DW）は fail-closed にできない可能性が在る**——worker 実行中に止めると成果物が失われる。**ここは MGR の裁定を仰ぐ。**

### 3-B. 新しい記録先を作る必要が在るか
> **★在る。** **理由は §1-2**（`create_task:320` により `events.jsonl` を使うと本番が止まる）。
> **★作るのは1つだけ。** **Event Trace の記録先1ファイルと、それを書く関数1つ。**

**★置き場所（2案。私は①を推すが、5レポ topology に触れるので裁定を仰ぐ）:**
| | 案 | 利点 | 欠点 |
|---|---|---|---|
| **①** | **新ディレクトリ `/home/takasan/etrace/`**（`etrace.py` + `event_trace.jsonl`。**git repo にしない**） | **どの層からも対等に import できる。層の上下を作らない** | **★6つ目のディレクトリが増える。** `2der_repo_topology`（5レポ）の記憶に触れる |
| ② | `ds/etrace.py` に置く | 新ディレクトリを作らない | **★DW が DS に依存する**（現在 `dw` は `ds` を1つも import していない＝実測）。層の逆転 |

**★どちらも「新規の台帳」ではない**（Taka が「共通の Event Trace 記録先1つ」を明示的に開いた範囲）。**ついでに他を作らない。**

---

## 4. 受入（Taka の6件 + MGR の⑦）
| # | 条件 | **示し方** |
|---|---|---|
| ① | 同一内容を CLI と webui から各1件投入 | §5 の依頼文。**★MGR の承認後にのみ実行** |
| ② | 両方とも同じ形式で Event Trace が残る | 2つの `run_id` の event 列を貼る |
| ③ | DS→RRI→EGL→DW のどこまで進んだかが `trace_id` で追える | `trace_id` で join した1本の系列を貼る |
| ④ | **既存の判断結果・返り値・保存内容が変わっていない** | **★投入前に既存 task の `/api/claude_packet` と `/api/state` を保存し、実装後に再取得して★差分ゼロを示す。** **加えて `twoder/regression/` の既存テストを実行し、`G-13` の既知3失敗以外が増えていないことを示す** |
| ⑤ | 記録失敗時の扱いを明示 | §3-A の裁定を SPEC に反映して明記 |
| ⑥ | 実データを貼って証明 | 上記すべて実値 |
| **⑦** | **記録を通さずに投入できる経路が無い** | **★入口の列挙では示さない**（§1-1 のとおり増える）。**次の3つで示す**: (a) 合流点4つが★唯一の書き手であることの `grep` 実測を再掲 (b) §1-1 の12入口それぞれについて、合流点のどれを通るかを表にする (c) **★合流点を通らずに DS/RRI/EGL/DW に書ける関数が無いことを、`open("a")` / `write` の全走査で示す** |

### 4-1. ★事前に予測を固定する（決定論で分かる分だけ）
> **①で同一文面を2回投入すると、`task_id = sha1(raw_input)[:8]` は同じになる。**
> **∴ 2回目の `create_task` は `already exists` で例外になり、`submit.py:434` の `except: pass` が握り潰す。**
> **∴ ★2件目は DW task を作らない。** **これは不具合ではなく★設計どおりである。**
> **∴ 受入②「両方とも Event Trace が残る」は満たせるが、受入③「DW まで追える」は★2件目については満たせない。**
> **★これを先に書いておく。** **後から「失敗した」と誤読しないため。**
> **★もし2件目にも DW まで追わせたいなら、文面を変えるしかない**（`task_id` が内容の関数であるため）。**その判断は MGR に委ねる。**

---

## 5. ★投入する依頼文（実行前に MGR の承認を得る）
**Taka の①は「同一内容を CLI と webui から各1件」。** **∴ 文面は1つ。それを2回使う。**
```
2DER の実行イベント記録について、DS・RRI・EGL・DW のどこまで進んだかを
1件の依頼として追跡できるようにしたい。現状で追跡が途切れる箇所を、
記録に残っている事実だけで挙げてください。
```
| | |
|---|---|
| **なぜこれか** | **実運用に近い**（我々が実際にいま解いている問い）／**★新しい機能の実装を頼んでいない**（膨らませない）／**DE 登録依頼ではない**ので段1.5 の fast path に入らず**本線を通る** |
| **投入回数** | **★2回だけ**（CLI 1・webui 1）。**それ以上は投入しない** |
| **★承認が要る** | **MGR がこの文面を承認するまで投入しない** |

---

## 6. ★やらないこと（禁止の遵守）
1. **新しい RRI 判断ロジックを作らない。** **4軸・7戦略・EGL 仕様・DW 仕様を1つも書き換えない。**
2. **第二段階を先取りしない。** **関数内部の全分岐・「呼ばれなかった処理」は本 SPEC の範囲外**（裁定②が Taka に上がっている最中）。
3. **記録先を2つ作らない。**
4. **入口に注意書きを足すことを解にしない**（§0）。
5. **`rthread_events.jsonl` を復活させない**（`G-33`・範囲外）。
6. **本文書はまだ `BUILD_ROLE: ★実装源` にしていない。** **裁定 A/B と §5 の承認を得てから、実装源として出し直す。**

## 7. ★未確認（「全部見た」と書かない）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **§2-2 の合流点②③（RRI/EGL）の唯一性は `grep` 1回で見ている。** **④①のような複数箇所の突き合わせをしていない** | **CC-α / 受入⑦(c) の全走査時に確定する** |
| 2 | **`egl/autonomy/*` と `twoder/probe/*` が独自に記録していないか** | CC-α / 受入⑦(c) |
| 3 | **12入口のうち③④⑤⑥は実行を見ていない**（`grep` のみ） | CC-α / 受入⑦(b) |
| 4 | `threads` が空になる原因（`G-37`） | **【未確認・誰が=CC-α / いつ=Event Trace の SPEC 着手時】→ MGR 裁定で本線外。据え置き** |

---
*CC-α D-42 SPEC 草案。★合否の1行への答え=入口を数えて塞がず「全員が必ず通る関数」の内側に置く（入口は増えるが合流点は増えない ∴ 記録しない入口を作れなくなる。注意書きは入口の数だけ必要になるが合流点は4つで固定）。★Q1 実測=入口は CLI と webui の2つではなく**少なくとも12**（submit を呼ぶのが8: CLI/webui/live_worker_runtime/runtime_supervisor/counterfactual_runner/codegen_run_fn/EGL のラッパ2／submit を通らず DW へ3／submit を通らず DS へ1）∴「CLI と webui に足す」は10個の抜け道を残し、入口を列挙して塞ぐ方式はこの時点で失敗——MGR の懸念は当たっていた。★Q2=**DW `events.jsonl` は記録先にできない**。MGR の指摘より強い理由が在り、`create_task:320` が `if _read_events(task_id): raise` なので `task_id` 鍵のイベントを1件でも先に書くと **CREATE が永久に拒否され本番停止**する（回避には DW 書き換えが要り禁止①に触れる）。副次的に `derive_state` が未知 phase を無視するため存在しない task が一覧に出る（禁止②に触れる）∴ 足りないのは「`task_id` 前を保持できる器」と「`submit()` を通らない入口も通る位置」の2つで、共通記録先を1つだけ新設する必要が在る。ただし DW events は捨てず `trace_id` で join し二重記録しない。★Q3 親子=`run_id` は合流点⓪で1回だけ発行し `sha1(raw_input+ts+uuid4)` で**内容から導かない**（同一文面の2回目を区別できることが `G-31` の要求）、`event_id` は `run_id`+連番で順序を id に入れ、`親 event_id` は①thread-local スタック頂上→②同一 `run_id` の最後の event→③null の順で**記録関数のみが決め、呼び手は親を渡せない（引数に持たない）**。②が要るのは CLI 投入を後から webui が進める場合にプロセスが違ってスタックが繋がらないため。★設計=関数1つ・依存ゼロ・記録先1ファイル、置く場所は入口でなく**合流点4つ**（⓪`submit()` 先頭／①DS の `record_utterance`/`record_dialogue_event`／②RRI `intent_record` の唯一の `open("a")`／③EGL `de_admission`(自ら ONLY sanctioned writer と宣言)／④DW `_append_event`(`_events_path()` を書きで使う唯一の箇所)）——各唯一性は実測。既存の引数・返り値・保存内容を変えず記録は内側の副作用とし、既存の読み手は1行も変えなくてよい。★裁定 A=fail-closed と fail-open の両帰結を提示（fail-closed は「記録の無い実行」を構造上消せるが記録機構が単一障害点になり、本日 `/tmp` に1000万ファイルが在った日なら 2DER は完全停止していた／fail-open は `G-36` が形を変えて戻る）。CC-α は**条件付き fail-closed** を推す=「止める」でなく「記録できないことを結果として返す」（既存の `_fail(system, gap)` と同じ形で新概念を作らない）。ただし合流点④(DW)は worker 実行中に止めると成果物が失われるため裁定を仰ぐ。★裁定 B=新設は**要る**（理由は §1-2）。作るのは記録先1ファイルと関数1つだけ。置き場所は①新ディレクトリ `/home/takasan/etrace/`(git repo にしない・層の上下を作らない／★6つ目のディレクトリで 5レポ topology に触れる) と ②`ds/etrace.py`(新ディレクトリ不要／**DW が DS に依存する**——現在 `dw` は `ds` を1つも import していないので層の逆転) の2案で①を推すが裁定を仰ぐ。★受入は Taka の6件＋⑦で、⑦は入口の列挙では示さず (a)合流点4つが唯一の書き手であることの実測 (b)12入口がどの合流点を通るかの表 (c)**合流点を通らずに書ける関数が無いことを `open("a")`/`write` の全走査で示す**。④は投入前後の `/api/claude_packet`・`/api/state` の差分ゼロと既存テストの失敗が `G-13` の既知3件から増えないことで示す。★事前に予測を固定=同一文面2回投入で `task_id` は同じになり2件目の `create_task` は `already exists` で `except: pass` に握り潰される ∴ **2件目は DW task を作らない。これは不具合でなく設計どおり**で、受入③は2件目については満たせない——後から「失敗した」と誤読しないため先に書く。2件目も DW まで追わせるなら文面を変えるしかなく、その判断は MGR に委ねる。★投入する依頼文を本文書に明記し（実運用に近く・新機能の実装を頼まず・DE 登録依頼でないので本線を通る）、**MGR が承認するまで投入しない・2回だけ**。★本文書はまだ実装源にしておらず、裁定 A/B と依頼文の承認を得てから出し直す。★未確認4件を明記（合流点②③の唯一性は grep 1回のみ／`egl/autonomy`・`twoder/probe` の独自記録／12入口のうち4つは実行を見ていない／`G-37` は据え置き）。*
