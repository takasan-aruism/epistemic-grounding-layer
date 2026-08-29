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
    # ★★[Claude実装] 2026-08-28(★MGR 裁定 EVO-0105 ／ ★計器の維持)=
    #   ★役の語を ★写しで 持たない= ★正本 `manager_v0.RESPONSIBLE_ROLES` から その場で 引く
    #     (★`/api/register_rules` と 同じ 作法)。★写しを 置くと ★役が 増えた 時に ずれる。
    #   ★直す前= `MGR|DESIGN|IMPL` の 3語を ★このファイルが 直に 持っていた=
    #     ★★Route/Topology も Ledger も ESDE も ★名乗れなかった(★2026-08-27 Topology の 報告)。
    #   ★実測(2026-08-28)= 既存の 役ファイル 13件は ★全て 07-28〜08-21 の MGR/DESIGN/IMPL=
    #     ★★いまの 8担当は ★1つも 使っていない ∴ ★旧3語を 残さない(★中間を 作らない)。
    ROLES="$(cd /home/takasan && python3 -c "import sys;sys.path.insert(0,'/home/takasan');from twoder import manager_v0 as M;print(' '.join(M.RESPONSIBLE_ROLES))" 2>/dev/null)"
    if [ -z "$ROLES" ]; then
      echo "★役の正本(manager_v0.RESPONSIBLE_ROLES)が引けません。★推測で通しません。" >&2; exit 1
    fi
    _ok=0; for _r in $ROLES; do [ "$R" = "$_r" ] && _ok=1; done
    if [ "$_ok" != 1 ]; then
      echo "役は次のいずれか(★正本から引いた値): $ROLES" >&2
      echo "★旧語 MGR は GENERAL_MGR に、DESIGN と IMPL は ★役ではなく手番語(next=)です。" >&2
      exit 1
    fi
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
