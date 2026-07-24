# 設計/監査 → 実装: EXEC_ARCH B — LLM Invocation Map handoff

- 発: 設計/監査(CC-α)/ 2026-07-24 / 正本: `SPEC_LLM_INVOCATION_MAP_v0.1.md`
- **repo=egl**(structure 作法)。EXEC_ARCH v0.2 §2B(最優先)。決定論・LLM 不使用。
- 設計は **実コードで grounding 済み**(呼出プリミティブ=`urllib.request.urlopen`、`:8005` 文字列の大半は docstring 否定宣言=vacuous 回避が核)。

## 依頼(SPEC §1〜§4)
1. `egl/structure/s_llm_invocations.py` を実装(AST 一次検出 + 文字列二次・区別付き)。出力 `egl/structure/LLM_INVOCATIONS.jsonl`。
2. schema は SPEC §2 のとおり。**call と mention を `record_class` で分離**(docstring 否定宣言/正規表現/denylist を CALL_SITE にしない)。**UNRESOLVED を捏造で埋めない**(G-4)。
3. `--check`(常設ゲート)= (1)再生成 byte 一致 (2)未登録 CALL_SITE 検出 (3)**陰性対照**(`:8005` を docstring だけに持つ決定論モジュールを CALL_SITE と誤検出しないことの自己テスト)。
4. 受入=本線実呼出点(SPEC §0 の ≈11 + wrapper)を CALL_SITE 捕捉、docstring 宣言を MENTION_ONLY 分離、`s2_extract.py` の README 矛盾を CALL_SITE 実在で裏付け。

## 拘束
- **LLM 不使用・決定論・byte一致再生成**。新 Registry/Ledger を作らず `egl/structure/` に置く。
- 状態語彙は既存2系へ写像(G-6・新設は PLANNED/UNKNOWN のみ)。
- スコープ=B のみ(A/C/D/MD導出器は別 spec)。green のため検出範囲を勝手に広げない→ halt。
- **完了=文書完成でなく、ゲートが未登録 CALL_SITE を1回検出 or 陰性対照で赤を実証**(v0.2 §5)。

## 完了後
- `CC_IMPL_..._LLM_INVOCATION_MAP_BUILT.md` → 設計側が再監査(byte一致 + call/mention 区別 + ゲート陰性対照)→ CONSISTENT → commit=Taka。管理インスタンスと並走。
