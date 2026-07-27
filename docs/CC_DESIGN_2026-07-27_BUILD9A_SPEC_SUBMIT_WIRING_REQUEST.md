# BUILD SPEC — Build 9A: **「配線せよ」を front door に投入し、経路が何を出すかを観測する**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.5）**
- 権限: `CC_MGR_2026-07-27_BUILD9_C_APPROVED.md`（裁定 (c) ＋追加条件）
- 経緯: `CC_DESIGN_2026-07-27_BUILD9_SENDBACK_REPLY_TARGET_CHANGES.md`（`BUILD_ROLE: 参照`）
- **`CC_DESIGN_2026-07-27_BUILD9_SPEC_LEDGER_QUERY.md` は SUPERSEDED。そこから作らないこと。**

---

## 0. ★これは何か。何ではないか
| | |
|---|---|
| **これは** | **依頼を front door に投入し、planner/worker が何を出すかを観測する build** |
| **これではない** | **配線を実装する build ではない。** 配線本体の SPEC（v2.0）は、本 build の結論が出た後に私が書く |
| **発火対象** | 我々（Claude 群）の作業指示1件 |
| **到達するか** | **【監査:IMPL】来る。** Build 8 で `python3 -m twoder.submit "<入力>"` が exit=0・台帳 1179→1180 を実測。**私自身は動かしていない**（v1.5） |
| **境界への寄与**（v1.4 §1） | **寄与する。** 「Claude が外から依頼し、2DER が作る」が成立するかを実物で測る。**Taka の言う「外注で生成、配置するまで」の実装可否そのもの** |

## 0-1. 精度の改善ではない。**成否も本 build の目的ではない**
**目的は「経路が何を出すか」を知ることである。** **不十分な結果も結果である。** **「2DER が良くなった／作れた」と書かない。**

---

## 1. 投入する依頼文（**DESIGN が確定。IMPL は1文字も変えない**）

```
宛: 設計/監査(CC-α)
既存の twoder/ids.py の resolve(rid) を、front door から呼べる acquisition method として配線してほしい。
新しい resolver は作らないこと。ids.resolve をそのまま使う。

やること:
1. submit.py の routing に分岐を1つ足す。request_type が OBSERVE_CURRENT_STATE で、かつ入力に台帳ID
   (DE-0001 のような接頭辞+数字) が含まれる場合、SELECTED_ACQUISITION_METHOD を LEDGER_QUERY にする。
   それ以外の OBSERVE_CURRENT_STATE は今までどおり RUNTIME_INSPECTION のままにする。
2. LEDGER_QUERY では、入力に含まれる各IDについて ids.resolve を呼び、結果を TRACE に入れる。
3. 返る状態を3つに分ける。記録が見つかった=ANSWERED、探したが無い=NOT_FOUND、
   その接頭辞に対応する持ち主が ids.py に無い=NOT_ANSWERABLE。
   NOT_ANSWERABLE を NOT_FOUND にしないこと。前者は機能が無い、後者はデータが無いで、別物である。
4. 該当しない時に別の観測へ切り替えないこと。何も返せないなら NOT_ANSWERABLE を返す。

条件: read-only。台帳に書かない。LLM を使わない。既存のテストを壊さない。
```

- **★通りやすくするための書き換えをしない。** 書き換えたら「経路が我々の依頼を扱えるか」の観測にならない。
- **投入は `python3 -m twoder.submit "<上記>"`**（`python3 twoder/submit.py` は起動しない。Build 8 で実証済）。
- **1回だけ投入する。** 繰り返さない（台帳を汚さない）。

---

## 2. ★予想を先に書く（実測前に固定・後から変えない）

| 項目 | DESIGN の予想 |
|---|---|
| `RRI_REQUEST_TYPE.request_type` | **`MODIFY_EXISTING`**（既存ファイルの改修依頼として読まれると見る。**`BUILD_CAPABILITY` になる可能性も同程度あると思うが、当てに行かず `MODIFY_EXISTING` に固定する**） |
| `RRI_PREFLIGHT.triggered` | **False**（指示語なし・`twoder/ids.py` と `submit.py` は実在） |
| `INTENT_STRATEGY.strategy` | **`DIRECT`** |
| `DW_TASK_ID` | **★返る**（`submit.py:391` で `BUILD_CAPABILITY`/`MODIFY_EXISTING` → `DW_IMPLEMENTATION`） |
| planner が PLAN に到達するか | **到達する** |
| worker が何らかのコードを出すか | **出す** |
| **`twoder/submit.py` に実際に配線が入るか** | **★入らない（F1/F2）。** 生成物は一時 workspace に留まると予想する |

**★予想が外れることは失敗ではない。外れたら「外れた」と書く。**
**特に最後の1行が外れて実際に配線が入った場合、それは本日最大の成果になる。** **その場合も IMPL は判定せず、事実だけ書く。**

---

## 3. ★★失敗したときの書き分け（MGR 追加条件・本 build の核）

**止まった場合、次のどれかを名指しで書くこと。混ぜない。**

| 区分 | 意味 | 次の欠落はどこか |
|---|---|---|
| **(1) 作れなかった** | planner/worker がコードを出せなかった／出したものが依頼と無関係 | **生成の限界。** planner/worker 側 |
| **(2) 作れたが置けなかった** | コードは出たが `twoder/` に配置されず、一時 workspace に留まった | **★配置の限界。** **Taka が Claude に残した役割「外注で生成、配置するまで」の配置が未実装ということになる。次の欠落はそこ** |
| **(3) 置けたが動かなかった** | 配置されたが既存テストが落ちる／`submit()` が壊れる | 品質の限界 |
| **(4) 通った** | 配線が入り、既存テストも通った | — |

**★(1) と (2) を混ぜて「失敗した」と書かないこと。** **別の欠落であり、次にやることが変わる。**

---

## 4. ★やってはいけないこと（順序を守る・MGR §4）
1. **手で配線を書かない。** **worker が出せなかった部分を IMPL が補完しない。** **補完したら経路の実証にならない。**
2. **手で配置しない。** 生成物が一時 workspace に留まったなら、**そのまま留めて報告する。**
3. **依頼文を書き換えて再投入しない。** 1回で終える。
4. **`twoder/operator.py` を改名しない。**
5. **`ids.resolve()` の正しさを台帳と照合しない**（照合は直読になる。**正しさの検定は設計/監査**）。
6. **本番コードを IMPL が直接変更しない。** 変更が要ると判断したら**止めて設計へ上げる。**

---

## 5. 受入
1. **投入した依頼文（逐語）と、返ってきた `TRACE` を全文記録する。**
2. **§2 の予想と実際を並べた表を出す。外れた項目に「外れた」と書く。**
3. **`RRI_REQUEST_TYPE` / `RRI_PREFLIGHT` / `INTENT_STRATEGY` / `SELECTED_ACQUISITION_METHOD` / `DISPATCH_RESULT` / `DW_TASK_ID` を全部書く。**
4. **`DW_TASK_ID` が返ったら、その task がどこまで進んだかを観測して書く**（PLAN 到達／worker 実行／生成物の場所）。**進めるために手を貸さない。**
5. **★§3 の区分を1つ名指しで書く。**
6. **生成物が在るなら、その置かれた実際のパスを書く。** **中身の良し悪しは判定しない。**
7. **`origin=MACHINE_SUBMIT` が記録されていること。**
8. **非回帰**: 本 build で本番コードが変わっていないなら不要。**変わった場合は `test_submit_e2e` / `test_preflight_gate` / `test_return_loop` / `test_dispatch_provenance` を実行して結果を貼る。**
9. **★運用方針 v1.5**: **「動く」と書くときは実行した再現コマンドと結果を併記する。読んだだけなら「読んだ」と書く。**
10. **1回しか投入していないことを明記する**（§4-13）。**1回の結果で経路の可否を断定しない。**
11. **観測を書き、判定・評価・提案をしない。** **判定は設計/監査。**
12. **commit しない**（MGR）。
13. **BUILT 冒頭に「運用方針 確認済（版: v1.5）」と受領文書一覧。**
14. **★front door を経て設計/監査に「届いた」のか、投入後に自分で `TRACE` を読みに行っただけなのかを1行で書く**（Build 8 で欠落した項目。**今回は必ず書く**）。

---

## 6. 位置づけ（緩めない）
- **配線が入っても「境界ができた」と言わない。** Claude と 2DER は同一 OS ユーザで動いており、**権限では区別できない**（D-15 §4）。
- **本 build が示せるのは「依頼が経路に入り、経路がどこまで行ったか」だけである。**
- **本当の受入（1問について我々が【直読】しなくなる）は、本 build では判定できない。**

---
*BUILD SPEC v1.0（★実装源）。Build 9A=「既存の `twoder/ids.py::resolve` を front door から呼べる acquisition method として配線せよ」を front door に1回だけ投入し、planner/worker が何を出すかを観測する。**配線を実装する build ではない**（本体 SPEC v2.0 は結論後に DESIGN が書く）。依頼文は DESIGN が確定し1文字も変えない・通りやすくする書き換えをしない・投入は `-m twoder.submit`。★予想を実測前に固定（MODIFY_EXISTING / preflight 不発火 / DIRECT / DW_TASK_ID は返る / planner は PLAN 到達 / **`submit.py` に実際の配線は入らない**）——最後が外れて配線が入ったら本日最大の成果だが、その場合も IMPL は判定せず事実だけ書く。★核=止まった時に「作れなかった」「作れたが置けなかった」「置けたが動かなかった」「通った」を名指しで書き分ける。特に「置けなかった」なら Taka が残した役割の**配置**が未実装ということであり次の欠落はそこ。★手で配線を書かない・手で配置しない・再投入しない・IMPL は ids.resolve の正しさを台帳と照合しない（照合は直読）。受入14=「届いたのか自分で読みに行っただけか」を1行で書く（Build 8 で欠落）。配線が入っても境界ができたとは言わない（同一 OS ユーザ・権限で区別不可）。*
