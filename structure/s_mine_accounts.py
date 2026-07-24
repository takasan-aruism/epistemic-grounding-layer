#!/usr/bin/env python3
"""s_mine_accounts — chart of accounts の決定論マイニング(RTHREAD stage 2b-1 / MINING_SPEC v0.1)。

「account を発明しない」の本体。DE ledger + rri_records を **決定論クラスタリング**し、
**安定 chart が在るかを測定**する(第一目的は chart 生成でなく安定性測定)。
LLM 不使用・決定論・byte一致再生成。prose は素性にしない(§1)。負の制御が load-bearing の核(§3)。

出口: 実 cross-seed agreement が負の制御(素性 shuffle ノイズ)を明確に上回らなければ
chart_status=NO_STABLE_STRUCTURE を記録し **chart を捏造しない**(正当な結論)。

usage:
  s_mine_accounts.py          # 再生成(ACCOUNT_CHART_CANDIDATE.jsonl + ACCOUNT_CHART_STABILITY.json)
  s_mine_accounts.py --check  # 常設ゲート(byte一致 + 負の制御 load-bearing = 実 > ノイズ)
"""
import hashlib
import json
import os
import re
import sys

import numpy as np

ROOT = "/home/takasan"
DE_LEDGER = os.path.join(ROOT, "egl", "DESIGN_EVIDENCE_LEDGER.jsonl")
RRI_RECORDS = os.path.join(ROOT, "rri", "rri_records.jsonl")
STRUCT = os.path.join(ROOT, "egl", "structure")
OUT_CAND = os.path.join(STRUCT, "ACCOUNT_CHART_CANDIDATE.jsonl")
OUT_STAB = os.path.join(STRUCT, "ACCOUNT_CHART_STABILITY.json")

ID_RX = re.compile(r"\b(?:DE|RREQ|RINT|RSIG|UTT|DEV|ADM)-\d+")
BANDS = ("OBSERVED", "IMPLEMENTED", "LIVE", "MEASURED", "PROPOSED", "PROVISIONAL", "REPORTED", "NONE", "OTHER")
KINDS = ("DE", "REQUEST", "INTENT", "RESEARCH_SIGNAL", "OTHER")
K_SWEEP = (4, 6, 8, 10)
SEEDS = (0, 1, 2, 3, 4)

W_COOC, W_BAND, W_KIND = 1.0, 0.5, 0.2   # cooc 主・band 中・kind 低(§1: 支配させない)


def _band(status):
    s = (status or "NONE")
    return s if s in BANDS else "OTHER"


def _load_records():
    """node = (node_id, kind, band, ref_ids set)。DE 517 + rri 698。prose は使わない。"""
    recs = []
    for line in open(DE_LEDGER, encoding="utf-8"):
        d = json.loads(line)
        nid = d.get("design_evidence_id") or ("DE?" + str(len(recs)))
        refs = set(ID_RX.findall(json.dumps(d, ensure_ascii=False)))
        refs.discard(nid)
        recs.append((nid, "DE", _band(d.get("claimed_status")), refs))
    for line in open(RRI_RECORDS, encoding="utf-8"):
        r = json.loads(line)
        nid = r.get("rri_record_id") or ("RRI?" + str(len(recs)))
        kind = r.get("kind") if r.get("kind") in KINDS else "OTHER"
        refs = set(ID_RX.findall(json.dumps(r, ensure_ascii=False)))
        refs.discard(nid)
        recs.append((nid, kind, "OTHER", refs))
    return recs


def _feature_matrix(recs):
    """cooc multi-hot(参照 ID 宇宙) + band one-hot + kind one-hot。determinism: 語彙は辞書順固定。"""
    id_universe = sorted({rid for _, _, _, refs in recs for rid in refs})
    id_ix = {rid: i for i, rid in enumerate(id_universe)}
    n, d_cooc = len(recs), len(id_universe)
    X = np.zeros((n, d_cooc + len(BANDS) + len(KINDS)), dtype=np.float64)
    for i, (_, kind, band, refs) in enumerate(recs):
        for rid in refs:
            X[i, id_ix[rid]] = W_COOC
        X[i, d_cooc + BANDS.index(band)] = W_BAND
        X[i, d_cooc + len(BANDS) + KINDS.index(kind)] = W_KIND
    return X


def _kmeans(X, k, seed, iters=60):
    """決定論 k-means。init=seed 由来の permutation で k 行を中心に。assign=argmin(tie は最小index=辞書順)。"""
    rng = np.random.default_rng(seed)
    C = X[rng.permutation(len(X))[:k]].copy()
    labels = np.zeros(len(X), dtype=np.int64)
    for _ in range(iters):
        # 距離^2 = ||x||^2 - 2 x·C + ||C||^2 ; argmin は同値時に最小 index を返す(辞書順 tie-break)
        d = (X * X).sum(1)[:, None] - 2.0 * (X @ C.T) + (C * C).sum(1)[None, :]
        new = d.argmin(1)
        if np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            m = labels == j
            if m.any():
                C[j] = X[m].mean(0)
    return labels


def _adjusted_rand(a, b):
    """Adjusted Rand Index(chance 補正)。乱ラベリングは ~0、完全一致は 1。
    raw Rand は K 大で true-negative ペアが支配し膨張する(vacuous)→ ARI で chance を除く。"""
    ua, ia = np.unique(a, return_inverse=True)
    ub, ib = np.unique(b, return_inverse=True)
    cont = np.zeros((len(ua), len(ub)), dtype=np.int64)
    np.add.at(cont, (ia, ib), 1)
    c2 = lambda x: x.astype(np.int64) * (x - 1) // 2
    sum_ij = int(c2(cont).sum())
    sum_a = int(c2(cont.sum(1)).sum())
    sum_b = int(c2(cont.sum(0)).sum())
    total = len(a) * (len(a) - 1) // 2
    expected = (sum_a * sum_b / total) if total else 0.0
    maxi = (sum_a + sum_b) / 2.0
    denom = maxi - expected
    return float((sum_ij - expected) / denom) if denom else 1.0


def _cross_seed_agreement(X, k):
    labs = [_kmeans(X, k, s) for s in SEEDS]
    vals = [_adjusted_rand(labs[i], labs[j]) for i in range(len(labs)) for j in range(i + 1, len(labs))]
    return float(np.mean(vals)), labs[0]


def _shuffle_features(X, seed=12345):
    """負の制御: 各素性列を独立に固定 seed で置換(相関/構造を壊し marginal は保つ)。"""
    rng = np.random.default_rng(seed)
    Xs = X.copy()
    for c in range(Xs.shape[1]):
        Xs[:, c] = Xs[rng.permutation(Xs.shape[0]), c]
    return Xs


MARGIN = 0.05   # 実 agreement が負の制御を明確に上回る最小差(甘くしない)


def mine():
    recs = _load_records()
    X = _feature_matrix(recs)
    Xn = _shuffle_features(X)
    real_by_k, neg_by_k, lab0_by_k = {}, {}, {}
    for k in K_SWEEP:
        real_by_k[k], lab0_by_k[k] = _cross_seed_agreement(X, k)
        neg_by_k[k], _ = _cross_seed_agreement(Xn, k)
    # 安定性最大の K(実 agreement) を採用(K も勝手に決めない=測る)
    K = max(K_SWEEP, key=lambda k: real_by_k[k])
    real, neg = real_by_k[K], neg_by_k[K]
    # 自明分割ガード: クラスタが record-kind(DE/REQUEST/INTENT/RESEARCH_SIGNAL) 分割に一致するなら
    # それは「account」でなく記録種別の自明構造 → chart でない(想像で account を捏造しない)。
    kind_labels = np.array([KINDS.index(recs[i][1]) if recs[i][1] in KINDS else len(KINDS)
                            for i in range(len(recs))])
    kind_align = _adjusted_rand(lab0_by_k[K], kind_labels)
    TRIVIAL = 0.5   # クラスタ vs record-kind の ARI がこれ以上 = 自明種別分割
    stable = (real - neg) >= MARGIN and real > neg and kind_align < TRIVIAL
    status = "STABLE_CANDIDATE" if stable else "NO_STABLE_STRUCTURE"

    stab = {
        "chart_status": status,
        "chosen_K": K,
        "margin_required": MARGIN,
        "real_agreement_by_K": {str(k): round(real_by_k[k], 6) for k in K_SWEEP},
        "neg_control_agreement_by_K": {str(k): round(neg_by_k[k], 6) for k in K_SWEEP},
        "real_minus_neg_at_K": round(real - neg, 6),
        "cluster_vs_record_kind_ARI_at_K": round(kind_align, 6),
        "trivial_kind_threshold": TRIVIAL,
        "n_records": len(recs),
        "n_features": int(X.shape[1]),
        "seeds": list(SEEDS),
        "note": (("NO_STABLE_STRUCTURE: 唯一安定な構造が record-kind の自明分割(cluster vs kind ARI=%.3f>=%.2f)であり、"
                  "意味ある account トポロジは無い。決定論素性(cooc/band)は種別しか復元しない=§0 の予想どおり。"
                  "chart を捏造しない(初版 rejected_alternative の回避)。命名(2b-2)へ進まない。" % (kind_align, TRIVIAL))
                 if kind_align >= TRIVIAL else
                 ("NO_STABLE_STRUCTURE: 実 agreement が負の制御を明確に上回らない。chart を捏造しない。"
                  if not stable else "安定クラスタ候補あり(record-kind でない)。命名(2b-2)へは別スライスで進む")),
    }

    # candidates: STABLE の時のみ出す(捏造しない)。NO_STABLE は空(header 行のみ)。
    cands = []
    if stable:
        labels = lab0_by_k[K]
        for j in range(K):
            members = sorted(recs[i][0] for i in range(len(recs)) if labels[i] == j)
            if not members:
                continue
            cid = "ACCT-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8]
            # top_features: メンバに多い band/kind(prose でない)
            bands = {}
            for i in range(len(recs)):
                if labels[i] == j:
                    bands[recs[i][2]] = bands.get(recs[i][2], 0) + 1
            top = sorted(bands.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
            cands.append({"cluster_id": cid, "members": members,
                          "top_features": [f"band:{b}={c}" for b, c in top], "name": None})
    return stab, cands


def _serialize_cands(cands):
    hdr = {"_meta": "ACCOUNT_CHART_CANDIDATE (name=null; 命名は 2b-2・安定時のみ)。空=NO_STABLE_STRUCTURE"}
    lines = [json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps(c, sort_keys=True, ensure_ascii=False) for c in cands]
    return "\n".join(lines) + "\n"


def main(argv):
    stab, cands = mine()
    cand_txt = _serialize_cands(cands)
    stab_txt = json.dumps(stab, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if "--check" in argv:
        red = []
        if not os.path.isfile(OUT_CAND) or open(OUT_CAND, encoding="utf-8").read() != cand_txt:
            red.append("REGEN_MISMATCH: ACCOUNT_CHART_CANDIDATE.jsonl not byte-identical")
        if not os.path.isfile(OUT_STAB) or open(OUT_STAB, encoding="utf-8").read() != stab_txt:
            red.append("REGEN_MISMATCH: ACCOUNT_CHART_STABILITY.json not byte-identical")
        # 負の制御 load-bearing: 実データ agreement が全 K でノイズを下回ってはならない
        # (下回る=miner がノイズに実より自信=vacuous)。採用 K で実 <= ノイズ なら RED。
        if stab["real_minus_neg_at_K"] < 0:
            red.append("NEGATIVE_CONTROL_FAILED: noise agreement >= real at chosen K (miner vacuous)")
        if red:
            print("MINE --check: RED")
            for m in red:
                print("  " + m)
            return 1
        print("MINE --check: GREEN (byte-identical; chart_status=%s; real-neg@K=%.4f; negative-control load-bearing)"
              % (stab["chart_status"], stab["real_minus_neg_at_K"]))
        return 0
    with open(OUT_CAND, "w", encoding="utf-8") as fh:
        fh.write(cand_txt)
    with open(OUT_STAB, "w", encoding="utf-8") as fh:
        fh.write(stab_txt)
    print("chart_status=%s chosen_K=%d real@K=%.4f neg@K=%.4f (records=%d features=%d)"
          % (stab["chart_status"], stab["chosen_K"],
             stab["real_agreement_by_K"][str(stab["chosen_K"])],
             stab["neg_control_agreement_by_K"][str(stab["chosen_K"])],
             stab["n_records"], stab["n_features"]))
    print("candidates written:", len(cands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
