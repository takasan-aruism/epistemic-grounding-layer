#!/usr/bin/env python3
"""★封印試験(★ITEM-2DER-EVO-0059 の LLM 分・受入 a/b/c/d)。

★★:8005 を 1回も 叩かない= ★呼びは 差し替える(★試験で GPU を 使わない)。
★★受入(a)『台帳へ 書かない』は ★実行では 示せない(★書かなかったのは 偶然かも しれない)
  ∴ ★★AST で ★書く道が 1本も 無いことを 見る= ★構造で 示す。
"""
import ast, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project_v0 as P

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_v0.py")


def test_d_index_is_refused_without_calling_the_llm():
    """★受入(d)= ★索引・目次・リンク集は ★作らずに 返す。★LLM も 呼ばない。"""
    r = P.project({"obs_id": "OBS-TEST-1", "source_kind": "INDEX", "text": "1. …\n2. …"})
    assert r["made"] is False, "INDEX なのに 作っている"
    assert r["cards"] == [], "INDEX なのに カードが 在る"
    assert r["called_llm"] is False, "INDEX で LLM を 呼んでいる（GPU の無駄・EVO-0058 の 成立範囲の外）"
    assert "EVO-0058" in r["why"], "作らない 理由に 出所が 書かれていない"


def test_unknown_kind_is_refused_too():
    """★知らない 語も 作らない(★黙って CONTENT 扱いに しない)。"""
    r = P.project({"obs_id": "OBS-TEST-2", "source_kind": "PDF", "text": "x"})
    assert r["made"] is False and r["called_llm"] is False
    assert "CONTENT" in r["why"] and "INDEX" in r["why"], "受け取る語を 示していない"


def _fake(_text):
    return ('[{"subject":"島津","predicate":"設立","object":"1875年","quote":"…"},'
            ' {"subject":"島津","predicate":"本社","object":"京都","quote":"…"}]'), "stop"


def test_c_ids_are_local_and_restart_per_source():
    """★受入(c)= ★F001 は ★projection 内の ローカル識別子= ★source ごとに 振り直す。"""
    a = P.project({"obs_id": "OBS-A", "source_kind": "CONTENT", "text": "…"}, call=_fake)
    b = P.project({"obs_id": "OBS-B", "source_kind": "CONTENT", "text": "…"}, call=_fake)
    assert [c["local_id"] for c in a["cards"]] == ["F001", "F002"]
    assert [c["local_id"] for c in b["cards"]] == ["F001", "F002"], "source を跨いで 連番になっている（恒久IDになりかけ）"
    assert all(c["obs_id"] == "OBS-A" for c in a["cards"]), "引く鍵(obs_id)が 付いていない"
    assert all(c["obs_id"] == "OBS-B" for c in b["cards"])


def test_b_shelves_never_mix():
    """★受入(b)= ★CONTENT 由来と INDEX 由来を ★同じ棚に 置かない。"""
    s = P.Shelf()
    assert s.add(P.project({"obs_id": "OBS-A", "source_kind": "CONTENT", "text": "…"}, call=_fake)) == "SHELVED"
    assert s.add(P.project({"obs_id": "OBS-I", "source_kind": "INDEX", "text": "…"})) == "REFUSED_NOT_MADE"
    assert len(s.shelves["CONTENT"]) == 2
    assert s.shelves["INDEX"] == [], "INDEX の棚に 物が 入った"
    assert len(s.refused) == 1


def test_broken_json_makes_nothing():
    """★返りが 壊れていたら ★0件(★埋めない・捏造しない)。"""
    r = P.project({"obs_id": "OBS-X", "source_kind": "CONTENT", "text": "…"},
                  call=lambda _t: ("すみません、出力できません。", "stop"))
    assert r["made"] is False and r["cards"] == []
    assert "JSON" in r["why"]


def test_a_there_is_no_road_to_the_ledger():
    """★受入(a)= ★台帳へ 書く道が ★1本も 無いこと(★AST で 見る)。"""
    tree = ast.parse(open(SRC, encoding="utf-8").read())
    # ★★私の 門の 欠陥を 直した(2026-09-01 実測)= ★`from twoder import submit_client` は
    #   ★ImportFrom.module が `twoder` ∴ ★`twoder.submit_client` と 突き合わせても 当たらない
    #   ∴ ★★名前の側も 併せて 組む= ★壊した実装を 与えて ★止まることを 確かめてある。
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
            mods |= {"%s.%s" % (n.module, a.name) for a in n.names}   # ★from X import Y
    banned = {"twoder.submit_client", "twoder.submit", "twoder.webui", "twoder.ledger",
              "submit_client", "submit"}
    assert not (mods & banned), "台帳へ書く module を import している: %s" % (mods & banned)

    writes = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = n.args[1].value
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if any(ch in (mode or "r") for ch in "wax+"):
                writes.append(ast.dump(n)[:60])
    assert not writes, "書き込みで open している: %s" % writes

    posts = [ast.dump(n)[:80] for n in ast.walk(tree)
             if isinstance(n, ast.Call) and "urlopen" in ast.dump(n.func)]
    # ★:8005 への 1本だけは 在ってよい(★推論の 口)。★台帳の 口(:8770)は 在っては ならない
    src = open(SRC, encoding="utf-8").read()
    assert ":8770" not in src and "/api/submit" not in src, "台帳の口を 叩く 記述が 在る"
    assert len(posts) <= 1, "外へ出る口が 2本以上 在る: %d" % len(posts)


def test_the_shelf_cannot_persist_anything():
    """★棚が ★保存の口を 持たないこと(★記憶の上にしか 無い)。"""
    for name in ("save", "write", "dump", "persist", "commit", "submit"):
        assert not hasattr(P.Shelf, name), "棚に 保存の口が 在る: %s" % name
