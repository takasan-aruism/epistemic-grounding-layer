# 設計/監査 → MGR（写: Taka / IMPL）: **D-32 — `RUNNER_FAILED` は「テストが落ちた」ではない。「テストが1件も集まらなかった」である。原因は私が書いた `immutable_tests` の書式**

- `BUILD_ROLE: 参照`（調査のみ。**1行も直していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: v2.0）**
- **受領した文書**: `CC_MGR_2026-07-28_VERDICT_RECEIVED_RUNNER_FAILED_IS_NOW_FIRST.md`

## 0. 答え（先に3つ）
1. **`RUNNER_FAILED` は「`run_runner` が `PASSED` を返さなかった」という catch-all である。** **中身を区別していない。**
2. **★今回は「テストが落ちた」ではない。** **`pytest` が1件も集められず、`exit 5`（no tests collected）だった。**
3. **★原因は私である。** **`immutable_tests` を「直接実行するスクリプト」の形で書いた。** **runner は `pytest` で起動する。**

---

## 1. D-32-1 `RUNNER_FAILED` は何を指すか【監査:CC-α】
```
再現: sed -n '151p' twoder/generate_via_runner.py（契約コメント逐語）
  run_runner status=="PASSED" → ok=True。それ以外 → ok=False reason="RUNNER_FAILED"
```
**∴ `PASSED` 以外を全部 `RUNNER_FAILED` にまとめている。**
> **∴ 「落ちた」も「走らせられなかった」も「集まらなかった」も、同じ1語になる。**
> **★本日の第一原則（失敗を正常に見える別の結果に置き換えない／状態を潰さない）の観点では、これは潰しである。**

## 2. D-32-2 どのコードが書いているか【監査:CC-α】
```
twoder/generate_via_runner.py:105（task_packet）
  "test_command": ["python3", "-m", "pytest", "-q", "test_impl.py"]     ← ★pytest で起動する
  "test_file": "test_impl.py", "test_body": immutable_tests             ← ★私の immutable_tests がそのまま test_impl.py になる
```

## 3. ★実測（この1件で何が起きたか）
```
対象: dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/ws-8cff562b1d/

再現: grep -c "^def test_" test_impl.py            → ★0
再現: grep -n "^def " test_impl.py                 → _ck / _boom / run   （★test_ で始まる関数が無い）
再現: python3 -m pytest -q test_impl.py            → "no tests ran" / ★exit 5（no tests collected）
再現: python3 test_impl.py                         → ★exit 0（全検査 PASS）
```
> **∴ 同じファイルが、`pytest` では「0件」、直接実行では「全部通る」。**
> **∴ `RUNNER_FAILED` の実体は「テストが1件も集まらなかった」である。** **コードの品質とは無関係である。**

---

## 4. ★誰の欠陥か（はっきり書く）
| 候補 | 判定 |
|---|---|
| worker（Qwen） | **違う。** `impl.py` は私の独立検定で MUST 13/13 を通した |
| runner / `generate_via_runner` | **違う。** `pytest` で起動する仕様は一貫している |
| **私（設計/監査）** | **★これである。** **`immutable_tests` を `def run():` ＋ `if __name__ == "__main__":` の形で書いた。** **`test_*` 関数を1つも定義しなかった** |

**★私は Build 13 の SPEC で、この `immutable_tests` を自分で書いた。**
**そして「`immutable_tests` はそのまま `test_impl.py` になる」ことも、Build 13 SPEC の §0 に自分で書いていた。**
> **∴ 書式が `pytest` で集まる形かを、確かめていなかった。**
> **∴ `test_command` が `pytest` であることは `generate_via_runner.py:105` に在った。読めば分かった。**
> **★本日ずっと繰り返している形である。** **今回は「読めば分かることを、自分の成果物の受入基準に混ぜた」。**

## 5. ★MGR の読みの訂正（重要）
**MGR は「我々の計器が、良いコードを捨てる向きに誤っていた」と書いた。**
**結論は正しい。** **しかし原因の所在が違う。**
> **計器（runner / pytest）は正しく動いていた。** **1件も集まらなかったのだから、`PASSED` を返さないのは正しい。**
> **誤っていたのは、私が渡した検査そのものである。**

**∴ 「計器が逆を言った」ではなく、★「私が空の検査を渡し、計器がそれを正しく報告した」。**
**∴ 直すべきは `RUNNER_FAILED` の語ではなく、まず私の書式である。**

**★ただし `RUNNER_FAILED` の潰しは残る**（§1）。**「0件」と「落ちた」が同じ語になるのは、次に別の誰かを同じ目に遭わせる。** **Gap に登録する。**

---

## 6. Gap Register
| id | 内容 | 状態 |
|---|---|---|
| **`G-25`** | **`RUNNER_FAILED` が catch-all で、「テストが落ちた」「走らせられなかった」「1件も集まらなかった」を区別しない。** `pytest` の `exit 5` が「不合格」と同じ扱いになる | OPEN |
| **`G-26`** | **`immutable_tests` の書式要件（`pytest` で集まる `test_*` 関数）が、どこにも書かれていない。** `test_command` は `generate_via_runner.py:105` に在るが、依頼文を書く側への案内が無い | OPEN |

## 7. やっていないこと
- **1行も直していない**（調査のみ）。
- **`immutable_tests` を書き直していない。**
- **再生成していない。**
- **`RUNNER_FAILED` の語を変えていない。**

---
*CC-α D-32。★`RUNNER_FAILED` は「`run_runner` が PASSED を返さなかった」の catch-all で、落ちた/走らせられなかった/集まらなかった を区別しない（本日の第一原則から見れば状態の潰しである）。★今回の実体は「テストが1件も集まらなかった」——`test_command` は `["python3","-m","pytest","-q","test_impl.py"]`（`generate_via_runner.py:105`）で、`test_body=immutable_tests` がそのまま `test_impl.py` になる。実測: `grep -c "^def test_"` = 0（関数は `_ck`/`_boom`/`run`）、`pytest -q` は "no tests ran" で **exit 5**、一方 `python3 test_impl.py` は **exit 0（全検査 PASS）**。∴ 同じファイルが pytest では0件、直接実行では全部通る。★誰の欠陥か=worker でも runner でもなく**私**。`immutable_tests` を `def run():`＋`__main__` の形で書き `test_*` 関数を1つも定義しなかった。`test_command` が pytest であることは読めば分かった。★MGR の「計器が良いコードを捨てる向きに誤っていた」は結論は正しいが原因の所在が違う——計器は正しく動いており（0件なら PASSED を返さないのが正しい）、誤っていたのは私が渡した検査である。∴「計器が逆を言った」ではなく「私が空の検査を渡し、計器がそれを正しく報告した」。ただし `RUNNER_FAILED` の潰しは残るので `G-25` に、書式要件がどこにも書かれていない件は `G-26` に登録。1行も直していない。*
