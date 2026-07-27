# BUILD SPEC — Build 19: **宣言を実装に変える1件目 — 孫まで掃除する（A）＋ 実行前の決定論検査（B）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-28_G17_CLOSED_AND_UNFREEZE_CONDITIONS.md`
- 対象 Gap: **`G-20`（`CONTRADICTED`）/ `G-21` / `G-22`**

## 0. ★これは何か
**`process_kill_cleanup: True` と書いてあるだけの箇所を、実際に掃除するようにする。**
**解凍は副産物である。目的ではない。**
**★「これで安全」と書かない。** **書くのは「孫プロセスが残らないことを実測で確認した」である。**

---

## 1. A — 孫まで掃除する（`live_worker_runtime._run_test` のみ）

### 1-1. 現状（実物）
```
twoder/live_worker_runtime.py:42
  r = subprocess.run(test_command, cwd=workspace, capture_output=True, text=True, timeout=timeout, shell=False)
```
**`timeout` は起動した直接の子を殺す。** **その子が起動した孫には届かない**（`G-21`・本日の INCIDENT の生存経路）。

### 1-2. 直す形
```
① 子を新しいセッション/プロセスグループで起動する（start_new_session=True）
② 正常終了・timeout・例外の いずれの場合も、最後に **プロセスグループごと** 掃除する
   （os.killpg(os.getpgid(pid), SIGKILL) 相当。既に死んでいれば無視）
③ 掃除の結果を戻り値に載せる: {"pg_cleanup": {"attempted": bool, "survivors_before": int, "survivors_after": int}}
```
- **★新しい実行系を作らない。** **`_run_test` の中だけを直す。**
- **既存の戻り値のキー（`passed` / `exit` / `stdout` / `stderr` / `timed_out` / `env_signals`）を変えない。** **追加のみ。**
- **`subprocess.run` を使い続けられないなら `Popen` に変えてよい**（**同じ関数の中に閉じること**）。
- **`shell=False` / `cwd=workspace` / `capture_output` 相当 / `timeout` の意味を変えない。**

### 1-3. ★禁止
- **`_MUST_BE_TRUE` に項目名を足して終わりにしない**（**それが `G-20` そのものである**）。
- **他の実行箇所（`runtime_inspection` / `dw.executor` 等）を、ついでに直さない。**

---

## 2. B — 実行前の決定論検査（新規・小さい）

### 2-1. 置く場所
**`twoder/` に1ファイル。** 例: `twoder/artifact_precheck.py`。**LLM を呼ばない。標準ライブラリのみ。**

### 2-2. ★検査項目（本日の実測から取る。想像で増やさない）
| # | 検査 | 根拠（本日の実測） |
|---|---|---|
| **P1** | **`if __name__ == '__main__':` が2つ以上ある** | INCIDENT の `jsonl_tool.py` は46行目と165行目に2つ |
| **P2** | **`subprocess` / `Popen` / `os.system` / `os.fork` / `os.execv` のいずれかが在る** | `run_test()` が自分自身を `subprocess` 起動していた |

- **★この2項目だけ。** **増やさない。**
- **判定は文字列/AST の決定論。** **`ast` を使ってよい。** **LLM を使わない。**
- **戻り値**: `{"safe_to_run": bool, "hits": [{"check": "P1"|"P2", "file": …, "line": …, "text": …}]}`
- **★`hits` が空でなければ `safe_to_run: False`。** **「安全そうだから通す」を作らない。**

### 2-3. 使い方（本 build では**呼び出し側を配線しない**）
- **本 build は「作る」まで。** **`_run_test` から呼ぶ配線は次の build。**
- **理由**: **A の実測（孫が残らないこと）を、B の配線と混ぜない。** **どちらが効いたか分からなくなる。**

---

## 3. 受入（すべて実行して結果を貼る）

### A について
1. **★孫が残らないことを実測する。** **手順:**
   - 一時ディレクトリに、**自分の子を1つ起動して即座に終了する**小さなテスト用スクリプトを置く（**`sleep` する孫を1つ作る形。無限増殖させない**）。
   - `_run_test` でそれを実行し、**戻ってきた直後に `pgrep` で孫の残存を数える。**
   - **修理前**: 孫が残ることを示す（**残らなければ、私の前提が誤っている。そう書いて止める**）。
   - **修理後**: **残らないことを示す。**
   - **★前後の実測値を両方貼る。**
   - **★テスト用スクリプトは無限に増えない形にすること**（本日の INCIDENT を再現しない）。
2. **既存の戻り値のキーが変わっていないこと。**
3. **非回帰**: `twoder/regression/test_live_worker_runtime.py` / `test_full_live_e2e.py`。**実行して貼る。**

### B について
4. **INCIDENT の `jsonl_tool.py`（`/tmp/refora_vgsranp1/ref_yvas4ez5/`）に当てて `safe_to_run: False` になること**（**実行せず・読むだけ**）。**`hits` を貼る。**
5. **Build 18 の保全物（`contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/`）に当てた結果を貼る。** **判定はしない。事実だけ。**
6. **`safe_to_run: True` になる無害な例1つでも確認する**（**検査が全部を落とす計器になっていないこと**）。

### 共通
7. **★「これで安全」と書かない。** **「孫プロセスが残らないことを実測で確認した」と書く。**
8. **触ったファイルを列挙**（`live_worker_runtime.py` と新規1ファイルのみ）。**他を1行も変えていないこと。**
9. **`/tmp` のサブディレクトリを消さない**（`refora_*` / `dw_beta_*` / `2der_runner_*` は証拠）。
10. **commit しない。** 冒頭に「運用方針 確認済（版: v1.9）」。**定型見出し＋★2軸の結果欄**（§4）。

---

## 4. BUILT の定型見出し（★2軸に変更・MGR 承認済）
```
## 到達経路
- [ ] (A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸。両方に丸を付ける）
### 経路（どこまで到達したか）
- [ ] 実装した / [ ] 途中で止めた（理由: ____）
### 結果（実測がどうだったか）
- [ ] A: 修理前に孫が残り、修理後に残らないことを実測した
- [ ] A: 修理前から孫が残らなかった（→ 設計の前提が誤り。止めて上げた）
- [ ] B: INCIDENT 対象で safe_to_run=False を確認した
- [ ] NOT_EVALUATED（____）
```

## 5. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| 修理前に孫が残るか | **★残る**（`timeout` は直接の子しか殺さないため） |
| 修理後 | **残らない** |
| B を INCIDENT 対象に当てる | **`safe_to_run: False`**（P1 と P2 の両方に当たる） |
| B を Build 18 保全物に当てる | **`safe_to_run: True`**（IMPL の grep で `__main__` 1つ・`subprocess` 無し） |
| 非回帰2本 | **PASS** |

**★外れたら「外れた」と書く。** **特に「修理前から孫が残らない」なら、`G-21` の私の読みが誤りである。**

---
*BUILD SPEC v1.0（★実装源）。Build 19=宣言を実装に変える1件目。A=`live_worker_runtime._run_test` の中だけを直し、子を新セッションで起動して正常終了/timeout/例外のいずれでもプロセスグループごと掃除し、結果を `pg_cleanup` として戻り値に追加（既存キーは変えない・新しい実行系を作らない・他の実行箇所をついでに直さない・`_MUST_BE_TRUE` に項目名を足して終わりにしない）。B=`twoder/artifact_precheck.py` を1ファイル新規、検査は本日の実測から取った2項目のみ（P1 `__main__` が2つ以上／P2 `subprocess`・`Popen`・`os.system`・`os.fork`・`os.execv` の有無）、決定論で LLM を使わず、hits が空でなければ `safe_to_run: False`（「安全そうだから通す」を作らない）。★本 build では B の配線をしない（A の実測と混ぜるとどちらが効いたか分からなくなる）。受入=★孫が残らないことを修理前後の実測で示す（テスト用スクリプトは無限増殖しない形）／既存キー不変／非回帰2本／B を INCIDENT 対象に当てて False・Build 18 保全物に当てて結果を貼る（判定しない）・無害な例で True（全部を落とす計器でないこと）／★「これで安全」と書かず「孫プロセスが残らないことを実測で確認した」と書く／`/tmp` のサブディレクトリは証拠なので消さない。BUILT は★2軸の結果欄。予想=修理前は孫が残る・修理後は残らない・INCIDENT 対象は False・Build 18 保全物は True・非回帰 PASS。*
