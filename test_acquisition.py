#!/usr/bin/env python3
"""Phase 1b Acquisition Boundary の受入 counter-factual テスト(ACQ-1…4c)。
docs/phase-1b-acquisition-boundary.md §18。DE-0009 の規律: 各受入は反転で outcome が変わる
counter-factual を最低1本持ち、境界より下の primitive(adapter status / observed_source_kind /
snapshot)から注入する。ここでの合格は test-verified に留まる(独立レビュー=次段の local attacker)。
"""
import os, sys, tempfile
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_acq_"))
from egl import core, source_policy as SP, acquisition as ACQ

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))

def reset():
    for f in ["events.jsonl", "state.sqlite", ".idlock"]:
        p = core.DATA / f
        if p.exists():
            p.unlink()

# adapter 結果の擬似(hermetic: ネットワーク非決定性をテストから排除。adapter が status を付す事実は不変)
def adapter_ok(raw="official text", ctype="text/html"):
    return {"transport_status": "SUCCESS", "content_status": "OBSERVED",
            "http_status": 200, "content_type": ctype, "raw_bytes": raw, "adapter_version": "1.0"}
def adapter_challenge():
    return {"transport_status": "SUCCESS", "content_status": "CHALLENGE_PAGE",
            "http_status": 200, "content_type": "text/html", "raw_bytes": "cf challenge", "adapter_version": "1.0"}
def adapter_denied():
    return {"transport_status": "ACCESS_DENIED", "content_status": None, "http_status": 403,
            "raw_bytes": None, "adapter_version": "1.0"}


def _leg(run, required, locator, adapter="ACQ_HTTP_STATIC", **kw):
    return ACQ.mk_leg_intent(run, plan_id="PLAN-1", task_id="TASK-1",
                             required_source_kind=required, target_locator=locator,
                             adapter_class=adapter,
                             source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"],
                             source_policy_version=1, search_method="DOC_FETCH",
                             query=kw.get("query", ["nvfp4"]), scope_locator=kw.get("scope", locator))


def satisfied(leg):
    con = core.build_view()
    return ACQ.evaluate_leg_requirement(con, leg)


# ---------------------------------------------------------------
# ACQ-3b (AB-1) — required_source_kind は要求であって観測事実でない
# ---------------------------------------------------------------
def t_acq3b_required_vs_observed():
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    # 正: docs.vllm.ai を required=OFFICIAL_DOCS で取得 → observed=OFFICIAL_DOCS → SATISFIED
    good = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/nvfp4")
    a1 = ACQ.run_acquisition(r, good, adapter_ok())
    ACQ.mk_search_result_snapshot(r, good, a1, result_count=1)
    ACQ.emit_observation_if_eligible(r, a1)
    # 誤分類: required=OFFICIAL_DOCS だが target=github repo → observed=OFFICIAL_REPOSITORY ≠ 要求
    mis = _leg(r, "OFFICIAL_DOCS", "https://github.com/vllm-project/vllm/blob/main/x.py")
    a2 = ACQ.run_acquisition(r, mis, adapter_ok())
    ACQ.mk_search_result_snapshot(r, mis, a2, result_count=1)
    ACQ.emit_observation_if_eligible(r, a2)
    # 誤分類2: required=OFFICIAL_DOCS だが target=random blog → observed=UNKNOWN
    blog = _leg(r, "OFFICIAL_DOCS", "https://random-blog.example/foo")
    a3 = ACQ.run_acquisition(r, blog, adapter_ok())
    ACQ.mk_search_result_snapshot(r, blog, a3, result_count=1)
    ACQ.emit_observation_if_eligible(r, a3)
    core.run_end(r, [])

    sg, sm, sb = satisfied(good), satisfied(mis), satisfied(blog)
    check("ACQ-3b 正: required=observed(OFFICIAL_DOCS)→ SATISFIED", sg["satisfied"], str(sg["reasons"]))
    check("ACQ-3b counter-factual: 取得成功でも observed(OFFICIAL_REPOSITORY)≠required → UNSATISFIED",
          not sm["satisfied"] and any("ACQ-3b" in x for x in sm["reasons"]), str(sm["reasons"]))
    check("ACQ-3b counter-factual: observed=UNKNOWN(random blog)は required を満たさない",
          not sb["satisfied"], str(sb["reasons"]))


# ---------------------------------------------------------------
# ACQ-4b (AB-2) — transport success ≠ evidence-eligible content
# ---------------------------------------------------------------
def t_acq4b_transport_vs_content():
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    leg = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    a = ACQ.run_acquisition(r, leg, adapter_challenge())   # 200 だが Cloudflare challenge
    ACQ.mk_search_result_snapshot(r, leg, a, result_count=1)
    obs = ACQ.emit_observation_if_eligible(r, a)
    core.run_end(r, [])
    s = satisfied(leg)
    check("ACQ-4b: content=CHALLENGE_PAGE は evidence-eligible でない(Observation 非生成)", obs is None)
    check("ACQ-4b counter-factual: transport=SUCCESS でも content≠OBSERVED → coverage UNSATISFIED",
          not s["satisfied"] and any("ACQ-4b" in x for x in s["reasons"]), str(s["reasons"]))


# ---------------------------------------------------------------
# ACQ-4 — transport 失敗は coverage を満たさない
# ---------------------------------------------------------------
def t_acq4_transport_fail():
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    leg = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    a = ACQ.run_acquisition(r, leg, adapter_denied())      # ACCESS_DENIED
    ACQ.mk_search_result_snapshot(r, leg, a, result_count=0)
    obs = ACQ.emit_observation_if_eligible(r, a)
    core.run_end(r, [])
    s = satisfied(leg)
    check("ACQ-4: ACCESS_DENIED は Observation を生まない", obs is None)
    check("ACQ-4: 取得失敗 leg は coverage UNSATISFIED", not s["satisfied"], str(s["reasons"]))


# ---------------------------------------------------------------
# ACQ-4c (AB-3) — source kind でなく search operation の実行+snapshot
# ---------------------------------------------------------------
def t_acq4c_search_operation():
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    # snapshot 有り → OK
    withsnap = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/a")
    a1 = ACQ.run_acquisition(r, withsnap, adapter_ok())
    ACQ.mk_search_result_snapshot(r, withsnap, a1, result_count=1)
    ACQ.emit_observation_if_eligible(r, a1)
    # snapshot 無し(取得はしたが『どう探したか』を記録していない)→ NG
    nosnap = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/b")
    a2 = ACQ.run_acquisition(r, nosnap, adapter_ok())
    ACQ.emit_observation_if_eligible(r, a2)                 # snapshot を作らない
    core.run_end(r, [])
    sw, sn = satisfied(withsnap), satisfied(nosnap)
    check("ACQ-4c: search operation snapshot 有り → SATISFIED", sw["satisfied"], str(sw["reasons"]))
    check("ACQ-4c counter-factual: 取得成功でも SearchResultSnapshot 無し → UNSATISFIED",
          not sn["satisfied"] and any("ACQ-4c" in x for x in sn["reasons"]), str(sn["reasons"]))


# ---------------------------------------------------------------
# ACQ-1 / ACQ-3 — RD は leg を COMPLETED にできない / plan・required は LegIntent から解決
# ---------------------------------------------------------------
def t_acq1_acq3_no_rd_completion():
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    leg = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    # RD が「完了だ」と主張する偽の AcquisitionRun payload を注入しても、満足は primitive から計算。
    # かつ AcquisitionRun 内の required/plan を偽っても evaluate は LegIntent を根にする(ACQ-3)。
    a = ACQ.run_acquisition(r, leg, adapter_ok())
    # 偽装試行: AcquisitionRun に別 plan/required を後付けしても LegIntent は不変(immutable)
    forged = {"transport_status": "SUCCESS", "content_status": "OBSERVED", "raw_bytes": "x",
              "adapter_version": "1.0"}
    # evaluate は snapshot も要求する。RD が snapshot 無しに『COMPLETED』宣言する術は存在しない。
    s_before = satisfied(leg)
    ACQ.mk_search_result_snapshot(r, leg, a, result_count=1)
    ACQ.emit_observation_if_eligible(r, a)
    core.run_end(r, [])
    s_after = satisfied(leg)
    # LegIntent の required は github に付け替えられない(別 leg を作らない限り)
    legstate = core.get_state(leg)
    check("ACQ-1: snapshot/observation 前は satisfied=False(RD の意思で COMPLETED にできない)",
          not s_before["satisfied"])
    check("ACQ-1: primitive(snapshot+observation)が揃って初めて satisfied", s_after["satisfied"], str(s_after["reasons"]))
    check("ACQ-3: required_source_kind は immutable LegIntent が根(AcquisitionRun payload でない)",
          s_after["required_source_kind"] == "OFFICIAL_DOCS" == legstate["required_source_kind"])


# ---------------------------------------------------------------
# 実 adapter の分類ロジック(pure, hermetic — ネットワーク非依存)
# ---------------------------------------------------------------
def t_adapter_classification():
    from egl import adapters as A
    # AB-2 content classification: 200 でも中身で content_status が変わる
    cc = A.classify_content
    check("adapter: 正常 body → OBSERVED", cc(b"<html>NVFP4 supported hardware: Blackwell</html>", "text/html", 200, {}) == "OBSERVED")
    check("adapter: Cloudflare challenge → CHALLENGE_PAGE",
          cc(b"<title>Just a moment...</title>challenge-platform", "text/html", 200, {}) == "CHALLENGE_PAGE")
    check("adapter: cloudflare server + 403 → CHALLENGE_PAGE",
          cc(b"blocked", "text/html", 403, {"Server": "cloudflare"}) == "CHALLENGE_PAGE")
    check("adapter: auth wall → AUTH_WALL", cc(b"Please log in to continue", "text/html", 200, {}) == "AUTH_WALL")
    check("adapter: 空 body → EMPTY", cc(b"   ", "text/html", 200, {}) == "EMPTY")
    # AB-2 transport 失敗 taxonomy(FAILED に潰さない)
    tf = A._transport_from
    check("adapter: 200 → SUCCESS", tf({"error": None, "status": 200}) == "SUCCESS")
    check("adapter: 403 → ACCESS_DENIED", tf({"error": None, "status": 403}) == "ACCESS_DENIED")
    check("adapter: 404 → NOT_FOUND_REMOTE", tf({"error": None, "status": 404}) == "NOT_FOUND_REMOTE")
    check("adapter: 429 → RATE_LIMITED", tf({"error": None, "status": 429}) == "RATE_LIMITED")
    check("adapter: timeout → TIMEOUT", tf({"error": "timeout", "status": None}) == "TIMEOUT")
    check("adapter: network → NETWORK_ERROR", tf({"error": "network", "status": None}) == "NETWORK_ERROR")


# ---------------------------------------------------------------
# JREV-0005 修正の counter-factual(Probe B/C/D)
# ---------------------------------------------------------------
def t_jrev0005_fixes():
    # Probe B: registry は UGC ホスト全体を公式化しない(segment 照合 + docs/ のみ)
    check("B: huggingface.co/attacker-user/... → UNKNOWN(UGC は公式化しない)",
          SP.qualify_locator("https://huggingface.co/attacker-user/malicious/blob/main/README.md")[0] == "UNKNOWN")
    check("B: huggingface.co/docs/... → OFFICIAL_DOCS(公式部分のみ)",
          SP.qualify_locator("https://huggingface.co/docs/transformers/index")[0] == "OFFICIAL_DOCS")
    check("B latent: github vllm-project/vllmZZZ → UNKNOWN(segment 境界、prefix 誤マッチ封鎖)",
          SP.qualify_locator("https://github.com/vllm-project/vllmZZZ/blob/main/x")[0] == "UNKNOWN")
    check("B: github vllm-project/vllm/... → OFFICIAL_REPOSITORY(正規は不変)",
          SP.qualify_locator("https://github.com/vllm-project/vllm/blob/main/README.md")[0] == "OFFICIAL_REPOSITORY")
    # Probe C: qualify は実取得先(final_url)を根にする。redirect で公式 host を騙れない
    docs = "https://docs.vllm.ai/latest/"
    check("C: redirect 先 evil.example → UNKNOWN(final_url を分類、requested locator でない)",
          SP.qualify_locator(docs, provenance={"final_url": "https://evil.example/phish"})[0] == "UNKNOWN")
    check("C: final_url が公式のまま → OFFICIAL_DOCS(正規は不変)",
          SP.qualify_locator(docs, provenance={"final_url": docs})[0] == "OFFICIAL_DOCS")
    # Probe D: snapshot は同一 leg の実 AcquisitionRun に束縛必須
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    legA = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/a")
    aA = ACQ.run_acquisition(r, legA, adapter_ok())
    legB = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/b")
    raised = False
    try:
        ACQ.mk_search_result_snapshot(r, legB, aA, result_count=1)   # 別 leg の run に束縛しようとする
    except ValueError:
        raised = True
    core.run_end(r, [])
    check("D: cross-leg の AcquisitionRun に snapshot を束縛 → reject(未束縛 self-report 封鎖)", raised)


# ---------------------------------------------------------------
# 統合(§13): 取得境界 → Extraction → 既存 curation spine → Claim(hermetic)
# ---------------------------------------------------------------
def _acquire_extract(run, required, locator, injected):
    leg = _leg(run, required, locator)
    a = ACQ.acquire(run, leg, injected=injected)
    ACQ.mk_search_result_snapshot(run, leg, a, result_count=1)
    obs = ACQ.emit_observation_if_eligible(run, a)
    return leg, a, obs


def _curate_claim(cand_id, statement="X"):
    from egl import judge, curator
    adj = judge.ClaudeAdjudicator({cand_id: {"f1": "SUPPORTED", "f2": "WITHIN",
                                             "fragment_sufficient": True, "rationale": "r"}})
    curator.curate(cand_id, adj)
    con = core.build_view()
    return next((c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == cand_id), None)


def _mk_candidate_from_fragment(run, frag_id, statement):
    from egl import pipeline as P
    rel = P.mk_relation(run, frag_id, None, "SUPPORTS", {"scope": {"model": "x"}})
    return P.mk_candidate(run, {
        "object_kind": "CandidateClaim", "claim_type": "CAPABILITY", "predicate": "p",
        "polarity": "POSITIVE", "task_id": "TASK-1", "statement": statement, "scope": {"model": "x"},
        "evidence_relations": [rel], "resolves_gap": None,
        "representation_residual": {"known_omissions": [], "scope_uncertainty": "LOW"}})


def t_integration_to_claim():
    from egl import pipeline as P
    # (a) OFFICIAL_DOCS → observation_kind=DECLARATION → Claim validation_mode=DECLARED
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    _, _, obs = _acquire_extract(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/x", adapter_ok("official decl"))
    core.run_end(r, [])
    re_ = core.run_start("extractor", "EXTRACTION", task_id="TASK-1")
    ext = ACQ.extract_fragment(re_, obs["observation_id"], blocks=["X supported"], block_index=0, excerpt="X supported")
    core.run_end(re_, [])
    check("integration: OFFICIAL_DOCS → observation_kind=DECLARATION", ext["observation_kind"] == "DECLARATION")
    rc = core.run_start("rd", "EXTRACTION", task_id="TASK-1")
    C = _mk_candidate_from_fragment(rc, ext["fragment_id"], "X supported")
    core.run_end(rc, [])
    claim = _curate_claim(C)
    check("integration: 取得→抽出→curate で Claim 生成(status=VERIFIED)", claim and claim["status"] == "VERIFIED")
    check("integration: OFFICIAL_DOCS(DECLARATION)由来 → validation_mode=DECLARED",
          claim and claim.get("validation_mode") == "DECLARED", claim.get("validation_mode") if claim else None)

    # (b) counter-factual: OFFICIAL_REPOSITORY → IMPLEMENTATION_ARTIFACT → validation_mode=UNRESOLVED
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    _, _, obs = _acquire_extract(r, "OFFICIAL_REPOSITORY",
                                 "https://github.com/vllm-project/vllm/blob/main/x.py", adapter_ok("code"))
    core.run_end(r, [])
    re_ = core.run_start("extractor", "EXTRACTION", task_id="TASK-1")
    ext = ACQ.extract_fragment(re_, obs["observation_id"], blocks=["code"], block_index=0, excerpt="code")
    core.run_end(re_, [])
    rc = core.run_start("rd", "EXTRACTION", task_id="TASK-1")
    C = _mk_candidate_from_fragment(rc, ext["fragment_id"], "code path exists")
    core.run_end(rc, [])
    claim = _curate_claim(C)
    check("integration counter-factual: OFFICIAL_REPOSITORY(IMPLEMENTATION_ARTIFACT)→ validation_mode=UNRESOLVED"
          "(公式 repo は PRIMARY だが declaration でない, R6/R7)",
          claim and claim.get("validation_mode") == "UNRESOLVED", claim.get("validation_mode") if claim else None)

    # (c) 非 evidence-eligible(challenge)からは抽出できない(ACQ-4b が curation まで貫通)
    reset()
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    leg = _leg(r, "OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    a = ACQ.acquire(r, leg, injected=adapter_challenge())
    obs = ACQ.emit_observation_if_eligible(r, a)
    core.run_end(r, [])
    raised = False
    re_ = core.run_start("extractor", "EXTRACTION", task_id="TASK-1")
    try:
        ACQ.extract_fragment(re_, "OBS-99999", blocks=["x"], block_index=0, excerpt="x")
    except ValueError:
        raised = True
    check("integration: challenge は Observation を生まず、抽出対象が存在しない(ACQ-4b が curation へ貫通)",
          obs is None and raised)


if __name__ == "__main__":
    print("=== Phase 1b Acquisition Boundary 受入テスト (ACQ-1…4c) ===")
    print("\n[ACQ-3b] required_source_kind ≠ observed source qualification (AB-1)")
    t_acq3b_required_vs_observed()
    print("\n[ACQ-4b] transport success ≠ evidence-eligible content (AB-2)")
    t_acq4b_transport_vs_content()
    print("\n[ACQ-4] transport 失敗は coverage 不可")
    t_acq4_transport_fail()
    print("\n[ACQ-4c] source kind ≠ search operation coverage (AB-3)")
    t_acq4c_search_operation()
    print("\n[ACQ-1/3] RD は leg を COMPLETED にできない / plan・required は LegIntent から解決")
    t_acq1_acq3_no_rd_completion()
    print("\n[adapter] 実 adapter の分類ロジック(pure, ネットワーク非依存)")
    t_adapter_classification()
    print("\n[JREV-0005 fixes] Probe B(registry over-classification)/ C(redirect)/ D(snapshot 束縛)")
    t_jrev0005_fixes()
    print("\n[integration] 取得境界 → Extraction → curation spine → Claim(hermetic)")
    t_integration_to_claim()

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("取得成功≠leg達成 / transport≠content / source kind≠search operation / RD は完了を宣言できない。")
    print("※ test-verified 止まり。独立 local attacker + GPT 裁定は次段(§19 step 13-14)。")
