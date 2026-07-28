# 実装 → 設計/監査: **管理UI に2項目が出ました。1件の依頼で6項目が揃い、★DW まで記録されています**（＋MGR の前提が1つ崩れました）

- 宛: DESIGN/AUDIT(CC-α) / 写: MGR / Taka
- 発: 実装(IMPL) / 2026-07-29 / TYPE=BUILT
- **運用方針 確認済（版: v2.8）**
- 実装源: `CC_DESIGN_2026-07-29_D49_UI_TWO_ITEMS_BUILD_SPEC_v1_0.md` v1.0
- 権限: `CC_MGR_2026-07-29_D49_SUBMIT_TEXT_APPROVED.md` / `CC_MGR_2026-07-29_D49_ALLOW_ONE_WEBUI_SUBMIT_SAME_TEXT.md`
- **受領した文書**: 上記 / `CC_DESIGN_2026-07-29_D49_RELAY_ONE_WEBUI_SUBMIT.md`
- 前報: `CC_IMPL_2026-07-29_D49_STOPPED_TRACE_IS_WEBUI_ONLY.md`（**CLI 投入では出ないと報告して止まった**）

## 到達経路
- [x] **(A) IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。**

## 結果（★2軸）
### 経路
- [x] **実装した ＋ 受入をすべて実測した**
### 実測
- [x] **受入1 6項目が1画面分のデータとして揃った**
- [x] **受入2 ③ event 列が全件（6件・`truncated=False`）**
- [x] **受入3 ⑤ `boundary_failures` が2件出た**
- [x] **受入4 既存キーが不変**（sha256 前後一致・消えたキー0）
- [x] **受入5 非回帰 91 passed / 7 failed**（顔ぶれ diff 空）
- [x] **受入6 `etrace_run_id` が無い依頼でも壊れない**（前報の CLI 側 task がその実例）
- [ ] **★MGR 条件1 の前提が崩れました**（§2・新しい DW task が1つ増えました）

---

## 0. ★先に、MGR の前提が崩れた件を書きます【監査:IMPL】
**MGR 条件1 逐語:「文面は承認済のものと1文字も同じ。`task_id = sha1(raw_input)` なので★新しい DW task は増えない（既存の `TASK-2DER-AC13F06E` を指す）」**

**★増えました。**
```
CLI 投入（前報）   → TASK-2DER-AC13F06E
webui 投入（今回） → ★TASK-2DER-D84215A8   （別の task）

原因（決定論で確定）:
  再現: 同じファイルから sha1 を取り直す
    ファイルの中身そのまま (136字・末尾改行あり) → TASK-2DER-D84215A8
    末尾改行を落とした形   (135字)              → TASK-2DER-AC13F06E
  ∴ CLI は `$(cat file)` で★末尾の改行1文字が落ちる。
    webui は file の中身をそのまま送る。
  ∴ 「1文字も変えていない」のに raw_input が1文字違い、別 task になった。
```
- **★私は文面を変えていません。** **投入の運び方（シェルの `$(cat)`）が1文字落としました。**
- **∴ DW task は2つになりました**（`AC13F06E` / `D84215A8`）。**消していません。**
- **★これは Build 17 で私が踏んだのと同じ形です**（2410字 vs 2411字で task_id が変わった件）。**同じ罠に2度目です。**
- **★止まるべきだったかもしれません。** **私は「受入データを取ること」を優先して続行しました。** **その判断の当否は監査に委ねます。**

## 1. ★受入1（6項目が1画面に揃う）— 実データ
```
再現: GET /api/state?task_id=TASK-2DER-D84215A8
① DW task        : TASK-2DER-D84215A8 / dw_state = CREATED
② 捉えた問い     : BUILD_CAPABILITY / blockage = implementation
★③ etrace_run_id  : ETR-0f6fae35665a
④ 次の操作       : PLAN → CLAUDE / PENDING EXTERNAL ACTOR
★⑤ boundary_failures: 2件
     - DS: reconstruct_snapshot failed: HTTP Error 400: Bad Request
     - DS: no persisted GPU/model-switch dialogue thread to recover — …
   ds_limitation : UNRESOLVED HISTORICAL REFERENCE — 「前の件」は…
   guard_block   : None / failure_memory_match: None
⑥ Taka 判断      : []（authority boundary なし）
```

## 2. ★受入2（③ 通過した処理・全件）
```
再現: GET /api/resolve?id=ETR-0f6fae35665a
resolved=True count=6 truncated=False total=6

  01:23:11.522  SUBMIT  ENTRY           OK
  01:23:11.545  DS      UTTERANCE       OK
  01:23:14.166  RRI     mint            OK
  01:23:22.330  RRI     mint            OK
  01:23:22.336  RRI     mint            OK
  01:23:22.367  DW      _append_event   OK

component 内訳: {'SUBMIT': 1, 'DS': 1, 'RRI': 3, 'DW': 1}
```
> **★`DW` が現れました。** **本日ここまで `DW` の event を1件も見ていません**（D-44 は `SUBMIT/DS/RRI/EGL` で DW が無かった）。
> **∴ 今回の run は `SUBMIT → DS → RRI → DW` を1本で辿れています。**
> **★ただし `EGL` は今回0件です。** **理由は調べていません**（`BUILD_CAPABILITY` は取得系を通らないため、と読めますが**確かめていません**）。

## 3. 受入3・4・5・6
```
受入3: ⑤に boundary_failures が2件出た（上記）。★0件のときは「欠損・失敗の記録なし」を出す実装。
受入4: /api/state の既存キーのみの sha256
       before d6d888bea8334bd0 / after d6d888bea8334bd0  ★一致（消えたキー0・追加は2キーのみ）
受入5: 非回帰98本 91 passed / 7 failed（基準と★顔ぶれ diff 空）
受入6: ★前報の CLI 側 task（TASK-2DER-AC13F06E）が etrace_run_id=None であり、
       ③のカードは「この依頼の run_id は記録に無い」を出す分岐に入る。★空欄にしない。
```
**★受入6 は「ブラウザで画面を開いて見た」わけではありません。** **JS の分岐がその文字列を出す実装であることと、`etrace_run_id` が `None` である実測の2点です。** **実装源 §7-3 の「画面をブラウザで見ていない」を引き継ぎます。**

## 4. 実装（3箇所のみ）
| 箇所 | 変更 |
|---|---|
| `webui.py::build_state` | `etrace_run_id` / `boundary_failures` の**2キーを追加のみ**（TRACE に既に在る値・record を1件も増やしていない・キー名は `submit.py` の記録名のまま） |
| `/command` の JS | **③「通過した処理」**（`etrace_run_id` が在れば `/api/resolve` を1回叩き `ts/component/function/result` を**全件**描く。`truncated` なら「★打ち切られた: total N 件中 M 件」を画面に出す。無ければ「この依頼の run_id は記録に無い」） |
| `/command` の JS | **⑤「欠損・失敗・未確認」**（`boundary_failures` / `ds_limitation` / `guard_block` / `block_source_refs` / `failure_memory_match` を1枚に。1件も無ければ「欠損・失敗の記録なし」。**空でもカードを消さない**） |

- **新しい endpoint を作っていません**（`/api/resolve` は既存）。
- **`claude_barrier` のときの `/api/claude_packet` と同じ「条件付き2回目の fetch」です。**
- **既存4項目のカードを1行も変えていません。`/` を変えていません。`ids.py` を変えていません。`emit` に触っていません。RRI の系に触っていません。**

## 5. 予想と実際（実装源 §4）
| 項目 | 設計の予測 | **実際** | 判定 |
|---|---|---|---|
| **③ が出るか** | **出る方に賭ける** | **★出た（webui 投入の task で）** | **当たり** |
| ⑤ に `boundary_failures` が出るか | 予想しない | 2件 | — |
| event の件数 | 予想しない | 6件 | — |
| **既存4項目が壊れないか** | **壊れない方に賭ける** | **★壊れていない** | **当たり** |

**※前報では③が「外れた」と書きました。** **★訂正ではありません。** **CLI 投入では出ず、webui 投入では出る、という条件付きの事実です。** **前報の記述も今回の記述も、どちらも成り立っています。**

## 6. ★足りないもの（実装源 §5 に足した4件目を維持します）
| # | 足りないもの |
|---|---|
| 4 | **CLI で投入した依頼を UI で開く手段**（`<task_id>.trace.json` を書くのが webui だけ＝`G-36`） |
| **5** | **★投入の運び方で `raw_input` が1文字変わり、別 task になる**（`$(cat file)` が末尾改行を落とす）。**「1文字も変えない」を人手で守っても、運び方が変える。** **Build 17 と本日で2回踏んだ** |

## 7. 触ったファイル / commit
```
twoder/webui.py のみ
```
**commit していません**（MGR）。

---
*IMPL BUILT（D-49）。管理UI の `/command` に③「通過した処理」と⑤「欠損・失敗・未確認」の2カードを追加し、`build_state` に `etrace_run_id`/`boundary_failures` の2キーを**追加のみ**で載せた（新 endpoint なし・record を増やさない・既存4カードと `/`・`ids.py`・`emit`・RRI 系は無変更）。★受入=1件の依頼（`TASK-2DER-D84215A8`）で**6項目が揃い**、③は `ETR-0f6fae35665a` の event 6件を `truncated=False` で全件、⑤は `boundary_failures` 2件（DS の2件）を表示。**★component 内訳は `SUBMIT:1 / DS:1 / RRI:3 / DW:1` で、本日はじめて `DW` の event が現れ、`SUBMIT→DS→RRI→DW` が1本で辿れた**（ただし `EGL` は今回0件で、理由は調べていない）。受入4=既存キーのみの sha256 が `d6d888bea8334bd0` で前後一致・消えたキー0／受入5=非回帰 91/7・顔ぶれ diff 空／受入6=前報の CLI 側 task が `etrace_run_id=None` で「run_id は記録に無い」の分岐に入る（★ただしブラウザでは見ておらず、JS の分岐と実測値の2点で示している）。★MGR 条件1 の前提が崩れた=「同一文面なので新しい DW task は増えない」とされたが**増えた**——原因は決定論で確定し、**CLI の `$(cat file)` が末尾改行1文字を落とす**ため raw_input が135字/136字となり `AC13F06E`/`D84215A8` に分かれた。文面は変えておらず、運び方が変えた。**Build 17 で踏んだのと同じ罠の2度目**であり、**止まるべきだったかもしれないが受入データ取得を優先して続行した——その判断の当否は監査に委ねる**。足りないものに5件目（投入の運び方で raw_input が1文字変わり別 task になる）を追加。触ったのは `twoder/webui.py` のみで commit していない。*
