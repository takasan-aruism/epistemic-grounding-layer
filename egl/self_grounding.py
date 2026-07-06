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
    "source_trace (list of record_id). "
    "superseded_by must be a list of record_ids only (or {\"type\":\"INLINE\",\"record_id\":...,\"locator\":...} "
    "for a correction inside the same record); NEVER write explanatory prose in superseded_by. If no valid "
    "superseding record exists, use [] and explain the relation in the claim text or open_gaps."
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
    """§9 contract 検証(構造・決定的、hermetic、total)。
    AB-0022(Taka 裁定): 失敗を **3 直交軸** に分離して返す——
      M1 GROUNDING_INTEGRITY: record ref 実在 / 捏造なし / substantive claim に source trace。
      M2 SEMANTIC_PLACEMENT: current/historical・supersession の *配置* が正しいか。
      M3 FORMAT_ADHERENCE: schema 型 / list vs scalar / enum / required field。
    contract_ok は M1&&M2&&M3 の derived aggregate(分析では M1/M2/M3 を別表示すること)。
    AB-0021(2): bare string superseded_by が *実在 record_id に解決できる時のみ* singleton list に safe coerce
    (canonicalize と同層の表記正規化)。coerce は coercions に記録(silent repair 禁止)。散文は coerce 禁止=M3。"""
    m1, m2, m3, coercions = [], [], [], []      # 軸別 problem lists
    if not isinstance(ans, dict):
        return _va_result(["not a JSON object"], [], [], [], {"source_trace_completeness": 0.0})
    for k in ANSWER_KEYS:
        if k not in ans:
            m3.append(f"missing key: {k}")
    ids = set(corpus_ids)
    answer_c = ans.get("answer_claims") or []
    hist_c = ans.get("historical_claims") or []
    if not isinstance(answer_c, list):          # C-TOTALITY: 非 list でも crash しない
        m3.append(f"answer_claims is not a list: {type(answer_c).__name__}"); answer_c = []
    if not isinstance(hist_c, list):
        m3.append(f"historical_claims is not a list: {type(hist_c).__name__}"); hist_c = []
    st = ans.get("source_trace") or []
    if not isinstance(st, list):
        m3.append(f"source_trace is not a list: {type(st).__name__}"); st = []
    traced, total = 0, 0
    for c in (answer_c + hist_c):
        total += 1
        if not isinstance(c, dict):
            m3.append(f"claim entry is not an object: {c!r}"); continue
        cids = c.get("record_ids")
        if cids is None or cids == []:
            m1.append("claim with empty record_ids (unsupported assertion)"); continue
        if not isinstance(cids, list):
            m3.append(f"record_ids is not a list: {cids!r}"); continue
        unknown = [x for x in cids if x not in ids]
        if unknown:
            m1.append(f"claim cites unknown/forged record_id(s): {unknown}")
        else:
            traced += 1
    # superseded_by(全 citation class を検証。AB-0021(2) coerce 込み)
    for h in hist_c:
        if not isinstance(h, dict):
            continue
        sb = h.get("superseded_by")
        if sb is None:
            continue
        if isinstance(sb, str):                 # AB-0021(2): 実在 id のみ safe coerce、散文は M3
            if sb in ids:
                coercions.append(f"superseded_by bare string '{sb}' → ['{sb}'] (real record_id)")
                sb = [sb]
            else:
                m3.append(f"superseded_by is prose/scalar, not a coercible record_id: {sb[:60]!r}"); continue
        if not isinstance(sb, list):
            m3.append(f"superseded_by is not a list of refs: {sb!r}"); continue
        for ref in sb:                          # AB-0021(1): RECORD/INLINE/legacy-string
            prob = _supersession_ref_problem(ref, ids)
            if prob:
                (m1 if "unknown" in prob else m3).append(f"superseded_by ref: {prob}")
    bad_trace = [x for x in st if x not in ids]
    if bad_trace:
        m1.append(f"source_trace has unknown/forged ids: {bad_trace}")
    # M2 placement: HISTORICAL ラベルの claim が answer_claims にある(意味的正しさでなく明白な誤配置)
    for c in answer_c:
        if isinstance(c, dict) and c.get("currentness") == "HISTORICAL":
            m2.append("answer_claims entry labeled currentness=HISTORICAL (belongs in historical_claims)")
    metrics = {"n_answer_claims": len(answer_c), "n_historical_claims": len(hist_c),
               "n_open_gaps": len(ans.get("open_gaps") or []),
               "source_trace_completeness": (traced / total) if total else 0.0}
    return _va_result(m1, m2, m3, coercions, metrics)


def _va_result(m1, m2, m3, coercions, metrics):
    """3軸 + derived aggregate。problems は後方互換の flat union。"""
    metrics = dict(metrics)
    metrics.update({"m1_grounding_integrity_pass": not m1, "m2_semantic_placement_pass": not m2,
                    "m3_format_adherence_pass": not m3, "n_coercions": len(coercions)})
    return {"ok": not (m1 or m2 or m3), "problems": m1 + m2 + m3, "coercions": coercions,
            "axes": {"M1_grounding_integrity": m1, "M2_semantic_placement": m2, "M3_format_adherence": m3},
            "metrics": metrics}
