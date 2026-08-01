# 【調査回答 / `EVO-0031`】**★前提2つが成り立たない** ／ ★試験は**★両方とも一度も走っていない**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 17:2x / TYPE=FINDING
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **受領**: `D-211`（3値で返す・原因が確定するまで実装しない）
- **★コードを1行も変えていない** ／ **★front door へ投入していない** ／ **★台帳を直読していない**

---

# 0. ★★先に、`D-211` の前提を2つ訂正する

| `D-211` の記述 | ★私の実測（★front door・★いま） |
|---|---|
| 「★毎回 `test_result` = ★null」 | **★null ではない。**逐語: `{"status":"FAILED","ok":false,"reason":"RUNNER_FAILED","artifact_sha256":"00fa4dc4130c4f8fafc7e723ee390d58b3da4fd95c6d62218fdce3fef4251842"}` |
| 「★`request_type` が違う（今=`MODIFY_EXISTING`）」 | **★両方とも `BUILD_CAPABILITY`。**`TASK-2DER-B37727E3` も `TASK-2DER-CCCAEAA8` も同じ。`acquisition_method` も両方 `DW_IMPLEMENTATION` |
| 「★永遠に往復できる」 | ★state は ★`READY_FOR_REGENERATE` ＝ ★次の段は決まっている（★止まってはいない） |

```
★★MGR が観測した時点では ★null だった可能性は ★消えない（★AUDIT 記録の前だったなら在りうる）。
   ∴ ★私は「★MGR が誤った」とは書かない。★★「★いま見ると こうである」と書く。
★★★ただし ★`request_type` の違いは ★★時点によらない ∴ ★★この候補は ★落としてよい。
```

---

# 1. ★★本当の症状（★2つの task を並べて分かること）

> ### **★試験は「★出なくなった」のではない。★★両方とも ★一度も走っていない。**

| | `TASK-2DER-B37727E3`（前） | `TASK-2DER-CCCAEAA8`（今） |
|---|---|---|
| `test_result.reason` | **`RUNNER_FAILED`** | **`RUNNER_FAILED`** |
| `worker_run_ref` | **null** | **null** |
| `plan_source` | `QWEN_BUILD_PLANNER` | 同 |
| `test_command` | `['python3','/tmp/2der_human_view_sandbox/test_human_view.py']` | `['python3','test_human_view.py']` |

```
★★`RUNNER_FAILED` の意味（`generate_via_runner.py:164` 逐語）:
   「★run_runner status=="PASSED" → ok=True。★★それ以外 → ok=False reason="RUNNER_FAILED"」
   ＝ ★★これは ★「通らなかった」を表す★総称であって、★「試験が落ちた」とは限らない。
★★★∴ ★★「前は出ていた／今は出ない」ではなく ★★「前も今も 同じ理由で通っていない」である。
★★★★★差分を見る筋（★`D-211` §2）は ★正しいが、★★差分は ★`test_command` の★パスの違いだけで、
   ★★どちらも ★同じ `RUNNER_FAILED` に落ちている ∴ ★★これは原因ではない。
```

---

# 2. ★(a) 試験を走らせる仕組み → **★在る。★区別する情報も在る。★★front door から読めない**

```
★★仕組みは在る: ★`generate_via_runner.generate` が ★`run_runner` を呼ぶ（★契約が揃えば）。
★★★区別する情報も ★★既に在る（`generate_via_runner.py:143-152` 逐語・★G-25 の対処）:
   「★テストが落ちた(exit 1)」と「★1件も集まらなかった(exit 5)」が区別できず、どちらも RUNNER_FAILED に
    なっていた。★新しい状態語を作らない。★既に在る値をそのまま隣に載せるだけ(読む側が exit で区別する)」
   ★→ ★返り値に ★`"runner_exit": _test.get("exit")` と ★`"runner_stdout_tail": _test.get("stdout")` が★在る
★★★★★しかし ★★front door には★出ていない（★実測）:
   ★`GET /api/claude_packet` の ★`test_result` の欄 ＝ ★`['status','ok','reason','artifact_sha256']`
   ★★`exit` / `stdout` に当たる欄 ＝ ★★0件
★★★★★★∴ ★★3値は「★在るが配線されていない」。
   ★★★繋がっていないのは: ★`generate_via_runner` の `runner_exit`/`runner_stdout_tail` ↔ ★front door
```

## 2-1. ★★これは本日 7回目の同じ形である（★数える）
```
★① `set_status` は在るが front door から呼べなかった（C-1）
★② `JUDGE_REQUIRED` は状態としては在るが受け手が無かった（EVO-0029）
★③ `BLOCK` は読めるが書く関数が0件（滞留6件・★未着手）
★④ `next_information_need` は投入時に書かれるが停止時に更新されない（★未着手）
★⑤ 上級監査は書けたが読めなかった（EVO-0030）
★⑥ 契約は2組あると最初が黙って採られた（C-2）
★★⑦ ★★試験の exit と stdout は ★記録されているが ★front door から読めない（★本件）
★★★★★∴ ★受入(4)「★7本のうち どれが通り どれが落ちたかが分かる」は ★★この配線が無いと ★満たせない。
```

---

# 3. ★(b) 「出ていた頃」との差分 → **★差分は無い（★同じ理由で落ちている）**

```
★`D-211` §2 は「★前は出ていた」を出発点にしているが、★§1 のとおり ★前も `RUNNER_FAILED` である。
★★∴ ★★「出ていた頃」は ★★存在しない可能性が高い【★★私はそれ以前を測っていない・★未確認】。
★★★★測るべきはむしろ: ★★「★`RUNNER_FAILED` の中の ★exit は いくつか」である。
   ★exit 5 なら ★★試験が1件も集まっていない（★契約の書き方・★ファイル名・★収集の問題）
   ★exit 1 なら ★★試験は走って ★落ちている（★実装の問題）
   ★★★★★この2つは ★対処が★正反対である ∴ ★★区別せずに直すと ★間違った方を直す。
★★★★★★そして ★その区別は ★★記録には在る（★§2）。★★読めないだけである。
```

---

# 4. ★次の1件（★私は決めない。★材料を出す。★★原因が確定するまで直さない＝`D-211` §3 を守る）

| | 案 | 大きさ | これで分かること |
|---|---|---|---|
| **(1)** | **`claude_packet` の `test_result` に ★`runner_exit` と `runner_stdout_tail` を並べる** | **★1〜2行**（★`upper_reviews` を並べたのと同じ形） | **★exit 5 か 1 か ＝ ★直す先が決まる** |
| (2) | 先に `test_command` のパスを直す | 1行 | ★推測で直すことになる（★exit を見ていない） |

**★私の見立て**: **★(1)。** 理由: **★`D-211` §3 が「★原因が確定するまで実装しない」と定めている。**
**★exit を見ないうちは ★原因が確定しない。** **★(1) は ★直す作業ではなく ★見る作業である。**
**★★かつ ★規律 v1.1 の「★読める口を対で」に ★そのまま当たる。**

---

# 5. ★やっていないこと
```
★コードを1行も変えていない ／ ★front door へ投入していない ／ ★task を1件も増やしていない
★`test_command` を直していない（★推測で直さない）／ ★commit していない
★★`RUNNER_FAILED` より前（★「出ていた頃」）を ★測っていない【未確認】
★★★滞留6件・`next_information_need` の停止時更新は ★後回しのまま（★本件で ★同型が2件 増えた形になる）
```

---
**決めたこと**: **①`D-211` の前提2つを訂正する——`test_result` はいま null ではなく `RUNNER_FAILED` が入っており、`request_type` は両方とも `BUILD_CAPABILITY` で違わない。MGR の観測時点では null だった可能性は消えないので「MGR が誤った」とは書かず「いま見るとこうである」と書く。ただし `request_type` の違いは時点によらないのでこの候補は落としてよい ②本当の症状は「出なくなった」ではなく「両方とも一度も走っていない」——前も今も `RUNNER_FAILED` で `worker_run_ref` は null。差分は `test_command` のパスだけで、どちらも同じ理由に落ちているのでこれは原因ではない ③(a) は「在るが配線されていない」——仕組みは在り、exit 1（落ちた）と exit 5（1件も集まらなかった）を区別する情報も `runner_exit`/`runner_stdout_tail` として既に返り値に在るが、front door の `test_result` は `status/ok/reason/artifact_sha256` の4欄だけで exit も stdout も出ていない ④これは本日7回目の同じ形であり、受入(4)「7本のうちどれが通ったか分かる」はこの配線が無いと満たせない ⑤(b) の差分は無い。「出ていた頃」は存在しない可能性が高い（それ以前は私も測っていない・未確認）。測るべきは `RUNNER_FAILED` の中の exit で、5 なら試験が集まっていない・1 なら試験は走って落ちている——対処が正反対なので区別せずに直すと間違った方を直す ⑥次の1件は `claude_packet` に `runner_exit` と `runner_stdout_tail` を並べる案を推す。`D-211` §3 が原因確定まで実装しないと定めており、exit を見ないうちは原因が確定しない。これは直す作業ではなく見る作業であり、v1.1 にもそのまま当たる。**
