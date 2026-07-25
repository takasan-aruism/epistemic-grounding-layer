# 設計/監査 → MGR: account 軸命名の判断2点（ADJREQ）

- 宛: MGR
- 発: 設計/監査(CC-α, DESIGN) / 2026-07-25 / TYPE=ADJREQ
- 対応: `CC_IMPL_2026-07-25_ACCOUNT_AXIS_NAMING_2b2_BUILT.md`
- 前提: 命名**機構は CONSISTENT**（独立検証済: 幾何 byte 不変 / サンプル決定論 / consensus 記録再判定 / provenance 完全 / 実 :8005 CALL_SITE 登録[24→25] / 全 gate GREEN）。id 正典・name 装飾・measure-first 厳守。以下は name の妥当性判断のみ。

## 命名結果
| axis | name | status | 3-seed proposals |
|---|---|---|---|
| AX-72ead44e (114 REQUEST) | 「Pythonモジュール実装」 | CONSENSUS 2/3 | Pythonモジュール新規作成 / **Pythonモジュール実装** / **Pythonモジュール実装** |
| AX2-48354b9a (28 REQUEST) | null | UNRESOLVED 1/3 | JSONLファイル解析CLI / JSONLファイル解析CLI作成 / JSONLファイル統計解析 |

## 判断①: AX-72ead44e = 「Pythonモジュール実装」を受容してよいか
- **DESIGN 推奨 = 受容**。114件の patch_bridge 実装依頼を的確に表す簡潔ラベル。やや broad だが id が正典・後で変更可。異議なし。

## 判断②: AX2 の UNRESOLVED — 厳密 consensus が意味一致を却下している（核心）
- 3 seed は**主題が明確に一致**（全て「JSONLファイル解析」）。seed0/1 は末尾「作成」差のみ、seed2 は「統計解析」。**厳密 normalized 完全一致 <2/3 ゆえ機械的に UNRESOLVED**。
- これは私の spec §3（正規化後の**完全一致** ≥2/3）が**過剰に厳密**な結果＝**揺れを許容すべき所（LLM の name 語尾ゆれ）に非許容ルールを当てた**。[[llm_arithmetic_drift_tolerant_design]]（Taka 訂正: 分類は機械で事前結晶化できない・LLM→consolidation で徐々に固める）に照らすと、この UNRESOLVED は**false-negative の疑い濃厚**。
- **DESIGN 推奨 = consensus を drift-tolerant な決定論 consolidation に精緻化**（新 LLM/embedding 不要・--check 再判定は決定論のまま）:
  - 例: 記録 proposals に **共通語幹抽出**（末尾 作成/CLI/ツール 等の装飾 suffix を決定論除去）or **支配的共有名詞トークン ≥2/3** で consensus 判定。→ AX2 は seed0/1 が「JSONLファイル解析CLI」で一致 or 共有核「JSONLファイル解析」で採用。
  - これで AX2 が命名成立（drift 許容・かつ決定論再判定可能）。
- 代替 = 現状 UNRESOLVED を honest として受容（LLM が exact 名を安定生成できない＝category が fuzzy の証、という解釈）。

## 依頼
- ① 受容でよいか。② consensus 厳密性を drift-tolerant 決定論 consolidation に緩めるか（推奨・Taka の分類哲学に整合）/ UNRESOLVED 受容か。**②は Taka の揺れ許容方針に触れるため最小 set で Taka 確認が要れば MGR 経由で。**
- 保留: 命名の commit は②裁定まで保留（AX2 の name が変わりうるため churn を避ける）。機構・AX-72ead44e 命名・幾何不変は達成済み。

---
*DESIGN CC-α。ADJREQ。機構は健全、name 妥当性の2点のみ。過剰厳密 consensus が意味一致を殺す false-negative を独断で緩めず上程。★3 本線＝これ自体。*
