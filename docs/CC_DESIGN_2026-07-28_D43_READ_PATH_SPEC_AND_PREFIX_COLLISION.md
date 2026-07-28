# 設計/監査 → MGR（写: Taka / IMPL）: **D-43 読み出し口 SPEC — ★その前に。`RUN-` は既に EGL のものだった。私の SPEC が prefix を衝突させた**

- `BUILD_ROLE: 参照`（**SPEC 草案。★まだ実装源にしない — 前提が変わったため MGR の確認が要る**）
- **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-07-28 / TYPE=FINDING + BUILD_SPEC(草案)
- **運用方針 確認済（版: `v2.2` — `§12` で日付が最も新しい行を採って確認）**
- **受領**: `CC_MGR_2026-07-28_D42_BUILT_RECEIVED_PHASE1_NOT_MET.md`（依頼①②③）

## 0. ★MGR の前提を訂正する（依頼①の「実物で確かめること」の結果）
> **MGR:「`/api/resolve` が `RUN-` を解決できるようにするのが最小のはず。実物で確かめること。」**

```
再現: sed -n '1,40p' twoder/ids.py

  Prefix ownership:
    OBS-/SRC-/ARUN-/RUN-/LEG-/SNAP-   EGL (egl.core.get_state)      ← ★RUN- は EGL のもの
  …
  if rid.split("-", 1)[0] in ("OBS", "SRC", "ARUN", "RUN", "LEG", "SNAP"):
      from egl import core
      st = core.get_state(rid)
      return st if st else None

再現: grep -n 'new_prefix="RUN"' egl/egl/core.py
  egl/egl/core.py:289    …, "started_at": now_iso()}, new_prefix="RUN")   ← ★EGL は今も RUN- を発行している
```
> **∴ `RUN-` は空いていない。** **EGL が所有し、今も発行している。**
> **∴ `GET /api/resolve?id=RUN-ee28ab4e9438` が `resolved:false` を返したのは、口が無いからではない。**
> **★EGL に転送され、EGL に無かったからである。** **口は在った。行き先が違った。**

### 0-1. ★これは私の欠陥である（4件目）
**実装源 §2-1 で `run_id = "RUN-" + sha1(...)` と書いたのは私である。**
- **`ids.py` の docstring は先頭14行に prefix 所有表を持っている。** **★私はこのファイルをこのセッションで読んでいる**（「15の prefix 系統」と自分で書いた）。
- **∴ 読んだ表に在るものを、確かめずに再利用した。**

> **★そして最も悪い形で壊れている**: **`ids.py` の運用原則は「an id that does not resolve is a hole, not something to fill from memory」である。**
> **∴ いま 2DER は、★実在する id を「穴だ」と報告している。** **原則そのものを裏切る状態を、私が作った。**
> **∴ `G-44` として登録する。**

---

## 1. ★空いている prefix の実測
```
再現: ids.py が扱う prefix の全列挙
  ADM AMEND ART ARUN CHG DE DEV INTV ITEM LEG OBS PHASE RINT ROADMAP RREQ RSIG RUN SNAP SRC TASK THREAD UTT  (22)
再現: grep -n "KNOWN_ID_PREFIXES" twoder/estimation_basis_binding.py
  ITEM- DE- CHG- ART- BENCH- ECON- AWW- TEV- HESC- TRACE- FCLS- CDEF- IFACE- SIG- AMEND- PHASE- APPROVAL-  (17)
```
| 候補 | 空いているか |
|---|---|
| **`ETR-`**（Event TRace run） | **★両方の表に無い。空いている** |
| **`EV-`**（個別 event） | **★両方の表に無い。空いている** |
| `RUN-` | **★EGL が所有。使えない** |

## 2. ★裁定を仰ぐ（私は決めない）— 既に書かれた記録をどうするか
**`event_trace.jsonl` には既に `RUN-ee28ab4e9438` を含む2 run 分が書かれている**（IMPL 実測）。
| | 案 | 帰結 |
|---|---|---|
| **(a)** | **prefix を `ETR-` に変える。既存2件はそのまま残す** | **★既存2件は解決しないままになる**（`RUN-` のため EGL へ飛ぶ）。**「移行前の2件」として記録に残す。★履歴を書き換えない** |
| (b) | 既存2件の `run_id` を書き換える | **★追記式台帳を遡って書き換える。** DS の原則「前向きのみ。過去レコードは遡って埋めない」に反する。**採るべきでない** |
| (c) | `RUN-` を EGL と共有し、EGL に無ければ etrace を見る | **★2つの店が同じ id に答えうる。** `ids.py` の「id は所有者が1つ」という設計を壊す。**採るべきでない** |

**【設計:CC-α】(a) を推す。** **★ただし私は決めない。** **(b) は履歴の書き換え、(c) は所有権の破壊であり、どちらも私が単独で選んでよい種類ではない。**

---

## 3. 読み出し口 SPEC（草案・裁定後に実装源へ）

### 3-1. ★新しい口を作らない
```
既存の口: GET /api/resolve?id=<any 2DER id>   （webui.py:513 → resolve_view → ids.resolve）
```
**★endpoint を1つも足さない。** **`ids.resolve` に分岐を2つ足すだけ。**

### 3-2. 追加する分岐（`twoder/ids.py`）
```python
if rid.startswith("ETR-"):          # Event Trace: 1 run の event 列
    from ds import etrace
    return etrace.resolve_run(rid)      # -> {"run_id":…, "events":[…], "count":N} / 無ければ None
if rid.startswith("EV-"):           # Event Trace: 単一 event
    from ds import etrace
    return etrace.resolve_event(rid)    # -> event dict / 無ければ None
```
- **`twoder → ds` は既存の辺**（8箇所）。**新しい依存を作らない。**
- **`ids.py` の docstring の prefix 所有表に2行足すこと**（**★表と実装がずれると、次に同じ事故が起きる**）。

### 3-3. `ds/ds/etrace.py` に足す2関数（**読み取り専用**）
```python
def resolve_run(run_id)   -> {"run_id":…, "events":[…順序どおり…], "count":N} | None
def resolve_event(ev_id)  -> event | None
```
- **★書き込みを一切しない。** **既存の `emit` / `open_run` / `span` を1行も変えない。**
- **★件数の上限を持つこと**（既定 500・超えたら `"truncated": true` と `total` を返す）。**台帳が育っても口が詰まらないため。**

### 3-4. ★受入（これで初めて D-42 の②③⑥が満たせる）
| # | 条件 | 示し方 |
|---|---|---|
| 1 | `GET /api/resolve?id=ETR-…` が event 列を返す | **実データを貼る** |
| 2 | **親子が本番で付いているか**（D-42 で未確認のまま） | **★返った列の `parent_event_id` を辿り、root から葉まで1本に繋がることを示す。繋がらなければ「繋がらない」と書く** |
| 3 | `GET /api/resolve?id=EV-…` が単一 event を返す | 実データ |
| 4 | **既存の id 解決が壊れていない** | **★`RUN-`（EGL）・`UTT-`・`TASK-`・`DE-` を各1件引いて、実装前後で同一を示す** |
| 5 | `LEDGER_REGISTRY` の判定が `ORPHAN` から変わる | **★機械の判定で示す**（`s10_ledger_registry --check`） |
| 6 | 非回帰が基準（91 passed / 7 failed）から増えていない | 実測 |

### 3-5. ★やらないこと
1. **新しい endpoint を作らない。**
2. **抜け道4件を「ついでに」塞がない**（MGR 禁止）。
3. **第二段階を先取りしない。**
4. **既存レコードを書き換えない**（§2 の (b) を採らない前提）。
5. **`emit` 側に手を入れない**（読み取りだけを足す）。

---

## 4. 依頼②③の材料（★私は決めない。材料だけ）

### 4-1. 抜け道4件 — **到達可能性を実測した**（D-42 監査より再掲）
| # | 抜け道 | 呼び手 | **本番到達** | **材料としての意味** |
|---|---|---|---|---|
| 1 | `rri/request_thread.py:73` | **0**（監査スクリプトのみ） | **しない** | **`G-33` と同一物。** 塞ぐ対象が動いていない |
| 2 | `egl/core.py:119` | `egl/curator.py`・`egl/pipeline.py` のみ | **しない**（`twoder`/`ds`/`rri`/`dw` はそれらを import しない） | **別系統の EGL パイプライン。** 2DER の依頼経路ではない |
| 3 | `dw/authorization.py:46` | **0** | **しない** | 同上 |
| **4** | **`dw/dispatch.py:162 _emit_pending`** | **`dispatch.py:132`（`dispatch_once` 内）** | **★する** | **★本物。** ただし根は §4-2 |

**★MGR の裁定文は「4件在れば存在する」としている。** **私は基準を書き換えない。**
**★材料として言えるのは「4件のうち3件は、いま呼ばれる経路が無い」までである。** **「だから実質1件」とは書かない。** **判断は MGR。**

### 4-2. `run_id` が付かない4入口（⑨〜⑫）と #4 は★同じ根
```
再現: grep -n "run_next" twoder/webui.py
  webui.py:591-592   if u.path == "/api/run_next":  step = D.dispatch_once(tid, _machine_registry(), TS)
```
> **合流点⓪（run の発行）は「投入」の経路にしか無い。** **「進行」の経路には無い。**
> **∴ `_emit_pending` に emit を足しても、★`run_id` の無い event が増えるだけである。**
> **∴ 「塞ぐ」を選ぶなら、塞ぐべきは4箇所ではなく★「進行経路に run を開くか」の1点である。**

**★これは第二段階の先取りに当たりうる**（実装源 §2-7-2）。**∴ 私は作らない。裁定を仰ぐ**（`G-41`）。

### 4-3. ★材料の限界（先に書く）
1. **#2 は「`twoder` が `egl.pipeline` を import しない」で判断した。** **動的 import は見ていない。**
2. **#4 が実際に何回通っているかは数えていない**（構造として通る、まで）。
3. **⑨〜⑫ の入口③④⑤⑥は実行を見ていない**（`grep` のみ・D-42 から引き継ぎ）。

---

## 5. ★未確認
| # | 未確認 | 誰が・いつ |
|---|---|---|
| 1 | **`ETR-` / `EV-` が「両方の表に無い」ことは2つの表で確かめた。** **prefix を持つ他の表が3つ目に無いかは見ていない** | **CC-α / 実装源に上げる前に全走査する** |
| 2 | `event_trace.jsonl` の中身は私も見ていない（読み出し口が無いため） | CC-α / 本 SPEC 実装後 |
| 3 | 既存2件の `RUN-…` が EGL 側で偶然衝突していないか（同じ文字列の EGL run が在るか） | **CC-α / 実装前に確認する** |

---
*CC-α D-43。★MGR の前提を訂正=「`/api/resolve` が `RUN-` を解決できるようにするのが最小」は成り立たない——`ids.py` の prefix 所有表で **`RUN-` は EGL のもの**であり（`OBS-/SRC-/ARUN-/RUN-/LEG-/SNAP-` → `egl.core.get_state`）、`egl/core.py:289` は今も `new_prefix="RUN"` を発行している ∴ `GET /api/resolve?id=RUN-ee28ab4e9438` が `resolved:false` を返したのは**口が無いからではなく EGL に転送されて EGL に無かったから**で、口は在り行き先が違った。★これは私の欠陥4件目=実装源 §2-1 で `run_id = "RUN-" + sha1(...)` と書いたのは私で、`ids.py` の prefix 所有表は先頭14行に在り**私はこのファイルをこのセッションで読んでいる**（「15の prefix 系統」と自分で書いた）∴ 読んだ表に在るものを確かめずに再利用した。**最も悪い形で壊れており、`ids.py` の運用原則「an id that does not resolve is a hole」に対し、いま 2DER は実在する id を「穴だ」と報告している**——原則そのものを裏切る状態を私が作った（`G-44` 登録）。★空き prefix の実測=`ids.py` は22 prefix、`estimation_basis_binding.KNOWN_ID_PREFIXES` は17 prefix を持ち、**`ETR-` と `EV-` はどちらの表にも無く空いている**。★裁定を仰ぐ=既に2 run 分が `RUN-` で書かれており、(a) prefix を `ETR-` に変え既存2件はそのまま残す（★履歴を書き換えない）／(b) 既存の `run_id` を書き換える（**追記式台帳を遡る＝DS の「前向きのみ」原則に反し採るべきでない**）／(c) `RUN-` を EGL と共有し無ければ etrace を見る（**2つの店が同じ id に答えうる＝所有権の設計を壊す**）——CC-α は (a) を推すが決めない。★読み出し口 SPEC=**新しい endpoint を1つも足さず** `ids.resolve` に `ETR-`/`EV-` の2分岐を足すだけ（`twoder→ds` は既存の辺で新しい依存を作らない）、`ds/ds/etrace.py` に読み取り専用の `resolve_run`/`resolve_event` を足す（**書き込みを一切せず既存の `emit`/`open_run`/`span` を1行も変えない**・件数上限500で超えたら `truncated`/`total` を返す）、**`ids.py` の docstring の prefix 所有表にも2行足す**（表と実装がずれると次に同じ事故が起きる）。受入6件=`ETR-`/`EV-` が引ける実データ／**返った列の `parent_event_id` を辿って root から葉まで1本に繋がることを示す（繋がらなければ繋がらないと書く）＝D-42 で未確認のままの項目**／`RUN-`(EGL)・`UTT-`・`TASK-`・`DE-` を各1件引いて既存の id 解決が実装前後で同一／`LEDGER_REGISTRY` の `ORPHAN` 判定が機械の判定で変わる／非回帰が基準 91/7 から増えていない。★依頼②③の材料=抜け道4件の**到達可能性を実測**し3件は呼び手0または別系統で本番到達しないが、**MGR の基準を書き換えず「4件のうち3件はいま呼ばれる経路が無い」までしか書かない**（判断は MGR）。到達する #4 と `run_id` が付かない⑨〜⑫は**同じ根**で、`webui.py:591-592` の `/api/run_next` が `dispatch_once` を直接呼び合流点ⓠを通らないため、**`_emit_pending` に emit を足しても `run_id` の無い event が増えるだけ** ∴ 塞ぐなら塞ぐべきは4箇所でなく「進行経路に run を開くか」の1点だが、これは第二段階の先取りに当たりうるので作らず裁定を仰ぐ（`G-41`）。材料の限界3件と未確認3件（**`ETR-`/`EV-` の空きは2つの表で見ただけで3つ目の表を見ていない——実装源に上げる前に全走査する**／`event_trace.jsonl` の中身は私も未見／既存2件の `RUN-…` が EGL 側と偶然衝突していないかは実装前に確認する）を明記。*
