# BUILD SPEC — Build 9B: **sandbox 完結の依頼を投入し、成果物をその場で受け取る（配置はしない）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.5）**
- 権限: `CC_MGR_2026-07-27_RECEIVE_AND_PLACE_APPROVED.md`（Taka「OK進めて」/ 条件1点=受け取りまでを1つの作業に）
- 設計本体: `CC_DESIGN_2026-07-27_RECEIVE_AND_PLACE_PROCEDURE.md`（`BUILD_ROLE: 参照`）
- **`..._BUILD9_SPEC_LEDGER_QUERY.md`（SUPERSEDED）と `..._BUILD9A_SPEC_SUBMIT_WIRING_REQUEST.md`（STOP 中）からは作らないこと。**

---

## 0. ★まず読む（運用方針 §5-4・本日7回「既存を読まずに欠落を語った」）
**着手前に、次を読んだと BUILT に1行書くこと。読まずに始めない。**
- `twoder/ids.py`（88行・既存の resolver。**作らない対象**）
- `twoder/build_planner.py` の `STRUCTURED_KEYS` / `PROD_REPO_ROOTS` / `DESTRUCTIVE_MARKERS`
- `twoder/artifact_registry.py` の docstring（配置の登記規律）

## 0-1. これは何か。何ではないか
| | |
|---|---|
| **これは** | **依頼を front door に投入し、sandbox 成果物を「消える前に」受け取るところまで** |
| **これではない** | **配置しない。登記しない。`submit.py` を触らない。** 配置は本 build の後、**設計/監査の検査を経てから**別 SPEC で行う |
| **発火対象** | 我々（Claude 群）の作業指示1件 |
| **到達するか** | **【監査:IMPL】来る。** Build 8 で `python3 -m twoder.submit "<入力>"` が exit=0・台帳 1179→1180 を実測。**私は動かしていない**（v1.5） |
| **境界への寄与** | **寄与する。** 「Claude が外から依頼し、2DER が sandbox で生成し、Claude が受け取る」——**Taka の「外注で生成、配置するまで」の前半を実物で通す** |

## 0-2. ★なぜ依頼文を変えたのか（通りやすくするためではない）
**旧依頼（Build 9A）は `/home/takasan/twoder` を `target_workspace` にする依頼であり、`build_planner.py:254` の決定論バリデーションが拒否する。**
**投げても経路の可否は測れない。** **∴ 経路の設計に合わせて訂正した。** **緩めたのではない。**

---

## 1. 投入する依頼文（**DESIGN が確定。IMPL は1文字も変えない**）

```
宛: 設計/監査(CC-α)
sandbox 内に、台帳IDの問い合わせを扱う薄いアダプタを1ファイルで作ってほしい。
production repo は触らないこと。配置は依頼者が行う。

仕様:
- 関数 answer(rid, resolve_fn, known_prefixes) を1つ作る。resolve_fn は呼び出し側が渡す。
  ids.py などの外部モジュールを import しないこと。標準ライブラリのみ。
- rid の接頭辞が known_prefixes に含まれない場合 -> {"state": "NOT_ANSWERABLE"} を返す。
- 接頭辞が含まれ、resolve_fn(rid) が None 以外を返した場合 -> {"state": "ANSWERED", "record": その返り値}
- 接頭辞が含まれ、resolve_fn(rid) が None を返した場合 -> {"state": "NOT_FOUND"}
- NOT_ANSWERABLE と NOT_FOUND を同じ値にしないこと。前者は対応する持ち主が無いという意味、
  後者は探したが記録が無いという意味で、別物である。
- 該当しない時に別の結果へ切り替えないこと。
- ネットワークを使わない。ファイルに書かない。
- 3つの状態それぞれについてテストを書き、実行して通すこと。
```

**投入方法（1回だけ）:**
```
cd /home/takasan && python3 -m twoder.submit "<上記の依頼文>"
```
- **`python3 twoder/submit.py` は起動しない**（Build 8 で実証済）。
- **★1回だけ投入する。** 繰り返さない。**再投入するなら「再投入した」と書く**（1回目と2回目は別の観測である）。

---

## 2. ★作業の順序（MGR 条件・受け取りまでを1つの作業にする）

**成果物は `tempfile.mkdtemp(prefix="2der_runner_")` 配下に出る（`generate_via_runner.py:88`・DE-0511）。消えうる。**
**∴ 投入と受け取りを別の作業に分けないこと。**

```
① 投入          python3 -m twoder.submit "<§1 の依頼文>"
② TRACE 記録     返ってきた TRACE を全文控える
③ task 観測      DW_TASK_ID が返ったら、どこまで進んだかを観測する（PLAN 到達 / worker 実行 / judge）
④ ★その場で受け取り  成果物のパスを特定し、直ちに保全する（§2-1）
⑤ 停止          ★ここで止まる。配置しない。BUILT を出す
```

### 2-1. 受け取り（保全）の方法
**保全先は既存の受け渡し場所を使う。新しい置き場を作らない。**
```
dev-workcell/contracts/out/SANDBOX_ARTIFACT-<TASK_ID>/
```
- **【監査:CC-α】`contracts/out` は既存の成果物受け渡し先であり、`.py` は1本も無く import 経路でもない**（`RESULT_PACKET` 等の JSON が実在。`dw/workcell.py:430` が正規の書き先として使う）。**∴ ここへ置いても実行経路に載らない。**
- **保全するもの**: 生成された全ファイル（そのまま）＋ `MANIFEST.json`
- **`MANIFEST.json` に必ず入れる**: 各ファイルの**相対パス / sha256 / バイト数**、**元の sandbox 絶対パス**、`TASK_ID`、`TRACE` の参照、**受け取った時刻**
- **★sha256 を取る理由**: 後で検査・配置するものが、受け取ったものと同一であることを示すため。**パスと散文は信用しない**（`artifact_registry` の docstring と同じ理由）。

### 2-2. 失われていた場合
- **「失われた」と記録する。** **黙って再投入しない。**
- **どこを探したか（パス）と、探した時刻を書く。**
- **これは失敗ではない。** **`tempfile` 配下に出る設計の帰結であり、次に決めるべきことの発見である。**

---

## 3. ★予想を先に書く（実測前に固定・後から変えない）
| 項目 | DESIGN の予想 |
|---|---|
| `RRI_REQUEST_TYPE.request_type` | **`BUILD_CAPABILITY`**（新規1ファイルの作成依頼。**Build 9A では `MODIFY_EXISTING` と予想していたが、依頼文が変わったので変えた。外れを隠すためではない**） |
| `RRI_PREFLIGHT.triggered` | **False** |
| `INTENT_STRATEGY.strategy` | **`DIRECT`** |
| `DW_TASK_ID` | **返る** |
| `build_planner.validate_plan` | **通る**（`target_workspace` が sandbox・`files_expected` 1本・`test_plan` あり） |
| **worker が3状態を正しく分けるか** | **★分けない方に賭ける。** **`NOT_ANSWERABLE` と `NOT_FOUND` を同じ扱いにする**のが最も起きやすい誤りだと考える |
| 成果物の置き場 | `/tmp/2der_runner_*/ws-*/` |
| 成果物が受け取れるか | **受け取れる**（run 直後なら残っていると予想する） |

**★外れたら「外れた」と書く。** **特に「3状態を分けられた」場合、それは予想が外れた側であり、良い結果である。** **その場合も IMPL は判定せず事実だけ書く。**

---

## 4. ★結果の区分（この名前で1つ名指しする・MGR 承認済）
| 名前 | 意味 |
|---|---|
| **`REJECTED_BY_DESIGN`** | planner が production repo 等を理由に拒否。**正しい動作。欠落ではない** |
| **`GENERATION_FAILED`** | PLAN/成果物が出ない、依頼と無関係なものが出た |
| **★`SANDBOX_ARTIFACT_READY`** | **成果物が sandbox に出て、受け取れた。＝設計どおりの正常終了。本 build の成功形** |
| **`ARTIFACT_LOST`** | 成果物は生成されたが、受け取る前に失われた（§2-2） |

**`PLACED_BUT_FAILING` / `PLACED_AND_GREEN` は本 build の範囲外**（配置しないため）。

---

## 5. やってはいけないこと
1. **配置しない。** 成果物を `twoder/` 等の実行経路に置かない。
2. **登記しない**（`artifact_registry.register` / `record_change` を呼ばない）。**登記は配置と同じ作業で行う。配置していないのに登記すると、記録が実体とずれる。**
3. **worker が出せなかった部分を手で補完しない。**
4. **依頼文を書き換えて再投入しない。**
5. **成果物の中身の良し悪しを判定しない。** **検査（C1〜C5）は設計/監査が行う。**
6. **`ids.resolve()` の正しさを台帳と照合しない**（照合は直読になる）。
7. **本番コードを変更しない。** 必要になったら**止めて設計へ上げる。**

---

## 6. 受入
1. **§0 の3点を読んだと1行書く。**
2. **投入した依頼文（逐語）と `TRACE` 全文。**
3. **§3 の予想と実際の表。外れた項目に「外れた」と書く。**
4. **`RRI_REQUEST_TYPE` / `RRI_PREFLIGHT` / `INTENT_STRATEGY` / `SELECTED_ACQUISITION_METHOD` / `DISPATCH_RESULT` / `DW_TASK_ID` を全部書く。**
5. **task がどこまで進んだかの観測**（PLAN 到達 / worker 実行 / test / judge）。**進めるために手を貸さない。**
6. **`build_planner` が拒否した場合、拒否理由（`reasons`）を逐語で書く。**
7. **★受け取りの結果**: 保全先パス、`MANIFEST.json` の内容（各ファイルの sha256 とバイト数）、元の sandbox パス。
8. **★§4 の区分を1つ名指しする。**
9. **`origin=MACHINE_SUBMIT` の確認。**
10. **1回しか投入していないことを明記**（§4-13）。**1回の結果で経路の可否を断定しない。**
11. **本番コードが変わっていないこと**（変わったら非回帰4本を実行して貼る）。
12. **★front door を経て設計/監査に「届いた」のか、投入後に自分で読みに行っただけなのかを1行で書く**（Build 8 で欠落した項目）。
13. **観測を書き、判定・評価・提案をしない。** **判定は設計/監査。**
14. **commit しない**（MGR）。
15. **BUILT 冒頭に「運用方針 確認済（版: v1.5）」と受領文書一覧。**
16. **v1.5**: **「動く」と書くときは実行した再現コマンドと結果を併記する。読んだだけなら「読んだ」と書く。**

---

## 7. この後の流れ（本 SPEC の範囲外・先に示す）
| 段 | 担当 | 内容 |
|---|---|---|
| **本 SPEC** | IMPL | 投入 → 生成観測 → **受け取り** → 停止 |
| 次段 | **設計/監査(CC-α)** | **検査 C1〜C5**（1ファイルか / テストは通ったか / `DESTRUCTIVE_MARKERS` / 台帳書き込みが無いか / 意図とずれていないか） |
| その次 | IMPL | **配置 + C6 非回帰 + `register`/`record_change` で登記** |
| その次 | 設計/監査 | **`verify()` で登記を独立に検証** |
| 最後 | MGR | commit |

## 8. 位置づけ（緩めない）
- **成果物が受け取れても「境界ができた」と言わない。** Claude と 2DER は同一 OS ユーザで、**権限では区別できない**（D-15 §4）。
- **本 build が示せるのは「依頼が経路に入り、sandbox で生成され、消える前に受け取れたか」だけである。**

---
*BUILD SPEC v1.0（★実装源）。Build 9B=sandbox 完結の依頼を front door へ1回投入し、成果物を消える前に受け取るところまで。★配置しない・登記しない（配置は検査後に別 SPEC）。依頼文は `answer(rid, resolve_fn, known_prefixes)` の薄いアダプタ——sandbox は PYTHONPATH が張られず `twoder/ids.py` を import できないので `resolve_fn` を引数で渡す仕様にした＝2本目の読み口を作らない。依頼文を変えた理由は「通りやすくするため」でなく、旧依頼が `build_planner.py:254` で決定論的に拒否されるため経路の設計に合わせた訂正。★順序=投入→TRACE→task 観測→**その場で受け取り**→停止（成果物は `tempfile.mkdtemp` 配下＝消えうる／DE-0511）。保全先は既存の `dev-workcell/contracts/out/`（.py が無く import 経路でないことを確認済）＋ MANIFEST に sha256/バイト数/元 sandbox パスを必ず入れる（パスと散文は信用しない）。失われたら「失われた」と記録し黙って再投入しない。★予想を固定（BUILD_CAPABILITY / validate_plan は通る / DW_TASK_ID 返る / **worker は NOT_ANSWERABLE と NOT_FOUND を同じにすると賭ける** / 受け取れる）——3状態を分けられたら予想が外れた側であり良い結果。★区分= REJECTED_BY_DESIGN / GENERATION_FAILED / SANDBOX_ARTIFACT_READY(成功形) / ARTIFACT_LOST。禁止=配置・登記・手での補完・再投入・中身の判定・台帳照合・本番変更。受入12=「届いたのか自分で読みに行っただけか」を書く。受け取れても境界ができたとは言わない。*
