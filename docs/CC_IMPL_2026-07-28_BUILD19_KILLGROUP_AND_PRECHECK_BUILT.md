# 実装 → 設計/監査: Build 19 — **孫プロセスが残らないことを実測で確認しました**（A）＋ 実行前の決定論検査を作りました（B）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-28_BUILD19_SPEC_KILL_GROUP_AND_PRECHECK.md` v1.0
- **受領した文書**: 上記 / `CC_MGR_2026-07-28_BUILD19_APPROVED.md`（写しで観測）
- 対象 Gap: `G-20`（`CONTRADICTED`）/ `G-21` / `G-22`
- **本文書は観測と実装を書きます。**

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

---

## 結果（★2軸・両方に丸）
### 経路（どこまで到達したか）
- [x] **実装した** / [ ] 途中で止めた

### 結果（実測がどうだったか）
- [x] **A: 修理前に孫が残り、修理後に残らないことを実測した**
- [ ] A: 修理前から孫が残らなかった（→ 設計の前提が誤り）
- [x] **B: INCIDENT 対象で `safe_to_run=False` を確認した**
- [ ] NOT_EVALUATED

---

## 1. A — 孫まで掃除する（`live_worker_runtime._run_test` のみ）

### 1-1. ★実測（修理の前後・両方貼ります）
**試験用スクリプト**（`~/.cc_tmp/b19/child.py`）: **孫を1つだけ起動して即終了する形**。**自分自身を起動しません＝無限に増えません**（本日の INCIDENT を再現しない条件）。
```
再現: cd /home/takasan/.cc_tmp/b19 && python3 measure.py
      （measure.py は _run_test を呼び、戻った直後に /proc からマーカー一致プロセスを数える）

===== 修理【前】 =====
実行前の孫の数: 0
戻り値のキー: ['exit', 'passed', 'stderr', 'stdout', 'timed_out']
passed=False / exit=None / timed_out=True
★戻った直後の孫の数: 1          ← ★残った
pg_cleanup キー: 無し
後片付け後の孫の数: 0

===== 修理【後】 =====
実行前の孫の数: 0
戻り値のキー: ['exit', 'passed', 'pg_cleanup', 'stderr', 'stdout', 'timed_out']
passed=False / exit=None / timed_out=True
★戻った直後の孫の数: 0          ← ★残らない
pg_cleanup = {'attempted': True, 'survivors_before': 2, 'survivors_after': 0}
後片付け後の孫の数: 0
```
**∴ 修理前は孫が1つ残り、修理後は残りません。** **`pg_cleanup` は、掃除の直前に2プロセス（子＋孫）が居て、直後に0になったことを記録しています。**

**★「これで安全」とは書きません。** **書けるのは「この試験形において、孫プロセスが残らないことを実測で確認した」ことだけです。**

### 1-2. 計器の誤りを1つ出しておきます【監査:IMPL】
**最初の計測で「孫が3」と出ましたが、これは誤りでした。** **数える側のコマンド行そのものにマーカー文字列が入っていて、自分自身を数えていました。**
**さらにその直後、後片付けの `pkill` が自分のシェルを巻き込んで落ちました**（同じ理由）。
**∴ マーカーを別ファイルへ分離し、数える側の命令行に文字列が現れない形に直してから取り直しています。** **上の値は取り直した後のものです。** **誤った値（3）を根拠にしていません。**

### 1-3. 変更の中身
```
① 子を start_new_session=True で起動する（＝独立したプロセスグループになる）
② 正常終了・timeout・例外の いずれの経路でも finally で os.killpg(pgid, SIGKILL)
③ 掃除の前後の在籍数を /proc から数え、pg_cleanup として戻り値に追加
```
- **既存キー（`passed` / `exit` / `stdout` / `stderr` / `timed_out` / `env_signals`）は変えていません。追加のみです**（上の実測でキー一覧を前後で示しています）。
- **`shell=False` / `cwd=workspace` / 出力の取得 / `timeout` の意味を変えていません。**
- **`subprocess.run` → `Popen` ＋ `communicate` に変えました**（実装源 §1-2 が許した範囲・**同じ関数の中に閉じています**）。
- **数え方は `/proc` の `stat` の `pgrp` 欄で、`pgrep` を使いません**（標準ライブラリのみ）。
- **`_MUST_BE_TRUE` に項目名を足していません**（**それが `G-20` そのもの**）。**他の実行箇所（`runtime_inspection` / `dw.executor` 等）を1行も触っていません**（`git status` で確認）。

### 1-4. 非回帰（実行して貼ります）
```
twoder/regression/test_live_worker_runtime.py  exit=0  15/15 passed
twoder/regression/test_full_live_e2e.py        exit=0  7/7 passed
```

---

## 2. B — 実行前の決定論検査（`twoder/artifact_precheck.py`・新規1ファイル）
- **LLM を呼びません。標準ライブラリのみ。**
- **検査は実装源の2項目だけです。増やしていません。**
  - **P1**: `if __name__ == "__main__":` が **2つ以上**（1つは普通なので2つ以上でのみ hit）
  - **P2**: `subprocess` / `Popen` / `os.system` / `os.fork` / `os.execv` のいずれか
- **`hits` が空でなければ `safe_to_run: False`。** **「安全そうだから通す」経路を作っていません。**
- **本 build では呼び出し側に配線していません**（実装源 §2-3。A の実測と混ぜないため）。

### 2-1. ④ INCIDENT の対象に当てる（★実行せず・読むだけ）
```
対象: /tmp/refora_vgsranp1/ref_yvas4ez5/jsonl_tool.py
safe_to_run = False / hits = 5
  P1  line 46   if __name__ == '__main__':
  P1  line 165  if __name__ == '__main__':
  P2  line 4    import subprocess
  P2  line 54   import subprocess
  P2  line 78   result = subprocess.run(
```
**∴ P1（46行目と165行目の2つ）と P2 の両方に当たりました。** **設計/監査が挙げた行番号と一致しています。**

### 2-2. ⑤ Build 18 の保全物に当てる（**判定はしません。事実だけ**）
```
files_checked = ['ws-8cff562b1d/impl.py', 'ws-8cff562b1d/test_impl.py']
safe_to_run = True / hits = []
```

### 2-3. ⑥ 無害な例（検査が全部を落とす計器になっていないこと）
```
一時ファイル: def add(a,b) と __main__ 1つだけの 6 行
safe_to_run = True / hits = []
```
**∴ 何でも False にする計器ではありません。**

### 2-4. この検査の限界（事実として先に書きます）
- **行単位の文字列一致です。** **コメントや文字列リテラル中の出現も hit にします。**
- **∴ 誤検出は起こりえます。** **ただし倒れる向きは常に「実行しない側」で、危ないものを安全に見せる向きには倒れません。**
- **`getattr` 等で間接的に起動する形は、この2項目では捕まえられません。** **項目を増やさないという指示に従い、増やしていません。**

---

## 3. 触ったファイル（実装源 §3-8）
```
再現: cd /home/takasan/twoder && git status --porcelain
  M live_worker_runtime.py        ← A
  ?? artifact_precheck.py         ← B（新規）
再現: git status --porcelain live_worker_scaffold.py runtime_inspection.py    → 出力なし（無変更）
再現: cd /home/takasan/dev-workcell && git status --porcelain dw/executor.py  → 出力なし（無変更）
```
**∴ 2ファイルのみです。他を1行も変えていません。**

## 4. 予想と実際（実装源 §5）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| 修理前に孫が残るか | **残る** | **★残った（1）** | **当たり** |
| 修理後 | 残らない | **★残らない（0）** | **当たり** |
| B を INCIDENT 対象に | `safe_to_run: False` | **`False`（P1×2・P2×3）** | **当たり** |
| B を Build 18 保全物に | `safe_to_run: True` | **`True`（hits 空）** | **当たり** |
| 非回帰2本 | PASS | **15/15・7/7 とも PASS** | **当たり** |

**5項目すべて当たりました。外れはありません。**

## 5. 守った禁止事項
- **`/tmp` のサブディレクトリを1件も消していません**（`refora_*` / `dw_beta_*` / `2der_runner_*` は証拠。**INCIDENT の `jsonl_tool.py` も読んだだけで消していません**）。
- **INCIDENT の対象を実行していません。** **Build 18 の保全物も実行していません**（凍結中）。
- **`_MUST_BE_TRUE` に項目名を足していません。**
- **他の実行箇所をついでに直していません。**
- **B を呼び出し側に配線していません。**
- **試験用スクリプトは無限に増えない形です**（孫1つ・自己起動なし）。**実測後に毎回後片付けしています**（残 0 を確認）。
- **commit していません**（MGR）。

## 6. commit
**していません。** 触った本番ファイル: `twoder/live_worker_runtime.py`（変更）/ `twoder/artifact_precheck.py`（新規）。

---
*IMPL BUILT（Build 19）。★A=`live_worker_runtime._run_test` の中だけを直し、子を `start_new_session=True` で独立したプロセスグループに置き、正常終了/timeout/例外のいずれの経路でも `finally` で `os.killpg(pgid, SIGKILL)` し、掃除前後の在籍数を `/proc` の `pgrp` から数えて `pg_cleanup` として戻り値に追加（既存キーは不変・`subprocess.run`→`Popen`+`communicate` に変更したが同じ関数内に閉じている・`pgrep` を使わず標準ライブラリのみ・`_MUST_BE_TRUE` に項目名を足していない・他の実行箇所は無変更）。★実測=**修理前は孫が1つ残り、修理後は0**（`pg_cleanup={'attempted':True,'survivors_before':2,'survivors_after':0}`）。**「これで安全」とは書かず「この試験形において孫プロセスが残らないことを実測で確認した」と書く。** ★計器の誤りを申告=初回は数える側のコマンド行にマーカーが入って自己一致し「孫3」と出し、続く `pkill` が自分のシェルを巻き込んだ。マーカーを別ファイルに分離して取り直しており、誤った値を根拠にしていない。非回帰 15/15・7/7 PASS。★B=`twoder/artifact_precheck.py` を新規1ファイル（LLM なし・標準ライブラリのみ・検査は P1/P2 の2項目のみ・hits が空でなければ `safe_to_run:False`・本 build では配線しない）。INCIDENT 対象は `False`（P1 が46行目と165行目、P2 が3件）、Build 18 保全物は `True`（hits 空・判定はしない）、無害な例も `True`（全部を落とす計器ではない）。限界=行単位の文字列一致なのでコメント/文字列中も hit になり誤検出はありうるが倒れる向きは常に「実行しない側」／`getattr` 等の間接起動は捕まえられないが項目は増やしていない。触ったファイルは2つのみで他は無変更。/tmp のサブディレクトリは1件も消さず、INCIDENT 対象も保全物も実行していない。予想5項目すべて当たり・外れなし。*
