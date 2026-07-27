#!/usr/bin/env bash
# ★層飛ばしの検出(決定論・コード構造のみ)
# DS → RRI → EGL → DW の順序を飛ばす import が増えていないかを見る。
# 既存分は baseline として固定し、「増えたか」だけを問題にする。
set -uo pipefail
BASE=/home/takasan/.claude/hooks/.layer_baseline
count() { # $1=検査するディレクトリ  $2=禁じたい import の正規表現
  grep -rlE "$2" --include='*.py' "$1" 2>/dev/null | grep -v '/test' | wc -l
}
DS_EGL=$(count /home/takasan/ds '^\s*(from|import)\s+egl')
DS_DW=$(count /home/takasan/ds '^\s*(from|import)\s+dw')
RRI_EGL=$(count /home/takasan/rri '^\s*(from|import)\s+egl')
RRI_DW=$(count /home/takasan/rri '^\s*(from|import)\s+dw')
CUR="ds->egl:$DS_EGL ds->dw:$DS_DW rri->egl:$RRI_EGL rri->dw:$RRI_DW"
if [ ! -f "$BASE" ]; then printf '%s\n' "$CUR" > "$BASE"; fi
OLD=$(cat "$BASE")
if [ "$CUR" = "$OLD" ]; then
  printf '層飛ばし: 増えていない (%s)\n' "$CUR"
else
  printf '★層飛ばしが変化: 現在[%s] / 基準[%s] ← 増えていれば RRI を飛ばしている疑い\n' "$CUR" "$OLD"
fi
