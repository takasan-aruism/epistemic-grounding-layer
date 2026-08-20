# declared — AXIS = MANAGER_WORKLIST_ADMISSION

発: MGR（進行担当）／ 宛: ESDE Evaluation 専任監査
根拠: `egl/docs/CC_DESIGN_2026-08-20_TO_MGR_ESDE_OPERATING_ORDER.md` §2①（実装・配線の前に置く1枚）
台帳: ITEM-2DER-EVO-0081（本 AXIS が支える item）／ 監査へ渡す先 ITEM-2DER-EVO-0083
置いた時刻: 2026-08-21（実装・配線の前・commit 済みの形で残す）

---

## 0. なぜこの一本を選んだか

EVO-0081 の記帳は「front door へ投げた新 task に手番が回らない」＝ dispatcher で詰まっている、と残している
（JAM_1〜JAM_5）。ところが**その記帳の後、同じ 2026-08-20 に、詰まり先を候補から外す分岐が
`twoder/manager_v0.py:262-275` へ入っている**。そして常駐 `twoder-manager.service` は
**2026-08-19 23:49:36 に停止したきり**（SIGTERM / Result=success / NRestarts=0 ＝ 意図的停止）。

∴ **その分岐は正規上流で一度も実行されていない。**
いま要るのは新規実装ではなく、既に置かれた admission 配線を正規上流で初めて走らせ、
declared のままの区間を observed へ動かすこと。

**原因名は付け直さない。** JAM_1〜JAM_5 は `MANAGER_V0_ONCE`（毎回新プロセス）運用下の実測であり、
常駐＋08-20 分岐の下で同じ結果になるとは限らない。

---

## 1. AXIS

`MANAGER_WORKLIST_ADMISSION`

front door に入った task が、常駐の選択器 `manager_v0._last_task` の work list に入り、
`tick()` がその1件で実行口を1回叩き、叩いた結果（allow / refuse + cause）が痕跡に残るところまで。

**AXIS の外**: その task が COMPLETE すること ／ どの task が選ばれるか
（優先順位は付けない＝Taka 正本 §2.3・`tasks_to_enqueue` 逐語「並べ替えも優先順位も付けない」）。

## 2. SCOPE

| 欄 | 値 |
|---|---|
| 入口 | `systemctl --user start twoder-manager.service` → `ExecStart=/home/takasan/miniconda/bin/python3 -m twoder.manager_v0` → `main()` |
| 出口 | `POST /api/run_until_barrier` の返り（`refused` / `cause`）と、その後の `GET /api/state` |
| authority | **新規発行 0**。既存 run-gate（`twoder/gate_decision.py`）と escalation 台帳の**読み**のみ |
| 保存先 | `ds.etrace`（`MANAGER_V0.tick` / `RUNGATE.receive`）、systemd journal。**新台帳 0** |
| 構成要素 | `manager_v0.main/tick/_last_task`、`twoder/tasks_to_enqueue.py`、`twoder/requeue_decision.py`、`twoder/human_escalation_ledger.py`、`dw/dispatch._MAP`、`twoder/gate_decision.py` |

## 3. 今回作る／直す対象

**新規実装 0 行・新規配線 0 本・新 state 0・新台帳 0・新 authority 0・新 front door 0・新語彙 0。**
対象は「既存配線の初回実走」。
実走で止まった場合のみ、**その一本を直接止めている1点だけ**を局所処理し、直後に本 AXIS へ戻る。

## 4. 通す予定の LINKAGE（edge）

```
systemd ─start→ manager_v0.main
  main ─→ receive_finished                        （COMPLETE 未受領を並びから落とす）
  main ─→ submit_next_contract                    （置かれた契約を1件投げる・選ばない）
  main ─→ tick ─→ _last_task
            ├ ① queue 先頭で machine_turn を探す    → dw.dispatch._MAP
            ├ ② submitted index → requeue_decision  → escalation 未解決は candidate_skip
            └ ③ /api/tasks + derive_state → tasks_to_enqueue → _queue_add
  tick ─POST /api/run_until_barrier {task_id, caller:"MANAGER_V0.tick"}→ RUNGATE
  RUNGATE ─→ gate_decision → allow なら dispatch.run_until_barrier ／ 否なら cause を返す
  tick ─→ _record ─→ ds.etrace.emit("MANAGER_V0","tick", …, handed_to="RUNGATE.receive")
```

## 5. 作る SYMMETRY の対（writer ↔ reader）

| 対 | writer | reader |
|---|---|---|
| tick の判断 | `manager_v0._record` → `ds.etrace.emit("MANAGER_V0","tick")` | `GET /api/etrace?task_id=` |
| 実行口の受け | `webui.py:1500` → `ds.etrace.emit("RUNGATE","receive")` | 同上（`handed_to` と対になる） |
| 選択器の生死 | systemd journal（`tick_failed:` / `tasks_to_enqueue wiring failed:`） | `journalctl --user -u twoder-manager` |

**この AXIS で新しい writer は作らない。** 3つとも既存。

## 6. 通るはずの HIERARCHY の境界

- General Manager（`manager_v0`）は**状態名を手で並べない** → 次の仕事の有無は `dw/dispatch.py::_MAP` に訊く
- 進めてよいかは **RUNGATE**（`gate_decision`）が決める。選択器は allow を自分で作らない
- 終端 task を通常 queue へ戻し続けない → **escalation 台帳の事実**（`human_escalation_ledger.states()`）を読むだけ
- 判定部品（`tasks_to_enqueue` / `requeue_decision`）は 2DER が契約経路で書いた物。足場は引いて渡すだけ

## 7. 正規上流の入口

`twoder-manager.service`（systemd user unit / `WorkingDirectory=/home/takasan`）。
**単体実行・sandbox・`MANAGER_V0_ONCE` は成功の証拠にしない**（運転指示 §3）。

## 8. 成立確認に使う実測証拠

1. `journalctl --user -u twoder-manager --since <start>`
2. `GET /api/etrace?task_id=<選ばれた task>` — `MANAGER_V0.tick` 行の `handed_to` / `gate_cause` / `dw_state_before` / `dw_state_after`
3. `GET /api/state?task_id=<選ばれた task>` — 叩く前後の `dw_state` / `next_operation`
4. `systemctl --user show twoder-manager -p ActiveState,ExecMainStatus,NRestarts`

**成立の線**: `MANAGER_V0.tick` の行が1本以上あり、`handed_to=RUNGATE.receive` と `gate_cause` が読める。
**refuse は AXIS の失敗ではない** — cause 付きで痕跡に残れば区間は通った（observed）。
**不成立の線**: tick 行が0本 ／ `tasks_to_enqueue wiring failed:` ／ `tick_failed:`。

## 9. AXIS 成立に必要な未検証事項 → **なし（DESIGN_HOLD ではない）**

前提4点はすべて 2026-08-20〜21 に読み取りで確定済み：

| 前提 | 実測 |
|---|---|
| 正規上流の入口が在る | unit file 実在・`enabled`・`inactive (dead) since 2026-08-19 23:49:36 / ExecMainStatus=15(SIGTERM) / Result=success / NRestarts=0` |
| admission 部品が callable で、現在値で to_add を返す | 純関数を読み取り再現：`/api/tasks`=576 件、dw events=4235 件、`derive_state` 集計 **CREATED=176**、`tasks_to_enqueue(cands, [])` → **to_add=176 / 先頭 `TASK-2DER-99E12CEF`**。`TASK-2DER-83BD03E1`・`TASK-2DER-D7977C1A` はともに CREATED で to_add に入る |
| 詰まり先が候補から外れる | `human_escalation_ledger.states()` の未解決4件に **`TASK-2DER-9F26BF5F` が実在**（HESC-3d2fecb61949 / trigger_state=JUDGE_REQUIRED）∴ `manager_v0.py:267-275` の escalation-skip が効く側に入る |
| 実行口と門が在る | `POST /api/run_until_barrier` 実在（`webui.py:1494`）。`gate_decision` の拒否語は **BLOCKED / NOT_RUNNABLE / TASK_MISMATCH** の3つのみ、他は OK。NOT_RUNNABLE のときだけ `decide_rearm_v2` の再武装経路がある |

## 10. 先に確定した副作用（隠さずに宣言する）

- 段③に到達した最初の tick で **CREATED 176 件が一度に queue へ入る**（`_queue_add` × 176）。先頭は `TASK-2DER-99E12CEF`
- 以後 `INTERVAL=60` 秒ごとに1件ずつ `run_until_barrier` を叩く。経路上に **build_planner(Qwen)** と
  **claude_senior（headless `claude -p`）** が居る
- **観測窓 = 3周（約3分）で停止**（Taka 裁定 2026-08-21）。回しっぱなしにしない

## 11. AXIS 外の未検証（UNVERIFIED として保留・進行は止めない）

- 選択器の並びファイルと submitted index の現在値 — **横読み禁止のため読めない**（2DER 境界フックが拒否）。
  引き継ぎ文書の「並び=1件 `TASK-2DER-B686EA09`」は 08-20 時点の値。∴ ②と③のどちらが先に task を返すかは走らせて見る
- `SENIOR_CALL_SKIPPED` が `PROCESS_EVENT_KINDS`（`dev-workcell/dw/workcell.py:235`）に無く
  `webui.py:649` の `except Exception: pass` が握り潰す件 — **別 AXIS**。
  同 enum のコメントに「★追加は この 1語だけ」（Taka 裁定 2026-08-20 / CONTROL_PLANE_BOOTSTRAP）とあり、語の追加には裁定が要る
- 176 件が一度に並びへ入ると `_GATES_MAX=200`（`webui.py:37`）の上限に近づき、古い門が落ちうる
- 未解決 escalation 4件（`9F26BF5F` / `229A3CD1` / `B7082857` / `C7396FE0`）は人待ち。触らない

## 12. 語の規律（本 AXIS の報告に適用）

`declared`（置いた）→ `callable`（同じ入力で同じ答え）→ `observed`（正規上流の実走で1回通った・証跡 id 付き）
→ `effect`（実際の判断を1度変えた）。
「動いた／入った／繋がった／直った／抑止した／COMPLETE／観測した／自動化した／自己修復した」は証拠 id を添えない限り書かない。
総合点は作らない。UNVERIFIED を MISSING・0・FAIL へ読み替えない。**✔ は自分で付けない**（判定は ESDE 監査が独立に出す）。
