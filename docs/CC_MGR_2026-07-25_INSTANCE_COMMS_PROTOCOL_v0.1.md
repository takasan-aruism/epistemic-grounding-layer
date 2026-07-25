# CC インスタンス間通信プロトコル v0.1（規約）

- 発: CC 管理(MGR) / 2026-07-25 / Taka 指示「きちんと設計せよ・人間リレー(コピペ=FAX)廃止」
- 目的: 役割インスタンス間の連絡を file channel で閉じ、Taka のコピペを廃す。情報は既存フロー通り 2DER に上がる（別途アップロード不要）。
- 位置づけ: 既存の file-drop + watch 慣行（稼働中の SPEC_DROP watch）を**再発明せず規約化**したもの。

## 1. トポロジ（連絡線）
```
coder(IMPL) ── audit(AUDIT) ── designer(DESIGN) ── manager(MGR)
```
- **隣接のみ連絡。coder↔manager は直接連絡しない**（Taka 方針）。
- **最重要リンク = audit ↔ designer（中間）**。ここが設計と実装の齟齬を吸収する。
- 各 instance は「自分の inbound リンクだけ」を watch する。

## 2. Transport = 既存の file-drop 慣行（新機構を作らない）
- `egl/docs` に file を置く = 送信。相手 instance の watch loop が拾う。
- instance 間可視性は共有 FS 上の file で即時（commit 不要・commit=Taka は durable 記録用）。
- 2DER には通常の ledger/event フローで反映。

## 3. 命名規約（だれ→だれ・型）
`CC_<FROM>_<date>_<topic>_<TYPE>.md`
- FROM ∈ {MGR, DESIGN, AUDIT, IMPL}
- TYPE ∈ {HANDOFF(下流へ指示) / FINDING(上流へ所見) / ADJREQ(裁定要求) / ADJRESULT(裁定結果) / STATUS}
- 本文冒頭に「宛: <role>」を明記。**出力はチャットでなく file にする**（＝人間経由を発生させない）。

## 4. 人間(Taka)を呼ぶ唯一の条件
- `TYPE=ADJREQ ∧ escalation=human`（機械にも上級監査にも決められない真の裁定）のみ。
- その場合も MGR が集約し**最小 set**で Taka へ。コピペ・リレー禁止。将来は 2DER UI 経由（§6）。

## 5. 各リンクの watch 責務
| role | watch する inbound | 直接見ない |
|---|---|---|
| MGR | DESIGN→MGR（ADJREQ/STATUS/FINDING 宛 MGR） | IMPL/coder |
| DESIGN | AUDIT→DESIGN, MGR→DESIGN | — |
| AUDIT | IMPL→AUDIT, DESIGN→AUDIT | — |
| IMPL | AUDIT→IMPL, DESIGN→IMPL | MGR |

## 6. 現状の gap（honest・過剰主張しない）
- 2DER webui への正式 surface（off-ramp / PHASE-11 Interface Transfer）は **UNMET**。
- 当面 transport = 共有 file + watch（既に zero-human で機能）。webui 配線は別スライスで feasibility を通してから昇格（今バラで足さない）。

## 7. 設計側(DESIGN)への当面のお願い（規約適用の第一歩）
- 裁定が要る時は**チャットでなく `CC_DESIGN_<date>_<topic>_ADJREQ.md`（宛: MGR）を file 投函**。MGR が watch し、証拠つき推奨まで詰めて、真に Taka しか決められない分だけ最小 set で上げる。
- 直近の `CC_MGR_2026-07-25_2BR3_CANONICAL_ADJUDICATION_RESULT.md`（裁定3件 confirmed）を拾って着手可。
