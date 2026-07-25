#!/usr/bin/env python3
"""regen_meta — structure/ script 集合を列挙/走査する **meta 派生台帳** を一括 regen(冪等・軽量・HF/GPU非依存)。

根因: 新しい structure/ script を足すたび、script 集合を走査する meta 派生(LLM_INVOCATIONS / TASK_CONTRACTS)が
stale 化し --check が RED→手動 fold(5回目)。commit 境界を跨いで gate RED が残るのを構造的に断つための単一エントリ。

- **META は AST/source 走査のみ**(埋め込み系 stage=e5/HF/GPU は絶対に含めない。重い・offline lock 問題を hook に持ち込まない)。
- 決定論ゆえ no-op なら差分ゼロ(何度でも安全=冪等)。META が増えたら1行追記(un-accounted 化しない)。
- ゲートは緩めない(fold を自動化するだけ。MENTION_ONLY 検出等の gate は正しい)。

usage:
  regen_meta.py          # meta 台帳を regen(pre-commit hook が git add で再ステージ)
  regen_meta.py --check  # 全 meta 台帳の --check を集約。RED なら未 fold の meta を具体名で出し非ゼロ終了
"""
import os
import subprocess
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
# meta 派生台帳の生成器(structure/ script 集合に依存・AST/source 走査のみ・HF/GPU 非依存)。
META = ["s_llm_invocations", "s_task_contract"]


def _run(mod, check):
    args = [sys.executable, os.path.join(STRUCT, mod + ".py")] + (["--check"] if check else [])
    r = subprocess.run(args, cwd=STRUCT, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    tail = out.splitlines()[-1] if out else ""
    return r.returncode, tail


def main(argv):
    check = "--check" in argv
    red = []
    for mod in META:
        rc, tail = _run(mod, check)
        print("%-18s %s%s" % (mod, "[--check] " if check else "[regen]  ", tail))
        if rc != 0:
            red.append(mod)
    if red:
        # ゲートは緩めず、どの meta 生成器が未 fold かを具体名で(bare REGEN_MISMATCH より原因が一目)
        print("REGEN_META %s: RED — 未 fold の meta: %s  → `python3 structure/regen_meta.py` で fold"
              % ("--check" if check else "regen", ", ".join(red)))
        return 1
    print("REGEN_META %s: GREEN (meta 台帳 byte一致: %s)" % ("--check" if check else "regen", ", ".join(META)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
