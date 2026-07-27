# BUILD SPEC — Build 10: **捨てられている planner の失敗理由を出す（修理・追加のみ）**

- **`BUILD_ROLE: ★実装源`**（本 build task の唯一の実装源。**IMPL はこの1本だけから作る**）
- **宛: IMPL（coder）** / 写: MGR / Taka
- 発: 設計/監査(CC-α) / 2026-07-27 / TYPE=BUILD_SPEC / v1.0
- **運用方針 確認済（版: v1.7）**
- 権限: `CC_MGR_2026-07-27_BUILD9C_RULING_SURFACE_THE_REASON.md`（裁定＋条件4点）
- 診断: `CC_DESIGN_2026-07-27_BUILD9C_AUDIT_PLANNER_REASON_DISCARDED.md`

---

## 0. ★これは修理である。新機能ではない（MGR 条件4）
**`build_planner` は失敗理由を必ず作っている。** **それを経路が捨てている。** **捨てるのをやめるだけである。**
- **挙動を変えない。** **fail-closed のまま**（無効な plan は今までどおり通らない）。
- **既存のキー・文字列・状態遷移を変えない。追加のみ。**
- **効果を測らない。** **「2DER が良くなった」と書かない。**

## 0-1. ★これは何に対して発火するのか。その入力は実際にここへ来るのか（運用方針 §5-5）
| | |
|---|---|
| 発火対象 | **PLAN 段で Qwen planner が失敗したとき** |
| 到達するか | **【監査:IMPL】来る。** Build 9C で実際に `CLAUDE_BARRIER` に落ちた（理由が見えないだけ） |
| 境界への寄与 | **寄与する。** **優先度1（台帳を読める仕組みを 2DER に作らせる）の計器である。** 理由が見えない限り、失敗しても原因が分からない |

---

## 1. ★捨てている場所は3つある（1つ直しても届かない）【監査:CC-α】

| # | 場所 | 何を捨てているか |
|---|---|---|
| **S1** | `dev-workcell/dw/dispatch.py:104-107`（PLAN 分岐） | `pres = planner(...)` を `recorded` 偽なら**その場で捨てる**。barrier の戻り値に載らない |
| **S2** | `dev-workcell/dw/dispatch.py:139-142`（`run_until_barrier` の trace） | trace に積むのは `state/operation/actor/dispatched/reason` のみ |
| **S3** | `twoder/webui.py:596-597`（`/api/run_next` の応答） | `{"dispatched","reason","nlo","state"}` だけを返す。**新しいキーを足しても、ここで落ちる** |

**★S1 だけ直しても、我々が使う webui 経路では見えない。** **3つとも直すこと。**

---

## 2. 変更内容（追加のみ）

### 2-1. S1 — `dispatch.py` の PLAN 分岐
```
現在:  planner = actors.get("BUILD_PLANNER")
       if planner is not None:
           pres = planner(task_id, None, nlo) or {}
           if pres.get("recorded"):  return {... "auto_served": "QWEN_BUILD_PLANNER"}
           # ここで pres が消える

方針:  pres を関数スコープの変数に保持し、後段の barrier 戻り値に
       "planner_outcome": <pres をそのまま> として載せる。
       planner が呼ばれなかった場合は None（★キーを常に置く。無いことと失敗を区別するため）。
```
- **`planner_outcome` の中身は raw のまま**（`{"recorded": False, "stage": ..., "reason": [...], ...}`）。**要約しない・整形しない・切り詰めない**（MGR 条件2）。
- **`plan` / `validation` が入っていても、そのまま載せてよい。**
- **★`planner_outcome` が `None` であることと、`{"recorded": False, ...}` であることを、必ず区別できるようにする。** **これが本 build の目的そのものである**（「未登録」と「呼ばれて失敗」を区別する）。

### 2-2. S2 — `run_until_barrier` の trace
trace の各要素に **`planner_outcome`** を足す（`step.get("planner_outcome")`）。

### 2-3. S3 — `webui.py` の `/api/run_next` 応答
返す dict に **`"planner_outcome": step.get("planner_outcome")`** を足す。
- **`/api/run_until_barrier` 側は `out["trace"]` を返しているので、S2 が入れば自動的に届く。** **確認すること。**

### 2-4. ★変えてはいけないもの
- `dispatched` / `reason`（`"CLAUDE_BARRIER"` の文字列）/ `nlo` / `pending_actor` / `auto_served`
- `_emit_pending` の書き込み内容（**台帳のスキーマを変えない**）
- `record_plan` の呼ばれ方、fail-closed の判定条件
- **`runtime_inspection` は触らない**（MGR 条件3・別件）

---

## 3. 非回帰（実行して結果を貼ること）
**`dispatch_once` / `run_until_barrier` に触れるテスト（9本）:**
```
twoder/regression/test_build_planner.py            ← ★本件の直撃。最優先
twoder/regression/test_alpha_beta_integration.py
twoder/regression/test_concurrency_and_run_gate.py
twoder/regression/test_full_live_e2e.py
dev-workcell/test_plan_template.py
dev-workcell/test_dw_workflow_equivalence.py
dev-workcell/test_upper_review_gate.py
dev-workcell/test_auto_disposition.py
```
**＋ 既定の4本:** `test_submit_e2e` / `test_preflight_gate` / `test_return_loop` / `test_dispatch_provenance`

**【監査:CC-α】戻り値の完全一致比較（`step == {...}`／`sorted(step.keys())`）は見つからなかった。** ∴ キー追加で壊れないと**予想する**。**壊れたら止めて設計へ上げること。assert を書き換えない。**

---

## 4. ★受入の本体 — 直した後、もう一度1回だけ動かして理由を見る

**修理を入れたら、Build 9C の段2 をもう一度だけ実行する。**
```
POST /api/run_next   body: {"task_id": "TASK-2DER-D6A93450"}
```
- **同じ task でよい。** **`state` は `CREATED` のままであり、PLAN は記録されていない**（Build 9C 観測）。**∴ 再実行できる。**
- **run-gate のため、直前に webui `/api/submit` へ同じ依頼文を1回投入する必要がある**（`_LAST` を立てるため）。**依頼文は Build 9B/9C と同一。1文字も変えない。**
- **投入は1回・RUN NEXT は1回。** `run_until_barrier` を使わない。

### 4-1. ★出すもの（これが本 build の成果）
> **`planner_outcome` を逐語で全文貼ること。** **`stage` と `reason` を1文字も省略しない。**

- **`reason` が配列なら全要素。** **長くても切らない。**
- **`planner_outcome` が `None` だった場合**: 「**planner は呼ばれていなかった**」ことが初めて確定する。**その場合も、そう書く。** **★私の §2 の推論（呼ばれている）が誤りだったことになる。そう書いてよい。**

---

## 5. 予想を先に書く（実測前に固定）
| 項目 | DESIGN の予想 |
|---|---|
| 非回帰 | **全て PASS**（キー追加のみ） |
| `planner_outcome` が `None` か否か | **★`None` ではない**（＝planner は呼ばれている。Build 9C 監査 §2 の推論） |
| `stage` | **`validation`** に賭ける（Qwen は JSON を出すが、11キーのどれかが要件を満たさないと見る） |
| `reason` の中身 | **`target_workspace` 関連** に賭ける（依頼文に workspace を指定していないため、planner が自分で決める必要がある） |

**★外れたら「外れた」と書く。** **特に `stage` が `build`（JSON が取れない等）だった場合、それは Qwen 側の問題であり、依頼文の問題ではない。区別が付く。**

---

## 6. やってはいけないこと
1. **`reason` を要約・整形・切り詰めしない。**
2. **fail-closed を緩めない。** **理由を出すことと、無効な plan を通すことは別である。**
3. **`runtime_inspection` を直さない**（別件）。
4. **テストの assert を書き換えない。** 壊れたら止めて上げる。
5. **依頼文を変えない。再投入を繰り返さない。**
6. **トークンを文書・argv・ログに出さない。**
7. **commit しない**（MGR）。

---

## 7. 併せて（前回未確認）
1. **`twoder/ledger_query.py` を削除したか。** **Build 9C の BUILT に記載が無い。** **未実施なら実施し、実施済なら「実施済」と書くこと。**（根拠: `.py`/設定からの参照0件・SUPERSEDED・2本目の読み口は境界にとって最悪）
2. **`/tmp/2der_runner_*` の増減**（PLAN が記録された場合のみ意味がある）。

---

## 8. 受入チェック（前回3回連続で欠落した項目は二択にする）
1. §1 の S1/S2/S3 の3箇所すべてを直したか。**直した diff の要点を1行ずつ。**
2. **非回帰 12本の実行結果を貼る。**
3. **★`planner_outcome` の全文（§4-1）。**
4. §5 の予想と実際の表。外れに「外れた」と書く。
5. **★次のどちらかに丸を付ける（3回連続で書かれていない項目）:**
   - [ ] **(A) 投入後、`planner_outcome` を IMPL が自分で読み、本 BUILT に転記した。設計/監査へ自動で届く経路は通っていない。**
   - [ ] **(B) 〇〇（経路名）を経て設計/監査へ届いた。**
6. §7 の2件。
7. 本番コードの変更は §2 の3箇所のみであること。**それ以外を1行も変えていないこと。**
8. **1回しか投入・1段しか進めていないこと。**
9. 観測と実装を書き、判定・評価をしない。
10. commit しない。BUILT 冒頭に「運用方針 確認済（版: v1.7）」と受領文書一覧。
11. **v1.5**: 「動く」と書くときは実行した再現コマンドと結果を併記する。

---

## 9. 位置づけ（緩めない）
- **理由が出ても「2DER が作れるようになった」と書かない。** **見えるようになっただけである。**
- **理由が1件見えても、それが唯一の原因とは限らない**（1回の観測・v1.5 §4-13）。

---
*BUILD SPEC v1.0（★実装源）。Build 10=捨てられている planner の失敗理由を出す修理（新機能ではない・挙動不変・fail-closed のまま・追加のみ）。★捨てている場所は3つ: S1 `dispatch.py:104-107` が `pres` を recorded 偽で捨てる／S2 `run_until_barrier` の trace が5キーしか積まない／S3 `webui.py:596-597` の `/api/run_next` 応答が4キーしか返さない——**S1 だけ直しても webui 経路では見えない**。`planner_outcome` を raw のまま載せ、`None`（呼ばれていない）と `{"recorded": False, ...}`（呼ばれて失敗）を必ず区別できるようにする＝本 build の目的そのもの。変えないもの=dispatched/reason 文字列/nlo/pending_actor/auto_served/`_emit_pending` の台帳スキーマ/fail-closed 判定/`runtime_inspection`(別件)。非回帰は dispatch に触れる9本＋既定4本（完全一致比較は見つからずキー追加で壊れないと予想・壊れたら assert を書き換えず止めて上げる）。★受入の本体=修理後に同じ task で1回だけ RUN NEXT し `planner_outcome` を逐語全文で貼る（`stage`/`reason` を1文字も省略しない）。`None` だったら私の推論が誤りであり、そう書いてよい。予想=非回帰全PASS/`planner_outcome` は None でない/`stage=validation`/`reason` は `target_workspace` 関連。受入5 は3回連続で欠落したため二択に丸を付ける形にした。併せて `ledger_query.py` 削除の実施/未実施を明記。理由が出ても「作れるようになった」と書かない——見えるようになっただけ。*
