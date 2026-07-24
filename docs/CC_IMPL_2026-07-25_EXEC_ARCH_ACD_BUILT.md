# 実装担当 → 設計/監査担当: EXEC_ARCH A/C/D 統合 s-stage（BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-25
- 対応: `CC_DESIGN_2026-07-25_EXEC_ARCH_ACD_HANDOFF.md`
- repo=egl。決定論・LLM 不使用・:8005/GPU 不使用。Stage B テンプレ準拠。

## 成果物（working tree・未commit）

- `egl/structure/s_exec_arch_acd.py`（単一 s-stage・3 jsonl 生成・統一 `--check`）
- `ENTRYPOINTS_EXT.jsonl`（A・13件）/ `READ_PATHS.jsonl`（C・14行）/ `STATE_MACHINES.jsonl`（D・52 symbol）

## 検証（Stage B と同水準）

- **本物の乖離を1回以上検出（§5 完了条件）**: D で **alias 矛盾 2件**（`CREATED`=dw/parallel_router、`CLOSED`=ds/rri＝同一 state symbol が別 machine で使用）。
- **常設ゲート load-bearing 実測**: entrypoint 1行除去 → `--check` **RED**（REGEN_MISMATCH）／復元で GREEN。alias 注入プローブ（§4-5）で検出力実証。
- **byte一致再生成**・**記録 symbol の実在検査**（A/D の source_file 実在）GREEN。
- **新状態語彙ゼロ**: state symbol は既存 edge/ladder 語彙へ写像 or `UNRESOLVED_NO_VOCAB_MAPPING`（曖昧化しない）。

## 各軸

- **A（13件）**: SHELL 6 / SYSTEMD 3 / VLLM_ENDPOINT 2 / TMUX 1 / CRON 1。status は edge 語彙へ（systemd/sh の実行有効性は静的不可 → `WIRED_EXECUTION_UNRESOLVED`／tmux・cron は runtime → `UNRESOLVED_DYNAMIC_LAUNCH`）。
- **D（52 symbol / 7 machine）**: rri request_thread・dw workcell・ds phase1・twoder（parallel_router/stale_packet_gate/failure_classifier）ほか。

## ★ 正直な flag（silently 合わせず裁定を仰ぐ・2b と同規律）

1. **D の語彙写像は 46/52 が `UNRESOLVED_NO_VOCAB`**: FSM の状態（SOFT/NARROWING/CREATED 等）は edge/ladder 語彙（LIVE/wired/proven＝辺・追跡の概念）に**大半が写像しない**。規律どおり新語彙を作らず UNRESOLVED にしたが、**「state 機械を edge/ladder に写像」という前提自体が少数しか適合しない**。写像先を別途定義するか、D は「別名矛盾検出」に絞るか裁定候補。
2. **C の `required_by_design` は決定論出典が無い**: 段ごとの「設計上読むべき資料」の機械可読な正本が存在せず、C2 規律に従い全行 `UNRESOLVED_NO_DESIGN_MANIFEST`。`actually_loaded`（AST の open）と gate 被覆は出したが、**CONTEXT_GAP 判定には design manifest 源が要る**（spec §2 の前提欠落）。
3. **CONTRADICTIONS.jsonl の sole-writer 抵触**: spec §3 は alias 矛盾を CONTRADICTIONS.jsonl へ追記と指示するが、同 ledger の **sole writer は `s6_contradictions.py`（DE-0491）**。手追記せず、矛盾は D 生成物内＋本 signal に別掲。**s6 が STATE_MACHINES.jsonl を読んで alias 矛盾を出す統合**を推奨（LLM Invocation Map の s2_extract 矛盾と同じ扱い）。

## ハンドオフ

- 次: **CC 独立再監査（byte一致 + 陰性対照 RED 実測 + 新語彙ゼロ + NO は被覆下）→ CONSISTENT → commit=Taka → DE 起票**。
- 上記 flag（D 写像前提 / C design-manifest 源 / CONTRADICTIONS sole-writer）の裁定があれば精緻化します。過剰主張より正直な UNRESOLVED を優先しました。
