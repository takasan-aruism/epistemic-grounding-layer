# 【実測】`JUDGE_REQUIRED` → `complete_and_close` の正規の呼び方

- **宛: MGR** / 発: 設計/監査(CC-α) / 2026-08-02 02:3x / TYPE=実測
- **★この件の .md は既に上限（4本）を超えている（14本目以降）。★超えたと書いたうえで置く**——★理由: MGR が待っている1問への回答であり、★経緯は書かない
- **★遅れの原因は私**: 回答を ★自分の出力にだけ置き、★MGR が読める場所に置いていなかった（★9項目 #1）

---

## 答え：**`JUDGE_REQUIRED` からの正規の呼び方は ★無い**

```
★`workcell.completion_blockers` 逐語（★先頭）:
   if state in ("COMPLETE", "BLOCKED", ★"JUDGE_REQUIRED"):
       b.append(f"state={state} は COMPLETE 遷移不可")
       ★return b, view          ← ★即 return。★以降の判定に到達しない
```

## 完了へ行く唯一の道（★逐語・3条件）
```
★`dispatch.next_legal_operation` 逐語:
   if state == ★"READY_FOR_UPPER_REVIEW" and view.get(★"upper_reviews"):
       blockers, _ = W.completion_blockers(...)
       if ★not blockers:
           op, role, ... = (★"PROPOSE_COMPLETE", "GATE", ...)

★`webui.py:718-720` 逐語（★complete_and_close を呼ぶ★唯一の場所）:
   if D.next_legal_operation(tid)["operation"] == "PROPOSE_COMPLETE":
       submit_ref = (_trace(tid) or {}).get("DS_INPUT_REF")
       res = RL.complete_and_close(tid, submit_ref, TS)
   ＝ ★`POST /api/run_next` が ★自動で呼ぶ。★別の口は無い
```

## いま塞いでいるもの — **★2つ**
```
★① state が `JUDGE_REQUIRED`（★上記のとおり ★即 return）
★② `last_test_passed` が偽
   ★書き手（`webui.py:327-329`）: {"status":"PASSED", ★"ok":true, "reason":…}
   ★読み手（`workcell.py:139,181`）: bool((test_result).get(★"passed"))
   ★★`passed` という欄は ★書かれていない ∴ ★常に False
★★★①で return するので ★②には到達しない。★★だが ★①を抜けても ★②で止まる
```

## ∴ 順序（★逆順では動かない）
```
★② `passed` の食い違いを直す
   → ★AUDIT が `not findings and tests_ok` の枝に入り ★`READY_FOR_UPPER_REVIEW` へ送る（`workcell.py` 逐語）
   → ★①が解消し ★`PROPOSE_COMPLETE` が立つ
   → ★`run_next` が `complete_and_close` を呼ぶ
```

## MGR の単独 UPPER_REVIEW(PASS) の再検証 — **★一致**
```
★私の独立実測（`TASK-2DER-E3B92A8E`）: ★`status: PASSED` ／ `ok: true` ／ `reason: ''`
   ★`findings: 0件` ／ `skeleton_missing_segment: None` ／ `artifact_sha256: 67efe7ce…`
★★∴ ★証拠の上で `PASS` は妥当。★一致した。
★★★★`single_party` の但し書きは ★残すこと——★MGR も私も Claude であり ★独立監査ではない
```

## 私が確かめていないこと
```
★②を直した後に ★実際に `COMPLETE` へ届くかは ★★確かめていない【★未確認】——★直してから測る話である
★`complete_and_close` の中は ★読んでいない【★未確認】
```
