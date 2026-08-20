# AXIS 再提出（第2窓）— `MANAGER_WORKLIST_ADMISSION` / admitted task が選ばれ実行口を叩いた

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
AXIS: `MANAGER_WORKLIST_ADMISSION`（継続・新 AXIS なし・**実装変更 0**）
返された1点: `UNVERIFIED_ADMITTED_TASK_NOT_YET_SELECTED`（観測不足）→ 第2窓で埋めた

## 実走

正規上流 `twoder-manager.service` 03:00:21 → 03:11:15（停止条件で自動停止）
`Result=success` / `NRestarts=0` / journal 例外 0 行 / コード変更なし（`twoder f1be519` のまま）

```
03:03:17  CONTRACT_STAGE reached   ETR-NORUN-0037   record_stages 完了(周1)
03:08:38  RUNGATE receive          ETR-NORUN-9955   received_from=MANAGER_V0.tick / TASK-2DER-99E12CEF
03:08:51  RUNGATE refuse           ETR-NORUN-9960   cause=MISSING_GATE / "rearm 不可: MISSING_GATE"
03:08:53  MANAGER_V0 tick          ETR-NORUN-0731   action=SLEEP / reason=MISSING_GATE / gate_cause=MISSING_GATE
                                                    dw_state_before=after=CREATED / stopped_at_stage=PLAN
```

`TASK-2DER-99E12CEF` は **02:50:48 の admission で work list に入った 176 件の先頭**（`to_add[0]`）。
修正前の 8 周（00:23–00:57）で tick が触れたのは段②由来の `FD9975C9` / `9F26BF5F` のみ。

## 4段

| 段 | 到達 |
|---|---|
| declared | `egl d051a1b`（実装の前） |
| callable | `tasks_to_enqueue` を純関数で再現 → `to_add`=176 |
| **observed** | admission（02:50:48 `ETR-NORUN-0561`/`0563`）→ **選択**（03:08:38 `9955`）→ **実行口**（03:08:51 `9960`）→ **記録**（03:08:53 `0731`） |
| **effect** | **在り**。選択器が渡す相手が段②由来から**段③由来**へ変わった。ただし **DW state は不変**（events 4235→4235・`derive_state` 差分 0・新規 task 0）＝門が `MISSING_GATE` で拒否したため |

## 訂正（私の以前の記述）

「門の拒否語は `BLOCKED` / `NOT_RUNNABLE` / `TASK_MISMATCH` の 3 つのみ」は **`gate_decision` 単体の話**でした。
実際の門は `NOT_RUNNABLE` のとき再武装経路へ回り、`twoder/decide_rearm_v2.py`（2DER 製・純関数）が
**`MISSING_GATE`** を返します（`gate_present` が偽）。**門の拒否語の列挙が不完全でした。**

## 特定していないこと（推測を書かない）

`FD9975C9` が並びの先頭から外れた理由は**特定していません**。`receive_finished` が受領して落とした可能性はあるが、
並びを読む口が私の側に無く、`twoder` に新しい commit も出ていないため確認できていない。
**並びを直接読める監査側で確定してください。**

## 記録して保留（触っていない）

- 段②③は `pick is None` のときだけ走る ∴ 並びに件が在る間 admission は再び走らない（監査からの申し送り）
- 周辺欠陥 4 件（`already_in_queue` が `no_machine_turn` を隠す ／ `_queue()` の `except: return []` ／
  artifact 登記 ／ 性能）・`SENIOR_CALL_SKIPPED`
- `MISSING_GATE` の先（EVO-0081 の受入条件）は **この AXIS の外**。進めていない

## 一本を止めるか

**私からは止めません。** 5 条件のいずれにも当たらず、DW の state は 1 件も動いていません。
