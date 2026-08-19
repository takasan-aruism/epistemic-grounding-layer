# 宛: Taka ―― **★自己修正は 成立した ／ ★★2DER 自身の 作法が 2DER の 監査に 誤検知を 起こした**

**`TASK-2DER-99CB3F62` ／ 2026-08-20 00:5x**
**★SELF_DEV_TOKEN = ★5/5（未消費）／ ★twoder HEAD = `3dd7d02`（不変）／ ★常駐 停止のまま**

---

## 1. ★★今夜 初めて ―― **自分で 直して 試験を 通した**

```
★GENERATE   passed = ★False ／ reason = RUNNER_FAILED ／ exit = 1 ／ sha = b2d21acb65a3
★★REGENERATE passed = ★★True ／ reason = "" ／ sha = e75ddeccc4c4
★★＝ ★2DER が ★自分の 失敗を ★自分の rework で ★通した（★Claude の 補完 0）
```

**★作った もの（★逐語・★2DER の PLAN）:**

```
requirement 「… a function ★adjudicate(input_data) that accepts either a dictionary or a
             JSON string. … validate required fields, check if a referenced source_file
             exists, and evaluate the request against ★deterministic rules …」
steps 「Implement ★deterministic decision engine that evaluates facts against rules.」
      「Implement ★rationale generator that attaches clear reasoning to each decision.」
      「Implement ★handoff payload formatter for downstream consumption.」
scope 「… ★No external API calls, database writes, or filesystem modifications
        outside the target workspace.」
```

**★成果物は ★実装されている（★私が 中身を 確認した）:**

```
★artifact = ★3449バイト ／ sha256 = e75ddeccc4c4…
★中身 = JSON 文字列/辞書の 受け入れ ／ 型検査 ／ ★"decision": "cannot_decide" の 分岐
        ／ "rationale" ／ "handoff" ／ error 語
★★＝ ★空実装では ない。★『決めきれない』を 出す 分岐も 実装されている。
```

## 2. ★★但し 完了しない ―― **上級監査が FAIL（★★誤検知）**

**`claude-senior` の 判断（★逐語・抜粋）:**

> 「★artifact_head の関数本体が依頼文そのままの docstring で、★実装が入っていない疑いが濃く、
> しかも契約は adjudicate(★input_data) なのに実物は adjudicate(★a) と★引数名が違う …
> ★封印試験が空実装を検知できていない可能性を示すため、試験が通ったことを完了の根拠にできない。」

**★★この 2つの 根拠は ★どちらも ★2DER 自身の 作法が 作った もの:**

```
★① 「docstring が 依頼文そのまま」
   ← ★`contract_from_plan` の 仕様（逐語）:
     「2行目は 空白4つと 三重引用符と ★requirement の1行と 三重引用符」
   ＝★★骨格が そう 作る 決まり。★実装の 有無とは 無関係。

★② 「契約は input_data なのに 実物は a」
   ← ★`contract_from_plan` の 仕様（逐語）:
     「引数は ★a, b, c … の順に、引数の数だけ ', ' で繋いだ名前にする」
   ＝★★骨格が 引数名を 潰す 決まり。★worker は 骨格に 従っただけ。

★★∴ ★上級監査は ★『2DER の 骨格生成規則の 出力』を ★『実装の 欠落』と 読んだ。
★★∴ ★正しく 実装され 試験も 通った 成果物が ★誤って FAIL に なった。
```

**★根拠（★私が 実物で 確かめた）:** artifact の 先頭は docstring だが、その ★直後から
`try:` / `isinstance(a, str)` / `json.loads` / `cannot_decide` の 分岐が ★実際に 書かれている。
**★上級監査は `artifact_head`（★先頭だけ）を 見て 判断している。**

## 3. ★もう1つ ―― **DISPOSE も 確定できない（★観測性の 傷）**

```
★DISPOSE 逐語 = {"verdict": ★"REMAINS", "defect_class": ★"INDETERMINATE",
   "basis": ["★no neutral runner result (exit_code=None, empty stdout/stderr);
             worker self-report is not a basis"]}
★★＝ ★成功した とき ★`runner_exit` と `runner_stdout_tail` を ★記録しない 設計 ∴
   ★裁定器が ★『通った』ことを ★証拠として 使えない。
★（★これは 私が 2026-08-19 に 記録した 傷 ③ が ★顕在化した もの）
```

## 4. ★★連鎖の 全体（★事実の 並び）

```
★① 2DER が 自分で 直して 試験を 通した（★成果）
★② しかし 成功時の runner 証拠が 記録されない → ★DISPOSE は INDETERMINATE
★③ 上級監査は artifact_head だけを 見る → ★骨格の 作法を 実装欠落と 誤読 → ★FAIL
★④ state = JUDGE_REQUIRED ／ `should_call_senior` は 次を 拒む（進展なし）
★★∴ ★正しい 成果物が ★完了に ならず ★止まる。
```

## 5. ★Claude が していないこと

```
★正解 0 ／ 判断基準 0 ／ 修正箇所 0 ／ 実装 0 ／ 契約 0 ／ 骨格 0 ／ 封印試験 0
★上級監査の 判断を ★書き換えていない ／ 記録を 訂正していない
★run_next 0 ／ 手動前進 0 ／ 常駐 再開 0 ／ 実 repo 書き込み 0（★HEAD 不変で 実証）
★★SELF_DEV_TOKEN = ★5/5（★1周が 閉じていない ∴ 消費 0）
```

## 6. ★上申（★私は 案を 出しません）

```
★★『2DER の 骨格生成規則』と『2DER の 上級監査の 読み方』が ★食い違っている。
   ・骨格は ★requirement を docstring に 入れ ★引数名を a,b,c に する
   ・上級監査は ★それを 実装欠落・契約違反と 読む
★★どちらを 直すかは ★設計判断 ∴ ★Taka の 裁定 か ★2DER への 差し戻し。
★★併せて ―― ★成功時に runner 証拠を 残さない 設計も ★同じ 停止に 効いている。
```
