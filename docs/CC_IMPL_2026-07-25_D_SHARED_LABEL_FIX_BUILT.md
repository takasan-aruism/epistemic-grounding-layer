# 実装(IMPL) → 監査/設計(AUDIT/DESIGN): build_D の label を SHARED_STATE に（BUILT・小）

- 宛: AUDIT（→ DESIGN）
- 発: 実装(IMPL) / 2026-07-25 / repo=egl / 決定論
- 対応: `CC_DESIGN_2026-07-25_D_SHARED_LABEL_FIX_HANDOFF.md`（裁定=(b-minimal)・意味論是正のみ・挙動不変）

## 成果物（working tree・未commit）
- `structure/s_task_contract.py`（**唯一の変更ファイル**。`build_D` の label 改名 + §3-5 gate 期待ラベル更新 + docstring/print 文言）
- **`STATE_MACHINES.jsonl` は byte 不変**（重要・事実確認済）: shared record は build_D の返り値＋`--check`/print でのみ surface され、**どの出力ファイルにも永続化されていない**（元の D 設計どおり=CONTRADICTIONS.jsonl の sole-writer は s6 ゆえ D は書かない）。ゆえに label 改名は s_task_contract.py のコード＋出力文言のみに影響し、生成物 jsonl は変わらない。
- 補足（scope 外・情報提示）: shared_state は現状 ephemeral（--check 出力のみ）。永続台帳化するかは別途 DESIGN 判断（handoff は「挙動不変」ゆえ本件では足さない）。

## 実装（最小・挙動不変）
1. `build_D` の共有 record: `type: CROSS_MACHINE_STATE_CONFLICT` → **`CROSS_MACHINE_SHARED_STATE`**。key `owners` → `sharing_machines`（可読化）。意味=「複数 machine が **authored された同一 canonical** を共有＝合意・正当」。surface 挙動は不変。
2. `--check` §3-5 D 検出力: CREATED→同 canonical 注入プローブの期待を **`type == "CROSS_MACHINE_SHARED_STATE"` まで assert**（ラベルを load-bearing 化）。検出力は不変。
3. docstring/print の「衝突/conflict」→「共有(合意)/shared」に是正。

## やらなかったこと（handoff スコープ厳守）
- **AMBIGUITY カテゴリは追加せず**（裁定B で distinct 確定済みの CREATED を誤再浮上させないため）。CREATED は `UNRESOLVED_NO_CANONICAL` のまま surface しない。
- 埋め込み・軸・membership・他ステージは不触。

## 検証（実測）
- `s_task_contract.py --check` **GREEN**（byte一致・auto-collapse/C/D 陰性対照 load-bearing）。
- **STATE_THREAD_CLOSED が `CROSS_MACHINE_SHARED_STATE` で surface**（sharing_machines=[ds/ds/phase1.py, rri/rri/request_thread.py]）＝(C) 裁定の実点灯を維持。
- **CREATED は UNRESOLVED_NO_CANONICAL のまま**（2件・裁定B distinct 維持・surface しない）。
- D 検出力の陰性対照が SHARED_STATE ラベルで load-bearing（ラベルを戻すと RED）。
- 全 7 gate（task_contract/embed/account/rthread_2br3/exec_arch_acd/llm_invocations/mine）GREEN。

## 併せて確認: corpus DE除外カスケードの C-drift が end-to-end で解消
- 私の DE loop 除去 → C が s_embed_axes/s_mine_accounts の `DESIGN_EVIDENCE_LEDGER` を **MISSING 検出** → **CC-α が §6 通り REQUIRED_INPUTS から DE台帳を除去**（now `["rri_records.jsonl"]`）→ **C MISSING ゼロ（30 OK / 7 UNRESOLVED）**。Task Contract の C-gate が実読 drift を検出し authoring が追随した good example。

## ハンドオフ
- 次: 設計再監査（byte一致 / SHARED_STATE surface / CREATED UNRESOLVED 維持 / D 検出力 load-bearing）→ CONSISTENT → commit=Taka → 単独 DE（軽微）。
- 本セッションの未commit 群（DE除外+再baseline+membership相対化+2b-r3+contract+LLM_INVOCATIONS+本 label 修正）は commit=Taka の1コミット群候補。

---
*実装(IMPL)。意味論の是正のみ・挙動不変。★3 本線は止めていません。*
