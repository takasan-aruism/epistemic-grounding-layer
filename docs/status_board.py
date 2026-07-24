#!/usr/bin/env python3
"""2DER STATUS BOARD — 2DER 自律化実験の計器(読み取り専用 / status_views 規律 / DE-0474 束縛4)。

位置づけ: このボードは「2DER が自分で課題を解決できるようになる」ための実験の計器である。
  北極星   = LIVE_WORKER_MINIMAL_PASS(Claude 抜きで開発ループが1本緑で回る) 等の自律フラグ。
  死因ラダー = その自律ループを塞いでいる障害物のトラッカー(正本は death_ladder.json)。
  → 死因が全て閉じ、北極星が MET になったとき、この実験は成功し本計器は役目を終える。

一次記録から決定論で1画面を再構築し、前回スナップショットとの差分を出す。
SoR には書き込まない。自分の状態/履歴(~/.2der_status/)のみ書く。
実行: cd /home/takasan/egl/docs && python3 status_board.py
  (twoder/operator.py の stdlib shadow を避けるため cwd を twoder 外に置くこと)
TTY 以外(cron 等)では自動で無色化する。
"""
import json, re, os, subprocess, datetime, sys

BASE  = '/home/takasan'
EGL   = f'{BASE}/egl'
REPOS = ['twoder', 'egl', 'ds', 'rri', 'dev-workcell']
STATE = f'{BASE}/.2der_status/snapshot.json'   # egl(SoR) の外に置く=working tree を汚さない
HIST  = f'{BASE}/.2der_status/history'

_tty = sys.stdout.isatty()
def c(code): return code if _tty else ''
G, Y, R, D, B, X = (c('\033[32m'), c('\033[33m'), c('\033[31m'),
                    c('\033[2m'), c('\033[1m'), c('\033[0m'))

def sh(cmd, cwd):
    try: return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception: return ''

def read_jsonl(path):
    out = []
    try:
        for l in open(path):
            l = l.strip()
            if l:
                try: out.append(json.loads(l))
                except Exception: pass
    except FileNotFoundError: pass
    return out

# ---- collect (決定論・純データ) ---------------------------------------------
def collect():
    m = {'ts': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

    # ① off-ramp flags
    try:
        d = json.load(open(f'{EGL}/experiments/offramp/OFFRAMP_FLAGS_v1.json'))
        fl = d['flags']
        m['flags_met'] = sum(1 for f in fl if f['status'] == 'MET')
        m['flags_tot'] = len(fl)
        m['lwm'] = next((f['status'] for f in fl if f['flag_id'] == 'LIVE_WORKER_MINIMAL_PASS'), '?')
    except Exception:
        m['flags_met'] = m['flags_tot'] = 0; m['lwm'] = '?'

    # ② 死因ラダー: 機械可読な death_ladder.json を最優先。無ければ anchor markdown へフォールバック
    death, death_names, death_src = {}, {}, 'none'
    dj = f'{EGL}/docs/death_ladder.json'
    if os.path.exists(dj):
        try:
            d = json.load(open(dj))
            for x in d['deaths']:
                death[x['id']] = x['status']; death_names[x['id']] = x['name']
            death_src = 'json'
        except Exception: pass
    if not death:
        try:
            txt = open(f'{EGL}/docs/2DER_SESSION_ANCHOR.md').read()
            for mm in re.finditer(r'^\|\s*#(\d)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$', txt, re.M):
                n, name, state = mm.group(1), mm.group(2).strip(), mm.group(3)
                mark = ('closed' if '✅' in state else
                        'open_hard' if ('✗' in state or '未。' in state) else
                        'open' if '⚠' in state else '?')
                death[n] = mark; death_names[n] = name
            death_src = 'anchor(md)'
        except FileNotFoundError: pass
    m['death'] = death; m['death_names'] = death_names; m['death_src'] = death_src

    # ③ 配線率
    import collections
    f = f'{BASE}/twoder/audit/ROADMAP_REGISTRY.jsonl'
    if not os.path.exists(f):
        hit = sh(['bash', '-lc', 'find twoder -name ROADMAP_REGISTRY*.jsonl'], BASE)
        f = hit.splitlines()[0] if hit else None
    wc = collections.Counter(); n = 0
    if f:
        for r in read_jsonl(f):
            if r.get('status') == 'DONE':
                wc[r.get('wiring_state', '(none)')] += 1; n += 1
    m['wiring'] = dict(wc); m['wiring_total'] = n

    # ④ DE 台帳
    ds = read_jsonl(f'{EGL}/DESIGN_EVIDENCE_LEDGER.jsonl')
    m['de_count'] = len(ds)
    m['de_last'] = ds[-1]['design_evidence_id'] if ds else '?'
    m['de_recent'] = [(d['design_evidence_id'], d.get('title', '')[:58]) for d in ds[-3:]]

    # ⑤ git 5 repo
    repos = {}
    for r in REPOS:
        cwd = f'{BASE}/{r}'
        sb = sh(['git', 'status', '-sb'], cwd).splitlines()
        head = sh(['git', 'log', '--oneline', '-1'], cwd)[:48]
        a = re.search(r'ahead (\d+)', sb[0]) if sb else None
        b = re.search(r'behind (\d+)', sb[0]) if sb else None
        dirty = len([l for l in sb[1:] if l.strip()])
        repos[r] = {'head': head, 'ahead': a.group(1) if a else '0',
                    'behind': b.group(1) if b else '0', 'dirty': dirty}
    m['repos'] = repos
    return m

# ---- diff -------------------------------------------------------------------
def diff(cur, prev):
    if not prev: return None, prev.get('ts') if prev else None
    lines = []
    if cur['flags_met'] != prev.get('flags_met'):
        lines.append(f"off-ramp {prev['flags_met']}→{cur['flags_met']} MET")
    if cur['lwm'] != prev.get('lwm'):
        lines.append(f"LIVE_WORKER_MINIMAL_PASS {prev['lwm']}→{cur['lwm']}")
    for n, mk in cur['death'].items():
        pmk = prev.get('death', {}).get(n)
        if pmk and pmk != mk:
            tag = '  ← 閉じた' if mk == 'closed' else ''
            lines.append(f"死因#{n} {pmk}→{mk}{tag}")
    lw, plw = cur['wiring'].get('LIVE_WIRED', 0), prev.get('wiring', {}).get('LIVE_WIRED', 0)
    if lw != plw: lines.append(f"LIVE_WIRED {plw}→{lw}")
    if cur['de_count'] != prev.get('de_count'):
        lines.append(f"DE {prev['de_count']}→{cur['de_count']} 件 (最新 {cur['de_last']})")
    for r, s in cur['repos'].items():
        ps = prev.get('repos', {}).get(r, {})
        chg = []
        if s['ahead'] != ps.get('ahead'): chg.append(f"↑{ps.get('ahead','?')}→{s['ahead']}")
        if s['dirty'] != ps.get('dirty'): chg.append(f"±{ps.get('dirty','?')}→{s['dirty']}")
        if s['head'] != ps.get('head'):   chg.append("new HEAD")
        if chg: lines.append(f"{r}: " + ' '.join(chg))
    return lines, prev.get('ts')

# ---- render -----------------------------------------------------------------
def bar(s=64): return '─' * s
def render(m, diff_lines, prev_ts):
    print(f'\n{B}┌─ 2DER STATUS BOARD {bar(24)} {m["ts"]} ─┐{X}')
    print(f' {D}自律化実験の計器 — 北極星 LIVE_WORKER_MINIMAL_PASS へ / 死因=ループを塞ぐ障害物{X}')
    fcol = G if m['flags_met'] == m['flags_tot'] and m['flags_tot'] else (Y if m['flags_met'] else R)
    lcol = G if m['lwm'] == 'MET' else R
    print(f' {B}北極星{X}   off-ramp {fcol}{m["flags_met"]}/{m["flags_tot"]} MET{X}'
          f'   │  LIVE_WORKER_MINIMAL_PASS={lcol}{m["lwm"]}{X}')
    if m['death']:
        cells = '  '.join((G if mk == 'closed' else (R if mk == 'open_hard' else Y)) +
                          f'#{n}{"✓" if mk=="closed" else "!"}' + X
                          for n, mk in sorted(m['death'].items()))
        unclosed = sum(1 for mk in m['death'].values() if mk != 'closed')
        hard = sum(1 for mk in m['death'].values() if mk == 'open_hard')
        print(f' {B}死因{X}     {cells}   ({R}未閉{unclosed}{X}/{len(m["death"])}'
              f'{f" ・本線を塞ぐ {R}{hard}{X}" if hard else ""}) {D}[{m["death_src"]}]{X}')
    w = m['wiring']
    print(f' {B}配線率{X}   {G}LIVE_WIRED {w.get("LIVE_WIRED",0)}/{m["wiring_total"]}{X}   '
          f'{D}孤島{w.get("TEST_ONLY_ISLAND",0)}・未判定{w.get("(none)",0)}・未束縛{w.get("UNBOUND_NOT_DETERMINABLE",0)}{X}')
    print(f' {B}DE台帳{X}   計{m["de_count"]}件   直近:')
    for did, title in m['de_recent']:
        print(f'   {D}{did}{X} {title}')
    print(f' {B}repo{X}')
    for r in REPOS:
        s = m['repos'][r]; flag = ''
        if s['ahead'] != '0': flag += f' {Y}↑{s["ahead"]}未push{X}'
        if s['behind'] != '0': flag += f' {R}↓{s["behind"]}{X}'
        if s['dirty']: flag += f' {Y}±{s["dirty"]}未commit{X}'
        if not flag: flag = f' {G}clean{X}'
        print(f'   {r:<13}{s["head"]:<50}{flag}')
    # 差分
    print(f'{B}├{bar(66)}┤{X}')
    if diff_lines is None:
        print(f' {D}(初回スナップショット — 次回から差分を表示){X}')
    elif not diff_lines:
        print(f' {G}変化なし{X} {D}(前回 {prev_ts} 比){X}')
    else:
        print(f' {B}Δ 前回 {prev_ts} からの変化{X}')
        for l in diff_lines: print(f'   {Y}•{X} {l}')
    # ボトルネック(本線を塞ぐ open_hard を先に)
    hard = [(n, m['death_names'].get(n, '')) for n, mk in sorted(m['death'].items()) if mk == 'open_hard']
    soft = [(n, m['death_names'].get(n, '')) for n, mk in sorted(m['death'].items()) if mk == 'open']
    if hard:
        print(f' {R}▲ 本線を塞ぐ{X}: ' + ' / '.join(f'#{n} {nm[:22]}' for n, nm in hard))
    if soft:
        print(f' {Y}△ 未解決{X}    : ' + ' / '.join(f'#{n} {nm[:22]}' for n, nm in soft))
    print(f'{B}└{bar(67)}┘{X}\n')

# ---- main -------------------------------------------------------------------
def main():
    cur = collect()
    prev = None
    if os.path.exists(STATE):
        try: prev = json.load(open(STATE))
        except Exception: pass
    dl, pts = diff(cur, prev)
    render(cur, dl, pts)
    # 自分の状態を更新(SoR ではない)
    try:
        json.dump(cur, open(STATE, 'w'), ensure_ascii=False)
        os.makedirs(HIST, exist_ok=True)
        stamp = cur['ts'].replace(' ', '_').replace(':', '')
        json.dump(cur, open(f'{HIST}/board_{stamp}.json', 'w'), ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f'snapshot write failed: {e}\n')

if __name__ == '__main__':
    main()
