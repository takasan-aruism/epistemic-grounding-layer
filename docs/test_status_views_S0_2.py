"""S0 immutable tests — 観測ビューの合否契約。作者: Claude(web)。
runner が workspace 外原本から供給する。実装者は変更不能。"""
import hashlib
import json
from pathlib import Path

import pytest

from status_views import (ViewError, build, derive_metrics, load_backlog,
                          load_gaps, load_ledger, load_runs, render_html)


def rec_hash(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "record_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def write_log(path: Path, records: list[dict], break_chain=False):
    """runner 互換の hash chain 付き run_log を作る。"""
    prev = "0" * 64
    lines = []
    for i, r in enumerate(records):
        rec = {"run_id": "R1", "seq": i, "ts": "2026-07-19T00:00:00Z",
               "prev_hash": prev, **r}
        rec["record_hash"] = rec_hash(rec)
        prev = rec["record_hash"]
        lines.append(json.dumps(rec, ensure_ascii=False))
    if break_chain and lines:
        bad = json.loads(lines[-1])
        bad["kind"] = "TAMPERED"          # record_hash を更新しない
        lines[-1] = json.dumps(bad, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_run(root: Path, run_id: str, status="PASSED", it=1,
             needs_human=False, break_chain=False, with_packet=True):
    d = root / run_id
    d.mkdir(parents=True)
    if with_packet:
        (d / "RESULT_PACKET.json").write_text(json.dumps(
            {"run_id": run_id, "task_id": "T", "status": status,
             "iterations_used": it, "needs_human": needs_human}),
            encoding="utf-8")
    write_log(d / "run_log.jsonl", [
        {"kind": "PACKET_START", "task_id": "T"},
        {"kind": "MODEL_REPLY", "iteration": 1, "reply": "x" * 500},
        {"kind": "TEST_RUN", "iteration": 1, "exit_code": 0,
         "output_tail": "1 passed"},
    ], break_chain=break_chain)
    return d


# ---------- load_runs ----------

def test_load_runs_basic(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "20260719T01Z-a")
    runs = load_runs(root)
    assert len(runs) == 1
    r = runs[0]
    assert r["run_id"] == "20260719T01Z-a" and r["status"] == "PASSED"
    assert r["chain_ok"] is True and r["chain_detail"] == "ok"
    assert r["events"] == 3
    assert r["iterations"][0]["test_exit_code"] == 0
    assert len(r["iterations"][0]["reply_excerpt"]) <= 200


def test_load_runs_detects_broken_chain(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1", break_chain=True)
    r = load_runs(root)[0]
    assert r["chain_ok"] is False and r["chain_detail"] != "ok"


def test_load_runs_missing_packet_is_unreadable(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1", with_packet=False)
    r = load_runs(root)[0]
    assert r["status"] == "UNREADABLE" and r["needs_human"] is True


def test_load_runs_sorted_desc_and_missing_root(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "aaa")
    make_run(root, "zzz")
    assert [r["run_id"] for r in load_runs(root)] == ["zzz", "aaa"]
    assert load_runs(tmp_path / "nope") == []


# ---------- load_gaps ----------

def gaps_file(tmp_path, lines):
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(json.dumps(x, ensure_ascii=False)
                           for x in lines) + "\n", encoding="utf-8")
    return p


def test_load_gaps_event_sourcing_merge(tmp_path):
    p = gaps_file(tmp_path, [
        {"event_id": "EV1", "object_type": "Claim", "object_id": "C1",
         "payload": {"x": 1}},
        {"event_id": "EV2", "object_type": "KnowledgeGap", "object_id": "G1",
         "payload": {"gap_id": "KGAP-1", "question": "q1", "status": "OPEN",
                     "required_for": ["REQ-005"]}},
        {"event_id": "EV3", "object_type": "KnowledgeGap", "object_id": "G1",
         "payload": {"status": "RESOLVED"}},
        {"event_id": "EV4", "object_type": "KnowledgeGap", "object_id": "G2",
         "payload": {"gap_id": "KGAP-2", "question": "q2", "status": "OPEN",
                     "required_for": []}},
    ])
    gaps = load_gaps(p)
    assert len(gaps) == 2                       # Claim は含まない
    by_id = {g["gap_id"]: g for g in gaps}
    assert by_id["KGAP-1"]["status"] == "RESOLVED"   # 後勝ち
    assert by_id["KGAP-1"]["question"] == "q1"       # マージ(消えない)
    assert by_id["KGAP-1"]["is_required"] is True
    assert by_id["KGAP-2"]["is_required"] is False
    assert gaps[0]["gap_id"] == "KGAP-1"             # required が先


def test_load_gaps_missing_file(tmp_path):
    assert load_gaps(tmp_path / "nope.jsonl") == []


# ---------- load_backlog / load_ledger ----------

def test_load_backlog_last_wins_and_state_order(tmp_path):
    p = tmp_path / "b.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in [
        {"id": "X1", "state": "OPEN", "title": "t"},
        {"id": "X1", "state": "DONE", "title": "t"},
        {"id": "A1", "state": "AWAITING_TAKA", "title": "t"},
        {"id": "B1", "state": "WEIRD_STATE", "title": "t"},
    ]) + "\n", encoding="utf-8")
    b = load_backlog(p)
    assert [x["id"] for x in b] == ["A1", "X1", "B1"]  # 未知stateは最後


def test_load_ledger_flexible_key_and_unparsed(tmp_path):
    p = tmp_path / "de.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in [
        {"de_id": "DE-0002", "note": "b"},
        {"id": "DE-0001", "note": "a"},
        {"no_identifier": True},
    ]) + "\n", encoding="utf-8")
    led = load_ledger(p)
    assert [x["de_id"] for x in led] == ["DE-0002", "DE-0001"]  # 降順


# ---------- metrics ----------

def test_derive_metrics(tmp_path):
    runs = [{"status": "PASSED", "needs_human": False, "chain_ok": True},
            {"status": "BUDGET_EXHAUSTED", "needs_human": True,
             "chain_ok": False}]
    gaps = [{"status": "OPEN", "is_required": True},
            {"status": "OPEN", "is_required": False},
            {"status": "RESOLVED", "is_required": True}]
    backlog = [{"id": "1", "state": "AWAITING_TAKA"}, {"id": "2", "state": "DONE"}]
    ledger = [{"de_id": "DE-1", "record": {}}]
    m = derive_metrics(runs, gaps, backlog, ledger, unparsed=3)
    assert m["runs_total"] == 2 and m["runs_passed"] == 1
    assert m["runs_needs_human"] == 1 and m["chain_failed"] == 1
    assert m["gaps_total"] == 3 and m["gaps_open"] == 2
    assert m["gaps_required_open"] == 1
    assert m["backlog_awaiting"] == 1 and m["backlog_done"] == 1
    assert m["ledger_count"] == 1 and m["unparsed_lines"] == 3


# ---------- render / build ----------

def test_render_html_contains_required_markers():
    runs = [{"run_id": "r1", "task_id": "T", "status": "BUDGET_EXHAUSTED",
             "iterations_used": 2, "needs_human": True, "chain_ok": False,
             "chain_detail": "line 2: seq", "iterations": [], "events": 3}]
    gaps = [{"gap_id": "KGAP-1", "question": "q", "status": "OPEN",
             "required_for": ["R"], "is_required": True}]
    backlog = [{"id": "X", "state": "AWAITING_TAKA", "title": "t"}]
    ledger = [{"de_id": "DE-1", "record": {}}]
    m = derive_metrics(runs, gaps, backlog, ledger, unparsed=2)
    html = render_html(m, runs, gaps, backlog, ledger, "2026-07-19T00:00:00Z")
    for token in ["2DER", "2026-07-19T00:00:00Z", "derived", "METRICS",
                  "RUNS", "GAPS", "BACKLOG", "LEDGER", "r1",
                  "BUDGET_EXHAUSTED", "CHAIN_FAIL", "NEEDS_HUMAN",
                  "REQUIRED", "UNPARSED"]:
        assert token in html, f"missing marker: {token}"


def test_render_html_escapes():
    runs = [{"run_id": "<script>x</script>", "task_id": "T&T",
             "status": "PASSED", "iterations_used": 1, "needs_human": False,
             "chain_ok": True, "chain_detail": "ok", "iterations": [],
             "events": 1}]
    m = derive_metrics(runs, [], [], [], unparsed=0)
    html = render_html(m, runs, [], [], [], "2026-07-19T00:00:00Z")
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_build_end_to_end(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1")
    ev = gaps_file(tmp_path, [
        {"event_id": "EV1", "object_type": "KnowledgeGap", "object_id": "G1",
         "payload": {"gap_id": "KGAP-1", "question": "q", "status": "OPEN",
                     "required_for": ["REQ-1"]}}])
    out = build({"runs_root": str(root), "out_title": "2DER",
                 "events": str(ev)})
    assert "html" in out and "metrics" in out
    assert out["metrics"]["runs_total"] == 1
    assert out["metrics"]["gaps_required_open"] == 1
    assert "REQUIRED" in out["html"]


def test_build_requires_config_keys(tmp_path):
    with pytest.raises(ViewError):
        build({"out_title": "2DER"})


def test_build_writes_nothing(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1")
    before = sorted(p.name for p in tmp_path.iterdir())
    build({"runs_root": str(root), "out_title": "2DER"})
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_malformed_lines_counted_not_crashing(tmp_path):
    p = tmp_path / "b.jsonl"
    p.write_text('{"id":"A","state":"OPEN"}\nNOT JSON\n', encoding="utf-8")
    b = load_backlog(p)          # 例外を投げない
    assert len(b) == 1


# ============ S0.1 追加: REPOS / PROBE ============

from status_views import load_probe, load_repos  # noqa: E402


def repos_file(tmp_path, obj):
    p = tmp_path / "repos.json"
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p


def test_load_repos_basic_and_sorted(tmp_path):
    p = repos_file(tmp_path, {"generated_at": "T", "repos": [
        {"name": "twoder", "head": "abc1234", "dirty": 2, "sync": "0/0"},
        {"name": "egl", "head": "6a4b508", "dirty": 0, "sync": "0/0",
         "error": None}]})
    r = load_repos(p)
    assert [x["name"] for x in r] == ["egl", "twoder"]
    assert r[0]["is_dirty"] is False and r[1]["is_dirty"] is True
    assert r[1]["dirty"] == 2


def test_load_repos_defaults_for_missing_keys(tmp_path):
    p = repos_file(tmp_path, {"repos": [{"name": "x"}]})
    r = load_repos(p)[0]
    assert r["head"] == "?" and r["dirty"] == -1 and r["sync"] == "?"
    assert r["error"] is None and r["is_dirty"] is False


def test_load_repos_missing_or_broken(tmp_path):
    assert load_repos(tmp_path / "nope.json") == []
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_repos(bad) == []
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"repos": "notalist"}), encoding="utf-8")
    assert load_repos(wrong) == []


def probe_dir(tmp_path, name, rows):
    d = tmp_path / "probes"
    d.mkdir(exist_ok=True)
    (d / name).write_text("\n".join(json.dumps(r) for r in rows) + "\n",
                          encoding="utf-8")
    return d


def test_load_probe_picks_newest_and_flags(tmp_path):
    probe_dir(tmp_path, "probe-20260719T01Z.jsonl",
              [{"check": "4a", "verdict": "LEAKED"}])
    d = probe_dir(tmp_path, "probe-20260720T02Z.jsonl", [
        {"check": "4a", "verdict": "BLOCKED"},
        {"check": "4d", "verdict": "OK"},
        {"check": "4f", "verdict": "LEAKED"}])
    pr = load_probe(d)
    assert pr["file"].endswith("probe-20260720T02Z.jsonl")   # 新しい方
    assert [c["check"] for c in pr["checks"]] == ["4a", "4d", "4f"]
    assert [c["ok"] for c in pr["checks"]] == [True, True, False]
    assert pr["all_ok"] is False


def test_load_probe_all_ok_and_alt_keys(tmp_path):
    d = probe_dir(tmp_path, "probe-a.jsonl", [
        {"id": "4a", "result": "blocked"},
        {"name": "4b", "status": "PASS"}])
    pr = load_probe(d)
    assert pr["all_ok"] is True and len(pr["checks"]) == 2


def test_load_probe_absent_is_fail_closed(tmp_path):
    pr = load_probe(tmp_path / "nodir")
    assert pr["checks"] == [] and pr["all_ok"] is False and pr["file"] == ""
    empty = tmp_path / "empty"
    empty.mkdir()
    assert load_probe(empty)["all_ok"] is False


def test_metrics_with_repos_and_probe():
    repos = [{"name": "a", "is_dirty": True, "dirty": 3},
             {"name": "b", "is_dirty": False, "dirty": 0}]
    probe = {"file": "p.jsonl", "all_ok": False, "checks": [
        {"check": "4a", "verdict": "BLOCKED", "ok": True},
        {"check": "4f", "verdict": "LEAKED", "ok": False}]}
    m = derive_metrics([], [], [], [], 0, repos=repos, probe=probe)
    assert m["repos_total"] == 2 and m["repos_dirty"] == 1
    assert m["probe_checks"] == 2 and m["probe_failed"] == 1
    assert m["probe_all_ok"] is False


def test_metrics_without_repos_probe_is_fail_closed():
    m = derive_metrics([], [], [], [], 0)
    assert m["repos_total"] == 0 and m["repos_dirty"] == 0
    assert m["probe_checks"] == 0 and m["probe_failed"] == 0
    assert m["probe_all_ok"] is False        # 証拠なし = ok ではない


def test_render_repos_probe_markers():
    repos = [{"name": "egl", "head": "6a4b508", "dirty": 0, "sync": "0/0",
              "error": None, "is_dirty": False},
             {"name": "rri", "head": "deadbee", "dirty": 4, "sync": "1/0",
              "error": None, "is_dirty": True}]
    probe = {"file": "probe-x.jsonl", "all_ok": False, "checks": [
        {"check": "4a", "verdict": "BLOCKED", "ok": True},
        {"check": "4f", "verdict": "LEAKED", "ok": False}]}
    m = derive_metrics([], [], [], [], 0, repos=repos, probe=probe)
    html = render_html(m, [], [], [], [], "2026-07-20T00:00:00Z",
                       repos=repos, probe=probe)
    for token in ["REPOS", "egl", "6a4b508", "rri", "DIRTY",
                  "PROBE", "4a", "4f", "PROBE_FAIL"]:
        assert token in html, f"missing marker: {token}"


def test_render_no_probe_marker():
    probe = {"file": "", "all_ok": False, "checks": []}
    m = derive_metrics([], [], [], [], 0, probe=probe)
    html = render_html(m, [], [], [], [], "T", probe=probe)
    assert "NO_PROBE" in html


def test_build_with_repos_and_probe(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1")
    rp = repos_file(tmp_path, {"repos": [
        {"name": "egl", "head": "abc", "dirty": 1, "sync": "0/0"}]})
    d = probe_dir(tmp_path, "probe-1.jsonl",
                  [{"check": "4a", "verdict": "BLOCKED"}])
    out = build({"runs_root": str(root), "out_title": "2DER",
                 "repos": str(rp), "probe_dir": str(d)})
    assert out["metrics"]["repos_total"] == 1
    assert out["metrics"]["repos_dirty"] == 1
    assert out["metrics"]["probe_all_ok"] is True
    assert "REPOS" in out["html"] and "DIRTY" in out["html"]
    assert "PROBE" in out["html"]


def test_build_broken_repos_counts_unparsed(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1")
    bad = tmp_path / "repos.json"
    bad.write_text("{broken", encoding="utf-8")
    out = build({"runs_root": str(root), "out_title": "2DER",
                 "repos": str(bad)})
    assert out["metrics"]["unparsed_lines"] >= 1
    assert "UNPARSED" in out["html"]


def test_build_still_writes_nothing_with_new_inputs(tmp_path):
    root = tmp_path / "runs"
    make_run(root, "r1")
    rp = repos_file(tmp_path, {"repos": []})
    d = probe_dir(tmp_path, "probe-1.jsonl", [{"check": "4a",
                                               "verdict": "OK"}])
    before = sorted(p.name for p in tmp_path.iterdir())
    build({"runs_root": str(root), "out_title": "2DER",
           "repos": str(rp), "probe_dir": str(d)})
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# ============ S0.2 追加: 新イベント形式 / 後方互換 / LEDGER 修正 ============

def v2_rec_hash(rec):
    body = {k: v for k, v in rec.items() if k != "record_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def write_events(path: Path, records: list[dict], break_chain=False):
    """runner v0.2 / emit_api 互換の segment を作る。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = "0" * 64
    lines = []
    for i, r in enumerate(records):
        rec = {"schema_version": "1", "segment_id": "seg-000001",
               "sequence_in_segment": i, "previous_event_hash": prev,
               "previous_segment_root": "0" * 64,
               "kind": r["kind"], "lane": "real",
               "retention_class": r.get("retention_class", "CLOSEABLE"),
               "producer_version": "runner-v0.2",
               "ts": "2026-07-20T00:00:00Z",
               "payload": r.get("payload", {})}
        rec["record_hash"] = v2_rec_hash(rec)
        prev = rec["record_hash"]
        lines.append(json.dumps(rec, ensure_ascii=False))
    if break_chain and lines:
        bad = json.loads(lines[-1])
        bad["payload"] = {"forged": True}      # record_hash は更新しない
        lines[-1] = json.dumps(bad, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_run_v2(root: Path, run_id: str, status="PASSED", it=1,
                needs_human=False, break_chain=False):
    d = root / run_id
    d.mkdir(parents=True)
    (d / "RESULT_PACKET.json").write_text(json.dumps(
        {"run_id": run_id, "task_id": "T2", "status": status,
         "iterations_used": it, "needs_human": needs_human}), encoding="utf-8")
    write_events(d / "events" / "seg-000001.jsonl", [
        {"kind": "WORKCELL_PACKET_START", "retention_class": "PERMANENT",
         "payload": {"task_id": "T2"}},
        {"kind": "WORKCELL_MODEL_REPLY", "retention_class": "SUMMARIZABLE",
         "payload": {"iteration": 1, "reply": "y" * 500}},
        {"kind": "WORKCELL_TEST_RUN",
         "payload": {"iteration": 1, "exit_code": 0, "output_tail": "1 passed"}},
    ], break_chain=break_chain)
    return d


def test_v2_events_read_and_chain_ok(tmp_path):
    root = tmp_path / "runs"
    make_run_v2(root, "n1")
    r = load_runs(root)[0]
    assert r["status"] == "PASSED" and r["task_id"] == "T2"
    assert r["chain_ok"] is True and r["chain_detail"] == "ok"
    assert r["events"] == 3
    assert r["iterations"][0]["test_exit_code"] == 0
    assert r["iterations"][0]["output_tail"] == "1 passed"
    assert len(r["iterations"][0]["reply_excerpt"]) == 200


def test_v2_events_broken_chain_detected(tmp_path):
    root = tmp_path / "runs"
    make_run_v2(root, "n1", break_chain=True)
    r = load_runs(root)[0]
    assert r["chain_ok"] is False and r["chain_detail"] != "ok"


def test_legacy_and_new_runs_coexist(tmp_path):
    """既存 run(旧形式)が読めなくなることは退行。"""
    root = tmp_path / "runs"
    make_run(root, "old1")          # 旧形式 run_log.jsonl
    make_run_v2(root, "new1")       # 新形式 events/
    runs = {r["run_id"]: r for r in load_runs(root)}
    assert len(runs) == 2
    assert runs["old1"]["chain_ok"] is True and runs["old1"]["events"] == 3
    assert runs["new1"]["chain_ok"] is True and runs["new1"]["events"] == 3
    assert runs["old1"]["iterations"][0]["test_exit_code"] == 0
    assert runs["new1"]["iterations"][0]["test_exit_code"] == 0


def test_new_format_preferred_when_both_present(tmp_path):
    root = tmp_path / "runs"
    d = make_run(root, "both")                       # 旧形式を先に作る
    write_events(d / "events" / "seg-000001.jsonl", [
        {"kind": "WORKCELL_PACKET_START", "payload": {}},
        {"kind": "WORKCELL_TEST_RUN",
         "payload": {"iteration": 9, "exit_code": 3, "output_tail": "NEW"}}])
    r = load_runs(root)[0]
    assert r["events"] == 2                          # 新形式を採用
    assert r["iterations"][0]["iteration"] == 9
    assert r["iterations"][0]["output_tail"] == "NEW"


def test_no_event_record_is_fail_closed(tmp_path):
    root = tmp_path / "runs"
    d = root / "bare"
    d.mkdir(parents=True)
    (d / "RESULT_PACKET.json").write_text(json.dumps(
        {"run_id": "bare", "task_id": "T", "status": "PASSED",
         "iterations_used": 1, "needs_human": False}), encoding="utf-8")
    r = load_runs(root)[0]
    assert r["events"] == 0
    assert r["chain_ok"] is False          # 証拠なし = ok ではない


def test_ledger_accepts_design_evidence_id(tmp_path):
    p = tmp_path / "de.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in [
        {"design_evidence_id": "DE-0450", "note": "a"},
        {"de_id": "DE-0449"},
        {"no_identifier": True},
    ]) + "\n", encoding="utf-8")
    led = load_ledger(p)
    assert [x["de_id"] for x in led] == ["DE-0450", "DE-0449"]


def test_ledger_priority_design_evidence_id_first(tmp_path):
    p = tmp_path / "de.jsonl"
    p.write_text(json.dumps(
        {"id": "WRONG", "design_evidence_id": "DE-0451"}) + "\n",
        encoding="utf-8")
    assert load_ledger(p)[0]["de_id"] == "DE-0451"


def test_unidentified_not_counted_as_unparsed(tmp_path):
    root = tmp_path / "runs"
    make_run_v2(root, "n1")
    p = tmp_path / "de.jsonl"
    p.write_text("\n".join([
        json.dumps({"design_evidence_id": "DE-0450"}),
        json.dumps({"no_identifier": True}),      # 有効な JSON、識別子なし
        "NOT JSON AT ALL",                        # JSON 解析失敗
    ]) + "\n", encoding="utf-8")
    out = build({"runs_root": str(root), "out_title": "2DER",
                 "ledger": str(p)})
    m = out["metrics"]
    assert m["ledger_count"] == 1
    assert m["unparsed_lines"] == 1          # 解析失敗のみ
    assert m["ledger_unidentified"] == 1     # 識別子なしは別枠
    assert "UNIDENTIFIED" in out["html"]


def test_metrics_ledger_unidentified_defaults_zero():
    m = derive_metrics([], [], [], [], 0)
    assert m["ledger_unidentified"] == 0
