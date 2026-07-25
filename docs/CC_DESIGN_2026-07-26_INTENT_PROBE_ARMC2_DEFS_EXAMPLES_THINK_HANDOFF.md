# 設計/監査 → 実装: 意図調べ arm-C2 — 二択に定義+具体例 / think on-off 比較 / 多数決+abstain（HANDOFF）

- 宛: IMPL（coder）
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-26 / model=Qwen3.6-35B-A3B(:8005)
- 正本: Taka 直接指示（「Cで進めるにしろ用語の定義と具体例を載せる／Think 入れて論理系を上げる／think 有無も比較／あなたの案も」）+ 既存 arm-C `s_intent_probe_armc.py` + RRI spec §9 + 本 handoff
- 位置づけ: arm-C の弱点（`b_probe_type`/`b_multi_type` の細分・seed一貫5/8）を**定義+例+think+多数決**で締める。**弁別は決定論集計のまま**（LLM は二択のみ）。

## 1. 各二択に「定義+具体例」を載せる（Taka 指示・core）
- 各 tiny prompt に**当該二択の用語定義（1文）+ 対比する具体例1〜2**を付す（few-shot）。RRI §9 準拠。特に弱い2二択:
- **`b_probe_type`（needs_probe=yes の時のみ）** — INTENT vs PREMISE:
  - 定義: 「INTENT＝依頼の**対象が何を指すか不明**（指示語・"あれ/それ"）。PREMISE＝依頼が**存在/成立を前提している事実**が確認せず信じられない。」
  - 例: `「あれどこにあったっけ？」→ INTENT`（対象不明） / `「以前作った Watcher 仕様どこ？」→ PREMISE`（仕様の存在が前提・怪しい）。
  - 二択: 「不確かなのは "対象が何を指すか(INTENT)" か "前提した事実/存在が在るか(PREMISE)" か？ → INTENT / PREMISE / **unsure**」
- **`b_multi_type`（determinacy=no/multi の時のみ）** — CHOICE vs BMV:
  - 定義: 「CHOICE＝主要 branch が**有限でユーザは一つを選びたい**（選択肢提示）。BMV＝**複数観点を比較して見せること自体が答え**（budget 内で短く）。」
  - 例: `「どの DB を使う？(Postgres/MySQL/SQLite)」→ CHOICE`（有限選択肢） / `「X のメリット・デメリットは？」→ BMV`（観点比較が答え）。
  - 二択: 「一つ選ばせる有限選択肢型(CHOICE) か、複数観点を比較提示する型(BMV) か？ → CHOICE / BMV / **unsure**」
- 効く二択（`b_context`/`b_determinacy`/`b_needs_probe`/`b_malformed`）にも簡潔な定義+例を付す（一貫性）。**定義/例は固定・記録**（prompt_id）。

## 2. think on/off を両方測って比較（Taka 指示）
- 各二択を **thinking OFF と thinking ON の両方**で実行（tiny ゆえ ON でも終端しやすい・max_tokens は自然終端を許す値・真の runaway のみ DIVERGE）。
- **論理系二択（probe_type/multi_type）が think で改善するか**を特に見る（Taka 仮説「論理系は think で多少まし」）。reasoning_tokens 記録。

## 3. 私の案（追加・measure-first）
- **(i) 二択ごと seed 多数決**: 各二択を N=3(以上) seed で実行し**多数決**で確定（tie→unsure）。seed一貫(5/8)とノイズの改善を測る。3B 並列ゆえ安い。
- **(ii) abstain（unsure）許容**: 二択が **"unsure" を返せる**。決定論集計は unsure を**無理に yes/no に倒さず** honest に扱う（該当次元が決まらなければ `UNRESOLVED_AGG` or 安全側 probe へ）。＝「定義+例でも LLM が弁別できない二択」を正直に炙り出す（measure-first）。

## 4. 比較（同 8 fixture × seed・決定論集計不変）
| 条件 | 内容 |
|---|---|
| C(baseline) | 素の二択（既測） |
| **C2-defs** | 定義+例あり |
| × think | OFF / ON |
| × vote | 単発 / seed多数決 |
- 指標: 戦略一致 / **弱2二択の的中率(probe_type/multi_type)** / seed一貫 / probe recall / abstain率 / 発散率 / レイテンシ・呼出数。
- **焦点**: 定義+例で弱2二択が改善するか / think が論理系二択を上げるか / 多数決で一貫性が上がるか / abstain がどこで出るか。
- 決定論集計ツリー（§9 弁別ルール）は不変（弁別は集計が持つ思想を維持）。

## 5. 規律 / 受入 / 完了後
- measure-first（改善しなければ"しない"を正直に・abstain を捏造で埋めない）・決定論部 byte 再現・provenance 完全（defs版/think/vote/abstain/reasoning_tokens/並列数）・両 :8005 CALL_SITE（meta fold）・全 gate GREEN・commit=Taka・★3 本線は止めない。
- `CC_IMPL_2026-07-26_INTENT_PROBE_ARMC2_..._BUILT.md` → 設計独立再監査 → 比較を MGR/Taka へ → commit=Taka → DE。
- DE 記録は front door(`record_de`)＋**candidate に `generated_by_principal`/`claiming_principal`=`CLAUDE_CODE`・`generation_mode="DIRECT"` 明示**（内部アクター開示・DE-0541 失念の再発防止）。

---
*DESIGN CC-α。実装は本ファイル保存でトリガ（宛 IMPL）。定義+例で二択を締める・think有無比較・多数決+abstain・弁別は決定論集計のまま・measure-first。★3 本線・止めない。*
