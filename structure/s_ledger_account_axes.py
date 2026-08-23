#!/usr/bin/env python3
"""[Claude実装] s_ledger_account_axes — ★勘定科目の軸を ★台帳の明細から 出す(★Taka 許可 2026-08-23)。

★なぜ 足すのか(★2026-08-23 実測)=
  ★`s_embed_axes.py` の corpus は `rri/rri_records.jsonl` だけ(4,864件)で、
  ★明細(勘定科目の提案・642件)を ★1件も 読んでいない。本文の重なりは ★108/642=17%。
  ★∴ 出る軸は「2DERが自分に出した依頼の種類」(進捗投函1503/実装依頼651…)で、
  ★明細の中身の軸では ない。これが「科目が7つしか出ない」の上流。

★既存を 書き換えない=
  ★`s_embed_axes.py` は ★裁定付きの 計器(Flag2 2026-07-25・--check でバイト一致)=★1文字も 触らない。
  ★埋め込み/クラスタ/負の制御は ★その部品を そのまま 呼ぶ=★自作しない。
  ★出力も 別ファイル ／ ★ベクトルの控えも 別ファイル(★既存の cache を 壊さない)。
  ★台帳は 直読しない=★rri の公開関数 `list_account_proposals()` から 引く。

★1つ 直したもの(★既存の 欠陥を 引き継がない)=
  ★既存は `K = max(real)` で K を 選ぶ=★負の制御を 見ていない。
  ★実測(母数4864)= real最大は K=8 だが ★分離(real-neg)最大は K=12。
  ★∴ ここでは ★K は `max(real - neg)` で 選ぶ。両方を 記録に 残す。

★捨てた ガード(★理由を 残す)=
  ★`kind_purity` は 明細では 意味が ない(★明細は 全て 同一種別)。
  ★`verdict` も 642件中 638件が NOT_DECIDED=★自明分割。∴ ★多様性ガードだけ 使う。

★LLM 0 ／ GPU 0 ／ :8005 不使用 ／ CPU のみ。命名は 別段(この段では name=null)。

usage:
  s_ledger_account_axes.py          # 明細→埋め込み→軸抽出→安定性測定(出力2ファイル)
  s_ledger_account_axes.py --check  # バイト一致再生成 + 負の制御 load-bearing
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

OUT_STAB = os.path.join(STRUCT, "LEDGER_ACCOUNT_AXES_STABILITY.json")
# ★`.jsonl` に しない=★毎回 まるごと 作り直す 控えで あって ★追記型の 台帳では ない
#   (★--check が バイト一致を 要求する 時点で 追記では ない)。★2026-08-23 に 監視が 拾ったので 実体に 名前を 合わせた。
OUT_CAND = os.path.join(STRUCT, "LEDGER_ACCOUNT_AXES_CANDIDATE.json")
EMB_CACHE = os.path.join(STRUCT, ".ledger_account_axes_vectors.npy")   # ★既存の cache とは 別

K_SWEEP = (4, 6, 8, 10, 12, 16, 20)
MARGIN = 0.05
DIV_TH = 0.30            # ★相異 text / メンバ数 が これ未満 = 退化(collapse) = RESIDUAL
CLIP = 512               # ★明細は 長文が 混ざる。埋め込みは max_length=256 tok で 切れるが 本文側も 揃える


def _sea():
    """★既存計器を 呼ぶだけ(★import 名の衝突を 避けるため spec 経由)。"""
    sp = importlib.util.spec_from_file_location("_sea_ledger", os.path.join(STRUCT, "s_embed_axes.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _ledger_records():
    """★corpus=明細(勘定科目の提案)。★台帳は直読しない=rri の公開関数から 引く。
    ★返り=[(question_id, verdict, memo)] ／ ★本文が 空の 行は 落とす(★偽の点を 作らない)。"""
    sys.path.insert(0, "/home/takasan/rri")
    from rri import request_thread as RT
    rows = RT.list_account_proposals()
    out = []
    for r in rows:
        txt = " ".join(str(r.get("memo") or "").split())[:CLIP]
        if txt:
            out.append((str(r.get("question_id")), str(r.get("verdict") or "?"), txt))
    out.sort(key=lambda x: x[0])          # ★決定論(★引いた順に 依存しない)
    return out


def _load_vectors(recs, sea):
    texts = [t for _, _, t in recs]
    key = hashlib.sha1(("||".join(texts) + "|" + sea.MODEL + "|" + sea.REVISION).encode()).hexdigest()
    if os.path.isfile(EMB_CACHE):
        try:
            blob = np.load(EMB_CACHE, allow_pickle=True).item()
            if blob.get("key") == key:
                return blob["X"]
        except Exception:
            pass
    X = sea._embed(texts)
    np.save(EMB_CACHE, {"key": key, "X": X})
    return X


def measure():
    sea = _sea()
    recs = _ledger_records()
    X = _load_vectors(recs, sea)
    Xn = sea._shuffle_features(X)
    real_by_k, neg_by_k, lab0 = {}, {}, {}
    for k in K_SWEEP:
        real_by_k[k], lab0[k] = sea._cross_seed(X, k)
        neg_by_k[k], _ = sea._cross_seed(Xn, k)
    # ★既存は max(real)。ここは ★max(real - neg)=★負の制御を 効かせる。
    K = max(K_SWEEP, key=lambda k: (real_by_k[k] - neg_by_k[k], -k))
    K_if_real_only = max(K_SWEEP, key=lambda k: (real_by_k[k], -k))
    real, neg = real_by_k[K], neg_by_k[K]
    labels = lab0[K]

    verdict_lab = sorted({v for _, v, _ in recs})
    vmap = {v: i for i, v in enumerate(verdict_lab)}
    verdict_align = sea._adjusted_rand(labels, np.array([vmap[recs[i][1]] for i in range(len(recs))]))

    per_axis, topic_axes = [], []
    for j in range(K):
        idx = [i for i in range(len(recs)) if labels[i] == j]
        if not idx:
            continue
        members = sorted(recs[i][0] for i in idx)
        diversity = len({recs[i][2] for i in idx}) / len(idx)
        verdict = "RESIDUAL" if diversity < DIV_TH else "TOPIC"
        aid = "LAX-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8]
        # ★代表例=軸の 重心に 近い順(★決定論・同値は id 昇順)。命名の 段が そのまま 使う。
        C = X[idx].mean(0)
        C = C / (np.linalg.norm(C) or 1.0)
        rank = sorted(idx, key=lambda i: (-float(X[i] @ C), recs[i][0]))
        per_axis.append({"axis_id": aid, "n": len(idx), "content_diversity": round(diversity, 4),
                         "verdict": verdict,
                         "sample_question_ids": [recs[i][0] for i in rank[:12]],
                         "sample_texts": [recs[i][2][:160] for i in rank[:6]]})
        if verdict == "TOPIC":
            topic_axes.append((aid, members, [recs[i][0] for i in rank[:12]]))
    per_axis.sort(key=lambda r: (r["verdict"] != "TOPIC", -r["n"]))
    n_topic = len(topic_axes)

    found = (real - neg) >= MARGIN and real > neg and n_topic >= 1
    status = "AXES_FOUND" if found else "NO_STABLE_AXES"

    n_unique = len({t for _, _, t in recs})
    # ★母数の 指紋。★--check が ★『計器が 揺れた』と ★『母数が 動いた』を 分ける ために 使う。
    corpus_fp = hashlib.sha256("||".join(t for _, _, t in recs).encode()).hexdigest()[:16]
    stab = {
        "chart_status": status,
        "corpus": "台帳の明細(list_account_proposals)",
        "corpus_fingerprint": corpus_fp,
        "n_records": len(recs), "n_unique_texts": n_unique,
        "n_topic_axes": n_topic,
        "chosen_K": K, "chosen_by": "max(real - neg)",
        "K_if_chosen_by_real_only": K_if_real_only,
        "real_ari_by_K": {str(k): round(real_by_k[k], 6) for k in K_SWEEP},
        "neg_control_ari_by_K": {str(k): round(neg_by_k[k], 6) for k in K_SWEEP},
        "real_minus_neg_by_K": {str(k): round(real_by_k[k] - neg_by_k[k], 6) for k in K_SWEEP},
        "real_minus_neg_at_K": round(real - neg, 6),
        "cluster_vs_verdict_ARI_at_K": round(verdict_align, 6),
        "per_axis": per_axis,
        "margin_required": MARGIN, "diversity_threshold": DIV_TH,
        "embed_dim": int(X.shape[1]),
        "model": sea.MODEL, "revision": sea.REVISION,
        "seeds": list(sea.SEEDS), "k_sweep": list(K_SWEEP),
        "dropped_guard": "kind_purity は 明細では 全て 同一種別=無意味 ／ verdict も 638/642 が NOT_DECIDED=自明。"
                         "∴ 多様性ガードのみ。",
        "differs_from_s_embed_axes": "corpus=明細(4,864件のRRI記録ではない) ／ K の選び方=max(real-neg)"
                                     "(max(real)ではない) ／ 出力先とベクトル控えは別ファイル。",
        "note": ("AXES_FOUND: TOPIC 軸 %d 個。命名は 別段(name=null)。" % n_topic) if found else
                "NO_STABLE_AXES: 軸を 捏造しない(★正当な結果)。",
    }
    cands = [{"axis_id": aid, "members": members, "sample_question_ids": samp, "name": None, "name_en": None}
             for aid, members, samp in topic_axes]
    return stab, cands


def _ser_stab(s):
    return json.dumps(s, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _ser_cand(cands):
    doc = {"_meta": "LEDGER_ACCOUNT_AXES_CANDIDATE — 台帳の明細から出した科目候補軸。"
                    "name/name_en=null(命名は別段)。空=NO_STABLE_AXES。"
                    "★台帳ではない=毎回まるごと作り直す控え(--check がバイト一致を要求する)。",
           "axes": cands}
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def main(argv):
    stab, cands = measure()
    st, ct = _ser_stab(stab), _ser_cand(cands)
    if "--check" in argv:
        red = []
        # ★母数は 生きている(★明細は 増える)。★∴ バイト一致を 求める のは ★指紋が 同じ 時だけ。
        #   ★指紋が 違う 時に RED を 出すと ★『世界が 動いた』を ★『計器が 壊れた』と 報告して しまう
        #   (★2026-08-23 実測=★私自身の 投函で 明細が 642→643 に なり ★この 誤報が 出た)。
        prev = None
        if os.path.isfile(OUT_STAB):
            try:
                prev = json.load(open(OUT_STAB, encoding="utf-8"))
            except Exception:
                prev = None
        if prev is None:
            red.append("NOT_GENERATED: LEDGER_ACCOUNT_AXES_STABILITY.json")
        elif prev.get("corpus_fingerprint") != stab["corpus_fingerprint"]:
            print("LEDGER_ACCOUNT_AXES --check: CORPUS_CHANGED "
                  "(母数が 動いた=判定しない。記録時 %s件/%s → いま %s件/%s。走らせ直すと 更新される)"
                  % (prev.get("n_records"), prev.get("corpus_fingerprint"),
                     stab["n_records"], stab["corpus_fingerprint"]))
            return 0
        else:
            if open(OUT_STAB, encoding="utf-8").read() != st:
                red.append("REGEN_MISMATCH: LEDGER_ACCOUNT_AXES_STABILITY.json")
            if not os.path.isfile(OUT_CAND) or open(OUT_CAND, encoding="utf-8").read() != ct:
                red.append("REGEN_MISMATCH: LEDGER_ACCOUNT_AXES_CANDIDATE.json")
        if stab["real_minus_neg_at_K"] < 0:
            red.append("NEGATIVE_CONTROL_FAILED: noise ARI >= real")
        if red:
            print("LEDGER_ACCOUNT_AXES --check: RED")
            for m in red:
                print("  " + m)
            return 1
        print("LEDGER_ACCOUNT_AXES --check: GREEN (byte-identical; status=%s; real-neg@K=%.4f)"
              % (stab["chart_status"], stab["real_minus_neg_at_K"]))
        return 0
    open(OUT_STAB, "w", encoding="utf-8").write(st)
    open(OUT_CAND, "w", encoding="utf-8").write(ct)
    print("status=%s K=%d(選び方=%s / realだけなら%d) real-neg@K=%.4f (明細=%d 相異=%d dim=%d) 軸=%d"
          % (stab["chart_status"], stab["chosen_K"], stab["chosen_by"], stab["K_if_chosen_by_real_only"],
             stab["real_minus_neg_at_K"], stab["n_records"], stab["n_unique_texts"],
             stab["embed_dim"], len(cands)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
