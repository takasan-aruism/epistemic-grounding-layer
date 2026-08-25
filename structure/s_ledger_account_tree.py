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


def _mint(prefix, members):
    """★新規科目の id(★従来と 同じ 規則= ★1バイトも 変えて いない)。"""
    return prefix + "-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:8]


def _entry(prefix, level, parent, idx, recs, X, axis_id=None):
    members = sorted(recs[i][0] for i in idx)
    C = X[idx].mean(0)
    C = C / (np.linalg.norm(C) or 1.0)
    rank = sorted(idx, key=lambda i: (-float(X[i] @ C), recs[i][0]))
    div = len({recs[i][2] for i in idx}) / len(idx)
    return {
        "axis_id": axis_id or _mint(prefix, members),
        "level": level, "parent": parent, "n": len(idx),
        "content_diversity": round(div, 4),
        "verdict": "RESIDUAL" if div < DIV_TH else "TOPIC",
        "members": members,
        "sample_question_ids": [recs[i][0] for i in rank[:SAMPLE_K]],
        "sample_texts": [recs[i][2][:160] for i in rank[:4]],
    }


# ────────────────────────────────────────────────────────────────────────────
# ★★同一性の 継承(増分更新)  ―― Taka 裁定 2026-08-24 / HESC-57d601359901 = (b) 採用
#   ★逐語:
#     「ACCOUNT_TREE生成器を、既存科目の axis_id を可能な限り継承する増分更新方式へ変更する。」
#     「既存科目へのmembers追加・減少だけを理由に axis_id を変更してはならない。」
#     「新規科目候補は新規IDとして生成してよいが、既存chartへの採用とは分離し、従来どおり承認対象とする。」
#     「科目の統合・分割・廃止など『同一性そのものを変更する操作』は自動更新に含めず、別途上申する。」
#     「現在の52科目および既存割当を基準状態として保持し」
#
# ★★継承先が 一意に 決まる 規則= ★★過半数。
#   ★`|new ∩ prev| / |prev| > 0.5` を 満たす 新しい 塊は ★高々1つしか 存在し得ない(★証明できる)
#   ∴ ★閾値を 勘で 選んで いない= ★一意性から 決まる。
#   ★★これが 裁定の『members の 追加・減少だけを 理由に id を 変えては ならない』の 実装=
#     ★過半数が 残って いる 限り ★同じ 科目と 見なす。
#
# ★★同一性そのものを 変える 操作は ★自動で 適用しない(★裁定の 逐語)=
#   MERGE_ABSORBED_CANDIDATE … 2つ以上の 既存科目が 同じ 新しい 塊を 主張した
#   SPLIT_CANDIDATE          … 既存科目の members が 複数の 新しい 塊へ 大きく 散った
#   RETIRE_CANDIDATE         … 過半数を 引き継ぐ 塊が 無い
#   ★どれも ★既存の entry を ★そのまま 持ち越す(`carried_forward`)= ★消さない ／ ★統合しない。
#   ★上申は `identity_ops_pending` として doc に 残す(★新台帳を 作らない)。
# ────────────────────────────────────────────────────────────────────────────
INHERIT_MIN_SHARE = 0.5     # ★過半数(★一意性から 決まる= 勘で 選んで いない)
SPLIT_MIN_SHARE = 0.25      # ★分割の 疑いを 記録する 線(★記録だけ= 適用しない)


def _adopted_accounts():
    """★★採択済みの 科目(chart)を 引く。★台帳は 直読しない= rri の 関数から 引く。

    ★★2026-08-25 Taka 裁定(B)で 足した= ★『chart に在る科目は RETIRE_CANDIDATE と呼ばない』。
      ★足した 理由(実測)= ★持ち越し 157件のうち ★33件が chart に在る= ★現役の 科目 だった。
        ★それを 毎回 『廃止候補』として 上申に 積んで いた= ★誤りの 再生産
        (★同型の 誤解を ART-7391be827a でも 出した= 『RETIRE 20件は 死んだ科目でなく 現役20科目』)。
    ★引けなければ 空集合= ★『引けない』を『採択されていない』と 混同しない ため
      ★下では ★空の時は 従来どおり(★誰も 除かない)。
    """
    try:
        sys.path.insert(0, "/home/takasan/rri")
        from rri import request_thread as RT
        return set(RT._load_chart()[1] or ())
    except Exception:
        return set()


def _prev_doc():
    """★1つ前の 控えを 読む(★これが 同一性の 出所)。★無ければ None= 初回は 従来どおり。"""
    if not os.path.isfile(OUT):
        return None
    try:
        with open(OUT, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None                        # ★読めない を『無い』と 混同しない= 初回扱いに 落とす


def _retire_or_adopted(p, adopted, why, ops):
    """★★持ち越す 1件に ★札を 付ける(★Taka 裁定 B)。

    ★`chart` に 在る= ★採択済みの 現役科目 ∴ ★『廃止候補』とは 呼ばない=
      ★`identity_op_pending` を 立てず ★`ops`(上申)にも 積まない。
      ★但し ★持ち越しは する= ★tree から 消すと ★既存割当が tree の 外を 指す
      (★`domain_ledger` の 門が それを 見て いる)。
    ★`chart` に 無い= ★従来どおり `RETIRE_CANDIDATE`。
    ★★これは 抑止では なく ★誤りの 修正= ★数え方を 変えて いない。
    """
    if p.get("axis_id") in adopted:
        return dict(p, carried_forward=True, adopted_in_chart=True,
                    identity_op_pending=None,
                    carried_why="★採択済み(chart)ゆえ 持ち越す= ★廃止候補では ない")
    ops.append({"op": "RETIRE_CANDIDATE", "axis_id": p["axis_id"], "why": why})
    return dict(p, carried_forward=True, identity_op_pending="RETIRE_CANDIDATE")


def _inherit(prefix, prev_entries, fresh):
    """★★新しい 塊へ ★既存の axis_id を 継承する。★書き込み 0 ／ LLM 0 ／ 決定論。

    ★引数 `fresh` = [{"idx":[…], "members":[…], "parent":…}] の 並び(★clustering の 結果)。
    ★返り= (assign, carried, ops)
      assign  … fresh の index → 継承する axis_id(★無ければ キー無し= 新規 id を 打つ)
      carried … ★持ち越す 既存 entry(★消さない)
      ops     … ★上申する 同一性操作の 候補
    """
    prev = [e for e in (prev_entries or []) if str(e.get("axis_id", "")).startswith(prefix + "-")]
    if not prev:
        return {}, [], []
    # ★★2026-08-25 実測で 直した(★入口の 一意化)=
    #   ★前回の 控えに ★同じ axis_id が 2行 以上 在ると ★別々の p が 別々の 塊を 主張し得る
    #   ∴ ★assign の 値が 重複する(★実測= LDET-d153d542 が 前回 3行 / 今回 2行)。
    #   ★1つの id は ★1つの entry= ★members が 最も 多い もの(★現物に 近い)を 残す。
    #   ★★消して いない= ★同じ id の 写しを 1つに 畳むだけ。
    _by = {}
    for e in prev:
        k = e.get("axis_id")
        if k not in _by or len(e.get("members") or ()) > len(_by[k].get("members") or ()):
            _by[k] = e
    prev = sorted(_by.values(), key=lambda e: e["axis_id"])
    fresh_sets = [set(f["members"]) for f in fresh]
    claims = {}                            # fresh index → [(overlap, prev_entry)]
    ops, carried = [], []
    adopted = _adopted_accounts()          # ★B: 採択済み= 廃止候補では ない
    for p in sorted(prev, key=lambda e: e["axis_id"]):
        pm = set(p.get("members") or ())
        if not pm:
            carried.append(_retire_or_adopted(p, adopted, "members 0件", ops))
            continue
        shares = sorted(((len(pm & fs) / float(len(pm)), len(pm & fs), i)
                         for i, fs in enumerate(fresh_sets)), key=lambda t: (-t[0], t[2]))
        top = shares[0] if shares else (0.0, 0, None)
        if top[0] <= INHERIT_MIN_SHARE:
            carried.append(_retire_or_adopted(
                p, adopted, "過半数を 引き継ぐ 塊が 無い(最大 share=%.3f)" % top[0], ops))
            continue
        claims.setdefault(top[2], []).append((top[1], p))
        spread = [{"share": round(sh, 4), "fresh_index": i}
                  for sh, ov, i in shares[1:] if sh >= SPLIT_MIN_SHARE]
        if spread:
            ops.append({"op": "SPLIT_CANDIDATE", "axis_id": p["axis_id"],
                        "why": "members が 複数の 塊へ 散った", "also": spread})
    assign = {}
    for i, cl in sorted(claims.items()):
        cl.sort(key=lambda t: (-t[0], t[1]["axis_id"]))
        assign[i] = cl[0][1]["axis_id"]
        for ov, p in cl[1:]:               # ★★統合は 自動で 適用しない= 持ち越す
            carried.append(dict(p, carried_forward=True,
                                identity_op_pending="MERGE_ABSORBED_CANDIDATE"))
            ops.append({"op": "MERGE_ABSORBED_CANDIDATE", "axis_id": p["axis_id"],
                        "why": "同じ 塊を %s も 主張した(★統合は 自動更新に 含めない)" % cl[0][1]["axis_id"]})
    # ★★2026-08-25 実測で 直した(★私の 設計欠陥)=
    #   ★同じ 既存 id が ★『継承先(assign)』と ★『持ち越し(carried)』の ★両方に 出て いた。
    #   ★実測= 詳細 267行 / 一意 262 ∴ ★4件が 重複(LDET-d153d542 は ★3行)。
    #   ★因果= ①ある回で p が 塊A を 主張して 継承 → ②次の回で p の members は 前回の まま(持ち越しは
    #     members を 更新しない)∴ ★過半数を 失い RETIRE/MERGE 側へ 落ちる → ★同じ id で 2行に なる。
    #   ★★1つの id は ★1つの entry でなければ ならない(★試験
    #     `test_two_levels_and_parenting` が『同じ 詳細科目が 2つの 親に 付いて いる』で 落ちた)。
    #   ★★決め方= ★★継承が 勝つ= ★assign に 出た id は ★carried から 除く。
    #     ★理由= 継承側は ★いまの members を 持つ(★現物)／ 持ち越し側は ★前回の members(★写し)。
    #     ★『現物 が 在るのに 写しを 残す』のは ★二重計上。
    #   ★★これは 抑止では なく ★同一性の 保存= ★消しては いない(★同じ id が 1行に なるだけ)。
    # ★★出口の 一意化= ★同じ id を 2つの 塊が 継承しない。
    #   ★強い 方(overlap 最大 → 同率なら fresh index が 小さい 方)が 勝ち、
    #   ★負けた 塊は ★継承を 諦める= ★新規 id を 打つ(`assign` から 落とす)。
    #   ★★これも 消して いない= ★1つの id が 1つの 塊に 付く だけ。
    best = {}
    for i, cl in sorted(claims.items()):
        aid = assign.get(i)
        if aid is None:
            continue
        ov = max((t[0] for t in cl), default=0)
        if aid not in best or (ov, -i) > best[aid][0]:
            best[aid] = ((ov, -i), i)
    keep = {v[1] for v in best.values()}
    for i in list(assign):
        if i not in keep:
            del assign[i]                  # ★負けた 塊= 新規 id を 打つ
    inherited_ids = set(assign.values())
    dropped = [e for e in carried if e["axis_id"] in inherited_ids]
    carried = [e for e in carried if e["axis_id"] not in inherited_ids]
    if dropped:
        ops = [o for o in ops if o["axis_id"] not in inherited_ids]
    ops.sort(key=lambda o: (o["op"], o["axis_id"]))
    carried.sort(key=lambda e: e["axis_id"])
    return assign, carried, ops


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

    # ★★clustering そのものは 1バイトも 変えて いない= ★先に 塊だけ 作り、
    #   ★その 後で ★同一性(axis_id)を 継承する(★Taka 裁定=(b) 増分更新)。
    prev = _prev_doc()
    fresh_cats, health = [], []
    for j in range(K1):
        idx = [i for i in range(len(recs)) if lab1[i] == j]
        if not idx:
            continue
        fresh_cats.append({"idx": idx, "members": sorted(recs[i][0] for i in idx)})
    cat_assign, cat_carried, ops = _inherit("LCAT", (prev or {}).get("categories"), fresh_cats)

    cats = []
    for ci, f in enumerate(fresh_cats):
        cats.append(_entry("LCAT", 1, None, f["idx"], recs, X, axis_id=cat_assign.get(ci)))

    fresh_details = []
    for ci, f in enumerate(fresh_cats):
        idx = f["idx"]
        parent = cats[ci]["axis_id"]
        sub_k = max(2, int(round(len(idx) / float(TARGET))))
        sub_k = min(sub_k, len(idx))
        Xs = X[idx]
        if sub_k >= 2 and len(idx) > sub_k:
            real2, sub_lab = sea._cross_seed(Xs, sub_k)
            neg2, _ = sea._cross_seed(sea._shuffle_features(Xs), sub_k)
            health.append({"parent": parent, "n": len(idx), "sub_k": sub_k,
                           "real_minus_neg": round(real2 - neg2, 6),
                           "passes_margin": bool((real2 - neg2) >= MARGIN)})
            for m in range(sub_k):
                sub_idx = [idx[t] for t in range(len(idx)) if sub_lab[t] == m]
                if sub_idx:
                    fresh_details.append({"idx": sub_idx, "parent": parent,
                                          "members": sorted(recs[i][0] for i in sub_idx)})
        else:
            fresh_details.append({"idx": idx, "parent": parent,
                                  "members": sorted(recs[i][0] for i in idx)})
    det_assign, det_carried, det_ops = _inherit("LDET", (prev or {}).get("details"), fresh_details)
    ops = ops + det_ops

    details, inherited, minted = [], 0, 0
    for di, f in enumerate(fresh_details):
        aid = det_assign.get(di)
        inherited += 1 if aid else 0
        minted += 0 if aid else 1
        details.append(_entry("LDET", 2, f["parent"], f["idx"], recs, X, axis_id=aid))

    # ★★持ち越し= ★消さない ／ ★統合しない(★裁定『同一性そのものを変更する操作は自動更新に含めない』)
    details += det_carried
    cats += cat_carried

    details.sort(key=lambda r: (r["parent"] or "", -r["n"], r["axis_id"]))
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
        # ★★同一性の 台帳では ない= ★この 控えの 中の 記録(★新台帳を 作って いない)
        "_identity": {
            "mode": "INCREMENTAL_INHERIT" if prev else "FIRST_GENERATION",
            "rule": ("既存科目の members の 過半数(> %.2f)を 引き継ぐ 塊へ axis_id を 継承する。"
                     "★過半数 ∴ 継承先は 一意。★members の 追加・減少だけでは id を 変えない。"
                     % INHERIT_MIN_SHARE),
            "inherit_min_share": INHERIT_MIN_SHARE,
            "split_min_share": SPLIT_MIN_SHARE,
            "details_inherited": inherited,
            "details_new_candidates": minted,
            "details_carried_forward": len(det_carried),
            "categories_carried_forward": len(cat_carried),
            "prev_details": len((prev or {}).get("details") or []),
            "prev_categories": len((prev or {}).get("categories") or []),
            # ★★自動で 適用しない= ★上申の 対象(★裁定の 逐語)
            "identity_ops_pending": ops,
            "note": ("★新規科目候補は 新規 id で 出すが ★chart への 採用は 別(承認対象)。"
                     "★統合・分割・廃止は 自動更新に 含めない= 該当の 既存 entry を そのまま 持ち越す。"),
        },
        "categories": cats, "details": details,
    }
    return doc


def _ser(doc):
    return json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _state(doc):
    """★★`--check` が 比べる のは ★状態(★`_identity` は 遷移の 記録 ∴ 外す)。

    ★★なぜ 外すか(★2026-08-24 実測)= ★`_identity` は 『前回から 何件 継承した / 何件 新規』を
      持つ ∴ ★同じ 母数でも ★前回が 違えば 値が 変わる(★52→88 の 回と 88→88 の 回で 違う)。
      ★これを バイト比較に 入れると ★決定論の 検査が ★永久に RED に なる=★鍵が 違う。
    ★∴ ★状態(categories / details / 指標)で 判定し ★`_identity` は 別に 表示する。
    """
    return {k: v for k, v in (doc or {}).items() if k != "_identity"}


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
        if _ser(_state(prev)) != _ser(_state(doc)):
            print("LEDGER_ACCOUNT_TREE --check: RED\n  REGEN_MISMATCH (★`_identity` を 除いた 状態で 不一致)")
            return 1
        I = doc.get("_identity") or {}
        print("LEDGER_ACCOUNT_TREE --check: GREEN (状態が byte-identical; カテゴリ%d / 詳細%d; 層2の合格 %s)"
              % (doc["n_categories"], doc["n_details"], doc["level2_all_pass_margin"]))
        print("  同一性: %s / 継承%s 新規%s 持ち越し%s / ★上申待ち %s件"
              % (I.get("mode"), I.get("details_inherited"), I.get("details_new_candidates"),
                 I.get("details_carried_forward"), len(I.get("identity_ops_pending") or [])))
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
