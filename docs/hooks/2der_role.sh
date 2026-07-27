#!/usr/bin/env bash
# セッションごとの役割を記録する(新スレッドで即座に自分の役割に就くため)
# 使い方: 2der_role.sh set {MGR|DESIGN|IMPL}   /   2der_role.sh get
set -uo pipefail
D=/home/takasan/.claude/hooks/.roles
mkdir -p "$D"
# セッション識別: 親プロセス群から claude のセッションを一意に取れないため、
# 「同一端末=同一役割」とみなし TTY を鍵にする。TTY が無い場合は PPID。
KEY=$(tty 2>/dev/null | sed 's|/|_|g')
[ -z "$KEY" ] || [ "$KEY" = "not_a_tty" ] && KEY="ppid_$PPID"
F="$D/$KEY"
case "${1:-get}" in
  set)
    R="${2:-}"
    case "$R" in MGR|DESIGN|IMPL) ;; *) echo "役割は MGR / DESIGN / IMPL のいずれか"; exit 1;; esac
    printf '%s\n' "$R" > "$F"
    echo "役割を $R に設定しました($F)"
    /home/takasan/.claude/hooks/2der_board.sh "$R"
    ;;
  get)
    if [ -f "$F" ]; then cat "$F"; else echo ""; fi
    ;;
  clear) rm -f "$F"; echo "役割を解除しました";;
esac
