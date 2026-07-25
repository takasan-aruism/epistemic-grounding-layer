#!/usr/bin/env python3
"""s_record_tags — test-origin タグ台帳(egl 側 overlay)。rri_records を read-only 走査し test 由来を決定論でタグ。

MGR 裁定(TEST_TAG_SCOPE): rri_records.jsonl は無改変(append-only provenance 源・非侵入原則)。egl 側に overlay
タグ台帳を置き rri_record_id で参照リンク。**overlay であって分離でない**(後から include/除外/重み付けを選べる状態に
するだけ・corpus からの物理排除はしない)。**判定不能は tag しない**(捏造ゼロ)。

決定論タグ基準(この2つのみ):
  1. explicit_test_marker: content に部分文字列 `adj-live-` を含む(承認裁定 fixture の明示マーカー)。
  2. repeated_fixture:     record の content_hash が corpus 内で 2回以上出現(同一 content 再投入=benchmark 反復)。
  両該当は explicit_test_marker 優先。ts batch は基準にしない(bulk import と区別不能=false-tag 回避)。

CPU のみ・LLM 不使用・:8005/GPU 不使用・決定論。

usage:
  s_record_tags.py          # RECORD_TAGS.jsonl 生成
  s_record_tags.py --check  # byte一致 + 基準 load-bearing + rri 無改変 + overlay 不変
"""
import hashlib
import json
import os
import sys
from collections import Counter

STRUCT = os.path.dirname(os.path.abspath(__file__))
RRI_RECORDS = "/home/takasan/rri/rri_records.jsonl"   # read-only(無改変・非侵入)
OUT = os.path.join(STRUCT, "RECORD_TAGS.jsonl")
MARKER = "adj-live-"


def _load_rri():
    """rri_records を read-only で読む。無改変。"""
    return [json.loads(l) for l in open(RRI_RECORDS, encoding="utf-8") if l.strip()]


def _content_str(r):
    return json.dumps(r.get("content"), ensure_ascii=False, sort_keys=True)


def build(records):
    """決定論タグ。返り: RECORD_TAGS 行の list(tag された record のみ・rri_record_id 昇順)。"""
    hash_counts = Counter(r.get("content_hash") for r in records if r.get("content_hash") is not None)
    tags = []
    for r in records:
        rid = r.get("rri_record_id")
        ch = r.get("content_hash")
        explicit = MARKER in _content_str(r)
        repeated = ch is not None and hash_counts[ch] >= 2
        if not (explicit or repeated):
            continue   # 判定不能=未 tag(捏造ゼロ)
        # 両該当は explicit 優先。副次理由も残す(後から重み付け可能に)。
        reason = "explicit_test_marker" if explicit else "repeated_fixture"
        criterion = ("content substring '%s'" % MARKER) if explicit \
            else ("content_hash occurs %dx" % hash_counts[ch])
        rec = {"rri_record_id": rid, "origin": "test", "reason": reason, "criterion": criterion}
        if explicit and repeated:
            rec["also"] = "repeated_fixture(content_hash occurs %dx)" % hash_counts[ch]
        tags.append(rec)
    tags.sort(key=lambda t: str(t["rri_record_id"]))
    return tags


def _ser(tags):
    hdr = {"_meta": ("RECORD_TAGS(egl overlay・rri無改変)。origin=test。基準=explicit_test_marker(adj-live-)/"
                     "repeated_fixture(content_hash>=2x)。overlay=分離でない・判定不能は未tag。tagged=%d" % len(tags))}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(t, sort_keys=True, ensure_ascii=False) for t in tags]) + "\n"


def _rri_sha():
    return hashlib.sha256(open(RRI_RECORDS, "rb").read()).hexdigest()


def check():
    red = []
    before = _rri_sha()
    records = _load_rri()
    tags = build(records)
    ser = _ser(tags)
    # byte 一致
    if not os.path.isfile(OUT) or open(OUT, encoding="utf-8").read() != ser:
        red.append("REGEN_MISMATCH: RECORD_TAGS.jsonl")
    # 基準 load-bearing(陰性対照 A): adj-live-* を含む record が必ず explicit で tag される(漏れたら RED)
    expl_ids = {r.get("rri_record_id") for r in records if MARKER in _content_str(r)}
    tagged_expl = {t["rri_record_id"] for t in tags if t["reason"] == "explicit_test_marker"}
    if expl_ids - tagged_expl:
        red.append("EXPLICIT_MARKER_MISSED: %s not tagged" % sorted(expl_ids - tagged_expl))
    if not expl_ids:
        red.append("EXPLICIT_MARKER_ABSENT: adj-live- 基準が空振り(検出力なし)")
    # 基準 load-bearing(陰性対照 B): content_hash を全て一意化 → repeated_fixture が消える(真の重複を見ている証拠)
    uniq = [dict(r, content_hash="UNIQUE-%d" % i) for i, r in enumerate(records)]
    if any(t["reason"] == "repeated_fixture" for t in build(uniq)):
        red.append("REPEATED_NOT_LOAD_BEARING: content_hash 一意化後も repeated_fixture が残る")
    if not any(t["reason"] == "repeated_fixture" for t in tags):
        red.append("REPEATED_ABSENT: repeated_fixture 基準が空振り(検出力なし)")
    # rri 無改変(read-only 担保): build 前後で rri_records の sha256 不変
    if _rri_sha() != before:
        red.append("RRI_MUTATED: rri_records.jsonl が改変された(非侵入原則違反)")
    # overlay 不変: 2b パイプラインが RECORD_TAGS を読まない(corpus/membership に影響しない)
    for stage in ("s_embed_axes.py", "s_account_axes.py", "s_rthread_2br3.py", "s_mine_accounts.py"):
        p = os.path.join(STRUCT, stage)
        if os.path.isfile(p) and "RECORD_TAGS" in open(p, encoding="utf-8").read():
            red.append("OVERLAY_VIOLATION: %s が RECORD_TAGS を参照(overlay でなく入力化)" % stage)
    if red:
        print("RECORD_TAGS --check: RED")
        for m in red:
            print("  " + m)
        return 1
    n_expl = sum(1 for t in tags if t["reason"] == "explicit_test_marker")
    n_rep = sum(1 for t in tags if t["reason"] == "repeated_fixture")
    print("RECORD_TAGS --check: GREEN (byte-identical; tagged=%d [explicit=%d repeated=%d] / %d records untagged=%d; "
          "criteria load-bearing; rri 無改変; overlay 不変)"
          % (len(tags), n_expl, n_rep, len(records), len(records) - len(tags)))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    records = _load_rri()
    tags = build(records)
    open(OUT, "w", encoding="utf-8").write(_ser(tags))
    n_expl = sum(1 for t in tags if t["reason"] == "explicit_test_marker")
    n_rep = sum(1 for t in tags if t["reason"] == "repeated_fixture")
    print("RECORD_TAGS: tagged=%d (explicit=%d repeated=%d) / %d records | untagged=%d (未分類=捏造ゼロ) | rri 無改変"
          % (len(tags), n_expl, n_rep, len(records), len(records) - len(tags)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
