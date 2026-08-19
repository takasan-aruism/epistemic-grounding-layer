# 宛: DESIGN（監査 CC）―― 契約作成の依頼: **差分を作る純関数1つ**（★本線に供給元が無い）

**依頼元: MGR ／ 2026-08-19 ／ Taka 指示「connector 本線配線へ続けて」**
**MGR は判断ロジックを書きません。実 repo へ書いていません。実装していません。**

---

## 1. ★なぜ要るか（★実測）

```
★本線の GENERATE が 作る `test_result['artifact']` = ★★丸ごとの source
   実測の 先頭: 'def dry_run_ok(files, expected_preimages, allowed_files):\n    """dry-run の…'
   ★diff では ない。
★呼び手 0（★2DER の 走査器で 数えた）:
   `worker_output_to_artifact` ／ `canonical_diff_artifact` ／
   `bridge_apply_connector` ／ `apply_cycle`
★★∴ ★今日 作った patch 一式（diff → 適用 → rollback）は ★繋ぐ 相手が 居ない。
★★本線は「★新しい 部品を 丸ごと 置く」だけ ＝ ★既存ファイルを 変える 経路が ★無い。
```

## 2. ★契約にしてほしいもの（★純関数 1本）

```
★足りない 判断は「★今の 中身と ★新しい 中身から ★unified diff を 作る」。
★入力（★どれも 既に 手元に 在る）:
   ・今の ファイルの テキスト（★`capture_preimage` / disk から 取れる）
   ・新しい テキスト（★`test_result['artifact']` が そのまま これ）
   ・filename
★返り（★形は DESIGN が 決める）:
   ・unified diff の テキスト ／ ★作れない時は その 理由の 語
★★満たしてほしい 形（★既存に 合わせる・★新しい 形式を 作らない）:
   ・`canonical_diff_artifact` が ★受け取れること
     逐語の 必須条件 = ★`--- a/<file>` と ★`+++ b/<file>` の 両方が 在る
   ・★`apply_unified_diff`（★封印試験16本・★配線済み）が ★当てられること
     ＝★★『作った diff を 当てると ★新しい テキストに なる』（★往復が 閉じる）
★★副作用 0（★ファイル・git を 触らない）／ ★決定論（★同じ入力で 同じ diff）。
★名前・引数・返りは ★DESIGN が 決める。
```

## 3. ★封印試験に入れてほしい観点（★中身は DESIGN が決める）

```
★★往復 … 作った diff を `apply_unified_diff` に 当てて ★新しいテキストに 戻る（★最重要）
★1行 ／ 複数行 ／ 複数 hunk（★離れた 2箇所）
★末尾改行の 有無（★元・新 の 4通り）
★変化なし … 同じテキスト → ★diff が 空 or 作らない（★語で 返す）
★空 … 元が 空（★create 相当）／ 新が 空（★delete 相当）
   ★★注意: ★`canonical_diff_artifact` は ★`--- /dev/null` 形を ★拒否する（★MGR 実測）
     ∴ ★create/delete を どう 扱うかは ★DESIGN が 決める（★★別件として 逃がしてもよい）
★決定論 … 同じ入力で ★同じ バイト列
★副作用 0
```

## 4. ★MGR が先に言っておくこと（★隠さない）

```
★① この部品が 出来ても ★『どの案件で 既存ファイルを 変えるか』は ★別問題。
   ★今の 本線は「★新しい 部品を 置く」だけ ∴ ★呼ぶ 場面が そもそも 無い。
   ★★= ★設計判断が 1つ 要る（★Taka / DESIGN）。★MGR は 決めない。
★② 配線（`apply_cycle` を 呼ぶ 場所）は ★別途・★足場（★今夜 10回目の 型）。
★③ create / delete は ★`canonical_diff_artifact` が 拒否する（★既に 別件記録）。
★④ `would_write_sha256` の 回帰は ★未修正（★`dry_run_ok` は 見ない ∴ 影響なし）。
```

## 5. MGR がしていないこと

```
★判断ロジック 0行 ／ 実装 0 ／ 実 repo 書き込み 0 ／ 新台帳 0
★delegated energize・初回 real-repo に 進んでいない
★暴走 TASK TASK-2DER-32EDB6C4 は BLOCKED の まま 触っていない
```
