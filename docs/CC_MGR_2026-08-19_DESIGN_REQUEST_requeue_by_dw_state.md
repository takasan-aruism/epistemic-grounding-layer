# 宛: DESIGN（監査 CC）―― 契約作成の依頼: 工程の再開は DW 正本の state だけで決める

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。この文書は要件だけです。**

---

## 1. 直してほしいこと（★1点だけ）

```
`manager_v0._last_task()` の 自己修復ループが、★受領の帳簿（done/received）を
★工程の判定に 流用している ため、★成果物を 受け取った task は
★DW の 工程が 途中でも ★二度と 並びへ 戻らない。

   if not tid or tid in q or ★tid in done: continue
   st = _call("/api/state?task_id=" + tid).get("dw_state")
   if not _machine_turn(st): continue
   _queue_add(tid); return tid
```

## 2. 四問の確認結果（★すべて正規面・正本から。★これが「可能」の根拠）

### ① manager の done/received は今後も必要か → **★必要**

```
`domain_dw.receive_finished()` 逐語:
 「★終わった 案件の 成果物を ★受け取り ★同じ物か 確かめ ★残す
   （★★置く・繋ぐ・使う は しない）。★判定=`check_artifact`（★sha が 一致するか だけ）」
`_append_index` 逐語:
 「★『その巡回の 物』だけを 出すと ★次の 巡回で 消える…∴ ★★積み上げて 残す」
★受領の 事実を 残す 帳簿として ★別の 役目が 在る ∴ ★消さない・★意味を 変えない。
```

### ② DW の「工程完了」を表す既存の判定器 → **★`manager_v0._machine_turn(state)`**

```
逐語「★その 状態に ★次の 仕事が 在り ／ ★それが 機械の 番なら True。
      ★未知の 状態=★`_MAP` に 無い → ★★False（★勝手に 分類しない）」
実装 = ★`dw.dispatch._MAP`（★正本）を 引き、★`op not in ("NONE","BLOCKED")` を 返すだけ。

★実測（★正規面）:
   COMPLETE                → _MAP の op = "NONE"    → ★False（★拾わない）
   READY_FOR_UPPER_REVIEW  → op = "UPPER_REVIEW"    → ★True （★拾う）
   DISPOSITION_REQUIRED    → op = "DISPOSE"         → ★True （★拾う）
   READY_FOR_REGENERATE    → op = "REGENERATE"      → ★True （★拾う）
   BLOCKED                 → op = "BLOCKED"         → ★False
```

**★新しい状態語も新しい判定器も要らない。★既に在り、★同じ関数の中で既に呼ばれている。**

### ③ `tid in done` の代わりに DW state で決められるか → **★できる（★既にその判定が後段に在る）**

```
★自己修復ループは ★既に `_machine_turn(st)` を 呼んでいる（★後段）。
★`tid in done` は ★その手前で 先に 弾いている ＝★★後段の 判定に 届かない。
∴ ★足すのではなく ★★手前の 除外を 外せば、★既存の DW 判定が そのまま 効く。
```

### ④ 「受領済み成果物を二重受領しない」性質を壊さないか → **★壊さない（★実測）**

```
`_append_index`（domain_dw.py:294）:
   if not any(r.get("task_id") == item.get("task_id") for r in rows):
       rows.append(item)
★★task_id で 重複を 弾く ∴ ★同じ task が 二度 received 行に ならない。

★かつ receive_finished 自身の 逐語:
 「★★受領は ★試験が 通った 物なら いつでも して よい
   （★★受領≠承認 ／ ★★何度でも 同じ）」
★∴ 再受領は ★設計上 許されている。
```

## 3. ★DESIGN が判断すべき副作用（★MGR が見つけた・★対処は DESIGN が決める）

**`manager_v0.main()` の1巡回の順序:**

```
record_stages() → ★receive_finished() → submit_next_contract() → ★tick()
```

```
★`receive_finished()` は ★`_queue()` を 舐め、受領できた task を
  ★`_queue_write(...)` で ★並びから 落とす（domain_dw.py:384）。
★`tick()` の 自己修復が 並びへ 戻すと、★次の 巡回の receive_finished が ★また 落とす。
★★→ 毎巡回「戻す→落とす」を 繰り返す 見込み（★未検証）。
★★ただし tick は 同じ巡回の 中で 走るので ★1巡回に 1手ずつは 前進する 見込み（★未検証）。
★`_append_index` は 重複を 弾く ∴ ★帳簿の 件数は 増えない（★実測）。
★`_place_and_commit` が 毎回 走るかは ★MGR は 確かめていない（★UNKNOWN）。
```

**★この往復を許容するか、別の形にするかは ★DESIGN が決める。★MGR は決めていません。**

## 4. 要件

```
★受領帳簿（done/received）は ★そのまま 残す・★意味を 変えない
★`receive_finished` の 受領責務を ★変えない
★新しい 状態語 0 ／ 新しい 判定器 0 ／ 新しい queue 0 ／ 新台帳 0 ／ front door の 口 0増
★工程を 再開するかは ★DW 正本の state だけで 決める（★既存 `_machine_turn` を 使う）
★queue への 二重追加を しない（★`_queue_add` は 既に `if tid not in q` を 持つ＝★実測）
```

## 5. 封印試験に必ず入れてほしい観点（★Taka 指定 ＋ 過去の失敗の型）

```
★received済み ＋ COMPLETE                → ★再取得しない
★received済み ＋ READY_FOR_UPPER_REVIEW  → ★★再取得する（★今回の 本題）
★received済み ＋ DISPOSITION_REQUIRED    → ★状態に応じて 正規経路
★queue 在籍中                            → ★二重追加しない
★未受領 TASK                             → ★従来どおり
★（★MGR から追加）BLOCKED / 未知の状態    → ★拾わない（★`_MAP` に 無い＝False の 既存規則）
★（★MGR から追加）先入れ先出しを 壊さない（★正本 §2.3「優先順位を 付けない」）
```

## 6. 契約の形（★既存どおり）

```
`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs（★CONTRACT_DOCS_DIR）
命名   = CC_DESIGN_2026-08-19_CONTRACT_<name>.md
→ ★置けば 常駐 `submit_next_contract` が 次の巡回で 自力で 投げる（★実証済み）
```

## 7. 受入（★MGR が正規面で確認します）

```
★TASK-2DER-6AC3EA20 を ★手で queue へ 追加しない
① READY_FOR_UPPER_REVIEW の まま 放置
② ★manager が 自力で 再取得（`_queue()` / `_last_task()` に 現れる）
③ ★headless `claude -p` が UPPER_REVIEW を 実施（identity = "claude-senior"）
④ state が 前進する
★run_next を 手で 叩かない ／ UPPER_REVIEW を Claude が 代行しない
```

## 8. MGR がしていないこと

```
★設計 0 ／ 実装 0 ／ 契約本文 0
★done の 意味を 変えていない ／ receive_finished を 触っていない
★task を 手で queue へ 戻していない ／ run_next 0
★§3 の 往復を どう 扱うかを 決めていない（★DESIGN の 裁定事項）
```
