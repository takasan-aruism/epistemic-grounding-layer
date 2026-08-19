# 宛: DESIGN（監査 CC）―― 契約作成の依頼: 同一入力の UPPER_REVIEW 再実行を抑止する純関数

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。この文書は要件と実データだけです。**

---

## 1. 直したいこと（★1点）

```
同一 TASK・同一 state・同一入力に対して ★高価な actor（`claude -p`）が 繰り返し 呼ばれた。
★実測: TASK-2DER-32EDB6C4 で ★15分に 29回（★1巡回で 12回＝`run_until_barrier` の `max_ops=12`）。
★止まったのは 抑止では なく ★task が queue から 落ちた 偶然。★再発する。
```

## 2. ★DESIGN が選ぶ2案（★Taka 指定・★MGR は選ばない）

```
A. ★`_ordinal` ベース
   「最後の upper_review より 後に generate / regenerate / audit / dispose が
     1つも 無ければ 再実行しない」
   ＋ ★記録に 欄を 1つも 足さない（★実測: 5種類の 記録すべてが `_ordinal` を 持つ）
   − ★「記録は 増えたが 中身は 同じ」を 区別できない

B. ★入力 fingerprint ベース
   `senior_review.build_prompt(task_id, view)` が ★既に 集めている 値で 同一性を 言う:
     task_id / state / last_test_passed / rework_count / completion_blockers /
     findings / record_test_passed / artifact_sha256 / artifact_head
   （★同関数の 逐語「★渡す物は 記録に在る値だけ(★申告を混ぜない)」）
   ＋ ★入力の 中身が 同じかを 直接 言える
   − ★同一性を 後から 言うには ★記録に 欄を 1つ 足す 必要が 在り得る（★DESIGN が 判断）
```

**★選定条件（★Taka 逐語）:**

```
・初回は 必ず 実行           ・入力変化後は 再実行可能
・入力不変なら 呼ばない       ・fail-closed 維持
・authority / _MAP / disposition 規則は ★変更しない
・★抑止した 事実と 理由を ★既存記録へ 残す
```

## 3. ★局所か一般か（★DESIGN が決める）

```
★局所 = UPPER_REVIEW だけ 抑止
★一般 = `run_until_barrier` の 停止条件に progress guard を 足す
   現在（`dw/dispatch.py:178-184` 逐語）:
       for _ in range(max_ops):            # ★max_ops=12
           step = dispatch_once(...)
           if not step["dispatched"]: break # ★『dispatch できたか』だけ＝★進んだかを 見ない

★★一般化する 場合の 条件（★Taka 逐語）=
   ★他 actor への ★非回帰を ★封印試験で 必ず 確認すること。
★MGR の実測（★参考・★断定しない）:
   barrier に 落ちない 操作 = GENERATE / AUDIT / REGENERATE / UPPER_REVIEW
   ★暴走したのは UPPER_REVIEW だけ。★他は 成功すると 状態が 進む
     （★実測: generate 1 / audit 2 / dispose 2 に対し upper_review 29）
   ∴ ★危険なのは「★成功しても 状態が 進まない 工程」。★現時点で 確認済みは UPPER_REVIEW のみ。
```

## 4. ★封印試験に使える実データ（★実際の記録・★MGR が正規面から取得）

**`TASK-2DER-32EDB6C4` の記録列（`_ordinal`, 種類）＝ 35件（うち upper_review 29件）:**

```json
[[3589,"generate"],[3590,"audit"],[3591,"dispose"],[3592,"upper_review"],
 [3594,"regenerate"],[3595,"audit"],[3596,"dispose"],
 [3597,"upper_review"],[3598,"upper_review"],[3599,"upper_review"],[3600,"upper_review"],
 [3601,"upper_review"],[3602,"upper_review"],[3603,"upper_review"],[3604,"upper_review"],
 [3605,"upper_review"],[3606,"upper_review"],[3607,"upper_review"],[3608,"upper_review"],
 [3609,"upper_review"],[3610,"upper_review"],[3611,"upper_review"],[3612,"upper_review"],
 [3613,"upper_review"],[3614,"upper_review"],[3615,"upper_review"],[3616,"upper_review"],
 [3617,"upper_review"],[3618,"upper_review"],[3619,"upper_review"],[3620,"upper_review"],
 [3621,"upper_review"],[3622,"upper_review"],[3623,"upper_review"],[3624,"upper_review"]]
```

**★MGR が この列に 案 A の規則を 当てた 結果 = ★許可 2回**
（★3592 と 3597 が 許可。★3598〜3624 の ★27回が 抑止される）

**★Taka の完了条件「29回相当の記録列に対し許可回数が実測どおり2回」は、★この列そのもので測れる。**

## 5. 契約の対象（★契約経路の制約に合わせる）

```
★`domain_dw._place_and_commit` は `def X(` から `twoder/X.py` を 決める
   ＝★置けるのは ★新しい 1関数の ファイルだけ（★既存ファイルは 書き換えられない）
★∴ 契約は ★純関数 1本:
     入力 = ★記録から 取れる 値（★案 A なら `_ordinal` の 一覧 ／ ★案 B なら 入力の 値）
     出力 = ★呼ぶ / 呼ばない ＋ ★理由の 語
     ★副作用 0（★ファイル・subprocess・LLM を 使わない）／ ★決定論
★名前・引数・返りの 形は ★DESIGN が 決める。
```

## 6. 封印試験に必ず入れてほしい観点（★中身は DESIGN が決める）

```
★Taka 指定の4つ:
   ①同じ入力で 1回目は ★許可   ②2回目は ★抑止
   ③regenerate 等で 入力が 変われば ★再度 許可
   ④★§4 の 実データ列に 対し 許可が ★2回
★MGR から 追加（★過去の 失敗の型）:
   ★空・None … 記録が 0件 ／ upper_review が 0件（★初回）／ 入力側が 0件
   ★順序    … `_ordinal` が 昇順でない 入力（★並べ直すか 拒否するか）
   ★同値    … 同じ `_ordinal` が 2つ（★実測では 起きていないが 決めておく）
   ★大小    … 入力側が 1件だけ ／ upper_review が 最後に 来ない 列
   ★決定論  … 同じ入力で 同じ出力
   ★一般化する 場合 … ★他 actor（GENERATE / AUDIT / REGENERATE）の 非回帰
```

## 7. ★MGR が先に言っておくこと（★隠さない）

```
★★① `twoder-manager.service` は ★停止中（★Taka 裁定(あ)・資源保護）。
   ★契約を egl/docs に 置いても ★`submit_next_contract` は manager の 巡回の 中に 在る
   ∴ ★★manager を 再開しない 限り ★契約は pending の まま 投げられない。
   ★再開の 可否は ★Taka の 裁定（★MGR は 勝手に 再開しない）。
   ★★再開すると ★同じ暴走が また 起き得る（★抑止は まだ 無い）。

★② この契約が 通っても ★配線は 別（★純関数が `twoder/X.py` に 置かれるだけ）。
   ★配線には ★別途 Taka の 一言が 要る（★今夜 既出・★裁定 A と 同じ形）。

★③ 現在 `TASK-2DER-32EDB6C4` は ★JUDGE_REQUIRED・★queue に 1件 在る
   （★MGR が 記録取得で `_last_task()` を 呼んだ 副作用・★開示済み）。
   ★manager を 再開すると ★この task から 再開する 見込み。
```

## 8. 契約の形（★既存どおり）

```
`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs ／ 命名 = CC_DESIGN_2026-08-19_CONTRACT_<name>.md
```

## 9. MGR がしていないこと

```
★設計 0 ／ 実装 0 ／ 契約本文 0 ／ A・B の 選定 0 ／ 局所・一般の 選定 0
★manager を 再開していない ／ queue を 編集していない ／ run_next 0
★apply_unified_diff / patch_bridge に 戻っていない
```
