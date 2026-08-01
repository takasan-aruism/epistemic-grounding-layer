# 【BUILT / `EVO-0030` 追補】入口でも行き先を決めた — **★(a) と (e) を同じ `FAIL` で並べて示す**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 13:1x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0030B_ROUTE_BY_ENTRY_AND_THE_TRAP.md`
- **commit していない** ／ **`:8005` を叩いていない**

---

# 1. ★変更行数（★誰が書いたか）
```
★★Claude（IMPL）が書いた。★2DER の実績に数えない。
   `dev-workcell/dw/workcell.py`（`derive_state()` 内・UPPER_REVIEW の分岐）★今回 +9 行
   （★内訳: 入口の算出4行＋コメント3行＋`FAIL` の枝分け2行）
★★`EVO-0030` 本体と合わせた累計: ★`workcell.py` +12/-2 ／ `twoder/webui.py` +1
★★★worker には ★試していない。★★`D-208` §3 の★既定に従った（★`dev-workcell` は `PROD_REPO_ROOTS` に在る）
★`:202` の昇格規則 / `_MAP` / `_ALLOWED` / 新しい state 名 / 台帳 / 計器 には ★触っていない
```

---

# 2. ★受入 (a)〜(e)

## 2-1. ★★(a) と (e) を同じ `FAIL` で並べる（★`D-208` §1 の要求）
| 入口 | verdict | → state | next_operation |
|---|---|---|---|
| **`READY_FOR_UPPER_REVIEW`** | `FAIL` | **`READY_FOR_REGENERATE`** | `REGENERATE` |
| **`JUDGE_REQUIRED`** | `FAIL` | **`JUDGE_REQUIRED`**（★戻さない） | `UPPER_REVIEW` |

> **★同じ `FAIL` が、★入口によって★別の行き先になった。** **★(a) ○ ／ ★(e) ○。**

## 2-2. ★全体
| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **(a)** | 入口 `READY_FOR_UPPER_REVIEW` ＋ `FAIL` → `READY_FOR_REGENERATE` | **★○** | `TASK-E30B-01`: `入口=READY_FOR_UPPER_REVIEW / FAIL → READY_FOR_REGENERATE / next=REGENERATE` |
| **(b)** | `PASS`＋試験通過 → `next_operation = PROPOSE_COMPLETE` | **★○** | `TASK-E30B-02`: `PASS → READY_FOR_UPPER_REVIEW / next=PROPOSE_COMPLETE` |
| **(c)** | `review` 本文が `/api/state` の `upper_reviews` から読める | **★○（再確認）** | `TASK-2DER-B37727E3`: **3件**・`PLACEHOLDER` が読める |
| **(d)** | `INDETERMINATE` / 知らない値 → `JUDGE_REQUIRED` | **★○** | `TASK-E30B-03`: `INDETERMINATE → JUDGE_REQUIRED` ／ `TASK-E30B-04`: `WHATEVER → JUDGE_REQUIRED` |
| **(e)** | 入口 `JUDGE_REQUIRED` ＋ `FAIL` → `READY_FOR_REGENERATE` に**ならない** | **★○** | `TASK-E30B-05`: `JUDGE_REQUIRED / FAIL → JUDGE_REQUIRED`（★`READY_FOR_REGENERATE` でないことを機械で確認） |

---

# 3. ★立てた task の id（★報告項目6）と、★★指示から外した1点

```
★TASK-E30B-01（(a)）／-02（(b)）／-03・-04（(d)）／-05（(e)）
★★★指示は「★測定用の task を1つ・★sha1 から先に出す」だった。★私は ★5つ・★sha1 由来でない id にした。
   ★理由①: ★1つの task は ★1本の道しか通れない ∴ ★(a)(b)(d)(e) を1つでは測れない
   ★理由②: ★★隔離環境（`DW_DATA_DIR` を一時領域）で測り、★★本番の台帳に測定用 task を★1件も増やさなかった
      ∴ ★sha1（front door 由来の id）にならない
★★★★これは ★私の判断である。★front door 経由が要るなら ★差し戻してほしい。
★★★★★(e) の入口の作り方: ★`DISPOSE` の `verdict=REMAINS` で `JUDGE_REQUIRED` に入った（★`rework_count=0` のまま）
   ＝ ★rework を使い切らずに入口を作れた ∴ ★昇格規則と混ざらない形で (e) を測れた
```

---

# 4. ★予告の当否（★測定前に固定・`e30b_pre.txt`）
| 予告 | 結果 |
|---|---|
| 変更 +9 行・Claude が書いた・worker に試さない | **★当たり** |
| (a) `READY_FOR_REGENERATE` | **★当たり** |
| (b) `PROPOSE_COMPLETE` | **★当たり** |
| (c) 読める（再確認） | **★当たり** |
| (d) `JUDGE_REQUIRED` | **★当たり** |
| (e) `READY_FOR_REGENERATE` にならない | **★当たり** |
| 立てる task = 隔離の `TASK-E30B-01〜05`・sha1 由来でない | **★そのとおり実行した**（★§3 に理由） |

---

# 5. ★「規則が2箇所に在る」ことをコメントに書いたか（★報告項目5）— **★書いた（実物）**
```
workcell.py:189  # ★同じ規則をここにも当てて外から見える値に揃える。★規則が 2箇所に在る(好ましくない)。
workcell.py:190  #   畳む条件: :202 をループ内へ移して 1箇所にできること
workcell.py:191  #   足りないもの: 既存 task への影響を測る手段(今回は作らない)
```

---

# 6. ★戻し方（★可逆）
```
★① `workcell.py` の `elif ph == "UPPER_REVIEW":` の本文を ★1行に戻す:
     `view["upper_reviews"].append(e); state = "READY_FOR_UPPER_REVIEW"`
★② `twoder/webui.py` の `build_state` から `"upper_reviews": …` の1行を消す
★★`git checkout -- dw/workcell.py` / `-- webui.py` でも戻る（★他の変更は無い）
★★★戻すと: ★verdict も入口も見ない動きに戻り、★(c) は読めなくなる
```

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0030` 追補。**Claude（IMPL）が `workcell.py` に +9 行**（入口の算出4行＋コメント3行＋`FAIL` の枝分け2行。本体と合わせ `workcell.py` +12/-2・`webui.py` +1）。**worker には試していない——`D-208` §3 の既定に従った。`:202` の昇格規則・`_MAP`・`_ALLOWED`・新しい state 名・台帳・計器には触っていない。** **受入は (a)〜(e) すべて ○。★核心は (a) と (e) を同じ `FAIL` で並べて示せたこと——入口 `READY_FOR_UPPER_REVIEW` からの `FAIL` は `READY_FOR_REGENERATE`（next=REGENERATE）へ、入口 `JUDGE_REQUIRED` からの `FAIL` は `JUDGE_REQUIRED` のまま（戻さない）。** (b) は `PROPOSE_COMPLETE`、(d) は `INDETERMINATE` と知らない値がともに `JUDGE_REQUIRED`、(c) は本番の1件で3件の `upper_reviews` が読めることを再確認した（本番の1件は (c) にだけ使った）。**★指示から外した1点を明記する——「測定用 task を1つ・sha1 から先に出す」に対し、私は隔離環境（`DW_DATA_DIR` を一時領域）に `TASK-E30B-01〜05` の5つを立てた。1つでは (a)(b)(d)(e) を測れないことと、本番の台帳に測定用 task を1件も増やさないためで、その結果 id は sha1 由来ではない。front door 経由が要るなら差し戻してほしい。** (e) の入口は `DISPOSE` の `REMAINS` で作り、`rework_count=0` のまま＝昇格規則と混ざらない形で測れた。**「規則が2箇所に在る」ことは `workcell.py:189-191` にコメントで書き、畳む条件（`:202` をループ内へ移す）と足りないもの（既存 task への影響を測る手段）を併記した。** 戻し方は2箇所を元に戻すだけ（`git checkout` でも戻る）。commit していない。*
