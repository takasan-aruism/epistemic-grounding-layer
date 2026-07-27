# 実装 → 設計/監査: Build 21 — **0件（exit 5）と失敗（exit 1）が区別できるようになり、空の検査は封じられなくなりました**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: §12 の最新は `v1.9`・2026-07-27）**
  ※**他の文書は「v2.0」と書いていますが、`CC_OPERATING_POLICY.md` に文字列 `v2.0` は在りません**（`grep` で0件）。**本体には §4-15（`G-23`）が追記済みですが、§12 の改訂履歴に行が足りていません。** **記憶で「v2.0」と書かず、実物を読んだ値を書きます。**
- 実装源: `CC_DESIGN_2026-07-28_BUILD21_SPEC_UNCOLLAPSE_AND_REJECT_EMPTY_TESTS.md` v1.0
- **受領した文書**: 上記 / `CC_MGR_2026-07-28_BUILD21_APPROVED.md`（写しで観測）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## 結果（★2軸・両方に丸）
### 経路
- [x] **実装した**（`generate_via_runner.py` / `contract_seal.py` の2本）/ [ ] 途中で止めた
### 実測
- [x] **G-25: `runner_exit` が 5（0件）と 1（失敗）で区別できることを実測した**
- [x] **G-25: `reason` は `"RUNNER_FAILED"` のまま（文字列を変えていない）**
- [x] **G-26: `test_` を持たない `immutable_tests` が `ValueError` で止まることを実測した**
- [x] **G-26: ★本日の依頼文（Build 13）に当てて `ValueError` になった**
- [x] **非回帰4系統 PASS。★引っかかる fixture は在りませんでした**

---

## 0. ★これは修理です。新機能ではありません
| 足した | 廃止した |
|---|---|
| 既に在る `exit` / `stdout` 末尾を、潰さずに隣に載せる | **`PASSED` 以外を全部 `RUNNER_FAILED` の1語にまとめる潰し** |
| 封じる前の決定論検査1つ | **空の検査を渡せてしまう穴** |

**新しい状態語を作っていません**（`no_tests_collected` のような語も作っていません）。**案内文書も作っていません。**

## 1. G-25 — どこで落ちていたか（★実物を読んで特定してから直しました）
```
再現: grep -n "\"test\"" twoder/live_worker_runtime.py
  224: "result": result, "safety": safety, "test": test, …     ← run_minimal_slice は _run_test の結果を "test" で返している
再現: sed -n '144,146p' twoder/generate_via_runner.py（修理前）
  return {"status": …, "reason": …, "classification": …, "run_id": …,
          "artifact_sha256": …, "artifact": …}                 ← ★"test" をここで捨てていた
```
**∴ `exit` は `run_runner` の正規化で落ちていました。** **実装源の予想どおりです。**

**直した形（2箇所・`generate_via_runner.py` のみ）:**
```
run_runner の戻り: runner_exit / runner_stdout_tail を追加（既存キーは1つも消していません）
generate の失敗分岐: reason はそのままに、その隣へ runner_exit / runner_stdout_tail を載せる
```
- **`live_worker_runtime` / `approval_registry` / `authority` を触っていません。**

### 1-1. 実測（両方）
```
再現: LWR._run_test(<test_ を持たない test_impl.py>, ["python3","-m","pytest","-q","test_impl.py"])
  0件の例 : exit=5 / passed=False
再現: LWR._run_test(<assert False の test_x>, 同上)
  落ちる例: exit=1 / passed=False
```
```
再現: run_runner を差し替えて generate を呼ぶ（★LLM を使わず・台帳も隔離）
{"ok": false, "run_id": "RID", "artifact_sha256": "", "reason": "RUNNER_FAILED",
 "contract_source": "packet", "runner_exit": 5, "runner_stdout_tail": "no tests ran"}
reason が RUNNER_FAILED のままか: True
```
**∴ 同じ `RUNNER_FAILED` でも、読む側は `runner_exit` で 5 と 1 を区別できます。**

## 2. G-26 — 空の検査を封じさせない（`contract_seal.extract_contract`）
**足した検査（1つ・行頭一致のみ）:**
```python
if not any(ln.startswith("def test_") for ln in immutable_tests.splitlines()):
    raise ValueError("immutable_tests has no pytest-collectable test (^def test_)")
```
- **コメントに出典を書きました**: `generate_via_runner.py:100`（`"test_command": ["python3","-m","pytest","-q","test_impl.py"]`）。
  ※実装源は `:105` と記していましたが、**実物では `:100`** でした（`test_command` の行）。**行番号だけ実物に合わせています。**
- **コメントに「runner が pytest でなくなったら、この検査もそこへ移すこと」と、この関数が pytest に結合する代償を書きました。**
- **件数の下限も命名規則の細目も作っていません。** **「0件なら拒否」だけです。**

### 2-1. 実測
```
test_ 無し: ValueError -> immutable_tests has no pytest-collectable test (^def test_)
test_ 有り: 通った / キー = ['immutable_tests','immutable_tests_sha256','sealed_by','skeleton','skeleton_sha256']
```

### 2-2. ★本日の依頼文（Build 13 の `immutable_tests`）に当てる
```
対象: 本日 Build 13/14/17/18 で投入した依頼文そのもの（2411字・機械抽出）
結果: ValueError -> immutable_tests has no pytest-collectable test (^def test_)
```
**∴ 今日の穴は、同じ依頼文をもう一度投入しても、封じる前に止まります。**

## 3. 非回帰（実装源 §2-3 の当たり）
```
twoder/test_contract_seal_spec.py           exit=0
twoder/test_contract_read_spec.py           exit=0
twoder/test_generate_via_runner_spec.py     exit=0
twoder/regression/test_live_coder_backend.py exit=0  8/8 passed
twoder/regression/test_live_worker_runtime.py exit=0 15/15 passed
```
- **★引っかかる fixture は1つもありませんでした。** **∴ fixture を書き換えていません**（書き換える必要が生じませんでした）。
- **`regression/` 配下で contract を組んでいるのは `test_live_coder_backend.py` の1本でした**（`grep -l` で特定）。

### 3-1. 実行方法の誤りを1つ申告します【監査:IMPL】
**最初 `python3 twoder/test_contract_seal_spec.py` の形で走らせ、3本が `ImportError: cannot import name 'eq' from 'operator'` で落ちました。**
**これは私の実行方法の誤りです**（`twoder/operator.py` が標準ライブラリを隠す既知の形・使用ガイド §4 に記載）。**`python3 -m twoder.…` で取り直しています。** **落ちた出力を非回帰の結果として扱っていません。**

## 4. 触ったファイル
```
再現: cd /home/takasan/twoder && git status --porcelain
  M contract_seal.py
  M generate_via_runner.py
```
**∴ 2本だけです。**

## 5. 予想と実際（実装源 §4）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| `exit` が正規化で落ちているか | 落ちている | **落ちていた**（`run_runner` が `res["test"]` を捨てていた） | **当たり** |
| 0件の例で `runner_exit` | 5 | **5** | **当たり** |
| 落ちる例で `runner_exit` | 1 | **1** | **当たり** |
| G-26 の非回帰 | **引っかかる fixture が在る** | **★1つも無かった** | **★外れた** |

## 6. 守った禁止事項
- **`GENERATE` を走らせていません。再生成していません。**
- **新しい状態語を作っていません。案内文書を作っていません。**
- **`live_worker_runtime` / `approval_registry` / `authority` を触っていません。**
- **fixture を書き換えていません。**
- **台帳に試験行を書いていません**（`DS_DATA_DIR` 等を一時ディレクトリへ隔離して実行）。
- **LLM を1回も呼んでいません。**
- **`/tmp` を消していません。**
- **commit していません**（MGR）。

## 7. 位置づけ（実装源 §5）
- **「テストが正しく走る」とは書きません。** **書けるのは「0件と失敗が区別できるようになった」「空の検査が封じられなくなった」だけです。**
- **設計/監査の `immutable_tests` を直していません**（本 build の範囲外）。

---
*IMPL BUILT（Build 21・修理）。★G-25=`exit` が落ちていた場所を実物で特定（`run_minimal_slice` は `_run_test` の結果を `"test"` で返しているのに、`run_runner` の正規化がそれを捨てていた）。`reason` の文字列は `"RUNNER_FAILED"` のまま変えず、隣に `runner_exit` / `runner_stdout_tail` を載せた（新しい状態語を作らない）。実測=0件の例 exit=5・落ちる例 exit=1・`generate` の戻りに両方が載り `reason` は不変。★G-26=`contract_seal.extract_contract` に「`^def test_` が0件なら `ValueError`」を1つ足し、出典（`generate_via_runner.py:100`。実装源は :105 としていたが実物は :100）と「runner が pytest でなくなったら移すこと」をコメントに明記。実測=`test_` 無しで `ValueError`、有りで従来どおり通過、**本日の依頼文（Build 13 の immutable_tests）に当てて `ValueError`＝今日の穴を塞いだ証拠**。非回帰5本すべて PASS で、★引っかかる fixture は1つも無かった（実装源の予想は外れ）∴ fixture を書き換えていない。★実行方法の誤りを申告=最初 `python3 twoder/xxx.py` の形で3本が `operator` shadowing の ImportError になったが、これは私の誤りで `-m` 形式で取り直しており、落ちた出力を結果に使っていない。触ったファイルは2本のみ。LLM 不使用・台帳隔離・GENERATE 未実行・commit なし。★運用方針の版=`CC_OPERATING_POLICY.md` に文字列 `v2.0` は無く §12 の最新は v1.9（本体には §4-15 が追記済だが履歴に行が足りていない）ので、記憶ではなく実物の値を書いた。「テストが正しく走る」とは書かない。*
