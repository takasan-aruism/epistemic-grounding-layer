"""2DER Process Optimizer — deterministic contracts (§11 versioning / §12 preservation review / §13 native capability).

Process Optimizer は role であって責任系ではない(DD-ARCH-4, EGL DE-0077)。SHALL NOT: research /
knowledge admission / self-adjudication / auto-apply。ここは Optimizer 候補を「自動採用してよいか」を
決める deterministic gate 群(LLM 判断でなく構造で fail-closed)。
"""
import json
from pathlib import Path

E = Path(__file__).resolve().parent
PVERDICTS = {"PRESERVED", "WEAKENED", "UNKNOWN"}
COVERAGE = {"ESTABLISHED", "NOT_ESTABLISHED"}


# ── §11 PROCESS_PROPERTY_SET versioning ───────────────────────────────────────
def load_property_set_versions():
    p = E / "process_property_set.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def current_property_set():
    vs = load_property_set_versions()
    return max(vs, key=lambda v: v["process_property_set_version"]) if vs else None


def property_introduced_version():
    """property_id -> それが導入された最小 version。"""
    out = {}
    for v in sorted(load_property_set_versions(), key=lambda x: x["process_property_set_version"]):
        for pid in v.get("introduced", []):
            out.setdefault(pid, v["process_property_set_version"])
    return out


def review_candidates(adopted_optimizations):
    """§11: 新 property が後から導入された時、旧 property-set version で preservation-review された
    optimization を REVIEW_REQUIRED として列挙。adopted_optimizations = [{id, preserved_against_property_set_version}]。
    返り: [{optimization_id, preserved_against, current_version, unreviewed_properties}]。"""
    cur = current_property_set()
    if not cur:
        return []
    cur_v = cur["process_property_set_version"]
    intro = property_introduced_version()
    out = []
    for opt in adopted_optimizations:
        pa = opt.get("preserved_against_property_set_version")
        if pa is None or pa < cur_v:
            unreviewed = [pid for pid, iv in intro.items() if (pa is None or iv > pa)]
            if unreviewed:
                out.append({"optimization_id": opt.get("id"), "preserved_against": pa,
                            "current_version": cur_v, "unreviewed_properties": sorted(unreviewed)})
    return out


# ── §12 property preservation review contract ─────────────────────────────────
def validate_preservation_review(review, property_set_version=None):
    """§12: Optimizer は self-adjudicate しない(別 actor が review)。全 property に entry 必須。
    missing != PRESERVED。WEAKENED/UNKNOWN があれば auto-adopt 不可。malformed は fail-closed。
    PRESERVED は mechanism_ref 必須。返り: {auto_adoptable: bool, problems: [...], missing: [...]}。"""
    if not isinstance(review, dict):
        return {"auto_adoptable": False, "problems": ["review is not a dict (fail-closed)"], "missing": []}
    entries = review.get("property_verdicts")
    if not isinstance(entries, list):
        return {"auto_adoptable": False, "problems": ["property_verdicts must be a list (fail-closed)"], "missing": []}
    v = property_set_version or (current_property_set() or {}).get("process_property_set_version")
    ver = next((x for x in load_property_set_versions() if x["process_property_set_version"] == v), None)
    required = {p["id"] for p in (ver or current_property_set() or {}).get("properties", [])}
    problems, seen = [], {}
    for e in entries:
        if not isinstance(e, dict) or not e.get("property_id"):
            return {"auto_adoptable": False, "problems": ["verdict entry malformed (fail-closed)"], "missing": []}
        pid, verdict = e.get("property_id"), e.get("verdict")
        if verdict not in PVERDICTS:
            return {"auto_adoptable": False, "problems": [f"verdict {verdict!r} 不正 (fail-closed)"], "missing": []}
        if verdict == "PRESERVED" and not e.get("mechanism_ref"):
            problems.append(f"{pid}: PRESERVED は mechanism_ref 必須")
        seen[pid] = verdict
    missing = sorted(required - set(seen))               # missing entry != PRESERVED
    if missing:
        problems.append(f"未 review property: {missing} (missing != PRESERVED)")
    weakened = [p for p, vd in seen.items() if vd == "WEAKENED"]
    unknown = [p for p, vd in seen.items() if vd == "UNKNOWN"]
    if weakened:
        problems.append(f"WEAKENED property {weakened} → 自動採用不可")
    if unknown:
        problems.append(f"UNKNOWN property {unknown} → 自動採用不可")
    return {"auto_adoptable": not problems, "problems": problems, "missing": missing}


# ── §13 native capability coverage ────────────────────────────────────────────
def validate_native_capability(nc):
    """§13: LLM self-report 禁止。ESTABLISHED は valid egl_record_ref を要する。無ければ NOT_ESTABLISHED。
    NOT_ESTABLISHED は RESEARCH_NEED candidate。返り: {effective_status, research_need: bool, problems}。"""
    if not isinstance(nc, dict):
        return {"effective_status": "NOT_ESTABLISHED", "research_need": True, "problems": ["nc not a dict (fail-closed)"]}
    for f in ("coverage_status", "component", "blocked_property"):
        if not nc.get(f):
            return {"effective_status": "NOT_ESTABLISHED", "research_need": True, "problems": [f"{f} 必須"]}
    st = nc.get("coverage_status")
    if st not in COVERAGE:
        return {"effective_status": "NOT_ESTABLISHED", "research_need": True, "problems": [f"coverage_status {st!r} 不正"]}
    ref = nc.get("egl_record_ref")
    if st == "ESTABLISHED" and not (isinstance(ref, str) and ref.strip()):
        # ESTABLISHED を主張するが EGL ref が無い → 無効化して NOT_ESTABLISHED 扱い(self-report 禁止)
        return {"effective_status": "NOT_ESTABLISHED", "research_need": True,
                "problems": ["ESTABLISHED は valid egl_record_ref を要する → self-report は NOT_ESTABLISHED 扱い"]}
    if st == "ESTABLISHED":
        return {"effective_status": "ESTABLISHED", "research_need": False, "problems": []}
    return {"effective_status": "NOT_ESTABLISHED", "research_need": True, "problems": []}
