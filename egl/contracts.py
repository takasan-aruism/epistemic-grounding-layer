"""Guard 契約レジストリ(C6)。恒久対策(Taka 裁定 2026-07-05)。

この系は claim に representation_residual(known_omissions)を義務付けた。同じ規律を
guard 自身へ折り返す: **全 validator/gate は自分が保証する性質(guarantees)と
保証しない性質(non_guarantees)を宣言する**。

3周のレビューが繰り返し見つけた故障は全て同型だった——
  DE-0005「計算して捨てる」/ M4「completeness は legality でない」/ GC-7「構造キーは意味でない」
= 「validator が検査している性質と、皆が検査していると思った性質のずれ」。
non_guarantees の宣言があれば、そのずれはレビュー前に自認リストに載る。レビューの仕事が
『ずれの発見』から『宣言の検証』へ変わる。これが guard の known_omissions。
"""

# guard_id -> {guarantees:[...], non_guarantees:[...], ref}
GUARD_CONTRACTS = {
    "core.append_event": {
        "guarantees": [
            "physical sole-writer(events.jsonl を書く唯一の経路)",
            "id-event atomicity(id 採番と書込が同一 lock/critical section, DE-0006)",
            "H6: 並行採番の直列化(flock)",
        ],
        "non_guarantees": [
            "semantic write authority の *prevention* は保証しない: 単一プロセスでは capability を"
            "forge し得るため『違反不可能』は騙らない。保証は *検出可能性*(audit_write_authority が"
            "有効 GRANT なき privileged write を機械検出、R1/DE-0021)",
            "self-grant 対策(DE-0024): grant は authorized issuer 発行時のみ有効。honest self-grant"
            "(issuer==grantee)は検出。ただし GRANT の issuer 欄自体が self-report ゆえ issuer=root の"
            "*詐称* は単一プロセスでは検出不能(署名/プロセス分離まで)= 根が一段下へ移る",
            "capability wiring は CORRECTION/COMPLETION のみ。Claim/Decision/leg 発行は未 wiring"
            "(audit で unprotected として可視、enforce は incremental)",
        ],
        "ref": "DE-0006 / DE-0021 / DE-0024 / R1",
    },
    "core._check_complete_revision": {  # M4
        "guarantees": [
            "revision completeness(UPDATE/CORRECTION/COMPLETION は現 object の top-level + 1段 nested を包含)",
        ],
        "non_guarantees": [
            "transition legality: status/polarity の遷移が正当かは検査しない(R2, 専用 transition event 管轄)",
            "2段以深の nested completeness(RMW 規律で担保、構造強制でない)",
            "field 値の意味的真正性",
        ],
        "ref": "DE-0007 / R2",
    },
    "core.correct_object": {
        "guarantees": [
            "CR-1 correction_class 必須 / CR-2 METADATA は epistemic fields 不変 /"
            " CR-3 FACTUAL は basis 必須 / CR-4 lifecycle(status/polarity)は CORRECTION 不可",
            "append-only(原 event 不変)・from/to provenance 記録",
        ],
        "non_guarantees": [
            "correction reason の意味的妥当性(basis が本当に訂正を支持するかは人/judge 判断)",
            "lifecycle 遷移そのもの(専用 transition event が別途必要)",
        ],
        "ref": "DE-0016 / R2",
    },
    "core.complete_object": {
        "guarantees": [
            "CP-1 missing/null→concrete のみ / CP-2 既存 non-null scalar 変更禁止 /"
            " CP-3 既存 collection 要素削除禁止 / CP-4 完結後 schema complete",
            "append-only・from/to provenance 記録",
        ],
        "non_guarantees": [
            "fill 値の意味的真正性",
        ],
        "ref": "DE-0017 / R2",
    },
    "gates.gate3_authority": {  # SC-2 / H1
        "guarantees": [
            "summary independence: SearchConclusion.status を信用せず leg event から coverage 再導出(H1)",
        ],
        "non_guarantees": [
            "leg authenticity: leg の source_kind / status / leg_plan_id は RD/producer 供給で、"
            "捏造(未確認 kind の COMPLETED leg / 他 plan の leg を leg_plan_id 付替え)は検出しない"
            "(R4, LegIntent 由来の取得ラッパー未実装)",
        ],
        "ref": "H1 / R4",
    },
    "gates.decide": {  # H3
        "guarantees": [
            "gate2 の claim_key 衝突を判定に反映(dead でない)/ importance で審査バー",
        ],
        "non_guarantees": [
            "claim identity の surface 正規化(case/区切り/既知 alias)は canonicalize_scope で実施(R3/DE-0022)。"
            "ただし version algebra(0.11 vs >=0.11 の包含)と entity 同一性(model variant)は未解決 →"
            "これらの表記差では依然 key が割れ得る(AB-0009 残、Entity Registry/scope algebra は Phase 1b)",
        ],
        "ref": "H3 / DE-0022 / R3",
    },
    "gates.gc7_lint": {  # H4
        "guarantees": [
            "asserted dimension(構造 scope キー) ∩ ground の known_omissions を検出",
        ],
        "non_guarantees": [
            "statement→scope 抽出の真正性: candidate の statement が主張する軸を scope に出さなければ"
            "GC-7 は素通り(H4b, RD self-report。後段 semantic lint GC-6 まで未強制)",
            "ground の known_omissions が未宣言なら vacuous(構造導出は second-extraction 待ち)",
            "statement の意味解釈そのもの(主防衛は設計上 Gate4 F1、GC-7 は見ない)",
        ],
        "ref": "H4 / H4b",
    },
    "gates.derive_validation_mode": {  # L4
        "guarantees": [
            "validation_mode を provenance から導出、導出不能は UNRESOLVED(既定値を捏造しない)",
        ],
        "non_guarantees": [
            "source_class の真正性: PRIMARY 判定は mk_source の RD 供給ラベル依存"
            "(GENERATED を PRIMARY と偽れば DECLARED が導出される。H1 と同型の leaf self-report)",
        ],
        "ref": "L4",
    },
}


def render():
    lines = ["# Guard non-guarantees(guard の known_omissions)"]
    for gid, c in GUARD_CONTRACTS.items():
        lines.append(f"\n## {gid}  [{c['ref']}]")
        for g in c["guarantees"]:
            lines.append(f"  ✓ {g}")
        for n in c["non_guarantees"]:
            lines.append(f"  ✗(非保証) {n}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
