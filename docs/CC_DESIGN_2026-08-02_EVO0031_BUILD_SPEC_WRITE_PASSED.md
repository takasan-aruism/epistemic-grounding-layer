# 【BUILD SPEC】`passed` を書く（★1欄・可逆）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-02 02:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.3）** ／ **★9項目 確認済（★§5）**
- **★裁定の在り処**: `ITEM-2DER-EVO-0031` の `status_note`（逐語「★最小・可逆で passed を書く…受入=TASK-2DER-E3B92A8E が COMPLETE に到達する」）
- **★この件の .md は上限超過（★超えたと書いて置く）**

---

## 1. やること（★1箇所・1行）

```python
# twoder/webui.py:327-331（★test_result を作る所）
              "test_result": {"status": "PASSED" if gr.get("ok") else "FAILED",
                              "ok": bool(gr.get("ok")),
                              ★"passed": bool(gr.get("ok")),      # ← ★足す（読み手が読む欄名）
                              "reason": gr.get("reason"), …},
```
```
★読み手（`dev-workcell/dw/workcell.py:139,181` 逐語）: `bool((pl.get("test_result") or {}).get(★"passed"))`
★★`ok` を消さない・変えない（★既存の読み手が在るかもしれない）。★★足すだけ
★★★戻し方: ★この1行を消す。★可逆
★★★★`_run_test` 由来の `test_result`（`live_worker_runtime.py:267`）は ★既に `test` をそのまま載せており
   ★★そちらに `passed` が在るかは ★★★私は確かめていない【★未確認】——★実装が ★同じ形になっているか見ること
```

## 2. ★`passed` を直した後に残る関門（★先に全部 数えた）

`completion_blockers` の全条件（★逐語・6件）:
```
① state が COMPLETE/BLOCKED/JUDGE_REQUIRED でない       → ★②が直れば AUDIT が UPPER_REVIEW へ送る見込み
② implementation run + test_result が存在する            → ★在る（実測）
③ ★last_test_passed が True                             → ★★本件で直す
④ independent audit run が存在する                       → ★在る（QWEN_AUDITOR・実測）
⑤ 最新 findings がすべて disposition 済で未解決が無い     → ★findings 0件（実測）∴ 空
⑥ upper_review run が存在する                            → ★2件 在る（実測）
```
**∴ ★③以外は満たしている見込み。★ただし ★①は ★②を直してから ★再走行しないと確定しない【未確認】**

## 3. ★`complete_and_close` の中身（★裁定「通す前に読ませること」）

```
★`twoder/return_loop.py:46-62` 逐語:
   ★① `W.propose_complete(task_id, obs, …)` を呼ぶ ＝ ★GATE。★blockers が在れば ★例外 → `{"completed": False, "reason": "GATE refused: …"}`
      ★★GATE は ★迂回されない（逐語:「The GATE … refuses if completion_blockers exist — it is NOT bypassed」）
   ★② ★`submit_utterance_ref` が無ければ ★`{"completed": True, ★"loop_closed": False}` で終わる
   ★③ 在れば ★`close_loop(...)` → DW→EGL admission→RRI residual→DS event
★★★∴ ★★`completed` と `loop_closed` は ★別物。★★「COMPLETE に到達した」は ★`completed: True` である
★★★★★`loop_closed: False` でも ★COMPLETE は成立する ∴ ★★両方を報告に書くこと
```

## 4. 受入
```
★(1) `TASK-2DER-E3B92A8E` の `dw_state` が ★`COMPLETE` になる（★Taka の完了条件）
★(2) `complete_and_close` の応答を ★逐語で持ち帰る（★`completed` と `loop_closed` を ★分けて書く）
★(3) 戻せる（★1行を消したら元に戻る）——★戻して確かめ、★また足す
★(4) ★GATE が拒否したら ★その `reason` を逐語で持ち帰る（★★迂回しない・★通ったことにしない）
★★★★進め方: ★`run_next` を ★止まるまで押す。★gate が閉じたら同一依頼文の再投入（★回数と理由を書く）
```

## 5. ★9項目（私の分）
```
1 読める口＝`GET /api/state` の `dw_state`（★確認済）／2 書く口＝既存の `record_generate`（★足すだけ）
3 理由を捨てない＝★GATE の `reason` を受入(4)に入れた／4 作っていないのでは＝★`ok` は在る（★名前が違うだけ）
5 走ったか＝★実装が webui 再起動を確かめる／6 ★★名前＝★本件そのもの（`ok` vs `passed`）
7 依頼と試験の矛盾＝★本件は機構 ∴ 該当なし／8 計器＝★front door の値を見る
★9 ★増える代わりに廃止＝★★「試験が通ったのに作り直しへ送られる」を畳む。★★欄は1つ増えるが ★★空回りの走行が消える
```

## 6. 禁止
```
★`ok` を消す・改名する ／ ★GATE を迂回する ／ ★`completion_blockers` を緩める
★新しい状態語・台帳・計器・エンドポイントを作る ／ ★commit する ／ ★`twoder` 配下で python を動かす
```
