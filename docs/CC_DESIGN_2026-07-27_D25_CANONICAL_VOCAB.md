# 設計/監査 → MGR（写: Taka / IMPL）: **正典は runtime 側の語彙。そして `#attempt-N` の一意性は `ts` で置き換えられる — G-12 と同じ穴だった**

- `BUILD_ROLE: 参照`（設計判断。**実装源は §4 の裁定後**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=FINDING
- **運用方針 確認済（版: v1.9）**
- **受領した文書**: `CC_MGR_2026-07-27_BUILD14_AUDIT_RECEIVED_ALIGN_VOCAB.md`

## 0. 答え（先に2つ）
1. **正典は runtime 側（`live_worker_runtime`）の語彙である。** **`approval_registry` は中立で、照合するだけである。**
2. **★`#attempt-N` を外しても一意性は失われない。** **一意性は `ts` で確保できる。** **∴ `G-12`（固定 ts）と同じ穴だった。**

---

## 1. どちらが正典か【監査:CC-α】

```
再現: sed -n '1,10p' twoder/approval_registry.py
  「approval_id(文字列)のみを受け、authority 台帳の GRANT 記録を引いて
    action_type / task_id / operation_class を照合する」
```
**∴ `approval_registry` は語彙を持たない。** **呼び出し側が渡した値と、台帳の GRANT 値を比べるだけである。**
**∴「検証が求める値」は `approval_registry` の主張ではなく、呼び出し側の主張である。**

```
再現: sed -n '71,72p' twoder/live_worker_runtime.py
  task_id = tp.get("task_id"); op = tp.get("operation_class", "LIVE_WORKER_TASK")
  action  = tp.get("action_type", "LIVE_WORKER_MINIMAL")
再現: sed -n '95p' twoder/live_worker_runtime.py
  val = AR.validate_by_token(approval_token, action, task_id, op, ts)
```
**∴ 語彙は task packet が宣言し、無ければ `LIVE_WORKER_TASK` / `LIVE_WORKER_MINIMAL` に落ちる。**
**∴ `task_id` は packet の素の値である。**

> **∴ 正典は「task packet が宣言する語彙」であり、既定値がそれを表している。**
> **∴ 直すのは `mint_token` 側である。** **`approval_registry` も `live_worker_runtime` も触らない。**

## 1-1. 新しい語彙を作らない（v1.9 の確認）
**`LIVE_WORKER_MINIMAL` / `LIVE_WORKER_TASK` は既存である**（`counterfactual_runner.py:54` が `AUTH.grant_approval("LIVE_WORKER_MINIMAL", TASK, "LIVE_WORKER_TASK", "taka", TS)` として実際に使っている）。
**∴ 既存語彙に寄せるだけであり、新設しない。**

---

## 2. ★`#attempt-N` は外せる（MGR の禁止に抵触しない）【設計:CC-α】

**MGR の禁止**: 「検証が素の task_id を求めているから suffix を外す」は禁止。**片方の修理をもう片方の修理で潰すことになる。**
**この禁止は正しい。** **ただし前提が1つ動く。**

```
approval_id = sha1("%s|%s|%s|%s" % (task_id, operation_class, action_type, ts))   （authority.py:133）
mint_token の docstring 逐語: 「attempt を入力に含めることで固定 TS 問題(webui.TS)を回避する」
```
**∴ `#attempt-N` は「`ts` が固定だから」入っている。** **一意性の源として `task_id` を借りているだけである。**
**∴ `ts` が attempt ごとに変われば、`task_id` を汚さずに一意性が得られる。**

> **∴ `#attempt-N` を外す代わりに `ts` を attempt ごとに変える。** **一意性は保たれる。** **死因#2 は復活しない。**
> **∴ これは `G-12`（`ts` が既定値）の修理と同じ穴である。** **1つ直すと3つ揃う。**

### 2-1. ★未確認（実装源に入れる前に確かめること）
**`validate_by_token(..., ts)` が `ts` を照合に使うか、消費/期限にしか使わないかを、私は確認していない。**
- **照合に使うなら**、mint と検証で同じ `ts` を渡す必要がある（packet 経由で運ぶ）。
- **使わないなら**、mint 側だけ変えればよい。
- **∴ これを確かめるまで、実装源を書かない。** **今日ずっと守ってきた順序である。**

---

## 3. 修理の形（案・裁定後に実装源へ）
```
twoder/generate_via_runner.py の mint_token のみを変える:
  _REAL_MINTER("USE_VLLM_INFERENCE", "<task>#attempt-N", "DW_MACHINE_OP", …)
    ↓
  _REAL_MINTER("LIVE_WORKER_MINIMAL", "<task>", "LIVE_WORKER_TASK", …, ts=<attempt ごとに変わる ts>)
```
- **`approval_registry` / `live_worker_runtime` / `authority` を変えない。**
- **新しい語彙・新しい台帳・新しいフラグを作らない。**
- **★これは修理である。** **「精度が動くまで新しい機構を作らない」の例外に当たる**（MGR §2-3）。

---

## 4. 裁定を仰ぐ1点
> **`ts` を attempt ごとに変えることを許すか。**

- **賛成の根拠**: `#attempt-N` の目的（一意性）をそのまま満たし、`task_id` を汚さない。**`G-12` の方向とも一致する。**
- **懸念**: **本系は「`ts` は生成せず受領する」を規律にしてきた**（`submit()` の `ts_source`）。**mint が `ts` を作るのは、その規律に触れる。**
- **【設計:CC-α】私は「触れない」と考える。** **`submit()` の `ts` は出来事の時刻であり、`approval_id` の `ts` は一意性のための入力である。** **意味が違う。**
- **★ただし断定しない。** **規律の解釈は MGR の領分である。**

---

## 5. Gap Register への登録（MGR §2-4）
**`G-16` を「同型3件目」として既に登録済み**（本文書で `note` を補強する）:
| # | 同型 |
|---|---|
| ① | 契約の規律が分析層（`UNRESOLVED_NO_CONTRACT`）と生成層（`SPEC_INCOMPLETE_NO_CONTRACT`）に |
| ② | 7戦略が決定論（`request_resolution`）と LLM（`intent_strategy`）に |
| ③ | **mint（`generate_via_runner`）と検証呼出（`live_worker_runtime`）の語彙** |

**統合しない。可視化する。**

---
*CC-α D-25。★正典は runtime 側の語彙——`approval_registry` は中立で照合するだけ（docstring 逐語）、語彙は `live_worker_runtime:71-72` が task packet から読み、無ければ `LIVE_WORKER_TASK`/`LIVE_WORKER_MINIMAL` に落ちる ∴ 直すのは `mint_token` 側だけで、`approval_registry` も `live_worker_runtime` も触らない。既存語彙（`counterfactual_runner:54` が実使用）に寄せるので新設しない。★`#attempt-N` は外せる——`approval_id=sha1(task_id|operation_class|action_type|ts)` で、suffix は「ts が固定だから」一意性の源として task_id を借りているだけ ∴ ts を attempt ごとに変えれば task_id を汚さず一意性が得られ、死因#2 は復活しない。**これは G-12(固定 ts) と同じ穴で、1つ直すと3つ揃う。** ★未確認=`validate_by_token` が ts を照合に使うか消費/期限にしか使わないか——確かめるまで実装源を書かない。★裁定を仰ぐ1点=`ts` を attempt ごとに変えることを許すか（`submit()` の「ts は生成せず受領する」規律に触れるか。私は出来事の時刻と一意性の入力は意味が違うので触れないと考えるが、規律の解釈は MGR の領分）。G-16 は同型3件目として登録済・統合しない・可視化する。*
