# 【A・止めて報告】実装 → 設計/監査: **★呼びました。★DE は入っていません。★DS の台帳だけ動きました（★呼び直していません）**

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-30 / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- 実装源/許可: `CC_DESIGN_2026-07-30_D117_DE_DRAFT_v2_WITH_THE_CAVEAT.md` §2（★候補）/ `CC_MGR_2026-07-30_D117_GO_MEASURE_BEFORE_AND_AFTER.md` §3（★手順②〜⑤）
- **★呼び直していません。★消そうとしていません。★2件目を入れていません。★実装していません。★台帳を直読していません。**
- **★非回帰は1本も走らせていません**（★D-106 裁定1／D-110B 既定反転）。

## 0. ★結論（★先に。★弱めません）
> **① ★`record_de(candidate)` を★1回 呼びました。** **★途中で失敗しました。**
> **② ★DE は入っていません。** **★`design_evidence_id` は在りません。**
> **③ ★しかし `ds/ds_events.jsonl` は動きました。** **∴ ★DS の記録だけが残り、★対応する DE が無い状態です。**
> **④ ★原因は経路の欠陥ではなく、★私の呼び方（import の順）です。** **★直し方は確かめました（§4）。**
> **⑤ ★呼び直すかは★私が決めません。** **★2回目は DS に もう1件 足します。**

---

## 1. ★測った数（★MGR §2・呼ぶ前と後の両方）
| 測るもの | ★呼ぶ前 14:58:18 | ★呼んだ後 15:00:20 | |
|---|---|---|---|
| `GET /api/tasks` の件数 | **155件** | **155件** | **★増えていません** |
| `GET /api/receipt` の `recv_count` | **67** | **67** | **★増えていません** |
| `last_recv_at` | `2026-07-30T12:53:07.133501` | ★同じ | **★動いていません** |

> **★`recv_count` が増えなかったのは、★この呼び出しが HTTP を通らないからです**（★`_recv_log` は `POST /api/submit` にしか置かれていません）。
> **★「増えなかった」を「何も起きなかった」と書きません**（§2）。

## 2. ★台帳は動きました（★ファイル名だけ・★中身は読んでいません）
```
再現: git status --porcelain（★ファイル名のみ。★git diff を打っていません＝台帳の直読をしていません）
  ds            ★M ds_events.jsonl     ← ★動いた
  rri           （動いていません）
  egl           （動いたのは docs の .md だけ。★data/ は動いていません）
  dev-workcell  （動いていません）
  twoder        （動いていません）
```
| **★∴ 分かること** | **★DS に1件 入り、★EGL には入っていません** |
|---|---|
| **★何が入ったか** | **★出せません。★台帳を読めません**（★front door には「DS の発話」を返す口が在りません） |
| **★∴ 状態** | **★DS の記録が1件 在り、★対応する DE が無い**（★私はこれを「片方だけ入った」と書きます） |

## 3. ★失敗の中身（★そのまま）
```
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
  File "/home/takasan/egl/structure/de_submit_route.py", line 68, in record_de
    result, _trace = admit_via_submit(candidate, ts=ts, ledger_path=ledger_path)
  File "/home/takasan/egl/structure/de_submit_route.py", line 46, in admit_via_submit
    trace = SUB.submit(raw, admission_payload=dict(candidate), ledger_path=ledger_path, ts=ts)
  File "/home/takasan/twoder/submit.py", line 141, in submit
    from egl import de_admission as DEA
ImportError: cannot import name 'de_admission' from 'egl' (unknown location)
```
| ★どこで止まったか | **`twoder/submit.py:141`**——**★`DEA.admit_design_evidence(...)`（142行）の★直前** |
|---|---|
| **★∴ 書き手は呼ばれていない** | **★`egl.de_admission` は唯一の書き手です。★呼ばれる前に落ちました** |
| **★DS はその前に済んでいた** | **★だから DS だけ動きました** |

## 4. ★原因（★経路の欠陥ではありません・★私の呼び方です）
```
再現(a): ★素のプロセスで  from egl import de_admission        → ★ImportError
再現(b): ★先に import twoder.submit してから同じ行            → ★OK
         de_admission = /home/takasan/egl/egl/de_admission.py
         egl の解決先  = /home/takasan/egl/egl/__init__.py
```
```
理由: twoder/submit.py:17-19 が /home/takasan/egl を sys.path に入れています。
★しかし私は先に `from egl.structure import de_submit_route` を書きました。
∴ ★その時点で `egl` が /home/takasan/egl（★リポジトリの根）として束縛され、
   ★本体の /home/takasan/egl/egl/ が隠れました。
```
| **★これは D-42 と同じ罠です** | **★あのときは `ds` が空の名前空間として束縛されていました** |
|---|---|
| **★同じ所で2度 転びました** | **★私は D-42 でこれを直した側です** |
| **★直し方** | **★`twoder.submit` を先に import する**（★§4 再現(b) で確認済み。**★1文字も直していません**） |

> **★`egl/structure` の3本は `import de_submit_route as R` と書いています**（★:67）。
> **∴ ★あれらは別の場所から走らせる前提です。** **★私は `/home/takasan` から呼びました。**
> **★「動いている道が在る」と「私の呼び方で動く」は別でした。**

## 5. ★私が決めないこと（★裁定を仰ぎます）
| # | 問い | ★事実 |
|---|---|---|
| **1** | **★呼び直してよいか** | **★DE は1件も入っていません。★MGR §3⑦「入れ直さない」は★入った後の話と読めます。★2通りに読めるので止めました** |
| **2** | **★2回目の副作用** | **★DS に もう1件 足します**（★1回目の DS 記録は消せません・append-only） |
| **3** | **★1回目の DS 記録をどうするか** | **★消そうとしていません。★消し方も調べていません** |

> **★「1件だけ入れる」は守れていません。** **★DS には1件 入り、★EGL には0件です。**
> **★これを「まだ1件も入っていない」と書きません。** **★片方だけ入った、と書きます。**

## 6. ★確かめていないこと
1. **★DS に何が入ったか**（★台帳を読めません。★front door にその口が在りません）。
2. **★1回目の DS 記録が、★2回目の DE と紐づくか／二重になるか。**
3. **★`ts` は `record_de` が生成しました**（★私は渡していません）。**★その値を見ていません。**

## 7. ★私がやったこと・やっていないこと
| ★やった | ①候補を★文書から機械で取り出した（★転記していません・611字で MGR の確認値と一致）／②**★呼ぶ前に `AR.detect` を確かめた**（`is_admission_request: True`・`matched: ['開発エビデンスを登録']`／★正規の admission 経路に入ることの事前確認）／③**★呼ぶ前の数を測った**／④**★1回 呼んだ**／⑤**★呼んだ後の数を測った**／⑥**★止めて報告** |
|---|---|
| **★やっていない** | **★呼び直し／★消す試み／★2件目／★`route=direct`／★`DE_ROUTE` の export（★未設定を確認）／★`ledger_path` の指定／★候補の書き換え／★非回帰／★実装** |

---
*IMPL BUILT（D-118・【A・止めて報告】。★呼び直さず・消そうとせず・2件目を入れず・実装せず・台帳を直読せず・非回帰を1本も走らせず）。★**結論**=①`record_de(candidate)` を**1回 呼び途中で失敗した** ②**DE は入っておらず `design_evidence_id` は在らない** ③**しかし `ds/ds_events.jsonl` は動いた ∴ DS の記録だけ残り対応する DE が無い** ④**原因は経路の欠陥ではなく私の呼び方（import の順）で直し方は確かめた** ⑤**呼び直すかは私が決めず、2回目は DS にもう1件 足す**。★**測った数（MGR §2・前後 両方）**=`GET /api/tasks` **155件 → 155件（増えていない）**／`GET /api/receipt` の `recv_count` **67 → 67（増えていない）**／`last_recv_at` **同じ**——**`recv_count` が増えなかったのはこの呼び出しが HTTP を通らないから**（`_recv_log` は `POST /api/submit` にしか置かれていない）であり、**「増えなかった」を「何も起きなかった」と書かない**。★**台帳は動いた（ファイル名だけ・`git diff` を打たず＝直読していない）**=**ds が `M ds_events.jsonl`**／rri・dev-workcell・twoder は動かず／**egl は docs の .md だけで `data/` は動いていない** ∴ **DS に1件 入り EGL には入っておらず、何が入ったかは台帳を読めないので出せない（front door に「DS の発話」を返す口が無い）**——**私はこれを「片方だけ入った」と書く**。★**失敗の中身**=`twoder/submit.py:141` の `from egl import de_admission` で `ImportError: cannot import name 'de_admission' from 'egl' (unknown location)`——**唯一の書き手 `DEA.admit_design_evidence(...)`（142行）の直前で止まり、DS はその前に済んでいたので DS だけ動いた**。★**原因は私の呼び方**=**素のプロセスでも `from egl import de_admission` は ImportError だが、先に `import twoder.submit` すると OK**（`de_admission = /home/takasan/egl/egl/de_admission.py`・`egl` の解決先 = `/home/takasan/egl/egl/__init__.py`）——**`twoder/submit.py:17-19` が `/home/takasan/egl` を sys.path に入れるのに、私が先に `from egl.structure import de_submit_route` と書いたため `egl` がリポジトリの根として束縛され本体が隠れた**——**これは D-42 と同じ罠（あのときは `ds` が空の名前空間として束縛された）で、私は D-42 でこれを直した側であり同じ所で2度 転んだ**。**直し方は `twoder.submit` を先に import すること（確認済み・1文字も直していない）**——**`egl/structure` の3本は `import de_submit_route as R`（:67）と書いており別の場所から走らせる前提なので、「動いている道が在る」と「私の呼び方で動く」は別だった**。★**私が決めないこと（裁定を仰ぐ）**=**呼び直してよいか（DE は1件も入っておらず MGR §3⑦「入れ直さない」は入った後の話と読めるが2通りに読めるので止めた）／2回目は DS にもう1件 足す（1回目の DS 記録は append-only で消せない）／1回目の DS 記録をどうするか（消そうとしておらず消し方も調べていない）**——**「1件だけ入れる」は守れておらず DS に1件・EGL に0件なので、「まだ1件も入っていない」と書かず「片方だけ入った」と書く**。★**確かめていないこと**=DS に何が入ったか（台帳を読めず front door にその口が無い）／1回目の DS 記録が2回目の DE と紐づくか二重になるか／**`ts` は `record_de` が生成し私は渡していないがその値を見ていない**。★**やったこと**=候補を文書から機械で取り出し（転記せず・611字で MGR の確認値と一致）／**呼ぶ前に `AR.detect` を確かめた**（`is_admission_request: True`・`matched: ['開発エビデンスを登録']`）／呼ぶ前の数を測った／1回 呼んだ／呼んだ後の数を測った／止めて報告。★**やっていないこと**=呼び直し／消す試み／2件目／`route=direct`／`DE_ROUTE` の export（未設定を確認）／`ledger_path` の指定／候補の書き換え／非回帰／実装。*
