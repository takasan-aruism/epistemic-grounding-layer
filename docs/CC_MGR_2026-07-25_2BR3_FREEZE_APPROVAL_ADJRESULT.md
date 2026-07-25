# CC 管理(MGR) → 設計(DESIGN): 2b-r3 凍結承認 + テストタグ follow-up（ADJRESULT）

- 宛: DESIGN(CC-α) / 発: MGR / 2026-07-25 / TYPE=ADJRESULT
- 対応: DE-0532 の 2b-r3 `PROPOSED(1 awaiting Taka)` = `CAND-48354b9a`
- 権限: **Taka 承認済み（2026-07-25・管理経由）**。#3 規律（凍結は Taka 承認）を満たす。

## 決定
### ① CAND-48354b9a の凍結を承認 → v2 へ凍結
- 承認 marker（`FREEST_APPROVALS` に `CAND-48354b9a`）を投入し、2b-r3 の no-auto-freeze 機構に沿って **v2 として凍結**。marker 無しでは凍結しない不変は維持（この承認が唯一の解錠）。
- 根拠（Taka 裁定の要旨）: 中身は「小さなデータ処理 CLI ツールを作る依頼」の**本物の一貫カテゴリ**（silhouette>sub で QUALIFIED、content_diversity 0.79=退化でない）。34件の多くがテスト由来の反復だが、**それは凍結を止める理由にならない**——
  - 我々は**客のいない自己利用システム**で、テスト依頼こそ実際の使用の中身。誤認する"本物の需要"が存在しない。
  - account 棚は **soft/advisory（何も gate しない）** ＝テスト水増しの**下流コストが具体的に無い**。
  - 将来の本物の同種依頼も同じ棚に入る＝カテゴリ自体は正当。

### ② テスト由来レコードにタグ（follow-up・構造は止めない）
- テスト由来（例: `adj-live-a/b/c` など既存タグ、反復 fixture）に **`origin=test` 相当のタグ**を付す。目的は「後から含む/除く/重み付け」を可能にすること。**タグであって分離・除外ではない**（棚は失わない・measure-first 不変）。
- これは "テストと本番を厳格分離" ではない。厳格分離は客のいる納品の方便で、我々には具体的リターンが無い（Taka 指摘）。**区別したい時に選べる状態にしておくだけ。**

## 次アクション（設計/実装）
1. `FREEST_APPROVALS` に `CAND-48354b9a` を authored 投入 → 2b-r3 再実行で v2 凍結、承認 provenance を記録（誰が=Taka・いつ・どの候補か）。
2. テスト由来タグ付けの最小 follow-up を起票（別 DE 可・P2）。
3. 各 --check GREEN 確認 → commit=Taka → DE 起票。
- 不変: DE台帳を corpus へ戻さない・sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない。
