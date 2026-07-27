# 実装 → 設計/監査: Build 15 — `approval_id` に nonce を足し、`#attempt-N` の細工を廃止した（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD15_SPEC_NONCE_AND_VOCAB.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_BUILD15_APPROVED.md`（写しで観測）
- **本文書は観測と実装を書きます。判定・評価をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` 削除 / `cc_register.py` path 欠陥: **[x] いずれも実施済**

---

## 0. ★これは修理です。新機能ではありません
| 足した | 廃止した |
|---|---|
| `grant_approval` の optional `nonce`（既定 `None` ＝ 現行と同一 id） | `mint_token` が `task_id` に `#attempt-N` を混ぜる細工 |

**差し引きで増えていません。** **`ts` を汚していません。`conformance_probe` を書き換えていません。**

## 1. 変更（2ファイルのみ）
| ファイル | 変更 |
|---|---|
| `twoder/authority.py` | `grant_approval(..., nonce=None)` を末尾に追加。hash 入力は **`nonce is None` なら従来どおり**、それ以外は `\|nonce` を1項目足す。**`validate_approval` は不変。GRANT 記録に `nonce` を保存していません**（照合に使われない列を足さないため） |
| `twoder/generate_via_runner.py` | `mint_token` を **正典語彙 `LIVE_WORKER_MINIMAL` / `LIVE_WORKER_TASK`**・**素の `task_id`**・**`nonce=attempt`** に。**docstring も書き換え、古い説明を残していません** |

**コードから `#attempt-` は消えています**（残存は私が書いた docstring 内の「"#attempt-N" 混入ではなく」という説明文のみ・`grep -n` で確認）。

## 2. 受入（すべて実行・結果を貼ります）

### ① 既定 `None` で id が変わらない【監査:IMPL】
```
修理【前】に実測: grant_approval("LIVE_WORKER_MINIMAL","TASK-X","LIVE_WORKER_TASK","taka","2026-07-11T09:00:00")
                 → APPROVAL-29ac9930ca
修理【後】に実測: 同じ引数            → APPROVAL-29ac9930ca      一致 = True
```
**※本番台帳に試験行を書かないよう `DS_DATA_DIR` を一時ディレクトリへ隔離して実行しています**（§3-7）。

### ② `conformance_probe` の `gate1b_ts`（★C2 の証拠・書き換えずに）
```
再現: PYTHONPATH=/home/takasan python3 -c "import sys;sys.path.insert(0,'/home/takasan/twoder/probe');
      import conformance_probe as P; print(P._gate1b_ts())"
結果: GateOutcome(passed=True, expected={'distinct': True}, actual={'distinct': True},
                  expected_from='/home/takasan/twoder/generate_via_runner.py:39-52',
                  actual_from='/home/takasan/twoder/generate_via_runner.py:39-52', …)
```
**`passed=True`。`conformance_probe.py` は1行も変えていません。**
※実装源は `twoder/conformance_probe.py` と記していましたが、**実在は `twoder/probe/conformance_probe.py`** でした（探索して確認）。

### ③ attempt 違いで id が異なる（同一 `ts`）
```
mint_token(1, task_id="T") = APPROVAL-a4382e1c7a
mint_token(2, task_id="T") = APPROVAL-1f0b0270f5      異なる = True
```

### ④ 台帳の `task_id` が素であること（★C1 の証拠）
```
approval_registry._load_grant("APPROVAL-a4382e1c7a")
  task_id         = 'T'                    （"#attempt" を含まない）
  action_type     = LIVE_WORKER_MINIMAL
  operation_class = LIVE_WORKER_TASK
```

### ⑤ 既存 GRANT が引き続き引けること
**①の修理後の実測が、修理前と同一の `APPROVAL-29ac9930ca` を返しています。** ＝ **既定 `None` 経路の id 生成は不変で、既存 GRANT の引き当てに影響しません。**
**なお本番台帳の既存 GRANT を直接引く確認は行っていません**（§3-7 の「台帳に試験行を書かない」を優先し、隔離環境で実行したため）。**この点は実施していないと申告します。**

### ⑥ 非回帰4本
```
twoder/tests/test_approval_registry.py        exit=0（出力0行）
twoder/tests/test_token_wiring.py             exit=0（出力0行）
twoder/regression/test_live_worker_runtime.py 15/15 passed
twoder/regression/test_full_live_e2e.py       7/7 passed
```
**※前2本は「成功時に何も出力しない」設計でした**（`exit=0` で判定）。**最初 `cwd` が `egl/docs` のままで `ModuleNotFoundError` を出しましたが、これは私の実行方法の誤りで、`PYTHONPATH=/home/takasan` を通して取り直しています。誤った出力を根拠にしていません。**

### ⑦ 触らないファイルが1行も変わっていないこと
```
git status --porcelain approval_registry.py live_worker_runtime.py conformance_probe.py
  → 出力なし（無変更）
git status --porcelain（全体）
  → M authority.py / M generate_via_runner.py   ← 指定2ファイルのみ
```

## 3. やらなかったこと（§3）
- **`ts` に attempt を入れていません。**
- **`conformance_probe` を書き換えていません。**
- **`task_id` に suffix を残していません。**
- **新しい語彙・台帳・フラグを作っていません**（`LIVE_WORKER_MINIMAL` / `LIVE_WORKER_TASK` は既存語彙）。
- **GRANT 記録に使われない列を足していません。**
- **`GENERATE` を走らせていません。**
- **`CC_REGISTER.jsonl` に試験行を書いていません**（試験は一時 `DS_DATA_DIR` で実施）。

## 4. 予想と実際
| 項目 | 予想 | **実際** | 判定 |
|---|---|---|---|
| 既定 `None` の id | 修理前後で一致 | **一致（`APPROVAL-29ac9930ca`）** | **当たり** |
| `gate1b_ts` | 通る | **`passed=True`** | **当たり** |
| 非回帰4本 | すべて PASS | **4本とも PASS**（前2本は exit=0） | **当たり** |

## 5. commit
**していません**（MGR）。触った本番ファイル: `twoder/authority.py` / `twoder/generate_via_runner.py`。

---
*IMPL BUILT（Build 15・修理）。`grant_approval` に optional `nonce` を追加（**既定 `None` で id が修理前と一致することを前後実測: `APPROVAL-29ac9930ca`**）、`mint_token` を正典語彙・素の `task_id`・`nonce=attempt` に変更し docstring も更新。**`gate1b_ts` は `conformance_probe` を書き換えずに `passed=True`（C2 の証拠）**、`_load_grant` の `task_id` は `'T'` で suffix なし（C1 の証拠）。非回帰4本 PASS。触らない3ファイルは無変更。**受入⑤の「本番台帳の既存 GRANT を直接引く確認」は、台帳に試験行を書かない規律を優先して実施していないと申告。** `GENERATE` は走らせていない。*
