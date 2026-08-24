# task → thread の一括読み口 — MGR への引き渡し（確定版）

- 起票: CC_ALPHA(監視) 2026-08-24
- 宛先: **MGR**（実装担当を割り当てる）
- 親: ITEM-2DER-EVO-0099 から出た finding。★但し **ESDE 固有機能ではない**
- artifact: `ART-cb3d453df3`

## 改訂履歴（★版の札は付けない。動いた数字と結論だけ残す）

| 日時 | 何が変わったか |
|---|---|
| 08-24 06:2x | 初版。「1件10秒超 / 609件で100分超」と書いた |
| 08-24 06:39 | **訂正**。測り直したら 2.6秒 / 26分（入口の並列化 EVO-0101 が並行して進んでいた） |
| 08-24 13:23 | 7時間の実走で **明細到達率 7.1%** が出た（優先度の根拠） |
| 08-24 14:1x | **確定版**。★探していた1パスは**既に在った**（`detail_backfill.thread_to_task`）。依頼が「作る」から「口を開ける」に変わった |

---

# 1. ★結論を先に —— 作るものは「口」だけ

**task→thread を1パスで作る関数は既に在る。** 新規実装は要らない。

```
twoder/detail_backfill.py:29  def thread_to_task():
    """★thread → task の 対応を 1パスで 作る(★TRACE が 正本= `RTHREAD_ID` を 持つ)。"""
```

**そして既に共通基盤として使われている**（＝Taka 条件「ESDE専用にしない」は**すでに満たされている**）:

| 呼び手 | 用途 |
|---|---|
| `twoder/task_similarity.py:89` | task の類似判定 |
| `twoder/domain_ledger.py:90` → `detail_backfill.plan_backfill` | **Ledger Domain W1 分類** |

★∴ **足りないのは front door の口 1本だけ**（`webui.py` に endpoint が **0件**・grep 実測）。

---

# 2. 依頼 —— `GET /api/task_threads`

## 2.1 返り

```json
{"total": 610, "with_thread": N, "without_thread": M, "unreadable": K,
 "rows": [{"task_id": "TASK-2DER-XXXX", "rthread_id": "RTHREAD-xxxx"},
          {"task_id": "TASK-2DER-YYYY", "rthread_id": null}]}
```

- **`total` を必ず載せる**（分母の無い数を返さない）
- `rthread_id` が無い task は **`null` で行を出す**。★**行を省かない**
- 読めなかった task は `unreadable` に数え、**理由を返す**
  （★「無い」と「読めない」を分ける）

## 2.2 既存関数の 3つの欠陥 —— 口を作るときに直す

`thread_to_task()` をそのまま裏返してはいけない。実測した欠陥:

| # | 欠陥 | 何が起きるか | 直し方 |
|---|---|---|---|
| 1 | `if th and th not in out` で **thread ごとに最初の task しか残さない** | 同じ thread を複数 task が指すと、後の task が **task→thread から消える** | task を鍵にする（thread を鍵にしない） |
| 2 | `RTHREAD_ID` を持たない task の**行を作らない** | 「thread が無い」が**沈黙**になる（分母から消える） | `null` で行を出す |
| 3 | 分母を返さない（素の dict） | 呼び手が「全件見た」と言えない | `total` / `with_thread` / `without_thread` / `unreadable` を返す |

★#1 と #2 は **私が今日4回出した finding と同じ型**（`ART-8810d0646e`）——
**「測れなかった／無かった」が表に出ない。**

## 2.3 ★禁止（Taka 条件・逐語）

> `/api/rthread?task_id=` をTASK件数ぶん繰り返す実装は禁止

★理由（実測）: `/api/rthread` は `build_state` 一式 + `list_questions` + `list_typed` + `_esde_for`
を全部通る。**thread の有無を知るだけでこれを 610 回通してはいけない。**
2.6秒 × 610 = **約26分**（06:39 実測。並列化前は 10秒超＝100分超）。

## 2.4 ★守ること

- **新台帳0 / 新state0 / 新ID0**。`runs/<task_id>.trace.json` の `RTHREAD_ID` を読むだけ
- **`runs/` は横読み禁止面** ∴ 読むのは **2DER 側（webui）でなければならない**。
  これが「2DER に聞いて返させる」形
- **意味判断をしない**。対応を返すだけ（★どれを測るべきかは Domain Manager が決める）

## 2.5 ★私が測れなかったこと（★実装側で測って報告してほしい）

**1パスの所要時間を私は測っていない。** `runs/` は私にとって横読み禁止面のため。
比較の目安になる既存の実測値は在る:

- `task_index()` は event を **1回読みで 528件 0.2秒**（`manager_v0.py:760` 逐語。1件ずつなら 53秒相当）
- `list_threads()` は **0.047秒**（★私がモジュール経由で実測。件数は動くので §3.1 を見ること）

★`thread_to_task()` は 610個の小さな JSON を開く形なので **上記とは別の測り方が要る**。
★「既存の呼び手が在るから速い」とは**言えない** —— `task_similarity` は
front door から呼ばれていない（grep 実測 0件）∴ **リクエスト内で通った証拠が無い。**

---

# 3. 受入条件（★これを満たしたら受け取る）

| # | 条件 | 判定のしかた |
|---|---|---|
| 1 | **1回の呼び出し**で 610 TASK 分が返る | `rows` の件数 == `total` |
| 2 | 既知の2本と一致する | `TASK-2DER-C032596E → RTHREAD-53614fdb` / `TASK-2DER-B14D7ACA → RTHREAD-6bfd5b30` |
| 3 | **標本20件が1件読みと一致** | 無作為20 task で `/api/rthread?task_id=` と突き合わせ **20/20**。★全件照合は約26分かかるので求めない |
| 4 | thread 側の分母と突き合わせる | **受入の時に `list_threads()` を走らせ**、`with_thread` の thread がその集合の**部分集合**であること。★はみ出したら報告。★**数を条件に書かない**（下記） |
| 5 | thread を持たない task が **`null` の行**で返る | `without_thread` > 0 かつ `rows` に `rthread_id: null` が在る |
| 6 | 所要時間を**報告する** | 実測値を1つ。★`/api/rthread` 610回（約26分）より速いこと |
| 7 | 新台帳0 / 新state0 / 新ID0 | 差分に台帳ファイルの新規が無い |
| 8 | ESDE 専用にしない | endpoint 名・返りに `esde` を含めない |

★**受入は MGR が行う。私（ESDE）は修理しない。**

## 3.1 ★分母は動く —— 条件に数を焼き込まない

| 測った時刻 | `list_threads()` | `/api/tasks` |
|---|---|---|
| 13:23 | **686** | 609 |
| 14:1x | **700** | 610 |

**約50分で thread が14本増えた。** ∴ 受入条件に `686` と書くと**必ず落ちる**。
★条件は「**受入時に走らせた値**を分母にする」と書く。★数そのものは条件にしない。

★これは今日ここで踏んだ実際の間違い —— 私は最初この表に `686` を焼き込んでいた。

## 3.2 ★受入条件②の錨は今も生きている（14:1x 実測）

| task | 期待 | 実測 | 一致 |
|---|---|---|---|
| `TASK-2DER-C032596E` | `RTHREAD-53614fdb` | `RTHREAD-53614fdb` | ○ |
| `TASK-2DER-B14D7ACA` | `RTHREAD-6bfd5b30` | `RTHREAD-6bfd5b30` | ○ |

★この2本は `list_threads()` の集合にも居る（確認済）∴ **条件②と④の錨として使える。**

---

# 4. 口ができた後 —— ESDE 側でやること（★まだ着手しない）

Taka 指示（逐語）:

> 口が完成したらESDE Domain Manager側では、**backlog先頭** ではなく、
> **未評価 ∩ threadあり** を優先して選ぶ。

★**いまは着手しない**（Taka 指示「ESDE Domain Managerの新機能追加は一旦止める」）。
口が受入を通ってから、`domain_esde.esde_backlog` の候補順を変える（★`require_thread` の既定も戻せる）。

## 4.1 before の基準値（★2026-08-24 実測・これと比べる）

再起動 06:22:22 → 13:22:05（**6時間59分**）の自動発火:

| 指標 | before |
|---|---|
| 発火数 | **14** |
| thread 到達数 | **1** |
| ETRACE 止まり数 | **13** |
| 明細 書戻し成功数 | **1** |
| 失敗数 | **0**（journal に `esde_failed` 0件） |
| **明細到達率** | **7.1%** |

★間隔 31.7〜37.3分（`ESDE_INTERVAL=1800` + 巡回の余り）。

## 4.2 after の測り方

**最低10回**自動発火させ、同じ5指標で比較する。

★測り方の鍵をここで固定する（★後で数が食い違わないため）:

- 発火数 = ETRACE の `component=ESDE_EVALUATION` のうち、**切り替え時刻より後**のもの
- thread 到達数 = そのうち `wrote=True`
- ETRACE 止まり数 = 発火数 − thread 到達数
- 失敗数 = journal の `esde_failed` ＋ Worker の非0終了
- ★**「task ごとの最新 ts」で数えない**。★再評価で ts が動くと発火数が減って見える
  （★2026-08-24 に私が一度これで数を間違えた）

## 4.3 これが改善したら

Taka 逐語:

> ここが改善したら、ESDE Domain Managerの「自動巡回」は一段完成とみなす。

---

# 5. なぜ共通基盤なのか（★念のため残す）

Domain Manager は「**結果を明細へ戻せる対象**」を選べないと、自動巡回の 93% が
ETRACE 止まりになる。これは ESDE だけの都合ではない:

- **ESDE**（実測済）: 14回中13回が `wrote=False thread=None`
- **Ledger Domain**（`TAKA_SPEC_2026-08-24_LEDGER_DOMAIN_v0.1.md`）: 同じ選別が要る。
  ★そもそも `thread_to_task` を**既に呼んでいる**（`domain_ledger` → `plan_backfill`）
- **Research Domain**（Taka 指摘）: 同じ選別が要る

∴ **口は front door 側に置く。ESDE には置かない。**
