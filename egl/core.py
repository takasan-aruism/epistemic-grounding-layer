"""EGL core: append-only event log (SoR) + rebuildable SQLite view + Run Ledger.

決定 K-1: jsonl = 正本(append-only), SQLite = current-state view(常時再構築可能, RC-3)。
event は「部分 payload の merge」意味論(coarse event-sourcing)。
rebuild は events を時系列 merge するだけ → RC-3/RC-4(time-travel)を満たす。
"""
import json, os, re, sqlite3, datetime, fcntl, contextlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
# AB-0005: DATA は env EGL_DATA_DIR で差し替え可能(既定 = canonical data/)。
# 試験は import 前に EGL_DATA_DIR を別 dir に向け、canonical SoR を汚さない。
# SoR=一次資産。特に H5(event log だけからの id 復元)検証は、log を汚すテストでは
# 検証自体が信用できない → SoR 系変更(DE-0006〜)の前提としてこの分離を先行させる。
DATA = Path(os.environ.get("EGL_DATA_DIR", str(BASE / "data")))
DATA.mkdir(parents=True, exist_ok=True)
EVENTS = DATA / "events.jsonl"
SQLITE = DATA / "state.sqlite"
LOCK = DATA / ".idlock"          # H6: 採番+書込の critical section を跨プロセスで直列化

# DE-0006 (H5/H6): counters.json(events から導出不能な第2 SoR)を廃止。
# id は append_event 内で log の high-water から採番する。id が存在する ⟺ その id を刻む
# event が log に存在する、を保証(『採番→後で書込』の分離を消す)。high-water 復元は帰結。
# 採番と書込を同一 lock 内で行い、並行 run の id 衝突(H6)を防ぐ。
SELF = "\x00SELF"                # payload 値がこれなら、採番した object_id で置換(自己参照 alias)
_ID_RE = re.compile(r"^([A-Z]+)-(\d+)$")

# ESTABLISHED axes (AX-6): claim_key はこの部分集合のみから作る(AX-2)
ESTABLISHED_AXES = ["runtime", "runtime_version", "gpu_arch", "quant", "model",
                    "os", "driver_version", "cuda_version", "kv_dtype"]


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def plus_days(days):
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).isoformat()


@contextlib.contextmanager
def _idlock():
    """H6: 跨プロセス排他。high-water 読取〜event 書込を1つの critical section に。"""
    fd = open(LOCK, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def _high_water():
    """log 全 event の event_id / object_id から prefix 毎の最大連番を導出(単一 SoR)。
    counters.json を持たない=喪失し得ない。high-water は log からの帰結にすぎない。"""
    hw = {}
    if not EVENTS.exists():
        return hw
    for line in EVENTS.read_text().splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        for val in (ev.get("event_id"), ev.get("object_id")):
            m = _ID_RE.match(val) if isinstance(val, str) else None
            if m:
                p, n = m.group(1), int(m.group(2))
                if n > hw.get(p, 0):
                    hw[p] = n
    return hw


# ---------- M4 (DE-0007): 完全 revision 契約を append_event が構造強制 ----------
def _check_complete_revision(event_type, object_id, payload):
    """partial-update を構造 reject。UPDATE の payload は現 object の全キー(top-level +
    1段ネスト)を包含しなければならない。『完全 object を書く契約』を driver 正直性(M1)に
    委ねず append_event 側で検査する。shallow-merge の兄弟キー喪失(M4)を構造的に不可能に。"""
    if "id" not in payload:
        raise ValueError(f"M4: event for {object_id} lacks 'id' (not a complete object)")
    if event_type != "UPDATE":
        return
    cur = get_state(object_id)
    if not cur:
        return                                    # 未知 object への UPDATE は別問題(dangling)
    miss = [k for k in cur if k not in payload]
    if miss:
        raise ValueError(f"M4: UPDATE {object_id} drops top-level keys {miss}; "
                         "must carry complete revision (partial-update rejected)")
    for k, v in cur.items():                       # 1段ネストの兄弟キー喪失も検出(例: temporal)
        if isinstance(v, dict) and isinstance(payload.get(k), dict):
            nmiss = [nk for nk in v if nk not in payload[k]]
            if nmiss:
                raise ValueError(f"M4: UPDATE {object_id} drops nested {k}.{nmiss}; "
                                 "complete revision required")


# ---------- Event log (append-only, 正本) ----------
def append_event(run_id, event_type, object_type, object_id, payload, new_prefix=None):
    """new_prefix 指定時: object_id を log high-water から採番し返す(id-in-append, H5)。
    payload 中および run_id の SELF 番兵は採番した id で置換(自己 alias を1 event で完結)。
    採番と書込は _idlock 内=不可分(H6)。new_prefix 省略時は object_id をそのまま使う(UPDATE 等)。"""
    with _idlock():
        hw = _high_water()
        evid = f"EV-{hw.get('EV', 0) + 1:05d}"
        if new_prefix is not None:
            object_id = f"{new_prefix}-{hw.get(new_prefix, 0) + 1:05d}"
        if run_id is SELF:
            run_id = object_id
        pl = {k: (object_id if v is SELF else v) for k, v in payload.items()}
        _check_complete_revision(event_type, object_id, pl)   # M4: partial を構造 reject
        ev = {"event_id": evid, "ts": now_iso(), "run_id": run_id,
              "event_type": event_type, "object_type": object_type,
              "object_id": object_id, "payload": pl}
        with open(EVENTS, "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return object_id


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


def get_state(object_id, until_ts=None):
    """object の現在状態を log から merge して返す(RMW の read 面)。
    DE-0007: UPDATE は完全 revision を書く必要があるため、変更前にこれで全キーを取得する。"""
    st = {}
    for ev in read_events(until_ts):
        if ev.get("object_id") == object_id:
            st = {**st, **ev["payload"]}
    return st


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
    # Run は id == run_id。両方を採番済み id に(SELF 番兵で1 event 完結)。
    return append_event(SELF, "CREATE", "Run", None,
                        {"id": SELF, "actor": actor, "activity_type": activity_type,
                         "task_id": task_id, "inputs": inputs or [], "outputs": [],
                         "irreversibility_class": irr, "status": "RUNNING",
                         "started_at": now_iso()}, new_prefix="RUN")


def run_end(rid, outputs, status="COMPLETED"):
    # M4: 完全 revision を書く(現 Run 状態を読み、lifecycle フィールドを更新して全体を再書込)。
    st = get_state(rid)
    st.update({"outputs": outputs, "status": status, "ended_at": now_iso()})
    append_event(rid, "UPDATE", "Run", rid, st)
