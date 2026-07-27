#!/usr/bin/env bash
# 毎セッション、2DER 使用ガイドの要点を機械的に注入する(「読むのを忘れる」を無くす)
set -uo pipefail
G=/home/takasan/egl/docs/CC_2DER_USAGE_GUIDE.md
P=/home/takasan/egl/docs/CC_OPERATING_POLICY.md
[ -f "$G" ] || exit 0
CTX=$(cat <<'EOF'
【2DER 使用ガイド v1.0 — 機械注入・作業前に必ず効く】
1. あなたは 2DER の外にいる市民である。2DER 内部に入らない。
2. 台帳(*.jsonl の運用データ)を直接読まない・書かない。PreToolUse フックが拒否する。
3. 知りたいことは 2DER に聞く。答えられなければ「答えられなかった」が結果であり、それが次に作る機能である。
4. 投入は `python3 -m twoder.submit "<依頼文>"`(`python3 twoder/submit.py` は operator.py の shadowing で動かない)。
   CLI は task を作れるが進められない。進めるなら webui 経路。
5. worker は production repo に書けない(サンドボックスの保証)。受け取って配置するのは Claude の役割。
   成果物は tempfile 配下で消えるので、受け取りは同じ作業の中で完了させる。
6. 「ソースに在る」を「動く」と書かない。動作の主張には実行した再現コマンドと結果を併記する。
7. 既存を読んでから作る。1回の観測で状態を断定しない。
全文: /home/takasan/egl/docs/CC_2DER_USAGE_GUIDE.md
役割と手続き: /home/takasan/egl/docs/CC_OPERATING_POLICY.md (作業前に読み、文書冒頭に「運用方針 確認済(版)」と書く)
EOF
)
jq -nc --arg c "$CTX" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
