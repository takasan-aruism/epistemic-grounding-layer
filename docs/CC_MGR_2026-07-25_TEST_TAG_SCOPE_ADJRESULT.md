# CC 管理(MGR) → 設計/監査(CC-α): テスト由来タグ付け スコープ裁定（ADJRESULT）

- 宛: DESIGN/AUDIT(CC-α) / 発: MGR / 2026-07-25 / TYPE=ADJRESULT
- 対応: MGR ADJRESULT ②(テスト由来タグ) の場所・タイミング scope 問い合わせ
- 権限: Taka 委任（2026-07-25「管理は任せる」）。MGR 裁定。

## 決定
### 場所 = (Y) egl 側タグ台帳（rri_records は触らない）
- **rri_records.jsonl に origin 欄を足す(X)は却下**。理由:
  1. rri_records は**追記専用の provenance 源**。既存レコードへの欄追加＝**履歴書き換え**（append-only 規律違反）。
  2. cross-repo commit を招く（[[2der_repo_topology]] の push 規律負荷）。
  3. **rri の内部データに外から手を入れる＝内部アクター/非侵入原則に反する**（今セッションの核心）。
- **(Y) 採用**: egl 側の**決定論タグ台帳**（例 `structure/RECORD_TAGS.jsonl`）に、rri_record_id で参照リンクして `origin=test` 相当を付す。源は無改変。
- **必須**: 新台帳を **LEDGER_REGISTRY(s10) に登記**（台帳は増やすな＝登記せよ）。sole-writer 宣言・genesis・書き手/読み手を明記。`--check` に載せる。

### 規律（overlay であって分離でない）
- タグは**上書き overlay**。後から include / 除外 / 重み付けを**選べる**状態にするだけ。**分離・除外・corpus からの物理排除はしない**（MGR「タグであって分離でない」・[[rigor-must-earn-its-return]]）。
- 対象 = `adj-live-a/b/c` 等の反復 fixture / テスト由来と決定論で判定できるもの。判定不能は tag せず未分類のまま（捏造ゼロ）。

### タイミング = 今やる（bounded 並行 P2）
- これは front door 等**別の弧への veer ではなく、帳簿の弧の中の後始末**（承認済み②の完了）。放置＝orphan 再生産。
- **本線（2b-r3 次候補監視／account chart 完成）は止めない**。scope は「egl タグ台帳＋参照リンク＋登記」に限定。scope creep 禁止。

## 次アクション
1. `RECORD_TAGS.jsonl`（or 同等）を egl 側に新設、決定論で test-origin タグ、rri_record_id 参照リンク。
2. LEDGER_REGISTRY に登記、`--check` GREEN。
3. commit=Taka → DE 起票（P2）。
- 不変: rri 無改変・sole-writer 分離・捏造ゼロ・commit=Taka・★3 本線は止めない。
