# 監視付き自律運用 設計メモ（Supervised Autonomy & Operating Economy）

> **status: PARTIAL DESIGN — 一部確定 / 一部 Taka 調査中**
> `AMEND-2DER-SUPERVISOR-LOOP-001` / `PHASE-2DER-EVO-08` / `ITEM-2DER-EVO-0016..0019`（すべて PROPOSED）に対応する設計ドラフト。
> 起点: Taka 方針 2026-07-12「回っているループを**誰がチェックするのか**を機構化する」。実装は未着手。

---

## 0. 動かない前提（ここは変わらない）

**本筋 = より低コストに、より高パフォーマンス。**
Claude を監視役に使う場合、**開発の主戦場にいるより安いこと**が必須の使用条件。安くないなら使う意味がない。
→ この "hard cost condition" を設計の各所に一級の制約として埋め込む（success metric にも含める）。

**基本フロー**: 2DER がループを回す → 必要な場面だけ Claude が監視・チェック → 問題があればそれを **2DER に差し戻す**（外部で直さない）。
**個人方針**: 事前に決めたことは勝手に回す。どうしても必要なときだけ人手で掬う。そこまで自動化できるなら尚良い。

---

## 1. 4 本柱

### 柱 A — 監視ループ `SUPERVISOR_LOOP`（ITEM-0016）
2DER が DW/operator ループを回している間、各完了オペを分類する監視を走らせる。
- **決定的ゲート優先**: まず `authority.gate`（LLM を使わない純関数）で分類。**共通パスは LLM ゼロ = 実質無料**。
- **境界だけで Claude を呼ぶ**: `AUTO_EXECUTE` のオペは黙って通す。`REQUIRES_APPROVAL` 境界 or 異常フラグのときだけ Claude を起動。しかも**主戦場より安いティア**で。
- **差し戻し**: 問題は 2DER の中（DE / candidate）へ ID 付きで戻す。out-of-band で直さない（author≠actor 維持）。
- 新しい知能パイプラインではない。既存 `authority` + `dispatch` の上に載る read-only 監視。

### 柱 B — 介入台帳 `INTERVENTION_LEDGER`（ITEM-0017）
監視介入を**一級の 2DER レコード**にする。`INTV-NNNN`:
| フィールド | 内容 |
|---|---|
| `ts` / `task_id` / `op` | いつ・どのタスクのどのオペで |
| `trigger` | deterministic-gate / anomaly のどちらで発火したか |
| `reason` | なぜ介入が要ったか |
| `action` | 何をしたか |
| `resolution` | 2DER へ差し戻した先の ref（DE/candidate id） |
| `decided_by` | **AUTO**（自動判定）/ **HUMAN_SCOOP**（人手掬い上げ） |
| `cost_class` | **free-deterministic**（ゲートのみ）/ **claude-invoked**（+ ティア） |

これが「自律が進んだ」の**唯一の誠実な証拠**になる：介入件数が減る + 人手掬い上げが減る。回帰テストの緑と同じ位置づけ。
DE 台帳と同じ **sole-writer 規律**（手動 append しない）。件数・コストは coverage matrix から引ける。

### 柱 C — コスト駆動のエンベロープ拡大 `COST_GOVERNED_ENVELOPE_WIDENING`（ITEM-0018）
今のヘビーな per-slice 承認体制は「掬い上げポイントが未計測」だから全部に人手を張っている。台帳が出れば**緩めてよい場所がデータで判る**。
- あるオペクラスが **N 回連続で human-scoop ゼロ** → そのクラスを `REQUIRES_APPROVAL → AUTO_EXECUTE` 方向へ移す **提案**を出す。
- エンベロープ変更自体は **REQUIRES_APPROVAL + 可逆**（一度は人間承認、いつでも戻せる）。
- **勝手な自動拡大はしない**。緩和は勘ではなく台帳が根拠。

### 柱 D — 独立監査チェック `INDEPENDENT_AUDIT_CHECK`（ITEM-0019）★一部 Taka 調査中
監視（柱 A）とは**別に**、独立した監査の目を入れる。
- **author≠auditor**: 監視ゲートのロジックを**共有しない**第二の視点。決定的ゲートが取りこぼすものを捕まえる。
- 位置づけ: 柱 A は「事前合意の範囲内か」を判定（コンプライアンス寄り）。柱 D は「そもそも判定基準が漏れていないか」を突く（別視点検出）。retention>detection の実績（gate 212 / independent audit 27 が実欠陥を反復検出）と整合。
- **同じ hard cost condition に従う**（デフォルト安価）。常時フル監査ではなく、サンプリング / トリガ起動で薄く回す。
- **⚠️ 設計未確定**: 発火条件・独立性の担保方法・コスト上限は Taka 調査後に pin する。ここは意図の骨子のみ。

---

## 2. コスト条件の埋め込み（どこで安さを担保するか）

| 層 | 安さの担保 |
|---|---|
| 共通パス | 決定的 `authority.gate` のみ = **LLM 呼び出しゼロ** |
| 起動条件 | Claude はオペ毎ではなく**境界/異常のみ**で起動 |
| ティア | 監視で Claude を呼ぶときは**主戦場より安いモデル/推論強度** |
| 計測 | 台帳の `cost_class` で free-deterministic と claude-invoked を区別、コスト/タスクを算出 |
| 成功判定 | **supervisor cost/task ≪ main-dev cost/task** かつ 介入件数が減少 |

監査チェック（柱 D）も同様に、常時ではなくトリガ/サンプリングで薄く。

---

## 3. 既存ロードマップとの噛み合わせ

- **柱 A（0016）** は Phase-03 の **0008（operator 機械オペ自動前進）** の上に載る → depends_on 0008。
- **柱 C（0018）** は Phase-04 の **0010（自律RD有効化）** の前提を安全に用意する（envelope をデータで広げる）。
- 実行経済 **Phase-07** はモデルコスト、本 Phase-08 は**運用コスト（誰がどれだけ人手/LLM を食うか）**。相補。

---

## 4. Claude の仕事はどこまでか（設計上の答え）

Taka の問い「このシステムの実装くらいまでが厳密な意味であなたの仕事か?」への設計上の回答:
**概ね YES。** 厳密な意味での Claude の仕事 = **この監視/台帳/コスト統治の系を作り切るところまで**。
それが動けば Claude の役割は「主戦場の開発者」から「**境界でだけ安く働く監視役**」へ圧縮される。
台帳が「人手掬い上げゼロ」を示すオペクラスが増えるほど、Claude の関与は薄くなる —— それが設計の目標状態。
（ただし §1 の通り、ループを回す主体が系になる Phase-03/04 が済むまでは、まだ人間/Claude が load-bearing。過大評価しない。）

---

## 5. 実装しないこと（この slice の非スコープ）

- 上記いずれの item も**未実装**（全 PROPOSED）。本書は設計ドラフト。
- 柱 D の詳細は **Taka 調査待ち**で pin しない。
- `:8005`/GPU に触れる部分（0008/0016 の実行部）は当然 **REQUIRES_APPROVAL**。
- 自律 RD（0010）は依然 **未有効**。

---

*参照: `AMEND-2DER-SUPERVISOR-LOOP-001` / `PHASE-2DER-EVO-08` / `ITEM-2DER-EVO-0016..0019`。全体像は [2DER_CAPABILITY_AND_ROADMAP_ja.md] 参照。数値は management_packet coverage matrix 由来。*
