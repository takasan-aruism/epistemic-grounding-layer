#!/usr/bin/env python3
"""Challenge Set C (DE-0009 / CB-7) — build-out G1 enforce 群の構造試験。

DE-0009 の2故障型を独立に張る:
  (1) counter-factual gate test = gate 出力を反転して outcome が変わることを要求
      → 反転で不変なら dead gate(H3/H4『計算して捨てる』型を検出)
  (2) 注入層原則 = 試験入力を「試験対象の境界より下の層」から注入
      → SearchConclusion.status(driver 引数)でなく leg event を注入
      → wrong-source 型(H1『誤 source を信用』型)を検出

この試験があれば、著者が過去に「SC-2 が構造ブロック」と過大報告したのを
防げた(= DE-0005 の再発防止)。合格 = 各 enforce が driver 正直性に依存しない証拠。
"""
import os, sys, tempfile
# AB-0005: canonical SoR(data/)を汚さないよう、egl を import する *前* に
# 隔離 data dir へ向ける。以降 core.DATA/EVENTS/... は全てこの temp を指す。
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_test_"))
from egl import core, gates, curator, judge, pipeline as P

RESULTS = []


def reset():
    for f in ["events.jsonl", "state.sqlite", "tt.sqlite"]:
        p = core.DATA / f
        if p.exists():
            p.unlink()


def check(name, passed, detail=""):
    RESULTS.append((name, passed, detail))
    mark = "PASS ✅" if passed else "FAIL ❌"
    print(f"  [{mark}] {name}" + (f"  — {detail}" if detail else ""))


# ---------- fixtures ----------
def evidence_fragment(run, source_class="PRIMARY"):
    s = P.mk_source(run, "src", source_class, "http://x")
    n = P.mk_observation(run, s, "Heading", ["b0", "b1", "b2"])
    return P.mk_fragment(run, n, 1, "b1")


def positive_candidate(run, scope, claim_type="CAPABILITY", predicate="runs_on",
                       resolves_gap=None, grounds_claims=None, scope_echo=None):
    f = evidence_fragment(run)
    rel = P.mk_relation(run, f, None, "SUPPORTS", {})   # DE-0006: candidate 前に to=None で先行
    payload = {"object_kind": "CandidateClaim", "claim_type": claim_type,
               "predicate": predicate, "polarity": "POSITIVE", "task_id": "T",
               "statement": "s", "scope": scope, "evidence_relations": [rel],
               "resolves_gap": resolves_gap, "validation_mode": "DECLARED",
               "representation_residual": {"known_omissions": [], "scope_uncertainty": "LOW"}}
    if grounds_claims:
        payload["grounds_claims"] = grounds_claims
    if scope_echo:
        payload["scope_echo"] = scope_echo
    return P.mk_candidate(run, payload)   # AB-0007: to_id を結線


def adj_for(cid, f1="SUPPORTED", f2="WITHIN", frag=True):
    return judge.ClaudeAdjudicator({cid: {"f1": f1, "f2": f2, "fragment_sufficient": frag,
                                          "rationale": "test"}})


def absence_candidate(run, plan, scon, gap=None):
    return P.mk_candidate(run, {
        "object_kind": "CandidateClaim", "claim_type": "ABSENCE", "predicate": "documents",
        "polarity": "ABSENCE", "task_id": "T", "statement": "not found in coverage",
        "scope": {"subject": "x", "coverage_profile": "COV-TECH-STANDARD"},
        "evidence_relations": [], "resolves_gap": gap, "search_conclusion": scon})


def claim_of(res):
    if not res.get("global_claim"):
        return None
    return core.get(core.build_view(), res["global_claim"])


# ================================================================
# T1 — H1: 注入層原則 + counter-factual(wrong-source 検出の本命)
#   SearchConclusion.status を "COMPLETED" に固定(driver が嘘をつく)したまま、
#   leg event だけを反転する。outcome が変われば = gate3 は scon.status でなく
#   leg event を見ている証拠。変わらなければ = wrong-source(H1 未修正)。
# ================================================================
def t1_h1_wrong_source():
    def drive(fail_repo):
        reset()
        r = core.run_start("rd", "CURATION", task_id="T")
        plan = P.mk_search_plan(r, "G", "COV-TECH-STANDARD")
        core.run_end(r, [plan])
        for kind in ["official_documentation", "release_notes", "official_repository"]:
            P.mk_search_leg("T", plan, kind,
                            simulate_fail=(fail_repo and kind == "official_repository"))
        # driver は常に COMPLETED と *嘘* をつく(status を信用させる罠)
        rc = core.run_start("rd", "SEARCH", task_id="T", inputs=[plan])
        scon = P.mk_search_conclusion(rc, plan, "COMPLETED", "NO_POSITIVE_EVIDENCE")
        core.run_end(rc, [scon])
        ra = core.run_start("rd", "EXTRACTION", task_id="T")
        C = absence_candidate(ra, plan, scon)
        core.run_end(ra, [C])
        return curator.curate(C)["outcome"]

    all_ok = drive(fail_repo=False)          # 全 leg COMPLETED
    one_failed = drive(fail_repo=True)       # repo leg だけ FAILED(scon.status は嘘のまま)
    # counter-factual: leg を反転しただけで outcome が変わること
    changed = all_ok != one_failed
    check("T1a H1 leg 注入で全成功 → ABSENCE 成立", all_ok == "ACCEPT", f"outcome={all_ok}")
    check("T1b H1 leg 反転(scon.status=COMPLETED の嘘は不変)→ ブロック",
          one_failed == "ABSENCE_BLOCKED_SC2", f"outcome={one_failed}")
    check("T1c H1 counter-factual: leg event が outcome を決める(scon.status でなく)",
          changed, f"{all_ok} → {one_failed}")


# ================================================================
# T2 — H3: gate2(dedup/conflict CS-1)が dead でない
#   同 claim_key の受理済み Claim があれば 2つ目は ACCEPT されない。
#   counter-factual: claim_key を変えれば ACCEPT に戻る。
# ================================================================
def t2_h3_gate2():
    reset()
    r = core.run_start("rd", "CURATION", task_id="T")
    core.run_end(r, [])
    scope = {"gpu_arch": "sm120", "quant": "nvfp4"}
    c1 = positive_candidate(r, scope)
    o1 = curator.curate(c1, adj_for(c1))["outcome"]                 # 先行受理
    c2 = positive_candidate(r, dict(scope))                        # 同 claim_key
    o2 = curator.curate(c2, adj_for(c2))["outcome"]                # 衝突すべき
    c3 = positive_candidate(r, {"gpu_arch": "sm120", "quant": "fp8"})  # 別 claim_key
    o3 = curator.curate(c3, adj_for(c3))["outcome"]                # 衝突しない
    check("T2a H3 先行 claim は ACCEPT", o1 == "ACCEPT", f"outcome={o1}")
    check("T2b H3 同 claim_key の 2つ目は CONFLICT(両方 ACCEPT の穴を塞ぐ)",
          o2 == "CONFLICT_REVIEW_REQUIRED", f"outcome={o2}")
    check("T2c H3 counter-factual: claim_key を変えれば ACCEPT に戻る(gate2 が live)",
          o3 == "ACCEPT", f"outcome={o3}")


# ================================================================
# T3 — H3/M5: importance が dead でない
#   REQUIRED_FOR_RESOLUTION gap を PARTIAL では埋められない。
#   counter-factual: SUPPORTING(gap 無)なら同 finding で ACCEPT。
# ================================================================
def t3_h3_importance():
    reset()
    r = core.run_start("rd", "CURATION", task_id="T")
    gap = P.mk_gap(r, "q", required_for=["REQ-1"], profile="EP")
    core.run_end(r, [gap])
    c_req = positive_candidate(r, {"gpu_arch": "sm120"}, resolves_gap=gap)
    o_req = curator.curate(c_req, adj_for(c_req, f1="PARTIAL"))["outcome"]
    c_sup = positive_candidate(r, {"gpu_arch": "sm120", "quant": "nvfp4"}, resolves_gap=None)
    o_sup = curator.curate(c_sup, adj_for(c_sup, f1="PARTIAL"))["outcome"]
    check("T3a H3 REQUIRED gap を PARTIAL では埋めない",
          o_req == "EVIDENCE_INSUFFICIENT", f"outcome={o_req}")
    check("T3b H3 counter-factual: SUPPORTING なら同 finding で ACCEPT(importance が live)",
          o_sup == "ACCEPT", f"outcome={o_sup}")


# ================================================================
# T4 — H4: GC-7 が curate 連鎖に接続されている(孤立 demo でない)
#   受理 claim の known_omissions 次元へ踏み込む候補は curate 内でブロック。
#   counter-factual: 踏み込まなければ通過(gc7 が live)。
# ================================================================
def t4_h4_gc7():
    reset()
    r = core.run_start("rd", "CURATION", task_id="T")
    g = core.append_event(r, "CREATE", "Claim", None, {
        "id": core.SELF, "object_kind": "Claim", "claim_type": "CAPABILITY", "predicate": "runs_on",
        "statement": "ground", "scope": {"gpu_arch": "sm120"}, "status": "VERIFIED",
        "representation_residual": {"known_omissions": ["operational_stability"]}}, new_prefix="C")
    core.run_end(r, [g])
    # 踏み込む: scope_echo に omitted 次元
    c_over = positive_candidate(r, {"gpu_arch": "sm120", "quant": "nvfp4"}, grounds_claims=[g],
                                scope_echo={"operational_stability": "sustained"})
    o_over = curator.curate(c_over, adj_for(c_over))["outcome"]
    # 踏み込まない
    c_ok = positive_candidate(r, {"gpu_arch": "sm120", "quant": "fp8"}, grounds_claims=[g])
    o_ok = curator.curate(c_ok, adj_for(c_ok))["outcome"]
    check("T4a H4 omitted 次元へ踏み込む候補は curate 内で GC7_BLOCKED",
          o_over == "GC7_BLOCKED", f"outcome={o_over}")
    check("T4b H4 counter-factual: 踏み込まなければ通過(gc7 が連鎖で live)",
          o_ok == "ACCEPT", f"outcome={o_ok}")


# ================================================================
# T5 — M3: dangling nobs/source で crash せず clean-fail
# ================================================================
def t5_m3_dangling():
    reset()
    r = core.run_start("rd", "CURATION", task_id="T")
    # fragment が存在しない norm_obs を指す(dangling)
    frag = core.append_event(r, "CREATE", "EvidenceFragment", None,
                             {"id": core.SELF, "norm_obs_id": "NOBS-99999", "block_index": 0,
                              "excerpt": "x", "taint_flags": []}, new_prefix="EFRAG")
    rel = P.mk_relation(r, frag, None, "SUPPORTS", {})
    C = P.mk_candidate(r, {
        "object_kind": "CandidateClaim", "claim_type": "CAPABILITY", "predicate": "p",
        "polarity": "POSITIVE", "task_id": "T", "statement": "s", "scope": {"gpu_arch": "sm120"},
        "evidence_relations": [rel], "resolves_gap": None})
    core.run_end(r, [C])
    try:
        o = curator.curate(C)["outcome"]
        crashed = False
    except Exception as e:                                   # None 添字なら旧挙動
        o, crashed = f"CRASH:{type(e).__name__}", True
    check("T5 M3 dangling で crash せず clean-fail(DEFER)",
          (not crashed) and o == "DEFER", f"outcome={o}")


# ================================================================
# T6 — AB-0003: bootstrap を teacher-signal 由来で stratify
#   positive(Claude 判定)= bootstrap True / ABSENCE(judge 無)= bootstrap False
# ================================================================
def t6_ab0003_bootstrap():
    reset()
    r = core.run_start("rd", "CURATION", task_id="T")
    core.run_end(r, [])
    c = positive_candidate(r, {"gpu_arch": "sm120"})
    pos_claim = claim_of(curator.curate(c, adj_for(c)))
    # ABSENCE 成立(全 leg COMPLETED)
    r2 = core.run_start("rd", "CURATION", task_id="T2")
    plan = P.mk_search_plan(r2, "G", "COV-TECH-STANDARD")
    core.run_end(r2, [plan])
    for kind in ["official_documentation", "release_notes", "official_repository"]:
        P.mk_search_leg("T2", plan, kind)
    rc = core.run_start("rd", "SEARCH", task_id="T2", inputs=[plan])
    scon = P.mk_search_conclusion(rc, plan, "COMPLETED", "NO_POSITIVE_EVIDENCE")
    core.run_end(rc, [scon])
    ra = core.run_start("rd", "EXTRACTION", task_id="T2")
    ca = absence_candidate(ra, plan, scon)
    core.run_end(ra, [ca])
    abs_claim = claim_of(curator.curate(ca))
    check("T6a AB-0003 positive(teacher signal)= bootstrap True",
          pos_claim and pos_claim.get("bootstrap") is True, f"bootstrap={pos_claim and pos_claim.get('bootstrap')}")
    check("T6b AB-0003 ABSENCE(judge 無)= bootstrap False(benchmark B 非汚染)",
          abs_claim and abs_claim.get("bootstrap") is False, f"bootstrap={abs_claim and abs_claim.get('bootstrap')}")


if __name__ == "__main__":
    print("=== Challenge Set C (DE-0009): build-out G1 enforce 構造試験 ===")
    print("\n[T1] H1 SC-2 wrong-source(注入層 + counter-factual)")
    t1_h1_wrong_source()
    print("\n[T2] H3 gate2 dedup/conflict(counter-factual)")
    t2_h3_gate2()
    print("\n[T3] H3/M5 importance(counter-factual)")
    t3_h3_importance()
    print("\n[T4] H4 GC-7 curate 接続(counter-factual)")
    t4_h4_gc7()
    print("\n[T5] M3 dangling clean-fail")
    t5_m3_dangling()
    print("\n[T6] AB-0003 bootstrap stratify")
    t6_ab0003_bootstrap()

    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed))
        sys.exit(1)
    print("全 enforce が driver 正直性に依存せず構造で成立(DE-0005 の過大報告を再発防止)")
