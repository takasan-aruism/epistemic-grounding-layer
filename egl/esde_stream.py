"""Operational Stream #1 — ESDE(Taka phase-transition directive 2026-07-06)。

EGL を人工 benchmark でなく **ESDE の最新研究**の調査に実運用する初の本格試験。EGL が ESDE に対し
「現在何が分かっているか / 昔は何を信じていたか / 何が撤回されたか / 何がまだ未確認か / 今の問題は
過去のどの失敗に似ているか」を正しく再構成できるかを測る。

規律(directive §5): author report や綺麗な現在の説明を current truth にしない。
**観測 / 推論 / 仮説 / 設計判断** を混ぜない。CURRENT / HISTORICAL-SUPERSEDED / OPEN-GAP /
REVIEW-FINDING / FAILURE-PATTERN を分離。gold key は人工生成せず独立 adjudication 確定の結果から。

corpus(bounded, directive §4-5): ESDE の memory 群(39 file)= 既に構造化された self-history。
source_class は prefix から contextual に(project/feedback/reference/index)。全 ESDE 履歴の大量 ingest はしない。
"""
from pathlib import Path
from . import self_grounding as SG

ESDE_MEMORY = Path("/home/takasan/.claude/projects/-home-takasan-esde-ESDE-Research/memory")

# directive §6: contextual source classes(単独の権威順位でない)
ESDE_SOURCE_CLASSES = {
    "PROJECT_STATE": "project_* = ある版/実験の到達状態が記録された(現行性は要判定)",
    "REVIEW_FINDING": "feedback_* = 規律/レビュー知見(何を主張してよいかの上限・失敗の教訓)",
    "SPECIFICATION": "reference_* = 技術仕様/公理/正式参照",
    "INDEX": "index_* = 索引(retrieval の地図であって事実の ground でない)",
}
_PREFIX = {"project": "PROJECT_STATE", "feedback": "REVIEW_FINDING",
           "reference": "SPECIFICATION", "index": "INDEX"}


def load_esde_corpus(mem=ESDE_MEMORY):
    """ESDE memory .md を self-history 記録へ。record_id=filename stem。source_class=prefix。"""
    records = []
    for p in sorted(Path(mem).glob("*.md")):
        if p.name == "MEMORY.md":
            continue
        stem = p.stem
        pref = stem.split("_", 1)[0]
        sclass = _PREFIX.get(pref, "PROJECT_STATE")
        records.append({"record_id": stem, "source_class": sclass, "ordinal": len(records),
                        "fields": {"file": p.name}, "text": p.read_text(errors="replace")})
    return records


# directive §5: observation/inference/hypothesis/design-decision を分けさせる ESDE 用 system prompt
ESDE_SYSTEM = (
    "You reconstruct the epistemic state of the ESDE research project from its own memory records "
    "(each with record_id, source_class). RULES: "
    "(1) Use ONLY the provided records; no outside knowledge. "
    "(2) NEVER take an author's clean current explanation as external truth. Separate epistemic kinds: "
    "tag each answer claim with epistemic_kind = OBSERVATION (a direct measured/run result), "
    "INFERENCE (interpretation drawn from results), HYPOTHESIS (proposed, not established), or "
    "DESIGN_DECISION (a chosen design/discipline). Do NOT present an INFERENCE as an OBSERVATION. "
    "(3) A claim that a later record CORRECTED or RETRACTED (e.g. an initial '床内' result later found to "
    "be a measurement artifact) MUST go in historical_claims, not answer_claims. "
    "(4) Respect stated claim ceilings (e.g. '対応がweight軌跡を方向づけたまで') — do not broaden them. "
    "(5) Every claim in answer_claims/historical_claims MUST cite record_id(s) in source_trace. "
    "(6) Put NOT_VERIFIED / open questions / next-step-pending items in open_gaps. "
    "Return ONLY a JSON object: answer_claims (list of {text, record_ids, currentness:CURRENT|HISTORICAL, "
    "epistemic_kind}), historical_claims (list of {text, record_ids, superseded_by}), "
    "open_gaps (list of strings), source_trace (list of record_id)."
)

# directive §6: 初期 operational RQ(実 ESDE 資料を読んだ結果に基づき置換可・理由記録)
ESDE_RQS = [
    ("RQ1", "現在の v1304 系列の最新到達点は何か(何が current で何が superseded か)。"),
    ("RQ2", "v1304c の直接観測結果は何で、何がまだ推論か(観測と推論を分離せよ)。"),
    ("RQ3", "rarity premise shift(前提ずれ)を直接支持する evidence は何か。"),
    ("RQ4", "weight 軌跡に memory が宿るという解釈を、直接支持する結果と、そこからの推論に分離せよ。"),
    ("RQ5", "v12 M5 の kernel drift / survival relation は現在どこまで有効か。"),
    ("RQ6", "attention center の現在の未測定軸は何か(open gap)。"),
    ("RQ7", "lens dependency / population definition に残る未保証は何か。"),
    ("RQ8", "過去に small-seed result を mechanism へ拡張して過大解釈した事例はあるか(failure pattern)。"),
    ("RQ9", "NOW observation と historical aggregation の分離に関連する過去 finding は何か。"),
    ("RQ10", "次 experiment に再発し得る過去 FAILURE_PATTERN は何か。"),
]


def answer_esde(question, records=None, superseded=None):
    records = records if records is not None else load_esde_corpus()
    superseded = superseded if superseded is not None else SG.detect_supersession(records)
    return SG.answer_question(question, records, superseded, system=ESDE_SYSTEM,
                             k=8, record_char_limit=2600, max_tokens=1500)


def measure(ans, corpus_ids):
    """directive §7 metrics の baseline 計測(構造・決定的な分)。意味 metric は独立 adjudication で。"""
    v = SG.validate_answer(ans, corpus_ids)
    obs = infer = 0
    for c in (ans.get("answer_claims") or []) if isinstance(ans, dict) else []:
        if isinstance(c, dict):
            if c.get("epistemic_kind") == "OBSERVATION":
                obs += 1
            elif c.get("epistemic_kind") == "INFERENCE":
                infer += 1
    m = dict(v["metrics"])
    m.update({"contract_ok": v["ok"], "n_observation": obs, "n_inference": infer,
              "problems": v["problems"][:3]})
    return m
