# 【押した結果】**★PLAN が成功すると、★その成功が run gate を閉じる** — ★GENERATE へは構造的に進めない

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-31 21:5x / TYPE=FINDING
- **運用方針 確認済（版: v2.9）** ／ **受領**: `D-189`（通す・条件3つ）／ **★直していない**（★条件③）
- **★新しい名前で置いた** ／ **★報告は `D-189` §5 の項目のみ**

---

# 1. ★押した。★0段 進んだ

```
★対象: TASK-2DER-E8F8CA7B（★state = READY_FOR_IMPLEMENTATION ＝ ★次は GENERATE）
★POST /api/run_next を ★6回。★★6回とも ★refused。★dispatched=false。★state 変化 0。
★逐語（返り値）: {"refused": true, "blocked": false, "runnable": ★false, "dispatched": false,
   "reason": "task TASK-2DER-E8F8CA7B is not the current runnable submit task (★TASK-2DER-E8F8CA7B)"}
★★★★メッセージは ★同じ id を「違う」と言っている ＝ ★原因の書き方が違う（★§3）
```

---

# 2. ★★原因（★決定論。★ソースの逐語で示す）

> ### **★`PLAN` の actor は `MANAGER` である。★gate は「★今 実行した actor」で次の可否を決める。★∴ PLAN が成功すると gate が閉じる。**

```
★① `dev-workcell/dw/dispatch.py:79` 逐語: `nlo = next_legal_operation(task_id)`
   ＝ ★`nlo` は ★これから実行する段のもの ∴ ★戻り値の `nlo` は ★「今 実行した段」である

★② 同 `:116-118` 逐語（★Qwen が計画を書いて成功した経路）:
      return {"dispatched": True, "operation": op, "actor_role": role, ...,
              "nlo": nlo, "auto_served": "QWEN_BUILD_PLANNER"}
   ＝ ★成功しても ★`nlo` は ★PLAN のまま。★`role` は ★`MANAGER`（★`_MAP`: CREATED→PLAN(MANAGER)）

★③ `twoder/webui.py:717` 逐語:
      _LAST.update({"runnable": step["nlo"]["actor_role"] not in ("MANAGER", "CLAUDE_SENIOR")
                    and step["nlo"]["operation"] not in ("NONE", "BLOCKED"), "task_id": tid})
   ＝ ★`"MANAGER" not in ("MANAGER","CLAUDE_SENIOR")` → ★★False

★★★∴ ★PLAN を ★Qwen が★1人で書き切っても、★gate は ★`runnable=False` を書き込む。
★★★★∴ ★`/api/run_next` は ★以後 ★何回 押しても refuse する。★GENERATE へは★到達できない。
★★★★★gate を開け直す唯一の口は ★`/api/submit`（`webui.py:666`）＝ ★★新しい task が立つ。
   ∴ ★★同じ task を ★GENERATE 以降へ進める経路が ★存在しない。
```

## 2-1. ★私が最初に疑って、★外したもの（★書いておく）
```
★★私は ★「webui の再起動で `_LAST` が消えた」と読んだ。★外れた。
   ★webui の起動は 18:40:57、★投入は 18:43 台 ∴ ★投入は再起動の★後である。
★★★`blocked=false` かつ ★id が一致している ∴ ★残る条件は ★`runnable=false` だけであり、
   ★そこから ★§2 の3行に辿り着いた。
```

---

# 3. ★もう1件（★小さいが、これが今日 我々を止めた）

```
★`webui.py:696` 逐語:
   reason = (gate["reason"] or f"task {tid} is not the current runnable submit task ({gate['task_id']})")
★★refuse の条件は ★3つ（blocked / not runnable / id 不一致）だが、
   ★メッセージは ★id 不一致の文だけ である。
★★★∴ ★`runnable=false` で拒否されたのに ★「id が違う」と表示され、★同じ id が2つ並ぶ。
★★★★これは ★直せば1行だが、★★条件③により★直していない。
```

---

# 4. ★`D-189` §5 の報告項目

| # | 項目 | 今回 |
|---|---|---|
| **1** | 2DER だけで完了した工程 | **★0段**（★1段も進まなかった） |
| **2** | Claude が介入しないと止まる工程 | **★GENERATE 以降すべて。★理由は方針ではなく★構造である**（§2） |
| **3** | Claude の仕事は増減 | **★今回は増減なし**（★押しただけ）。★ただし **★減らせる箇所が1つ 特定された** |
| **4** | 一時的補助か永久か | **★現状は「★永久に Claude を要求する」形になっている。**★意図かどうかは★私には判定できない |
| **5** | 2DER 主体率 | **★0%** |

**★各段の actor**
```
★押した: ★Claude（私）／ ★進んだ段: ★無し ／ ★書いた actor: ★無し
★★前回まで: ★観測＝2DER ／ ★PLAN＝2DER（`QWEN_BUILD_PLANNER`）／ ★GENERATE 以降＝★未到達
```

---

# 5. ★★これは Taka の指標に直接 効く（★今日いちばん大きい発見だと思う）

```
★★Taka の最終目標（逐語）: 「★2DER が Observation / PLAN / Generate / Audit / 修正提案 /
   Ledger 更新 まで自律して実行し、★最後に私へ『承認しますか』だけを聞いてくる状態」
★★★今日まで我々は「★GENERATE を押していないから進んでいない」と説明してきた。
★★★★★実際は ★押しても進まない。★★PLAN の成功そのものが★次段を閉じている。
★★∴ ★「Claude が押していないから」ではなく「★2DER が自分で先へ行けない造りだから」である。
★★★これは ★`G-89`（PLAN 段への監査分離）より ★上流の1件である。
```

## 5-1. ★★ただし断定しないこと
```
★★これが ★意図した安全装置なのか ★取り違えなのかは ★私には決められない。
   ★意図の可能性: ★「Claude が submit した文脈でしか DW を進めない」という★暴走止めである読み方
   ★取り違えの可能性: ★「今 実行した段の actor」で判定しており、★「次の段の actor」ではない
★★★∴ ★私は「バグである」と書かない。★★「構造としてこうなっている」までを書く。
★★★★直し方も書かない（★条件③・★裁定の前に案を出すと手番を飛ばす）。
```

---

# 6. ★やっていないこと
```
★直していない（★条件③）／ ★コードを1行も変えていない ／ ★新しい task を立てていない
★★★`/api/submit` を押していない（★押せば gate は開くが ★★別 task になる ＝ ★今回の1件ではなくなる）
★成果物を production に入れていない（★条件②。★そもそも生成に至っていない）
★GENERATE の結果を PLAN 規則の評価に混ぜていない（★条件①。★結果が存在しない）
★測定を1本も足していない ／ ★commit していない
★★保留はそのまま: Ledger ／ 図 ／ (c) の patch ／ `G-96` ／ `G-98`
```

---
**決めたこと**: **①`run_next` を6回 押して 0段 進んだ。6回とも refused で、`blocked=false`・`runnable=false`・id は一致していた ②原因は決定論で特定した——`dispatch_once` が返す `nlo` は「今 実行した段」であり（`dispatch.py:79`）、Qwen が計画を書き切った成功経路でも `nlo` は PLAN・`actor_role` は MANAGER のまま（`:116-118`）。`webui.py:717` はその actor で次の可否を決めるので `"MANAGER" not in ("MANAGER","CLAUDE_SENIOR")` が False になり、★PLAN の成功そのものが gate を閉じる ③gate を開け直す口は `/api/submit` だけで、それは新しい task を立てる ∴ 同じ task を GENERATE 以降へ進める経路が存在しない ④私は最初「再起動で `_LAST` が消えた」と読んで外した（投入は再起動の後だった）⑤拒否メッセージが3つの条件のうち id 不一致の文しか持たないため、同じ id が2つ並ぶ表示になっていた——直せば1行だが条件③により直していない ⑥報告5項目は 2DER 単独 0段／GENERATE 以降すべてが構造的に停止／Claude の仕事は増減なし／現状は永久に Claude を要求する形／2DER 主体率 0% ⑦これは Taka の指標に直接 効く——今日まで「押していないから進まない」と説明してきたが、実際は押しても進まない。ただし意図した安全装置か取り違えかは私には決められないので「バグである」とは書かず、直し方も書かない。**
