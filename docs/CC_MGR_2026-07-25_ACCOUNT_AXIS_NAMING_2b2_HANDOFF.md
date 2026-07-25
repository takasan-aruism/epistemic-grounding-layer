# CC 管理(MGR) → 設計/監査(CC-α): 勘定科目の命名（2b-2）HANDOFF

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-25 / TYPE=HANDOFF
- 位置づけ: ★3 本線＝帳簿「見つける層」完成の残り。凍結済み棚に人間可読な名前を付ける。
- **:8005 ゲート**: **Taka が USE_VLLM_INFERENCE を本タスクに開放（2026-07-25・LLM 実行 OK）**。

## 目的
今、凍結棚は ID だけで名無し（`ACCOUNT_AXES_v2`: `AX-72ead44e` / `AX2-48354b9a`、`name:null`）。中身に基づく**簡潔な名前**を付け、帳簿を人間可読にする。

## 方式（LLM 3-seed consensus）
- 各凍結棚について、その所属レコードの**実 content を代表サンプリング**（決定論・件数と抽出は固定）し、Qwen3.6-35B-A3B(:8005) に「このまとまりを表す簡潔なカテゴリ名」を提案させる。
- **3 seed で実行し、≥2/3 一致した名前を採用**。一致しなければ `name: "UNRESOLVED_NO_CONSENSUS"`（**無理に付けない＝measure-first・捏造ゼロ**）。
- 決定論部（サンプリング/一致集計）は決定論、LLM 呼出のみが非決定論。**命名 provenance（model/seeds/サンプルID/一致結果）を記録**し監査可能に。

## 規律（重要）
- **name は id の"ラベル"であって identity ではない**（RRI spec）。**id が正典・name は後で変えられる装飾**。命名で**凍結メンバーシップ/軸の幾何は一切変えない**（v1/v2 不変を維持、name フィールド追記のみ・versioned）。
- 対象は **v2 の凍結棚2つ**に限定（RESIDUAL/未凍結候補は命名しない）。scope creep 禁止。
- sole-writer 分離・全 --check GREEN・commit=Taka・**★3 本線＝これ自体**。
- 命名は初の実 :8005 CALL_SITE になる→ LLM_INVOCATIONS に真の呼出点として登録（meta self-heal(DE-0536) が commit 境界で fold）。

## 依頼フロー
1. DESIGN: 命名 spec（サンプリング規則・prompt・consensus 判定・provenance schema・不変テスト）を起票 → IMPL。
2. IMPL: 実装（:8005 実行込み）→ AUDIT 独立再監査。
3. 命名結果を DESIGN/MGR へ（棚名が妥当か・consensus 経路が正しいか）。**"本物の話題名 or 塊"の最終判断が要れば MGR 経由で最小 set を Taka へ**。
4. --check GREEN → commit=Taka → DE 起票。

## 完了後
これで帳簿「見つける層」完成に到達（残 P2 後片付けは DE-0536 でほぼ済）。→ front door 復帰の区切り候補（Taka 確認事項として保持）。
