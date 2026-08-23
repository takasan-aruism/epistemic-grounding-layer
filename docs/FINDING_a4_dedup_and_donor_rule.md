# FINDING: (kind,file) 重複除去 と 供給元規則の併設（同一 leave-one-out 比較）

作成: Claude Code (MGR) / 2026-08-24 / 親: ITEM-2DER-EVO-0094
関連: ART-ddc85390f7（file 追加鍵の少数実走）/ ART-d6809170f9 / ART-2a589bd5d3

Taka 裁定 逐語:
「(kind,file) の重複除去は実装する。候補水増しの既知欠陥として修正し、有用候補が消えないことを試験で固定。」
「『供給元が持っていて対象TASKが持っていない』向きを、採用規則ではなく観測規則として併設する。」
「現行 missing-rate 規則は消さない。両者を同じ leave-one-out で比較する。」
「n=1 の結果だけで正規規則へ昇格しない。」
「母数拡大はその比較後。逆向きの規則のまま母数だけ増やさない。」
「blocking / required / PLAN品質改善の主張は禁止のまま。」

## 1. (kind,file) 重複除去 ―― 既知欠陥の修正

★水増しの正体 = **同じ file の 同じ kind を 科目別の部分群3つが それぞれ 出していた**。
実測 = 24提案 → **8提案**（kind の集合は不変）。

★有用候補が消えないことの担保を **規則そのものに埋めた**:
- 残すのは `missing_rate` 最大 → 同率なら `n_tasks` 最大の1件
- **畳んだ相手は捨てず `merged_from` に根拠として残す**（出所を消さない）
- ∴ **出る kind の集合は畳む前と完全に同じ** = 有用候補は原理的に消えない

★試験で固定（新規9本 / `twoder/regression/test_task_similarity.py` 計27本 全通過）:

| 試験 | 固定した事実 |
|---|---|
| `test_dedup_never_drops_a_kind` | ★出る kind 集合・(kind,file) 集合が畳む前と完全一致 |
| `test_dedup_collapses_same_kind_and_file` | 同じ (kind,file) は1件になる |
| `test_dedup_keeps_different_file_separate` | file が違えば畳まない |
| `test_dedup_keeps_the_strongest_and_records_the_rest` | 最強を残し `merged_from` に相手を残す |
| `test_dedup_is_idempotent_and_safe_on_empty` | 冪等・空でも安全 |
| `test_dedup_handles_file_none_for_base_rule` | base 側 (file=None) も kind ごとに畳める |
| `test_donor_rule_is_observation_only_not_adopted` | ★観測規則は正規規則に昇格していない |
| `test_donor_rule_does_not_replace_missing_rate_rule` | ★現行規則を消していない（両方引ける・閾値 0.67 維持） |
| `test_donor_rule_fires_only_when_donor_has_it_and_i_do_not` | 供給元が持ち自分が持たない時だけ出る |

## 2. 観測規則の併設（★採用していない）

```
RULE_MISSING_RATE  = "MISSING_RATE"     # ★採用規則（現行・消していない）
RULE_DONOR_HAS_IT  = "DONOR_HAS_IT"     # ★観測規則
OBSERVATION_ONLY_RULES = ("DONOR_HAS_IT",)
```

- 返りの各件に `observation_only: True`
- `dry_run_pair()` の返りに `rules: {"adopted": ["MISSING_RATE"], "observation_only": ["DONOR_HAS_IT"]}`
  = **どちらが採用規則かをデータ側が持つ**（人の記憶に置かない）

## 3. ★同一 leave-one-out での3側比較（file を持つ 16 TASK・重複除去後）

| 側 | 提案 | 有用 | 有用率 | already_present | 候補なし | 正しい沈黙 | 取り逃し | 正しく返せた率 |
|---|---|---|---|---|---|---|---|---|
| **base**（MISSING_RATE・採用規則） | 16 | 13 | **0.812** | 3 | 11 | 10 | 1 | 0.909 |
| **withfile**（MISSING_RATE + file） | 8 | 6 | **0.750** | 2 | 13 | 12 | 1 | 0.923 |
| **★donor**（DONOR_HAS_IT・★観測のみ） | 2 | 2 | **1.000** | 0 | 15 | 15 | **0** | **1.000** |

★**base に無かった有用候補: withfile = 0 / ★donor = 2**

発火の全件（donor 側）:

```
TASK-2DER-EF6826DC   actual={CHANGE,CONSTRAINT,FACT,GOAL}  ← SPEC 0 / TEST 0
   base = なし   withfile = なし
   ★donor = SPEC <- TASK-2DER-ED65242E-hiWrsw
            TEST <- TASK-2DER-ED65242E-hiWrsw   （同 file = twoder/account_gate.py）
```

EF6826DC は SPEC/TEST 無しで走り **REGEN=1 / DISPOSE=2 / BLOCK=1** で失敗した依頼。

## 4. ★昇格しない理由（数字が良いが n=1）

- donor 側の有用率 1.000・取り逃し 0 は **発火が1 TASK・2提案しか無い**ため。
  ★**16 TASK 中 15 TASK で沈黙している**。分母がほぼ全部「出さなかった」側にある。
- 有用率 1.000 は **既知の失敗例1件を当てた**だけで、規則の一般性を示していない。
- ∴ **正規規則へ昇格しない**（Taka 裁定 逐語）。`OBSERVATION_ONLY_RULES` に置いたまま。
- ★`withfile` は base に無かった有用候補が **0件**のまま = **file を missing_rate 規則に足す形は効いていない**。

## 5. 母数拡大について（★まだ行っていない）

Taka 裁定 逐語「母数拡大はその比較後。逆向きの規則のまま母数だけ増やさない」。
★比較の結果、**`missing_rate + file` は向きが目的と逆のまま**（新規有用候補 0）。
∴ **この形のまま母数だけ増やすことはしない**。donor 規則は n=1 で昇格できない。
→ 次に要るのは **donor 規則が発火する対をもっと集めること**（＝供給元が存在する file 対の母数）
   であり、`missing_rate + file` の母数拡大ではない。判断は Taka へ上げる。

## 6. 禁止の維持

- ★blocking 化していない / ★required 化していない
- ★PLAN 品質の改善を主張していない
- symbol は引き続き類似群の入力から除外（`REF_KINDS_EXCLUDED = ("symbol",)`）
