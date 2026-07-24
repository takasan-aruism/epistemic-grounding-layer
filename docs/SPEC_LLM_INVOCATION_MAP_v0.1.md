# SPEC: EXEC_ARCH B — LLM Invocation Map v0.1(決定論台帳)

> **EXEC_ARCH v0.2 §2 B(最優先)への回答。** 全 LLM 呼出点の決定論台帳。RRI 条件スタンプ(T31)の前提資産。
> **LLM 不使用・決定論・byte一致再生成。** 起草: 設計/監査(CC-α)/ 正本: `CC_MGR_2026-07-24_EXEC_ARCH_v0.2_DEV_HANDOFF.md` §2B + `RRI_SPEC_MACHINE_v1_1.json`。

- **置き場:** `egl/structure/LLM_INVOCATIONS.jsonl`(既存 structure 作法・新 Registry を作らない)。生成器 `egl/structure/s_llm_invocations.py`。
- **完了条件(v0.2 §5 準拠・文書完成を成功としない):** 常設ゲートが **未登録の実呼出点を1回以上検出** or 陰性対照(呼んでいない決定論モジュールを呼出点と誤検出しないこと)を実証。

## §0. grounding(実測・2026-07-24)
- **本コードベースの LLM 呼出プリミティブは `urllib.request.urlopen(req, ...)`**(req は :8005/:8006 の `/v1/chat/completions` を POST)。**`requests`/`openai`/`httpx` は本線では使われていない**(grep 実測: requests.post は denylist/NET_MARKER 定義の2件のみ=呼出でない)。
- **`:8005` 文字列一致の大半は docstring の否定宣言**(「no LLM/:8005, deterministic, hermetic」)。→ **文字列スキャン単独は vacuous oracle**(呼んでいないモジュールを呼出点と誤認)。**call と mention の区別が spec の核。**
- 実呼出点(本線・実測): `twoder/qwen_worker.py` / `egl/structure/s2_extract.py` / `egl/autonomy/{ingest,investigate}.py` / `rri/rri/{research_intent,request_type}.py`(`_chat` wrapper) / `egl/egl/{self_grounding,judge_vllm}.py` / `ds/ds/phase1.py` / `dev-workcell/dw/adapters.py`。wrapper 集約点=`_chat`(rri×2)/`adjudicate`(judge_vllm/judge)/`call_vllm`(runner doc)。
  - **[訂正 2026-07-24, 実装が反証]** 初版 §0 は `egl/egl/adapters.py` を LLM 呼出点に挙げたが**誤り** — これは `_http_get`/`fetch_github`/`fetch_http_static` の **HTTP web-fetch アダプタ**で :8005/chat を持たない(`dev-workcell/dw/adapters.py` との取り違え)。scanner は正しく CALL_SITE にしていない=AST が LLM/非LLM を弁別できている証拠。この訂正自体が「文字列 grounding を鵜呑みにしない」spec の狙いを実証。
- `experiments/run_*.py`(≈30)は別クラス=研究 one-off。
- README 矛盾(管理側指摘)の実像: `s2_extract.py:100` は urlopen 実呼出=README「LLM不使用」と**真に矛盾**。`s1_symbols.py:16` は `NET_HINT` 正規表現の定義のみ=**呼出でない**(mention)。→ 区別を台帳に反映。

## §1. 検出方式(決定論・二段)
**(1) AST 一次検出(load-bearing):** 各 .py を AST 解析し、以下を呼出点とする:
- `urllib.request.urlopen(...)` の Call ノードで、引数 `req`/url が **LLM endpoint に解決**するもの(同一関数内で `Request(url=...)` の url に `:8005`/`:8006`/`/v1/chat/completions` を含む定数/f-string、または endpoint 定数参照 `DEFAULT_ENDPOINT` 等)。
- 既知 wrapper(`_chat`/`adjudicate`/`call_vllm`)の **定義**と、その **呼出 Call**。
**(2) 文字列 二次検出(補助・区別付き):** `:800[56]` `/v1/chat/completions` `model=` を含む行は候補にするが、**AST で呼出と確認できないものは `record_class=MENTION_ONLY`** として別記(docstring 否定宣言・正規表現・denylist を呼出点にしない)。

## §2. レコード schema(`LLM_INVOCATIONS.jsonl` 1行=1呼出点)
```
{
  "invocation_id": "LLMINV-<8hex>",          # file:func:lineno の決定論ハッシュ
  "caller": "<repo>/<path>:<func>",          # 呼出元
  "lineno": <int>,
  "record_class": "CALL_SITE | WRAPPER_DEF | MENTION_ONLY",   # ← call と mention を分離(§0核)
  "class": "MAINLINE | EXPERIMENT | DOC_ARTIFACT",
  "model": "<literal or UNRESOLVED>",        # payload の model= 値を AST で解決、不能は UNRESOLVED(捏造しない・G-4)
  "endpoint": "<:8005|:8006|UNRESOLVED>",
  "system_prompt_source": "<literal|var:NAME|UNRESOLVED>",
  "context_builder": "PYTHON | LLM_SELF_EXPLORE | UNRESOLVED",  # 誰が context を組むか
  "schema_enforced": true|false|UNRESOLVED,   # response_format/chat_template_kwargs 等
  "output_validator": "<func or NONE or UNRESOLVED>",
  "failure_handling": "<raise|retry|empty-nonterminal|UNRESOLVED>",
  "result_store": "<path or NONE or UNRESOLVED>",
  "status": "LIVE | GATED(USE_VLLM_INFERENCE) | HERMETIC_TESTABLE | UNRESOLVED",
  "gate_ref": "<authority policy key or NONE>"   # 例 USE_VLLM_INFERENCE
}
```
- **UNRESOLVED を一級市民に**(G-4): AST で確定できない欄は捏造せず UNRESOLVED。空欄・推測で埋めない。
- 状態語彙は既存2系へ写像(G-6): 辺 LIVE/WIRED_UNENTERED/… を再利用、新設は PLANNED/UNKNOWN のみ。

## §3. 常設ゲート(v0.2 §5 の(3)「未登録 LLM 呼出点の検出」)
`s_llm_invocations.py --check`:
1. **再生成 byte 一致**(G-T3): 台帳を再生成し既存と byte 一致でなければ赤。
2. **未登録検出**: AST が見つけた `record_class=CALL_SITE` で **台帳に無いもの**があれば赤(=新規 LLM 呼出が登録されず紛れ込むのを防ぐ)。
3. **陰性対照(vacuous 防止・G-T1 相当)**: 「`:8005` を docstring にだけ持つ決定論モジュール」を検出器に食わせ、**CALL_SITE と誤検出しない**ことを自己テスト(検出器が call/mention を区別できると実証)。

## §4. 受入(完了=乖離1回検出 or 陰性対照赤)
- 台帳が本線実呼出点(§0 の11+wrapper)を **CALL_SITE として捕捉**、docstring 否定宣言を **MENTION_ONLY に分離**。
- `--check` の陰性対照が「壊すと赤」を実証(検出器が空振りでない)。
- experiments を EXPERIMENT クラスで別集計(本線を汚さない)。
- **s2_extract.py の README 矛盾**を CALL_SITE 実在で裏付け → 既存 `CONTRADICTIONS.jsonl` に CONTRADICTED 追記(管理側と整合)。

## §5. スコープ / 非スコープ
- 本 spec は **B(LLM Invocation Map)のみ**。A(Runtime Entry 拡張)/ C(Read Paths)/ D(State Machine Map)/ MD 導出器は別 spec(EXEC_ARCH 継続)。
- LLM を検出に使わない(決定論)。model/prompt の**意味的**評価はしない(呼出点の台帳化のみ)。

## §6. 完了後
- `CC_IMPL_..._LLM_INVOCATION_MAP_BUILT.md` → 設計側が再監査(byte一致 + call/mention 区別 + ゲート陰性対照)→ CONSISTENT → commit=Taka。
- 管理インスタンスと並走(照合・監視)。
