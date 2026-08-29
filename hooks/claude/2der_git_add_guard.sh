#!/usr/bin/env bash
# MGR は「まとめて add」を使わない。パスを明示させる。
# 理由: 2026-07-28 に3回、何を commit したか把握しないまま commit した
#       (コード変更を「記録の更新」で / IMPL の作業中ファイルを BUILT 前に / 他者の成果物を無自覚に)。
#       規律として書いて2回破ったので、機械で止める。
# ★引用符と heredoc の中は見ない。初版は自分の commit message 中の文字列に反応し、
#   さらに「自分を直すコマンド」まで止めた(本日4回目の自己一致・G-23 と同型)。
set -uo pipefail
IN="$(cat)"
exec python3 - "$IN" <<'PY'
import json, re, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
if d.get("tool_name") != "Bash":
    sys.exit(0)
c = (d.get("tool_input") or {}).get("command") or ""
# 引用符・heredoc の中(commit message や、フック自身を書き直す本文)を取り除いてから判定する
c = re.sub(r"<<-?'?\"?(\w+)'?\"?.*?^\1", " ", c, flags=re.S | re.M)
c = re.sub(r"'[^']*'", " ", c)
c = re.sub(r'"[^"]*"', " ", c)
def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}, ensure_ascii=False))
    sys.exit(0)

if re.search(r"(^|[|;&\n])\s*git\s+(-C\s+\S+\s+)?add\s+(-A|--all|\.)(\s|$)", c):
    deny(
        "2DER 規律(運用方針 §8-4): まとめて add せず、★add するパスを明示してください。"
        "理由: 2026-07-28 に3回、何を commit したか把握しないまま commit しました"
        "(IMPL の作業中ファイル / 他者の成果物)。規律として書いて2回破ったので、機械で止めています。"
    )
# ★2026-08-09 追加: パスを「明示」したつもりで $(git status --porcelain | awk …) を渡し、
#   ★中身を見ないまま IMPL の source を2回 commit した(CHG-0129 と CHG-0142 の after_commit が空になった)。
#   ∴ ★add の引数に コマンド置換 を使うのを止める。読んでから 名前で書く。
if re.search(r"(^|[|;&\n])\s*git\s+(-C\s+\S+\s+)?add\b[^|;&\n]*\$\(", c):
    deny(
        "2DER 規律: ★add の引数に コマンド置換($(...))を使わないでください。"
        "理由: 2026-08-09 に、パスを明示したつもりで status の出力をそのまま渡し、"
        "★IMPL が置いた source(intent_strategy.py)を自分の『走行の記録』に紛れ込ませ、"
        "★2DER 側の commit を2回 奪いました(CHG-0129/CHG-0142 の after_commit が空)。"
        "★先に status を表示して読み、★ファイル名を1つずつ書いてください。"
    )
# ★MGR が add してよいのは 記録(*.jsonl)と 文書(docs/*.md)だけ。source は 2DER が commit する。
m = re.search(r"(^|[|;&\n])\s*git\s+(-C\s+\S+\s+)?add[ \t]+(?P<args>[^|;&\n]+)", c)
if m:
    bad = [a for a in m.group("args").split()
           if not a.startswith("-") and not a.endswith(".jsonl")
           and not (a.endswith(".md") and "docs/" in a)]
    # ★2026-08-14 Taka 裁定で 置き換え(逐語):
    #   「台帳は自動で良い、コードは人で。ただ、2DER がコードを書く場合は別。
    #     あくまで例外的に Claude が実装をする場合は、それがそうとわかりやすくするために
    #     分けて Commit するように」
    # ∴ MGR が source を入れるのは「例外的に Claude が実装した」場合 → ★混ぜない・★名乗る。
    good = [a for a in m.group("args").split()
            if not a.startswith("-") and (a.endswith(".jsonl")
                                          or (a.endswith(".md") and "docs/" in a))]
    if bad and good:
        deny(
            "2DER 規律(★Taka 裁定 2026-08-14): ★記録/文書 と source を ★同じ add に混ぜないでください。"
            "★逐語『例外的に Claude が実装をする場合は、それがそうとわかりやすくするために分けて Commit する』。"
            "★混ざった物: source=" + " ".join(bad[:3]) + " ／ 記録=" + " ".join(good[:3]) + " ／ "
            "★2回に分けて add・commit してください。"
        )
    if bad and "CLAUDE_IMPL" not in c:
        deny(
            "2DER 規律(★Taka 裁定 2026-08-14): ★source を入れてよいのは"
            "『★例外的に Claude が実装した』場合だけです(★2DER が書いた物は 2DER 側の口)。"
            "★止めた物: " + " ".join(bad[:5]) + " ／ "
            "★名乗ってください: コマンドの先頭に ★CLAUDE_IMPL=1 を置き、"
            "★commit message の先頭を ★[Claude実装] にしてください"
            "(★message の 印は 機械で見ていない＝★人の規律。★見る形にするのが次の宿題)。"
        )
PY
