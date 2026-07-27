#!/usr/bin/env python3
"""受入オラクル — Build 9B の成果物 answer(rid, resolve_fn, known_prefixes) の契約テスト。

★v2(2026-07-27): 依頼文を修正したので、成果物を見る前に基準も更新した。緩めていない(P1→MUST 昇格・例外時 UNKNOWN を追加)。
★成果物が届く前に固定した。届いてから基準を決めると後付けになる。
   固定日: 2026-07-27 / 固定者: 設計/監査(CC-α) / 依頼文の出典: CC_DESIGN_2026-07-27_BUILD9B_SPEC_...md §1

usage:  python3 oracle_answer_contract.py <成果物の.pyへのパス>
出口:   MUST が1件でも落ちたら exit=1。UNSPECIFIED は合否に数えない(私の仕様の穴)。
"""
import sys, os, importlib.util

MUST, PRINCIPLE, UNSPEC = [], [], []


def _load(path):
    spec = importlib.util.spec_from_file_location("cand", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if not hasattr(m, "answer"):
        print("FATAL: answer() が無い"); sys.exit(1)
    return m.answer


def check(bucket, name, cond, detail=""):
    bucket.append((name, bool(cond), detail))


def main(path):
    answer = _load(path)
    KP = ("DE", "UTT")

    # --- M1: 未対応の接頭辞は NOT_ANSWERABLE ---
    r = answer("XYZ-0001", lambda rid: None, KP)
    check(MUST, "M1 未対応接頭辞 -> NOT_ANSWERABLE", r.get("state") == "NOT_ANSWERABLE", repr(r))

    # --- M2: 対応接頭辞 + 記録あり -> ANSWERED、かつ record は resolve_fn の返り値そのもの ---
    rec = {"design_evidence_id": "DE-0525", "x": 1}
    r = answer("DE-0525", lambda rid: rec, KP)
    check(MUST, "M2a 記録あり -> ANSWERED", r.get("state") == "ANSWERED", repr(r))
    check(MUST, "M2b record が resolve_fn の返り値そのもの", r.get("record") == rec, repr(r.get("record")))

    # --- M3: 対応接頭辞 + None -> NOT_FOUND ---
    r = answer("DE-99999", lambda rid: None, KP)
    check(MUST, "M3 記録なし -> NOT_FOUND", r.get("state") == "NOT_FOUND", repr(r))

    # --- M4: ★NOT_ANSWERABLE と NOT_FOUND が別の値であること（本 build の核） ---
    a = answer("XYZ-0001", lambda rid: None, KP).get("state")
    b = answer("DE-99999", lambda rid: None, KP).get("state")
    check(MUST, "M4 NOT_ANSWERABLE != NOT_FOUND", a != b, "%r vs %r" % (a, b))

    # --- P1: 未対応接頭辞では resolve_fn を呼ばないこと ---
    #     存在/非存在を決定論で先に確定し、確定した側の分岐にだけ渡す（Taka の第一原則）。
    #     ★v2: 新しい依頼文はこれを明記した ∴ MUST に昇格する。
    #       （成果物を見る前に、依頼文が変わったことを理由に上げている。緩めたのではない）
    calls = []
    answer("XYZ-0001", lambda rid: calls.append(rid), KP)
    check(MUST, "M8 未対応接頭辞では resolve_fn を呼ばない", calls == [], "呼ばれた回数=%d" % len(calls))

    # --- M6: falsy だが None でない記録は ANSWERED（`if resolve_fn(rid):` を使うと落ちる） ---
    for falsy in ({}, [], "", 0, False):
        r = answer("DE-0001", lambda rid: falsy, KP)
        check(MUST, "M6 falsy な記録(%r) -> ANSWERED" % (falsy,), r.get("state") == "ANSWERED", repr(r))

    # --- M7: known_prefixes が空なら常に NOT_ANSWERABLE ---
    r = answer("DE-0001", lambda rid: {"a": 1}, ())
    check(MUST, "M7 known_prefixes 空 -> NOT_ANSWERABLE", r.get("state") == "NOT_ANSWERABLE", repr(r))

    # --- UNSPECIFIED: 私の依頼文が定義していない。落ちても不合格にしない（仕様の穴＝私の責任） ---
    for bad in ("", "DE", "-0001", "0001", None):
        try:
            r = answer(bad, lambda rid: None, KP)
            check(UNSPEC, "U 不正な rid %r で例外を出さない" % (bad,), isinstance(r, dict), repr(r))
        except Exception as e:
            check(UNSPEC, "U 不正な rid %r で例外を出さない" % (bad,), False, "%s: %s" % (type(e).__name__, e))
    # v2: 例外時の扱いも依頼文に明記した ∴ MUST
    try:
        r = answer("DE-0001", lambda rid: (_ for _ in ()).throw(RuntimeError("boom")), KP)
        check(MUST, "M9 resolve_fn が例外 -> UNKNOWN を返し、例外を素通ししない",
              r.get("state") == "UNKNOWN", repr(r))
    except Exception as e:
        check(MUST, "M9 resolve_fn が例外 -> UNKNOWN を返し、例外を素通ししない", False,
              "%s: %s" % (type(e).__name__, e))

    print("=== MUST (合否に数える) ===")
    for n, ok, d in MUST:
        print("  %s  %s%s" % ("PASS" if ok else "FAIL", n, ("   <- " + d) if not ok else ""))
    print("=== PRINCIPLE (原則由来だが依頼文に未記載。合否に数えない=落ちたら私の記載漏れ) ===")
    for n, ok, d in PRINCIPLE:
        print("  %s  %s%s" % ("ok  " if ok else "note", n, ("   <- " + d) if not ok else ""))
    print("=== UNSPECIFIED (私の仕様の穴。合否に数えない) ===")
    for n, ok, d in UNSPEC:
        print("  %s  %s%s" % ("ok  " if ok else "note", n, ("   <- " + d) if not ok else ""))
    failed = [n for n, ok, _ in MUST if not ok]
    print("\nMUST: %d/%d PASS" % (len(MUST) - len(failed), len(MUST)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    main(os.path.abspath(sys.argv[1]))
