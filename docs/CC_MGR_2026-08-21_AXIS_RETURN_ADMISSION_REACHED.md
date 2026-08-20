# AXIS 再提出 — `MANAGER_WORKLIST_ADMISSION` / admission 到達

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
AXIS: `MANAGER_WORKLIST_ADMISSION`（継続・新 AXIS なし）
直した欠損 ID: `LINKAGE_STAGE2_RETURN_PREEMPTS_STAGE3` の**1点のみ**

## 在り処

| | |
|---|---|
| declared（実装の前に commit） | `egl d051a1b` → `docs/CC_MGR_2026-08-21_DECLARED_STAGE2_RETURN_PREEMPTS_STAGE3.md` |
| 実装 | `twoder f1be519`（`_last_task()` のみ / +25 −3） |
| 実走 | 正規上流 `twoder-manager.service` 02:47:51 → 02:51:44（停止条件で自動停止・`Result=success` / `NRestarts=0` / journal 例外 0 行） |

## 直したこと（1点）

段②は候補を1件見つけると **その場で `return`** していた ∴ 段③（`tasks_to_enqueue` = admission）は
段②が何も返さなかった周にしか走らない。→ `return` を `break` にし `_pick2` に控え、**段③を必ず通す**。
**返す値の優先は段②のまま**（変えたのは「段③を通るか通らないか」だけ）。
併せて `_queue_add` に既存 `_record` で受け側の1行（`phase=admission`）を付けた
＝ `_queue_add` は書き手だけで読み手が無く admission が観測できなかったため。
新 state 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 front door 0 ／ 新管理機構 0 ／ 登録語彙 0。

## 実測（1周の中で完結・証跡 id）

```
02:50:41  CONTRACT_STAGE reached          ETR-NORUN-0037            record_stages 完了(周1)
02:50:44  MANAGER_V0 tick                 ETR-NORUN-0377            9F26BF5F  AWAITING_HUMAN(段② skip)
          ── 段② が FD9975C9 を候補に控える(return しない) ──
02:50:48  MANAGER_V0 tick                 ETR-NORUN-0561            D7977C1A  ADMITTED / phase=admission
02:50:48  MANAGER_V0 tick                 ETR-NORUN-0563            83BD03E1  ADMITTED / phase=admission
02:50:50  RUNGATE receive                 ETR-NORUN-8474            FD9975C9(段②の候補を tick が回した)
02:50:50  DISPATCH next_legal_operation   ETR-503bf9c38a1a-0751
02:51:03  MANAGER_V0 tick                 ETR-NORUN-0573            FD9975C9  RUN / 進める
```

admission 行の中身（両方同じ）: `admitted_count=176 / already_in_queue=0 / skipped_not_created=400`
（400 = 576 − 176・整合）。event id の順序 `0377 → 0561/0563 → 0573` も整合。

## 4段

| 段 | 到達 |
|---|---|
| declared | `egl d051a1b` |
| callable | `tasks_to_enqueue` を純関数で再現 → `to_add`=176 ／ `83BD03E1` index 170 ／ `D7977C1A` index 168 |
| **observed** | 上記 etrace 行。**`83BD03E1` と `D7977C1A` が work list admission に到達**（task_id 付き）。段②が候補を返した**同じ周**に段③が走った＝`段②→段③` の連動 |
| effect | **未達**。DW events 4235→4235 ／ `derive_state` 差分 0。停止条件で止めたため、admission 後に選択が変わるところは見ていない |

修正前（8周・00:23–00:57）は段③ 0 回・admission 0 件。

## 触っていないもの（記録済みのまま保留）

周辺欠陥 4 件（`already_in_queue` が `no_machine_turn` を隠す ／ `_queue()` の `except: return []` ／
artifact 登記 ／ 性能）。`SENIOR_CALL_SKIPPED` も別 AXIS のまま。
前回の `twoder 0498733`（前進不能 task の再供給を減らす）は別の欠陥なので戻さず残した。

## 一本を止めるか

**私からは止めません。** 5 条件のいずれにも当たらず、DW の state は 1 件も動いていません。
