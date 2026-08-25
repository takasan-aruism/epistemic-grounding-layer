#!/usr/bin/env python3
"""s_llm_invocations — 全 LLM 呼出点の決定論台帳(EXEC_ARCH B / SPEC_LLM_INVOCATION_MAP_v0.1)。

v0.2(Inference Control Domain §13 Phase 1): worker 系統を2つに分ける。VLLM(:8005/:8006 への urlopen)に加え
CLAUDE_P(headless `claude -p` の subprocess 起動)を一次検出に入れる。v0.1 は urlopen だけを見ていたため
Claude Worker の呼出点が 0件 として台帳に載らなかった(実測 4件 = senior_review/question_review/webui x2)。
検出は AST 一次のまま(文字列単独は vacuous)。argv は module 定数 list と局所 `list(CONST)` まで解決する。

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
CLAUDE_BIN = "claude"                         # headless Claude Code worker(CLI)
CLAUDE_PRINT_FLAGS = ("-p", "--print")        # 非対話(1往復)である証拠
SUBPROC_FUNCS = ("run", "Popen", "check_output", "call", "check_call")

# ── v0.3(Inference Control §13 Phase 1 の残り): 欄を「埋める」のでなく ★既存の閉じた語彙へ写す ──
# ★新語を作らない。正本= twoder/handoff_contract.py:44 VERDICTS(写し。--check で drift を見る)。
#   EXISTS   = 在る(呼出点の本文から取れた)
#   ABSENT   = 探して 無い(★設計上 持っていない)
#   UNVERIFIED = この scope では 決められない(★0件と書かない)
# ★PARTIAL / CONFLICT は この計器では 発生しない(1呼出点に1つの事実しか見ていない) ∴ 使わない。
VERDICTS = ("EXISTS", "PARTIAL", "ABSENT", "CONFLICT", "UNVERIFIED")
SCHEMA_KEYS = ("response_format", "guided_json", "guided_regex", "guided_choice", "tools", "tool_choice")
RUNTIME_KEYS = ("temperature", "seed", "max_tokens")
VALIDATOR_NAMES = ("loads", "search", "findall", "match", "fullmatch")

# ── v0.4: 知識を呼出点から引けるようにする(★新台帳を作らない=知識は既存の docs に置いたまま) ──
# doc 側が ★自分で名乗る(名前一致で拾わない= vacuous 回避)。HTML コメントに次を書く:
#   2DER:LLM_KNOWLEDGE / knowledge_id: LLMK-0001 / call_sites: <rel>:<func> ...
#   applies_when: <field>=<value> ...   / maturity: <既存の梯子の語>
# ★成熟度の正本= twoder/egl_integration.py:17 _LADDER(写し。--check で drift を見る)。
KNOWLEDGE_MARKER = "2DER:LLM_KNOWLEDGE"
KNOWLEDGE_DIR = os.path.join(ROOT, "egl", "docs")
MATURITY_LADDER = ("REPORTED", "INFERRED", "OBSERVED", "MEASURED", "REPRODUCED", "ACCEPTED")
KNOWLEDGE_FIELDS = ("knowledge_id", "call_sites", "applies_when", "maturity")
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


def _payload_dict(fn):
    """呼出の body になる dict(model/messages を持つ最初の Dict)。無ければ None。"""
    for n in ast.walk(fn):
        if not isinstance(n, ast.Dict):
            continue
        keys = {k.value for k in n.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "model" in keys and "messages" in keys:
            return n
    return None


def _dict_get(d, key):
    for k, v in zip(d.keys, d.values):
        if isinstance(k, ast.Constant) and k.value == key:
            return v
    return None


def _lit_or_unresolved(node, const_map, fn=None):
    """定数なら値、module 定数名なら値、関数の既定引数なら値。取れなければ UNRESOLVED(捏造しない)。"""
    if isinstance(node, ast.Constant) and not isinstance(node.value, (dict, list)):
        return json.dumps(node.value, ensure_ascii=False)
    if isinstance(node, ast.Name):
        if node.id in const_map:
            return const_map[node.id]
        if fn is not None:                      # 関数の既定引数(seed=0 / max_tokens=1200)
            args = fn.args
            defaults = list(args.defaults)
            pos = list(args.args)[len(args.args) - len(defaults):]
            for a, d in zip(pos, defaults):
                if a.arg == node.id and isinstance(d, ast.Constant):
                    return json.dumps(d.value, ensure_ascii=False)
            for a, d in zip(args.kwonlyargs, args.kw_defaults):
                if a.arg == node.id and isinstance(d, ast.Constant):
                    return json.dumps(d.value, ensure_ascii=False)
    return "UNRESOLVED"


def _runtime_of(fn, const_map, call_node):
    """temperature / seed / max_tokens / timeout。★取れないものは UNRESOLVED のまま残す。"""
    out = {k: "UNRESOLVED" for k in RUNTIME_KEYS}
    out["timeout"] = "UNRESOLVED"
    d = _payload_dict(fn)
    if d is not None:
        for k in RUNTIME_KEYS:
            v = _dict_get(d, k)
            if v is not None:
                out[k] = _lit_or_unresolved(v, const_map, fn)
    if call_node is not None:
        for kw in call_node.keywords:
            if kw.arg == "timeout":
                out["timeout"] = _lit_or_unresolved(kw.value, const_map, fn)
    return out


def _system_prompt_of(fn):
    """messages に role=system が在るか -> (verdict, source)。★source は1つのことだけ指す。"""
    d = _payload_dict(fn)
    if d is None:
        return "UNVERIFIED", "UNRESOLVED"
    msgs = _dict_get(d, "messages")
    if not isinstance(msgs, ast.List):
        return "UNVERIFIED", "UNRESOLVED"
    for m in msgs.elts:
        if not isinstance(m, ast.Dict):
            return "UNVERIFIED", "UNRESOLVED"
        role = _dict_get(m, "role")
        if isinstance(role, ast.Constant) and role.value == "system":
            content = _dict_get(m, "content")
            if isinstance(content, ast.Constant):
                return "EXISTS", "LITERAL"
            if isinstance(content, ast.Name):
                names = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
                return "EXISTS", ("PARAM" if content.id in names else "PYTHON")
            return "EXISTS", "PYTHON"
    return "ABSENT", "ABSENT"          # ★messages は読めた・system 役が 無い(設計上 持っていない)


def _schema_enforced_of(fn):
    d = _payload_dict(fn)
    if d is None:
        return "UNVERIFIED"
    keys = {k.value for k in d.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return "EXISTS" if keys & set(SCHEMA_KEYS) else "ABSENT"


def _output_validator_of(fn):
    """返答を そのまま使わずに 通す物が 在るか(json.loads / re.* / parse_*)。"""
    for n in ast.walk(fn):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if nm in VALIDATOR_NAMES or nm.startswith("parse_"):
            return "EXISTS"
    return "ABSENT"


def _failure_handling_of(fn, call_node):
    """呼出が try の中に在るか。★『在る/無い』だけを言う(質は見ていない)。"""
    if call_node is None:
        return "UNVERIFIED"
    for n in ast.walk(fn):
        if isinstance(n, ast.Try):
            for b in n.body:
                for x in ast.walk(b):
                    if x is call_node:
                        return "EXISTS"
    return "ABSENT"


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


def _list_consts(tree):
    """module-level 定数名 -> list の要素(str は値、非 str は None)。argv 解決用。"""
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List):
            continue
        vals = []
        for e in node.value.elts:
            vals.append(e.value if isinstance(e, ast.Constant) and isinstance(e.value, str) else None)
        for t in node.targets:
            if isinstance(t, ast.Name):
                out[t.id] = vals
    return out


def _local_lists(fn, list_consts):
    """関数内の argv 候補: `cmd = [...]` / `cmd = CONST` / `cmd = list(CONST)`。解決不能は入れない。"""
    out = {}
    for n in ast.walk(fn):
        if not isinstance(n, ast.Assign):
            continue
        v, vals = n.value, None
        if isinstance(v, ast.List):
            vals = [e.value if isinstance(e, ast.Constant) and isinstance(e.value, str) else None
                    for e in v.elts]
        elif isinstance(v, ast.Name):
            vals = list_consts.get(v.id)
        elif isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "list" \
                and len(v.args) == 1 and isinstance(v.args[0], ast.Name):
            vals = list_consts.get(v.args[0].id)
        if vals is not None:
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = list(vals)
    return out


def _argv_of(call, fn, list_consts):
    """subprocess 呼出の第1引数を argv(list of str|None) へ解決。解決不能は None(捏造しない)。"""
    if not call.args:
        return None
    a0 = call.args[0]
    if isinstance(a0, ast.List):
        return [e.value if isinstance(e, ast.Constant) and isinstance(e.value, str) else None
                for e in a0.elts]
    if isinstance(a0, ast.Name):
        return _local_lists(fn, list_consts).get(a0.id) or list_consts.get(a0.id)
    if isinstance(a0, ast.Call) and isinstance(a0.func, ast.Name) and a0.func.id == "list" \
            and len(a0.args) == 1 and isinstance(a0.args[0], ast.Name):
        return list_consts.get(a0.args[0].id)
    return None


def _is_claude_p(argv):
    """argv が headless claude worker の起動か。argv[0]==claude かつ -p/--print を含むこと。"""
    if not argv or not argv[0]:
        return False
    if os.path.basename(argv[0]) != CLAUDE_BIN:
        return False
    return any(f in argv for f in CLAUDE_PRINT_FLAGS if f)


def _nested_call_ids(fn):
    """入れ子の関数/lambda が持つ Call の id 集合。呼出点は ★最内の関数へ1回だけ帰属させる
    (ast.walk は入れ子も辿るため、外側の関数にも同じ呼出が二重計上される)。"""
    ids = set()
    for inner in ast.walk(fn):
        if inner is fn or not isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        for n in ast.walk(inner):
            if isinstance(n, ast.Call):
                ids.add(id(n))
    return ids


def _subprocess_names(tree):
    """import から subprocess の別名を取る -> (module_aliases, 直輸入した関数名)。
    ★引数として渡された `run(cmd)` のような注入口を呼出点に数えないための決定論の縛り。"""
    mods, funcs = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "subprocess":
                    mods.add(a.asname or a.name)
        elif isinstance(n, ast.ImportFrom) and n.module == "subprocess":
            for a in n.names:
                if a.name in SUBPROC_FUNCS:
                    funcs.add(a.asname or a.name)
    return mods, funcs


def _claude_p_calls(fn, list_consts, sp_mods, sp_funcs):
    """関数内の claude -p 起動を全件返す [(lineno, argv)]。入れ子ぶんは最内の関数が持つ。"""
    hits = []
    nested = _nested_call_ids(fn)
    for n in ast.walk(fn):
        if id(n) in nested:
            continue
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Attribute):
            base = f.value.id if isinstance(f.value, ast.Name) else None
            ok = f.attr in SUBPROC_FUNCS and base in sp_mods
        elif isinstance(f, ast.Name):
            ok = f.id in sp_funcs
        else:
            ok = False
        if not ok:
            continue
        argv = _argv_of(n, fn, list_consts)
        if _is_claude_p(argv):
            hits.append((n.lineno, argv))
    return hits


def _knowledge_docs():
    """名乗った doc だけを読む -> [{knowledge_id, call_sites, applies_when, maturity, doc}]。
    ★決定論のため path 順に走る。★欄が欠けた doc は 捨てずに 返す(--check が名指しする)。"""
    out = []
    for dp, dns, fns in sorted(os.walk(KNOWLEDGE_DIR)):
        dns.sort()
        for fn in sorted(fns):
            if not fn.endswith(".md"):
                continue
            ab = os.path.join(dp, fn)
            try:
                txt = open(ab, encoding="utf-8").read()
            except Exception:
                continue
            if KNOWLEDGE_MARKER not in txt:
                continue
            rec = {"doc": os.path.relpath(ab, ROOT), "knowledge_id": None,
                   "call_sites": [], "applies_when": {}, "maturity": None}
            head = txt.split(KNOWLEDGE_MARKER, 1)[1]
            for ln in head.splitlines():
                s = ln.strip()
                if s.startswith("-->") or s.startswith("#"):
                    break
                if ":" not in s:
                    continue
                k, v = s.split(":", 1)
                k, v = k.strip(), v.strip()
                if k == "knowledge_id":
                    rec["knowledge_id"] = v
                elif k == "call_sites":
                    rec["call_sites"] = [x for x in v.replace(",", " ").split() if x]
                elif k == "maturity":
                    rec["maturity"] = v
                elif k == "applies_when":
                    for pair in v.split():
                        if "=" in pair:
                            a, b = pair.split("=", 1)
                            rec["applies_when"][a] = b
            out.append(rec)
    return out


def _knowledge_for(rec, docs):
    """1呼出点に効く知識の id。①doc が名指しした ②applies_when が全部一致(=同型 call)。"""
    ids = set()
    for k in docs:
        if not k["knowledge_id"]:
            continue
        if rec["caller"] in k["call_sites"]:
            ids.add(k["knowledge_id"])
            continue
        aw = k["applies_when"]
        if aw and all(str(rec.get(f)) == v for f, v in aw.items()):
            ids.add(k["knowledge_id"])
    return sorted(ids)


def _mint(caller, func, lineno):
    return "LLMINV-" + hashlib.sha1(("%s:%s:%d" % (caller, func, lineno)).encode()).hexdigest()[:8]


def _record(rel, func, lineno, record_class, model="UNRESOLVED", endpoint="UNRESOLVED",
            gate_ref="NONE", status="UNRESOLVED", worker="VLLM", runtime=None,
            system_prompt="UNVERIFIED", system_prompt_source="UNRESOLVED",
            schema_enforced="UNVERIFIED", output_validator="UNVERIFIED",
            failure_handling="UNVERIFIED"):
    runtime = runtime or {}
    caller = "%s:%s" % (rel.replace("\\", "/"), func)
    return {
        "invocation_id": _mint(rel, func, lineno),
        "caller": caller,
        "lineno": lineno,
        "record_class": record_class,
        "worker": worker,
        "class": _klass(rel),
        "model": model,
        "endpoint": endpoint,
        "system_prompt": system_prompt,
        "system_prompt_source": system_prompt_source,
        "context_builder": "PYTHON",
        "schema_enforced": schema_enforced,
        "output_validator": output_validator,
        "failure_handling": failure_handling,
        # ★result_store は ★呼び手の側に在る ∴ この scope(呼出点の関数)では 決められない。
        #   ★埋めない= UNVERIFIED。★0件・不在と 書かない。
        "result_store": "UNVERIFIED",
        "temperature": runtime.get("temperature", "UNRESOLVED"),
        "seed": runtime.get("seed", "UNRESOLVED"),
        "max_tokens": runtime.get("max_tokens", "UNRESOLVED"),
        "timeout": runtime.get("timeout", "UNRESOLVED"),
        "status": status,
        "gate_ref": gate_ref,
        "knowledge_refs": [],
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

    list_consts = _list_consts(tree)
    sp_mods, sp_funcs = _subprocess_names(tree)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    # v0.2: CLAUDE_P worker(headless claude -p)。endpoint は CLI、model は CLI 既定ゆえ UNRESOLVED(捏造しない)。
    for fn in funcs:
        for lineno, argv in _claude_p_calls(fn, list_consts, sp_mods, sp_funcs):
            _cnode = None
            for n in ast.walk(fn):
                if isinstance(n, ast.Call) and n.lineno == lineno:
                    _cnode = n
                    break
            # ★CLI に system prompt の旗が在るか(--system-prompt / --append-system-prompt)。
            _has_sys = any(a and a.startswith("--") and "system-prompt" in a for a in argv)
            # ★--output-format json は 返答の形の 指定 ∴ schema_enforced は EXISTS。
            _has_fmt = "--output-format" in [a for a in argv if a]
            recs.append(_record(rel, fn.name, lineno, "CALL_SITE", worker="CLAUDE_P",
                                model="UNRESOLVED", endpoint="CLI(claude -p)", status="LIVE",
                                system_prompt=("EXISTS" if _has_sys else "ABSENT"),
                                system_prompt_source=("CLI_FLAG" if _has_sys else "ABSENT"),
                                schema_enforced=("EXISTS" if _has_fmt else "ABSENT"),
                                output_validator=_output_validator_of(fn),
                                failure_handling=_failure_handling_of(fn, _cnode)))

    call_funcs = set()
    for fn in funcs:
        uo = _has_urlopen(fn)
        if uo is not None and _func_is_llm(fn, const_map):
            _sp, _sps = _system_prompt_of(fn)
            recs.append(_record(rel, fn.name, uo.lineno, "CALL_SITE",
                                model=_model_of(fn, const_map),
                                endpoint=_endpoint_of(src, const_map, fn),
                                runtime=_runtime_of(fn, const_map, uo),
                                system_prompt=_sp, system_prompt_source=_sps,
                                schema_enforced=_schema_enforced_of(fn),
                                output_validator=_output_validator_of(fn),
                                failure_handling=_failure_handling_of(fn, uo),
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
        vllm_ish = CHAT_MARKER in src or any(p in src for p in PORT_MARKERS) or "urlopen" in src
        claude_ish = CLAUDE_BIN in src and any(f in src for f in SUBPROC_FUNCS)
        if not vllm_ish and not claude_ish:
            continue
        recs += analyze(rel, src)
    docs = _knowledge_docs()
    for r in recs:
        r["knowledge_refs"] = _knowledge_for(r, docs) if r["record_class"] == "CALL_SITE" else []
    recs.sort(key=lambda r: (r["record_class"] != "CALL_SITE", r["worker"], r["caller"], r["lineno"]))
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


# v0.2 陰性対照: docstring に `claude -p` を書くだけの決定論モジュール + 別コマンドの subprocess。
# 文字列走査なら CLAUDE_P CALL_SITE と誤検出する → 陰性対照が赤になるべき。
_NEG_CONTROL_CLAUDE = (
    '"""runner. mentions `claude -p` in THIS docstring only. no LLM worker is started."""\n'
    'import subprocess\n'
    'CMD = ["git", "status", "--porcelain"]\n'
    'def run_it():\n'
    '    return subprocess.run(list(CMD), capture_output=True, text=True)\n'
)


# v0.2 陰性対照(2): 引数で渡された runner を呼ぶだけ。argv は claude -p だが subprocess を呼んでいない。
# 「argv に claude -p が在れば呼出点」とする実装なら誤検出する → 陰性対照が赤になるべき。
_NEG_CONTROL_INJECTED = (
    '"""injected runner only. the real subprocess lives in the caller."""\n'
    'CMD = ["claude", "-p", None]\n'
    'def make(run):\n'
    '    def fn(prompt):\n'
    '        cmd = list(CMD)\n'
    '        cmd[2] = prompt\n'
    '        return run(cmd)\n'
    '    return fn\n'
)


def _negative_control_ok():
    recs = analyze("synthetic/neg_control.py", _NEG_CONTROL)
    recs += analyze("synthetic/neg_control_claude.py", _NEG_CONTROL_CLAUDE)
    recs += analyze("synthetic/neg_control_injected.py", _NEG_CONTROL_INJECTED)
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
    # ★語彙 drift: 正本(twoder/handoff_contract.VERDICTS)と 写しが ずれたら 赤。
    try:
        sys.path.insert(0, ROOT)
        from twoder.handoff_contract import VERDICTS as _CANON
        if tuple(_CANON) != tuple(VERDICTS):
            red.append("VOCAB_DRIFT: VERDICTS copy != twoder/handoff_contract.VERDICTS %s" % (tuple(_CANON),))
    except Exception:
        pass                                  # ★引けなければ 黙って通す(この計器は 台帳であって 門ではない)
    # ★閉じた語彙の外の値を 書いていないか(自分の記録を 自分で数える)
    for l in existing.splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        if r["record_class"] != "CALL_SITE":
            continue
        for f in ("system_prompt", "schema_enforced", "output_validator", "failure_handling", "result_store"):
            if r.get(f) not in VERDICTS:
                red.append("VOCAB_VIOLATION: %s.%s=%r not in VERDICTS" % (r["caller"], f, r.get(f)))
    # ★知識 doc の門: 宛先が実在するか / 成熟度が既存の梯子の語か / id が重複しないか
    _docs = _knowledge_docs()
    _callers = {r["caller"] for r in build() if r["record_class"] == "CALL_SITE"}
    _seen_ids = {}
    for k in _docs:
        if not k["knowledge_id"]:
            red.append("KNOWLEDGE_NO_ID: %s" % k["doc"])
            continue
        if k["knowledge_id"] in _seen_ids:
            red.append("KNOWLEDGE_ID_DUP: %s in %s and %s"
                       % (k["knowledge_id"], _seen_ids[k["knowledge_id"]], k["doc"]))
        _seen_ids[k["knowledge_id"]] = k["doc"]
        if k["maturity"] not in MATURITY_LADDER:
            red.append("KNOWLEDGE_MATURITY_UNKNOWN: %s=%r not in _LADDER" % (k["doc"], k["maturity"]))
        for cs in k["call_sites"]:
            if cs not in _callers:
                red.append("KNOWLEDGE_TARGET_MISSING: %s names %s which is not a CALL_SITE" % (k["doc"], cs))
    try:
        sys.path.insert(0, ROOT)
        from twoder.egl_integration import _LADDER as _CANON_LADDER
        _canon = tuple(sorted(_CANON_LADDER, key=lambda x: _CANON_LADDER[x]))
        if _canon != MATURITY_LADDER:
            red.append("VOCAB_DRIFT: MATURITY_LADDER copy != twoder/egl_integration._LADDER %s" % (_canon,))
    except Exception:
        pass
    if red:
        print("LLM_INVOCATIONS --check: RED")
        for m in red:
            print("  " + m)
        return 1
    rows = [json.loads(l) for l in existing.splitlines() if l.strip()]
    calls = [r for r in rows if r["record_class"] == "CALL_SITE"]
    by_w = {}
    for r in calls:
        by_w[r.get("worker", "VLLM")] = by_w.get(r.get("worker", "VLLM"), 0) + 1
    wtxt = " ".join("%s=%d" % (k, by_w[k]) for k in sorted(by_w))
    n_k = sum(1 for r in calls if r.get("knowledge_refs"))
    print("LLM_INVOCATIONS --check: GREEN (negative-control ok; %d CALL_SITE registered [%s]; "
          "knowledge %d doc -> %d call site(s); byte-identical)"
          % (len(calls), wtxt, len(_docs), n_k))
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
    n_cp = sum(1 for r in recs if r["record_class"] == "CALL_SITE" and r["worker"] == "CLAUDE_P")
    print("wrote %d records to %s (CALL_SITE=%d [VLLM=%d CLAUDE_P=%d] WRAPPER_DEF=%d MENTION_ONLY=%d)"
          % (len(recs), OUT, n_call, n_call - n_cp, n_cp, n_wrap, n_ment))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
