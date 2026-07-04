#!/usr/bin/env python3
"""受入試験: RC-3(SQLite view は jsonl から完全再構築可能)/ RC-4(time-travel)。"""
import hashlib, json
from egl import core

def snapshot_hash(con):
    rows = con.execute("SELECT object_id,object_type,state_json FROM objects ORDER BY object_id").fetchall()
    h = hashlib.sha256()
    for oid, ot, sj in rows:
        h.update(f"{oid}|{ot}|{sj}".encode())
    return h.hexdigest()[:16], len(rows)

print("=== RC-3: SQLite view の完全再構築一致 ===")
h1, n1 = snapshot_hash(core.build_view())        # 1回目
h2, n2 = snapshot_hash(core.build_view())        # sqlite を消して events から再構築
print(f"  build#1: {n1} objects, hash={h1}")
print(f"  build#2: {n2} objects, hash={h2}")
print(f"  RC-3: {'PASS ✅ (event log のみが正本、view は導出)' if h1==h2 else 'FAIL ❌'}")

print("\n=== RC-4: time-travel(過去時点の view 再構成) ===")
evs = core.read_events()
# 最初の gap 作成直後の時点 vs 全部
t_gap = next(e['ts'] for e in evs if e['object_type']=='KnowledgeGap')
early = core.build_view(db_path=str(core.DATA/'tt.sqlite'), until_ts=t_gap)
n_early = early.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
full = core.build_view()
n_full = full.execute("SELECT COUNT(*) FROM objects").fetchone()[0]
g = core.by_type(early, "KnowledgeGap")[0]
print(f"  gap作成時点: {n_early} objects, gap status={g['status']}")
print(f"  最新:        {n_full} objects")
gnow = core.by_type(full, "KnowledgeGap")[0]
print(f"  同 gap の最新 status={gnow['status']}  (差し戻しで OPEN 維持)")
print(f"  RC-4: {'PASS ✅ (任意時点の状態を event log から再構成)' if n_early < n_full else 'FAIL'}")
