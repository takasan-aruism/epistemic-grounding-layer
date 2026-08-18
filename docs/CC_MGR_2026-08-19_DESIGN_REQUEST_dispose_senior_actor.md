# 宛: DESIGN（監査 CC）―― 契約作成の依頼: DISPOSE の judgment-required を headless Claude へ上申する

**依頼元: MGR ／ 2026-08-19 ／ Taka 裁定に基づく**
**MGR は設計も実装も契約本文も書きません。この文書は要件だけです。**

---

## 1. 直してほしいこと（★1点だけ）

```
DISPOSE で 機械処分できない 所見（judgment-required・★実測 22.4%）が
★Claude barrier で 止まり ★誰も 呼ばれない。
★UPPER_REVIEW には 同じ場面で headless Claude を 呼ぶ 仕組みが 在り ★908回 動いている。
★DISPOSE にだけ その actor が 無い。
```

## 2. 四問の確認結果（★すべて正本・2DER の面から。★これが「可能」の根拠）

### ① `claude_barrier=True` は何を意味するか → **★「その役の actor がまだ登記されていない」**

**`dw/dispatch.py:34` の逐語（★Taka 自身の裁定コメント）:**

```
# Taka 裁定 2026-08-07: ★CLAUDE_SENIOR を登記したので barrier を開ける(★戻す時は True に戻す1語)。
"READY_FOR_UPPER_REVIEW":   ("UPPER_REVIEW", "CLAUDE_SENIOR", ..., ★False),
"JUDGE_REQUIRED":           ("UPPER_REVIEW", "CLAUDE_SENIOR", ..., ★False),
```

**∴ UPPER_REVIEW は元 `True` で、★actor を登記した時に `False` へ変えた。**
**`True` ＝「対話型 MGR 待ち」でも「Claude 判断が必要」でもなく、★「呼べる相手が居ない」の意。**
（★`dispatch.py:45` の `# upper review (Claude barrier)` は★変更前のコメントが残っている＝現状と食い違う）

### ② DISPOSE 用 headless actor を既存責務境界の中で追加できるか → **★できる**

```
差し込み口 = webui.py:608-609 `_machine_registry()` の 返り
   {"CODING_WORKER": cw, "INDEPENDENT_AUDITOR": au, ★"MANAGER": mgr,
    "BUILD_PLANNER": build_planner, "CLAUDE_SENIOR": SRV.make_actor(_now())}
★MANAGER の 欄は ★既に 在る（★新しい 役を 増やさない）。
★対照 = twoder/senior_review.py（★前例・3384B）
```

### ③ Claude の返答を既存の口へ戻せるか → **★戻せる（2本とも既存）**

```
① actor が その場で 記録  … dw/workcell.py::record_disposition(task_id, finding_dispositions,
                              ts, manager_identity)
                              verdict∈{ACCEPTED, PARTIAL, REJECTED, REMAINS}
                              PARTIAL は accepted_portion 必須 ／ malformed は ★fail-closed
② front door から 戻す    … webui.py:629-630  `/api/ingest`
                              op == "DISPOSE" → W.record_disposition(..., "claude-manager")
                              逐語「★state advances via the real records」
```

### ④ Taka を通さず自走再開できるか → **★できる**

```
★UPPER_REVIEW の 前例が それを 908回 実証している
   senior_review の fn が その場で W.record_upper_review(..., "claude-senior")
   → ★state が 進む（★呼び出し→返り値で 完結・★人が 押す 場面が 無い）
★Taka が 要るのは authority 層3 だけ（★/api/pending_approvals・★この経路に 居ない）
```

## 3. 要件

```
★対照は twoder/senior_review.py（★同じ形にする・★新しい形を 作らない）
★新しい 役 0（MANAGER の 欄を 使う）／ 新しい 判断規則 0 ／ 新台帳 0 ／ front door の 口 0増
★`_TEST_CATEGORIES` を 変えない ／ `disposition.py` の 判定規則を 変えない
★機械が judgment-required を 自動処分しては ならない
   （★実測: 今まで ★0件。★この境界を 壊さない＝★最重要）
★記録の identity は 機械の "2der-auto-dispose" と ★区別できる 語にする
   （★誰が 決めたかを 後から 数えられる形＝★前例は "claude-senior"）
★読めない返事・呼べなかった時は ★何も記録せず recorded=False を返す（★fail-closed）
   （★senior_review 逐語「語が PASS/FAIL でなければ ★何も記録せず recorded=False を返す」）
★返事の 読み取りは ★既存の 部品を 使う（★新規に 作らない＝senior_review の 前例）
```

## 4. ★DESIGN が決めること（★MGR は決めていません）

```
★(a) `_MAP` の "DISPOSITION_REQUIRED" の claude_barrier を False にするか
      → ★Taka 2026-08-07 の 前例と 同じ 一語（★逐語「戻す時は True に戻す1語」）
      → ★但し ★正本に 触れる ∴ ★DESIGN が 妥当性を 判定する
★(b) 機械処分できる件と できない件を どこで 分けるか
      ★注意（★MGR が 見つけた 危険。★対処は DESIGN が 決める）:
        dispatch.py:117-124 は `mechanically_dispositionable` が True の時だけ fn を 呼び、
        False なら ★その分岐を 素通りして 163行の barrier へ 落ちる。
        ★barrier を False に しただけだと 168行の 機械 dispatch へ 進み、
        ★現在の MANAGER actor（webui.py:588-599）は ★条件を 見ずに 必ず
        `reproduction_dispose_fn` / `adjudicate_dispose_fn` を 走らせて
        ★"2der-auto-dispose" で 記録する。
        ＝★★judgment-required を 機械が 自動処分してしまう（★安全境界の 破れ）。
      → ★この危険を どう 塞ぐかは ★DESIGN が 決める
★(c) 呼び出しの 上限（★senior_review は TIMEOUT_S=180）
```

## 5. 契約の形（★既存どおり）

```
`<<<2DER:SKELETON>>>` / `<<<2DER:IMMUTABLE_TESTS>>>` / `<<<2DER:END>>>`
置き場 = /home/takasan/egl/docs（★CONTRACT_DOCS_DIR）
命名   = CC_DESIGN_2026-08-19_CONTRACT_<name>.md
→ ★置けば 常駐 `submit_next_contract` が ★次の巡回で 自力で 投げる（★実証済み: 3分で 拾った）
```

**★封印試験に必ず書いてほしい観点（★過去の失敗の型から。★中身は DESIGN が決める）:**

```
★大小   … 所見 0件 ／ 1件 ／ 複数（★一部だけ 機械処分できる 混在の 場合）
★順序   … 機械処分できる件が 在る時、★機械が 先に 処理するか
★空・None … Claude が 呼べなかった ／ 返事が 空 ／ 語が 未知（★何も 記録しない）
★安全境界 … ★judgment-required を "2der-auto-dispose" が 記録しないこと（★最重要）
★冪等   … 二度 呼んでも 二重に 記録しないこと
★既存経路 … 機械処分可の 77.6% が ★今までどおり 自動で 通ること
```

## 6. 受入（★MGR が front door と GM の正規面で確認します）

```
① judgment-required の task を 1件 使う（★実在: TASK-2DER-4E2A58F2・DISPOSITION_REQUIRED）
② ★Claude（対話型）が DISPOSE しない・★run_next を 手で 叩かない
③ ★常駐が 自力で headless Claude を 呼ぶ
④ `record_disposition` に ★機械と 区別できる identity で 記録が 残る
⑤ state が DISPOSITION_REQUIRED から ★次状態へ 自力遷移する
⑥ ★Taka 途中裁定 = 0 で 閉じる
```

## 7. MGR がしていないこと

```
★設計 0 ／ 実装 0 ／ 契約本文 0
★_MAP / _TEST_CATEGORIES / disposition 規則を 触っていない
★DISPOSE を 代行していない ／ run_next 0 ／ Taka に 途中裁定を 求めていない
```
