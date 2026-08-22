# declared — TEST_REPAIR 着手前の全件調査

発: ESDE Evaluation 専任監査（Claude）／ 宛: MGR・Taka
根拠: Taka 指示 2026-08-23 §0「実装前に全件調査。いきなりコードを書かない」§8「Claude 自身がいきなり実装しない」
台帳: `ITEM-2DER-EVO-0090`（REQUEST_DEFECT_AND_SUPERSEDE）
**★実装はしていない。★本書を commit してから設計へ進む。**

---

## ★★0. 調査で根本原因が変わった（★最重要・先に書く）

**私と Taka が共有していた診断 `defect_class = INVENTED_UNSPECIFIED_BEHAVIOR` は、根本原因の取り違えだった。**

`twoder/build_planner.py` の PLAN prompt に **固定の要求が2箇所** 埋まっている（逐語）:

```
:161  '"test_plan": array of strings (each a test case incl. the required error cases),'
:176  '"test_body": string (... MUST cover the missing-file case and the malformed-JSON case),'
```

- ∴ `TASK-2DER-EF6826DC` の `test_missing_file` / `test_malformed_json` は **Qwen の発明ではない。prompt が「必ず入れろ」と命じていた。**
- `config_path` も帰結である。**ファイルを一切扱わない関数**に「ファイル欠損の場合を必ず試験しろ」と要求したので、Qwen は**ファイル引数を作るしかなかった**。
- 検索は2つの鍵で確認した（鍵1=`test_body` の生成箇所 / 鍵2=`MUST cover|required error cases|error case`）。**該当は build_planner.py の2行のみ。**

**★真の欠陥型は `INVENTED_UNSPECIFIED_BEHAVIOR` ではなく、**
**`PLANNER_PROMPT_INJECTS_TASK_IRRELEVANT_TEST_CASES`（生成器が task と無関係な試験を全件に強制する）である。**

**★これは TEST_REPAIR より上流であり、修復機構より先に直すほうが安い。**
修復機構を作っても、**producer が毎回 同じ不整合を注入し続ける**。

**★私の記帳の訂正が要る**: `ITEM-2DER-EVO-0090` の 03:34:48（UPPER_REVIEW_RESULT_FIRST_INSTANCES）で
「5要素は依頼文に1文字も無い」と書いた。**依頼文には無いが ★prompt には在った。**
「私の実測と一致する」と書いたのは、**prompt を読んでいなかったため**である。★本日4回目の「片側だけ見て断定」。

**★ED65242E は別物**: 私の依頼が試験6件を閉じて列挙したため、prompt の固定要求は上書きされた
（新しい封印試験に missing-file / malformed-JSON は **無い**）。ED65242E の欠陥は
`CONTRADICTORY_EXPECTATIONS`（16文字に PENDING と INVALID の両方を期待）で、**原因は私の依頼文**
（「日本語10〜15文字」と書いて **例も日本語で書け** と書かなかった）。**この2件は別の故障型である。**

---

## 1. 試験を生成する既存経路

| # | 経路 | 逐語の位置 |
|---|---|---|
| 1 | **BUILD_PLANNER の prompt** が Qwen に `test_body` を書かせる | `build_planner.py:176` |
| 2 | 投入時のマーカー `<<<2DER:IMMUTABLE_TESTS>>>` | `contract_seal.py:23` |

★鍵2（`def test_` を組み立てる文字列処理）= **0件**。∴ 試験は **LLM が書くか 人が書くか の2つだけ**。

## 2. `immutable_tests` を書く全経路

| # | 書き手 | 出所 | 封印 |
|---|---|---|---|
| 1 | `contract_seal.extract_contract` | raw_input のマーカー | **CREATE payload["contract"] に封印** |
| 2 | `contract_from_plan` | PLAN の `test_body` | **封印しない**（GENERATE のたびに導出） |

★呼び手: `build_planner:377` / `domain_dw:114` / `webui:1266`。
★実測: `ED65242E` も `EF6826DC` も **CREATE に contract 無し = 経路2（PLAN 由来）**。
∴ **PLAN を置き直せば契約も入れ替わる。封印を壊す必要がない。**
★封印を持つ task は `webui` 逐語「**封印契約を持つ task は 1バイトも触らない**」に従い対象外。

## 3. PLAN を再生成・置換する既存経路

- `record_plan` の門 = `_ALLOWED["PLAN"] = {"CREATED", "PLANNING"}`
- **`record_plan` は `has_plan` を見ていない** ∴ **2本目の PLAN は記録できる**
- `derive_state` は PLAN を読むと `state = READY_FOR_IMPLEMENTATION`
- **`PLANNING` を生成する所 = 0件**（鍵1=`state = "PLANNING"` / 鍵2=全 repo の `PLANNING` 文字列。ヒットは STATES 定義と `_ALLOWED` のみ）

**∴ 置換経路は「半分だけ」在る。受け皿と復帰は在り、そこへ送る者だけが居ない。**

## 4. preserve 可能な既存情報（★実測・ED65242E）

| 情報 | 在るか | 出所 |
|---|---|---|
| 元 PLAN の `test_body` 全文 | **在る** | `view["plans"][-1]` |
| 元 `requirement` | **在る** | 同上・finding にも複製 |
| 通った試験名 / 落ちた試験名 | **在る** | `runner_stdout_tail`（500文字） |
| 元契約の SHA | 封印時のみ | `CREATE payload["contract"]` |

## 5. authority / approval の既存規則

- `twoder/authority.py` の表に **試験・契約・PLAN に関する項は無い**（鍵2 で `TEST|CONTRACT|PLAN|SEAL` を検索し、該当は `REGRESSION_TEST`(AUTO_EXECUTE) の1件のみ）
- `record_plan` に **authority 検査は無い**（`_require_state` のみ）
- ∴ **PLAN の置き直しに既存の承認規則は存在しない。**★新設するなら Taka 裁定が要る。

## 6. `ORACLE_DEFECT` の producer / consumer

- **producer = 1つ**: `dw/adjudicator.adjudicate`（tier2 参照オラクル）
- **consumer = 1つ**: `dw/workcell.py:180`（本日 `test_repair_gate` を挟んだ）
- 他は `experiments/` のみ。★本番の消費者は **1箇所しかない**。

## 7. TEST_REPAIR 相当の既存機能

**0件。** 鍵1=`regenerate_test|test_repair|fix_test|rewrite_test`（作用）／
鍵2=`TEST_REPAIR|REPAIR_REQUIRED|ORACLE_ISOLATION|REGENERATE_TEST`（状態語）。
本日私が置いた `test_repair_gate` 以外のヒットは無い。

## 8. supersede との関係

- 本日実装（`supersede_seal` / `create_task(supersedes=)` / `superseded_by()`）
- **supersede = 設問ごと作り直す（新ID）／ TEST_REPAIR = 同一ID内で試験だけ直す**
- ★重ならない。★但し **どちらを使うかの判定規則が無い** ―― これは欠損として記録する。

## 9. 修復後に通常経路へ戻す既存入口

**在る。** `PLANNING` → `record_plan` → `READY_FOR_IMPLEMENTATION` → 以後は通常の GENERATE/AUDIT/DISPOSE。
★新しい復帰口を作る必要はない。

---

## ★★調査から出た結論（★設計の前に Taka の裁定を求める点）

1. **TEST_REPAIR を作る前に、producer を直すほうが安い。**
   `build_planner.py:176` の「MUST cover the missing-file case and the malformed-JSON case」は
   **task の内容と無関係に全件へ注入される**。これが在る限り、修復機構は同じ不整合を毎回受ける。
   ★但しこの1行を消すと **ファイルを扱う task の試験が薄くなる可能性** が在る。
   ∴ 「消す」ではなく「**task が file を扱う時だけ要求する**」が筋だが、
   ★それを決定論で判定できるかは **未検証（UNVERIFIED）**。

2. **`ED65242E` は producer 起因ではない。** ∴ TEST_REPAIR の実証例としては **依然有効**。

3. **supersede と TEST_REPAIR の使い分け規則が無い。** ★別 AXIS として立てる。

4. **失敗型を再利用可能な knowledge として残す既存経路** は
   `finding`（署名は在るが front door の投影が落とす・22:19 に指摘済）と
   `function_table`（既知の失敗型の器になり得るが本線の自動呼び手0）の2つ。
   ★新台帳は作らない。★どちらに載せるかは MGR の EXPERIENCE_REUSE_CYCLE（EVO-0083）と重なる。

## ★私がしていないこと

★TEST_REPAIR の実装 0 ／ producer の修正 0 ／ 新台帳 0 ／ 新 authority 0 ／ 新 front door 口 0。
★本日置いたのは `test_repair_gate`（**分離して停止するところまで**・Taka 指示の範囲）のみ。
