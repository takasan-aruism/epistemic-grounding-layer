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
