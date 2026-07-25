#!/usr/bin/env python3
"""s_de_route_equiv — front-door slice1 同値検証: DE 記録の「直叩き」vs「submit 経由」が byte 同値の ledger 行を生むか。

証明→切替→(後スライスで)閉塞 の順。**この段では直叩きを塞がない**(enforcement なし・並行運用)。
scope: 同値は **ledger 行**について。submit は追加で RRI residual / DS thread event / trace を生む(=front-door
provenance=移行の価値)が、それは ledger 行を変えない(ledger-row-neutral)ことを確認する。

hermetic: temp DE ledger(直叩き用/submit用で別ファイル=dup rejection 回避+実 ledger 不汚染) + DS/RRI/EGL data dir を temp 隔離
(submit の DS thread/RRI 書込が実状態を汚さない)。決定論・冪等。measure-first(差は ROUTE_DIVERGENCE で surface・握り潰さない)。

usage:  s_de_route_equiv.py [--check]
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = "/home/takasan"
STRUCT = os.path.dirname(os.path.abspath(__file__))
REAL_LEDGER = os.path.join(ROOT, "egl", "DESIGN_EVIDENCE_LEDGER.jsonl")
TMPBASE = os.environ.get("TMPDIR") or "/home/takasan/.cc_tmp"

# 代表 candidate: ADMITTED(record-occurrence) / REJECTED-schema / REJECTED-ceiling / BEHAVIORAL-downgrade。
# temp ledger は空から始まるので DE-90xx は実 ledger と衝突しない。
CANDIDATES = [
    {"label": "ADMITTED", "cand": {
        "design_evidence_id": "DE-9001", "observation": "front-door slice1 の同値検証用の代表ケース(記録)",
        "decision": "DE 記録を submit 経由へ移行する", "decision_owner": "Taka",
        "claimed_status": "PROVISION", "evidence_refs": ["docs/CC_DESIGN_2026-07-26_FRONTDOOR_SLICE1"]}},
    {"label": "REJECTED_SCHEMA", "cand": {
        "design_evidence_id": "DE-9002", "observation": "decision_owner 欠落で schema reject されるケース",
        "decision": "reject される", "evidence_refs": ["x"]}},   # decision_owner 欠落
    {"label": "REJECTED_CEILING", "cand": {
        "design_evidence_id": "DE-9003", "observation": "self-improving system で over-claim ceiling に触れる",
        "decision": "hard reject", "decision_owner": "Taka", "evidence_refs": ["x"]}},
    {"label": "BEHAVIORAL_DOWNGRADE", "cand": {
        "design_evidence_id": "DE-9004", "observation": "this works in production so it is fine",
        "decision": "behavioral claim は再検証なしで REPORTED に降格", "decision_owner": "Taka",
        "evidence_refs": ["x"]}},
]


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.isfile(path) else "ABSENT"


def _hermetic_env():
    """DS/RRI/EGL の書込を temp 隔離(submit の front-door provenance 書込で実状態を汚さない)。"""
    d = tempfile.mkdtemp(dir=TMPBASE, prefix="de_route_")
    for k in ("DS_DATA_DIR", "RRI_DATA_DIR", "EGL_DATA_DIR"):
        os.environ[k] = d
    return d


def run_pair(entry):
    """1 candidate を2経路で別 temp ledger に admit。同一 ts(submit の正典 ts)で比較。
    返り dict: label / row_direct / row_submit / res_direct / res_submit / has_frontdoor_trace / loop。"""
    import de_submit_route as R
    from egl import de_admission as DEA
    cand = entry["cand"]
    tmpA = tempfile.mktemp(dir=TMPBASE, suffix="_direct.jsonl")
    tmpB = tempfile.mktemp(dir=TMPBASE, suffix="_submit.jsonl")
    # route B(submit) 先 → 正典 ts を抽出(submit がハードコードする ts に直叩きを合わせる)
    resB, trace = R.admit_via_submit(cand, ledger_path=tmpB)
    rowB = _read(tmpB)
    ts = json.loads(rowB)["egl_admission"]["admitted_at"] if rowB.strip() else "2026-07-11T08:00:00"
    # route A(直叩き) 同一 ts
    resA = DEA.admit_design_evidence(dict(cand), ts, ledger_path=tmpB and tmpA)
    rowA = _read(tmpA)
    for t in (tmpA, tmpB):
        if os.path.isfile(t):
            os.unlink(t)
    return {"label": entry["label"], "row_direct": rowA, "row_submit": rowB,
            "res_direct": resA, "res_submit": resB,
            "loop": trace.get("ADMISSION_LOOP_TRACE"),
            "has_frontdoor_trace": bool(trace.get("RRI_ADMISSION_CLASSIFICATION")) and bool(trace.get("DS_THREAD_UPDATE") or not resB.get("admitted"))}


def _diff(a, b):
    if a == b:
        return ""
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            return "first diff @%d: direct=...%r vs submit=...%r" % (i, a[max(0, i - 15):i + 15], b[max(0, i - 15):i + 15])
    return "length differs: direct=%d submit=%d" % (len(a), len(b))


def check():
    real_before = _sha(REAL_LEDGER)
    _hermetic_env()
    red, results = [], []
    for entry in CANDIDATES:
        try:
            r = run_pair(entry)
        except Exception as e:
            red.append("ROUTE_ERROR[%s]: %r" % (entry["label"], e))
            continue
        results.append(r)
        # 同値(最重要): ledger 行が byte 一致(REJECTED は両者とも空行=一致)
        if r["row_direct"] != r["row_submit"]:
            red.append("ROUTE_DIVERGENCE[%s]: ledger 行が不一致 — %s"
                       % (r["label"], _diff(r["row_direct"], r["row_submit"])))
        # result dict(admitted/status)も一致。`ledger`(temp パス)は経路ごとに別 temp ゆえ比較から除外(行 byte が正典)。
        ra = {k: v for k, v in (r["res_direct"] or {}).items() if k != "ledger"}
        rb = {k: v for k, v in (r["res_submit"] or {}).items() if k != "ledger"}
        if ra != rb:
            red.append("RESULT_DIVERGENCE[%s]: %r vs %r" % (r["label"], ra, rb))
        # front-door provenance: submit 経路は RRI 分類→(admission)→DS thread の loop trace を生む(=移行の価値)
        if not r["has_frontdoor_trace"]:
            red.append("NO_FRONTDOOR_PROVENANCE[%s]: submit 経路が RRI/DS trace を生んでいない" % r["label"])
    # sole-writer 不変: 実 DESIGN_EVIDENCE_LEDGER を一切汚していない(temp のみに書いた)
    if _sha(REAL_LEDGER) != real_before:
        red.append("REAL_LEDGER_MUTATED: 実 ledger が harness で変化(sole-writer/hermetic 違反)")
    if red:
        print("DE_ROUTE_EQUIV --check: RED")
        for m in red:
            print("  " + m)
        return 1
    n_admit = sum(1 for r in results if r["res_submit"].get("admitted"))
    print("DE_ROUTE_EQUIV --check: GREEN (ledger-row byte 同値 %d candidate[admit=%d/reject=%d]; "
          "front-door provenance 生成; sole-writer=egl.de_admission 不変; 実 ledger 不汚染; 直叩き未閉塞=並行運用)"
          % (len(results), n_admit, len(results) - n_admit))
    for r in results:
        st = (r["res_submit"] or {}).get("admission_status")
        print("  %-20s route-equal=%s status=%s loop=%s"
              % (r["label"], r["row_direct"] == r["row_submit"], st, r["loop"]))
    return 0


def main(argv):
    return check()   # 検証ハーネス(持続出力なし・gate のみ)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
