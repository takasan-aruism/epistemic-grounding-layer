# declared — 返された欠損1点の修理: `PLANNER_OUTCOME_DISCARDED_ON_RUN_UNTIL_BARRIER`

発: MGR ／ 宛: ESDE Evaluation 専任監査 ／ **✔ は付けていません**
開発者規律 確認済(`2DER_DEVELOPER_DISCIPLINE_v1.0` / `TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3`)
**★これは実装の前に置く1枚。★コードはまだ1行も変えていない。**

```
item      ITEM-2DER-EVO-0081 の1件のみ(1 AXIS = 1 item)
AXIS      CREATED_TASK_PLAN_ADMISSION（★継続・新 AXIS は立てない）
           = 2026-08-21 11:08:18 ESTABLISHED / 11:43:03 R1 も認定(ETR-a5886e3e2de8)
直す欠損   ★1点のみ = PLANNER_OUTCOME_DISCARDED_ON_RUN_UNTIL_BARRIER
測ったHEAD twoder 2395cc1 / dev-workcell 68c3b4c / egl 7cb61ec
```

## 1. 何が未達か（監査の逐語を受ける）

declared §1 SCOPE の exit は2つある。

```
exit  dispatch_once が PLAN を機械で処理し W.record_plan が走る
      ★または BUILD_PLANNER が fail-closed で barrier に落ちたという記録が残る
```

**後半が未達。** 残っているのは「落ちた」（`stopped_at_stage=PLAN` / `gate_cause=""`）だけで、
**「なぜ落ちたか」が残っていない**。今回それを得るために、私は `verify_task` を**別途叩いた**
＝**計器ではなく人が補った**。

## 2. 全件調査（作用起点・探した範囲を併記）

**探索範囲** = `twoder dev-workcell` の `*.py` 全件（`grep -rn "planner_outcome"`）。

| | 実測 | 状態 |
|---|---|---|
| 作る側 | `dw/dispatch.py:103`(初期化) `:145`(代入) `:167`(barrier の戻り値) `:182`(trace の各段) | PRESENT |
| その意図 | `dispatch.py:101` 逐語「**Build 10: planner の失敗理由を捨てない。`planner_outcome` は常にキーとして置く**」 | PRESENT |
| 運ぶ側 | `webui.py` の `/api/run_until_barrier` は `{"trace": out["trace"], ...}` を返す ∴ **各段の `planner_outcome` は応答に載っている** | PRESENT |
| 読む側 | **`twoder/manager_v0.py` に `planner_outcome` の出現 0行**（監査の実測と一致・私も再確認） | **ABSENT** |

**∴ 値は既に常駐の手元まで届いている。捨てているだけ。**

## 3. 因果鎖

```
① dispatch_once   planner を呼ぶ → 失敗 → planner_outcome に raw を入れて barrier へ
② run_until_barrier  trace の各段に planner_outcome を積んで返す(dispatch.py:182)
③ webui           trace をそのまま HTTP 応答に載せる
④ manager_v0.tick res を受け取る … ★ここで捨てる(_record は自分の decide_tick の結論だけ)
⑤ 記録            etrace に「落ちた」は残るが「なぜ」は残らない
```

**★止まっている点は④。**

## 4. ESDE 宣言（実装前）

```
EQUALITY   canonical形式 = planner_outcome(None または dict)。
           ★identity rule = trace の段の並び順(task_id ではない=1周に複数段ある)
           producer=dw/dispatch.py / consumer=★0
           ★None(planner を呼ばなかった) と {"recorded": False,...}(呼んで失敗) は
           ★別の意味 ∴ None を落とすと2つが畳まれる → status = 欠損はあるが CONFLICT ではない
SYMMETRY   required 2(writer / reader) / present 1 / missing 1
           missing_ID = PLANNER_OUTCOME_HAS_NO_READER
LINKAGE    L1 dispatch → trace          observed(dispatch.py:182)
           L2 trace → HTTP 応答          observed(webui)
           L3 HTTP 応答 → manager の記録  ★BROKEN(本件)
           declared 3 / observed 2 / broken 1
HIERARCHY  required 2 (1)足場は運ぶだけ・判断を書かない (2)新しい台帳/口/語彙を作らない
           passed 2 / violation 0
```

## 5. 置こうとしている最小差分（★まだ置いていない）

```
twoder/manager_v0.py の tick 内、既存の _record(d, {...}) の extra に1欄 足すだけ
  "planner_outcome": [t.get("planner_outcome") for t in (res.get("trace") or [])]
```

- **要約・整形・切り詰めをしない**（`dispatch.py:101` の逐語を守る）
- **`None` を捨てない** ―― 段ごとにそのまま並べる。`None`（呼ばなかった）と
  `{"recorded": False, ...}`（呼んで失敗）を畳まない
- **新しい口 0 ／ 新しい台帳 0 ／ 新しい語彙 0 ／ 判断 0行**（既存 `_record` に欄を足すだけ）
- **既存の欄は1つも変えない**（追加のみ）

## 6. R2 DENOMINATOR（実装前に測れる分）

```
現在  manager_v0.py 内の planner_outcome 出現 = 0 行
      ∴ 常駐経由で barrier に落ちた周の「なぜ」が残っている件数 = ★0 / 全件
目標  常駐が1周して barrier に落ちたとき、その周の記録に理由が1つ以上載ること
```

## 7. R4 — この差分で壊してはいけないもの

```
①既存の欄(action / task_id / reason / handed_to / phase / dw_state_before / dw_state_after /
  stopped_at_stage / gate_cause)が1つも変わらないこと
②_record が失敗しても常駐が止まらないこと(既存の try/except + journal 1行の形を壊さない)
③planner_outcome が大きい場合に ★黙って切られないこと
  ―― ★UNVERIFIED: etrace 側の上限を私はまだ測っていない。実装後に実測して報告する
```

## 8. DESIGN_HOLD の判定

**推測が残っている点＝1（§7③ の上限）。** ただしこれは**実装後に実測できる**種類で、
値を運ぶこと自体の可否には影響しない（切られたら切られたと分かる形で報告する）。
∴ **DECISION = GO**。

## 9. 触っていないもの

`dispatch.py`（作る側は既に正しい）／ `decide_rearm_v2` ／ `_MAP` ／
前 AXIS の REARM 263 ／ `_GATES_MAX` ／ `SENIOR_CALL_SKIPPED` ／ EVO-0082 の DISPOSE ／
`PLAN_AUTHOR_IDENTITY_HAS_NO_READER`（★監査の指示どおり**別件として数える**・本件では直さない）／
未commit 30件 ／ 未push ／ 台帳 mismatch ／ D188・D190。
