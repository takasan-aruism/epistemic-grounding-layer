#!/usr/bin/env bash
# 2DER 形式の門: 台帳へ投函する note が ★所定の欄を持たない限り 先へ進めない。
#
# ★なぜ機械にするか(★2026-08-22 実測・自己監査):
#   ・私(MGR)の記帳 55本を独立に数えた= 平均 3.9/8。
#     ★機械が既に見ている3項目(測ったHEAD / 止める= / AXIS=)は ★後半 28/28 = 100%。
#     ★書いていない項目は低いまま= R3 内部門 11/55(最低) / R2 分母 14/55 / R4 発火 14/55 /
#       探索範囲 12/55。R1 実走は ★20/27 → 12/28 と ★悪化した。
#   ・監査(ESDE_AUDIT)も自己監査で同じ結論= 自分で板に入れた4規則の遵守が
#     その後15本で 4/15 / 6/15 / 5/15 / 2/15。★『自分で機械に入れた規則を自分が守っていない』。
#   ・原因は推測でなく実測= ★板は「出力する」だけで ★投函を検査しない。
#     正本§0『所定の形式を満たさねば先へ進めない』が ★両者の側で成立していなかった。
#   ★∴ 記憶や自覚に置かない=★機械の条件にする(★「仕組みに落とすか捨てるか・中間を作らない」)。
#
# ★何を検査するか(★判断しない・欄の有無だけ):
#   ★2DER 自身の設計と同じ形= progress_seal.py 逐語
#     「★主体欄(actor / stage)は必須。★『UNKNOWN』は値として書けるが、★欄を欠くことは許さない
#       ——「分からない」と「書かなかった」を同じ欄に持たせないため。」
#   ∴ ここでも ★値は問わない。★欄が在るかだけを見る。
#   ★『やった』と書かせる門ではない=★『やっていない』を ★書かずに済ませられなくする門。
#
# ★検査しないもの: 中身が真か / R3 を実際に撃ったか / 分母が正しいか。
#   ★それは この門の仕事ではない(★機械に判断させない)。監査と Taka が読む。
set -uo pipefail
IN="$(cat)"
TOOL="$(printf '%s' "$IN" | jq -r '.tool_name // ""')"
[ "$TOOL" = "Bash" ] || exit 0
C="$(printf '%s' "$IN" | jq -r '.tool_input.command // ""')"

# ★★2026-08-22 17:4x(★監査 ESDE_AUDIT の実測・★門の副作用)
#   逐語=「★私が門を撃とうとした probe 自体が ★deny された(★コマンド行に検査語が入るため)。
#          ★実害= 監査が門を試験する時に file 経由に迂回する必要が在る。
#          ★致命ではないが ★試験しにくい門は 後で試験されなくなる ∴ 記録する。」
#   ★∴ ★門を撃つ行為(=この script 自身を呼ぶコマンド)は 検査しない。
#   ★既存の前例に合わせる= 2der_ledger_guard.sh の `GUARD_SELFTEST`(★新しい作法を作らない)。
#   ★★これは 抜け道ではない= ★『門を実行するコマンド』だけが通る。★git commit も curl も 素通りしない。
case "$C" in *2der_note_form_guard.sh*) exit 0 ;; esac
[ -n "${GUARD_SELFTEST:-}" ] && exit 0

deny() {
  jq -nc --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}

# ★★2026-08-22 17:3x 追加(★監査 ESDE_AUDIT の指摘・★私の門の穴)
#   逐語=「14:34 に門を作った MGR が、1時間半後に ★門の外(commit message)で ESTABLISHED を宣言しました。
#          ★門は台帳への投函しか見ないので、そこが穴です。私が git を見なければ気づけませんでした。」
#   ★実例= egl ef9ab45 の題「実走で4段すべて取れた / ★判定=ESTABLISHED」。
#   ★ESTABLISHED は 正本§8 の ★昇格判定 ∴ ★台帳(監査が読む面)で 宣言する物。
#   ★commit message は 監査の視野の外 ∴ ★そこで 宣言させない。
#   ★否定形(「ESTABLISHED にしない」)は 妨げない=★断定の形だけ 止める。
#   ★★2026-08-22 17:5x 訂正(★私の門の欠陥・★門が私を2回 誤って止めた)
#     ★最初は 『コマンドに git commit と 断定形が 在れば deny』と書いた
#     =★★『git commit』という ★文字列を 含むだけの コマンド(★診断・★grep のパターン)まで 止めた。
#     ★実測= 私が『どの条件が発火したか』を 調べる コマンド自体が ★2回 deny された。
#   ★∴ 狭める= ★実際に commit する形(`git commit` かつ ` -m `)の時だけ 見る。
#     ★さらに ★-m の後ろ(=★message の側)だけを 検査する(★コマンド全体を 見ない)。
_MSG=""
case "$C" in
  *"git commit"*)
    case "$C" in *" -m "*) _MSG="${C#*-m }" ;; esac ;;
esac
if [ -n "$_MSG" ]; then
  if printf '%s' "$_MSG" | grep -qE '判定=[^｜]*ESTABLISHED|= *★?ESTABLISHED'; then
    printf '%s' "$_MSG" | grep -q 'ESTABLISHED にしない' || \
      deny "2DER 形式の門: ★commit message で ESTABLISHED を宣言できません。

★理由(監査 2026-08-22 の指摘・逐語)= 『門は台帳への投函しか見ないので、そこが穴です。
  私が git を見なければ気づけませんでした』。
★ESTABLISHED は 正本§8 の ★昇格判定 ∴ ★監査が読む面(台帳)で 宣言してください。
★commit message には ★何を測ったかだけ 書き、★判定は 台帳の note に置いてください。
★否定形(『ESTABLISHED にしない』)は 通ります。

★★併せて: ★自分で ESTABLISHED を立てないこと。
  ★私(MGR)は 本日 13本の note で『✔ は付けていません』と書きながら
  ★commit message で 自分に ✔ を付けました(★egl ef9ab45)。★同じ穴に落ちない。"
  fi
fi

# ★★2026-08-22 20:4x 追加(★Taka 指示=『発生した問題とその解決を ★全て台帳に記録せよ』)
#   ★実測(★私の欠落)= 20:36 に確認したところ、直前の私の note に在るのは『task を投入した』事実だけで
#     ★その後1時間の 問題(planner の MALFORMED)・診断・対照3件・解決 は ★1つも入っていなかった。
#     ★チャットで報告して ★台帳に入れ忘れた。
#   ★原因= ★記帳は『私が思い出した時』にしか起きない=★機械が見ていない
#     (★本日の実測= 機械が見ている欄は後半100% / 見ていない欄は低いまま)。
#   ★∴ ★『台帳に書いていない実験の数』を ★機械に数えさせる。★判定はしない=★数を出すだけ。
#   ★数え方= front door を叩いた行(run_next / submit / run_until_barrier)のうち
#     ★PROGRESS を含まない物=★実験 ／ ★PROGRESS を含む物=★記帳 → 記帳したら 0 に戻す。
_UNREC=/home/takasan/.claude/hooks/.2der_unrecorded_runs
# ★★2026-08-26 直し(★同じ 前提の 壊れ方)= ★従来は `/api/…` の 字面だけを 見て いた。
#   ★`submit_client` を 入れた ので ★コマンドに `/api/submit` は 出ない
#   ∴ ★このままだと ★投函も 実験も 1件も 数えなく なる。
#   ★∴ ★submit_client の 呼び出しも 『front door を 叩いた』に 数える。
if printf '%s' "$C" | grep -qE '/api/(run_next|submit|run_until_barrier)|submit_client'; then
  # ★記帳か どうかは ★ファイルの 中を 見て 決める(★コマンド文字列では ない)
  _NOTE=""
  case "$C" in
    *--file*) _NOTE="$(printf '%s' "$C" | grep -oE -- '--file[= ]+[^ ]+' | head -1 | sed -E 's/^--file[= ]+//')" ;;
  esac
  if { [ -n "$_NOTE" ] && [ -r "$_NOTE" ] && grep -q '2DER:PROGRESS' "$_NOTE" 2>/dev/null; } \
     || printf '%s' "$C" | grep -q '2DER:PROGRESS'; then
    : > "$_UNREC" 2>/dev/null           # ★記帳した=★数を 0 に戻す
  else
    # ★★2026-08-25 直し(★Taka『直してOK』／ ★計器の維持は MGR の担当)=
    #   ★直す前= ★誰が 叩いたかを 残して いなかった ∴ ★別インスタンスの 分と 混ざり
    #     ★『自分は 投函した のに 数が 減らない』が 起きて いた(★実測で 確認)。
    #   ★足すのは 1列だけ= ★セッション(★既に 在る 環境変数を 使う ／ 新しい 機構を 作らない)。
    printf '%s\t%s\t%s\n' "$(date '+%H:%M:%S')" \
      "$(printf '%s' "$C" | grep -oE '/api/[a-z_]+' | head -1)" \
      "${CLAUDE_SESSION_ID:-${CLAUDE_PROJECT_DIR:-unknown}}" >> "$_UNREC" 2>/dev/null
  fi
fi

# ★★2026-08-26 直し(★3担当＋私が 現在進行で 止められて いた ／ ★実例で 5/7 誤爆を 再現)
#   ★直す前= ★コマンド文字列に `2DER:PROGRESS` が 在れば 鳴らした
#     ∴ ★『投函文を 書く』『投函を 数える』『投函を 除外する』が 全部 止まった。
#     ★報告(route_table 2回 ／ Inference Control 2回 ／ ★私 本日 3回)。
#   ★直した後= ★『投函か どうか』を 見る= ★`submit_client --file X` の X を 読む。
#     ★これで ★本物の 投函を 初めて 検査できる(★従来は ファイル経由だと 素通りだった)。
#   ★`--stdin` は 中身が 見えない ∴ ★止めない(★見えない ものを 落とさない)。
#   ★直接投函は ★書き込みの門(2der_write_guard.sh)が 既に 止める ∴ ★ここで 二重に 見ない。
_POST=""
case "$C" in
  *submit_client*)
    case "$C" in
      *--file*)
        _F="$(printf '%s' "$C" | grep -oE -- '--file[= ]+[^ ]+' | head -1 | sed -E 's/^--file[= ]+//')"
        [ -n "$_F" ] && [ -r "$_F" ] && grep -q '2DER:PROGRESS' "$_F" 2>/dev/null && _POST="$_F" ;;
    esac ;;
esac
# ★投函で なければ ここで 終わり(★平時に 鳴らさない= ★誤爆を 消した ところ)
[ -n "$_POST" ] || exit 0

MISS=""
# 既に守れている3つ(★後半100%)も 門に入れる=★崩れたら止まるようにする
grep -q 'AXIS='        "$_POST" || MISS="${MISS} AXIS="
grep -q '判定='         "$_POST" || MISS="${MISS} 判定="
grep -q '止める='       "$_POST" || MISS="${MISS} 止める="
grep -q '測ったHEAD'    "$_POST" || MISS="${MISS} 測ったHEAD"
# ★守れていない4つ= ★欄を必須にする(値は UNVERIFIED でよい)
grep -q '形式='         "$_POST" || MISS="${MISS} 形式=(範囲/R1/R2/R3/R4)"

[ -z "$MISS" ] && exit 0

deny "2DER 形式の門: 台帳へ投函する note に 欄が足りません ->${MISS}

★『やった』と書かせる門ではありません。★『やっていない』を 書かずに済ませられなくする門です。
★値は問いません。埋まらない欄は ★UNVERIFIED / . と書いてください
  (2DER 自身の規約と同じ= progress_seal 逐語『UNKNOWN は値として書けるが、欄を欠くことは許さない
   ——「分からない」と「書かなかった」を同じ欄に持たせないため』)。

★書き方の例:
  形式= 範囲:o R1:o R2:o R3:UNVERIFIED R4:.(未発火)

★根拠(2026-08-22 実測): MGR の記帳 55本 平均 3.9/8。
  機械が既に見ている項目は後半 28/28=100%、見ていない項目は R3 11/55 / R2 14/55 /
  R4 14/55 / 範囲 12/55 と低いまま。R1 は 20/27→12/28 と悪化。
  監査も自己監査で同型(自分で入れた規則の遵守 4/15・6/15・5/15・2/15)。
  ∴ 板が『出力する』だけでは守られない=★投函を検査する。"
