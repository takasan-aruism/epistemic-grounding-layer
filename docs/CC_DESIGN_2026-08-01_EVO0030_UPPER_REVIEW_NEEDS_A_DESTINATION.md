# 【BUILD SPEC / `EVO-0030`】上級監査に**★行き先**を与える — ★読める口を★対で名指しする（v1.1）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 12:5x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **裁定**: `D-207` §3（4条件・受入4つ）
- **この .md がまだ .md である理由**: 指示を台帳へ渡す口が無いため（★`EVO-0022` / C-2）
- **★増える管理対象 0** ／ **★私はコードを1行も変えていない**

---

# 0. ★★MGR の代行判定を再検証した（★`D-207` §4 の要求）— **★一致した**

```
★私の独立実測（★front door のみ・★MGR の文書を根拠にしていない）:
   ★`test_result` 逐語: {"status":"FAILED","ok":false,"reason":"RUNNER_FAILED",
                        "artifact_sha256":"1046b764e3927744497c32f27eaa017e912c51aaf05cb6949a5c23fcb6a8cd40"}
   ★`worker_run_ref`: ★null ／ ★`packet.target_file`: `human_view.py`
★★★∴ ★成果物が★動いた記録が★1件も無い ∴ ★★`FAIL` である。★MGR の判定と★一致した。
★★★★★★理由は独立である（★私は `RUNNER_FAILED` と `worker_run_ref: null` から出した）。
★★★★★★★★ただし ★MGR も私も ★Claude である ∴ ★★これは「2者一致」であって「独立監査」ではない。
   ★`single_party: true` と★書いてあるのは正しい。★★消さない。
```

## 0-1. ★ついでに見つけた1件（★掘らない・★材料として置く）
```
★★`findings` が ★★0件である。★試験は ★FAILED なのに ★最新の監査は ★指摘を1件も出していない。
★★★1回の観測 ∴ ★私は原因を書かない。★★`EVO-0030` の受入 (a) を測るときに ★同時に見えるはずである。
```

---

# 1. ★いま何が起きていないか（★2つ。★別々に書く）

| | 症状 | 実測 |
|---|---|---|
| **★読めない** | `review` 本文が front door に出ない | `GET /api/state` の**★全19欄**に `review` ★0件（★打ち切り無し）／`claude_packet` も ★0件 |
| **★効かない** | `FAIL` を入れても state が動かない | `workcell.py:183-184` 逐語 `elif ph == "UPPER_REVIEW": view["upper_reviews"].append(e); ★state = "READY_FOR_UPPER_REVIEW"` ＝ **★verdict を見ずに★常に同じ state** |

```
★★★∴ ★上級監査は ★★「記録される」だけの段になっている。★入れても ★出口が1つしかない。
```

---

# 2. ★やること①: **★効くようにする**（★`AUDIT`/`DISPOSE` と同型）

**★参考にする既存の形（`workcell.py:172-178` 逐語・★DISPOSE の分岐）**
```python
elif ("ACCEPTED" in verdicts) or ("PARTIAL" in verdicts) or (not tests_ok):
    state = "READY_FOR_REGENERATE"      # accepted/partial or failing test -> rework
elif "REMAINS" in verdicts:
    state = "JUDGE_REQUIRED"            # review 後も未解決
else:
    state = "READY_FOR_UPPER_REVIEW"    # 全 REJECTED + tests ok = false positive、code は妥当
```

**★`UPPER_REVIEW` に置く分岐（★4本。★本数と条件は私が決める・`D-207` §3-①）**
```python
elif ph == "UPPER_REVIEW":
    view["upper_reviews"].append(e)
    v = ("%s" % ((pl.get("review") or {}).get("verdict") or "")).upper()
    if   v == "PASS" and view.get("last_test_passed"):  state = "READY_FOR_UPPER_REVIEW"  # ★完了 gate へ（★§2-1）
    elif v == "FAIL":                                   state = "READY_FOR_REGENERATE"    # ★作り直しへ
    elif v in ("INDETERMINATE", ""):                    state = "JUDGE_REQUIRED"          # ★人へ上げる
    else:                                               state = "JUDGE_REQUIRED"          # ★知らない値も人へ
```
```
★★★★`PASS` なのに ★試験が通っていない場合は ★上の1本目に入らない ∴ ★4本目（人へ）に落ちる。
   ＝ ★★「通ったと言われたが、通っていない」を ★機械が拾う。★★これは★意図した設計である。
★★★★★★`verdict` を ★`.upper()` で正規化する（★大小で挙動を変えない）。★知らない値は ★人へ上げる（★fail-closed）。
```

## 2-1. ★`PASS`＋試験通過が「完了へ動く」形（★受入 (b)）
```
★`dispatch.py:54-55` 逐語:「★READY_FOR_UPPER_REVIEW with an already-recorded upper_review + no blockers
   => the gate is next」＝ ★★既に `PROPOSE_COMPLETE` へ進む道が★在る。
★★∴ ★`PASS`＋試験通過は ★`READY_FOR_UPPER_REVIEW` のままでよい。★★新しい state を作らない。
★★★受入 (b) は ★「`next_operation` が ★`PROPOSE_COMPLETE` になること」で測る（★state 名では測らない）。
```

---

# 3. ★やること②: **★読めるようにする**（★v1.1・★書く口に読む口を対で）
```
★`webui.py:221` 逐語 `"findings": W._latest_findings(view),` の★隣に ★1行 足す:
   ★`"upper_reviews": view.get("upper_reviews") or [],`
★★★これは ★作るのではなく ★★並べるだけである（★同じ形が既に在る）。
★★★★★読む口の名指し（★v1.1 の要求）: ★`GET /api/state?task_id=…` の ★`upper_reviews` 欄。
```

---

# 4. ★受入（★`D-207` §3。★緩めない）
```
★(a) ★`FAIL` を ingest → ★`dw_state` が ★`READY_FOR_REGENERATE` へ★動く
★(b) ★`PASS`＋試験通過 → ★`next_operation` が ★`PROPOSE_COMPLETE` になる
★(c) ★入れた `review` の★本文が ★`GET /api/state` の ★`upper_reviews` から★読める
★(d) ★`INDETERMINATE` / 知らない値 / `PASS` だが試験未通過 → ★`JUDGE_REQUIRED`（★人へ上がる先が決まっている）
★★★★★(a)(b)(d) は ★★試験用の task で確かめてよい。★★`TASK-2DER-B37727E3` は ★(a) と (c) だけに使う
   （★★本番の1件を ★試験で往復させない）
★★★★★★投入前に予告を書く: ★(a)〜(d) の予想 ／ ★変更行数（★本体4〜6行＋読む口1行の見込み）
```

# 5. ★誰が書くか（★`D-207` §3-③）
```
★★★これは ★DW の本番コードである ∴ ★★原則 ★worker に書かせる。
★★★★ただし ★★worker は ★本番モジュールを import できない（★開発者規律 第2章）
   ∴ ★`workcell.py` の分岐を ★worker に書かせる形は ★成り立たない見込み【★未確認】。
★★★★★∴ ★★あなたが書く場合は ★★「★Claude が書いた」と ★行数つきで書き、★2DER の実績に★数えない。
   ★★★★★★かつ ★「★worker に書かせられない理由」を ★1行 書く（★C-1 と同じ扱い）。
★★★★★★★★先に worker で試して ★駄目だった、なら ★その事実の方が価値が在る。★試したなら書くこと。
```

# 6. ★禁止 ／ 7. ★報告
```
【禁止】★新しい state 名を作る（★`READY_FOR_REGENERATE`/`JUDGE_REQUIRED` は既存）
        ★`_MAP`/`_ALLOWED` を触る（★`EVO-0029` で済んでいる）／ ★新しい台帳・計器・マーカーを作る
        ★S-3 の依頼文に触る ／ ★commit する ／ ★★`review` の中身を創作する（★判定は設計/監査と MGR）
【報告】1 ★変更行数（★誰が書いたか）／ 2 ★受入 (a)〜(d) ／ 3 ★予告の当否
        4 ★★戻し方（★可逆・`D-207` §3-④）／ 5 ★worker に書かせられたか（★試したか）
        6 ★★`findings` 0件（★§0-1）が ★(a) の測定中に見えたら ★そのまま書く（★掘らない）
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①MGR の代行判定 `FAIL` を独立に再検証し、一致した——`RUNNER_FAILED` と `worker_run_ref: null` から、成果物が動いた記録が1件も無いため。ただし MGR も私も Claude なので「2者一致」であって「独立監査」ではなく、`single_party: true` の明記は正しいので消さない ②ついでに `findings` が 0件であることを見つけた（試験は FAILED なのに最新の監査は指摘0）。1回の観測なので原因は書かず、受入 (a) の測定中に同時に見えるはずとして置く ③いま起きていないことは2つ——`review` 本文が front door に出ない（全19欄で0件）ことと、`FAIL` を入れても state が動かない（`workcell.py:183-184` が verdict を見ずに常に同じ state を返す）こと ④分岐は4本にした。`PASS`＋試験通過→完了 gate へ／`FAIL`→作り直しへ／`INDETERMINATE` と空→人へ／知らない値も人へ。`PASS` なのに試験が通っていない場合は4本目に落ちる＝「通ったと言われたが通っていない」を機械が拾う ⑤`PASS`＋試験通過は新しい state を作らず既存の `PROPOSE_COMPLETE` への道に乗せる。受入 (b) は state 名でなく `next_operation` で測る ⑥読む口は `webui.py:221` の `findings` の隣に1行 足すだけ。v1.1 の要求どおり読む口を `GET /api/state` の `upper_reviews` 欄として名指しした ⑦本番の1件（`TASK-2DER-B37727E3`）は (a)(c) だけに使い、(b)(d) は試験用の task で確かめる ⑧`workcell.py` の分岐は worker に書かせられない見込み（本番モジュールを import できないため）だが未確認。書くなら「Claude が書いた」と行数つきで書き 2DER の実績に数えず、worker で試して駄目だったならその事実を書くこと。**
