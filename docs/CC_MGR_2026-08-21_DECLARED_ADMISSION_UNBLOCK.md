# declared（2枚目）— 同じ AXIS `MANAGER_WORKLIST_ADMISSION` の循環を止める

発: MGR（進行担当）／ 宛: ESDE Evaluation 専任監査
根拠: `CC_DESIGN_2026-08-20_TO_MGR_ESDE_OPERATING_ORDER.md` §2①（実装・配線の**前**に置く1枚）
台帳: ITEM-2DER-EVO-0081 ／ 監査へ渡す先 ITEM-2DER-EVO-0083
前提: 1枚目 `CC_MGR_2026-08-21_DECLARED_MANAGER_WORKLIST_ADMISSION.md`（`egl 7e0f8ab`）と
実走報告 `CC_MGR_2026-08-21_AXIS_HANDOFF_MANAGER_WORKLIST_ADMISSION.md`（`egl 18446cf`）
**新しい AXIS は立てない。同じ AXIS の続き。**
**ESDE 正本は現在使用中の版で固定する**（別スレッドの未 commit 変更は取り込まない・触らない）。

---

## 1. 止める循環（実測で1点に限定済み）

```
段② が FD9975C9 を requeue → tick が回す → dw_state 不変 → _STOPPED_AT が伸びる
  → decide_tick が「同じ所で2回」→ 並びから落とす → 次周 in_queue=False に戻る
  → 段② が requeue_decision 規則5 で また requeue → …（段③へ永久に落ちない）
```

証跡: `ETR-NORUN-0394`(RUN) → `-0789` `-1180`(STOP) ／ 窓3 `-0393` `-0788` `-1179` `-1570` `-1961`。
8周すべてで `tasks_to_enqueue`（段③）未到達、DW events 4235→4235、状態差分 0。

## 2. 先に確認した既存機構（新規を作らない根拠）

| 確認先 | 結果 |
|---|---|
| 判断器 `twoder/manager_decide.py::decide_tick` | **既存・2DER 製**。「同じ所で2回」の規則（その3）を**すでに持っている**。`stopped_at` を引数で受ける |
| 記憶 `manager_v0.py:34 _STOPPED_AT` | **既存**（プロセス内・再起動で消える。文書化済みの限界） |
| `tick()` の落とし方 | `decide_tick` の返り `reason == "同じ所で2回"` で `_queue_write` から除く（`manager_v0.py:385-386`） |
| 段②（`manager_v0.py:250-277`） | **同じ記憶を見ていない**。`requeue_decision` の返りだけで戻す |
| escalation-skip（`:262-275`） | 既存。未解決 escalation の task は既に戻さない（実走で毎周発火を確認） |
| work list を返す口 | **front door に 0**（`webui.py` に該当ルート無し）→ §6 参照 |
| authority / 台帳 / RRI | 触らない。読みもしない（この変更は authority を発行しない） |

∴ **新しい判定器・新しい記憶・新しい語彙は要らない。**

## 3. 今回変更する最小箇所（1ファイル・1ブロック）

`twoder/manager_v0.py` — `_last_task()` 段②のループ内、**escalation-skip の後・`_queue_add(tid)` の直前**に
次の1ブロックのみを足す（他は1行も変えない）:

```python
_stop = _STOPPED_AT.get(tid) or []
if _stop:
    _dq = _use("decide_tick", decide_tick,
               {"task_id": tid, "dw_state": _s.get("dw_state")}, None, _stop)
    if _dq.get("action") == STOP:
        _record({...}, {"phase": "candidate_skip", ...})
        continue
```

**この変更の意味は1つだけ**: `tick` が「走らせない」と決めた物を、段②が戻さない。
判断は書かない（`decide_tick` の返りをそのまま使う）。記憶は増やさない（`_STOPPED_AT` は既存）。
**消さない**（並びからも submitted index からも削除しない）＝次の候補へ進むだけ。
`_STOPPED_AT` はプロセス内 ∴ 再起動で忘れる＝恒久の除外表にならない。

**新 state 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 front door 0 ／ 新管理機構 0 ／ 新語彙 0。**

## 4. 期待する遷移（この通りに動かなければ不成立）

| 周 | 段② | tick | `_STOPPED_AT[FD9975C9]` |
|---|---|---|---|
| 1 | FD9975C9 を戻す（記憶なし） | RUN → 状態不変 | `[UPPER_REVIEW]` |
| 2 | （段①が並びから拾う） | STOP「同じ所で2回」→ 並びから落とす | `[UPPER_REVIEW, UPPER_REVIEW]` |
| 3 | **新ブロックが STOP を受けて `continue`** → 次の候補 | その候補を回す | — |
| … | 進めない候補は 2周で同じく skip される | | |
| N | 段②に戻す候補が尽きる → **段③ `tasks_to_enqueue` へ落ちる** | CREATED の task を回す | — |

## 5. 成立条件（`FD9975C9` を処理したことではない）

1. **段②→段③ の連動**: `tasks_to_enqueue` の呼び出しが etrace に出ること（event_id で示す）
2. **admission**: 走行前の8周で tick 行が **1本も無かった** task（`CREATED`）に、
   `MANAGER_V0.tick` と `RUNGATE.receive` の行が **task_id 付きで**出ること
3. **effect**: DW events 件数 または `derive_state` が動くこと（4235 からの差分）

報告は `declared / callable / observed / effect` を分けて出す。総合点は作らない。

## 6. 取れない証拠（隠さない）

**work list（並び）の中身を返す口が front door に無い。**
∴「front door 投入の `83BD03E1` / `D7977C1A` が並びに入った」を **observed では出せない**。
出せるのは次の2つに分かれる:

- **callable**: 同じ純関数 `tasks_to_enqueue` に同時刻の `/api/tasks` と `derive_state` を渡して再計算し、
  両 task が `to_add` に入ることを示す（2026-08-21 00:0x に再現済み: to_add=176）
- **observed**: 段③が実際に呼ばれたこと＋その走行で `CREATED` の task が tick に渡ったこと

この差は **`CC_2DER_USAGE_GUIDE.md §2` の言う「返せない」がそのまま結果**。
**新しい front door を足して埋めない**（§3 の禁止）。記録して保留する。

## 7. 触らないもの（記録済みのまま保留）

- `requeue_decision` の `already_in_queue` が `no_machine_turn` を隠す件
- `_queue()` の `except: return []`
- artifact 登記（`artifact_ids` に後付けの口が無い）
- 性能（`record_stages` の `/api/control` 111.5 秒 ／ `/api/state` 1回 2.2 秒）
- `SENIOR_CALL_SKIPPED` が `PROCESS_EVENT_KINDS` に無い件

いずれも**今回の循環を直接止めていない**。

## 8. 不成立のときの返し方

新しい原因説明を広げない。**同じ AXIS 上で最初に切れた edge を1点だけ**返す。
