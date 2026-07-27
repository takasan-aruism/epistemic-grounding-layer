# 実装 → 設計/監査: Build 13 — **契約が封印され、PLAN まで通った**（BUILT）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.9）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD13_SPEC_WORKER_WITH_CONTRACT.md` v1.0
- **受領した文書**: 上記実装源 / `CC_MGR_2026-07-27_STAGE3_GO_RESUME_DEV.md`（写しで観測）
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 到達経路
- [x] **(A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- `twoder/ledger_query.py` の削除: **[x] 実施済**（本 build では触っていない）
- **`cc_register.py` の path 表記の欠陥（`CC_DESIGN_..._D21_PATH_CONVENTION_DEFECT.md`）: [ ] 未対応**——**実装源が降りていないため触っていません。**§6 に事実を書きます。

---

## 1. 依頼文の扱い（1文字も変えていません）【監査:IMPL】
**手打ちせず、実装源 §1 の ```` ブロックを機械的に抽出して投入しました。**
```
文字数            : 2411
<<<2DER:SKELETON>>>       : 1
<<<2DER:IMMUTABLE_TESTS>>>: 1
<<<2DER:END>>>            : 2
先頭 : 宛: 設計/監査(CC-α)
末尾 : <<<2DER:END>>>
```
**マーカーの対応は壊れていません。`/api/submit` は例外を返していません**（実装源が想定した `ValueError` / 500 は発生していません）。

## 2. 投入と進行（各1回）【監査:IMPL】
```
POST /api/submit   → task_id=TASK-2DER-21F64D9D / request_type=BUILD_CAPABILITY / runnable=true
POST /api/run_next → dispatched=true / reason=None      ← 1回だけ
nlo                : state=CREATED / operation=PLAN / actor_role=MANAGER / actor_id=CLAUDE
planner_outcome    : null（キーは存在）
```
**結果:**
```
derive_state('TASK-2DER-21F64D9D') = READY_FOR_IMPLEMENTATION / has_plan: True
events = ['CREATE', 'PROCESS_EVENT', 'PLAN']
```
**`run_until_barrier` を使っていません。GENERATE へ進んでいません。token を迂回していません。**

## 3. ★契約が封印されたことの確認【監査:IMPL】
実装源 §2 は「**確認は次段の `GENERATE` でしか出ない可能性がある**」としていましたが、**台帳の CREATE イベントで確認できました。**

**(a) `contract_seal.extract_contract` の返り（同じ依頼文で直接実行）:**
```
返り型 : dict（例外なし）
  skeleton               : def answer(rid, resolve_fn, known_prefixes): …
  immutable_tests        : from impl import answer / KP = ("DE","UTT") …
  skeleton_sha256        : 0ece422b0069e1fba8cc9698842744eee977678ee496fc88c04f7f11de3aab6d
  immutable_tests_sha256 : 3458567194083aba5097c1f35363f726e8a5bf855bfccfc7433127831f1f0d78
  sealed_by              : contract_seal
```
**(b) task の `CREATE` payload:**
```
CREATE payload のキー : ['contract', 'goal', 'knowledge_packet', 'project_id']
contract の有無       : True
contract のキー       : ['immutable_tests', 'immutable_tests_sha256', 'sealed_by',
                         'skeleton', 'skeleton_sha256']
```
**＝ 契約は `skeleton` / `immutable_tests` とその sha256 つきで task に入っています。**

## 4. 予想と実際
| 項目 | 予想 | **実際** | 判定 |
|---|---|---|---|
| `RRI_REQUEST_TYPE` | `BUILD_CAPABILITY` | **`BUILD_CAPABILITY`** | **当たり** |
| `DW_TASK_ID` | 新しい id | **`TASK-2DER-21F64D9D`**（`B9B4DA3B` と別） | **当たり** |
| 契約が封印されたか | **される**（確認は GENERATE でしか出ない可能性） | **された。CREATE で確認できた** | **当たり**（確認時期は予想より早い） |

## 5. Build 12 との差（事実）
| | Build 12 | **Build 13** |
|---|---|---|
| 契約マーカー | 無し | **有り（両方・対応も揃う）** |
| `extract_contract` | — | **dict を返した（例外なし）** |
| task の `contract` | — | **入っている（sha256 つき）** |
| 到達 | `GENERATE` まで進み `SPEC_INCOMPLETE_NO_CONTRACT` | **`PLAN` で停止（仕様どおり）** |

## 6. 未対応として申告します（本 build の範囲外）
**`egl/docs/cc_register.py` の path 表記の欠陥**（`CC_DESIGN_2026-07-27_D21_PATH_CONVENTION_DEFECT.md`）は**未対応**です。
**事実として1点補足します**: 当該 FINDING は原因を CC-α の入力としていますが、**D-21 の受入③で `record_doc("egl/docs/...")` を実際に呼んだのは私です。** 同じ BUILT の受入②では `docs/CC_x.md`（repo 相対）で一致を示しており、**私は同一文書内で2つの表記を使い分けたまま気づいていませんでした。**
**`cc_register.py` は変更していません。** 修正の実装源を待ちます。

## 7. 守った禁止事項
- **依頼文を1文字も変えていません**（機械抽出）。
- **`run_next` は1回・`run_until_barrier` 不使用・GENERATE へ進んでいません。**
- **token を迂回していません。**
- **本番コードを変更していません**（本 build では1行も）。
- **成果物の検査・配置・配線をしていません。**

## 8. 観測の限界（事実として）
- **1回しか実行していません。**
- **契約が worker に正しく渡るかは未確認です**（`GENERATE` を実行していないため）。**確認できたのは「task に封印されている」ところまでです。**

## 9. commit
**していません**（MGR）。

---
*IMPL BUILT（Build 13）。実装源の依頼文を機械抽出して1文字も変えず投入（2411字・マーカー対応 OK・`/api/submit` は例外なし）。`TASK-2DER-21F64D9D` で `PLAN` が記録され `READY_FOR_IMPLEMENTATION`。**★契約の封印を CREATE payload で確認**（`skeleton`/`immutable_tests`＋各 sha256・`sealed_by=contract_seal`）——実装源は「GENERATE でしか出ない可能性」としていたが CREATE で確認できた。予想3項目とも当たり。GENERATE へ進まず停止。`cc_register.py` の path 欠陥は未対応（実装源待ち）だが、受入③で `egl/docs/...` を渡したのは私であると申告する。*
