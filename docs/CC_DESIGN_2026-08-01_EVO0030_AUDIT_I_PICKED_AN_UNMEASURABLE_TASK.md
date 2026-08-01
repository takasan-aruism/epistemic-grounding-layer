# 【BUILT 監査 / `EVO-0030`】**★読めるようになった** — ★ただし受入(a) は★「×」ではなく**★この task では測れない**

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 13:0x / TYPE=FINDING
- **開発者規律 確認済（版: v1.1 / 2026-08-01）** ／ **受領**: `CC_IMPL_2026-08-01_EVO0030_DESTINATION_BUILT.md`
- **★報告を読む前に自分で叩いた** ／ **★コードを1行も変えていない** ／ **★ingest していない**

---

# 1. ★受入(c) — **★○。★同型5件目が★閉じた**

```
★`GET /api/state?task_id=TASK-2DER-B37727E3` に ★`upper_reviews` 欄が ★在る（★3件）
★★中身が★逐語で読める（★1件目・逐語）:
   {"phase":"UPPER_REVIEW","role":"MANAGER","identity":"claude-senior",
    "payload":{"review":{"verdict":★"PLACEHOLDER","note":"配線確認のための仮の記録。
    中身は設計/監査が書き MGR が承認する（IMPL は創作しない）。EVO-0029 受入②のため。"}}}
★★★★★∴ ★★昨日から数えて5回目の「★書けるが読めない」が ★★これで1件 閉じた。
```

## 1-1. ★★私の【未確認】が1つ解けた（★悪い方ではなかった）
```
★私は ★`EVO-0029` の監査で「★仮の判定が ★本物として台帳に残っていないか ★確かめられない」と書いた。
★★★読めるようになったので ★確かめた: ★★`verdict` は ★`PLACEHOLDER` であり ★`PASS` ではない。
   ★かつ ★note に「★IMPL は創作しない」と★書いてある。
★★★★∴ ★★私の懸念（★仮の PASS を本物と読み違える）は ★起きていない。★IMPL の書き方が正しかった。
```

---

# 2. ★★受入(a) — **★「×」と書かない。★★この task では★測れない**

```
★実測: ★最新の upper_review（★ordinal 801）は ★`verdict: "FAIL"`
   ★しかし ★`dw_state` は ★`READY_FOR_REGENERATE` ではなく ★★`JUDGE_REQUIRED`
★★★一見 ★受入(a) の × に見える。★★違う。
★★★★原因（★決定論・逐語）:
   ★`workcell.py:41`   `REWORK_ESCALATION_THRESHOLD = 2   # rework がこの回数を超えたら JUDGE_REQUIRED へ強制昇格`
   ★`workcell.py:202`  `if state in ("READY_FOR_REGENERATE","DISPOSITION_REQUIRED")
                         and view["rework_count"] >= REWORK_ESCALATION_THRESHOLD: state = "JUDGE_REQUIRED"`
★★★★★★∴ ★`FAIL` は ★★正しく `READY_FOR_REGENERATE` へ動いている。
   ★その★直後に ★既存の昇格規則が ★`JUDGE_REQUIRED` へ★上書きしている。
★★★`TASK-2DER-B37727E3` は ★REGENERATE を★2回 済ませている（★私が押した記録）＝ ★rework を使い切っている。
```

## 2-1. ★★誤りは私の SPEC にある（★3回目）
```
★私は SPEC §4 で「★(a) と (c) は ★`TASK-2DER-B37727E3` で確かめてよい」と書いた。
★★★この task は ★rework を使い切っている ∴ ★★(a) は ★構造的に測れない。
★★★★★私は ★昇格規則を ★知っていた（★`D-198` で「★rework 2回超の強制昇格＝設計どおり」と★自分で書いた）。
   ★★★知っていて ★測れない task を ★指定した。
★★★★★★本日 ★私の SPEC の誤り ★3件目である（①C-1 の位置 ②`_ALLOWED` の見落とし ③本件）。
```

## 2-2. ★★∴ 正しい判定
```
★★受入(a): ★★「★測れなかった」。★★`×` でも `○` でもない。
★★★★実装は ★私の SPEC どおりに書いており（★差分は §3）、★★コードの側に誤りは★見つかっていない。
★★★★★★測るには ★★rework を使っていない task が要る（★私の SPEC §4 が「(b)(d) は試験用の task で」と
   ★書いた ★その形を ★(a) にも当てるべきだった）。
```

---

# 3. ★差分（★独立に確認）

| repo | 変更 | 誰が |
|---|---|---|
| `dev-workcell/dw/workcell.py` | **+12/-1**（★分岐・逐語で私の SPEC §2 と一致） | ★IMPL（Claude） |
| `twoder/webui.py` | **+1**（★`upper_reviews` を並べた） | ★IMPL（Claude） |

```
★新しい state 名: ★0件（`READY_FOR_REGENERATE` / `JUDGE_REQUIRED` は既存）
★`_MAP` / `_ALLOWED` / 台帳 / 計器 / マーカー: ★触っていない
★★★`PASS` でも試験未通過なら人へ、という★私が最も重視した1本が ★逐語で入っている:
   `if v == "PASS" and bool(view.get("last_test_passed")):` … `else: state = "JUDGE_REQUIRED"`
```

---

# 4. ★次の1件（★私は決めない。★材料を出す）

| | 案 | 大きさ |
|---|---|---|
| **(1)** | **★rework 未使用の task を1つ立てて ★(a)(b)(d) を測る** | **★測定のみ。★コード変更 0** |
| (2) | ★測らずに `DONE` にする | 0 ／ ★★「効く」を確かめないまま残る |

**★私の見立て**: **★(1)。** 理由: **★(c) は閉じたが ★(a)(b)(d) は ★1つも測れていない。**
**★★「読めるようになった」までは書けるが、★「効くようになった」は ★まだ書けない。**

```
★★★★★★測るのに ★本番の依頼は要らない（★契約つきの小さな依頼を1回 投入し、★GENERATE を1回 だけ通せば
   ★rework 0 の状態で ★UPPER_REVIEW まで行ける見込み【★未確認】）。★★これは ★IMPL の手番である。
```

---

# 5. ★やっていないこと
```
★ingest していない ／ ★コードを1行も変えていない ／ ★新しい task を立てていない
★台帳を直読していない（★`/api/state` のみ）／ ★commit していない
★★`findings` 0件（★私が `EVO-0030` SPEC §0-1 で置いた材料）は ★今回 見えていない ∴ ★そのまま置く
★★★後回しはそのまま: `D-199` ／ C-3 ／ `registered_at` の固定値 ／ C-2 ／ C-4 の表示反映
```

---
**決めたこと**: **①受入(c) は ○。`GET /api/state` に `upper_reviews` 欄が在り、中身が逐語で読める。昨日から5回続いた「書けるが読めない」が1件 閉じた ②私の【未確認】が解けた——`verdict` は `PLACEHOLDER` であって `PASS` ではなく、note に「IMPL は創作しない」と書いてある。仮の判定を本物と読み違える懸念は起きていない。IMPL の書き方が正しかった ③受入(a) は「×」と書かない。最新の review は `FAIL` なのに `dw_state` は `JUDGE_REQUIRED` だが、これは `FAIL` が正しく `READY_FOR_REGENERATE` へ動いた直後に、既存の昇格規則（rework 2回超で強制昇格・`workcell.py:41,202`）が上書きしているためである ④誤りは私の SPEC にある——この task は REGENERATE を2回 済ませており rework を使い切っているので (a) は構造的に測れない。しかも私はその昇格規則を `D-198` で自分で書いて知っていた。本日3件目の SPEC の誤りである ⑤∴ 正しい判定は「測れなかった」。実装は SPEC どおりで、コードの側に誤りは見つかっていない ⑥差分は `workcell.py +12/-1` と `webui.py +1`、新しい state 名は0件、`_MAP`/`_ALLOWED`/台帳/計器に触っていない。私が最も重視した「PASS でも試験未通過なら人へ」の1本が逐語で入っている ⑦次は rework 未使用の task で (a)(b)(d) を測る案を推す。コード変更0で、本番の依頼も要らない。「読めるようになった」までは書けるが「効くようになった」はまだ書けない。**
