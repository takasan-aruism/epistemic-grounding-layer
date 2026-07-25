#!/usr/bin/env python3
"""de_submit_route — DE 記録を front door(twoder.submit)経由で admit する薄い入口。

front-door 移行(A) slice1。我々の DE 記録を `egl.de_admission` 直叩き(=公式 bypass)でなく、submit の
DE-admission fast path(DS→RRI classify→egl.de_admission→residual→DS thread)経由にする第一歩。
[[ai-must-be-internal-actor-not-intruder]]（正面玄関から入る内部アクター）。

- **egl.de_admission は依然 sole ledger writer**（submit はそれを呼ぶだけ・手動 append しない）。
- payload=現行 DE candidate dict そのまま（新スキーマ不要）。raw_input は AR.detect を is_admission=True にするための決定論生成。
- 注: `twoder.submit.submit` は ts をハードコード("2026-07-11T08:00:00")＝引数を取らない。ゆえ本ラッパの ts は
  API 対称性のため受けるだけで submit へは注入しない(submit が正典 ts を持つ)。同値検証は submit の ts に合わせる。
"""
import os
import sys

ROOT = "/home/takasan"
for _p in (ROOT, ROOT + "/ds", ROOT + "/rri", ROOT + "/egl", ROOT + "/dev-workcell"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

MARKER = "開発エビデンスを登録"   # rri.admission_request.detect を is_admission_request=True にする決定論キーワード


def build_raw_input(candidate):
    """candidate から admission raw_input を決定論生成(AR.detect=True にするのが目的・payload が正典)。"""
    did = candidate.get("design_evidence_id") or "DE-?"
    obs = str(candidate.get("observation", ""))[:120]
    return "%s: %s — %s" % (MARKER, did, obs)


def admit_via_submit(candidate, ts=None, ledger_path=None):
    """front door(submit)経由で DE を admit。submit が DS→RRI classify→egl.de_admission→residual→DS thread を回す。
    返り (result, trace): result=TRACE['EGL_ADMISSION_RESULT']（直叩きと同一関数の戻り）、trace=front-door provenance。
    ts は submit がハードコードするため注入しない(API 対称性のため受けるだけ)。"""
    import twoder.submit as SUB
    raw = build_raw_input(candidate)
    trace = SUB.submit(raw, admission_payload=dict(candidate), ledger_path=ledger_path)
    return trace.get("EGL_ADMISSION_RESULT"), trace
