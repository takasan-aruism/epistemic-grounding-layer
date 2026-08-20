# declared（3枚目）— `LINKAGE_STAGE2_RETURN_PREEMPTS_STAGE3` の1点だけを直す

発: MGR（進行担当）／ 宛: ESDE Evaluation 専任監査
根拠: `CC_DESIGN_2026-08-20_TO_MGR_ESDE_OPERATING_ORDER.md` §2①（実装・配線の**前**に置く1枚）
AXIS: **`MANAGER_WORKLIST_ADMISSION`（継続・新 AXIS は立てない）**
台帳: ITEM-2DER-EVO-0081 ／ 返す先 ITEM-2DER-EVO-0083
ESDE 正本は現在使用中の版で固定（別スレッドの未 commit 変更は取り込まない）。

---

## 1. 直す1点（監査が名指しした欠損 ID）

`LINKAGE_STAGE2_RETURN_PREEMPTS_STAGE3`

`manager_v0._last_task()` の段②は候補を1件見つけると **その場で `return`** する。
∴ 段③（`tasks_to_enqueue` = admission）は「段②が何も返さなかった周」にしか実行されない。
段②が前進不能 task を再供給し続ける限り、**admission は永久に起きない**。

**前回の私の修正（`twoder 0498733`）はこの1点を直していない。**
あれは「前進不能 task の再供給」を減らすもので、`return` による遮断そのものは残っている。
2つは別の欠陥なので、**戻さずに残し**、今回この1点を直す（戻すと再供給が復活し、
段③に落ちても次周でまた段②に取られる形が戻るため）。

## 2. 先に確認した既存機構（新規を作らない根拠）

| 確認先 | 結果 |
|---|---|
| `tasks_to_enqueue`（2DER 製・純関数） | **「並べ替えも優先順位も付けない」**＝ *足すだけ*。無条件に通しても優先順位を作らない |
| `_queue_add`（`manager_v0.py:115`） | 既存。並びへ足すだけ（重複は足さない） |
| 段②の役目 | 「投げた案件を拾い直す」自己修復。**どれを先に回すか**の優先は段②のまま変えない |
| work list を返す口 | **front door に 0**（`webui.py` に該当ルート無し。`deferred_active_tasks` は `_active_2der_tasks` 由来で並びではない） |
| `_record` → `ds.etrace` → `GET /api/etrace?task_id=` | **既存の writer↔reader の対**。`_queue_add` にはこの対が無い＝admission が観測できない |
| `_clip` の上限 | `_MAX=2000` 文字 ∴ **176 件の id を1行には入れられない**（`to_add` 全部を1行で残す案は不可） |

## 3. 変更する最小箇所（1ファイル・`_last_task()` のみ）

**(a) 段②の `return` を `break` にし、段③を必ず通す**

```python
_pick2 = None                      # ← 段②の前で初期化
...
                _queue_add(tid)
                _pick2 = tid       # ← return tid をやめる
                break
...
    if pick is None:               # 段③（_pick2 が在っても pick は None ∴ 必ず通る）
        ...
        if _pick2 is None and _r["to_add"]:
            return _r["to_add"][0]
    return _pick2 or pick
```

**返す値の優先は段②のまま**（段②が拾った案件を先に回す）。変えるのは
**「段③を通るか通らないか」だけ**。∴ 優先順位を新しく作らない。

**(b) `_queue_add` に受け側の記録を付ける（admission を観測可能にする）**

段③の `for _t in _r["to_add"]: _queue_add(_t)` に、**既存の `_record`** で1件1行を足す。
`_record` は `task_id` を添えて `ds.etrace` に書く ∴ `GET /api/etrace?task_id=` で
**その task が work list に入ったことを引ける**。
`to_add` が非空になるのは **admission が実際に起きた周だけ**（次周は `already_in_queue`）
∴ この行は**一度きり**で、毎周増え続けない。

**新 state 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 front door 0 ／ 新管理機構 0。**
`reason="ADMITTED"` は既存 `_record` の自由文欄（`AWAITING_HUMAN` / `ESCALATED` と同じ扱い）で、
登録語彙（`PROCESS_EVENT_KINDS` 等）を増やすものではない。

## 4. 期待する遷移

| 周 | 段② | 段③ | tick |
|---|---|---|---|
| 1 | 候補を1件 `_queue_add` して **break** | **必ず走る** → `to_add`=176 を `_queue_add` ＋ 1件1行 `_record` | 段②の候補を回す |
| 2 以降 | 前進不能なら 2 周で skip（`0498733`） | `to_add`=0（`already_in_queue`） | 並びの先頭から |

**周1で `83BD03E1`（`to_add` 内 index 170）と `D7977C1A`（index 168）が admission に到達する。**
（index は 2026-08-21 02:4x の読み取り再現値。`to_add`=176・先頭 `99E12CEF`）

## 5. 停止条件（ここで止める・次へ進まない）

`GET /api/etrace?task_id=TASK-2DER-83BD03E1` **または** `…=TASK-2DER-D7977C1A` に
`MANAGER_V0` の `phase=admission` 行が **task_id 付きで** 出た時点で停止し、同じ AXIS を ESDE 監査へ返す。

併せて出す実測:
- **段②→段③ の連動**: 段②が候補を返した同じ周に段③が走ったこと（`tasks_to_enqueue` の etrace 行）
- **effect**: DW events 件数 / `derive_state` の 4235 からの差分

## 6. 触らない（記録済みのまま保留・周辺欠陥 4 件）

`requeue_decision` の `already_in_queue` が `no_machine_turn` を隠す件 ／ `_queue()` の `except: return []` ／
artifact 登記 ／ 性能（`record_stages` の 111.5 秒・`/api/state` 2.2 秒）。
（`SENIOR_CALL_SKIPPED` も別 AXIS のまま。）

## 7. 不成立のときの返し方

新しい原因説明を広げない。同じ AXIS 上で**最初に切れた edge を1点だけ**返す。
