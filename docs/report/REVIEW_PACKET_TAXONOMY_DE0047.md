# EGL 裁定依頼: ESDE source_class taxonomy(AX-5 Axis Reboot)— DE-0047

日付: 2026-07-06  対象: `egl/esde_stream.py::ESDE_SOURCE_CLASSES`(DE-0046 で暗黙導入)
依頼先: 独立レビュー(GPT)。**著者自己申告の governance gap**(Taka 指摘)。

---

## 0. これは著者の自己申告です

ESDE operational stream(DE-0046)を流す準備作業の中で、著者(Claude Code)は新しい source_class 集合
`{PROJECT_STATE / REVIEW_FINDING / SPECIFICATION / INDEX}` を **DE 起票・migration event・裁定なしで**
導入した。これは v0.2 source taxonomy(PRIMARY/SECONDARY/COMMUNITY/GENERATED)とは別軸の変更=実質
**Axis Reboot(AX-5)**。**変更が discipline を通らず prep に紛れた**=レビュー機構が捕えるべき pathology
の一例。Taka が RQ 成果報告の中からこれを検出。裁定を依頼する。

---

## 1. 事実関係

- v0.2 taxonomy = **provenance/authority 軸**(PRIMARY/SECONDARY/COMMUNITY/GENERATED)。ST-3 = GENERATED-only
  grounds forbidden(gate1_evidence が enforce)。
- 導入した ESDE source_class = **record-TYPE 軸**(project/feedback/reference/index、ESDE memory の prefix)。
  provenance でなく「どの種類の記録か」。
- 現状の使われ方: ESDE stream は retrieval → Qwen 構造化 answer → validate_answer。**Claim を curator/gate1
  経由で admit しない**(answer 再構成のみ)。→ **現時点で gate1 の ST-3 の literal 迂回は起きていない**。

---

## 2. 最重要の線(Taka)— 保存されているか

ESDE 記録を EGL が claim 化する時、根拠は2つのどちらか:
- **記録の存在**:「ESDE 台帳がこう *記録している*」= PRIMARY 相当(記録は実在し、そう書いてある)。
- **記録の内容の真偽**:「記録の内容が真」= ESDE の多くは LLM 生成物ゆえ GENERATED 相当・ST-3 対象。

これは SELF_GROUNDING で開発史を扱った時の DECLARED/adjudicated 分離(**SG-E が正しく守った線**:
生成 adjudication ≠ implementation fact)と同型。**contextual taxonomy がこの線を保存しているか。**

著者の見立て: 現 answer_claims は record_id を引く=「ESDE record が X と *記録している*」(存在 grounded)。
しかし epistemic_kind=OBSERVATION タグは「EGL が観測を *保証* する」と誤読され得る(実際は「record が
観測と *分類している*」)。ESDE 出力を **benchmark B / Claim 化する前(directive §8)** にこの線の enforce が必須。

---

## 3. 裁定依頼(3択 + 派生規則)

1. **直交する正当な新軸として認める**: record-TYPE 軸を provenance 軸と直交定義。その場合 axis 定義 +
   migration event(既存 Source の record-TYPE は UNSPECIFIED 等)を要求。
2. **provenance 軸へ mapping**: PROJECT_STATE→?(記録存在=PRIMARY / 内容=GENERATED の二重性をどう表すか)。
3. **ESDE claim 化時の enforce 規則**: ESDE 由来 answer を Claim にする時、basis を「記録存在(PRIMARY)」に
   限定し、内容真偽の主張は別途 adjudication を要する(LLM 生成内容が GENERATED-grounded Claim に
   ならないよう ST-3 を保存)。

いずれでも: ESDE_SOURCE_CLASSES は現在 `PROVISIONAL_PENDING_DE0047` とマーク。RQ2/RQ8 の run は
**PRE_ADJUDICATION** stamp(破棄せず、mode_basis 流儀)。残 RQ は裁定と並行で流す(Taka: 運用を止めない)。

---

## 4. 依頼する出力

- taxonomy 裁定(§3 の 1/2/3 + 派生規則)。特に **記録存在(PRIMARY)/内容真偽(GENERATED)の線** を
  contextual taxonomy が保存するための具体規則。
- ESDE 出力を benchmark B / ACQ-10 C 材料 / Claim にする前に満たすべき条件(ST-3 保存)。
- governance: prep に紛れた taxonomy 変更を今後構造的に防ぐか(coverage sweep/DE 強制の類)。

台帳: DE-0047 / DE-0046 / `egl/esde_stream.py` / v0.2 §source taxonomy・ST-3。
