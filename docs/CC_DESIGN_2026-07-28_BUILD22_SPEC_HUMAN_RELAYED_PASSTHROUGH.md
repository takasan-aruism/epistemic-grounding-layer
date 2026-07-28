# BUILD SPEC — Build 22: **`origin` / `relayed_by` / `authored_by` を front door に通す（G-30）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=BUILD_SPEC / **v1.1**（MGR の3点訂正を反映）
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- 権限: `CC_MGR_2026-07-28_G30_RULING_NOT_BLOAT_BUILD22.md`

## 0. ★これは修理である。新機能ではない
| 足す | 廃止する |
|---|---|
| `submit()` の引数3つ（**既定は現行のまま**） | **front door が `origin="MACHINE_SUBMIT"` を直書きしている固定** |

**新しい台帳・記録の種類・語彙を作らない**（`HUMAN_RELAYED` / `relayed_by` / `authored_by` は DS に既に在る）。
**目的**: **依頼主の言葉を「依頼主が書いた」として台帳に残せるようにする。**
> **★これは記録を正直にする修理であり、系の判断は1つも変わらない。**
> **「全案件を台帳経由で管理する」の必要条件であって、十分条件ではない。**（MGR 訂正 (1)）

---

## 1. ★MGR の予想を、実行前に訂正する（私が読んだ事実）
**MGR は §3-4 で「(c) `origin` だけ渡した場合は**素通りする**」と予想した。**
```
再現: sed -n '113,117p' ds/ds/phase0.py
  if origin not in ORIGINS:
      raise ValueError(...)
  if origin == "HUMAN_RELAYED" and not (relayed_by and authored_by):
      raise ValueError("origin=HUMAN_RELAYED は relayed_by と authored_by の併記を要求する"
                       "（『直接打った』と偽らないため）")
```
> **★DS は強制している。素通りしない。** **`HUMAN_RELAYED` を単独で渡せば `ValueError` になる。**
> **∴ これは予想ではなく、読めば分かる事実である。** **予想欄に入れない**（規律: 予想を固定する前に、決定論で確定できることを確定する）。
> **★IMPL は「読んだ結果」ではなく「実行した結果」で確かめること。** **私の読みが誤っていれば、そう書く。**

**∴ 設計上の帰結**: **`submit()` は3つを素通しするだけでよい。** **検証を自分で書かない。** **DS が既に守っている。**

---

## 2. 変更（2ファイル・最小）
```
① twoder/submit.py::submit(
     raw_input, conversation_id="taka-main", seed=0, admission_payload=None,
     ledger_path=None, formal_candidates=None, ts=None,
     origin="MACHINE_SUBMIT", relayed_by=None, authored_by=None)      ← ★既定は現行の値
   → phase0.record_utterance(..., origin=origin, relayed_by=relayed_by, authored_by=authored_by)

② twoder/webui.py /api/submit
   body に在れば渡す。無ければ渡さない（＝現行動作）。
   例: SUB.submit(b.get("raw",""), **{k: b[k] for k in ("origin","relayed_by","authored_by") if k in b})
```
- **★推測しない。** **body に無ければ何も渡さない。** **「Claude が投入したから `HUMAN_RELAYED` だろう」と自動判定しない。**
- **★`TRACE` に `origin` を出すかは変えない**（既に `DS_INPUT_REF` で辿れる。**表示を増やさない**）。

## 3. やってはいけないこと（MGR §3-2・強い順）
1. **★過去レコードを遡って埋めない**（DS の「前向きのみ」を破らない）。
2. **★`origin` を推測して埋めない。** 申告が無ければ `MACHINE_SUBMIT` のまま。
3. **★新しい `origin` の値を作らない**（5種で足りる）。
4. **★受入のために本番台帳へ投入しない。** **`submit()` の `ledger_path` と、DS の一時領域を使うこと**（**`DS_DATA_DIR` を一時ディレクトリへ隔離する。Build 15 で IMPL がやった形**）。
5. **他を直さない**（`ids.resolve` の RRI 経由化は別件）。
6. **`CC_REGISTER.jsonl` に試験行を書かない。**

## 4. 受入（すべて一時台帳で・実行して貼る）
| # | 場合 | 期待 |
|---|---|---|
| **(a)** | 引数を渡さない | **`origin=MACHINE_SUBMIT`**（★既存が壊れていない証拠） |
| **(b)** | `HUMAN_RELAYED` ＋ `relayed_by=Claude` ＋ `authored_by=Taka` | **そのまま記録される**（3項目を貼る） |
| **(c)** | `HUMAN_RELAYED` だけ | **★`ValueError`**（§1・**私は読んだだけ。IMPL は実行して確かめる**） |
| **(d)** | `origin` に5種以外の値 | **`ValueError`**（DS の既存検査） |
| **(e)** | **★`HUMAN_RELAYED` の場合と `MACHINE_SUBMIT` の場合で `submit()` の返り値を比べる** | **`TRACE` / 分類結果 / `task_id` が★同一であること。** **「変わらない」を主張でなく実測で出す**（MGR 訂正 (2)・★本 build で最も重要） |

**そのほか:**
5. **非回帰**: `submit` を通る既存試験（`twoder/regression/test_submit_e2e.py` ほか、`grep -l "SUB.submit\|submit(" twoder/regression/` で特定してから）。**実行して貼る。**
6. **★front door（`GET /api/resolve?id=UTT-…`）で、記録された `origin` が読めることを確かめる。** **一時台帳の記録は front door から読めない可能性がある。** **読めなければ「読めない」と書く**（本番へ投入して確かめない）。
7. **触ったファイルが2本だけであること**（`git status --porcelain`）。
8. **commit しない。** 冒頭に「運用方針 確認済（版: …）」＝**`§12` で日付が最も新しい行を読んでから書く**。定型見出し＋2軸の結果欄。

## 4-1. ★位置づけ（緩めない・MGR 訂正 (3)）
- **★「依頼主の言葉が系に効くようになった」と書かない。**
- **書けるのは「依頼主が書いたと記録できるようになった」だけである。**
- **★BUILT に RRI 全体の話を書かない**（Taka 明示: Build 22 の修理と RRI の実態調査を混同しない）。

## 5. 予想（実測前に固定・★(c) は予想に入れない）
| 項目 | DESIGN の予想 |
|---|---|
| (a) 既存が壊れていないか | **壊れていない** |
| (b) 3項目がそのまま残るか | **残る** |
| 非回帰 | **PASS** |
| **(e) 返り値の同一性** | **★同一である**（`origin` は DS の記録にのみ効き、`submit()` の分類も `task_id`(=`sha1(raw_input)`)も参照しないと読んだ） |
| **受入6（front door から一時台帳の `origin` が読めるか）** | **★読めない方に賭ける**（`/api/resolve` は既定の台帳を見るはずで、一時 `DS_DATA_DIR` を見ないと読んだ）**【未確認・誰が=IMPL / いつ=本 build】** |

---
*BUILD SPEC **v1.1**（★実装源・MGR の3点訂正を反映）。★訂正(1) 目的は「記録を正直にする修理であり系の判断は1つも変わらない。『全案件を台帳経由で管理する』の**必要条件であって十分条件ではない**」——初版は「前提条件である」とだけ書いており言い過ぎだった。★訂正(2) 受入に (e) を追加=**`HUMAN_RELAYED` と `MACHINE_SUBMIT` で `submit()` の返り値(`TRACE`/分類結果/`task_id`)が同一であることを実測**（Taka が問うているのは「何が変わって何が変わらないか」であり、**変わらないことの実測が答えの半分**。本 build で最も重要）。★訂正(3) 位置づけ=「依頼主の言葉が系に効くようになった」と書かず「依頼主が書いたと記録できるようになった」だけを書く／BUILT に RRI 全体の話を混ぜない(Taka 明示)。以下、初版の内容: Build 22=`origin`/`relayed_by`/`authored_by` を front door に通す修理（新しい台帳・記録種別・語彙を作らず、既定は現行のままなので既存呼び出しは変わらない）。目的は依頼主の言葉を「依頼主が書いた」として残せるようにすることで、「全案件を台帳経由で管理する」の前提条件。★MGR の予想「(c) は素通りする」を実行前に訂正——`ds/ds/phase0.py:116` が `origin=="HUMAN_RELAYED" and not (relayed_by and authored_by)` で `ValueError` を投げており**強制している**。読めば分かる事実なので予想欄に入れない（規律: 予想を固定する前に決定論で確定できることを確定する）が、IMPL は実行して確かめ、私の読みが誤っていればそう書く。∴ `submit()` は素通しするだけでよく検証を自分で書かない。変更は `submit.py`(3引数を通す)と `webui.py`(body に在れば渡す・無ければ渡さない)の2本。禁止=過去を遡らない/推測で埋めない/新しい値を作らない/★受入で本番台帳へ投入せず `DS_DATA_DIR` を隔離する/他を直さない。受入=(a)既定で MACHINE_SUBMIT (b)3項目がそのまま (c)★ValueError (d)5種以外は ValueError ＋非回帰＋★front door から `origin` が読めるかの確認（読めなければ「読めない」と書き本番投入しない）。予想は (a)(b)非回帰＋★受入6は「読めない方に賭ける」で、(c) は予想に入れない。*
