#!/usr/bin/env python3
"""s_account_axes — RTHREAD 2b-r2: TOPIC 軸の catch-all 裁定 → 凍結(Frozenset) + 多重所属 + 濃淡。

2b-r1(s_embed_axes) の TOPIC 軸を入力に、各軸が本物の話題軸(COHERENT)か寄せ場(CATCH_ALL)かを
**silhouette vs sub-silhouette** で決定論裁定し、COHERENT のみ versioned Frozenset ACCOUNT_AXES_v1 に凍結。
各問いに軸ごとの density(cosine)を出す(多重所属可・全軸閾値未満=その他)。density は observed のみで gate しない(T26)。

CPU のみ・LLM 不使用・:8005/GPU 不使用・決定論(埋め込みは s_embed_axes の pin を継承・.npy は derived 非commit)。

usage:
  s_account_axes.py          # 裁定→凍結→membership 生成
  s_account_axes.py --check  # byte一致再生成 + 凍結不変 + 負の制御 load-bearing
"""
import hashlib
import json
import os
import sys

import numpy as np

import s_embed_axes as R   # 埋め込み/records/kmeans/shuffle を継承(同一 pin=決定論)

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT_AXES = os.path.join(STRUCT, "ACCOUNT_AXES_v1.json")
OUT_MEMB = os.path.join(STRUCT, "ACCOUNT_MEMBERSHIP.jsonl")
K = 4                       # r1 の採用 K
VERSION = "v1"
PURITY_TH, DIV_TH = R.PURITY_TH, R.DIV_TH
# membership は負の制御相対(density - null > R.MARGIN)。絶対 cosine 閾値(旧 MEMB_TH)は撤廃
# (e5 anisotropy で全ベクトルが高 cosine=絶対閾値は退化。裁定A: 幻覚的絶対定数の禁止)。


def _dist2(X, Y):
    return np.maximum(0.0, (X * X).sum(1)[:, None] - 2.0 * (X @ Y.T) + (Y * Y).sum(1)[None, :])


def _silhouette_samples(X, labels):
    D = np.sqrt(_dist2(X, X))
    uniq = np.unique(labels)
    sil = np.zeros(len(X))
    for i in range(len(X)):
        same = labels == labels[i]
        n_same = int(same.sum())
        a = (D[i, same].sum() / (n_same - 1)) if n_same > 1 else 0.0
        others = [D[i, labels == c].mean() for c in uniq if c != labels[i]]
        b = min(others) if others else 0.0
        sil[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0
    return sil


def _axis_silhouette(X, labels, j):
    m = labels == j
    return float(_silhouette_samples(X, labels)[m].mean()) if m.any() else 0.0


def _sub_silhouette(Xsub):
    if len(Xsub) < 4:
        return 0.0
    sub = R._kmeans(Xsub, 2, 0)
    if len(np.unique(sub)) < 2:
        return 0.0
    return float(_silhouette_samples(Xsub, sub).mean())


def _r1_topic_axes(recs, X, labels):
    """r1 の F-B ガード(purity+diversity)で TOPIC 軸を再現。"""
    topic = []
    for j in range(K):
        idx = [i for i in range(len(recs)) if labels[i] == j]
        if not idx:
            continue
        kinds = [recs[i][1] for i in idx]
        purity = max(kinds.count(k) for k in set(kinds)) / len(idx)
        diversity = len({recs[i][2] for i in idx}) / len(idx)
        if not (purity >= PURITY_TH and diversity < DIV_TH):   # RESIDUAL でない=TOPIC
            topic.append((j, idx, round(purity, 4), round(diversity, 4)))
    return topic


def _adjudicate(X, labels, topic):
    """§2: 各 TOPIC 軸に silhouette と sub_silhouette。sub>=sil なら CATCH_ALL(降格)。"""
    sil_all = _silhouette_samples(X, labels)
    out = []
    for j, idx, purity, diversity in topic:
        sil = float(sil_all[np.array(idx)].mean())
        sub = _sub_silhouette(X[np.array(idx)])
        verdict = "CATCH_ALL" if sub >= sil else "COHERENT"
        out.append({"cluster": j, "idx": idx, "kind_purity": purity, "content_diversity": diversity,
                    "silhouette": round(sil, 6), "sub_silhouette": round(sub, 6),
                    "catch_all_verdict": verdict})
    return out


def _neg_silhouette(X, labels):
    """負の制御: 列 shuffle で silhouette が chance(~0)へ崩れるか(load-bearing)。"""
    Xn = R._shuffle_features(X)
    return float(_silhouette_samples(Xn, labels).mean())


def _null_density(X, dirs):
    """anisotropy 由来の density 下限 = 列 shuffle した埋め込みの各軸への平均 cosine(軸ごとスカラー)。"""
    dirs = np.asarray(dirs)
    if not len(dirs):
        return np.zeros(0)
    return (R._shuffle_features(X) @ dirs.T).mean(0)


def assign_membership(X, dirs, null=None):
    """membership を負の制御相対に。所属条件 = density_a(e) - null_a > R.MARGIN(絶対 cosine 閾値なし)。
    多重所属可・全軸未達=その他。返り: (hits[[axis_idx]], dens[np.array], null[np.array])。
    2b-r3 の v2 re-membership も本関数を共有(A.MEMB_TH 依存を廃す)。"""
    dirs = np.asarray(dirs)
    if not len(dirs):
        return [[] for _ in range(len(X))], [np.zeros(0) for _ in range(len(X))], np.zeros(0)
    if null is None:
        null = _null_density(X, dirs)
    D = X @ dirs.T
    hits = [[a for a in range(len(dirs)) if (D[i, a] - null[a]) > R.MARGIN] for i in range(len(X))]
    return hits, [D[i] for i in range(len(X))], null


def build():
    recs = R._content_records()
    X = R._load_vectors(recs)
    labels = R._kmeans(X, K, 0)
    topic = _r1_topic_axes(recs, X, labels)
    adj = _adjudicate(X, labels, topic)
    neg_sil = _neg_silhouette(X, labels)
    real_sil = float(_silhouette_samples(X, labels).mean())

    frozen = []
    for a in adj:
        if a["catch_all_verdict"] != "COHERENT":
            continue
        idx = np.array(a["idx"])
        members = sorted(recs[i][0] for i in a["idx"])
        centroid = X[idx].mean(0)
        n = np.linalg.norm(centroid)
        direction = (centroid / n) if n > 0 else centroid
        frozen.append({
            "axis_id": "AX-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8],
            "version": VERSION,
            "frozen_direction": [round(float(v), 6) for v in direction],
            "kind_verdict": "TOPIC",
            "catch_all_verdict": a["catch_all_verdict"],
            "seed_member_ids": members[:10],
            "n_members_r1": len(members),
            "silhouette": a["silhouette"], "sub_silhouette": a["sub_silhouette"],
        })
    frozen.sort(key=lambda f: f["axis_id"])

    dirs = np.array([f["frozen_direction"] for f in frozen]) if frozen else np.zeros((0, X.shape[1]))
    null = _null_density(X, dirs)
    axes_doc = {
        "version": VERSION,
        "model": R.MODEL, "revision": R.REVISION,
        "n_frozen_axes": len(frozen),
        "membership_rule": "density_a(e) - null_a > R.MARGIN (負の制御相対・絶対 cosine 閾値なし)",
        "membership_margin": R.MARGIN,
        "membership_null_per_axis": {frozen[a]["axis_id"]: round(float(null[a]), 6) for a in range(len(frozen))},
        "real_mean_silhouette": round(real_sil, 6),
        "neg_control_mean_silhouette": round(neg_sil, 6),
        "per_axis_adjudication": [{k: a[k] for k in
                                   ("kind_purity", "content_diversity", "silhouette",
                                    "sub_silhouette", "catch_all_verdict")} for a in adj],
        "axes": frozen,
        "note": ("catch-all 裁定(sub_silhouette>=silhouette=CATCH_ALL 降格)で COHERENT %d 軸のみ凍結。"
                 "density は observed のみで gate しない(T26)。account 次元は soft(保存則なし)。" % len(frozen)),
    }

    # §4: membership(多重所属可・全軸未達=その他)。相対所属 density_a-null_a>R.MARGIN(anisotropy 底上げを null で相殺)。
    memb = []
    hits, dens_list, _ = assign_membership(X, dirs, null=null)
    for i, (nid, kind, _) in enumerate(recs):
        dens = dens_list[i]
        axes_hit = [{"axis_id": frozen[a]["axis_id"], "density": round(float(dens[a]), 6),
                     "margin_over_null": round(float(dens[a] - null[a]), 6)} for a in hits[i]]
        rec = {"element_id": nid, "kind": kind,
               "axes": sorted(axes_hit, key=lambda x: (-x["margin_over_null"], x["axis_id"])),
               "unclassified": len(axes_hit) == 0,
               "all_densities": {frozen[a]["axis_id"]: round(float(dens[a]), 6) for a in range(len(frozen))}}
        memb.append(rec)
    # membership 相対性(陰性対照): shuffle 埋め込みで再割当 → anisotropy 底上げが null で相殺され所属が崩壊
    hits_shuf, _, _ = assign_membership(R._shuffle_features(X), dirs)
    axes_doc["membership_real_assigned"] = int(sum(1 for m in memb if not m["unclassified"]))
    axes_doc["membership_other_count"] = int(sum(1 for m in memb if m["unclassified"]))
    axes_doc["membership_shuffle_assigned"] = int(sum(1 for h in hits_shuf if h))
    return axes_doc, memb


def _ser_axes(d):
    return json.dumps(d, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _ser_memb(memb):
    return "".join(json.dumps(m, sort_keys=True, ensure_ascii=False) + "\n" for m in memb)


def main(argv):
    axes_doc, memb = build()
    at, mt = _ser_axes(axes_doc), _ser_memb(memb)
    if "--check" in argv:
        red = []
        if not os.path.isfile(OUT_AXES) or open(OUT_AXES, encoding="utf-8").read() != at:
            red.append("REGEN_MISMATCH: ACCOUNT_AXES_v1.json (freeze drift or non-deterministic)")
        if not os.path.isfile(OUT_MEMB) or open(OUT_MEMB, encoding="utf-8").read() != mt:
            red.append("REGEN_MISMATCH: ACCOUNT_MEMBERSHIP.jsonl")
        # 負の制御 load-bearing: real silhouette が負の制御を上回る(shuffle で崩壊)
        if axes_doc["real_mean_silhouette"] <= axes_doc["neg_control_mean_silhouette"]:
            red.append("NEGATIVE_CONTROL_FAILED: shuffle silhouette >= real (not load-bearing)")
        # membership 相対性(陰性対照 load-bearing): shuffle 埋め込みでは所属が崩壊(anisotropy 底上げでなく真の近さを測る証拠)
        if axes_doc["n_frozen_axes"] > 0 and \
                axes_doc["membership_shuffle_assigned"] >= axes_doc["membership_real_assigned"]:
            red.append("MEMBERSHIP_NEG_CONTROL_FAILED: shuffled assigned(%d) >= real(%d) (絶対底上げを測っている)"
                       % (axes_doc["membership_shuffle_assigned"], axes_doc["membership_real_assigned"]))
        # 絶対 cosine 閾値定数ゼロ(裁定A): MEMB_TH 等が再導入されていないこと
        if "MEMB_TH" in globals():
            red.append("ABSOLUTE_CONSTANT_PRESENT: MEMB_TH re-introduced (membership must be neg-control relative)")
        if red:
            print("ACCOUNT_AXES --check: RED")
            for m in red:
                print("  " + m)
            return 1
        print("ACCOUNT_AXES --check: GREEN (byte-identical; frozen=%d; real_sil=%.4f neg_sil=%.4f; "
              "membership real_assigned=%d その他=%d shuffle_assigned=%d; neg load-bearing)"
              % (axes_doc["n_frozen_axes"], axes_doc["real_mean_silhouette"], axes_doc["neg_control_mean_silhouette"],
                 axes_doc["membership_real_assigned"], axes_doc["membership_other_count"],
                 axes_doc["membership_shuffle_assigned"]))
        return 0
    open(OUT_AXES, "w", encoding="utf-8").write(at)
    open(OUT_MEMB, "w", encoding="utf-8").write(mt)
    unclf = sum(1 for m in memb if m["unclassified"])
    print("frozen_axes=%d (real_sil=%.4f neg_sil=%.4f) | membership: %d elements, その他=%d"
          % (axes_doc["n_frozen_axes"], axes_doc["real_mean_silhouette"],
             axes_doc["neg_control_mean_silhouette"], len(memb), unclf))
    for a in axes_doc["per_axis_adjudication"]:
        print("  sil=%.3f sub=%.3f -> %s (purity=%.2f div=%.3f)"
              % (a["silhouette"], a["sub_silhouette"], a["catch_all_verdict"], a["kind_purity"], a["content_diversity"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
