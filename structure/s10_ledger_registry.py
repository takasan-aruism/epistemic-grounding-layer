#!/usr/bin/env python3
"""LEDGER_REGISTRY — 全台帳の登記簿。台帳ごとに「目的・作った prog・いつ・書き手・読み手・
版管理・生死」を決定論で集める。Taka の方針: 台帳がこのシステムの根幹であり、大半の開発は
何かしらの台帳に紐づく。特定部分の深掘りで全体を忘れる「AI 痴呆」が起きても、この 1 冊から
「何をしたかったか」を再構成できるようにする。

決定論で出せるものは LLM に判定させない（構造再構成 spec §0）。本器は事実のみ集める:
  - genesis     : 初出コミット（日付・sha・件名）と、そこに現れる DE-/CHG- id
  - writer      : その台帳のパス定数を所有する .py（= 作っているプログラム）
  - readers     : basename を参照する .py（writer を除く）
  - liveness    : live path 68 file から参照されるか / 最終更新 / 放置日数 / 行数
  - governance  : git 追跡下か / SoR 宣言の有無 / 書き手が単一か
「目的」は発明しない。genesis 件名と writer の module docstring 冒頭を **raw のまま** 載せ、
読む側（人間 or 未来の Claude）が意図を復元する材料にする。

出力: egl/structure/LEDGER_REGISTRY.jsonl（登記簿本体） + 標準出力サマリ。
検査: --check で「宣言された唯一書き手 vs 実測書き手」の食い違いを非0で報告。
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path("/home/takasan")
REPOS = ["egl", "rri", "ds", "dev-workcell", "twoder"]
S = ROOT / "egl" / "structure"
OUT = S / "LEDGER_REGISTRY.jsonl"
TODAY = "2026-07-22"

# --- live path 集合（構造再構成の REACHABILITY から。wired=true のファイル）---
WIRED = {json.loads(l)["key"] for l in open(S / "REACHABILITY.jsonl") if json.loads(l).get("wired")}

# --- 全 .py の本文キャッシュ（repo 相対 key）---
PY = {}
for r in REPOS:
    for rel in subprocess.check_output(["git", "-C", str(ROOT / r), "ls-files"], text=True).split():
        if rel.endswith(".py"):
            k = f"{r}/{rel}"
            try:
                PY[k] = (ROOT / r / rel).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                PY[k] = ""

WRITE_SIGNAL = re.compile(r'open\([^)]*["\']\s*[aw]\s*["\']|\.write\(|\.write_text\(|json\.dump\(')
DOCSTRING = re.compile(r'^\s*(?:#!.*\n)?\s*(?:[rubRUB]*)"""(.*?)"""', re.S)


def all_ledgers():
    """git 追跡下 + gitignore された台帳の両方を拾う（重要台帳ほど gitignore される実態がある）。"""
    seen = {}
    for r in REPOS:
        tracked = set(subprocess.check_output(["git", "-C", str(ROOT / r), "ls-files"], text=True).split())
        # gitignore された .jsonl も列挙（--others --ignored）
        ignored = subprocess.check_output(
            ["git", "-C", str(ROOT / r), "ls-files", "--others", "--ignored", "--exclude-standard"], text=True).split()
        for rel in sorted(set(tracked) | set(ignored)):
            if not rel.endswith(".jsonl"):
                continue
            if rel.startswith("structure/"):   # 本再構成の派生物は対象外
                continue
            if "/fixtures/" in rel or "/problems/" in rel:  # 実験の入力 fixture は台帳でない
                continue
            key = f"{r}/{rel}"
            seen[key] = (r, rel, rel in tracked)
    return seen


def genesis(repo, rel, tracked):
    if not tracked:
        # 追跡外: git に生誕記録なし。ファイル先頭行の ts を代替として拾う
        p = ROOT / repo / rel
        first_ts = None
        try:
            for line in p.read_text(errors="ignore").splitlines():
                if line.strip():
                    o = json.loads(line)
                    first_ts = o.get("ts") or o.get("recorded_at") or o.get("registered_at") \
                        or o.get("created_at") or o.get("admitted_at")
                    break
        except Exception:
            pass
        return {"date": None, "commit": None, "subject": None, "first_row_ts": first_ts,
                "de_ids": [], "chg_ids": [], "source": "UNTRACKED_NO_GIT_GENESIS"}
    out = subprocess.check_output(
        ["git", "-C", str(ROOT / repo), "log", "--diff-filter=A",
         "--format=%ad|%h|%s%n%b", "--date=format:%Y-%m-%d", "--", rel], text=True)
    blocks = [b for b in out.split("\n") if b.strip()]
    if not blocks:
        return {"date": None, "commit": None, "subject": None, "de_ids": [], "chg_ids": [], "source": "NO_ADD_COMMIT"}
    first = blocks[-1] if "|" in blocks[-1] else next((b for b in reversed(blocks) if "|" in b), blocks[-1])
    parts = first.split("|", 2)
    date, commit, subject = (parts + [None, None, None])[:3]
    de = sorted(set(re.findall(r"DE-\d{3,4}", out)))
    chg = sorted(set(re.findall(r"CHG-\d{3,4}", out)))
    return {"date": date, "commit": commit, "subject": subject, "de_ids": de, "chg_ids": chg, "source": "GIT_ADD"}


def last_touch(repo, rel, tracked):
    if not tracked:
        p = ROOT / repo / rel
        try:
            mt = subprocess.check_output(["date", "-r", str(p), "+%Y-%m-%d"], text=True).strip()
        except Exception:
            mt = None
        return mt, "MTIME_UNTRACKED"
    d = subprocess.check_output(
        ["git", "-C", str(ROOT / repo), "log", "-1", "--format=%ad", "--date=format:%Y-%m-%d", "--", rel], text=True).strip()
    return (d or None), "GIT_LOG"


def idle_days(d):
    if not d:
        return None
    return (int(subprocess.check_output(["date", "-d", TODAY, "+%s"], text=True))
            - int(subprocess.check_output(["date", "-d", d, "+%s"], text=True))) // 86400


def _is_nonprod(k):
    return bool(re.search(r'(^|/)(test_|conftest)|_test\.py$|/tests?/|/regression/|/experiments?/|/docs/', k))


def path_owner(repo, base):
    """この台帳を **書いている** .py を静的に特定する。2 層で返す:
      strict = 当該パス変数への write-mode open/write を確認したもの（高精度）
      loose  = basename を参照し、かつモジュールに書込みがある（高再現・パス未確認）
    さらに本番コードと test/experiment/docs を分離する。所有者ゼロ = 真の orphan。"""
    strict, loose = [], []
    pat = re.compile(re.escape(base))
    for k, txt in PY.items():
        if not k.startswith(repo + "/") or base not in txt:
            continue
        if WRITE_SIGNAL.search(txt):
            loose.append(k)
        # (1) この台帳のパスに束縛された変数名を集める: `VAR = ... "basename" ...`
        #     もしくは EVENTS 定数経由（`EVENTS = "basename"` → 別行で `X = dir / EVENTS`）
        pathvars = set()
        for ln in txt.splitlines():
            m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', ln)
            if not m:
                continue
            var, rhs = m.group(1), m.group(2)
            if pat.search(rhs) and ("Path(" in rhs or "/" in rhs or "environ" in rhs
                                    or re.match(r'["\']', rhs)):
                pathvars.add(var)
        # EVENTS 定数を経由する二段束縛（`EVENTS="events.jsonl"` → `p = data_dir()/EVENTS`）
        const_names = {v for v in pathvars}
        for ln in txt.splitlines():
            m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$', ln)
            if m and any(re.search(r'\b%s\b' % re.escape(c), m.group(2)) for c in const_names) \
                    and ("/" in m.group(2) or "Path(" in m.group(2)):
                pathvars.add(m.group(1))
        if not pathvars:
            continue
        # (2) その変数に対する **書込み** があるか（read_text は除外）
        alt = "|".join(re.escape(v) for v in pathvars)
        wrote = re.search(
            r'open\(\s*(?:str\(\s*)?(?:%s)\b[^)]*["\'][aw]' % alt, txt) \
            or re.search(r'\b(?:%s)\.open\(\s*["\'][aw]' % alt, txt) \
            or re.search(r'\b(?:%s)\.write_text\(' % alt, txt) \
            or (re.search(r'\b(?:%s)\.open\(' % alt, txt) and ".write(" in txt)
        if wrote:
            strict.append(k)
    chosen = strict or loose
    prod = [k for k in chosen if not _is_nonprod(k)]
    nonprod = [k for k in chosen if _is_nonprod(k)]
    return {
        "programs": prod or nonprod,          # 本番があれば本番、無ければ test/experiment
        "production": prod,
        "nonproduction": nonprod,
        "confidence": ("CONFIRMED_WRITE_TO_PATH" if strict else
                       ("REFERENCES_AND_WRITES_PATH_UNCONFIRMED" if loose else "NONE")),
    }


def declared_sole_writer(prod_owners):
    for k in prod_owners:
        if re.search(r"ONLY sanctioned writer|唯一の(書き手|writer)|sole writer|ONLY writer", PY.get(k, "")):
            return k
    return None


def readers(base, writers):
    rs = [k for k, txt in PY.items() if base in txt and k not in writers]
    return sorted(rs)


def live_ref(base):
    return sorted(w for w in WIRED if base in (ROOT / w).read_text(errors="ignore") if (ROOT / w).exists())


def sor_flag(owners, rel):
    for k in owners:
        if re.search(r"\bSoR\b|Source of Record|source of truth|append-only.*SoR", PY.get(k, "")):
            return "SoR_DECLARED"
    if "audit/" in rel or "REGISTRY" in rel.upper() or "LEDGER" in rel.upper():
        return "LEDGER_BY_NAME"
    return "UNDECLARED"


def docfirst(k):
    m = DOCSTRING.search(PY.get(k, ""))
    if not m:
        return None
    return " ".join(m.group(1).strip().split())[:240]


# EGL の 4 層 bootstrap で各 repo に配られる台帳（canonical writer は egl 側のみ）
BOOTSTRAP_REPLICAS = {"DESIGN_EVIDENCE_LEDGER.jsonl", "REVIEW_LEDGER.jsonl", "audit_backlog.jsonl"}

# canonical 運用台帳（本線を成す台帳。instance store と区別する — 点2の弱点補正）。
# LIVE 分類が「reader コードの到達性」と「そのインスタンスの現用」を混ぜないよう明示列挙。
CANONICAL_LEDGERS = {
    "ds/ds_events.jsonl", "rri/rri_records.jsonl", "egl/data/events.jsonl", "dev-workcell/events.jsonl",
    "egl/DESIGN_EVIDENCE_LEDGER.jsonl", "twoder/audit/ROADMAP_REGISTRY.jsonl", "twoder/audit/CHANGE_LOG.jsonl",
    "twoder/audit/ARTIFACT_REGISTRY.jsonl", "dev-workcell/data/pending_actor.jsonl",
    "twoder/failure_memory.jsonl", "twoder/failure_recurrence.jsonl",
    "twoder/audit/COMPLETION_DEFINITION_REGISTRY.jsonl",
}


def ledger_role(ledger_id, base, liveness):
    """台帳の役割。canonical 運用台帳 / instance store / governance を分ける（点2）。"""
    if ledger_id in CANONICAL_LEDGERS:
        return "CANONICAL"
    if liveness == "LIVE" and base == "events.jsonl":
        return "INSTANCE_STORE"     # egl/data_*/events, run_sor/events 等: 同一書き手の scenario 実体
    if liveness == "LIVE":
        return "GOVERNANCE_LIVE"    # REVIEW_LEDGER / audit_backlog 等の小規模 live 台帳
    return {"IDLE_HAS_WRITER": "IDLE", "ORPHAN": "EXPERIMENT_RESIDUE",
            "REPLICA_SHADOW": "REPLICA", "SHIPMENT_COPY": "SHIPMENT"}.get(liveness, "OTHER")


def classify_writer(repo, base, ow, all_owner_index):
    """書き手ゼロの台帳を、欠陥（真の orphan）と正常（複製/パラメタ化）に分ける。"""
    if ow["programs"]:
        return "RESOLVED"
    if base in BOOTSTRAP_REPLICAS and repo != "egl":
        return "BOOTSTRAP_REPLICA(canonical=egl/%s)" % base   # 正常。読み手が base= を渡さない限り死蔵
    if all_owner_index.get(base):
        return "PARAMETRIZED_SHARED_WRITER(%s)" % all_owner_index[base][0]
    return "NONE_ORPHAN"


def build():
    rows = []
    entries = sorted(all_ledgers().items())
    # basename -> それを所有する writer prog（他パスで検出されたもの）
    owner_index = {}
    owner_cache = {}
    for key, (repo, rel, tracked) in entries:
        base = os.path.basename(rel)
        ow = owner_cache.setdefault((repo, base), path_owner(repo, base))
        if ow["programs"]:
            owner_index.setdefault(base, []).extend(ow["production"] or ow["programs"])
    for key, (repo, rel, tracked) in entries:
        base = os.path.basename(rel)
        p = ROOT / repo / rel
        n = sum(1 for ln in p.read_text(errors="ignore").splitlines() if ln.strip()) if p.exists() else 0
        gen = genesis(repo, rel, tracked)
        lt, lt_src = last_touch(repo, rel, tracked)
        ow = owner_cache[(repo, base)]
        prod = ow["production"]
        sole = declared_sole_writer(prod)
        rds = readers(base, ow["programs"])
        live_readers = [r for r in rds if r in WIRED]
        wres = classify_writer(repo, base, ow, owner_index)
        is_ship = "/docs/" in rel or "SUBMIT_" in rel   # 出荷束/ドキュメント同梱の複製
        # basename 衝突で live に見える複製・出荷コピーは live 扱いしない
        live = [] if (wres.startswith("BOOTSTRAP_REPLICA") or is_ship) else live_ref(base)
        rows.append({
            "ledger_id": key,
            "basename": base, "repo": repo, "path": rel,
            "rows": n,
            "genesis": gen,
            "purpose_raw": {  # 発明しない。事実のみ。
                "genesis_subject": gen.get("subject"),
                "writer_docstring": docfirst(sole or (prod[0] if prod else (ow["programs"][0] if ow["programs"] else ""))),
            },
            "writer_programs": ow["programs"],
            "writer_production": prod,
            "writer_nonproduction": ow["nonproduction"],
            "writer_confidence": ow["confidence"],
            "declared_sole_writer": sole,
            "writer_count": len(ow["programs"]),
            "production_writer_count": len(prod),
            "writer_resolution": wres,
            "readers": rds,
            "live_readers": live_readers,
            "live_referenced": bool(live),
            "governance": {
                "git_tracked": tracked,
                "sor": sor_flag(ow["programs"], rel),
                "shipment_or_docs_copy": is_ship,
                "last_touch": lt, "last_touch_source": lt_src,
                "idle_days": idle_days(lt),
            },
            "liveness": (
                "REPLICA_SHADOW" if wres.startswith("BOOTSTRAP_REPLICA")
                else "SHIPMENT_COPY" if is_ship
                else "LIVE" if live
                else "ORPHAN" if wres == "NONE_ORPHAN"
                else "IDLE_HAS_WRITER"),
            "trust_tier": "T3_DERIVED", "regenerable": True,
            "derived_from": "git genesis + AST path-owner + REACHABILITY(wired) + basename readers",
        })
    # role は liveness 確定後に付与
    for r in rows:
        r["role"] = ledger_role(r["ledger_id"], r["basename"], r["liveness"])
    return rows


def main():
    rows = build()
    if "--check" in sys.argv:
        bad = []
        for r in rows:
            # 宣言された唯一書き手があるのに、本番書き手が複数 → 規律破れ
            if r["declared_sole_writer"] and r["production_writer_count"] > 1:
                bad.append((r["ledger_id"], "declared-sole-but-multiple-prod-writers", r["writer_production"]))
            # live で読まれるのに真の書き手が居ない（複製/パラメタ化は除外）→ 供給不能
            if r["live_referenced"] and r["writer_resolution"] == "NONE_ORPHAN":
                bad.append((r["ledger_id"], "live-read-but-genuinely-no-writer", []))
            # canonical 運用台帳は sole writer 必須（§4 実測を規律に昇格。DE-0491）:
            #   本番書き手が複数 → 規律違反 / 本番書き手ゼロ → 手埋め前提の腐敗リスク
            if r.get("role") == "CANONICAL":
                if r["production_writer_count"] > 1:
                    bad.append((r["ledger_id"], "CANONICAL-must-have-sole-writer-but-multiple", r["writer_production"]))
                elif r["production_writer_count"] == 0:
                    bad.append((r["ledger_id"], "CANONICAL-has-no-production-writer", r["writer_nonproduction"]))
        for lid, why, extra in bad:
            print(f"MISMATCH {lid}: {why} {extra}")
        print(f"\n{len(bad)} mismatch(es) over {len(rows)} ledgers")
        sys.exit(1 if bad else 0)

    if "--apply" in sys.argv:
        with OUT.open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"wrote {OUT} ({len(rows)} ledgers)")

    # サマリ
    import collections
    live = [r for r in rows if r["liveness"] == "LIVE"]
    orphan = [r for r in rows if r["liveness"] == "ORPHAN"]
    idle = [r for r in rows if r["liveness"] == "IDLE_HAS_WRITER"]
    shadow = [r for r in rows if r["liveness"] in ("REPLICA_SHADOW", "SHIPMENT_COPY")]
    untracked_live = [r for r in live if not r["governance"]["git_tracked"]]
    print(f"\n台帳 {len(rows)} 本  |  LIVE {len(live)}（うち追跡外 {len(untracked_live)}）  "
          f"ORPHAN {len(orphan)}  IDLE_HAS_WRITER {len(idle)}  複製/出荷影 {len(shadow)}")
    print("writer_resolution:", dict(collections.Counter(r["writer_resolution"].split("(")[0] for r in rows)))
    print(f"\n{'台帳':<46}{'行':>6}{'生死':>16}{'書手解決':>26}{'放置':>5}  genesis/purpose")
    for r in sorted(rows, key=lambda x: (x["liveness"] != "LIVE", -x["rows"])):
        g = r["genesis"]
        tr = "T" if r["governance"]["git_tracked"] else "·"
        print(f"{r['ledger_id']:<46}{r['rows']:>6}{r['liveness']:>16}{r['writer_resolution'][:26]:>26}"
              f"{(r['governance']['idle_days'] if r['governance']['idle_days'] is not None else '?'):>5}"
              f"  {tr} {g.get('date') or 'UNTR'} {(g.get('subject') or '')[:38]}")


if __name__ == "__main__":
    main()
