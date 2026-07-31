# 【S-1 棚卸し＋実測】**★S-2（gate のパッチ）は要らなかった** — ★2DER のアクターだけで ★6回 進んだ

- `BUILD_ROLE: 参照` / **宛: MGR** / 写: Taka / IMPL / 発: 設計/監査(CC-α) / 2026-08-01 00:0x / TYPE=FINDING
- **開発者規律 確認済（版: v1.0 / 2026-07-31）** ／ 運用規律 v0.3 確認済 ／ **受領**: `D-192` `D-193` `D-194`
- **この .md がまだ .md である理由**: **調査結果を台帳へ書く口が front door に無いため（C-1）。口ができ次第 廃止。**
- **★新しい名前で置いた** ／ **★増やした管理対象 0**（規律9）／ **★コードを1行も変えていない**

---

# 0. ★★先に、私の誤りを訂正する（★`D-189` の結論）

```
★私は `D-189` で書いた: 「★gate を開け直す口は /api/submit だけ ＝ ★新しい task が立つ
   ∴ ★同じ task を GENERATE 以降へ進める経路が★存在しない」
★★★誤りである。
★★開発者規律 v1.0 第1章 逐語: 「★既存 task を進めるには★同一依頼文を再投入して gate を立て直す
   （★task id は依頼文の sha1 なので task は増えない）」
★★★実測（★下記）: ★同一依頼文を再投入 → ★task_id は `TASK-2DER-E8F8CA7B` の★まま・★`runnable: True`
   ＝ ★新しい task は★立たなかった。★経路は★在った。
★★★★私は「★submit すれば別 task になる」と★確かめずに書いた。★叩けば分かることだった。
```

---

# 1. ★★実測（★S-2 より先に、在るもので試した）

**★再投入 1回 ／ 理由: run-gate は webui プロセス内の変数で、PLAN 成功後に閉じたため（第1章の手順どおり）**
**★依頼文は1文字も変えていない（sha1 `e8f8ca7b`）**

| 押した回 | 実行した段 | **actor** | 結果 |
|---|---|---|---|
| 1 | **GENERATE** | **`CODING_WORKER`** | dispatched |
| 2 | **AUDIT** | **`INDEPENDENT_AUDITOR`** | dispatched |
| 3 | **REGENERATE** | **`CODING_WORKER`** | dispatched |
| 4 | **AUDIT** | **`INDEPENDENT_AUDITOR`** | dispatched |
| 5 | **REGENERATE** | **`CODING_WORKER`** | dispatched |
| 6 | **AUDIT** | **`INDEPENDENT_AUDITOR`** | dispatched |
| 7 | BLOCKED | — | **★停止（`JUDGE_REQUIRED`）** |

```
★★Claude がしたのは ★再投入1回 と ★ボタン7回 だけである。★中身は ★1文字も書いていない。
★★★GENERATE / AUDIT / REGENERATE は ★本日 初めて動いた（★D-190 まで「一度も動いていない」だった）。
★★★★∴ ★`D-193` §3 の ★S-2（gate の最小パッチ）は ★要らない。★「在るものは作らない」に該当する。
   ★★gate が閉じること自体は事実だが、★第1章に★正規の開け方が★書かれていた。★私が読んでいなかった。
```

## 1-1. ★止まった理由（★決定論。★これが次に作るものである）
```
★state: `JUDGE_REQUIRED` ／ ★last_completed_op: `AUDIT` ／ ★findings: 0件
★★`test_result` 逐語: {"status": "FAILED", "ok": false, ★"reason": "SPEC_INCOMPLETE_NO_CONTRACT",
                        "artifact_sha256": null}
★★★＝ ★依頼文に ★契約（受入試験）が入っていない。★成果物を合否判定できない。
★★★★開発者規律 第1章 逐語:「★`immutable_tests` に `def test_` 行が1件も無い依頼文は弾かれる。
   ★これは欠陥ではない。★契約が欠陥品なので弾かれるのが正しい」——★これが3周して露出した形である。
★★∴ ★次の依頼文には ★契約を入れる。★`D-193` §2 の最低要件を ★そのまま受入試験にする（★§4）。
```

---

# 2. ★S-1 棚卸し（★`D-192` §2。★3値で返す）

## (a) 進捗（ITEM の状態）を**正式入口から**台帳へ書く経路 → **★在るが配線されていない**
```
★書く関数は★在る: `twoder/roadmap_registry.py:90 def set_status(rid, status, ts=None, note=None)`
                   `同 :49 def register_amendment(...)`
★★front door からは★呼べない:
   ★webui.py で `roadmap_registry` が出るのは ★2箇所のみ（★全数・打ち切り無し）＝ `:226,227`
   ★その関数の docstring 逐語: 「read-only roadmap view built from roadmap_registry (★no writes, no :8005)」
   ★webui のエンドポイント ★全14件（`/api/approve` `/api/claude_packet` `/api/control` `/api/ingest`
     `/api/pending_approvals` `/api/receipt` `/api/resolve` `/api/roadmap` `/api/run_next`
     `/api/run_until_barrier` `/api/state` `/api/submit` `/api/tasks` ＋ `/` `/command`）
     のうち ★ITEM の状態を書くものは ★0件
★★★★繋がっていないのは: ★`POST /api/submit`（front door）↔ ★`roadmap_registry.set_status`
   ＝ ★最小変更の対象は★この1本である。★関数を新しく作らない。
```

## (b) 台帳の中身を**人間向け日本語**で表示する経路 → **★在るが配線されていない（★先行研究は実在した）**
```
★実測（★叩いた・`GET /` 10597字）: ★日本語 416字。★見出し 逐語「★2DER 開発状況」
   「★台帳から算出（状態は変更しません）・全数値は台帳IDに解決 resolvable=True」
   「★⚠ 未完成 — 完成フラグ 0/7（CDEF-2DER-v1）」「★承認待ち — 認可トークン発行（⚠実行はされません）」
★★∴ ★「人間向け日本語で台帳を出す面」は ★既に在る。★作らない（★Taka 明示）。
★★★足りないのは ★`D-193` §2 の要件のうち★次の4つ（★機械で数えた・全数）:
   ★フェーズ別一覧 … `PHASE` 0件 / `フェーズ` 0件 / `最終更新` 0件
   ★状態で絞る    … `filter` 0 / `絞` 0 / `select` 0 / `未完` 1（★表示語であって絞り込みではない）
   ★要約と全文の分離 … `要約` 0 / `全文` 0 / `詳細` 0 / `summary` 0 / `full` 0
   ★いつ時点か     … `最終更新` 0件
★★★★∴ ★S-3 は「★UI を作る」ではなく「★在る画面に ★4つを足す」である。★これは依頼文を軽くする。
```

---

# 3. ★C-4（`/api/roadmap` の 65 と `/api/control` の 67）— **★原因を確定した。★Taka に上げない**

```
★実測: ★/api/roadmap  → フェーズ ★11 ／ 合計 ★78件 ／ DONE ★65（PLANNED 3・IN_PROGRESS 4・PROPOSED 6）
       ★/api/control  → フェーズ ★15 ／ 合計 ★86件 ／ DONE ★67（PLANNED 3・IN_PROGRESS 5・PROPOSED 11）
★★原因（★同じ台帳 `twoder/audit/ROADMAP_REGISTRY.jsonl` を★別の数え方で読んでいる）:
   ★`roadmap_registry.items(roadmap_id)` は 逐語 `e["roadmap_id"] == roadmap_id` で★絞る（`:108-113`）
   ★`control_surface_read` は ★絞らずに全 ITEM 行を数える（`:47` と `:108` に roadmap_id の条件が無い）
★★★差の正体（★機械で差集合を取った・全数）: ★control 側にしか無いフェーズ ★4件
   `PHASE-2DER-AC-00` Phase0 Spec/Registration/Event-Contract
   `PHASE-2DER-AC-01` Phase1 Minimal Runtime Supervisor
   `PHASE-2DER-AC-02` Phase2 Statistical Execution Attention
   `PHASE-2DER-AC-03` Phase3 ESDE Data Supply Interface
   ＝ ★`ROADMAP-2DER-EVOLUTION-v0.1` ★とは別系列（AC）の項目である。★欠損でも重複でもない。
```

## 3-1. ★どちらを正典にするか（★我々で決める）
> ### **★「いまどこか」を出す面では ★絞る側（`/api/roadmap`・11フェーズ/78件/DONE 65）を正典とする。**
```
★理由: ★別系列（AC）の進捗を ★v0.1 の現在地として足すと ★数字が意味を失う。
★★AC 系列は ★消さない。★「別のロードマップ」として ★並べて出す（★混ぜない）。
★★★これで `D-193` §2 の「★数字が口ごとに食い違う間は両方を並べて出す」も★自然に満たす。
★★★★`/api/control` を直す話は★していない（★読み手が違うため）。★直すなら別件。
```

---

# 4. ★次の1件（★S-3。★1件だけ・★私は依頼文を投入していない）

> ### **★人間用UIの4つの不足を、★2DER に作らせる。★依頼文に★契約（受入試験）を入れる。**

```
★§1-1 のとおり、★契約の無い依頼文は ★3周して `JUDGE_REQUIRED` で止まる ∴ ★契約は必須である。
★★受入試験に載せるもの（★`D-193` §2 から★機械で検証できるものだけ）:
   ★`def test_phase_list_has_japanese_title_and_status()` … フェーズ別一覧が出る
   ★`def test_filter_incomplete_only()`                   … 未完だけに絞れる
   ★`def test_summary_and_full_are_separate_fields()`      … 要約と全文が別欄
   ★`def test_page_shows_asof_and_source_ledger_ids()`     … いつ時点か・どの台帳ID由来か
   ★`def test_shows_both_counts_while_they_disagree()`     … 65 と 67 を両方 出す
★★訳す場所は ★表示時にする。★理由: ★登録時に訳すと ★原文が失われ、★機械側（英語・記号可）と
   ★人間側を分けるという Taka の指示に反する。★訳し直す条件＝ ★原文が更新された時。
★★★これは ★依頼文であって ★実装ではない ∴ ★私は書かない。★IMPL が front door から投入する。
```

---

# 5. ★これは A のどの数字を動かしたか（★1行で書く）
```
★★2DER だけで完了した工程: ★2段（観測・PLAN）→ ★★5種／実行6回（＋GENERATE・AUDIT・REGENERATE）
★Claude が介入しないと止まる工程: ★7段 → ★★1段（★再投入と押下のみ。★JUDGE_REQUIRED の裁定は残る）
★Claude の仕事: ★★減った（★中身を1文字も書いていない）
★一時的補助か永久か: ★★今回 足したものは ★0 ∴ ★永久化するものが無い
★2DER 主体率（★この一連）: ★★実行6回すべてが 2DER のアクター。★Claude は ★押下8回・生成0
```

---

# 6. ★やっていないこと
```
★gate にパッチを当てていない（★要らなかった）／ ★コードを1行も変えていない ／ ★commit していない
★S-3 の依頼文を投入していない ／ ★UI を自分で書いていない ／ ★測定を1本も足していない
★新しい台帳・新しい計器を作っていない（★増やした管理対象 0）
★★`D-191`（gate の意図調査）は ★Taka 指示で止まったまま ∴ ★やっていない
★★★止めたものはそのまま: 案C の測定 ／ 受入3 の採点 ／ Ledger ／ 図 ／ (c) patch
```

---
**決めたこと**: **①`D-189` の「同じ task を進める経路が存在しない」は誤りだった——同一依頼文を再投入したら task_id は同じまま `runnable: True` になり、新しい task は立たなかった。叩けば分かることを確かめずに書いた ②∴ `D-193` §3 の S-2（gate の最小パッチ）は要らない。在るもので通った ③再投入1回＋押下7回で GENERATE → AUDIT → REGENERATE → AUDIT → REGENERATE → AUDIT が動いた——本日 初めてで、Claude は中身を1文字も書いていない ④止まったのは `JUDGE_REQUIRED` で、理由は `SPEC_INCOMPLETE_NO_CONTRACT`＝依頼文に契約（受入試験）が無いこと。これが次に作るものである ⑤S-1(a) は「在るが配線されていない」——`set_status`/`register_amendment` は在るが webui は read-only でしか使わず、全14エンドポイントに書く口が0。繋ぐべきは `POST /api/submit` ↔ `set_status` の1本 ⑥S-1(b) も「在るが配線されていない」——`GET /` は既に日本語で台帳を出しており（先行研究は実在）、足りないのはフェーズ別一覧・絞り込み・要約/全文の分離・いつ時点かの4つだけ。∴ S-3 は「UI を作る」ではなく「4つを足す」 ⑦C-4 の 65 対 67 は、同じ台帳を一方は `roadmap_id` で絞り他方は絞らずに数えているため。差は別系列 `PHASE-2DER-AC-00〜03` の4フェーズで、欠損でも重複でもない。「いまどこか」の面では絞る側を正典とし、AC 系列は別ロードマップとして並べて出す ⑧S-3 の受入試験5本と「訳すのは表示時」の理由を固定した。依頼文の投入は IMPL。**
