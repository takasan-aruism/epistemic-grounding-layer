#!/usr/bin/env python3
"""VALIDATION_TARGET 軸(DE-0047 / Taka 暫定裁定)のテスト。ネットワーク非依存。
記録存在(RECORD_OCCURRENCE)/ 内容真偽(CONTENT_ASSERTION)/ 挙動(BEHAVIORAL_PROPERTY)を分け、
記録が在るだけで内容真理・挙動を自動確立しない線を検査。"""
import sys
from egl import validation_target as VT

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


def t_targets():
    check("RECORD_OCCURRENCE: 記録が在れば eligible", VT.target_problem("RECORD_OCCURRENCE", {"RECORD"}) is None)
    check("RECORD_OCCURRENCE: 記録が無ければ不足", VT.target_problem("RECORD_OCCURRENCE", set()) is not None)
    # 核心の線: 記録が在るだけでは BEHAVIORAL_PROPERTY を確立しない(DE-0036 が実際に直したか、は artifact/test 要)
    check("BEHAVIORAL_PROPERTY: 記録単独では不足(記録存在≠挙動)",
          VT.target_problem("BEHAVIORAL_PROPERTY", {"RECORD"}) is not None)
    check("BEHAVIORAL_PROPERTY: test/run artifact があれば eligible",
          VT.target_problem("BEHAVIORAL_PROPERTY", {"RECORD", "TEST_ARTIFACT"}) is None)
    # 内容真偽は record occurrence 単独では立たない
    check("CONTENT_ASSERTION: record occurrence 単独では不足(記録存在≠内容真理)",
          VT.target_problem("CONTENT_ASSERTION", {"RECORD"}) is not None)
    check("CONTENT_ASSERTION: adjudication/corroboration があれば eligible",
          VT.target_problem("CONTENT_ASSERTION", {"RECORD", "ADJUDICATED"}) is None)
    check("未知 target → problem", VT.target_problem("BOGUS", {"RECORD"}) is not None)


def t_line_preservation():
    # 線の保存規則が明示されている(RECORD_OCCURRENCE は内容真理/挙動/測定を自動確立しない)
    mn = VT.MUST_NOT_AUTO_ESTABLISH["RECORD_OCCURRENCE"]
    check("線: RECORD_OCCURRENCE は『X が外部事実として真』を自動確立しない",
          any("externally true" in x for x in mn))
    check("線: RECORD_OCCURRENCE は『実装が X の通り振る舞う』を自動確立しない",
          any("implementation behaves" in x for x in mn))
    # 逆方向も別 Claim
    check("線(逆): BEHAVIORAL_PROPERTY は『設計判断が記録された』を含意しない",
          any("recorded" in x for x in VT.MUST_NOT_AUTO_ESTABLISH["BEHAVIORAL_PROPERTY"]))


if __name__ == "__main__":
    print("=== VALIDATION_TARGET 軸 (DE-0047, PROVISIONAL) ===")
    print("\n[targets] target 別 eligible evidence"); t_targets()
    print("\n[line] 記録存在 vs 内容真偽 vs 挙動 の線の保存"); t_line_preservation()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("記録が在る(RECORD_OCCURRENCE)だけでは内容真理も挙動も自動では立たない=線を型で保存。")
