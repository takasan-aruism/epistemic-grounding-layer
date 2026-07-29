# 設計/監査 → MGR（写: Taka / IMPL）: **D-71 — ★推測していたら間違えていた。依存待ちは18件。★4区分に入らない18件が在る。★開始日は front door から取れない**

- `BUILD_ROLE: 参照`（**調査のみ。★実装していない・投入していない・台帳を直読していない**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-29 / TYPE=FINDING
- **運用方針 確認済（版: `v2.8`）** / **裁定**: `CC_MGR_2026-07-29_D70_RULING_SHOW_THE_MISSING_GROUND.md` §5

## 0. ★結論
> **① 「依存待ち」は★18件**（`CREATED` 12 ＋ `READY_FOR_UPPER_REVIEW` 5 ＋ `DISPOSITION_REQUIRED` 1）。
> **② ★私が推測で書こうとした 36 は★誤りだった。** **`JUDGE_REQUIRED` は `claude_barrier=False` である。**
> **③ ★`JUDGE_REQUIRED` 18件は、Taka の4区分の★どれにも入らない**（§3）。
> **④ ★開始日は front door から★取れない**（§4）。**D-70 の「出せる見込み」は★取り消す。**

---

## 1. ★全数の実測（155件・打ち切り無し・読み取りのみ）
```
再現: 155件について GET /api/state?task_id=… → dw_state | claude_barrier | actor_role
総件数 155 / 確認 155 / 打ち切り無し

  67  READY_FOR_AUDIT          | False | QWEN_AUDITOR
  49  READY_FOR_IMPLEMENTATION | False | QWEN_LIVECODER
  18  JUDGE_REQUIRED           | ★False | ★"-"
  12  CREATED                  | True  | CLAUDE
   5  READY_FOR_UPPER_REVIEW   | True  | CLAUDE
   2  BLOCKED                  | False | "-"
   1  READY_FOR_REGENERATE     | False | QWEN_LIVECODER
   1  DISPOSITION_REQUIRED     | True  | CLAUDE
```

## 2. ★私が推測しなかったことが効いた（記録する）
```
D-70 で私が書いたこと: 「★推測で 18+12+5+1=36 と書かない。
                        JUDGE_REQUIRED が barrier かを確かめていないためである」
実測                : ★JUDGE_REQUIRED は claude_barrier=False
∴ ★依存待ちは 36 ではなく 18 である。
```
> **★書いていれば、2倍の数を MGR に渡していた。**
> **★「出せると言えるが、出していない」と書いたのが効いた。**

## 3. ★4区分に入らない18件が在る（★最重要・新しい発見）
```
JUDGE_REQUIRED 18件: claude_barrier=False かつ actor_role="-"
∴ ★機械の担当者が居ない（"-"）。★人の判断待ちでもない（barrier=False）。
```
| Taka の区分 | 入るか | 理由 |
|---|---|---|
| 停止中 | **★入らない** | `BLOCKED` ではない |
| 依存待ち | **★入らない** | `claude_barrier=False` |
| 背景保持 | **★入らない** | **★背景保持は「機械が進められる」もの**（`QWEN_*` が付く）。**これは `actor_role="-"` で★誰も進められない** |
| 現在前面化すべき | **★判断できない** | 決める値が無い（D-70 §3） |

> **★∴ 155件のうち18件は、★Taka の4区分のどれにも当てはまらない。**
> **★私は5つ目を作らない**（MGR 明示「4区分をそのまま使う。増やさない」）。
> **★事実だけ出す: 「4区分のどれにも入らないものが18件在る」。** **★どうするかは MGR/Taka の裁定である。**

### 3-1. ★これは今日の型と同じである
> **★「どこにも入らないもの」を、無理にどこかへ入れない。**
> **★入れれば「背景保持117件」が「135件」になり、★誰も進められない18件が背景に紛れる。**

## 4. ★開始日は front door から取れない（★D-70 を訂正する）
```
再現: GET /api/resolve?id=TASK-…      → record のキーは ['events','state','task_id'] のみ
再現: GET /api/state?task_id=…        → ts/date/time を含むキー ★無し
再現: GET /api/claude_packet?task_id=… → ts 系 ★無し
```
| | |
|---|---|
| **D-70 で私が書いたこと** | 「開始日 → **★出せる見込み**（DW の `CREATE` event に `ts` が在る）」 |
| **★訂正** | **★データは在る。★front door から取れない。** **★別のことである** |
| **∴** | **★「出せる見込み」を取り消す。** **★出すには新しい口が要る**（MGR 条件に触れる） |

> **★これは本日ずっと出ている「在るが読めない」である。** **★`G-46`・`G-58` と同じ形。**

## 5. ★Taka の欠落5件（★実測後の確定版）
| Taka の指摘 | **判定（実測後）** |
|---|---|
| タスク名なし | **★出せる**（`_task_goal` が在る。**★front door 経由は未確認**） |
| 状態なし | **★出せる**（`/api/state` の `dw_state`・155件 実測済） |
| **開始日なし** | **★出せない**（§4。**★訂正**） |
| 優先度なし | **★出せない**（決める値が無い） |
| なぜ表示されたか不明 | **★出せる**（「COMPLETE でも BLOCKED でもないから」） |

> **★D-70 では「5件中4件は既に在るが捨てている」と書いた。** **★実測後は 3件である。** **★訂正する。**

## 6. ★件数（MGR へ返す）
```
停止中          2
依存待ち       18
背景保持      117
現在前面化    ★決める値が無い（出せない）
★どれにも入らない  18   ← ★新しい発見
──────────────
合計          155
```

## 7. ★私は実装しない・区分を増やさない
- **★調査のみ。** **コードを1行も変えていない。** **★投入していない。**
- **★5つ目の区分を作っていない。** **★18件を「事実」として出しただけである。**
- **★LLM に分類させていない。** **★すべて決定論。**

## 8. ★未確認
| # | | 誰が・いつ |
|---|---|---|
| 1 | **`_task_goal` の値が front door から取れるか**（タスク名） | **★確かめていない。** CC-α / 指示が在れば |
| 2 | **`JUDGE_REQUIRED` が何を待っているのか** | **★分からない。** `actor_role="-"` としか出ない |
| 3 | **`actor_role="-"` の `BLOCKED` 2件との違い** | **★state が違うだけで、担当者はどちらも "-" である** |

---
*CC-α D-71（調査のみ）。★結論=①**依存待ちは18件**（`CREATED` 12＋`READY_FOR_UPPER_REVIEW` 5＋`DISPOSITION_REQUIRED` 1）②**私が推測で書こうとした 36 は誤りだった**（`JUDGE_REQUIRED` は `claude_barrier=False`）③**`JUDGE_REQUIRED` 18件は Taka の4区分のどれにも入らない** ④**開始日は front door から取れない**（D-70 の「出せる見込み」を取り消す）。★155件を全数実測（`READY_FOR_AUDIT` 67/False/QWEN_AUDITOR、`READY_FOR_IMPLEMENTATION` 49/False/QWEN_LIVECODER、**`JUDGE_REQUIRED` 18/False/"-"**、`CREATED` 12/True/CLAUDE、`READY_FOR_UPPER_REVIEW` 5/True/CLAUDE、`BLOCKED` 2/False/"-"、`READY_FOR_REGENERATE` 1/False/QWEN_LIVECODER、`DISPOSITION_REQUIRED` 1/True/CLAUDE）。★**推測しなかったことが効いた**——D-70 で「推測で36と書かない。`JUDGE_REQUIRED` が barrier か確かめていないため」と書いており、**書いていれば2倍の数を MGR に渡していた**。★**最重要=4区分に入らない18件が在る**——`JUDGE_REQUIRED` は `claude_barrier=False` かつ `actor_role="-"` で、**機械の担当者が居らず人の判断待ちでもない** ∴ 停止中(`BLOCKED` でない)・依存待ち(barrier=False)・背景保持(**背景保持は機械が進められるもので `QWEN_*` が付くが、これは誰も進められない**)のどれにも入らない。**5つ目を作らず事実だけ出す**——**入れれば「背景保持117件」が「135件」になり、誰も進められない18件が背景に紛れる**。★**開始日は front door から取れない**（`/api/resolve` の record は `events`/`state`/`task_id` のみ、`/api/state` と `/api/claude_packet` に ts 系は無し）——**データは在るが front door から取れないのは別のことであり、「出せる見込み」を取り消す。出すには新しい口が要る**（`G-46`・`G-58` と同じ「在るが読めない」）。★**Taka の欠落5件の確定版**=タスク名は出せる（front door 経由は未確認）／状態は出せる／**開始日は出せない（訂正）**／優先度は出せない／なぜ表示されたかは出せる——**D-70 の「5件中4件は既に在るが捨てている」を「3件」に訂正する**。★件数=停止中2／依存待ち18／背景保持117／現在前面化は決める値が無い／**どれにも入らない18**＝155。★CC-α は実装せず**5つ目の区分を作らず**18件を事実として出しただけで、**すべて決定論**（LLM に分類させていない）。★未確認=`_task_goal` の値が front door から取れるか／**`JUDGE_REQUIRED` が何を待っているのか（`actor_role="-"` としか出ない）**／`actor_role="-"` の `BLOCKED` 2件との違いは state だけ。*
