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
    if event_type not in ("UPDATE", "CORRECTION", "COMPLETION"):  # 後続 state 変更=完全 revision 必須
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
def append_event(run_id, event_type, object_type, object_id, payload, new_prefix=None,
                 principal=None, capability=None):
    """new_prefix 指定時: object_id を log high-water から採番し返す(id-in-append, H5)。
    payload 中および run_id の SELF 番兵は採番した id で置換(自己 alias を1 event で完結)。
    採番と書込は _idlock 内=不可分(H6)。new_prefix 省略時は object_id をそのまま使う(UPDATE 等)。
    R1: principal/capability を刻む(semantic write authority を audit で検出可能にする)。"""
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
        if principal is not None:
            ev["principal"] = principal
        if capability is not None:
            ev["capability"] = capability
        with open(EVENTS, "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return object_id


# ---------- R1 (DE-0021): semantic write authority(検出水準、prevention でない)----------
# physical sole-writer(append_event)は成立するが、どの actor がどの event_type を発行してよいか
# =semantic authority は別。単一プロセス内では capability を forge し得るので『違反不可能』は保証
# しない(それを騙るのが本系列が繰返し捕まった過大報告)。保証は『違反が必ず検出可能』=
# 発行(GRANT)記録なき capability での privileged write を audit_write_authority が機械検出。
# 将来プロセス分離すれば同じ registry で prevention へ硬化できる。
PRIVILEGED_EVENTS = {"CORRECTION": "CORRECTOR", "COMPLETION": "COMPLETER"}
# capability を発行してよい principal(宣言された root authority)。
# self-grant 対策(JREV-0002): grant は『発行者が当該 capability の authorized issuer』の時のみ有効。
# ⚠️ 残余(non_guarantee): GRANT の issuer 欄自体は self-report。issuer=root の詐称は単一プロセスでは
#    検出不能(署名/プロセス分離まで)。honest self-grant(issuer==grantee)は検出可能。
CAPABILITY_ISSUERS = {"CORRECTOR": {"root"}, "COMPLETER": {"root"}}


def issue_capability(run, grantee, capability, issuer="root"):
    """capability の発行を event 記録。issuer(発行者)も刻む=『誰が発行したか』を audit が見る。
    既定 issuer=root(系の bootstrap authority)。self-grant は issuer=grantee を明示して行われる。"""
    gid = append_event(run, "CAPABILITY_GRANT", "Capability", None,
                       {"id": SELF, "principal": grantee, "capability": capability,
                        "issuer": issuer, "granted_by_run": run}, new_prefix="CAP")
    return {"principal": grantee, "capability": capability, "grant_id": gid}


def _valid_grants(until_ts=None):
    """発行者が当該 capability の authorized issuer である GRANT のみ有効(self-grant を排除)。"""
    out = set()
    for e in read_events(until_ts):
        if e.get("event_type") == "CAPABILITY_GRANT":
            p = e["payload"]
            if p.get("issuer") in CAPABILITY_ISSUERS.get(p["capability"], set()):
                out.add((p["principal"], p["capability"]))
    return out


def _unauthorized_grants(until_ts=None):
    """authorized issuer でない者が発行した GRANT(honest self-grant 等)を可視化する。"""
    bad = []
    for e in read_events(until_ts):
        if e.get("event_type") == "CAPABILITY_GRANT":
            p = e["payload"]
            if p.get("issuer") not in CAPABILITY_ISSUERS.get(p["capability"], set()):
                bad.append({"grant": e["object_id"], "issuer": p.get("issuer"),
                            "grantee": p["principal"], "capability": p["capability"],
                            "reason": "self-grant / unauthorized issuer"})
    return bad


def audit_write_authority(until_ts=None, enforce_types=None):
    """privileged event が『authorized issuer 発行の capability を伴って』書かれているかを走査
    (R1 の保証=検出可能性)。
    - violations: capability を claim しているが *有効な* GRANT が無い(forge / self-grant で得た token)
    - unauthorized_grants: authorized issuer 以外が発行した GRANT(honest self-grant を可視化)
    - unprotected: privileged だが capability 無し。enforce_types 指定でこれも violation 化
    canonical stream は当面 unprotected。forge/self-grant は常に検出。issuer 詐称は非保証。"""
    enforce_types = set(enforce_types or [])
    granted = _valid_grants(until_ts)
    violations, unprotected = [], []
    for ev in read_events(until_ts):
        req = PRIVILEGED_EVENTS.get(ev.get("event_type"))
        if not req:
            continue
        cap, pr = ev.get("capability"), ev.get("principal")
        if cap is None:
            rec = {"event_id": ev["event_id"], "event_type": ev["event_type"],
                   "object_id": ev["object_id"], "reason": "no capability (unprotected)"}
            (violations if ev["event_type"] in enforce_types else unprotected).append(rec)
        elif cap != req or (pr, cap) not in granted:
            violations.append({"event_id": ev["event_id"], "event_type": ev["event_type"],
                               "object_id": ev["object_id"], "principal": pr, "capability": cap,
                               "reason": "no valid grant (forged / self-granted capability)"
                                         if (pr, cap) not in granted else "wrong capability for event_type"})
    return {"violations": violations, "unprotected": unprotected,
            "unauthorized_grants": _unauthorized_grants(until_ts)}


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


# R3(DE-0022): scope value canonicalization。v0.2 §7.1 は次元名の controlled vocab を規定したが
# 値の正規化を規定し忘れていた → 表記揺れ(vllm/VLLM, nv-fp4/nvfp4)で claim_key が割れ、identity
# gaming が dedup 以外(conflict/ABSENCE reuse/lineage)へ波及する。claim_key 生成前に必ず通す。
# raw scope は state に保存されたまま(この関数は key 生成にのみ canonical を使う)。
CANON_VERSION = "canon-1a.0"
SCOPE_ALIASES = {"nvfp4": "nvfp4", "fp8": "fp8", "vllm": "vllm", "sglang": "sglang",
                 "blackwell": "sm120", "sm120": "sm120"}   # 既知 alias(軽量 Entity Registry 代替)


def canonicalize_scope(scope):
    """surface 正規化: lowercase / whitespace・区切り(- _ 空白)除去 / 既知 alias。
    ※ version algebra(0.11 vs >=0.11)や entity 同一性は解決しない=non_guarantee(AB-0009 残)。"""
    out = {}
    for k, v in (scope or {}).items():
        if isinstance(v, str):
            c = v.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
            out[k] = SCOPE_ALIASES.get(c, c)
        else:
            out[k] = v
    return out


def claim_key(state):
    """OM/§14.2: ESTABLISHED 軸のみから安定 key を作る。R3: canonical scope から生成。"""
    if state.get("object_kind") not in ("CandidateClaim", "Claim"):
        return None
    scope = canonicalize_scope(state.get("scope", {}))
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


# ---------- Correction (L4 / DE-0008): append-only の訂正・撤回機構 ----------
# R2: M4 は completeness validator であって transition validator ではない。CORRECTION/COMPLETION が
# 「何でも直せる/書き換えられる」特権経路にならないよう、mutation policy を明示強制する。
LIFECYCLE_FIELDS = {"status", "polarity"}   # claim lifecycle は専用 transition event 管轄(CR-4)
EPISTEMIC_FIELDS = {"status", "polarity", "claim_type", "evidence_relations", "validation_mode",
                    "absence_validation", "outcome", "finding"}   # METADATA 訂正で触れない(CR-2)


def _cap(token):
    return (token["principal"], token["capability"]) if token else (None, None)


def correct_object(run, object_type, object_id, changes, reason, correction_class, basis=None,
                   capability=None):
    """過去 event を書換えず CORRECTION event で訂正する。M4 完全 revision + from/to provenance。
    R2 mutation policy(GPT CR-1..4):
      CR-1 correction_class ∈ {FACTUAL, METADATA} 必須
      CR-2 METADATA は epistemic fields(status/polarity/evidence/validation_mode 等)を変更禁止
      CR-3 FACTUAL は basis(根拠 event / decision ref)必須
      CR-4 lifecycle(status/polarity)遷移は CORRECTION でなく専用 transition event(未実装)で行う
    ※ completeness(M4)と legality(遷移正当性)は別物。CORRECTION は後者を主張しない。"""
    if correction_class not in ("FACTUAL", "METADATA"):                       # CR-1
        raise ValueError("CR-1: correction_class must be FACTUAL or METADATA")
    lc = [k for k in changes if k in LIFECYCLE_FIELDS]                        # CR-4
    if lc:
        raise ValueError(f"CR-4: lifecycle fields {lc} require a dedicated transition event, not CORRECTION")
    if correction_class == "METADATA":                                       # CR-2
        ep = [k for k in changes if k in EPISTEMIC_FIELDS]
        if ep:
            raise ValueError(f"CR-2: METADATA correction must not change epistemic fields {ep}")
    if correction_class == "FACTUAL" and not basis:                          # CR-3
        raise ValueError("CR-3: FACTUAL correction requires a basis (grounding event / decision ref)")
    st = get_state(object_id)
    if not st:
        raise ValueError(f"correction target {object_id} does not exist")
    record = {"corrected_at": now_iso(), "corrected_by_run": run, "reason": reason,
              "correction_class": correction_class, "basis": basis,
              "field_changes": {k: {"from": st.get(k), "to": v} for k, v in changes.items()}}
    st.update(changes)
    st["corrections"] = st.get("corrections", []) + [record]
    pr, cap = _cap(capability)
    return append_event(run, "CORRECTION", object_type, object_id, st, principal=pr, capability=cap)


def complete_object(run, object_type, object_id, fills, reason, capability=None):
    """先行生成時に未確定だったフィールドを埋める(完結)。M4 完全 revision + from/to provenance。
    R2 mutation policy(GPT CP-1..4):
      CP-1 missing/null → concrete のみ許可(fill 値は非 None)
      CP-2 既存 non-null scalar の変更禁止(completion 名目の rewrite を封じる)
      CP-3 既存 collection 要素の削除禁止
      CP-4 完結後 revision は schema complete(append_event の M4 guard が担保)
    AB-0007: to_id=None 先行生成 Relation の結線がこれ。OM-3 の恒久 null link を塞ぐ。"""
    st = get_state(object_id)
    if not st:
        raise ValueError(f"completion target {object_id} does not exist")
    for k, v in fills.items():
        cur = st.get(k, None)
        if v is None:                                                        # CP-1
            raise ValueError(f"CP-1: COMPLETION must fill {k} to a concrete value (got None)")
        if isinstance(cur, (list, tuple, set, dict)) and cur:                # CP-3
            raise ValueError(f"CP-2/3: {k} already has a non-empty collection; COMPLETION cannot mutate it")
        if cur is not None and not (isinstance(cur, (list, tuple, set, dict)) and not cur):  # CP-2
            raise ValueError(f"CP-2: COMPLETION cannot change existing non-null field {k} (={cur!r})")
    record = {"completed_at": now_iso(), "completed_by_run": run, "reason": reason,
              "field_fills": {k: {"from": st.get(k), "to": v} for k, v in fills.items()}}
    st.update(fills)
    st["completions"] = st.get("completions", []) + [record]
    pr, cap = _cap(capability)
    return append_event(run, "COMPLETION", object_type, object_id, st, principal=pr, capability=cap)
