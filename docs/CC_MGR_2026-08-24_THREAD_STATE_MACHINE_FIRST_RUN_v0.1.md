# thread 状態機械の本番初回実行 v0.1 — 明細の結果を thread へ返す経路

**作成: Claude Code（MGR）／ 2026-08-24**
**裁定（逐語）: 今回の本質は present_gaps の未配線ではなく、thread状態遷移が本番で一度も実行されていないこと。
既存644 threadがすべてSOFTである点を正本の現状として扱う。新state・新event type・新IDは追加しない。**
**完了条件（逐語）: ED65242Eの完了条件は「RESOLVEDにすること」ではなく、
thread状態機械が本番で正しく動き、未解決が残るため正しく止まることとする。**

---

## 0. 実装前の全件調査（8項目）

| # | 項目 | 実測 |
|---|---|---|
| ① | `present_gaps` | writer=`request_thread` のみ／**reader 0**／**本番 caller 0**／**authority 無し**／**fail-closed 条件 0**（引数を1つも検査せず append していた） |
| ② | `THREAD_ACCEPTED` | producer=`accept_thread`（**本番 caller 0**）／consumer=`advance_state` の RESOLVED guard のみ／条件＝全 OPEN_GAP を `DECLINED`/`TRANSFERRED` で網羅列挙 |
| ③ | thread 状態を決める関数 | `project`(status)／`advance_state`／`TRANSITIONS`／`resolve_thread`。**状態を動かす5関数すべて本番呼び手0**。本番呼び手があるのは `open_thread` と `raise_question` の2つだけ |
| ④ | 処分の反映 | `in_flight_count`（処分イベントを持たない数・独立導出）と `open_gaps` に効く。`RESOLVED`/`REJECTED`/`MERGED_INTO` は**同じく in_flight を減らすだけで区別されない**。`OPEN_GAP` だけが `present_gaps` 必須という追加条件を持つ |
| ⑤ | `ds_delivery_receipt` | **正本なし・schema なし・consumer なし・検査なし**。`/api/receipt` は front door の投入受領で「1件ごとには答えられない」と明記＝**別物** |
| ⑥ | TASK 側へ返すもの | `manager_v0.py:790-815` が既に `resolve_thread` を引き `question_counts`／`open_gaps` を載せている。**`unresolved_question_ids` だけが「RRI に口が無い」で UNKNOWN** |
| ⑦ | 重複する口 | **無い**。`dev-workcell` は `request_thread` を1行も読まない。DW 完了門9件（`STATE_NOT_COMPLETABLE`〜`LINKAGE_EDGE_NOT_OBSERVED`）に RRI 由来は0。橋は `twoder` だけ |
| ⑧ | 既存機構で閉じるか | **閉じられた**。新 state / event type / ID は**1つも足していない** |

### 0.1 ★最大の発見

```
644 thread の 状態 : {'SOFT': 644}   ← ★STATE_ADVANCED が本番に0件
明細 988 / 割当済み 27 / 処分済み 5   （27・5 はすべて 2026-08-23 に入れた分）
```

`present_gaps` が未配線なのではなく、**thread の状態遷移そのものが本番で一度も実行されていなかった。**

---

## 1. ① RRI に thread 集約の読み口を追加

`rri.request_thread.thread_summary(thread_id)` — **読むだけ**。

**★差集合を新しく作っていない。** `manager_v0` の逐語は
「★raised から resolved を 引いて 作れば それは ★私の 新しい 規則 ∴ ★作らない」だったが、
`project()` が既に使っている定義（逐語「処分イベントを持たない raised 問いの数(残差でなく独立導出)」）で
**数の代わりに id を返しているだけ**である。一致は試験で固定した
（`len(unresolved_question_ids) == project()["in_flight_count"]`）。

返り: `unresolved_question_ids` / `disposals`（明細ごとの処分内訳）/ `open_gap_ids` /
`presented_ids` / `unpresented_open_gap_ids` / `accepted` /
`can_advance_to_resolved` / `blocked_by` ＋ 分母（`raised_total` ほか）。

`blocked_by` の `text` は **`advance_state` の逐語をそのまま**使う（新しい文言を作らない）。

---

## 2. ② `present_gaps` を fail-closed 化

検査するのは**3つだけ**:

1. `question_ids` が空でない
2. そのすべてが**この thread で実際に `OPEN_GAP` 処分された明細**である
3. `ds_delivery_receipt` が空文字列/None でない

**★`ds_delivery_receipt` の意味・schema・consumer は定義していない**（裁定どおり別 AXIS）。
正本が無いものの中身をここで決めると語彙の発明になるため、**空だけを弾く**。
試験 `test_receipt_semantics_are_not_defined_here` が「空でなければ何でも通る」ことを固定している。

**本番 thread で実際に拒否させた:**

```
空の一覧              -> ★拒否 present_gaps requires at least one question_id
受領が空              -> ★拒否 ds_delivery_receipt must not be empty
OPEN_GAP でない明細   -> ★拒否 not OPEN_GAP in this thread: ['Q-9d3f4bb0'] (open_gap=[])
```

直す前は**提示していない明細を提示済みにでき、受領が空でも通った**（`advance_state` の門は
`GAP_PRESENTED` が在るかだけを見る）。

---

## 3. ③ ED65242E で `SOFT → NARROWING`（既存遷移表の正規経路）

**★裸の `True` を証拠にしていない。** guard の中身は TRACE に実在する値をそのまま刻んだ。

| guard | 刻んだ値 | 出所 |
|---|---|---|
| `request_type_ok` | `MODIFY_EXISTING` ＋ basis | `TRACE.rri.resolved_intent`（`rri.request_resolution`） |
| `bind_context_ok` | `residual=PROVISIONAL…` / `anchoring=MEDIUM` | `twoder/submit.py:277 rri.context_binding.bind_context` |

`PROVISIONAL` は**正規のモード**である（`context_binding` の規律 GAP-DS-3＝短会話に構造を被せない）。
`anchoring` は `UNRESOLVED` ではなく `MEDIUM` ∴ binding は成立している。

```
遷移前 status: SOFT  →  ★遷移後 status: NARROWING
```

**644 thread のうち、本番で状態遷移が起きたのはこの1本が初めて。**

---

## 4. ④ 未解決が残る限り完了しない（実測）

```
status=NARROWING  raised=27 resolved=2 in_flight=25
★証拠つき2件が RESOLVED : ['Q-19be9e79', 'Q-9d3f4bb0']
★残り25件を未解決として保持 : 25件（★unresolved_question_ids と in_flight_count が一致）
can_advance_to_resolved : False
   IN_FLIGHT_REMAINS        RESOLVED requires in_flight_count==0 (got 25)
   THREAD_ACCEPTED_MISSING  THREAD_ACCEPTED required for RESOLVED

★実際に advance_state(RESOLVED) を試した -> RThreadIllegalTransition で拒否
★保存則 I1 : 27 = resolved2 + open_gap0 + rejected0 + merged0 + in_flight25
★保存則 I2 : 例外なし（起票時・割当後の両側）
★QUESTION_RAISED を書き換えていない : per_account_balances == {'UNCLASSIFIED': 27}
```

---

## 5. ⑤ TASK 側は既存 `manager_v0` の集約を使う（DW には触れていない）

`manager_v0.item_state` が「口が無い」で UNKNOWN にしていた欄を、今回の読み口で埋めた。
**引けない時は従来どおり UNKNOWN**（「無い」と「引けなかった」を混ぜない）。

実際に `ITEM-2DER-EVO-0082` で通した（ED65242E は**どの ITEM にも属していない**ため別 item で実証）:

```
TASK-2DER-616AC70A  unresolved_question_ids 6件 / thread_can_advance false
                    thread_blocked_by [IN_FLIGHT_REMAINS, THREAD_ACCEPTED_MISSING]
TASK-2DER-81F60030  4件 / false
TASK-2DER-8F857A27  5件 / false
出所: rri.request_thread.thread_summary.unresolved_question_ids
```

**`dev-workcell` には1バイトも触っていない**（DW→RRI は層違反）。

---

## 6. ★自分の計器を2回疑って直した

1. `item_state` の返りを `st["task_details"]` で読んで「0件」と出した → **実際は `st["fields"]["task_details"]`**。
   **コードではなく私の読み方が壊れていた**（3件ある）。
2. 試験が**実行順に依存して落ちた**。原因を2回誤診（環境変数の設定位置 → module 属性）してから、
   失敗の中身を実際に読んで確定: **`test_question_evidence.py` が `os.environ.setdefault` を使っていたため、
   別 file が先に置いた chart の path を掴み、その file の chart を上書きしていた**。
   ∴ 各 file 固有の変数に控え、書き込みも自分の path へ行うようにした。
   **順序を3通り変えて全通過することを確認**（a b c / c b a / b a c）。

---

## 7. 触っていないもの

- `EVENT_TYPES` / `STATES` / `DISPOSALS` / `TRANSITIONS` / `UNCLASSIFIED_FORBIDDEN_DISPOSAL`
- `accept_thread` / `human_replied` / `advance_state` の判定ロジック
- `QUESTION_RAISED` / `per_account_balances` / `suspense_balance`
- `dev-workcell` 全体 ／ `webui.py`（担当が別インスタンス）
- ED65242E 以外の 643 thread（**1本も遷移させていない**）

## 8. 別 AXIS へ送るもの

1. **`ds_delivery_receipt` の意味・schema・consumer**（裁定どおり今回の完了条件に含めない）
2. **`accept_thread` を誰が呼ぶか** ―― `THREAD_ACCEPTED` は「人間の扉」であり、
   本番の呼び手を作るには authority の設計が要る。**未着手**
3. **front door のプロセス劣化が再発**（別担当の管轄）。実測:
   再起動直後 `task_index` **0.49秒** ／ 1時間稼働後 **88秒**。
   口ごとの増分は `/` +8MB・`/api/etrace` +0MB・`/api/rthread` −6MB で、
   **2026-08-23 に潰した 782MB 丸読みとは別の原因**。時間の経過とともに劣化する。
4. **ED65242E がどの ITEM にも属していない**（150 item 中 task_ids を持つのは6件のみ）

## 9. 試験

`rri` 70本 ＋ `twoder` 53本 ＝ **123本 全通過**（新規14本）。
順序を3通り変えても同じ結果になることを確認済み。
