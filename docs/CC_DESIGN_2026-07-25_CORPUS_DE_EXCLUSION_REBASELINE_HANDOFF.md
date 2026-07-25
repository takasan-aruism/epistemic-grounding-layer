# 設計/監査 → 実装: DE台帳を埋め込み corpus から除外 + 2b 再baseline（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / repo=egl / 決定論・LLM不使用・:8005/GPU不使用・CPU e5 pin `614241f6`
- 正本: `CC_MGR_2026-07-25_2BR3_FLAG2_CORPUS_ADJRESULT.md`（Flag2 裁定: DE除外＝根治 / 即時 re-baseline 承認）+ 本 handoff
- 位置づけ: ★3 本線の corpus 整合。Flag2 解決＝2b-r3 commit の前提。

## 0. 絶対規律（gaming 防止・最重要）
- **measure-first**: DE除外後の **request-only corpus（rri_records のみ）** で「その他優勢／弱い軸」が出ても、それが request 領域の正直な現状。
- **DE台帳を再投入して軸を無理に出すことは禁止＝捏造**。候補が減る/消えるのは正しい結果。
- 決定論・sole-writer 分離・捏造ゼロ・commit=Taka。

## 1. DE 除外（2本のみ・最小）
埋め込み/mining corpus から `DESIGN_EVIDENCE_LEDGER.jsonl` を外す。**corpus = rri_records のみ**（REQUEST=content.raw / INTENT=content.resolved、実在698件）。
- `structure/s_embed_axes.py`: `DE_LEDGER` ループ（line 43 付近 `for line in open(DE_LEDGER…)`）を除去。`DE_LEDGER` 定数も未使用なら削除。
- `structure/s_mine_accounts.py`: 同様に `DE_LEDGER` ループ（line 47 付近）を除去。
- **他は触らない**。s_account_axes は embed 出力経由ゆえ直接改修不要（再baseline で追随）。

## 2. 再baseline（決定論・DE除外後 corpus で一気に）
現 corpus（rri_records のみ）に対し 2b パイプラインを再生成:
1. `s_embed_axes.py`（2b-r1）→ EMBED_AXES_CANDIDATE/STABILITY 更新
2. `s_account_axes.py`（2b-r2）→ ACCOUNT_AXES_v1 / ACCOUNT_MEMBERSHIP 更新
3. `s_rthread_2br3.py`（2b-r3）→ FREEZE_CANDIDATE 更新（新 base の その他 に対して）

## 3. ゲート GREEN 化
- `s_embed_axes.py --check` / `s_account_axes.py --check` を **byte一致 GREEN**（drift 解消）。
- `s_llm_invocations.py`: 本 session の新 script（s_task_contract / s_rthread_2br3）が MENTION/CALL を追加していれば **regen して登録** → `--check` GREEN。
- `s_task_contract.py --check` / `s_rthread_2br3.py --check` GREEN 維持（no-auto-freeze・I1 不変）。

## 4. 報告（BUILT に正直に）
- **新候補集合**を報告: 予測＝`CAND-98f1a155`(DEブロブ)は**自然消滅**、`CAND-29580ee0`(real topic)は**残るか要再確認**。QUALIFIED 数・各 silhouette/sub/diversity/kind_purity。
- 除外前後の record 数（corpus 906/916 → 698 系）と membership 数の変化。
- 候補ゼロ（NO_CANDIDATE）でも正当＝request 領域の正直な現状（DE再投入で埋めない）。

## 5. 受入（設計が独立再検証）
- 私が fresh 再実行して 3 --check（embed/account/llm_invocations）が byte一致 GREEN。
- corpus が rri_records のみ（DE台帳非参照）をコードで確認できる。
- 2b-r3 候補が新 base 上で決定論再現。98f1a155 消滅・退化除外不変。
- **絶対閾値定数ゼロ**不変・no-auto-freeze 不変・I1 保存不変。

## 6. 完了後（設計側の後続＝私がやる）
- 設計(私)が `REQUIRED_INPUTS.jsonl` の **s_embed_axes / s_mine_accounts の required_inputs から `DESIGN_EVIDENCE_LEDGER.jsonl` を除去**（除外で実読から消えるため。放置すると C が偽 MISSING）。← これは Task Contract の C-gate が drift を検出する good example。
- その後 commit=Taka（**除外＋再baseline＋2b-r3＋contract更新＋LLM_INVOCATIONS regen を1コミット群**）→ DE 起票。
- 想定と実測がズレたら silently 合わせず BUILT に正直記録。過剰主張より正直な NO_CANDIDATE。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。measure-first 厳守＝DE再投入禁止。★3 本線・止めない。*
