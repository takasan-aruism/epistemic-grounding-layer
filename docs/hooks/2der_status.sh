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

# --- 2. MGR 未応答（★台帳から引く。ls と mtime の走査をやめた＝D-21 のゴール） ---
LEDGER_PENDING=$(cd /home/takasan/egl && timeout 10 python3 -c "
import sys; sys.path.insert(0,'/home/takasan/egl/docs')
try:
    import cc_register as R
    rows=R.pending('MGR')
    print(len(rows))
    for x in rows[:8]: print('  - '+x.get('path','?'))
except Exception as e:
    print('ERR '+str(e)[:60])
" 2>/dev/null)
PN=$(printf '%s' "$LEDGER_PENDING" | head -1)
PENDING=$(printf '%s' "$LEDGER_PENDING" | tail -n +2)
# --- 2b. ★Taka にしか出せない件（D-59 の3区分目）---
# 理由: 「画面をブラウザで見ていない」が D-45 から14 build 放置された。
#       未確認表に書くだけでは Taka に届かない=「出したことにならない」。
# ★新しい台帳は作らない。既存の CC_REGISTER の宛先 TAKA を使う(ACTORS に既に在った)。
TAKA_PENDING=$(cd /home/takasan/egl && timeout 10 python3 -c "
import sys; sys.path.insert(0,'/home/takasan/egl/docs')
try:
    import cc_register as R
    rows=R.pending('TAKA')
    print(len(rows))
    for x in rows[:4]: print('  - '+x.get('path','?'))
except Exception as e:
    print('ERR')
" 2>/dev/null)
TN=$(printf '%s' "$TAKA_PENDING" | head -1)
TAKA_LIST=$(printf '%s' "$TAKA_PENDING" | tail -n +2)
# ずれ検出(F1): 台帳の DOC 行数 と 実ファイル数
DRIFT=$(cd /home/takasan/egl && timeout 10 python3 -c "
import sys,glob,os; os.chdir('/home/takasan/egl'); sys.path.insert(0,'/home/takasan/egl/docs')
try:
    import cc_register as R
    c=R.counts(); import os
    files=len([f for f in glob.glob('docs/CC_*.md')])
    print('台帳 DOC %s / docs 実ファイル %d' % (c.get('doc_rows','?'), files))
except Exception as e:
    print('判定不能')
" 2>/dev/null)

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
line "MGR 未応答    : ${PN} 件（台帳から。走査ではない）"
# ★2026-07-29: Taka「またあなたで止まってる」2回。真因=「未応答0」を「やることが無い」と読んでいた。
#   ★1つの 0 が2つを指していた(応答すべき文書が無い / 私の手番が無い)。本日ずっと直してきた形が計器に在った。
#   ★新しい計器を作らない。0 のときだけ、読み違いを名指しする1行を出す。
if [ "${PN:-x}" = "0" ]; then
  line "  ★未応答0 は「やることが無い」ではない。→ 次の指示を出したか / 誰の何を待つか名指ししたか"
fi
# ★2026-08-08: Taka「なんで私にバケツリレーさせる？」。真因=★上の「未応答」は【文書】だけを数えており、
#   ★台帳の note で渡された手番(next=MGR)を1件も見ていなかった。実装が 17:15:51 に next=MGR で渡し、
#   ★私は 6秒後に台帳を読まずに書いた=手番に気づかず、Taka が伝令になった。
#   ★新しい計器を作らない。既存の口(GET /api/resolve)で 台帳の最新1件を 1行 出す(実測 0.08秒)。
#   ★2026-08-08 追記: 最初は EVO-0035 の1件だけ見ていた=★設計が EVO-0058 に書いた手番を見落とした。
#   ∴ ★進行中の item を全部 見る(★roadmap から機械で取る・実測 合計1秒未満)。
HANDOFF=$(timeout 12 python3 -c "
import json,urllib.request,base64,re
def get(p,TOK):
    r=urllib.request.Request('http://100.107.6.119:8770'+p)
    r.add_header('Authorization','Basic '+base64.b64encode(('taka:'+TOK).encode()).decode())
    return json.loads(urllib.request.urlopen(r,timeout=6).read().decode())
try:
    TOK=open('/home/takasan/twoder/.access_token').read().strip()
    rm=get('/api/roadmap',TOK); ids=[]
    for ph in rm.get('phases') or []:
        for it in (ph.get('items') or []):
            if it.get('status')=='IN_PROGRESS': ids.append(it.get('item_id') or it.get('id'))
    rows=[]
    for i in ids:
        try:
            h=get('/api/resolve?id=%s&history=1'%i,TOK)['history'][-1]
        except Exception: continue
        n=h.get('status_note') or ''
        x=(re.findall(r'next=(\w+)',n) or ['?'])[0]
        # ★2026-08-09 直し: 時刻だけ(HH:MM:SS)で並べていたため ★昨日の 22:12 が 今日の 16:49 より新しく見えた。
        #   ∴ ★日付を含む registered_at で並べる。表示は時刻だけにする(日付が違う時は日付も出す)。
        ts=h['registered_at']
        rows.append((ts, i.replace('ITEM-2DER-',''), (re.findall(r'actor=(\w+)',n) or ['?'])[0], x))
    rows.sort(reverse=True)
    import datetime
    today=datetime.date.today().isoformat()
    def _t(ts): return ts[11:19] if ts[:10]==today else ts[5:16]
    # ★★2026-08-17(★DESIGN の 指摘=★FINDING)=★前は ★`next=='MGR'` を ★『私の手番』と 出していた
    #   =★★同じ 表が 3役 すべてに 入る ∴ ★★DESIGN には ★逆向きに 嘘を つく。
    #   ∴ ★★★役を 判定する 仕組みを 作らない=★★事実(★誰の 手番か)を そのまま 出す。
    if rows:
        top=rows[0]
        print('次の手番=%s ／ %s %s(最後=%s)' % (top[3], _t(top[0]), top[1], top[2]))
        by={}
        for t,i,a,nx in rows: by[nx]=by.get(nx,0)+1
        print('  待ち=' + ' / '.join('%s:%d' % (k,v) for k,v in sorted(by.items())))
    else:
        print('取得できず')
except Exception:
    print('取得できず')
" 2>/dev/null)
line "台帳の手番    : ${HANDOFF}"
# --- ★2026-08-10 追加: 前回この表を出してから 何が変わったか を1行で区別する ---
#   理由(★設計からの利用者報告・実害): 通知の1行が すべて同じ見た目で並ぶため
#   ★「コードが変わった」と「台帳へ書いただけ」を読み分けられず、★実装9行の日を「動いている」と Taka に報告した。
#   ★新しい計測は足さない=★git と 既に引いている roadmap の値を 分類して並べるだけ。
SINCE=$(timeout 15 python3 -c "
import subprocess, os
SNAP='/home/takasan/.claude/hooks/.2der_since_snapshot'
REPOS='ds rri egl dev-workcell twoder'.split()
prev={}
try:
    for ln in open(SNAP):
        k,_,v=ln.strip().partition('='); prev[k]=v
except Exception: pass
cur={}; code=[]; recs=0; docs=0
for r in REPOS:
    d='/home/takasan/'+r
    try:
        sha=subprocess.run(['git','-C',d,'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
    except Exception: continue
    if not sha: continue
    cur[r]=sha
    old=prev.get(r)
    if not old or old==sha: continue
    out=subprocess.run(['git','-C',d,'diff','--numstat',old+'..'+sha],capture_output=True,text=True).stdout
    add=rm=0; names=[]
    for ln in out.splitlines():
        f=ln.split('\t')
        if len(f)<3: continue
        path=f[2]
        if path.endswith('.jsonl'): recs+=1; continue
        if path.endswith('.md'): docs+=1; continue
        try: add+=int(f[0]); rm+=int(f[1])
        except Exception: pass
        names.append(os.path.basename(path))
    if names: code.append('%s +%d/-%d(%s)'%(r,add,rm,','.join(sorted(set(names))[:3])))
parts=[]
if code: parts.append('★コード '+' / '.join(code))
if recs: parts.append('記録のみ %d'%recs)
if docs: parts.append('文書 %d'%docs)
if not parts: parts.append('変化なし')
open(SNAP,'w').write(''.join('%s=%s\n'%(k,v) for k,v in cur.items()))
print(' ／ '.join(parts))
" 2>/dev/null)
line "前回から      : ${SINCE:-判定不能}"

case "$HANDOFF" in
esac
if [ "${TN:-0}" != "0" ] && [ "${TN:-ERR}" != "ERR" ]; then
  line "★Taka にしか出せない件: ${TN} 件（我々の受入では埋まらない）"
  printf '%s\n' "$TAKA_LIST" | sed 's|.*/|  - |'
fi
# ★2026-08-10: 行を1本 足すので 1本 減らす(★設計の報告『量が原因で読み飛ばした』)。
#   ★台帳のずれ は 何日も同じ値 ∴ full のときだけ出す(★値は消さない)。
[ "$MODE" = "full" ] && line "台帳のずれ    : ${DRIFT}"
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
  if [ "$newest" = "1" ]; then STALE="$STALE ${mod}(pid $pid, ${age}h前起動: ソースが新しい【要否は未確認・2026-08-02 実測で再起動不要だった事例あり=EVO-0033】)"; fi
done
line "実行中プロセス:${STALE:- ソースより新しい起動 or 該当なし}"
# --- 5. ★逃げ道を使おうとした回数(フックが拒否した実数・自己申告でない) ---
CL=/home/takasan/.claude/hooks/.cheat_attempts.log
if [ -f "$CL" ]; then
  TODAY_N=$(grep -c "^$(date '+%Y-%m-%d')" "$CL" 2>/dev/null || echo 0)
  ALL_N=$(wc -l < "$CL" 2>/dev/null || echo 0)
  line "台帳の直読を試みた回数: 本日 ${TODAY_N} / 累計 ${ALL_N}（フックが拒否した実数）"
  # ★数字だけでは「何を読もうとしたか」が分からず、計器が誤解を招く。直近1件を出す。
  if [ "${TODAY_N:-0}" -gt 0 ] 2>/dev/null; then
    line "  直近の拒否: $(tail -1 "$CL" 2>/dev/null | cut -c1-150)"
  fi
else
  line "台帳の直読を試みた回数: 0（記録開始以降）"
fi

line "$(/home/takasan/.claude/hooks/2der_gap_flow.sh 2>/dev/null || echo 'Gap の流れ: 判定不能')"
line "$(/home/takasan/.claude/hooks/2der_arch_fresh.sh 2>/dev/null || echo '実行構造の資料: 判定不能')"
line "$(/home/takasan/.claude/hooks/2der_layers.sh 2>/dev/null || echo '層飛ばし: 判定不能')"
line "★A（自己申告計器）は 2026-08-02 に廃止した。主体は台帳で見る: GET /api/resolve?id=ITEM-…&history=1 の status_note の actor（2DER/Claude/MGR/Taka）。人が set する値は証拠にしない（v0.3 §13.3）"
line "全体: 2DER を一本の道にする(横から見る経路を潰し、使うことで育てる)"
CURPOS=$(timeout 20 python3 - <<'PYEOF' 2>/dev/null || echo "現在地: front door から取れない"
import json,base64,urllib.request
tok=open("/home/takasan/twoder/.access_token").read().strip()
req=urllib.request.Request("http://100.107.6.119:8770/api/roadmap",
    headers={"Authorization":"Basic "+base64.b64encode(("taka:"+tok).encode()).decode()})
d=json.load(urllib.request.urlopen(req,timeout=15))
items=[i for p in d.get("phases",[]) for i in p.get("items",[])
       if i["item_id"].startswith("ITEM-2DER-EVO-00") and i["item_id"][-4:].isdigit() and int(i["item_id"][-4:])>=21]
act=[i for i in items if i["status"]=="IN_PROGRESS"]
done=[i for i in items if i["status"]=="DONE"]
defr=[i for i in items if i["status"] in ("DEFERRED","PROPOSED")]
def fmt(x): return "%s %s" % (x["item_id"].replace("ITEM-2DER-",""), x["title"][:34])
print("現在地(台帳から機械が出す): 進行中 %d件=%s ／ 済 %d件 ／ 後回し %d件" % (
    len(act), " ; ".join(fmt(a) for a in act[:4]) or "なし", len(done), len(defr)))
PYEOF
)
line "$CURPOS"
line "MGR の担当: 段3 の指示と受領 / 裁定 / Taka への報告 / commit・push / 計器の維持"
line "規律: 記憶で俯瞰しない。既存を読んでから作る。ソースに在る≠動く。1回の観測で断定しない。台帳の直読は【直読】と明記。"
