
# 実装 → 設計/監査: Build 14 — `GENERATE` は走り sandbox も作られたが、**中身は0ファイル**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD14_SPEC_GENERATE_AND_RECEIVE.md` v1.0
- **受領した文書**: 上記実装源 / `CC_DESIGN_2026-07-27_BUILD13_AUDIT.md`（前段）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**
- `cc_register.py` の path 欠陥: **[x] 実施済**（D-21 修正・監査通過）

---

## 1. 手順①（鮮度確認）【監査:IMPL】
```
webui   : pid 1594748 / 起動 月 7月 27 18:37:58 2026
webui.py               2026-07-27 18:05:37
dispatch.py            2026-07-27 18:05:20
generate_via_runner.py 2026-07-23 15:11:52
qwen_worker.py         2026-07-15 23:35:49
```
**起動が全ソースより新しいことを確認して続行しました。**
※初回の確認で相対パスを使い、`pwd` が `egl/docs` だったため4ファイルとも「存在しない」と出ました。**絶対パスで取り直しています**（上表）。**誤った出力を根拠にしていません。**

## 2. 手順②〜⑤【監査:IMPL】
```
② 投入前 /tmp/2der_runner_* : 56
③ POST /api/submit          : task_id=TASK-2DER-21F64D9D / runnable=true   ← 依頼文は Build 13 と同一（機械抽出・1文字も変えず）
④ POST /api/run_next        : dispatched=true / reason=None                ← 1回だけ・run_until_barrier 不使用
   投入後 /tmp/2der_runner_* : 57
   新規                      : /tmp/2der_runner_tx15qmh2
⑤ 保全先                    : dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D/
   保全したファイル数        : ★0
```

### 2-1. ★新規 sandbox は作られたが、中は空でした
```
$ ls -laR /tmp/2der_runner_tx15qmh2
drwx------ 2 takasan takasan 4096  7月 27 22:49 .
（ファイルなし）
```
**∴ 保全対象が存在しないため、ファイルの保全はしていません。**
**探索したパス**: `/tmp/2der_runner_*` / **時刻**: 2026-07-27 22:49（実行時）。**黙って再投入していません。**

## 3. `derive_state` と events
```
derive_state('TASK-2DER-21F64D9D') = READY_FOR_AUDIT
events = ['CREATE', 'PROCESS_EVENT', 'PLAN', 'GENERATE']
```

## 4. ★`generate_runs` の payload（逐語・全文・要約していません）
```json
{
 "task_id": "TASK-2DER-21F64D9D",
 "phase": "GENERATE",
 "role": "WORKER",
 "identity": "2der-generate-via-runner",
 "run_id": "SLICE-TASK-2DER-21F64D9D",
 "ts": "2026-07-11T09:00:00",
 "payload": {
  "diff": null,
  "test_result": {
   "status": "FAILED",
   "ok": false,
   "reason": "action_type mismatch (ledger=USE_VLLM_INFERENCE, need=LIVE_WORKER_MINIMAL); task_id mismatch (ledger=TASK-2DER-21F64D9D#attempt-1, run=TASK-2DER-21F64D9D); operation_class LIVE_WORKER_TASK outside approved scope",
   "artifact_sha256": ""
  },
  "problems": [
   "action_type mismatch (ledger=USE_VLLM_INFERENCE, need=LIVE_WORKER_MINIMAL); task_id mismatch (ledger=TASK-2DER-21F64D9D#attempt-1, run=TASK-2DER-21F64D9D); operation_class LIVE_WORKER_TASK outside approved scope"
  ]
 },
 "_ordinal": 726
}
```
- **`contract_source` というキーは payload に存在しません**（実装源 §2-3 が名指ししていた項目）。
- **`artifact_sha256` は `""`**（Build 12 は `null` でした）。
- **`problems` は1件のみ**（3つの不一致が1文字列に連結されています）。

## 5. `/api/run_next` の応答
```
dispatched : true
reason     : None
planner_outcome : キーは存在（値 null）
```

## 6. Build 12 との差（事実のみ）
| | Build 12（契約なし） | **Build 14（契約つき）** |
|---|---|---|
| `reason` | `SPEC_INCOMPLETE_NO_CONTRACT` | **token gate の3件の不一致**（`action_type` / `task_id` / `operation_class`） |
| 新規 sandbox | **作られず**（56→56） | **作られた**（56→57・ただし中身0） |
| `artifact_sha256` | `null` | `""` |

## 7. 予想と実際
| 項目 | 予想 | **実際** | 判定 |
|---|---|---|---|
| `dispatched` / `actor_role` | `true` / `CODING_WORKER` | **`true`**／`nlo.actor_role` は応答に含まれず | **一部当たり・一部判定不能** |
| 新しい `2der_runner_*` | **1つ増える** | **1つ増えた** | **当たり** |
| `contract_source` | `ledger` | **キー自体が payload に無い** | **★外れ（指標が成立しない）** |
| `verify_skeleton_preserved` | 通る | **到達していない**（その手前で FAILED） | **判定不能** |

## 8. 守った禁止事項
- **各操作1回ずつ**（submit 1・`run_next` 1）。**`run_until_barrier` 不使用。**
- **依頼文を1文字も変えていません**（Build 13 と同一・機械抽出）。
- **検査・配置・登記・配線をしていません。**
- **`TASK-2DER-B9B4DA3B` と `TASK-2DER-D6A93450` に触っていません。**
- **token を迂回していません。**
- **本番コードを変更していません**（本 build では1行も）。
- **成果物の中身を貼っていません・評価していません**（そもそも0ファイル）。

## 9. 観測の限界（事実として）
- **1回しか実行していません。**
- **`reason` に挙がった3件の不一致の原因を調べていません**（実装源の範囲外）。
- **空の `2der_runner_tx15qmh2` を削除していません**（そのまま残しています）。

## 10. commit
**していません**（MGR）。

---
*IMPL BUILT（Build 14）。鮮度確認（起動 18:37:58 > 全ソース）後、Build 13 と同一依頼文で submit 1回・`run_next` 1回。**`GENERATE` が記録され `READY_FOR_AUDIT` へ。新規 sandbox `/tmp/2der_runner_tx15qmh2` が1つ増えたが中身は0ファイルで、保全対象なし。** `reason` は Build 12 の `SPEC_INCOMPLETE_NO_CONTRACT` から **token gate の3件の不一致**（`action_type` / `task_id` / `operation_class`）に変わった。**`contract_source` キーは payload に存在せず、予想の指標が成立しなかった。** 中身の評価・配置・登記・配線なし。本番コード無変更。1回のみの観測。*
