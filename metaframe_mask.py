"""MASK_PIPELINE v1 — 決定的な abstraction pipeline(Round B pair design 用)。
concrete incident 表現から domain 固有名詞を除き構造 role token へ置換する。
人間/Claude が incident ごとに手書きしない(=『Claude が上手に抽象化できる』を測らないため)。
固定 procedure。SHA-256 を held-out 選定前に記録する。
"""
import re

VERSION = "MASK_PIPELINE_v1"
# domain 固有名詞 → 構造 role token(ESDE / software / GPU / workflow / data domain 横断)
_TERMS = [
    # ESDE
    (r"v9\.\d+[a-z]?|v10\.\d+|v11\d+|v12\.?\d*|v13\d*", "VERSION"),
    (r"B_Gen", "PARAM"), (r"Q_remaining|Q0|Q値|Q消費|Q reduction", "RESERVE"),
    (r"n_core|n=2|n=5|n≥6", "SIZE"), (r"CID|cid", "UNIT"), (r"label|ラベル", "GROUP"),
    (r"R=0|R>0|R>0参加", "STATE"), (r"phase\+r|phase＋r", "AXIS"), (r"theta|θ", "ANGLE"),
    (r"Fetch|fetch", "READ_OP"), (r"E3|E1|E2|E3_contact", "EVENT"), (r"Layer [AB]|Layer_[AB]", "TRACK"),
    (r"missing_flags|missing比率", "FLAG"), (r"age_factor", "RATIO"), (r"ghost|ghost化|ghost累積", "STALE_ACCUM"),
    (r"S≥0\.20|S>=0\.20|閾値", "THRESHOLD"), (r"認知層|物理層", "LAYER"), (r"one-way firing|片方向発火", "ASYMMETRY"),
    # software / validator
    (r"validator|gate implementation|test\b|tests\b|counterexample|fail-open|audit(or)?", "CHECK"),
    (r"finding(s)?|rework", "FLAGGED_ITEM"),
    # GPU / infra
    (r"vLLM|GPU|VRAM|swap|Sleep Mode|co-serve|model[- ]switch|tensor|KV cache", "COMPONENT"),
    (r"latency|throughput|memory footprint", "PERF_METRIC"),
    # generic
    (r"\b\d{1,3}(\.\d+)?\s?%|\b\d{2,}(\.\d+)?", "NUMBER"),
    (r"Taka|Gemini|GPT|Claude|Code A|Qwen", "ACTOR"),
]


def mask(text):
    """concrete → abstract。domain noun を role token へ。決定的。"""
    s = str(text)
    for pat, tok in _TERMS:
        s = re.sub(pat, tok, s, flags=re.I)
    # 連続 role token の圧縮
    s = re.sub(r"\b(NUMBER)(\s+NUMBER)+\b", "NUMBER", s)
    return s


def abstract_incident(concrete_repr):
    """incident の concrete 表現(pre/tension/distinction/revised)を masking して abstract 表現に。"""
    return mask(concrete_repr)


def pipeline_source():
    """この pipeline の source を返す(SHA-256 固定用)。"""
    import inspect, sys
    return inspect.getsource(sys.modules[__name__])
