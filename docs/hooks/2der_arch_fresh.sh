#!/usr/bin/env bash
# Execution Architecture の鮮度: 記録された commit と現在の HEAD を比べる
# (作業指示書 §8 の自動検査案の最小版。新しい機構を作らず、既存 JSON と git だけを使う)
set -uo pipefail
J=/home/takasan/egl/docs/2DER_EXECUTION_ARCHITECTURE.json
[ -f "$J" ] || { echo "実行構造の資料: 無い"; exit 0; }
python3 - "$J" <<'PY'
import json,subprocess,sys
j=json.load(open(sys.argv[1],encoding='utf-8'))
rec={c['repo']:c['commit'] for c in j.get('generated_from',{}).get('commits',[])}
stale=[]
for repo,c in rec.items():
    d='/home/takasan/'+repo
    try:
        head=subprocess.run(['git','-C',d,'rev-parse','--short','HEAD'],capture_output=True,text=True).stdout.strip()
    except Exception:
        head='?'
    if not head or head[:7]==c[:7]: continue
    # ★コードが変わった時だけ「古い」とする(文書 commit で鳴らない)
    try:
        ch=subprocess.run(['git','-C',d,'diff','--name-only',c+'..HEAD'],capture_output=True,text=True).stdout
    except Exception:
        ch=''
    py=[l for l in ch.splitlines() if l.endswith('.py')]
    if py: stale.append('%s(記録%s→現在%s / .py %d本変化)'%(repo,c[:7],head[:7],len(py)))
g=len(j.get('gaps',[])); cmp=len(j.get('components',[])); e=len(j.get('edges',[]))
if stale:
    print('実行構造の資料: ★古い — '+' '.join(stale)+' / 要更新 (gap %d)'%g)
else:
    print('実行構造の資料: 現在の HEAD と一致 (component %d / edge %d / gap %d)'%(cmp,e,g))
PY
