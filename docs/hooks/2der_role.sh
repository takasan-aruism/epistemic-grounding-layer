#!/usr/bin/env bash
# セッションごとの役割を記録する(新スレッドで即座に自分の役割に就くため)
# 使い方: 2der_role.sh set {MGR|DESIGN|IMPL} / get / key(自己診断) / clear
#
# ★2026-07-28 修理: 旧版は TTY を鍵にしていたが、Claude Code の Bash は TTY を持たないため
#   `tty` が失敗し、★日本語 locale のエラー文「tty ではありません」がそのまま鍵になっていた。
#   ∴ 鍵が全インスタンスで同一になり、役割ファイルは1個しかできず、
#     最後に set した者の役割が★3インスタンス全員に配られていた(設計/監査に「役割: MGR」と表示)。
#   フォールバック `[ "$KEY" = "not_a_tty" ]` も、英語 locale の実出力が `not a tty`(空白)なので
#   最初から一度も効いていなかった。
#   → セッション固有の CLAUDE_CODE_SESSION_ID を鍵にする。無ければ CLAUDE_PID、最後に PPID。
#   → 鍵は必ず英数字・ハイフン・アンダースコアだけに正規化する(locale やエラー文に依存させない)。
set -uo pipefail
D=/home/takasan/.claude/hooks/.roles
mkdir -p "$D"

_sanitize() { printf '%s' "$1" | tr -c 'A-Za-z0-9_-' '_' | cut -c1-64; }

if [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
  KEY="sid_$(_sanitize "$CLAUDE_CODE_SESSION_ID")"
elif [ -n "${CLAUDE_PID:-}" ]; then
  KEY="cpid_$(_sanitize "$CLAUDE_PID")"
else
  KEY="ppid_$(_sanitize "$PPID")"
fi
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
  key)   # ★自己診断: いま何を鍵にしているかを見せる(鍵が潰れていないか確認できる)
    printf '%s\n' "$KEY"
    ;;
  clear) rm -f "$F"; echo "役割を解除しました";;
esac
