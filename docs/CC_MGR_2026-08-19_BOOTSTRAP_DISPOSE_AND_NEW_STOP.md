# 宛: Taka / 設計 / 監査 ―― ブートストラップ DISPOSE（★1回・別記録）と、新しい停止点

**★この1回は「通常運転の Claude 依存」に数えない。★能力起動のブートストラップとして別に記録する。**

## 0. ブートストラップの記録（★1回だけ・Taka 裁定 A 2026-08-19）

```
対象      = TASK-2DER-6AC3EA20（dispose_decision・封印試験17本）
入口      = front door ★/api/ingest（★既存の正規口）
実施者    = ★対話型 MGR Claude（★今回に限り Taka が許可）
記録      = dispose_runs 1件 ／ ★identity = "claude-manager"
結果      = state ★DISPOSITION_REQUIRED → ★READY_FOR_UPPER_REVIEW
★queue へ 手で 追加 = 0 ／ ★run_next = 0 ／ ★Taka 途中裁定 = 0
```

### 判断の根拠（★記録との突き合わせ・★所見の文章の善し悪しではない）

**封印試験が何を要求しているかを読んだ:**

```
試験は ★単一エラーだけを 検査する
   assert r["names"] == ["PASS"] ／ ["F9"] ／ ["F1"] ／ ["F1"]
★複数行の エラー蓄積を 要求する 試験は ★1本も 無い
```

| finding | category | verdict | 根拠 |
|---|---|---|---|
| `AF-…seed101-run-0` | scope_expansion (high) | **REJECTED** | 「早期 return は誤り」の主張だが**封印試験が要求していない**。★所見自身の `suggested_check` が「試験が複数 ID を期待するか**確認せよ**」＝確認したら期待していなかった |
| `AF-…seed101-run-1` | requirement_not_implemented (medium) | **REJECTED** | 同じ根拠。★所見自身が「`names` は昇順」の実装を `correct` と認めている |
| `AF-…seed101-run-2` | self_report_primitive (low) | **REJECTED** | ★所見自身が「While the spec requires these specific strings」と書いており、**契約がその語を要求している** ∴ 欠陥ではない |

**★3件とも「契約（骨格＋封印試験）の外ではない」という一点で決めた。**

## 1. ★新しい停止点 —— 自走再開しなかった

```
★DISPOSE 後 14分（★1分ごとに観測）:
   state        = READY_FOR_UPPER_REVIEW（★変化なし）
   upper_reviews= ★0
   _queue()     = ★[]
   _last_task() = ★None
```

### なぜ止まったか（★実測で2つ潰し、1つ残った）

常駐は barrier に当たった task を**並びから落とす**（頭詰まり防止の既存作法）。
落とした task を拾い直す**自己修復の経路は在る**（`manager_v0._last_task()` の中・逐語
「★★2026-08-15 19:5x 実測=★★投げた 案件が ★並びから 落ちていた…∴ ★★★投げた 記録から 拾い直す(★自己修復)」）。

**★その自己修復関数を呼んだら `None` を返した。**

```
自己修復の 除外条件 3つ:
   ① tid in queue            → ★queue は [] ∴ 該当しない（★実測）
   ② not _machine_turn(st)   → ★READY_FOR_UPPER_REVIEW は _machine_turn=★True ∴ 該当しない（★実測）
   ③ tid in done（受領済み） → ★残るのは これだけ
```

**★③は消去法の推定。★UNKNOWN のまま残す。**
確かめるには `runs/manager_done_index.json` の横読みが要り、**★禁止されているのでしていない。**

### ★心当たり（★推定・★確定ではない）

```
この task は ★機械が 既に 成果物を 置いて commit している
   commit 8ff2324「[2DER実装] dispose_decision: TASK-2DER-6AC3EA20
                   (★機械が 置いた=★人の手 0 ／ ★Taka 許可 2026-08-17)」
∴「成果物は 受け取った」扱いに なり得る
   ★一方 DW の state は まだ READY_FOR_UPPER_REVIEW
＝★★常駐の 帳簿では『済み』／ DW 正本では『途中』= ★★鍵が 違う
```

**★同型が今夜も出ている**（`/api/roadmap` 136 と `items()` 144 ／ `MANAGER_V0` の大小 ほか）。

## 2. ★完了条件に対する結果

| 条件 | 結果 |
|---|---|
| ブートストラップ Claude DISPOSE = 1回 | **★成立**（1回・`claude-manager`） |
| それ以外の対話型 Claude DISPOSE = 0回 | **★成立**（0回） |
| headless Claude actor が本線接続される | **✗ 未達**（★部品 `dispose_decision` は置かれたが★配線は別・未確認） |
| judgment-required を1件 headless で処理 | **✗ 未達**（★到達しなかった） |
| disposition 記録後に 2DER が自走再開 | **★✗ 未達 ―― ここが新しい停止点** |
| Taka 途中裁定 0 | **★成立**（0） |

## 3. ★次の停止点（★1つだけ）

```
★★barrier で 並びから 落とした task を、★barrier が 解けた 後に 誰も 並びへ 戻さない。
   ・自己修復の 経路は ★在る（`_last_task()` の 中）
   ・★その 関数が この task に対して ★None を 返す
   ・除外条件の ①② は 実測で 否定済み ∴ ★③（受領済み扱い）が 残る＝★UNKNOWN
```

**★これは接続の欠落でも安全境界でもなく、★「2つの帳簿の食い違い」の型。**

## 4. ★副次的に判明したこと

```
★機械が 成果物を 置いて commit する 経路は ★動いている（★人の手 0）
   7ae9a60 tasks_to_enqueue（TASK-2DER-4E2A58F2）
   8ff2324 dispose_decision（TASK-2DER-6AC3EA20）
★★COMPLETE を 待たずに 配置される（★置いてある≠繋がっている ／ ★置いてある≠完了している）
```

## 5. していないこと

```
★許可された DISPOSE 1回 以外の 代行 0
★run_next 0 ／ queue へ 手で 追加 0 ／ Taka へ 追加質問 0
★_MAP / _TEST_CATEGORIES / disposition 規則 / 安全境界を 触っていない
★runs/ の 横読みを していない（★③を 推測で 断定していない）
★止まった先を Claude が 穴埋めしていない
```
