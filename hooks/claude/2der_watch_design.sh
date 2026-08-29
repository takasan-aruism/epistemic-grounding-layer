#!/usr/bin/env bash
# ★2026-08-21: 中身は `2der_watch.sh` に移した(★役割で引ける形にした=★MGR にも 監視が 要る)。
#   ★この file は ★既存の 案内・引き継ぎ文書が この path を 名指ししている ので 残す 呼び出し口。
#   ★DESIGN の 状態file は 従来と 同じ `.2der_watch_design_state` を 使う(★積み上げた 値を 捨てない)。
exec env ROLE=DESIGN /home/takasan/.claude/hooks/2der_watch.sh "$@"
