#!/usr/bin/env bash
# 2DER 状況表(軽量版・決定論・LLM ゼロ)
# 目的: MGR が「記憶で俯瞰する」のをやめ、機械が出す表を毎ターン見る。
# 出力: 1画面のテキスト。呼び出し側(hook)が additionalContext として注入する。
set -uo pipefail
REPOS="ds rri egl dev-workcell twoder"
DOCS=/home/takasan/egl/docs
CACHE=/home/takasan/.claude/hooks/.2der_status_cache
MODE="${1:-brief}"

line() { printf '%s\n' "$1"; }

# --- 1. repo 同期(git は台帳読みでないので直接見てよい) ---
DIRTY=""; AHEAD=""
for r in $REPOS; do
  d="/home/takasan/$r"
  [ -d "$d/.git" ] || continue
  n=$(cd "$d" && git status --porcelain 2>/dev/null | wc -l)
  ab=$(cd "$d" && git rev-list --left-right --count '@{u}...HEAD' 2>/dev/null || echo "? ?")
  a=$(printf '%s' "$ab" | awk '{print $2}')
  [ "$n" != "0" ] && DIRTY="$DIRTY $r:$n"
  [ "${a:-0}" != "0" ] && AHEAD="$AHEAD $r:+$a"
done

# --- 2. MGR 未応答の受信箱(mtime 比較・決定論) ---
LASTMGR=$(ls -t "$DOCS"/CC_MGR_*.md 2>/dev/null | head -1)
if [ -n "${LASTMGR:-}" ]; then
  PENDING=$(find "$DOCS" -maxdepth 1 -name 'CC_DESIGN_*.md' -newer "$LASTMGR" -o -maxdepth 1 -name 'CC_IMPL_*.md' -newer "$LASTMGR" 2>/dev/null | sort)
else
  PENDING=""
fi
PN=$(printf '%s' "$PENDING" | grep -c . || true)

# --- 3. 台帳登記の整合(既存プログラムを呼ぶ。台帳の直読ではない) ---
# 重いので full のときだけ実行し、結果をキャッシュする
if [ "$MODE" = "full" ]; then
  RC=$(cd /home/takasan/egl && timeout 180 python3 structure/s10_ledger_registry.py --check 2>&1 | tail -1)
  printf '%s\n' "$RC" > "$CACHE"
else
  RC=$(cat "$CACHE" 2>/dev/null || echo "(未取得: SessionStart で取得)")
fi

# --- 出力 ---
line "【2DER 状況表 / $(date '+%m-%d %H:%M') / mode=$MODE】"
line "repo 未commit :${DIRTY:- なし}"
line "repo 未push   :${AHEAD:- なし}"
line "MGR 未応答    : ${PN} 件"
if [ "$PN" != "0" ]; then
  printf '%s\n' "$PENDING" | sed 's|.*/|  - |' | head -8
fi
line "台帳登記 check: $RC"

# --- 4. ★動いているプロセスが、いまのソースを持っているか ---
# (2026-07-27: webui が4日前起動のまま=修理が実行中の系に入っていない、を見逃した)
STALE=""
for spec in "twoder.webui:/home/takasan/twoder:/home/takasan/dev-workcell" "twoder.operator:/home/takasan/twoder"; do
  mod="${spec%%:*}"; dirs="${spec#*:}"
  pid=$(pgrep -f "python3 -m $mod" | head -1)
  [ -z "$pid" ] && continue
  pstart=$(stat -c %Y /proc/"$pid" 2>/dev/null || echo 0)
  newest=0
  for d in $(printf '%s' "$dirs" | tr ':' ' '); do
    m=$(find "$d" -name '*.py' -newermt "@$pstart" -print -quit 2>/dev/null)
    [ -n "$m" ] && newest=1
  done
  age=$(( ( $(date +%s) - pstart ) / 3600 ))
  if [ "$newest" = "1" ]; then STALE="$STALE ${mod}(pid $pid, ${age}h前起動: ★ソースが新しい=再起動が要る)"; fi
done
line "実行中プロセス:${STALE:- ソースより新しい起動 or 該当なし}"
# --- 5. ★逃げ道を使おうとした回数(フックが拒否した実数・自己申告でない) ---
CL=/home/takasan/.claude/hooks/.cheat_attempts.log
if [ -f "$CL" ]; then
  TODAY_N=$(grep -c "^$(date '+%Y-%m-%d')" "$CL" 2>/dev/null || echo 0)
  ALL_N=$(wc -l < "$CL" 2>/dev/null || echo 0)
  line "台帳の直読を試みた回数: 本日 ${TODAY_N} / 累計 ${ALL_N}（フックが拒否した実数）"
else
  line "台帳の直読を試みた回数: 0（記録開始以降）"
fi

line "$(/home/takasan/.claude/hooks/2der_layers.sh 2>/dev/null || echo '層飛ばし: 判定不能')"
line "優先度(MGR 固定): 1=段0 途中まで在るものの発見(D-23 EXEC_ARCH/Task Contract) / 2=段1 4軸7カテゴリ・勘定科目の自動設定は繋がっているか / 3=段2 Execution Architecture 本体(EXEC_ARCH_WORK_ORDER_v0_1.md) / 4=台帳を読める仕組み"
line "規律: 記憶で俯瞰しない。既存を読んでから作る。ソースに在る≠動く。1回の観測で断定しない。台帳の直読は【直読】と明記。"
