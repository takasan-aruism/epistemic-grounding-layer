"""EGL core: append-only event log (SoR) + rebuildable SQLite view + Run Ledger.

決定 K-1: jsonl = 正本(append-only), SQLite = current-state view(常時再構築可能, RC-3)。
event は「部分 payload の merge」意味論(coarse event-sourcing)。
rebuild は events を時系列 merge するだけ → RC-3/RC-4(time-travel)を満たす。
"""
import json, os, sqlite3, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
EVENTS = DATA / "events.jsonl"
SQLITE = DATA / "state.sqlite"
COUNTERS = DATA / "counters.json"

# ESTABLISHED axes (AX-6): claim_key はこの部分集合のみから作る(AX-2)
ESTABLISHED_AXES = ["runtime", "runtime_version", "gpu_arch", "quant", "model",
                    "os", "driver_version", "cuda_version", "kv_dtype"]


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def plus_days(days):
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).isoformat()


def new_id(prefix):
    c = json.loads(COUNTERS.read_text()) if COUNTERS.exists() else {}
    c[prefix] = c.get(prefix, 0) + 1
    COUNTERS.write_text(json.dumps(c))
    return f"{prefix}-{c[prefix]:05d}"


# ---------- Event log (append-only, 正本) ----------
def append_event(run_id, event_type, object_type, object_id, payload):
    ev = {"event_id": new_id("EV"), "ts": now_iso(), "run_id": run_id,
          "event_type": event_type, "object_type": object_type,
          "object_id": object_id, "payload": payload}
    with open(EVENTS, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def read_events(until_ts=None):
    if not EVENTS.exists():
        return []
    out = []
    for line in EVENTS.read_text().splitlines():
        if line.strip():
            ev = json.loads(line)
            if until_ts is None or ev["ts"] <= until_ts:
                out.append(ev)
    return out


def claim_key(state):
    """OM/§14.2: ESTABLISHED 軸のみから安定 key を作る。"""
    if state.get("object_kind") not in ("CandidateClaim", "Claim"):
        return None
    scope = state.get("scope", {})
    axes = {k: scope[k] for k in ESTABLISHED_AXES if k in scope}
    body = ",".join(f"{k}={axes[k]}" for k in sorted(axes))
    return f"{state.get('claim_type')}:{state.get('predicate')}({body})"


# ---------- SQLite current-state view (RC-3: rebuildable) ----------
def build_view(db_path=SQLITE, until_ts=None):
    if os.path.exists(db_path):
        os.remove(db_path)
    merged = {}   # object_id -> (object_type, state dict)  ← merge 意味論
    for ev in read_events(until_ts):
        oid = ev["object_id"]
        cur = merged.get(oid, (ev["object_type"], {}))[1]
        merged[oid] = (ev["object_type"], {**cur, **ev["payload"]})
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE objects(object_id TEXT PRIMARY KEY, object_type TEXT,
                   state_json TEXT, claim_key TEXT)""")
    for oid, (ot, st) in merged.items():
        con.execute("INSERT INTO objects VALUES(?,?,?,?)",
                    (oid, ot, json.dumps(st, ensure_ascii=False), claim_key(st)))
    con.commit()
    return con


def get(con, object_id):
    r = con.execute("SELECT state_json FROM objects WHERE object_id=?", (object_id,)).fetchone()
    return json.loads(r[0]) if r else None


def by_type(con, object_type):
    return [json.loads(r[0]) for r in
            con.execute("SELECT state_json FROM objects WHERE object_type=?", (object_type,)).fetchall()]


# ---------- Run Ledger (RL-*) ----------
def run_start(actor, activity_type, task_id=None, inputs=None, irr="REPLAYABLE"):
    rid = new_id("RUN")
    append_event(rid, "CREATE", "Run", rid,
                 {"id": rid, "actor": actor, "activity_type": activity_type,
                  "task_id": task_id, "inputs": inputs or [], "outputs": [],
                  "irreversibility_class": irr, "status": "RUNNING",
                  "started_at": now_iso()})
    return rid


def run_end(rid, outputs, status="COMPLETED"):
    append_event(rid, "UPDATE", "Run", rid,
                 {"outputs": outputs, "status": status, "ended_at": now_iso()})
