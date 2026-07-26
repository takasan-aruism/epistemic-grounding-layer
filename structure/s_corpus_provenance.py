#!/usr/bin/env python3
"""s_corpus_provenance — front door を通った入力の母数を、除外規則ごとに確定する（MGR 依頼A / I-2）。

★背景: 「実発話の 42% が400字超・平均3446字」は**我々自身が機械生成した codegen プロンプトを実発話と誤認**した
  結果である疑いが出た（計器が自分の活動を食う・3例目）。**除外規則を列挙して記録し、negative control を付ける。**

★規律（本スクリプトの設計方針）:
  - 除外規則は **我々自身の生成テンプレートに由来する構造的マーカー**に限る。**「長いから除外」はしない。**
  - **数字が望む形になるまで規則を足さない。** 規則を足したら**理由と件数と実例**を必ず出す。
  - **残った長文は残ったまま出す**（人が目視で判断できるように先頭を表示する）。**最終的な正典の確定は DESIGN/MGR。**
  - **negative control**: 人間の入力であることが明らかなものが除外されないことを検査する。

usage: s_corpus_provenance.py [--check]
"""
import json
import os
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "CORPUS_PROVENANCE.json")
CORPUS = "/home/takasan/ds/ds_events.jsonl"

# ── 除外規則（★列挙・記録・理由つき）───────────────────────────────────────────────────────────────
#    kind: PREFIX = 先頭一致 / CONTAINS = 含む
RULES = [
    {"id": "R1-DE-ADMISSION", "kind": "PREFIX", "marker": "開発エビデンスを登録",
     "why": "front door の DE 記録ラッパ de_submit_route.build_raw_input が生成する決定論文字列"},
    {"id": "R2-DE-ADMISSION-ALT", "kind": "PREFIX", "marker": "開発根拠を登録",
     "why": "同じ DE 記録の旧表記。同一の機械生成系統"},
    {"id": "R3-GEN-NONCE", "kind": "CONTAINS", "marker": "# gen-nonce",
     "why": "codegen ループが投入するプロンプトの nonce ヘッダ"},
    {"id": "R4-IMPLEMENT-STANDALONE", "kind": "CONTAINS", "marker": "IMPLEMENT a NEW standalone",
     "why": "codegen プロンプトのテンプレート文言"},
    {"id": "R5-MUST-CONTAIN", "kind": "CONTAINS", "marker": "MUST contain",
     "why": "同上（受入条件節のテンプレート）"},
    {"id": "R6-STDLIB-ONLY", "kind": "CONTAINS", "marker": "stdlib ONLY",
     "why": "同上（依存制約節のテンプレート）"},
    {"id": "R7-BUILD-CAPABILITY-TASK", "kind": "CONTAINS", "marker": "BUILD_CAPABILITY / 新規コード実装",
     "why": "我々が書いた実装タスク投入テンプレートの見出し。人間の会話文には現れない"},
    {"id": "R8-IMPLEMENT-ITEM", "kind": "CONTAINS", "marker": "IMPLEMENT ITEM-",
     "why": "ITEM 仕様の実装指示テンプレート"},
]
# negative control: 人間の入力であることが明らかで、**除外されてはならない**もの
NEGATIVE_CONTROL = ["本番環境を調べて", "前の件を優先して進めて", "ベトナム語アプリを直して",
                    "schedulerを復活させて検知に使って"]


def _matches(rule, text):
    return text.startswith(rule["marker"]) if rule["kind"] == "PREFIX" else (rule["marker"] in text)


def load_user_utterances():
    out = []
    with open(CORPUS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("record_type") == "UTTERANCE" and r.get("speaker") == "USER":
                out.append(r.get("raw_text", ""))
    return out


def assess():
    raw = load_user_utterances()
    # 規則ごとの件数（★any-match と first-match の両方を出す。重なりを隠さない）
    any_match = {r["id"]: sum(1 for t in raw if _matches(r, t)) for r in RULES}
    first_match = {r["id"]: 0 for r in RULES}
    kept = []
    for t in raw:
        hit = next((r["id"] for r in RULES if _matches(r, t)), None)
        if hit:
            first_match[hit] += 1
        else:
            kept.append(t)
    uniq = list(dict.fromkeys(kept))
    lens = sorted(len(x) for x in uniq)
    over400 = [x for x in uniq if len(x) > 400]
    # 残った長文（人が目視で判断できるように）
    residual = [{"len": len(x), "head": x[:110].replace("\n", " ")}
                for x in sorted(uniq, key=len, reverse=True)[:10]]
    # negative control
    nc = [{"text": t, "excluded": any(_matches(r, t) for r in RULES)} for t in NEGATIVE_CONTROL]
    return {
        "series": {"raw_user_utterances": len(raw),
                   "excluded_total": len(raw) - len(kept),
                   "after_exclusion": len(kept),
                   "unique_deduped": len(uniq)},
        "per_rule_first_match": first_match, "per_rule_any_match": any_match,
        "rules": RULES,
        "length": {"median": lens[len(lens) // 2] if lens else None,
                   "mean": round(sum(lens) / len(lens), 1) if lens else None,
                   "max": lens[-1] if lens else None,
                   "over_400_n": len(over400),
                   "over_400_pct": round(100.0 * len(over400) / len(uniq), 1) if uniq else None},
        "residual_longest": residual,
        "negative_control": nc,
        "negative_control_ok": all(not c["excluded"] for c in nc),
        "caveat": ("★正典の確定は DESIGN/MGR。本スクリプトは規則ごとの件数と残りを出すだけである。"
                   "残った長文が依然として機械生成に見える場合、規則が足りない可能性があるが、"
                   "**数字が望む形になるまで規則を足すことはしない**（計器を自分に有利にしないため）。"),
    }


def check():
    r = assess()
    ok = True
    print("[%s] negative control: 人間の入力が除外されない (%d 件)"
          % ("PASS" if r["negative_control_ok"] else "FAIL", len(r["negative_control"])))
    for c in r["negative_control"]:
        if c["excluded"]:
            print("       - 誤除外: %s" % c["text"])
    ok &= r["negative_control_ok"]
    ids = [x["id"] for x in RULES]
    print("[%s] 除外規則が一意に列挙されている (%d 件)" % ("PASS" if len(ids) == len(set(ids)) else "FAIL", len(ids)))
    ok &= len(ids) == len(set(ids))
    a = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    print("[%s] 決定論再現" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    r = assess()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    s = r["series"]
    print("front door を通った入力の母数（★『実発話』とは書かない）")
    print("  生 USER 発話           : %d" % s["raw_user_utterances"])
    print("  除外（規則ごと・first-match / any-match）:")
    for rule in RULES:
        print("    %-26s %-4d / %-4d  %s"
              % (rule["id"], r["per_rule_first_match"][rule["id"]], r["per_rule_any_match"][rule["id"]],
                 rule["why"][:40]))
    print("  除外合計               : %d" % s["excluded_total"])
    print("  除外後                 : %d" % s["after_exclusion"])
    print("  ★dedup 後（候補母数）  : %d" % s["unique_deduped"])
    L = r["length"]
    print("  長さ: 中央値 %s / 平均 %s / 最大 %s / 400字超 %d件 = %s%%"
          % (L["median"], L["mean"], L["max"], L["over_400_n"], L["over_400_pct"]))
    print("  残った長い入力（★目視用・機械生成に見えるなら規則が足りない）:")
    for x in r["residual_longest"][:6]:
        print("    [%5d] %s" % (x["len"], x["head"]))
    print("  → %s" % OUT)
    print("  ※%s" % r["caveat"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
