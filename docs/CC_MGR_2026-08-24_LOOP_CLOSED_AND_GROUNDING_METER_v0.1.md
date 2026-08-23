# 2条件の決着 — 自動循環の書き込み実証と、根拠/発明の決定論的計器 v0.1

**作成: Claude Code（MGR）／ 2026-08-24**
**裁定（逐語・要点）: 1.threadあり＋未記帳runありのTASKを軽量に1件抽出し、常駐が手呼びなしでEvidenceを書き、
次PLAN入力まで戻ることを確認する 2.PLAN内のTEST/SPEC等を明細側と対応づけ、根拠あり／根拠なしを数える。
★LLM出力文章の一致率を評価基準にしない。effectがノイズ床を越えた場合だけ「有効」とする**

---

## 1. ★条件1 — 閉じた

### 1.1 軽量抽出（15分で終わらなかった探索 → 2.0秒）

`detail_feedback.scan_unrecorded()`。**1パス×3回だけ**:

- 走行台帳（782MB）を**1回**流す。`ds.etrace._read_all(contains=…)` の篩を使い、
  該当しない行は **`json.loads` すらしない**（所有APIの逐語の作法）
- 明細台帳は `list_evidence(None)` で**1回**全件
- TRACE は task ごとに1 file（小さい）

**直す前は `feed_back` を task ごとに呼び、その度に 782MB を走らせていた** ∴ 15分で終わらず母数が出せなかった。

### 1.2 ★途中で見つけた欠陥を直した

**`scan` と `feed_back` が選ぶ走行がずれていた**（実測: scan は `run_test` を選び、
`feed_back` は `run_minimal_slice` を書いた）。ずれると**書いた後も「未記帳」と言い続ける**。
∴ その task の走行を**全部**持ち、**1つも記帳されていない時だけ**候補にする形にした
（どちらが選ばれても正しく閉じる）。

### 1.3 ★手呼びなしの書き込み（本番の台帳）

`TASK-2DER-02931E17` を並びの先頭に置いただけで、**`feed_back` は手で呼んでいない。**

```
QE-f9cb86fe   ★書いた人: MANAGER_V0.tick / front_door
              LOCAL_MEASUREMENT / MEASURED   ['ETR-8e6031841aa0-0009']
              "run_minimal_slice FAILED / status=FAILED"
★根拠の id も QE- 自体も front door の resolver で引ける
★I1/I2 例外なし（raised=1 / in_flight=1）
★次PLAN入力へ戻る: _detail_facts が 392バイトの事実を返す
   - (request level): verified as LOCAL_MEASUREMENT/MEASURED from ETR-8e6031841aa0-0009
   - UNSETTLED ITEMS IN THIS REQUEST: 1 of 1
★抽出 147件 → 146件（書いた task が候補から消えた）
```

**明細 → PLAN → DW結果 → Evidence記帳 → 次PLAN入力 が、手呼びなしで一周した。**

---

## 2. 条件2 — 計器はできた。効果は ★UNVERIFIED

### 2.1 計器の原理（★文章の一致率を使っていない）

判定は**語の出所**。**実測で締めた**:

| 締めた理由（すべて実測の偽陽性） | 対処 |
|---|---|
| 普通の英単語を数えると**翻訳を発明と誤判定**する（明細「3. book_name が空文字」↔ PLAN "book_name is empty string" で `empty` が新語） | **コード識別子と数だけ**を見る（snake_case / ALL_CAPS / camelCase / 数） |
| `test_impl` … **prompt 自身**が指示する名前（"X.py -> test_X.py"） | prompt 由来語として既知に入れる |
| `APIs` … 依頼文「API」の英語複数形 | 大文字語の末尾 `s` を落として照合 |
| `FileNotFoundError` / `JSONDecodeError` … **prompt が「MUST cover」と命じている** | 同上 |
| `test_existing_account` 等 … **試験関数の名前**（挙動ではない。prompt が `test_` 始まりを命じている） | `test_` 接頭辞の語は取らない |
| `#7` `#8` … 箇条書きの通し番号。★最初の直し方（行頭番号の除去）は**片側にしか効かず**（PLAN は "Test 3:"、明細は "3. …"）逆に `#3` を新語にした | **新語が数だけの時は発明と数えない**（識別子が1つも新しくない） |

**この定義で実測の事故が機械的に捕まる** ―― EF6826DC の発明は
`config_path`（snake_case）と `ERROR`（ALL_CAPS）だった。計器の試験で固定している。

### 2.2 対照（ED65242E / 同一 task / `temperature=0` / seed 0〜7 × 2群 = 16走行）

```
除外(PLAN が出なかった): 1/16
A_no_facts    有効8走行  invented 0,0,0,0,0,0,0,0   invented率 平均 0.000
B_with_facts  有効7走行  invented 0,0,0,0,0,0,0     invented率 平均 0.000

★ノイズ床 0.000 ／ 群間差 0.000  ->  ★UNVERIFIED
```

明細の種別ごとの根拠（延べ）:

```
A_no_facts    SPEC 47 / TEST 48 / FACT 18 / CONSTRAINT 4 / CHANGE 1 / UNSEGMENTED 8
B_with_facts  SPEC 53 / TEST 38 / FACT  9 / CONSTRAINT 3 /            UNSEGMENTED 3
```

### 2.3 ★なぜ効果が出ないか（★これが本当の結論）

**ED65242E では両群とも invented が 0 である。直すべきものが無い。**

この依頼は **SPEC 8 / TEST 6** の完全に仕様化された依頼であり、
事実blockが有っても無くても planner は発明しない。
∴ **この task は効果を測る対照になっていない。**

**効果を測るなら、発明が実際に起きる依頼で測らなければならない。**
実測で存在するのは `EF6826DC`（**SPEC 0 / TEST 0**）で、
**worker が依頼文に無い挙動（`config_path` / `ERROR`）を発明して2周失敗し打ち切られた**案件である。

∴ 次の対照は **EF6826DC** で行うべきである。**本セッションでは実施していない。**

### 2.4 前回の測定との違い（記録として残す）

同じ実験を**偽陽性を含んだ計器**で回した時は、群間差 0.023〜0.025 対 ノイズ床 0.066〜0.375 で
やはり UNVERIFIED だった。**判定は変わらないが、理由が変わった**:
「ノイズに埋もれた」ではなく **「両群とも 0 で差が出ようが無い」** が正しい。

---

## 3. 触っていないもの

- `dev-workcell` 全体 ／ `webui.py` ／ `domain_dw.py`
- `_observation_facts` / `_plan_prompt` の既存の文面
- ED65242E と 02931E17 以外への書き込み（**0件**）
- `EVENT_TYPES` / `DISPOSALS` / `STATES` / `TRANSITIONS`

## 4. 未確認・次に要るもの

1. **EF6826DC（SPEC 0 / TEST 0）での対照が未実施。** 効果の有無はそこで初めて測れる
2. **`PLAN が出なかった` 走行が 1/16 ある。** parse 失敗か生成失敗かを分けていない
3. 計器は **`test_` 接頭辞の語を丸ごと捨てている**。
   ∴ **試験名に紛れ込んだ本物の発明は取りこぼす**（例: `test_config_path_missing`）。
   いまは `test_` を外した残りで判定していないため、**取りこぼしの量を測っていない**
4. 自動循環は `manager_v0.tick` が**並びの先頭1件**しか見ない。
   146件の残りへ広げるかは ③（拡大）の裁定に属する

## 5. 試験

`twoder` 106本（1 skip）＋ `rri` 70本 ＝ **176本 全通過**（新規18本）。
