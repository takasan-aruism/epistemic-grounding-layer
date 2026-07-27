#!/usr/bin/env bash
# MGR は git add -A / git add . を使わない。パスを明示させる。
# 理由: 2026-07-28 に3回、何を commit したか把握しないまま commit した
#       (dw/dispatch.py のコード変更を「実行記録の更新」で / IMPL の作業中ファイルを BUILT 前に /
#        オラクルを入れたことに気付かずに)。規律として書いて2回破ったので、機械で止める。
set -uo pipefail
IN="$(cat)"
[ "$(printf '%s' "$IN" | jq -r '.tool_name // ""')" = "Bash" ] || exit 0
C="$(printf '%s' "$IN" | jq -r '.tool_input.command // ""')"
printf '%s' "$C" | grep -Eq 'git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?add[[:space:]]+(-A|--all|\.)([[:space:]]|$)' || exit 0
jq -nc --arg r '2DER 規律(運用方針 §8-4): git add -A / git add . は使いません。★add するパスを明示してください。理由: 2026-07-28 に3回、何を commit したか把握しないまま commit しました(IMPL の作業中ファイル / 他者の成果物)。規律として書いて2回破ったので、機械で止めています。' \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
