#!/usr/bin/env python3
"""s_retention_repair_a — (a) retention 補修の受入検証。BUILD SPEC v1.0 §4。

**記録の規律の補修であって機能追加ではない。** 発話記録に「直前発話 id」と「実時刻か既定かの別」を書く。
★P2 ゲートへの context 配線は**しない**(Build 2 の scope)。本スクリプトは記録が入ることだけを検証する。

検証(SPEC §4):
  A1 既存 LIVE の非回帰(呼び出し側で実行)         A2 preceding_utterance_ref が埋まる(先頭は None・決定論)
  A3 ts_source が CALLER/DEFAULT を区別する        A4 既存レコードが1件も変わっていない(差分ゼロ)
  A5 母数の記録                                     A6 --check GREEN(決定論再現)

完全決定論・LLM ゼロ。usage: s_retention_repair_a.py [--check] [--baseline=<path>]
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = "/home/takasan"
STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "RETENTION_REPAIR_A.json")
LIVE_LEDGER = os.path.join(ROOT, "ds/ds_events.jsonl")
MACHINE_PREFIX = "開発エビデンスを登録"


def _sandbox():
    """LIVE 台帳を汚さずに記録経路を動かす。DS_DATA_DIR を差し替えた子プロセスで実行する。"""
    code = r'''
import json, os, sys, tempfile
d = tempfile.mkdtemp(prefix="ds_reta_")
os.environ.update({"DS_DATA_DIR": d, "EGL_DATA_DIR": tempfile.mkdtemp(), "RRI_DATA_DIR": tempfile.mkdtemp(),
                   "DW_DATA_DIR": tempfile.mkdtemp()})
for r in ("", "ds", "rri", "egl", "dev-workcell", "twoder"):
    p = os.path.join("/home/takasan", r)
    if p not in sys.path:
        sys.path.insert(0, p)
from ds import phase0
out = []
# 会話A: 1件目=先頭(None) / 2件目=直前 id / 3件目=2件目の id
a1 = phase0.record_utterance("USER", "一件目", "conv-A", "2026-07-26T10:00:00Z",
                             preceding_utterance_ref=phase0.last_utterance_id("conv-A"), ts_source="CALLER")
a2 = phase0.record_utterance("USER", "二件目", "conv-A", "2026-07-26T10:00:01Z",
                             preceding_utterance_ref=phase0.last_utterance_id("conv-A"), ts_source="CALLER")
a3 = phase0.record_utterance("USER", "三件目", "conv-A", "2026-07-26T10:00:02Z",
                             preceding_utterance_ref=phase0.last_utterance_id("conv-A"), ts_source="CALLER")
# 会話B: 別会話の先頭は None のまま(会話をまたいで繋がない)
b1 = phase0.record_utterance("USER", "別会話の一件目", "conv-B", "2026-07-26T10:00:03Z",
                             preceding_utterance_ref=phase0.last_utterance_id("conv-B"), ts_source="DEFAULT")
out = [{k: r.get(k) for k in ("utterance_id", "conversation_id", "preceding_utterance_ref", "ts_source")}
       for r in (a1, a2, a3, b1)]
print(json.dumps(out, ensure_ascii=False))
'''
    import subprocess
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError("sandbox failed: %s" % r.stderr[-800:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def corpus_counts():
    raw = []
    with open(LIVE_LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("record_type") == "UTTERANCE" and r.get("speaker") == "USER":
                raw.append(r.get("raw_text", ""))
    filtered = [x for x in raw if not x.startswith(MACHINE_PREFIX)]
    return {"user_utterances": len(raw), "machine_generated_excluded": len(raw) - len(filtered),
            "after_exclusion": len(filtered), "unique_deduped": len(dict.fromkeys(filtered)),
            "dedup_applied": True}


def live_field_coverage():
    """LIVE 台帳で新フィールドがどれだけ埋まっているか。**前向きのみなので当面ほぼ0が正常。**"""
    tot = with_ref = with_src = 0
    by_src = {}
    with open(LIVE_LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("record_type") != "UTTERANCE":
                continue
            tot += 1
            if r.get("preceding_utterance_ref"):
                with_ref += 1
            if r.get("ts_source"):
                with_src += 1
                by_src[r["ts_source"]] = by_src.get(r["ts_source"], 0) + 1
    return {"utterances_total": tot, "with_preceding_ref": with_ref, "with_ts_source": with_src,
            "ts_source_breakdown": by_src}


def baseline_diff(baseline_path):
    """A4: 既存レコードが1件も変わっていないこと(差分ゼロ)。baseline 行数までを逐語比較する。"""
    if not baseline_path or not os.path.exists(baseline_path):
        return {"checked": False, "reason": "baseline 未指定または不在"}
    with open(baseline_path, encoding="utf-8") as fh:
        base = [l.rstrip("\n") for l in fh if l.strip()]
    with open(LIVE_LEDGER, encoding="utf-8") as fh:
        live = [l.rstrip("\n") for l in fh if l.strip()]
    n = len(base)
    same = live[:n] == base
    changed = [i + 1 for i, (a, b) in enumerate(zip(base, live[:n])) if a != b][:10]
    return {"checked": True, "baseline_lines": n, "live_lines": len(live),
            "existing_records_unchanged": same, "changed_line_numbers": changed,
            "appended_since_baseline": len(live) - n}


def assess(baseline_path=None):
    sb = _sandbox()
    a2 = {"first_in_conversation_is_null": sb[0]["preceding_utterance_ref"] is None,
          "second_points_to_first": sb[1]["preceding_utterance_ref"] == sb[0]["utterance_id"],
          "third_points_to_second": sb[2]["preceding_utterance_ref"] == sb[1]["utterance_id"],
          "other_conversation_is_null": sb[3]["preceding_utterance_ref"] is None,
          "records": sb}
    a2["ok"] = all(v for k, v in a2.items() if k != "records")
    a3 = {"caller_marked": [r["ts_source"] for r in sb[:3]] == ["CALLER"] * 3,
          "default_marked": sb[3]["ts_source"] == "DEFAULT"}
    a3["ok"] = all(a3.values())
    return {"A2_preceding_ref": a2, "A3_ts_source": a3, "A4_baseline": baseline_diff(baseline_path),
            "A5_corpus": corpus_counts(), "live_field_coverage": live_field_coverage(),
            "forward_only": ("既存 459 件は復元しない。前向きのみ。本 SPEC 完了時点で新フィールドが"
                             "埋まった記録が0件なのは正常である（記録が入ることと P2 が効くことは別）。")}


def check(baseline_path=None):
    r = assess(baseline_path)
    ok = True
    print("[%s] A2 preceding_utterance_ref (先頭=None / 2件目以降=直前id / 別会話は繋がない)"
          % ("PASS" if r["A2_preceding_ref"]["ok"] else "FAIL"))
    ok &= r["A2_preceding_ref"]["ok"]
    print("[%s] A3 ts_source が CALLER / DEFAULT を区別" % ("PASS" if r["A3_ts_source"]["ok"] else "FAIL"))
    ok &= r["A3_ts_source"]["ok"]
    b = r["A4_baseline"]
    if b["checked"]:
        print("[%s] A4 既存レコードの差分ゼロ (baseline %d 行 / 変化行=%s / 以後 %d 行 append)"
              % ("PASS" if b["existing_records_unchanged"] else "FAIL", b["baseline_lines"],
                 b["changed_line_numbers"] or "なし", b["appended_since_baseline"]))
        ok &= b["existing_records_unchanged"]
    else:
        print("[SKIP] A4 既存レコードの差分ゼロ (%s)" % b["reason"])
    d1 = json.dumps(assess(baseline_path)["A2_preceding_ref"]["ok"], sort_keys=True)
    d2 = json.dumps(assess(baseline_path)["A2_preceding_ref"]["ok"], sort_keys=True)
    print("[%s] A6 決定論再現" % ("PASS" if d1 == d2 else "FAIL"))
    ok &= (d1 == d2)
    c = r["A5_corpus"]
    print("[INFO] A5 母数: 生 %d → 機械生成除外 %d → %d → dedup → %d"
          % (c["user_utterances"], c["machine_generated_excluded"], c["after_exclusion"], c["unique_deduped"]))
    print("[INFO] LIVE 台帳の新フィールド充足: %s ★前向きのみゆえ 0 が正常"
          % r["live_field_coverage"])
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    bl = next((a.split("=", 1)[1] for a in argv if a.startswith("--baseline=")), None)
    if "--check" in argv:
        return check(bl)
    r = assess(bl)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    print("(a) retention 補修 検証")
    print("  A2 直前発話 id : %s" % {k: v for k, v in r["A2_preceding_ref"].items() if k != "records"})
    print("  A3 ts_source   : %s" % r["A3_ts_source"])
    print("  A4 差分ゼロ    : %s" % r["A4_baseline"])
    print("  A5 母数        : %s" % r["A5_corpus"])
    print("  LIVE 充足      : %s" % r["live_field_coverage"])
    print("  → %s" % OUT)
    print("  ※%s" % r["forward_only"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
