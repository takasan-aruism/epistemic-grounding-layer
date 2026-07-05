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
    "acquisition.evaluate_leg_requirement": {  # Phase 1b / ACQ-1..4c
        "guarantees": [
            "leg requirement 充足を RD 宣言でなく primitive から計算(ACQ-1): 実行済 SearchResultSnapshot"
            "(ACQ-4c、同一 leg の AcquisitionRun に束縛)+ content_status=OBSERVED な evidence-eligible "
            "RawObservation(ACQ-4b)+ observed_source_kind が required に policy 一致(ACQ-3b/AB-1)を全て要求。"
            "required は immutable LegIntent から解決(AcquisitionRun payload でない=ACQ-3)。transport 成功でも "
            "content≠OBSERVED や observed≠required は UNSATISFIED",
            "final_url binding(JREV-0005 Probe C 後): source qualification は adapter-reported final_url を"
            "根に分類する(requested locator でない)。registry 一致 host への redirect 詐称でも、実取得先が"
            "未登録なら UNKNOWN=強い種別を得ない",
        ],
        "non_guarantees": [
            "adapter honesty(新 leaf): transport_status/content_status は adapter が付す。嘘をつく adapter"
            "(challenge を OBSERVED と偽る等)は単一プロセスでは検出不能。RD self-report の根が adapter へ"
            "移った(H1/source_class と同型。プロセス分離/署名まで prevention でなく検出水準)",
            "observed_source_kind は code 候補(§11 上界): 最小 Entity Registry 由来で、未登録 host は "
            "UNKNOWN(=required 不充足の安全側)。JREV-0005 Probe B/C 修正で over-classification は封鎖"
            "(segment 単位照合で UGC ホスト全体の公式化を防ぐ / 実取得先 final_url で分類し redirect 詐称を防ぐ)。"
            "残余: registry の *網羅性*・entity 同一性・所有権継続・repo 移管・侵害された公式アカウントは範囲外"
            "(不明は UNKNOWN で fail-closed)。final_url は adapter-reported 実行 metadata で、外部 transport "
            "attestation 境界に対して独立検証されない(adapter/code-trust 境界内=adapter honesty leaf)",
            "policy_match は first slice 厳密一致: substitution(OFFICIAL_RELEASE が OFFICIAL_DOCS を満たす等)"
            "は未実装。coverage_requirements 駆動の matcher は後続",
            "ACQ-4c の search operation 意味検証(JREV-0005 Probe D): snapshot は同一 leg の実 AcquisitionRun へ "
            "束縛必須にした(未束縛 self-report を封鎖)。ただし search_method/query/scope が Source Policy の"
            "要求 search operation に *意味的に* 一致するかの検証は first slice 未実装(束縛のみ)",
            "taint-lineage / MEASURED・REPRODUCED / extraction 独立性は未(Phase 1b 後段)",
        ],
        "ref": "Phase 1b ACQ-1..4c / AB-1/2/3 / DE-0032",
    },
    "self_grounding.answer_question": {  # SELF_GROUNDING baseline / DE-0042
        "guarantees": [
            "構造化 answer contract を validate_answer が決定的に検査(hermetic): 各 answer/historical claim は"
            "実在 record_id を引く必要があり、無出典 assertion・捏造 record_id を検出。source_trace_completeness を計測",
            "2トラック分離(JREV-0006 §13): 構造トラック(corpus 取込/supersession/retrieval/contract)は"
            "hermetic・決定的で LLM 非依存。意味トラック(Qwen 生成)は teacher_signal",
        ],
        "non_guarantees": [
            "baseline のみ: retrieval は naive keyword(関連 record を miss し得る)、supersession は heuristic"
            "(supersede/撤回/廃止 語 + rule token で over/under-flag する)、answerer は単一 Qwen(teacher_signal、"
            "prompt 依存)。answer の正しさは保証しない——構造(出典の実在)のみ検査",
            "§10 metrics は baseline 部分実装(source_trace_completeness のみ算出)。CURRENT/SUPERSEDED 混同率 /"
            "Missing Critical Claim / Scope Overreach / Failure-Pattern Retrieval は gold key + 独立 attacker の"
            "SG-A..I mutation 敵対ラウンド(JREV-0007)まで未計測。corpus は 2 ledger のみ(report/packet 未取込)",
        ],
        "ref": "SELF_GROUNDING / JREV-0006 directive / DE-0042",
    },
    "pipeline.apply_outcome": {  # DE-0039/0040/0041 (JREV-0006 data-integrity)
        "guarantees": [
            "DE-0040 factual admission: VERIFIED は judge entailment(SUPPORTED)*かつ* policy-eligible な "
            "PRIMARY SUPPORTS path を要する。SECONDARY/policy 非適格 source は entail されても REPORTED 止まり"
            "(judge entailment ≠ claim admission)。admission_basis に eligible path を記録",
            "DE-0039 bootstrap_eligible: teacher_signal と分離した code 導出。VERIFIED + validation_mode∈"
            "{DECLARED,SPECIFIED} + policy-eligible + no-taint のみ True。UNRESOLVED/非適格/PARTIAL/taint を"
            "自律化原料(benchmark B)から fail-closed で排除",
            "DE-0041: entailment_status を分離記録。VERIFIED=EVIDENCE_SUPPORTED(judge-entailment + policy-"
            "eligible admission)であって外的真理でない",
        ],
        "non_guarantees": [
            "★source authenticity は依然 leaf(Gate4+ETB の脅威モデル外): policy-eligible な PRIMARY source でも"
            "*捏造された内容* は judge に正しく entail され VERIFIED を mint し得る(JREV-0006 attack 7)。"
            "『VERIFIED = 外的真理』ではない。source 真正性は adapter honesty/registry/署名の領域",
            "policy-eligibility は first slice で source_class==PRIMARY を proxy(observed_source_kind の "
            "policy.preferred/supplementary 照合は後続)。knowledge_status lifecycle(SUPERSEDED/RETRACTED)未",
        ],
        "ref": "DE-0039/0040/0041 / JREV-0006",
    },
    "etb.scan_content": {  # ETB §16.2 / DE-0038
        "guarantees": [
            "ETB-4: 取得内容を data として走査し zero-width / bidi(trojan-source)/ instruction-like "
            "(EN+JA)/ hidden HTML を taint_flags で検出。ETB-5: taint は AcquisitionRun→RawObservation→"
            "NormalizedObservation→Fragment へ伝播(EF-4: 継承+再走査加算)。tainted fragment は gate1 GC-8 が"
            "構造 block(judge が SUPPORTED と言っても claim 化しない=LLM 従順に非依存)",
        ],
        "non_guarantees": [
            "scanner は heuristic: 難読化(部分 zero-width 挿入 / 同義言い換え / 未知言語)や新種 injection は "
            "pattern を回避し得る。taint は ETB-6 に従い自動破棄でなく GC-8 block(過検出は fail-safe 側)。"
            "ETB-2(tool 起動不可)は judge が f1/f2 JSON のみ返す構造で成立、ETB-3(policy 変更禁止)も同様",
        ],
        "ref": "ETB §16.2 / GC-8 / DE-0038",
    },
    "judge_vllm.VLLMAdjudicator": {  # Phase 1b real Gate4 / JREV-0005 next-priority B
        "guarantees": [
            "fail-closed: judge 出力の破損/不正 enum/空 content/vLLM 到達不能は UNJUDGEABLE/UNRESOLVED へ倒し、"
            "decide() が EVIDENCE_INSUFFICIENT にする=**実モデルが壊れても勝手に SUPPORTED/ACCEPT にしない**"
            "(実測: 統合が壊れていた間も false accept ゼロ)",
            "model + prompt version を finding.adjudicator に刻む。temperature=0(再現性)",
            "実モデル敵対ラウンド1回で world-knowledge trap(fragment 未支持の真 claim)と scope-exceed を"
            "止めた(NOT_SUPPORTED/EXCEEDS → 不受理)= judge が bounded context のみで裁定した実証(demo_gate4_vllm)",
        ],
        "non_guarantees": [
            "teacher_signal であって ground truth でない(CB-5): finding は bootstrap 判定の材料で、正しさの"
            "保証ではない。単一モデル・単一ラウンド。model は誤り得る(統計的保証でない)",
            "ETB / prompt-injection は多層で強制(DE-0038): 1層目=構造(acquisition が ETB-4 scan→taint→"
            "gate1 GC-8 が injection 汚染 evidence を judge 到達前に block、LLM 従順に非依存)。2層目=judge "
            "prompt 硬化(ETB-1: evidence は untrusted data、<evidence> 内の指示に従わない)で実モデルが "
            "EN/role-tag/JA injection に従わなかった(live 1ラウンド)。**残余**: ETB scan は heuristic ゆえ "
            "難読化/新種 injection は pattern を回避し得る(taint 過検出は GC-8 で fail-safe 側)。judge 硬化は "
            "単一モデル/prompt 依存で統計保証でない",
            "『world knowledge を使わない』規律は system prompt 依存(構造強制でない)。prompt/model 差替で"
            "挙動変化。抽出独立性(extractor≠judge)も現状は role 分離のみで敵対検証は1ラウンド",
        ],
        "ref": "Phase 1b Gate4 / JREV-0005 §13 / DE-0037",
    },
    "gates.gate1_evidence": {  # BA-REL-001 / JREV-0004
        "guarantees": [
            "ground relation の presence / 構造的受理可能性(evidence_relations が実在 fragment→source へ解決)",
        ],
        "non_guarantees": [
            "relation_type の意味フィルタ: Gate1 は SUPPORTS/REFUTES/CONTRADICTS を区別せず構造受理する"
            "(BA-REL-001)。『evidence 受理 = support 確立』ではない。mode 導出は derive_validation_mode が"
            "別途 eligible SUPPORTS path のみに絞る(REFUTES-only 候補は Gate1 通過だが derive は UNRESOLVED"
            "=fail-closed、unearned mode を grant しない)。Gate1 の意味責任が拡張する時に再訪",
        ],
        "ref": "BA-REL-001 / JREV-0004",
    },
    "gates.derive_validation_mode": {  # L4
        "guarantees": [
            "validation_mode を provenance から導出、導出不能は UNRESOLVED(既定値を捏造しない)",
            "polarity fail-closed(F/JREV-0003): 未知/欠落/typo の polarity は Gate0 で reject かつ derive で "
            "UNRESOLVED。POSITIVE→DECLARED の最特権分岐へ素通りさせない(『既定値の存在自体が誤り』の polarity 層適用)",
        ],
        "non_guarantees": [
            "source_class の真正性: PRIMARY 判定は mk_source の RD 供給ラベル依存"
            "(GENERATED を PRIMARY と偽れば DECLARED が導出される。H1 と同型の leaf self-report)",
            "observation_kind の真正性(R6 の残余 leaf self-report): R6/DE-0025 Phase 1a で DECLARED は"
            "『PRIMARY + DECLARATION 観測(同一観測)』、SPECIFIED は『PRIMARY + DECLARATION|SPECIFICATION』"
            "に限定した——source_class 単独導出(authentic PRIMARY でも measurement/prose を DECLARED にする)は"
            "封じた。ただし observation_kind 自体も RD 供給ラベルゆえ、種別詐称(MEASUREMENT を DECLARATION と"
            "偽る)は単一プロセスでは検出不能(source_class 真正性と同型、根が一段下へ)",
            "MEASURED/REPRODUCED 未導出(Phase 1b/F3a): measurement/reproduction 観測は現状 UNRESOLVED へ倒す"
            "(『無理に賢く導出しない』)。Activity/run type と Measurement schema/Reproduction link を入力に持つ"
            "mode candidate 導出は F3a フル(Phase 1b)。ゆえに測定/再現由来の claim は当面 mode を得ない",
            "taint-lineage 未実装(R8/DE-0030 残余): mode は eligible な非 GENERATED SUPPORTS path から導出"
            "(袋の大域 GENERATED veto は撤廃、単調)。ただし generated 素材が primary fragment の抽出に"
            "*関与* した場合の taint 伝播(DERIVED_FROM_GENERATED/TAINT_RELEVANT)は未表現=Phase 1b",
            "negative_basis の真正性(R7/DE-0029 残余): NEGATIVE の理由 negative_basis は Gate0 で enum 検査"
            "するが、どの enum 値を付すかは RD 供給(polarity/source_class と同型の leaf self-report)",
        ],
        "ref": "L4 / R6 DE-0025 / R8 DE-0030 / R7 DE-0029(fixed: mode⊥polarity + negative_basis)",
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
