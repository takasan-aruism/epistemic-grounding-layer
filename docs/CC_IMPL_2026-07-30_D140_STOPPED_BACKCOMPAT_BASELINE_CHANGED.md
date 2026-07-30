# 【停止・要確認】D-140 — 後方互換 基準値が1件 変わった（`SUBMIT-zOlryQ` が `false → true`）

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-30 23:5x / TYPE=FINDING
- **運用方針 確認済（版: v2.8）** / **実装源**: `CC_DESIGN_2026-07-30_D140_BUILD_SPEC_TRACEKEY_RESOLVE.md`
- **受領した MGR 文書**: **無し**
- **★2DER 優先原則の例外**（正典 §9 で IMPL が書くと明示）。**★この修正を「2DER が担当した工程」に数えない。★1/8 は動かない。**
- **`:8005` は使っていない**

---

# 0. ★聞きたいことは1つ（★YES/NO で答えられる形）
> **`SUBMIT-zOlryQ`（第1試行の入口）が解けるようになったまま、E2E 再投入へ進んでよいか。**

**★私は投入前で止めている。** **★webui は再起動していない＝この変更はまだ本番で動いていない。**

| 読み方 | 出どころ | 結論 |
|---|---|---|
| **止まれ** | SPEC §3-1「★1件でも `resolved` が変わったら後方互換を壊している。そこで止めて報告」＋ §6 | **★1件 変わった → 止まる** |
| **進んでよい** | 正典 §4「過去の第1試行記録を利用できる場合は、`SUBMIT-zOlryQ` でも確認する」／ D-140 §1-1「**★既存の記録だけで決定論的に解けるなら可**」 | ★行を1行も足していない（§4 に証拠）→ 該当する |

**★私は設計判断をしないので、ここで止める。**

---

# 1. ★実装前調査（正典 §2 の6項目・read-only）

| # | 項目 | 現状 | 根拠ファイル・行 | 修正要否 |
|---|---|---|---|---|
| 1 | `trace_key` の発行箇所 | `(tid or "SUBMIT") + "-" + urandom(4) の base64` | `twoder/webui.py:661` | **不要** |
| 2 | `trace_key` が保存されているか | **保存されている**（submit の時点で全 TRACE を書く） | `webui.py:662` → `RUNS/<key>.trace.json`（`RUNS` は `webui.py:25` = `/home/takasan/twoder/runs`） | **不要** |
| 3 | `/api/resolve` が対応する ID 種別（★全件・打ち切り無し） | **14分岐・22 prefix**: `ETR-` / `UTT-` / `DEV-` / `THREAD-` / `OBS`・`SRC`・`ARUN`・`RUN`・`LEG`・`SNAP` / `TASK-` / `ADM-` / `DE-` / `RREQ`・`RINT`・`RSIG` / `AUTHP:`・`AUTHD:` / `ART-` / `CHG-` / `ROADMAP`・`PHASE`・`ITEM`・`AMEND` / `INTV-` — **★`SUBMIT-` は無い** | `twoder/ids.py:31-79` | **★要** |
| 4 | `RUNTIME_INSPECTION` 時の ID の関係 | submit ID=`trace_key`（webui 発行）／input=`DS_INPUT_REF`=`UTT-`／**RRI record ID=★TRACE に無い（判定値のみ）**／`OBS`=`EGL_SOURCE_REFS`／`ARUN`・`SRC`=`OBS` record 経由／response=trace record 自身（応答はここから組まれる） | `submit.py:95,101,113,214,370,375,391` ／ `webui.py:671-687` | **★RRI record ID は今回の対象外（足さない）** |
| 5 | 接続情報を既に保持している正典台帳 | **Event Trace（`ds.etrace`）**。`ETR-` run が `parent_event_id` と**実時刻 `ts`** を持つ（本件は 21 event）。submit trace record が id 群を1箇所に集めている | `ds/ds/etrace.py:41,109-113,160-167` | **★新しい台帳は不要** |
| 6 | **接続が失われる具体的なコード位置（★1箇所）** | **`resolve` に `SUBMIT-` の分岐が無く、`return None` に落ちる** | **`twoder/ids.py:82`**（分岐一覧は 31-79） | **★要** |

**★調査中に見つけた別の欠陥（★今回の対象に足していない）**: 受付時刻として `submit()` に渡る `ts` は既定値 `2026-07-11T08:00:00` に落ちている（`submit.py:93-94`）。**★実時刻は Event Trace 側が持っていた**ので、そちらを使った。**★`ts` の既定化そのものは直していない。**

---

# 2. ★修正（★1件・1ファイル）
```
変更ファイル: twoder/ids.py （★これ1本。★他は1行も変えていない）
変更内容    : ① docstring に SUBMIT- を1行 追加
              ② _resolve_submit_trace() を追加（★既存 record を読むだけ）
              ③ resolve() に `SUBMIT-` の分岐を1つ 追加
```
**★採った方式: (b)「`trace_key` から既存の正典 record ID 群へ決定論的に解決する」。**
**理由（1行）**: **(a) は `trace_key` を台帳へ登録する＝台帳に手を出すことになる。(b) は submit が既に書いている record を読むだけで済み、新しい台帳も新しい API も要らない。**

**★作っていないもの**: 新しい台帳／新しい resolve API／今回専用の GPU 分岐／DW task 生成方式の変更／Planner の新設・強制起動／要約処理。
**★fail-closed（正典 §3 の6条件を、そのまま実装に置いた）**: 実体が無い／入力内容が無い／親子関係が確認できない／受理時刻が確認できない／**request との対応が曖昧**（ENTRY event の `raw_input` と**完全一致**で照合）／参照先が存在しない（`UTT-`・`OBS-` を1件ずつ `resolve` して1つでも欠ければ `None`）→ **いずれかに当たれば `None`。★部分的に解けた形を返さない。**

---

# 3. ★テスト結果（★走らせたものの名前と結果。★総数は書かない）

## 3-1. ★後方互換 基準値8件（T1・★設計が 23:29:54 に取った値と1件ずつ突き合わせ）
| ID | 設計の基準値 | 修正後 | 一致 |
|---|---|---|---|
| `ARUN-00954` | true / キー13 | true / キー13 | ○ |
| `OBS-00955` | true / キー10 | true / キー10 | ○ |
| `DE-0525` | true / キー10 | true / キー10 | ○ |
| `TASK-2DER-B11764B3` | true / キー3 | true / キー3 | ○ |
| `ETR-fdf52322e5bf` | true / キー5 | true / キー5 | ○ |
| `UTT-1010` | true / キー12 | true / キー12 | ○ |
| **`SUBMIT-zOlryQ`** | **false** | **★true / キー14** | **★×（★これが停止理由）** |
| `NO-SUCH-ID-XYZ` | false | false | ○ |

> **★7件は完全に一致している（`resolved` も record のキー数も）。★変わったのは1件だけである。**

## 3-2. ★読み出しだけで走らせたもの
| test | 結果 |
|---|---|
| **T2**（未知の `trace_key` は失敗する） | **○** `SUBMIT-zzzzzz` → `resolved=false` |
| **T8 相当**（同一 ID を2回 解決して一致） | **○** `SUBMIT-zOlryQ` を2回 → **完全一致** |
| **T3〜T6・T7** | **★未実施**（★新しい `trace_key` が要る＝投入が要る。★止めているので走らせていない） |

## 3-3. ★`SUBMIT-zOlryQ` は正典 §1 の必須条件を満たしている（★参考。★採否は設計）
```
受理された入力内容 ○ 「現在のGPU使用状況を取得し、…要約してください。」（★正典の依頼文と一致）
受理時刻           ○ 2026-07-30T22:30:24.892111
                     ★receipt の last_recv_at 22:30:24.891921 と 190µs 差／★私の POST 22:30:24.886058 の直後
RRI 判定           ○ OBSERVE_CURRENT_STATE / acquisition_method=RUNTIME_INSPECTION
runtime inspection ○ status=OBSERVED / host_ref / observations
observation 参照   ○ OBS-00955〜00958（★ARUN-00954〜00957 も record 経由で並ぶ）
最終応答参照       ○ runs/SUBMIT-zOlryQ.trace.json（★応答はここから組まれている）
入力の DS 記録     ○ UTT-1011 ／ Event Trace ETR-2d6b7350abee（21 event）
```

---

# 4. ★「行を足していない」ことの証拠（D-140 §1-1）
```
5 repo の未commit:  ds(なし)  rri(なし)  egl(なし)  dev-workcell(なし)  twoder( M ids.py のみ)
∴ ★台帳へ1行も書いていない。★過去記録に後付けしていない。★既存の record だけで解けた
```

---

# 5. ★私が触った操作の全件
```
★コード変更 1件（twoder/ids.py）  ★commit していない  ★webui を再起動していない（=本番は未反映）
★投入していない（POST /api/submit は0回）  ★run_next を押していない  ★:8005 を使っていない
★GPU を自分で測っていない
★【直読】の試み 1回: `ls twoder/runs/SUBMIT-*.trace.json` がフックに拒否された
   → ★存在確認を諦め、★2DER 自身のコードに読ませる形で実装した（★これが正しい形だった）
```

---

# 6. ★進んでよい場合、私がそのまま実行する手順（★確認だけ欲しい）
```
① webui 再起動（★操作内容/操作者/理由/既存運用か/主体判定への影響 と ★run-gate 初期化を BUILT に全件 書く）
② /api/resolve で基準値8件を★もう一度（★本番の口で T1 を取り直す）
③ 正典から依頼文を機械抽出（★sha1 が 0c458f38… と一致するか確認。違えば止める）
④ POST /api/submit 1回 → ★直後に GET /api/receipt → ★新しい trace_key を resolve（T3〜T6）
⑤ T7（新 trace_key に ARUN-00954〜57 / OBS-00955〜58 が出てこない）・T8（2回 一致）
⑥ 第1試行と同じ口で証拠回収 → 比較表で BUILT
```

---
*IMPL → 設計/監査。**投入前で停止**。D-140 の修正（`twoder/ids.py` 1ファイル・`SUBMIT-` 分岐1つ・既存 record を読むのみ）は実装済みで、**後方互換 基準値8件のうち7件は `resolved` も record キー数も完全一致、`SUBMIT-zOlryQ` の1件だけが `false→true` に変わった**。SPEC §3-1/§6 は「1件でも変わったら止めて報告」、正典 §4 と D-140 §1-1 は「既存の記録だけで決定論的に解けるなら可」で**2通りに読める**ため、**設計の確認を待つ**。**台帳へ1行も書いていない（5 repo の未commit は `twoder/ids.py` のみ）／webui 未再起動＝本番未反映／投入0回／`:8005` 未使用。** 走らせたのは T1（基準値8件の突き合わせ）・T2（`SUBMIT-zzzzzz`→false）・T8 相当（2回一致）で、**T3〜T7 は投入が要るため未実施**。*
