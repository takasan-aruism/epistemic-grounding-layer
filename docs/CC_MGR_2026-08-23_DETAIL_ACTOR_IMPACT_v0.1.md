# 影響調査 ①: 明細の台帳に「誰が書いたか」を残す

## A. 読み手の全数（QUESTION_TYPED / QUESTION_DISPOSED）

| # | 場所 | 何を読むか | 欄が1つ増えたら |
|---|---|---|---|
| 1 | `rri/request_thread.py:217` `list_typed` | 固定キー列 | ★落ちる（読む欄に足さないと出ない） |
| 2 | `rri/request_thread.py:253` `list_questions` | disposal/reason_code/target_id/ts | ★落ちる（同上） |
| 3 | `rri/request_thread.py:340` `advance_state` guard | question_id / disposal | 影響なし |
| 4 | `rri/request_thread.py:360` `accept_thread` guard | question_id / disposal | 影響なし |
| 5 | `rri/request_thread.py:389` `project` | disposal で数える | 影響なし |
| 6 | `egl/docs/audit_rthread_stage1.py:99,100` | question_id | 影響なし |
| 7 | `twoder/webui.py rthread_view` | list_typed / project の戻り | 1 経由 |

★事象の「欄の集合」を検査する仕組みは **存在しない**（探した範囲: `rri/rri/*.py`、`egl/docs/audit_rthread*.py` の
`set(e.keys())` / `schema` / `allowed_keys` / `REQUIRED_KEYS`）。∴ **欄を足しても既存の読み手は壊れない**。

## B. ★署名の逐語照合（これが制約）

`egl/docs/audit_rthread_stage1.py:44-54` が **source の文字列**として照合している:

```
"def dispose_question(thread_id, question_id, disposal, ts, reason_code=None, target_id=None):"
"def raise_question(thread_id, memo, ts, account_id=\"DEFAULT\"):"
```

∴ **`dispose_question` / `raise_question` に引数を足してはならない**（足すと監査の FAIL が増える）。

## C. baseline（★私の変更の前から壊れている）

| 監査 | 結果 | 中身 |
|---|---|---|
| `audit_rthread_stage1.py` A | **FAIL(1件)** | `raise_question` の署名が `account_id="DEFAULT"` から `UNCLASSIFIED` へ乖離（過去の変更） |
| 同 B | PASS | 5 passed |
| 同 C | **例外で停止** | `ValueError: off-chart account_id 'DEFAULT'` |
| `audit_rthread_stage2a.py` | **CONSISTENT** | A/B/C1/C2/D1/D2 全 PASS |

★この2件は **私が壊したものではない**。変更後も「FAIL 1件・同じ文言」であることを確認する（増えたら私のせい）。

## D. 決めたこと

1. **既存の書き手の署名を1バイトも変えない** ∴ 引数で actor を渡さない
2. **`ACTOR_RECORDED` を1つ足す**（`QUESTION_ANNOTATED` / `QUESTION_ACCOUNT_PROPOSED` /
   `QUESTION_TYPED` を後から足したのと同じ作法。`EVENT_TYPES` の定数は触らない）
   - 欄: `type / thread_id / ref_id / ref_type / actor / action / via / ts / sealed_by`
   - `via` = `front_door` / `direct`（★横から書いたことを隠さない）
3. 読み手 `list_typed` / `list_questions` に **actor を join** して返す
4. 既に書いた 33件＋3件は **追記で名乗り直す**（消さない）

## E. 事前に潰すエラー

| 起きうる事 | 潰し方 |
|---|---|
| `actor` が空で呼ばれる | ValueError（fail-closed。★『誰か分からない』を作らない） |
| `ref_id` が実在しない | 呼び手が確かめる。実在しなければ ValueError |
| `action` が自由文字列で揺れる | ★閉じた列挙にする（`STRUCTURE` / `DISPOSE` / `RAISE` / `ANNOTATE`） |
| 同じ ref_id に2回 | append-only。★最後の行が効く（他の読み口と同じ作法） |
| 既存の読み手が壊れる | A 表のとおり 3〜7 は影響なし。1・2 は読む欄に足す |
| 監査の FAIL が増える | 変更後に stage1/stage2a を再実行し、C の baseline と一致することを確認 |

## F. 試験の順（★一つずつ・全部作ってからテストしない）

1. `ACTOR_RECORDED` の書き手＋読み手だけ作る → 単体試験
2. **1件だけ** 通す（ED65242E の typed 1件に actor を付ける）→ 破綻がないか
3. stage1 / stage2a を再実行 → baseline と一致するか
4. front door（`/api/rthread`）が壊れていないか
5. 合格したら 33件＋3件へ広げる

---

## G. 実施記録（★一つずつ・各段で確認した実測）

### 段①-1: 書き手＋読み手だけ作る → 単体試験
- 足したもの: `rri/rri/request_thread.py` に `record_actor()` / `actors_of()` / `ACTOR_ACTIONS` / `ACTOR_VIAS`
- ★既存の書き手の署名は **1バイトも変えていない**（`dispose_question` / `raise_question` / `EVENT_TYPES`）
- 試験 `rri/rri/test_actor_recorded.py` **9本 全通過**
  - 空の actor / 未登録の action / 未登録の via / 空の ref_id を **ValueError で拒否**（fail-closed）
  - 同じ ref_id は最後の行が効く
  - ★複式保存則に1件も混ざらない（`project()` が前後で完全一致）
  - ★既存の署名が source に在ることを試験で固定

### 段①-2: baseline と一致するか（★私が壊していないことの確認）
| 監査 | baseline（変更前） | 変更後 | 判定 |
|---|---|---|---|
| `audit_rthread_stage1.py` A | FAIL 1件（`raise_question` の署名乖離） | **FAIL 1件・同じ文言** | 一致 |
| 同 B | PASS 5 passed | **PASS 5 passed** | 一致 |
| 同 C | 例外で停止（off-chart 'DEFAULT'） | **同じ例外** | 一致 |
| `audit_rthread_stage2a.py` | CONSISTENT（A/B/C1/C2/D1/D2 全 PASS） | **CONSISTENT** | 一致 |

★stage1 の FAIL と例外は **私の変更の前から在るもの**（過去に `account_id="DEFAULT"` → `UNCLASSIFIED`
へ変えた際に監査側が追随していない）。**今回それを増やしていない**。

### 段①-3: 1件だけ通す（★全部作ってからテストしない）
```
前  明細 33 ／ 名乗り 0 件 ／ 複式 raised 27 / resolved 0 / open_gap 0 / in_flight 27
後  明細 33 ／ 名乗り 1 件 ／ 複式 raised 27 / resolved 0 / open_gap 0 / in_flight 27
    QT-be82a703 → actor=claude-mgr / action=STRUCTURE / via=direct
★複式は完全一致 ／ ★明細の件数も不変
```

### 段①-4: front door が壊れていないか
```
ED65242E  readable=True 明細27 構造化33 未解決0
EF6826DC  readable=True 明細13 構造化 0 未解決3
0C458F38  readable=True 明細 0 構造化None 未解決0
task_index 593件 / 完了88
twoder の試験 33本 全通過 ／ rri の新試験 9本 全通過
```

## H. まだやっていないこと（次の1件ずつ）

1. 既に書いた **33件（構造化）＋3件（OPEN_GAP）** に名乗りを付ける（いまは1件だけ）
2. `list_typed` / `list_questions` に actor を join して返す
3. front door と画面に「誰が書いたか」を出す
4. ②front door の口を作り、直接呼びをやめる（★例外経路は残して記録する＝Taka 裁定）

### 段①-5: 読み手に actor を join
- 影響の全数調査: `list_typed` / `list_questions` の読み手は **`twoder/webui.py` の2箇所だけ**。
  戻り値を辞書比較で固定している試験は **無い** ∴ 欄を足しても壊れない
- `recorded_by` / `recorded_via` を join。★名乗っていなければ **`None`**（空文字や既定値で埋めない）
- 試験を2本追加 → **11本 全通過**
- ★webui は起動時の rri を掴むため **再起動が要る**（再起動前は 0件に見えた＝バグではない）

### 段①-6: 既存の記録に名乗りを付ける（★追記＝不可逆）
```
RTHREAD-4d89c66c [typed]     名乗り 1 → 33 (付けた 32件)  複式が動いていないか: True
RTHREAD-e6f77617 [disposed]  名乗り 0 →  3 (付けた  3件)  複式が動いていないか: True
```
すべて `actor=claude-mgr` / `via=direct`。★**横から書いた事実をそのまま記録**した（隠さない）。

### 段①-7: 画面に出す
- 構造化の表に **「誰が書いたか」** 列。`via=direct` は **★横から(direct)** と赤で出す
- 要約行に `名乗りあり 33件（うち ★横から書いた 33）`
- 旧明細の表にも「誰が書いたか」列
- 実測: `構造化33 ／ 名乗りあり33 ／ うち横から33` ＝ **これまでの構造化は全部 Claude が横から書いた**と
  画面から読める状態になった

### 段①-8: 最終確認（baseline と一致）
| | 結果 |
|---|---|
| `audit_rthread_stage1.py` | **FAIL 1件・同じ文言**（baseline と一致） |
| `audit_rthread_stage2a.py` | **CONSISTENT**（baseline と一致） |
| `rri/test_actor_recorded.py` | 11本 全通過 |
| `twoder/regression/` 3本 | 33本 全通過 |
| front door | 3 task とも `readable=True` |

## I. 段① 完了。次は段②（front door の口）

★段②の目的= ★`via=direct` を **0 に近づける**（横から書くのをやめる）。
★Taka 裁定=「②③はそんな感じ。**例外処理として残しておくべき**」∴ **direct の経路は消さない**。
  残したうえで **記録に残す**（いまの `via` がその役目）。

---

## J. ★今回の全件調査の反省（Taka 指摘 2026-08-23）

**私の失敗**: `ACTOR_RECORDED` を足す前に `grep "QUESTION_TYPED|QUESTION_DISPOSED"` で
「**その2つの型を読む場所**」だけ調べ、「全件調査した」と報告した。
★新しい型は **どの型フィルタにも掛からない** ので、危険面はそこではない。

**Taka 逐語**:
> 新しい event type を追加する際の調査対象は「その type 名を読む場所」ではなく、
> **その event collection を type 非限定で読む全 consumer**。今後はここを事前チェック項目にする。

### 事前チェック項目（今後これを通す）
```
①その event collection を読む口を全部出す（ファイル直読・読み関数の呼び手をモジュール内で全数）
②そのうち ★type で絞っていない ものを名指しする ← ★ここが本命
③importer を ★別名 import 込みで全数（`from x import y as _Y` は名前 grep に掛からない）
④返却 schema を変える時は ★その read surface の consumer も全件
   ★同じ物を引く口が2つ在れば ★両方直す（片肺にしない）
⑤既存の読み手が ★同じ数を返すか実測（型が混ざっていないか）
⑥その台帳が ★LEDGER_REGISTRY に登記されているか（未登記なら計器が見ていない）
⑦変更前に ★baseline を取り、変更後に ★増えていないことを照合
```

### やり直した全件調査の結果（2026-08-23）
| 調べたこと | 結果 |
|---|---|
| `rthread_events.jsonl` を**直読**するコード | **0件**（全部 `_read` 経由。試験は一時ファイルへ退避） |
| `request_thread` 内で **type 非限定**に event を回す関数 | 2つ（`_read` / `resolve_thread`）。どちらも中で `project()` に渡すだけで安全 |
| `request_thread` の importer | **8ファイル**（前回は6件しか見ていなかった）。追加2件は `egl/structure/s_ledger_account_axes.py` と `..._axis_names.py`＝`list_account_proposals()` 経由（type 絞りあり）で安全 |
| 既存の読み手が同じ数を返すか（実測） | `list_account_proposals` = **645件** = `QUESTION_ACCOUNT_PROPOSED` と完全一致。**新 type は混ざっていない** |
| ★前回の Explore 報告の誤り | `twoder/question_review.py` が明細を読むと報告されていたが、**実際は読んでいない**（`route_edge_vote` を読む）。★別インスタンスの報告を鵜呑みにしていた |

---

## K. 段①-9: read surface の片肺を直す（Taka 指示 ①）

### 実装前の consumer 全件（`ids.resolve`）
| consumer | 戻り値の使い方 | 欄が増えたら |
|---|---|---|
| `twoder/detail_refs.py:45` | `is None` のみ | 影響なし |
| `twoder/dispatch_provenance.py:61` | `is None` のみ | 影響なし |
| `twoder/build_planner.py:119` | `OBS-` の `acquisition_run_id` | Q- を触らない |
| `twoder/experiment_candidate.py:233` | finding/source id | Q- を触らない |
| `twoder/webui.py:1087` `/api/resolve` | JSON でそのまま返す | 追加のみ＝安全 |
| `twoder/regression/test_dispatch_provenance.py` / `test_forward_admission.py` | 存在確認のみ | 影響なし |

★**戻り値の欄の集合を固定している consumer は 0件**（探した範囲＝上の全 importer と呼び出し箇所）。

### 実装
`twoder/ids.py` の `Q-` 分岐に `recorded_by` / `recorded_via` を足した。
★作法は**同じ分岐に既に在る先例** `next_action` に合わせた ―
「★名乗りが在る時だけ足す（★空の欄を作らない）／★組み立ては twoder 側（rri の戻りを書き換えない）」。

### 実測
```
名乗り済み Q-8e44cc36 → recorded_by=claude-mgr / recorded_via=direct   欄=あり
名乗り無し Q-e42a1f3c → 欄=★無い（空の欄を作らない）
front door /api/resolve?id=Q-8e44cc36 → recorded_by: claude-mgr
```
| 確認 | 結果 |
|---|---|
| `test_dispatch_provenance.py`（script） | **11/11 passed** |
| `audit_rthread_stage1.py` | FAIL 1件・同じ文言（baseline 一致） |
| `audit_rthread_stage2a.py` | CONSISTENT（baseline 一致） |
| `rri/test_actor_recorded.py` | **12本 全通過**（★両口が同じ答えを返すことを試験で固定） |

## L. 付随して見つかった件（今回は直さない・記録のみ）
- `ids.all_resolve(['ART-e8dfcab57d'])` → **unresolved**。
  `CC_REGISTER` の `doc_id`（ART-）と `artifact_registry` の ART- が**別の id 空間**で、
  ★前者は `ids.resolve` で引けない。★「登記した＝引ける」ではない。
