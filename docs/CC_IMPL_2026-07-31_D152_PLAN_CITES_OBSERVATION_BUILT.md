# 【BUILT】D-152 — **★PLAN が Observation の ID を引用した。★しかし「使って立った」とは言えない**

- `BUILD_ROLE: 参照` / **宛: 設計/監査(CC-α)** / 写: MGR / Taka / 発: 実装(IMPL) / 2026-07-31 03:2x / TYPE=BUILT
- **運用方針 確認済（版: v2.8）** ／ **実装源**: `CC_DESIGN_2026-07-31_D152_BUILD_SPEC_PLAN_CITES_OBSERVATION.md`
- **受領した MGR 文書**: **無し**（依頼文のみ `CC_MGR_2026-07-31_D152_…` §5 から**機械で抽出**）
- **`:8005` が呼ばれた**（★私は0件。**★`run_next` で 2DER が3回**。`runtime_recovery.attempts=3` と一致）

---

# 1. ★変更した1箇所
```
twoder/submit.py  観測分岐 ／ 2 hunk ／ 20挿入・19削除 ／ diff に gpu・nvidia は ★0件
内容: knowledge_packet の provenance に ★egl_source_refs（既に在る OBS の id）を渡す
```
> **★迷いを1行（SPEC §7 に従い、狭い方を採って進んだ）**: **「1箇所＝provenance に1行 足す」と読むと★実行不能だった**——`EGL_SOURCE_REFS` は**観測の後**に入るのに、task 生成は**観測の前**に在ったためである。**★狭い方＝「同じ分岐の中で、既存の task 生成ブロックを観測の後ろへ動かす」を採った。★新しい処理は1つも足していない**（削除19行は移動元）。

**★作っていないもの**: 新しい台帳／新しい API／新しい ID 族。**★観測を Task の下流へ移していない**（観測は今までどおり投入時に走る。★参照を渡しただけ）。
**★後方互換**: 基準値**11件すべて不変**（`resolved` も record キー数も）。

---

# 2. ★受入（★1条件に1つの印。★「概ね」と書かない）

| # | 受入（Taka 逐語） | 印 | 実測 |
|---|---|---|---|
| **1** | `cites_source_ids` が空でない | **○** | `['OBS-00975','OBS-00976','OBS-00977','OBS-00978']` |
| **2** | 対象 Observation または Ledger 記録の ID を引用する | **○** | **★今回の投入の `egl_source_refs` と完全一致**（別の投入の id ではない） |
| **3** | 既に観測済みの能力を、新規作成対象として重複計画しない | **★×** | **★重複計画している。** `target_file="tool.py"` / `files_expected=["tool.py","test_tool.py"]` / `steps[0]="ポート状況取得の基盤ロジック設計（/proc/net/tcp解析、ss/netstatコマンド実行、socket接続テストの3段階アプローチ）"` ＝**★`ss -ltn` で既に取れている能力を、★新規に作る対象にしている** |
| **4** | 証拠から不足が判定された場合だけ改修 Task を作る | **★×** | **★「何が取れていないか」を観測から述べていない。** 語の出現を数えた（打ち切り無し）: **「観測」0 ／「既に」0 ／「取得済」0 ／「ss -ltn」0 ／「プロセス」0**。`OBS-` は8回 出るが**★id の羅列であって内容の参照ではない**。`unresolved_assumptions` も OS/Python/JSON の一般前提のみ |
| **補** | 後方互換 | **○** | 11件 不変 |
| **補** | 1箇所・GPU 固有語なし | **○** | `submit.py` のみ／2 hunk／20挿入19削除／`gpu`・`nvidia` **0件** |

---

# 3. Last PASS
> **★受入2。** **`PLAN` が、★この投入で生まれた Observation の ID を、★取り違えずに引用した**
> （`plan_source=QWEN_BUILD_PLANNER` ／ `runtime_recovery={attempts:3, final_max_tokens:8192, RECOVERED}` ／ `CREATED → READY_FOR_IMPLEMENTATION`）。

# 4. First FAIL
> **★受入3（重複計画）。** **★id は引用されたが、★中身は使われていない。**
> **★∴「Observation を使って PLAN が立つ」は★まだ証明できていない。**（★「概ね引用できた」とは書かない）

---

# 5. ★2DER 担当工程数の前回差分
```
★0（★今回の修正は IMPL が書いた ∴ 2DER の担当に数えない）
```

# 6. ★次に直す1件（★実施しない）
> **`build_planner.py` の `_plan_prompt`（99-126行）に、★観測の中身を渡す。**
> **根拠**: 現在プロンプトに入るのは **goal と `trace_id` だけ**である ∴ **★planner は `OBS-` の id を「引用すべきもの」としてすら見ていない**（id は provenance 経由で **plan 生成後に** `cites_source_ids` へ入る＝`build_planner.py:203`）。**★受入3・4 が届かない直接原因はここ1点である。**

---

# 7. ★予告の当否（★1つずつ）

| # | 予告 | 結果 |
|---|---|---|
| **P-1** | 受入1 は立つ | **★当たり** |
| **P-2** | 受入2 は立つ | **★当たり** |
| **P-3** | 受入3 は立たない見込み（プロンプトに観測が入らないため） | **★当たり**（★「いちばん外れてほしい所」だったが、★外れなかった） |
| **P-4** | 受入4 は判定できない見込み | **★当たり**（★判定材料が無いのではなく、**★計画が観測に言及していない**ので不成立と判定した） |
| **P-5** | `MODIFY_EXISTING` か `BUILD_CAPABILITY` に落ちる | **★外れた。** **`OBSERVE_CURRENT_STATE` に落ちた**（`acquisition_method=RUNTIME_INSPECTION`）<br>**★ただし予告の帰結（「task が作られず PLAN に届かない」）は起きなかった**——**`D-144` で観測経路も task を作るようにしたため、`TASK-2DER-444E7599` が生まれ、PLAN まで届いた** |

**★依頼文**: 56字 / sha1 `444e75993d556ec27651bc282f24f4c7906e6b53`（★MGR 文書から機械抽出・打ち直していない）。**★予告 task_id `TASK-2DER-444E7599` と実測が一致。**

---

# 8. ★私が行った操作（★全件）
```
★実装: twoder/submit.py 1箇所（2 hunk・20挿入19削除）
★運用: webui 再起動 1回（旧 PID 3941865 → 新 PID 3950052 / 03:09:39）
        操作者=IMPL ／ 理由=submit.py の変更を本番へ反映 ／ ★既存運用 ／ ★2DER の担当に数えない
        ★run-gate は初期化された（★以後の投入で立て直るため結果に影響なし）
★投入: POST /api/submit ★1回（03:10:14。receipt last_recv_at=03:10:14.656361・recv_count 75→76）
★実行: POST /api/run_next ★1回（03:10:57 → 03:11:47・50.3秒）。★他の task は押していない
★停止: ★PLAN が出た所で止めた。★GENERATE へ進んでいない
★していないこと: ★Ledger（保留中）を触っていない ／ ★観測を task の下流へ移していない
                  ★新しい台帳・API・ID 族を作っていない ／ ★自分で :8005 を叩いていない
                  ★commit していない ／ ★テストは0本（走らせていない）
★副作用: tasks 158 → 159（+1）
```

---
*IMPL → 設計/監査（写: MGR / Taka）。D-152。**変更は `twoder/submit.py` 1箇所（2 hunk・20挿入19削除・`gpu`/`nvidia` 0件）で、観測経路の provenance に既に在る `EGL_SOURCE_REFS` を `egl_source_refs` として渡した。★「provenance に1行足す」だけでは実行不能（`EGL_SOURCE_REFS` は観測の後に入るのに task 生成は観測の前だった）ため、狭い方＝同じ分岐内で既存ブロックを観測の後ろへ移す、を採った（新しい処理は足していない）。** 後方互換11件は不変。**受入は 1○（`cites_source_ids` = `OBS-00975〜00978`）／2○（★今回の投入の id と完全一致）／★3×（`tool.py` を新規作成する計画＝`ss -ltn` で既に取れている能力を重複計画）／★4×（「観測」「既に」「取得済」「ss -ltn」「プロセス」の出現がいずれも0＝不足を観測から述べていない）。** **Last PASS=受入2、First FAIL=受入3 ∴「Observation を使って PLAN が立つ」は★まだ証明できていない（「概ね引用できた」とは書かない）。** 予告は **P-1〜P-4 が当たり、P-5 だけ外れた**（`OBSERVE_CURRENT_STATE` に落ちたが、`D-144` の task 生成により PLAN までは届いたので、予告の帰結は起きなかった）。**2DER 担当工程数の前回差分は 0。** 次に直す1件は **`build_planner.py:99-126` の `_plan_prompt` に観測の中身を渡すこと**（現在は goal と `trace_id` のみ ∴ planner は id を見てすらいない）。**GENERATE は押していない。commit していない。***
