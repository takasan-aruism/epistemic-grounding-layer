#!/usr/bin/env python3
"""s_embed_axes — 意味埋め込みで安定な離散軸(科目候補)が出るかの経験的テスト(RTHREAD 2b-r1 / EMBED_AXES v0.1)。

CPU 意味埋め込み(intfloat/multilingual-e5-small, pin)で内容テキストをベクトル化し、
**安定軸が実在するか**を負の制御付きで測る。構造素性は NO_STABLE(DE-0521, record-kind の自明分割のみ)。
本テストの問い=「内容の意味なら話題軸が出るか」。measure-first: 出なければ NO_STABLE_AXES(正当な結果)。

CPU のみ・:8005/GPU/スリープ不使用・density は gate しない(T26)。LLM 不使用。

usage:
  s_embed_axes.py          # 埋め込み→軸抽出→安定性測定(出力2ファイル)
  s_embed_axes.py --check  # byte一致再生成 + 負の制御 load-bearing
"""
import hashlib
import json
import os
import sys

import numpy as np

ROOT = "/home/takasan"
DE_LEDGER = os.path.join(ROOT, "egl", "DESIGN_EVIDENCE_LEDGER.jsonl")
RRI_RECORDS = os.path.join(ROOT, "rri", "rri_records.jsonl")
STRUCT = os.path.join(ROOT, "egl", "structure")
OUT_STAB = os.path.join(STRUCT, "EMBED_AXES_STABILITY.json")
OUT_CAND = os.path.join(STRUCT, "EMBED_AXES_CANDIDATE.jsonl")
EMB_CACHE = os.path.join(STRUCT, ".embed_axes_vectors.npy")   # 決定論 artifact(再 DL/再埋め込み回避)

MODEL = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"   # F-A: commit pin(可変 main を廃し再現性 robust)
PURITY_TH = 0.85                  # F-B: 個別軸 kind 純度がこれ以上 かつ 低多様性 = RESIDUAL(topic でない)
DIV_TH = 0.30                     # F-B: content 多様性(相異 text / メンバ数)がこれ未満 = 退化(collapse)
KINDS = ("DE", "REQUEST", "INTENT")
K_SWEEP = (4, 6, 8, 10, 12)
SEEDS = (0, 1, 2, 3, 4)
MARGIN = 0.05
TRIVIAL = 0.5


def _content_records():
    """内容テキストのみ(ID/封印は含めない)。DE=observation+decision / REQUEST=content.raw / INTENT=content.resolved。"""
    recs = []
    for line in open(DE_LEDGER, encoding="utf-8"):
        d = json.loads(line)
        txt = " ".join(str(d.get(k, "")) for k in ("observation", "decision")).strip()
        recs.append((d.get("design_evidence_id") or ("DE?%d" % len(recs)), "DE", txt))
    for line in open(RRI_RECORDS, encoding="utf-8"):
        r = json.loads(line)
        kind, c = r.get("kind"), (r.get("content") or {})
        if kind == "REQUEST":
            # REQUEST の content は異種: raw_input(153)/t(45)/task(13)/raw(1)。全て内容テキスト。
            txt = c.get("raw_input") or c.get("raw") or c.get("t") or c.get("task") or ""
            recs.append((r.get("rri_record_id"), "REQUEST", str(txt).strip()))
        elif kind == "INTENT":
            recs.append((r.get("rri_record_id"), "INTENT", str(c.get("resolved", "")).strip()))
    return [(nid, kind, txt) for nid, kind, txt in recs if txt]


def _embed(texts):
    """e5-small CPU 決定論埋め込み(passage: 接頭・mean-pool・L2)。float noise を抑えるため 6桁丸め。"""
    import sys
    # torchvision(env で InterpolationMode 欠落=版不整合)を import 段でブロック。e5 はテキスト専用で不要。
    sys.modules.setdefault("torchvision", None)
    sys.modules.setdefault("torchvision.transforms", None)
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True, warn_only=True)
    tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModel.from_pretrained(MODEL, revision=REVISION)
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 32):
            batch = ["passage: " + t for t in texts[i:i + 32]]
            enc = tok(batch, padding=True, truncation=True, max_length=256, return_tensors="pt")
            o = model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).to(o.dtype)
            emb = (o * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            out.append(emb.cpu().numpy())
    return np.round(np.vstack(out).astype(np.float64), 6)


def _resolved_commit():
    return REVISION   # F-A: commit を pin したので refetch せず固定値(再現性 robust・network 不要)


# ── clustering machinery (MINING と同一・計器教訓 ARI を継承) ──────────────────
def _kmeans(X, k, seed, iters=60):
    rng = np.random.default_rng(seed)
    C = X[rng.permutation(len(X))[:k]].copy()
    labels = np.zeros(len(X), dtype=np.int64)
    for _ in range(iters):
        d = (X * X).sum(1)[:, None] - 2.0 * (X @ C.T) + (C * C).sum(1)[None, :]
        new = d.argmin(1)                 # 同値は最小 index(辞書順 tie-break)
        if np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            m = labels == j
            if m.any():
                C[j] = X[m].mean(0)
    return labels


def _adjusted_rand(a, b):
    ua, ia = np.unique(a, return_inverse=True)
    ub, ib = np.unique(b, return_inverse=True)
    cont = np.zeros((len(ua), len(ub)), dtype=np.int64)
    np.add.at(cont, (ia, ib), 1)
    c2 = lambda x: x.astype(np.int64) * (x - 1) // 2
    sij, sa, sb = int(c2(cont).sum()), int(c2(cont.sum(1)).sum()), int(c2(cont.sum(0)).sum())
    total = len(a) * (len(a) - 1) // 2
    exp = (sa * sb / total) if total else 0.0
    denom = (sa + sb) / 2.0 - exp
    return float((sij - exp) / denom) if denom else 1.0


def _cross_seed(X, k):
    labs = [_kmeans(X, k, s) for s in SEEDS]
    vals = [_adjusted_rand(labs[i], labs[j]) for i in range(len(labs)) for j in range(i + 1, len(labs))]
    return float(np.mean(vals)), labs[0]


def _shuffle_features(X, seed=12345):
    """負の制御: 各次元を独立に固定 seed で置換(意味の joint 構造を壊す・marginal 保持)。
    ※『行 shuffle』は点集合不変で cross-seed 安定を崩さない=非 load-bearing。列(次元)shuffle が load-bearing。"""
    rng = np.random.default_rng(seed)
    Xs = X.copy()
    for c in range(Xs.shape[1]):
        Xs[:, c] = Xs[rng.permutation(Xs.shape[0]), c]
    return Xs


def _load_vectors(recs):
    texts = [t for _, _, t in recs]
    key = hashlib.sha1(("||".join(texts) + "|" + MODEL + "|" + REVISION).encode()).hexdigest()
    if os.path.isfile(EMB_CACHE):
        try:
            blob = np.load(EMB_CACHE, allow_pickle=True).item()
            if blob.get("key") == key:
                return blob["X"]
        except Exception:
            pass
    X = _embed(texts)
    np.save(EMB_CACHE, {"key": key, "X": X})
    return X


def measure():
    recs = _content_records()
    X = _load_vectors(recs)
    Xn = _shuffle_features(X)
    real_by_k, neg_by_k, lab0 = {}, {}, {}
    for k in K_SWEEP:
        real_by_k[k], lab0[k] = _cross_seed(X, k)
        neg_by_k[k], _ = _cross_seed(Xn, k)
    K = max(K_SWEEP, key=lambda k: real_by_k[k])
    real, neg = real_by_k[K], neg_by_k[K]
    labels = lab0[K]
    kind_lab = np.array([KINDS.index(recs[i][1]) for i in range(len(recs))])
    kind_align = _adjusted_rand(labels, kind_lab)

    # F-B: 個別軸の自明性ガード(集約 kind_align では INTENT-pure collapse を見逃す)。
    # 単一種別寄り(purity>=0.85) かつ 低 content 多様性(相異 text/メンバ<0.30) の軸は topic でない=RESIDUAL。
    per_axis, topic_axes = [], []
    for j in range(K):
        idx = [i for i in range(len(recs)) if labels[i] == j]
        if not idx:
            continue
        members = sorted(recs[i][0] for i in idx)
        kinds = [recs[i][1] for i in idx]
        purity = max(kinds.count(k) for k in set(kinds)) / len(idx)
        diversity = len({recs[i][2] for i in idx}) / len(idx)
        verdict = "RESIDUAL" if (purity >= PURITY_TH and diversity < DIV_TH) else "TOPIC"
        aid = "AX-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8]
        per_axis.append({"axis_id": aid, "n": len(idx), "kind_purity": round(purity, 4),
                         "content_diversity": round(diversity, 4), "verdict": verdict})
        if verdict == "TOPIC":
            topic_axes.append((aid, members))
    per_axis.sort(key=lambda r: (r["verdict"] != "TOPIC", -r["n"]))
    n_topic = len(topic_axes)

    # 安定(負の制御) かつ TOPIC 軸が1つ以上(個別ガード) なら AXES_FOUND。全て RESIDUAL なら NO_STABLE。
    found = (real - neg) >= MARGIN and real > neg and n_topic >= 1
    status = "AXES_FOUND" if found else "NO_STABLE_AXES"

    stab = {
        "chart_status": status,
        "n_topic_axes": n_topic,
        "chosen_K": K,
        "real_ari_by_K": {str(k): round(real_by_k[k], 6) for k in K_SWEEP},
        "neg_control_ari_by_K": {str(k): round(neg_by_k[k], 6) for k in K_SWEEP},
        "real_minus_neg_at_K": round(real - neg, 6),
        "cluster_vs_record_kind_ARI_at_K": round(kind_align, 6),
        "per_axis": per_axis,
        "margin_required": MARGIN, "trivial_kind_threshold": TRIVIAL,
        "purity_threshold": PURITY_TH, "diversity_threshold": DIV_TH,
        "n_records": len(recs), "embed_dim": int(X.shape[1]),
        "model": MODEL, "revision": REVISION, "resolved_commit": _resolved_commit(),
        "seeds": list(SEEDS),
        "compare_structural": "structural features = NO_STABLE (DE-0521, record-kind trivial). "
                              "本テスト=意味埋め込みで話題軸が出るか。",
        "note": (("AXES_FOUND: TOPIC 軸 %d 個(個別ガード通過・cross-kind topic)。残りは RESIDUAL/その他"
                  "(単一種別 collapse=INTENT resolved 退化など)。2b-r2 で TOPIC 軸のみ凍結+多重所属+濃淡へ。"
                  % n_topic)
                 if found else
                 "NO_STABLE_AXES: 全軸が RESIDUAL(単一種別 collapse)または real-neg margin 不足。"
                 "軸を捏造しない=正当な結果(DE-0521 と同 retention)。2b-r2 凍結へ進まない。"),
    }
    # F-B: candidate は TOPIC 軸のみ(RESIDUAL は per_axis に verdict 付きで別掲)。
    cands = [{"axis_id": aid, "members": members, "centroid_top_terms": [], "name": None}
             for aid, members in topic_axes]
    return stab, cands


def _ser_stab(s):
    return json.dumps(s, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _ser_cand(cands):
    hdr = {"_meta": "EMBED_AXES_CANDIDATE (name=null; 凍結/命名は 2b-r2・AXES_FOUND 時のみ)。空=NO_STABLE_AXES"}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(c, sort_keys=True, ensure_ascii=False) for c in cands]) + "\n"


def main(argv):
    stab, cands = measure()
    st, ct = _ser_stab(stab), _ser_cand(cands)
    if "--check" in argv:
        red = []
        if not os.path.isfile(OUT_STAB) or open(OUT_STAB, encoding="utf-8").read() != st:
            red.append("REGEN_MISMATCH: EMBED_AXES_STABILITY.json")
        if not os.path.isfile(OUT_CAND) or open(OUT_CAND, encoding="utf-8").read() != ct:
            red.append("REGEN_MISMATCH: EMBED_AXES_CANDIDATE.jsonl")
        if stab["real_minus_neg_at_K"] < 0:
            red.append("NEGATIVE_CONTROL_FAILED: noise ARI >= real (miner vacuous)")
        if red:
            print("EMBED_AXES --check: RED")
            for m in red:
                print("  " + m)
            return 1
        print("EMBED_AXES --check: GREEN (byte-identical; status=%s; real-neg@K=%.4f; kind_align=%.3f; neg load-bearing)"
              % (stab["chart_status"], stab["real_minus_neg_at_K"], stab["cluster_vs_record_kind_ARI_at_K"]))
        return 0
    open(OUT_STAB, "w", encoding="utf-8").write(st)
    open(OUT_CAND, "w", encoding="utf-8").write(ct)
    print("status=%s K=%d real@K=%.4f neg@K=%.4f kind_align=%.4f (records=%d dim=%d) candidates=%d"
          % (stab["chart_status"], stab["chosen_K"],
             stab["real_ari_by_K"][str(stab["chosen_K"])], stab["neg_control_ari_by_K"][str(stab["chosen_K"])],
             stab["cluster_vs_record_kind_ARI_at_K"], stab["n_records"], stab["embed_dim"], len(cands)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
