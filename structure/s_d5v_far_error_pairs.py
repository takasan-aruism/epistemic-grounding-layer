#!/usr/bin/env python3
"""s_d5v_far_error_pairs — 依頼 D5-V: 遠隔誤りの per-fixture 前後対応表。決定論・LLM 不使用。

入力: MENU_RESTRICTION_BUILD4_ROWS.jsonl（per-(batch,run,fixture,seed,arm) の選択結果）
出力: 表1つ + 3つの数。**(a)/(b) の判定はしない**（依頼の明示指示・判定は DESIGN）。

判定基準（★既定のまま・測定後に動かさない）:
  STOP = {INTENT_PROBE, PREMISE_PROBE, DEFER}   /   ACT = {DIRECT, CONTEXT_RESOLVE, CHOICE, BOUNDED_MULTI_VIEW}
  遠隔誤り = 選択が期待と異なり、かつ STOP/ACT の境界を跨ぐこと

usage: s_d5v_far_error_pairs.py [--check]
"""
import json
import os
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(STRUCT, "MENU_RESTRICTION_BUILD4_ROWS.jsonl")
OUT = os.path.join(STRUCT, "D5V_FAR_ERROR_PAIRS.json")

STOP_SET = {"INTENT_PROBE", "PREMISE_PROBE", "DEFER"}


def side(strategy):
    if strategy is None:
        return "NONE"
    return "STOP" if strategy in STOP_SET else "ACT"


def is_far(expected, choice):
    """★選択が None（NO_CANDIDATE / DIVERGE）の回は遠隔誤りに数えない（誤答と同列に数えない規律）。"""
    if choice is None or choice == expected:
        return False
    return (expected in STOP_SET) != (choice in STOP_SET)


def load_pairs():
    if not os.path.exists(ROWS):
        return None, "ROWS が無い（再実行がまだ・または保存に失敗）"
    by_key = {}
    with open(ROWS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            k = (r["batch"], r["run"], r["fixture_id"], r["seed"])
            by_key.setdefault(k, {})[r["arm"]] = r
    pairs = [(k, v["A_postfilter"], v["B_menurestrict"]) for k, v in sorted(by_key.items())
             if "A_postfilter" in v and "B_menurestrict" in v]
    return pairs, None


def build():
    pairs, err = load_pairs()
    if err:
        return {"error": err}
    table, c1, c2, c3 = [], [], [], []
    for (batch, run, fid, seed), a, b in pairs:
        exp = a["expected"]
        af, bf = is_far(exp, a["choice"]), is_far(exp, b["choice"])
        if not (af or bf):
            continue
        row = {"batch": batch, "run": run, "fixture_id": fid, "seed": seed, "expected": exp,
               "A_choice": a["choice"], "A_far": af, "A_side": side(a["choice"]),
               "B_choice": b["choice"], "B_far": bf, "B_side": side(b["choice"]),
               "expected_side": side(exp), "A_status": a["status"], "B_status": b["status"]}
        table.append(row)
        if af and b["choice"] == exp:
            c1.append(row)
        elif af and bf:
            c2.append(row)
        elif (not af) and bf:
            c3.append(row)
    def _cnt(rows, key):
        out = {}
        for r in rows:
            out[r[key]] = out.get(r[key], 0) + 1
        return out
    return {
        "pairs_total": len(pairs), "table_rows": len(table), "table": table,
        "count1_A_far_to_B_correct": {"n": len(c1), "by_fixture": _cnt(c1, "fixture_id")},
        "count2_A_far_to_B_still_far": {"n": len(c2), "by_fixture": _cnt(c2, "fixture_id"),
                                        "moved_to": _cnt(c2, "B_choice")},
        "count3_new_far_in_B_only": {"n": len(c3), "by_fixture": _cnt(c3, "fixture_id"),
                                     "moved_to": _cnt(c3, "B_choice")},
        "other_rows_A_far_B_neither": len(table) - len(c1) - len(c2) - len(c3),
        "criteria": {"STOP": sorted(STOP_SET), "note": "選択が None の回は遠隔誤りに数えない。判定基準は測定後に動かしていない。"},
        "scope_note": "★(a)/(b) の判定はしない（依頼 D5-V の明示指示）。表と3つの数のみ。",
    }


def check():
    r = build()
    if "error" in r:
        print("[SKIP] %s" % r["error"])
        print("\n--check GREEN（入力待ち）")
        return 0
    ok = True
    a = json.dumps(build(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(build(), ensure_ascii=False, sort_keys=True)
    print("[%s] 決定論再現" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    print("[%s] A/B の対が揃っている (%d 対)" % ("PASS" if r["pairs_total"] else "FAIL", r["pairs_total"]))
    ok &= bool(r["pairs_total"])
    n = r["count1_A_far_to_B_correct"]["n"] + r["count2_A_far_to_B_still_far"]["n"] \
        + r["count3_new_far_in_B_only"]["n"] + r["other_rows_A_far_B_neither"]
    print("[%s] 3分類 + その他 が表の行数と一致 (%d = %d)" % ("PASS" if n == r["table_rows"] else "FAIL",
                                                              n, r["table_rows"]))
    ok &= (n == r["table_rows"])
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    r = build()
    if "error" in r:
        print("入力なし: %s" % r["error"])
        return 2
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    print("D5-V 遠隔誤りの前後対応（対 %d / 表 %d 行）★(a)(b)の判定はしない" % (r["pairs_total"], r["table_rows"]))
    print("%-3s %-3s %-5s %-4s %-20s %-20s %-18s" % ("b", "run", "fx", "seed", "A_choice(側)", "B_choice(側)", "期待(側)"))
    for x in r["table"]:
        print("%-3d %-3d %-5s %-4d %-20s %-20s %-18s %s"
              % (x["batch"], x["run"], x["fixture_id"], x["seed"],
                 "%s(%s)%s" % (x["A_choice"], x["A_side"], "★" if x["A_far"] else ""),
                 "%s(%s)%s" % (x["B_choice"], x["B_side"], "★" if x["B_far"] else ""),
                 "%s(%s)" % (x["expected"], x["expected_side"]), ""))
    print("\n  (1) A で遠隔誤り → B で正解        : %d件 %s"
          % (r["count1_A_far_to_B_correct"]["n"], r["count1_A_far_to_B_correct"]["by_fixture"]))
    print("  (2) A で遠隔誤り → B でも遠隔誤り  : %d件 移り先=%s"
          % (r["count2_A_far_to_B_still_far"]["n"], r["count2_A_far_to_B_still_far"]["moved_to"]))
    print("  (3) A では遠隔誤りでない → B で新規: %d件 %s 移り先=%s"
          % (r["count3_new_far_in_B_only"]["n"], r["count3_new_far_in_B_only"]["by_fixture"],
             r["count3_new_far_in_B_only"]["moved_to"]))
    print("  その他(A で遠隔誤り → B は正解でも遠隔誤りでもない): %d件" % r["other_rows_A_far_B_neither"])
    print("  → %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
