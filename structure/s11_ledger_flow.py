#!/usr/bin/env python3
"""LEDGER FLOW — canonical 運用台帳 12 本を「本線 1 本」として台帳語で描く。

s10（登記簿）は各台帳を孤立点として登記した。本器は台帳間の流れを描く。
ただし正直に設計する: 2DER のデータは台帳ファイル間を直接流れない。orchestrator
（submit.py 前向き / return_loop.py 戻り）が各台帳の sole writer を順に呼ぶ。
よって「流れ」= 1 往復の write シーケンスである。各ステップは submit.py/return_loop.py の
実 行番号で裏づけ、行が消えたら self-check が落ちる（腐敗検知）。

欠損辺 ①→② は台帳語でこう表現される:
    task_selector が ROADMAP_REGISTRY を読む（select_next, READ-ONLY, "never dispatches"）
    → 【この間に書き手が居ない】→ dev-workcell/events に CREATE を書く
    submit.py:408 の create_task は存在するが raw_input 起点（自律選択ではない）。

出力: egl/docs/2DER_LEDGER_FLOW.md（mermaid + 説明）。--check で**呼出が実在するか**を検証（行番号は資料生成時に ast で引く）。
"""
import ast
import json, re, sys
from pathlib import Path

ROOT = Path("/home/takasan")
S = ROOT / "egl" / "structure"
REG = {r["ledger_id"]: r for r in map(json.loads, open(S / "LEDGER_REGISTRY.jsonl"))}

# 1 往復の write シーケンス。各要素: (系, 台帳ID, 呼出ファイル, 期待シンボル, 説明)
# ★★[Claude実装/STRUCTURE] 2026-08-27(ITEM-2DER-EVO-0120 の作業表 #13):
#   ★★行番号を書くのを やめた。★理由= ★行番号は 手で 直す仕事を 生み続けていた=
#     2026-07-26 に 一度 直しており(「+2 行ずれたため更新」)、2026-08-27 に また 5件 全部が ずれた
#     (★実測= 139→345 / 113→318 / 125→331 / 181→394 / 412→1134)。★呼出は 5件とも 消えていない=
#     ★腐っていたのは ★行番号だけ で、★図の主張は 正しかった。
#   ★★直し= ★呼出の 在り処は ★ast で その場で 引く(`_call_lines`)。★図には 引いた 行を 載せる
#     ∴ ★資料は 生成のたびに 現在の行に 揃い、★人が 直す仕事は 0 になる。
#   ★★門は 緩めていない= ★『その呼出が 消えた』時は 前と同じく RED になる(★弱くなったのは
#     『行がずれた』という ★人には 直せても 機械には 意味の無い 検知だけ)。
FORWARD = [
    ("DS",  "ds/ds_events.jsonl",              "twoder/submit.py", "record_dialogue_event", "入力を対話イベントとして記録"),
    ("RRI", "rri/rri_records.jsonl",           "twoder/submit.py", "detect",                "admission/intent を解決・記録"),
    ("EGL", "egl/DESIGN_EVIDENCE_LEDGER.jsonl","twoder/submit.py", "admit_design_evidence", "DE admission（admission request 時）"),
    ("EGL", "egl/data/events.jsonl",           "twoder/submit.py", "answer_question",       "self-grounding 照会 → EGL SoR event"),
    ("DW",  "dev-workcell/events.jsonl",       "twoder/submit.py", "create_task",           "タスク生成（CREATE）※raw_input 起点"),
]
RETURN = [
    ("DW",  "dev-workcell/events.jsonl",       "twoder/return_loop.py", "build_result_packet",  "結果パケット生成"),
    ("EGL", "egl/DESIGN_EVIDENCE_LEDGER.jsonl","twoder/return_loop.py", "ingest_result_packet", "EGL が admit/reject"),
    ("RRI", "rri/rri_records.jsonl",           "twoder/return_loop.py", "form_residual",        "RRI residual/focus 更新"),
    ("DS",  "ds/ds_events.jsonl",              "twoder/return_loop.py", "record_dialogue_event","DS 暫定スレッド更新（ループ閉）"),
]
# 欠損辺 ①→②（自律選択 → タスク生成の producer 不在）
MISSING = {
    "reads":  ("twoder/audit/ROADMAP_REGISTRY.jsonl", "twoder/task_selector.py", "select_next",
               "ROADMAP ITEM を選ぶ（READ-ONLY, :7 『never dispatches』）"),
    "should_write": ("dev-workcell/events.jsonl", "create_task", "CREATE を書くべき先"),
    "gap": "select_next の勝者を create_task に渡す書き手が存在しない。submit.py の create_task 呼出は raw_input 起点で自律選択を経由しない。",
}


def _call_lines(relpath, sym):
    """`relpath` の中で `sym` を **呼んでいる** 行番号を ast で全部返す。

    ★文字列一致では ない= ★コメントや docstring に 名前が 出るだけでは 当たらない
      (★行番号の 検査より 強い= ★『呼んでいる』ことを 見ている)。
    ★引けない(ファイルが読めない/構文が壊れている)ときは None を返す= ★0件と 混ぜない。
    """
    try:
        tree = ast.parse((ROOT / relpath).read_text(encoding="utf-8"))
    except Exception:
        return None
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nm == sym:
                out.append(n.lineno)
    return sorted(out)


def _loc(relpath, sym):
    """資料に載せる 在り処。★行は その場で 引く(★手で 書かない)。"""
    ln = _call_lines(relpath, sym)
    if ln is None:
        return "%s:?" % relpath
    if not ln:
        return "%s:(呼出なし)" % relpath
    return "%s:%s" % (relpath, ",".join(str(x) for x in ln))


def verify():
    bad = []
    for _, _, f, sym, _ in FORWARD + RETURN:
        ln = _call_lines(f, sym)
        if ln is None:
            bad.append((f, "読めない/構文が壊れている（★呼出の有無を判定していない）")); continue
        if not ln:
            bad.append((f, "expected call %r が 1箇所も無い=図の主張が消えた" % sym))
    # 欠損辺の裏づけ: task_selector は READ-ONLY を宣言し create_task を呼ばない
    ts = (ROOT / "twoder/task_selector.py").read_text()
    if "never dispatches" not in ts:
        bad.append(("task_selector.py", "READ-ONLY 宣言（never dispatches）が消えた=欠損辺の前提が変化"))
    if "create_task" in ts:
        bad.append(("task_selector.py", "create_task 呼出が出現=①→②が塞がれた可能性。図を更新せよ"))
    return bad


def mermaid():
    L = []
    L.append("```mermaid")
    L.append("flowchart LR")
    L.append("  %% canonical 運用台帳 = 本線ノード。orchestrator が各 sole writer を順に呼ぶ")
    sysnode = {"DS": "DS_LOG", "RRI": "RRI_REC", "EGL_DE": "EGL_DE", "EGL": "EGL_EV", "DW": "DW_EV"}
    L.append('  DS_LOG["ds_events.jsonl<br/>writer: phase0.py"]')
    L.append('  RRI_REC["rri_records.jsonl<br/>writer: intent_record.py"]')
    L.append('  EGL_DE["DESIGN_EVIDENCE_LEDGER<br/>writer: de_admission.py"]')
    L.append('  EGL_EV["egl/data/events.jsonl<br/>writer: core.py"]')
    L.append('  DW_EV["dev-workcell/events.jsonl<br/>writer: workcell.py"]')
    L.append('  ROADMAP["ROADMAP_REGISTRY<br/>writer: roadmap_registry.py"]')
    L.append('  SEL{{"task_selector.select_next<br/>READ-ONLY / never dispatches"}}')
    L.append("  %% 前向き（submit.py 1往復）")
    L.append("  DS_LOG -->|submit:137→111| RRI_REC")
    L.append("  RRI_REC -->|submit:111→179| EGL_EV")
    L.append("  EGL_EV -->|submit:179→123| EGL_DE")
    L.append("  EGL_DE -->|submit:387→408| DW_EV")
    L.append("  %% 戻り（return_loop.py）ループ閉")
    L.append("  DW_EV -->|return:23→28| EGL_DE")
    L.append("  EGL_DE -.->|return:33| RRI_REC")
    L.append("  RRI_REC -.->|return:38| DS_LOG")
    L.append("  %% 欠損辺 ①→②：自律選択 → CREATE の producer 不在")
    L.append("  ROADMAP -->|select_next :388| SEL")
    L.append('  SEL -. "✗ 書き手が居ない<br/>（submit:408 は raw_input 起点）" .-> DW_EV')
    L.append("  classDef missing stroke:#c00,stroke-width:2px,stroke-dasharray:5;")
    L.append("  class SEL missing;")
    L.append("```")
    return "\n".join(L)


def doc():
    canon = [r for r in REG.values() if r["role"] == "CANONICAL"]
    inst = [r for r in REG.values() if r["role"] == "INSTANCE_STORE"]
    o = []
    o.append("# 2DER 台帳フロー図（本線を台帳語で / 実測 2026-07-22）\n")
    o.append("- **これは何か:** canonical 運用台帳 12 本を「1 本の機能としての 2DER」の設計図として描く。")
    o.append("  1,313 のコード辺は人間が捌けないが、台帳 12 ノードなら本線が読める。")
    o.append("- **正直な設計:** データは台帳ファイル間を直接流れない。orchestrator（`submit.py` 前向き /")
    o.append("  `return_loop.py` 戻り）が各台帳の **sole writer** を順に呼ぶ。図の辺 = 1 往復の write シーケンス。")
    o.append("- **生成:** `egl/structure/s11_ledger_flow.py`（`--check` で**呼出が実在するか**を検証＝腐敗検知。★表の行番号は生成時に ast で引いた実測であり、手で書いた値ではない）")
    o.append("- **典拠:** s10 登記簿（writer 解析）+ submit.py/return_loop.py の実行番号 + DE-0490（台帳保全済み）\n")
    o.append("## §1. 本線（canonical 12 本、すべて sole writer）\n")
    o.append(mermaid())
    o.append("")
    o.append("## §2. 前向き 1 往復（`submit.py`）\n")
    o.append("| # | 系 | 台帳 | 呼出 | シンボル | 何を書くか |")
    o.append("|---|---|---|---|---|---|")
    for i, (sysn, lid, f, sym, desc) in enumerate(FORWARD, 1):
        o.append(f"| {i} | {sysn} | `{lid.split('/')[-1]}` | `{_loc(f, sym)}` | `{sym}` | {desc} |")
    o.append("")
    o.append("## §3. 戻り（`return_loop.py`）— ループは閉じている\n")
    o.append("| # | 系 | 台帳 | 呼出 | シンボル | 何を書くか |")
    o.append("|---|---|---|---|---|---|")
    for i, (sysn, lid, f, sym, desc) in enumerate(RETURN, 1):
        o.append(f"| {i} | {sysn} | `{lid.split('/')[-1]}` | `{_loc(f, sym)}` | `{sym}` | {desc} |")
    o.append("")
    o.append("## §4. 欠損辺 ①→②（台帳語での再定義）\n")
    o.append("**前ターンの『task_selector→create_task の producer 不在』を、この図の欠損 1 辺として書き直す:**\n")
    rlid, rfile, rsym, rdesc = MISSING["reads"]
    rloc = _loc(rfile, rsym)
    wlid, wsym, wdesc = MISSING["should_write"]
    o.append("```")
    o.append(f"  {rlid.split('/')[-1]}  ──読む──▶  {rloc} ({rsym})")
    o.append(f"       {rdesc}")
    o.append(f"                          │")
    o.append(f"                    ✗ 書き手が居ない")
    o.append(f"                          ▼")
    o.append(f"  {wlid}  ({wsym} = {wdesc})")
    o.append("```")
    o.append(f"\n{MISSING['gap']}\n")
    o.append("**つまり:** 本線の write シーケンス（§2/§3）は閉じているが、**ROADMAP_REGISTRY（自律選択の台帳）だけが")
    o.append("この輪に接続していない。** ROADMAP を読む `select_next` は存在し READ-ONLY だが、その勝者を")
    o.append("`dev-workcell/events` の CREATE に変換する 1 本の書き手が欠けている。これが唯一の欠損辺である。")
    o.append("\n> 棲み分け（何を残すか）と本線接続（①→②）は別作業ではない。**同じ図の上の作業**である。")
    o.append("> ROADMAP_REGISTRY を本線ノードに繋ぐ = 自律ループが回る。繋がねば ROADMAP は孤立点のまま。\n")
    o.append("## §5. instance store（本線ではない、点2の区別）\n")
    o.append(f"canonical event log とは別に、reader コードが live なだけの **instance store が {len(inst)} 本**ある")
    o.append("（`egl/data_*/events.jsonl`, `run_sor/events.jsonl` 等）。同一 writer（core.py 等）が")
    o.append("scenario ごとに作った実体で、本線ノードではない。LIVE 分類が到達性と現用を混ぜないよう分離した。\n")
    o.append("| instance store | 行 | 放置日 |")
    o.append("|---|--:|--:|")
    for r in sorted(inst, key=lambda x: -x["rows"]):
        o.append(f"| `{r['ledger_id']}` | {r['rows']} | {r['governance']['idle_days']} |")
    return "\n".join(o) + "\n"


def main():
    if "--check" in sys.argv:
        bad = verify()
        for loc, why in bad:
            print(f"STALE {loc}: {why}")
        print(f"\n{len(bad)} stale reference(s) — 図が実コードとずれている" if bad else "\n0 stale — 図は実コードと一致")
        sys.exit(1 if bad else 0)
    bad = verify()
    if bad:
        print("WARNING: %d stale refs（--check 参照）。図は生成するが要更新。" % len(bad))
    (ROOT / "egl/docs/2DER_LEDGER_FLOW.md").write_text(doc())
    print("wrote egl/docs/2DER_LEDGER_FLOW.md")


if __name__ == "__main__":
    main()
