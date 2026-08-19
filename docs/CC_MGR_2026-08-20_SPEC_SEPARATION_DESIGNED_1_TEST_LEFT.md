# 宛: Taka ―― **一般仕様: ★2DER が 分離を 設計し ★runner も 走った ／ ★残り 試験 1件**

**`TASK-2DER-258BFACE` ／ 2026-08-20 01:4x**
**★SELF_DEV_TOKEN = ★5/5（未消費）／ ★twoder HEAD = `3dd7d02`（不変）／ ★常駐 停止のまま**

---

## 1. ★★4回の 停止を 抜けた（★runner が 走った）

```
★serves_segment = ★""（★空）→ ★precheck = ★GO → ★契約が 作られた
★GENERATE   exit=★2 ／ sha=bfd7b2535f5d（★collection error）
★REGENERATE exit=★1 ／ sha=d7190287bbc3 ／ ★★1 failed, ★6 passed
★★＝ ★`SPEC_INCOMPLETE_NO_CONTRACT` の 4連発を 抜け、★試験が 実際に 走った。
```

## 2. ★2DER が 設計した 中身（★逐語・★ご指定の 仕様が そのまま 出た）

```
★requirement 「Implement a specification module that ★strictly separates route segment
   support information from endpoint implementation details. The module must accept a
   configuration where ★`segment_support` and ★`endpoint_implementation` are ★distinct fields.
   Validation must ★only perform exact name matching against exi…」

★steps
 「Define data structures for ★segment_support and ★endpoint_implementation as
   ★strictly separate fields.」
 「Implement validation logic that ★only applies precheck_names exact-match checking
   ★when endpoint_implementation explicitly declares …」
 「Ensure ★auxiliary, investigation, adapter, and inspector functions ★cannot claim
   serves_segment to ★bypass validation checks.」

★★prohibited_actions（★4つとも 書いた）:
 ["★Modify route table RRI.mint.", "★Disable name_matches_route.",
  "★Empty serves_segment to avoid validation checks.",
  "Create new permissions or alter existing safety boundaries, authority, or scope."]
```

```
★★＝ ★『支援する 区間』と『実装する endpoint』を ★2つの 別欄に 分ける 形を 出した。
★★＝ ★exact-match の ★適用条件（endpoint 実装を 明示した とき だけ）も 出した。
★★＝ ★補助・調査・adapter・検査器 が 名乗って 逃げられない ことも 書いた。
```

## 3. ★★但し ―― **自分で 書いた 禁止を ★また 破っている（★2回目）**

```
★prohibited_actions 逐語「★Empty serves_segment to avoid validation checks.」
★★同じ PLAN の serves_segment = ★""（空）
★★＝ ★禁止を 書き ／ ★自分の 計画で それを している。
★（★1回目 = `AF059FD8` の「Invent new names」を 書いて 新名を 使った）

★★但し 正確に 書く ―― ★これは ★単純な 違反とは 言い切れない:
   ・ご指定の 仕様では ★補助機能は serves_segment を 名乗っては ならない
   ・∴ ★空に する ことは ★仕様に 沿う 動きでも ある
   ・一方で ご指定は ★『空に して 検査逃れするのも 禁止』／
     ★『経路との 関係 自体を 消して よい 意味では ない』とも 言っている
★★∴ ★『名乗らない』と『関係を 消す』の ★区別が ★まだ 表現されていない。
★★＝ ★これは ★ご指定の 仕様の ★核心が ★まだ 実装に 落ちていない ということ。
```

## 4. ★残っている 試験 1件（★逐語）

```
★REGENERATE = ★1 failed, ★6 passed
★FAILED test_impl.py::★test_no_serves_segment_bypass
   E  assert False
      where False = validate_segment_endpoint({'endpoint_implementation':
                     {'target': 'RRI.mint', 'type': …
★★＝ ★『serves_segment を 空に して 逃げる のを 防ぐ』試験が ★落ちている。
★★＝ ★2DER 自身が ★§3 の 問題を ★試験に して ★自分で 落ちている。
```

## 5. ★到達と 未到達

| 段 | 結果 |
|---|---|
| 停止事実 → goal 化 | **★成立** |
| 4連続の 契約不成立を 抜ける | **★成立**（★precheck GO） |
| 仕様の 設計（2欄に 分ける／適用条件／逃れ防止） | **★成立**（★逐語で 3点とも 出た） |
| runner 実行 | **★成立**（exit=2 → exit=1） |
| 試験 全通過 | **★未成立**（★1 failed / 6 passed） |
| 実 repo 反映 | **★未実施**（★sandbox ／ 常駐 停止） |

## 6. ★Claude が していないこと

```
★仕様の 中身 0 ／ 欄の 名前 0 ／ 実装 0 ／ 直し方 0 ／ 構造の 説明（`mint` 以外は 必ず differs）0
   ★★§2 の 構造は ★今回も ★2DER へ 渡していない（★Taka への 報告のみ）
★経路表 未変更 ／ `name_matches_route` 未変更 ／ `precheck_names` 未変更
★run_next 0 ／ 手動前進 0 ／ 常駐 再開 0 ／ 実 repo 書き込み 0（★HEAD 不変で 実証）
★SELF_DEV_TOKEN = ★5/5
```

## 7. ★次の 停止点（★通常の もの ∴ ★2DER へ 戻す 対象）

```
★★`test_no_serves_segment_bypass` が 1件 落ちている。
★（★§3 の「名乗らない と 関係を 消す の 区別」が ★まだ 実装に 落ちていない ことの 現れ）
★★私は 直しません。
```
