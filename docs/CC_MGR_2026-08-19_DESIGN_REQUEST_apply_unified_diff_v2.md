# 宛: DESIGN（監査 CC）―― 契約作成の依頼: `apply_unified_diff` 修正版（★失敗理由を特定した）

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。BLOCKED の TASK を再開していません（記録だけ読みました）。**

---

## 1. ★失敗理由（★1つに特定・★BLOCKED TASK に残っていた記録から）

```
TASK-2DER-32EDB6C4（★BLOCKED のまま・★再開していない）
   generate   _ordinal 3589 … status=FAILED / reason=RUNNER_FAILED / runner_exit=1
   regenerate _ordinal 3594 … status=FAILED / reason=RUNNER_FAILED / runner_exit=1
   ★どちらも ★同じ 4本が 落ちた（★16本中 ★12 passed / ★4 failed）

★落ちた 4本:
   test_several_lines_keep_the_untouched_ones
   test_two_hunks_are_both_applied
   test_a_text_without_a_trailing_newline_stays_that_way
   test_an_empty_original_can_receive_lines

★1回目の 実際の 例外（★記録の 逐語）:
   assert None == 'a'      （test_impl.py:95）
★2回目の 実際の 例外（★記録の 逐語）:
   E  - a
   E  + a                  （★見た目が 同じ＝★末尾の 改行の 差）
```

### ★1つに絞った理由

**通った12本と落ちた4本を分けているのは「★1行・1 hunk・末尾改行あり」かどうか。**

| 落ちた試験 | 契約が要求している形（★逐語） | 共通点 |
|---|---|---|
| `several_lines_keep_the_untouched_ones` | `"a\nb\nc\n"` に `@@ -2 +2 @@` → `"a\nB\nc\n"` | **★触っていない行を残す** |
| `two_hunks_are_both_applied` | `@@ -1 +1 @@` と `@@ -4 +4 @@` の2つ → `"A\nb\nc\nD\n"` | **★hunk が2つ** |
| `a_text_without_a_trailing_newline_stays_that_way` | `"hello"`（★改行なし）→ `"world"` | **★末尾改行が無い** |
| `an_empty_original_can_receive_lines` | `""` に `@@ -0,0 +1 @@` → `"a"` | **★元が空** |

**★∴ 実装は「★1行を まるごと 置き換える」形だけを 満たし、
★★hunk の 位置指定（`@@ -2 +2 @@`）を 使って ★元の 行を 部分的に 差し替える 処理が 無い。**
**★その結果、上の4形では ★`None` を返す（＝適用を拒否した）か、★末尾改行を落とした。**

**★1回目の `assert None == 'a'` が それを直接示す ―― ★実装は「当てられない」と判断して `None` を返している。**

## 2. ★修正版契約に入れてほしいこと（★中身は DESIGN が決める）

```
★同じ 部品名で よい（★`apply_unified_diff`）。★新しい patch 形式を 作らない。
★★骨格に ★hunk ヘッダ（`@@ -l,s +l,s @@`）の 扱いを 明記してほしい:
     ・★元の どの行から どれだけを 置き換えるか
     ・★hunk が 複数 在る 場合の 進め方
     ・★`-` / `+` / ` `（文脈行）の 扱い
     ・★末尾改行の 有無を ★元のまま 保つ
     ・★元が 空（`@@ -0,0 +1 @@`）の 場合
★★上の 4本は ★そのまま 封印試験に 残してほしい（★同じ形で 再度 測れるように）
```

## 3. Taka 指定の完了条件（★変更なし）

```
・/tmp Hermetic のみ            ・hello\n ＋ unified diff → world\n
・diff 文字列そのものを 返さない  ・不一致は fail-closed
・複数 hunk                     ・決定論              ・副作用 0
```

## 4. ★MGR が確認したこと・していないこと

```
★確認: BLOCKED TASK の ★記録だけを 読んだ（generate / regenerate の test_result）
★していない: ★TASK の 再開 0 ／ ★再投入 0 ／ ★実装 0行 ／ ★実 repo energize に 触っていない
             ★patch_bridge 本体に 配線していない
★manager は 稼働継続 ／ ★暴走 TASK は BLOCKED の まま
```

## 5. 契約の形（★既存どおり）

```
`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs ／ 命名 = CC_DESIGN_2026-08-19_CONTRACT_<name>.md
→ ★置けば 常駐が 次の巡回で 自力で 投げる（★manager は 動いている）
★★同じ sha は 二度 投げられない ∴ ★中身が 変われば 自動で もう一度 投げられる
   （逐語「★飛ばす 鍵を 名前 → 骨格の sha へ 変える」）
```
