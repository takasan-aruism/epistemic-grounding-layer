#!/usr/bin/env python3
"""s_rthread_2br3 — RTHREAD 2b-r3: その他が濃い方向を持ったら稀に・意図的に・versioned で新軸を追加凍結する規律の機械化。

裁定A(CC_MGR 2BR3): 機械は凍結しない=候補を証拠付きで surface するだけ。実凍結の引き金は Taka 承認(versioned commit)。
絶対規律: **新しい絶対閾値定数を導入しない**。濃さ/本物判定はすべて負の制御に対する相対 margin(既存機構 R.MARGIN/R.DIV_TH の再利用)。

入力  = 2b-r2 ACCOUNT_MEMBERSHIP の その他/UNCLASSIFIED 部分集合(全軸閾値未満)。現状 v1=0軸 → その他=全 corpus。
#1 濃さ = 2b-r1 の load-bearing 相対検定を その他に適用(k-means分割→cross-seed ARI安定→列shuffleでsilhouette崩壊→候補silがshuffle marginを超える)。
#2 本物 = F-B 自明性ガード(content_diversity>DIV_TH) かつ catch-all検定(sub_silhouette<silhouette)。退化はRESIDUALへ落とし候補から除外。
#3 propose→approve = QUALIFIED を ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl に surface。機械はここで停止。
   ACCOUNT_AXES_v2.json は FREEZE_APPROVALS.jsonl に {candidate_id, approved_by:"Taka"} が在るときだけ生成(marker無しでv2=RED)。
#4 versioning = v2 は v1 を不変コピー + 承認軸のみ追加。membership は axes_version を自己記述。v1 は触らない。
#5 I1 保存則 = count(要素 in) == count(軸∪その他 で説明済み)。その他=catch-all ゆえゼロ落ちしない。

CPU のみ・LLM 不使用・:8005/GPU 不使用・決定論(埋め込みは s_embed_axes の pin `614241f6` を継承)。

usage:
  s_rthread_2br3.py          # その他→候補surface(+承認済みなら v2)
  s_rthread_2br3.py --check  # byte一致 + 候補検出/退化除外/no-auto-freeze/I1 の負の制御 load-bearing
"""
import copy
import hashlib
import json
import os
import sys

import numpy as np

import s_embed_axes as R      # records/vectors/kmeans/ARI/shuffle/cross_seed を継承(同一 pin=決定論)
import s_account_axes as A    # silhouette/sub_silhouette を継承(2b-r2 catch-all 検定)

STRUCT = os.path.dirname(os.path.abspath(__file__))
IN_MEMB = os.path.join(STRUCT, "ACCOUNT_MEMBERSHIP.jsonl")        # 2b-r2 membership(その他 入力源)
IN_AXES1 = os.path.join(STRUCT, "ACCOUNT_AXES_v1.json")           # v1(不変・v2 の土台)
OUT_CAND = os.path.join(STRUCT, "ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl")
OUT_V2 = os.path.join(STRUCT, "ACCOUNT_AXES_v2.json")             # 承認時のみ
OUT_MEMB2 = os.path.join(STRUCT, "ACCOUNT_MEMBERSHIP_v2.jsonl")   # 承認時のみ(axes_version=v2)
APPROVALS = os.path.join(STRUCT, "FREEZE_APPROVALS.jsonl")        # authored: {candidate_id, approved_by}

# 新定数ゼロ: 既存の相対 margin/多様性ガードのみ再利用(幻覚定数の禁止・裁定A §0)
MARGIN = R.MARGIN            # cross-seed ARI と候補 silhouette の「負の制御を超える」相対 margin
DIV_TH = R.DIV_TH           # F-B 自明性ガード(content 多様性)
# v2 re-membership は A.assign_membership(負の制御相対)を共有。絶対 cosine 閾値(旧 MEMB_TH)は撤廃


# ── 入力: その他/UNCLASSIFIED 部分集合 ────────────────────────────────────────
def _other_subset():
    """ACCOUNT_MEMBERSHIP の unclassified==True の element_id 集合。"""
    ids = set()
    for l in open(IN_MEMB, encoding="utf-8"):
        if l.strip():
            m = json.loads(l)
            if m.get("unclassified"):
                ids.add(m["element_id"])
    return ids


def _subset_recs_vectors():
    recs = R._content_records()
    X = R._load_vectors(recs)
    other = _other_subset()
    mask = np.array([r[0] in other for r in recs])
    return [recs[i] for i in range(len(recs)) if mask[i]], X[mask]


# ── #1 濃さ(相対検定・新定数なし) + #2 本物(既存ガード再利用) ──────────────────
def _cand_id(members):
    return "CAND-" + hashlib.sha1("|".join(sorted(members)).encode()).hexdigest()[:8]


def qualify_candidates(recs, X):
    """その他集合(recs,X)から候補方向を surface。全判定を負の制御相対で。承認判断はしない(propose のみ)。
    返り: (candidates[…evidence+verdict], partition_diag)。"""
    if len(X) < 8:
        return [], {"chosen_K": 0, "cross_seed_ARI": 0.0, "neg_cross_seed_ARI": 0.0,
                    "partition_stable": False, "reason": "SUBSET_TOO_SMALL"}
    Xn = R._shuffle_features(X)
    # K sweep: 実 cross-seed ARI が最大の K を採用(r1 と同一手続き)。負の制御=列 shuffle の cross-seed ARI。
    real_by_k, neg_by_k = {}, {}
    for k in R.K_SWEEP:
        if k >= len(X):
            continue
        real_by_k[k], _ = R._cross_seed(X, k)
        neg_by_k[k], _ = R._cross_seed(Xn, k)
    if not real_by_k:
        return [], {"chosen_K": 0, "cross_seed_ARI": 0.0, "neg_cross_seed_ARI": 0.0,
                    "partition_stable": False, "reason": "NO_VALID_K"}
    K = max(real_by_k, key=lambda k: real_by_k[k])
    real_ari, neg_ari = real_by_k[K], neg_by_k[K]
    # #1 条件2+3: partition が cross-seed 安定 かつ 列 shuffle で chance へ崩壊(load-bearing)
    partition_stable = (real_ari - neg_ari) >= MARGIN and real_ari > neg_ari

    labels = R._kmeans(X, K, 0)
    sil_all = A._silhouette_samples(X, labels)
    sil_shuf = A._silhouette_samples(Xn, R._kmeans(Xn, K, 0))   # 負の制御 silhouette(方向密度が chance か)
    neg_sil_mean = float(sil_shuf.mean())

    cands = []
    for j in np.unique(labels):
        idx = np.where(labels == j)[0]
        members = sorted(recs[i][0] for i in idx)
        kinds = [recs[i][1] for i in idx]
        texts = {recs[i][2] for i in idx}
        purity = max(kinds.count(k) for k in set(kinds)) / len(idx)
        diversity = len(texts) / len(idx)
        sil = float(sil_all[idx].mean())
        sub = A._sub_silhouette(X[idx])
        # #1 条件4: 候補 silhouette が 負の制御(shuffle silhouette 平均)を margin 超え
        neg_margin = sil - neg_sil_mean
        dense = partition_stable and neg_margin >= MARGIN
        # #2: F-B 自明性(低多様=退化) / catch-all(sub>=sil=内部で割れる寄せ場) は RESIDUAL に落とす
        if len(idx) < 4:
            verdict = "RESIDUAL_TOO_SMALL"    # well-definedness: sub_silhouette は n<4 で未定義(既存 bound 再利用・密度定数でない)
        elif not dense:
            verdict = "REJECTED_NOT_DENSE_VS_NEG"
        elif diversity <= DIV_TH:
            verdict = "RESIDUAL_LOW_DIVERSITY"
        elif sub >= sil:
            verdict = "RESIDUAL_CATCH_ALL"
        else:
            verdict = "QUALIFIED"
        cands.append({
            "candidate_id": _cand_id(members),
            "cluster": int(j),
            "n_members": len(idx),
            "member_ids_seed": members[:10],
            "kind_purity": round(purity, 4),
            "content_diversity": round(diversity, 4),
            "silhouette": round(sil, 6),
            "sub_silhouette": round(sub, 6),
            "neg_control_margin": round(neg_margin, 6),   # sil - shuffle_sil(相対・絶対閾値でない)
            "cross_seed_ARI": round(real_ari, 6),
            "verdict": verdict,
        })
    cands.sort(key=lambda c: c["candidate_id"])
    diag = {"chosen_K": int(K), "cross_seed_ARI": round(real_ari, 6),
            "neg_cross_seed_ARI": round(neg_ari, 6), "neg_sil_mean": round(neg_sil_mean, 6),
            "real_mean_silhouette": round(float(sil_all.mean()), 6),
            "partition_stable": bool(partition_stable), "reason": "OK"}
    return cands, diag


# ── #4 承認時のみ v2(versioned-append・v1 不変) ───────────────────────────────
def _load_approvals():
    """authored: {candidate_id, approved_by}。approved_by=='Taka' のみ有効。無ければ空(=v2 生成しない)。"""
    if not os.path.isfile(APPROVALS):
        return set()
    ok = set()
    for l in open(APPROVALS, encoding="utf-8"):
        if l.strip() and not l.startswith("#"):
            a = json.loads(l)
            if a.get("approved_by") == "Taka" and a.get("candidate_id"):
                ok.add(a["candidate_id"])
    return ok


def build_v2(recs, X, cands):
    """承認 marker が在る QUALIFIED 候補のみ v1 に追加凍結して v2 を返す。無ければ (None, None)。"""
    approved_ids = _load_approvals()
    qualified = {c["candidate_id"]: c for c in cands if c["verdict"] == "QUALIFIED"}
    to_freeze = [qualified[cid] for cid in sorted(approved_ids) if cid in qualified]
    if not to_freeze:
        return None, None
    v1 = json.load(open(IN_AXES1, encoding="utf-8"))
    v2 = copy.deepcopy(v1)                       # v1 の軸を不変コピー(v1 ファイルは触らない)
    v2["version"] = "v2"
    labels = R._kmeans(X, max(c["cluster"] for c in cands) + 1, 0) if cands else np.array([])
    new_axes = []
    for c in to_freeze:
        idx = np.where(labels == c["cluster"])[0]
        centroid = X[idx].mean(0)
        n = np.linalg.norm(centroid)
        direction = (centroid / n) if n > 0 else centroid
        new_axes.append({
            "axis_id": c["candidate_id"].replace("CAND-", "AX2-"),
            "version": "v2", "frozen_direction": [round(float(v), 6) for v in direction],
            "kind_verdict": "TOPIC", "catch_all_verdict": "COHERENT",
            "seed_member_ids": c["member_ids_seed"], "n_members_r1": c["n_members"],
            "silhouette": c["silhouette"], "sub_silhouette": c["sub_silhouette"],
            "approved_by": "Taka", "from_candidate": c["candidate_id"],
        })
    v2["axes"] = sorted(v1.get("axes", []) + new_axes, key=lambda a: a["axis_id"])
    v2["n_frozen_axes"] = len(v2["axes"])
    v2["note"] = "v2 = v1 不変コピー + Taka 承認済み新軸 %d 本(2b-r3)。v1 は不変。" % len(new_axes)

    # v2 基準で re-membership(axes_version 自己記述)。**全 corpus(388)** を母集団に(その他部分集合でない=completeness)。
    # 由来: 2b-r3 は freeze-0 時代(その他=全corpus)に作られたが、v1 が軸を持つ今 その他(274)≠全corpus(388)。
    # 母集団を全 corpus に戻し、AX-72ead44e 所属114件の欠落・多重所属漏れ・v2 I1 の 274 過小担保を根治。
    full_recs = R._content_records()
    Xfull = R._load_vectors(full_recs)
    dirs = np.array([a["frozen_direction"] for a in v2["axes"]]) if v2["axes"] else np.zeros((0, Xfull.shape[1]))
    hits, dens_list, null = A.assign_membership(Xfull, dirs)   # 負の制御相対・v2 全軸・多重所属可
    memb2 = []
    for i, (nid, kind, _) in enumerate(full_recs):
        dens = dens_list[i]
        hit = [{"axis_id": v2["axes"][a]["axis_id"], "density": round(float(dens[a]), 6),
                "margin_over_null": round(float(dens[a] - null[a]), 6)} for a in hits[i]]
        memb2.append({"element_id": nid, "kind": kind, "axes_version": "v2",
                      "axes": sorted(hit, key=lambda x: (-x["margin_over_null"], x["axis_id"])),
                      "unclassified": len(hit) == 0})
    return v2, memb2


# ── #5 I1 保存則(易しい不変量・ゼロ落ち検出) ─────────────────────────────────
def check_conservation(memb):
    """count(要素 in) == count(軸∪その他 で説明済み)。各要素が 1つ以上の軸 or その他=unclassified。"""
    n_in = len(memb)
    n_explained = sum(1 for m in memb if (m.get("axes") or m.get("unclassified")))
    return n_in == n_explained, {"n_in": n_in, "n_explained": n_explained}


def _base_membership(recs):
    """候補段階(v2 未承認)の membership = 全要素 その他(v1=0軸ゆえ)。I1 用の説明済み集合。"""
    return [{"element_id": r[0], "kind": r[1], "axes_version": "v1",
             "axes": [], "unclassified": True} for r in recs]


# ── シリアライズ/ゲート ───────────────────────────────────────────────────────
def _ser_cand(cands, diag):
    n_q = sum(1 for c in cands if c["verdict"] == "QUALIFIED")
    hdr = {"_meta": ("ACCOUNT_AXES_FREEZE_CANDIDATE (2b-r3 propose only)。QUALIFIED=%d。"
                     "機械は凍結しない=Taka 承認(FREEZE_APPROVALS)時のみ v2。空/全非QUALIFIED=NO_CANDIDATE(その他優勢継続=正当)。"
                     % n_q), "diag": diag}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(c, sort_keys=True, ensure_ascii=False) for c in cands]) + "\n"


def _ser_json(d):
    return json.dumps(d, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _ser_memb(memb):
    return "".join(json.dumps(m, sort_keys=True, ensure_ascii=False) + "\n" for m in memb)


def _synthetic(dense, seed=7, per=30, nb=4, dim=16):
    """負の制御用の合成その他。K_SWEEP(min=4)に合わせ nb=4 の分離塊。
    dense=True: 多様 text(→QUALIFIED 期待)。dense=False: 同一 text の低多様 collapse(→RESIDUAL 期待・幾何は同じ密)。"""
    rng = np.random.default_rng(seed)
    centers = rng.normal(0, 1, (nb, dim))            # ランダム密方向(joint 相関=実 e5 を模す。列 shuffle で崩壊)
    centers = centers / np.linalg.norm(centers, axis=1, keepdims=True)
    Xs, recs = [], []
    for b in range(nb):
        Xs.append(centers[b] + rng.normal(0, 0.08, (per, dim)))
        for i in range(per):
            gid = b * per + i
            txt = ("distinct text %d unique %d" % (gid, gid * 7)) if dense else "identical collapsed text"
            recs.append(("S%d" % gid, "DE", txt))
    X = np.vstack(Xs).astype(np.float64)
    X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
    return recs, np.round(X, 6)


def check():
    recs, X = _subset_recs_vectors()
    cands, diag = qualify_candidates(recs, X)
    v2, memb2 = build_v2(recs, X, cands)
    memb = memb2 if memb2 is not None else _base_membership(recs)
    red = []

    ct = _ser_cand(cands, diag)
    if not os.path.isfile(OUT_CAND) or open(OUT_CAND, encoding="utf-8").read() != ct:
        red.append("REGEN_MISMATCH: ACCOUNT_AXES_FREEZE_CANDIDATE.jsonl")

    # §6-2 候補検出力(陰性対照): 合成の濃い方向→QUALIFIED / 列 shuffle→崩壊(load-bearing)
    sr, sx = _synthetic(dense=True)
    sc, _ = qualify_candidates(sr, sx)
    if not any(c["verdict"] == "QUALIFIED" for c in sc):
        red.append("CAND_DETECTION_FAILED: injected dense direction not surfaced QUALIFIED")
    sc_shuf, _ = qualify_candidates(sr, R._shuffle_features(sx))
    if any(c["verdict"] == "QUALIFIED" for c in sc_shuf):
        red.append("NEG_CONTROL_NOT_LOAD_BEARING: shuffled synthetic still QUALIFIED")

    # §6-3 退化除外(陰性対照): 低多様 collapse→RESIDUAL(凍結候補に残ったら RED)
    dr, dx = _synthetic(dense=False)
    dc, _ = qualify_candidates(dr, dx)
    if any(c["verdict"] == "QUALIFIED" for c in dc):
        red.append("DEGENERATE_NOT_EXCLUDED: low-diversity collapse surfaced as QUALIFIED")

    # §6-4 no-auto-freeze: 承認 marker が無いのに v2 ファイルが在る→RED
    if os.path.isfile(OUT_V2) and not _load_approvals():
        red.append("AUTO_FREEZE_VIOLATION: ACCOUNT_AXES_v2.json exists without Taka approval marker")
    # 承認が在る/無いに応じた v2/membership の byte 一致
    if v2 is not None:
        if not os.path.isfile(OUT_V2) or open(OUT_V2, encoding="utf-8").read() != _ser_json(v2):
            red.append("REGEN_MISMATCH: ACCOUNT_AXES_v2.json")
        if not os.path.isfile(OUT_MEMB2) or open(OUT_MEMB2, encoding="utf-8").read() != _ser_memb(memb2):
            red.append("REGEN_MISMATCH: ACCOUNT_MEMBERSHIP_v2.jsonl")
        # §completeness: v2 membership は **全 corpus** を母集団に(その他部分集合でない)。全388の zero-drop 担保。
        n_full = len(R._content_records())
        if len(memb2) != n_full:
            red.append("V2_MEMBERSHIP_INCOMPLETE: membership_v2=%d != full corpus %d (その他部分集合で評価している)"
                       % (len(memb2), n_full))

    # §6-5 I1 保存則 + ゼロ落ち検出(陰性対照): 1件落とすと保存則が破れる(v2 時=全corpus 388, 候補段階=その他)
    ok, info = check_conservation(memb)
    if not ok:
        red.append("I1_CONSERVATION_FAILED: %s" % info)
    if len(memb) > 1:
        dropped_ok, _ = check_conservation(memb[:-1] + [{"element_id": memb[-1]["element_id"],
                                                         "kind": memb[-1]["kind"], "axes": [], "unclassified": False}])
        if dropped_ok:   # ゼロ落ちを作ったのに保存則が通る=検出力なし
            red.append("I1_NOT_LOAD_BEARING: dropped element not detected by conservation")

    if red:
        print("RTHREAD_2b-r3 --check: RED")
        for m in red:
            print("  " + m)
        return 1
    n_q = sum(1 for c in cands if c["verdict"] == "QUALIFIED")
    if v2 is not None:
        status = "V2_FROZEN(%d)" % v2["n_frozen_axes"]
    elif n_q > 0:
        status = "PROPOSED(%d awaiting Taka)" % n_q
    else:
        status = "NO_CANDIDATE"
    print("RTHREAD_2b-r3 --check: GREEN (byte-identical; %s; K=%d ARI=%.4f neg=%.4f stable=%s; "
          "cands=%d QUALIFIED=%d; neg-controls cand/degenerate/no-auto-freeze/I1 load-bearing; I1 %s)"
          % (status, diag["chosen_K"], diag["cross_seed_ARI"], diag["neg_cross_seed_ARI"],
             diag["partition_stable"], len(cands), n_q, info))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    recs, X = _subset_recs_vectors()
    cands, diag = qualify_candidates(recs, X)
    open(OUT_CAND, "w", encoding="utf-8").write(_ser_cand(cands, diag))
    v2, memb2 = build_v2(recs, X, cands)
    if v2 is not None:                       # 承認 marker が在るときだけ v2(#3 propose→approve)
        open(OUT_V2, "w", encoding="utf-8").write(_ser_json(v2))
        open(OUT_MEMB2, "w", encoding="utf-8").write(_ser_memb(memb2))
    n_q = sum(1 for c in cands if c["verdict"] == "QUALIFIED")
    ok, info = check_conservation(memb2 if memb2 is not None else _base_membership(recs))
    print("subset(その他)=%d | K=%d cross_seed_ARI=%.4f neg=%.4f stable=%s"
          % (len(recs), diag["chosen_K"], diag["cross_seed_ARI"], diag["neg_cross_seed_ARI"], diag["partition_stable"]))
    print("candidates=%d QUALIFIED=%d %s | I1 conservation=%s %s"
          % (len(cands), n_q, "→ NO_CANDIDATE(その他優勢継続)" if n_q == 0 else "→ propose(承認待ち)",
             ok, info))
    if v2 is not None:
        print("v2 FROZEN: %d axes (Taka 承認済み)" % v2["n_frozen_axes"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
