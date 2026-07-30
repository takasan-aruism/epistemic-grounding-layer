# 【BUILD SPEC】**★PLAN が直前の Observation を使って立つ**ことを証明する（1箇所）

- `BUILD_ROLE: ★実装源` / **宛: IMPL** / 写: MGR / Taka / 発: 設計/監査(CC-α) / 2026-07-31 03:1x / TYPE=BUILD_SPEC
- **運用方針 確認済（版: v2.8）** ／ **正典**: `TAKA_2026-07-31_HOLD_THE_DIAGRAM_PROVE_PLAN_USES_OBSERVATION.md`（逐語）／**実施**: `CC_MGR_2026-07-31_D152_…`
- **★`CC_DESIGN_2026-07-31_D151_BUILD_SPEC_LEDGER_RAW_OUTPUT.md` は★保留（`CC_DESIGN_2026-07-31_HOLD_LEDGER_SPEC.md`）。★本書が今回の実装源である。**
- **★2DER 優先原則の例外**（IMPL が書く）。**★担当工程数の差分は 0 の見込み。★0 なら「0」と書く。**

---

# 1. ★設計の調査（★read-only で読んだ。★これが今回の設計の全部である）

| # | ★事実 | 根拠（★実読） |
|---|---|---|
| **1** | **`cites_source_ids` は★provenance の `egl_source_refs` から来る** | **`twoder/build_planner.py:203`** `plan["cites_source_ids"] = provenance.get("egl_source_refs") or []` |
| **2** | **★観測経路の packet の provenance に `egl_source_refs` は入っていない** | 実測（`TASK-2DER-67FE6548` の provenance = `trace_id / ds_input_id / rri_request_id / rri_intent_id / etrace_run_id / dw_task_id`） |
| **3** | **★観測の id は同じ投入の中で既に在る** | `submit.py` が `_rec("EGL_SOURCE_REFS", [...])` に `OBS-…` を入れている（★観測経路の中） |
| **4** | **★planner が見るプロンプトには、★goal と `trace_id` しか入っていない** | **`build_planner.py:99-126`** `_plan_prompt(goal, provenance)` は `"TASK (verbatim user request):%s"` と `"(provenance trace: %s)" % trace_id` だけ |

> ### **★∴ 1箇所で届くのは受入1・2 までである。★3・4 は届かない見込みである（§3 の予告）。**
> **★これは「止まる理由」ではない。★狭い方を採って進み、★結果を観測する**（`D-151` §1 / `D-152` §3）。

---

# 2. ★やること（★1箇所だけ）

```
★観測経路の knowledge_packet の provenance に、★同じ投入で既に在る `EGL_SOURCE_REFS`（OBS の id）を
★`egl_source_refs` として渡す。
```
| 条件 | |
|---|---|
| **★場所** | **`twoder/submit.py` の観測分岐 1箇所**（★`D-144` で作った `_obs_kp` の provenance） |
| **★作らないもの** | **新しい ID 族／新しい台帳／新しい API**（★既に在る `OBS-` の id をそのまま渡すだけ） |
| **★線を越えない** | **★これは「観測を Task の下流へ移す」ではない。★既に在る観測の★参照を渡すだけである**（`D-152` §4） |
| **★語の禁止** | **★diff に `gpu` / `nvidia` を0件**（大小無視・打ち切り無しで走査して示す） |
| **★触らないもの** | `BUILD_CAPABILITY`/`MODIFY_EXISTING` 経路 ／ Ledger（生出力）★保留中 ／ GPU 取得 ／ `_CATALOG` ／ 選別 |

---

# 3. ★予告（★投入前に固定する。★外れたら「外れた」と書く）

| # | 予告 | 確信 |
|---|---|---|
| **P-1** | **受入1（`cites_source_ids` が空でない）は★立つ** | 高（§1-1・§1-3） |
| **P-2** | **受入2（Observation の ID を引用）は★立つ**（★`OBS-…` が入る） | 高 |
| **P-3** | **★受入3（重複計画しない）は★立たない見込み** — **★planner のプロンプトに観測の中身も id も入らない**（§1-4）∴ **★前回と同じ「スクリプトを新しく作れ」が出ると予想する** | **★中。★ここが今回いちばん外れてほしい所** |
| **P-4** | **受入4（証拠から不足が判定された場合だけ改修 Task）は★判定できない見込み**（P-3 が立たなければ判定材料が無い） | 中 |
| **P-5** | **★依頼文の分類**: `MODIFY_EXISTING` か `BUILD_CAPABILITY` に落ちると予想する（★「取得できるようにする方法を検討」があるため）。**★`OBSERVE_CURRENT_STATE` に落ちたら「外れた」と書く**（★その場合 task が作られず PLAN に届かない） | **★低。★最も外れそう** |

---

# 4. ★確認（★MGR が固定した依頼文。★1文字も変えない）

```
現在の待ち受けポートの状況を確認し、確認できない項目があれば、それを取得できるようにする方法を検討してください。
```
**★`CC_MGR_2026-07-31_D152_PROOF_FIRST_LEDGER_WAITS.md` の §5 から機械で抜く**（★打ち直さない）。**★字数と sha1 を BUILT に書く。★`TASK-2DER-` + sha1 先頭8桁大文字 が予告 task_id である（★自分で計算して先に書く）。**

## 4-1. 手順
```
① 修正 → webui 再起動（★全件 記録。★run-gate 初期化も）
② POST /api/submit ★1回 → ★直後に GET /api/receipt（★他の口を叩く前に）
③ POST /api/run_next?task_id=… ★1回
④ GET /api/claude_packet?task_id=… で ★implementation_packet_ref を引く
⑤ ★PLAN が出たらそこで止める。★GENERATE へ進まない
```

---

# 5. ★受入（★1条件に1つの印。★まとめない。★「概ね引用できた」と書かない）

| # | 受入（★Taka 逐語） | ★示し方 |
|---|---|---|
| **1** | **`cites_source_ids` が空でない** | `implementation_packet_ref.cites_source_ids` の実値 |
| **2** | **対象 Observation または Ledger 記録の ID を引用する** | **★その id が★今回の投入で生まれた `OBS-…` と一致するか**（★別の投入の id なら不成立） |
| **3** | **★既に観測済みの能力を、新規作成対象として重複計画しない** | **★`objective` / `files_expected` / `steps` の実文**。**★前回と同じ「`ss` を実行するスクリプトを作れ」なら★不成立**（★1・2 が立っていても） |
| **4** | **証拠から不足が判定された場合だけ改修 Task を作る** | **★計画が「何が取れていないか」を観測から述べているか**。★述べていなければ不成立 |
| **補** | 後方互換 | **★下の基準値11件を取り直して1件ずつ**（★`D-151 SPEC §3-1` の値） |
| **補** | 1箇所・GPU 固有語なし | 変更ファイル／hunk／挿入削除行数 ／ `gpu`/`nvidia` 0件 |

---

# 6. ★やってはいけないこと
```
★観測を Task の下流へ移す設計変更  ★GENERATE を押す  ★新しい台帳・API・ID 族の追加
★Ledger（生出力）を同時に直す（★保留中）  ★別の欠陥を見つけたことを理由に止まる
★「概ね引用できた」と書く  ★commit しない  ★61本の非回帰は走らせない
★:8005 を自分で叩かない（★2DER が内部で呼ぶのは可。★呼ばれたら1行 書く）
```

# 7. ★止まってよい場所（★狭い）
```
★この1件が実行不能である具体的証拠  ★データ破壊／既存互換性破壊／ロールバック不能の証拠
★★それ以外は止まらない。★2通りに読めたら★狭い方を採って進み、★迷いを報告に1行 書く
```

# 8. ★報告（★正典の6項目。★増やさない）
```
1. 変更した1箇所  2. 受入1〜4 の判定（★1条件に1つの印）  3. Last PASS  4. First FAIL
5. ★2DER 担当工程数の前回差分（★0 なら「0」）  6. 次に直す1件
★予告 P-1〜P-5 の当否を1つずつ  ★宛: 設計/監査(CC-α)。TYPE=BUILT
```

---
**決めたこと**: **①`cites_source_ids` は provenance の `egl_source_refs` から来る（`build_planner.py:203`）が、観測経路の packet はそれを持っていない ∴ 直すのは1箇所＝既に在る `EGL_SOURCE_REFS` を観測 packet の provenance に渡すこと ②ただし planner のプロンプトには goal と `trace_id` しか入らない（`build_planner.py:99-126`）∴ 受入1・2 は立つが3・4 は届かない見込みで、それを予告として先に固定した（止まらずに進み結果を観測する） ③依頼文は MGR 固定のものを機械で抜いて1回だけ投入し、PLAN が出たら止める。**
