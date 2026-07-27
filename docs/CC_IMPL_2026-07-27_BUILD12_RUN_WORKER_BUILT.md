# 実装 → 設計/監査: Build 12 — worker は走ったが**成果物は生成されず**（`SPEC_INCOMPLETE_NO_CONTRACT`）（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.7）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD12_SPEC_RUN_WORKER_AND_RECEIVE.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD12_APPROVED.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**（Build 11 で報告済・本 build では触っていない）

---

## 1. 手順①（着手前の鮮度確認・10R の教訓）【監査:IMPL】
```
実行中   : pid 1594748 / 起動 月 7月 27 18:37:58 2026 / python3 -m twoder.webui 8770
ソース   : twoder/webui.py              2026-07-27 18:05:37
           dev-workcell/dw/dispatch.py  2026-07-27 18:05:20
           twoder/submit.py             2026-07-27 13:03:00
```
**起動がすべてのソースより新しいことを確認しました。止めずに続行しています。**

## 2. 手順②〜④（1つの作業として続けて実行）【監査:IMPL】
```
投入前 sandbox 数 : 56          （/tmp/2der_runner_* の実数）
POST /api/submit  : task_id=TASK-2DER-B9B4DA3B / runnable=true    ← 依頼文は Build 11 と同一・1文字も変えず
POST /api/run_next: dispatched=true / reason=None                 ← 1回だけ
投入後 sandbox 数 : 56          （★増減なし）
新規 sandbox      : []          （★存在しない）
```
**∴ 保全（`contracts/out/SANDBOX_ARTIFACT-…/`）を行っていません。MANIFEST も作っていません。保全対象が存在しないためです。**

## 3. ★worker は走りました。成果物が出なかっただけです【監査:IMPL】
```
nlo          : state=READY_FOR_IMPLEMENTATION / operation=GENERATE /
               actor_role=CODING_WORKER / actor_id=QWEN_LIVECODER
derive_state : READY_FOR_AUDIT
events       : ['CREATE', 'PROCESS_EVENT', 'PLAN', 'GENERATE']
```
**`GENERATE` が記録され、`READY_FOR_AUDIT` に進んでいます。**

**`generate_runs` の中身（逐語）:**
```json
{"task_id": "TASK-2DER-B9B4DA3B", "phase": "GENERATE", "role": "WORKER",
 "identity": "2der-generate-via-runner", "run_id": "seam-B4DA3B",
 "ts": "2026-07-11T09:00:00",
 "payload": {"diff": null,
             "test_result": {"status": "FAILED", "ok": false,
                             "reason": "SPEC_INCOMPLETE_NO_CONTRACT",
                             "artifact_sha256": null},
             "problems": ["SPEC_INCOMPLETE_NO_CONTRACT"]}}
```
- **`diff` は `null`、`artifact_sha256` も `null`。**
- **`reason` は `SPEC_INCOMPLETE_NO_CONTRACT` の1件のみ。**

**この文字列の出所（コード）**: `twoder/generate_via_runner.py:149` のコメントに
`contract 無 → reason="SPEC_INCOMPLETE_NO_CONTRACT"` とあります（`twoder/test_generate_via_runner_spec.py:92,100` にも同名の assert）。
**私が確認したのはこの記載までです。なぜ contract が無いと判定されたかは調べていません。**

## 4. `planner_outcome`
```
run_next の返りキー : ['dispatched', 'nlo', 'planner_outcome', 'reason', 'state']
planner_outcome     : None
```
**キーは存在します**（Build 11 と同じ）。**今回は PLAN 段ではなく GENERATE 段なので、値が `None` であることの意味は私の観測では判定材料が不足しています。**

## 5. 守った禁止事項（実装源）
- **成果物の中身を評価していません**（そもそも生成されていません）。
- **受入オラクルを開封していません。**
- **配置・登記・配線をしていません。**
- **2段以上進めていません**（`run_next` は1回）。
- **失敗しても手で書いていません**（`answer()` を私が実装していません）。
- **`run_until_barrier` を使っていません。**
- **token を迂回していません**（要求されませんでした）。
- **本番コードを変更していません**（本 build では1行も）。

## 6. 観測の限界（事実として）
- **1回しか実行していません。**
- **`SPEC_INCOMPLETE_NO_CONTRACT` の原因を調べていません**（実装源の範囲外）。
- **`READY_FOR_AUDIT` に進んでいるので、次に `run_next` を打つと audit 段が動きます。打っていません。**

## 7. commit
**していません**（MGR）。**本 build では本番コードを変更していません。**

---
*IMPL BUILT（Build 12）。手順①で起動 18:37:58 > 全ソース mtime を確認して続行。同一依頼文で submit 1回・run_next 1回。**`dispatched: true` で `GENERATE` が記録され `READY_FOR_AUDIT` へ進んだが、sandbox は 56→56 で増えず、`diff: null` / `artifact_sha256: null` / `problems: ["SPEC_INCOMPLETE_NO_CONTRACT"]`** ＝ **worker は走ったが成果物が生成されなかった**。保全対象が無いため保全も MANIFEST 作成もしていない。中身の評価・オラクル開封・配置・登記・配線はしていない。1回のみの観測。*
