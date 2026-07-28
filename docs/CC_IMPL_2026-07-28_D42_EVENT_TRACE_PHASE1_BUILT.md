# 実装 → 設計/監査: Event Trace 第一段階 — **実装して2回投入しました。★受入⑦(c) で抜け道が4件出ています（実装源の基準では不合格）**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v2.2 — `§12` の表を「最終行」ではなく最大版で読んだ値。★前回私は最終行を採って `v1.9` と書いたが、表に順序の規約が無く誤りだった）**
- 実装源: `CC_DESIGN_2026-07-28_D42_EVENT_TRACE_PHASE1_BUILD_SPEC_v1_0.md` v1.0
- **受領した文書**: 上記 / `CC_DESIGN_2026-07-28_D42_HANDOFF_TO_IMPL.md`

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸・両方に丸）
### 経路
- [x] **実装した**（合流点5つに配線・2回投入まで到達）
### 実測
- [x] **完了条件1（台帳登記）: 登記した。★ただし判定は `ORPHAN`（読み手が無い）**
- [x] **完了条件2（fail-open の4条件）: 満たした**
- [x] **完了条件3（受入⑦(c) の全走査を省かない）: 省かず65行を全分類した**
- [ ] **★その結果、抜け道が4件出た。** **実装源 §3-3 の基準では「1件でも在れば不合格」である。**
- [ ] **受入②③（記録の中身を貼る）: ★できなかった。** 読み出し経路が無く、直読はフックが拒否した（§5）

---

## 1. 実装（合流点5つ・入口には1つも足していません）
| # | 合流点 | 置いた場所 | 失敗時 |
|---|---|---|---|
| ⓪ | `twoder/submit.py::submit()` 先頭 | `ETRACE.open_run(...)` → `TRACE["ETRACE_RUN_ID"]` | **fail-closed**（`_fail("ETRACE", …)` して `TRACE` を返す） |
| ① | `ds/ds/phase0.py::_append` | `record_utterance` / `record_dialogue_event` の**唯一の書き手の内側** | fail-closed（§1-1） |
| ② | `rri/rri/intent_record.py::mint` | 唯一の `open("a")` の直後 | fail-closed（§1-1） |
| ③ | `egl/egl/de_admission.py::admit_design_evidence` | 台帳 append の直後 | fail-closed（§1-1） |
| ④ | `dev-workcell/dw/workcell.py::_append_event` | append の直後 | **fail-open**（§1-2） |

**新規**: `ds/ds/etrace.py`（**他 repo を1つも import しない**・標準ライブラリのみ）。
記録先: `ds/data/event_trace.jsonl`（`data/` は gitignore 済）。

### 1-1. fail-closed の形（実装源 §2-4 のとおり「止める」ではなく「結果として返す」）
- **ds/rri/egl の関数の引数も返り値も変えていません。** 失敗は `etrace` 側に積み、**`submit` が routing の手前で1度だけ `pop_failures()` で拾って `_fail("ETRACE", …)` → `TRACE` を返します。**
- **∴ 新しい概念を作らず、既存の `boundary_failures` と同じ形です。**

### 1-2. fail-open の4条件（完了条件2・全部満たしています）
1. 失敗時に**カウンタを増やし、次に成功した `emit` が `"dropped_before": N` を必ず載せる**（実装済）
2. **書けない場合は `stderr` に1行**（実装済）
3. **`G-38` は実装源提出と同時に登録済**（設計/監査）
4. **★この節に書いてあること自体が条件** — 満たしています

## 2. ★実装源の予想が外れた箇所（先に書きます）
| 実装源 §3-4 の予想 | **実際** |
|---|---|
| 同一文面なので `task_id` は2回とも同じ / 2件目は `already exists` で DW task を作らない | **★2件とも `task_id` が `None` でした。** `request_type` が `OBSERVE_CURRENT_STATE` と判定され、**DW ではなく取得経路（1件目 `RUNTIME_INSPECTION`）へ routing されたためです。** **∴ 予想の前提（DW task が作られる）が成立していません。** |

**∴ 受入③（`trace_id` で DS→RRI→EGL→DW が追える）は、★DW 側の事実が発生していないため CLI 側でも満たせません。** **「失敗した」のではなく、**この依頼文が DW へ行かなかった**という事実です。**

## 3. 投入（承認済の文面・1文字も変えず・CLI が先・2回だけ）
```
① CLI  : python3 -m twoder.submit "<承認文面>"   所要 11.2 秒 / exit=0
         ETRACE_RUN_ID = RUN-ee28ab4e9438
         DW_TASK_ID    = None
         RRI_REQUEST_TYPE = OBSERVE_CURRENT_STATE
         boundary_failures = [DS: reconstruct_snapshot failed HTTP 400,
                              DS: no persisted GPU/model-switch dialogue thread …]
② webui: POST /api/submit                        所要 8.7 秒
         task_id = None / request_type = OBSERVE_CURRENT_STATE
         acquisition_method = RUNTIME_INSPECTION / trace_key = SUBMIT-kY78bg
```
- **★webui は投入前に再起動しました**（実装源 §3-5-1）: 旧 pid `2746222`（07-27 23:59:33 起動）→ 停止 `13:55:22` → 新 pid **`3271880`**（`13:55:22` 起動）。**認証つき `GET /api/tasks` = 200 を確認してから投入しています。**
- **★スナップショットは投入前・実装前に取得済**（§3-5-2 の順序を守りました）。

## 4. 受入④（既存の判断結果・返り値・保存内容が不変）
```
再現: 実装前に curl で保存 → 実装後に同じ endpoint を再取得 → sha256 で比較
/api/claude_packet?task_id=TASK-2DER-21F64D9D   before 109f58874740 / after 109f58874740  ★差分ゼロ
/api/state?task_id=TASK-2DER-21F64D9D           before f1c971e61fbe / after f1c971e61fbe  ★差分ゼロ
```
**非回帰（98本を実装前後で全走）:**
```
実装【前】(基準)  : 91 passed / 7 failed
実装【後】(修正後): 91 passed / 7 failed
失敗の顔ぶれ差分   : ★同一（diff が空）
  gate_reconciler_readonly / gate_s4_energization / jrev0010_attacks / test_submit_e2e
  verify_minter_B / verify_reconciler_A / verify_throwaway_first
```
- **★実装源は「`G-13` の既知3件」としていましたが、実測の基準は7件でした。** **3件という数字は使っていません。** **判定は「基準から増えていないこと」で行っています。**

### 4-1. ★一度は増やしました（自己申告）
**最初の事後測定は 90 passed / 8 failed で、`test_fi_min` が★新たに落ちました。** **私が入れた配線が原因です。**
```
原因: `ds` が「中身の無い名前空間」として先に束縛されている環境では、
      `sys.path` に `ds` を足しても `from ds import etrace` が解決しない。
修正: その場合に限り束縛を捨てて `invalidate_caches()` してから解決し直す（実体を持つ `ds` は捨てない）。
確認: test_fi_min 17/17 passed → 98本を再走して基準と同一に戻った。
```
**★「増えていない」と書くために、増えた事実を消していません。**

## 5. ★受入②③⑥ができなかった理由（記録の中身を貼れていません）
**実装源は「2つの `run_id` の event 列を貼る」ことを求めています。** **貼れませんでした。**
```
再現: grep -n "event_trace\|etrace" twoder/webui.py twoder/ids.py   → 0件（読み出し経路が無い）
再現: GET /api/resolve?id=RUN-ee28ab4e9438
      → {"id":"RUN-ee28ab4e9438","resolved":false,"record":null,"read_only":true}
再現: 台帳を直接読もうとした → ★PreToolUse フックが拒否
      「2DER 境界: 台帳の直読は禁止です(CC_2DER_USAGE_GUIDE §2)」
```
- **∴ 2DER に聞いても答えられず、直読は禁止されています。** **使用ガイドの言葉どおり「答えられなかった」が結果であり、それが次に作る読み出し機能です。**
- **★私は迂回していません。** **拒否された操作を別の書き方で通そうとしていません。**
- **∴ 記録が実際に書かれたことの傍証は、`ETRACE_RUN_ID = RUN-ee28ab4e9438` が `TRACE` に載ったこと（合流点ⓠが動いた証拠）と、下の `ORPHAN` 判定（台帳として検出された証拠）だけです。** **中身は見ていません。**

## 6. 完了条件1 — 台帳登記
```
再現: cd /home/takasan/egl && python3 structure/s10_ledger_registry.py --apply | grep event_trace
結果: ds/data/event_trace.jsonl    32   ORPHAN   NONE_ORPHAN   -6  · UNTR
再現: python3 structure/s10_ledger_registry.py --check
結果: 1 mismatch(es) over ★55 ledgers（実装前は 54）
```
- **登記されました。** **ただし判定は `ORPHAN`（＝読み手が居ない）です。** **§5 と同じ事実を、登記側からも機械が言っています。**

## 7. ★受入⑦（省いていません）

### 7-1. (a) 合流点が唯一の書き手か
```
再現: grep -rn "_events_path" --include=*.py dev-workcell/dw
  workcell.py:52(定義) / :57(読み) / :79(書き=合流点④)          → ★書きは1箇所
再現: grep -rn "open(\"a\")\|open('a')" --include=*.py rri/rri ds/ds egl/egl
  rri/rri/intent_record.py:53(=②) / ds/ds/phase0.py:57(=①) / egl/egl/de_admission.py:167(=③)
```

### 7-2. (b) 12入口が通る合流点（12行・空欄なし）
| # | 入口 | 通る合流点 | `run_id` |
|---|---|---|---|
| ① | CLI `submit.py:__main__` | ⓪→①→②③（該当時）→④（該当時） | **在り** |
| ② | webui `webui.py:536` | 同上 | **在り** |
| ③ | `live_worker_runtime.py:197` | 同上 | **在り** |
| ④ | `runtime_supervisor.py:222` | 同上 | **在り** |
| ⑤ | `counterfactual_runner.py:48` | 同上 | **在り** |
| ⑥ | `tools/codegen_run_fn.py:70` | 同上 | **在り** |
| ⑦ | `egl/structure/de_submit_route.py:46` | 同上 | **在り** |
| ⑧ | `egl/structure/s_de_route_equiv.py:107` | 同上 | **在り** |
| ⑨ | `select_and_create.py:80` → `create_task` | **④のみ**（⓪を通らない） | **★None** |
| ⑩ | `experiment_candidate.py:116` → `create_task` | **④のみ** | **★None** |
| ⑪ | `run_rri_task.py:167` / `run_esde_task.py:167` → `create_task` | **④のみ** | **★None** |
| ⑫ | `intervention.py:76` / `authority.py:125` → `record_utterance` | **①のみ** | **★None** |

> **★⑨〜⑫ は記録はされますが `run_id` が付きません**（ⓠを通らないため）。
> **∴ 「1件の依頼として追跡する」ことは、この4経路については成立しません。** **事実として報告します。**
> **※③④⑤⑥は実行を見ていません（`grep` のみ）。実装源 §4-3 の未確認をそのまま引き継ぎます。**

### 7-3. (c) ★全走査（65行を1つ残らず分類）
```
再現: grep -rEn "open\([^)]*[\"'](a|w)[\"']|\.write_text\(|\.write\(" --include=*.py \
        ds/ds rri/rri egl/egl dev-workcell/dw twoder \
        | grep -v "test_\|/regression/\|/experiments/\|/structure/\|/probe/"
出た行: 65
```
| 分類 | 件数 | 内訳 |
|---|---|---|
| **[合流点である]** | 8 | `intent_record.py:53,54` / `phase0.py:57,58` / `de_admission.py:167,168` / `workcell.py:81,82` |
| **[記録機構自身]** | 3 | `ds/ds/etrace.py:107,108,117` |
| **[台帳を書かない]** | 42 | ロック(`egl/core.py:44`)／成果物パケット(`workcell.py:437`)／一時 json(`submit.py:168`)／sandbox 書き込み(`live_worker_runtime.py:30,31`)／HTTP 応答(`webui.py:489`)／token ファイル／snapshot・runs 出力／codegen 出力 等 |
| **[★抜け道]** | **8**（4箇所） | **下表** |
| **[分類できない＝実装源の4区分に枠が無い]** | 4 | `twoder` 自身の台帳（`artifact_registry` / `failure_memory` / `roadmap_registry` / `human_escalation_ledger` / `economy_decision_ledger` / `completion_definition_registry` / `benchmark_run_ledger` / `active_work_and_wait_ledger` / `claude_intervention_log`）。**DS/RRI/EGL/DW の台帳ではないので「抜け道」に入れず、しかし「台帳を書かない」でもありません。** **区分の不足として申告します** |

**★抜け道（合流点を通らずに DS/RRI/EGL/DW の台帳に書ける関数）:**
| 場所 | 関数 | 書く先 | 系 |
|---|---|---|---|
| `rri/rri/request_thread.py:73` | `_append` | `RTHREAD_EVENTS`（`rthread_events.jsonl`） | **RRI** |
| `egl/egl/core.py:119` | `append_event` | `egl/data/events.jsonl` | **EGL** |
| `dev-workcell/dw/authorization.py:46` | `_append` | DW authorization 台帳 | **DW** |
| `dev-workcell/dw/dispatch.py:162` | `_emit_pending` | `dev-workcell/data/pending_actor.jsonl` | **DW** |

> **★実装源 §3-3 の基準では「抜け道が1件でも在れば、その時点で不合格」です。** **4件在ります。**
> **★原因の見立ては書きません**（監査の担当）。**事実として、合流点5つは「各系の1つの台帳」の唯一の書き手であって、「各系のすべての台帳」の唯一の書き手ではありませんでした。**
> **★`egl/egl/core.py:119` は、実装源 §4-2 が「未確認」に挙げた項目そのものです。** **全走査に含めた結果、出ました。**

## 8. 触ったファイル
```
ds           : M ds/phase0.py            ?? ds/etrace.py（新規）
rri          : M rri/intent_record.py
egl          : M egl/de_admission.py     M structure/LEDGER_REGISTRY.jsonl（--apply の結果）
dev-workcell : M dw/workcell.py
twoder       : M submit.py
（上記以外の M は台帳＝実行の結果であり、私が編集したものではありません）
```
- **既存関数の引数・返り値・保存内容を1つも変えていません。** **DW の `phase`/`role`/`state`/`PROCESS_EVENT_KINDS` を1つも増やしていません。** **`record_utterance` の返り値に `event_id` を足していません。** **`provenance.trace_id` の値を変えていません。**

## 9. 守った禁止事項（実装源 §2-7）
- 新しい RRI 判断ロジック・4軸・7戦略・EGL/DW 仕様を1つも書き換えていません。
- **第二段階を先取りしていません**（関数内部の全分岐・「呼ばれなかった処理」に手を出していません）。
- **記録先を2つ作っていません**（1ファイルのみ）。
- **入口に注意書きを足していません**（入口には1行も触れていません）。
- **`rthread_events.jsonl` を復活させていません**（`G-33`。抜け道として**報告**しただけです）。
- **`dw → twoder` の既存逆転を直していません**（`G-39`）。
- **投入は2回だけ・文面は1文字も変えていません。**
- **commit していません**（MGR）。

## 10. 未確認（「全部見た」と書きません）
1. **③④⑤⑥の入口は実行を見ていません**（`grep` のみ・実装源から引き継ぎ）。
2. **`event_trace.jsonl` の中身を1行も見ていません**（§5）。**∴ 親子関係が本番で意図どおり付いたかは未確認です。** **隔離環境の smoke では `EV-…-0001..0004` が親子で繋がることを確認しています。**
3. **抜け道4件が実際に呼ばれるかは調べていません**（構造として書けることのみ示しました）。

---
*IMPL BUILT（D-42 Event Trace 第一段階）。合流点5つに配線し（⓪`submit()` 先頭=fail-closed で `_fail("ETRACE",…)` として結果を返す／①DS `_append`／②RRI `mint`／③EGL `admit_design_evidence`／④DW `_append_event`=fail-open）、新規 `ds/ds/etrace.py`（他 repo を import しない・標準ライブラリのみ・記録先 `ds/data/event_trace.jsonl`）。既存の引数/返り値/保存内容を1つも変えず、**受入④は `/api/claude_packet`・`/api/state` とも sha256 一致で差分ゼロ**、非回帰98本は**基準 91/7 と実装後 91/7 で失敗の顔ぶれまで同一**。★一度は増やした事実を申告=最初の事後測定で `test_fi_min` が新規に落ち（`ds` が中身の無い名前空間として先に束縛されると `sys.path` 追加だけでは解決しない）、その場合に限り束縛を捨てて再解決する修正を入れて基準へ戻した。★webui は投入前に再起動（旧 2746222 → 新 3271880）、スナップショットは実装前に取得。投入は承認文面のまま CLI→webui の2回のみで、**2件とも `task_id` が None**（`OBSERVE_CURRENT_STATE` と判定され DW でなく取得経路へ routing）∴ 実装源 §3-4 の予想は前提（DW task が作られる）から成立せず、受入③は満たせない。★受入②③⑥（event 列を貼る）は**できなかった**——読み出し経路が無く（`webui`/`ids` に該当 0件）、`/api/resolve` は `resolved:false`、直読は PreToolUse フックが拒否した。使用ガイドどおり「答えられなかった」が結果であり、それが次に作る読み出し機能である（迂回していない）。完了条件1=台帳登記は実施したが判定は **ORPHAN（読み手が無い）**で、登記側からも同じ事実が出た。★完了条件3=受入⑦(c) の全走査を省かず65行を全分類し、**抜け道が4件**（`rri/request_thread.py:73`→rthread_events／`egl/core.py:119`→egl/data/events.jsonl／`dw/authorization.py:46`／`dw/dispatch.py:162`→pending_actor.jsonl）。**実装源 §3-3 の基準では1件でも在れば不合格であり、4件在る。** 合流点5つは「各系の1つの台帳」の唯一の書き手であって「各系のすべての台帳」の唯一の書き手ではなかった（`egl/core.py` は実装源 §4-2 が未確認に挙げた項目そのもの）。加えて `twoder` 自身の9台帳は4区分のどれにも入らず、**区分の不足**として申告する。受入⑦(b) の12入口表は空欄なしで、**⑨〜⑫（`create_task` 直呼び3件・`record_utterance` 直呼び1件）は ⓪ を通らないため `run_id` が付かず、1件の依頼として追跡できない**。未確認=③④⑤⑥の入口は実行未確認／`event_trace.jsonl` の中身は1行も見ていない（∴本番の親子関係は未確認・隔離 smoke では確認済）／抜け道4件が実際に呼ばれるかは未調査。commit していない。*
