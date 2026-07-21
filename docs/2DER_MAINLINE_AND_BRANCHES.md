# 2DER 本線と支流（実測 2026-07-22）

- **導出:** `egl/structure/LINEAGE.jsonl` / `HISTORY_EVENTS.jsonl` / `REACHABILITY.jsonl` / `ITEM_LADDER.jsonl`
- **本線の定義（1 つに固定）:** 入力 → RRI(意図解決) → DW(実行) → 結果 → EGL(admission) → 台帳 → 次
  この一周に直接寄与する辺を持つものが本線。**それ以外を「不要」とは呼ばない。**
- **claim ceiling:** 分類は到達性・実行痕跡・命名規則からの導出。価値判断ではない。

---

## §1. 本線 1 本（What survived）

```
2DER AUTONOMOUS RESEARCH LOOP v0
  (docs/2DER_TECHNICAL_SPECIFICATION.md:5, 2026-07-10 Taka v0-direction authority)
  「既存資産を機械接続し manual relay を減らす。self-improvement claim ではない」

  ① ITEM 選択          task_selector.py       実装済・LIVE 呼出元 0
  ② → DW タスク生成     ✗ ABSENT                        ← 唯一の欠損辺
  ③ Worker 実行        qwen_worker / live_worker_runtime   LIVE
  ④ 検証 / patch 適用   patch_bridge / bridge_minter        LIVE（実配備済み）
  ⑤ EGL admission     egl/de_admission.py                 LIVE（submit.py:123）
  ⑥ ループ閉じ         return_loop.py:23→28→33→38          LIVE（4 系すべてに接続）
  ⑦ → ① へ            ② が無いため回らない
```

**②以外は全部通っている。** 詳細な呼出点は `2DER_END_TO_END_WIRING_MAP.md`。

---

## §2. コード量の分布（427 files / 44,914 LOC）

| 系譜 | files | LOC | 比率 |
|---|---|---|---|
| **core_path** | 48 | 6,874 | 15.3% |
| observability | 8 | 1,052 | 2.3% |
| **safety_support** | 9 | **955** | **2.1%** |
| migration_handoff | 3 | 929 | 2.1% |
| **本線 小計** | **68** | **9,810** | **21.8%** |
| test | 157 | 13,808 | 30.7% |
| unwired_support | 85 | 10,241 | 22.8% |
| experimental_branch | 97 | 9,748 | 21.7% |
| historical_residue | 20 | 1,307 | 2.9% |
| **支流・残渣 小計** | **359** | **35,104** | **78.2%** |

> **「監査システムを作っていた」という印象と、実際にライブで安全側に効いているコード量は
> 一致しない。`safety_support` は 955 LOC（2.1%）にすぎない。**
> 監査の重量はコードではなく、**プロセス側**（DE 484 件 / JREV / GA / 承認ゲート）に載っている。

---

## §3. フェーズ（境界は「系統間の依存が新しく生まれた commit」で機械的に切った）

主観的な章立てをしていない。682 commit の AST import 差分から算出。

| 期間 | commits | 中核系統間の辺の誕生 | 性格 | 本線への寄与 |
|---|---|---|---|---|
| **P1** 07-05〜07-07 | 105 | 36 | EGL/DS/RRI/DW 各系の骨格、4 系ループ初回クローズ | **土台** |
| **P2** 07-08〜07-10 | 51 | **1** | HBB / AFE frame 実験 | 支流（CLOSED-NEG） |
| **P3** 07-11〜07-15 | 409 | **103** | 2DER 本体の配線（submit / conductor / UI / return_loop / failure-memory） | **本線** |
| **P4** 07-16〜07-22 | 117 | **0** | bridge / energization / 実配備 / FIX-01 | 既存継ぎ目の深掘り |

```
最後の中核系統間の辺の誕生 : 2026-07-15
以降 117 commit (17%) で新規系統間接続 = 0
```

### P4 を誤読しないこと

P4 は無価値ではない。`PROJECT_GOAL.md §6` の DE ブロック分析では、
DE-0401–0450 の帯に essential=YES が **23 件**集中しており、全期間で最大級の荷重帯である。
ただしそれらは **既に存在する継ぎ目（TWODER→DW / TWODER→EGL）の内側**を固める作業であり、
新しい系統間接続を作る作業ではなかった。

> **「系を繋ぐ」フェーズは 07-15 に終わり、以後は「繋いだ中を固める」フェーズに移った。
> 欠損辺 ①→② は、その繋ぐフェーズの中で一度も着手されないまま終わった。**

---

## §4. 支流の内訳（それぞれ、何であったか）

### 4.1 P2 の実験枝 — HBB / AFE（DE-0101–0150）

- 目的: Taka の frame 突破を、彼の介入なしに再現する（DE-0106）
- 帰結: `DE-0112`「SEALED one-shot; engine showed **no added value over skepticism**」
- 分類: `experimental_branch`。**CLOSED-NEGATIVE**
- コード量: `egl/experiments/` に 57 files / 6,486 LOC が残存

### 4.2 adjudicator efficacy（DE-0301–0350）

- 目的: test 失敗の欠陥クラス自動判定
- 帰結: `DE-0323`「closed the oracle-separation preregs as **measurement-not-identifiable**」
- ただし `dw/adjudicator.py` は **LIVE**（`live_worker_runtime.py:50` から）。
  実験は閉じたが、成果物の一部は本線に残っている。

### 4.3 IMPL-PLATFORM 島（DE-0250、07-13）

- 28 子項目を一括発行。`DE-0250` の裁定文は **「registration only」**
- 現況: **DONE 30 件が `TEST_ONLY_ISLAND`**
  （子モジュール → `end_to_end_acceptance_harness` → その回帰テスト、で閉じた輪）
- 分類: `unwired_support`（85 files / 10,241 LOC の主要部）

### 4.4 出荷束の複製

`egl/docs/SUBMIT_2026-07-21/` 配下に `patch_bridge.py` / `bridge_reconciler.py` /
`runner_v0.2.3.py` 等の複製が存在（`ARCHIVE_OR_EXPERIMENT`）。
本体は `twoder/` 側。**同一ファイルが 2 箇所にある状態**。

---

## §5. 独立監査（JREV）の分布

```
07-05: 11   07-06: 4   07-18: 3   07-19: 1   07-21: 3
07-07 〜 07-17 : 0（11 日間）
```

**JREV は立ち上げ期（P1）と bridge 期（P4）の両端にのみ存在し、
最も多くの辺が生まれた配線期（P3, 07-11〜07-15）には 1 件も入っていない。**

「監査が多すぎる」という印象と逆に、**本線が作られていた時期こそ監査が空白**だった。
`ROADMAP_DONE_BUT_NOT_WIRED` 30 件が P3〜その直後に集中しているのと整合する。

---

## §6. 何を残し、何を畳むかの材料（判断は Taka）

本書は分類のみを提示する。以下は**判断ではなく、判断に必要な数字**である。

| 対象 | files / LOC | 状態 | 材料 |
|---|---|---|---|
| IMPL-PLATFORM 島 | 約 30 モジュール | DONE だが未配線 | 配線する / DONE を降格する / 島として明示保存する |
| `egl/experiments/` | 57 / 6,486 | CLOSED-NEG の実験枝 | 結論は DE に記録済み。コードの保存要否 |
| `egl/docs/SUBMIT_*` の複製 | 11 / 2,113 | 出荷束の展開物 | 本体との重複 |
| ORPHAN | 20 / 1,307 | 呼出元も CLI も無い | — |
| `task_selector` 島 | 3 モジュール | ①→② の片側 | **繋ぐ（T-3）** |
