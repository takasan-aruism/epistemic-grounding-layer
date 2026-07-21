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

出力: egl/docs/2DER_LEDGER_FLOW.md（mermaid + 説明）。--check で行番号裏づけを検証。
"""
import json, re, sys
from pathlib import Path

ROOT = Path("/home/takasan")
S = ROOT / "egl" / "structure"
REG = {r["ledger_id"]: r for r in map(json.loads, open(S / "LEDGER_REGISTRY.jsonl"))}

# 1 往復の write シーケンス。各要素: (系, 台帳ID, 呼出ファイル:行, 期待シンボル, 説明)
# 行番号は grep 実測（2026-07-22）。--check が各行に期待シンボルが在ることを確認する。
FORWARD = [
    ("DS",  "ds/ds_events.jsonl",              "twoder/submit.py:137", "record_dialogue_event", "入力を対話イベントとして記録"),
    ("RRI", "rri/rri_records.jsonl",           "twoder/submit.py:111", "detect",                "admission/intent を解決・記録"),
    ("EGL", "egl/DESIGN_EVIDENCE_LEDGER.jsonl","twoder/submit.py:123", "admit_design_evidence", "DE admission（admission request 時）"),
    ("EGL", "egl/data/events.jsonl",           "twoder/submit.py:179", "answer_question",       "self-grounding 照会 → EGL SoR event"),
    ("DW",  "dev-workcell/events.jsonl",       "twoder/submit.py:408", "create_task",           "タスク生成（CREATE）※raw_input 起点"),
]
RETURN = [
    ("DW",  "dev-workcell/events.jsonl",       "twoder/return_loop.py:23", "build_result_packet",  "結果パケット生成"),
    ("EGL", "egl/DESIGN_EVIDENCE_LEDGER.jsonl","twoder/return_loop.py:28", "ingest_result_packet", "EGL が admit/reject"),
    ("RRI", "rri/rri_records.jsonl",           "twoder/return_loop.py:33", "form_residual",        "RRI residual/focus 更新"),
    ("DS",  "ds/ds_events.jsonl",              "twoder/return_loop.py:38", "record_dialogue_event","DS 暫定スレッド更新（ループ閉）"),
]
# 欠損辺 ①→②（自律選択 → タスク生成の producer 不在）
MISSING = {
    "reads":  ("twoder/audit/ROADMAP_REGISTRY.jsonl", "twoder/task_selector.py:388", "select_next",
               "ROADMAP ITEM を選ぶ（READ-ONLY, :7 『never dispatches』）"),
    "should_write": ("dev-workcell/events.jsonl", "create_task", "CREATE を書くべき先"),
    "gap": "select_next の勝者を create_task に渡す書き手が存在しない。submit.py:408 は raw_input 起点で自律選択を経由しない。",
}


def verify():
    bad = []
    for _, _, loc, sym, _ in FORWARD + RETURN:
        f, ln = loc.rsplit(":", 1)
        try:
            line = (ROOT / f).read_text().splitlines()[int(ln) - 1]
        except Exception:
            bad.append((loc, "line-out-of-range")); continue
        if sym not in line:
            bad.append((loc, "expected %r not on line: %s" % (sym, line.strip()[:70])))
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
    o.append("- **生成:** `egl/structure/s11_ledger_flow.py`（`--check` で各行番号の裏づけを検証＝腐敗検知）")
    o.append("- **典拠:** s10 登記簿（writer 解析）+ submit.py/return_loop.py の実行番号 + DE-0490（台帳保全済み）\n")
    o.append("## §1. 本線（canonical 12 本、すべて sole writer）\n")
    o.append(mermaid())
    o.append("")
    o.append("## §2. 前向き 1 往復（`submit.py`）\n")
    o.append("| # | 系 | 台帳 | 呼出 | シンボル | 何を書くか |")
    o.append("|---|---|---|---|---|---|")
    for i, (sysn, lid, loc, sym, desc) in enumerate(FORWARD, 1):
        o.append(f"| {i} | {sysn} | `{lid.split('/')[-1]}` | `{loc}` | `{sym}` | {desc} |")
    o.append("")
    o.append("## §3. 戻り（`return_loop.py`）— ループは閉じている\n")
    o.append("| # | 系 | 台帳 | 呼出 | シンボル | 何を書くか |")
    o.append("|---|---|---|---|---|---|")
    for i, (sysn, lid, loc, sym, desc) in enumerate(RETURN, 1):
        o.append(f"| {i} | {sysn} | `{lid.split('/')[-1]}` | `{loc}` | `{sym}` | {desc} |")
    o.append("")
    o.append("## §4. 欠損辺 ①→②（台帳語での再定義）\n")
    o.append("**前ターンの『task_selector→create_task の producer 不在』を、この図の欠損 1 辺として書き直す:**\n")
    rlid, rloc, rsym, rdesc = MISSING["reads"]
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
