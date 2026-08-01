# 【BUILT / `EVO-0029` 訂正版】**★2つ目の関門も開いた。★書けた** — ★ただし **★書いた中身は読めない**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 12:0x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0029_I_MISSED_THE_SECOND_TABLE.md`
- **★3つ目の関門は出なかった** ／ **commit していない**

---

# 1. ★変更行数
```
★`dev-workcell/dw/dispatch.py`  +1行（★前回の `_MAP` の1行。★そのまま）
★`dev-workcell/dw/workcell.py`  +1/-1行（★今回。★`_ALLOWED["UPPER_REVIEW"]` に `"JUDGE_REQUIRED"` を1語）
★★合計 ★2ファイル・★2箇所。★どちらも1行。★`conformance.py` / `ingest` / 状態語 / 台帳には触っていない
```

---

# 2. ★受入（①〜⑤）

| # | 受入 | 判定 | 実測（逐語） |
|---|---|---|---|
| **①** | `next_operation` が `UPPER_REVIEW` | **★○** | `dw_state=JUDGE_REQUIRED / next=UPPER_REVIEW / actor=CLAUDE` |
| **②** | `POST /api/ingest` が `WorkflowViolation` を返さず通る | **★○** | **通った**。返り値 `dw_state=READY_FOR_UPPER_REVIEW / last=UPPER_REVIEW` |
| **③** | `dw_state` が `READY_FOR_UPPER_REVIEW` に変わる | **★○** | `/api/state` で確認: `dw_state=READY_FOR_UPPER_REVIEW / last=UPPER_REVIEW / next=UPPER_REVIEW / actor=CLAUDE` |
| **④** | 戻せる（2箇所を戻すと `BLOCKED`） | **★○（実際に戻して確かめ、また足した）** | 戻した後: `next=BLOCKED / actor=-`（★`git diff` が**空**＝完全に元に戻った）／足し直した後: `next=UPPER_REVIEW / actor=CLAUDE` |
| **⑤** | **書いた review が front door から読めるか** | **★★×——「書けたが読めない」** | 下表 |

## 2-1. ★受入⑤（★同型を5回目にしないための実測・★口を5つ叩いた）
| 口 | 書いた中身（`PLACEHOLDER`）が出るか | `upper_review` の語が出るか |
|---|---|---|
| `/api/state?task_id=` | **★出ない** | 出る |
| `/api/claude_packet?task_id=` | **★出ない** | 出る |
| `/api/resolve?id=` | **★出ない** | 出る |
| `/api/tasks` | 出ない | 出ない |
| `/api/control` | 出ない | 出ない |

```
★★∴ ★「上級監査が済んだ」ことは ★front door から分かる（★`last_completed_op=UPPER_REVIEW`・★語も出る）
★★★しかし ★★「★何と書かれたか」は ★どの口からも読めない。
★★★★★∴ ★★「書けたが読めない」。★★これが ★5回目の同型である（★言い換えない）。
```

---

# 3. ★3つ目の関門は出たか（★報告項目5）
```
★★出なかった。★`ingest` は1回で通り、★`derive_state` も ★`READY_FOR_UPPER_REVIEW` を返した。
★設計の下調べ（`conformance.py:31` に `JUDGE_REQUIRED` が既に入っている）は ★実行でも裏づけられた。
★★∴ ★止めて聞く条件には ★当たらなかった。
```

---

# 4. ★予告の当否（★投入前に固定・`e29b_pre.txt`）

| 予告 | 結果 |
|---|---|
| 変更は1語（＝1行） | **★当たり** |
| ① `next=UPPER_REVIEW` | **★当たり** |
| ② `ingest` が通る | **★当たり** |
| ③ `READY_FOR_UPPER_REVIEW` | **★当たり** |
| ④ 2箇所を戻すと `BLOCKED` | **★当たり**（★`git diff` が空になることまで確認） |
| ⑤ **読めない見込み** | **★当たり。★ただし「まったく出ない」ではない**——**★`upper_review` の語は3つの口に出る。★出ないのは★中身である**（★私の予告より状況は細かい） |

---

# 5. ★前回の副作用は解消した
```
★前回の BUILT で書いた「★押せる顔をして押せない」状態は ★解消した。
   ★いまは ★next=UPPER_REVIEW と表示され、★実際に ★書ける。
★★戻す必要は ★無くなった（★戻す指示が来れば ★2箇所を消すだけ・★確認済）。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0029` 訂正版＝`workcell._ALLOWED["UPPER_REVIEW"]` に `"JUDGE_REQUIRED"` を1語。**変更は2ファイル・2箇所・どちらも1行（`dispatch._MAP` の1行＋今回の1語）で、`conformance.py`・`ingest`・状態語・台帳には触っていない。** **受入①②③④は すべて ○——`next=UPPER_REVIEW`、`POST /api/ingest` が `WorkflowViolation` を返さず通り、`dw_state` が `READY_FOR_UPPER_REVIEW`（`last_completed_op=UPPER_REVIEW`）に変わり、2箇所を戻すと `next=BLOCKED` に戻って `git diff` が空になることまで確かめて、また足した。★3つ目の関門は出なかった（`conformance.py` の下調べが実行でも裏づけられた）。** **★受入⑤は ×——口を5つ叩いたが、書いた中身（`PLACEHOLDER`）は `/api/state`・`/api/claude_packet`・`/api/resolve`・`/api/tasks`・`/api/control` の どこにも出ない。`upper_review` という語は3つの口に出るので「上級監査が済んだ」ことは分かるが、「何と書かれたか」は読めない ＝ ★「書けたが読めない」。これが5回目の同型である（言い換えない）。** 予告は5つとも当たったが、⑤だけ**私の予告より状況が細かかった**——「まったく出ない」のではなく「語は出るが中身が出ない」。**前回 報告した「押せる顔をして押せない」副作用は解消した。** commit していない。*
