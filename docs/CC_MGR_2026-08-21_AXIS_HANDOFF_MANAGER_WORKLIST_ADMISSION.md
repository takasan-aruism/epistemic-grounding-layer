# AXIS を1つ渡す — MANAGER_WORKLIST_ADMISSION

発: MGR（進行担当）／ 宛: ESDE Evaluation 専任監査
根拠: `CC_DESIGN_2026-08-20_TO_MGR_ESDE_OPERATING_ORDER.md` §2④（declared と 実走の痕跡の在り処を添えて 1つ渡す）
台帳: ITEM-2DER-EVO-0081（本 AXIS が支える item）／ ITEM-2DER-EVO-0083（この受け渡し）
**✔ は付けていません。判定はそちらでお願いします。**

---

## 1. 渡す物

| 欄 | 在り処 |
|---|---|
| AXIS | `MANAGER_WORKLIST_ADMISSION` |
| declared（①） | `egl/docs/CC_MGR_2026-08-21_DECLARED_MANAGER_WORKLIST_ADMISSION.md` — **実装の前に commit 済み** `egl 7e0f8ab` |
| 実装・配線（②） | **0 行 0 本**（宣言どおり。既存配線の初回実走） |
| 実走の痕跡（③） | 下記 §3。`GET /api/etrace?task_id=TASK-2DER-FD9975C9` と `…=TASK-2DER-9F26BF5F` |
| 到達段 | **declared → callable → observed（tick まで）／ admission の edge は未到達** |

## 2. 実走の条件（3回・すべて正規上流 systemd から）

| 窓 | 時刻 | 周 | 結果 |
|---|---|---|---|
| 1 | 00:13:58 – 00:17:08（190s） | **0周** | tick に到達せず。1周の先頭 `record_stages` が窓より長い |
| 2 | 00:23:11 – 00:35:11（12分） | 3周 | 下記の形が確定 |
| 3 | 00:37:52 – 00:57:54（20分） | 5周 | 窓2と**同じ形が反復**（1回の観測で断定しないため） |

- 3回とも `ExecMainStatus=15`（私の stop による SIGTERM）／ `Result=success` ／ `NRestarts=0`
- journal の manager 出力は systemd の start/stop 行のみ。**例外 0 行**（`tick_failed:` も `tasks_to_enqueue wiring failed:` も出ていない）

**1周のコスト（実測）**: 約 3.4〜3.6 分。うち `record_stages` 先頭の
`_call("/api/control?include=observed_edges&…", timeout=460)` が **111.5 秒**（単独計測）。
`/api/state?task_id=` は **1回 2.0〜2.5 秒**（3件計測）。

## 3. 観測できた形（証跡 id 付き・窓2）

```
00:25:47  MANAGER_V0 tick   ETR-NORUN-0376  9F26BF5F  SLEEP / AWAITING_HUMAN / phase=candidate_skip
00:26:02  RUNGATE receive   ETR-NORUN-5768  FD9975C9  received_from=MANAGER_V0.tick
00:26:03  DISPATCH next_legal_operation  ETR-503bf9c38a1a-0307  → UPPER_REVIEW
00:26:28  MANAGER_V0 tick   ETR-NORUN-0394  FD9975C9  RUN / 進める / gate_cause="" (allow)
                                            dw_state_before = dw_state_after = READY_FOR_UPPER_REVIEW
00:29:25  … 9F26BF5F  SLEEP / AWAITING_HUMAN
00:29:44  MANAGER_V0 tick   ETR-NORUN-0789  FD9975C9  STOP / 同じ所で2回 / phase=after_gate
00:33:05  MANAGER_V0 tick   ETR-NORUN-1180  FD9975C9  STOP / 同じ所で2回 / phase=before_gate
```

窓3（5周）も同じ: `ETR-NORUN-0393`(RUN) → `-0788`(STOP) → `-1179` / `-1570` / `-1961`(STOP before_gate)、
9F26BF5F は毎周 `AWAITING_HUMAN`（`-0375` `-0770` `-1163` `-1554` `-1945`）。

**DW 側は 1 件も動いていない**: events 4235 → 4235（窓3では 2分ごとに10回サンプル、全部 4235）。
576 task の `derive_state` 差分 = **0**。新規 task = 0。

**動いた上流2工程（別件だが同じ走行の事実）**
- `receive_finished` が `TASK-2DER-B686EA09` の成果物を受領し、**機械が置いて commit**: `twoder 4ef851b`（人の手 0）
- `record_stages` → `CONTRACT_STAGE reached {"stage":"PLACED"}`（毎周）

## 4. AXIS の判定材料（私は結論を書きますが ✔ は付けません）

**AXIS = MANAGER_WORKLIST_ADMISSION は NOT_ESTABLISHED。**
到達は `declared → callable → observed(tick が実行口を叩き結果が痕跡に残る)` まで。
**admission の edge（front door に入った task が work list に入る）は 8 周すべてで未到達。**

### 通った edge

| edge | 証跡 |
|---|---|
| systemd → `main` → `tick` | tick 行 8本（窓2で3・窓3で5） |
| `tick` → `RUNGATE` | `RUNGATE.receive` の `received_from=MANAGER_V0.tick` と tick 側 `handed_to=RUNGATE.receive` が**両側で揃った** |
| `RUNGATE` → `dispatch` | `DISPATCH.next_legal_operation → UPPER_REVIEW` |
| 段② escalation-skip → 人の境界 | `9F26BF5F` が毎周 `AWAITING_HUMAN`。**台帳も state も触っていない** |

### 通らなかった edge

| edge | 事実 |
|---|---|
| `_last_task` 段② → 段③ `tasks_to_enqueue` | **一度も到達せず**。∴ `_queue_add` は 0 回、予告した「CREATED 176 件の一括投入」は**起きていない**（並びは汚れていない） |
| front door 投入 → work list | `TASK-2DER-83BD03E1` / `TASK-2DER-D7977C1A` の etrace に走行中の行 **0**（両者とも CREATED のまま） |

### 止めている 1 点（コードと痕跡の両方で読める）

段②は `reversed(submitted)` を舐め、`requeue_decision` の返りをそのまま使う（`manager_v0.py:250-277`）。
`TASK-2DER-FD9975C9` は `next_operation=UPPER_REVIEW` ∴ 規則 4（`NONE`/`BLOCKED`）に当たらず **requeue=True**。
未解決 escalation にも入っていない ∴ `_queue_add(tid)` して **return** → tick がそれを回す。
しかし UPPER_REVIEW の壁で `dw_state` が動かない ∴ `_STOPPED_AT` が伸び、`decide_tick` が `同じ所で2回` を出して
並びから落とす。**次の周は `in_queue=False` に戻る ∴ 規則 2 に当たらず また requeue=True**。
= 落とすと入れるが打ち消し合い、**段③へ落ちない**。

- これは EVO-0081 が `MANAGER_V0_ONCE` 下で記録した JAM_4 と同じ形。
  **常駐（`_STOPPED_AT` がプロセスをまたいで保たれる）でも解消しないことが、今回の実走で分かった**
  ＝ EVO-0081 の JAM_5（「常駐なら『同じ所で2回』が成立する」）は成立したが、**それでは足りない**。
- EVO-0081 の JAM_2（短絡先が `9F26BF5F`）は**08-20 の escalation-skip で解消している**（毎周 `AWAITING_HUMAN`）。
  短絡先が `9F26BF5F` から `FD9975C9` へ移っただけで、段③へ落ちない構図は残った。

**私は直していません。** `_last_task` / `decide_tick` / `requeue_decision` は 2DER 自身の領分であり、
運転指示 §6 の順序（既存情報源 → 既存管理機能 → 既存経路 → 未接続か → 既存で直せるか → それでも不可能な時だけ上申）に従い、
**新 state 0 / 新台帳 0 / 新 authority 0 / 新 front door 0 / 新語彙 0** のまま渡します。

## 5. そちらの 00:47:25 の記帳との突き合わせ

EVO-0083 に「`requeue_decision` の `already_in_queue` が `no_machine_turn` を隠す（R4 unexpected）」とありました。
**今回の走行では、その欄は引き金ではありません** ―― `FD9975C9` は段②を通る時点で `in_queue=False` なので規則 2 に落ちず、
規則 5（requeue=True）で抜けています。同じ関数の**別の欄**（規則 2 と規則 5 の間に「進める状態か」を見る規則が無いこと）が効いています。
指摘そのものを否定していません。**同じ関数の 2 つの穴は別々に数えてください。**

## 6. UNVERIFIED（AXIS 外・MISSING や 0 へ読み替えないでください）

- submitted index の行数と並びファイルの現在値 — **横読み禁止で読めず、front door にそれを返す口も無い**。
  ∴「段②が何行舐めたか」は**返せない**（`CC_2DER_USAGE_GUIDE.md §2` の言う「返せないが結果」）
- `SENIOR_CALL_SKIPPED` が `PROCESS_EVENT_KINDS` に無い件 — 別 AXIS。語の追加には裁定が要る
- `_GATES_MAX=200` の脱落 — 段③に到達しなかったので**今回は起きていない**（未検証のまま）
- `record_stages` の 111.5 秒が正しい費用かどうか — 測っただけで、妥当性は判定していない

## 7. 一本を止めるか

**私からは止めません。** 上の 5 条件（証拠の偽 / authority 侵害 / 不可逆破壊 / COMPLETE 虚偽成立 / 暴走）に当たる事象は
観測されていません。走行中に増えた記録は etrace と `receive_finished` の受領のみで、state は 1 件も動いていません。
