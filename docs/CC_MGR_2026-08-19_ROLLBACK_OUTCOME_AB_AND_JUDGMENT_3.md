# 宛: Taka ―― A/B 実走: **A成立・B成立、ただし reconciler は ★判定3（重大欠陥）**

**実装 0。実 repo 書き込み 0。暴走 TASK は BLOCKED のまま未接触。**

---

## 0. 結論

```
★A rollback 成功        = ★成立
★B rollback 失敗        = ★成立（★ROLLED_BACK の 虚偽記録 ★0 ／ ★fail-closed）
★★reconciler の 第3outcome 扱い = ★★判定 3（★誤って BALANCED に なる）
   → ★Taka 指示どおり ★即停止して 報告する。
```

## 1. 納品された部品（★2DER が書いた・★MGR は1行も書いていない）

```
twoder/rollback_outcome.py（★52行・commit ★ecf17c4「機械が 置いた=人の手 0」・封印試験 13本）
   def rollback_outcome(attempted, error_type, existed, disk_sha, preimage_sha)
   返り = {"outcome", "reason", "escalate"}
   ★使える語 = "ROLLED_BACK" ／ ★"ROLLBACK_FAILED" ／ None
   ★逐語「"APPLIED" は どの場合も 返さない」
   ★DESIGN の 裁定 = ★(あ)（第3の語を PATCH_APPLICATION の outcome に 入れる）
```

## 2. ★A ―― rollback 成功（★実走）

```
適用 → on-disk 'world\n' ／ PATCH_APPLICATION(APPLIED, post_apply_sha256)
復元（★energize あり）→ 例外 None ／ on-disk ★'hello\n'
部品 → {'outcome': 'ROLLED_BACK', 'reason': None, 'escalate': False}
記録 → ★['APPLIED', 'ROLLED_BACK']
★★reconciler → ★BALANCED
★ROLLED_BACK の 虚偽 = ★False
```

## 3. ★B ―― rollback 失敗（★実走・★意図的に失敗させた）

**失敗のさせ方**: `_restore_preimage(ws, plan, ★None)` ＝ energize を渡さない
（★`_require_energize` が `TypeError` を投げる）。

```
復元 → ★例外 TypeError ／ on-disk ★'world\n'（★戻っていない）
部品 → ★{'outcome': 'ROLLBACK_FAILED', 'reason': 'restore_raised', 'escalate': ★True}
記録 → ★['APPLIED', 'ROLLBACK_FAILED']
★★ROLLED_BACK の 虚偽記録 = ★0（★要件どおり）
★fail-closed = ★成立（★例外が 上へ 抜ける ／ 後続の 適用・確定 なし）
```

## 4. ★★判定 3 ―― reconciler が誤って BALANCED になる

**`ReconResult`（★case B・★全欄）:**

```
balanced                    ★True
orphans_event_without_git   ()
orphans_git_without_event   ()
baseline                    False
checked_files               ('t.txt',)
applies_seen                1
unbound_events_seen         0
★★on-disk = 'world\n'（★戻っていない＝★不可逆のまま）
★★『戻せなかった』事実が ★verdict に ★1つも 出ていない
```

### ★なぜそうなるか（★実物）

```
`_fold_expected` は ★'APPLIED' と 'ROLLED_BACK' の ★2語しか 見ない:
    if   outcome == 'APPLIED':      expected[fn] = post.get(fn)
    elif outcome == 'ROLLED_BACK':  expected[fn] = None
★★'ROLLBACK_FAILED' は ★どちらにも 当たらない ∴ ★expected を ★1文字も 動かさない
→ ★直前の APPLIED の 期待値（world の sha）が ★そのまま 残る
→ ★on-disk は 'world\n'（★戻っていない）∴ ★一致する
→ ★★covered に 入り ★BALANCED
```

### ★★これがなぜ重大か

```
★`bridge_reconciler` の BALANCED は ★飾りでは ない ―― ★`bridge_minter` の ★門(3)の 材料:
   逐語「(3) the reconciler proves a FRESH balance (bridge_reconciler.latest_balance_proof) …
         ★None/imbalanced/stale => ★refuse」
★★∴ ★『rollback に 失敗して 不可逆に なった 直後』でも ★門(3)は 通る
   ＝★★次の energize が ★止まらない。
★★『安全側に 倒れる』のでは なく ★★『青信号を 出す』方向に 倒れている。
```

**★但し 誤解のないように（★正確に書く）:**

```
★reconciler は ★'ROLLBACK_FAILED' を ★'ROLLED_BACK' と ★取り違えては いない（★無視している）。
★『git と PATCH_APPLICATION が 一致しているか』という ★自分の 定義では ★BALANCED は 正しい。
★★問題は ★その BALANCED が ★門(3)で ★『次へ 進んでよい』の 意味に 使われること。
★★＝ ★★鍵が 違う（★今夜 何度も 出た 型）。
```

## 5. ★次の修正対象（★Taka の順序どおり・★1箇所）

```
★★`bridge_reconciler` の ★第3outcome 対応 ―― ★1箇所（`_fold_expected`）。
★MGR は ★直していない ／ ★どう 直すかも ★決めていない（★DESIGN 案件）。
★★材料（★参考・★決定ではない）:
   ・'ROLLBACK_FAILED' が 在る 間は ★balanced を 立てない、という 形が 素直
   ・★但し ★`ReconResult` に 欄が 増える か ★`balanced` の 意味が 変わる ∴ ★DESIGN が 決める
   ・★`emit_reconciliation` / `latest_balance_proof` の 形は ★触らない 方が 影響が 小さい
```

## 6. ★完了条件に対する結果

| 条件 | 結果 |
|---|---|
| A 成立 | **★成立** |
| B で `ROLLED_BACK` の虚偽記録 0 | **★0件** |
| B で fail-closed | **★成立** |
| reconciler の第3outcome 扱いを 1〜3 で確定 | **★★3** |
| 実 repo 書き込み 0 | **★成立**（すべて `/tmp/rb*` 配下） |

## 7. していないこと

```
★実装 0行 ／ 判断ロジック 0行 ／ 配線 0
★patch fingerprint / post_apply_sha256 / allowed_files / preimage / provenance /
  bridge_minter / authority / 実 repo energize の 意味を 1つも 変えていない
★暴走 TASK TASK-2DER-32EDB6C4 は ★BLOCKED のまま 触っていない
★connector 本線接続・delegated energize・初回 real-repo に 進んでいない
```
