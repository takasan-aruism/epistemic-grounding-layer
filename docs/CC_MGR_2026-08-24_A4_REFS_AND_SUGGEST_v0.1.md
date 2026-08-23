# A4-①② refs=0 の原因確定 と 不足情報候補の接続 v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**ITEM: `ITEM-2DER-EVO-0094`**
**裁定（逐語・要点）: 順序を固定 ①refs=0 の原因調査 ②既存の不足情報候補を「提案」として次回TASK投入へ接続
③少数実走で効果を測る ④その後に母数拡大 ⑤embedding は最後／
「0件だから存在しない」と結論しない。writer / reader / projection のどこで消えたかを分ける／blocking にしない**

---

## 1. ★① refs=0 の原因 — **writer が居なかった**

「0件だから存在しない」とは結論していない。**3つに分けて確かめた。**

| 層 | 実測 | 判定 |
|---|---|---|
| **producer（抽出器）** | `twoder.detail_refs.extract_refs` は**動く** ―― 対照で `twoder/account_gate.py` `/api/approve` `classify_account` を取れた | ★正常 |
| **writer（呼び手）** | **`extract_refs` の本番呼び手 0件**（試験だけ）。`requirement_structure.structure()` は `refs` を**1文字も書いていなかった**。`detail_backfill` は `structure()` の返りをそのまま渡す ∴ **常に空** | ★**ここで消えた** |
| **ledger** | 全version で `refs` を持つ行 **4行 / 1 thread**（`RTHREAD-4d89c66c`）＝**段2 で私が手で入れた分だけ** | ★書かれていなかった |
| **reader / projection** | `list_typed` は `refs` を返りの欄に**入れている** | ★正常 |
| **最新versionだけ読むことで消えたか** | 全version 4行・いまの版 4行 ＝ **同じ**。★版の切替では消えていない | ★否 |
| **対象73 TASK に ref 候補が無いのか** | ★**否**。直したら 956参照が取れた | ★否 |
| **段2/段3以降に限定されていたか** | ★**否**。限定ではなく**呼び手が存在しなかった** | ★否 |

**∴ 原因は「writer が居ない」。抽出器でも読み口でも projection でもない。**

### 1.1 直したもの

`structure(raw_text, parent_request_id, with_refs=False, check_refs=False)`
- **既存の `extract_refs` をそのまま呼ぶ**（新しい抽出器 0）
- **既定は両方 `False` ＝ 従来と完全に同じ返り**（試験で固定）
- `detail_backfill` を `with_refs=True, check_refs=True` に繋いだ

### 1.2 適用結果

```
REFS_APPLY 74.0秒  thread 89 / refs を持つ行 167
台帳: 構造化 1,159行 中 ★refs を持つ行 171 / ★参照 956
参照の型: symbol 735 / 2der_id 124 / file 94 / api 3
```

**類似群の共通 refs 型: ★0/11群 → 5/11群**

```
OBSERVE_CURRENT_STATE|LDET-2d01f311   file 0.333 / symbol 0.167
BUILD_CAPABILITY|LDET-b654430e        2der_id 0.400 / symbol 0.200 / file 0.200
MODIFY_EXISTING|LDET-9fad13bd         ★file 0.500 / 2der_id 0.250
MODIFY_EXISTING|LDET-04574589         ★file 0.667 / 2der_id 0.333
BUILD_CAPABILITY|LDET-26ee37a2        ★2der_id 0.667 / symbol 0.333 / file 0.333
```

★**半数以上の TASK が持つ参照型**: `file` 2群 / `2der_id` 1群。
∴ **「file ref が必要」というテンプレート候補は、いま材料が出てきた**（前回は0件で作れなかった）。

---

## 2. ★② 不足情報候補の接続（★blocking にしていない）

`task_similarity.suggest_missing(request_type, accounts)` / `suggest_for_task(task_id)`。

**裁定で禁じられたことを実装で守った:**

| 禁止 | 実装 |
|---|---|
| required と断定しない | 語は **`missing_often`** の意味の `missing_rate`。返りに `required` という語が無い |
| 自動拒否しない | **返りに拒否の指示を持たない**（`reject` 等の語が0） |
| TASK内容を補完して発明しない | **不足の種別名しか返さない**（本文を作らない） |
| 不足候補を提示するだけ | `basis` に逐語で `"this is an observation, not a requirement"` |
| `proposed_kind` を正本入力に使わない | **LLM を1回も呼んでいない** |
| 1件や2件で作らない | `MIN_TASKS_FOR_SUGGESTION = 3` ／ `MISSING_THRESHOLD = 0.67` |

### 2.1 実測（提案の中身）

```
MODIFY_EXISTING  完了ワークフロー   -> SPEC(100%・4TASK) / TEST(100%) / GOAL(100%)
MODIFY_EXISTING  タスク状態管理     -> SPEC(100%・3TASK) / TEST(100%) / GOAL(100%)
BUILD_CAPABILITY データ統合ツール   -> FACT(100%・7TASK) / TEST(100%) / CONSTRAINT(100%) / CHANGE(86%) / GOAL(86%)
OBSERVE_CURRENT_STATE 分析        -> TEST(100%・6TASK) / GOAL(100%) / FACT(83%)
★当たらない例                     -> 群0・提案なし(★推測で 埋めない)
```

**★まだ front door / RRI へ配線していない。** 口は在るが、投入時に自動で出す配線は
**③の少数実走の結果を見てから**にする（裁定の順序どおり）。

---

## 3. ④ 母数拡大の下調べ（★構造化不足を類似度で埋めない）

```
TRACE を持つ TASK: 1,399
  FULL        218 (15.6%)  ★群に入れる(鍵＋詳細明細)
  KEYS_ONLY   299 (21.4%)  ★LOW_INFORMATION(鍵は在るが構造化なし)
  TYPE_ONLY   882 (63.0%)  ★LOW_INFORMATION(request_type だけ)
  NO_KEY        0 ( 0.0%)
```

**`FULL` は 218件**（前回の観測は 73 TASK だった ＝ refs 適用で構造化が増えた分）。
`KEYS_ONLY` の request_type 分布: `BUILD_CAPABILITY` 169 / `OBSERVE` 67 / `MODIFY_EXISTING` 59 / `RESUME_PRIOR` 4。

**★`LOW_INFORMATION` は別扱いにしたまま、群へ入れていない。**

---

## 4. ⑤ embedding — 触っていない

裁定どおり最後。**1行も書いていない。**
`request_type + account` の11群で refs も出るようになったため、
**「既存鍵では群に入らないが人間には似て見える TASK」を救う必要は、まだ実測されていない。**

---

## 5. 触っていないもの

- `detail_refs` の抽出規則（**1文字も変えていない** ―― 呼び手を足しただけ）
- `KINDS` / `_CUES` / `_CUES_V2` / 勘定科目 / 処分 / 保存則
- LLM（`kind_vote` は**1回も呼んでいない**）
- front door / RRI への配線（★②の口は作ったが**繋いでいない**）
- embedding

## 6. 未確認・次

1. **③少数実走が未実施** ―― 候補提示あり／なしの比較はこれから
2. **`symbol` が 735件と突出**。`_SYMBOL` の正規表現が広すぎる可能性は**未検証**
   （段2 で「型注記を関数と誤認する」事故を1度直しているが、母数が変わった）
3. **`refs` の実在率を測っていない** ―― `check_refs=True` で確認はしたが、
   ✓/✗ の内訳を集計していない
4. `FULL` が 73 → 218 に増えた内訳（refs 適用で構造化が付いた分）を**分離していない**
