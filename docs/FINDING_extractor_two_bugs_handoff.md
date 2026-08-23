# FINDING: 参照抽出器の残る欠陥3件（A4 本線への実害は無し・別担当へ）

作成: Claude Code (MGR) / 2026-08-24
親: ART-d6809170f9（候補1 before/after）/ ITEM-2DER-EVO-0094

Taka 裁定 逐語:
「抽出器バグ2件 ・s_*.py の切り出しずれ ・test_ 単独 は別findingとして登録し、
 A4入力へ実害があるかを確認する。file側の共有9件に混ざっていないなら本線を止めず別担当へ送る。
 混ざっているなら先に除外規則だけ直す。」

## 判定: ★混ざっていない → 本線は止めない

| # | 欠陥 | 実例 | 共有file 9件に混入 | A4 正本入力(5条件通過後)に混入 |
|---|---|---|---|---|
| ① | `s_*.py` の切り出しずれ | `s_embed_axes.py` / `s_ledger_account_axes.py` / `s_ledger_account_axis_names.py` / `s_ledger_account_tree.py` | ★無し | ★無し |
| ② | `test_` 単独（接頭辞だけを symbol として拾う） | `test_` | 原理的に無し（symbol 側） | ★無し（symbol は入力から除外中） |
| ③ | ★新規発見: メタ変数を file として拾う | `twoder/X.py`（依頼文の `def X(` → `twoder/X.py` という説明） | ★混ざっていた（2 thread） | ★無し |

- ①② は共有file 9件に1件も現れない。
- ③ `twoder/X.py` は共有file 9件には現れたが、**A4 の正本入力（5条件通過後）では消える**
  （当該2明細は UNVERIFIED / FACT で、条件③④により母数外）。実測 = 共有file 9 → ★3。
- ∴ 3件とも **A4 入力への実害は現時点で 0**。除外規則は広げない（候補1の裁定を維持）。

## 別担当へ送る内容

- ① は抽出器の切り出し規則の欠陥。`s_` で始まる4件がどの原文から出たかを特定し、境界を直す。
- ② は `test_` のような接頭辞のみ・末尾が `_` の識別子を symbol と見なさない。
- ③ はメタ変数（`X` / `<name>` 等のプレースホルダ）を file と見なさない。
  ★注意: ③ は「人が依頼文に書いた文字列」であり、生成物ではない。
  候補1 の除外規則（SKELETON / IMMUTABLE_TESTS）では対象外。別の判定が要る。

## 再測の鍵（引き継ぐ人が同じ数字を出せるように）

- 母集団 = `rri/rri/rthread_events.jsonl` の `QUESTION_TYPED`（thread ごと最新 ts のみ）
- 抽出 = `twoder.detail_refs.extract_refs(text, check=False, skip_generated=True)`
- 共有file = 2 thread 以上に出る file
- A4 正本入力 = `twoder.task_similarity.eligible_details()`（5条件 / refs は読む側で取り直す）
