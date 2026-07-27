# BUILD SPEC — Build 11: **新しい task を `CREATED` から PLAN まで通す（依頼文は DESIGN が確定）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.7）**
- 権限: `CC_MGR_2026-07-27_10R_RECEIVED_NEXT_IS_PRIORITY1_SUBMIT.md`（裁定 (2)＋条件。**「文面は DESIGN が確定する」**）

---

## 0. ★MGR 案の文面を採らない（理由を先に・裁定 (2) 自体は採る）【設計:CC-α】

**MGR の案**: 「**既存の `twoder/ids.py::resolve` を front door から呼べる acquisition method として配線せよ**」

**この文面は投げるべきでないと考える。3つの理由:**
1. **`build_planner` が決定論で拒否する。** 配線先は `twoder/submit.py` であり、`PROD_REPO_ROOTS`（`build_planner.py:59`）に `/home/takasan/twoder` が含まれ、`:254` で `target_workspace` が production repo なら REJECT される。**Build 9A で確定済み。**
2. **今日確立した役割分担と矛盾する。** **生成＝2DER（sandbox）／配置・配線＝Claude**（MGR `..._STOP_ENDORSED_PLACEMENT_IS_CLAUDES_JOB.md` の裁定）。**配線を 2DER に依頼するのは、その裁定を取り消すことになる。**
3. **★MGR 自身の基準に反する。** MGR §3-1-2 は「捨て駒の依頼を投げると、台帳に意味のない task が残る。本物なら残ってよい」とした。**構造的に達成不可能な goal を持つ task は、捨て駒より悪い。** **永久に完了しない task が台帳に残る。**

**∴ 裁定 (2)（新しい task を `CREATED` から通す）は採る。文面だけ差し替える。**

## 0-1. 代わりに投げるもの — **私自身の仕様の穴を直した、修正版のアダプタ依頼**
**Build 9B で投げた依頼文には、私が後から見つけた穴が2つあった**（`..._BUILD9B_ACCEPTANCE_ORACLE_FIXED.md` §3）:
- **P1**: 「未対応の接頭辞では `resolve_fn` を呼ばない」——**Taka の第一原則そのものなのに、1文字も書いていなかった。**
- **U**: `resolve_fn` が例外を投げた場合の扱いを定義していなかった。

**∴ その2点を明記した版を投げる。**
| | |
|---|---|
| **本物か** | **本物である。** 優先度1（台帳を読む部品）の中核であり、私の記載漏れの修復でもある |
| **sandbox で完結するか** | **する。** `resolve_fn` を引数で受け取る純関数＋テスト。production repo を触らない |
| **task id が変わるか** | **変わる**（`sha1(raw_input)` が別・`submit.py:405`）。∴ 新しい `CREATED` task ができる |
| **失敗しても収穫か** | **なる。** `planner_outcome` に理由が出る（MGR §3-1-3 の意図はそのまま満たす） |

---

## 1. 投入する依頼文（**DESIGN が確定。IMPL は1文字も変えない**）

```
宛: 設計/監査(CC-α)
sandbox 内に、台帳IDの問い合わせを扱う薄いアダプタを1ファイルで作ってほしい。
production repo は触らないこと。配置は依頼者が行う。

仕様:
- 関数 answer(rid, resolve_fn, known_prefixes) を1つ作る。resolve_fn は呼び出し側が渡す。
  外部モジュールを import しないこと。標準ライブラリのみ。
- rid の接頭辞が known_prefixes に含まれない場合 -> {"state": "NOT_ANSWERABLE"} を返す。
  このとき resolve_fn を呼んではならない。存在しないと分かっているものを問い合わせないこと。
- 接頭辞が含まれ、resolve_fn(rid) が None 以外を返した場合 -> {"state": "ANSWERED", "record": その返り値}
- 接頭辞が含まれ、resolve_fn(rid) が None を返した場合 -> {"state": "NOT_FOUND"}
- resolve_fn が例外を投げた場合 -> {"state": "UNKNOWN"} を返す。例外を素通しさせないこと。
  NOT_FOUND にしないこと。探せなかったことと、探して無かったことは別である。
- NOT_ANSWERABLE と NOT_FOUND と UNKNOWN を、それぞれ別の値にすること。
  NOT_ANSWERABLE は対応する持ち主が無い、NOT_FOUND は探して無い、UNKNOWN は探せなかった、である。
- 該当しない時に別の結果へ切り替えないこと。
- ネットワークを使わない。ファイルに書かない。
- 4つの状態それぞれについてテストを書き、実行して通すこと。
```

**投入・進行（この順・各1回）:**
```
POST /api/submit    {"raw": "<上記>"}                → DW_TASK_ID を控える
POST /api/run_next  {"task_id": "<上で返った id>"}   → 1回だけ
```
- **`/api/submit` の直後に `/api/run_next`**（run-gate が立つ順序）。**間に他の submit を挟まない。**
- **`run_until_barrier` を使わない。**
- **token を要求されたら迂回しない。止めて上げる。**

---

## 2. ★PLAN が記録されたら、そこで止まる
- **`derive_state` が `READY_FOR_IMPLEMENTATION` になったら、それ以上 `run_next` を打たない。**
- **worker（`CODING_WORKER`）に進まない。** **成果物の生成は本 build の範囲外である。**

---

## 3. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| `request_type` | **`BUILD_CAPABILITY`** |
| `DW_TASK_ID` | **返る（新しい id。`TASK-2DER-D6A93450` ではない）** |
| run-gate | `runnable: true` |
| **`planner_outcome` キーの有無** | **★在る**（修理が新プロセスに入っているため。**これが修理の実証**） |
| **PLAN の成否** | **★成功する方に賭ける**（`dispatched: true` / `auto_served: QWEN_BUILD_PLANNER`） |
| 成功時の `auto_served` | **`QWEN_BUILD_PLANNER`**（`PT.plannable` は偽のはずなので決定論テンプレではない） |
| 失敗時の `stage` | `validation` |

**賭けの根拠**: **Build 10 で同じ形の依頼が PLAN に到達した**（旧プロセス）。**ただし各1回であり、planner は揺れる**（9C は barrier）。**∴ 弱い賭けである。外れても不思議はない。**
**★成功しても失敗しても、`planner_outcome` キーが在れば修理は実証される。** **そこが本 build の主目的である。**

---

## 4. 受入 — **BUILT の定型見出しにすること（受入項目として書くと6回連続で落ちたため）**

**BUILT に、次の見出しをそのまま置くこと:**

```
## 到達経路
- [ ] (A) 本 BUILT の内容は、IMPL が自分で読んで転記した。設計/監査へ自動で届く経路は通っていない。
- [ ] (B) 〇〇（経路名）を経て設計/監査へ届いた。

## 前回からの持ち越し
- twoder/ledger_query.py の削除: [ ] 実施済 / [ ] 未実施 / [ ] 本 build では触っていない
```

**そのほかに出すもの:**
1. 投入した依頼文（逐語）と `/api/submit` の応答全文。
2. **`/api/run_next` の応答全文（キーを省略しない）。** **★`planner_outcome` キーの有無を明示。**
3. **`planner_outcome` の中身を逐語全文**（`None` なら `None` と書く。`dict` なら `stage`・`reason` を1文字も省略しない）。
4. **`auto_served` の値**（無ければ「無い」）。
5. `derive_state(<新 task>)` と events。
6. §3 の予想と実際の表。**外れに「外れた」と書く。**
7. **プロセスの起動時刻とソース mtime を並べて記載**（実行時の鮮度確認・10R の教訓）。
8. **`TASK-2DER-D6A93450` に一切触っていないこと。**
9. 本番コードを変更していないこと。**各操作1回ずつ。**
10. 観測を書き、判定・評価・提案をしない。**commit しない。** 冒頭に「運用方針 確認済（版: v1.7）」と受領文書一覧。
11. **v1.5**: 「動く」と書くときは実行した再現コマンドと結果を併記する。
12. **トークンを文書・argv・ログに出さない。**

---

## 5. やってはいけないこと
1. **依頼文を通りやすく書き換えない。**
2. **PLAN 記録後に `run_next` を打たない**（worker が動く）。
3. **run-gate / token gate を迂回しない。**
4. **`planner_outcome` を要約・整形・切り詰めしない。**
5. **本番コードを変更しない。**
6. **成功しても「作れるようになった」「良くなった」と書かない。**

---

## 6. 設計/監査の側の記録（IMPL は読まなくてよい）
**受入オラクルを更新した。** **成果物を見る前に、依頼文が変わったことを理由に更新している。緩めていない。**
| | |
|---|---|
| 旧 sha256 | `8d709d18f812b9c63b1df1deba79d57a79b36fe2269b200b8d004f1080bff722` |
| **新 sha256** | **`77af5668b5548f87ffac10c2fb075484ff10824365d33ac89666efff7ad9965e`** |
| 変更 | **P1 を `PRINCIPLE` → `MUST`（M8）に昇格**（依頼文に明記したため）／**M9（例外時 `UNKNOWN`）を追加** |
| 検証 | **旧仕様どおりの参照実装に当てて 12/13**（M9 のみ落ちる＝新要件だけが効いている） |

---
*BUILD SPEC v1.0（★実装源）。Build 11=新しい task を `CREATED` から PLAN まで通す。★MGR 案の文面（ids.resolve を配線せよ）は採らない——`PROD_REPO_ROOTS` により決定論で拒否される(Build 9A 確定)、今日確立した役割分担（生成=2DER sandbox／配置・配線=Claude）と矛盾する、そして構造的に達成不可能な goal の task が永久に台帳に残る（MGR 自身の「本物なら残ってよい」基準に反する）。裁定(2)は採り、文面のみ差し替える。★代わりに投げるのは、私自身が Build 9B で書き落とした2点（P1=未対応接頭辞では resolve_fn を呼ばない＝Taka の第一原則／例外時の扱い）を明記した修正版アダプタ依頼——本物であり sandbox 完結であり task id が変わる。手順=submit 直後に run_next 1回、PLAN が記録されたら止まり worker には進まない。予想=`planner_outcome` キーは在る（修理の実証・本 build の主目的）／PLAN は成功する方に弱く賭ける（Build 10 で到達したが planner は揺れる）。★受入は BUILT の定型見出し方式に変更（受入項目として書いたら「到達経路の二択」が6回・`ledger_query` 削除が4回連続で落ちたため）。オラクルは成果物を見る前に締めた（P1→MUST 昇格・例外時 UNKNOWN 追加／旧 sha 8d709d1… → 新 sha 77af566…／旧仕様の参照実装で 12/13＝新要件だけが効くことを確認）。*
