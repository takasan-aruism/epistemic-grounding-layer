# 2DER MISSING EDGES（実測 2026-07-22）

- **本書は `twoder/audit/MISSING_EDGES.md`（2026-07-12, DE-0173）を SUPERSEDE する。**
  旧版は破棄しない。§3 に差分を示す。
- **導出:** `egl/structure/EDGE_INVENTORY.jsonl` / `REACHABILITY.jsonl` / `EXECUTION_EVIDENCE.jsonl`
- **手法:** AST 呼出グラフ + 実行痕跡。**LLM 不使用**
- **重要な非対称:** `wired` の**肯定**は静的に可能だが、**否定**は静的には不可能
  （動的ディスパッチ。呼出点の 43.2% が未解決）。
  **本書で「繋がっていない」と述べる項目には、必ず実行痕跡側の根拠を併記する。**

---

## §1. 【最重要】欠損辺 ①→② — ITEM 選択 → DW タスク生成

### 実測

```
twoder/task_selector.py::select_next の呼出元
    TEST_ONLY_ISLAND     twoder/regression/test_task_selector.py
    IMPLEMENTED_UNWIRED  twoder/experiments/task_selector_authority_v0.1/eval_harness.py
    → LIVE な呼出元 0

dev-workcell/dw/workcell.py::create_task の LIVE な呼出元（全 2 本）
    LIVE   twoder/submit.py:408
    LIVE   twoder/experiment_candidate.py:116
    → いずれも task_selector を経由しない
```

`twoder/routing_delivery.py` は自ら "READ-ONLY delivery packets ... without launching a worker" と記す。
`DE-0347`（2026-07-17）はこの島を **intentional READ-ONLY boundary** として登録し、
未接続の半分（`create_task-from-selected_item` producer）が **ABSENT** であると記録している。
severance class = `CANONICAL_AUTHORITY_CONFLICT_REQUIRES_TAKA_DECISION`。

### 意味

**2DER は「与えられた仕事を実行して閉じる」ことはできるが、「次の仕事を自分で選んで着手する」ことができない。**
supervised executor と autonomous loop を分ける辺が、ちょうど 1 本残っている。

### 接続に必要なもの（T-3）

**新規機構ではない。既存の 2 つの呼出面を繋ぐ配線である。**

```
必要な producer:
    task_selector.select_next(...) の勝者 →  dw.workcell.create_task(...)

参照実装は既に live path に存在する:
    twoder/submit.py:408  が同じ create_task 呼出を行っている
    twoder/experiment_candidate.py:116 も同形（acquisition 由来の候補からタスクを起こす）

満たすべき制約（既存コードから機械的に導かれるもの）:
  1. `execution_admission` の再計算を通すこと
     （task_selector.py:297 が "select_next (winner) and execution_admission
       (fresh recompute for staleness/invalidation)" と自ら述べている）
  2. `twoder/authority.py:POLICY` の `DW_MACHINE_DISPATCH`(AUTO_EXECUTE) の範囲に収めるか、
     範囲外なら REQUIRES_APPROVAL としてゲートを通すこと
  3. 生成タスクは `twoder/artifact_registry.py` / ROADMAP ITEM を引用できること
     （candidate の全フィールドが resolvable な 2DER id を持つ規律 — DE-0180）
```

### ただし、繋いでも回るとは限らない

実行ファネル（`dev-workcell/events.jsonl` 674 件）:

```
CREATE 147 → PLAN 140 → GENERATE 90 → AUDIT 40 → DISPOSE 16 → COMPLETE 1
```

**タスク 147 件に対し COMPLETE 到達は 1 件。** ①→② を塞いでも、このファネルが
変わらなければ、自動生成されたタスクが滞留するだけになる。
**①→② の接続と、ファネルの歩留まりは別問題として扱うこと。**

---

## §2. その他の未接続（実測）

| # | 対象 | 状態 | 根拠 |
|---|---|---|---|
| 1 | `egl/egl/adapters.py`（`fetch_github` / `fetch_http_static`） | **SUPPORT_OFF_LIVE_PATH** | 取得スパイン `egl/acquisition.py::acquire` は LIVE（3 箇所から）だが、アダプタ本体は live 到達しない |
| 2 | `egl/egl/judge_vllm.py`（Gate4 判定） | **SUPPORT_OFF_LIVE_PATH** | live path から到達しない |
| 3 | `dev-workcell/dw/workflow.py::run_standard_workflow` | **SUPPORT_OFF_LIVE_PATH** | テスト済みの一括ワークフローは使われず、webui/operator が手組みで段階実行する |
| 4 | `egl/egl/etb.py`（証拠信頼境界） | **SUPPORT_OFF_LIVE_PATH** | 直接到達しない（acquisition 経由の間接呼出は静的に未解決） |
| 5 | RRI formal validation 8 本 | **WIRED_UNENTERED** | §3 参照 |
| 6 | IMPL-PLATFORM 系 22 子項目ほか計 30 ITEM | **TEST_ONLY_ISLAND** | §3 参照 |

---

## §3. 07-12 版との差分

### 3.1 撤回された主張

旧版 §11:
> RRI formal validation/handoff suite … All implemented + individually tested, **all unwired**.

**「unwired」は誤り。しかし「実行時に一度も走らない」は正しい。**

```
documented  YES   ITEM-2DER-EVO-0002 status=DONE / DE-0231
implemented YES   validator 8 本の実体
wired       YES   twoder/submit.py:99 に呼出が実在
executed    NO    RRI_FORMAL_VALIDATION は 337 トレース中 0 件
proven      NO
```

理由は `twoder/submit.py:96-99`:
```python
# SKIPPED when no candidates are supplied (default) => no behavior change
if formal_candidates:
    from twoder import rri_formal as RF
    fv = RF.run_formal_validation(formal_candidates, ts)
```
**`formal_candidates` は既定で空。配線はあるが分岐に入る呼出元が無い。**
状態名として `WIRED_UNENTERED` を新設した（`STRUCTURAL_RECONSTRUCTION_SPEC_v0.2.md` §B）。

### 3.2 新たに判明した島

旧版に記載の無い、より大きな構造:

```
end_to_end_acceptance_harness.py (217 LOC)
    imported_by = [自分の回帰テストのみ]
parallel_router / economy_operator / egl_integration / ...(計 30 ITEM 分)
    imported_by = [acceptance_harness, 自分のテスト]
```

`ROADMAP_REGISTRY` の **DONE 67 件のうち 30 件が、この閉じた輪の中にある**。
`DE-0287`「acceptance harness proving 35/35 ACs against real shipped modules」の
35/35 は真であるが、**証明対象は live path に接続されていないモジュール群である**。

一次資料 `DE-0250`（2026-07-13）は
> Issue the full Proposal-A child set now (**registration only**)

と明記している。登録は仕様どおりだった。その後 ROADMAP 上で DONE に遷移し、
配線工程が行われないまま残っている。

→ **`ROADMAP.status = DONE` は「モジュールが存在し単体テストが通る」を意味しており、
「live path に接続されている」を意味していない。** この定義の明文化（または 30 件の降格）は
Taka 裁定事項。

### 3.3 旧版で正しかったもの（現在も成立）

| 旧版 # | 主張 | 現況 |
|---|---|---|
| #2 | 研究要求 → Web/GitHub 取得が繋がっていない | `egl/egl/adapters.py` は今も off-live-path |
| #13 | `dw/workflow.py` の一括ワークフローが使われない | 今も off-live-path |
| #7 | operator ループに専用テストが無い | `LIVE_CODE_TESTED_ONLY_INDIRECTLY` として再検出 |

### 3.4 旧版から改善したもの

| 旧版 # | 主張 | 現況 |
|---|---|---|
| #3 | DW RESULT_PACKET → EGL admission に配線が無い | **繋がった。** `twoder/return_loop.py:23→28` が `build_result_packet` → `ingest_result_packet` を実行（DE-0175/0176） |
| #5 | EGL に DE claim を書く関数が live path に無い | **繋がった。** `submit.py:123` / `live_worker_runtime.py:139` / `runtime_supervisor.py:218` → `egl.de_admission.admit_design_evidence`（DE-0178） |

---

## §4. 本書の限界

1. **`wired=NO` は静的解析では証明できない。** 上表の「off-live-path」は
   「静的到達性が無く、かつ当該系統の実行痕跡が無い」ことを意味する。
   動的 import / 関数テーブル経由の呼出は検出できない（呼出点の 43.2% が未解決）。
2. `egl/etb.py` は `egl.acquisition.run_acquisition` から呼ばれている可能性がある
   （07-12 版はそう記録している）。**本書は「静的に到達しない」としか言えない。**
3. `DISPOSE 16` の内訳は未解析。ファネルの歩留まりの解釈には追加分解が要る。
