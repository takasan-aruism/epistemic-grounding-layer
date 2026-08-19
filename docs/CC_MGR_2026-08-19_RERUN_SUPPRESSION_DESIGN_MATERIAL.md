# 宛: Taka / 設計（DESIGN が決める） / 監査 ―― 再実行抑止: **鍵は既に全部そろっている**

**実装 0。新しい台帳 0。固定回数ルールを作っていない。`manager` は停止したまま。**

## 0. 最初に ―― 実測が完全に閉じた

```
同じ TASK の 記録を `_ordinal`（★DW の 単調な 通し番号）で 並べる:

  3589 generate      ← 入力が 変わった
  3590 audit         ← 入力が 変わった
  3591 dispose       ← 入力が 変わった
  3592 ★upper_review ← ★正しい（★直前に 入力が 変わった）
  3594 regenerate    ← 入力が 変わった
  3595 audit         ← 入力が 変わった
  3596 dispose       ← ★最後の 入力変化
  3597 …… 3624  ★upper_review ×★28   ← ★★入力が 1つも 変わっていないのに 28回

★『前回の upper_review より 後に 入力が 変わった時だけ 呼ぶ』を 当てると
   ★★29回 → ★2回（★27回が 不要だった）
```

## 1. 再実行抑止の既存前例（★3つとも実物を読んだ）

| 前例 | 形 | 実際に効いているか |
|---|---|---|
| **`route_worker` + `route_adopt`** | `registered = {(source,target) …}` を**既存の記録から作り**、`if pair in registered: already++ ; continue` | **★効いている**（★machine 206行が二重登録なく積み上がった） |
| `route_adopt.adopt` の行 | `input_hash` / `prompt_version` / `vote_run_id` / `model` を**同じ行に残す** | ★残っている（★後から同一性を言える形） |
| `patch_bridge` | `fingerprint = sha256(canonical diff)`。`expected_fingerprint` と違えば**拒否** | **★効いている**（★MGR が使い捨ての場で実測） |
| `domain_dw._append_index` | `if not any(r["task_id"] == item["task_id"] …)` で**重複を弾く** | **★効いている**（★received が水増ししない） |

**★共通の作法 = 「★既存の記録を読み、★同じ物なら やらない」。★新しい台帳を作った例は1つも無い。**

## 2. UPPER_REVIEW で使える既存の鍵

### (a) ★入力そのものは既に1箇所に集まっている

**`senior_review.build_prompt(task_id, view)` 逐語「★渡す物は 記録に在る値だけ(★申告を混ぜない)」:**

```
task_id / state / last_test_passed / rework_count / completion_blockers /
findings / record_test_passed / ★artifact_sha256 / artifact_head
```

**∴ Taka が挙げた6つは★すべてこの1関数の中に既に揃っている。**
**＝「前回と同じ入力か」は ★この文字列の hash 1つで言える（★新しい欄を作らずに済む案 (A)）。**

### (b) ★もっと安い鍵 ―― **`_ordinal` だけで足りる（★新しい欄が 1つも 要らない）**

```
★実測: `generate_runs` / `regenerate_runs` / `audit_runs` / `dispose_runs` / `upper_reviews`
   ★どれも `_ordinal` を 持つ（★DW の event log の 通し番号・★単調）
★∴ 規則は 1行で 言える:
     ★「★最後の upper_review の _ordinal より 後に、
        ★入力を作る記録（generate / regenerate / audit / dispose）が 1つも 無ければ 呼ばない」
★★これは 既存の 記録だけで 判定でき、★新しい 欄も 台帳も hash も 要らない。
★★§0 の 実測で 29回 → 2回 に なる。
```

**★(a) と (b) の違い（★MGR は選ばない）:**

```
(a) prompt の hash  … ★入力の 中身が 同じかを 直接 言える ／ ★但し 記録に 欄を 1つ 足す 必要
(b) _ordinal 比較   … ★欄を 足さない ／ ★但し「記録は 増えたが 中身は 同じ」を 区別できない
★どちらを 採るか、あるいは 併用かは ★DESIGN が 決める。
```

## 3. 最小要件 5つへの当てはめ（★(b) の場合）

| # | 要件 | 満たすか |
|---|---|---|
| ① | 初回の UPPER_REVIEW は実行する | **★満たす**（★3592 は「直前に入力変化」＝実行される） |
| ② | state も入力も変わっていなければ再実行しない | **★満たす**（★3597〜3624 が止まる） |
| ③ | artifact/test/findings/disposition が変わったら再実行可能 | **★満たす**（★generate/regenerate/audit/dispose が新しい `_ordinal` を作るため） |
| ④ | fail-closed を維持 | **★満たす**（★「呼ばない」だけ。★PASS を勝手に作らない） |
| ⑤ | Taka 裁定が要る authority 境界を変えない | **★満たす**（★`_MAP` も `authority` も触らない） |

## 4. 局所修正か、一般 progress guard か（★MGR は決めない・材料だけ）

### 局所（UPPER_REVIEW だけ）

```
＋ 影響範囲が 小さい ／ ＋ 他 actor の 挙動を 変えない
− ★同じ穴が 他にも 在る（★下記）
```

### 一般（`run_until_barrier` の停止条件に progress を足す）

**現在の停止条件（`dispatch.py:178-184` 逐語）:**

```python
for _ in range(max_ops):          # ★max_ops=12
    step = dispatch_once(...)
    if not step["dispatched"]:
        break                      # ★『dispatch できたか』だけ。★進んだかを 見ない
```

```
＋ ★同型の 穴を まとめて 塞ぐ
＋ ★材料は 同じ（★`_ordinal` の 最大値が 増えたか）
− ★全 actor に 効く ∴ ★正しく 何度も 走るべき 工程を 止め得る
   （★MGR は 「そういう工程が 在るか」を ★確かめていない ＝★UNKNOWN）
```

**★他にも同じ穴が在るかの手掛かり（★実測・★断定しない）:**

```
`dispatch_once` で ★barrier に 落ちない 操作 = GENERATE / AUDIT / REGENERATE / ★UPPER_REVIEW
   （★_MAP の claude_barrier=False の 5つ）
★このうち ★高価なのは ★UPPER_REVIEW（`claude -p`）と ★GENERATE/AUDIT（Qwen）。
★今回 暴走したのは UPPER_REVIEW だけ ―― ★他が 暴走しないのは
   ★成功すると 状態が 進むから（★実測: generate 1 / audit 2 / dispose 2）。
★★∴ 危険なのは「★成功しても 状態が 進まない 工程」= ★今のところ UPPER_REVIEW だけが 確認済み。
```

## 5. 既存の安全境界への影響

```
★変えない: `_MAP`（claude_barrier）／ `authority`（層1/2/3）／ `disposition` 規則 ／
           `_TEST_CATEGORIES` ／ `receive_finished` の 受領責務 ／ front door の 口
★★「呼ばない」だけなので ★fail-closed が ★強くなる 方向（★緩まない）
★★但し ★1つだけ 注意（★DESIGN へ）:
   ★止めた 結果 ★永久に JUDGE_REQUIRED の まま 残る task が 出る。
   ★それは ★『静かな滞留』＝★今夜 何度も 出た「不在が 遵守に 見える」の 型に なり得る。
   ★∴ ★止めた 事を ★記録に 残す（★理由の 語つき）ことを 要件に 入れてほしい。
```

## 6. 次の最小実装1件（★MGR は実装しない）

```
★★1件 = 「★前回の upper_review より 後に 入力を作る記録が 1つも 無ければ
           ★CLAUDE_SENIOR を dispatch しない」―― ★純関数 1本で 書ける。
   入力 = 記録から 取れる `_ordinal` の 一覧（★upper_reviews と 入力側）
   出力 = 呼ぶ / 呼ばない ＋ ★理由の 語
   ★副作用 0・決定論 ∴ ★契約経路（`def X(` → `twoder/X.py`）に そのまま 乗る
★★配線先は ★DESIGN が 決める（★局所 = webui の CLAUDE_SENIOR actor ／
   ★一般 = dispatch の run_until_barrier）。★配線は ★別途 Taka の 一言が 要る（★今夜 既出）。
```

## 7. 優先度（★Taka の指摘に対する MGR の実測）

```
★Taka 逐語「50〜100並列で 回す構想なら、1件の 無限上級監査が 大量に 複製される」
★実測の 裏づけ:
   ・1巡回で ★12回（max_ops）
   ・止まったのは ★抑止では なく ★task が queue から 落ちた 偶然
   ・★1件で 15分に 29回 ＝ ★100並列なら 同じ 15分で ★理論上 2,900回
★★∴ MGR も ★優先度は 高いと 見る（★但し 判断は Taka）。
```

## 8. していないこと

```
★実装 0 ／ 設計の 決定 0（(a)/(b)・局所/一般 は DESIGN へ）
★新台帳 0 ／ 固定回数ルール 0 ／ 新しい 状態語 0
★apply_unified_diff の 試験失敗に 戻っていない ／ patch_bridge に 戻っていない
★manager service は ★停止したまま ／ queue を 編集していない ／ run_next 0
```
