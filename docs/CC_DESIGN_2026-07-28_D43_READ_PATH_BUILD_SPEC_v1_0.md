# BUILD SPEC — prefix 是正 ＋ Event Trace 読み出し口 v1.0（★実装源）

- `BUILD_ROLE: ★実装源`（**本文書が実装の唯一の典拠**）
- **★宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-28
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **裁定**: `CC_MGR_2026-07-28_D43_PREFIX_RULING.md` / `CC_MGR_2026-07-28_D42_RULINGS_ABC_AFTER_AUDIT.md`
- **前提の発見**: `CC_DESIGN_2026-07-28_D43_READ_PATH_SPEC_AND_PREFIX_COLLISION.md`（**本文書が優先する**）

---

## 0. ★この build は「読み出し口を作る」だけではない
> **MGR 裁定: 「prefix を直さずに読み出し口だけ作らない」。** **1つの build である。**
> **★理由: いま 2DER は、実在する id を「穴だ」と報告している**（`ids.py` の原則を裏切っている）。**読み出し口を先に作っても、衝突した id では引けない。**

---

## 1. ★衝突は1件ではなく2件だった（全走査の結果）
```
再現: 発行されている prefix の全集合を4系統から収集
      (new_prefix= / PREFIX 表 / ids.py の分岐 / KNOWN_ID_PREFIXES)
→ 56件: ADM AMEND APPROVAL ART ARUN AWW BENCH C CAND CAP CC CCI CDEC CDEF CFR CHG CTX DE DEV
        ECON EEV EFRAG EV FCLS HESC IFACE INTV ITEM KGAP LEG NOBS OB OBS PHASE PTASK REL RINT
        RIREQ ROADMAP RREQ RSIG RUN SCON SIG SLICE SNAP SPLAN SPOL SRC TASK TEV TF TH THREAD TRACE UTT
```
| prefix | 所有者 | 根拠 |
|---|---|---|
| **`RUN-`** | **EGL** | `egl/egl/core.py:289` `new_prefix="RUN"` |
| **`EV-`** | **★EGL（2件目の衝突。前回の草案では見落としていた）** | `egl/egl/core.py:105` `evid = f"EV-{hw.get('EV',0)+1:05d}"` |
| **`ETR-`** | **★誰も使っていない** | 56件の集合に無い |

> **★前回の草案は `EV-` を「空いている」と書いた。** **2つの表しか見ていなかったためである。**
> **★MGR が「全走査してから選べ」を条件にしたから見つかった。** **条件が機能した。**

## 2. ★採る形（新 prefix は★1つだけ）
```
run   : ETR-<12hex>                 例 ETR-ee28ab4e9438
event : ETR-<12hex>-<4桁連番>        例 ETR-ee28ab4e9438-0001
```
| | |
|---|---|
| **なぜ1つか** | **★登記する prefix が1つで済む。** 衝突の面積を最小にする。**2つ足せば2倍の確認が要る** |
| **解決の分け方** | **★`rid.count("-")` で決定論的に分岐する。** 2つなら event、1つなら run。**推測を挟まない** |
| **`event_id` の中身** | **順序が id に入る**（従来どおり連番）。**★親子は `parent_event_id` が持つ。id から親を導かない** |

---

## 3. 実装

### 3-1. `ds/ds/etrace.py`（**発行側の変更は prefix のみ**）
```
open_run : "RUN-" + sha1(...)[:12]        →  "ETR-" + sha1(...)[:12]     ★ここだけ
emit     : "EV-" + rid[4:] + "-%04d"      →  rid + "-%04d"                ★run_id をそのまま前置
```
- **★`sha1` の入力を変えない。** **`uuid4` を使う点も変えない。** **同一文面の2回目を区別できることは `G-31` の要求である。**
- **★`emit` / `span` / 親子の決め方を1行も変えない。**

### 3-2. `ds/ds/etrace.py` に足す2関数（**読み取り専用**）
```python
def resolve_run(rid)    -> {"run_id": rid, "events":[…順序どおり…], "count": N,
                            "truncated": bool, "total": M} | None
def resolve_event(eid)  -> event dict | None
```
- **★書き込みを一切しない。** ファイルを `"r"` でしか開かない。
- **上限 500 件**。超えたら先頭500件 + `"truncated": true` + `"total"`。
- **★該当が無ければ `None`**（空 dict を返さない。`ids.resolve` が「穴」と正しく言えるように）。

### 3-3. `twoder/ids.py`（**新しい口を作らない**）
```python
if rid.startswith("ETR-"):
    from ds import etrace
    return etrace.resolve_event(rid) if rid.count("-") >= 2 else etrace.resolve_run(rid)
```
- **`twoder → ds` は既存の辺**（8箇所）。**新しい依存を作らない。**
- **★endpoint を1つも足さない**（`/api/resolve` が `ids.resolve` を呼ぶ既存経路）。

### 3-4. ★所有表への登記（MGR 条件1）
**`twoder/ids.py` の docstring 先頭の Prefix ownership 表に、次の1行を足すこと:**
```
  ETR-                Event Trace (ds.etrace)   ← run は ETR-<hex>、event は ETR-<hex>-<seq>
```
> **★これを省いたら不合格である。** **登記しなければ、次の誰かが同じ衝突を作る。** **本日それを我々がやった。**

### 3-5. ★既存2件の扱い（MGR 条件3・黙って処理しない）
- **`event_trace.jsonl` に既に書かれた `RUN-…` / `EV-…` の行を★1行も消さない・書き換えない。**
- **代わりに、本 build の報告に次を明記すること:**
```
本日 13:5x の2 run（RUN-ee28ab4e9438 ほか）は★旧 prefix である。
新 prefix 移行前の記録であり、ETR- では引けない。★意図的に残した。
```
- **★理由: 追記式台帳を遡って書き換えないため**（DS の原則「前向きのみ。過去レコードは遡って埋めない」）。

### 3-6. ★変えないもの（MGR 条件4 ほか）
- **EGL 側を1行も変えない。** **`RUN-` / `EV-` は EGL のままである。**
- `ids.py` の既存分岐を1つも変えない（**追加のみ**）。
- `webui.py` を変えない。
- 合流点の `emit` 呼び出し箇所（submit / phase0 / intent_record / de_admission / workcell）を**1行も変えない**。
- **第二段階を先取りしない。** **進行経路の run（裁定 B）は★本 build に含めない。**
- **`_emit_pending` への emit を足さない**（裁定 B の後）。
- **到達しない3件（`G-45`）を塞がない。**

---

## 4. 受入
| # | 条件 | 示し方 |
|---|---|---|
| **1** | `GET /api/resolve?id=ETR-…` が run の event 列を返す | **★実データを貼る**（1件でも投入して新 prefix の run を作る必要が在る。**★投入は1回だけ**） |
| **2** | `GET /api/resolve?id=ETR-…-0001` が単一 event を返す | 実データ |
| **3** | **★親子が本番で付いているか**（D-42 で未確認のまま） | **返った列の `parent_event_id` を root から辿り、1本に繋がることを示す。★繋がらなければ「繋がらない」と書く。繋げようとしない** |
| **4** | **既存の id 解決が壊れていない** | **★`RUN-`(EGL) / `EV-`(EGL) / `UTT-` / `TASK-` / `DE-` を各1件引き、実装前後で同一を示す。** **特に `RUN-` と `EV-` は今回の当事者である** |
| **5** | **所有表に登記した** | `ids.py` docstring の差分を貼る |
| **6** | `LEDGER_REGISTRY` の `ORPHAN` 判定が変わる | **★機械の判定で示す**（`python3 structure/s10_ledger_registry.py --check`）。**変わらなければ「変わらなかった」と書く** |
| **7** | 非回帰が基準から増えていない | **基準 = 91 passed / 7 failed（D-42 実測）。★顔ぶれの diff も示す** |
| **8** | **旧2件を残したことの明記** | §3-5 の文言 |

### 4-1. ★投入について
- **投入は1回だけ**（新 prefix の run を1つ作るため）。**文面は問わない**（前回のような routing の予想を立てない。**★今回は routing に依存する受入項目が無い**）。
- **★webui を再起動してから投入すること**（本日2回踏んだ型）。

## 5. ★止まってよい場所（報告して止まる。自分で決めない）
| # | 条件 |
|---|---|
| 1 | **`ETR-` が実は使われていた**（私の全走査が漏れていた）→ **★私の誤り。報告してほしい** |
| 2 | **`ids.resolve` に分岐を足すと既存の id 解決が変わった** |
| 3 | **親子が繋がらなかった** → **★繋げる修正をしない。** 事実を報告する（それは次の段の材料である） |
| 4 | SPEC が2通りに読める |

---

## 6. ★未確認（引き継ぐ）
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`event_trace.jsonl` の中身を、設計も実装も1行も見ていない** | **本 build で初めて見える。★見えた結果が予想と違っても、それが結果である** |
| 2 | **EGL の `EV-` が `ids.resolve` で解決できないこと**（`ids.py` に `EV` の分岐が無い）— **EGL 側の別の穴かもしれない** | **CC-α / 本 build の後に調べる。★本 build では触らない** |
| 3 | 進行経路の run（裁定 B）／`_emit_pending`（裁定 C 順序3） | 次段 |

---
*CC-α D-43 BUILD SPEC v1.0（実装源・宛 IMPL）。★この build は prefix 是正と読み出し口の1つ（MGR 裁定「prefix を直さずに読み出し口だけ作らない」。実在する id を「穴だ」と報告している状態を先に消す）。★全走査の結果、衝突は1件でなく**2件**だった=`RUN-` は `egl/core.py:289` の `new_prefix="RUN"`、**`EV-` は `egl/core.py:105` の `evid = f"EV-{hw.get('EV',0)+1:05d}"`**——前回の草案は2つの表しか見ずに `EV-` を「空いている」と書いており、**MGR が「全走査してから選べ」を条件にしたから見つかった**。発行済 prefix の全集合56件に `ETR-` は無い。★採る形は新 prefix **1つだけ**=run が `ETR-<12hex>`、event が `ETR-<12hex>-<4桁連番>` で、登記する prefix が1つで済み衝突の面積が最小になる。解決は `rid.count("-")` で決定論的に分岐（2つなら event、1つなら run）し推測を挟まない。★実装=発行側の変更は prefix のみ（`sha1` の入力も `uuid4` も変えない——同一文面の2回目を区別できることは `G-31` の要求／`emit`・`span`・親子の決め方を1行も変えない）、`ds/ds/etrace.py` に**読み取り専用**の `resolve_run`/`resolve_event` を足す（ファイルを `"r"` でしか開かず、上限500件で超えたら `truncated`/`total`、該当無しは空 dict でなく `None` を返して `ids.resolve` が「穴」と正しく言えるように）、`twoder/ids.py` に `ETR-` の1分岐を足す（`twoder→ds` は既存の辺・endpoint を1つも足さない）。★**`ids.py` の docstring の Prefix ownership 表に登記すること——省いたら不合格**（登記しなければ次の誰かが同じ衝突を作る。本日それを我々がやった）。★既存2件は**1行も消さず書き換えず**、報告に「本日の2 run は旧 prefix であり `ETR-` では引けない。意図的に残した」と明記する（追記式台帳を遡らない＝DS の「前向きのみ」原則）。★変えないもの=EGL 側を1行も変えない（`RUN-`/`EV-` は EGL のまま）／`ids.py` の既存分岐は追加のみ／`webui.py` を変えない／合流点の `emit` 呼び出しを1行も変えない／進行経路の run（裁定 B）と `_emit_pending` への emit は本 build に含めない／到達しない3件（`G-45`）を塞がない。★受入8件=`ETR-…` と `ETR-…-0001` が引ける実データ／**親子を root から辿り1本に繋がることを示す。繋がらなければ「繋がらない」と書き繋げようとしない**／**`RUN-`(EGL)・`EV-`(EGL)・`UTT-`・`TASK-`・`DE-` を各1件引いて実装前後で同一**（特に `RUN-`/`EV-` は当事者）／所有表の差分を貼る／`ORPHAN` 判定の変化を機械の判定で示し変わらなければそう書く／非回帰は基準 91/7 と顔ぶれ diff／旧2件を残したことの明記。投入は1回だけで文面は問わず（今回は routing に依存する受入項目が無い）、**webui を再起動してから投入する**（本日2回踏んだ型）。★止まってよい場所=`ETR-` が実は使われていた（CC-α の全走査漏れ＝私の誤りなので報告してほしい）／既存の id 解決が変わった／**親子が繋がらなかった（繋げる修正をせず事実を報告する。それが次段の材料）**／SPEC が2通りに読める。★未確認=`event_trace.jsonl` の中身を設計も実装も1行も見ておらず本 build で初めて見える（見えた結果が予想と違ってもそれが結果）／**EGL の `EV-` は `ids.resolve` に分岐が無く解決できない＝EGL 側の別の穴かもしれないが本 build では触らない**／進行経路の run と `_emit_pending` は次段。*
