# 【BUILD SPEC】`run_next` を**1回だけ押す** — **★コードを1行も変えない（★修正ではなく確認）**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-31 01:3x / TYPE=BUILD_SPEC
- **運用方針 確認済（版: v2.8）** ／ **正典**: `TAKA_2026-07-31_RUNTIME_INSPECTION_COMMON_BASE_ORDER.md` ／ **裁定**: `CC_MGR_2026-07-31_D146_…md`
- **★これは何に対して発火するのか**: **★`TASK-2DER-0C458F38` ただ1件。★他の task を押さない。**

## ★なぜやるのか（★1行）
```
★task は CREATED（PLAN 待ち）で止まっている。★我々が押していないからである。
∴ ★「Task → Runtime が流れない」と確かめたわけではない。★「流していない」だけである。
★押せば分かることを、★推測で書かない（運用方針 §4-13）。
```
**★これは修正ではない。★コード変更 0行 ∴ 正典の「一度に一箇所だけ修正」「設計変更禁止」「能力追加禁止」に触れない。**

---

# 1. ★やること（★これだけ）

```bash
cd /home/takasan
T=$(cat twoder/.access_token); B="http://100.107.6.119:8770"
curl -s -m 900 -u "taka:$T" -X POST "$B/api/run_next?task_id=TASK-2DER-0C458F38"
```
| | |
|---|---|
| 回数 | **★1回だけ**（★`task_id` を必ず付ける。★付けないと `refused` になる） |
| 応答 | **★全文を残す**（`-o /dev/null` を使わない） |
| 再投入 | **★しない**（`POST /api/submit` を押さない） |
| **★止まる場所** | **★`PLAN` が終わったら そこで終了。★`GENERATE` へ進まない**（★本番投入は Taka の案件） |

---

# 2. ★受入（★1条件に1つの印。★まとめない）

| # | 受入 | ★示し方 |
|---|---|---|
| **E-1** | 押した結果 | **★返り値の全文。`dispatched` か `refused` か。`refused` ならその `reason`** |
| **E-2** | task の状態変化 | **押す前後の `GET /api/state?task_id=` を並べる**（`dw_state` / `last_completed_op` / `next_operation` / `actor_role` / `claude_barrier`） |
| **E-3** | **★Task → Runtime が流れたか（★核心）** | **★新しい `ARUN-` / `OBS-` が生まれたかを、★下の基準値で判定する**（★生まれたら流れた／★生まれなければ流れていない） |
| **E-4** | PLAN が動いたなら、誰が作ったか | **★`GET /api/claude_packet?task_id=` の `implementation_packet_ref.plan_source`**（`QWEN_BUILD_PLANNER` か `RULE_TEMPLATE_2DER_EVO_0007` か）＋ **`runtime_recovery`** |
| **E-5** | 副作用 | **★`GET /api/tasks` の件数**（★基準 157）。**★増えたら書く** |

## 2-1. ★基準値（★設計が押す前に取った。2026-07-31 01:24:27・★これで判定する）
```
★ARUN の最新 = ARUN-00965（★ARUN-00966 は resolved=false ＝ 未生成）
★OBS  の最新 = OBS-00966 （★OBS-00967  は resolved=false ＝ 未生成）
★task の状態 = CREATED / last_completed_op=CREATE / next_operation=PLAN /
               actor_role=CLAUDE / claude_barrier=true / dispatch_status=PENDING EXTERNAL ACTOR
★tasks 件数  = 157
```
> **★E-3 の判定は決定論である**: **★`ARUN-00966` または `OBS-00967` が `resolved=true` になったか、それだけを見る。**
> **★「たぶん走った」と書かない。★増えていなければ「増えていない」と書く。**

---

# 3. ★やってはいけないこと
```
★コードを1行も変えない（★これは確認であって修正ではない）
★GPU 取得・生出力（blob）・A-3（新形式 trace_key）を★触らない
★他の task を押さない ★再投入しない ★webui を再起動しない
★止まったら直さない・迂回しない ★commit しない
★61本の非回帰は走らせない ★:8005 を自分で叩かない（★2DER が内部で呼ぶのは可。★呼ばれたら1行 書く）
```

# 4. ★止まってよい場所
```
★`refused` が返った → ★そこで終了。★理由をそのまま書く（★gate の都合なら、それが結果である）
★`PLAN` が終わった → ★そこで終了。★次の `run_next` を押さない
★`claude_barrier` で止まった → ★そこで終了。★押し破らない（★Claude が判断する場所である）
★2通りに読めた → ★止めて設計へ聞く
```

# 5. ★報告（★正典の形。★増やさない）
```
★Last PASS / First FAIL / 原因 / 修正内容（★今回は「無し（コード0行）」）/ 次回確認箇所 ★の5行
★受入 E-1〜E-5 は別表で1つずつ
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①`TASK-2DER-0C458F38` に対して `run_next` を1回だけ押す（コード0行・修正ではなく確認） ②核心は E-3＝`ARUN-00966`／`OBS-00967` が生まれたかの決定論判定（設計が押す前に基準値を固定した） ③`PLAN` が終わるか `refused` か `claude_barrier` で止まったら、そこで終了して返す。**
