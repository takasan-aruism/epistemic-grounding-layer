# 【BUILT 監査 / S-3】報告は概ね一致 — **★ただし「1段ごとに再投入が要る」は★私の実測と食い違う**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 01:3x / TYPE=FINDING
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ **受領**: `CC_IMPL_2026-08-01_S3_CONTRACT_RUN_BUILT.md`
- **この .md がまだ .md である理由**: 監査結果を台帳へ書く口が front door に無いため（C-1）
- **★報告を読む前に自分で測ってある**（`CC_DESIGN_2026-08-01_D198_...` §1）／ **★コードを1行も変えていない**

---

# 1. ★一致した項目（★私の独立実測と突き合わせた。★誤りは見つからなかった）

| 項目 | IMPL の報告 | ★私の実測 | |
|---|---|---|---|
| 停止した状態 | `DISPOSITION_REQUIRED` / next=`DISPOSE` | 同 | ✓ |
| `test_result` | `RUNNER_FAILED` / `artifact_sha256: 479629fd…` | 同（★sha256 まで一致） | ✓ |
| findings | 2件・`AF-…run-0` / `AF-…run-1` | 同（★finding_id まで一致） | ✓ |
| 各段の actor | PLAN=Qwen ／ GENERATE・REGENERATE=`QWEN_LIVECODER` ／ AUDIT=`QWEN_AUDITOR` | 同 | ✓ |
| **書いた行数 0** | 0 | **★独立に確認**: `human_view.py` は5 repo の production 配下に ★0件（`find`・打ち切り無し）／`twoder` の git status ★0 | ✓ |
| 「5段 進んだ」を「できた」と書かない | そう書いている | 同意 | ✓ |
| 自分の計器の誤りを自分で申告 | Monitor が空基準値で落ちていた（`.get()` を文字列に呼んだ） | — | ★正しい作法 |

---

# 2. ★★食い違い1件（★これは Taka の指標に直接 効く数字である）

> ### **★IMPL §3「★1回 dispatch するたびに gate が閉じるので、★再投入が5回 要った」**
> ### **★私の実測: ★submit 1回のあと、★`run_next` を★連続で押して★6段 進んだ。★再投入は 0 回。**

```
★私の走行（★`TASK-2DER-E8F8CA7B`・★同じコード・★同じ webui プロセス）逐語:
   1回目 dispatched=True  op=GENERATE
   2回目 dispatched=True  op=AUDIT
   3回目 dispatched=True  op=REGENERATE
   4回目 dispatched=True  op=AUDIT
   5回目 dispatched=True  op=REGENERATE
   6回目 dispatched=True  op=AUDIT
   7回目 dispatched=False op=BLOCKED   ←★ここで初めて止まった
★★★＝ ★間に ★`/api/submit` を ★1回も挟んでいない。★refused も ★1回も出ていない。
```

## 2-1. ★なぜ食い違うか（★仕組みの側から。★1回の観測で断定しない）
```
★`webui.py:717` 逐語: `_LAST.update({"runnable": step["nlo"]["actor_role"] not in ("MANAGER","CLAUDE_SENIOR")
                        and step["nlo"]["operation"] not in ("NONE","BLOCKED"), "task_id": tid})`
★★GENERATE=`CODING_WORKER` ／ AUDIT=`INDEPENDENT_AUDITOR` ／ REGENERATE=`CODING_WORKER`
   ＝ ★どれも `MANAGER` / `CLAUDE_SENIOR` ではない ∴ ★`runnable` は ★True のまま。★閉じない。
★★★閉じるのは ★`MANAGER`（＝PLAN・DISPOSE）と ★`CLAUDE_SENIOR`（＝UPPER_REVIEW）の後だけである。
★★★★∴ ★「1段ごとに閉じる」は ★仕組みからも ★私の実測からも ★支持されない。
★★★★★★ただし ★IMPL は ★実際に refused を受け取っている（★逐語を載せている）∴ ★嘘ではない。
   ★閉じた原因が ★「dispatch のたび」ではなく ★別に在る。★私は原因を★断定しない。
   ★候補（★未確認）: ★PLAN 直後の1回は閉じる（★`MANAGER`）／★別の submit が割り込んだ／★別プロセス
```

## 2-2. ★なぜこれが重要か
```
★★Taka の成功指標は「★Claude の仕事が減っているか」である。
   ★報告どおりなら ★Claude は ★submit 6回＋押下7回 ＝ ★13回 触っている。
   ★私の実測なら ★submit 1回＋押下7回 ＝ ★8回。★★1.6倍 違う。
★★★∴ ★この数字は ★放置すると ★「2DER は1段ごとに人手が要る」と★誤って残る。
★★★★私は ★どちらが正しいかを ★断定しない。★★両方の実測を並べて置く（★片方だけ書かない）。
```

---

# 3. ★次に確かめること（★1回で決まる。★私はまだやっていない）
```
★★`TASK-2DER-B37727E3` は いま ★`DISPOSE`（★MANAGER）で止まっている。
   ∴ ★★`DISPOSE` を ingest した★直後に ★`run_next` を★連続で押せば、★どちらが正しいか★1回で分かる:
   ★連続で進む → ★閉じるのは MANAGER/CLAUDE_SENIOR の後だけ（★私の読みが正しい）
   ★1回で refused → ★IMPL の観測が正しく、★私の読みが不足している
★★★これは ★`D-200` §4 の ingest の★直後に ★ついでに測れる ∴ ★新しい作業を増やさない。
★★★★測るのは ★MGR が ingest した後である ∴ ★私は今 押さない。
```

---

# 4. ★判定
```
★★BUILT は ★受け入れてよい。★★数字1件（再投入5回の理由）だけ ★保留にする。
★理由: ★成果物・停止点・actor・行数0 は ★すべて一致した。★作法（自分の計器の誤りの自己申告）も正しい。
★★★保留にした1件は ★§3 で ★次の ingest のついでに決着する ∴ ★止める理由にならない。
```

---

# 5. ★やっていないこと
```
★ingest していない（★MGR の承認の手番）／ ★`run_next` を押していない ／ ★コードを1行も変えていない
★S-3 の依頼文に触っていない ／ ★新しい台帳・計器・状態語を作っていない
★★`D-199` は保留のまま ／ ★C-3 ／ `D-191` ／ 案C の測定 ／ 受入3 の採点 ／ Ledger ／ 図 ／ (c) patch も同じ
```

---
**決めたこと**: **①BUILT を独立に測り直して突き合わせた——停止点・`test_result`（sha256 まで）・findings（finding_id まで）・各段の actor・書いた行数0（`human_view.py` は5 repo の production 配下に0件、`twoder` の git status も0）はすべて一致し、誤りは見つからなかった ②IMPL が自分の Monitor の誤りを自分で申告したのは正しい作法である ③食い違いが1件——IMPL は「1回 dispatch するたびに gate が閉じるので再投入が5回 要った」と書いたが、私の実測では submit 1回のあと `run_next` を連続で押して6段 進み、再投入は0回・refused も0回だった ④仕組みから見ても、閉じるのは `MANAGER`（PLAN・DISPOSE）と `CLAUDE_SENIOR`（UPPER_REVIEW）の後だけで、`CODING_WORKER`/`INDEPENDENT_AUDITOR` の後は閉じない ⑤ただし IMPL は実際に refused を受け取っており嘘ではない。原因は「dispatch のたび」ではなく別に在るが、私は断定しない ⑥これは重要である——報告どおりなら Claude は13回、私の実測なら8回で1.6倍 違い、放置すると「1段ごとに人手が要る」と誤って残る。両方の実測を並べて置く ⑦決着は次の ingest の直後に `run_next` を連続で押せば1回で付く。新しい作業を増やさない。私は今 押さない ⑧BUILT は受け入れてよく、保留にするのはこの数字1件だけである。**
