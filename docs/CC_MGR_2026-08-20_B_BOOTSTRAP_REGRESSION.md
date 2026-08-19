# 宛: Taka ―― **上位欠陥 B ブートストラップ修正 と ★回帰試験の 結果**

**修正 commit `24c649a` ／ 2026-08-20 03:0x-03:1x**
**★SELF_DEV_TOKEN = ★5/5 ／ ★常駐 停止のまま ／ ★実 repo 書き込み 0**

---

## 1. ★直した 3点（★抑制 0 ／ 情報削除 0）

| # | file | 変更 | 実測された 根拠 |
|---|---|---|---|
| ① | `generate_via_runner.py` | ★成功時にも `artifact_head` を 載せる（★証拠を 足すだけ） | ★`senior_review.py:32-39` は `artifact_head` だけを 見る が、その 欄は `SKELETON_VIOLATION` 経路(:347)でしか 作られない ∴ ★成功時は None ＝ ★上級監査に 実装が 1文字も 見えない |
| ② | `domain_dw.py` | ★precheck の 注記を ★成果物の docstring へ 差し込むのを やめる（★注記は `precheck` に 残る） | ★2件で `dead_guard` / `self_report_primitive` の 根拠に された |
| ③ | `contract_from_plan.py` | ★契約に 署名が 在れば ★その 引数名を 使う（★読めない 時は 従来どおり `a,b,c` ＝ fail-safe） | ★3件で「契約は f(file_path) なのに 実物は f(a)」＝ 署名不一致 と 読まれた |

## 2. ★回帰試験（★元の goal 文を そのまま 再投入）

```
99CB3F62 → ★22CD9E77 ／ E8AAEA8C → ★491FDE7F
3361D3E1 → ★A1E15473 ／ A36B3881 → ★E7E65315
```

### ★修正が 効いた 実測

```
★注記が 骨格に 入っているか = ★4件とも ★False（★修正前は 必ず 入っていた）
★引数名 = ★`def adjudicate(★context)` ／ ★`def load_task(★path)`（★修正前は `(a)`）
   ※ `validate_segment_endpoint(a)` は ★requirement に 署名が 無く ★fail-safe が 働いた（★想定内）
★`artifact_head` = ★成功時に 載るように なった（★`22CD9E77` は passed=True で ★head 有）
```

### ★合格条件の 判定

| # | 条件 | 結果 | 根拠 |
|---|---|---|---|
| ① | 機械生成物 由来の 偽陽性が 消える | **★達成** | ★findings は ★`test_failure` のみ。★`dead_guard` 0 ／ `self_report_primitive` 0 ／ `scope_expansion` 0（★修正前は 3件） |
| ② | 実装 由来の 正当な finding は 残る | **★達成** | ★`test_failure` が 残る（★2件は 実際に passed=False）／ ★上級監査も 実質的な 指摘を 出している |
| ③ | B 修理 task 自身が B で 止まらない | **★達成** | ★★FAIL の 根拠が ★別の 欠陥に 変わった（★下記） |

### ★★③の 根拠 ―― **上級監査の 言い分が 変わった**

```
★修正前（`A36B3881`）:
  「artifact_head の関数本体が依頼文そのままの docstring で、★実装が入っていない疑いが濃く」
  「契約は adjudicate(input_data) なのに実物は adjudicate(★a) と引数名が違う」
  ＝ ★★B 由来の 偽陽性

★★修正後（`22CD9E77`・★passed=True）:
  「★成果物が repo に無い（dev-workcell/contracts/out に … RESULT_PACKET も SANDBOX_ARTIFACT も
   無く、sha … は events.jsonl の記録にしか存在せず …）うえ、生成された
   `adjudicate(context: dict) -> dict` は既存の adjudicator.adjudicate / judge.adjudicate の
   ★どの signature とも一致せず ★呼び手が0で、依頼の『記録に残し、次の作業へ繋ぐ』が
   満たされていない」
```

```
★★＝ 監査は ★実装を 正しく 読めるように なった（★`adjudicate(context)` を 正確に 引用）。
★★＝ FAIL の 根拠は ★『実装が 無い』では なく ★『配置と 結線が 無い』
   ＝ ★★上位欠陥 C（作れる ／ 繋がらない）＝ ★実在する 欠陥の ★正当な 指摘。
```

## 3. ★残存（★隠さない）

```
★`docstring` が requirement の 丸写し という 規約は ★残っている
   （★worker が 要件を 見る 唯一の 面 ∴ ★変えていない）
★監査は それを ★補足と して 述べる が ★もう「実装が 無い」とは 結論しない
★`E7E65315`（4件目）は ★着地が 遅れ ★別途 実走中 ―― ★結果は 追記する
★上級監査は ★依然 FAIL を 出す ―― ★但し ★理由は C（★B では ない）
```

## 4. ★ブートストラップ 終了

```
★★Taka の 指示どおり ―― ★ここで 終了する。
★★これ以上 Claude は ★設計も 修正も 続けない。
★次に 停止が 出たら ★2DER へ 戻す（★通常の 運転に 復帰）。
```

## 5. ★していないこと

```
★A / C / D / E の 修正 0（★B のみ）／ ★判定ロジックの 抑制 0 ／ ★情報の 削除 0
★経路表 未変更 ／ `name_matches_route` 未変更 ／ `precheck_names` の ★判定 未変更
   （★変えたのは ★注記を 成果物へ 差し込む 1箇所だけ）
★DISPOSE 0（★滞留 2件 `E8AAEA8C` `3361D3E1` は 未接触）
★実 repo 書き込み 0 ／ 常駐 停止のまま ／ `MANAGER_V0_ONCE` のみ
★SELF_DEV_TOKEN = ★5/5（★1周が 閉じていない ∴ 消費 0）
```
