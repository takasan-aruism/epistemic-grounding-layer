"""Phase 1b — Source Policy / Source Qualification / Policy Matcher
(docs/phase-1b-acquisition-boundary.md §3,§5,§11,§14,§15)。

AB-1 の核: required_source_kind(SearchPlan の *要求*)と observed_source_kind(取得した Source の
provenance から評価した *実際の種別*)を分ける。coverage は取得成功でなく『observed が required に
policy 下で一致』で満たされる。qualify は code 由来の *上界候補*(LLM は confirm/downgrade/unresolved
のみ、elevate 不可 = §11 safe-direction)。
"""
from urllib.parse import urlparse
from . import core

# §12/§5 source kind controlled vocabulary(observation_kind とは別軸: source の *種別*)
SOURCE_KINDS = {
    "FORMAL_SPEC", "OFFICIAL_DOCS", "OFFICIAL_REPOSITORY", "OFFICIAL_RELEASE", "OFFICIAL_ISSUE",
    "REPRODUCIBLE_RUN", "REPRODUCTION_RUN", "PRIMARY_RESEARCH",
    "INDEPENDENT_BENCHMARK", "TECHNICAL_REPORT", "COMMUNITY_REPORT", "OPERATIONAL_REPORT",
    "PRIVATE_GUIDE", "UNKNOWN",
}

# source_class(PRIMARY/SECONDARY/GENERATED)への写像。UNKNOWN を PRIMARY と騙らない(安全側)。
_PRIMARY_KINDS = {"FORMAL_SPEC", "OFFICIAL_DOCS", "OFFICIAL_REPOSITORY", "OFFICIAL_RELEASE",
                  "OFFICIAL_ISSUE", "REPRODUCIBLE_RUN", "REPRODUCTION_RUN", "PRIMARY_RESEARCH"}

def source_class_for(observed_kind):
    if observed_kind in _PRIMARY_KINDS:
        return "PRIMARY"
    return "SECONDARY"          # UNKNOWN / community / private / benchmark 等は PRIMARY にしない


# §14 versioned ledger object。SOFTWARE_TECHNICAL v1(§5.1 / §15 coverage rules)。
SOFTWARE_TECHNICAL_V1 = {
    "source_policy_id": "SPOL-SOFTWARE-0001", "profile": "SOFTWARE_TECHNICAL", "version": 1,
    "preferred_classes": ["FORMAL_SPEC", "OFFICIAL_DOCS", "OFFICIAL_REPOSITORY", "OFFICIAL_RELEASE",
                          "OFFICIAL_ISSUE", "REPRODUCIBLE_RUN", "PRIMARY_RESEARCH"],
    "supplementary_classes": ["INDEPENDENT_BENCHMARK", "TECHNICAL_REPORT", "COMMUNITY_REPORT"],
    "discovery_classes": ["SEARCH_ENGINE", "REPOSITORY_SEARCH", "COMMON_CRAWL", "COMMUNITY"],
    # §15 coverage requirements(小さい明示ルール)
    "coverage_requirements": {
        "compatibility_exists": {"any_of": ["OFFICIAL_DOCS", "OFFICIAL_REPOSITORY", "OFFICIAL_RELEASE"]},
        "operational_success": {"any_of": ["REPRODUCTION_RUN", "REPRODUCIBLE_RUN"],
                                "or_independent": {"kind": "OPERATIONAL_REPORT", "n": 2}},
        "not_found": {"all_of": ["OFFICIAL_DOCS", "OFFICIAL_REPOSITORY", "OFFICIAL_ISSUE"]},
    },
}
POLICIES = {SOFTWARE_TECHNICAL_V1["source_policy_id"]: SOFTWARE_TECHNICAL_V1}


def mk_source_policy(run, policy):
    """Source Policy を versioned ledger object として記録(§14)。SearchPlan/LegIntent が
    source_policy_id + version を参照 → 歴史的再構築(ACQ-8)。"""
    p = dict(policy)
    p["id"] = core.SELF
    return core.append_event(run, "CREATE", "SourcePolicy", None, p, new_prefix="SPOL")


# §11 最小 Entity Registry: machine-observable provenance(locator host/path)→ (entity, source_kind)。
# code 由来の候補上界。registry 不明は UNKNOWN(強い種別を code が捏造しない)。
ENTITY_REGISTRY = [
    {"host": "github.com", "path": "vllm-project/vllm", "entity": "vLLM", "kind": "OFFICIAL_REPOSITORY"},
    {"host": "github.com", "path": "huggingface/", "entity": None, "kind": "OFFICIAL_REPOSITORY"},
    {"host": "docs.vllm.ai", "path": "", "entity": "vLLM", "kind": "OFFICIAL_DOCS"},
    {"host": "huggingface.co", "path": "", "entity": None, "kind": "OFFICIAL_DOCS"},
]


def qualify_locator(locator, adapter=None, provenance=None):
    """AB-1: 取得した source の provenance から observed_source_kind 候補を評価(code 上界)。
    registry に無い host は UNKNOWN(=required を満たせない安全側)。将来は adapter provenance
    (git commit/path 等)や entity registry 拡張で精緻化。"""
    host, path = "", ""
    if locator:
        u = urlparse(locator if "//" in locator else "//" + locator)
        host = (u.hostname or "").lower()
        path = (u.path or "").lstrip("/")
    for r in ENTITY_REGISTRY:
        if host == r["host"] and path.startswith(r["path"]):
            return r["kind"], r["entity"]
    return "UNKNOWN", None


def policy_match(required_source_kind, observed_source_kind, policy=None):
    """AB-1 Policy Matcher: observed が required を policy 下で満たすか。
    first slice は厳密一致(richer substitution — 例: OFFICIAL_RELEASE が OFFICIAL_DOCS を満たす等 —
    は後続で policy.coverage_requirements 駆動にする)。observed=UNKNOWN は決して満たさない。"""
    if observed_source_kind in (None, "UNKNOWN"):
        return False
    return observed_source_kind == required_source_kind
