#!/usr/bin/env python3
"""第0手: ROADMAP `DONE` の意味を確定し、全 DONE 項目に計算値 `wiring_state` を付与する。

背景（実測）:
  `ROADMAP.status = DONE` は「モジュールが存在し単体テストが通る」を意味しており、
  「live path に接続されている」を意味していない。DONE 67 件のうち 30 件が
  ROADMAP_DONE_BUT_NOT_WIRED（CONTRADICTIONS.jsonl, HIGH）。

設計上の制約（これを守るために status を書き換えない）:
  - `task_selector.py:23  EXCLUDED_STATUSES = ("DONE","DROPPED","DEFERRED")`
  - `roadmap_registry.is_blocked()` は依存先が status=="DONE" であることを要求する
  - `task_selector.py:349` は未知 status を `unknown_status` として fail-closed 扱いにする
  → status を変えると live な選択・依存解決の挙動が変わる。よって **status は不変**とし、
    加算的な計算列 `wiring_state` を付ける。意味は定義側で確定させる。

方式: ROADMAP_REGISTRY.jsonl は append-only / latest-wins（roadmap_registry.py:3）。
  各 DONE 項目の最新行を verbatim に複製し、計算列のみを足して追記する。
  status / depends_on / acceptance 等は 1 バイトも変えない。

wiring_state の値は本パイプラインで実測から生じた分類をそのまま使う（新語を発明しない）:
  LIVE_WIRED                live entrypoint から到達する
  TEST_ONLY_ISLAND          実装済みだが importer がテストのみ
  IMPLEMENTED_UNWIRED       実装済みだが importer が無い
  UNBOUND_NOT_DETERMINABLE  ITEM にファイルが束縛できず判定不能（U10）
"""
import json, sys
from pathlib import Path

S = Path("/home/takasan/egl/structure")
REG = Path("/home/takasan/twoder/audit/ROADMAP_REGISTRY.jsonl")
TS = "2026-07-22T04:00:00+09:00"
AMEND_ID = "AMEND-2DER-DONE-SEMANTICS-v1"

rows = [json.loads(l) for l in REG.read_text().splitlines() if l.strip()]
ladder = {r["item_id"]: r for r in map(json.loads, open(S / "ITEM_LADDER.jsonl"))}
contra = {r["subject"]: r for r in map(json.loads, open(S / "CONTRADICTIONS.jsonl"))
          if r.get("type") == "ROADMAP_DONE_BUT_NOT_WIRED"}

if any(r.get("amendment_id") == AMEND_ID for r in rows):
    sys.exit("already applied — ROADMAP_REGISTRY already carries %s" % AMEND_ID)

# latest-wins で ITEM を解決
latest = {}
for r in rows:
    if r.get("kind") == "ITEM" and r.get("item_id"):
        latest[r["item_id"]] = r
done = {k: v for k, v in latest.items() if v.get("status") == "DONE"}


def classify(item_id):
    """5 状態ラダーと矛盾台帳からの機械的写像。判断を挟まない。"""
    lad = ladder.get(item_id)
    if lad is None:
        return "UNBOUND_NOT_DETERMINABLE", [], "no ITEM_LADDER row"
    w = lad["ladder"]["wired"]
    files = lad.get("bound_files") or []
    if w == "YES":
        return "LIVE_WIRED", lad.get("wired_files") or [], "ladder.wired=YES"
    if w.startswith("UNRESOLVED"):
        return "UNBOUND_NOT_DETERMINABLE", files, "ladder.wired=%s" % w
    c = contra.get(item_id)
    if c is None:
        return "IMPLEMENTED_UNWIRED", files, "ladder.wired=NO, no contradiction row"
    imp = "importers=[" in (c.get("detail") or "")
    return ("TEST_ONLY_ISLAND" if imp else "IMPLEMENTED_UNWIRED"), c.get("evidence") or files, c["detail"]


out, tally = [], {}
for item_id, row in sorted(done.items()):
    state, ev, basis = classify(item_id)
    tally[state] = tally.get(state, 0) + 1
    new = dict(row)  # verbatim copy — status を含め既存フィールドは変更しない
    new["registered_at"] = TS
    new["wiring_state"] = state
    new["wiring_evidence"] = ev
    new["wiring_basis"] = basis
    new["wiring_derived_from"] = "egl/structure/ITEM_LADDER.jsonl + CONTRADICTIONS.jsonl (T3_DERIVED, regenerable)"
    new["amendment_ref"] = AMEND_ID
    out.append(new)

amend = {
    "kind": "AMENDMENT", "amendment_id": AMEND_ID,
    "roadmap_id": "ROADMAP-2DER-EVOLUTION-v0.1",
    "title": "DONE の意味を確定し、加算列 wiring_state を導入（status は不変）",
    "status": "ACCEPTED", "registered_at": TS,
    "amendment_type": "DEFINITION",
    "definition_of_done": ("status=DONE は『当該 ITEM の成果物が存在し、その受入条件（acceptance）を"
                           "満たしたことが記録されている』ことのみを意味する。**live path への接続を意味しない。**"
                           "接続の有無は加算列 wiring_state が持つ。"),
    "does_not_mean": ["live path に接続されている", "本番で実行された", "proven である（CDEF-2DER-v1 参照）"],
    "new_field": "wiring_state ∈ {LIVE_WIRED, TEST_ONLY_ISLAND, IMPLEMENTED_UNWIRED, UNBOUND_NOT_DETERMINABLE}",
    "status_unchanged_reason": ("task_selector.EXCLUDED_STATUSES と roadmap_registry.is_blocked() が "
                                "status==DONE に依存しているため、status の書換えは live な選択・依存解決の"
                                "挙動変更になる。よって加算列で表現し、既存行は 1 バイトも変更しない。"),
    "applies_to": "status=DONE の全 ITEM（%d 件）" % len(out),
    "tally": tally,
    "recorded_in": "DE-0488",
    "derived_from": "egl/structure/ITEM_LADDER.jsonl + CONTRADICTIONS.jsonl",
    "trust_tier": "T3_DERIVED", "regenerable": True,
    "claim_ceiling": "DONE_SEMANTICS_FIXED_NO_BEHAVIOR_CHANGE",
}

if "--apply" not in sys.argv:
    print("DRY RUN — DONE %d 件" % len(out))
    for k, v in sorted(tally.items(), key=lambda x: -x[1]):
        print("  %-26s %d" % (k, v))
    sys.exit(0)

with REG.open("a") as f:
    f.write(json.dumps(amend, ensure_ascii=False) + "\n")
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("appended %d rows (1 AMENDMENT + %d ITEM)" % (len(out) + 1, len(out)))
for k, v in sorted(tally.items(), key=lambda x: -x[1]):
    print("  %-26s %d" % (k, v))
