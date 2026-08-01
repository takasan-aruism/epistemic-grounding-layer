# 【BUILT / `EVO-0029`】1行は効いた。**★しかし書けない** — ★`_MAP` の外に★もう1つの表が在る

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-08-01 08:1x / TYPE=BUILT
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **実装源**: `CC_DESIGN_2026-08-01_EVO0029_GIVE_JUDGE_REQUIRED_A_TURN.md`
- **★止めた**（★`workcell.py` を変えるのは §5 で禁止されている）／ **commit していない**

---

# 1. ★変更行数
```
★`dev-workcell/dw/dispatch.py` のみ ／ ★+1行 / -0行（★案A のまま）
   "JUDGE_REQUIRED":           ("UPPER_REVIEW",    "CLAUDE_SENIOR",      "TASK+RUNS+TEST_RESULT",       True),
★★他のファイルは1行も変えていない（`workcell.py` / `webui.py` / `ingest` に触っていない）
```

---

# 2. ★受入（①〜⑤）

| # | 受入 | 判定 | 実測（逐語） |
|---|---|---|---|
| **①** | `next_operation` が `BLOCKED` → `UPPER_REVIEW` | **★○** | `dw_state=JUDGE_REQUIRED / next=UPPER_REVIEW / actor=CLAUDE / barrier=True`（★前: `next=BLOCKED / actor=- / barrier=False`） |
| **②** | `POST /api/ingest` が `ValueError` を返さず通る | **★×** | **`{"error": "WorkflowViolation: phase UPPER_REVIEW は state=JUDGE_REQUIRED から不可(allowed=['READY_FOR_UPPER_REVIEW'])"}`** |
| **③** | `dw_state` が `READY_FOR_UPPER_REVIEW` に変わる | **★×（到達せず）** | `dw_state=JUDGE_REQUIRED` のまま（★`last=AUDIT` も不変） |
| **④** | 戻せる（1行を消したら `BLOCKED` に戻る） | **★○（★実際に消して確かめ、また足した）** | 消した後: `next=BLOCKED / actor=- / barrier=False`／足し直した後: `next=UPPER_REVIEW / actor=CLAUDE` |
| **⑤** | 書いた review が front door から読めるか | **★測れない** | **★②が通っていないので ★review が存在しない。**「読めない」ではなく**「書けていないので測れない」**（★「測って0」と「測れない」を分ける） |

---

# 3. ★止まった理由（★逐語・1つ）

> ### **★`_MAP` の外に、★もう1つの許可表が在る。**

```
★`dw/dispatch.py:_MAP`      … ★状態 → 次の操作・actor・入力・barrier（★私が1行 足した表）
★★`dw/workcell.py:_ALLOWED` … ★★操作 → ★それを許す状態（★別の表）
   逐語 `workcell.py:336`: "UPPER_REVIEW": {"READY_FOR_UPPER_REVIEW"}
   逐語 `workcell.py:340-343`: _require_state → state not in _ALLOWED[phase] なら WorkflowViolation
★★★∴ ★`_MAP` が「あなたの手番は UPPER_REVIEW だ」と言っても、
   ★`record_upper_review` は ★`JUDGE_REQUIRED` からの UPPER_REVIEW を ★受け付けない。
★★★★★SPEC §2-1 の見立て（★「`_require_state` を通る ∴ 案A が要る」）は ★半分だけ当たっていた——
   ★案A は ★必要だが ★十分ではない。★`_ALLOWED` の1行が★もう1つ要る。
★★★★★★私は ★`workcell.py` を変えない（★§5 の禁止）∴ ★ここで止めた。
```

## 3-1. ★★いま生じている副作用（★先に言う・★判断は設計/MGR）
```
★★1行を足したままなので、★`/api/state` は ★「next=UPPER_REVIEW / actor=CLAUDE」と ★手番が在るように見える。
★★★しかし ★書こうとすると ★WorkflowViolation で弾かれる ＝ ★★「押せる顔をして押せない」状態である。
★★★★★これは ★BLOCKED と表示されていた時より ★誤解を招く可能性が在る。
★★★★★★∴ ★★戻す（1行を消す）方がよければ ★言ってほしい。★★私は ★SPEC ⑦「また足す」に従って ★足したままにしている。
```

---

# 4. ★予告の当否（★投入前に固定・`e29_pre.txt`）

| 予告 | 結果 |
|---|---|
| 変更は1行 | **★当たり** |
| ① `BLOCKED` → `UPPER_REVIEW`（actor `-`→`CLAUDE_SENIOR`、barrier `False`→`True`） | **★当たり**（actor の表示は `CLAUDE`） |
| ② `ingest` が通る | **★★外れた**（`WorkflowViolation`） |
| ③ `READY_FOR_UPPER_REVIEW` になる | **★★外れた**（到達せず） |
| ④ 消したら戻る | **★当たり**（★実際に消して確かめ、また足した） |
| ⑤ **読めない見込み** | **★★予告そのものが成り立たなかった**（★書けていないので測れない）。**★「読めない」と書けば嘘になる** |

**★順序を1つ変えた（★予告に理由を書いた）**: 手順は ⑤ingest → ⑥1行消して④ だが、**★ingest が通れば task は `JUDGE_REQUIRED` でなくなり ④が確かめられない** ∴ **①→④→②③** の順にした。**★受入の中身は1つも変えていない。**（★結果として ②が通らなかったので、この並べ替えが無くても ④は確かめられたことになる）

---

# 5. ★戻して戻ったか（★報告項目4）
```
★戻った。★1行を消して再起動 → ★`next=BLOCKED / actor=- / barrier=False`（★元と同じ）
★★また足して再起動 → ★`next=UPPER_REVIEW / actor=CLAUDE`
★★★∴ ★この変更は ★1行の足し引きで完全に戻せる。
```

# 6. ★読む口は在ったか（★報告項目5）
```
★★測れていない（★②が通っていないため）。★ただし ★材料だけ書く:
   ★`workcell.py:184` 逐語 `view["upper_reviews"].append(e)` ＝ ★view には ★溜まる欄が在る
   ★★`/api/state` の `work` のキーは ★`next_information_need` / `acquisition_method` / `dw_task_id` の3つだけ
      ＝ ★★`upper_reviews` は ★front door の応答に ★出ていない
★★★∴ ★設計の見立て（★「`upper_reviews` を front door から読む口は見つけていない」）と ★同じものを ★私も見た。
★★★★「書いたら読める」は ★★まだ確かめられていない（★書けていないので）。
```

---
*IMPL → 設計/監査（写: MGR / Taka）。`EVO-0029`＝案A（`dispatch.py:_MAP` に `JUDGE_REQUIRED` の1行）。**変更は 1行・1ファイルのみ。** **受入①○（`next` が `BLOCKED`→`UPPER_REVIEW`、actor `-`→`CLAUDE`、barrier `False`→`True`）／★②×（`POST /api/ingest` が `WorkflowViolation: phase UPPER_REVIEW は state=JUDGE_REQUIRED から不可(allowed=['READY_FOR_UPPER_REVIEW'])`）／③×（到達せず・`JUDGE_REQUIRED` のまま）／④○（1行を消したら `BLOCKED` に戻り、足し直したら `UPPER_REVIEW` に戻った＝完全に可逆）／⑤は「読めない」ではなく★「書けていないので測れない」。** **止まった理由は1つ——`_MAP` の外に `workcell.py:_ALLOWED` というもう1つの表が在り、逐語 `"UPPER_REVIEW": {"READY_FOR_UPPER_REVIEW"}` なので `JUDGE_REQUIRED` からの UPPER_REVIEW は `_require_state` で弾かれる。案A は必要だが十分ではなく、`_ALLOWED` にもう1行 要る。`workcell.py` の変更は §5 で禁止されているので止めた。** **★副作用を先に言う——1行を足したままなので `/api/state` は「手番が在る」ように見えるのに書けば弾かれる＝「押せる顔をして押せない」状態であり、`BLOCKED` 表示より誤解を招きうる。戻す方がよければ言ってほしい（私は SPEC ⑦「また足す」に従って足したままにしている）。** 予告は①④が当たり、②③が外れ、⑤は予告そのものが成り立たなかった。手順の順序を1つ変えた理由（ingest 後は ④が確かめられない）は投入前に予告へ書いた。**読む口については、`workcell.py:184` に `view["upper_reviews"]` が在る一方 `/api/state` の `work` は3キーだけで `upper_reviews` は front door に出ていない——設計の見立てと同じものを私も見た。** commit していない。*
