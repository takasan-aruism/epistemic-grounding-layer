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
