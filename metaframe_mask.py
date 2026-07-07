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


# ── MASK_PIPELINE v2 — token 漏れ修正(placeholder token でなく自然 generic 名詞句)──────
# v1 欠陥: ALL-CAPS token(VERSION/STATE/SIZE)を model が parrot し foreign token が answer に漏れる。
# v2: 自然な generic 名詞句へ置換 → echo されても自然に読め、ESDE literal(R=0 等)は消える。
VERSION_V2 = "MASK_PIPELINE_v2"
# v2: DOMAIN 固有名詞のみ generic 名詞句へ。generic 語(audit/finding/validator/latency/check)は残す
# (cross-domain で自然)。冠詞重複は後処理で潰す。
_TERMS_V2 = [
    (r"v9\.\d+[a-z]?|v10\.\d+|v11\d+|v12\.?\d*|v13\d*", "an earlier run"),
    (r"B_Gen", "a derived parameter"), (r"Q_remaining|Q0|Q値|Q消費|Q reduction", "a depletable reserve"),
    (r"n_core", "the size measure"), (r"n=2|n=5|n≥6", "a size category"),
    (r"CidSelfBuffer", "a state buffer"), (r"CID|cid", "a unit"), (r"label|ラベル", "group"),
    (r"R=0[- ]?contaminated", "invalid-subset-contaminated"), (r"R=0 のまま|R=0 混入|R=0", "the invalid subset"),
    (r"R>0参加|R>0", "the valid subset"), (r"phase\+r|phase＋r", "a contributing axis"),
    (r"theta|θ", "an angle value"), (r"Fetch|fetch", "read"),
    (r"E3_contact|E3|E1|E2", "a contact event"),
    (r"Layer [AB]|Layer_[AB]", "a track"), (r"age_factor", "a decay ratio"),
    (r"ghost accumulation|ghost化|ghost累積|ghost", "stale retired elements accumulating"),
    (r"S≥0\.20|S>=0\.20|閾値", "a hard threshold"), (r"認知層|物理層", "a layer"),
    (r"birth-time|birth時|生誕時|birth-mode|birth 方式", "initialization"),
    (r"Step-?0 [Aa]udit", "an audit"),
    (r"one-way firing|片方向発火", "one-directional interaction"),
    (r"vLLM|Sleep Mode|co-serve|model[- ]switch|KV cache", "a component capability"),
    (r"\b\d{1,3}(\.\d+)?\s?%", "some proportion"), (r"\b\d{2,}(\.\d+)?", "some number"),
    (r"Taka|Gemini|GPT|Claude|Code A|Qwen", "a reviewer"),
    (r"apparent[- ]structure", "the apparent version"), (r"grounded[- ]structure", "the grounded version"),
    (r"self-awareness|self-tracking", "genuine self-behavior"),
]


def mask_v2(text):
    s = str(text)
    for pat, rep in _TERMS_V2:
        s = re.sub(pat, rep, s, flags=re.I)
    # 冠詞重複・崩れの後処理(v1 token 漏れの再来を防ぐ)
    s = re.sub(r"\b([Aa])n?\s+(a|an|the|some)\b", r"\2", s)   # "a a/an/the/some" -> 後者
    s = re.sub(r"\b[Tt]he\s+(a|an|some)\b", r"the", s)
    s = re.sub(r"\bsome number(\s+some number)+\b", "some number", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s


def abstract_incident_v2(concrete_repr):
    return mask_v2(concrete_repr)


def pipeline_source():
    """この pipeline の source を返す(SHA-256 固定用)。"""
    import inspect, sys
    return inspect.getsource(sys.modules[__name__])
