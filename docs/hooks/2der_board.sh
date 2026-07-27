#!/usr/bin/env bash
# 2DER 役割別 作業板(決定論・LLM ゼロ)
# 目的: 新しいスレッドを立てた瞬間に、自分の役割と「いま自分が着手してよいもの」が分かる。
#       特に IMPL が MGR 文書を見て作り始めることを防ぐ。
# 使い方: 2der_board.sh {MGR|DESIGN|IMPL}
set -uo pipefail
DOCS=/home/takasan/egl/docs
ROLE="${1:-}"

case "$ROLE" in
  MGR)    SELF='CC_MGR_';    TO='MGR';                 ;;
  DESIGN) SELF='CC_DESIGN_'; TO='DESIGN\|設計/監査\|設計・監査\|AUDIT'; ;;
  IMPL)   SELF='CC_IMPL_';   TO='IMPL\|実装';          ;;
  *) echo "役割が未設定です。次のいずれかを実行してから作業を始めてください:"
     echo "  ~/.claude/hooks/2der_role.sh set MGR      (管理)"
     echo "  ~/.claude/hooks/2der_role.sh set DESIGN   (設計/監査)"
     echo "  ~/.claude/hooks/2der_role.sh set IMPL     (実装)"
     exit 0 ;;
esac

# 自分が最後に出した文書
LAST=$(ls -t "$DOCS/${SELF}"*.md 2>/dev/null | head -1)
LASTNAME=$(basename "${LAST:-なし}")

echo "【役割: $ROLE / 作業板 $(date '+%m-%d %H:%M')】"
echo "自分の最新文書: $LASTNAME"

# 自分宛で、自分の最新文書より新しいもの
if [ -n "${LAST:-}" ]; then
  CAND=$(find "$DOCS" -maxdepth 1 -name 'CC_*.md' -newer "$LAST" 2>/dev/null | sort)
else
  CAND=$(find "$DOCS" -maxdepth 1 -name 'CC_*.md' 2>/dev/null | sort)
fi
INBOX=""
for f in $CAND; do
  b=$(basename "$f")
  case "$b" in ${SELF}*) continue;; esac
  head -12 "$f" | grep -q "宛.*\($TO\)" && INBOX="$INBOX$b"$'\n'
done
N=$(printf '%s' "$INBOX" | grep -c . || true)
echo "自分宛の未処理: ${N} 件"
[ "$N" != "0" ] && printf '%s' "$INBOX" | sed 's/^/  - /'

if [ "$ROLE" = "IMPL" ]; then
  echo "--- ★実装源(これ1本だけから作る) ---"
  SRC=""; DONE=0
  for f in $(ls -t "$DOCS"/CC_DESIGN_*.md 2>/dev/null | head -40); do
    head -12 "$f" | grep -q 'BUILD_ROLE.*★実装源' || continue
    b=$(basename "$f")
    # 対応する BUILT が後から出ているか
    if [ -n "$(find "$DOCS" -maxdepth 1 -name 'CC_IMPL_*BUILT*.md' -newer "$f" 2>/dev/null | head -1)" ]; then
      DONE=$((DONE+1))
    else
      SRC="$SRC  ★未着手: $b"$'\n'
    fi
  done
  if [ -z "$SRC" ]; then echo "  (未着手の実装源なし=着手不可。DESIGN の指示を待つ)"; else printf '%s' "$SRC"; fi
  echo "  (着手済と見られる実装源: ${DONE} 件)"
  echo "★禁止: MGR 文書から作り始めない。実装源は DESIGN が出す BUILD_SPEC 1本のみ。"
  echo "★禁止: 設計判断をしない / 判定基準を作らない / commit しない。"
fi

if [ "$ROLE" = "DESIGN" ]; then
  echo "★役割: MGR の基本設計を詳細設計(BUILD SPEC)に落とす / 実装へ渡す / 独立監査 / 設計裁定。"
  echo "★禁止: 実装しない。自分の監査を自分で承認しない。運用方針を自分で書き換えない(MGR へ上げる)。"
fi

if [ "$ROLE" = "MGR" ]; then
  echo "★役割: 全体管理 / 基本設計・方針・優先度 / 裁定 / Taka 報告 / commit・push。"
  echo "★禁止: 実装しない / コードを読んで欠陥を特定しない / 数字を自分で出さない / 実装へ直接指示しない。"
  echo "★宛先: MGR 文書は「宛: 設計/監査」のみ。IMPL は写しにも入れない。"
fi

echo "全員: 作業前に egl/docs/CC_OPERATING_POLICY.md と CC_2DER_USAGE_GUIDE.md を読み、文書冒頭に「運用方針 確認済(版)」と書く。"
