#!/usr/bin/env python3
"""s_binder_real_context_feasibility — 実 context での束縛先判定(M6)が測定可能かを決定論で判定する。

CC-α 再監査(CC_DESIGN_2026-07-26_BUILD1A_PRIME_REAUDIT_FINDING §5)の承認条件:
  (1) 測定のみ・本番配線はしない  (2) 分岐しなかった場合も報告  (3) ★欠損を先に数える

本スクリプトは (3) を実行する。結論は台帳 BINDER_REAL_CONTEXT_FEASIBILITY.json に残す。
**測定そのもの(合成でない実 context での分岐)は、直前文脈を復元する手段が corpus に無いため実行できない。**
その「無い」を根拠つきで示すのが本スクリプトの目的（EGL: 根拠なき claim を認めない）。

完全決定論・LLM ゼロ。usage: s_binder_real_context_feasibility.py [--check]
"""
import json
import os
import sys
from collections import Counter

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "BINDER_REAL_CONTEXT_FEASIBILITY.json")
CORPUS = "/home/takasan/ds/ds_events.jsonl"
MACHINE_PREFIX = "開発エビデンスを登録"
TARGET_SURFACE = "前の件"   # AMB-REF-002 が実データで撃つ唯一の表層(DE-0550)


def load():
    utt, dev = [], []
    with open(CORPUS, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            r["_line"] = i
            if r.get("record_type") == "UTTERANCE":
                utt.append(r)
            elif r.get("record_type") == "DIALOGUE_EVENT":
                dev.append(r)
    return utt, dev


def assess():
    utt, dev = load()
    user = [r for r in utt if r.get("speaker") == "USER"]
    natural = [r for r in user if not (r.get("raw_text") or "").startswith(MACHINE_PREFIX)]
    by_id = {r.get("utterance_id"): r for r in utt}

    # 手段1: preceding_utterance_ref
    has_ref = [r for r in natural if r.get("preceding_utterance_ref")]
    ref_resolves = [r for r in has_ref if r.get("preceding_utterance_ref") in by_id]

    # 手段2: timestamp による順序復元
    stamps = Counter(r.get("timestamp") for r in utt)
    distinct_ts = len(stamps)

    # 手段3: conversation_id によるスレッド分割
    convs = Counter(r.get("conversation_id") for r in utt)

    # 手段4: DIALOGUE_EVENT による隣接リンク
    ref_lens = Counter(len(d.get("utterance_refs") or []) for d in dev)

    # 対象発話(AMB-REF-002 が実データで撃つ2件)が直前文脈を持つか
    targets = [r for r in natural if TARGET_SURFACE in (r.get("raw_text") or "")]
    tinfo = []
    for t in targets:
        cid = t.get("conversation_id")
        same = sorted([r for r in utt if r.get("conversation_id") == cid],
                      key=lambda r: ((r.get("timestamp") or ""), r["_line"]))
        pos = [j for j, r in enumerate(same) if r["_line"] == t["_line"]][0]
        prev = same[pos - 1] if pos > 0 else None
        covering = [d for d in dev if t.get("utterance_id") in (d.get("utterance_refs") or [])]
        tinfo.append({"utterance_id": t.get("utterance_id"), "text": t.get("raw_text"),
                      "conversation_id": cid, "position_in_conversation": pos + 1, "conversation_size": len(same),
                      "preceding_utterance_ref": t.get("preceding_utterance_ref"),
                      "prev_by_line_order": (prev.get("raw_text") if prev else None),
                      "dialogue_events_covering": len(covering),
                      "thread_candidates": [c for d in covering for c in (d.get("thread_candidates") or [])]})

    means = {
        "preceding_utterance_ref": {"populated": len(has_ref), "of": len(natural),
                                    "resolvable": len(ref_resolves), "usable": len(ref_resolves) > 0},
        "timestamp_ordering": {"distinct_timestamps": distinct_ts, "utterances": len(utt),
                               "usable": distinct_ts >= len(utt) * 0.9},
        "conversation_id_threads": {"buckets": len(convs), "largest_bucket": convs.most_common(1)[0] if convs else None,
                                    "usable": False if not convs else convs.most_common(1)[0][1] < 50},
        "dialogue_event_adjacency": {"utterance_refs_len_distribution": dict(ref_lens),
                                     "usable": any(k > 1 for k in ref_lens)},
    }
    feasible = any(m["usable"] for m in means.values())
    return {"corpus": {"utterances": len(utt), "user": len(user), "natural_after_exclusion": len(natural),
                       "unique_deduped": len(dict.fromkeys(r.get("raw_text") for r in natural)),
                       "dialogue_events": len(dev)},
            "means_examined": means,
            "targets": tinfo,
            "real_context_measurement_feasible": feasible,
            "conclusion": ("実 context を復元する手段が corpus に存在しないため、M6 の実 context 版は測定できない。"
                           if not feasible else "測定可能な手段が存在する。")}


def check():
    a = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    det = a == b
    r = assess()
    print("[%s] 決定論再現" % ("PASS" if det else "FAIL"))
    print("[%s] 判定が出ている (feasible=%s)" % ("PASS", r["real_context_measurement_feasible"]))
    print("[%s] 対象発話を特定できている (%d件)"
          % ("PASS" if r["targets"] else "FAIL", len(r["targets"])))
    ok = det and bool(r["targets"])
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    r = assess()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    c = r["corpus"]
    print("実 context 測定の可否 (CC-α 承認条件(3): 欠損を先に数える)")
    print("  母数: UTTERANCE %d / USER %d / 自然文 %d / ユニーク %d / DIALOGUE_EVENT %d"
          % (c["utterances"], c["user"], c["natural_after_exclusion"], c["unique_deduped"], c["dialogue_events"]))
    for name, m in r["means_examined"].items():
        print("  [%s] %-28s %s" % ("使える" if m["usable"] else "使えない", name,
                                   {k: v for k, v in m.items() if k != "usable"}))
    print("\n  対象発話(AMB-REF-002 が実データで撃つ2件):")
    for t in r["targets"]:
        print("   - %s (%s)" % (t["text"][:52], t["utterance_id"]))
        print("     会話内位置 %d/%d / ref=%s / 直前(行順)=%s"
              % (t["position_in_conversation"], t["conversation_size"], t["preceding_utterance_ref"],
                 (t["prev_by_line_order"] or "(無し)")[:40]))
    print("\n  → 実 context 測定は %s" % ("可能" if r["real_context_measurement_feasible"] else "★不可能"))
    print("  → %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
