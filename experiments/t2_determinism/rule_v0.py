#!/usr/bin/env python3
"""★T2『決定論に寄せられるか』を 実測する(★ITEM-2DER-EVO-0020 の 積み残し)。

★★対象= `egl/structure/s2_extract.py:call`(★T2 5件のうち ★唯一 Qwen が 推論する 1件)。
★★測る欄= `lifecycle_signal` ★1欄だけ。
  ★理由= ★schema は 形は 閉じているが ★値が 閉じているのは この欄だけ(★5値の 列挙)。
    残り10欄は ★自由記述 ∴ ★決定論に 寄せる 対象に ならない。
  ★★これが T2 の 正しい 読み方= ★『schema 在り』は ★出力が 閉じている 印では ない。

★★事実は ★自分で ソースから 作る= ★SYMBOL_INDEX/FILE_MANIFEST は ★門が 止める(★迂回しない)。
"""
import ast, json, os, re
from collections import Counter, defaultdict

REPOS = ["/home/takasan/twoder", "/home/takasan/egl", "/home/takasan/rri",
         "/home/takasan/ds", "/home/takasan/dev-workcell"]
SIGNALS = ["ACTIVE", "SCAFFOLD", "EXPERIMENT", "DEPRECATED", "UNKNOWN"]
DEP = re.compile(r"DEPRECATED|廃止|deprecated|OBSOLETE|使わない|置換済")
EXP = re.compile(r"(^|/)(experiments?|gpu_experiment|sandbox|scratch)(/|$)")


def _mods():
    """★どの module 名が どの ファイルか(★import を 突き合わせる ため)。"""
    out = {}
    for repo in REPOS:
        for root, _d, fs in os.walk(repo):
            if "/.git" in root:
                continue
            for f in fs:
                if f.endswith(".py"):
                    p = os.path.join(root, f)
                    out.setdefault(f[:-3], []).append(p)
    return out


def importers(paths):
    """★誰が どのファイルを import しているか= ★呼び手の 数(★決定論・AST)。"""
    mods = _mods()
    cnt = Counter()
    for p in paths:
        try:
            tree = ast.parse(open(p, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    names.add(a.name.split(".")[-1])
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    names.add(n.module.split(".")[-1])
                for a in n.names:
                    names.add(a.name)
        for nm in names:
            for tgt in mods.get(nm, []):
                if tgt != p:
                    cnt[tgt] += 1
    return cnt


def classify(path, src, imported_by):
    """★規則(★5行)。-> (値, 理由)

    ★順番が 効く= ★上から 当てて 最初に 当たった もの。
    """
    if DEP.search(src[:4000]):
        return "DEPRECATED", "先頭4000字に 廃止の語が 在る"
    if EXP.search(path) or os.path.basename(path).startswith("test_"):
        return "EXPERIMENT", "道すじが 実験/試験"
    if imported_by > 0:
        return "ACTIVE", "他の .py から import されている(%d本)" % imported_by
    if "if __name__" in src:
        return "SCAFFOLD", "呼び手0だが 単体で 起動できる"
    return "UNKNOWN", "呼び手0・単体起動も 無い"
