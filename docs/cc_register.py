"""CC 管理台帳（暫定）— 3インスタンスが「どの文書が在り、誰宛で、未処理か」を1本から知るための道具。

★これは 2DER の外に置く、**我々（MGR/DESIGN/IMPL）の連携用の台帳**である。
  台帳ができても「2DER で管理されるようになった」とは言わない。

★退役条件: front door から `ART-` の本文が返るようになったら、内容を artifact_registry の登記へ移し、
  本台帳・`_meta` の doc_id 計算式の重複・状況表のずれ検出行を **同時に** 廃止する。

★`twoder` を import しない（裁定 F3: 消える重複 < 残る依存）。式は下に書き写す。
  **式の出所**: `twoder/artifact_registry.py:30-31` の `artifact_id_for()` を実読し、
  **区切りは `"|"`、桁数は `[:10]`** であることを確認して合わせた（仕様案の `[:8]` は【未確認】とされていた）。

★排他制御・retry・ロックを作らない（裁定 F4/F2）。**追記のみ。状態を書き換えない。** 取りこぼしはずれ検出が捕まえる。
★標準ライブラリのみ・LLM 不使用。
"""
import datetime
import glob
import hashlib
import json
import os

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTER = os.path.join(DOCS_DIR, "CC_REGISTER.jsonl")
REPO = "egl"

TYPES = ("HANDOFF", "BUILD_SPEC", "BUILT", "FINDING", "STATUS")
ACTORS = ("MGR", "DESIGN", "IMPL", "TAKA")
BUILD_ROLES = ("IMPL_SOURCE", "REFERENCE", "SUPERSEDED")

_META = ("CC 管理台帳(暫定)。目的=3インスタンスが『どの文書が在り、誰宛で、未処理か』をディレクトリ走査でなく"
         "1本から知る。★退役条件=front door から ART- の本文が返るようになったら、内容を artifact_registry の"
         "登記へ移し、本台帳と本 _meta の doc_id 計算式の重複、および状況表のずれ検出行を同時に廃止する。"
         "doc_id = 'ART-' + sha1('<repo>|<relative_path>').hexdigest()[:10] ——式の出所は "
         "twoder/artifact_registry.py:30-31 の artifact_id_for()。実読して区切り '|' と桁数 [:10] に合わせた"
         "(仕様案の [:8] は【未確認】とされていたため実物を採った)。重複であることを隠さない"
         "(MGR 裁定 F3: 消える重複 < 残る依存)。")


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def doc_id_for(relative_path, repo=REPO):
    """★式は twoder/artifact_registry.py:30-31 と同一（import しない・書き写す）。"""
    return "ART-" + hashlib.sha1((repo + "|" + relative_path).encode()).hexdigest()[:10]


def _ensure():
    """1行目の `_meta` を固定で置く。既に在れば触らない（追記のみ）。"""
    if os.path.exists(REGISTER) and os.path.getsize(REGISTER) > 0:
        return
    with open(REGISTER, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"_meta": _META, "started_at": _now()}, ensure_ascii=False) + "\n")


def _rows():
    _ensure()
    out = []
    with open(REGISTER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _append(rec):
    _ensure()
    with open(REGISTER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def started_at():
    for r in _rows():
        if "_meta" in r:
            return r.get("started_at")
    return None


def record_doc(path, type, frm, to, build_role, supersedes=None):
    """文書を登録し doc_id を返す。**列を足さない。**"""
    if type not in TYPES:
        raise ValueError("type must be one of %s, got %r" % (list(TYPES), type))
    if frm not in ACTORS or to not in ACTORS:
        raise ValueError("from/to must be one of %s" % (list(ACTORS),))
    if build_role not in BUILD_ROLES:
        raise ValueError("build_role must be one of %s, got %r" % (list(BUILD_ROLES), build_role))
    did = doc_id_for(path)
    _append({"kind": "DOC", "doc_id": did, "path": path, "type": type, "from": frm, "to": to,
             "build_role": build_role, "supersedes": supersedes, "ts": _now()})
    return did


def record_done(doc_id, by, by_doc_id):
    """処理済みを追記する。**元の DOC 行は書き換えない。**"""
    if by not in ACTORS:
        raise ValueError("by must be one of %s, got %r" % (list(ACTORS), by))
    _append({"kind": "DONE", "doc_id": doc_id, "by": by, "by_doc_id": by_doc_id, "ts": _now()})


def pending(to=None):
    """DOC 行のうち DONE の無いもの。`to` を渡せば宛先で絞る。"""
    rows = _rows()
    done = {r["doc_id"] for r in rows if r.get("kind") == "DONE"}
    return [r for r in rows if r.get("kind") == "DOC" and r["doc_id"] not in done
            and (to is None or r.get("to") == to)]


def counts():
    """★`files_since_start` は `_meta.started_at` 以降に作られた `egl/docs/CC_*.md` だけを数える。
    過去の文書は数えない（前向きのみ——数えると常にずれる）。"""
    rows = _rows()
    start = started_at()
    n_files = 0
    if start:
        t0 = datetime.datetime.fromisoformat(start).timestamp()
        for p in glob.glob(os.path.join(DOCS_DIR, "CC_*.md")):
            if os.path.getmtime(p) >= t0:
                n_files += 1
    return {"doc_rows": sum(1 for r in rows if r.get("kind") == "DOC"), "files_since_start": n_files}
