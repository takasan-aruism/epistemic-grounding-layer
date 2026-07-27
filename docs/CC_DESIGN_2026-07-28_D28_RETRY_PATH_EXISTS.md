# 設計/監査 → MGR（写: Taka / IMPL）: **D-28 — 再試行の道は既に在る。近道は意図的に塞がれている。新しい task を作らない**

- `BUILD_ROLE: 参照`
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-28_RETRY_PATH_CHECK_FIRST.md` / `CC_IMPL_2026-07-28_BUILD16_STOPPED_BEFORE_RUN_NEXT.md`

## 0. 答え（先に3つ）
1. **★再試行の道は既に在る。** `READY_FOR_AUDIT → AUDIT → DISPOSITION_REQUIRED → DISPOSE → READY_FOR_REGENERATE → REGENERATE`
2. **★近道は意図的に塞がれている。** コード逐語（`dispatch.py:307`）: **「§3: raw AUDIT からは REGENERATE 不可(dispose 必須)」**
3. **∴ 新しい task を作らない。** **捨て駒を増やさない。** **既存の道を1段ずつ歩く。**

---

## 1. ★私の SPEC が間違っていた（先に）【設計:CC-α】
**Build 16 SPEC は `TASK-2DER-21F64D9D` を `GENERATE` の対象として書いた。**
**しかし Build 14 の時点で、その task は既に `READY_FOR_AUDIT` へ進んでいた。**

> **★`GENERATE` は失敗しても段を進める。** **`record_generate` は結果の成否に関わらず遷移を記録する。**

**∴ 「失敗したのだからやり直せる」は成り立たない。** **失敗も1回の実行として消費される。**
**∴ 私は Build 14 の BUILT に `derive_state = READY_FOR_AUDIT` と書かれているのを読みながら、Build 16 で `GENERATE` を指定した。** **自分の監査に書いた事実を、自分の SPEC で使わなかった。**
**★IMPL が撃つ前に止めたので、無駄撃ちにならなかった。**

---

## 2. 既存の再試行経路【監査:CC-α・コード構造】
```
再現: grep -n "READY_FOR_REGENERATE\|def rework_items\|def record_regenerate" dev-workcell/dw/workcell.py
      grep -n "REGENERATE" dev-workcell/dw/dispatch.py
```
| 段 | 状態 → 操作 / actor |
|---|---|
| 現在 | **`READY_FOR_AUDIT`** → `AUDIT` / `INDEPENDENT_AUDITOR`（Qwen） |
| 次 | `DISPOSITION_REQUIRED` → `DISPOSE` / `MANAGER`（**機械処理可なら自動**） |
| その次 | **`READY_FOR_REGENERATE`** → `REGENERATE` / `CODING_WORKER`（Qwen） |

**`dispatch.py:307` 逐語**: `"REGENERATE": {"READY_FOR_REGENERATE"},  # §3: raw AUDIT からは REGENERATE 不可(dispose 必須)`
**`workcell.py:141` 逐語**: `state = "READY_FOR_REGENERATE"  # code fault -> rework; execution fault -> retry`

> **∴ 「監査を飛ばして作り直す」は、設計として禁じられている。** **裁定を経ないやり直しを許さない構造である。**
> **∴ これは本日ずっと守ってきた規律（失敗を握り潰さない・裁定を経る）が、DW 側に既に実装されている例である。**

## 3. ★ただし、この道が今回通るかは UNKNOWN
| 懸念 | 内容 |
|---|---|
| **U-1** | **監査する成果物が無い**（`diff=null` / `artifact_sha256=""`）。**Qwen auditor が何を返すか未知** |
| **U-2** | **`rework_items` は「最新 audit の ACCEPTED finding」を渡す。** **finding が0件なら渡すものが無い** |
| **U-3** | **`webui` の `cw` アダプタは `EXECUTION_DEFECT` の再試行で「同じコードを再実行（新規生成なし）」を行う**（DE-0324）。**しかしコードは生成されていない。** **`reconstruct_code` が何を返すか未知** |

**∴「道が在る」＝「今回通る」ではない。** **昇格させない。**

## 4. 提案（1段ずつ・裁定を待つ）
**`AUDIT` を1段だけ撃ち、何が返るかを観測する。**
- **新しい task を作るより安い**（捨て駒を増やさない）。
- **U-1 の答えがその場で出る。**
- **止まったら止まったで、それが道の限界の記録になる。**
- **★`DISPOSE` へは進まない。** **1段のみ。**

**【設計:CC-α】新しい task を作るのは、この道が塞がっていると分かってからでよい。**
**★MGR §2-1 が用意した「新しい task を作る場合」の手順は、まだ使わない。**

## 5. Gap Register（MGR §2-1-4 は今は該当しない）
**task は2つのまま**（`D6A93450` / `21F64D9D`）。**3つ目を作らないので、Gap 登録は不要。**
**代わりに1件登録する:**
| id | 内容 |
|---|---|
| **G-19** | **`GENERATE` は失敗しても段を進める**（`record_generate` が成否に関わらず遷移を記録）。**∴ 同じ task で `GENERATE` をやり直すには、`AUDIT → DISPOSE → REGENERATE` を経る必要がある。近道は設計として塞がれている** |

---
*CC-α D-28。★再試行の道は既に在る=`READY_FOR_AUDIT → AUDIT → DISPOSITION_REQUIRED → DISPOSE → READY_FOR_REGENERATE → REGENERATE`。近道は意図的に塞がれている（`dispatch.py:307` 逐語「raw AUDIT からは REGENERATE 不可(dispose 必須)」）＝裁定を経ないやり直しを許さない構造で、本日ずっと守ってきた規律が DW 側に既に実装されている例。∴ 新しい task を作らない。★私の SPEC が間違っていた——Build 16 で `21F64D9D` を GENERATE の対象にしたが、Build 14 の時点で既に `READY_FOR_AUDIT` へ進んでいた。**`GENERATE` は失敗しても段を進める**（`record_generate` は成否に関わらず遷移を記録）ので「失敗したのだからやり直せる」は成り立たない。自分の監査に書いた事実を自分の SPEC で使わなかった。IMPL が撃つ前に止めたので無駄撃ちにならなかった。★ただし道が今回通るかは UNKNOWN（監査する成果物が無い/finding が0なら rework_items が空/生成されていないコードを reconstruct_code が返せない）。提案=`AUDIT` を1段だけ撃って観測する（新 task より安い・止まればそれが道の限界の記録）。task は2つのままなので3つ目の Gap 登録は不要で、代わりに G-19（GENERATE は失敗しても段を進める・近道は塞がれている）を登録。*
