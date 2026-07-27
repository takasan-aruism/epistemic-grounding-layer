# BUILD SPEC — Build 15: **`approval_id` に nonce を足し、`#attempt-N` の細工を廃止する（修理）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.9）**
- 権限: `CC_MGR_2026-07-27_D26_APPROVED_NONCE_TRADE.md`
- 根拠: `CC_DESIGN_2026-07-27_D26_BLAST_RADIUS.md`（影響範囲）/ `..._D25_CANONICAL_VOCAB.md` §1（正典語彙）

## 0. ★これは修理である。新機能ではない
**足すもの / 廃止するもの を対にする（v1.9）:**
| 足す | 廃止する |
|---|---|
| `approval_id` の計算に **optional な nonce**（既定 `None` ＝現行と同一の id） | **`task_id` に `#attempt-N` を混ぜる細工**（`mint_token`） |

**∴ 差し引きで増えていない。** **「一意性のために別フィールドを汚す」細工が消え、一意性の入力が正面から1つ増える。**

## 0-1. 何を直すのか（3つの制約を同時に立てる）
| 制約 | 満たし方 |
|---|---|
| **C1** 検証は素の `task_id` を求める | **suffix を付けない** |
| **C2** 同一 `ts` で attempt だけ変えて id が異なる | **nonce を hash 入力に含める** |
| **C3** `approval_id` の入力が4項目しか無い | **★1項目増やす。これが本体** |

**★`ts` を汚さない。`conformance_probe` を書き換えない。**

---

## 1. 変更（2ファイルのみ）

### 1-1. `twoder/authority.py`
```
grant_approval(action_type, task_id, operation_class, approved_by, ts,
               approved_scope=None, expiry=None, nonce=None)      ← nonce を末尾に追加

approval_id の hash 入力:
  nonce が None      → 現行どおり "task_id|operation_class|action_type|ts"（★id が変わらない）
  nonce が None 以外 → 上に nonce を1項目足した文字列
```
- **`validate_approval` は変更しない**（`approval_registry` の docstring が「既存の `authority.validate_approval` は変更しない」と宣言している）。
- **GRANT 記録に `nonce` を保存するかは、保存しない**（**検証は id で引くだけであり、保存しても照合に使われない＝使われない列を足さない**）。

### 1-2. `twoder/generate_via_runner.py` の `mint_token`
```
現行: _REAL_MINTER("USE_VLLM_INFERENCE", "%s#attempt-%s" % (task_id, attempt), "DW_MACHINE_OP", …)
修理: _REAL_MINTER("LIVE_WORKER_MINIMAL", task_id, "LIVE_WORKER_TASK", …, nonce=attempt)
```
- **語彙は既存**（`counterfactual_runner.py:54` が実使用）。**新設しない。**
- **`task_id` は素のまま。**
- **docstring を直す**（「attempt を入力に含める」の意味が `task_id` から `nonce` に変わったため）。**★古い説明を残さない。**

### 1-3. 触らないもの
`approval_registry.py` / `live_worker_runtime.py` / `conformance_probe.py` / `authority.validate_approval` / 既存の呼び出し7箇所。

---

## 2. 受入（すべて実行して結果を貼る）
1. **★既定 `None` で id が変わらないこと**——**修理の前後で、同じ引数から同じ `approval_id` が出ることを実測して示す**（例: `grant_approval("LIVE_WORKER_MINIMAL","TASK-X","LIVE_WORKER_TASK","taka","2026-07-11T09:00:00")`）。**前後の値を両方貼る。**
2. **★`conformance_probe` の `gate1b_ts` が通ること**（**書き換えずに**）。**これが C2 の証拠である。**
3. **`mint_token(1, task_id="T")` と `mint_token(2, task_id="T")` が異なる id を返すこと**（同一 `ts`）。
4. **`mint_token` が返した id を `authority` 台帳から引くと、`task_id` が素の値であること**（C1 の証拠）。
5. **既存 GRANT 記録が引き続き引けること**（**修理前に存在した id を1つ選び、`approval_registry._load_grant` で引けることを示す**）。
6. **非回帰**: `twoder/tests/test_approval_registry.py` / `test_token_wiring.py` / `twoder/regression/test_live_worker_runtime.py` / `test_full_live_e2e.py`。**実行して結果を貼る。**
7. **`approval_registry.py` / `live_worker_runtime.py` / `conformance_probe.py` を1行も変えていないこと。**
8. **修理であって新機能ではないと明記。**
9. **commit しない。** 冒頭に「運用方針 確認済（版: v1.9）」。**定型見出し（到達経路 / 前回からの持ち越し）。**
10. **v1.5**: 「動く」と書くときは再現コマンドと結果を併記。

## 3. やってはいけないこと
1. **`ts` に attempt を入れない**（MGR 裁定）。
2. **`conformance_probe` を書き換えない**（試験を仕様に合わせて曲げない）。
3. **`task_id` に suffix を残さない。**
4. **新しい語彙・台帳・フラグを作らない。**
5. **GRANT 記録に使われない列を足さない。**
6. **`GENERATE` を走らせない**（本 build は修理まで。実行は次）。
7. **台帳（`CC_REGISTER.jsonl`）に試験行を書かない。** 試験が要るなら一時ファイルで。

## 4. 予想（実測前に固定）
| 項目 | 予想 |
|---|---|
| 既定 `None` の id | **修理前後で一致する** |
| `gate1b_ts` | **通る** |
| 非回帰4本 | **すべて PASS** |
| **【未確認】** | **`authority.py` の間接呼び出しを私は網羅していない。** **非回帰が落ちたら、そこで止めて上げること** |

---
*BUILD SPEC v1.0（★実装源）。Build 15=`approval_id` に optional な nonce を足し、`mint_token` の `#attempt-N` 細工を廃止する修理（足す/廃止するを対にしたので差し引き増えていない）。C1 素の task_id・C2 同一 ts で attempt 一意・C3 入力を1項目増やす、を同時に立てる。★`ts` を汚さず `conformance_probe` を書き換えない。変更は `authority.py`(nonce を末尾に追加・None なら現行と同一 id・`validate_approval` は不変・GRANT に nonce を保存しない＝使われない列を足さない) と `generate_via_runner.mint_token`(正典語彙 LIVE_WORKER_MINIMAL/LIVE_WORKER_TASK・素の task_id・nonce=attempt・docstring も直して古い説明を残さない) の2ファイルのみ。受入=既定 None で修理前後の id が一致することを実測／`gate1b_ts` が書き換えずに通る（C2 の証拠）／attempt 違いで id が異なる／台帳の task_id が素（C1 の証拠）／既存 GRANT が引き続き引ける／非回帰4本／触らないファイルを1行も変えていない。禁止=ts に attempt を入れない・probe を曲げない・suffix を残さない・新語彙を作らない・使われない列を足さない・GENERATE を走らせない・台帳に試験行を書かない。【未確認】間接呼び出しは未網羅なので非回帰が落ちたら止めて上げる。*
