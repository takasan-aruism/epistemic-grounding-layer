#!/usr/bin/env bash
# 2DER 境界: 台帳(*.jsonl)の直読を機械的に拒否する。
# 許す: コード構造の読み取り / 2DER のプログラム実行 / git 操作(メッセージに台帳名が現れるため)。
# 拒否: テキストユーティリティや即席 python による台帳の中身の読み取り。
set -uo pipefail
IN="$(cat)"
TOOL="$(printf '%s' "$IN" | jq -r '.tool_name // ""')"
ROOTS='/home/takasan/(egl|ds|rri|twoder|dev-workcell)/'
CHEATLOG=/home/takasan/.claude/hooks/.cheat_attempts.log
deny() {
  # ★逃げ道を使おうとした回数を機械で数える(自己申告に頼らない)
  # ただし自己試験の実行は数えない(計器が自分の活動を数えるのを避ける)
  [ -n "${GUARD_SELFTEST:-}" ] && { jq -nc --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
  printf '%s\t%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$TOOL" "$(printf '%s' "${C:-${P:-}}" | head -c 160 | tr '\n' ' ')" >> "$CHEATLOG" 2>/dev/null
  jq -nc --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}
REASON='2DER 境界: 台帳の直読は禁止です(egl/docs/CC_2DER_USAGE_GUIDE.md §2)。台帳の中身は 2DER に聞いてください。答えられないなら「答えられなかった」が結果であり、それが次に作る読み出し機能です。'

REASON_TRACE='2DER 境界: 実行結果(TRACE/runs)の横読みは禁止です。2DER に聞いて返させること。返せないなら「返せない」が結果であり、それが次に作る機能です(egl/docs/CC_2DER_USAGE_GUIDE.md §2)。'

if [ "$TOOL" = "Read" ]; then
  P="$(printf '%s' "$IN" | jq -r '.tool_input.file_path // ""')"
  printf '%s' "$P" | grep -Eq "$ROOTS.*[.]jsonl$" && deny "$REASON"
  printf '%s' "$P" | grep -Eq '/twoder/runs/' && deny "$REASON_TRACE"
  exit 0
fi

[ "$TOOL" = "Bash" ] || exit 0
C="$(printf '%s' "$IN" | jq -r '.tool_input.command // ""')"

# 除外1: git 操作(commit メッセージに台帳名が現れて誤検知するため)
printf '%s' "$C" | grep -Eq '(^|[|;&[:space:]])git([[:space:]]|$)' && exit 0
# 除外2: フック自身の保守
printf '%s' "$C" | grep -q '2der_ledger_guard' && exit 0

# 実行結果(runs/)の横読みも塞ぐ
if printf '%s' "$C" | grep -Eq '/twoder/runs/|twoder/runs/[^ ]*\.json'; then
  if printf '%s' "$C" | grep -Eq '(^|[|;&[:space:]])(cat|head|tail|less|more|grep|rg|sed|awk|jq|wc|sort|uniq|cut|nl|tac|ls)([[:space:]]|$)'; then
    deny "$REASON_TRACE"
  fi
fi

# 除外3: ★front door 経由(★2DER に聞く=★正規経路)。★URL の中の .jsonl は ★直読ではない。
#   ★★2026-08-22 実測(★誤検知)= `curl .../api/ledger_rows?ledger_id=egl/docs/CC_REGISTER.jsonl` が
#     ★URL を path と見なされ ★同じ行の `wc` と組んで deny された。
#     ★これは ★門が『2DER に聞け』と言った当の行為を 止めている=★誤検知。
#   ★直し方= ★URL のトークンだけを 取り除いてから 判定する。
#     ★抜け道にならない= `curl ... ; cat x.jsonl` の `cat x.jsonl` は ★URL の外 ∴ 従来どおり止まる。
C_CHK="$(printf '%s' "$C" | sed -E "s#https?://[^[:space:]\"'\`]+##g")"

# パスとして現れる .jsonl のみを対象にする(文中の言及は対象外)
printf '%s' "$C_CHK" | grep -Eq "(^|[[:space:]<>=('\"\`])[./~][^[:space:]'\"\`]*[.]jsonl" || exit 0
C="$C_CHK"

if printf '%s' "$C" | grep -Eq '(^|[|;&[:space:]])(cat|head|tail|less|more|grep|rg|egrep|fgrep|sed|awk|jq|wc|sort|uniq|cut|nl|tac|column|strings)([[:space:]]|$)'; then
  deny "$REASON"
fi
if printf '%s' "$C" | grep -Eq 'open\(|json[.]loads|readlines|read_json|pd[.]read'; then
  deny "$REASON"
fi
exit 0
