# 宛: 設計 / 監査 ―― HUMAN_BARRIER の原因（修正せず・原因のみ）

## 0. 判定 ―― **3. 実装/配線欠陥**

正確には **役の語彙のずれ ＋ 門のラッチ**。安全境界が正しく人を要求したのではない。

## 1. 対照（5件・投入は全て同じ経路 `submit_next_contract`）

| | task | 契約を書いた | 結果 |
|---|---|---|---|
| ★塞1 | 0FC6A1A0 | MGR（散文） | HUMAN_BARRIER |
| ★塞2 | 749D379A | **DESIGN** | HUMAN_BARRIER |
| ○通1 | 6EA3D63F | DESIGN | COMPLETE |
| ○通2 | 3E9386EF | DESIGN | COMPLETE |
| ○通3 | 87BACCCA | DESIGN | COMPLETE |

**塞がれた側に DESIGN の契約が入っている** ∴「MGR の依頼文だから」は**否定**。

## 2. 現在の状態を比べても原因は出ない（先に潰した筋）

差が出た欄は `task_id` `rthread_id` `split_gates`（案件ごとに違って当然）と
`upper_reviews` `next_operation`（通った側が完了した**結果**）。**比較方法として無効。**

## 3. 機構（正本＝実装を読んで確定）

```python
# twoder/decide_rearm.py（2DER 製・純関数）
if role not in ('CODING_WORKER','INDEPENDENT_AUDITOR'):
    return 'HUMAN_BARRIER'
```
```python
# twoder/webui.py:1531 /api/run_next の末尾
_gate_put(tid, runnable = step["nlo"]["actor_role"] not in ("MANAGER","CLAUDE_SENIOR")
                          and step["nlo"]["operation"] not in ("NONE","BLOCKED"))
```
```python
# 呼ばれる条件（webui・2026-08-18 に MGR が配線）
_v = _DR(_GATES.get(tid) is not None, gate["blocked"], _nlo0["actor_role"], undisposed)
```

**成立する筋:**

1. `CREATED` の次操作は `PLAN` / 役 `MANAGER`。
2. 初回 `run_next` で PLAN が進まないと、`_gate_put` が **`runnable=False` を記録**（役が MANAGER のため）。
3. 以後の `run_next` は `NOT_RUNNABLE` → `decide_rearm` へ。
4. **門は存在する**ので `MISSING_GATE` にならず、役が `MANAGER` なので **必ず `HUMAN_BARRIER`**。
5. **ラッチ** ―― 機械が自力で戻す道が無い。

**通った3件は初回の PLAN が進み、役が `CODING_WORKER` になって `runnable=True` が立った。**
∴ 差は**初回 PLAN が通ったか**であり、契約の作者でも内容でもない。

## 4. 「安全停止」か「役判定が人側へ倒れた」か ―― **後者**

```
_MAP        CREATED → PLAN の役 = "MANAGER"
実際        ★PLAN は Qwen の planner が自動で供する
            （`manager_v0._machine_turn` の逐語コメント＝過去の実測として記録済み）
decide_rearm  役名だけで「人」と判定 → HUMAN_BARRIER
```

**機械が供する工程を、役の名前だけで人の関門とみなしている。**
`decide_rearm` の白名簿は `CODING_WORKER` / `INDEPENDENT_AUDITOR` の2つで、
**`MANAGER`（＝planner が供する PLAN）が漏れている。**

**この配線は 2026-08-18 に MGR（私）が入れた**（`webui.py` の `decide_rearm` 呼び出し）。
**私が入れた門が、私の仕事を止めた。**

## 5. R6 と同じ問題か ―― **★違う。症状が重なるだけ。**

| | 根 |
|---|---|
| HUMAN_BARRIER | **役の語彙のずれ**（MANAGER を人とみなす）＋ 門のラッチ |
| R6 の穴 | **門の状態を task ごとに出せない**（手番は出せる） |

**R6 に門の欄を足してもこの障害は防げない。**早く気づけただけ。**別 item として扱うべき。**

## 6. 残る不明点（隠さない）

**あの2件で「なぜ初回の PLAN が進まなかったか」は私の記録に無い。**
front door は planner の失敗理由を応答に載せる（`webui` の逐語コメント Build 10(S3)）が、
**私の走行スクリプトが状態だけ印字して捨てた。** 再試行は**しない**（Taka 明示）。

**∴ 機構は確定・引き金は未確定。**

## 7. していないこと

解除・迂回・再試行で押し通していない ／ `false_negative_rate` を別経路で実装していない ／
R6 の権限門欄を足していない ／ 22件・33件へ広げていない。**EVO-0019 v1 は停止のまま。**

## 8. 修正が要るなら（最小1点・実施していない）

`decide_rearm` の白名簿に **`MANAGER` を足すか否か**。
ただし **`decide_rearm` は 2DER 製の純関数**であり、MGR が書き換える物ではない。
**変更するなら契約経路で作り直す。** 裁定は Taka。
