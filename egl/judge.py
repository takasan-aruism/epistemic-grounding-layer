"""Gate 4 = Claude-in-loop adjudicator (決定 K-2, CB-5: teacher signal not ground truth)。

FI-3: LLM judge の本務は ENTAILMENT と SCOPE の2 family に縮小(他はコード/scanner)。
AM-11: enum に UNJUDGEABLE/UNRESOLVED。判定不能は DEFER でなく EVIDENCE_INSUFFICIENT へ。
EI-3: judge packet は fragment 単体でなく bounded source context(heading+前後block+fragment)。
EI-6: judge は FRAGMENT_INSUFFICIENT を出せる(手元の観測内での不足申告のみ、自由探索禁止)。
"""
from . import core

F1_VALUES = {"SUPPORTED", "PARTIAL", "NOT_SUPPORTED", "CONTRADICTS", "UNJUDGEABLE"}
F2_VALUES = {"WITHIN", "EXCEEDS", "NARROWER", "DISJOINT", "UNRESOLVED"}


def build_packet(con, candidate):
    """EI-3: bounded source context を組む。normalized observation は保存済みなので構築コストのみ。"""
    packets = []
    for rel_id in candidate.get("evidence_relations", []):
        rel = core.get(con, rel_id)
        frag = core.get(con, rel["from_id"])
        nobs = core.get(con, frag["norm_obs_id"])
        blocks = nobs["blocks"]
        idx = frag["block_index"]
        bounded = {
            "heading": nobs.get("section_heading"),
            "prev_block": blocks[idx - 1] if idx > 0 else None,
            "fragment": frag["excerpt"],
            "next_block": blocks[idx + 1] if idx + 1 < len(blocks) else None,
            "source_class": core.get(con, nobs["source_id"])["source_class"],
        }
        packets.append({"fragment_id": frag["fragment_id"], "bounded_context": bounded})
    return {"candidate_id": candidate["id"], "statement": candidate["statement"],
            "scope": candidate["scope"], "claim_type": candidate["claim_type"],
            "evidence_packets": packets}


class Finding:
    """ENTAILMENT + SCOPE の2 family。common_run_id で単一run相関を後から層別(FI-5)。"""
    def __init__(self, candidate_id, f1, f2, common_run_id, rationale,
                 fragment_sufficient=True, adjudicator="claude"):
        assert f1 in F1_VALUES and f2 in F2_VALUES, (f1, f2)
        self.candidate_id = candidate_id
        self.f1_entailment = f1          # ENTAILMENT family
        self.f2_scope = f2               # SCOPE family
        self.fragment_sufficient = fragment_sufficient  # EI-6
        self.common_run_id = common_run_id
        self.rationale = rationale
        self.adjudicator = adjudicator
        self.teacher_signal = True       # CB-5

    def as_dict(self):
        return {"candidate_id": self.candidate_id, "f1_entailment": self.f1_entailment,
                "f2_scope": self.f2_scope, "fragment_sufficient": self.fragment_sufficient,
                "common_run_id": self.common_run_id, "rationale": self.rationale,
                "adjudicator": self.adjudicator, "teacher_signal": self.teacher_signal}


class ClaudeAdjudicator:
    """Claude(私)が in-loop で判定する境界。findings 辞書を注入する(この walk では driver が用意)。
    実運用では packet を人間/別セッションClaude に提示し finding を受け取る対話ステップになる。"""
    def __init__(self, findings_by_candidate):
        self._f = findings_by_candidate

    def adjudicate(self, packet, common_run_id):
        f = self._f[packet["candidate_id"]]
        return Finding(packet["candidate_id"], f["f1"], f["f2"], common_run_id,
                       f["rationale"], f.get("fragment_sufficient", True))
