# 【BUILD SPEC】`EVO-0058` L0 — **★経路表を .py の定数にする（★台帳を作らない）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL**（★封入不要＝★純データ・契約なし） / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-04 23:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.13）** ／ 親: `ITEM-2DER-EVO-0035` ／ 裁定: MGR（★.py の定数＝台帳でない・2者一致）
- **★v1.8 の宣言**: **★核は無い・★2DER 工程 0**（★データであり ★判断が無い。★L1 は ★段3 の `locate_failure` が既に第一版）
- **★私の予告**: ★worker **0件**（★走らせない）／★Claude **定数ファイル1本のみ・★論理0行**
- **★走行 0・★task 増 0・★commit 0**
- **★廃止するもの（規律9）**: ★`CC_DESIGN_2026-08-04_EVO0058_ROUTE_TABLE_18.md` を ★正典から降ろす（★人が .md の表を目で追う運用を畳む）

---

## 1. ★置き場と形

```
★置き場 = `twoder/route_table.py` ／ ★中身 = ★定数1つ（`ROUTE`）だけ。★関数を書かない・★import を増やさない。
★★`locate_failure(route, events)` に ★引数で渡す（★段3 の契約は ★1文字も変えない＝★余分な欄は無視される）
★★★∴ ★2つ目の経路表を作らない。★L0 と ★段3 の route は ★同じ1本である。
```

## 2. ★1行の形（★MGR 裁定＝設計案を採用）

| 欄 | 意味 | `locate_failure` が使うか |
|---|---|---|
| `id` | 区間（S01..S18） | ★使う |
| `from` / `to` | 誰から誰へ | 使わない（★人が読む） |
| `sends` / `returns` | 渡す / 返る | 使わない |
| `component` / `function` / `phase` | ★実行記録との照合鍵。★None＝観測が無い区間 | ★使う |
| `require_nonnull` | ★これが None なら失敗とみなす欄 | ★使う |
| `fails_as` | 落ち方（★人が読む） | 使わない |
| `actor` | 主体 | ★使う |
| `actor_confirmed` | ★記録から一意に確かめたか | 使わない（★人と後の層が読む） |

## 3. ★★中身（★そのまま置く。★1文字も足さない・減らさない）

```python
# twoder/route_table.py — EVO-0058 L0: 期待をデータで持つ。★判断を書かない(定数のみ)。
# 出典: CC_DESIGN_2026-08-04_EVO0058_ROUTE_TABLE_18.md(段1 の実測) + 2026-08-04 の RUNNER 観測(S14)。
# actor_confirmed=False は「★記録から一意に確かめていない」の印。★埋めたことにしない。
ROUTE = [
 {"id": "S01", "from": "人(front door)", "to": "submit()", "sends": ["raw_input"], "returns": ["task_id", "TRACE"],
  "component": "SUBMIT", "function": "ENTRY", "phase": None, "require_nonnull": [],
  "fails_as": ["入口で拒否", "記録が残らない"], "actor": "Claude", "actor_confirmed": False},
 {"id": "S02", "from": "submit", "to": "DS phase0", "sends": ["utterance"], "returns": ["utterance_id"],
  "component": "DS", "function": "UTTERANCE", "phase": None, "require_nonnull": [],
  "fails_as": ["発話が登記されない"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S03", "from": "submit", "to": "DS phase1", "sends": ["transcript"], "returns": ["threads"],
  "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い"], "actor": "2DER", "actor_confirmed": False},
 {"id": "S04", "from": "submit", "to": "RRI request_type", "sends": ["raw_input"], "returns": ["request_type"],
  "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い"], "actor": "2DER", "actor_confirmed": False},
 {"id": "S05", "from": "submit", "to": "RRI preflight_gate", "sends": ["raw_input"], "returns": ["decision"],
  "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い"], "actor": "2DER", "actor_confirmed": False},
 {"id": "S06", "from": "submit", "to": "RRI intent_record", "sends": ["kind", "payload"],
  "returns": ["RREQ/RINT/RSIG id"], "component": "RRI", "function": "mint", "phase": None, "require_nonnull": [],
  "fails_as": ["id が発行されない"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S07", "from": "submit", "to": "EGL admission", "sends": ["admission_payload"], "returns": ["DE id"],
  "component": "EGL", "function": "admit_design_evidence", "phase": None, "require_nonnull": [],
  "fails_as": ["根拠が登記されない"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S08", "from": "submit", "to": "contract_seal", "sends": ["raw_input"], "returns": ["skeleton", "tests"],
  "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い", "契約が抽出できない"], "actor": "Claude", "actor_confirmed": False},
 {"id": "S09", "from": "submit", "to": "DW create_task", "sends": ["goal", "contract"], "returns": ["CREATE event"],
  "component": "DW", "function": "_append_event", "phase": "CREATE", "require_nonnull": [],
  "fails_as": ["task already exists"], "actor": "Claude", "actor_confirmed": True},
 {"id": "S10", "from": "run_next", "to": "dispatch next_legal_operation", "sends": ["state"],
  "returns": ["op", "actor"], "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い"], "actor": "Claude", "actor_confirmed": False},
 {"id": "S11", "from": "run_next", "to": "run-gate(_LAST)", "sends": ["task_id"], "returns": ["allow", "refused"],
  "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["応答には理由が出るが記録に残らない"], "actor": "Claude", "actor_confirmed": False},
 {"id": "S12", "from": "dispatch", "to": "PLAN", "sends": ["knowledge_packet"], "returns": ["implementation_packet"],
  "component": "DW", "function": "_append_event", "phase": "PLAN", "require_nonnull": [],
  "fails_as": ["計画が出ない"], "actor": "2DER", "actor_confirmed": False},
 {"id": "S13", "from": "dispatch", "to": "generate_via_runner.generate", "sends": ["contract"],
  "returns": ["artifact"], "component": "DW", "function": "_append_event", "phase": "GENERATE",
  "require_nonnull": [], "fails_as": ["結果だけ残り中が残らない"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S14", "from": "generate", "to": "runner(run_minimal_slice)→worker", "sends": ["packet"],
  "returns": ["impl.py"], "component": "RUNNER", "function": "run_minimal_slice", "phase": None,
  "require_nonnull": ["artifact_len"],
  "fails_as": ["artifact_len=0/None", "result=FAILED", "生成が空"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S15", "from": "generate", "to": "runner の試験実行", "sends": ["impl.py", "tests"],
  "returns": ["exit", "stdout"], "component": None, "function": None, "phase": None, "require_nonnull": [],
  "fails_as": ["観測が無い"], "actor": "2DER", "actor_confirmed": False},
 {"id": "S16", "from": "dispatch", "to": "AUDIT(QwenAuditor)", "sends": ["diff", "test_result"],
  "returns": ["findings"], "component": "DW", "function": "_append_event", "phase": "AUDIT",
  "require_nonnull": [], "fails_as": ["JUDGE_REQUIRED で停止"], "actor": "2DER", "actor_confirmed": True},
 {"id": "S17", "from": "ingest/auto", "to": "DISPOSE", "sends": ["findings"], "returns": ["dispositions"],
  "component": "DW", "function": "_append_event", "phase": "DISPOSE", "require_nonnull": [],
  "fails_as": ["処置が決まらない"], "actor": "MGR", "actor_confirmed": True},
 {"id": "S18", "from": "run_next", "to": "PROPOSE_COMPLETE→close_loop", "sends": ["result_packet"],
  "returns": ["COMPLETE"], "component": "DW", "function": "_append_event", "phase": "COMPLETE",
  "require_nonnull": [], "fails_as": ["completion_blockers で止まる"], "actor": "Claude", "actor_confirmed": False},
]
```

## 4. ★★この表が自分で言っていること（★埋めたことにしない）

```
★観測が在る区間 = ★11（S01 S02 S06 S07 S09 S12 S13 ★S14 S16 S17 S18）
★★観測が無い区間 = ★7（S03 S04 S05 S08 S10 S11 S15）―― ★段1 の8から ★1 減った（★S14 が埋まったため）
★★★主体を ★記録から一意に確かめた区間 = ★★8 だけ（`actor_confirmed=True`）
   ＝ ★18区間のうち ★10 は ★主体が【未確認】。★これを ★消さない。
★★★★★段1 §4 の逐語（★空欄の主体は設計上の担当を書いた）を ★機械可読にしただけ ＝ ★新しい主張をしていない
```

## 5. 受入

```
★(1) ★`twoder/route_table.py` が ★§3 と ★1文字違わず置かれる（★sha256 で照合）
★(2) ★`from twoder.route_table import ROUTE` が ★通る（★論理0行・★import 副作用なし）
★(3) ★★`locate_failure(ROUTE, events)` が ★段3 の契約を ★1文字も変えずに ★動く
     ★★★本日の実事故に当て、★★(a)0字 (b)refused (c)JUDGE_REQUIRED (d)空 artifact の ★4件の結果を ★逐語で書く
★(4) ★`actor_confirmed=False` が ★10件 在ることを ★数えて書く（★埋めたことにしない）
★(5) ★Claude の行数（★定数ファイルの行数・★論理は0と書く）／★(6) ★戻せる ／★(7) ★61本を走らせない
★★★(8) ★段1 の .md を ★正典から降ろしたことを ★1行 書く（★規律9 の廃止側）
★★★★★予告を投入前に書く: ★受入(3) の4件で ★返ると思う verdict
```

## 6. 禁止

```
★`route_table.py` に ★関数・分岐・import を書く（★定数だけ）／ ★.jsonl にする（★台帳を作らない）
★`actor_confirmed` を ★埋めるために ★記録以外から主体を決める
★観測が無い区間を ★表から消す ／ ★段3 の契約を ★本件で変える
★★『経路表が埋まった』と書く（★観測が無い区間は ★7 残っている）
★61本を走らせる ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
