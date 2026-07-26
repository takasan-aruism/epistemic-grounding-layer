#!/usr/bin/env python3
"""s_existence_premise_1c — Build 1c(P4 存在の前提 + 出口 SUPERSEDE)の測定ハーネス。BUILD SPEC v1.0 §9/§10。

「以前作った X」「先週決めた Y」は **X/Y が存在する**という前提を渡してくる。LLM に疑わせず、機械が台帳に当たる。
3状態(GROUNDED / NOT_FOUND / UNKNOWN)を持ち **UNKNOWN を NOT_FOUND に潰さない**。探索そのものを返り値に含め反証可能にする。

★本ハーネスが特に測るもの(SPEC §10 の要求 + 実装中に見つかった2つの落とし穴):
  M1 PP1/PP2/PP3 で発火 / M2 D1・D2・D3 で非発火 / M3 発火率(dedup 済ユニーク298件・母数を毎回記録)
  M4 既存 HBB-30 ゲートの非回帰(★最優先) / M5 HBB-30「約6倍」を探索対象の4通りで測る
  M6 ★自己言及の汚染(我々の設計文書が fixture を引用しているだけで GROUNDED になる罠)
  M7 ★3状態が潰れないこと(UNKNOWN を NOT_FOUND にしない)

完全決定論・:8005 不使用・LLM 呼出ゼロ。usage: s_existence_premise_1c.py [--check]
"""
import json
import os
import sys

for _r in ("", "rri", "ds", "egl", "dev-workcell", "twoder"):
    _p = os.path.join("/home/takasan", _r)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rri import existence_grounding as EG   # noqa: E402
from rri import preflight_gate as PG        # noqa: E402

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "EXISTENCE_PREMISE_1C.jsonl")
CORPUS = "/home/takasan/ds/ds_events.jsonl"
MACHINE_PREFIX = "開発エビデンスを登録"

FIXTURES = [
    ("PP1", "以前作った Watcher 仕様ってどこ？", True),
    ("PP2", "先週決めた方針のメモある？", True),
    ("PP3", "君が言ってた予備の鍵はどこ？", True),
    ("D1", "Windows 10 の一般提供開始日は？", False),
    ("D2", "1024 は 2 の何乗ですか？", False),
    ("D3", "1 マイルは何キロメートル？", False),
    ("BV3", "この設計案の得失は？", False),
    ("CH1", "どのデータベースを採用すべき？", False),
    ("BV1", "白樺の木材としての価値は？", False),
]
HBB_OBJECT = "約6倍"
HBB_AMBIG = ("a theoretical document says ternary systems show about 6x higher emergence score than binary "
             "systems; recover the derivation")
LEGACY_NLO = ("CLARIFY_FIRST (gate RRI-GATE-AMBIGUOUS-QUANT-001): ambiguous quantitative claim — concrete "
              "number + vague/missing source. RRI holds before DW/acquisition; provide a clear source "
              "(author/title/venue/url) to proceed. proposed EGL status=WEAK_UNSOURCED_QUANTITATIVE_CLAIM")


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


def measure():
    rows, res = [], {}

    # ── M1/M2 fixture ────────────────────────────────────────────────────────────────────────────────
    fx = []
    for fid, text, expect in FIXTURES:
        g = PG.detect(text)
        fired = g["triggered"] and g["gate_id"] == "RRI-GATE-UNGROUNDED-EXISTENCE-001"
        fx.append({"id": fid, "text": text, "expected_fire": expect, "fired": fired,
                   "decision": g["decision"] if fired else g["decision"],
                   "state": g["signals"].get("grounding_state"), "object": g["signals"].get("object"),
                   "queries": g["signals"].get("queries"), "searched": g["signals"].get("searched"),
                   "ok": fired is expect})
    res["M1_PP_fired"] = {f["id"]: f["fired"] for f in fx if f["id"].startswith("PP")}
    res["M2_D_not_fired"] = {f["id"]: f["fired"] for f in fx if f["id"].startswith("D")}
    res["fixture_all_ok"] = all(f["ok"] for f in fx)
    rows.append({"row_type": "FIXTURE", "cases": fx})

    # ── M3 発火率(★母数を毎回記録 — CC-α 裁定: 計器が自分の活動を食う)────────────────────────────────
    raw, filtered, uniq = corpus()
    fires = []
    for u in uniq:
        g = PG.detect(u)
        if g["triggered"] and g["gate_id"] == "RRI-GATE-UNGROUNDED-EXISTENCE-001":
            fires.append({"text": u, "object": g["signals"].get("object"),
                          "state": g["signals"].get("grounding_state"), "decision": g["decision"]})
    res["M3_corpus"] = {"user_utterances": len(raw), "machine_generated_excluded": len(raw) - len(filtered),
                        "after_exclusion": len(filtered), "unique_deduped": len(uniq),
                        "existence_gate_fired": len(fires),
                        "fire_rate_pct": round(100.0 * len(fires) / len(uniq), 2), "dedup_applied": True}
    res["M3_hits"] = fires
    rows.append({"row_type": "CORPUS", "summary": res["M3_corpus"], "fired_hits_all": fires})

    # ── M4 既存ゲート非回帰(★最優先)──────────────────────────────────────────────────────────────────
    a = PG.detect(HBB_AMBIG)
    m4 = {"CLARIFY_FIRST": a["decision"] == "CLARIFY_FIRST" and a["gate_id"] == PG.GATE_ID,
          "STRONGLY_DISCOURAGE_DW": PG.detect(HBB_AMBIG, failure_hits=[{"failure_id": "FAIL-002"}])["decision"]
          == "STRONGLY_DISCOURAGE_DW",
          "ALLOW_WITH_WARNING": PG.detect(HBB_AMBIG, user_insists=True)["decision"] == "ALLOW_WITH_WARNING",
          "ALLOW_abstract": PG.detect("what does emergence mean in ternary vs binary systems, conceptually?")
          ["decision"] == "ALLOW",
          "next_legal_operation_verbatim": PG.next_legal_operation(a) == LEGACY_NLO}
    res["M4_non_regression"] = m4
    res["M4_all_green"] = all(m4.values())
    rows.append({"row_type": "NON_REGRESSION", "checks": m4})

    # ── M5 HBB-30「約6倍」を探索対象4通りで測る(★除いた時が本番)────────────────────────────────────
    variants = {"base(散文なし+登記台帳)": (), "+hbb_candidates.json": ("HBB_CANDIDATES",)}
    m5 = {}
    for name, extra in variants.items():
        r = EG.check_existence(HBB_OBJECT, extra_targets=extra)
        m5[name] = {"state": r["state"], "decision": EG.STATE_TO_DECISION[r["state"]],
                    "grounding_hits": r["grounding_hits"], "mention_hits": r["mention_hits"],
                    "self_referential_hits": r["self_referential_hits"],
                    "declared_prior": [str(d.get("id")) + "(src=" + str(d.get("source_de")) + ")"
                                       for d in r["declared_prior"]],
                    "queries": r["queries"], "searched": r["searched"]}
    # ★対照: 登記台帳が無ければ SUPERSEDE に到達しないこと（何が仕事をしているかを示す）
    _saved = EG.CLAIM_STATUS_REGISTRY
    EG.CLAIM_STATUS_REGISTRY = "/nonexistent/CLAIM_STATUS_REGISTRY.jsonl"
    EG._CACHE.pop(("CLAIM_STATUS", _saved), None)
    _wo = EG.check_existence(HBB_OBJECT)
    EG.CLAIM_STATUS_REGISTRY = _saved
    EG._CACHE.pop(("CLAIM_STATUS", "/nonexistent/CLAIM_STATUS_REGISTRY.jsonl"), None)
    m5["登記台帳を外した場合(対照)"] = {"state": _wo["state"], "decision": EG.STATE_TO_DECISION[_wo["state"]],
                                        "grounding_hits": _wo["grounding_hits"], "mention_hits": _wo["mention_hits"],
                                        "self_referential_hits": _wo["self_referential_hits"],
                                        "declared_prior": [], "queries": _wo["queries"], "searched": _wo["searched"]}
    res["M5_hbb"] = m5
    res["M5_registry_is_load_bearing"] = _wo["state"] != "DECLARED_UNVERIFIED"
    rows.append({"row_type": "HBB30_SEARCH_SCOPE", "variants": m5, "object": HBB_OBJECT,
                 "registry_is_load_bearing": res["M5_registry_is_load_bearing"]})

    # ── M6 自己言及の汚染(我々の設計文書が fixture を引用しているだけで接地扱いにならないか)──────────
    m6 = {}
    for fid, text, _e in FIXTURES[:3]:
        obj = PG.past_reference_object(text)[1]
        r = EG.check_existence(obj)
        m6[fid] = {"object": obj, "state": r["state"], "grounding_hits": r["grounding_hits"],
                   "mention_hits": r["mention_hits"], "self_referential_hits": r["self_referential_hits"],
                   "evidence_refs": [(e.get("id") or e["ref"]) for e in r["evidence"][:4]]}
    res["M6_self_reference"] = m6
    res["M6_no_false_grounding"] = all(v["state"] != "GROUNDED" for v in m6.values())
    # 接地の根拠が我々自身の DE 記録かどうかを明示（裁定§5 の原則に照らして検査する）
    import json as _j
    _own = set()
    with open("/home/takasan/egl/DESIGN_EVIDENCE_LEDGER.jsonl", encoding="utf-8") as _fh:
        for _l in _fh:
            _l = _l.strip()
            if _l:
                _r = _j.loads(_l)
                if _r.get("generated_by_principal") == "CLAUDE_CODE":
                    _own.add(_r.get("design_evidence_id"))
    res["M6_ledger_self_authored"] = {"claude_code_records": len(_own)}
    for k, v in m6.items():
        v["evidence_is_self_authored_de"] = [e for e in v["evidence_refs"] if e in _own]
    rows.append({"row_type": "SELF_REFERENCE_CONTAMINATION", "cases": m6})

    # ── M7 3状態が潰れないこと ───────────────────────────────────────────────────────────────────────
    multi = EG.check_existence("ゼクスカリバー式 量子茶漬け 生成器")   # 実在せず・複数語→異表記3通り以上作れる
    single = EG.check_existence("ゼクスカリバー式量子茶漬け生成器")     # 実在せず・単一語→異表記が2通りしか作れない
    partial = EG.check_existence("Watcher 仕様")                       # 言及のみ
    real = EG.check_existence("preflight_gate.py")                     # FILE_MANIFEST に実在
    novel = EG.check_existence("ゼクスカリバー クオンティス フーガロン")   # 全構成語が実在しない
    alt = EG.check_existence("ゼクスカリバー式 量子茶漬け 生成器", partial_forces_unknown=False)  # 別解釈
    m7 = {"実在しない(単一語)": single["state"], "実在しない(一般語込み複数語)": multi["state"],
          "★負の対照: 実在しない造語": novel["state"], "言及のみ": partial["state"],
          "★実在ファイル preflight_gate.py": real["state"],
          "NOT_FOUND 前の異表記数": len(novel["queries"])}
    res["M7_states"] = m7
    # ★★裁定§2(レコード全体)適用後に露見した汚染。**負の対照が壊れているので RED として扱う。**
    res["M7_contamination"] = {
        "negative_control_broken": novel["state"] != "NOT_FOUND",
        "negative_control_evidence": [e["id"] for e in novel["evidence"][:3]],
        "real_file_mislabeled": real["state"] == "DECLARED_UNVERIFIED",
        "real_file_declared_prior_source": [d["id"] for d in real["declared_prior"][:3]],
        "note": ("負の対照『ゼクスカリバー クオンティス フーガロン』は私が本テスト用に作った造語だが、"
                 "**私がその造語を DE 報告に書いた結果、DE 台帳に入り、対照が成立しなくなった**。"
                 "同様に実在ファイル preflight_gate.py が DECLARED_UNVERIFIED と誤標識される"
                 "(私の DE-0554 の本文に DECLARED/UNVERIFIED の語が含まれるため)。"),
    }
    res["M7_all_ok"] = (not res["M7_contamination"]["negative_control_broken"]
                        and not res["M7_contamination"]["real_file_mislabeled"]
                        and real["state"] == "GROUNDED" and novel["state"] == "NOT_FOUND")
    # ★★射程の限界(SPEC §9(c) の帰結)。黙って規則を緩めず、限界として記録し裁定を仰ぐ。
    res["M7_scope_limit"] = {
        "single_token_queries": len(single["queries"]), "min_required": EG.MIN_QUERIES_FOR_NOT_FOUND,
        "multi_token_partial_hits": multi["partial_hits"],
        "alt_interpretation_state": alt["state"],
        "consequence": (
            "SPEC §9(c) を字句どおり実装すると **NOT_FOUND はほぼ到達不能** になる。理由は2つ: "
            "(1) 空白を含まない単一語は機械的に異表記を3通り作れず常に UNKNOWN。"
            "(2) 複数語でも構成語に一般語(例『生成器』)が1つ在るだけで部分一致が立ち UNKNOWN に落ちる"
            "(実測: 実在しない『ゼクスカリバー式 量子茶漬け 生成器』で部分一致 %d件)。"
            "＝ P4 が『探した上で無い』と言えるのは **全構成語が我々の記録に一度も出てこない対象** に限られる。"
            % multi["partial_hits"]),
        "adjudication_needed": (
            "『部分一致があれば UNKNOWN』の解釈が2通りある。(A) 字句どおり=構成語の部分一致でも UNKNOWN(既定・現状)。"
            "(B) 別解釈=部分一致は弱い手掛かりに留め、対象そのものの異表記が全て0hitなら NOT_FOUND。"
            "同じ入力で (A)=%s / (B)=%s。**既定は変更していない。どちらが正典かの裁定を求める。**"
            % (multi["state"], alt["state"])),
    }
    rows.append({"row_type": "THREE_STATES", "checks": m7, "scope_limit": res["M7_scope_limit"],
                 "nonexistent_multi_detail": {k: multi[k] for k in ("queries", "searched", "hits", "basis")},
                 "nonexistent_single_detail": {k: single[k] for k in ("queries", "hits", "basis")}})
    # ── M8 df 閾値の頑健性（CC-α 依頼B③）★測定後に都合の良い値へ動かさない ─────────────────────────
    probes = [("負の対照(造語)", "ゼクスカリバー クオンティス フーガロン", "NOT_FOUND"),
              ("PP1", "Watcher 仕様", "UNKNOWN"), ("PP2", "方針のメモ", "UNKNOWN"),
              ("PP3", "予備の鍵", "UNKNOWN"),
              ("実在ファイル", "preflight_gate.py", "GROUNDED"),
              ("HBB-30", HBB_OBJECT, "DECLARED_UNVERIFIED"),
              # ★弁別語規則が実際に働くのは TOKEN 部分一致が立つ時だけ。それを狙った probe を入れる。
              ("一般語込み(生成器)", "ゼクスカリバー式 量子茶漬け 生成器", "UNKNOWN"),
              ("既存語込み(preflight_gate)", "架空の preflight_gate 仕様書", "UNKNOWN")]
    thresholds = (1, 5, 10, 20, 50, 100, 500)
    m8 = {}
    for name, obj, expect in probes:
        row = {}
        for th in thresholds:
            row[th] = EG.check_existence(obj, df_threshold=th)["state"]
        m8[name] = {"expected_at_fixed_threshold": expect, "by_threshold": row,
                    "stable": len(set(row.values())) == 1,
                    "matches_expectation_at_20": row[EG.DISCRIMINATIVE_DF_THRESHOLD] == expect
                    if EG.DISCRIMINATIVE_DF_THRESHOLD in row else None}
    res["M8_threshold_sensitivity"] = m8
    res["M8_fixed_threshold"] = EG.DISCRIMINATIVE_DF_THRESHOLD
    res["M8_all_stable"] = all(v["stable"] for v in m8.values())
    # ★「安定」と「効いていない」を混同しない。規則が働くには df >= 閾値 の構成語が要る。
    dfs = {}
    for name, obj, _e in probes:
        dfs[name] = EG.check_existence(obj)["token_document_frequency"]
    max_df = max([d for v in dfs.values() for d in v.values()] or [0])
    res["M8_rule_exercised"] = {
        "token_document_frequencies": dfs, "max_observed_df": max_df,
        "fixed_threshold": EG.DISCRIMINATIVE_DF_THRESHOLD,
        "any_token_excluded_at_fixed_threshold": max_df >= EG.DISCRIMINATIVE_DF_THRESHOLD,
        "excluded_tokens_at_fixed": sorted({tok for v in dfs.values() for tok, d in v.items()
                                            if d >= EG.DISCRIMINATIVE_DF_THRESHOLD}),
        "sensitive_probes": sorted(k for k, v in m8.items() if not v["stable"]),
        "insensitive_probes": sorted(k for k, v in m8.items() if v["stable"]),
        "sensitive_range": sorted({th for k, v in m8.items() if not v["stable"]
                                   for th in thresholds
                                   if v["by_threshold"][th] != v["by_threshold"][thresholds[-1]]}),
    }
    rows.append({"row_type": "DF_THRESHOLD_SENSITIVITY", "fixed": EG.DISCRIMINATIVE_DF_THRESHOLD,
                 "thresholds": list(thresholds), "cases": m8})
    return rows, res


def check():
    ok = True
    rows, res = measure()
    for label, key in (("fixture 期待どおり(PP発火/D非発火)", "fixture_all_ok"),
                       ("既存 HBB-30 非回帰(★最優先)", "M4_all_green"),
                       ("★負の対照が生きている(自己記録で汚染されていない)", "M7_all_ok"),
                       ("自己言及で GROUNDED にならない", "M6_no_false_grounding")):
        print("[%s] %s" % ("PASS" if res[key] else "FAIL", label))
        ok &= res[key]
    a = json.dumps(measure()[0], ensure_ascii=False, sort_keys=True)
    b = json.dumps(measure()[0], ensure_ascii=False, sort_keys=True)
    print("[%s] 決定論再現(2回走らせて完全一致)" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    pats = PG.load_patterns(use_cache=False)
    ex = [p for p in pats if p["pattern_id"] == "AMB-EXIST-001"]
    print("[%s] pattern DB スキーマ (%d パターン・AMB-EXIST-001 在り=%s)"
          % ("PASS" if ex else "FAIL", len(pats), bool(ex)))
    ok &= bool(ex)
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    rows, res = measure()
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = res["M3_corpus"]
    print("Build 1c(P4 存在の前提) 実測 — 完全決定論・LLM ゼロ")
    print("  M1 PP 発火    : %s" % res["M1_PP_fired"])
    print("  M2 D 非発火   : %s (すべて False が正)" % res["M2_D_not_fired"])
    print("  M3 発火率     : %d/%d = %.2f%%  ★母数(%d→除外%d→%d→dedup→%d)"
          % (c["existence_gate_fired"], c["unique_deduped"], c["fire_rate_pct"],
             c["user_utterances"], c["machine_generated_excluded"], c["after_exclusion"], c["unique_deduped"]))
    for h in res["M3_hits"][:12]:
        print("       %-10s %-12s | %s" % (h["state"], h["decision"], h["text"][:52]))
    print("  M4 非回帰     : %s" % res["M4_all_green"])
    print("  M5 HBB-30「約6倍」を探索対象別に:")
    for k, v in res["M5_hbb"].items():
        print("       %-22s → %-20s %-14s 接地hit=%d 言及hit=%d declared_prior=%s"
              % (k, v["state"], v["decision"], v["grounding_hits"], v["mention_hits"], v["declared_prior"]))
    print("  M6 自己言及の汚染:")
    for k, v in res["M6_self_reference"].items():
        print("       %-4s %-14s → %-10s 接地hit=%d 言及hit=%d(うち自己言及%d)"
              % (k, v["object"], v["state"], v["grounding_hits"], v["mention_hits"], v["self_referential_hits"]))
    print("  M7 3状態      : %s" % res["M7_states"])
    ct = res["M7_contamination"]
    print("  ★M7 汚染      : 負の対照が壊れた=%s (根拠=%s) / 実在ファイルの誤標識=%s (根拠=%s)"
          % (ct["negative_control_broken"], ct["negative_control_evidence"],
             ct["real_file_mislabeled"], ct["real_file_declared_prior_source"]))
    print("  ★DE台帳のうち CLAUDE_CODE 起票: %d件" % res["M6_ledger_self_authored"]["claude_code_records"])
    print("  M8 df 閾値の頑健性 (固定値=%d):" % res["M8_fixed_threshold"])
    for k, v in res["M8_threshold_sensitivity"].items():
        print("       %-16s %s  安定=%s" % (k, v["by_threshold"], v["stable"]))
    print("       → 全 probe が閾値に対して安定: %s" % res["M8_all_stable"])
    ex = res["M8_rule_exercised"]
    print("       ★観測された最大 df=%d / 固定閾値=%d → 閾値で除外された語がある: %s"
          % (ex["max_observed_df"], ex["fixed_threshold"], ex["any_token_excluded_at_fixed_threshold"]))
    print("       ★閾値20 で除外される語: %s" % ex["excluded_tokens_at_fixed"])
    print("       ★閾値に感度がある probe: %s / 無い probe: %s"
          % (ex["sensitive_probes"], ex["insensitive_probes"]))
    print("       ★感度がある閾値域: %s (固定値 %d はこの域の外)"
          % (ex["sensitive_range"], ex["fixed_threshold"]))
    print("  → %s" % OUT)
    print("  ※射程は『記録の規律』に等しい。記録の無い対象は UNKNOWN にしかならない。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
