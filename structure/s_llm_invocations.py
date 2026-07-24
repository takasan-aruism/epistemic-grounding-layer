#!/usr/bin/env python3
"""s_llm_invocations — 全 LLM 呼出点の決定論台帳(EXEC_ARCH B / SPEC_LLM_INVOCATION_MAP_v0.1)。

LLM を検出に使わない(決定論・byte一致再生成)。core=call と mention の区別:
文字列スキャン単独は vacuous(docstring 否定宣言/regex/denylist を呼出点と誤認)。
一次検出は AST(urlopen Call + module が LLM chat endpoint を持つ)。二次(文字列)は MENTION_ONLY。

usage:
  s_llm_invocations.py            # 台帳を再生成(LLM_INVOCATIONS.jsonl)
  s_llm_invocations.py --check    # 常設ゲート(byte一致 / 未登録CALL_SITE / 陰性対照)
"""
import ast
import hashlib
import json
import os
import sys

ROOT = "/home/takasan"
REPOS = ("twoder", "egl", "rri", "ds", "dev-workcell")
OUT = os.path.join(ROOT, "egl", "structure", "LLM_INVOCATIONS.jsonl")

CHAT_MARKER = "/v1/chat/completions"          # LLM chat primitive(最強シグナル)
PORT_MARKERS = (":8005", ":8006")             # vLLM server ports
WRAPPER_NAMES = ("_chat", "adjudicate", "call_vllm")
EXCLUDE_DIRS = ("__pycache__", ".git", "node_modules")


def _iter_py():
    for repo in REPOS:
        base = os.path.join(ROOT, repo)
        for dp, dns, fns in os.walk(base):
            dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
            for fn in fns:
                if fn.endswith(".py"):
                    ab = os.path.join(dp, fn)
                    yield repo, os.path.relpath(ab, ROOT), ab


def _klass(rel):
    parts = rel.replace("\\", "/").split("/")
    if "experiments" in parts or "gpu_experiment" in parts:
        return "EXPERIMENT"
    if "docs" in parts or any(p.startswith("SUBMIT") for p in parts):
        return "DOC_ARTIFACT"
    return "MAINLINE"


def _str_consts(tree):
    """module-level 定数名 -> str 値。plain literal と os.environ.get(k,'default')/getenv の default を解決。"""
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        val = None
        v = node.value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            val = v.value
        elif isinstance(v, ast.Call):
            f = v.func
            is_env = (isinstance(f, ast.Attribute) and f.attr == "get") or \
                     (isinstance(f, ast.Name) and f.id == "getenv")
            if is_env and len(v.args) >= 2 and isinstance(v.args[1], ast.Constant) \
                    and isinstance(v.args[1].value, str):
                val = v.args[1].value
        if val is not None:
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = val
    return out


def _func_is_llm(fn, const_map):
    """関数レベル判定(§1(1)準拠): 関数の literal + 参照 module 定数に chat/port marker、または wrapper 名。"""
    blob = _func_texts(fn)
    for nm in _names_used(fn) & set(const_map):
        blob += "\n" + const_map[nm]
    if CHAT_MARKER in blob or any(p in blob for p in PORT_MARKERS):
        return True
    return fn.name in WRAPPER_NAMES


def _func_texts(fn):
    """関数内の全 str リテラルを連結(chat marker 検出用)。"""
    return "\n".join(n.value for n in ast.walk(fn)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str))


def _names_used(fn):
    return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}


def _has_urlopen(fn):
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Attribute) and f.attr == "urlopen") or \
               (isinstance(f, ast.Name) and f.id == "urlopen"):
                return n
    return None


def _endpoint_of(module_text, const_map, fn):
    """関数が触れる LLM endpoint を解決。UNRESOLVED は捏造しない(G-4)。"""
    # 関数内リテラル or 参照する module 定数から port/endpoint を拾う
    blob = _func_texts(fn)
    for nm in _names_used(fn) & set(const_map):
        blob += "\n" + const_map[nm]
    for p in PORT_MARKERS:
        if p in blob:
            return p
    return "UNRESOLVED"


def _model_of(fn, const_map):
    """payload の model= 値(dict "model": <literal> or var)。不能は UNRESOLVED。"""
    for n in ast.walk(fn):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "model":
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        return v.value
                    if isinstance(v, ast.Name):
                        return const_map.get(v.id, "UNRESOLVED")
                    return "UNRESOLVED"
    return "UNRESOLVED"


def _module_is_llm(module_text, const_map):
    """module が LLM chat endpoint を持つか(chat marker を定数 or 本文に)。"""
    if CHAT_MARKER in module_text:
        return True
    for v in const_map.values():
        if CHAT_MARKER in v:
            return True
    return False


def _mint(caller, func, lineno):
    return "LLMINV-" + hashlib.sha1(("%s:%s:%d" % (caller, func, lineno)).encode()).hexdigest()[:8]


def _record(rel, func, lineno, record_class, model="UNRESOLVED", endpoint="UNRESOLVED",
            gate_ref="NONE", status="UNRESOLVED"):
    caller = "%s:%s" % (rel.replace("\\", "/"), func)
    return {
        "invocation_id": _mint(rel, func, lineno),
        "caller": caller,
        "lineno": lineno,
        "record_class": record_class,
        "class": _klass(rel),
        "model": model,
        "endpoint": endpoint,
        "system_prompt_source": "UNRESOLVED",
        "context_builder": "PYTHON",
        "schema_enforced": "UNRESOLVED",
        "output_validator": "UNRESOLVED",
        "failure_handling": "UNRESOLVED",
        "result_store": "UNRESOLVED",
        "status": status,
        "gate_ref": gate_ref,
    }


def analyze(rel, src):
    """1 file -> records。AST 一次(CALL_SITE/WRAPPER_DEF) + 文字列二次(MENTION_ONLY)。"""
    recs = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return recs
    const_map = _str_consts(tree)
    module_llm = _module_is_llm(src, const_map)

    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    call_funcs = set()
    for fn in funcs:
        uo = _has_urlopen(fn)
        if uo is not None and _func_is_llm(fn, const_map):
            recs.append(_record(rel, fn.name, uo.lineno, "CALL_SITE",
                                model=_model_of(fn, const_map),
                                endpoint=_endpoint_of(src, const_map, fn),
                                status="GATED(USE_VLLM_INFERENCE)"
                                       if "USE_VLLM_INFERENCE" in src else "LIVE",
                                gate_ref="USE_VLLM_INFERENCE" if "USE_VLLM_INFERENCE" in src else "NONE"))
            call_funcs.add(fn.name)
        if fn.name in WRAPPER_NAMES and module_llm:
            if fn.name not in call_funcs or uo is None:
                recs.append(_record(rel, fn.name, fn.lineno, "WRAPPER_DEF",
                                    endpoint=_endpoint_of(src, const_map, fn)))

    # 二次: chat/port marker を持つが CALL_SITE でない = MENTION_ONLY(module 単位で1件)
    if not any(r["record_class"] == "CALL_SITE" for r in recs):
        if CHAT_MARKER in src or any(p in src for p in PORT_MARKERS):
            # docstring 否定宣言 / regex / denylist を呼出点にしない
            recs.append(_record(rel, "<module>", 1, "MENTION_ONLY"))
    return recs


def build():
    recs = []
    for repo, rel, ab in _iter_py():
        try:
            src = open(ab, encoding="utf-8").read()
        except Exception:
            continue
        if CHAT_MARKER not in src and not any(p in src for p in PORT_MARKERS) \
                and "urlopen" not in src:
            continue
        recs += analyze(rel, src)
    recs.sort(key=lambda r: (r["record_class"] != "CALL_SITE", r["caller"], r["lineno"]))
    return recs


def _serialize(recs):
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in recs)


# ── 陰性対照(vacuous 防止・G-T1): docstring だけに endpoint を持つ決定論モジュール ──
# 実 egl/egl/adapters.py と同型: urlopen を持つが LLM でない web-fetch。:8005//v1/chat は docstring のみ。
# vacuous 検出器(文字列 or module レベル)なら CALL_SITE と誤検出する → 陰性対照が赤になるべき。
_NEG_CONTROL = (
    '"""fetch adapter. mentions :8005 and /v1/chat/completions in THIS docstring only.\n'
    'deterministic web-fetch, no LLM call."""\n'
    'import re\n'
    'import urllib.request\n'
    'PAT = re.compile(r":8005")\n'
    'def fetch(url):\n'
    '    req = urllib.request.Request(url)\n'
    '    with urllib.request.urlopen(req, timeout=5) as r:\n'
    '        return r.read()\n'
)


def _negative_control_ok():
    recs = analyze("synthetic/neg_control.py", _NEG_CONTROL)
    # CALL_SITE を1件も出してはならない(mention は可)
    return not any(r["record_class"] == "CALL_SITE" for r in recs)


def check():
    fresh = _serialize(build())
    existing = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
    red = []
    if fresh != existing:
        red.append("REGEN_MISMATCH: ledger not byte-identical to fresh regen (run without --check to update)")
    # 未登録 CALL_SITE
    reg_ids = {json.loads(l)["invocation_id"] for l in existing.splitlines() if l.strip()}
    for r in build():
        if r["record_class"] == "CALL_SITE" and r["invocation_id"] not in reg_ids:
            red.append("UNREGISTERED_CALL_SITE: %s" % r["caller"])
    if not _negative_control_ok():
        red.append("NEGATIVE_CONTROL_FAILED: detector flagged a docstring-only module as CALL_SITE (vacuous)")
    if red:
        print("LLM_INVOCATIONS --check: RED")
        for m in red:
            print("  " + m)
        return 1
    calls = sum(1 for l in existing.splitlines() if l.strip() and json.loads(l)["record_class"] == "CALL_SITE")
    print("LLM_INVOCATIONS --check: GREEN (negative-control ok; %d CALL_SITE registered; byte-identical)" % calls)
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    recs = build()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(_serialize(recs))
    n_call = sum(1 for r in recs if r["record_class"] == "CALL_SITE")
    n_wrap = sum(1 for r in recs if r["record_class"] == "WRAPPER_DEF")
    n_ment = sum(1 for r in recs if r["record_class"] == "MENTION_ONLY")
    print("wrote %d records to %s (CALL_SITE=%d WRAPPER_DEF=%d MENTION_ONLY=%d)"
          % (len(recs), OUT, n_call, n_wrap, n_ment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
