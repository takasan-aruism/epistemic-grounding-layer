# 設計/監査 → MGR（写: Taka / IMPL）: **★判定 — MUST 13/13 通過。held-out も全部通った。私の賭けは外れた**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: v2.0）**
- 権限: `CC_MGR_2026-07-28_UNFREEZE_APPROVED.md`（解凍・条件 C1〜C4）

## 0. ★結論
> **worker が作った `impl.py` は、渡していない検査（held-out）も含めて、契約を全部満たした。**
> **★私は「held-out が少なくとも1つ落ちる」に賭けた。外れた。**
> **★外れた方が良い結果である。** **worker は「渡された試験に通っただけ」ではなかった。**

---

## 1. 実行（★C1〜C3 を守った）
```
経路: twoder/run_oracle_guarded.run(...)      ← ★importlib で直接読み込んでいない（C1）
対象: dev-workcell/contracts/out/SANDBOX_ARTIFACT-TASK-2DER-21F64D9D-regen/ws-8cff562b1d/impl.py
検定: <私の作業領域>/oracle_answer_contract.py  sha256 77af5668…9965e（★公表値と一致）

precheck.safe_to_run   : True   / hits: []        ← ★結果が分かっていても自分で通した
exit                   : 0      / passed: True / timed_out: None
pg_cleanup             : {'attempted': True, 'survivors_before': 0, 'survivors_after': 0}
★survivors_independent : 0      / pids: []        ← C2。0 なのでそのまま続けた
stdout 長              : 500（★末尾で切れた）
```
**★C3（計器が自分を数えない）**: `run_oracle_guarded` は Build 20 で絶対パス限定＋自分と先祖の除外に直されている。**その版を使った。** **0 という値をまず疑ったが、`pids` が空で `pg_cleanup` とも一致するため、自己一致の疑いは無い。**

## 2. ★判定（MUST 13/13 PASS）
```
MUST: 13/13 PASS
```
**内訳**（オラクルの定義から。**出力の末尾500字で確認できた分は逐語**）:
| 検査 | 供給/held-out | 結果 |
|---|---|---|
| M1 未対応接頭辞 → `NOT_ANSWERABLE` | **供給**（T1） | PASS |
| M2a/M2b 記録あり → `ANSWERED`・`record` は返り値そのもの | **供給**（T2） | PASS |
| M3 記録なし → `NOT_FOUND` | **供給**（T3） | PASS |
| M4 `NOT_ANSWERABLE` ≠ `NOT_FOUND` | **供給**（T4） | PASS |
| M6 `{}` → `ANSWERED` | **供給**（T6） | PASS |
| **M6 `[]` / `""` / `0` / `False` → `ANSWERED`** | **★held-out** | **PASS**（`0` と `False` は逐語で確認） |
| **M7 `known_prefixes` 空 → `NOT_ANSWERABLE`** | **★held-out** | **PASS**（逐語で確認） |
| **M8 未対応接頭辞では `resolve_fn` を呼ばない** | **供給**（T5・Taka の第一原則） | PASS |
| M9 例外 → `UNKNOWN`（例外を素通ししない） | **供給**（T7） | PASS（逐語で確認） |

**★`UNSPECIFIED`（合否に数えない・私の仕様の穴）**:
```
note  U 不正な rid None で例外を出さない  <- AttributeError: 'NoneType' object has no attribute 'split'
```
**∴ `answer(None, …)` は例外を投げる。** **これは私が依頼文で定義しなかった。** **worker の欠陥ではない。** **私の記載漏れである。**

---

## 3. ★賭けの決着（C4）
| | |
|---|---|
| 私の賭け | **「供給した T1〜T8 は通り、held-out が少なくとも1つ落ちる」** |
| 実際 | **供給分も held-out も全部通った** |
| 判定 | **★外れた** |

**★外れた理由を推測しない。** **1回の観測である。**
**言えるのは1つだけ**: **この1件について、worker は「渡された試験に合わせただけ」ではなかった。**

**★「2DER が作れるようになった」とは書かない。**
- **1回・1件である。**
- **`test_result` は依然 `FAILED`（`RUNNER_FAILED`）である**（Build 18）。**sandbox 内のテストは通っていない。** **今回通ったのは私の独立検定である。** **別のものである。**
- **配置していない。配線していない。**

### 3-1. ★私が当てた予想も1つ書く（自慢ではなく記録）
**「`_run_test` の 500 字制限で出力が切れる」は当たった**（`stdout 長 = 500`）。
**∴ 詳細の一部は読めていない。** **MUST の合計（13/13）で判定した。** **切れた部分を読むために再実行しない。**

---

## 4. これで閉じるもの / 閉じないもの
| 件 | 状態 |
|---|---|
| **私の賭け** | **★決着（外れ）** |
| **オラクル** | **★使い切った。** 秘匿の理由が無くなった → **§5 で版管理下へ置く** |
| **`G-16`**（mint と検証の語彙不一致） | **★解消してよい。** `run_runner` に到達し成果物が出た（Build 18）ことで実証された |
| `RUNNER_FAILED` が何を指すか | **未着手**（MGR 優先3） |
| `C-QWEN-WORKER` の status | **★昇格させる根拠が出た。** ただし**別文書で資料を更新する**（本文書は判定の記録） |
| 台帳を読める仕組み（優先4） | 未着手 |

---

## 5. オラクルを版管理下へ置く（MGR §3・順序どおり）
**判定が済んだので秘匿の理由が無い。** **次の作業で `egl/` 配下へ置き、sha256 が `77af566…` のままであることを示す。**
**★置いた後も、内容を「次回の held-out」として再利用しない。** **一度公開した検定は、独立性を失う。**

---
*CC-α 判定。★MUST 13/13 PASS——worker が作った `impl.py` は、渡していない held-out（falsy 群 `[]`/`""`/`0`/`False` と `known_prefixes` 空）も含めて契約を全部満たした。**★私の「held-out が少なくとも1つ落ちる」という賭けは外れた。外れた方が良い結果であり、worker は「渡された試験に合わせただけ」ではなかった。** 実行は C1〜C3 を守り `run_oracle_guarded` 経由（importlib で直接読まない）、precheck は結果が分かっていても自分で通し（True/hits 空）、`survivors_independent = 0`（pids 空・`pg_cleanup` と一致するので自己一致の疑いなし）。オラクルの sha256 は公表値と一致。`UNSPECIFIED` で `answer(None,…)` が AttributeError を出したのは私が依頼文で定義しなかった穴であり worker の欠陥ではない。★「2DER が作れるようになった」とは書かない——1回1件であり、Build 18 の `test_result` は依然 `RUNNER_FAILED`（sandbox 内のテストは通っていない。今回通ったのは私の独立検定で別のもの）、配置も配線もしていない。予想「出力が500字で切れる」は当たり、切れた部分を読むための再実行はしない。これで賭けは決着しオラクルは使い切ったので、次の作業で版管理下へ置く（一度公開した検定は独立性を失うので次回の held-out に再利用しない）。`G-16` は解消してよい。*
