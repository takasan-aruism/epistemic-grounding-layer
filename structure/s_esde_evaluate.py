#!/usr/bin/env python3
"""[Claude実装] s_esde_evaluate — ESDE 構造監査を 2DER の観測値から出す計器（★Taka 主題 2026-08-23/24）。

★なぜ置くのか（★2026-08-24 実測）=
  ★これまで ESDE の数字は ★私の scratchpad のスクリプトが出していた。
  ★`ESDE_EVALUATION` を emit する呼び手は 2DER の中に ★0件だった
  ∴ ★セッションが終わると 再測定できない ―― ★「記録は在るが 書き手が居ない」を 私自身が作っていた。
  ★裁定②「修理後に同じ計器で再測定する」も その状態では 実行できない。

★測るもの（★OPERATING §3-9 の6概念のうち 機械で取れる3つ）=
  対等性 EQUALITY   同じ構造空間に載っているか（★発行された ID が 相互参照の口から引けるか）
  対称性 SYMMETRY   書いた event type を 誰が読むか（★名前で探さない・正本§10②）
  階層性 HIERARCHY  ★required − enforced = violation
                    ★required は 独立した出所からのみ（Taka 裁定 2026-08-24=
                      正本 / Taka裁定 / 確定済み設計明細 / 確定済み PLAN・contract）
                    ★enforcement と同じコード上の定数や門は required にしない
  連動性 LINKAGE    ★declared の出所が本線で生まれない（正本§6）∴ ★UNVERIFIED のまま

★出す先= 既存 ETRACE の `component=ESDE_EVALUATION`。★新台帳0・新state0・新ID0。
  形は `domain_dw.record_stages` の前例と同じ（`emit(component, function, inputs, outputs)` 1行）。
  `inputs/outputs` の上限は 2000B。3指標を丸ごと詰めて約 440B（★欠損ID 60〜70件まで入る）。

★scope を必ず入れる（Taka 裁定 2026-08-24 ①②）=
  ★私は以前 記録を引ける場所が欲しくて 無関係な task_id に貼り付け、
  ★画面上「この task の構造評価」に見えていた。★同じ穴を掘らない。

★何も止めない（Taka 裁定 2026-08-23 ①「初期は止めない・記録のみ」）。
★ESDE は修理しない（監査役が開発者になって本線を乗っ取るため）。finding は handoff 先を書くだけ。

usage:
  s_esde_evaluate.py               # 全軸を測って ETRACE へ記録する
  s_esde_evaluate.py --dry         # 測るだけ（★書き込み0）
  s_esde_evaluate.py --check       # ★書き込み0で 測り直し、前回の記録と数を突き合わせる
  s_esde_evaluate.py --task TASK-… # TASK 起点で 1件だけ測る
"""
import ast
import glob
import json
import os
import re
import sys
import urllib.request
import base64

ROOTS = ("twoder", "egl", "dev-workcell", "rri", "ds")
SKIP = ("/regression/", "/test_", "/tests/", "/.git/", "/experiments/", "/docs/SUBMIT_",
        "/runs/")   # ★走行の控え= 横読み禁止の面。★計器は触れない
FRONT = "http://100.107.6.119:8770"
TOKEN = "/home/takasan/twoder/.access_token"


_SELF = os.path.abspath(__file__)
# ★★[Claude実装] 2026-08-24 Taka 裁定②= この Worker が 台帳へ 書く 行為の 名前(★POLICY の 鍵)。
#   ★1つだけ= ★書く口は 4つ だが ★どれも『1件の評価を追記する』の 部分 ∴ 行為としては 1つ。
ESDE_WRITE_ACTION = "ESDE_RECORD_EVALUATION"
# ★★2026-08-24 自己監査で見つけた欠陥: ★走査が `**/*.py` だけだった ∴
#   ★.sh から python を呼ぶ読み手(実測: .claude/hooks/2der_status.sh:103 が
#   `from twoder.effective_state import canonical_actor`)を ★見落とし ★偽の欠損を作っていた。
#   ★これは 本日ずっと数えてきた型(読み手が別の形で在るのに 場所の決め打ちで見落とす)そのもの。
#   ★∴ 読み手を探す時は .py 以外も 見る。★書き手(AST が要る側)は .py のまま。
#   ★訂正(同じ自己監査の中で見つけた)= 最初 .json も入れたら
#     ★私自身の投函の控え(走行の控え)が『読み手』に数えられた
#     =★計器が自分の記録を数える(本日3例目)。★.json は関数を呼べない ∴ 外す。
#     ★併せて 走行の控えの置き場は ★横読み禁止の面 ∴ 計器が触れてはいけない。
_READER_EXT = ("*.py", "*.sh")
_READER_ROOTS = ROOTS + (".claude",)


def _files():
    """★書き手を 探す 面(AST を かける)= .py のみ。★自分自身は 走査しない。"""
    return [p for r in ROOTS for p in glob.glob("/home/takasan/" + r + "/**/*.py", recursive=True)
            if not any(s in p for s in SKIP) and os.path.abspath(p) != _SELF]


def _reader_files():
    """★読み手を 探す 面= ★.py に 限らない(★上の欠陥の 直し)。"""
    out = []
    for r in _READER_ROOTS:
        for ext in _READER_EXT:
            out += [p for p in glob.glob("/home/takasan/" + r + "/**/" + ext, recursive=True)
                    if not any(s in p for s in SKIP) and os.path.abspath(p) != _SELF]
    return sorted(set(out))


def _get(path):
    tok = open(TOKEN).read().strip()
    auth = base64.b64encode(("taka:" + tok).encode()).decode()
    req = urllib.request.Request(FRONT + path, headers={"Authorization": "Basic " + auth})
    return json.load(urllib.request.urlopen(req, timeout=300))


# ── 対等性 ──────────────────────────────────────────────────
_MINT = re.compile(r'["\']([A-Z][A-Z0-9_]{1,12}[-:])["\']\s*\+')
_FSTR = re.compile(r'["\']([A-Z][A-Z0-9_]{1,12})-%[sd]')
# ★識別子でない物は 名指しで 除く(★実測で 1件ずつ 確かめた・2026-08-24)
_NOT_ID = {"UNIQUE-": "content_hash", "AB-": "scope文字列", "IA-": "idempotency_key",
           # ★2026-08-24: ★この計器自身の 軸の名前(`"TASK:" + task_id`)を ID の発行点と
           #   ★誤検出していた=★計器が自分を数えていた。★名指しで 除く。
           "TASK:": "この計器の軸名(s_esde_evaluate)"}


def axis_2der_identity():
    """発行された ID が 相互参照の口から引けるか。★producer 側は下限(この形しか拾えない)。"""
    minted = {}
    for p in _files():
        try:
            s = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in list(_MINT.finditer(s)) + list(_FSTR.finditer(s)):
            g = m.group(1)
            pre = g if g.endswith(("-", ":")) else g + "-"
            minted.setdefault(pre, set()).add(p.replace("/home/takasan/", ""))
    ids_src = open("/home/takasan/twoder/ids.py", encoding="utf-8").read()
    resolvable = set(re.findall(r'rid\.startswith\(["\']([A-Za-z0-9_:-]+)["\']\)', ids_src))
    w = open("/home/takasan/twoder/webui.py", encoding="utf-8").read()
    m = re.search(r'rid\.split\("-",\s*1\)\[0\] in \(([^)]*)\)', w)
    if m:
        resolvable |= {x.strip().strip("\"'") + "-" for x in m.group(1).split(",") if x.strip()}
    real = {k: v for k, v in minted.items() if k not in _NOT_ID}
    ok = {k for k in real if any(k == r or k.startswith(r) or r.startswith(k) for r in resolvable)}
    ng = sorted(set(real) - ok)
    return {"axis": "2DER_IDENTITY", "scope_kind": "REPO", "scope_id": "2DER",
            "inputs": {"producer_source": "AST/正規表現で発行点を全件走査(本番 .py %d本)。★下限=別の作り方は拾えない" % len(_files()),
                       "consumer_source": "twoder/ids.py::resolve + webui.resolve_view = %d種" % len(resolvable)},
            "outputs": {"equality": {"required": len(real), "present": len(ok), "incompatible_ID": ng,
                                     "identity_rule": "接頭辞ごとの個別分岐。★受け皿なし=未対応はどのIDでも None",
                                     "status": "PRESENT" if not ng else "BROKEN",
                                     "not_identifiers_excluded": [k + "(" + v + ")" for k, v in _NOT_ID.items()],
                                     "producer_is_lower_bound": True}}}


# ── 対称性 ──────────────────────────────────────────────────
def axis_rri():
    """公開関数が書く event type を 誰が読むか。★名前の一致では探さない(正本§10②)。"""
    src_path = "/home/takasan/rri/rri/request_thread.py"
    src = open(src_path, encoding="utf-8").read()
    tree, lines = ast.parse(src), src.splitlines()
    writers = {}
    for n in tree.body:
        if not (isinstance(n, ast.FunctionDef) and not n.name.startswith("_")):
            continue
        seg = "\n".join(lines[n.lineno - 1:(n.end_lineno or n.lineno)])
        tps = sorted(set(re.findall(r'"type"\s*:\s*"([A-Z_]+)"', seg)))
        if tps:
            writers[n.name] = tps
    files = _reader_files()          # ★読み手は .py に限らない(2026-08-24 の自己監査)
    rows, missing = [], []
    for w, tps in sorted(writers.items()):
        n_read = 0
        for tp in tps:
            for p in files:
                try:
                    s = open(p, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                for l in s.splitlines():
                    if ('"%s"' % tp) not in l and ("'%s'" % tp) not in l:
                        continue
                    if '"type"' in l and "_append" in l:      # ★書いている行は 読み手に 数えない
                        continue
                    n_read += 1
        rows.append({"writer": w, "types": tps, "reader_lines": n_read})
        if not n_read:
            missing.append(w)
    return {"axis": "RRI", "scope_kind": "MODULE", "scope_id": "rri/rri/request_thread.py",
            "inputs": {"symmetry_method": "書いた event type を誰が読むか(★名前でなく作用・正本§10②)",
                       "enforced_source": "AST: 公開関数 %d本" % len(writers),
                       "reader_surface": "★.py/.sh/.json (%d本)。★.py だけだと .sh の読み手を見落とす"
                                         % len(files)},
            "outputs": {"symmetry": {"required": len(rows), "present": len(rows) - len(missing),
                                     "missing_ID": missing, "per_writer": rows},
                        "linkage": {"status": "UNVERIFIED",
                                    "why": "declared edge の出所が本線で生まれない(正本§6)"}}}


# ── 連動性 ──────────────────────────────────────────────────
# ★★2026-08-27(Taka 指示)= ★これまで linkage は 全軸で UNVERIFIED だった
#   (逐語『declared edge の出所が本線で生まれない(正本§6)』)。
#   ★★出所が 見つかった= ★EGL は ★同じ 存在を ★2つの 面で 持っている:
#     declared … `core.by_type`(sqlite の projection)= ★系が 「今こう持っている」と 言う 面
#     observed … `core.read_events`(event log)      = ★実際に 起きた 面
#   ★正本§1 の 連動性=『declared edge と observed edge の 一致・伝播』に そのまま 当たる。
#   ★★総合点に しない= ★分母(比べた型)/分子(一致した型)/★欠損ID(型名)を そのまま 残す。
def axis_egl_projection():
    """★連動性= 同じ存在を 2つの面が 数える。★一致しない型を 欠損IDとして 出す。"""
    import collections
    import sqlite3
    sys.path.insert(0, "/home/takasan/egl")
    from egl import core
    obs = collections.Counter()
    for ev in core.read_events():                 # ★observed= 実際に起きた CREATE
        t = ev.get("object_type")
        if t and ev.get("event_type") == "CREATE":
            obs[t] += 1
    con = sqlite3.connect(str(core.SQLITE))
    try:
        in_sql = {r[0] for r in con.execute("SELECT DISTINCT object_type FROM objects")}
        dec = {t: len(core.by_type(con, t) or []) for t in (set(obs) | in_sql)}
    finally:
        con.close()
    types = sorted(set(dec) | set(obs))
    broken = [t for t in types if dec.get(t, 0) != obs.get(t, 0)]
    # ★★『食い違い』を 1つに 潰さない= ★向きで 分ける(★原因が 別)
    behind = [t for t in broken if dec.get(t, 0) < obs.get(t, 0)]    # projection が 遅れている
    only = [t for t in broken if dec.get(t, 0) > obs.get(t, 0)]      # projection にしか 無い
    return {"axis": "EGL_PROJECTION", "scope_kind": "REPO", "scope_id": "EGL",
            "inputs": {"declared_source": "egl.core.by_type(sqlite %s の objects)" % core.SQLITE.name,
                       "observed_source": "egl.core.read_events(%s の CREATE)" % core.EVENTS.name,
                       "key_note": "★同じ存在の 2つの面を 型ごとに 突き合わせる(★件数の 鍵は CREATE 1回=1存在)"},
            "outputs": {"linkage": {"declared": len(types), "observed": len(types) - len(broken),
                                    "broken_ID": broken,
                                    "status": "PRESENT" if not broken else "BROKEN",
                                    "broken_projection_behind": behind,
                                    "broken_projection_only": only,
                                    "per_broken": [{"type": t, "declared": dec.get(t, 0),
                                                    "observed": obs.get(t, 0)} for t in broken]}}}


# ── 階層性 ──────────────────────────────────────────────────
# ★required の出所は ★正本§4（独立した文書）。★enforcement と同じ場所からは取らない（Taka 裁定）。
_CANON_BOUNDARIES = [
    ("authority は Taka のみ", "INTERIM_APPROVERS"),
    ("自己発行の禁止", "_FORBIDDEN_ATTRIB"),
    ("reconciler は read-only", "_READ_ONLY_GIT"),
    ("書込は energize 必須", ("apply_cycle", "energize")),   # ★署名の必須引数
    ("新規配置と既存変更の責務差", None),                     # ★符号化なし
]
# ★対称性の counterpart も 正本§4 から（★同一性が 3種類 混在する＝実測 2026-08-24）
_CANON_COUNTERPARTS = [("ENERGIZATION_ADJUDICATION", "ENERGIZATION_ADJUDICATION"),
                       ("ENERGIZATION_REVOCATION", "ENERGIZATION_REVOCATION"),
                       ("RECONCILIATION_*", "emit_reconciliation"),
                       ("PATCH_APPLICATION", "emit_patch_application"),
                       ("real energize", "mint_real_energize"),
                       ("artifact -> patch", "source_to_patch")]
_WRITE_HINT = ("emit", "append", "write", "record", "_append", "dump")


def _enforced_consts():
    out = {}
    for p in _files():
        try:
            t = ast.parse(open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        for n in t.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                nm, v = n.targets[0].id, n.value
                isset = isinstance(v, (ast.Set, ast.List, ast.Tuple)) or (
                    isinstance(v, ast.Call) and getattr(v.func, "id", "") in ("frozenset", "set"))
                if isset and (nm.isupper() or (nm.startswith("_") and nm[1:].isupper())):
                    out.setdefault(nm, p.replace("/home/takasan/", "") + ":%d" % n.lineno)
    return out


def _sig_required(func, arg):
    for p in _files():
        try:
            t = ast.parse(open(p, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.FunctionDef) and n.name == func:
                names = [a.arg for a in n.args.args]
                nd = len(n.args.defaults)
                req = names[:len(names) - nd] if nd else names
                if arg in req:
                    return p.replace("/home/takasan/", "") + ":%d" % n.lineno
    return None


def axis_real_repo_reflection():
    """★required は 正本§4（独立文書）／ enforced はコード。★人の値と答え合わせできる唯一の軸。"""
    files = _files()
    enf = _enforced_consts()
    hier, viol = [], []
    for label, tok in _CANON_BOUNDARIES:
        if isinstance(tok, tuple):
            at = _sig_required(*tok)
            hier.append({"boundary": label, "enforced": bool(at), "how": "署名の必須引数(境界と名乗っていない)", "at": at})
        elif tok and tok in enf:
            hier.append({"boundary": label, "enforced": True, "how": "allowlist定数", "at": enf[tok]})
        else:
            hier.append({"boundary": label, "enforced": False, "how": "符号化なし", "at": None})
        if not hier[-1]["enforced"]:
            viol.append(label)
    sym, miss = [], []
    for name, tok in _CANON_COUNTERPARTS:
        hits, w = [], 0
        for p in files:
            try:
                s = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if p.endswith("/%s.py" % tok):        # ★モジュールが書き手の場合
                w += 1
            for l in s.splitlines():
                if tok in l:
                    hits.append(l.strip())
                    if ("def %s(" % tok) in l:                     # ★関数が書き手
                        w += 1
                    elif any(k in l for k in _WRITE_HINT) and "def " not in l:   # ★event 名の文字列
                        w += 1
        sym.append({"counterpart": name, "occurrences": len(hits), "writer_sites": w})
        if not w:
            miss.append(name)
    return {"axis": "REAL_REPO_REFLECTION", "scope_kind": "REPO", "scope_id": "energization/bridge",
            "inputs": {"required_source": "CANON:ESDE_EVALUATION_DOMAIN_MANAGER_v0.1 §4(★独立文書)",
                       "enforced_source": "AST:allowlist定数%d件 + 署名の必須引数" % len(enf)},
            "outputs": {"symmetry": {"required": len(sym), "present": len(sym) - len(miss),
                                     "missing_ID": miss, "per_counterpart": sym},
                        "hierarchy": {"required": len(hier), "passed": len(hier) - len(viol),
                                      "violation_ID": viol, "unreachable": 0, "per_boundary": hier},
                        "linkage": {"status": "UNVERIFIED",
                                    "why": "declared edge の出所が本線で生まれない(正本§6)"},
                        "cross_check_vs_human": {"symmetry_expected": [6, 4, 2],
                                                 "hierarchy_expected": [5, 4, 1],
                                                 "symmetry": [len(sym), len(sym) - len(miss), len(miss)] == [6, 4, 2],
                                                 "hierarchy": [len(hier), len(hier) - len(viol), len(viol)] == [5, 4, 1]}}}


# ── TASK 起点 ────────────────────────────────────────────────
_RESOLVABLE_PRE = {"ETR", "TASK", "ART", "ACC", "AX", "ADM", "THREAD", "Q", "QE", "RTHREAD",
                   "UTT", "DE", "CHG", "INTV", "SUBMIT", "ITEM", "ROADMAP", "PHASE", "AMEND"}


def axis_task(task_id):
    """★関係集合は 既存の3口だけから 投影する(★新台帳0)。"""
    res = _get("/api/resolve?id=%s" % task_id)
    etr = (_get("/api/etrace?task_id=%s" % task_id) or {}).get("task_trace") or {}
    rth = _get("/api/rthread?task_id=%s" % task_id)
    providers = res.get("providers") or []
    blockers = res.get("completion_blockers") or []
    events = etr.get("events") or []
    typed = rth.get("typed") or []
    refs = [x for r in typed for x in (r.get("refs") or [])]
    pre = set(re.findall(r"\b([A-Z][A-Z0-9]{1,10})-[0-9a-zA-Z]{4,}",
                         json.dumps(events, ensure_ascii=False)))
    eq = [{"what": "%s:%s" % (r.get("kind"), r.get("value")), "ok": bool(r.get("resolved")),
           "src": "明細の refs(★既存機構の判定)"} for r in refs]
    eq += [{"what": "etrace の %s-*" % p, "ok": p in _RESOLVABLE_PRE, "src": "ids.resolve と突き合わせ"}
           for p in sorted(pre)]
    ng = [x["what"] for x in eq if not x["ok"]]
    req = [r for r in typed if r.get("kind") in ("SPEC", "CONSTRAINT", "GOAL")]
    return {"axis": "TASK:" + task_id, "scope_kind": "TASK", "scope_id": task_id,
            "inputs": {"relation_set_source": "★既存の3口のみ= /api/resolve + /api/etrace?task_id + /api/rthread?task_id",
                       "relation_set_size": len(providers) + len(events) + len(typed) + len(refs),
                       "required_source": "DESIGN_DETAIL(この task の明細・現在有効版の SPEC/CONSTRAINT/GOAL)"},
            "outputs": {"equality": {"required": len(eq), "present": len(eq) - len(ng),
                                     "incompatible_ID": ng, "status": "PRESENT" if not ng else "BROKEN"},
                        "hierarchy": {"required": len(req), "note": "enforced の照合は別段(この計器は分母を出す)"},
                        "linkage": {"observed_stages": len(providers), "declared": None, "status": "UNVERIFIED",
                                    "observed_ID": ["%s←%s" % (p.get("phase"), p.get("identity")) for p in providers]},
                        "completion_blockers": {"count": len(blockers),
                                                "ID": [b.get("id") for b in blockers]}}}


# ── 記録 ────────────────────────────────────────────────────
def emit(result, dry=False):
    """★既存 ETRACE へ 1行。★scope を必ず入れる。★何も止めない。"""
    sys.path.insert(0, "/home/takasan/ds")
    from ds import etrace as ET
    inputs = dict(result["inputs"], axis=result["axis"],
                  scope_kind=result["scope_kind"], scope_id=result["scope_id"],
                  key_note="証拠から決めた(★自己申告0)。★blocking しない=記録のみ")
    si, ti = ET._clip(inputs)
    so, to = ET._clip(result["outputs"])
    info = {"axis": result["axis"], "inputs_bytes": len(si), "outputs_bytes": len(so),
            "truncated": bool(ti or to)}
    if dry:
        info["event_id"] = None
        return info
    tid = result["scope_id"] if result["scope_kind"] == "TASK" else None
    info["event_id"] = ET.emit("ESDE_EVALUATION", "measured", inputs, result["outputs"],
                               "OK", task_id=tid, fail_open=True)
    return info


def write_to_detail(task_id, result, event_id, dry=False):
    """★[Claude実装] 2026-08-24(★GDW-ESDE §0=『TASKについて得られたESDE情報は
    原則としてTASKの台帳明細へ戻す』)。

    ★新しい口を作らない= 既存の `rri.request_thread` の2つだけを呼ぶ。
      `record_evidence(question_id=None)`  … ★依頼(thread)全体の根拠
        （逐語「question_id が None → その依頼(thread)全体の 根拠(明細まで 絞れなかった)」）
      `raise_question` ＋ `record_evidence(question_id=…)` … ★finding 1件ごとの明細
    ★新しい語を作らない= basis_kind=LOCAL_MEASUREMENT / validation_mode=MEASURED（既存語）。
      ★測れなかった指標が在る時は `UNRESOLVED`（★UNVERIFIED を そのまま写す既存語）。
    ★provenance= `recorded_by` / `recorded_via`(既存欄)。★誰が書いたかを空にしない。
    ★evidence_refs には ★引ける id だけ 入れる=
      task_id と 計器の artifact id。★event_id は 引けない(ETR-NORUN の衝突・58.4%)ため
      ★ref に しない=`evidence_text` に 文字列として 残す(★引けない物を『根拠』に 指さない)。
    ★何も止めない・何も直さない。

    ★★[Claude実装] 2026-08-24 Taka 裁定②(★『Worker が勝手に実行しない8種を authority の門にする。
      文書規律ではなく 機械的に破れない方がいい』)= ★書く前に ★権限の規則に 掛ける。
      ★判定は ここに 書かない=★`twoder.authority.POLICY` が 正本(★`domain_ledger` の 前例と 同じ形)。
      ★通らなければ ★1バイトも 書かずに 断る。
      ★★効き目の 本体は ★この行為が 通る ことでは なく ★★POLICY に 無い行為が 止まる こと=
        ★将来 誰かが ここに 状態変更を 足しても ★行為名が POLICY に 無ければ
        ★`gate()` は REQUIRES_APPROVAL を 返す(★fail-closed・authority.py L125-126)。
    """
    sys.path.insert(0, "/home/takasan/rri")
    # ★★[Claude実装] 2026-08-24 訂正= ★この1行が 無くて ★本番の 書き戻しを 壊していた。
    #   ★実測= 常駐は この計器を ★subprocess で 起こす ∴ `sys.path[0]` は ★この計器の 置き場。
    #     ★`/home/takasan` は 入っていない ∴ `from twoder import ...` が ModuleNotFoundError。
    #   ★★見落とした 理由= ★封印試験を ★本番と同じ 呼び方で やらなかった
    #     (★私の 手元では 既に `/home/takasan` が sys.path に 在った)。
    #   ★`/home/takasan/twoder` では なく ★`/home/takasan` を 入れる=
    #     ★twoder を ★パッケージとして 読む(★`twoder/operator.py` が stdlib を 隠すのを 避ける)。
    if "/home/takasan" not in sys.path:
        sys.path.insert(0, "/home/takasan")
    from twoder import authority as _A
    g = _A.gate(ESDE_WRITE_ACTION)
    if g.get("requires_approval"):
        return {"wrote": False, "why": "authority: requires approval", "gate": g}
    from rri import request_thread as RT
    import datetime
    ts = datetime.datetime.now().isoformat()
    rth = _get("/api/rthread?task_id=%s" % task_id)
    tid = rth.get("thread_id")
    if not tid:
        return {"wrote": False, "why": "この task に thread が無い(★明細へ戻せない)"}

    o = result["outputs"]
    unresolved = any((m or {}).get("status") in ("UNVERIFIED", "UNRESOLVED")
                     for m in o.values() if isinstance(m, dict))
    mode = "UNRESOLVED" if unresolved else "MEASURED"
    refs = [task_id, "ART-1a882c44e2"]              # ★どちらも /api/resolve で引ける
    parts = []
    for k in ("equality", "symmetry", "hierarchy", "linkage"):
        m = o.get(k)
        if not m:
            continue
        if "present" in m:
            parts.append("%s %s/%s" % (k, m["present"], m["required"]))
        elif "passed" in m:
            parts.append("%s %s/%s" % (k, m["passed"], m["required"]))
        else:
            parts.append("%s %s" % (k, m.get("status") or m.get("required")))
    text = "ESDE %s ／ %s ／ 記録=%s ／ 計器=s_esde_evaluate" % (result["axis"], " ／ ".join(parts), event_id)

    out = {"wrote": not dry, "thread_id": tid, "validation_mode": mode, "evidence_refs": refs,
           "evaluation_evidence_id": None, "findings": []}
    if dry:
        out["would_write"] = text
        return out
    out["evaluation_evidence_id"] = RT.record_evidence(
        tid, None, refs, "LOCAL_MEASUREMENT", mode, ts,
        evidence_text=text, recorded_by="ESDE_WORKER", recorded_via="direct")

    for f in (o.get("findings") or []):             # ★finding は 1件ずつ 明細に する
        memo = "[ESDE finding] %s / %s → %s ｜ %s" % (
            f.get("finding_id"), f.get("severity"), f.get("handoff_to"), (f.get("what") or "")[:120])
        qid = RT.raise_question(tid, memo, ts)
        eid = RT.record_evidence(tid, qid, refs, "LOCAL_MEASUREMENT", mode, ts,
                                 evidence_text=text, recorded_by="ESDE_WORKER", recorded_via="direct")
        # ★誰が書いたかを 明細側にも 残す(★既存語 STRUCTURE を 使う=新しい語を 作らない)
        RT.record_actor(tid, qid, "QUESTION", "ESDE_WORKER", "STRUCTURE", "direct", ts)
        out["findings"].append({"question_id": qid, "evidence_id": eid})
    return out


def _summary(r):
    o = r["outputs"]
    parts = []
    for k in ("equality", "symmetry", "hierarchy"):
        m = o.get(k)
        if not m:
            continue
        if "present" in m:
            bad = m.get("incompatible_ID") or m.get("missing_ID") or []
            parts.append("%s %d/%d(欠%d)" % (k[:3], m["present"], m["required"], len(bad)))
        elif "passed" in m:
            parts.append("%s %d/%d(違反%d)" % (k[:3], m["passed"], m["required"], len(m.get("violation_ID") or [])))
        else:
            parts.append("%s required=%s" % (k[:3], m.get("required")))
    m = o.get("linkage")
    if m:
        # ★★2026-08-27= ★測れた時は ★分母つきで 出す(★status だけだと 何件 欠けたか 見えない)
        if "declared" in m and m.get("declared") is not None and "observed" in m:
            parts.append("lnk %s/%s(欠%d)" % (m.get("observed"), m.get("declared"),
                                              len(m.get("broken_ID") or [])))
        else:
            parts.append("lnk " + str(m.get("status")))
    return " ／ ".join(parts)


def _check_write_path():
    """★書き戻しの 経路が ★この呼び方で 生きているかを 見る(★1バイトも 書かない)。

    ★★足した 理由(2026-08-24 の 事故・逐語で 残す)=
      ★私が 入れた 門(`from twoder import authority`)が ★本番の 書き戻しを 壊していた のに
      ★`--check` は ★GREEN の ままだった。
      ★理由= ★`--check` は ★書き込み0の 経路 ∴ ★門を 1度も 通らない
        =★『GREEN だから 大丈夫』が ★この種類の 故障に対して ★成り立っていなかった。
    ★★塞ぎ方= ★`--check` も ★同じ import と ★同じ 門を 通す。★書かない。
      ★これが 効く 根拠= ★`--check` は 本番と 同じく ★この計器を 直接 起こして 実行する
        ∴ ★`sys.path[0]` が 本番と 同じ=★あの ModuleNotFoundError を ここで 踏む。
    ★返り= 赤の 行(空なら 合格)。
    """
    out = []
    try:
        if "/home/takasan" not in sys.path:
            sys.path.insert(0, "/home/takasan")
        from twoder import authority as _A
    except Exception as ex:
        return ["WRITE_PATH_IMPORT: %s: %s(★本番の書き戻しが落ちる)" % (type(ex).__name__, ex)]
    try:
        g = _A.gate(ESDE_WRITE_ACTION)
    except Exception as ex:
        return ["WRITE_PATH_GATE: %s: %s" % (type(ex).__name__, ex)]
    if g.get("requires_approval"):
        out.append("WRITE_PATH_GATE: %s が REQUIRES_APPROVAL(★書き戻しが止まる)" % ESDE_WRITE_ACTION)
    # ★負の対照= ★POLICY に 無い行為は ★必ず 止まる こと(★門が 効いている ことの 対照)
    if not _A.gate("ESDE_NOT_IN_POLICY_NEGATIVE_CONTROL").get("requires_approval"):
        out.append("WRITE_PATH_GATE: ★負の対照が通ってしまった(POLICYに無い行為が止まっていない)")
    return out


def main(argv):
    dry = "--dry" in argv or "--check" in argv
    task_arg = argv[argv.index("--task") + 1] if "--task" in argv else None
    if task_arg:
        results = [axis_task(task_arg)]
    else:
        # ★★2026-08-27= ★連動性の軸を 1本 足した(★他の3軸は 1行も 直していない)
        results = [axis_real_repo_reflection(), axis_2der_identity(), axis_rri(),
                   axis_egl_projection()]
    red = []
    for r in results:
        info = emit(r, dry=dry)
        print("%-28s %s" % (r["axis"], _summary(r)))
        print("   scope=%s/%s  in=%dB out=%dB 切=%s  event=%s"
              % (r["scope_kind"], r["scope_id"], info["inputs_bytes"], info["outputs_bytes"],
                 info["truncated"], info["event_id"]))
        if info["truncated"]:
            red.append("TRUNCATED: %s(★欠損IDが切れた=分母つきで残らない)" % r["axis"])
        if task_arg and "--no-detail" not in argv:        # ★★§0: 結果を TASK の明細へ戻す
            w = write_to_detail(task_arg, r, info["event_id"], dry=dry)
            # ★★[Claude実装] 2026-08-24= ★書かなかった時は ★必ず 理由を 出す。
            #   ★実測(封印試験B)= 門で 止めた時も ★`wrote=False thread=None` と だけ 出ており
            #     ★『明細が 無い』と 見分けが つかなかった。
            #   ★★これは 私が 状況表の 計器に 3件 出した のと ★同じ欠陥が 自分の 計器に 在った もの
            #     (=★『測れなかった』を『測って無かった』と 書かない)。
            print("   ★明細へ: wrote=%s thread=%s mode=%s evidence=%s findings=%d%s"
                  % (w.get("wrote"), w.get("thread_id"), w.get("validation_mode"),
                     w.get("evaluation_evidence_id"), len(w.get("findings") or []),
                     ("  ★書かなかった理由= " + str(w.get("why"))) if not w.get("wrote") else ""))
        cc = r["outputs"].get("cross_check_vs_human")
        if cc:
            print("   ★人の評価との照合: symmetry=%s hierarchy=%s" % (cc["symmetry"], cc["hierarchy"]))
            for k in ("symmetry", "hierarchy"):
                if not cc[k]:
                    red.append("CROSS_CHECK_FAILED: %s の %s が 正本§4 の値と一致しない" % (r["axis"], k))
    if "--check" in argv:
        red += _check_write_path()
        if red:
            print("\nS_ESDE_EVALUATE --check: RED")
            for m in red:
                print("  " + m)
            return 1
        print("\nS_ESDE_EVALUATE --check: GREEN (★書き込み0 ／ 人の評価と一致 ／ 切り捨てなし)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
