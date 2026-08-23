# FINDING: A4 file 追加鍵の少数実走（leave-one-out・16 TASK）

作成: Claude Code (MGR) / 2026-08-24 / 親: ITEM-2DER-EVO-0094
関連: ART-d6809170f9（候補1 before/after）/ ART-2a589bd5d3（抽出器の残欠陥3件）

Taka 裁定 逐語（本走行の目的）:
「次の目的は『fileが似ているから同じTASK』と決めることではなく、同じfile群に触れるTASKで
 SPEC / TEST / GOAL / CONSTRAINT / evidence の不足傾向が再利用できるかを見ること。」
「file単独でclusterを作らず、request_type + account + file の追加鍵として使った場合に
 既存11群がどう分かれるかを見る。」
「少数実走では leave-one-out を維持し、自分自身の情報を候補生成に使わない。」
「blocking化しない。required化しない。PLAN品質改善もまだ主張しない。」

## 0. 母数の訂正（★台帳の refs は古い抽出器の結果）

- 台帳の `refs` は候補1 以前の抽出器で取ったもの（契約マーカー内の生成物を含む）。
  ★履歴は消さず **読む側で取り直した**（`eligible_details(recompute_refs=True)`）。
- 共有file（2件以上で共有）は **thread 単位 9件 → A4 正本入力(5条件通過後) ★3件**。

| file | TASK 数 |
|---|---|
| `latest_test_result.py` | 8 |
| `twoder/source_to_patch.py` | 2 |
| `twoder/account_gate.py` | 2 |

★`latest_test_result.py` の8件は **同一依頼文の再投入**（`0810-0640a` / `0811-0255` / `0811-2225` …
日付だけ違う）。全件 account なし・kind={CHANGE:1}・evidence 0。
∴ **科目鍵が付かないため群を作れず、自動的に落ちる**＝偽の類似を科目が止めていた。

## 1. 横断集計（共有file 9件・thread 単位）

| file | thread | request_type | 欠けている kind | evidence | REGEN / DISPOSE / BLOCK |
|---|---|---|---|---|---|
| `latest_test_result.py` | 8 | 全て MODIFY_EXISTING | 全件 SPEC/TEST/GOAL/CONSTRAINT | 全件 0 | 全件 0 |
| `twoder/account_gate.py` | 2 | MODIFY_EXISTING | ED65242E=欠け無し / **EF6826DC=SPEC,TEST** | 9 / **0** | 0,0,0 / **1,2,1** |
| `twoder/X.py` | 2 | OBSERVE_CURRENT_STATE | SPEC/TEST/GOAL/CONS | 0 / 1 | 1,2,0 |
| `twoder/patch_bridge.py` | 2 | MODIFY / OBSERVE | SPEC/TEST/GOAL | 0 | 0,0,0 / 1,2,0 |
| `twoder/operator.py` | 2 | MODIFY / OBSERVE | SPEC/TEST/GOAL | 0 | 同上 |
| `CC_MGR_…SAFE_SINGLE_SHOT…md` | 2 | MODIFY / OBSERVE | SPEC/TEST/GOAL | 0 | 1,2,0 両方 |
| `CC_MGR_…PIPELINE_CONVENTIONS…md` | 2 | OBSERVE 両方 | SPEC/TEST | 0 | 0,0,0 / 1,2,0 |
| `twoder/source_to_patch.py` | 2 | MODIFY 両方 | SPEC/TEST/GOAL | 0 | 0,0,0 両方 |
| `twoder/bridge_minter.py` | 2 | MODIFY / BUILD | SPEC/TEST/GOAL / TEST | 0 | 0,0,0 両方 |

★**供給元（同じ file に触れ、相手が欠く kind を持つ TASK）が居るのは `twoder/account_gate.py` の1対だけ**。
他は「両方とも同じものを欠いている」＝引き写す先が無い。

## 2. 計器の欠陥2件（先に直した）

1. **dw の `task_id` と TRACE の `task_id` が形式違いで繋がっていなかった**
   （TRACE=`TASK-2DER-ED65242E-hiWrsw` / dw=`TASK-2DER-ED65242E`）。
   重なり **131/348 → 正規化後 281/281**。成功/失敗・再生成回数を取りこぼしていた。
2. `eligible_details()` の refs が台帳の古い抽出結果を読んでいた（上の 0.）。

## 3. 既存11群に file を追加鍵として足した場合の分かれ方

| 群 | file を持つ task | 2 task 以上を保つ部分群 |
|---|---|---|
| MODIFY_EXISTING｜完了ワークフロー | 4/4 | ★`source_to_patch.py` 2 task |
| MODIFY_EXISTING｜タスク状態管理 | 3/3 | ★`source_to_patch.py` 2 task（同じ対） |
| 残り9群 | — | ★分かれない |

★**11群のうち2群だけ**が分かれ、中身は同じ1対。**file を1件も持たない task が 26件**。
file 追加鍵の群は6つできるが、実体は **4 TASK・全て n=2**。

## 4. 少数実走（leave-one-out・file を持つ 16 TASK・重複除去後）

| | 提案 | 有用 | 有用率 | already_present |
|---|---|---|---|---|
| base（request_type + account） | 16 | 13 | **0.812** | 3 |
| withfile（+ file・母数下限1） | 8 | 6 | **0.750** | 2 |

- ★**file を足して初めて出た有用候補: 0**
- ★**file を足して出た誤った候補: 2**（`ED65242E` の SPEC/TEST。**already_present が2/2とも捕捉**）
- ★**候補なしを正しく返せた率: 12/13 = 0.923**（取り逃し1＝ EF6826DC）
- ★**母数下限2**（「1件2件でテンプレートを作らない」の線）では leave-one-out で n=2→1 に落ち、
  **withfile の提案は 16 TASK すべて 0件**。
- ★重複提案の欠陥: 除去前は 24提案（同一 file が科目別部分群3つに現れ SPEC/TEST/GOAL が3重）。
  **(kind, file) で重複除去が要る**。

## 5. ★中心的な発見: 提案規則の向きが目的と逆

一番効いてほしい1件が、下限を1まで下げても出ない。

```
TASK-2DER-EF6826DC   SPEC 0 / TEST 0 で走り REGEN=1・DISPOSE=2・BLOCK=1 で失敗
   base=なし   withfile=なし
   ★同 file(twoder/account_gate.py) の供給元: SPEC=[ED65242E] / TEST=[ED65242E]
```

原因: 現行 `suggest_missing` は「似た群で **その kind が無いことが多い**」（`missing_rate ≥ 0.67`）で発火する。
leave-one-out で残るのは ED65242E 1件で、**ED65242E は SPEC も TEST も持つ** ∴ `missing_rate = 0` ∴ 沈黙。
★**供給元が居るときほど黙る**。逆に `ED65242E` に出た誤り2件は、欠けている EF6826DC が母数に居たから出た。

Taka の目的（「同じfile群に触れるTASKで不足傾向が再利用できるか」）は
**「隣が持っていて自分が持っていない」** という向き。現行規則はその逆を測っている。

## 6. 対照: 「供給元が持っている」向きの規則（★採用していない・観測のみ）

同じ leave-one-out で、`同じ file に触れる過去 TASK がその kind を持ち、自分は持たない` を提案とした場合:

| | 提案 | 有用 | 有用率 | base に無かった有用 |
|---|---|---|---|---|
| 供給元規則 | 2 | 2 | **1.000** | **2** |

★**発火したのは EF6826DC ただ1件**（SPEC / TEST、供給元は ED65242E）。
★**n=1 の対照であり、規則の採用根拠にはならない**。既知の失敗例1件を当てただけである。

## 7. 結論（現時点）

- **file 単独では A4 の入力として効いていない**（新規有用候補 0 / 誤り +2 / 有用率 0.812→0.750）。
- ただし原因は「file が無意味」ではなく **提案規則の向きが目的と逆で、
  file が指した正しい供給元を使えていない** こと。
- **blocking化していない / required化していない / PLAN品質の改善は主張していない。**
- symbol は引き続き類似群の入力から除外（`REF_KINDS_EXCLUDED = ("symbol",)`）。

## 8. 次に上げる判断（Taka へ）

1. 提案規則に「供給元が持っている」向きを **観測として** 併設するか（n=1 なので採用ではなく併記）。
2. `(kind, file)` の重複除去を入れるか（明確な欠陥・実害は提案件数の水増し）。
3. file 追加鍵は母数が薄い（16/44 TASK・共有3件）。母数拡大を先にするか、規則の向きを先にするか。
