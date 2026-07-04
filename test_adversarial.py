#!/usr/bin/env python3
"""JREV-0001 findings の敵対テスト(R1/R3/R4/H4b)。

R1(修正=検出水準)/ R3(修正=surface 正規化)/ R4(仕様確定・vuln 記録)/ H4b(gap 記録)。
※ ここでの合格は test-verified に留まる。property の再判定(JREV-0002)は独立レビューが行う
   ——著者が自分の修正を JUDGE_VERIFIED と宣言しない(自己検証の禁忌)。
"""
import os, sys, tempfile
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_adv_"))
from egl import core, gates, pipeline as P

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


def reset():
    for f in ["events.jsonl", "state.sqlite", ".idlock"]:
        p = core.DATA / f
        if p.exists():
            p.unlink()


# ===============================================================
# R1 — semantic write authority(検出水準)。prevention でなく『違反が必ず検出可能』。
# ===============================================================
def t_r1_write_authority():
    reset()
    r = core.run_start("sys", "CURATION")
    cid = core.append_event(r, "CREATE", "Claim", None,
                            {"id": core.SELF, "object_kind": "Claim", "status": "REPORTED", "note": "x"},
                            new_prefix="C")
    tok = core.issue_capability(r, "curator", "CORRECTOR")
    core.correct_object(r, "Claim", cid, {"note": "y"}, "fix", "METADATA", capability=tok)
    a1 = core.audit_write_authority()
    check("R1a 発行済 capability での CORRECTION は audit clean", not a1["violations"], str(a1["violations"]))
    # forge: GRANT 記録なき capability で privileged write
    core.append_event(r, "CORRECTION", "Claim", cid, {**core.get_state(cid), "note": "z"},
                      principal="rd_attacker", capability="CORRECTOR")
    a2 = core.audit_write_authority()
    check("R1b forge(GRANT 記録なき capability)を audit が検出", len(a2["violations"]) >= 1, str(a2["violations"]))
    # capability 無しの privileged write → 既定 unprotected、enforce 指定で violation(harden ratchet)
    core.complete_object(r, "Claim", cid, {"extra": "1"}, "fill")   # capability 無し
    a3 = core.audit_write_authority()
    a4 = core.audit_write_authority(enforce_types=["COMPLETION"])
    check("R1c capability 無し privileged は unprotected(既定 violation でない)",
          any(u["event_type"] == "COMPLETION" for u in a3["unprotected"]))
    check("R1d enforce_types 指定で unprotected も violation 化(prevention へ硬化する ratchet)",
          any(v["event_type"] == "COMPLETION" for v in a4["violations"]))


# ===============================================================
# R3 — claim_key identity gaming を scope canonicalizer が封鎖(surface 層)。
# ===============================================================
def t_r3_identity_canon():
    reset()
    c = core.canonicalize_scope({"runtime": "VLLM", "quant": "NV-FP4", "gpu_arch": "Blackwell"})
    check("R3a canonicalize: VLLM/NV-FP4/Blackwell → vllm/nvfp4/sm120",
          c == {"runtime": "vllm", "quant": "nvfp4", "gpu_arch": "sm120"}, str(c))
    r = core.run_start("rd", "CURATION")
    core.append_event(r, "CREATE", "Claim", None,
                      {"id": core.SELF, "object_kind": "Claim", "claim_type": "CAPABILITY",
                       "predicate": "runs_on", "scope": {"runtime": "vllm", "quant": "nvfp4"}}, new_prefix="C")
    core.run_end(r, [])
    con = core.build_view()
    variant = {"object_kind": "CandidateClaim", "claim_type": "CAPABILITY", "predicate": "runs_on",
               "scope": {"runtime": "VLLM", "quant": "NV-FP4"}}
    g2 = gates.gate2_candidates(con, variant)
    check("R3b 表記揺れ(VLLM/NV-FP4)でも claim_key 一致 → 衝突検出(gaming 封鎖)",
          bool(g2["dup_conflict_candidate_ids"]), str(g2))
    diff = {"object_kind": "CandidateClaim", "claim_type": "CAPABILITY", "predicate": "runs_on",
            "scope": {"runtime": "vllm", "quant": "fp8"}}
    check("R3c counter-factual: 真に別 quant は衝突しない", not gates.gate2_candidates(con, diff)["dup_conflict_candidate_ids"])
    resid = core.canonicalize_scope({"runtime_version": "0.11"}) != core.canonicalize_scope({"runtime_version": ">=0.11"})
    check("R3d 宣言境界: version algebra(0.11 vs >=0.11)は未解決=別 key(AB-0009 残)", resid)


# ===============================================================
# R4 — leg_plan_id binding forgery(vuln 記録)。修正=LegIntent、取得ラッパー実装時(AB-0010)。
# ===============================================================
def t_r4_leg_binding_vuln():
    reset()
    r = core.run_start("rd", "CURATION")
    plan = P.mk_search_plan(r, "G", "COV-TECH-STANDARD")
    core.run_end(r, [])
    P.mk_search_leg("T", plan, "official_documentation")
    P.mk_search_leg("T", plan, "release_notes")            # official_repository を欠く
    before = gates._derive_checked_kinds(core.build_view(), plan)
    # forge: 別文脈で成功した leg を leg_plan_id=plan として直接 append(provenance binding forgery)
    rid = core.run_start("attacker", "SEARCH", task_id="OTHER")
    st = core.get_state(rid)
    st.update({"leg_plan_id": plan, "source_kind": "official_repository",
               "outputs": [], "status": "COMPLETED", "ended_at": core.now_iso()})
    core.append_event(rid, "UPDATE", "Run", rid, st)
    after = gates._derive_checked_kinds(core.build_view(), plan)
    status, _ = gates.evaluate_coverage("COV-TECH-STANDARD", after)
    check("R4(vuln 記録)forge した leg_plan_id で coverage 充足=binding 未検証(LegIntent 待ち AB-0010)",
          "official_repository" in after and status == "COMPLETED", f"{before} -> {after} : {status}")


# ===============================================================
# H4b — statement→scope 抽出の self-report。GC-7 は scope-key ベースで statement 主張を見ない(gap 記録)。
# ===============================================================
def t_h4b_statement_scope():
    reset()
    r = core.run_start("rd", "CURATION")
    g = core.append_event(r, "CREATE", "Claim", None,
                          {"id": core.SELF, "object_kind": "Claim",
                           "representation_residual": {"known_omissions": ["operational_stability"]}},
                          new_prefix="C")
    core.run_end(r, [])
    con = core.build_view()
    gclaim = core.get(con, g)
    overreach = {"statement": "X is stable under sustained load", "scope": {"runtime": "vllm"}}
    ok, msg = gates.gc7_lint(con, overreach, gclaim)
    check("H4b(gap 記録)statement 安定性主張 + scope 軸欠落 → GC-7 素通り(主防衛は設計上 Gate4 F1)", ok, msg)
    honest = {"statement": "X", "scope": {"runtime": "vllm", "operational_stability": "claimed"}}
    ok2, _ = gates.gc7_lint(con, honest, gclaim)
    check("H4b counter-factual: scope に軸が出れば GC-7 は block(scope-key ベースの証拠)", not ok2)


if __name__ == "__main__":
    print("=== JREV-0001 敵対テスト (R1/R3/R4/H4b) ===")
    print("\n[R1] semantic write authority(検出水準)")
    t_r1_write_authority()
    print("\n[R3] claim_key identity gaming / scope canonicalizer")
    t_r3_identity_canon()
    print("\n[R4] leg_plan_id binding forgery(vuln 記録・LegIntent 待ち)")
    t_r4_leg_binding_vuln()
    print("\n[H4b] statement→scope self-report(gap 記録)")
    t_h4b_statement_scope()

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("R1 検出可能・R3 surface 封鎖・R4/H4b は仕様/gap を敵対テストで確定。再判定は独立 JREV-0002")
