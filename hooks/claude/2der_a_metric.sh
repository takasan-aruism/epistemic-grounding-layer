#!/usr/bin/env bash
# 2DER「A の数字」— B に潜って全体を忘れるのを、規律ではなく機械で止める。
#
# 背景（2026-07-31・Taka 指示）:
#   A→B→C→D の開発が B→B'→B''→B''' になり全体を忘れる、が延々と解消しない。
#   B には機械が在る（台帳/ゲート/フック/状況表）。★A には機械が無かった。
#   ∴ A へ引き戻す役を、毎回 Taka が人力でやっていた。★それを機械へ移す。
#
# 指標（Taka が 2026-07-31 に定義した逐語）:
#   ★A  = 2DER だけで完了した工程数
#   ★副 = Claude が介入しなければ止まる工程数
#
# ★新しい台帳ではない。★状況表が既に持っているキャッシュと同じ扱いの状態ファイル1つ。
# ★移管予定: 値の保持は最終的に 2DER 側（`/api/control` の roadmap 面）へ移す。
#            移せた時点で本スクリプトは消える。【未確認: /api/control の中身は設計が確認する】
#
# 使い方:
#   2der_a_metric.sh              … 1〜2行を出力（状況表から呼ばれる）
#   2der_a_metric.sh set <A> <副> "<何が動いたか>"  … ★工程が実際に進んだ時だけ更新する
set -uo pipefail
F=/home/takasan/.claude/hooks/.2der_a_metric
THRESHOLD_MIN=120   # ★これを超えて動かなければ名指しする

if [ "${1:-show}" = "set" ]; then
  A="${2:?A の値（2DER だけで完了した工程数）}"
  SUB="${3:?副の値（Claude が介入しないと止まる工程数）}"
  WHAT="${4:-}"
  printf '%s\t%s\t%s\t%s\n' "$(date +%s)" "$A" "$SUB" "$WHAT" >> "$F"
  echo "A=$A 副=$SUB を記録した（$WHAT）"
  exit 0
fi

[ -f "$F" ] || { echo "★A: 未設定（★2der_a_metric.sh set <A> <副> \"<何が動いたか>\" で初期化する）"; exit 0; }

LAST=$(tail -1 "$F")
TS=$(printf '%s' "$LAST" | cut -f1)
A=$(printf '%s' "$LAST" | cut -f2)
SUB=$(printf '%s' "$LAST" | cut -f3)
WHAT=$(printf '%s' "$LAST" | cut -f4)
NOW=$(date +%s)
MIN=$(( (NOW - TS) / 60 ))
if [ "$MIN" -ge 60 ]; then ELAPSED="$((MIN/60))時間$((MIN%60))分"; else ELAPSED="${MIN}分"; fi

printf '★A【自己申告・補助表示・非証拠／2026-07-31 廃止決定・C-1 で機械算出へ置換】: 2DERだけで完了した工程 = %s段 ／ Claude が要る工程 = %s段（最終更新 %s前%s）\n' \
  "$A" "$SUB" "$ELAPSED" "${WHAT:+ / $WHAT}"
printf '  ※この値は人が set したものである。v0.3 §13.3 により主体・進捗の判定根拠に使わない（開発者規律 §12）\n'

# ★閾値を超えたら、Taka がやっていた「なにやってんの」を機械が言う。
if [ "$MIN" -ge "$THRESHOLD_MIN" ]; then
  printf '  ★★A が %s 動いていない。→ ★いまの作業は A のどの数字を動かすか？ ★1行で書けないなら降りない\n' "$ELAPSED"
fi
