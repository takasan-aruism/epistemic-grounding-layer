# 実装担当 → 設計/監査担当: EXEC_ARCH B — LLM Invocation Map v0.1（BUILT）

- 発: 実装インスタンス（Monitor `b0718vzrg`）/ 2026-07-24
- 対応: `SPEC_LLM_INVOCATION_MAP_v0.1.md` / `CC_DESIGN_2026-07-24_LLM_INVOCATION_MAP_HANDOFF.md`
- repo=egl（structure 作法）。LLM 不使用・決定論・byte一致再生成。

## 成果物（working tree・未commit）

- `egl/structure/s_llm_invocations.py`（AST 一次検出＋文字列二次・区別付き＋`--check` 常設ゲート）
- `egl/structure/LLM_INVOCATIONS.jsonl`（227 records: **CALL_SITE=24 / WRAPPER_DEF=1 / MENTION_ONLY=202**）

## 検証（§4 受入・完了条件）

- **本線実呼出点 10/11 を CALL_SITE 捕捉**（qwen_worker / s2_extract / autonomy{ingest,investigate} / rri{research_intent,request_type} / self_grounding / judge_vllm / ds phase1 / dw adapters）。endpoint=`:8005`・model=`Qwen3.6-35B-A3B` を AST で解決（`os.environ.get` default も解決）。
- **call/mention 分離**: docstring 否定宣言 / regex 定義 / denylist は `MENTION_ONLY`（202件）。s1_symbols.py の `NET_HINT` regex 等は CALL_SITE にしていない。
- **`--check` 常設ゲート load-bearing を実証（完了条件 v0.2 §5）**:
  - drift/未登録: ledger から1 CALL_SITE 行を除くと **RED**（`REGEN_MISMATCH` + `UNREGISTERED_CALL_SITE`）
  - 陰性対照: 検出器を vacuous 化（mention を call 扱い）すると **RED**（負の制御は実 egl/adapters と同型の「urlopen を持つ web-fetch ＋ :8005 は docstring のみ」をモデル化）。real 検出器では GREEN。
- experiments（experiments/ ＋ gpu_experiment）を **EXPERIMENT クラスで別集計**（11件）。UNRESOLVED は捏造せず明示（G-4）。

## ★ 重要 finding（§0 grounding の誤り・spec の「矛盾したら halt/報告」に従う）

- **`egl/egl/adapters.py` は LLM 呼出点ではない。** これは **HTTP web-fetch アダプタ**（`_http_get`/`fetch_github`/`fetch_http_static`＝任意 URL/github 取得）で、`:8005`/`/v1/chat/completions` を持たない（grep 実測 0）。
- SPEC §0 は「egl/{self_grounding,**adapters**,judge_vllm}」を LLM 呼出点に挙げるが、これは誤り（dw/adapters との取り違え、または web-fetch を LLM と誤認）。**私の scanner は正しく CALL_SITE にしていない**＝call/mention/LLM-非LLM を実 AST で弁別できている証拠（§0 を鵜呑みにせず、§0 の1件を反証した）。
- → §0 の mainline は「10 LLM chat 呼出点 ＋ web-fetch(adapters は別物)」に訂正推奨。

## flag（sole-writer 規律）

- `s2_extract.py` の README 矛盾は LLM_INVOCATIONS.jsonl の CALL_SITE（`egl/structure/s2_extract.py:call` ep=:8005）で裏付け済み。
- ただし **CONTRADICTIONS.jsonl の sole writer は `s6_contradictions.py`**。sole-writer 規律により私は手で追記しない。**s6 が LLM_INVOCATIONS.jsonl を読んで s2_extract の CONTRADICTED を出す統合**を推奨（設計/管理側）。

## claim ceiling / v0.1 の既知限界

- `record_class=CALL_SITE` は §1(1) どおり「urlopen ＋ 関数が :8005/:8006//v1/chat を解決」。**:8005 の health(/v1/models) チェックも :8005 ゆえ CALL_SITE に入る**（例 test_full_live_e2e:_live_8005・class MAINLINE・model UNRESOLVED）。chat と health の細分・TEST クラスは v0.2。
- WRAPPER_DEF 検出は最小（wrapper が urlopen を直に持つ場合は CALL_SITE 側に出る）。

## ハンドオフ

- 次: **CC 再監査（byte一致 + call/mention 区別 + ゲート陰性対照 load-bearing）→ CONSISTENT → commit=Taka**。§0 grounding 訂正（egl/adapters）と s6 統合は設計/管理側で。
