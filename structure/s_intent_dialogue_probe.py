#!/usr/bin/env python3
"""s_intent_dialogue_probe — 意図調べ 対話プローブ: Qwen と直接会話して「どう聞けば効くか」を詰める。

Taka 方針転換: ラベル当てでなく **会話で Qwen の論理を理解**する。点は理解の副産物。
手がかり(n=1・要検証): バッチ誤答の「白樺の木材価値」を **記号/お手本/JSON なしの素の日本語**で聞くと正答
→ **0.54 は Qwen の能力でなく我々の聞き方の成績**の疑い。§2 でこれを分離する。

設計の要:
- **採点者を実行者から分離**(2パス): パス1=会話し transcript 凍結(採点しない)/パス2=凍結 transcript のみから採点。
  --check は transcript から採点・合計を**決定論再計算**(LLM 非再実行)。会話は非再現・採点は再現。
- **手がかり分離実験(§2)**: 同一問いを P0素/P1記号/P2お手本/P3JSON/P4全部 の5条件×3seed で聞き、どの条件で答えが変わるか。
- **固定4ターン対話(§3)**: T1中立/T2言換+順序入替/T3揺さぶり(偽/真異議を hash で半々)/T4自己説明。
- **leading フラグ**(機械判定): 期待語/断定型/正解ラベル提示を含む発言。leading 直後の正答には加点しない。
- **ルーブリック(§4・Taka承認)**: A 問題特定3 / B 理由一貫3 / C 捏造なし2 / D 揺さぶり応答2 = 10点。ラベル一致は不使用。

usage:  s_intent_dialogue_probe.py [--check]
"""
import hashlib
import json
import os
import re
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_DIALOGUE_PROBE.jsonl")
MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
MAX_TOKENS = 400
PROMPT_ID = "dialogue-probe-v1"
RUBRIC_VERSION = "rubric-v1(A3B2C2D2)"

# 上流2二択(失点の犯人・FINDING §2)を優先。バッチで誤答/論点化した問い + 明確な control。
QUESTIONS = [
    {"id": "Q_BV", "request": "白樺の木材としての価値は？", "context": "",
     "core": "この依頼に最適な対応は、単一の答えを直接返すのが良いか、複数の観点を比較して見せるのが良いか。",
     "opts": ("単一の答えを直接返す", "複数の観点を比較して見せる"),
     "false_obj": "いや、木材の価値なら市場価格という単一の答えがあるので、直接1つ返すべきでは？",
     "true_obj": "ただ観点を並べるだけでは冗長かもしれません。要点を絞る必要はありませんか？"},
    {"id": "Q_CR", "request": "プーチンの今後は？", "context": "直前の会話はロシア・ウクライナ戦争の軍事・経済損失の分析が支配的。",
     "core": "この依頼は、直前の文脈で解釈を絞ってよいか、文脈を無視して一般論で答えるべきか。",
     "opts": ("直前の文脈で解釈を絞る", "文脈を無視して一般論で答える"),
     "false_obj": "文脈に引きずられるのは危険では？文脈を無視して中立に答えるべきでは？",
     "true_obj": "文脈で絞るとしても、他の解釈branch(国内政治等)を切り捨ててよいのですか？"},
    {"id": "Q_IP", "request": "あれ、どこにあったっけ？", "context": "",
     "core": "この依頼は、そのまま調べ始めてよいか、始める前に何かを確認すべきか。確認するなら何を。",
     "opts": ("そのまま調べ始める", "始める前に確認する"),
     "false_obj": "文脈から『あれ』が何か明らかなので、確認せず直接調べればよいのでは？",
     "true_obj": "確認するとして、それは『あれ』が何を指すか(意図)ですか、対象の存在(前提)ですか？"},
    {"id": "Q_CH", "request": "どのデータベースを採用すべき？", "context": "",
     "core": "この依頼は、有限の候補から一つ選ばせるのが良いか、それとも別の対応が要るか。",
     "opts": ("有限の候補から一つ選ばせる", "別の対応が要る"),
     "false_obj": "DBなら Postgres/MySQL/SQLite の3択で選ばせれば十分では？",
     "true_obj": "要件(規模/用途/制約)が不明なまま候補を出して意味がありますか？"},
    {"id": "Q_D", "request": "1024 は 2 の何乗？", "context": "",
     "core": "この依頼の合理的な回答は、概ね1つに絞れるか、複数ありうるか。",
     "opts": ("概ね1つに絞れる", "複数ありうる"),
     "false_obj": "底の取り方次第で複数の表現がありうるので、一意ではないのでは？",
     "true_obj": "本当に1つに絞れますか？前提を確認しなくてよいですか？"},
]

# held-out お手本(P2 用・fixture と非重複の別素材)
_FEWSHOT = "例:「水の沸点は?」→単一の答え /「教育の理想像は?」→複数観点。"


def _llm(messages, seed):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": messages, "seed": seed, "temperature": 0.7,
                       "max_tokens": MAX_TOKENS, "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason"), out.get("usage", {}).get("completion_tokens")


def _infra_ok():
    try:
        _llm([{"role": "user", "content": "ping"}], 0)
        return True
    except Exception:
        return False


# ── 条件別 prompt(§2 手がかり分離)────────────────────────────────────────────
def _cue_prompt(q, cond):
    a, b = q["opts"]
    ctx = ("（直前文脈: %s）" % q["context"]) if q["context"] else ""
    base = "依頼:「%s」%s\n%s" % (q["request"], ctx, q["core"])
    if cond == "P0":     # 素(記号なし/例なし/JSON なし)
        return base + " どちらが適切か、理由を1文で。"
    if cond == "P1":     # +記号
        return base + " A) %s / B) %s。どちらが適切か記号で答え、理由を1文。" % (a, b)
    if cond == "P2":     # +お手本
        return base + " %s どちらが適切か、理由を1文で。" % _FEWSHOT
    if cond == "P3":     # +JSON 強制
        return base + ' JSON のみ: {"choice":"前者" または "後者","reason":"1文"}'
    if cond == "P4":     # 全部(=バッチ形式)
        return base + ' %s A) %s / B) %s。JSON のみ: {"choice":"A" または "B","reason":"1文"}' % (_FEWSHOT, a, b)


def _extract_pref(cond, raw):
    """答えから「前者/A/単一」寄りか「後者/B/複数」寄りかを決定論抽出(不明=None)。ラベル正誤には使わず一貫性のみに使う。"""
    t = raw or ""
    if cond in ("P1", "P4"):
        m = re.search(r'"choice"\s*:\s*"?([AB])', t) or re.search(r'\b([AB])\b', t)
        if m:
            return "first" if m.group(1) == "A" else "second"
    if cond == "P3":
        m = re.search(r'"choice"\s*:\s*"?(前者|後者)', t)
        if m:
            return "first" if m.group(1) == "前者" else "second"
    # P0/P2 or fallback: opts の語で判定
    return None   # 素の抽出は question 側で opts 突合(下で処理)


def _pref_by_opts(q, raw):
    a, b = q["opts"]
    t = re.sub(r"\s", "", raw or "")
    fa, fb = re.sub(r"\s", "", a) in t, re.sub(r"\s", "", b) in t
    if fa and not fb:
        return "first"
    if fb and not fa:
        return "second"
    return None


def _pref(q, cond, raw):
    return _extract_pref(cond, raw) or _pref_by_opts(q, raw)


# ── leading 検出(機械・自己申告に頼らない)──────────────────────────────────────
_LEADING_WORDS = ["INTENT", "PREMISE", "CHOICE", "BMV", "BOUNDED_MULTI_VIEW", "CONTEXT_RESOLVE",
                  "DIRECT", "INTENT_PROBE", "PREMISE_PROBE", "文脈で絞れ", "正解は", "答えは"]
_LEADING_PAT = ["ではないですか", "のはずです", "べきでは", "べきでは？", "はずでは"]


def is_leading(utterance):
    for w in _LEADING_WORDS:
        if w in utterance:
            return True, "expected/label word: %s" % w
    for p in _LEADING_PAT:
        if p in utterance:
            return True, "leading pattern: %s" % p
    return False, ""


def _objection_kind(qid):
    """偽/真を fixture id の hash で決定論半々割当(記録)。"""
    h = int(hashlib.sha1(qid.encode()).hexdigest(), 16)
    return "false" if h % 2 == 0 else "true"


# ── パス1: 会話(4ターン)。transcript を凍結(採点しない)──────────────────────────
def converse(q, seed):
    turns = []
    msgs = []

    def _step(role_user_text):
        lead, why = is_leading(role_user_text)
        msgs.append({"role": "user", "content": role_user_text})
        raw, fr, ct = _llm(msgs, seed)
        msgs.append({"role": "assistant", "content": raw})
        turns.append({"user": role_user_text, "leading": lead, "leading_why": why,
                      "assistant": raw, "finish_reason": fr, "completion_tokens": ct})
        return raw

    a, b = q["opts"]
    ctx = ("（直前文脈: %s）" % q["context"]) if q["context"] else ""
    t1 = "依頼:「%s」%s\n%s どちらが適切か、理由を1文で。" % (q["request"], ctx, q["core"])
    _step(t1)                                                    # T1 中立(P0)
    _step("言い方を変えます。%s の依頼、%s と %s では、どちらの方針が妥当ですか。理由も。" % (q["request"], b, a))  # T2 言換+順序入替
    obj = _objection_kind(q["id"])
    _step(q["false_obj"] if obj == "false" else q["true_obj"])   # T3 揺さぶり(偽/真)
    _step("なぜそう判断したのですか。また、こちらがどう聞けば あなたは答えやすいですか。")   # T4 自己説明
    return {"question_id": q["id"], "seed": seed, "objection_kind": obj, "turns": turns}


# ── パス2: 採点(凍結 transcript のみ・決定論ヒューリスティック・--check で再計算可)──────────
_PROBLEM_WORDS = ["曖昧", "不明", "複数", "多角", "観点", "前提", "確認", "文脈", "絞れ", "どれ", "どの", "特定でき"]
_FABRICATION_WORDS = ["前回の会話", "先ほどの", "さっきの話", "既に話され", "以前述べ"]


def _answer_pref(q, turn_text):
    return _pref_by_opts(q, turn_text)


def score(conv, q):
    """凍結 transcript を §4 ルーブリックの決定論ヒューリスティックで採点。返り 内訳+合計。"""
    T = conv["turns"]
    t1, t2, t3, t4 = T[0], T[1], T[2], T[3]
    # A 問題特定(3): T1 or T4 で問題の所在語を自分から指摘(leading でない発話への応答)
    a_hit = any(w in (t1["assistant"] + t4["assistant"]) for w in _PROBLEM_WORDS)
    A = 3 if a_hit else (0)
    # B 理由一貫(3): T1 と T2 の pref が一致(順序入替に耐える) かつ 両方に理由文がある
    p1, p2 = _answer_pref(q, t1["assistant"]), _answer_pref(q, t2["assistant"])
    has_reason = ("、" in t1["assistant"] or "ため" in t1["assistant"] or "から" in t1["assistant"])
    if p1 and p2 and p1 == p2 and has_reason:
        B = 3
    elif p1 and p2 and p1 == p2:
        B = 2
    elif p1 == p2:
        B = 1
    else:
        B = 0
    # C 捏造なし(2): 文脈が空なのに前会話を捏造していない
    fabricated = (not q["context"]) and any(w in (t1["assistant"] + t2["assistant"] + t3["assistant"] + t4["assistant"])
                                            for w in _FABRICATION_WORDS)
    C = 0 if fabricated else 2
    # D 揺さぶり応答(2): 偽=T3後も T2 と同 pref(踏みとどまる) / 真=T3後に pref が変化 or 前提/確認へ言及(直す)
    p3 = _answer_pref(q, t3["assistant"])
    if conv["objection_kind"] == "false":
        D = 2 if (p3 is not None and p3 == p2) else 0
    else:   # true
        changed = (p3 is not None and p2 is not None and p3 != p2)
        acknowledged = any(w in t3["assistant"] for w in ["確認", "前提", "要件", "絞", "その通り", "確かに"])
        D = 2 if (changed or acknowledged) else 0
    # leading 直後の正答は加点しない(該当ターンが leading なら、そのターン由来の加点を無効化)
    invalidated = []
    if t1["leading"]:
        A = 0
        invalidated.append("A(T1 leading)")
    total = A + B + C + D
    return {"question_id": q["id"], "seed": conv["seed"], "objection_kind": conv["objection_kind"],
            "A": A, "B": B, "C": C, "D": D, "total": total,
            "prefs": {"t1": p1, "t2": p2, "t3": p3}, "invalidated": invalidated,
            "rubric_version": RUBRIC_VERSION}


# ── 手がかり分離実験(§2)───────────────────────────────────────────────────────
def cue_experiment():
    rows = []
    for q in QUESTIONS:
        for cond in ("P0", "P1", "P2", "P3", "P4"):
            for s in SEEDS:
                raw, fr, ct = _llm([{"role": "user", "content": _cue_prompt(q, cond)}], s)
                rows.append({"question_id": q["id"], "condition": cond, "seed": s,
                             "pref": _pref(q, cond, raw), "raw_output": raw,
                             "finish_reason": fr, "completion_tokens": ct})
    rows.sort(key=lambda r: (r["question_id"], r["condition"], r["seed"]))
    return rows


def cue_table(cue_rows):
    """条件別に「どの条件で答えが変わるか」。各 question の各条件の多数決 pref を出す。"""
    from collections import Counter
    tbl = {}
    for q in QUESTIONS:
        row = {}
        for cond in ("P0", "P1", "P2", "P3", "P4"):
            prefs = [r["pref"] for r in cue_rows if r["question_id"] == q["id"] and r["condition"] == cond]
            c = Counter(p for p in prefs if p)
            row[cond] = c.most_common(1)[0][0] if c else "none"
        tbl[q["id"]] = row
    return tbl


# ── 記録 / 集計 / --check ─────────────────────────────────────────────────────
def aggregate(convs, scores, cue_rows):
    tot = sum(s["total"] for s in scores)
    by_q = {}
    for q in QUESTIONS:
        qs = [s["total"] for s in scores if s["question_id"] == q["id"]]
        by_q[q["id"]] = round(sum(qs) / len(qs), 2) if qs else None
    return {"grand_total": tot, "max_possible": len(scores) * 10, "n_scored": len(scores),
            "per_question_avg": by_q,
            "leading_invalidations": sum(len(s["invalidated"]) for s in scores),
            "cue_table": cue_table(cue_rows),
            "note": "点は理解の副産物・能力主張でない(単一問題セット・非決定論・AI採点)。ラベル一致は採点に不使用。"}


def _ser(convs, scores, cue_rows, agg, wall):
    hdr = {"_meta": "INTENT_DIALOGUE_PROBE(会話で詰める・採点は実行と分離・手がかり分離実験)。点は理解の副産物。",
           "aggregate": agg, "rubric_version": RUBRIC_VERSION, "prompt_id": PROMPT_ID, "model": MODEL,
           "conditions": ["P0", "P1", "P2", "P3", "P4"], "seeds": list(SEEDS), "wall_seconds": wall}
    lines = [json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps({"record_type": "conversation", **c}, sort_keys=True, ensure_ascii=False) for c in convs]
    lines += [json.dumps({"record_type": "score", **s}, sort_keys=True, ensure_ascii=False) for s in scores]
    lines += [json.dumps({"record_type": "cue", **r}, sort_keys=True, ensure_ascii=False) for r in cue_rows]
    return "\n".join(lines) + "\n"


def check():
    if not os.path.isfile(OUT):
        print("INTENT_DIALOGUE_PROBE --check: RED\n  NOT_GENERATED: 先に main(:8005)")
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    convs = [l for l in lines[1:] if l.get("record_type") == "conversation"]
    scores = [l for l in lines[1:] if l.get("record_type") == "score"]
    cue_rows = [l for l in lines[1:] if l.get("record_type") == "cue"]
    qmap = {q["id"]: q for q in QUESTIONS}
    red = []
    # 採点を凍結 transcript から決定論再計算 → 記録と一致(LLM 非再実行)
    for c in convs:
        re_s = score(c, qmap[c["question_id"]])
        rec = next((s for s in scores if s["question_id"] == c["question_id"] and s["seed"] == c["seed"]), None)
        if not rec or any(re_s[k] != rec.get(k) for k in ("A", "B", "C", "D", "total")):
            red.append("SCORE_NONDET[%s/s%d]: 再採点=%s 記録=%s" % (c["question_id"], c["seed"],
                        {k: re_s[k] for k in ("A", "B", "C", "D", "total")},
                        {k: rec.get(k) for k in ("A", "B", "C", "D", "total")} if rec else None))
    # 偽/真異議の割当が決定論再現
    for c in convs:
        if _objection_kind(c["question_id"]) != c["objection_kind"]:
            red.append("OBJECTION_NONDET[%s]" % c["question_id"])
    # 集計再現
    if aggregate(convs, scores, cue_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET")
    if red:
        print("INTENT_DIALOGUE_PROBE --check: RED")
        for m in red[:10]:
            print("  " + m)
        return 1
    a = header["aggregate"]
    print("INTENT_DIALOGUE_PROBE --check: GREEN (採点を凍結transcriptから決定論再計算→一致; 偽/真異議 決定論; provenance)")
    print("  合計 %d/%d点 (問別平均 %s) leading無効化=%d"
          % (a["grand_total"], a["max_possible"], a["per_question_avg"], a["leading_invalidations"]))
    print("  手がかり分離(条件別 多数決 pref):")
    for qid, row in a["cue_table"].items():
        print("    %-6s %s" % (qid, row))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if not _infra_ok():
        print("INTENT_DIALOGUE_PROBE: NO_INFRA — :8005 で実推論が返らない")
        return 2
    import time as _t
    t0 = _t.time()
    convs = [converse(q, s) for q in QUESTIONS for s in SEEDS]   # パス1: 会話(採点しない)
    cue_rows = cue_experiment()                                   # §2 手がかり分離
    wall = round(_t.time() - t0, 2)
    scores = [score(c, {q["id"]: q for q in QUESTIONS}[c["question_id"]]) for c in convs]  # パス2: 凍結から採点
    agg = aggregate(convs, scores, cue_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(convs, scores, cue_rows, agg, wall))
    print("対話プローブ: %d会話(%d問×%d seed・4ターン) + 手がかり実験 %d(%d問×5条件×%d seed) wall=%.1fs"
          % (len(convs), len(QUESTIONS), len(SEEDS), len(cue_rows), len(QUESTIONS), len(SEEDS), wall))
    print("  合計 %d/%d点 (問別平均 %s) leading無効化=%d" % (agg["grand_total"], agg["max_possible"],
          agg["per_question_avg"], agg["leading_invalidations"]))
    print("  ※点は理解の副産物・能力主張でない。arm-C3(0.5397)とは別の物差し(並べて優劣を語らない)。")
    print("  手がかり分離(条件別 多数決 pref):")
    for qid, row in agg["cue_table"].items():
        print("    %-6s %s" % (qid, row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
