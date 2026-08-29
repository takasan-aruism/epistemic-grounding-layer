#!/usr/bin/env bash
# 2DER 役割別の常駐監視 — Monitor ツールから呼ぶ。
#
# ★2026-08-21: `2der_watch_design.sh` を ★役割で 引ける形に した(★中身は 同じ計器)。
#   ★変えた理由(実測 2件):
#     ①★MGR に 監視が 無かった=★監査が next=MGR を 返しても ★誰も 起こさない。
#       実測=05:09:31 に監査が返し ★私が気づいたのは 05:33(Taka の問い)=★24分 の空白。
#     ②★DESIGN 側の 手番判定が ★`ESDE_AUDIT` を 拾えていなかった
#       (★判定は `in ('DESIGN','AUDIT')` ／ ★台帳の実語は `next=ESDE_AUDIT`)
#       =★MGR が 監査へ 渡しても ★★★手番の行が 一度も 鳴らない。
#   ★新しい計器は 作っていない=★既存の front door の口(GET /api/roadmap, /api/resolve)と
#     ★既存の 2der_board.sh だけを 叩く。★状態file は 役割ごと(DESIGN は 従来と同じ path)。
#
# 出す行(これ以外は黙る):
#   ★手番     : 台帳の next= が 自分に なった
#   ★新着     : 自分宛の CC_*.md が増えた
#   ★入口停止 : front door が2回続けて答えない(単一障害点)
#   ★居座り   : 同じ手番のまま STALL_H 時間
#   ★順番が来ない: next が 自分で無いまま STALL_H 時間
#   ★交代     : next= が別の役に移った(1行だけ・状況の追随用)
#
# 使い方: ROLE=MGR    2der_watch.sh        (常駐・既定 120 秒間隔)
#         ROLE=DESIGN 2der_watch.sh
#         INTERVAL=60 STALL_H=2 …          (上書き可)
#         ROLE=MGR 2der_watch.sh once      (1回だけ評価して終わる=自己試験)
#
# ★cwd を /home/takasan に固定する。twoder 配下で python3 を動かすと operator.py が
#   stdlib の operator を隠して落ちる(2026-08-04 実証)。
set -uo pipefail
cd /home/takasan || exit 1

ROLE="$(printf '%s' "${ROLE:-DESIGN}" | tr a-z A-Z)"
case "$ROLE" in
  MGR)    MINE='MGR' ;;
  # ★★2026-08-24: ★役割が 変わった(ESDE_AUDIT → System Operations Domain Manager)。
  #   ★計器が 追随していなかった= ★私は `instance: SYSTEM_OPS` で 書き、手番は next=Taka/Claude に
  #   なるため ★`next=DESIGN|AUDIT` は 二度と 現れない ∴ ★『順番が来ない』が 106時間 と 出た(★偽陽性)。
  #   ★今朝 CC_ALPHA が直した `twoder-manager-v0`(存在しない unit 名)と ★同じ型=
  #   ★名乗った名前が 引けない と 計器は 永久に 同じ嘘を つく。
  DESIGN) MINE='DESIGN|AUDIT|ESDE_AUDIT|SYSTEM_OPS' ;;
  IMPL)   MINE='IMPL' ;;
  *) echo "ROLE は MGR / DESIGN / IMPL のいずれか(いま: $ROLE)"; exit 1 ;;
esac
SELF_INSTANCE="${ROLE}_MAIN|${ROLE}_THREAD"
# ★2026-08-21: 監査は 05:44 から instance を DESIGN_MAIN → ESDE_AUDIT に変えた(監査の自己申告)。
#   ∴ DESIGN 役で 張る 監視が ★自分の書いた行で 鳴らないよう 同じ組に 入れる。
[ "$ROLE" = "DESIGN" ] && SELF_INSTANCE="${SELF_INSTANCE}|ESDE_AUDIT|SYSTEM_OPS"   # ★2026-08-24 役割変更

INTERVAL="${INTERVAL:-120}"
STALL_H="${STALL_H:-3}"
STATE="/home/takasan/.claude/hooks/.2der_watch_$(printf '%s' "$ROLE" | tr A-Z a-z)_state"
BOARD=/home/takasan/.claude/hooks/2der_board.sh
FD="${FD:-http://100.107.6.119:8770}"   # 自己試験で差し替えられるようにする
ERRF="/tmp/.2der_watch_$(printf '%s' "$ROLE" | tr A-Z a-z).err"

# 台帳の手番を1行で取る(状況表と同じ口・同じ式)。出力: "<item> <next> <actor> <ts> <instance>"
handoff() {
  MINE_RE="$MINE" SELF_RE="$SELF_INSTANCE" timeout 20 python3 -c "
import json,urllib.request,base64,re,os
def get(p,TOK):
    r=urllib.request.Request('$FD'+p)
    r.add_header('Authorization','Basic '+base64.b64encode(('taka:'+TOK).encode()).decode())
    return json.loads(urllib.request.urlopen(r,timeout=8).read().decode())
TOK=open('/home/takasan/twoder/.access_token').read().strip()
rm=get('/api/roadmap',TOK); rows=[]
for ph in rm.get('phases') or []:
    for it in (ph.get('items') or []):
        if it.get('status')!='IN_PROGRESS': continue
        i=it.get('item_id') or it.get('id')
        try: h=get('/api/resolve?id=%s&history=1'%i,TOK)['history'][-1]
        except Exception: continue
        n=h.get('status_note') or ''
        rows.append((h['registered_at'], i.replace('ITEM-2DER-',''),
                     (re.findall(r'next=(\w+)',n) or ['?'])[0],
                     (re.findall(r'actor=(\w+)',n) or ['?'])[0],
                     (re.findall(r'instance=(\w+)',n) or ['-'])[0]))
# ★2026-08-21: ★registered_at が None の item が 1件でも 在ると ★ここで TypeError で 落ち
#   ★stderr が 捨てられて ★『front door が 答えない』と ★同じ 空に なっていた(★実測)。
#   ★★この行に バッククォートを 書くと shell が 実行してしまう(★1回 踏んだ)=★記号を 使わない。
#   ∴ ★None を 最後に 送る 鍵で 並べる(★行は 捨てない)。
rows.sort(key=lambda r: (r[0] or ''), reverse=True)
# ★2026-08-18: ★『進行中0件』と『入口が答えない』を ★同じ空で 返していた
#   =★★6時間 盲目に なった(FDFAIL=181)。∴ ★別の語で 返す(★『無い』を 一語で 処理しない)。
if not rows:
    print('NO_ACTIVE_ITEM - - - -'); raise SystemExit(0)
pat=re.compile(r'^(%s)\$' % os.environ['MINE_RE'], re.I)
selfpat=re.compile(r'^(%s)\$' % os.environ['SELF_RE'], re.I)
# ★2026-08-21 実測: ★返すのは1行だけ ∴ ★自分が書いた next=MGR の行が 最新だと
#   ★その下にある ★他者が書いた 本物の手番(監査の ESTABLISHED)が ★隠れる。
#   ∴ ★選ぶ段階で 自分の行を 外す(★黙らせるだけでは 取り落とす)。無ければ 従来どおり。
mine=[r for r in rows if pat.match(r[2] or '') and not selfpat.match(r[4] or '')]
if not mine:
    mine=[r for r in rows if pat.match(r[2] or '')]
t,i,nx,ac,inst = (mine[0] if mine else rows[0])
print('%s %s %s %s %s' % (i,nx,ac,t,inst))
" 2>"$ERRF"
  # ★2026-08-21: ★計器自身が 壊れた 時に ★『入口が答えない』へ 化けていた。
  #   ∴ ★別の語で 返す(★『無い』を 一語で 処理しない ―― この file 自身の 規律を 自分に 適用する)。
  if [ ! -s "$ERRF" ]; then return 0; fi
  # ★入口が 答えない(通信) と ★計器が 壊れた(それ以外) を 分ける。
  #   ★直し方が 正反対 ―― 前者は front door を 見る ／ 後者は この file を 直す。
  if grep -qE 'URLError|HTTPError|timed out|TimeoutError|ConnectionResetError|IncompleteRead|RemoteDisconnected' "$ERRF"; then
    return 0        # ★空で返す=下の FDFAIL 経路(=入口の沈黙)へ
  fi
  printf 'PY_ERROR %s\n' "$(tail -1 "$ERRF" | cut -c1-160)"
}

# 自分宛の未処理(既存の作業板をそのまま使う)
inbox() { "$BOARD" "$ROLE" 2>/dev/null | sed -n 's/^  - //p' | sort | tr '\n' ',' ; }

now_epoch() { date +%s; }
say() { printf '%s [%s] %s\n' "$(date '+%m-%d %H:%M')" "$ROLE" "$1"; }

# 状態: prev_handoff / prev_inbox / same_since(epoch) / stall_said(epoch) / fd_fail
PREV_H=""; PREV_I=""; SAME_SINCE=$(now_epoch); STALL_SAID=0; FDFAIL=0
if [ -f "$STATE" ]; then
  # shellcheck disable=SC1090
  . "$STATE" 2>/dev/null || true
fi

save() {
  {
    printf 'PREV_H=%q\n' "$PREV_H"
    printf 'PREV_I=%q\n' "$PREV_I"
    printf 'SAME_SINCE=%s\n' "$SAME_SINCE"
    printf 'STALL_SAID=%s\n' "$STALL_SAID"
    printf 'FDFAIL=%s\n' "$FDFAIL"
    printf 'MINE_SINCE=%s\n' "${MINE_SINCE:-0}"
    printf 'MINE_SAID=%s\n' "${MINE_SAID:-0}"
    printf 'STALLS=%s\n' "${STALLS:-0}"
    printf 'STALL_ALERT_AT=%s\n' "${STALL_ALERT_AT:-0}"
    printf 'IDLE_SAID=%s\n' "${IDLE_SAID:-0}"
    printf 'PYERR_SAID=%s\n' "${PYERR_SAID:-0}"
  } > "$STATE"
}

is_mine() { printf '%s' "$1" | grep -Eqi "^(${MINE})$"; }

tick() {
  H="$(handoff)"
  # ★計器が 壊れた=★入口の 沈黙とは 別。1時間に1回だけ 出す(★背景に しない)。
  case "$H" in
    PY_ERROR*)
      if [ "$(( $(now_epoch) - ${PYERR_SAID:-0} ))" -ge 3600 ]; then
        say "★この監視自身が落ちている(入口の沈黙ではない): ${H#PY_ERROR }"
        PYERR_SAID=$(now_epoch)
      fi
      save; return ;;
  esac
  if [ -z "$H" ]; then
    FDFAIL=$((FDFAIL+1))
    # ★2026-08-18: ★同じ詰まりを 何度も 鳴らさない(★9時間で 7回=★背景に なる)。
    #   ★1時間に 1回だけ 出し ／ ★その間の 回数を 数えて 添える(★値は 消さない)。
    if [ "$FDFAIL" = "2" ]; then
      STALLS=$(( ${STALLS:-0} + 1 ))
      if [ "$(( $(now_epoch) - ${STALL_ALERT_AT:-0} ))" -lt 3600 ]; then save; return; fi
      STALL_ALERT_AT=$(now_epoch)
      # ★2026-08-18: ★『停止』と決めつけない=★実測3回とも ★プロセスは生きていた。
      #   ★答えない時は ★生死を 同じ行で 出す(★直し方が 正反対=★再起動 か ★重い問いを やめる か)。
      P=$(pgrep -f 'python3 -m twoder.webui' | head -1)
      if [ -n "$P" ]; then
        AGE=$(( $(now_epoch) - $(stat -c %Y /proc/"$P" 2>/dev/null || now_epoch) ))
        L=$(ss -ltn 2>/dev/null | grep -c 8770)
        say "★入口が答えない(2回連続) ／ ★プロセスは生きている(pid $P ／ 起動から $((AGE/3600))時間) ／ 待受 $L =★『落ちた』でなく★『詰まっている』=★重い走査を疑う(★再起動では直らない) ／ ★この監視が数えた詰まり 累計 ${STALLS} 回"
      else
        say "★入口が居ない(2回連続 ／ プロセス無し)=★★これは停止。commit が0になる=誰も迂回していない"
      fi
    fi
    save; return
  fi
  [ "$FDFAIL" -ge 2 ] && say "入口 復帰: front door が答えた"
  FDFAIL=0

  # ★進行中0件=★入口は生きている。★手番の判定は飛ばすが ★自分宛の新着は 見続ける。
  if [ "${H%% *}" = "NO_ACTIVE_ITEM" ]; then
    I="$(inbox)"
    if [ "$I" != "$PREV_I" ] && [ -n "$I" ]; then say "★新着(自分宛): ${I%,}"; fi
    PREV_I="$I"
    if [ "$(( $(now_epoch) - ${IDLE_SAID:-0} ))" -ge $((STALL_H*3600)) ]; then
      say "進行中0件: 台帳に動いている案件が無い(入口は生きている)。★次の案件が立つまで私の手番は来ない"
      IDLE_SAID=$(now_epoch)
    fi
    save; return
  fi

  ITEM=$(printf '%s' "$H" | awk '{print $1}')
  NEXT=$(printf '%s' "$H" | awk '{print $2}')
  ACTOR=$(printf '%s' "$H" | awk '{print $3}')
  INST=$(printf '%s' "$H" | awk '{print $5}')

  if [ "$H" != "$PREV_H" ]; then
    SAME_SINCE=$(now_epoch); STALL_SAID=0
    # ★2026-08-17 の規則『自分が書いた行で 自分が鳴るのをやめる』は ★手番の枝にも かかる。
    #   ★2026-08-21 実測=★自分で next=MGR と書いた 直後に ★自分宛の手番として 鳴った
    #   (★[[instrument-counts-its-own-record]] の 型。★私は 既に 知っている ∴ 情報が 0)。
    #   ★黙らせただけに しない=★放置すれば 下の『居座り』が STALL_H 時間後に 拾う。
    if printf '%s' "$INST" | grep -Eq "^(${SELF_INSTANCE})$"; then :
    elif is_mine "$NEXT"; then
      say "★手番: $ITEM の next=$NEXT (最後に書いたのは $ACTOR / $INST)。★書く前にその item を history=1&history_limit=0 で読む"
    else
      say "交代: $ITEM の next=$NEXT (最後=$ACTOR / $INST)"
    fi
    PREV_H="$H"
  else
    AGE=$(( ( $(now_epoch) - SAME_SINCE ) / 3600 ))
    if [ "$AGE" -ge "$STALL_H" ] && [ "$(( $(now_epoch) - STALL_SAID ))" -ge $((STALL_H*3600)) ]; then
      say "★居座り: $ITEM が next=$NEXT のまま ${AGE}時間 動かない。誰の何を待っているか名指しする"
      STALL_SAID=$(now_epoch)
    fi
  fi

  # ★2026-08-18: ★「同じ手番のまま」だけでは足りない=★他所で動き続けると SAME_SINCE が毎回 戻り
  #   ★『私の順番が いつまでも 来ない』を 拾えない。∴ ★別の鍵=★next が私で無いまま何時間か、で1本 見る。
  if is_mine "$NEXT"; then
    MINE_SINCE=0; MINE_SAID=0
  else
    [ "${MINE_SINCE:-0}" = "0" ] && MINE_SINCE=$(now_epoch)
    WAIT=$(( ( $(now_epoch) - MINE_SINCE ) / 3600 ))
    if [ "$WAIT" -ge "$STALL_H" ] && [ "$(( $(now_epoch) - ${MINE_SAID:-0} ))" -ge $((STALL_H*3600)) ]; then
      say "★順番が来ない: ${WAIT}時間 私の手番が無い(いまの next=$NEXT / $ITEM)。★止まっているのか・私が要らない工程なのかを1回だけ確かめる"
      MINE_SAID=$(now_epoch)
    fi
  fi

  I="$(inbox)"
  if [ "$I" != "$PREV_I" ] && [ -n "$I" ]; then
    say "★新着(自分宛): ${I%,}"
    # ★2026-08-19: ★依頼が 文書で 来ると ★台帳の next= が 動かない=★『順番が来ない』が 誤って 鳴る。
    #   ∴ ★新着も『私の番が来た』と 数える(★時計を 戻す)。
    MINE_SINCE=0; MINE_SAID=0
  fi
  PREV_I="$I"
  save
}

if [ "${1:-}" = "once" ]; then tick; exit 0; fi

while true; do
  tick
  sleep "$INTERVAL"
done
