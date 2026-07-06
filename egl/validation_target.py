"""VALIDATION_TARGET 軸(DE-0047 / Taka 暫定裁定 2026-07-06)。

「記録が存在する ≠ 記録内容が外部事実として真」を表す新しい **直交軸**。source taxonomy(provenance:
PRIMARY/SECONDARY/COMMUNITY/GENERATED)を増やすのでなく、Claim/Evidence evaluation 側の軸とする。
provenance は target 判定の *入力* であって、PRIMARY/GENERATED の shortcut で代替しない。
同じ Source/Observation からでも、Claim 化する時の target に応じて eligible evidence path が変わる。

⚠ PROVISIONAL: これは Taka の *要約ベース* 暫定裁定に沿う実装。packet 本文
(docs/report/REVIEW_PACKET_TAXONOMY_DE0047.md)による正式 property-level 裁定は未(独立 review 待ち)。
"""

VALIDATION_TARGETS = {
    "RECORD_OCCURRENCE": "記録が存在し X と述べた / 決定・review・verdict が記録された(記録存在の一次観測)",
    "CONTENT_ASSERTION": "記録内容 X が外部事実として真である",
    "BEHAVIORAL_PROPERTY": "実装が X の通り振る舞う / 測定現象 X が起きた",
}

# 線の保存規則: 各 target が確立してよいこと / 自動では確立しないこと
MAY_ESTABLISH = {
    "RECORD_OCCURRENCE": ["record exists", "record states X", "decision/review/verdict was recorded"],
    "CONTENT_ASSERTION": ["content X is externally true (subject to adjudication)"],
    "BEHAVIORAL_PROPERTY": ["implementation behaves as X", "measured phenomenon X occurred"],
}
MUST_NOT_AUTO_ESTABLISH = {
    # RECORD_OCCURRENCE の記録が在るだけで内容真理/挙動/測定を自動確立しない
    "RECORD_OCCURRENCE": ["X is externally true", "implementation behaves as X", "measured phenomenon X occurred"],
    # 逆方向: 挙動 evidence があっても「設計判断が歴史的に記録された」は別 Claim
    "BEHAVIORAL_PROPERTY": ["a design decision was historically recorded"],
}


def target_problem(target, evidence_kinds):
    """target と手持ち evidence_kinds(集合)から不足を返す(None=eligible)。first slice の保守規則。
    evidence_kinds 例: {'RECORD'} / {'RECORD','TEST_ARTIFACT'} / {'RECORD','RUN_ARTIFACT'}。
    RECORD = 記録が存在しそう述べている(LEDGER/REPORT/任意の記録された source)。"""
    if target not in VALIDATION_TARGETS:
        return f"unknown validation_target {target!r}"
    if target == "RECORD_OCCURRENCE":
        return None if "RECORD" in evidence_kinds else "RECORD_OCCURRENCE は記録の存在を要する"
    if target == "BEHAVIORAL_PROPERTY":
        if evidence_kinds & {"TEST_ARTIFACT", "RUN_ARTIFACT", "IMPLEMENTATION_ARTIFACT", "REPRODUCED"}:
            return None
        return "BEHAVIORAL_PROPERTY は implementation/test/run artifact を要する(記録単独では不足)"
    if target == "CONTENT_ASSERTION":
        if evidence_kinds & {"CORROBORATING_PRIMARY", "ADJUDICATED"}:
            return None
        return "CONTENT_ASSERTION は record occurrence 単独では確立しない(corroboration/adjudication が要る)"
    return None
