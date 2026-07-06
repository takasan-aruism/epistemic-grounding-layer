# Decision Packet — GPU Co-Serve Conflict

Task: System-Level Operational Decision(Taka directive v0.1）。日: 2026-07-07。
形成: RRI=Qwen3.6(currently served, seed0)／ measurement plan=Qwen3.6(seed1)／ design audit=Qwen3.6(seed207)。
Claude(orchestrator)の事前 preference は封緘（CLAUDE_PRIOR_PREFERENCE_SEALED.json, sha256 758650b7…）で system 形成に非注入。
**measurement 未実行・operating policy 未実装**（§0/§16.13）。

---

## §6 EGL evidence / gap packet（DECLARED / OBSERVED / MEASURED / INFERENCE 分離）
- **DECLARED / SPECIFIED**: Coder-Next = 80B総/3B active, NVFP4 ≈46GB（script comment / model card）。intended tp=2。
- **OBSERVED（現状）**: qwen36_vllm が 8005 で稼働、両 GPU に各 ~30.5GB（**gpu-memory-utilization 0.92 の *予約* 値**であり必ずしも実 weight footprint でない）。Coder-Next dir 45GB on disk。8006 空き。両 serve script 実在。
- **MEASURED（local）**: **無し**。swap / co-serve / latency / RAM peak / failure rate はいずれも未計測。
- **INFERENCE**: co-serve 不可は **declared から推論**（実測でない）。現 61GB 使用は 0.92 util の予約で、実 weight は不明。
- **preserved gaps**: 上記 §5 の measurement_axes 全て NOT_MEASURED。
- **failure patterns**: IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION（assertion→measured fact / server-ready→task-ready / one startup→policy を禁止）。

---

## Decision Packet（§13 short format）

**OBSERVED PROBLEM**
Qwen3.6 と Qwen3-Coder-Next が現構成で co-serve 不可と *される*。DW の標準 role flow は GENERATE=Coder-Next /
AUDIT=Qwen3.6 を要するが、両者を同時 serve できない（とされる）ため operating mode 未定。

**WHY THE CURRENT SYSTEM CANNOT CHOOSE YET**
system(RRI) が自力で blockage を **measurement** と分類。決定は local 運用挙動（実 VRAM / co-serve 可否 / swap
latency / repeated-swap 安定性）に依存し、これらは docs で解けない。しかも **co-serve 不可自体が declared assertion で
未実測**。local 運用 evidence がゼロなので、今 operating mode を選べない（選べば premature preference）。

**OPTIONS THAT REMAIN**（system は選ばない）
co-serve / sequential swap / single-model fallback — いずれも measurement 次第。

**EVIDENCE THAT CHANGES THE CHOICE**
1. 実 Coder-Next VRAM / **co-serve feasibility**（もし実際に co-serve 可能なら conflict 自体が消え swap policy 不要）。
2. swap latency + repeated-swap 安定性（sequential swap なら、rework 頻度に対しコスト許容か）。
3. server-ready / first-real-request latency（cold-start penalty）。

**RECOMMENDED NEXT ACTION**
audited-clean な最小 measurement slice を実行。**最初に co-serve feasibility / 実 VRAM**（決定を最も flip し得る）。
⚠ これは disruptive: 稼働中 Qwen3.6(8005, 46h)を停止して Coder-Next の load / co-serve を試す必要がある。

**NEW TRUST ROOT / NON-GUARANTEE**
operating-mode policy は未採用。co-serve「不可」は未検証。measurement は single-machine / single-config。
single-Qwen auditor の blind spot。

**REQUIRED HUMAN DECISION**
disruptive な measurement slice の実行を承認するか（= 稼働 Qwen3.6 を一旦止めて Coder-Next / co-serve を計測）。
※ これは「解決策を人に設計させる」のではなく、system が形成した decision process の次の一手（disruptive 実行）の go/no-go。

---

## §10 Human intervention log
- **H2/H3/H4 = 0**（本 experiment 内）: system が blocked decision 特定 / measurement 分類 / spec-vs-local 分離 /
  co-serve 未検証の指摘 / measurement plan 形成 を、人の design 介入なしで実施。Claude preference は封緘・非注入。
- before-state（記録・隠さない）: 前ターンで Claude が「a/b/c から選んで + Claude-auditor 推奨」と **人に選ばせよう** とした
  = これが本 directive が是正した H4。今回は system が代替した。
- H0（将来）: model stop/start の物理承認は design content を足さなければ H0。

## §11 model identity
RRI/measurement-plan/audit の actor = Qwen3.6-35B-A3B @ localhost:8005（container qwen36_vllm, vllm nightly, NVFP4, tp2）。
Coder-Next は未起動 = role 未 exercised（candidate のまま）。Claude = orchestrator（形成非介入）。

## §14 判定
**strong-leaning**: H3=0 / H4=0 で、system が「measurement が要るか」を自力判定し、operating mode を premature に
選ばず、しかも **co-serve 不可の前提自体を疑って検証対象にした**。返したのは大きな設計問題でなく小さな決定
（measurement 実行の go）。一般化しない（1 event / single Qwen3.6 / measurement 未実行）。

---

## MEASURED RESOLUTION (approved slice executed 2026-07-07)
co-serve = **IMPOSSIBLE (MEASURED)**: Coder-Next 22.22 GiB/GPU + Qwen3.6 ~14.3 GiB/GPU = 36.5 > 31.8 GiB/GPU（KV 前に超過）。
swap latency 171s(fwd)/186s(rev)、GPU release 5s。Coder-Next 起動 SUCCESS・生成 coherent（smoke、role 未validated）。
still-unmeasured: 実 rework/swap 頻度、repeated-swap 安定性。

## §16.10 DW operating-mode candidates（fresh subagent, sealed 未見）
- **A** sequential swap per item（intended G36 auditor 維持、cost は rework 頻度に比例）
- **B** batched phase swap（N 件 generate→1 swap→audit、swap を N で amortize、latency-to-first-audit 増）
- **C** Coder-Next 常駐 + different-class auditor（human/upper-tier or 小 model or off-box G36。hot loop に swap なし。intended G36 audit 品質を犠牲、substitute 未証明）
- **D** commit を defer し bounded instrumented trial（A を小 real task set で）で **swap 頻度 + 安定性を測る** → low→A / high→B、C は fallback
- **MANAGER_NOTE**: 現 evidence では production mode を確定できない。A vs B は swap 頻度で決まり、それは未測（assume 禁止）。D 推奨。

## §16.11 independent audit + §upper-review disposition
audit(Qwen seed311, manager_note_sound=True)の findings を Manager が disposition:
- premature_preference(C) → **PARTIAL**: C は fallback として caveat 済。C を default にしない、を強化。
- assumed_switch_cost(A/B) → **REJECTED**: subagent は rework 頻度を DEPENDENT_UNKNOWN と明示し D で測ると した。cost 構造は論理依存で assumed value でない。
- non_decision_changing_metrics → **PARTIAL**: D の trial が decision-changing 変数(swaps/item)を測ることを担保。
- procrastination_deferral(D) → **PARTIAL(ACCEPT caution)**: D は evidence-blocked(swap 頻度が A/B を分ける・assume 禁止)だが **bounded/instrumented** であること（subagent が既に規定）。
- unmeasured_fact_viability(C) → **ACCEPTED**: C は substitute-auditor 品質が未測ゆえ fallback-only、別途 effectiveness check 前提。

## §16.12 FINAL Decision Packet
**OBSERVED PROBLEM**: generator(Coder-Next)と auditor(G36=Qwen3.6)が co-serve 不可（**measured**）で、DW operating mode 未定。
**WHY CANNOT CHOOSE YET**: A/B を分ける **swap 頻度が未測**（assume 禁止）。C は substitute-auditor 品質が未測。同一 model self-audit は独立性違反で除外。
**OPTIONS THAT REMAIN**: A / B（swap 頻度依存）、C（fallback, 効果未証明）。co-serve は除外（measured）。
**EVIDENCE THAT CHANGES THE CHOICE**: 実 rework/swap 頻度（low→A / high→B）+ repeated-swap 安定性。
**RECOMMENDED NEXT ACTION**: **D** — 最初の RRI-through-DW tasks を A（sequential swap）で走らせつつ **swaps/item と安定性を計測**（= 既定の step4 RRI 実装が swap-frequency trial を兼ねる）。その measured 頻度で A/B を自動確定、C は fallback。
**NEW TRUST ROOT / NON-GUARANTEE**: production policy 未採用。swap 頻度/安定性/substitute-auditor 品質は未測。DW effectiveness NOT_PROVEN。
**REQUIRED HUMAN DECISION**: 最初の RRI-through-DW tasks を **A モード(sequential swap)の instrumented trial** として走らせてよいか（swap 頻度を実測し A/B を確定）。

## §post-hoc — Claude 封緘 preference との比較（hash 一致で開封）
Claude の事前 preference = **「(b) Claude-as-auditor」= 実質 Candidate C**。
- system は C を **独立に導出**したが、**推奨しなかった**——C の cost(substitute audit 品質 未証明)を指摘し **fallback** に留め、**D(まず swap 頻度を測る)** を推奨。
- → **私(Claude)の premature preference(C)は、まさに本 experiment が是正する H4。** 規律ある system は「まだ選べない、swap 頻度を測れ」と、より正しい答えを出した。

## §measurement of the experiment（§14）
- **H2/H3/H4 = 0**（system が blocked decision 特定 / measurement 分類 / co-serve 前提の検証 / measurement plan / operating-mode candidates / 「まだ選べない・測れ」の結論 を、人の design 介入なしで形成。Claude preference 封緘・非注入）。
- **§14 strong 条件を満たす**: system が「local measurement が要るか」を自力で 2 段（co-serve 実測 → swap 頻度 要測）判定し、operating mode を premature に選ばなかった。
- before-state: 前ターン Claude の a/b/c + C 推奨 = H4（記録・隠さない）。experiment がこれを是正。
- 一般化しない（1 event / single Qwen3.6 / 1 subagent / swap 頻度 未測）。

---

## MEASURED — A-mode instrumented trial (RRI validate_iec, executed 2026-07-07)
2 items 実行(run1 + patched run2)。両 item とも **4 swaps**（各 1 rework）。
- **swap latency ≈ 174.5s/swap（~2.9 min）**、8 swaps 全成功（**failures 0** = repeated-swap 安定）。
- **swaps/item ≈ 4**（rework 起因）。→ mode A の swap overhead ≈ 4×174.5 ≈ **~11.6 min/item**（1 rework 時）。
- rework の駆動源: run1=auditor over-flag、run2=coder 初回 error → **F5 gate**（auditor findings=[] でも failing test で rework）。
- validate_iec は run2 で **DW gate COMPLETE**（Coder-Next 生成 + Qwen3.6 独立監査 + F5 + upper-review probe）→ RRI に commit。
- **A vs B の含意（narrow, N=2）**: 両 item が 1 rework=4 swaps ゆえ mode A は ~12 min/item の swap 支配。rework が続くなら
  **B（batched）で swap を amortize** が効く方向。ただし N=2、rework 頻度は本格運用で再測が要る。commit は Taka 判断。
