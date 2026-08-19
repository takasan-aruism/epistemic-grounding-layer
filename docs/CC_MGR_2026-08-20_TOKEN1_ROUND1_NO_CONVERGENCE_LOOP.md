# 宛: Taka ―― **token 1 の 1周目: ★試験は 直らず ／ ★★2DER は 自力で 回り続けられない**

**2026-08-20 00:0x ／ ★SELF_DEV_TOKEN = ★5/5（★まだ 消費していない）**
**★常駐 停止のまま ／ ★twoder HEAD = `3dd7d02`（★実行の 前後で 不変）**

---

## 1. ★投入までに 2回 差し戻された（★2DER の 門が ★私に 向いて 作動）

```
★1回目 = RRI_INTENT_HOLD ／ request_type = OBSERVE_CURRENT_STATE
★2回目 = RRI_INTENT_HOLD ／ request_type = MODIFY_EXISTING（★出所を ★散文で 書いた）
★★3回目 = ★通過（DW_IMPLEMENTATION / runnable=True）
          ＝★2DER が 返した 記録ID（DE-0484 等）を ★明示した とき だけ
★門の 正体 = `submit.py:482-491` ／ `rri.intent_strategy` の 合議が `PREMISE_PROBE`
   逐語「required to proceed: 依頼が 前提に している 事実が 記録の どこに 在るか（ID または ファイル名）」
★★＝ ★欠陥では ない。★証拠規律の 門が ★私(MGR)に 向いて 効いた。
```

## 2. ★1周の 結果 ―― **★試験は 通らなかった**

**`TASK-2DER-92FE6932`（★私は 原因も 直し方も 与えていない）**

```
★1 tick で 進んだ 範囲 =
   CREATE → PLAN → GENERATE → AUDIT → DISPOSE → UPPER_REVIEW
   → REGENERATE → AUDIT → DISPOSE → UPPER_REVIEW  ＝ ★rework 1回
★GENERATE   passed=False ／ exit=1 ／ sha=1585029a0921 ／ ★2 failed, 2 passed
★REGENERATE passed=False ／ exit=1 ／ sha=d2033bf4f768 ／ ★2 failed, 2 passed
★落ちた 試験は ★入れ替わった:
   前回 = test_malformed_json_source ／ test_signature_mismatch_handling
   今回 = ★test_valid_request ／ test_signature_mismatch_handling
★AUDIT findings = 各1件（test_failure）
★target_workspace = `sandbox/workspace`（★実 repo では ない）
★★twoder HEAD = 3dd7d02（★commit 0 ／ push 0 ＝ ★安全な単独実行口が 効いている）
```

```
★★＝ ★2DER は 実装と 試験の ★両方を 書き直したが ★収束しなかった。
★★＝ ★『動かない』のでは ない。★『動いて 落ち続けている』。
```

## 3. ★★露出した 欠落 ―― **自力で 回り続ける 口が 無い**

```
★いまの 状態 = JUDGE_REQUIRED ／ rework_count = 1 ／ upper_reviews = 2
★next_operation = UPPER_REVIEW ／ actor_role = CLAUDE ／ claude_barrier = ★True
★★`should_call_senior` = {"call": ★false, "reason": ★"no_progress_since_last_review",
      last_review_ordinal: 3878, latest_input_ordinal: 3877}
```

**★意味（★事実の 連鎖）:**

```
★① 1 tick で 回れるのは ★rework 1回まで（★max_ops=12 の 中で 2巡して 終端）
★② 終端 `JUDGE_REQUIRED` の 次は `UPPER_REVIEW` で ★claude_barrier=True
★③ その 上級監査は ★guard が「前回以降 新しい 入力が 無い」として ★呼ばない
★★∴ ★何度 tick を 叩いても ★state は 動かない
★★∴ ★次の 一手は ★『新しい goal を 投入する』こと ―― ★それを するのは ★いま 私(MGR)
★★＝ ★★『試験が 通るまで 自分で 回り続ける』口が ★存在しない。
★（★同じ 形は `TASK-2DER-7D461717` でも 実測済み ＝ ★2回目の 再現）
```

## 4. ★token の 扱い（★私の 判断では なく 定義に 照らす）

**Taka 定義（逐語）:**
> 1 token は、1つの停止点 → goal化 → 原因調査 → PLAN → 変更生成 → TEST/AUDIT
> → 実repo反映 → 再実走 → 次停止点または解消確認 の1周に対して消費する。

```
★到達 = 停止点 → goal化 → PLAN → 変更生成 → TEST/AUDIT
★★未到達 = ★実repo反映（★sandbox の まま）／ ★再実走 ／ ★解消確認
★★∴ ★1周は 完了していない ∴ ★token は ★消費していない（★5/5）
```

## 5. ★決めていただきたいこと（★2つ・★私は 選びません）

```
★(あ) ★同じ停止点の まま ★もう1回 goal を 投入して 回す
      （★私が 毎回 投入する ＝ ★『Claude が 回している』形が 残る）
★(い) ★『自力で 回り続ける 口が 無い』を ★自己開発ループの 欠落として 扱い、
      ★その口を 作ること 自体を 次の goal に する
      （★但し ★それも 私が 投入する ∴ ★最初の 一押しは 消えない）
★★どちらも ★token の 数え方に 影響する ∴ ★Taka の 判断。
```

## 6. していないこと

```
★原因 0 ／ 直し方 0 ／ 骨格 0 ／ 封印試験 0 ／ 実装 0 ／ 修正案 0
★run_next 0 ／ 手動前進 0 ／ 常駐 再開 0 ／ `_place_and_commit` 改造 0
★実 repo への 書き込み 0（★HEAD 不変で 実証）
```
