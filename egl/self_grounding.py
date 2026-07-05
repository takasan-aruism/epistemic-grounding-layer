"""SELF_GROUNDING(JREV-0006 directive §3-16)— EGL が自らの開発史を最初の実 system-level
epistemic workload にする。EGL は自分が『今何を信じ / なぜ / 以前は何を / 何が supersede したか /
未検証は何か / どの過去 failure pattern が現設計に似るか』を、自分の台帳から再構築できるか。

first slice: bounded corpus = DESIGN_EVIDENCE_LEDGER + REVIEW_LEDGER(構造化済み self-history 記録)。
retrieval → real Qwen が構造化 answer(answer_claims/historical_claims/open_gaps/source_trace)を生成。
判定は NL 類似でなく **構造化 answer** を評価。2トラック: hermetic(構造・決定的)+ SELF_GROUNDING(意味・LLM)。

authority は contextual(§6): DESIGN_LEDGER=決定が記録された証拠(実装真実でない)/ REVIEW_LEDGER=
review verdict の証拠(実装挙動が真とは限らない)。author says implemented ≠ counter-factual test showed。
"""
import json, re, urllib.request, urllib.error, socket
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# §6 self-history source classes(authority は contextual、単独の権威順位でない)
SOURCE_CLASSES = {
    "DESIGN_LEDGER": "設計決定が記録された強い証拠(実装が真とは限らない)",
    "REVIEW_LEDGER": "review verdict の強い証拠(実装挙動が真とは限らない)",
}
# §7 claim classes
CLAIM_CLASSES = ["IMPLEMENTATION_FACT", "TEST_RESULT", "REVIEW_FINDING", "DESIGN_DECISION",
                 "CURRENT_SYSTEM_STATE", "HISTORICAL_STATE", "FAILURE_PATTERN"]

# §5 bounded corpus(全 project file でなく、期待史が human-reviewable な範囲)
CORPUS_FILES = [
    ("DESIGN_EVIDENCE_LEDGER.jsonl", "DESIGN_LEDGER"),
    ("REVIEW_LEDGER.jsonl", "REVIEW_LEDGER"),
]


def load_corpus(base=BASE):
    """ledger jsonl を self-history 記録へ。ordinal=行順=時系列(supersession 判定の下地)。"""
    records = []
    for fname, sclass in CORPUS_FILES:
        p = Path(base) / fname
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rid = obj.get("design_evidence_id") or obj.get("review_id") or f"{sclass}-{i}"
            records.append({"record_id": rid, "source_class": sclass, "ordinal": len(records),
                            "fields": obj, "text": json.dumps(obj, ensure_ascii=False)})
    return records


_RULE_TOKEN = re.compile(r"\b(R\d+|DE-\d{4}|JREV-\d{4}|ACQ-\d+[a-z]?|H\d[a-z]?|M\d|L\d|F\b|AB-\d+)\b")


def detect_supersession(records):
    """『supersede/撤回/解除/否定』を述べる後続記録が、参照する先行 rule token を superseded にする
    (heuristic、§SG-D の version-aware answer の下地)。返り: {superseded_token: [{by, note}]}。"""
    superseded = {}
    for r in records:
        t = r["text"]
        # 保守的: 明示的な上書き語のみ(REJECTED 等の verdict 語は over-flag するので使わない=heuristic 残余)
        if not re.search(r"supersede|撤回|廃止", t, re.I):
            continue
        for m in set(_RULE_TOKEN.findall(t)):
            if m == r["record_id"]:
                continue
            superseded.setdefault(m, []).append({"by": r["record_id"], "ordinal": r["ordinal"]})
    return superseded


def retrieve(question, records, k=8):
    """naive keyword retrieval(baseline)。question の語 ∩ record text で採点。上位 k。"""
    q = set(re.findall(r"[A-Za-z0-9\-_]+|[ぁ-んァ-ヶ一-龠]+", question.lower()))
    q = {w for w in q if len(w) >= 2}
    scored = []
    for r in records:
        low = r["text"].lower()
        score = sum(1 for w in q if w in low)
        # id 直接言及は強い信号
        for tok in _RULE_TOKEN.findall(question):
            if tok.lower() in low:
                score += 3
        if score:
            scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], x[1]["ordinal"]))
    return [r for _, r in scored[:k]]


# §8 Q1-Q16(凍結 benchmark)
BENCHMARK = [
    ("Q1", "What is the current Phase 1a completion claim?"),
    ("Q2", "What does Phase 1a explicitly NOT guarantee?"),
    ("Q3", "What was the DE-0005 failure?"),
    ("Q4", "List every confirmed case where an upstream summary was replaced by a lower primitive that later proved self-reportable or forgeable."),
    ("Q5", "What is the current root of trust for search-leg completion?"),
    ("Q6", "What is still NOT verified about leg authenticity?"),
    ("Q7", "Explain the difference between ABSENCE, NEGATIVE claim, and explicit negative specification."),
    ("Q8", "What did R7 change?"),
    ("Q9", "What did R8 change?"),
    ("Q10", "What were the three JREV-0005 pre-remediation defects?"),
    ("Q11", "What did DE-0036 change in each case?"),
    ("Q12", "What does the current Gate4 actually guarantee, and what does it NOT guarantee?"),
    ("Q13", "What does ETB structurally block? Does it guarantee that all prompt injection is detected?"),
    ("Q14", "Why is a fabricated plausible official-looking document still dangerous after Gate4 + ETB?"),
    ("Q15", "What are the current blockers before autonomous RD activation?"),
    ("Q16", "Which current unresolved design boundary most closely resembles a previously observed EGL failure pattern, and why?"),
]

# §9 構造化 answer contract(NL は rendering 層。benchmark は構造化 answer を先に評価)
ANSWER_KEYS = ["answer_claims", "historical_claims", "open_gaps", "source_trace"]

_ENDPOINT = "http://localhost:8005/v1/chat/completions"
_MODEL = "Qwen3.6-35B-A3B"
SG_PROMPT_VERSION = "self-grounding-1b.0"

_SYSTEM = (
    "You reconstruct EGL's epistemic state from its own development-history records. "
    "You are given RECORDS (each with record_id, source_class, ordinal). RULES: "
    "(1) Use ONLY the provided records; do not use outside knowledge. "
    "(2) A record marked as SUPERSEDED must NOT be presented as current belief — put it in historical_claims. "
    "(3) Do NOT broaden a narrow/property-scoped verdict into a subsystem-wide guarantee. "
    "(4) source_class DESIGN_LEDGER = a design decision was recorded (not that implementation is true); "
    "REVIEW_LEDGER = a review verdict (not that behaviour is externally true). "
    "(5) Every substantive claim in answer_claims/historical_claims MUST cite at least one record_id in source_trace. "
    "(6) List relevant NOT_VERIFIED / DEFERRED / known non-guarantees in open_gaps. "
    "Return ONLY a JSON object with keys: answer_claims (list of {text, record_ids, currentness:CURRENT|HISTORICAL}), "
    "historical_claims (list of {text, record_ids, superseded_by}), open_gaps (list of strings), "
    "source_trace (list of record_id)."
)


def _vllm_chat(prompt, max_tokens=1200, system=None):
    body = json.dumps({"model": _MODEL, "temperature": 0, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": system or _SYSTEM},
                                    {"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(_ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


def _extract_json(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(text[i:j + 1])
    except Exception:
        return None


def _records_block(records, superseded, limit=1400):
    lines = []
    for r in records:
        sup = superseded.get(r["record_id"])
        tag = f" SUPERSEDED_BY={[s['by'] for s in sup]}" if sup else ""
        body = r["text"]
        if len(body) > limit:
            body = body[:limit] + "…"
        lines.append(f"[{r['record_id']} source_class={r['source_class']} ordinal={r['ordinal']}{tag}]\n{body}")
    return "\n\n".join(lines)


def answer_question(question, records=None, superseded=None, system=None, k=8, record_char_limit=1400,
                    max_tokens=1200):
    """baseline: retrieve → Qwen が構造化 answer を生成。返り: (answer_dict|None, retrieved_ids, raw)。
    system: answerer の system prompt override(ESDE 等 別 workload 用。既定=EGL self-history)。"""
    records = records if records is not None else load_corpus()
    superseded = superseded if superseded is not None else detect_supersession(records)
    hits = retrieve(question, records, k=k)
    prompt = (f"QUESTION: {question}\n\nRECORDS:\n{_records_block(hits, superseded, record_char_limit)}\n\n"
              "Return the JSON answer object now.")
    try:
        raw = _vllm_chat(prompt, max_tokens=max_tokens, system=system)
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as e:
        return None, [r["record_id"] for r in hits], f"vllm_unreachable:{e}"
    return _extract_json(raw), [r["record_id"] for r in hits], raw


def _supersession_ref_problem(ref, ids):
    """AB-0021(1): supersession reference を検証。3型を許容——外部 record による置換(RECORD)、
    同一 record 内の自己訂正(INLINE: record 内 inline 訂正で discrete 後継 record が無い場合、ESDE で実在)、
    legacy な record_id 文字列。id の実在を要求(INLINE は locator 必須)。"""
    if isinstance(ref, str):
        return None if ref in ids else f"unknown record_id {ref!r}"
    if isinstance(ref, dict):
        t = ref.get("type")
        if t == "RECORD":
            return None if ref.get("id") in ids else f"RECORD ref unknown id {ref.get('id')!r}"
        if t == "INLINE":
            if ref.get("record_id") not in ids:
                return f"INLINE ref unknown record_id {ref.get('record_id')!r}"
            loc = ref.get("locator")
            return None if isinstance(loc, str) and loc.strip() else "INLINE ref missing locator"
        return f"unknown supersession ref type {t!r}"
    return f"supersession ref must be str/RECORD/INLINE, got {type(ref).__name__}"


def validate_answer(ans, corpus_ids):
    """§9 contract 検証(構造・決定的、hermetic)。返り: {ok, problems, metrics}。
    JREV-0007: **全 citation class**(claim.record_ids / historical.superseded_by / source_trace)を検証。
    total 関数(非 dict claim で crash せず problem)。currentness placement の決定的整合検査。"""
    problems = []
    if not isinstance(ans, dict):
        return {"ok": False, "problems": ["not a JSON object"], "metrics": {}}
    for k in ANSWER_KEYS:
        if k not in ans:
            problems.append(f"missing key: {k}")
    ids = set(corpus_ids)
    answer_c = ans.get("answer_claims") or []
    hist_c = ans.get("historical_claims") or []
    # C-TOTALITY(JREV-0007 §6): claim collections が list でない malformed 出力でも crash しない(total)。
    if not isinstance(answer_c, list):
        problems.append(f"answer_claims is not a list: {type(answer_c).__name__}"); answer_c = []
    if not isinstance(hist_c, list):
        problems.append(f"historical_claims is not a list: {type(hist_c).__name__}"); hist_c = []
    st = ans.get("source_trace") or []
    if not isinstance(st, list):
        problems.append(f"source_trace is not a list: {type(st).__name__}"); st = []
    traced = 0
    total = 0
    for c in (answer_c + hist_c):
        total += 1
        if not isinstance(c, dict):            # NEW_DEFECT-2: 非 dict でも crash せず problem 化(total)
            problems.append(f"claim entry is not an object: {c!r}")
            continue
        cids = c.get("record_ids")
        if cids is None or cids == []:
            problems.append("answer claim with empty record_ids (unsupported assertion)")
            continue
        if not isinstance(cids, list):
            problems.append(f"record_ids is not a list: {cids!r}")
            continue
        unknown = [x for x in cids if x not in ids]
        if unknown:
            problems.append(f"answer claim cites unknown record_id(s): {unknown}")
        else:
            traced += 1
    # NEW_DEFECT-1: superseded_by も load-bearing な citation class(supersede 証拠を名指す)ゆえ検証
    for h in hist_c:
        if not isinstance(h, dict):
            continue
        sb = h.get("superseded_by")
        if sb is None:
            continue
        if not isinstance(sb, list):           # bare string は top-level 不正(coerce は AB-0021(2), 後段)
            problems.append(f"superseded_by is not a list (AB-0021: list of RECORD/INLINE refs or record_ids): {sb!r}")
            continue
        for ref in sb:                          # AB-0021(1): 各 ref を RECORD/INLINE/legacy-string で検証
            prob = _supersession_ref_problem(ref, ids)
            if prob:
                problems.append(f"superseded_by ref invalid: {prob}")
    # scope-clarity: currentness placement の決定的整合(明白な誤配置を検出。意味的正しさは非保証)
    for c in answer_c:
        if isinstance(c, dict) and c.get("currentness") == "HISTORICAL":
            problems.append("answer_claims entry labeled currentness=HISTORICAL (belongs in historical_claims)")
    bad_trace = [x for x in st if x not in ids]
    if bad_trace:
        problems.append(f"source_trace has unknown ids: {bad_trace}")
    metrics = {"n_answer_claims": len(answer_c), "n_historical_claims": len(hist_c),
               "n_open_gaps": len(ans.get("open_gaps") or []),
               "source_trace_completeness": (traced / total) if total else 0.0}
    return {"ok": not problems, "problems": problems, "metrics": metrics}
