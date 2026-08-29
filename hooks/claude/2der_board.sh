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
  # ★宛の「欄」だけを見る(2026-08-12 修正)。旧 `宛.*ROLE` は同じ行の ★`発: MGR` にも当たり、
  #   全1119本のうち MGR 994 / DESIGN 973 / IMPL 584 を「自分宛」と数えていた(実測)。
  #   ∴ 宛 から 次の欄(／ ・ 写 ・ 発)までを切って判定する → MGR 315 / DESIGN 542 / IMPL 262。
  #   書式は3種ある: `宛: X ／` ／ `- **宛: 設計/監査(CC-α)** ／` ／ `… / **宛: 設計/監査** / 写:`
  #   ∴ ASCII の / では切らない(「設計/監査」を割ってしまう)。
  head -12 "$f" | grep -m1 '宛' | sed 's/.*宛/宛/' | sed 's/／.*//' | sed 's/写.*//' | sed 's/発.*//' \
    | grep -q "$TO" && INBOX="$INBOX$b"$'\n'
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
  # ★2026-08-17: 監視はセッションが変わると死ぬ。「覚えておく」でなく機械が毎回 名指しする。
  echo "★監視の張り直し(スレッドを立てたら最初に1回): Monitor で 'ROLE=DESIGN /home/takasan/.claude/hooks/2der_watch.sh' を常駐(persistent)。"
  echo "  ※ 旧 2der_watch_design.sh はそのまま使える(同じ物を呼ぶ薄い口)。"
  echo "  出す行=★手番(next=DESIGN/AUDIT/★ESDE_AUDIT) / ★新着(自分宛) / ★入口停止(front door 2回連続) / ★居座り(3時間) / ★この監視自身が落ちた。それ以外は黙る。"
  echo "  ★2026-08-21 修正: 以前は next=ESDE_AUDIT を手番と認識できず鳴らなかった。"
  # ★★2026-08-22 Taka 指示『直して』。★自己監査の実測=私が出した台帳 note 25本のうち
  #   SYMMETRY 1 / CREATION 1 / R3 1 / HIERARCHY 2 / R2 3 / SCOPE 3 / LINKAGE 4 /
  #   EQUALITY 5 / UNDERSTANDING 5 / DECISION 5 ＝ ★全欄で返したのは 0 本。
  #   ★正本§12『報告は この形で出す』を ★監査自身が守っていなかった。
  #   ★MGR には板で機械に名指しさせておいて ★自分は口頭の決意だけだった=同じ型。
  #   ★直し=★新機構0。★板に4件足す(記憶に頼らない)。
  echo "★★監査が返す前に4つ(★Taka 指示 2026-08-22『直して』／★正本§0=形式を満たさねば先へ進めない):"
  echo "  ①★§12 の全欄で返す= AXIS/SCOPE/EQUALITY(★identity rule 必須)/SYMMETRY/LINKAGE/"
  echo "     HIERARCHY/R1/R2/R3/R4/UNDERSTANDING(★昇格先)/CREATION/DECISION。"
  echo "     ★欄が埋まらない時は ★空欄にせず UNVERIFIED と書く(★省略は禁止)。"
  echo "  ②★§10⑨ R4= ★拒否条件を全列挙し ★各拒否を実際に発火させる。"
  echo "     ★発火数/全条件数 を必ず書く(★実績 最大 5/15=一度も完遂していない)。"
  echo "  ③★§10③ 因果鎖を ★自分でも端から端まで書く(★MGR の検算だけで済ませない)。"
  echo "  ④★§11『局所関数だけを見て全体経路が成立したと結論する』"
  echo "     ★実際に破った(2026-08-22 00:37 _gate_put だけ見て webui.py:1494 の共有ゲートを見落とした)。"
  echo "     ★呼び手・門・共有分岐を ★全件 grep してから機構を結論する。"
fi

if [ "$ROLE" = "MGR" ]; then
  echo "★役割: 全体管理 / 基本設計・方針・優先度 / 裁定 / Taka 報告 / commit・push。"
  echo "★禁止: 実装しない / コードを読んで欠陥を特定しない / 数字を自分で出さない / 実装へ直接指示しない。"
  echo "★宛先: MGR 文書は「宛: 設計/監査」のみ。IMPL は写しにも入れない。"
  # ★2026-08-21: ★MGR には 監視が 無かった=★監査が next=MGR を 返しても 誰も 起こさない
  #   (★実測 08-21: 監査 05:09:31 → 私が気づいたのは 05:33 の Taka の問い=★24分 の空白)。
  echo "★監視の張り直し(スレッドを立てたら最初に1回): Monitor で 'ROLE=MGR /home/takasan/.claude/hooks/2der_watch.sh' を常駐(persistent)。"
  echo "  出す行=★手番(next=MGR) / ★新着(自分宛) / ★入口停止(front door 2回連続) / ★居座り(3時間) / ★順番が来ない / ★この監視自身が落ちた。それ以外は黙る。"
  # ★★2026-08-21 Taka 裁定『ルーチンが間違っている。直せ』。
  #   ★実測=EVO-0085 で 5周 PLAN を頼み、5周目に build_planner.py:319 の
  #     validate_plan(target_workspace は PROD_REPO_ROOTS 配下 不可)を見つけた。
  #     ★1周目に その2行を読んでいれば DESIGN_HOLD に出来た=★5周は 進捗0。
  #   ★原因の構造=★正本 §10 の順 ②全件調査→③因果鎖→④DESIGN_HOLD→⑤declared に対し
  #     実際は ①決める→declared→頼む で ★②が declared の後ろに回っていた。
  #   ★直し=★新機構0。★declared に 1欄 足す(下)。
  echo "★★依頼を出す前に1つ(★Taka 裁定 2026-08-21『ルーチンが間違っている。直せ』):"
  echo "  ★declared に『依頼先の制約を作用ベースで全件調査した結果』の欄を書いてから頼む。"
  echo "  ★依頼先= planner / worker / 門(validator)。★『その形の成果物を そもそも作れるか』を先に見る。"
  echo "  ★最低限見る物: build_planner.validate_plan(受入と拒否) / PROD_REPO_ROOTS(書ける場所) /"
  echo "                 domain_dw._place_and_commit(置く先の決まり方) / submit の前提検査。"
  echo "  ★これを書かずに頼んだ周は ★進捗0 として記帳する(★『PLAN が少し良くなった』は数えない)。"
  # ★★2026-08-22: ★本日 私が最も多く踏んだ型(★自分で6回 数えた)。
  #   実例= 『停止条件で自動停止』/『1 tick=PLAN 1件』/『副作用0で測れる』/『門の拒否語は3つ』/
  #         『REARM=0』/『claude -p を事後に数える手が無い』★全部 後から訂正した。
  #   ★Taka 逐語『嘘つきと仕事するのは疲れる』= ★毎回 最初の報告が信用できない、という意味。
  #   ★直し=★新機構0。★断定の形を1つ決める。
  echo "★★断定する前に1つ(★2026-08-22 / 本日 6回 踏んだ型):"
  echo "  ★『在る』『無い』『0件』『通った』と書く前に ★探した範囲と分母を同じ行に書く。"
  echo "  ★例: 『無い(探した範囲= ds rri egl dev-workcell twoder の *.py 全件)』"
  echo "  ★分母が出せない時は ★UNVERIFIED と書く。★『無い』と書かない。"
  echo "  ★1回の観測で断定しない。★訂正は 後からでなく ★書く前に潰す。"
fi

echo "全員: 作業前に egl/docs/2DER_DEVELOPER_DISCIPLINE_v1.0.md と TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3.md を読み、文書冒頭に「開発者規律 確認済(版)」と書く。★旧 CC_OPERATING_POLICY.md / CC_2DER_USAGE_GUIDE.md は廃止・置換済(対応表=規律 §12)。"
