# `rri/rri/rthread_events.jsonl` の役割確定 v0.1

**作成: Claude Code（MGR）／ 2026-08-23**
**指示: Taka 逐語「すぐ LEDGER_REGISTRY へ追記しない。まずこのファイルの役割を全件調査する。
writer / reader / owner / authority / 正本性 / 再生成可能性 / retention / integrity / resolve経路を確定し、
正式台帳なら登録／projection・cache なら正本との関係を登録。ここは明細システム再設計の基盤なので
局所修理として扱わない」**

## 0. 探した範囲（先に書く）

- `s10_ledger_registry.py` を **実際に実行**（`all_ledgers()` / `build()` を読み取り専用で）
- `request_thread.py` の全関数を走査（`_append` を呼ぶ関数の全数）
- 5 repo の `*.py` から `_append(` の module 外呼び出しを grep
- `/api/ledgers`（front door）と `all_ledgers()` の**集合差**を実測
- git の追跡状態・実体の行数/バイト数

---

## 1. ★根本原因の確定 — 「1 mismatch」の正体

状況表がこのセッション中ずっと出していた **「台帳登記 check: 1 mismatch(es) over 56 ledgers」** は、
**この台帳のことだった**。

```
母数 all_ledgers()          : 56件   ← rthread_events.jsonl を ★拾っている
登記簿 LEDGER_REGISTRY.jsonl: 55件
★母数に在るのに未登記        : ['rri/rri/rthread_events.jsonl']   ← ★これ1件だけ
★登記されているのに母数に無い : なし
```

**`build()` を走らせると 56行が作られ、rthread の行も作られる。**
∴ **コードの欠陥ではなく、登記簿ファイルが古い**（`s10_ledger_registry.py` を再実行していない）。

## 2. 9軸の確定

| 軸 | 確定 | 根拠 |
|---|---|---|
| **writer** | `rri/rri/request_thread.py` の **11関数のみ**（`open_thread` / `raise_question` / `annotate_question` / `propose_account` / `record_actor` / `record_typed` / `dispose_question` / `present_gaps` / `human_replied` / `advance_state` / `accept_thread`）。★**module 外からの `_append` 呼び出しは 0件** | 全関数走査＋5 repo の grep |
| **reader** | **8ファイル**（`webui` / `submit` / `ids` / `manager_v0` / `account_candidates` / `egl/structure` 2本 / regression 1本）。★すべて公開関数経由で、`_read` の module 外呼び出しは 0件 | importer 全数（別名 import 込み） |
| **owner** | `rri`（`request_thread.py` が docstring で **sole writer** を宣言） | 逐語「sole writer of rthread_events.jsonl」 |
| **authority** | 書き込みは **module の公開関数のみ**。`account_id` は chart に対し fail-closed、`disposal` は閉じた4語、`ACTOR_ACTIONS`/`ACTOR_VIAS` も閉じた列挙。★人の承認を要する経路は `approve_account`（別台帳） | ソース |
| **★正本性** | ★**SoR（正式台帳）**。逐語「**first-class store は event stream のみ(architecture)**」。`project()` の方が **projection（派生）** であり、`RTHREAD は projection(fat record を作らない=裁定#25)` はレコード形の話 | docstring 逐語 |
| **再生成可能性** | ★**再生成できない**。依頼文から明細を作り直すことは可能だが、`question_id` は `(thread_id, memo, ts, account_id)` の sha1 ∴ **ts が失われると同じ id を再現できない**。annotation / account 提案 / disposal / actor は**他のどこにも無い** | `_mint` の実装 |
| **retention** | ★**git 追跡下**（gitignore ではない）。実体 **3,338行 / 1.05MB**。append-only。★消してよい根拠は無い | `git ls-files` |
| **integrity** | ★**複式保存則が2本**: I1 `raised_total == resolved+open_gap+rejected+merged+in_flight`（`check_conservation`）／ I2 科目次元（`check_account_conservation`）。★違反は `RThreadConservationError` で halt | ソース＋実測（本日 OPEN_GAP 3件で釣ることを確認） |
| **resolve経路** | `ids.resolve("RTHREAD-…")` → `resolve_thread`（projection）／ `ids.resolve("Q-…")` → `resolve_question` + `next_action` + `recorded_by`。★**引ける** | 実測 |

## 3. ★判定

**正式台帳（SoR）である。** ∴ Taka 指示の「正式台帳なら登録」に該当する。

ただし登録の仕方に **2つの欠陥**が同時に出た。

### 欠陥A: `role` が `GOVERNANCE_LIVE` になる（本来 `CANONICAL`）
`build()` の実測:
```
liveness: LIVE   role: GOVERNANCE_LIVE
```
`ledger_role()` は **`CANONICAL_LEDGERS` という手書きの明示列挙**に無ければ CANONICAL にしない
（`s10_ledger_registry.py:210-217`）。この列挙に **rthread_events.jsonl が入っていない**。
∴ **明細の SoR が「小規模 live 台帳」に分類される。**

### 欠陥B: `readers: []` と判定される（実際は8ファイル）
`readers(base, writers)` は **basename をコード本文から grep** する実装（`:180-182`）。
`request_thread.py` は `_EVENTS` 変数経由で開くため、**読み手側のコードに `rthread_events.jsonl` の
文字列が現れない** ∴ 0件と出る。実測:
```
readers("rthread_events.jsonl", []) = ['rri/rri/request_thread.py']   ← 書き手自身しか出ない
```
★この穴は **rthread に限らない**（変数経由で台帳を開く全ての台帳に効く）。

## 4. ★局所修理にしない — 直す順序の提案

| # | やること | 種類 | 影響 |
|---|---|---|---|
| 1 | `CANONICAL_LEDGERS` に `rri/rri/rthread_events.jsonl` を足す | ★**手書き正本の変更**（Taka 裁定が要る） | 明細の SoR が CANONICAL として登記される |
| 2 | 登記簿を再生成（`s10_ledger_registry.py` を実行） | 再生成（べき等） | 55 → 56件。★「1 mismatch」が消える |
| 3 | 欠陥B（`readers` の穴）を別件として記録 | 調査 | ★rthread 以外にも効くので**単独で影響調査が要る** |

★**2 を先にやってはいけない**（role が `GOVERNANCE_LIVE` のまま固定されるため）。**1 → 2 の順**。
★3 は「明細システム再設計の基盤」ではないので、別の item として切り出す。

## 5. Taka 裁定が要る点

`CANONICAL_LEDGERS` は **手書きで維持されている正本の列挙**であり、
ここに1件足すことは **「何が本線の台帳か」の定義を変える**こと。
∴ 局所修理として私が勝手に足さない。**裁定をお願いします。**

---

## 6. ★訂正（2026-08-23・消さずに残す）

### 誤った報告
> 「状況表がこのセッション中ずっと出していた『台帳登記 check: 1 mismatch(es) over 56 ledgers』は、
> **この台帳のことだった**」（本書 §1 の当初の記述）

**★これは誤りだった。**

### 正しい事実（実測）
`s10_ledger_registry.py --check` の mismatch は **登記漏れの数ではなく、規律違反の数**である
（`main()` の実装: sole-writer 宣言違反 / live-read-but-no-writer / CANONICAL の writer 数）。

```
MISMATCH rri/rri/ambiguity_patterns.jsonl: live-read-but-genuinely-no-writer []
1 mismatch(es) over 56 ledgers
```

`over 56` の 56 は **`build()` が数えた母数**であって、登記簿ファイルの行数（55）とは**無関係**。
∴ **rthread の登記では mismatch は 0 にならない**。変更前も後も同じ1件。

### なぜ間違えたか
`56` と `55` という2つの数の差が1であったことと、`mismatch 1` の 1 を**同じ原因に帰属させた**。
★数が一致しただけで因果を結んだ（[[numbers-need-their-key]] の型 ―― ★鍵が違う数を突き合わせた）。

### ★受入条件の訂正（Taka 裁定 2026-08-23）
取り下げ: ~~mismatch 1 → 0~~

| 訂正後の受入条件 | 実測 | 判定 |
|---|---|---|
| LEDGER_REGISTRY 55 → 56 | **55 → 56** | ✅ |
| `rri/rri/rthread_events.jsonl` role = CANONICAL | **CANONICAL** | ✅ |
| `production_writer_count` = 1 | **1**（既存 CANONICAL 12件と同じ形） | ✅ |
| 既存55台帳に意図しない属性変化なし | **変化2件のみ**: `event_trace` の `rows` 再計測／rthread 自身 | ✅ |
| **rthread 追加による新規 mismatch = 0** | **0**（mismatch は変更前と同一の1件） | ✅ |

### 分離した別 AXIS（今回に混ぜない）
1. **reader 検出器の欠陥** — `readers()` が basename を本文 grep する実装。
   ★変数経由で開く全系統に効く。★次 AXIS で**偽陰性・偽陽性を分母つきで**測る
2. **`ambiguity_patterns.jsonl` の `live-read-but-genuinely-no-writer`** — 今回と無関係の既存 mismatch

### Taka の観察（逐語・記録として残す）
> 「今回かなり典型的な ESDE の効き方になっています。最初の因果帰属は誤っていたけれど、
> 分母・別軸・作用を切り分けたことで、**未登記問題 / reader 検出問題 /
> ambiguity_patterns の writer 欠損** が別の存在として分離できた。」

## 7. 実施結果（②③）
```
② s10_ledger_registry.py --apply → wrote LEDGER_REGISTRY.jsonl (56 ledgers)
③ /api/ledgers → 件数 56 ／ rthread: role=CANONICAL / liveness=LIVE / rows=3341
   role 内訳: CANONICAL 13(+1) / REPLICA 9 / IDLE 11 / INSTANCE_STORE 7
              / EXPERIMENT_RESIDUE 11 / GOVERNANCE_LIVE 3(-1) / SHIPMENT 2
```
