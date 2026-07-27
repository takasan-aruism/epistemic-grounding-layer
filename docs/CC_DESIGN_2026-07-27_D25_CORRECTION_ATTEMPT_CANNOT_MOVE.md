# 設計/監査 → MGR（写: Taka / IMPL）: **★D-25 §2 を撤回する — `#attempt-N` は外せない。MGR の条件が私の誤りを捕まえた**

- `BUILD_ROLE: 参照`（**`CC_DESIGN_2026-07-27_D25_CANONICAL_VOCAB.md` §2 を撤回。§1 は維持**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-27_D25_APPROVED_FIX_MINT_ONLY.md`

## 0. 撤回
**私は「`#attempt-N` を外しても一意性は `ts` で確保できる」と書いた。誤りである。**
**MGR の条件「実 ts に変えて既存の決定論検査が壊れないかを先に確認せよ」で、壊れることが分かった。**

```
再現: sed -n '230,240p' twoder/probe/conformance_probe.py
  a = mint(1, task_id="TASKG1B", ts="2026-07-11T09:00:00")
  b = mint(2, task_id="TASKG1B", ts="2026-07-11T09:00:00")
  distinct = a != b        # SPEC §3: death#2 決着
```
**∴ この probe は「同じ `ts` で attempt だけ変えたとき id が異なる」ことを検査している。**
**∴ 一意性を `ts` に移すと、この検査は同一 `ts` を渡すので id が一致し、落ちる。**
**∴ 「片方の修理が、もう片方の修理を潰す」——MGR が名指しした形そのものである。** **今日2回目。**

**★MGR の当初の禁止（`#attempt-N` を単純に外すな）が正しかった。** **私が動かした前提の方が誤っていた。**

---

## 1. 制約が3つ同時に立っている【監査:CC-α】
| # | 制約 | 出所 |
|---|---|---|
| **C1** | 検証は **素の `task_id`** を求める | `live_worker_runtime:71` が `tp["task_id"]` を渡す |
| **C2** | 一意性は **attempt だけで**（同一 `ts` でも）取れねばならない | `conformance_probe._gate1b_ts` |
| **C3** | `approval_id = sha1(task_id\|operation_class\|action_type\|ts)` の4項目しか効かない | `authority.py:133` |

**∴ C1 で `task_id` は使えない。C3 で `operation_class`/`action_type` は語彙が固定。∴ 残るのは `ts` だけ。**
**∴ C2 を満たすには、`ts` に attempt を入れるしかない。**

## 2. ★そこで値の衝突が起きる（私は決めない）
> **`ts` に `#attempt-N` を入れると、`ts` フィールドに時刻でない文字列が入る。**

- **検証は `ts` を照合に使わない**（`approval_registry` は `expiry` 比較と消費にしか使わない）。**∴ 機能的には無害。**
- **しかし `AUTHORITY_APPROVAL_GRANT` の記録に、時刻でない値が残る。**
- **★これは本日ずっと潰してきた「記録に嘘を書く」形である。** **`ts_source` を作ってまで「既定値に落ちた事実」を残してきた系で、`ts` に時刻でないものを入れるのは逆行する。**

**∴ 選択肢は3つ。いずれも代償がある。**
| 案 | 内容 | 代償 |
|---|---|---|
| **(A)** | **`ts` に `#attempt-N` を入れる**（mint 1箇所） | **記録の `ts` が時刻でなくなる。** 触る範囲は最小 |
| **(B)** | **`authority.grant_approval` の `approval_id` に nonce/attempt を加える** | **`authority` を触る**（MGR は mint のみと裁定）。**`ts` は時刻のまま保てる** |
| **(C)** | **`live_worker_runtime` が検証に使う `task_id` を packet から suffix つきで受け取る** | **task 同一性が下流で濁る**（`record_generate` も同じ id を使う）。**採らない方がよい** |

**【設計:CC-α】私は (B) を推す。** 理由: **`ts` は時刻であるべきで、一意性は一意性の仕組みで取るべきである。** **「触る範囲が最小」より「記録が正しい」を上に置く。**
**★ただし MGR は「mint の1箇所だけ」と裁定している。** **∴ 範囲を広げる判断は MGR の領分であり、私は決めない。**

---

## 3. 語彙の修正は、どの案でも変わらない
```
mint_token: "USE_VLLM_INFERENCE" → "LIVE_WORKER_MINIMAL"
            "DW_MACHINE_OP"      → "LIVE_WORKER_TASK"
```
**この2つは C1〜C3 と独立であり、どの案でも必要である。** **∴ 先に確定してよい。**

## 4. 私の誤り（消さない）
1. **「`#attempt-N` は外せる」は誤り**（§0）。**probe を読まずに「`ts` で代替できる」と書いた。**
2. **本日、私は「読んでから作る」を掲げながら、`conformance_probe` を読まずに設計判断を出した。** **MGR の条件が無ければ、そのまま実装源にしていた。**
3. **`ts` が照合に使われないことは確認したが、「使われないから何を入れてもよい」ではない**——**記録としての正しさは別問題である。** **§2 で気づいた。**

---
*CC-α。★D-25 §2 を撤回——`#attempt-N` は外せない。`conformance_probe._gate1b_ts` が「同じ ts で attempt だけ変えたとき approval_id が異なる」ことを検査しており、一意性を ts に移すとこの検査が落ちる＝MGR が名指しした「片方の修理がもう片方を潰す」形そのもの（今日2回目）。MGR の当初の禁止が正しく、私が動かした前提の方が誤っていた。★制約が3つ同時に立つ: C1 検証は素の task_id を求める / C2 一意性は同一 ts でも attempt だけで取れねばならない / C3 approval_id は4項目しか効かない ∴ 残るのは ts だけで、C2 を満たすには ts に attempt を入れるしかない。★そこで値の衝突=`ts` に時刻でない文字列が入る（検証は ts を照合に使わないので機能的には無害だが、`AUTHORITY_APPROVAL_GRANT` の記録に嘘が残る＝`ts_source` まで作って「既定値に落ちた事実」を残してきた系に逆行する）。選択肢は (A) ts に suffix（範囲最小・記録が嘘）/ (B) `authority` の approval_id に nonce を加える（範囲が広がる・記録は正しい）/ (C) packet に suffix つき task_id（下流の task 同一性が濁る・採らない）。私は (B) を推すが、MGR が「mint の1箇所だけ」と裁定しているので範囲を広げる判断は MGR の領分。語彙の修正（LIVE_WORKER_MINIMAL / LIVE_WORKER_TASK）はどの案でも必要なので先に確定してよい。私の誤り=probe を読まずに設計判断を出した（「読んでから作る」を掲げながら）／「照合に使われないから何を入れてもよい」ではないと §2 で気づいた。*
