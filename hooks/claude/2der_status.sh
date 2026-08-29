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
  # ★★2026-08-29 GENERAL_MGR= ★ESDE の依頼(08-24 §5 候補②)を 採った。
  #   ★起きていたこと= ★SessionStart は 10秒で 打ち切られ 控えを 書き直せない。
  #     ★brief は 打ち切られた事実を 知らない ∴ ★6日前の値を「現在」の顔で 出し続けた。
  #   ★直し= ★値は 消さない。★控えが 6時間より 古ければ ★いつの断面かを 添える。
  #   ★why 候補②= ①は 別の走らせ口が 増える ／ ③は 打ち切られた時に 黙るのが 直らない。
  #   ★★「数には鍵を添える」と 同じ= ★古い値でも 断面が 分かれば 使える。
  if [ -f "$CACHE" ]; then
    _age=$(( ( $(date +%s) - $(stat -c %Y "$CACHE" 2>/dev/null || echo 0) ) / 60 ))
    if [ "$_age" -gt 360 ]; then
      RC="$RC  ★古い（$(date -d "@$(stat -c %Y "$CACHE")" '+%m-%d %H:%M' 2>/dev/null) 時点 / ${_age}分前）"
    fi
  fi
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
    # ★2026-08-24: 主体の canonicalization は 2DER の部品から 引く(★ここで 定義しない)
    try:
        import sys as _s; _s.path.insert(0,'/home/takasan')
        from twoder.effective_state import canonical_actor as _CANON
    except Exception:
        _CANON = lambda v: v          # ★引けない時は 寄せない(★黙って 別の判定を 作らない)
    rm=get('/api/roadmap',TOK); ids=[]
    for ph in rm.get('phases') or []:
        for it in (ph.get('items') or []):
            if it.get('status')=='IN_PROGRESS': ids.append(it.get('item_id') or it.get('id'))
    rows=[]
    for i in ids:
        try:
            h=get('/api/resolve?id=%s&history_limit=1'%i,TOK)['history'][-1]
        except Exception: continue
        n=h.get('status_note') or ''
        # ★★2026-08-24(★Taka 裁定③『主体を集計する全 projection で同じ canonicalization を使う』)=
        #   ★ここで 独自に 寄せない。★twoder/effective_state.canonical_actor を 呼ぶ(★1つだけ置く)。
        x=_CANON((re.findall(r'next=(\w+)',n) or ['?'])[0])
        # ★2026-08-09 直し: 時刻だけ(HH:MM:SS)で並べていたため ★昨日の 22:12 が 今日の 16:49 より新しく見えた。
        #   ∴ ★日付を含む registered_at で並べる。表示は時刻だけにする(日付が違う時は日付も出す)。
        # ★2026-08-20 直し: ★registered_at が None の item が 1件でも 在ると
        #   ★rows.sort が TypeError(str vs NoneType)=★except で 全体が 『取得できず』に なり、
        #   ★next=MGR の 手番が 1件 在っても 表から 消えた(実測: EVO-0081/0082 が None)。
        #   ∴ ★None は '' に 寄せて 最後に 並べる(★手番の 行を 落とさない)。
        ts=h.get('registered_at') or ''
        rows.append((ts, i.replace('ITEM-2DER-',''), _CANON((re.findall(r'actor=(\w+)',n) or ['?'])[0]), x))
    rows.sort(reverse=True)
    import datetime
    today=datetime.date.today().isoformat()
    def _t(ts): return (ts[11:19] if ts[:10]==today else ts[5:16]) if ts else '時刻なし'
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
# --- ★2026-08-22 追加: 「next=2DER なのに 2DER が居ない」を名指しする(欠陥 TURN_ADDRESSED_TO_2DER_HAS_NO_READER) ---
#   実測(監査 ESDE_AUDIT / 私も独立に確認): progress_seal.ACTORS に '2DER' は在るが
#   監視の役の語彙(2der_watch.sh:34-36 MGR / DESIGN|AUDIT|ESDE_AUDIT / IMPL)に 2DER は無い。
#   ∴ next=2DER は ★書けるが 誰にも届かない。しかも表には「待ち=2DER:N」と出るので
#   ★止まっていることが 正常に見える(★不在が遵守に見える)。
#   ★機構は増やさない: 既に出している N と 既に在る常駐の生死を 突き合わせて 1行 出すだけ。
#   ★両方が立った時だけ 出す(片方だけなら 黙る=平時に鳴らさない)。
# --- ★2026-08-22 追加: 「台帳に書いていない実験」を名指しする(★Taka 指示=問題と解決を全て台帳へ) ---
#   ★数えるのは 2der_note_form_guard.sh(★PreToolUse)。ここは ★出すだけ(★判定しない)。
#   ★実測の発端= 20:36 に Taka から確認を受け、★1時間ぶんの問題と解決が台帳に無いことが判った。
UNREC_F=/home/takasan/.claude/hooks/.2der_unrecorded_runs
if [ -s "$UNREC_F" ]; then
  UNREC_N=$(wc -l < "$UNREC_F" | tr -d ' ')
  # ★★2026-08-25 直し(★Taka『直してOK』)= ★名前が 実態と ずれて いた。
  #   ★数え方の 逐語(2der_note_form_guard.sh)= 『PROGRESS を含まない物=実験 ／
  #     含む物=記帳 → ★記帳したら 0 に戻す』∴ ★これは
  #     ★『front door を叩いてから ★まだ PROGRESS を投函していない 回数』であって
  #     ★『台帳に 永久に 残らなかった 実験』では ★ない(★後者だと 読める 名前だった)。
  #   ★併せて ★誰の 分かを 出す= ★数える側に セッション列を 足した(★混ざりを 隠さない)。
  UNREC_WHO=$(awk -F'\t' '{print $3}' "$UNREC_F" 2>/dev/null | sort -u | wc -l | tr -d ' ')
  line "★未投函の走行  : ${UNREC_N} 回 (front door を叩いた後 まだ PROGRESS を投函していない)"
  line "                  → ★記帳すれば 0 に戻る ／ ★セッション ${UNREC_WHO} 本ぶんが 混ざり得る"
  line "                  → 直近: $(tail -3 "$UNREC_F" | cut -f1,2 | tr '\n' ' ')"
fi
W2DER=$(printf '%s' "${HANDOFF}" | grep -o '2DER:[0-9]*' | head -1 | cut -d: -f2)
# ★★2026-08-24 直し(★CC_ALPHA 監視の実測・Taka 許可): ★引いていた unit 名が 存在しなかった。
#   ★`twoder-manager-v0` は systemd に 無い ∴ ★常に inactive が返り、
#   ★常駐が active でも 毎回『誰も起こさない=永久停止』を出していた(★偽陽性)。
#   ★実在する名前= `twoder-manager.service`(★実測 2026-08-24 03:48 active/running)。
#   ★名前を1つ直すだけ=★新しい判定を足していない。★『名乗った名前が引けるか』は 対等性の欠損そのもの。
MGRV0=$(systemctl --user is-active twoder-manager.service 2>/dev/null)
if [ -n "${W2DER:-}" ] && [ "${W2DER:-0}" -gt 0 ] 2>/dev/null && [ "${MGRV0}" != "active" ]; then
  line "★誰も起こさない : next=2DER が ${W2DER} 件 ／ twoder-manager.service = ${MGRV0}"
  line "                  → 機械の番だが 常駐が居ない=永久停止。窓を切って回すか 常駐を上げる"
elif [ -n "${W2DER:-}" ] && [ "${W2DER:-0}" -gt 0 ] 2>/dev/null; then
  line "機械の手番      : next=2DER が ${W2DER} 件 ／ 常駐は active(★取りに行けているかは別)"
fi
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
  # ★★2026-08-29 GENERAL_MGR= ★見出しを 足した。★ESDE が 08-24 に報告し ★5日 生きていた欠陥=
  #   ★この一覧は 見出しが 無く、直前の「★Taka にしか出せない件」の 直後に 並ぶ ∴
  #   ★★2つの 別の山が 1つに 見えた(★ESDE 本人が『自分が渡し先を間違えた』と 誤読した)。
  #   ★新しい計器は 作らない。★見出しを1行 出すだけ(★数も 順位も 変えない)。
  line "★MGR の手番（上とは別の山・我々で閉じられる）: ${PN} 件"
  printf '%s\n' "$PENDING" | sed 's|.*/|  - |' | head -8
fi
line "台帳登記 check: $RC"

# --- 4. ★動いているプロセスが、いまのソースを持っているか ---
# (2026-07-27: webui が4日前起動のまま=修理が実行中の系に入っていない、を見逃した)
# ★★2026-08-29 に 2つ直した(MGR)。★why= ★裁定の材料が 古い版から読まれる事故が 62秒差で 起きかけた。
#   ★RRI が escalation の二択を直したのが 14:33:29 / 常駐の起動が 14:34:31。
#   ★もし修正が2分 遅ければ ★MGR は 古い版を読んで『畳む』と裁定し得た。★畳めば戻せない。
#   ★① twoder.manager_v0 が ★監視対象に 入っていなかった(★巡回が居る常駐なのに)。
#   ★② 『ソースが新しい』としか出さず ★どの file かを 出さなかった ∴ ★裁定の材料が 古いかを 判定できない。
#   ★③ 【要否は未確認…】の括弧は ★無視してよい理由に 読める ∴ ★file 名を出して 各自に判定させる形へ。
STALE=""
for spec in "twoder.webui:/home/takasan/twoder:/home/takasan/dev-workcell" "twoder.manager_v0:/home/takasan/twoder" "twoder.operator:/home/takasan/twoder"; do
  mod="${spec%%:*}"; dirs="${spec#*:}"
  pid=$(pgrep -f "python3 -m $mod" | head -1)
  [ -z "$pid" ] && continue
  pstart=$(stat -c %Y /proc/"$pid" 2>/dev/null || echo 0)
  files=""
  for d in $(printf '%s' "$dirs" | tr ':' ' '); do
    f=$(find "$d" -name '*.py' -newermt "@$pstart" -printf '%f ' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | sort -u | head -6 | tr '\n' ' ')
    [ -n "$f" ] && files="$files$f"
  done
  age=$(( ( $(date +%s) - pstart ) / 3600 ))
  nf=$(printf '%s' "$files" | wc -w)
  if [ "$nf" -gt 0 ]; then
    STALE="$STALE
  ★${mod}(pid $pid, ${age}h前起動)= ★載っていない .py ${nf}本以上: ${files}"
  fi
done
line "実行中プロセス:${STALE:- ソースより新しい起動 or 該当なし}"
if [ -n "$STALE" ]; then
  line "  ★↑この .py について裁定を書く前に、載っているかを確かめる(★載っていない版を材料にすると 取り返しのつかない裁定が出る)"
fi
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
