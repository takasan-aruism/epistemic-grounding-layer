# 【BUILT / `EVO-0030`】**★読めるようになった。★行き先も付いた** — ★(a) は本番の1件では見えない（★既存の昇格規則）

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 12:4x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0030_UPPER_REVIEW_NEEDS_A_DESTINATION.md`
- **commit していない** ／ **`:8005` を叩いていない**

---

# 1. ★変更行数（★誰が書いたか）
```
★★Claude（IMPL）が書いた。★2DER の実績に数えない。
   `dev-workcell/dw/workcell.py`  ★+11 / -1（★UPPER_REVIEW の分岐）
   `twoder/webui.py`              ★+1（★`build_state` に `upper_reviews` を1行）
★★合計 ★+12 / -1。★新しい state 名を作っていない（★足した語は
   `READY_FOR_UPPER_REVIEW` / `READY_FOR_REGENERATE` / `JUDGE_REQUIRED` ＝★すべて既存）
★`_MAP` / `_ALLOWED` / 台帳 / マーカー / S-3 の依頼文には触っていない
```

## 1-1. ★worker に書かせたか（★報告項目5）
```
★★試していない。★理由を書く:
   ★`build_planner.py:59-60` 逐語 `PROD_REPO_ROOTS = ("/home/takasan/egl", …, "/home/takasan/dev-workcell", …)`
   ＝ ★worker は ★`dev-workcell` に ★決定論で書けない（★サンドボックスの保証。★使用ガイド §3 に既出）
★★∴ ★`workcell.py` の分岐を worker に書かせる形は ★成り立たない。★1回 投げれば task が1件 増えるだけである
★★★★「試した方が価値が在る」は理解している。★★私は ★既に文書化された決定論の拒否を根拠に ★試さない方を採った。
   ★★★この判断が違うなら ★差し戻してほしい。
```

## 1-2. ★★SPEC の行番号と、名指しされた読む口が食い違っていた（★1件・先に書く）
```
★SPEC §3: 「`webui.py:221` の `"findings"` の隣に1行」＋「読む口＝`GET /api/state` の `upper_reviews` 欄」
★★実測: ★`webui.py:221` は ★★`claude_packet()` の中である（`def claude_packet` は :206）。
   ★`/api/state` を作るのは ★`build_state()`（:104）。★★別の関数である。
★★★私は ★★一度 行番号どおりに置き、★`/api/claude_packet` から読めることを確かめた（★2件・`PLACEHOLDER` 出た）
★★★★その上で ★★受入(c) が名指しした口（`/api/state`）に合わせて ★`build_state` へ移した（★1行のまま）。
★★★★★★∴ ★いま `upper_reviews` が出るのは ★`/api/state` だけである。★`claude_packet` には出ない。
   ★両方に出すかは ★設計の判断 ∴ ★私は増やさなかった。
```

---

# 2. ★受入 (a)〜(d)

| # | 受入 | 判定 | 実測 |
|---|---|---|---|
| **(c)** | `review` 本文が `GET /api/state` の `upper_reviews` から読める | **★○** | **3件 読めた**。1件目の payload 逐語: `{"review": {"verdict": "PLACEHOLDER", "note": "配線確認のための仮の記録。…"}}` |
| **(a)** | `FAIL` → `READY_FOR_REGENERATE` | **★○（★隔離環境）／★本番の1件では見えない（理由は §3）** | 隔離: `verdict=FAIL → state=READY_FOR_REGENERATE / next=REGENERATE`／本番 `B37727E3`: **`JUDGE_REQUIRED`** |
| **(b)** | `PASS`＋試験通過 → `next_operation` が `PROPOSE_COMPLETE` | **★○** | 隔離: `verdict=PASS → state=READY_FOR_UPPER_REVIEW / next=PROPOSE_COMPLETE` |
| **(d)** | `INDETERMINATE` / 知らない値 / `PASS` だが試験未通過 → `JUDGE_REQUIRED` | **★○（2/3）／★1つは前提に到達できず** | `INDETERMINATE → JUDGE_REQUIRED`／`WHATEVER → JUDGE_REQUIRED`／**`PASS` だが試験未通過は、★そもそも `AUDIT` の時点で `READY_FOR_REGENERATE` になり ★`UPPER_REVIEW` を記録できない**（★`_ALLOWED` が拒む）＝ **★この枝は実行では踏めない** |

**★隔離環境で測った**（`DW_DATA_DIR` を一時領域に向けた・**★本番の台帳には1行も書いていない**）。**本番の1件（`B37727E3`）は SPEC の指示どおり (a) と (c) にだけ使った。**

---

# 3. ★(a) が本番の1件で見えない理由（★私の変更ではない・逐語）

```
★`workcell.py:41` 逐語  `REWORK_ESCALATION_THRESHOLD = 2   # rework がこの回数を超えたら JUDGE_REQUIRED へ強制昇格`
★`workcell.py:202` 逐語 `if state in ("READY_FOR_REGENERATE","DISPOSITION_REQUIRED") and view["rework_count"] >= …: state = "JUDGE_REQUIRED"`
★★実測: ★`TASK-2DER-B37727E3` は ★`rework_count = 2` ＝ ★閾値に達している
★★★∴ ★私の分岐は ★`READY_FOR_REGENERATE` を出しているが、★その直後に ★既存の規則が ★`JUDGE_REQUIRED` へ昇格させる。
★★★★★これは ★私の変更の不具合ではなく、★★既に在る意図された機構である（★2回 rework しても直らないものは人へ）。
★★★★★★∴ ★本番の1件で (a) を測ると ★必ず `JUDGE_REQUIRED` になる。★隔離環境で測った理由がこれである。
```

---

# 4. ★予告の当否（★投入前に固定・`e30_pre.txt`）

| 予告 | 結果 |
|---|---|
| 変更行数 `workcell +11/-1` ＋ `webui +1` | **★当たり** |
| (a) `FAIL → READY_FOR_REGENERATE` | **★半分**——隔離では当たり。**★本番の1件では外れた**（★既存の昇格規則。★予告に書いていなかった） |
| (b) `PROPOSE_COMPLETE` | **★当たり** |
| (c) `/api/state` の `upper_reviews` から読める | **★当たり**（★ただし §1-2 のとおり ★置き場所を移して初めて当たった） |
| (d) `JUDGE_REQUIRED` | **★2/3 当たり**。**★`PASS` だが試験未通過は ★実行では踏めない枝だった**（★予告では踏める前提だった） |

---

# 5. ★戻し方（★可逆・報告項目4）
```
★① `dev-workcell/dw/workcell.py` の `elif ph == "UPPER_REVIEW":` の本文を
     ★1行 `view["upper_reviews"].append(e); state = "READY_FOR_UPPER_REVIEW"` に戻す
★② `twoder/webui.py` の `build_state` から ★`"upper_reviews": …` の1行を消す
★★どちらも ★足しただけなので ★消せば元に戻る。★`git checkout -- <file>` でも戻せる（★他の変更は無い）
★★★★戻すと ★(c) は読めなくなり、★(a)(b)(d) は「verdict を見ない」動きに戻る。
```

---

# 6. ★`findings` 0件について（★報告項目6・★掘っていない）
```
★設計が §0-1 で挙げた「★試験は FAILED なのに findings が 0件」は、★(a) の測定中にも ★そのまま見えた:
   ★`/api/state` の応答に ★`findings` 欄が ★無い（★`claude_packet` には在り、★そこでは 0件）
★★私は原因を書かない（★1回の観測・★掘るなと指示されている）。★見えたことだけ書く。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0030`。**Claude（IMPL）が書いた+12/-1**（`workcell.py` の UPPER_REVIEW 分岐 +11/-1、`webui.py` の `build_state` に `upper_reviews` +1）。新しい state 名は作らず、`_MAP`/`_ALLOWED`/台帳/マーカーにも触っていない。**worker には試していない——`build_planner.py:59-60` の `PROD_REPO_ROOTS` に `dev-workcell` が入っており決定論で書けないため（既出のサンドボックス保証）。試さない判断が違うなら差し戻してほしい。** **★SPEC の行番号と名指しされた読む口が食い違っていた——`webui.py:221` は `claude_packet()` の中で、`/api/state` を作るのは `build_state()` である。一度 行番号どおりに置いて `claude_packet` から読めることを確かめたうえで、受入(c) が名指しした `/api/state` へ移した（1行のまま。両方に出すかは設計の判断なので増やしていない）。** **受入は (c)○（3件 読めた・逐語つき）／(a)○（隔離環境で `FAIL → READY_FOR_REGENERATE`）／(b)○（`PASS`＋試験通過 → `next_operation=PROPOSE_COMPLETE`）／(d) 2/3○（`INDETERMINATE` と知らない値は `JUDGE_REQUIRED`）。** **★(a) が本番の1件で見えないのは私の不具合ではなく既存の機構——`REWORK_ESCALATION_THRESHOLD=2` と `workcell.py:202` により、`rework_count=2` の `B37727E3` では `READY_FOR_REGENERATE` が直後に `JUDGE_REQUIRED` へ昇格する。だから隔離環境（`DW_DATA_DIR` を一時領域）で測り、本番の台帳には1行も書いていない。** **★(d) の3つ目「`PASS` だが試験未通過」は実行では踏めない枝だった——試験未通過だと `AUDIT` の時点で `READY_FOR_REGENERATE` になり `_ALLOWED` が `UPPER_REVIEW` の記録を拒むため。** 戻し方は2箇所を消すだけ（`git checkout` でも戻る）。**`findings` 0件は (a) の測定中にもそのまま見えた（`/api/state` には欄が無く `claude_packet` では0件）——原因は書かない。** commit していない。*
