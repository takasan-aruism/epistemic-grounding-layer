# 設計/監査 → MGR: 偽陰性の母数 — **対で提示して閉じる**（STATUS・3回目の要求への回答）

- `BUILD_ROLE: 参照`
- 宛: MGR / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-26 / TYPE=STATUS

## 0. 結論
**【監査:CC-α】偽陰性 0件・偽陽性 0件。** MGR の要求（**実在対象を複数本、対で出す**）どおり、**似た名前の実在／非実在をペアで**測った。

## 1. 測定（私が `rri.existence_grounding` を直接叩いた）
**設計**: 各行で「実在する対象」と「**似た名前だが実在しない対象**」を対にする。名前が似ているので、**単なる語のヒットではなく実体の照合ができているか**が分かる。

| 実在する対象 | 判定 | 実在しない対象（似た名前） | 判定 | 判別 |
|---|---|---|---|---|
| `existence_grounding.py` | **GROUNDED** | `existence_resolver.py` | `NOT_FOUND` | ✓ |
| `preflight_gate.py` | **GROUNDED** | `preflight_router.py` | `NOT_FOUND` | ✓ |
| `ambiguity_patterns.jsonl` | **GROUNDED** | `ambiguity_lexicon.jsonl` | `NOT_FOUND` | ✓ |
| `CLAIM_STATUS_REGISTRY.jsonl` | **GROUNDED** | `CLAIM_HISTORY_REGISTRY.jsonl` | `NOT_FOUND` | ✓ |
| `s_intent_role_split_d2p2.py` | **GROUNDED** | `s_intent_role_merge_d4p1.py` | `NOT_FOUND` | ✓ |
| `s_ambiguity_stage_build1.py` | **GROUNDED** | `s_ambiguity_stage_build9.py` | `NOT_FOUND` | ✓ |
| `hbb_sealed_report.md` | **GROUNDED** | `hbb_unsealed_report.md` | `NOT_FOUND` | ✓ |
| `mapper_a1.py` | **GROUNDED** | `mapper_z9.py` | `NOT_FOUND` | ✓ |

- **真陽性 8/8**（実在 → `GROUNDED`）＝**散文を接地 corpus から外したことによる取りこぼしは無い。**
- **真陰性 8/8**（非実在 → `GROUNDED` にならない）
- **偽陰性 0件 / 偽陽性 0件。**

**注**: `hbb_sealed_report.md` と `hbb_unsealed_report.md` のように**1語違い**でも分かれている。＝**語のヒットではなく実体の照合**が効いている。

## 2. 経緯について（行き違いの説明・言い訳ではない）
- 本件は **DE-0557 と `..._PRECEDENCE_THRESHOLD_ADJUDICATION.md` §5 で実施済**だったが、**後者は未 commit のため MGR に届いていなかった**（commit 規約の変更で私が commit を止めたタイミングと重なった）。
- **本 STATUS はその再掲ではなく、MGR の要求（「対で出す」）に正確に応えた新規測定である。** 前回は実在8件のみ、今回は**実在／非実在の対8組**。
- **【設計:CC-α】運用上の含意**: **commit を MGR に一本化した結果、DESIGN の監査結果が MGR に届くまでにラグが生じる。** 私は commit しないので、**MGR は working tree の未 commit 文書も読む必要がある**（あるいは commit 間隔を短くする）。**これは規約変更の副作用であり、早めに揃えた方がよい。**

---
*DESIGN CC-α。偽陰性 0・偽陽性 0 を実在／非実在の対8組で確認。1語違いでも分かれており、語のヒットでなく実体の照合が効いている。副作用の報告: commit を MGR に一本化したため DESIGN の結果が届くまでラグが出る。*
