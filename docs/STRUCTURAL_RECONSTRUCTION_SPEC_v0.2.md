# 2DER STRUCTURAL RECONSTRUCTION — 実装仕様 v0.2

- **status: SPEC (改訂)** — v0.1 を **SUPERSEDE** する
- **authored_by: CLAUDE_CODE** — 2026-07-22
- **改訂根拠:** Stage 1〜3 の実測。すべて `docs/STRUCTURAL_RECONSTRUCTION_PROGRESS.md` §3.1–3.4 に記録済み
- v0.1 で定めた §0 目的・終了条件・反支流条項・R1〜R5・§7 トレーサビリティ試験は**そのまま有効**。
  本書は変更点のみを正本として上書きする（未言及部分は v0.1 が生きる）。

---

## §A. 改訂サマリ（v0.1 → v0.2）

| # | 変更 | 実測根拠 |
|---|---|---|
| **C1** | 辺の status に `WIRED_UNENTERED` / `TEST_ONLY_ISLAND` を追加 | §3.2 RRI formal / §3.4 IMPL-PLATFORM 30 件 |
| **C2** | **否定の主張規則**を新設（`NO` は被覆下でのみ言える） | §3.4 の自己訂正 |
| **C3** | LLM 出力の採用単位を「散文」から「引用行範囲」へ変更。3 シード合議を必須化 | §3.3 I3（散文 Jaccard 0.51 / 行範囲 0.83） |
| **C4** | LLM Stage の入口で**陰性対照**を必須化 | §3.3 I2（`guided_json` が黙殺されていた） |
| **C5** | 低生存率フィールドを単独根拠にしない。`authority_checks` は決定論に置換 | §3.3 生存率 54.2% |
| **C6** | Wave 計画を改訂（Stage 3 は LLM 不要と判明） | §3.4 |
| **C7** | 本パイプライン自身の :8005 接触を authority 記録対象とする | §4-U12 |

---

## §B. 【C1】辺の status 決定表（v0.1 §4.2 を置換）

v0.1 の決定表は `implemented / wired / executed` の 3 値だけで分類していたため、
実測で現れた 2 つの状態を表現できなかった。以下を正本とする。

| status | 定義 | 判定条件 | 実例 |
|---|---|---|---|
| `LIVE` | 呼ばれ、実行痕跡がある | caller が live 到達 ∧ 呼出点が到達 ∧ 実行証拠あり | DS→RRI→EGL→DW（117/117 トレース） |
| **`WIRED_UNENTERED`** | 呼出点は実在するが、その分岐に入らない | 呼出点が **falsy 既定の条件**の内側 ∧ 実行証拠 0 | RRI formal validation（`submit.py:97 if formal_candidates:`） |
| **`TEST_ONLY_ISLAND`** | テスト／受入ハーネスからのみ到達 | caller の到達元がテスト系に限られる | IMPL-PLATFORM 22 子項目 → `end_to_end_acceptance_harness` → 自分の回帰テスト |
| `IMPLEMENTED_UNWIRED` | 実装はあるが呼出元が無い | 呼出点 0 | — |
| `DOCUMENTED_ONLY` | 文書にあるがコードが無い | doc 参照あり ∧ 実装 0 | — |
| `MISSING` | 実装も呼出も無い | 該当なし | ① ITEM選択 → ② DWタスク生成（T-3 の対象） |
| `CONTRADICTED` | 列同士が矛盾 | 決定表のどの行にも当たらない | → `CONTRADICTIONS.jsonl` |

### `WIRED_UNENTERED` の機械的検出（新設）

呼出点を囲む `if` 条件が、**同一関数の引数であって既定値が falsy** である場合に立てる。
これは「実装済み・配線済み・しかし既定で無効」という族を機械的に拾うための検出器であり、
§3.2 の RRI 事例を一般化したものである。誤検出は `UNRESOLVED` へ送る（握り潰さない）。

---

## §C. 【C2】否定の主張規則（新設・全 Stage に適用）

> **`NO` は、そのシグナル空間が走査で被覆されている場合にのみ主張してよい。
> 被覆されていない場合は `UNRESOLVED_<理由>` とする。**

- 実例: UI / OPERATOR / AUTHORITY / AUDIT は専用の実行シグナル名前空間を持たない。
  初版はこれを `executed=NO` としたが、これは**偽の主張**であって保守的判定ではない。
- 対応する既知の非対称（v0.1 §4-U7 を昇格）:
  **`wired` の肯定は静的に可能だが、否定は静的には不可能。**
  動的ディスパッチ（`rri_formal.py:STAGES` の `fn(...)` 等）を AST は越えられない。
  コールサイトの 43.2% が未解決である。
  → **`wired=no` を主張する辺には、必ず `executed` 側の根拠を併記すること。**

---

## §D. 【C3】LLM 出力の採用単位（v0.1 §3.2/§3.4 を置換）

実測（§3.3 I3、seed 7 vs 101、25 ファイル）:

```
lifecycle_signal 一致              64%   (5値カテゴリ、偶然 20%)
actual_capabilities 内容語 Jaccard  中央値 0.51
evidence 行範囲の重なり             中央値 0.83
```

**Qwen は「どこが重要か」は安定して特定するが、「それを何と呼ぶか」は毎回変わる。**

### 採用規則（必須）

1. **真理の単位は引用行範囲であり、散文ではない。** 散文は行範囲に付くラベルとして保持する。
2. **3 シード合議を必須とする。** 同一フィールド内で **2/3 以上のシードが重なる行範囲
   （重なり ≥ 0.5）を引用した項目のみ採用**。
3. 非採用は破棄せず `UNRESOLVED.jsonl` へ隔離する。
4. 単一シードの生出力（`FILE_EXTRACTION*.jsonl`）は、**下流の根拠として使用禁止**。
   下流が読んでよいのは `FILE_EXTRACTION_CONSENSUS.jsonl` のみ。

実績: 合議 238 ファイル / 採用 3,460 / 不採用 1,078（候補の 23.8%）。

---

## §E. 【C4】陰性対照の義務化（新設）

LLM を用いる Stage は、本番投入前に**陰性対照**を通さねばならない。

> **陰性対照 = 要求した制約が効いていなければ絶対に出ない出力を要求する試験。**
> 「期待どおりの出力が出た」は、制約が効いた証拠にならない。

事故の記録（I2）: 初回のスモークテストは
`prompt: 'Return {"ok":true,"n":3} exactly.'` + 同形スキーマだった。
これは制約の有無を区別できない。結果、`guided_json` が黙殺されている vLLM ビルド上で
241 件を回し、全破棄した（OK 106 件もスキーマ非準拠）。

**確定した事実（環境依存・再検証必須）:**

| 方式 | この vLLM ビルドでの挙動 |
|---|---|
| `guided_json` | **黙って無視される** |
| `extra_body.guided_json` | 黙って無視される |
| `response_format: {"type":"json_schema", ..., "strict":true}` | **強制が効く** |

呼び出し形状は 2DER で実証済みのもの（`dev-workcell/dw/adapters.py:_vllm_chat`）に合わせる:
`temperature 0` / `seed` 指定 / `chat_template_kwargs: {"enable_thinking": false}`。

---

## §F. 【C5】フィールド別信頼度（新設）

3 シード合議の生存率は、**そのフィールドがどれだけ客観的かの実測値**である。

| フィールド | 生存率 | 取扱い |
|---|---|---|
| `actual_capabilities` | 90.4% | 単独根拠として可 |
| `claimed_capabilities` | 81.9% | 可 |
| `failure_modes` | 81.6% | 可 |
| `side_effects` | 79.1% | 可 |
| `capability_gap` | 64.7% | **要補強**（決定論的証拠と併記） |
| `limitations` | 60.6% | 要補強 |
| `authority_checks` | **54.2%** | **使用禁止。`twoder/authority.py:POLICY` の決定論的解析に置換** |

---

## §G. 【C6】Wave 計画（v0.1 §9 を置換）

Stage 3 は LLM 不要で完了した。5 状態ラダーは全列が決定論で計算できる。
**LLM の役割は「AST が出せない記述」に限定され、構造判定には一切関与しない。**

| Wave | 内容 | 並列 | LLM | 実績/予定 |
|---|---|---|---|---|
| 0 | Stage 1a–1e Inventory / 到達性 / executed | – | なし | ✅ 決定論、再実行でバイト一致 |
| 1 | Stage 2 file extraction ×3 seed + 合議 | 30 | Qwen | ✅ 生成 129 万 tok / 約 9 分 |
| 2 | Stage 3 COMPONENT_INVENTORY + ITEM_LADDER | – | **なし** | ✅ LLM 不要と判明 |
| 3 | **Stage 4 EDGE_INVENTORY** | – | 原則なし | ⬜ 次 |
| 4 | Stage 5 HISTORY_EVENTS + フェーズ分割 | – | 一部 | ⬜ |
| 5 | Stage 6 統合 / 矛盾監査 / 系譜監査 | 3–5 | Qwen + Claude | ⬜ |
| 6 | Stage 7 TR-1..6 | – | なし | ⬜ |
| 7 | 人間向け 4 本 + 既存 audit 群との diff | – | Claude | ⬜ |

矛盾検出は v0.1 §6.1 のとおり、7 種のうち 5 種を機械計算する。
本改訂により **6 種目（`ROADMAP.status=DONE` ∧ `wired=NO`）も機械計算に移す**
（§3.4 で 30 件を実測済み）。LLM に残るのは「同一コンポーネントの記述不一致」1 種のみ。

---

## §H. 【C7】本パイプライン自身の権限記録（新設）

`twoder/authority.py:POLICY` は `USE_VLLM_INFERENCE`（`:8005` への任意の接触）を
**`REQUIRES_APPROVAL`** と分類している。

Stage 2 の Qwen 呼び出しは Claude のスクリプトから直接行われ、このゲートを経由していない。
Taka の口頭指示はあるが、**2DER の機構としての承認記録は存在しない**。

規定:
1. 本パイプラインの `:8005` 接触は、実績（呼出回数・トークン・壁時計）を
   `PROGRESS.md` に記録する。**記録は承認の代替ではない。**
2. 恒常運用へ昇格させる場合は `authority.gate("USE_VLLM_INFERENCE")` 経由に改める。
   本作業は一過性の調査であるため、v0.2 では記録のみとする。
3. この扱いの可否を **Taka 裁定 5 点目**として §I に追加する。

---

## §I. Taka 裁定を要する点（v0.1 §10 を拡張）

1. `ARTIFACT_REGISTRY.used_by_live_path`（210 件中 198 件 `unknown`）への計算値書き戻しの可否
2. 生成物の置き場所を `egl/structure/` とすることの可否（第 6 リポを作らない判断）
3. TERMINAL 条件 T-3（欠損辺 ①→② の producer 仕様導出）を必須とすることの可否
4. 予算上限（現在は Claude の暫定値: 生成 200 万 tok / 1,800 s）
5. **【新規】** 本パイプラインの `:8005` 接触を authority ゲート外で継続してよいか（§H）
6. **【新規】** `ROADMAP.status=DONE` の定義。§3.4 の実測では
   「モジュールが存在し単体テストが通る」を意味し「live path に接続されている」を意味しない。
   この定義を明文化するのか、DONE 30 件を降格するのか。
