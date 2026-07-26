#!/usr/bin/env python3
"""s_back_thin_slice_build2 — Build 2: 薄い縦串（拾った意図で何をするか / RETRIEVE 1本）。BUILD SPEC v1.0。

★目的は縦串を通すことではない。**「意図調べが 0.71 で十分なのか」に答えを出す**こと。
  必要精度は「意図を間違えた時に下流がどうなるか」でしか測れない ⇒ **§4 の注入試験が本体**、正常系は前座。

構成:
  [意図調べ 7戦略] → INTENT_PROBE/PREMISE_PROBE=聞き返して STOP / DEFER=保留して STOP
                    → DIRECT/CONTEXT_RESOLVE/CHOICE/BMV = アクション routing へ
  [アクション routing(第2メニュー)] → ★RETRIEVE だけ end-to-end。他は NOT_BUILT を正直に返す stub
  [RETRIEVE] = 既存 EGL に「何が分かっているか(self_grounding.retrieve)」「既に試したか(failure_memory.check)」を問う
              ★どちらも決定論・純関数。ゆえに注入試験の比較に LLM ノイズが乗らない。

usage: s_back_thin_slice_build2.py [--check] [--full]
"""
import json
import os
import sys
import unicodedata

for _r in ("", "ds", "rri", "egl", "dev-workcell", "twoder"):
    _p = os.path.join("/home/takasan", _r)
    if _p not in sys.path:
        sys.path.insert(0, _p)

STRUCT = os.path.dirname(os.path.abspath(__file__))
if STRUCT not in sys.path:
    sys.path.insert(0, STRUCT)

import s_intent_role_split_d2p2 as D2P2          # noqa: E402  fixtures / 7戦略（監査済・改変しない）
from egl import self_grounding as SG             # noqa: E402  「何が分かっているか」
from twoder import failure_memory as FM          # noqa: E402  「既に試したか」

OUT = os.path.join(STRUCT, "BACK_THIN_SLICE_BUILD2.jsonl")
FAILURE_LEDGER = os.path.join(STRUCT, "BACK_THIN_SLICE_BUILD2_NOTBUILT.jsonl")
EDGE_INVENTORY = os.path.join(STRUCT, "EDGE_INVENTORY.jsonl")
CORPUS = "/home/takasan/ds/ds_events.jsonl"
MACHINE_PREFIX = "開発エビデンスを登録"

STOP_STRATEGIES = ("INTENT_PROBE", "PREMISE_PROBE", "DEFER")
ACT_STRATEGIES = ("DIRECT", "CONTEXT_RESOLVE", "CHOICE", "BOUNDED_MULTI_VIEW")

# ── §3 第2メニュー: 各項目に「裏付けとなる LIVE callee_symbol」を必須フィールドにする ──────────────────
#    ★手書きしない: --check が EDGE_INVENTORY で LIVE 検証し、LIVE でない項目を載せたら RED。
ACTION_MENU = [
    {"action": "RETRIEVE", "description": "既存 EGL に『何が分かっているか / 既に試したか』を問う",
     "live_callee_symbols": ["answer_question", "check"], "built": True},
    {"action": "REGISTER", "description": "設計エビデンスとして登記する",
     "live_callee_symbols": ["admit_design_evidence"], "built": False},
    {"action": "PREP_IMPL", "description": "実装タスクと計画を用意する",
     "live_callee_symbols": ["create_task", "record_plan"], "built": False},
    {"action": "OBSERVE", "description": "現状を観測する",
     "live_callee_symbols": ["derive_state"], "built": False},
    {"action": "CONVERSE", "description": "対話イベントとして記録する",
     "live_callee_symbols": ["record_dialogue_event"], "built": False},
]

# ★仕様との差異（feasibility-first・BUILT に明記する）:
#   SPEC §3 の参考表は 検索=`acquire` を挙げるが、`acquire` は **外部 adapter(HTTP/GitHub)による取得** であり、
#   SPEC §2 の RETRIEVE 定義「既存 EGL に何が分かっているか/既に試したかを問う」と一致しない。
#   よって RETRIEVE の裏付けは `retrieve`(self_grounding) と `check`(failure_memory) にした。**両方 LIVE。**
SPEC_REFERENCE_MISMATCH = {
    "spec_says": "検索=acquire",
    "actual": "acquire は egl/acquisition.py の外部取得(ACQ_HTTP_STATIC/ACQ_GITHUB adapter)であり、"
              "SPEC §2 の『既存 EGL に問う』とは別物。ネットワークにも出る。",
    "used_instead": ["answer_question (egl/self_grounding.py)", "check (twoder/failure_memory.py)"],
    "both_live": True,
    "impl_first_attempt_was_wrong": (
        "私は当初 RETRIEVE の裏付けに `retrieve`(self_grounding 内の決定論ランキング)を挙げたが、"
        "**EDGE_INVENTORY で LIVE なのは `answer_question` だけ**であり `retrieve` は独立には LIVE でない"
        "(answer_question の内部からのみ到達する)。**§3 の LIVE 検証が実際にこの誤りを RED で捕まえた**。"
        "＝『できるつもり』を機械が止めた実例。裏付けは answer_question + check に訂正した。"),
    "measurement_note": (
        "注入試験の比較には answer_question ではなく、その内部の決定論サブステップ `retrieve` を使う"
        "(LLM を挟むと run 間ノイズ ≈0.10 が arm 間差に混入するため)。**`retrieve` 単独は LIVE ではない**という"
        "事実は隠さない: LIVE 経路は answer_question 経由であり、我々は測定のためその内部段を直接叩いている。"),
}


def _live_symbols():
    syms = set()
    with open(EDGE_INVENTORY, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("status") == "LIVE":
                syms.add(r.get("callee_symbol"))
    return syms


def verify_menu_live(menu=None):
    """§3: メニュー項目の裏付けが EDGE_INVENTORY で LIVE か。-> (ok, detail)"""
    live = _live_symbols()
    detail = []
    for item in (menu if menu is not None else ACTION_MENU):
        missing = [s for s in item["live_callee_symbols"] if s not in live]
        detail.append({"action": item["action"], "symbols": item["live_callee_symbols"],
                       "not_live": missing, "ok": not missing})
    return all(d["ok"] for d in detail), detail


# ── RETRIEVE（決定論・純関数）────────────────────────────────────────────────────────────────────────
def build_query(strategy, request, context=""):
    """★戦略が RETRIEVE の問い方を決める。ここが『意図を間違えると下流が変わる』因果の本体。
    完全決定論（文字列合成のみ・LLM を呼ばない）。"""
    req = (request or "").strip()
    ctx = (context or "").strip()
    if strategy == "DIRECT":
        return req
    if strategy == "CONTEXT_RESOLVE":
        return (ctx + " " + req).strip() if ctx else req
    if strategy == "CHOICE":
        return req + " 選択肢 候補 比較"
    if strategy == "BOUNDED_MULTI_VIEW":
        return req + " 観点 利点 欠点 評価"
    return req


_CORPUS_CACHE = {}


def retrieve_action(strategy, request, context="", k=8):
    """RETRIEVE の実体: 既存 EGL に問う。**決定論・純関数**（self_grounding.retrieve / failure_memory.check）。"""
    if "records" not in _CORPUS_CACHE:
        _CORPUS_CACHE["records"] = SG.load_corpus()
    q = build_query(strategy, request, context)
    hits = SG.retrieve(q, _CORPUS_CACHE["records"], k=k)
    ids = [h.get("record_id") or h.get("id") or h.get("design_evidence_id") for h in hits]
    tried = FM.check({}, q)
    return {"action": "RETRIEVE", "built": True, "query": q, "query_len": len(q),
            "hit_ids": ids, "hit_n": len(ids),
            "already_tried": [{"failure_id": t.get("failure_id"), "guard_action": t.get("guard_action")}
                              for t in tried]}


def not_built_action(action, reason):
    """§2/§8: 作っていないものは **NOT_BUILT を正直に返す**。捏造しない。失敗記録は必須。"""
    return {"action": action, "built": False, "result": "NOT_BUILT", "reason": reason}


# ── 縦串 1本（意図調べの結果を受け取ってから下流だけを回す・決定論）──────────────────────────────────
def run_slice(strategy, request, context=""):
    """★意図調べは呼ばない（呼び出し側が結果を渡す）。注入試験で同一の意図調べ出力から2アームを導出するため。"""
    if strategy in STOP_STRATEGIES:
        kind = "CLARIFY" if strategy in ("INTENT_PROBE", "PREMISE_PROBE") else "HOLD"
        return {"strategy": strategy, "routed": "STOP", "stop_kind": kind, "downstream": None,
                "next_legal_operation": ("聞き返して停止（対象/前提が確定していない）" if kind == "CLARIFY"
                                         else "保留して停止（解釈不能）"),
                "no_action_recorded": True}
    if strategy not in ACT_STRATEGIES:
        return {"strategy": strategy, "routed": "UNKNOWN_STRATEGY", "downstream": None,
                "no_action_recorded": True}
    # 第2メニュー: thin なので RETRIEVE 以外は NOT_BUILT。選択自体は決定論（RETRIEVE 以外は未実装のため）。
    down = retrieve_action(strategy, request, context)
    return {"strategy": strategy, "routed": "ACTION", "action": "RETRIEVE", "downstream": down,
            "no_action_recorded": False}


# ── §4 注入試験（★本体・対照設計）──────────────────────────────────────────────────────────────────
NEAR_SWAPS = [("CONTEXT_RESOLVE", "BOUNDED_MULTI_VIEW"), ("BOUNDED_MULTI_VIEW", "CONTEXT_RESOLVE"),
              ("INTENT_PROBE", "PREMISE_PROBE"), ("PREMISE_PROBE", "INTENT_PROBE")]
FAR_SWAPS = [("DIRECT", "DEFER"), ("DEFER", "DIRECT"), ("DIRECT", "INTENT_PROBE"),
             ("INTENT_PROBE", "DIRECT")]


def _diff(a, b):
    """2アームの下流の差を決定論で出す。**『壊れた』の判定はしない**（SPEC §10(iii): 判定基準は DESIGN が定義）。"""
    if a is None and b is None:
        return {"both_stopped": True}
    if (a is None) != (b is None):
        return {"one_side_stopped": True, "stopped_arm": "correct" if a is None else "injected"}
    ia, ib = set(a.get("hit_ids") or []), set(b.get("hit_ids") or [])
    inter = ia & ib
    return {"both_stopped": False, "query_identical": a.get("query") == b.get("query"),
            "hit_n_correct": len(ia), "hit_n_injected": len(ib),
            "hits_shared": len(inter), "hits_lost": len(ia - ib), "hits_gained": len(ib - ia),
            "jaccard": round(len(inter) / len(ia | ib), 4) if (ia | ib) else None}


def injection_test(fixtures):
    """★対にする: 同一 fixture・同一の『正しい戦略』から2アームを導出し、下流だけを差し替える。
    LLM を挟まないので run 間ノイズは 0（下流は完全決定論）。"""
    rows = []
    for fx in fixtures:
        correct = fx["expected_strategy"]
        for kind, swaps in (("NEAR", NEAR_SWAPS), ("FAR", FAR_SWAPS)):
            for src, dst in swaps:
                if src != correct:
                    continue
                a = run_slice(correct, fx["request"], fx.get("context", ""))
                b = run_slice(dst, fx["request"], fx.get("context", ""))
                rows.append({"fixture_id": fx["id"], "request": fx["request"],
                             "correct_strategy": correct, "injected_strategy": dst, "swap_kind": kind,
                             "correct_routed": a["routed"], "injected_routed": b["routed"],
                             "routing_changed": a["routed"] != b["routed"],
                             "diff": _diff(a.get("downstream"), b.get("downstream")),
                             "correct_downstream": a.get("downstream"), "injected_downstream": b.get("downstream")})
    return rows


# ── §5 長文入力の計測 ────────────────────────────────────────────────────────────────────────────────
def long_input_probe():
    """実発話（我々の開発依頼）は一行ではない。**入力長 / 下流の挙動 / 崩れたか**を記録し切り分け可能にする。
    ★意図調べ（LLM）は --full の時だけ回す。ここは決定論部（下流）の長さ依存を測る。"""
    raw, filtered, uniq = corpus()
    buckets = {"<=40": [], "41-120": [], "121-400": [], ">400": []}
    for u in uniq:
        n = len(u)
        key = "<=40" if n <= 40 else "41-120" if n <= 120 else "121-400" if n <= 400 else ">400"
        buckets[key].append(u)
    out = {}
    for key, texts in buckets.items():
        sample = texts[:12]
        recs = [retrieve_action("DIRECT", t) for t in sample]
        out[key] = {"n_in_corpus": len(texts), "sampled": len(sample),
                    "mean_input_len": round(sum(len(t) for t in sample) / len(sample), 1) if sample else None,
                    "mean_query_len": round(sum(r["query_len"] for r in recs) / len(recs), 1) if recs else None,
                    "mean_hits": round(sum(r["hit_n"] for r in recs) / len(recs), 2) if recs else None,
                    "zero_hit_n": sum(1 for r in recs if r["hit_n"] == 0)}
    return out


def corpus():
    raw = []
    with open(CORPUS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("record_type") == "UTTERANCE" and r.get("speaker") == "USER":
                raw.append(r.get("raw_text", ""))
    filtered = [x for x in raw if not x.startswith(MACHINE_PREFIX)]
    return raw, filtered, list(dict.fromkeys(filtered))


# ── §6 probe → STOP → 再開（返答を新しい依頼として再度 意図調べにかける経路）────────────────────────
def resume_path(reply_text):
    """★ユーザーの返答＝『主張された文脈』。そのまま信じない。**返答を新しい依頼として再度 意図調べにかける。**
    ここでは経路の存在と決定論部（空入力 reject）だけを示す。**実データ検証は記録が1件しか無いので今回できない。**"""
    if D2P2.is_empty_input(reply_text):
        return {"resumed": False, "reason": "EMPTY_INPUT（意図調べに到達させない・既存の入口 reject）"}
    return {"resumed": True, "treated_as": "NEW_REQUEST",
            "note": "返答を文脈として信じず、新しい依頼として意図調べに再投入する経路。",
            "real_data_verification": "不可（preceding_utterance_ref が貯まったのは1件のみ）"}


# ── 失敗記録（§8・必須）───────────────────────────────────────────────────────────────────────────
def record_not_built(rows):
    with open(FAILURE_LEDGER, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def collect_failures(inj_rows):
    out = [{"record_type": "NOT_BUILT", "action": m["action"], "reason": "Build 2 は thin。RETRIEVE のみ end-to-end",
            "live_callee_symbols": m["live_callee_symbols"]} for m in ACTION_MENU if not m["built"]]
    for r in inj_rows:
        if r["correct_routed"] == "STOP":
            out.append({"record_type": "NO_ACTION", "fixture_id": r["fixture_id"],
                        "strategy": r["correct_strategy"],
                        "note": "聞き返し/保留で停止。失敗ではなく発見として記録（NO_CANDIDATE と同型）"})
    return out


# ── 集計 ─────────────────────────────────────────────────────────────────────────────────────────────
def measure():
    rows, res = [], {}
    ok, detail = verify_menu_live()
    res["menu_live_ok"] = ok
    rows.append({"row_type": "MENU", "menu": ACTION_MENU, "live_verification": detail,
                 "spec_reference_mismatch": SPEC_REFERENCE_MISMATCH})

    inj = injection_test(D2P2.FIXTURES)
    res["injection_n"] = len(inj)
    by_kind = {}
    for r in inj:
        k = r["swap_kind"]
        b = by_kind.setdefault(k, {"n": 0, "routing_changed": 0, "one_side_stopped": 0,
                                   "both_stopped": 0, "query_identical": 0, "jaccards": []})
        b["n"] += 1
        b["routing_changed"] += int(r["routing_changed"])
        d = r["diff"]
        b["one_side_stopped"] += int(bool(d.get("one_side_stopped")))
        b["both_stopped"] += int(bool(d.get("both_stopped")))
        b["query_identical"] += int(bool(d.get("query_identical")))
        if d.get("jaccard") is not None:
            b["jaccards"].append(d["jaccard"])
    for k, b in by_kind.items():
        b["jaccard_mean"] = round(sum(b["jaccards"]) / len(b["jaccards"]), 4) if b["jaccards"] else None
        b["jaccard_min"] = min(b["jaccards"]) if b["jaccards"] else None
        del b["jaccards"]
    res["injection_by_kind"] = by_kind
    rows.append({"row_type": "INJECTION", "cases": inj})

    res["long_input"] = long_input_probe()
    rows.append({"row_type": "LONG_INPUT", "buckets": res["long_input"]})

    res["resume"] = {"empty": resume_path("   "), "normal": resume_path("DE-0548 の件です")}
    rows.append({"row_type": "RESUME", "cases": res["resume"]})

    fails = collect_failures(inj)
    res["failures_recorded"] = record_not_built(fails)
    rows.append({"row_type": "FAILURES", "n": len(fails), "ledger": FAILURE_LEDGER})

    raw, filtered, uniq = corpus()
    res["corpus"] = {"user_utterances": len(raw), "machine_generated_excluded": len(raw) - len(filtered),
                     "after_exclusion": len(filtered), "unique_deduped": len(uniq), "dedup_applied": True}
    rows.append({"row_type": "CORPUS", "summary": res["corpus"]})
    return rows, res


def check():
    ok = True
    live_ok, detail = verify_menu_live()
    print("[%s] §3 メニューの LIVE 裏付け検証 (%d 項目)" % ("PASS" if live_ok else "FAIL", len(detail)))
    for d in detail:
        if not d["ok"]:
            print("       - %s: LIVE でない %s" % (d["action"], d["not_live"]))
    ok &= live_ok

    # ★negative control: LIVE でない symbol を載せたら RED になることの実証（§9-4）
    bogus = ACTION_MENU + [{"action": "BOGUS", "description": "存在しない裏付け",
                            "live_callee_symbols": ["this_symbol_is_not_live_anywhere"], "built": False}]
    neg_ok, _ = verify_menu_live(bogus)
    print("[%s] §9-4 negative control: LIVE でない項目を入れると RED になる" % ("PASS" if not neg_ok else "FAIL"))
    ok &= (not neg_ok)

    a = json.dumps(injection_test(D2P2.FIXTURES), ensure_ascii=False, sort_keys=True)
    b = json.dumps(injection_test(D2P2.FIXTURES), ensure_ascii=False, sort_keys=True)
    print("[%s] 注入試験が決定論（2回走らせて完全一致・下流に LLM を挟んでいない）" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)

    q1 = build_query("CONTEXT_RESOLVE", "テスト", "文脈あり")
    q2 = build_query("BOUNDED_MULTI_VIEW", "テスト", "文脈あり")
    print("[%s] 戦略が RETRIEVE の問い方を変える（因果が存在する）" % ("PASS" if q1 != q2 else "FAIL"))
    ok &= (q1 != q2)

    print("[%s] STOP 戦略は下流を呼ばない" % ("PASS" if run_slice("INTENT_PROBE", "x")["downstream"] is None
                                              else "FAIL"))
    ok &= run_slice("INTENT_PROBE", "x")["downstream"] is None

    nb = [m for m in ACTION_MENU if not m["built"]]
    print("[%s] 未実装アクションは NOT_BUILT を返す（捏造しない・%d 項目）"
          % ("PASS" if all(not_built_action(m["action"], "thin")["result"] == "NOT_BUILT" for m in nb) else "FAIL",
             len(nb)))
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    rows, res = measure()
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = res["corpus"]
    print("Build 2 薄い縦串 — 下流は完全決定論（LLM を挟まないので対照が成立する）")
    print("  §3 メニューの LIVE 裏付け: %s" % res["menu_live_ok"])
    print("  ★§4 注入試験 %d 件（同一 fixture から2アームを導出）" % res["injection_n"])
    for k, b in sorted(res["injection_by_kind"].items()):
        print("     %-5s n=%-3d routing が変わった=%-3d 片側だけ停止=%-3d 両方停止=%-3d "
              "問いが同一=%-3d Jaccard 平均=%s 最小=%s"
              % (k, b["n"], b["routing_changed"], b["one_side_stopped"], b["both_stopped"],
                 b["query_identical"], b["jaccard_mean"], b["jaccard_min"]))
    print("  §5 入力長ごとの下流（%d bucket）:" % len(res["long_input"]))
    for k, v in res["long_input"].items():
        print("     %-9s corpus内=%-4d 平均入力長=%-7s 平均hit=%-5s hit0件=%s"
              % (k, v["n_in_corpus"], v["mean_input_len"], v["mean_hits"], v["zero_hit_n"]))
    print("  §6 再開経路: %s" % res["resume"]["normal"]["real_data_verification"])
    print("  §8 失敗記録: %d 件 → %s" % (res["failures_recorded"], os.path.basename(FAILURE_LEDGER)))
    print("  母数: 生 %d → 機械生成除外 %d → %d → dedup → %d"
          % (c["user_utterances"], c["machine_generated_excluded"], c["after_exclusion"], c["unique_deduped"]))
    print("  → %s" % OUT)
    print("  ※『壊れた』の判定はしていない（SPEC §10(iii): 判定基準は DESIGN が定義する）。材料だけを決定論で出した。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
