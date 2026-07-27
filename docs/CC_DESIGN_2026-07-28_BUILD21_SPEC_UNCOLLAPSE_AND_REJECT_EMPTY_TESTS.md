# BUILD SPEC — Build 21: **`RUNNER_FAILED` を潰さない（G-25）＋ 空の検査を封じさせない（G-26）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v2.0）**
- 権限: `CC_MGR_2026-07-28_D32_RECEIVED_MY_READING_WAS_WRONG.md` §5（D-33）
- 原因調査: `CC_DESIGN_2026-07-28_D32_RUNNER_FAILED_IS_MY_FORMAT.md`

## 0. ★これは修理である。新機能ではない
| 足す | 廃止する |
|---|---|
| **既に在る情報（`exit` / 収集件数）を、潰さずに載せる** | **「PASSED 以外を全部 `RUNNER_FAILED` の1語にまとめる」という潰し** |
| **契約を封じる前の決定論検査1つ** | **「空の検査を渡せてしまう」という穴** |

**★新しい状態語を発明しない。** **★案内文書を作らない**（本日、文書での注意喚起が効かないことを実証した）。

---

## 1. G-25 — `RUNNER_FAILED` を潰さない

### 1-1. 現状
```
twoder/generate_via_runner.py（契約コメント逐語）
  run_runner status=="PASSED" → ok=True。それ以外 → ok=False reason="RUNNER_FAILED"
```
**∴ 「落ちた（pytest exit 1）」「1件も集まらなかった（exit 5）」「走らせられなかった」が同じ1語になる。**

### 1-2. 直す形
```
reason の文字列は変えない（"RUNNER_FAILED" のまま。既存 assert を壊さない）
★その隣に、既に在る値をそのまま載せる:
  runner_exit        : test の終了コード（int / 取れなければ None）
  runner_stdout_tail : 既に取っている stdout の末尾（★新たに取得しない・在るものを載せるだけ）
```
- **★新しい状態語を作らない。** **`no_tests_collected` のような語も作らない。** **`exit` を載せれば読む側が区別できる。**
- **`exit` が `run_runner` の正規化（`{status, run_id, artifact_sha256, artifact}`）で落ちているなら、そこを通すこと。** **正規化の形は変えてよいが、既存キーは消さない。**
- **★どこで落ちているかを、実物を読んで特定してから直すこと。** **推測で足さない。**

### 1-3. 触ってよい範囲
`twoder/generate_via_runner.py` のみ。**`live_worker_runtime` / `approval_registry` / `authority` を触らない。**

---

## 2. G-26 — 空の検査を封じさせない

### 2-1. 置く場所（★設計判断とその理由）
**`twoder/contract_seal.py::extract_contract` に、決定論の検査を1つ足す。**
```
immutable_tests に「行頭が def test_ で始まる行」が1つも無ければ ValueError（★fail-closed）
```
**理由:**
1. **★最も早い。** **封じる前に止まるので、空の検査が task に入らない**（MGR §3-2）。
2. **同じ関数が既に fail-closed の検査を持っている**（マーカーの片方欠落 / END 欠落 → `ValueError`）。**同型を1つ足すだけである。**
3. **★代償を明記する**: **`contract_seal` が「runner が `pytest` であること」に結合する。**
   **∴ コメントに `generate_via_runner.py:105`（`test_command` が pytest）を出典として書くこと。**
   **∴ runner が pytest でなくなったら、この検査も移すこと。** **その旨もコメントに書く。**

### 2-2. 検査の形
- **行頭一致のみ**（`^def test_`）。**AST を使ってもよいが、増やさない。**
- **★「0件なら拒否」だけ。** **件数の下限や命名規則の細目を作らない。**
- **エラーメッセージに、何が足りないかを書く**（例: `immutable_tests has no pytest-collectable test (^def test_)`）。

### 2-3. ★非回帰の当たり（先に確認させる）
```
既存の contract を持つ fixture / test が、この検査に引っかからないかを先に確認すること:
  twoder/test_contract_seal_spec.py
  twoder/test_contract_read_spec.py
  twoder/test_generate_via_runner_spec.py
  twoder/regression/ 配下で contract を組み立てているもの
```
**★引っかかるものが在れば、そこで止めて上げること。** **fixture を書き換えて通さない。**

---

## 3. 受入（すべて実行して貼る）
1. **G-25**: **`exit` が payload に載ることを実測**。**pytest が0件になる例（`test_*` 無し）で `runner_exit = 5`、テストが落ちる例で `runner_exit = 1` を、両方示す。**
   - **★`reason` が `"RUNNER_FAILED"` のままであることも示す**（文字列を変えていない証拠）。
2. **G-26**: **`test_*` を持たない `immutable_tests` で `extract_contract` が `ValueError` になること。** **持つものは従来どおり通ること。** **両方貼る。**
3. **★実際に本日の依頼文（Build 13 の `immutable_tests`）に当てると `ValueError` になることを示す。** **これが「今日の穴を塞いだ」証拠である。**
4. **非回帰**: §2-3 の4系統 ＋ `twoder/regression/test_live_worker_runtime.py`。**実行して貼る。**
5. **触ったファイルが `generate_via_runner.py` と `contract_seal.py` の2本だけであること**（`git status --porcelain`）。
6. **新しい状態語を作っていないこと・案内文書を作っていないこと。**
7. **★`GENERATE` を走らせない。再生成しない。** 本 build は修理まで。
8. **commit しない。** 冒頭に「運用方針 確認済（版: v2.0）」。**定型見出し＋2軸の結果欄。**

## 4. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| `exit` が正規化で落ちているか | **★落ちている方に賭ける**（`run_runner` の戻りは `{status, run_id, artifact_sha256, artifact}` の4キーと docstring に書かれている） |
| 0件の例で `runner_exit` | **5** |
| 落ちる例で `runner_exit` | **1** |
| G-26 の非回帰 | **★引っかかる fixture が在る方に賭ける**（既存の contract 試験が `test_*` を持つ形とは限らない） |

**★外れたら「外れた」と書く。**
**★MGR 指示により、「書式を直した `immutable_tests` で再生成したら通るか」は予想しない**（本 build の範囲外）。

## 5. 位置づけ
- **★これで「テストが正しく走る」とは書かない。** **書けるのは「0件と失敗が区別できるようになった」「空の検査が封じられなくなった」だけである。**
- **私の `immutable_tests` を直すのは、本 build ではない。**

---
*BUILD SPEC v1.0（★実装源）。Build 21=`RUNNER_FAILED` の潰しを解く(G-25)＋空の検査を封じさせない(G-26)。修理であり、足すのは「既に在る情報を潰さずに載せる」ことと「封じる前の決定論検査1つ」、廃止するのは「PASSED 以外を1語にまとめる潰し」と「空の検査を渡せる穴」。★新しい状態語を発明せず案内文書も作らない（文書での注意喚起が効かないことを本日実証した）。G-25=`reason` は `"RUNNER_FAILED"` のままにして隣に `runner_exit` と既存の `stdout` 末尾を載せる（`no_tests_collected` のような語も作らない。exit を載せれば読む側が区別できる）。正規化で exit が落ちているならそこを通すが、**どこで落ちているかを実物を読んで特定してから直す**。触るのは `generate_via_runner.py` のみ。G-26=`contract_seal.extract_contract` に「`^def test_` が0件なら ValueError」を1つ足す（最も早く止まる／同じ関数が既に fail-closed 検査を持つ／★代償として `contract_seal` が pytest に結合するので出典 `generate_via_runner.py:105` と「runner が変わったら移す」をコメントに書く）。★非回帰の当たりを先に確認させ、引っかかる fixture が在れば止めて上げる（fixture を書き換えて通さない）。受入=exit が 5 と 1 で区別できることを両方実測／`reason` が不変である証拠／`test_*` 無しで ValueError・有りで従来どおり／★本日の Build 13 の immutable_tests に当てて ValueError になること（今日の穴を塞いだ証拠）／非回帰5系統／触ったファイル2本のみ／再生成しない。予想=exit は正規化で落ちている方に賭ける／0件は 5・失敗は 1／G-26 で引っかかる fixture が在る方に賭ける。★「テストが正しく走る」とは書かない。*
