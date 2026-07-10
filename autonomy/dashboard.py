"""SLICE-5: minimal self-contained UI correction surface (2DER autonomous loop v0).

Generates a single static HTML file (no CDN, no server) from the CURRENT_STATE projection.
It is a CORRECTION/ADJUDICATION surface, not a polished product: for each item it shows the
exact `python3 autonomy/amend.py ...` command Taka runs to emit a machine-readable correction
event (contract §10). Loop: view -> copy amend command -> run -> rebuild state -> see effect.
The HTML is regenerable (gitignored). C≠H; no self-improvement claim.
"""
import sys, os, json, html, argparse
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from autonomy.current_state import build_current_state, REPO

CSS = """
:root{--bg:#f7f7f5;--fg:#1a1a1a;--mut:#666;--card:#fff;--line:#e2e0da;--accent:#3a5f8a;
--warn:#9a6a00;--bad:#a33;--good:#2c6e49;--code:#f0efea}
@media(prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e6e6e6;--mut:#9aa0a8;--card:#1e2127;
--line:#2c313a;--accent:#7aa2d6;--warn:#d6a54a;--bad:#e07a7a;--good:#6fbf8f;--code:#0f1115}}
:root[data-theme=light]{--bg:#f7f7f5;--fg:#1a1a1a;--mut:#666;--card:#fff;--line:#e2e0da;--code:#f0efea}
:root[data-theme=dark]{--bg:#16181c;--fg:#e6e6e6;--mut:#9aa0a8;--card:#1e2127;--line:#2c313a;--code:#0f1115}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:24px}
h1{font-size:20px;margin:0 0 2px}h2{font-size:14px;text-transform:uppercase;letter-spacing:.06em;
color:var(--mut);margin:28px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.stat .n{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
.stat .l{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:8px 0}
.card.hold{border-left:3px solid var(--warn)}.card.bad{border-left:3px solid var(--bad)}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);
color:var(--mut);margin-right:6px}.tag.mech{color:var(--good)}.tag.claude{color:var(--accent)}.tag.taka{color:var(--warn)}
code,pre{background:var(--code);border:1px solid var(--line);border-radius:6px;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}
code{padding:1px 5px}pre{padding:10px;overflow-x:auto;margin:6px 0 0}
.amend{color:var(--mut);font-size:12px;margin-top:6px}
ul{margin:6px 0;padding-left:20px}li{margin:2px 0}
.muted{color:var(--mut)}.right{float:right;color:var(--mut);font-size:12px}
.legend{font-size:12px;color:var(--mut);margin-top:6px}
"""

JS = """(function(){var t=document.getElementById('t');t.onclick=function(){
var r=document.documentElement,d=r.getAttribute('data-theme')||
(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
r.setAttribute('data-theme',d==='dark'?'light':'dark')};})();"""


def esc(x):
    return html.escape(str(x), quote=True)


def amend_cmd(action, target, content):
    return f'python3 autonomy/amend.py {action} "{esc(target)}" "{esc(content)}"'


def render(state):
    seals = state["seals"]
    n_ok = sum(1 for s in seals if s["status"] == "OK")
    n_mis = sum(1 for s in seals if s["status"] == "MISMATCH")
    cf = state["component_files"]
    ncomp = sum(len(v) for v in cf.values())
    P = []
    P.append(f'<div class="wrap"><button id="t" style="float:right">◐ theme</button>')
    P.append(f'<h1>2DER autonomous loop — state surface</h1>')
    P.append(f'<div class="sub">as_of {esc(state["as_of"])} · schema {esc(state["schema_version"])} · '
             f'correction/adjudication surface (not a product) · owner=Taka</div>')

    # A SYSTEM STATE
    P.append('<h2>A · System state</h2><div class="grid">')
    for n, l in [(state["latest_de"], "latest DE"), (state["n_de_entries"], "DE entries"),
                 (ncomp, "components"), (f'{n_ok}/{len(seals)}', "seals OK"),
                 (len(state["closed_branches"]), "closed branches"),
                 (len(state["validation_failures"]), "validation fails"),
                 (len(state["candidate_executable_work"]), "candidate work"),
                 ("stale" if state["spec_staleness"]["stale"] else "synced", "spec")]:
        P.append(f'<div class="stat"><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>')
    P.append('</div>')
    if n_mis:
        P.append(f'<div class="card bad"><b>{n_mis} seal MISMATCH</b> — integrity break, priority-1 work.</div>')
    P.append('<div class="legend">UNOWNED: ' + ' · '.join(esc(u) for u in state["unowned_constructs"]) + '</div>')

    # C TAKA DECISION QUEUE
    P.append('<h2>C · Taka decision queue</h2>')
    if state["authority_pending"]:
        for a in state["authority_pending"]:
            P.append(f'<div class="card hold"><span class="tag taka">{esc(a["action"])}</span>'
                     f'<b>{esc(a["target_object"])}</b> — {esc(a.get("content"))}'
                     f'<div class="muted">{esc(a.get("reason") or "")} · {esc(a["event_id"])}</div></div>')
    else:
        P.append('<div class="muted">no active Taka holds/redirects.</div>')

    P.append('<h2>Candidate executable work (mechanical) — correct here</h2>')
    if not state["candidate_executable_work"]:
        P.append('<div class="muted">none pending.</div>')
    for w in state["candidate_executable_work"]:
        held = "hold" if w.get("held_by") else ""
        tgt = w.get("kind")
        P.append(f'<div class="card {held}"><span class="tag">P{esc(w.get("priority"))}</span>'
                 f'<span class="tag">{esc(w.get("kind"))}</span>'
                 + (f'<span class="tag taka">HELD {esc(w["held_by"])}</span>' if w.get("held_by") else '')
                 + f'<span class="right">ref: {esc(w.get("ref"))}</span>'
                 f'<div class="amend">Taka correction (emits a machine event, not a text edit):</div>'
                 f'<pre>{amend_cmd("TAKA_HOLD", tgt, "reason")}\n'
                 f'{amend_cmd("TAKA_REDIRECT", tgt, "do this instead")}\n'
                 f'{amend_cmd("TAKA_PRIORITY_OVERRIDE", tgt, "9")}</pre></div>')

    # overlay effects (visible downstream effect of prior corrections)
    P.append('<h2>Applied Taka corrections (downstream effects)</h2>')
    if state["taka_overlay_effects"]:
        P.append('<ul>' + ''.join(f'<li>{esc(e)}</li>' for e in state["taka_overlay_effects"]) + '</ul>')
    else:
        P.append('<div class="muted">no corrections applied yet. Run an amend command above, then rebuild state.</div>')

    # E TASK DETAIL (validation failures + closed branches, expandable)
    P.append('<h2>E · Detail</h2>')
    if state["validation_failures"]:
        P.append('<details><summary>validation failures ('
                 + str(len(state["validation_failures"])) + ')</summary><ul>')
        for f in state["validation_failures"]:
            P.append(f'<li>{esc(f.get("artifact"))} — {esc(f.get("kind"))} {esc(f.get("detail",""))}</li>')
        P.append('</ul></details>')
    P.append('<details><summary>closed branches (' + str(len(state["closed_branches"]))
             + ', CLAUDE-DERIVED heuristic)</summary><ul>')
    for c in state["closed_branches"]:
        P.append(f'<li>{esc(c["de"])} — {esc(c["decision"])}</li>')
    P.append('</ul></details>')

    # D CORRECTION reference
    P.append('<h2>D · Correction / amendment (machine events)</h2>'
             '<div class="muted">Every correction is an append-only event in AUTONOMY_LEDGER.jsonl '
             '(owner=Taka), not a text edit. Reversible (a later event supersedes). Actions:</div>'
             '<pre>TAKA_CORRECTION  TAKA_PRIORITY_OVERRIDE  TAKA_HOLD  TAKA_REJECT\n'
             'TAKA_REDIRECT  TAKA_AUTHORITY_RECLASSIFICATION  TAKA_CONTEXT_ADDITION</pre>'
             '<div class="muted">After running an amend command, regenerate: '
             '<code>python3 autonomy/build_state.py &amp;&amp; python3 autonomy/dashboard.py</code></div>')
    P.append('<div class="legend" style="margin-top:20px">origin tags: '
             '<span class="tag mech">MECHANICAL</span> parsed fact · '
             '<span class="tag claude">CLAUDE-DERIVED</span> heuristic/interpretive · '
             '<span class="tag taka">TAKA-OWNED</span> owner authority. '
             'Program disposition / value·UX / new premise = TAKA-GATED.</div>')
    P.append('</div>')
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>2DER autonomous loop — state</title><style>{CSS}</style></head>'
            f'<body>{"".join(P)}<script>{JS}</script></body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "autonomy_dashboard.html"))
    a = ap.parse_args()
    html_str = render(build_current_state())
    Path(a.out).write_text(html_str)
    print(f"-> {a.out} ({len(html_str)} bytes)")


if __name__ == "__main__":
    main()
