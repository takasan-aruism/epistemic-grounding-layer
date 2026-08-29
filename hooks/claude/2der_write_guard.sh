#!/usr/bin/env bash
# ★★2der_write_guard — Claude が 台帳へ 書く 経路を ★submit_client の 1本に 束ねる。
#
# ★★Taka 指示 2026-08-26 逐語=
#   『Claude が /api/submit や内部 writer を自由に直接呼べる状態をやめる』
#   『2DERが使うのとClaudeが使うのは意味が違う。前者は組み込まれてた正規なルート。
#     後者は勝手にやってるハッカーのようなもの』
#
# ★★塞ぐのは ★関数では なく ★Claude の 手= ★2DER 内部(常駐・worker・submit.py)は 一切 触らない。
#   ★同じ 作りの 先例= 2der_ledger_guard.sh(台帳の 直読を 止めて いる)。
#
# ★★実測(2026-08-26)で 列挙した 迂回経路:
#   A. 台帳ファイルへ 直に 書く      … 170箇所 / 122ファイル
#   B. import して 呼べる 書き手関数 … 87個 / 60ファイル
#   C. HTTP の 書く口               … 8口(approve complete consult ingest rthread_add run_next scout submit)
#   D. その他                       … git commit ／ CLI `python3 -m twoder.submit` ／ legacy 画面
#
# ★★通すもの= ★`twoder.submit_client` を 呼ぶ もの だけ。
# ★★通す 例外= ★読み(GET)・検査(--dry-run)・試験(pytest)。
set -uo pipefail

IN=$(cat)
CMD=$(printf '%s' "$IN" | python3 -c 'import sys,json;d=json.load(sys.stdin);print((d.get("tool_input") or {}).get("command") or "")' 2>/dev/null || true)
[ -z "$CMD" ] && exit 0

deny() {
  printf '%s' "$1" 1>&2
  exit 2
}

# ── ★submit_client を 使って いるなら 通す(★これが 唯一の 口) ──
case "$CMD" in
  *submit_client*) exit 0 ;;
esac

# ── ★試験は 通す(★封印試験が 動かないと 直せなく なる) ──
case "$CMD" in
  *pytest*|*"-m pytest"*) exit 0 ;;
esac

# ── ★★読みだけの コマンドは 通す(★2026-08-27 の 誤爆で 足した) ──
#   ★実測= `grep -n "set_status(" …` が 拒否された= ★読みなのに 止まった。
#   ★『書き手の 名前が 文字列に 在る』と『書き手を 呼んで いる』は 別物。
#   ★★甘くしない 線= ★読み専用の 道具だけで 出来て いる 時に 限る。
#     ★python / curl / tee / git commit などが 1語でも 混ざれば ★この 抜けは 使えない。
_READ_ONLY=1
for _w in $(printf '%s' "$CMD" | tr '|;&' '\n\n\n'); do
  :
done
# ★各 区切りの 先頭語を 取り 読み専用の 一覧に 在るかを 見る
_SEG=$(printf '%s' "$CMD" | tr '|;' '\n\n')
while IFS= read -r _line; do
  _line=$(printf '%s' "$_line" | sed -E 's/^[[:space:]]+//')
  [ -z "$_line" ] && continue
  _w1=$(printf '%s' "$_line" | awk '{print $1}')
  _w2=$(printf '%s' "$_line" | awk '{print $2}')
  case "$_w1" in
    grep|rg|egrep|fgrep|sed|awk|cat|head|tail|less|wc|sort|uniq|ls|find|cut|tr|nl|diff|column|xargs|echo|printf|cd|true) ;;
    git)
      case "$_w2" in
        log|show|diff|status|blame|grep|ls-files|rev-parse|cat-file|describe) ;;
        *) _READ_ONLY=0 ;;
      esac ;;
    *) _READ_ONLY=0 ;;
  esac
done <<EOF_SEG
$_SEG
EOF_SEG
# ★`sed` は 書ける(-i) ／ `xargs` は 何でも 呼べる ∴ ★その 2つは 別に 見る
printf '%s' "$CMD" | grep -qE '(^|[[:space:]|;])sed[[:space:]]+[^|;]*-i' && _READ_ONLY=0
printf '%s' "$CMD" | grep -qE '(^|[[:space:]|;])xargs[[:space:]]' && _READ_ONLY=0
# ★出力の 向き先が ★実体の ファイルなら 読みでは ない。
#   ★★2026-08-27 誤爆= `2>/dev/null` を 書きと 見て いた(★捨て先は 書きでは ない)。
#   ★除く= /dev/null / /dev/stderr / /dev/stdout / &1 &2 のような fd。
_REDIR=$(printf '%s' "$CMD" | grep -oE '>>?[[:space:]]*[^[:space:];|)]+' || true)
if [ -n "$_REDIR" ]; then
  while IFS= read -r _r; do
    [ -z "$_r" ] && continue
    _t=$(printf '%s' "$_r" | sed -E 's/^>>?[[:space:]]*//')
    case "$_t" in
      /dev/null|/dev/stderr|/dev/stdout|"&1"|"&2"|"&-") ;;
      *) _READ_ONLY=0 ;;
    esac
  done <<EOF_REDIR
$_REDIR
EOF_REDIR
fi
[ "$_READ_ONLY" = "1" ] && exit 0

WHY=""
HOW=""

# ── C. HTTP の 書く口へ 直に 投げて いないか ──
if printf '%s' "$CMD" | grep -qE '(curl|wget|urlopen|urllib\.request|requests\.post|httpx)' \
   && printf '%s' "$CMD" | grep -qE '/api/(submit|approve|complete|consult|ingest|rthread_add|run_next|scout|ledger_dispose)([^_a-zA-Z0-9]|$)'; then
  WHY="front door の 書く口へ 直に 投げて います"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi

# ── B. 書き手の 関数を 直に 呼んで いないか(★実測で 出た 名前だけ) ──
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE '(register_item|register_amendment|register_phase|register_roadmap|append_task_id|set_status|grant_approval|consume_approval|raise_question|dispose_question|assign_account|record_evidence|record_typed|record_actor|advance_state|create_task|record_audit|record_disposition|record_generate|record_plan|record_utterance|record_dialogue_event|register_plan|record_measurement|ledger_dispose_apply|ledger_dispose_bulk)[[:space:]]*\('; then
  WHY="台帳の 書き手を 直に 呼んで います(★2DER 内部から 呼ぶのは 正規 ／ ★Claude が 呼ぶのは 迂回)"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi

# ── A. 台帳ファイルへ 直に 書いて いないか ──
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE "open\([^)]*\.jsonl[^)]*,[[:space:]]*['\"][aw]" ; then
  WHY="台帳ファイルへ 直に 書いて います"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE '>>?[[:space:]]*[^[:space:]]*\.jsonl'; then
  WHY="台帳ファイルへ リダイレクトで 書いて います"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi

# ── E. その場書き換え(★2026-08-27 実測で 見つけた 穴= ★改修前から 素通りして いた) ──
#   ★`>>` は 見て いたが ★`sed -i` `perl -i` `tee` は 見て いなかった。
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE '((sed|perl|ruby)[[:space:]]+[^|;]*-i|[[:space:]]tee([[:space:]]|$))' \
   && printf '%s' "$CMD" | grep -qE '\.jsonl'; then
  WHY="台帳ファイルを その場で 書き換えて います(sed -i / perl -i / tee)"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi

# ── F. xargs は 何でも 呼べる(★読み専用の 顔で 書ける) ──
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE '(^|[[:space:]|;])xargs([[:space:]]|$)' \
   && printf '%s' "$CMD" | grep -qE '(sed|perl|python3?|tee|rm|mv|cp|git)'; then
  WHY="xargs 経由で 書ける 道具を 呼んで います(★読み専用の 顔で 書ける)"
  HOW="1本ずつ 何を するか 見える 形で 書いてください"
fi

# ── D. CLI の BYPASS(★規律4 逐語『TRACE を1件も残さない=BYPASS』) ──
if [ -z "$WHY" ] && printf '%s' "$CMD" | grep -qE '(python3?|python)[[:space:]]+-m[[:space:]]+twoder\.submit([[:space:]]|$)'; then
  WHY="CLI の twoder.submit は BYPASS です(★規律4 逐語=『task を作れるが進められず 実行記録を1件も残さない』)"
  HOW="python3 -m twoder.submit_client --file <本文> を 使ってください"
fi

[ -z "$WHY" ] && exit 0

deny "2DER 書き込みの門: ${WHY}

★★Claude が 台帳へ 書く 口は ★1本だけです= twoder.submit_client。
   ${HOW}

★なぜ= 2DER 自身が 内部から 呼ぶのは ★組み込まれた 正規ルート。
       ★Claude が 外から 直に 呼ぶのは ★迂回です(Taka 2026-08-26)。
       ★実測(同日)= 迂回できる 経路は ★A ファイル直書き 170箇所 ／ B 書き手関数 87個 ／
       C HTTP の 書く口 9口 ／ D CLI・git。★これを 1本に 束ねています。

★使い方:
   1) 本文を ファイルに 書く(★進捗マーカーを 使う ときは item/actor/stage が 要ります)
   2) python3 -m twoder.submit_client --file <その ファイル>
   3) 返りが LANDED なら 入って 引けた。
      REJECTED なら ★理由・足りない物・次の一手が 返ります。
      SENT_BUT_NOT_LANDED は ★200 だが 入って いない(★200 を 成功と 呼ばない)。
   ★送らずに 検査だけ したい ときは --dry-run。

★読み(GET)・pytest は 止めていません。"
