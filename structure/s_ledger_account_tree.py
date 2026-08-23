#!/usr/bin/env python3
"""[Claude実装] s_ledger_account_tree — 勘定科目を ★2層(カテゴリ→詳細)に する(★Taka 許可 2026-08-23)。

★なぜ 足すのか(★2026-08-23 実測・Taka 指摘『あれだけ数あって候補は5個だけ？』)=
  ★`s_ledger_account_axes.py` は K を ★max(real-neg) で 選ぶ。
  ★この 指標は ★粗く 割るほど 高く なる ので、★必ず 少数に 落ちる(★実測=6本・最大の塊 161件)。
  ★∴ ★再現しやすさで 粒度を 決めていた=★帳簿として 使えるかで 決めていなかった。

★直し方=★粒度は ★『1科目あたり 何件に したいか』で 決める(★下の TARGET)。
  ★real-neg は ★選ぶ ためでは なく ★健全性の 確認 として 記録する。
  ★実測(母数644)= K=80 でも real-neg=0.4304 ＝ ★合格線 0.05 の 8.6倍。★細かくしても 通る。

★層=
  ★層1(カテゴリ)= max(real-neg) で 選ぶ(★粗い 括りは 再現性で 決めて よい)。
  ★層2(詳細)   = 各カテゴリの 中を ★n/TARGET で 割る。

★既存は 触らない= 埋め込み/クラスタ/負の制御は `s_embed_axes.py` を そのまま 呼ぶ。
★台帳は 直読しない=`s_ledger_account_axes._ledger_records()` 経由(★rri の公開関数)。
★命名は 別段(この段では name=null)。

usage:
  s_ledger_account_tree.py          # 2層に割る(出力1ファイル)
  s_ledger_account_tree.py --check  # 母数の指紋が同じ時だけ バイト一致を見る
"""
import hashlib
import importlib.util
import json
import os
import sys

import numpy as np

STRUCT = os.path.dirname(os.path.abspath(__file__))
# ★★2026-08-24 自己監査: ★この計器は corpus に 明細(台帳)しか 使わない ∴
#   ★自分自身を 数える経路は いま 無い。★但し s_esde_evaluate では
#   ★自分の軸名を ID の発行点と 誤検出して 偽陽性を出した(実測)。
#   ★∴ 将来 コードを走査する処理を 足す時は ★必ず 自分を 除外すること。

OUT = os.path.join(STRUCT, "LEDGER_ACCOUNT_TREE.json")

TARGET = 12              # ★詳細1本あたりの 明細の 目安(★粒度は ここで 決める=指標では 決めない)
L1_K_SWEEP = (4, 6, 8, 10, 12)
MARGIN = 0.05
DIV_TH = 0.30
SAMPLE_K = 12


def _mods():
    sp = importlib.util.spec_from_file_location("_lax", os.path.join(STRUCT, "s_ledger_account_axes.py"))
    lax = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(lax)
    return lax, lax._sea()


def _entry(prefix, level, parent, idx, recs, X):
    members = sorted(recs[i][0] for i in idx)
    C = X[idx].mean(0)
    C = C / (np.linalg.norm(C) or 1.0)
    rank = sorted(idx, key=lambda i: (-float(X[i] @ C), recs[i][0]))
    div = len({recs[i][2] for i in idx}) / len(idx)
    return {
        "axis_id": prefix + "-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8],
        "level": level, "parent": parent, "n": len(idx),
        "content_diversity": round(div, 4),
        "verdict": "RESIDUAL" if div < DIV_TH else "TOPIC",
        "members": members,
        "sample_question_ids": [recs[i][0] for i in rank[:SAMPLE_K]],
        "sample_texts": [recs[i][2][:160] for i in rank[:4]],
    }


def measure():
    lax, sea = _mods()
    recs = lax._ledger_records()
    X = lax._load_vectors(recs, sea)
    Xn = sea._shuffle_features(X)

    # ── 層1: カテゴリ ──
    real_by_k, neg_by_k, lab0 = {}, {}, {}
    for k in L1_K_SWEEP:
        real_by_k[k], lab0[k] = sea._cross_seed(X, k)
        neg_by_k[k], _ = sea._cross_seed(Xn, k)
    K1 = max(L1_K_SWEEP, key=lambda k: (real_by_k[k] - neg_by_k[k], -k))
    lab1 = lab0[K1]

    cats, details, health = [], [], []
    for j in range(K1):
        idx = [i for i in range(len(recs)) if lab1[i] == j]
        if not idx:
            continue
        cat = _entry("LCAT", 1, None, idx, recs, X)
        cats.append(cat)

        # ── 層2: 詳細(★粒度は n/TARGET。★指標では 決めない) ──
        sub_k = max(2, int(round(len(idx) / float(TARGET))))
        sub_k = min(sub_k, len(idx))
        Xs = X[idx]
        if sub_k >= 2 and len(idx) > sub_k:
            real2, sub_lab = sea._cross_seed(Xs, sub_k)
            neg2, _ = sea._cross_seed(sea._shuffle_features(Xs), sub_k)
            health.append({"parent": cat["axis_id"], "n": len(idx), "sub_k": sub_k,
                           "real_minus_neg": round(real2 - neg2, 6),
                           "passes_margin": bool((real2 - neg2) >= MARGIN)})
            for m in range(sub_k):
                sub_idx = [idx[t] for t in range(len(idx)) if sub_lab[t] == m]
                if sub_idx:
                    details.append(_entry("LDET", 2, cat["axis_id"], sub_idx, recs, X))
        else:
            details.append(_entry("LDET", 2, cat["axis_id"], idx, recs, X))

    details.sort(key=lambda r: (r["parent"], -r["n"], r["axis_id"]))
    cats.sort(key=lambda r: (-r["n"], r["axis_id"]))
    corpus_fp = hashlib.sha256("||".join(t for _, _, t in recs).encode()).hexdigest()[:16]
    doc = {
        "_meta": "LEDGER_ACCOUNT_TREE — 勘定科目の2層(カテゴリ→詳細)。name=null(命名は別段)。"
                 "★台帳ではない=毎回まるごと作り直す控え。"
                 "★粒度は TARGET(1科目あたりの件数)で決める=再現性の指標では決めない。",
        "corpus": "台帳の明細(list_account_proposals)",
        "corpus_fingerprint": corpus_fp,
        "n_records": len(recs), "n_unique_texts": len({t for _, _, t in recs}),
        "target_per_detail": TARGET,
        "level1_K": K1, "level1_chosen_by": "max(real - neg)",
        "level1_real_minus_neg_by_K": {str(k): round(real_by_k[k] - neg_by_k[k], 6) for k in L1_K_SWEEP},
        "level1_real_minus_neg_at_K": round(real_by_k[K1] - neg_by_k[K1], 6),
        "n_categories": len(cats), "n_details": len(details),
        "margin_required": MARGIN,
        "level2_health": health,
        "level2_all_pass_margin": all(h["passes_margin"] for h in health) if health else None,
        "model": sea.MODEL, "revision": sea.REVISION, "seeds": list(sea.SEEDS),
        "categories": cats, "details": details,
    }
    return doc


def _ser(doc):
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def main(argv):
    doc = measure()
    s = _ser(doc)
    if "--check" in argv:
        prev = json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else None
        if prev is None:
            print("LEDGER_ACCOUNT_TREE --check: RED\n  NOT_GENERATED")
            return 1
        if prev.get("corpus_fingerprint") != doc["corpus_fingerprint"]:
            print("LEDGER_ACCOUNT_TREE --check: CORPUS_CHANGED (母数が 動いた=判定しない。%s件 → %s件)"
                  % (prev.get("n_records"), doc["n_records"]))
            return 0
        if open(OUT, encoding="utf-8").read() != s:
            print("LEDGER_ACCOUNT_TREE --check: RED\n  REGEN_MISMATCH")
            return 1
        print("LEDGER_ACCOUNT_TREE --check: GREEN (byte-identical; カテゴリ%d / 詳細%d; 層2の合格 %s)"
              % (doc["n_categories"], doc["n_details"], doc["level2_all_pass_margin"]))
        return 0
    open(OUT, "w", encoding="utf-8").write(s)
    bad = [h for h in doc["level2_health"] if not h["passes_margin"]]
    print("明細=%d 相異=%d ／ カテゴリ=%d(K=%d real-neg=%.4f) ／ 詳細=%d(1本あたり目安%d件)"
          % (doc["n_records"], doc["n_unique_texts"], doc["n_categories"], doc["level1_K"],
             doc["level1_real_minus_neg_at_K"], doc["n_details"], TARGET))
    print("層2の健全性: 合格 %d/%d%s"
          % (len(doc["level2_health"]) - len(bad), len(doc["level2_health"]),
             ("  ★落ちた=" + ", ".join("%s(%.4f)" % (h["parent"], h["real_minus_neg"]) for h in bad)) if bad else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
