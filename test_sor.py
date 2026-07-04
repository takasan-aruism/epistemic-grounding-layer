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
from egl import core
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


if __name__ == "__main__":
    print("=== SoR 契約試験 (DE-0006 H5/H6) ===")
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

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed))
        sys.exit(1)
    print("counters.json 廃止・id-in-append・H6 lock が log だけで成立(単一 SoR)")
