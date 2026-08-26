#!/usr/bin/env python3
"""s_llm_false_stop — LLM が門になっている呼出の ★誤停止を 正解なしで数える計器(LLMK-0006 の機械化)。

★正解ラベルを1件も作らずに 誤停止を特定する2つの型:
  ①定義違反 : その語の定義に反する出力を数える(例 DEFER=「不正形・解釈不能」なのに 整った依頼文)
  ②自己矛盾(束) : ★意味を変えない摂動(nonce/日時/ID だけが違う)の束で 門の答が割れたら 少数側は誤り
  ③自己矛盾(反復): ★同じ入力を N 回 通して 答が割れたら 少数側は誤り(★束が無くても使える)

★1回の走行を 門の性質として 報告しない(2026-08-26 実測: 同じ55本・同じ経路で 止まった数が
   2 と 4 に 動いた)。∴ ★既定で 反復する(--repeat)。

★入力は front door からしか取らない(台帳を直読しない)。
★このモジュールは ★何も書かない・★意味を付けない(★事実だけ 返す)。
★★2026-08-27 是正= ★明細の文を組むのも 投函も ★`twoder/domain_inference_control.py`(Domain Manager)へ 移した。
  ★理由= GDW 正本 §6「Workerは事実を作る。Managerは意味と次の行動を決める」を 私が 破っていた
  (★門を 差し替えた 瞬間に 偽の意味づけが 台帳へ 入った= 数値は正しく 解釈だけが 偽)。
★★全文を使う(2026-08-26 実測: goal_head の120字 切片で測ると 停止率が 25% と出て、
   全文では 4% だった= 6倍。切片で測った数字を門の性質として報告しない)。

usage:
  s_llm_false_stop.py --self-test              # 計器の陰性/陽性対照だけ(LLM 0回)
  s_llm_false_stop.py [--limit N] [--repeat N] # 実測(front door + :8005 を実走)
  s_llm_false_stop.py --repeat 3 --prob 10                     # 止まった件の ★確率 p を 追加で測る
  s_llm_false_stop.py --gate route --prob 10                   # 別の門(経路を決める側)で 同じことを測る
"""
import base64, json, os, re, sys, urllib.request

FRONT = os.environ.get("TWODER_FRONT", "http://100.107.6.119:8770")
TOKEN_PATH = "/home/takasan/twoder/.access_token"
STOP_WORDS_DEFINED_AS_MALFORMED = ("DEFER",)   # 定義が「不正形・解釈不能」である語(intent_strategy.py:32 逐語)
REQUEST_MARK = "ほしい"                         # ★依頼文であることの表層条件(意味で選ばない)


def _auth():
    tok = open(TOKEN_PATH).read().strip()
    return "Basic " + base64.b64encode(("taka:" + tok).encode()).decode()


def _get(path, timeout=120):
    req = urllib.request.Request(FRONT + path, headers={"Authorization": _auth()})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_requests(limit=None):
    """front door から ★全文の依頼文を取る。-> [{task_id, text}]。★切片(goal_head)は使わない。"""
    idx = _get("/api/task_index")
    seen, out = set(), []
    for r in idx.get("tasks") or []:
        if not isinstance(r, dict):
            continue
        head = (r.get("goal_head") or "").strip()
        if len(head) < 40 or head.startswith("<<<") or REQUEST_MARK not in head or head in seen:
            continue
        seen.add(head)
        out.append(r["task_id"])
        if limit and len(out) >= limit:
            break
    rows = []
    for tid in out:
        try:
            g = (_get("/api/state?task_id=" + tid) or {}).get("goal") or ""
        except Exception:
            g = ""
        if g:
            rows.append({"task_id": tid, "text": g})
    return rows


_NONCE = re.compile(r"(TASK-2DER-[0-9A-Fa-f]{6,}|[0-9]{3,}[-_][0-9A-Za-z]{2,}|\b[0-9a-f]{7,}\b|[0-9]{2,})")


def normalize(text):
    """★意味を変えない差(nonce/ID/日時/数字)を落とす。★語は落とさない。"""
    t = _NONCE.sub("#", text)
    return re.sub(r"\s+", " ", t).strip()


def cluster(rows):
    """正規化後が同じものを1つの束にする。-> {key: [row, ...]}"""
    cl = {}
    for r in rows:
        cl.setdefault(normalize(r["text"]), []).append(r)
    return cl


def measure_prob(rows, gate, ids, trials=10):
    """★止まった件の 確率 p を 直接測る。★反復3回では 集計自体が揺れる(2026-08-26 実測:
    『3回とも止まった』が 走行ごとに 0件 と 1件 に動いた) ∴ 候補だけ 多く引く。
    -> {task_id: {"p":…, "stops":…, "trials":…, "strategies":{…}}}"""
    by_id = {r["task_id"]: r for r in rows}
    out = {}
    for tid in ids:
        r = by_id.get(tid)
        if not r:
            continue
        got = [gate(r["text"]) for _ in range(trials)]
        stops = sum(1 for _, st in got if st)
        strat = {}
        for s_, _ in got:
            strat[s_] = strat.get(s_, 0) + 1
        out[tid] = {"p": round(stops / trials, 2), "stops": stops, "trials": trials,
                    "strategies": dict(sorted(strat.items(), key=lambda x: -x[1]))}
    return out


def measure_repeat(rows, gate, repeat=3, well_formed=None):
    """★同じ標本を repeat 回 通す。-> 集計 dict。★1回ぶんの数字は『走行の1標本』として残す。"""
    runs = [measure(rows, gate, well_formed) for _ in range(repeat)]
    stops = {}
    for r in runs:
        for tid in r["_stopped_ids"]:
            stops[tid] = stops.get(tid, 0) + 1
    always = [t for t, c in stops.items() if c == repeat]
    flaky = sorted([(t, c) for t, c in stops.items() if 0 < c < repeat], key=lambda x: -x[1])
    ids = set(always) | {t for t, _ in flaky}
    fs = set()
    for r in runs:
        fs |= {x[0] for x in r["definition_violations"]} | {x[0] for x in r["cluster_minority"]}
    fs |= {t for t, _ in flaky}
    return {
        "n": len(rows), "repeat": repeat,
        "stopped_ids": sorted(stops),
        "stopped_per_run": [r["stopped"] for r in runs],
        "stop_rate_per_run": [r["stop_rate"] for r in runs],
        "stopped_at_least_once": len(ids),
        "stopped_every_run": len(always),
        "flaky_stops": [(t, "%d/%d" % (c, repeat)) for t, c in flaky],
        "definition_violations": sorted({(x[0], x[1]) for r in runs for x in r["definition_violations"]}),
        "cluster_minority": sorted({(x[0], x[1]) for r in runs for x in r["cluster_minority"]}),
        "false_stops": len(fs),
        "false_stop_rate": round(len(fs) / len(rows), 3) if rows else None,
        "note": "flaky_stops は 同じ入力で 止まったり 止まらなかったり した件 ∴ 少なくとも片方は誤り",
    }


def measure(rows, gate, well_formed=None):
    """gate(text) -> (strategy, stopped)。well_formed(text) -> bool(既定=依頼の印が在る)。
    -> 報告 dict。★分母を必ず持つ。"""
    wf = well_formed or (lambda t: REQUEST_MARK in t)
    res = [(r, ) + tuple(gate(r["text"])) for r in rows]
    n = len(res)
    stopped = [x for x in res if x[2]]
    # ①定義違反
    violations = [x for x in stopped if x[1] in STOP_WORDS_DEFINED_AS_MALFORMED and wf(x[0]["text"])]
    # ②自己矛盾(束の少数側)
    cl = cluster([x[0] for x in res])
    by_id = {x[0]["task_id"]: x for x in res}
    split, minority = 0, []
    for key, members in cl.items():
        if len(members) < 2:
            continue
        flags = [by_id[m["task_id"]][2] for m in members]
        if len(set(flags)) > 1:
            split += 1
            keep = sum(flags) <= len(flags) - sum(flags)      # 少数側=止まる側が少なければ止まる側
            minority += [by_id[m["task_id"]] for m in members if by_id[m["task_id"]][2] is keep]
    ids = {id(x) for x in violations} | {id(x) for x in minority}
    return {
        "n": n,
        "stopped": len(stopped),
        "stop_rate": round(len(stopped) / n, 3) if n else None,
        "strategies": {s: sum(1 for x in res if x[1] == s) for s in sorted({x[1] for x in res})},
        "clusters": len(cl),
        "clusters_multi": sum(1 for v in cl.values() if len(v) >= 2),
        "clusters_split": split,
        "definition_violations": [(x[0]["task_id"], x[1], x[0]["text"][:60]) for x in violations],
        "cluster_minority": [(x[0]["task_id"], x[1], x[0]["text"][:60]) for x in minority],
        "false_stops": len(ids),
        "false_stop_rate": round(len(ids) / n, 3) if n else None,
        "_stopped_ids": [x[0]["task_id"] for x in stopped],
    }


# ── 対照(計器が判別能力を持つことを LLM 0回で示す) ──────────────────────────────
def _fake_rows():
    base = "その関数を直してほしい。 nonce=%s"
    return ([{"task_id": "T%d" % i, "text": base % ("0810-%04d" % i)} for i in range(6)]
            + [{"task_id": "TX", "text": "まったく別の依頼です。新しい能力を作ってほしい。"}])


def self_test():
    rows = _fake_rows()
    red = []
    # 陰性①: 全部通す門 -> 誤停止 0
    r = measure(rows, lambda t: ("DIRECT", False))
    if r["false_stops"] != 0:
        red.append("NEG1: all-pass gate reported %d false stops" % r["false_stops"])
    # 陰性②: 全部止める門 -> 束は割れない ∴ 少数側 0。定義違反だけが立つ
    r = measure(rows, lambda t: ("PREMISE_PROBE", True))
    if r["cluster_minority"]:
        red.append("NEG2: all-stop gate produced cluster minority %d" % len(r["cluster_minority"]))
    # 陽性①: 束の1本だけ止める門 -> 少数側 1
    r = measure(rows, lambda t: ("PREMISE_PROBE", True) if t.endswith("0003") else ("DIRECT", False))
    if len(r["cluster_minority"]) != 1:
        red.append("POS1: one-off stop not caught (minority=%d)" % len(r["cluster_minority"]))
    # 陽性②: 整った依頼文に DEFER -> 定義違反
    r = measure(rows, lambda t: ("DEFER", True))
    if len(r["definition_violations"]) != len(rows):
        red.append("POS2: DEFER on well-formed requests not flagged (%d)" % len(r["definition_violations"]))
    # 陽性③: 反復で割れる門 -> flaky として立つ(★束が無くても捕まる)
    _state = {"i": 0}
    def _flip(t):
        _state["i"] += 1
        return ("PREMISE_PROBE", True) if _state["i"] % 2 else ("DIRECT", False)
    rr = measure_repeat(rows, _flip, repeat=3)
    if not rr["flaky_stops"]:
        red.append("POS3: repeat-flaky gate produced no flaky_stops")
    # 陰性④: 反復しても安定な門 -> flaky 0
    rr = measure_repeat(rows, lambda t: ("DIRECT", False), repeat=3)
    if rr["flaky_stops"] or rr["false_stops"]:
        red.append("NEG4: stable pass-gate flagged flaky=%s fs=%d" % (rr["flaky_stops"], rr["false_stops"]))
    # 陽性④: p が既知の門(2回に1回 止まる)-> p≈0.5 が返る
    _c = {"i": 0}
    def _half(t):
        _c["i"] += 1
        return ("PREMISE_PROBE", True) if _c["i"] % 2 else ("DIRECT", False)
    pr = measure_prob(rows, _half, [rows[0]["task_id"]], trials=10)
    if pr[rows[0]["task_id"]]["p"] != 0.5:
        red.append("POS4: known p=0.5 gate measured as %.2f" % pr[rows[0]["task_id"]]["p"])
    # 陰性⑤: 常に通す門 -> p=0.0
    pr = measure_prob(rows, lambda t: ("DIRECT", False), [rows[0]["task_id"]], trials=5)
    if pr[rows[0]["task_id"]]["p"] != 0.0:
        red.append("NEG5: all-pass gate measured p=%.2f" % pr[rows[0]["task_id"]]["p"])
    # 陰性③: 正規化が語を落としていない(別の依頼が同じ束に入らない)
    if len(cluster(rows)) != 2:
        red.append("NEG3: normalize collapsed distinct requests (clusters=%d)" % len(cluster(rows)))
    if red:
        print("s_llm_false_stop --self-test: RED")
        for m in red:
            print("  " + m)
        return 1
    print("s_llm_false_stop --self-test: GREEN (陰性5 / 陽性4 とも期待どおり ★意味づけの対照は Domain Manager 側)")
    return 0












# ── 門は 差し替えられる(★1つの計器で 複数の門を 同じ形で測る)────────────────────────
#   contract: gate(text) -> (label, stopped_bool)
#   ★route 門は「止める/止めない」ではなく ★行き先が変わるか を見る ∴ stopped は常に False とし、
#     ★label(=下流の枝)の 揺れを --prob の分布で 読む。
ROUTE_BRANCH = {   # Phase 3 実測: request_type の 6語 -> 下流は 4挙動(submit.py:573/1026/1099/1107/1217)
    "OBSERVE_CURRENT_STATE": "OBSERVE",
    "RESUME_PRIOR": "RESUME",
    "BUILD_CAPABILITY": "BUILD_OR_MODIFY",
    "MODIFY_EXISTING": "BUILD_OR_MODIFY",
    "DECIDE": "ELSE",
    "OTHER": "ELSE",
}


def route_gate(text):
    """rri/rri/request_type.py:classify_request_type -> 下流の枝。"""
    sys.path.insert(0, "/home/takasan/rri")
    from rri import request_type as RT
    o = RT.classify_request_type(text) or {}
    return ROUTE_BRANCH.get(o.get("request_type"), "ELSE"), False


def label_stability(prob):
    """--prob の結果から ★ラベルが全試行で同じだった件数を数える。"""
    same = sum(1 for v in prob.values() if len(v["strategies"]) == 1)
    return {"stable": same, "n": len(prob), "rate": round(same / len(prob), 3) if prob else None}


def default_gate(text):
    sys.path.insert(0, "/home/takasan/rri")
    from rri import intent_strategy as IST
    r = IST.resolve_consensus(text)
    return r.get("strategy"), bool(IST.stops_before_action(r))


def main(argv):
    if "--self-test" in argv:
        return self_test()
    limit = None
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    repeat = 3
    if "--repeat" in argv:
        repeat = int(argv[argv.index("--repeat") + 1])
    gate = default_gate
    gate_name = "stop(intent_strategy.resolve_consensus)"
    if "--gate" in argv and argv[argv.index("--gate") + 1] == "route":
        gate, gate_name = route_gate, "route(request_type.classify_request_type)"
    rows = fetch_requests(limit)
    print("front door から全文で取れた依頼文: %d本 / 反復 %d回" % (len(rows), repeat))
    print("門: %s" % gate_name)
    out = measure_repeat(rows, gate, repeat=repeat)
    out["gate"] = gate_name
    if "--prob" in argv:
        trials = int(argv[argv.index("--prob") + 1])
        # ★route 門は 止まらない ∴ 候補が0件になる → 全件を引く(★ここで黙って0件にしない)
        ids = out["stopped_ids"] or [r["task_id"] for r in rows]
        out["prob"] = measure_prob(rows, gate, ids, trials=trials)
        out["label_stability"] = label_stability(out["prob"])
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
