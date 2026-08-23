# 段5-②③ — 既存明細への科目割当と `dispose_question` の修理 v0.1

**作成: Claude Code（MGR）／ 2026-08-23**
**裁定（逐語）: 1.既存明細へ科目割当eventを追加する書き手を作る 2.projectionで effective_account_id を出す
3.dispose_question をその値を見るようにする 4.まず ED65242E 1 thread だけで UNCLASSIFIED → 割当 → RESOLVED
→ 保存則維持 を実走 5.通ったら既存974件への遡及範囲を測る**
**前提: 段5 構造判定（`ART-9aff0cedf4`）の欠落②③／chart 採用（`ART-4edb08ed44`）で欠落①は解決済み**

## 0. 着手前の全件調査

projection の欄を名指しで読む場所を5repoで全件（`per_account_balances` / `suspense_balance` /
`in_flight_count` / `raised_total` / `project(`）。

**全consumer が「名前で読む」だけで、欄の集合を厳密比較する場所は無い** ∴ 欄の追加は安全。
（`twoder/task_overview.py`・`twoder/manager_v0.py`・`webui.py`・`egl/docs/audit_rthread_*`・各試験を確認）

`advance_state` の逐語も確認した ―― `suspense_balance` は**門ではない**
（「suspense 決着は in_flight==0 に包摂される(独立 guard 不要=F-2)」）。

---

## 1. ★既存の数を1つも動かしていない

`per_account_balances` と `suspense_balance` は**起票時の値で数えたまま**にした。
理由は逐語「byte-identical・DERIVED」＝**監査がこの数で照合している**ため。

割当を反映した数は**別の欄**で出す（同じ名前に別の意味を入れない）:

| 欄 | 意味 |
|---|---|
| `per_account_balances` | ★**起票時**の科目で数えた（従来どおり） |
| `suspense_balance` | ★**起票時** UNCLASSIFIED かつ未処分（従来どおり） |
| `effective_account_ids` | {question_id: **いま載っている**科目} |
| `per_effective_account_balances` | 割当を反映した内訳 |
| `suspense_balance_effective` | 割当を反映した未分類 |
| `assigned_count` | 割当 event を持つ明細の数 |

**I2（科目次元）は割当側にも掛けた**（片側だけ検査すると抜け道になる）。
`check_account_conservation` も割当側の off-chart を弾く。
どちらも**欄が在る時だけ見る**ので、古い projection でも落ちない。

---

## 2. ★出口規則そのものは緩めていない

`dispose_question` の変更は**見る値だけ**である。

```
直す前: QUESTION_RAISED の account_id（最初の1件で break）
直した後: effective_account_of() ＝ 起票時の値に割当を上書きしたもの
```

「分類されていない問いを解決済みにするな」という規則は**そのまま**。
**割当が1件も無ければ従来と完全に同じ値**になる。

封印試験で固定した:

| 試験 | 内容 |
|---|---|
| `test_gate_still_refuses_a_genuinely_unclassified_question` | 割当が無ければ RESOLVED は**拒否** |
| `test_gate_opens_only_after_an_assignment` | 割当の後だけ通る |
| `test_gate_closes_again_if_assigned_back_to_unclassified` | UNCLASSIFIED へ戻すと**また閉じる** |
| `test_other_disposals_are_unchanged_for_unclassified` | OPEN_GAP/REJECTED/MERGED は元から通る＝**触っていない** |
| `test_raise_time_value_is_never_rewritten` | `QUESTION_RAISED` を上書きしない（append-only） |
| `test_sealed_constants_are_untouched` | `EVENT_TYPES`/`DISPOSALS`/`UNCLASSIFIED_FORBIDDEN_DISPOSAL` |

### 2.1 既存監査の失敗は本件と無関係（切り分け済み）

`egl/docs/audit_rthread_stage1.py` の selftest_C が `ValueError: off-chart account_id: 'DEFAULT'` で落ちる。
**変更前の版と変更前の chart(5件)を隔離して同じ呼び出しを実行し、同一の失敗を確認した**（既存事象）。
最初 `PYTHONPATH` で切り分けようとしたが**上書きが効いておらず同じ実体を読んでいた**ので、
モジュールを直接ロードし直して測り直した。

---

## 3. 足したもの（`rri/rri/request_thread.py`）

- `assign_account(thread_id, question_id, account_id, ts, basis=…, recorded_by=…, recorded_via=…)`
  → event `QUESTION_ACCOUNT_ASSIGNED`。chart に無い id は `ValueError`（`raise_question` と同じ規律）。
  **`UNCLASSIFIED` へ戻す割当も許す**（誤りを取り消せる道を塞がない）。決定論 id。**最後の行が効く／履歴は消さない**
- `effective_account_of(thread_id)` / `list_assignments(thread_id, question_id=None)`
- `list_threads()` / `count_questions()` — ★**分母を作るための読み**（下記 §5 の理由）

---

## 4. ★ED65242E で実走した（本番の台帳）

```
割り当てた                        : 27 / 27 件
  LDET-68ad5c78 アカウント選択ロジック 11 ／ LDET-ae01943f 書籍名検証 8
  LDET-b2c8842a ステータス検証ルール  3 ／ LDET-2e0002c3 ステータス 2
  LDET-a5e121fc 関数実装 1 ／ LDET-dc8bc11f ファイルパス検証 1
  ★LDET-15a929ca（命名未確定）      1  ← Q-865c8458
★未分類  起票時 27 → ★割当後 0
★保存則  I1/I2 とも例外なし（★割当側にも掛けた）
```

### 4.1 RESOLVED は★根拠が付いた明細だけに限った

**無根拠に「満たされた」と書かない**ため、段4 で証拠を記帳した2件だけを処分した。

```
Q-9d3f4bb0 (#4 FACT・根拠 QE-9c0f0460)      -> ★RESOLVED 通った
Q-19be9e79 (#13 CONSTRAINT・根拠 QE-7cc9e60b) -> ★RESOLVED 通った

raised=27 resolved=2 open_gap=0 rejected=0 merged=0 in_flight=25
★I1 恒等式 raised == resolved+open_gap+rejected+merged+in_flight : True
★I2 例外なし（両側）
```

**残り25件は意図的に処分していない**（満たされたと言える根拠がまだ無いため）。

### 4.2 門が緩んでいないことを本番と同じ chart で確認

```
割当の無い明細 + RESOLVED -> ★拒否（UNCLASSIFIED question cannot be disposed as RESOLVED）
```

---

## 5. ★遡及範囲（真の分母で測った）

**分母が所有APIから引けなかった。** `list_account_proposals` は**提案を持つ明細しか返さない**（649件）。
∴ 「返せない」が結果であり、それが次に作る読み口である ―― として `count_questions()` / `list_threads()` を足し、
**986件**という真の分母を得た。

| | 実測 |
|---|---|
| 依頼(thread) | **642** |
| 明細（真の分母） | **986** |
| ★2層モデルが科目を出せる | **644（65%）** |
| ★その科目が chart に在る＝**いま割り当てられる** | **644（65%）** |
| ★遡及できない | **342（35%）** |
| 1件でも割り当てられる依頼 | **353 / 642** |
| ★1件も割り当てられない依頼 | **289** |
| 命名未確定の科目に入る明細 | **11**（科目1本 = `LDET-15a929ca`） |

**遡及できない342件の理由**: 2層モデルの corpus は `list_account_proposals`（649件）であり、
**科目提案を持たない明細はそもそも分類されていない**。289本の依頼がまるごとこれに当たる。

※ 前回まで「明細974件」と書いていたが、所有API で数え直すと **986件**。
以後の分母はこちらを使う（974 は台帳を直読していた頃の数）。

---

## 6. 触っていないもの

- `QUESTION_RAISED` の値／`per_account_balances`／`suspense_balance`
- `EVENT_TYPES` / `DISPOSALS` / `UNCLASSIFIED_FORBIDDEN_DISPOSAL` / `STATES` / `TRANSITIONS`
- `present_gaps` / `advance_state` / `approve_account` / `account_gate.decide`
- ED65242E 以外の 641 thread（**1件も割り当てていない**）
- `webui.py`（担当が別インスタンス）

## 7. 残っているもの

| 欠落 | 状態 |
|---|---|
| ① chart に58科目が無い | ★解決済み（`ART-4edb08ed44`） |
| ② 既存明細へ科目を書き戻す書き手 | ★**解決済み（本記録）** |
| ③ `dispose_question` が初期値しか見ない | ★**解決済み（本記録）** |
| ④ `present_gaps` の本番呼び手が0件 | **未解決**（DS 管轄）。∴ **thread 全体は RESOLVED 状態へ進めない** |

**明細1件ごとの RESOLVED は通るようになったが、thread を RESOLVED 状態へ進めるには
`present_gaps` と `THREAD_ACCEPTED` が要り、どちらも本番の呼び手が無い。**

## 8. 未確認

- 遡及の実行（644件への一括割当）は**していない**。ED65242E の27件のみ。
  一括するかは、誤割当の取り消し手順（`UNCLASSIFIED` へ戻す）を含めて別途決める
- 342件を分類に載せるには `propose_account` を回すか、2層モデルの corpus を広げる必要がある。**未着手**
- `dispose_question` は**二重処分を検出しない**（既存の F-1 指摘）。RESOLVED を誤って付けた場合の
  取り消し手順は無い ∴ §4.1 で根拠のある2件に限った
