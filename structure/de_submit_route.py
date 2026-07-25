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


def now_ts():
    """実時刻(UTC・DE ledger の admitted_at 形式 2026-07-25T11:45:21Z)。de_admission 直叩きと同じ実時刻源。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def admit_via_submit(candidate, ts=None, ledger_path=None):
    """front door(submit)経由で DE を admit。submit が DS→RRI classify→egl.de_admission→residual→DS thread を回す。
    slice1b: ts を submit へ**実注入**(submit は受領のみ・生成しない)。ts 未指定=実時刻を生成して渡す
    (呼び手が実時刻を与える＝de_admission 直叩きと同じ源＝admitted_at の実時刻運用を維持)。
    返り (result, trace): result=TRACE['EGL_ADMISSION_RESULT']（直叩きと同一関数の戻り）、trace=front-door provenance。"""
    import twoder.submit as SUB
    if ts is None:
        ts = now_ts()
    raw = build_raw_input(candidate)
    trace = SUB.submit(raw, admission_payload=dict(candidate), ledger_path=ledger_path, ts=ts)
    return trace.get("EGL_ADMISSION_RESULT"), trace


def record_de(candidate, ts=None, ledger_path=None, route=None):
    """正典 DE 記録ルーチン(slice1c switch)。**既定=front door**(submit 経由・実 ts=admit_via_submit)。

    我々の DE 記録が正面玄関(DS→RRI→egl.de_admission→residual→DS thread)を通る内部アクター化の入口。
    切替点は**呼び出し口のみ**(de_admission 本体/ledger schema は不変・sole-writer=egl.de_admission)。

    route: "submit"(既定・front door) / "direct"(rollback=直叩き admit_design_evidence)。
      解決順: 引数 route → env `DE_ROUTE` → "submit"。**Rollback 手順**: `record_de(cand, route="direct")`
      もしくは `DE_ROUTE=direct` を export すれば即 直叩きへ戻る(直叩き未閉塞・並行運用)。
    返り: admission result(直叩きと同形: admitted/design_evidence_id/admission_status/…)。
    """
    import os as _os
    r = route or _os.environ.get("DE_ROUTE") or "submit"
    if ts is None:
        ts = now_ts()
    if r == "direct":
        from egl import de_admission as DEA
        return DEA.admit_design_evidence(dict(candidate), ts, ledger_path=ledger_path)
    result, _trace = admit_via_submit(candidate, ts=ts, ledger_path=ledger_path)
    return result
