#!/usr/bin/env python3
"""SoR 契約試験 — DE-0006 (H5/H6)。

H5: counters.json(events から導出不能な第2 SoR)を廃止し、id を append_event 内で
    log の high-water から採番する。『採番済み id ⟺ その id を刻む event が log に存在』を
    保証するので、high-water は log からの再スキャンで常に正しく復元できる(第2 SoR 不要)。
H6: 採番+書込を同一 lock に入れ、並行 run の id 衝突を防ぐ。

この試験は AB-0005(test isolation)を前提に成立する: log を汚すテストで『log だけから
id が復元される』ことは検証できない。EGL_DATA_DIR で canonical SoR と隔離してから検証する。
"""
import os, sys, tempfile
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_sor_"))
from egl import core, gates, pipeline as P
import multiprocessing as mp

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


def reset():
    for f in ["events.jsonl", "state.sqlite", ".idlock"]:
        p = core.DATA / f
        if p.exists():
            p.unlink()


def mk(prefix="TH", run="R"):
    return core.append_event(run, "CREATE", "Thing", None, {"id": core.SELF}, new_prefix=prefix)


# ---------------------------------------------------------------
# T1 — H5: 第2 SoR(counters.json)が存在しない / id は log だけから決まる
# ---------------------------------------------------------------
def t_h5_no_second_sor():
    reset()
    ids = [mk() for _ in range(5)]
    no_counter = not (core.DATA / "counters.json").exists()
    seq_ok = ids == [f"TH-{i:05d}" for i in range(1, 6)]
    hw_ok = core._high_water().get("TH") == 5
    check("T1a H5 counters.json を持たない(第2 SoR 廃止)", no_counter)
    check("T1b H5 id は log high-water から連番採番", seq_ok, f"ids={ids}")
    check("T1c H5 high-water は log からの導出のみ", hw_ok, f"hw(TH)={core._high_water().get('TH')}")


# ---------------------------------------------------------------
# T2 — H5: 『採番 ⟺ event 存在』。log を消して再スキャンしても next id が一致
#          (= 第2 SoR 無しで high-water 復元)。旧 counters.json 喪失時の衝突が起きない。
# ---------------------------------------------------------------
def t_h5_highwater_recovered_from_log():
    reset()
    for _ in range(3):
        mk()
    # 別プロセス相当: in-memory 状態を一切持たず、log 再スキャンだけで次 id を確定
    hw_before = core._high_water().get("TH")
    nxt = mk()
    check("T2a H5 log 再スキャンの high-water = 3(counters.json 無しで復元)", hw_before == 3, f"hw={hw_before}")
    check("T2b H5 次 id は high-water+1、gap/衝突なし", nxt == "TH-00004", f"next={nxt}")


# ---------------------------------------------------------------
# T3 — H5: id は event と不可分。採番だけで event を書かない経路が存在しない
#          (new_id 単独 API を廃止したことの確認)。
# ---------------------------------------------------------------
def t_h5_id_inseparable_from_event():
    reserve_only = hasattr(core, "new_id")
    check("T3 H5 事前採番 API(new_id)が存在しない=id は append と不可分",
          not reserve_only, "new_id 残存" if reserve_only else "")


# ---------------------------------------------------------------
# T4 — H6: 並行採番で衝突しない(lock)。lock が無効なら high-water の read-modify-write が
#          race して同一 id が複数生成される → このテストが FAIL する(= lock の必要性の証拠)。
# ---------------------------------------------------------------
def _worker(m):
    for _ in range(m):
        core.append_event("R", "CREATE", "Thing", None, {"id": core.SELF}, new_prefix="CC")


def t_h6_concurrent_no_collision():
    reset()
    K, M = 4, 30
    ctx = mp.get_context("fork")
    procs = [ctx.Process(target=_worker, args=(M,)) for _ in range(K)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    evs = core.read_events()
    cc = [e["object_id"] for e in evs if isinstance(e.get("object_id"), str) and e["object_id"].startswith("CC-")]
    evids = [e["event_id"] for e in evs]
    check("T4a H6 並行 K×M 採番で object_id 衝突なし & 個数一致",
          len(cc) == K * M and len(cc) == len(set(cc)), f"n={len(cc)} uniq={len(set(cc))} expect={K*M}")
    check("T4b H6 event_id も衝突なし(EV も同一 lock 下で採番)",
          len(evids) == len(set(evids)), f"n={len(evids)} uniq={len(set(evids))}")


# ---------------------------------------------------------------
# T5 — RC-3 不変: id-in-append 後も view は log から決定的に再構築できる
# ---------------------------------------------------------------
def t_rc3_still_holds():
    reset()
    import hashlib

    def snap():
        con = core.build_view()
        rows = con.execute("SELECT object_id,state_json FROM objects ORDER BY object_id").fetchall()
        h = hashlib.sha256()
        for oid, sj in rows:
            h.update(f"{oid}|{sj}".encode())
        return h.hexdigest()[:16]

    for _ in range(4):
        mk()
    check("T5 RC-3 view は log から決定的再構築(id-in-append 後も不変)", snap() == snap())


# ---------------------------------------------------------------
# T6 — M4 (DE-0007): partial-update を append_event が構造 reject
# ---------------------------------------------------------------
def t_m4_partial_rejected():
    reset()
    oid = core.append_event("R", "CREATE", "Thing", None,
                            {"id": core.SELF, "a": 1, "b": 2}, new_prefix="TH")
    try:
        core.append_event("R", "UPDATE", "Thing", oid, {"id": oid, "a": 9})   # 'b' を落とす
        rej = False
    except ValueError:
        rej = True
    check("T6a M4 partial UPDATE(兄弟キー drop)を構造 reject", rej)
    try:
        core.append_event("R", "UPDATE", "Thing", oid, {"id": oid, "a": 9, "b": 2})
        ok = True
    except ValueError:
        ok = False
    check("T6b M4 counter-factual: 完全 revision の UPDATE は通る", ok)


# ---------------------------------------------------------------
# T7 — M4: nested 兄弟キー喪失(shallow-merge の M4 本体)も reject / 完全なら保存
# ---------------------------------------------------------------
def t_m4_nested_sibling():
    reset()
    oid = core.append_event("R", "CREATE", "Obj", None,
                            {"id": core.SELF, "temporal": {"x": 1, "y": 2}}, new_prefix="OB")
    try:
        core.append_event("R", "UPDATE", "Obj", oid, {"id": oid, "temporal": {"x": 1}})  # y 消失
        rej = False
    except ValueError:
        rej = True
    check("T7a M4 nested 兄弟キー drop(temporal.y)を reject", rej)
    core.append_event("R", "UPDATE", "Obj", oid, {"id": oid, "temporal": {"x": 1, "y": 2, "z": 3}})
    st = core.get_state(oid)
    check("T7b M4 完全 nested UPDATE は通り兄弟が保存される", st["temporal"] == {"x": 1, "y": 2, "z": 3},
          f"temporal={st['temporal']}")


# ---------------------------------------------------------------
# T8 — L4 (DE-0008): validation_mode を provenance から導出。既定値を捏造しない。
# ---------------------------------------------------------------
def t_l4_derive_validation_mode():
    reset()
    r = core.run_start("rd", "CURATION")
    sp = P.mk_source(r, "primary", "PRIMARY", "loc")
    np_ = P.mk_observation(r, sp, "H", ["b0", "b1", "b2"])
    fp = P.mk_fragment(r, np_, 1, "b1")
    rel_p = P.mk_relation(r, fp, None, "SUPPORTS", {})
    sg = P.mk_source(r, "generated", "GENERATED", "loc")
    ng = P.mk_observation(r, sg, "H", ["b0", "b1", "b2"])
    fg = P.mk_fragment(r, ng, 1, "b1")
    rel_g = P.mk_relation(r, fg, None, "SUPPORTS", {})
    core.run_end(r, [])
    con = core.build_view()
    prim = gates.derive_validation_mode(con, {"polarity": "POSITIVE", "evidence_relations": [rel_p]})
    gen = gates.derive_validation_mode(con, {"polarity": "POSITIVE", "evidence_relations": [rel_g]})
    neg = gates.derive_validation_mode(con, {"polarity": "NEGATIVE", "evidence_relations": [rel_p]})
    try:
        gates.derive_validation_mode(con, {"polarity": "ABSENCE"})
        abs_raises = False
    except ValueError:
        abs_raises = True
    absv = gates.derive_absence_validation(con, {"polarity": "ABSENCE", "search_conclusion": None})
    check("T8a L4 PRIMARY 由来 → DECLARED(provenance 導出)", prim == "DECLARED", prim)
    check("T8b L4 counter-factual: GENERATED のみ → UNRESOLVED(既定を捏造しない)", gen == "UNRESOLVED", gen)
    check("T8c R5 NEGATIVE + PRIMARY → SPECIFIED(明示的不支持 claim 専用)", neg == "SPECIFIED", neg)
    check("T8d R5 ABSENCE に validation_mode を求めると reject(NOT_FOUND と規定不在の再混同を封じる)", abs_raises)
    check("T8e R5 ABSENCE は別軸 absence_validation(SEARCH_COVERAGE_COMPLETED)",
          absv["mode"] == "SEARCH_COVERAGE_COMPLETED", str(absv))


# ---------------------------------------------------------------
# T9 — L4: CORRECTION 機構。過去 event を書換えず訂正(本系初の RETRACTION 先例)。
# ---------------------------------------------------------------
def t_l4_correction_append_only():
    reset()
    r = core.run_start("rd", "CURATION")
    cid = core.append_event(r, "CREATE", "Claim", None,
                            {"id": core.SELF, "object_kind": "Claim", "status": "VERIFIED",
                             "validation_mode": "DECLARED",
                             "temporal": {"observation_time": "t0", "valid_until": "t9"}}, new_prefix="C")
    core.run_end(r, [cid])
    r2 = core.run_start("rd", "CURATION")
    core.correct_object(r2, "Claim", cid, {"validation_mode": "UNRESOLVED"},
                        reason="provenance 未確認: 既定 DECLARED は無根拠 (L4)",
                        correction_class="FACTUAL", basis="DE-0008 provenance 再検査")
    core.run_end(r2, [cid])

    evs = core.read_events()
    st = core.get_state(cid)
    fc = (st.get("corrections") or [{}])[-1].get("field_changes", {}).get("validation_mode")
    orig_intact = any(e["object_id"] == cid and e["event_type"] == "CREATE"
                      and e["payload"].get("validation_mode") == "DECLARED" for e in evs)
    check("T9a L4 correction: 訂正値が view で有効", st.get("validation_mode") == "UNRESOLVED",
          st.get("validation_mode"))
    check("T9b L4 correction: from/to provenance が corrections に残る",
          fc == {"from": "DECLARED", "to": "UNRESOLVED"}, str(fc))
    check("T9c L4 correction: 原 CREATE event は書換えられず log に残る(append-only)", orig_intact)
    check("T9d L4 correction: 完全 revision で nested 兄弟(temporal)保存",
          st.get("temporal") == {"observation_time": "t0", "valid_until": "t9"}, str(st.get("temporal")))


# ---------------------------------------------------------------
# T10 — AB-0007: relation.to_id を candidate 確定後に COMPLETION で結線(恒久 null link を残さない)
# ---------------------------------------------------------------
def t_ab0007_relation_completion():
    reset()
    r = core.run_start("rd", "CURATION")
    s = P.mk_source(r, "x", "PRIMARY", "loc")
    n = P.mk_observation(r, s, "H", ["b0", "b1", "b2"])
    f = P.mk_fragment(r, n, 1, "b1")
    rel = P.mk_relation(r, f, None, "SUPPORTS", {})           # to=None で先行生成
    cid = P.mk_candidate(r, {"object_kind": "CandidateClaim", "claim_type": "CAPABILITY",
                             "predicate": "p", "polarity": "POSITIVE", "task_id": "T",
                             "statement": "s", "scope": {"gpu_arch": "sm120"},
                             "evidence_relations": [rel], "resolves_gap": None})
    core.run_end(r, [cid])
    evs = core.read_events()
    st = core.get_state(rel)
    orig_null = any(e["object_id"] == rel and e["event_type"] == "CREATE"
                    and e["payload"].get("to_id") is None for e in evs)
    ff = (st.get("completions") or [{}])[-1].get("field_fills", {}).get("to_id")
    check("T10a AB-0007 candidate 確定後 relation.to_id が結線される", st.get("to_id") == cid, st.get("to_id"))
    check("T10b AB-0007 原 CREATE は to_id=None のまま log 残存(append-only)", orig_null)
    check("T10c AB-0007 完結 provenance(from None→to cid)が completions に残る",
          ff == {"from": None, "to": cid}, str(ff))


# ---------------------------------------------------------------
# T11 — R2: CORRECTION/COMPLETION transition-legality guard(GPT CR/CP + 3 counter-factual)
# ---------------------------------------------------------------
def _raises(fn):
    try:
        fn(); return False
    except ValueError:
        return True


def t_r2_correction_completion_policy():
    reset()
    r = core.run_start("rd", "CURATION")
    cid = core.append_event(r, "CREATE", "Claim", None,
                            {"id": core.SELF, "object_kind": "Claim", "status": "REJECTED",
                             "polarity": "POSITIVE", "validation_mode": "DECLARED",
                             "source_class": "COMMUNITY"}, new_prefix="C")
    core.run_end(r, [cid])
    r2 = core.run_start("rd", "CURATION")
    # CR-1: class 無し
    check("T11a CR-1 correction_class 無しは reject",
          _raises(lambda: core.correct_object(r2, "Claim", cid, {"note": "x"}, "r", correction_class=None)))
    # CR-4 / counter-factual①: REJECTED→VERIFIED を CORRECTION で復活 → reject
    check("T11b CR-4 counter-factual: REJECTED→VERIFIED を CORRECTION で復活 → reject",
          _raises(lambda: core.correct_object(r2, "Claim", cid, {"status": "VERIFIED"}, "revive",
                                              correction_class="FACTUAL", basis="x")))
    # CR-2: METADATA が epistemic(validation_mode)を変更 → reject
    check("T11c CR-2 METADATA correction が validation_mode を変更 → reject",
          _raises(lambda: core.correct_object(r2, "Claim", cid, {"validation_mode": "REPRODUCED"}, "r",
                                              correction_class="METADATA")))
    # CR-3: FACTUAL に basis 無し → reject
    check("T11d CR-3 FACTUAL correction に basis 無し → reject",
          _raises(lambda: core.correct_object(r2, "Claim", cid, {"validation_mode": "UNRESOLVED"}, "r",
                                              correction_class="FACTUAL")))
    # counter-factual②: 既存 source_class=COMMUNITY を COMPLETION で PRIMARY に → reject(CP-2)
    check("T11e CP-2 counter-factual: 既存 source_class を COMPLETION で書換 → reject",
          _raises(lambda: core.complete_object(r2, "Claim", cid, {"source_class": "PRIMARY"}, "upgrade")))
    # counter-factual③: 欠落 validation_mode(別 object)を COMPLETION で UNRESOLVED に → accept(CP-1)
    oid = core.append_event(r2, "CREATE", "Claim", None,
                            {"id": core.SELF, "object_kind": "Claim", "status": "REPORTED"}, new_prefix="C")
    core.complete_object(r2, "Claim", oid, {"validation_mode": "UNRESOLVED"}, "fill missing")
    core.run_end(r2, [cid])
    check("T11f CP-1 counter-factual: 欠落 field を COMPLETION で concrete 化 → accept",
          core.get_state(oid).get("validation_mode") == "UNRESOLVED")
    # METADATA で非 epistemic(locator 相当)は通る
    ok_meta = True
    try:
        core.correct_object(r2, "Claim", cid, {"note": "typo fix"}, "r", correction_class="METADATA")
    except ValueError:
        ok_meta = False
    check("T11g CR-2 counter-factual: METADATA で非 epistemic field は通る", ok_meta)


# ---------------------------------------------------------------
# T12 — 恒久対策: 全 guard が non_guarantees(guard の known_omissions)を宣言している
# ---------------------------------------------------------------
def t_guard_non_guarantees_declared():
    from egl import contracts
    missing = [g for g, c in contracts.GUARD_CONTRACTS.items() if not c.get("non_guarantees")]
    check("T12a 全 guard が non_guarantees を宣言(guard の known_omissions)", not missing, str(missing))
    # レビューで confirmed だった性質が宣言に載っているか(自認の事前化)
    m4 = " ".join(contracts.GUARD_CONTRACTS["core._check_complete_revision"]["non_guarantees"])
    gc7 = " ".join(contracts.GUARD_CONTRACTS["gates.gc7_lint"]["non_guarantees"])
    ae = " ".join(contracts.GUARD_CONTRACTS["core.append_event"]["non_guarantees"])
    check("T12b R2 が M4 の non_guarantee に事前記載(transition legality)", "transition legality" in m4)
    check("T12c H4b が GC-7 の non_guarantee に事前記載(statement→scope)", "statement→scope" in gc7)
    check("T12d R1 が append_event の non_guarantee に事前記載(semantic write authority)",
          "semantic write authority" in ae)


if __name__ == "__main__":
    print("=== SoR 契約試験 (DE-0006 H5/H6 + DE-0007 M4 + DE-0008 L4 + AB-0007 + R2/R5 + guard契約) ===")
    print("\n[T1] H5 第2 SoR 廃止 / log 由来 id")
    t_h5_no_second_sor()
    print("\n[T2] H5 high-water を log から復元")
    t_h5_highwater_recovered_from_log()
    print("\n[T3] H5 id と event の不可分性")
    t_h5_id_inseparable_from_event()
    print("\n[T4] H6 並行採番 lock(この FAIL は lock の必要性の counter-factual)")
    t_h6_concurrent_no_collision()
    print("\n[T5] RC-3 不変")
    t_rc3_still_holds()
    print("\n[T6] M4 partial-update 構造 reject (DE-0007)")
    t_m4_partial_rejected()
    print("\n[T7] M4 nested 兄弟キー保存")
    t_m4_nested_sibling()
    print("\n[T8] L4 validation_mode 導出 (DE-0008)")
    t_l4_derive_validation_mode()
    print("\n[T9] L4 CORRECTION 機構(append-only 訂正)")
    t_l4_correction_append_only()
    print("\n[T10] AB-0007 relation 完結 event(COMPLETION 結線)")
    t_ab0007_relation_completion()
    print("\n[T11] R2 CORRECTION/COMPLETION transition-legality guard")
    t_r2_correction_completion_policy()
    print("\n[T12] 恒久対策: guard non_guarantees 宣言")
    t_guard_non_guarantees_declared()

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed))
        sys.exit(1)
    print("counters.json 廃止・id-in-append・H6 lock が log だけで成立(単一 SoR)")
