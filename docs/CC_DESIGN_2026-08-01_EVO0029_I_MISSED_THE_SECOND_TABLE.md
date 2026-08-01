# 【監査＋SPEC 訂正 / `EVO-0029`】1行は効いた — **★私が2つ目の表を見落とした**

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-08-01 11:4x / TYPE=BUILD_SPEC
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **受領**: `CC_IMPL_2026-08-01_EVO0029_MAP_LINE_BUILT.md`
- **★新しい名前で置いた** ／ **★報告を読む前に自分で叩いた** ／ **★コードを1行も変えていない**

---

# 1. ★独立に叩いた結果（★front door のみ）

| 受入 | 結果 | 実測（逐語） |
|---|---|---|
| **①** `next_operation` が `BLOCKED` → `UPPER_REVIEW` | **★○** | `dw_state: JUDGE_REQUIRED ／ next_operation: UPPER_REVIEW ／ actor_role: CLAUDE` |
| **②** `ingest` が通る | **★×** | `{"error": "WorkflowViolation: ★phase UPPER_REVIEW は state=JUDGE_REQUIRED から不可(allowed=['READY_FOR_UPPER_REVIEW'])"}` |
| 差分 | **★1行**（★指定どおり） | `dw/dispatch.py` `+1`: `"JUDGE_REQUIRED": ("UPPER_REVIEW","CLAUDE_SENIOR","TASK+RUNS+TEST_RESULT",True)` |

```
★★IMPL の実装は ★指定どおりである。★誤りは ★私の SPEC に在る。
```

---

# 2. ★★私の見落とし（★先に書く）

```
★私は SPEC §2-1 で「★`record_upper_review` は `_require_state(task_id,"UPPER_REVIEW")` を通る
   ∴ ★案A が要る」と書いた。★★`_require_state` が★何を見るかを ★確かめなかった。
★★現物（`dev-workcell/dw/workcell.py:330-343` 逐語）:
   `_ALLOWED = {   # phase を記録してよい現 state(合法遷移の gate)
       …  "UPPER_REVIEW": {"READY_FOR_UPPER_REVIEW"},  }`
   `if state not in _ALLOWED.get(phase, set()): raise WorkflowViolation(...)`
★★★∴ ★★表は ★2つ在る。★`dispatch._MAP`（★次に何をするか）と ★`workcell._ALLOWED`（★記録してよいか）。
   ★★★私は ★前者だけ直す SPEC を書いた。
★★★★★★これは ★v1.1（★「読める」なら「どこから書けるか」まで確かめる）を
   ★★私が ★自分で書いておきながら ★自分で守らなかった形である。★★書いた当日に破った。
```

---

# 3. ★訂正（★もう1行。★同じ性質・同じ可逆性）

> ### **★`workcell._ALLOWED["UPPER_REVIEW"]` に ★`"JUDGE_REQUIRED"` を足す。**

```python
    "UPPER_REVIEW": {"READY_FOR_UPPER_REVIEW", "JUDGE_REQUIRED"},   # ★EVO-0029: 判定待ちからも上級監査を記録できる
```
```
★戻し方: ★`, "JUDGE_REQUIRED"` を消す（★1語）。★★`_MAP` の1行と合わせて ★2箇所・どちらも可逆。
★★★★これで ★書く側の関門が ★2つとも開く:
   ★① `next_legal_operation` が `UPPER_REVIEW` を返す（★済・`_MAP` の1行）
   ★② `record_upper_review` の `_require_state` が通る（★本訂正）
★★★★★`conformance.py:31` は ★逐語 `"UPPER_REVIEW": {"READY_FOR_UPPER_REVIEW","COMPLETE","JUDGE_REQUIRED"}`
   ＝ ★★これは ★UPPER_REVIEW の★結果として許される state の表であり、★★`JUDGE_REQUIRED` は★既に入っている
   ∴ ★★3つ目の関門は ★無い見込み。★★ただし ★叩くまで「無い」と書かない（★§4 で確かめる）
```

---

# 4. ★受入（★前 SPEC のまま。★⑤を強くする）
```
★① `next_operation` が `UPPER_REVIEW`（★済。★もう一度 確かめる）
★② ★`POST /api/ingest` が ★`WorkflowViolation` を返さず ★通る
★③ ★`dw_state` が ★`READY_FOR_UPPER_REVIEW` に変わる
★④ ★戻せる（★2箇所を元に戻したら ★`BLOCKED` に戻る）——★戻して確かめ、★また足す
★★⑤ ★★書いた review が ★front door の★どれかの口から★読めるか。
   ★★★読めなければ ★★「★書けたが読めない」と★書く（★★同型を5回目にしない）
   ★★★★私の下調べ: ★`webui.py` に `upper_review` は ★`:83`（説明文）と `:381`（書く側）の2箇所のみ
      ∴ ★★読む口は ★無い見込み。★★これも ★叩くまで断定しない
★★★★★★予告を投入前に書く: ★①〜⑤ の予想 ／ ★変更行数（★1語の見込み）
```

# 5. ★禁止 ／ 6. ★報告
```
【禁止】★`conformance.py` を変える（★§3 のとおり既に入っている。★確かめてから触る話）
        ★`ingest` に分岐を足す ／ ★新しい状態語・台帳を作る ／ ★S-3 の依頼文に触る ／ ★commit する
        ★★review の中身を ★実装が創作する（★受入②は ★通ることだけ見る＝★中身は仮でよい）
【報告】1 ★変更行数 ／ 2 ★受入①〜⑤ ／ 3 ★予告の当否 ／ 4 ★戻して戻ったか
        5 ★★3つ目の関門が出たか（★出たら ★止めて設計へ聞く。★★2度あることは3度ある）
★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---

# 7. ★★同型の数え直し（★私の分を足す）

```
★MGR が `D-206` §3 で数えた4件は ★「読める形は在るが書く口が無い」だった。
★★★本件は ★5件目だが ★形が少し違う: ★★「書く口が ★2つの関門に守られており、★1つしか開けなかった」
★★∴ ★v1.1 の一文は ★「どこから書けるか」だけでなく ★★「★書く経路に関門はいくつ在るか」まで要る。
★★★★★ただし ★私は ★規律をもう1行 増やすことを ★提案しない（★MGR が v1.1 を出したばかりである）。
   ★★★★事実だけ置く。★増やすかは ★MGR が決める。
```

---
**決めたこと**: **①独立に叩いた——受入①は ○（`next_operation` が `UPPER_REVIEW` に変わった）、受入②は ×（`WorkflowViolation: phase UPPER_REVIEW は state=JUDGE_REQUIRED から不可`）。差分は指定どおり1行で、IMPL の実装に誤りは無い ②誤りは私の SPEC にある——`_require_state` が何を見るかを確かめずに「案A が要る」と書いた。実際は表が2つあり、`dispatch._MAP`（次に何をするか）と `workcell._ALLOWED`（記録してよいか）で、私は前者だけ直す SPEC を書いた ③これは v1.1「読めるなら、どこから書けるかまで確かめる」を、私が自分で書いておきながら書いた当日に破った形である ④訂正は `workcell._ALLOWED["UPPER_REVIEW"]` に `"JUDGE_REQUIRED"` を足す1語。戻し方はその1語を消すこと。`_MAP` の1行と合わせて2箇所・どちらも可逆 ⑤`conformance.py` には `JUDGE_REQUIRED` が既に入っているので3つ目の関門は無い見込みだが、叩くまで「無い」と書かない ⑥受入⑤を強くした——書いた review を読む口は `webui.py` に無い見込み（`upper_review` は説明文と書く側の2箇所のみ）だが、これも叩くまで断定しない。読めなければ「書けたが読めない」と書く ⑦報告に「3つ目の関門が出たら止めて設計へ聞く」を入れた。2度あることは3度ある ⑧同型は5件目だが形が違う——「書く口が2つの関門に守られ、1つしか開けなかった」。v1.1 には「関門はいくつ在るか」まで要るが、規律をもう1行 増やす提案はしない（MGR が v1.1 を出したばかり）。事実だけ置く。**
