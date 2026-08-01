# 【実測】`passed` を書いた — **COMPLETE には到達していない（`CLAUDE_BARRIER` で停止）**

- **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-02 02:5x / TYPE=BUILT
- **規律 v1.3 確認済 ／ 9項目 確認済（外れた番号なし）** ／ **実装源**: `CC_DESIGN_2026-08-02_EVO0031_BUILD_SPEC_WRITE_PASSED.md`

---

# 1. 変更

```
twoder/webui.py  +3 / -1（"passed" 1行 ＋ 既存行の分割）。ok は消していない・変えていない。
他のファイルは触っていない。新しい状態語・台帳・計器・エンドポイントなし。
```

# 2. SPEC §1 の【未確認】への答え（投入前に実測）

```
twoder/live_worker_runtime.py:79 逐語: res = {"passed": proc.returncode == 0, "exit": proc.returncode, …}
∴ _run_test 由来の test_result には passed が既に在る。
   欠けていたのは runner seam(webui.py cw)の経路だけである。
```

# 3. 受入

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| (1) | `E3B92A8E` が `COMPLETE` | **未達** | `run_until_barrier` の trace（逐語）: `{"state":"JUDGE_REQUIRED","operation":"UPPER_REVIEW","actor":"CLAUDE","dispatched":false,"reason":"CLAUDE_BARRIER"}` |
| (2) | `complete_and_close` の応答 | **未実施** | GATE に到達していない（`completed`/`loop_closed` とも得ていない） |
| (3) | 戻せる | **○** | 手で1行を戻した版が `HEAD` と**バイト一致** |
| (4) | GATE の `reason` | **該当なし** | GATE は呼ばれていない（迂回もしていない） |

# 4. 走行

```
再投入1回（sha1 一致・task 増なし）→ 応答 runnable=true / next_legal_operation=UPPER_REVIEW
run_until_barrier 1回（0.25秒）→ 1段も dispatch されず CLAUDE_BARRIER で停止。
webui 再起動を確認（9項目 #5）: 起動 02:41:37 > webui.py 02:41:26。
★passed が実際に記録に書かれることは まだ示せていない。
   理由: GENERATE/REGENERATE が1回も走っていない（E3B92A8E は JUDGE_REQUIRED ∴ 次の段は UPPER_REVIEW のみ）。
   他の2 task（816D6F68 / 0E5E8675）は いずれも READY_FOR_AUDIT ＝ 次の段は AUDIT で test_result を書かない。
   ∴ 「ソースに在る」までである。「動く」とは書かない。
```

# 5. 次に要るもの（私の手番ではない）

```
E3B92A8E の次の段は UPPER_REVIEW（actor=CLAUDE）＝ 記録するのは人の判定であり、実装の手番ではない。
UPPER_REVIEW が記録されれば EVO-0030 の分岐が行き先を決め、そこから completion_blockers の ③ を
passed が満たすかが測れる。
```

# 6. 戻し方

```
webui.py の `"passed": bool(gr.get("ok")),` の1行を消し、直前の2行を元の1行に戻す。
※ commit 後は `git checkout --` では戻らない。
```
