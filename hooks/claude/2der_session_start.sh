#!/usr/bin/env bash
# 毎セッション、2DER 使用ガイドの要点を機械的に注入する(「読むのを忘れる」を無くす)
set -uo pipefail
G=/home/takasan/egl/docs/2DER_DEVELOPER_DISCIPLINE_v1.0.md
P=/home/takasan/egl/docs/TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3.md
[ -f "$G" ] || exit 0
CTX=$(cat <<'EOF'
【2DER 現場の開発者規律 v1.0 — 機械注入・作業前に必ず効く】
★運転規則は2本だけ: 現場=2DER_DEVELOPER_DISCIPLINE_v1.0.md / 運用=TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3.md。3本目を作らない。
★旧 CC_OPERATING_POLICY.md と CC_2DER_USAGE_GUIDE.md は 2026-07-31 に廃止・置換済(対応表=規律 §12)。掘り返さない。
0-A. ★★最上位の原則(Taka 2026-08-07・逐語)=『Claude code にはプロジェクトを正しく進行する能力はない。2DER を使っても無理なのだから
   より構造的に無理な理由(コンテキストの記憶が邪魔をする)がある。従って★あなた方を減らしていくという方向性が原則であり真理である。ここがブレることはない』。
   ★★∴ 提案は必ず『2DER 側で完結する形』から出す。3Claude が担う案を先に出さない。出したら、それ自体が この原則からの逸脱である。
   ★★★実績(2026-08-07)=上級監査を Claude Code にする案を ★Taka が3回 出して やっと通った。★★同じ案を2回 言わせたら、その時点で私の失敗として登録する。
0. ★Taka 常設命令(全役割 絶対遵守): 全案件を台帳経由 / ★新規の台帳を作らない / ★台帳に直接手を出さない / DS-RRI 経由で。畳めないものを使い続けるときは、畳む条件と、いま何が足りないかを必ず併記する。
1. あなたは 2DER の外にいる市民である。2DER 内部に入らない。production コードを自分で書かない(実装は worker、Claude は検査して配置するだけ)。
2. 台帳(*.jsonl の運用データ)を直接読まない・書かない。PreToolUse フックが拒否する。読み出しは GET /api/resolve?id= が動く。
3. 知りたいことは 2DER に聞く。答えられなければ「答えられなかった」が結果であり、それが次に作る機能である。
4. ★入口は一つ。投入は webui 経路(/api/submit・/command)。CLI(`python3 -m twoder.submit`)は task を作れるが進められず、
   ★実行記録(TRACE)を1件も残さない(G-36)=BYPASS。使うなら「記録が残らない」と書いてから使う。
5. ★worker の隔離は「書けない」ではなく「書かない」(G-90)。効いているのは呼び手の tempfile / planner の拒否 / commit 禁止の3つ。
   「安全だから押してよい」と読まない。成果物は tempfile 配下で消えるので、受け取りは同じ作業の中で完了させる。
6. 「ソースに在る」を「動く」と書かない。動作の主張には実行した再現コマンドと結果を併記する。
7. 既存を読んでから作る。1回の観測で状態を断定しない。
8. ★進捗は台帳へ書く。.md は「台帳へ書く口が無くて書けなかった」時だけ。その .md には「どの口が無いのか」を1行書く。
   ★★その .md の 置き場は 1枚に 決まった(2026-08-26 Taka)= /home/takasan/egl/docs/CC_LEDGER_UI_GAPS.md に 追記する。
   ★規則では なく 収集シート(3本目の規則では ない ／ ★台帳には 載せない= ARTIFACT 登記しない)。
   ★★全担当が 書く。書くのは 3つ= ①UI に不足している機能 ②UI で問題が起きている箇所 ③自分の担当で直さないといけないこと。
   ★形は そのファイルの 雛形どおり(担当 / 何をしたか / 何が足りないか1行 / 実測の日付)。★直し方は 書かなくてよい。
   ★★数字が在れば 必ず 入れる(件数と分母)= 優先順位は そこで 決まる。★推測で 書かない= 実際に やって できなかった ことだけ。
   ★迂回したこと自体は 責めない= 隠すほうが 困る。★★UI が 直った段階で MGR が ここの 全部を 台帳へ 登録する
   ∴ ★書いて いない ものは 台帳に 載らない。★以後 ページからしか 登録・変更 できなく する(権限で縛る)。
   ★★書く場所= ★そのファイルの 末尾に 在る ★自分の担当の 見出しの 下(★同時に書いて 消し合わない ため)。
   ★他の担当の 欄に 書かない。★どこにも 当てはまらなければ「その他」の下に 名乗りを1行 書いてから 書く。
   ★UI= http://100.107.6.119:8770/control
9. ★一つの閉塞を解消するために、新しい管理対象(文書/計器/役割/インスタンス/承認工程/台帳)を二つ以上増やさない。
   増やすならその場で「既存の何を廃止するか」を同時に書く。書けないなら増やさない。
全文: /home/takasan/egl/docs/2DER_DEVELOPER_DISCIPLINE_v1.0.md
運用規律: /home/takasan/egl/docs/TAKA_2026-07-31_SELF_EVOLUTION_ARCH_v0_3.md (作業前に読み、文書冒頭に「開発者規律 確認済(版)」と書く)
EOF
)
ROLE="$(/home/takasan/.claude/hooks/2der_role.sh get 2>/dev/null || true)"
if [ -n "$ROLE" ]; then
  RB="$(/home/takasan/.claude/hooks/2der_board.sh "$ROLE" 2>/dev/null || true)"
else
  RB="【役割が未設定】作業を始める前に次を実行すること:
  ~/.claude/hooks/2der_role.sh set MGR      (管理)
  ~/.claude/hooks/2der_role.sh set DESIGN   (設計/監査)
  ~/.claude/hooks/2der_role.sh set IMPL     (実装)
★役割を設定するまで、自分宛でない文書に基づいて作業を始めないこと。"
fi
BOARD="$RB

$(/home/takasan/.claude/hooks/2der_status.sh full 2>/dev/null || echo '(状況表の取得に失敗)')"
jq -nc --arg c "$CTX

$BOARD" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
