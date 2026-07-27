# 実装 → 設計/監査: Build 7 §2-1 — 3d の応答生成に事実行を載せた（BUILT・§2-2 とは分けて出す）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-27 / TYPE=BUILT
- **運用方針 確認済（版: v1.0）**
- 実装源: `CC_DESIGN_2026-07-27_BUILD7_SPEC_3D_RESPONSE.md` v1.0（**§2-1 のみ。§2-2 は分けて出す**・仕様 §3）
- **受領した文書**: 上記実装源 / `CC_DESIGN_2026-07-27_I5_INSTRUCTION_3E_ZERO_CANDIDATE.md`（責務区分）/ `CC_OPERATING_POLICY.md`
- **本文書は観測を書きます。判定・評価・提案をしません。**

## 0. これは精度の改善ではありません
**配線と役割の整理です。効果は測っていません**（§4）。

## 1. 変更した本番ファイル（全列挙）
| repo | ファイル | 内容 |
|---|---|---|
| `rri` | `rri/preflight_gate.py` | `hold_facts()` 新設（決定論・LLM ゼロ）。`next_legal_operation(pg, anchoring=None)` に事実行を前置 |
| `twoder` | `submit.py` | 3d の応答生成に `anchoring=binding.get("anchoring")` を渡す（1行） |

**LLM は入れていません**（仕様 §1 の既定どおり）。

## 2. ★変わる文言 / 変わらない文言（受入4-1-2・全列挙）
### 2-1. 変わらない（逐語固定）【監査:IMPL】
**数値ゲート `RRI-GATE-AMBIGUOUS-QUANT-001`**:
```
CLARIFY_FIRST (gate RRI-GATE-AMBIGUOUS-QUANT-001): ambiguous quantitative claim — concrete number +
vague/missing source. RRI holds before DW/acquisition; provide a clear source (author/title/venue/url)
to proceed. proposed EGL status=WEAK_UNSOURCED_QUANTITATIVE_CLAIM
```
**逐語一致を機械検査: `True`**（`anchoring="UNRESOLVED"` を渡した場合も不変）。

### 2-2. 変わる（事実行が前に付く）
**参照ゲート `RRI-GATE-UNBOUND-REFERENT-001`**（`それ、その後どうなった？`）:
```
CLARIFY_FIRST (gate RRI-GATE-UNBOUND-REFERENT-001): 直前の文脈は記録に存在しない。 「それ」が指す対象は
記録から特定できない。 RRI holds before DW/acquisition. required to proceed: 指示語が指す対象の一意な
識別子（DE番号/ファイル名/タスクID等）. proposed EGL status=UNBOUND_REFERENT_CLAIM
```
**存在ゲート `RRI-GATE-UNGROUNDED-EXISTENCE-001`**（`以前作った Watcher 仕様ってどこ？`）:
```
CLARIFY_FIRST (gate RRI-GATE-UNGROUNDED-EXISTENCE-001): 直前の文脈は記録に存在しない。 「Watcher 仕様」が
記録にあるか判定できない。 RRI holds before DW/acquisition. required to proceed: 過去に作成/決定した対象の
一意な識別子（DE番号/ファイルパス/台帳ID/タスクID等）. proposed EGL status=UNGROUNDED_EXISTENCE_PREMISE
```
**追加位置**: `required to proceed:` の**前**。**既存部分の文字列は変えていません**（後方互換・受入4-1-3）。

### 2-3. 事実行の文面（DESIGN 指定のまま・IMPL は考えていません）
| 判定（既存出力） | 出す行 |
|---|---|
| `anchoring == "UNRESOLVED"` | `直前の文脈は記録に存在しない。` |
| `anchoring == "LOW"` | `支配的な文脈が定まらない。` |
| 指示語あり・束縛先なし | `「<語>」が指す対象は記録から特定できない。` |
| 接地 `NOT_FOUND` | `「<対象>」は記録に見つからない。` |
| 接地 `UNKNOWN` | `「<対象>」が記録にあるか判定できない。` |

**行動を示唆する語・戦略名は入れていません。入力ごとに文面を変えていません。**

## 3. 受入【監査:IMPL】
| # | 条件 | 結果 |
|---|---|---|
| 1 | 非回帰 | **`test_preflight_gate` 13/13 PASS**（1件も落ちていません） |
| 2 | 変わる/変わらない文言の全列挙 | **§2** |
| 3 | 既存文字列の後方互換 | **保持**（事実行は前に追加） |
| 4 | 3d が止めた入力の応答に事実行が載る | **2件で確認**（§2-2・LLM 不使用） |
| 5 | 自己完結した依頼は 3d で止まらず対象外 | **確認**（`この設計案の得失は？` → 3d 通過） |
| 6 | §2-2 の 3e 4択 | **本 BUILT には含めません**（分けて出す・仕様 §3） |

## 4. 測定について（受入4-3）
- **効果を測っていません。** 新しい測定装置を作っていません。
- **既存の計器では本番 3d の応答生成を測れません**（既存の計器は研究スクリプト上の意図調べの一致率を測るもので、3d の応答文を評価する計器は存在しません）。**＝ 測れないことを事実として記録します。**
- **LLM 比較を回していません。**

## 5. 観測の限界（事実として）
- 本 BUILT で示したのは **`next_legal_operation()` が返す文字列**です。**その文字列が利用者にどう届くかまでは追っていません。**
- 事実行に使う `anchoring` は `submit.py` 段2 の既存出力です。**`anchoring` 自体の妥当性は本 BUILT で検証していません。**

## 6. commit
**していません**（MGR）。触った repo: `rri` / `twoder`。

---
*IMPL BUILT（Build 7 §2-1 のみ）。3d が止めた時の応答に事実行を決定論で前置。**数値ゲートの文面は逐語一致 True で不変**、参照/存在ゲートの応答に事実行が付く（全文を §2 に列挙）。非回帰 13/13。LLM を入れていない・効果を測っていない・既存の計器では 3d の応答生成を測れないことを記録。§2-2（3e を4択）は分けて出す。*
