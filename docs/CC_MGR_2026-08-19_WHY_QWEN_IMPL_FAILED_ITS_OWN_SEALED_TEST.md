# 宛: Taka ―― `TASK-2DER-7D461717`: **★判定 C（PLAN と実装の接続・契約変換）**

**2026-08-19 ／ 正規記録のみ。★Claude の 修正案 0 ／ PLAN 補完 0 ／ test 0 ／ 実装 0 ／ run_next 0。**

---

## 0. 答え ―― **★C。しかも「実装が試験に落ちた」のではなく ★試験は一度も走っていない**

```
★test_result.reason        = ★"SPEC_INCOMPLETE_NO_CONTRACT"
★test_result.runner_exit   = ★null        （★runner が 動いていない）
★runner_stdout_tail        = ★null        （★出力が 無い）
★diff                      = ★0 バイト     （★成果物が 作られていない）
★artifact_sha256 / artifact_head = ★どちらも null
```

## 1. ★最初に失敗した条件（★1つだけ）

**`twoder/generate_via_runner.py::generate()` :279-283**

```python
has_skel  = packet.get("skeleton") is not None
has_tests = packet.get("immutable_tests") is not None
if has_skel and has_tests:  ...          # ★packet 経路
else:                                     # ★ledger 経路へ 落ちる
    create_ev = read_create_event(...)
    contract = payload.get("contract")
    if not contract:
        return {"ok": False, ..., "reason": "SPEC_INCOMPLETE_NO_CONTRACT"}   # ★:296
```

```
★Qwen の packet が 持つ 欄 = requirement / test_body / test_file / test_command /
                              allowed_files / test_plan / completion_criteria …（24欄）
★Qwen の packet が ★持たない 欄 = ★skeleton ／ ★immutable_tests
★∴ :283 が False → ledger 経路へ
★goal 投入の CREATE payload の 欄 = ['goal','knowledge_packet','project_id']（★contract 無し）
★∴ :296 で ★fail-closed
```

**★つまり `test_body`(1906B) は 記録に 在るのに、`immutable_tests` へ 変換する 者が 居ない。**

## 2. なぜ A / B / D ではないか（★事実で）

```
★A（PLAN/test設計が悪い）… ★違う。`validate_plan` を 通り、test_plan 4件・
   completion_criteria 5件・完全な pytest module 1906B を 持つ。
★B（実装が悪い）… ★違う。★実装は 一度も 作られていない（diff=0B / artifact=None）。
★D（runner/test環境が悪い）… ★違う。★runner は 呼ばれていない（runner_exit=null）。
★E（複数要因）… ★現時点では 名指しできない。★最初の 停止で 後段が 全部 空振りしている ため、
   その先に 別の 欠陥が 有るか 無いかは ★まだ 測れていない（★無いとは 言えない）。
```

## 3. 後段の記録（★すべて「材料が無い」と言っている＝★整合している）

```
AUDIT ×2 (2der-adjudicator)   findings=[TF-461717 / category=test_failure]
DISPOSE ×2 (2der-auto-dispose) verdict=REMAINS / defect_class=★INDETERMINATE / tier=deterministic
   basis 逐語「no neutral runner result (exit_code=None, empty stdout/stderr);
              worker self-report is not a basis」
UPPER_REVIEW ×2 (claude-senior) verdict=FAIL
   基礎「artifact_sha256・artifact_head が共に None で成果物の実在が確認できない」
```

**★2DER 自身が「判断の材料が無い」と正しく言っています（★捏造していない）。**

## 4. ★正本への記帳（★済）

```
front door /api/submit → TASK-2DER-9092B26A
★progress_write = {"ok": true, "item": "ITEM-2DER-EVO-0019",
                   "status": "IN_PROGRESS", "actor": "MGR", "stage": "RECORD"}
★内容 = goal → Qwen PLAN → sealed test → GENERATE が ★Claude DESIGN 0 で 成立したこと
        ＋ 停止点が 契約変換(C)であること
```

## 5. ★Claude DESIGN 版 11件を外す方法（★調査のみ・★状態は変更していません）

**★既存の口を全部当たった結果:**

| 方法 | 効くか | 備考 |
|---|---|---|
| `deferred_*`（front door の欄） | **★効かない** | ★数えるだけ。逐語「★『いま前に出すべきもの』は判定しない（前に出す順番を決める値が 2DER に無い）」 |
| 待ち行列から外す | **★効かない** | ★11件とも `submitted` に **無い**（自己修復は戻さない）が、★10件は `CREATED` ∴ **私が今日配線した `tasks_to_enqueue` が次に拾い直す** |
| `dw.workcell.block_task(task_id, reason, ts, identity)` | **★効く** | ★`CREATED` でなくなり 部品が 拾わない ／ `_machine_turn` からも 外れる |
| 新しい規則をコードに足す | ― | **★禁止（作りません）** |

```
★★但し `block_task` は ★戻す口が 存在しない（★`unblock` / `reopen` = ★検索結果 0件）
   ＝★不可逆。★暴走 TASK-2DER-32EDB6C4 も この理由で BLOCKED の まま。
★★∴ ★Taka の 許可なしには 実行しません。
★内訳: E050D682 は `JUDGE_REQUIRED` ∴ 部品は 元々 拾わない（★残り 10件が CREATED）
```

## 6. していないこと

```
★修正案 0 ／ PLAN 補完 0 ／ test 0 ／ 実装 0 ／ 契約 0 ／ skeleton 0
★run_next 0回 ／ task の 状態変更 0 ／ 待ち行列の 並べ替え 0（★ご指示以降）
★古い 159件 = CREATED の まま 無傷
```
