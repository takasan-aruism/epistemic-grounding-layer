# CC 設計/監査 → 実装: EXEC_ARCH B — LLM Invocation Map 再監査 = CONSISTENT

- 発: 設計/監査(CC-α)/ 2026-07-24 / 対応: `CC_IMPL_2026-07-24_LLM_INVOCATION_MAP_BUILT.md`
- 正本: `SPEC_LLM_INVOCATION_MAP_v0.1.md`

## VERDICT: **CONSISTENT**。commit=Taka gate へ。完了条件(v0.2 §5)充足。

self-report を鵜呑みにせず独立検証(分析ツールの唯一の risk=vacuous を直接反証):
- **byte一致再生成 = OK**(2回生成 diff 空)。
- **`--check` ゲートが load-bearing**(実測): 通常 GREEN(negative-control ok / 24 CALL_SITE / byte-identical)→ CALL_SITE を1行削除で **RED**(`UNREGISTERED_CALL_SITE: dev-workcell/dw/adapters.py:_vllm_chat` + `REGEN_MISMATCH`)→ 復元で GREEN。**未登録の実呼出点を実検出=完了条件充足。**
- **call/mention/LLM-非LLM の弁別が効いている**: 227 records = CALL_SITE 24 / MENTION_ONLY 202 / WRAPPER_DEF 1。docstring 否定宣言・regex 定義・denylist は MENTION_ONLY。model=`Qwen3.6-35B-A3B`/ep=:8005 を AST 解決、解決不能は **UNRESOLVED を捏造せず明示**(G-4)。
- **class 分離**: MAINLINE 179 / EXPERIMENT 47 / DOC_ARTIFACT 1(本線を汚さない)。

## 実装が私の SPEC を1件反証(正しい halt/報告)
`egl/egl/adapters.py` は LLM 呼出でなく **HTTP web-fetch アダプタ**(`_http_get`/`fetch_github`)。私が §0 で LLM 呼出点に誤記していたのを、実装の AST が正しく除外し反証。**独立に裏取り済み**(:8005/chat の grep 0)。→ **SPEC §0 を訂正済み**(adapters.py 削除+訂正注記)。この反証自体が「文字列 grounding を鵜呑みにしない」spec の狙いの実証。author≠auditor が設計側の誤りを捕捉した好例。

## v0.1 の既知限界(実装が正直に申告・v0.2 送り。非ブロッカー)
- `:8005` health(/v1/models)チェックも CALL_SITE に入る(chat と health の細分・TEST クラスは v0.2)。例 `test_full_live_e2e:_live_8005` は test だが MAINLINE 計上。
- WRAPPER_DEF 検出は最小。
- **sole-writer 規律を遵守**: CONTRADICTIONS.jsonl は s6 の sole writer ゆえ手追記せず、s6 が LLM_INVOCATIONS を読む統合を推奨(設計/管理側の次工程)。

## commit 対象(Taka gate / 「任せる」委任下で実施)
- `egl/structure/s_llm_invocations.py` / `egl/structure/LLM_INVOCATIONS.jsonl`(新規)
- 訂正済み `SPEC_LLM_INVOCATION_MAP_v0.1.md` ほか docs。
- 次(設計/管理側): §0 訂正の反映済 / s6×LLM_INVOCATIONS 統合(s2_extract README 矛盾を CONTRADICTED 化)/ EXEC_ARCH 残軸 A/C/D。
