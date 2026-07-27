# 実装 → 設計/監査: Build 17 — **1段目で `refused: "no submit yet"`。再起動が run-gate を初期化していました**（BUILT・BLOCKED）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-28 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-28_BUILD17_SPEC_WALK_TO_REGENERATE.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-28_D28_APPROVED_WALK_THE_PATH.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案の採否をしません。**

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て届いた。

## プロセス鮮度（実行時）
- **webui pid `2746222` / 起動 `2026-07-27 23:59:33`**
- ソース mtime: `webui.py` 18:05:37 / `authority.py` 23:24:27 / `generate_via_runner.py` 23:24:27 / `dispatch.py` 18:05:20 / `workcell.py` 07-23 06:07:26
- [x] **起動がソースより新しい** / [ ] 古い（→ 止めた）

---

## 歩いた段（撃つ前の状態を必ず書く）
- **1段目: 前=`READY_FOR_AUDIT` / 操作=`POST /api/run_next` 1回 / 後=`READY_FOR_AUDIT`（変化なし）**
- **2段目以降: 実行していません**（1段目が拒否されたため）

### 1段目・実行前の確認（実装源 §1-①）
```
再現: cd /home/takasan/dev-workcell && python3 -c "
from dw import workcell, dispatch
print(workcell.derive_state('TASK-2DER-21F64D9D')[0])
n=dispatch.next_legal_operation('TASK-2DER-21F64D9D')
print(n['operation'], n['actor_role'], n['claude_barrier'])"
結果: READY_FOR_AUDIT
      AUDIT / INDEPENDENT_AUDITOR / claude_barrier=False
```
**∴ 予期した状態でした。だから撃ちました。**

### 1段目・`/api/run_next` の応答全文（逐語・要約していません）
```json
{
  "refused": true,
  "blocked": false,
  "runnable": false,
  "dispatched": false,
  "reason": "no submit yet",
  "task_id": "TASK-2DER-21F64D9D"
}
```
**所要 0.020 秒。** **∴ LLM は呼ばれていません**（Qwen 監査は動いていません）。

## 1. ★拒否の原因（決定論・逐語）【監査:IMPL】
```
再現: grep -n "no submit yet" -B 12 twoder/webui.py
逐語（webui.py:29-32）:
  # run-gate: /api/run_next|run_until_barrier may advance a DW task ONLY when the LAST submit produced a
  # runnable, non-blocked task (backend guarantee; UI disabling alone is insufficient). DEAD-APPROACH
  # BLOCK or a non-runnable (observe/blocked) context => refused, no dispatch.
  _LAST = {"blocked": False, "runnable": False, "task_id": None, "reason": "no submit yet"}
```
- **`_LAST` は webui プロセスの中に持つ変数で、プロセス起動時にこの初期値になります。**
- **Build 16 で私が webui を再起動したため、Build 14 の `submit` が残した `_LAST` が消えています。**
- **∴ `run_next` は「直前の submit が無い」として拒否しました。** **これは gate が設計どおり働いた結果であり、故障ではありません**（コメント逐語「UI を無効化するだけでは不十分」）。

### 1-1. ★私が持ち込んだ状態です
**再起動は実装源（Build 16）の手順で、常設手順として承認されたものですが、それによって run-gate が初期化されることを、私は事前に申告していません。** **事実として記録します。**

## 2. 変化していないこと（実測）
```
実行後 derive_state = READY_FOR_AUDIT       （前と同じ）
audit_runs = 0 / generate_runs = 1 / rework_count = 0
/tmp/2der_runner_* : 投入前 57 → 実行後 57  （増減なし・1件も消していません）
```
**∴ 台帳にも sandbox にも、何も足していません。**

## 3. ★止めた理由（実装源 §1-② の「予期しないもの → 止めて上げる」）
**`run_next` を通すには、この webui プロセスで `/api/submit` を1回行う必要があります。**
**しかし実装源 §1 の手順に `submit` はありません。** **∴ 独断で足さずに止めました。**

**私が確かめていないこと（事実として）:**
- **既存 task に `/api/submit` を撃ったとき何が起きるかを、実測していません**（撃っていないため）。
- **Build 14 の記録では、再投入後も events は4件のまま `CREATE` が二重化していませんでしたが、それは記録からの観測であって今回の実測ではありません。**
- **`_LAST` を submit 以外で満たす経路が在るか否かを、私は調べていません。**

## 結果の区分（1つに丸）
- [ ] REACHED_REGENERATE（READY_FOR_REGENERATE に到達して止まった）
- [ ] NEEDS_DISPOSE（findings が在り DISPOSITION_REQUIRED になった）
- [ ] STOPPED_UNEXPECTED（予期しない状態で止めた）
- [x] **BLOCKED（gate に拒否された）** ← `reason: "no submit yet"`

## 4. 予想と実際（実装源 §3）
| 項目 | DESIGN の予想 | **実際** | 判定 |
|---|---|---|---|
| `AUDIT` は dispatch される | `true` | **`dispatched: false`（`refused: true`）** | **★外れた** |
| `findings` の件数 | 0件 | **監査が動いていないため無し** | **判定不能** |
| `AUDIT` 後の状態 | `READY_FOR_REGENERATE` | **`READY_FOR_AUDIT`（変化なし）** | **★外れた** |
| 必要な `run_next` の回数 | 1回 | **1回撃って拒否・到達せず** | **★外れた** |
| `DISPOSE` | 経由しない | **到達していない** | **判定不能** |

**★外れました。** **原因は監査の中身ではなく、その手前の run-gate です。**

## 5. 守った禁止事項
- **`REGENERATE` を実行していません。`run_until_barrier` を使っていません。**
- **監査の出力を採点していません**（そもそも動いていません）。
- **新しい task を作っていません。`D6A93450` / `B9B4DA3B` に触っていません。**
- **手で findings や disposition を書いていません。**
- **オラクルを開封していません。**
- **本番コードを1行も変更していません。**
- **`/tmp` を1件も消していません**（数えただけ）。**新規作成もしていません。**
- **`CC_REGISTER.jsonl` に試験行を書いていません。**
- **`twoder/runs/*.trace.json` を読んでいません。**

## 6. commit
**していません**（MGR）。**本 build で本番ファイルの変更はありません。**

---
*IMPL BUILT（Build 17・**BLOCKED**）。鮮度確認（pid 2746222・起動 23:59:33 > 全ソース mtime）後、実行前に `derive_state=READY_FOR_AUDIT` / `next=AUDIT` / `claude_barrier=False` を確認して `run_next` を1回だけ撃った。★応答は `refused:true, dispatched:false, reason:"no submit yet"`（0.020秒・**LLM は呼ばれていない**）。原因は決定論で確定=`webui.py:32` の `_LAST` がプロセス内変数で、起動時に `"no submit yet"` に初期化される（逐語コメント「直前の submit が runnable な task を作ったときにのみ DW task を進めてよい／UI を無効化するだけでは不十分」）∴ Build 16 で私が再起動したため Build 14 の submit が残した状態が消えた。**gate が設計どおり働いた結果であり故障ではない。** 再起動が run-gate を初期化することを事前に申告していなかったのは私の記録漏れ。実測=状態・audit_runs・sandbox 数すべて変化なし（57→57、1件も消していない）。★止めた理由=`run_next` を通すには当該プロセスで `/api/submit` が要るが、実装源 §1 の手順に submit は無いため独断で足さずに止めた。未確認=既存 task への submit の挙動は撃っていないので不明／`_LAST` を submit 以外で満たす経路の有無は調べていない。予想は4項目中3項目が★外れ（原因は監査の中身でなく手前の run-gate）。*
