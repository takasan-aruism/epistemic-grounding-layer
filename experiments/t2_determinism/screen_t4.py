#!/usr/bin/env python3
"""★T4 21件の 依頼文を ★2つの型で 選別する(★ITEM-2DER-EVO-0020)。

★★型は 今日 見つけた 2つ=
  ★LLMK-0013 依頼文が 自分と 矛盾する= ★事実を 渡しておいて『与えていない』と 禁じる
  ★LLMK-0014 値が 閉じている 欄が 在るのに ★schema で 縛っていない

★★全部を 手で 読まない= ★機械に 当たりを 出させ ★当たりだけ 読む
  (★21本 × 数百行= 手読みは 私の 得意でない ／ ★見落としが 静かに 入る)。
★★選別は 決定論= ★文字列の 有無だけ。★判定は しない= ★『疑い』を 出すだけ。
"""
import ast, os, re, sys

FILES = [
 "dev-workcell/dw/adapters.py", "ds/ds/phase1.py",
 "egl/autonomy/ingest.py", "egl/autonomy/investigate.py",
 "egl/egl/judge_vllm.py", "egl/egl/self_grounding.py",
 "egl/experiments/run_gpu_conflict.py", "egl/experiments/run_odf_narrow.py",
 "egl/experiments/run_sleep_wake_measure.py",
 "egl/structure/s_account_axis_names.py", "egl/structure/s_intent_dialogue_probe.py",
 "egl/structure/s_intent_probe_armc.py", "egl/structure/s_intent_probe_armc2.py",
 "egl/structure/s_intent_probe_armc3.py", "egl/structure/s_intent_probe_proto.py",
 "egl/structure/s_intent_role_split.py", "egl/structure/s_ledger_account_axis_names.py",
 "rri/rri/intent_strategy.py", "rri/rri/request_type.py", "rri/rri/research_intent.py",
 "twoder/domain_inference_control.py",
]
ROOT = "/home/takasan/"

# ★A= 禁止の 言い回し(★『君は それを 知らされていない』系)
DENY = re.compile(r"(NEVER|Never |not been given|do not have|cannot decide|you have not|"
                  r"判断しないで|判断するな|してはいけない|しないでください|禁止|推測しないで)")
# ★A の 相棒= 事実を 渡している 印
FACTS = re.compile(r"(FACTS|facts|事実|与えられた|以下の情報|渡された|imported_by|"
                   r"AST|材料|入力|データ)")
# ★B= 値が 閉じている 印(★選択肢を 言葉で 並べている)
ENUM = re.compile(r"(次のいずれか|いずれか1つ|どれか1つ|one of|choose one|"
                  r"のみを (返|出力)|だけを (返|出力)|[A-Z_]{3,}\s*/\s*[A-Z_]{3,}\s*/\s*[A-Z_]{3,})")


def literals(path):
    """★AST で 文字列を 取る(★import しない= ★副作用を 起こさない)。"""
    try:
        t = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except Exception as e:
        return []
    out = []
    for n in ast.walk(t):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) >= 60:
            out.append(n.value)
    return out


def main():
    hitA, hitB, none = [], [], []
    print("★T4 21件の 依頼文を 選別(★決定論・文字列の有無だけ ／ ★判定でなく 疑い)")
    print("%-52s %7s %5s %5s" % ("ファイル", "文字列", "★矛盾", "★閉じ"))
    for rel in FILES:
        p = ROOT + rel
        ls = literals(p)
        blob = "\n".join(ls)
        a = bool(DENY.search(blob)) and bool(FACTS.search(blob))
        b = bool(ENUM.search(blob))
        print("%-52s %7d %5s %5s" % (rel[:52], len(ls), "★" if a else ".", "★" if b else "."))
        (hitA if a else none).append(rel)
        if b:
            hitB.append(rel)
    print()
    print("★矛盾の疑い= %d/%d 件 %s" % (len(hitA), len(FILES), hitA))
    print("★閉じられる疑い= %d/%d 件" % (len(hitB), len(FILES)))
    print()
    print("★★この選別は ★当たりを出すだけ= ★1件ずつ 実物を 読んでからでないと 認定しない")
    print("★★偽陰性が 在りうる= ★依頼文が 外部ファイル/変数で 組まれていると 文字列に 出ない")


if __name__ == "__main__":
    main()
