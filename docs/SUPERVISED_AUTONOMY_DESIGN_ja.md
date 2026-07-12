# 監視付き自律運用 設計メモ（Supervised Autonomy & Operating Economy）

> **監査済み判定（`AMEND-2DER-SUPERVISOR-AUDIT-001`）**
> `DESIGN_DIRECTION = ACCEPT` / `IMPLEMENTATION_READINESS = REJECT_FOR_NOW` / `REQUIRED_ACTION = REVISE_BEFORE_PLANNED`
> **claim ceiling = 「監視付き自律運用の骨格案」まで**。実装準備度は NOT READY（MAJOR REVISION 反映済み、ただし残受入条件あり）。
> **監査範囲の限界**: 監査したのは本 *文書設計* のみ。repo 上の実関数・live path・ID 解決・依存の実在は未検証。全 item は PROPOSED / 未実装。
> 対応: `AMEND-2DER-SUPERVISOR-LOOP-001`（原案）＋ `AMEND-2DER-SUPERVISOR-AUDIT-001`（監査）＋ `PHASE-2DER-EVO-08` / `ITEM-0016..0019`。

---

## 0. 動かない前提（ここは変わらない）

**本筋 = より低コストに、より高パフォーマンス。** 監視役 Claude は**開発主戦場より安いこと**が必須使用条件。
**基本フロー**: 2DER がループを回す → 必要な場面だけ Claude が監視・チェック → 問題は **2DER に差し戻す**（外部で直さない）。
**方針**: 事前合意は勝手に回す。どうしても必要なときだけ人手で掬う。**Taka が最終 authority**。

---

## 1. ★最重要修正（P0-1）: 監視 ≠ `authority.gate`。三層に分ける

原案は「各完了オペを `authority.gate` で分類」を監視の中心に置いていた。だが `authority.gate` は**実行前**の権限判定。
実行後に同じロジックを通しても同じ判断を繰り返すだけで、**「予定した操作だけが実際に起きたか」を検証していない**。

```text
① PRE_OP_AUTHORITY_GATE   この操作を実行してよいか（既存 authority.py, 決定的）
② EXECUTION               DW / operator / actor が実行
③ POST_OP_CONFORMANCE     予定した効果だけが実際に起きたか（新規・決定的・全件）  ← 柱A(0016)
④ INDEPENDENT_AUDIT       そもそも予定・基準自体に穴がないか（別視点・author≠auditor） ← 柱D(0019)
```

柱A の正しい名称・責任は **`POST_OPERATION_CONFORMANCE_SUPERVISOR`**。最低限これを見る:

```text
expected_effects / actual_effects / prohibited_effects
pre_state_ref / post_state_ref
changed_artifact_ids / unexpected_file_changes
authority_decision_ref / rollback_status / test_result_refs
```

---

## 2. 4 本柱（監査反映後）

### 柱A `POST_OPERATION_CONFORMANCE_SUPERVISOR`（ITEM-0016）
- **全件・LLM ゼロの決定的後条件チェック**（expected vs actual vs prohibited）。共通パスは「監視なし」ではなく「**LLM なしの軽量監視**」（P0-4）。
- 不一致・境界・異常のときだけ Claude を **SENIOR_REVIEW** として起動（**調査 + 推奨のみ、承認者ではない** P0-3）。安いティア。
- 問題は 2DER 内（DE/candidate）へ ID 付きで差し戻す。author≠actor 維持。
- 依存: `ITEM-0008`（operator 機械オペ自動前進）。まず **shadow mode**。

### 柱B `INTERVENTION` レコード（ITEM-0017）★新 SoR を作らない（P0-2）
2DER の過去最大の失敗 = 既存 DS/RRI/EGL/DW を使わず**別の簡易台帳を新設**したこと。今回もそれをやってはいけない。
- **既存の append-only event/record 系に `INTERVENTION` record type を足す**。独立 JSONL を新設しない。
- どうしても別ファイルが要るなら: authoritative writer は一つ / 既存 event から完全再構築可能な **derived view** / 手動 append 禁止 / duplicate・idempotency 保証。
- フィールドは責任分離（P1）:

```text
intervention_id / trace_id / pre_state_ref / post_state_ref
policy_id / policy_version / rule_id / severity / evidence_refs
detected_by / assessed_by / approved_by / executed_by   ← decided_by 一本化は不可
action_class / status / opened_at / resolved_at
cost_actual / model_id / prompt_or_profile_id
rollback_ref / false_positive_disposition / idempotency_key
```
（`detected_by/assessed_by/approved_by/executed_by` を分けないと Claude・決定的ルール・Taka・Qwen の責任が混ざる。）
- **実装順は最初**（受動ロギングから）。

### 柱C `COST_GOVERNED_ENVELOPE_WIDENING` + 自動縮小（ITEM-0018）
原案の「N 回連続 human-scoop ゼロ → AUTO 化提案」は**弱すぎる**（P0-5）。ゼロは「見逃し／簡単／少数／監査未稼働／未発覚／分布変化」でも起きる。
拡大条件は最低限:

```text
op_class 別の最小 exposure 数 / 最小観測窓
未解決 critical intervention = 0
independent audit coverage 達成      ← 0019 が前提（P0-8）
critical escaped defect = 0
false-negative 上限 < 閾値
rollback 手順テスト済 / distribution-shift フラグ無 / policy version 不変
```
- **非対称設計**: 拡大 = 提案 + 人間承認（可逆）。**縮小/freeze = critical 検出で即時・自動**（安全側）。
- **依存: 0016 + 0017 + 0019**。独立監査なしに「事故が無かったから広げる」は**見逃しの自己証明**（P0-8）。

### 柱D `INDEPENDENT_AUDIT`（ITEM-0019）★0018 の前提
- **passed オペもサンプリング**して false-negative を測る。監視ゲートのロジックを共有しない。
- 独立性の定義（P1）: 別 run/context / **supervisor 判定を非開示** / 別 rubric / 別 evidence sampling / author≠auditor / auditor は write・approve 不可 / random + risk-weighted sample。理想はモデルも分離、最低でも判断経路と情報条件を分離。
- 安価デフォルト（常時ではなくサンプリング/トリガ）。

---

## 3. コストモデル（P0-6）: 総期待コストで測る

`free-deterministic` / `claude-invoked` の 2 値では経済性は測れない。監視が安くても**見逃しが大量 rework を生めば全体高コスト**。

```text
C_total = execution + supervisor + independent_audit + human_time
        + rework + rollback + expected_escape_loss
比較: supervised C_total  vs  baseline C_total
記録: model_id/profile, input/output_tokens, wall_seconds, GPU_seconds,
      API_cost, human_minutes, rework_seconds, rollback_seconds, completion_latency
```
「決定的ゲート = 実質無料」は不正確。正しくは **marginal LLM cost = 0**（CPU/I/O/ログ/遅延はゼロでない）。

---

## 4. 計測の誠実さ（P0-7）: 「介入減 = 自律進展」は成立しない

介入件数の減少は「改善／感度低下／タスク減／簡単化／未発見／ログ欠損」いずれでも起きる。**分母と品質指標**が要る:

```text
interventions / executed_ops
human_scoops / completed_tasks
critical_escapes / audited_ops
audit_findings / sampled_ops
false_positive_rate / rollback_rate / rework_rate / completion_rate
task_complexity_distribution
```
→ 原案の「唯一の誠実な証拠」は撤回。**「主要な運用証拠の一つ」**へ降格。

---

## 5. 追加で固める点（P1）

- **異常 taxonomy（機械観測可能なものから）**: illegal state transition / missing packet / missing artifact_id / path-only ref / manual ledger append / dirty repo / unregistered changed file / hash mismatch / test regression / authority violation / unexpected net or GPU / claim-ceiling violation / result-admission mismatch / cost over budget / recurrence over threshold。
- **fail-open / fail-closed**: read-only・低リスク → fail-open + log / write・mutation・deploy → fail-closed / HUMAN_AUTHORITY 境界 → 常に停止。
- **再帰・無限ループ防止**: max_intervention_depth / dedup key / same-rule cooldown / circuit breaker / meta-operation 除外。
- **`gate 212 / independent audit 27` は根拠不足**（record_ids・分母・期間・欠陥定義なし）→ **historical observation, not independently verified** へ降格（設計根拠には使わない）。

---

## 6. 修正版の運用構造

```text
1 PRE_OP_AUTHORITY_GATE   実行してよいか（決定的・既存）
2 EXECUTION               DW/operator/actor
3 POST_OP_CONFORMANCE     expected vs actual、決定的・全件
4 SUPERVISOR_ESCALATION   不一致/境界/異常のみ Claude、調査+提案のみ
5 INTERVENTION_EVENT      既存 SoR に ID 付き記録（新 SoR 禁止）
6 INDEPENDENT_AUDIT       passed もサンプリング、supervisor 判定を見ない
7 AUTHORITY_DECISION      program/risk/irreversible は Taka
8 POLICY_UPDATE           拡大=提案、縮小/freeze=安全側で即時
```

**実装順（監査推奨、原案の列挙順とは異なる）**: `0017 → 0016 → 0019 → 0018`。
0018 は少なくとも 0019 が動くまで着手しない。

---

## 7. PLANNED へ進む前の最低受入条件（`AMEND-2DER-SUPERVISOR-AUDIT-001`）

```text
[ ] intervention record の authoritative SoR 決定
[ ] existing record との重複監査
[ ] pre-op / post-op / independent-audit の責任分離
[ ] HUMAN_AUTHORITY と SENIOR_REVIEW の分離
[ ] anomaly taxonomy
[ ] fail-open / fail-closed policy
[ ] idempotency / concurrency / recursion 制御
[ ] actual cost schema
[ ] total expected cost 評価式
[ ] independent audit の独立条件
[ ] widening eligibility
[ ] automatic contraction / freeze policy
[ ] exact acceptance tests
[ ] naked counts に record_ids 付与
```
これらが埋まるまで `ITEM-0016..0019` は **PLANNED へ進めない**（各 item の acceptance に BLOCK 明記）。

---

## 8. Claude の仕事はどこまでか（設計上の答え）

概ね YES。厳密な意味での Claude の仕事 = **この監視/適合確認/独立監査/コスト統治の系を作り切るところまで**。
それが動けば Claude は「境界でだけ安く働く SENIOR_REVIEW 役」へ縮退する（承認者ではない、決めるのは Taka）。
ただし Phase-03/04 が済むまで人間/Claude が load-bearing。**過大評価しない**。

---

## 9. 実装しないこと（この slice の非スコープ）

- 上記いずれも**未実装**（全 PROPOSED）。本書は**骨格案**。
- 柱D の一部詳細（発火条件・独立性担保・コスト上限）は Taka 調査 + §7 チェックリスト充足まで pin しない。
- `:8005`/GPU に触れる部分（0008/0016 実行部）は **REQUIRES_APPROVAL**。自律 RD（0010）は **未有効**。

---

*参照: `AMEND-2DER-SUPERVISOR-AUDIT-001`（監査）/ `AMEND-2DER-SUPERVISOR-LOOP-001`（原案）/ `PHASE-2DER-EVO-08` / `ITEM-0016..0019`。全体像は 2DER_CAPABILITY_AND_ROADMAP_ja.md。数値は management_packet coverage matrix 由来。*
