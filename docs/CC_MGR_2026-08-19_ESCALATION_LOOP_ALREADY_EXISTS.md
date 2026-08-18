# 宛: Taka / 設計 / 監査 ―― 「2DER → Claude 例外判断 → 2DER」は **既存機能だけで既に閉じている**

**実装 0。DISPOSE / UPPER_REVIEW を代行していない。`run_next` 0。Taka に途中裁定を求めていない。**

## 0. 結論

```
★★目標形（2DER自走 → 例外検出 → 証拠収集 → Claudeへ上申 → 判断 → 返却 → 自走再開）は
★★★既に 実装され ★908回 動いている。
★Claude の 実行主体 = ★★`claude -p`（★headless・非対話）
★Taka は この 経路に ★居ない。
★★∴「Taka がターミナルで Claude に付き添う」形は ★構造としては 既に 不要。
```

## 1. A. UPPER_REVIEW

### A1. 既存の機械経路 —— **★在る。しかも2本。**

```
① 決定論の 自動PASS  = dw/upper_review_gate.py（ITEM-2DER-EVO-0009）
     逐語「a task that is trivially clean by recorded DW state has nothing to review.
           For that subset only, this deterministically records a machine UPPER_REVIEW PASS」
     逐語「★Everything non-trivial stays a Claude barrier.」
② ★Claude 上申      = twoder/senior_review.py
     逐語「CLAUDE_SENIOR = ★2DER が起動する別プロセスの Claude Code(headless)。」
     逐語「★Taka 裁定 2026-08-07 20:56: 上級監査の担い手は Claude Code。
           ★3Claude(ターミナルの MGR/DESIGN/IMPL)が本文を書くことは禁止。
           ★★Taka が YES を押す形も不可(呼び出し→返り値で完結)。」
     MODEL_CMD = ★['claude', '-p', <prompt>, '--output-format', 'json'] ／ TIMEOUT_S = 180
```

### A2/A3. 実績（★507 task 全件・記録の `identity`）

```
upper_review 記録を 持つ task = ★189
   ★claude-senior           = ★908 回   ← ★headless Claude が 判断した
   ★2der-auto-upper-review  = ★ 74 回   ← ★決定論の 自動PASS
                                = ★機械 7.5% ／ ★Claude 92.5%
★verdict の 分布 = 読めなかった（★私が 引いた 鍵が 違う。★『0件』とは 書かない）
いま 待ち = JUDGE_REQUIRED 41 ／ READY_FOR_UPPER_REVIEW 13
```

### A4. Claude へ上がる理由 —— **★安全境界（★接続欠落ではない）**

```
dw/dispatch.py:155-162
   if op == "UPPER_REVIEW" and fn is not None:
       if URG.trivially_clean(task_id): → 自動PASS
       # ★non-trivial -> fall through to the Claude barrier (senior judgment required)

★★ただし _MAP では UPPER_REVIEW の claude_barrier = ★False
   READY_FOR_UPPER_REVIEW -> ('UPPER_REVIEW','CLAUDE_SENIOR','TASK+RUNS+TEST_RESULT', ★False)
   JUDGE_REQUIRED         -> ('UPPER_REVIEW','CLAUDE_SENIOR','TASK+RUNS+TEST_RESULT', ★False)
∴ dispatch:163 の barrier に ★落ちない = ★★機械 dispatch で CLAUDE_SENIOR actor が 呼ばれる
   ＝★headless claude が 走る（★人が 押す 場面が 無い）
```

### A5. いまの自走 task が DISPOSE 後どこで止まるか

```
TASK-2DER-4E2A58F2（dw_state=DISPOSITION_REQUIRED / last_completed_op=AUDIT）
★DISPOSE を 越えれば その先の UPPER_REVIEW は ★barrier では ない
   → ACCEPTED が 在れば READY_FOR_REGENERATE（★機械 CODING_WORKER）
   → 全部 REJECTED なら READY_FOR_UPPER_REVIEW（★headless claude）
★∴ ★止まるのは DISPOSE ★1箇所だけ。
```

## 2. B. Claude 例外処理の経路

### B1/B2. `claude-manager` の実体 —— **★`/api/ingest` に POST した外部 Claude**

```
webui.py:588-599  機械の MANAGER actor は ★必ず "2der-auto-dispose" を名乗る
webui.py:612-630  def ingest(task_id, actor_role, result)
     docstring 逐語「Ingest a bounded Claude-actor result into DW;
                     ★state advances via the real records.」
     op == "PLAN"        → W.record_plan(..., ★"claude-manager")
     op == "DISPOSE"     → W.record_disposition(..., ★"claude-manager")
     op == "UPPER_REVIEW"→ 語を is_known_verdict で 検査してから 記録

★∴ `claude-manager` = ★front door の `/api/ingest` 口へ 判断を 返した Claude。
★★対話型 MGR かどうかは ★記録から 区別できない（★UNKNOWN・★私は 推測しない）。
★一方 `claude-senior` は ★senior_review.py が subprocess で 起動した
  ★`claude -p`＝★非対話と ★確定している。
```

### B3/B4. 2DER から Claude へ仕事を渡す正式な上申機構

| 機構 | DISPOSE | UPPER_REVIEW |
|---|---|---|
| **`senior_review`（`claude -p`）** | **✗ 未接続** | **★接続済み・908回 実績** |
| `human_escalation_packet` | **✗** | **✗** |

```
★`human_escalation_packet` は ★人（Taka）へ 上げる 器（★§15・REQUIRED_FIELDS 5欄）で
   ★Claude へ 渡す 器では ない ∴ ★ここでは 使わない のが 正しい。
★DISPOSE の Claude tier は ★意図的に OFF:
   webui.py:595 逐語 `ADJ.adjudicate_dispose_fn(..., claude_fn=★None)`
   webui.py:591 逐語「tier-3 Claude fallback = ★OFF (INDETERMINATE -> labeled JR)」
   ＝★DISPOSE で 決まらない 件は ★JUDGE_REQUIRED へ 落ち → ★UPPER_REVIEW → ★headless claude
   ＝★★逃げ道は 既に 設計されている
```

### B5. Claude の判断を 2DER へ戻し自動再開する経路 —— **★在る（2本）**

```
① headless 経路 : senior_review の fn が ★その場で W.record_upper_review(..., "claude-senior")
                  → ★state が 進む（★戻す 通信が 要らない＝★呼び出し→返り値で 完結）
② 外部 Claude   : front door ★`/api/ingest`（18口の1つ）
                  → record_plan / record_disposition / record_upper_review
                  → ★「state advances via the real records」（逐語）
★どちらも ★Taka を 通らない。
```

### B6. いま Taka への対話要求が発生する地点 —— **★authority 層3 だけ**

```
★正規口 = `/api/pending_approvals`（★実測で 引けた）
   例: {"task_id":"ITEM-2DER-EVO-0015","action_type":"CHANGE_AUTHORITY_CEILING",
        "reason":"行為の段 IRREVERSIBLE > item の上限 REVERSIBLE ∴ 止める"}
        {"action_type":"NO_SUCH_ACTION","reason":"POLICY に無い行為 ∴ 止める(fail-closed)"}
★authority.gate_for_item が 層3(REQUIRES_TAKA) を 返す 場面
   ＝★不可逆 ／ ★POLICY に 無い 行為 ／ ★evidence≠OK
★★これは ★本当に Taka 裁定が 要る 場面（★方針どおり）。
```

## 3. ★「高度判断が必要」と「Taka が付き添わないと進まない」の切り分け

```
★許容する 方（★既に そうなっている）
   UPPER_REVIEW → headless `claude -p` → 記録 → 自走再開 ／ ★908回 ／ ★Taka 不在

★除去したい 方（★実測で どこに 在るか）
   ★2DER の 経路には ★無い。
   ★今夜 私（対話型 MGR）が やっていた
     ・front door を 手で 叩く ／ ・GM を 手で 呼ぶ ／ ・停止点を 見つけて Taka に 報告する
   ＝★★これは 2DER の 通常経路では なく ★開発作業（★2DER を 育てる 側）。
   ★★∴ ★通常運転の 経路からは ★既に 除去されている。
```

**★言い換え: 「Taka が付き添う」のは ★2DER が動く ためではなく、★★2DER を 直す ため。**

## 4. 最終報告（指定の形）

```
★通常系で 2DER だけが 処理する 範囲
    受信 / DS / RRI / EGL / SEAL / TASK生成 / task_ids追記 / RRI thread /
    PLAN（決定論 template ＋ Qwen build_planner）/ GENERATE / TEST /
    AUDIT（Qwen）/ DISPOSE の 77.6% / UPPER_REVIEW の 7.5%（trivially clean）/
    経路表の 自動採択（206行）

★Claude 高度判断へ 上申される 範囲
    UPPER_REVIEW の non-trivial ＝ ★908回（★92.5%）
    DISPOSE の judgment-required ＝ ★22.4%（★★ただし 上申機構は 未接続）

★Claude の 実行主体
    UPPER_REVIEW … ★`claude -p --output-format json`（★headless・TIMEOUT 180秒）
    DISPOSE      … ★`/api/ingest` へ 返した 外部 Claude（★対話型かは ★UNKNOWN）

★Claude 判断結果の 2DER への 戻り道
    ① headless: その場で W.record_upper_review → 自走再開
    ② 外部    : front door `/api/ingest` → 実記録 → 自走再開
    ★どちらも Taka を 通らない

★Taka を 必要とする 箇所
    ★authority 層3 のみ（不可逆 / POLICY 外 / evidence≠OK）／ 口は `/api/pending_approvals`

★★接続欠落（★1つだけ）
    ★★DISPOSE の judgment-required → Claude を 呼ぶ 手が 無い
       ・UPPER_REVIEW 側には `senior_review.make_actor` が 在り dispatch から 呼ばれる
       ・★DISPOSE 側には 同型の actor が ★無い
       ・★_MAP で DISPOSE の claude_barrier = ★True ∴ dispatch:163 で 止まる
    ★★＝「どことどこ」= ★`dw/dispatch.py` の DISPOSE 分岐 ↔ ★DISPOSE 用の headless Claude actor

★次に 機械化すべき 最小1箇所
    ★★`senior_review` と 同型の DISPOSE actor（★`claude -p` を 呼び
      `W.record_disposition(..., "claude-…")` する）を 作り dispatch へ 渡す。
    ★これは ★安全境界の 変更では ない（★判断は 依然 Claude が する）。
    ★★但し `_MAP` の claude_barrier=True を どう 扱うかは ★正本に 触れる ∴ ★Taka 裁定が 要る。
```

## 5. 「Taka がターミナルに付き添わなくても閉じるか」への答え

```
★★UPPER_REVIEW については ★★既に 完全に 閉じている（★908回の 実績・★Taka 不在）。
★DISPOSE については ★閉じていない ―― ★22.4% が Claude を 待つが ★呼ぶ 手が 無い。
★★∴ 残りは ★1本の actor だけ。★構造は 既に 全部 在る。
```

## 6. していないこと

```
★実装 0 ／ 新しい 判断規則 0
★_TEST_CATEGORIES / _MAP / disposition 規則を 触っていない
★DISPOSE / UPPER_REVIEW を 代行していない ／ run_next 0 ／ Taka に 途中裁定を 求めていない
★verdict が 読めなかったことを ★『0件』と 書いていない（★鍵が 違う）
★`claude-manager` が 対話型かどうかを ★推測で 埋めていない（★UNKNOWN）
```
