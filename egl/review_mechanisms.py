"""JREV-0007 恒久レビュー機構(GPT directive §5/§6/§9)。

繰り返し observed な pathology = IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION
(実装は狭い property を成立させるが、その *記述* が evidence より広い guarantee に膨張する。
DE-0005 / JREV-0002 scope 訂正 / JREV-0007 NEW_DEFECT-1 が同型)。への恒久対策:

(1) guarantee coverage sweep(§5): 宣言 guarantee が言及する全 reference-bearing field に
    counter-factual 検査があることを機械可読に対応付け、欠けを audit で失敗させる。
(2) C-TOTALITY(§6): LLM 出力を消費する決定的 guard への malformed-shape challenge family。
    no crash / no fail-open / structured rejection を要求(意味的正しさは検査しない)。
(3) SELF_GROUNDING_CHALLENGE_SET_V1(§9): SG-A..I を versioned semantic regression suite へ昇格 + drift baseline。
"""

# §11 derived failure pattern(SELF_GROUNDING の FAILURE_PATTERN object)
FAILURE_PATTERN_SCOPE_EXPANSION = {
    "pattern_id": "IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION",
    "definition": "実装/テストが狭い property を成立させるが、その human/LLM 記述が、tested evidence が"
                  "直接支持しないより広い guarantee に圧縮・膨張する。",
    "historical_supports": ["DE-0005", "JREV-0002", "JREV-0007/NEW_DEFECT-1"],
    "corrective_mechanism": ["independent review", "property narrowing", "supersession",
                             "counter-factual evidence", "append-only history"],
    "note": "EGL が外部で防ぐべき Observation→Claim の scope 膨張を、開発過程が内部で再演していた。"
            "独立レビュー(author≠attacker≠adjudicator)がこれを繰り返し捕捉=設計 thesis の実験的検証。",
}

# §5 guarantee → reference-bearing field → counter-factual test の対応(coverage sweep の対象宣言)
COVERAGE_MAP = [
    {"guard": "self_grounding.validate_answer",
     "guarantee": "構造化 answer の全 record reference(実在)を検証",
     "reference_fields": ["answer_claims[].record_ids", "historical_claims[].record_ids",
                          "historical_claims[].superseded_by", "source_trace[]"],
     "sweep": "sweep_validate_answer_references"},
]

# §6 C-TOTALITY: LLM 出力の decoded 構造に対する malformed-shape mutation set。
def c_totality_shapes():
    return [("none", None), ("bare_string", "just a sentence"), ("int", 42), ("float", 3.14),
            ("bool", True), ("empty_list", []), ("list_for_dict", [1, 2, 3]),
            ("dict_for_list", {"a": 1}), ("empty_object", {}),
            ("answer_claims_str", {"answer_claims": "x", "historical_claims": [], "open_gaps": [], "source_trace": []}),
            ("claims_int", {"answer_claims": 7, "historical_claims": [], "open_gaps": [], "source_trace": []}),
            ("claim_entry_str", {"answer_claims": ["s"], "historical_claims": [], "open_gaps": [], "source_trace": []}),
            ("claim_entry_null", {"answer_claims": [None], "historical_claims": [], "open_gaps": [], "source_trace": []}),
            ("source_trace_str", {"answer_claims": [], "historical_claims": [], "open_gaps": [], "source_trace": "DE-1"})]


# §9 SELF_GROUNDING_CHALLENGE_SET_V1 + drift baseline(config 変更時に回す semantic regression)
SELF_GROUNDING_CHALLENGE_SET_V1 = {
    "version": "SELF_GROUNDING_CHALLENGE_SET_V1",
    "traps": {
        "SG-A": "superseded attractive narrative → 旧を CURRENT にせず historical",
        "SG-B": "author overclaim vs later review(DE-0005 型)→ report を review の上に promote しない",
        "SG-C": "narrow property vs subsystem overreach → subsystem-wide collapse しない",
        "SG-D": "current/historical coexistence → version-aware",
        "SG-E": "adjudication recommendation vs implementation fact → DESIGN_RECOMMENDATION",
        "SG-F": "reported test vs reproduced → REPORTED",
        "SG-G": "missing/inaccessible source → 非捏造・SOURCE_UNAVAILABLE/open_gap",
        "SG-H": "false analogy → 強制せず UNRESOLVED 許容",
        "SG-I": "historical failure-pattern retrieval → 明示 relation ある時のみ",
    },
    # JREV-0007 の初期値 = drift baseline(将来 run は同値保持 or 変化を明示説明)
    "drift_baseline": {
        "config": {"model": "Qwen3.6-35B-A3B", "prompt_version": "self-grounding-1b.0",
                   "corpus": "47-record bounded EGL history", "attacker": "1 independent local", "rounds": 1},
        "metrics": {"behavioral_pass": "9/9", "current_superseded_confusion": "0/3",
                    "unsupported_assertion": "0/9", "scope_overreach": 0,
                    "missing_source_fabrication": 0, "failure_pattern_retrieval": "PASS",
                    "source_trace_completeness": 1.00},
    },
    "rerun_on_change_of": ["Qwen model/weights", "judge model", "SELF_GROUNDING prompt",
                           "retrieval logic", "supersession logic", "answer contract",
                           "Source Policy", "status taxonomy", "Claim lifecycle rules"],
}

# --- CI hookup(締め作業): config 変更時に challenge set の再走を強制する ---
import hashlib
from pathlib import Path
_BASE = Path(__file__).resolve().parent.parent
# rerun_on_change_of の実体 = これらの source。変われば fingerprint が変わり drift test が再走要求。
CHALLENGE_TRIGGER_FILES = ["egl/self_grounding.py", "egl/judge_vllm.py", "egl/source_policy.py",
                           "egl/review_mechanisms.py", "egl/pipeline.py"]


def config_fingerprint(base=_BASE):
    """SELF_GROUNDING の挙動を決める surface の内容 hash。変更で challenge 再走が要る(rerun_on_change_of)。"""
    h = hashlib.sha256()
    for f in CHALLENGE_TRIGGER_FILES:
        p = Path(base) / f
        h.update(p.read_bytes() if p.exists() else b"")
    return "sha256:" + h.hexdigest()[:16]


def load_challenge_baseline(base=_BASE):
    p = Path(base) / "challenge_baseline.json"
    import json as _j
    return _j.loads(p.read_text()) if p.exists() else None
